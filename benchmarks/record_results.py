"""Export aggregate-only evidence from completed benchmark JSON reports."""
import argparse
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("reports", nargs="+", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    measurements, runs = [], []
    for path in args.reports:
        report = json.loads(path.read_text())
        runs.append({k: report.get(k) for k in ("run_id", "mode", "seed", "git_revision", "source_sha256",
                                               "versions", "platform", "python", "wall_seconds", "training_p_error",
                                               "policy_probes", "output_leakage_control")})
        for row in report["workloads"]:
            audit = row.get("fhe", {}).get("training_audit", {})
            measurement = {"run_id": report["run_id"], "dataset": row["dataset"], "status": row["status"],
                           "p_error": report.get("training_p_error"), "rows": row.get("rows"),
                           "groups": row.get("independent_groups"), "actual_training_records": row.get("actual_training_records"),
                           "steps": row.get("steps"), "batch_size": row.get("batch_size"),
                           "float": row.get("float", {}).get("utility"),
                           "quantized": row.get("quantized", {}).get("utility"),
                           "fhe": row.get("fhe", {}).get("utility"),
                           "max_weight_error": row.get("fhe", {}).get("max_weight_difference_vs_quantized"),
                           "inference_error": row.get("fhe", {}).get("inference", {}).get("max_difference_vs_quantized"),
                           "count_error": row.get("query", {}).get("absolute_error"),
                           "count_unit": "records; not globally deduplicated patients",
                           "engineering_checks": row.get("engineering_checks"),
                           "training_compute_seconds": sum(audit.get("seconds", {}).get("updates", [])),
                           "training_dispatch_seconds": audit.get("process_seconds"),
                           "training_request_bytes": audit.get("request_bytes"),
                           "evaluation_key_bytes": audit.get("evaluation_key_bytes"),
                           "execution_environment": audit.get("execution_environment", "local subprocess"),
                           "encrypted_silo_blob_count": audit.get("encrypted_silo_blob_count"),
                           "query_execution_environment": row.get("query", {}).get("audit", {}).get("execution_environment"),
                           "query_encrypted_silo_blob_count": row.get("query", {}).get("audit", {}).get("encrypted_silo_blob_count"),
                           "inference_execution_environment": "local subprocess" if row.get("fhe", {}).get("inference") else "not run",
                           "attacks": row.get("attacks", [])}
            if "error" in row:
                measurement["error"] = row["error"]
            measurements.append(measurement)
    output = {"runs": runs, "measurements": measurements,
              "scope": "Engineering smoke tests, 4 updates of 8 records; not clinical validation or proof of privacy.",
              "comparison": "Library-default failures and stricter numerical-error runs are separate measurements; see local-evidence.json for both.",
              "privacy": "Shared customer-key gateway; released counts/models and metadata can leak; no DP or malicious-worker proof."}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2, allow_nan=False) + "\n")
    lines = ["# Measured benchmark evidence", "", output["scope"], "", output["comparison"], "",
             "| Dataset | PBS error | Status | Float AUROC | FHE AUROC | Weight error | Count error | Training compute (s) |",
             "|---|---:|---|---:|---:|---:|---:|---:|"]
    def number(value):
        return "—" if value is None else f"{value:.5g}"
    for item in measurements:
        lines.append("| " + " | ".join([item["dataset"], number(item["p_error"]), item["status"],
            number((item["float"] or {}).get("auroc")), number((item["fhe"] or {}).get("auroc")),
            number(item["max_weight_error"]), number(item["count_error"]), number(item["training_compute_seconds"])]) + " |")
    lines += ["", "All numerical failures are kept visible. A passing correctness check is not a privacy certification.",
              "", "The full JSON includes membership-attack metrics, source hashes, versions and communication sizes."]
    args.output.with_suffix(".md").write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
