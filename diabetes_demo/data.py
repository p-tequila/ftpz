"""Load the original measurements; learn preprocessing on training rows only."""

from dataclasses import dataclass
from pathlib import Path

import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler

ROOT = Path(__file__).resolve().parents[1]
FEATURES = ["age", "sex", "bmi", "bp", "s1", "s2", "s3", "s4", "s5", "s6"]


@dataclass
class Dataset:
    X_train: np.ndarray
    X_test: np.ndarray
    y_train: np.ndarray
    y_test: np.ndarray
    train_ids: np.ndarray
    test_ids: np.ndarray
    scaler: MinMaxScaler
    threshold: float
    clipped_test_values: int

    @property
    def labels_train(self):
        return (self.y_train > self.threshold).astype(int)

    @property
    def labels_test(self):
        return (self.y_test > self.threshold).astype(int)


def prepare(seed=42, directory=ROOT / "data" / "diabetes"):
    X = np.loadtxt(directory / "diabetes_data_raw.csv.gz")
    y = np.loadtxt(directory / "diabetes_target.csv.gz")
    if X.shape != (442, 10) or y.shape != (442,):
        raise ValueError("Expected 442 patients, 10 features, and 442 targets")
    if not np.isfinite(X).all() or not np.isfinite(y).all():
        raise ValueError("Dataset contains missing or non-finite values")
    train_ids, test_ids = train_test_split(np.arange(len(y)), test_size=0.2, random_state=seed)
    scaler = MinMaxScaler(feature_range=(-1, 1), clip=True).fit(X[train_ids])
    outside = (X[test_ids] < scaler.data_min_) | (X[test_ids] > scaler.data_max_)
    return Dataset(
        scaler.transform(X[train_ids]), scaler.transform(X[test_ids]),
        y[train_ids], y[test_ids], train_ids, test_ids, scaler,
        float(np.median(y[train_ids])), int(outside.sum()),
    )
