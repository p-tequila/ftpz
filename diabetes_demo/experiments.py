"""Linear inference and matched logistic training: real client/server FHE benchmarks."""

import hashlib
import importlib.metadata
import platform
from time import perf_counter

import numpy as np
from scipy.special import expit
from sklearn.linear_model import LogisticRegression, LinearRegression
from sklearn.metrics import accuracy_score, f1_score, roc_auc_score, r2_score, mean_absolute_error, mean_squared_error

from .crypto import infer, timed, train
from .data import FEATURES, ROOT


def batch_schedule(rows, steps, seed):
    generator = np.random.default_rng(seed)
    return [generator.choice(rows, size=8, replace=False) for _ in range(steps)]


def float_training(X, y, batches):
    """Match Concrete's minibatch logistic loss, zero start, and learning rate 1."""
    weights = np.zeros(X.shape[1])
    bias = 0.0
    for indices in batches:
        features, labels = X[indices], y[indices]
        error = expit(features @ weights + bias) - labels
        weights -= features.T @ error / len(indices)
        bias -= error.mean()
    return fitted_model(weights, np.array([bias]))


def fitted_model(weights, bias):
    """Expose explicitly trained coefficients through sklearn's prediction API."""
    model = LogisticRegression()
    model.classes_ = np.array([0, 1])
    model.coef_ = np.asarray(weights).reshape(1, -1)
    model.intercept_ = np.asarray(bias).reshape(1)
    model.n_features_in_ = model.coef_.shape[1]
    model.n_iter_ = np.array([0])  # sklearn's optimizer was not used
    return model


def scores(y, probabilities):
    return {
        "accuracy": float(accuracy_score(y, probabilities > 0.5)),
        "f1": float(f1_score(y, probabilities > 0.5, zero_division=0)),
        "auc": float(roc_auc_score(y, probabilities)),
    }


def benchmark_plain(model, X, repeats=3):
    """Median per-record latency with the same one-patient call shape as FHE."""
    predict = model.predict_proba if hasattr(model, "predict_proba") else model.predict
    predict(X[:1])
    durations = []
    for _ in range(repeats):
        start = perf_counter()
        for row in X:
            predict(row[None, :])
        durations.append((perf_counter() - start) / len(X))
    return float(np.median(durations))


def run_logistic(data, steps, bits, seed, progress, save_weights):
    # Import the ML stack before Concrete's compiler runtime. On Apple Silicon,
    # loading the compiler first can crash the subsequent Torch/LLVM conversion.
    from concrete.ml.sklearn import LogisticRegression as ConcreteLogisticRegression
    from concrete.ml.sklearn import SGDClassifier
    from concrete import fhe

    X, y = data.X_train, data.labels_train
    batches = batch_schedule(len(X), steps, seed)
    progress("2/4  Logistic regression: matched plaintext and encrypted training…")
    plaintext, float_seconds = timed(float_training, X, y, batches)

    # Internal clear run: calibrate the training circuit and isolate quantization.
    trainer = SGDClassifier(
        fit_encrypted=True, parameters_range=(-1.0, 1.0), max_iter=steps,
        random_state=seed, early_stopping=False, verbose=0,
    )
    trainer.training_fhe_configuration = fhe.Configuration()
    _, calibration_seconds = timed(
        trainer.fit, X, y, fhe="disable",
        coef_init=np.zeros((1, X.shape[1])), intercept_init=np.zeros(1),
    )
    model_info = {
        "features": FEATURES, "steps": steps, "seed": seed,
        "preprocessing": {
            "kind": "MinMaxScaler", "feature_range": [-1, 1], "clip": True,
            "scale": data.scaler.scale_.tolist(), "offset": data.scaler.min_.tolist(),
            "training_min": data.scaler.data_min_.tolist(),
            "training_max": data.scaler.data_max_.tolist(),
        },
        "target": {"definition": "progression > training median", "threshold": data.threshold},
        "versions": {name: importlib.metadata.version(name)
                     for name in ["concrete-ml", "concrete-python", "numpy"]},
    }
    weights, bias, training_audit = train(
        trainer, X, y, batches, save_weights=save_weights, model_info=model_info,
    )
    if save_weights is not None:
        from pathlib import Path
        from .weights import private_json
        private_json(Path(save_weights) / "client-private/plaintext_model.json", {
            "model": "logistic regression", "training": "plaintext",
            "feature_order": FEATURES,
            "weights": dict(zip(FEATURES, plaintext.coef_.ravel().tolist())),
            "bias": float(plaintext.intercept_[0]),
            "preprocessing": model_info["preprocessing"], "target": model_info["target"],
        })
    if not all(training_audit["checks"].values()):
        raise AssertionError("Encrypted training privacy checks failed")
    encrypted = fitted_model(weights, bias)
    seconds = training_audit["seconds"]
    fhe_training_seconds = (
        calibration_seconds + seconds["key_generation"] + seconds["encrypt_all"]
        + seconds["server_process_total"] + seconds["decrypt_final_weights"]
    )

    progress(f"3/4  Logistic regression: predicting on {len(data.y_test)} test patients: plaintext versus FHE…")
    # Only the FHE-trained model is compiled for encrypted inference.
    concrete, conversion_seconds = timed(
        ConcreteLogisticRegression.from_sklearn_model, encrypted, X, n_bits=bits,
    )
    _, compile_seconds = timed(concrete.compile, X)
    ordinary = plaintext.predict_proba(data.X_test)[:, 1]
    quantized = concrete.predict_proba(data.X_test, fhe="disable")[:, 1]
    predictions, audit = infer(concrete, data.X_test)
    protected = predictions[:, 1]
    np.testing.assert_allclose(protected, quantized, rtol=0, atol=1e-8)
    timing = audit["seconds"]
    plain_per_patient = benchmark_plain(plaintext, data.X_test)
    fhe_per_patient = (
        timing["encrypt_all"] + timing["server_compute_all"] + timing["decrypt_all"]
    ) / len(data.y_test)
    rows = [
        {
            "name": "Plaintext", "training": "Plaintext SGD", "inference": "Plaintext",
            "train_seconds": float_seconds, "train_compute_seconds": float_seconds,
            "inference_setup_seconds": 0.0,
            "inference_ms": plain_per_patient * 1000,
            "metrics": scores(data.labels_test, ordinary),
            "probabilities": ordinary.tolist(),
        },
        {
            "name": "FHE", "training": "Encrypted SGD", "inference": "Encrypted inputs",
            "train_seconds": fhe_training_seconds,
            "train_compute_seconds": seconds["server_compute_all"],
            "inference_setup_seconds": conversion_seconds + compile_seconds + timing["key_generation"],
            "inference_ms": fhe_per_patient * 1000,
            "metrics": scores(data.labels_test, protected),
            "probabilities": protected.tolist(),
        },
    ]
    return {
        "model": "Logistic regression", "kind": "logistic",
        "task": "Progression score above the training-set median",
        "threshold": data.threshold, "steps": steps,
        "saved_weights": str(save_weights) if save_weights is not None else None,
        "train_rows": len(data.y_train), "test_rows": len(data.y_test),
        "rows": rows, "training_audit": training_audit,
        "inference_audit": audit,
        "max_quantized_fhe_difference": float(np.max(np.abs(protected - quantized))),
        "training_calibration_seconds": calibration_seconds,
        "inference_conversion_seconds": conversion_seconds,
        "inference_compile_seconds": compile_seconds,
        "metadata": {
            "seed": seed, "batch_size": 8, "learning_rate": 1.0,
            "initialization": "zero weights and bias", "penalty": None,
            "early_stopping": False, "training_bits": trainer.n_bits_training,
            "training_p_error": trainer.training_p_error, "inference_bits": bits,
            "security_configuration": str(trainer.training_fhe_configuration.security_level),
            "features": FEATURES, "train_row_ids": data.train_ids.tolist(),
            "test_row_ids": data.test_ids.tolist(),
            "batch_row_ids": [data.train_ids[indices].tolist() for indices in batches],
            "test_labels": data.labels_test.tolist(),
            "clipped_test_feature_values": data.clipped_test_values,
            "preprocessing": "Train-only min/max scaling to [-1, 1]; identical clipping for both branches",
            "feature_min": data.scaler.data_min_.tolist(),
            "feature_max": data.scaler.data_max_.tolist(),
            "python": platform.python_version(), "machine": platform.machine(),
            "versions": {
                name: importlib.metadata.version(name)
                for name in ["concrete-ml", "concrete-python", "scikit-learn", "numpy"]
            },
            "data_sha256": {
                name: hashlib.sha256((ROOT / "data/diabetes" / name).read_bytes()).hexdigest()
                for name in ["diabetes_data_raw.csv.gz", "diabetes_target.csv.gz"]
            },
        },
    }


def run(data, steps, bits, seed, progress, destination):
    from pathlib import Path
    from concrete.ml.sklearn import LinearRegression as ConcreteLinearRegression
    from .weights import private_json

    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=True)
    progress("1/4  Linear regression: plaintext training, plaintext and encrypted inference…")
    linear, fit_seconds = timed(LinearRegression().fit, data.X_train, data.y_train)
    ordinary = linear.predict(data.X_test)
    concrete, conversion_seconds = timed(
        ConcreteLinearRegression.from_sklearn_model, linear, data.X_train, n_bits=bits,
    )
    _, compile_seconds = timed(concrete.compile, data.X_train)
    quantized = concrete.predict(data.X_test, fhe="disable").ravel()
    protected, audit = infer(concrete, data.X_test)
    protected = protected.ravel()
    np.testing.assert_allclose(protected, quantized, rtol=0, atol=1e-8)
    timing = audit["seconds"]
    linear_rows = []
    for name, prediction, latency in [
        ("Plaintext", ordinary, benchmark_plain(linear, data.X_test) * 1000),
        ("FHE inference", protected, 1000 * (timing["encrypt_all"] + timing["server_compute_all"]
                                           + timing["decrypt_all"]) / len(data.y_test)),
    ]:
        linear_rows.append({
            "name": name, "training": "Plaintext OLS (shared model)",
            "inference": "Plaintext" if name == "Plaintext" else "Encrypted inputs",
            "train_seconds": fit_seconds, "train_compute_seconds": fit_seconds,
            "inference_ms": latency,
            "inference_setup_seconds": 0.0 if name == "Plaintext" else
                conversion_seconds + compile_seconds + timing["key_generation"],
            "metrics": {"r2": float(r2_score(data.y_test, prediction)),
                        "rmse": float(np.sqrt(mean_squared_error(data.y_test, prediction))),
                        "mae": float(mean_absolute_error(data.y_test, prediction))},
            "predictions": prediction.tolist(),
        })
    private_json(destination / "linear_model.json", {
        "model": "linear regression", "training": "plaintext",
        "feature_order": FEATURES, "weights": dict(zip(FEATURES, linear.coef_.tolist())),
        "bias": float(linear.intercept_),
        "preprocessing": {"kind": "MinMaxScaler", "scale": data.scaler.scale_.tolist(),
                          "offset": data.scaler.min_.tolist(), "clip": True, "feature_range": [-1, 1]},
        "target": {"definition": "one-year diabetes progression score"},
    })
    logistic = run_logistic(data, steps, bits, seed, progress, destination / "logistic")
    # Keep shared reproducibility data once in the final artifact.
    metadata = logistic.pop("metadata")
    progress("4/4  Verifying both models and writing the final demo…")
    return {
        "schema_version": 4, "train_rows": len(data.y_train), "test_rows": len(data.y_test),
        "threshold": data.threshold, "steps": steps, "metadata": metadata,
        "models_directory": str(destination),
        "experiments": [
            {"model": "Linear regression", "kind": "linear", "rows": linear_rows,
             "task": "Predict the continuous one-year progression score",
             "encrypted_training_supported": False,
             "inference_audit": audit, "inference_conversion_seconds": conversion_seconds,
             "inference_compile_seconds": compile_seconds,
             "max_quantized_fhe_difference": float(np.max(np.abs(protected - quantized)))},
            logistic,
        ],
    }
