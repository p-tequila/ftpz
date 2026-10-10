import unittest

import numpy as np

from diabetes_demo.experiments import batch_schedule, float_training
from diabetes_demo.data import ROOT, prepare
from diabetes_demo.server import validate_request
from diabetes_demo.predict import predict_raw


class ComparisonTests(unittest.TestCase):
    def test_reused_linear_model_returns_score_without_sigmoid(self):
        from sklearn.linear_model import LinearRegression
        data = prepare()
        raw = np.loadtxt(ROOT / "data/diabetes/diabetes_data_raw.csv.gz")
        model = LinearRegression().fit(data.X_train, data.y_train)
        info = {"features": list(range(10)), "preprocessing": {
            "scale": data.scaler.scale_.tolist(), "offset": data.scaler.min_.tolist(),
            "clip": True, "feature_range": [-1, 1],
        }}
        actual = [predict_raw(row, model.coef_, model.intercept_, info, "linear")
                  for row in raw[data.test_ids]]
        np.testing.assert_allclose(actual, model.predict(data.X_test), atol=1e-10)

    def test_saved_prediction_uses_training_scaler_and_clips(self):
        data = prepare()
        raw = np.loadtxt(ROOT / "data/diabetes/diabetes_data_raw.csv.gz")
        model = float_training(data.X_train, data.labels_train, batch_schedule(353, 3, 42))
        info = {"features": list(range(10)), "preprocessing": {
            "scale": data.scaler.scale_.tolist(), "offset": data.scaler.min_.tolist(),
            "clip": True, "feature_range": [-1, 1],
        }}
        # Include out-of-training-range measurements to catch missing clipping.
        samples = np.vstack([raw[data.test_ids], data.scaler.data_max_ + 100])
        actual = [predict_raw(row, model.coef_.ravel(), model.intercept_, info) for row in samples]
        expected = model.predict_proba(data.scaler.transform(samples))[:, 1]
        np.testing.assert_allclose(actual, expected, atol=1e-12)
        with self.assertRaises(ValueError):
            predict_raw(np.full(10, np.nan), model.coef_.ravel(), model.intercept_, info)

    def test_preprocessing_has_no_test_set_leakage(self):
        data = prepare()
        raw = np.loadtxt(ROOT / "data/diabetes/diabetes_data_raw.csv.gz")
        self.assertEqual((len(data.train_ids), len(data.test_ids)), (353, 89))
        self.assertFalse(set(data.train_ids) & set(data.test_ids))
        self.assertEqual(len(set(data.train_ids) | set(data.test_ids)), 442)
        np.testing.assert_array_equal(data.scaler.data_min_, raw[data.train_ids].min(axis=0))
        np.testing.assert_array_equal(data.scaler.data_max_, raw[data.train_ids].max(axis=0))
        self.assertEqual(data.threshold, np.median(data.y_train))
        np.testing.assert_array_equal(data.labels_test, data.y_test > data.threshold)
        np.testing.assert_array_equal(data.test_ids, prepare().test_ids)

    def test_float_updates_match_concrete_training_algorithm(self):
        import torch
        from concrete.ml.sklearn._fhe_training_utils import LogisticRegressionTraining

        rng = np.random.default_rng(4)
        X = rng.uniform(-1, 1, (24, 3))
        y = rng.integers(0, 2, 24)
        batches = batch_schedule(len(X), 4, seed=42)
        model = float_training(X, y, batches)
        trainer = LogisticRegressionTraining(iterations=1, learning_rate=1)
        weights = torch.zeros((1, 3, 1), dtype=torch.float64)
        bias = torch.zeros((1, 1, 1), dtype=torch.float64)
        for batch in batches:
            weights, bias = trainer(
                torch.tensor(X[batch][None, :]),
                torch.tensor(y[batch].reshape(1, 8, 1), dtype=torch.float64),
                weights, bias,
            )
        np.testing.assert_allclose(model.coef_.ravel(), weights.numpy().ravel(), atol=1e-12)
        np.testing.assert_allclose(model.intercept_, bias.numpy().ravel(), atol=1e-12)

    def test_batch_schedule_matches_concrete_sampler(self):
        generator = np.random.default_rng(42)
        for actual in batch_schedule(353, 15, 42):
            np.testing.assert_array_equal(actual, generator.choice(353, size=8, replace=False))
            self.assertEqual(len(set(actual)), 8)

    def test_server_rejects_plaintext_or_secret_key_fields(self):
        request = {"operation": "inference", "evaluation_keys": "", "inputs": []}
        self.assertEqual(validate_request(request), "inference")
        for field in ("secret_key", "X_train", "labels", "plaintext"):
            with self.assertRaises(ValueError):
                validate_request({**request, field: "must not cross this boundary"})


if __name__ == "__main__":
    unittest.main()
