"""Reproducible real-data utility, leakage, protocol and system benchmarks."""
import argparse
import importlib.metadata
import json
from pathlib import Path
import platform
import subprocess
from time import perf_counter
import uuid
import numpy as np
from sklearn.metrics import accuracy_score, average_precision_score, brier_score_loss, f1_score, roc_auc_score
from diabetes_demo.experiments import fitted_model, float_training
from .attacks import differencing_control, gradient_positive_control, loss_probe, policy_attacks, shadow_lira_probe
from .datasets import TRAINING_DATASETS, batches_for_sites, inventory, load, partition
from .queries import Query, owner_count
from .security import Ledger, digest


def utility(model, X, y):
    p = model.predict_proba(X)[:, 1]
    return {"accuracy": float(accuracy_score(y, p > .5)),
            "f1": float(f1_score(y, p > .5, zero_division=0)),
            "auroc": float(roc_auc_score(y, p)) if len(set(y)) > 1 else None,
            "auprc": float(average_precision_score(y, p)) if len(set(y)) > 1 else None,
            "brier": float(brier_score_loss(y, p)), "test_rows": len(y), "test_positives": int(y.sum())}


def run_dataset(name, mode, steps, seed, authority_ledger, cache, inference_rows, p_error=.01):
    from .backend import compile_trainer, encrypted_count, encrypted_training, quantized_training
    from diabetes_demo.crypto import infer, timed
    table = load(name)
    X, clipped = table.normalized()
    sites, test = partition(table, seed)
    batches = batches_for_sites(sites, steps, seed)
    ordinary, float_seconds = timed(float_training, X, table.y, batches)
    row = {"dataset": name, "mode": mode, "status": "completed", "task": table.task,
           "rows": len(X), "independent_groups": len(np.unique(table.groups)),
           "site_rows": [len(site) for site in sites], "train_pool_rows": sum(map(len, sites)),
           "actual_training_records": len(np.unique(np.concatenate(batches))),
           "test_groups": len(np.unique(table.groups[test])), "features": table.features,
           "normalization_clipped_values": clipped, "steps": steps, "batch_size": 8,
           "contract_hash": digest(table.contract()),
           "float": {"utility": utility(ordinary, X[test], table.y[test]), "train_seconds": float_seconds},
           "attacks": [gradient_positive_control(X, table.y), loss_probe(ordinary, X, table.y, batches, test),
                       shadow_lira_probe(ordinary, X, table.y, table.groups, batches, test, seed)]}
    query = Query(table.features[0], "ge", table.bounds[0][0])
    # All records, including held-out records, participate in a separate cohort-query workload.
    unique_groups = np.unique(table.groups)
    query_sites = [np.flatnonzero(np.isin(table.groups, unique_groups[i::4])) for i in range(4)]
    counts = [owner_count(table, site, query) for site in query_sites]
    reference = sum(counts)
    row["query"] = {"spec": query.to_dict(), "oracle_total": reference,
                    "release": "exact approved total only; no site subtotals", "dp": False}
    if mode == "baseline":
        row["query"]["backend"] = "plaintext oracle only"
        row["fhe"] = {"status": "not_run"}
        return row
    if X.shape[1] not in cache:
        print(f"  Compiling {X.shape[1]}-feature training circuit using public bounds", flush=True)
        cache[X.shape[1]] = compile_trainer(X.shape[1], seed, p_error)
    trainer, calibration, compile_seconds = cache[X.shape[1]]
    (qw, qb), quantized_seconds = timed(quantized_training, trainer, X, table.y, batches)
    quantized = fitted_model(qw, qb)
    row["quantized"] = {"utility": utility(quantized, X[test], table.y[test]),
                        "training_p_error": trainer.training_p_error,
                        "training_n_bits": trainer.n_bits_training,
                        "train_seconds": quantized_seconds, "public_circuit_compile_seconds": compile_seconds,
                        "probability_mae_vs_float": float(np.mean(np.abs(
                            quantized.predict_proba(X[test])[:, 1] - ordinary.predict_proba(X[test])[:, 1])))}
    if mode == "quantized":
        row["query"]["backend"] = "plaintext oracle only"
        row["fhe"] = {"status": "not_run", "note": "quantized arithmetic is NOT encrypted execution"}
        return row
    weights, bias, audit = encrypted_training(trainer, X, table.y, batches, row["contract_hash"], authority_ledger)
    protected = fitted_model(weights, bias)
    train_difference = float(max(np.max(np.abs(weights - qw)), np.max(np.abs(bias - qb))))
    row["fhe"] = {"status": "executed", "utility": utility(protected, X[test], table.y[test]),
                  "max_weight_difference_vs_quantized": train_difference, "training_audit": audit}
    row["attacks"].append(loss_probe(protected, X, table.y, batches, test) | {"model": "FHE-trained, customer-released"})
    row["attacks"].append(shadow_lira_probe(protected, X, table.y, table.groups, batches, test, seed)
                          | {"model": "FHE-trained, customer-released"})
    if inference_rows:
        from concrete.ml.sklearn import LogisticRegression as ConcreteLogisticRegression
        encrypted_model = ConcreteLogisticRegression.from_sklearn_model(protected, calibration, n_bits=6)
        _, compile_inference = timed(encrypted_model.compile, calibration)
        subset = X[test[:inference_rows]]
        expected = encrypted_model.predict_proba(subset, fhe="disable")
        actual, infer_audit = infer(encrypted_model, subset)
        row["fhe"]["inference"] = {"rows": len(subset), "compile_seconds": compile_inference,
                                    "max_difference_vs_quantized": float(np.max(np.abs(actual - expected))),
                                    "audit": infer_audit,
                                    "policy_scope": "internal benchmark of teammate's inference worker; not a public release API"}
    total, query_audit = encrypted_count(counts, row["contract_hash"], authority_ledger, query_spec=query.to_dict())
    row["query"].update({"backend": "real FHE", "released_total": total,
                         "absolute_error": abs(total - reference), "audit": query_audit})
    row["engineering_checks"] = {"exact_training_quantized_parity": train_difference < 1e-8,
                                  "exact_query_parity": total == reference,
                                  "wrong_key_rejected_empirically": audit["wrong_key_recovery_failed"]}
    if not all(row["engineering_checks"].values()):
        row["status"] = "failed_engineering_check"
    return row


def write_report(path, report):
    path.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    lines = ["# Platform benchmark", "", f"Run: `{report['run_id']}` · mode: `{report['mode']}`", "",
             "This is an engineering benchmark, not a security certification or clinical validation.", "",
             "| Dataset | Status | Float AUROC | Quantized AUROC | FHE AUROC | Query error |",
             "|---|---|---:|---:|---:|---:|"]
    def score(row, key):
        value = row.get(key, {}).get("utility", {}).get("auroc")
        return "—" if value is None else f"{value:.4f}"
    for row in report["workloads"]:
        lines.append(f"| {row['dataset']} | {row['status']} | {score(row, 'float')} | {score(row, 'quantized')} | {score(row, 'fhe')} | {row.get('query', {}).get('absolute_error', 'not run')} |")
    lines += ["", "## Boundaries", ""] + [f"- {v}" for v in report["limitations"]]
    path.with_suffix(".md").write_text("\n".join(lines) + "\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["baseline", "quantized", "execute"], default="baseline")
    parser.add_argument("--datasets", nargs="+", choices=TRAINING_DATASETS, default=list(TRAINING_DATASETS))
    parser.add_argument("--steps", type=int, default=4)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--inference-rows", type=int, default=2)
    parser.add_argument("--p-error", type=float, default=.01, help="Concrete ML training PBS numerical error setting")
    parser.add_argument("--output", type=Path, default=Path("outputs/platform"))
    args = parser.parse_args()
    if args.steps < 4 or args.steps > 16 or args.inference_rows < 0 or not 0 < args.p_error < 1:
        parser.error("prototype supports 4–16 updates, and nonnegative inference rows")
    run_id = uuid.uuid4().hex
    destination = args.output / run_id
    destination.mkdir(parents=True, exist_ok=False)
    try:
        revision = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    except (OSError, subprocess.CalledProcessError):
        revision = "unavailable"
    from .datasets import file_hash
    sources = sorted(Path("nftpz_platform").glob("*.py")) + sorted(Path("diabetes_demo").glob("*.py"))
    report = {"run_id": run_id, "mode": args.mode, "seed": args.seed, "git_revision": revision,
              "source_sha256": {str(path): file_hash(path) for path in sources}, "training_p_error": args.p_error,
              "platform": platform.platform(), "python": platform.python_version(),
              "versions": {name: importlib.metadata.version(name) for name in ("concrete-ml", "concrete-python", "numpy", "scikit-learn")},
              "inventory": inventory(), "policy_probes": policy_attacks(),
              "output_leakage_control": differencing_control(), "workloads": [],
              "limitations": [
                  "Customer-controlled shared-key encryption gateway; not multi-key or threshold FHE.",
                  "Cloud worker receives ciphertexts and evaluation keys, but local same-user processes are NOT an OS isolation boundary.",
                  "Azure container identity/private network deployment is separate and not proven by these local results.",
                  "Four tiny updates test the pipeline, not converged clinical utility. Group-held-out splits, public fixed normalization bounds.",
                  "FHE hides computation inputs, not approved outputs. Exact counts remain vulnerable to differencing; no differential privacy.",
                  "FHE does not prove worker correctness or stop malicious owner poisoning, traffic analysis, or compromised key authorities.",
                  "Site labels, schedule, dimensions and ciphertext sizes remain visible to the cloud worker.",
                  "Loss-threshold and 32-shadow Gaussian LiRA adaptation are preliminary; float surrogates, no exact Concrete-shadow or RMIA reproduction.",
                  "No raw records, record identifiers, private keys or patient predictions are included in these reports.",
                  "Local audit hashes are not externally anchored; no crash-resumable training or remote attestation yet.",
              ]}
    start = perf_counter()
    ledger = Ledger(destination / "authority.sqlite")
    cache = {}
    try:
        for name in args.datasets:
            print(f"[{name}] {args.mode}: starting", flush=True)
            try:
                row = run_dataset(name, args.mode, args.steps, args.seed, ledger, cache, args.inference_rows, args.p_error)
            except Exception as error:
                import traceback
                traceback.print_exc()
                row = {"dataset": name, "status": "failed", "error": f"{type(error).__name__}: {error}"}
            report["workloads"].append(row)
            report["wall_seconds"] = perf_counter() - start
            write_report(destination / "report.json", report)
            print(f"[{name}] {row['status']}", flush=True)
    finally:
        ledger.close()
    print(destination / "report.json", flush=True)
    if any(row["status"] != "completed" for row in report["workloads"]):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
