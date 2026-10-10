"""Executable probes with explicit surfaces and negative/positive controls."""
import base64
import copy
import tempfile
from pathlib import Path
import time
import numpy as np
from .metrics import membership_metrics
from .security import Authority, Denied, Ledger, digest, make_manifest, verify
from .worker import validate_request


def policy_attacks():
    authority = Authority()
    request = {"operation": "aggregate", "evaluation_keys": base64.b64encode(b"test-eval-key").decode(),
               "inputs": ["AA=="] * 4}
    policy = {"principal": "benchmark-client", "min_cohort": 5, "max_releases": 1}
    manifest = make_manifest(request, "program", "schema", "test", policy)
    approval = authority.approve(manifest)
    results = []
    def check(name, action):
        try:
            action()
        except (Denied, ValueError):
            results.append({"id": name, "blocked": True, "risk": ["IND", "ORG"]})
        else:
            results.append({"id": name, "blocked": False, "risk": ["IND", "ORG"]})
    verify(approval, authority.public_key, request, "program")  # positive allowed control
    for field, value in [("purpose", "unauthorized"), ("schema_hash", "wrong"), ("key_id", "wrong")]:
        modified = copy.deepcopy(approval)
        modified["manifest"][field] = value
        check(f"unsigned-{field}-tamper", lambda a=modified: verify(a, authority.public_key, request, "program"))
    check("wrong-program", lambda: verify(approval, authority.public_key, request, "changed"))
    check("expired", lambda: verify(approval, authority.public_key, request, "program", now=time.time() + 7200))
    check("ciphertext-tamper", lambda: verify(approval, authority.public_key, {**request, "inputs": ["AQ=="] * 4}, "program"))
    check("untrusted-signer", lambda: verify(approval, Authority().public_key, request, "program"))
    check("missing-site", lambda: validate_request({**request, "inputs": request["inputs"][:3]}))
    for field in ("plaintext", "secret_key", "labels"):
        check(f"reject-{field}", lambda f=field: validate_request({**request, f: "forbidden"}))
    with tempfile.TemporaryDirectory() as temp:
        ledger = Ledger(Path(temp) / "audit.sqlite")
        ledger.claim(manifest)
        check("job-replay", lambda: ledger.claim(manifest))
        check("small-cohort", lambda: ledger.release(manifest, cohort_size=1))
        check("unauthorized-reader", lambda: ledger.release(manifest, cohort_size=10, caller="other"))
        ledger.release(manifest, cohort_size=10)
        check("duplicate-release", lambda: ledger.release(manifest, cohort_size=10))
        check("query-budget", lambda: ledger.release({**manifest, "job_id": "new"}, cohort_size=10))
        results.append({"id": "audit-hash-chain", "passed": ledger.audit_valid(), "risk": ["ORG"]})
        ledger.db.execute("UPDATE events SET event='{}' WHERE seq=1")
        results.append({"id": "audit-tamper-detection", "passed": not ledger.audit_valid(), "risk": ["ORG"]})
        ledger.close()
    return results


def loss_probe(model, X, y, batches, test):
    members = np.unique(np.concatenate(batches))
    def losses(indices):
        p = np.clip(model.predict_proba(X[indices])[:, 1], 1e-12, 1 - 1e-12)
        return -(y[indices] * np.log(p) + (1-y[indices]) * np.log(1-p))
    return {"id": "MIA-loss-threshold", "method": "Yeom et al. loss-based membership probe (adapted)",
            "risk": ["IND", "BIO"], "surface": "customer-released model, not ciphertext",
            "query_budget": len(members) + len(test),
            "metrics": membership_metrics(losses(members), losses(test))}


def gradient_positive_control(X, y):
    # For ONE clear binary-logistic example: dL/dw = x*dL/db.
    # This algebraic control is not a claimed implementation of DLG/Geiping.
    x, label = X[0], y[0]
    db = .5 - label
    recovered = x * db / db
    return {"id": "single-example-gradient-ratio", "risk": ["IND", "BIO"],
            "surface": "unprotected single-example gradient plus bias gradient",
            "reconstruction_rmse": float(np.sqrt(np.mean((x - recovered) ** 2))),
            "encrypted_cloud_surface": "not exposed by this protocol",
            "caution": "positive control only; not an attack on FHE"}


def differencing_control():
    # k-threshold alone does not stop two LARGE adjacent cohort answers.
    return {"id": "adjacent-cohort-differencing", "risk": ["IND", "BIO", "ORG"],
            "surface": "two released exact counts", "query_budget": 2,
            "unprotected_target_recovery": (31 - 30 == 1),
            "both_counts_pass_min_cohort_5": True, "residual_risk": "OPEN",
            "needed": "reviewed query families or correctly accounted DP; rate limiting is not DP"}


def gaussian_likelihood_ratio(target, in_confidence, out_confidence):
    """Per-example Gaussian LiRA-style log likelihood ratio, with variance floor."""
    from scipy.stats import norm
    inside = np.asarray(in_confidence)
    outside = np.asarray(out_confidence)
    return norm.logpdf(target, inside.mean(axis=0), np.maximum(inside.std(axis=0), 1e-3)) - norm.logpdf(
        target, outside.mean(axis=0), np.maximum(outside.std(axis=0), 1e-3))


def shadow_lira_probe(model, X, y, groups, batches, test, seed=42, shadows=32):
    """Small, explicit online Gaussian LiRA adaptation for logistic workloads.

    Knows candidate features/labels; trains paired in/out shadow models. Uses
    floating-point logistic surrogates, so it is NOT a faithful full-paper
    reproduction against Concrete quantized training. No record IDs emitted.
    """
    from diabetes_demo.experiments import float_training
    from time import perf_counter
    started = perf_counter()
    rng = np.random.default_rng(seed)
    def one_per_group(indices):
        seen, chosen = set(), []
        for index in rng.permutation(indices):
            if groups[index] not in seen:
                seen.add(groups[index])
                chosen.append(index)
        return np.array(chosen, dtype=int)
    member = one_per_group(np.unique(np.concatenate(batches)))
    nonmember = one_per_group(test)
    n = min(32, len(member), len(nonmember), len(batches) * 8)
    if n < 4:
        return {"id": "MIA-LiRA-logistic-adaptation", "status": "insufficient_independent_candidates"}
    candidate = np.r_[member[:n], nonmember[:n]]
    candidate_groups = set(groups[candidate])
    auxiliary = np.array([i for i in range(len(X)) if groups[i] not in candidate_groups], dtype=int)
    def confidence(fitted):
        p = fitted.predict_proba(X[candidate])[:, 1]
        correct = np.clip(np.where(y[candidate] == 1, p, 1-p), 1e-8, 1-1e-8)
        return np.log(correct) - np.log1p(-correct)
    inside, outside = [[] for _ in candidate], [[] for _ in candidate]
    for _ in range(shadows // 2):
        permutation = rng.permutation(len(candidate))
        for included in (permutation[:n], permutation[n:]):
            selected = candidate[included]
            pool = np.r_[selected, auxiliary]
            # Every claimed shadow member appears in at least one update.
            schedule = np.r_[selected, rng.choice(pool, len(batches)*8-len(selected), replace=True)]
            schedule = rng.permutation(schedule).reshape(len(batches), 8)
            fitted = float_training(X, y, schedule)
            scores = confidence(fitted)
            for i, value in enumerate(scores):
                (inside if i in included else outside)[i].append(value)
    target_scores = gaussian_likelihood_ratio(confidence(model), np.asarray(inside).T, np.asarray(outside).T)
    # Threshold calibration is disjoint from the reported attack evaluation.
    split = max(1, n // 2)
    calibrated_negative = target_scores[n:n+split]
    threshold = float(np.max(calibrated_negative))
    eval_positive, eval_negative = target_scores[split:n], target_scores[n+split:]
    metrics = membership_metrics(-eval_positive, -eval_negative, seed=seed)
    metrics.update({"heldout_tpr_at_calibrated_threshold": float(np.mean(eval_positive > threshold)),
                    "heldout_fpr_at_calibrated_threshold": float(np.mean(eval_negative > threshold)),
                    "calibration_nonmembers": split})
    return {"id": "MIA-LiRA-logistic-adaptation", "risk": ["IND", "BIO"],
            "source": "https://arxiv.org/abs/2112.03570", "surface": "released model probabilities",
            "shadow_models": shadows, "in_and_out_models_per_candidate": shadows // 2,
            "candidate_unit": "one record per independent group", "target_queries": len(candidate),
            "shadow_prediction_queries": shadows * len(candidate),
            "metrics": metrics, "seconds": perf_counter()-started,
            "assumptions": "known candidate features/labels and auxiliary same-distribution records",
            "limitations": "32 float logistic surrogates; not exact quantized shadows or full-paper reproduction; tiny low-FPR sample"}
