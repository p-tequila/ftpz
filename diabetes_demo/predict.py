"""Reuse saved linear or FHE-trained logistic weights without retraining."""

import argparse
import contextlib
import io
import json
from pathlib import Path
from time import perf_counter

import numpy as np
from scipy.special import expit

from .data import FEATURES, ROOT
from .weights import load_bundle


def predict_raw(raw, weights, bias, info, model="logistic"):
    """Apply the saved scaler and coefficients, with sigmoid for logistic only."""
    raw = np.asarray(raw, dtype=float)
    if raw.shape != (len(info["features"]),) or not np.isfinite(raw).all():
        raise ValueError("Expected ten finite raw feature values")
    preprocessing = info["preprocessing"]
    scaled = raw * np.asarray(preprocessing["scale"]) + np.asarray(preprocessing["offset"])
    if preprocessing["clip"]:
        scaled = np.clip(scaled, *preprocessing["feature_range"])
    score = float(scaled @ weights + float(np.asarray(bias).ravel()[0]))
    return float(expit(score)) if model == "logistic" else score


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("models", type=Path)
    parser.add_argument("--model", choices=["linear", "logistic"], default="logistic")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--row", type=int, help="zero-based public dataset row, 0–441")
    source.add_argument("--features", type=float, nargs=10, metavar="VALUE",
                        help="raw values in order: " + ", ".join(FEATURES))
    args = parser.parse_args()
    if args.row is not None and not 0 <= args.row < 442:
        parser.error("--row must be between 0 and 441")
    raw = (np.loadtxt(ROOT / "data/diabetes/diabetes_data_raw.csv.gz")[args.row]
           if args.row is not None else np.asarray(args.features))
    logs = io.StringIO()
    start = perf_counter()
    try:
        with contextlib.redirect_stdout(logs), contextlib.redirect_stderr(logs):
            if args.model == "logistic":
                weights, bias, info = load_bundle(args.models / "logistic")
            else:
                saved = json.loads((args.models / "linear_model.json").read_text())
                weights = np.array([saved["weights"][feature] for feature in saved["feature_order"]])
                bias = np.array([saved["bias"]])
                info = {**saved, "features": saved["feature_order"]}
        restore_seconds = perf_counter() - start
        start = perf_counter()
        probability = predict_raw(raw, weights, bias, info, args.model)
        prediction_ms = (perf_counter() - start) * 1000
    except (ValueError, OSError, RuntimeError) as error:
        parser.exit(1, f"Prediction failed: {error}\n")
    if args.model == "logistic":
        print(f"FHE-trained logistic · class {int(probability > .5)} · probability {probability:.3f}")
        print(f"Target: progression score > {info['target']['threshold']:g} (demo threshold)")
    else:
        print(f"Plaintext-trained linear · predicted progression score {probability:.2f}")
    print(f"Restore model: {restore_seconds:.3f} s · preprocess + predict: {prediction_ms:.3f} ms")


if __name__ == "__main__":
    main()
