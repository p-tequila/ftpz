"""Small, dependency-free metrics used by the first benchmark harness."""

from math import sqrt
from typing import Iterable


def relative_error(actual: float, reference: float) -> float:
    denominator = max(abs(reference), 1e-12)
    return abs(actual - reference) / denominator


def rmse(actual: Iterable[float], predicted: Iterable[float]) -> float:
    actual, predicted = list(actual), list(predicted)
    if len(actual) != len(predicted):
        raise ValueError("metric inputs must have equal lengths")
    errors = [(a - p) ** 2 for a, p in zip(actual, predicted)]
    if not errors:
        raise ValueError("rmse requires at least one pair")
    return sqrt(sum(errors) / len(errors))


def binary_attack_advantage(labels: Iterable[int], scores: Iterable[float]) -> float:
    """Return TPR-FPR at the best observed threshold."""
    labels, scores = list(labels), list(scores)
    if len(labels) != len(scores) or not set(labels) <= {0, 1}:
        raise ValueError("aligned binary labels required")
    from math import isfinite
    from itertools import groupby
    if not all(isfinite(score) for score in scores):
        raise ValueError("finite scores required")
    pairs = sorted(zip(scores, labels), reverse=True)
    positives = sum(labels)
    negatives = len(labels) - positives
    if not positives or not negatives:
        raise ValueError("attack advantage needs both classes")
    true_positive = false_positive = 0
    best = 0.0
    for _, tied in groupby(pairs, key=lambda pair: pair[0]):
        for _, label in tied:
            if label:
                true_positive += 1
            else:
                false_positive += 1
        best = max(best, true_positive / positives - false_positive / negatives)
    return best


def membership_metrics(member_losses, nonmember_losses, seed=42):
    """Loss-threshold membership probe; descriptive, not a privacy guarantee.

    Members must be examples actually used in updates, not the whole train pool.
    IID bootstrap is illustrative; use group bootstrap for correlated records.
    """
    import numpy as np
    from sklearn.metrics import roc_auc_score, roc_curve
    positive = -np.asarray(member_losses)
    negative = -np.asarray(nonmember_losses)
    labels = np.r_[np.ones(len(positive)), np.zeros(len(negative))]
    scores = np.r_[positive, negative]
    if not len(positive) or not len(negative):
        return {"status": "insufficient_members_or_nonmembers"}
    auc = float(roc_auc_score(labels, scores))
    fpr, tpr, _ = roc_curve(labels, scores)
    rng = np.random.default_rng(seed)
    estimates = [roc_auc_score(labels, np.r_[rng.choice(positive, len(positive)),
                                            rng.choice(negative, len(negative))])
                 for _ in range(200)]
    return {"auc": auc, "auc_bootstrap_95pct": np.quantile(estimates, [.025, .975]).tolist(),
            "empirical_best_advantage": binary_attack_advantage(labels, scores),
            "tpr_at_fpr_01": float(max(tpr[fpr <= .01], default=0)),
            "nonmember_count": len(negative), "member_count": len(positive),
            "fpr_resolution": 1 / len(negative),
            "caution": "in-sample attack thresholds; not held-out attack validation; IID bootstrap"}
