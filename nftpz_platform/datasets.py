"""Owner-side, purpose-limited real-data adapters. No raw rows in run reports."""
from dataclasses import dataclass
import csv
import gzip
import hashlib
import json
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"


@dataclass
class Table:
    name: str
    X: np.ndarray
    y: np.ndarray
    groups: np.ndarray
    features: tuple[str, ...]
    bounds: tuple[tuple[float, float], ...]
    task: str
    source_paths: tuple[Path, ...]

    def normalized(self):
        X = np.asarray(self.X, dtype=float)
        if X.ndim != 2 or X.shape[1] != len(self.bounds):
            raise ValueError("dataset violates feature contract")
        if len(X) != len(self.y) or len(X) != len(self.groups):
            raise ValueError("unaligned dataset")
        if not np.isfinite(X).all() or not set(self.y) <= {0, 1}:
            raise ValueError("finite features and binary labels required")
        low, high = np.asarray(self.bounds).T
        if np.any(low >= high):
            raise ValueError("invalid public bounds")
        clipped = int(((X < low) | (X > high)).sum())
        return np.clip(2 * (X - low) / (high - low) - 1, -1, 1), clipped

    def contract(self):
        return {"version": 1, "dataset": self.name, "features": list(self.features),
                "bounds": self.bounds, "normalization": "fixed-public-bounds-to-[-1,1]",
                "label": self.task, "unit": "patient_or_subject", "missing": "adapter-defined"}


def read_csv(path):
    opener = gzip.open if str(path).endswith(".gz") else open
    with opener(path, "rt", newline="") as handle:
        return list(csv.DictReader(handle))


def one(pattern):
    paths = sorted(DATA.glob(pattern))
    if len(paths) != 1:
        raise FileNotFoundError(f"Expected exactly one local source: {pattern}; found {len(paths)}")
    return paths[0]


def load(name):
    if name == "diabetes":
        x, y = DATA / "diabetes/diabetes_data_raw.csv.gz", DATA / "diabetes/diabetes_target.csv.gz"
        raw = np.loadtxt(x)
        # Fixed threshold for a reproducible benchmark, NOT a diagnostic cutoff.
        return Table(name, raw[:, [2, 3]], (np.loadtxt(y) > 150).astype(int),
                     np.arange(len(raw)).astype(str), ("bmi", "blood_pressure"),
                     ((10, 70), (40, 200)), "progression score > 150 (benchmark only)", (x, y))
    if name == "synthea":
        p, c = one("additional/synthea/**/patients.csv"), one("additional/synthea/**/conditions.csv")
        patients, conditions = read_csv(p), read_csv(c)
        positive = {r["PATIENT"] for r in conditions if "diabetes" in r["DESCRIPTION"].lower()}
        # No dates of birth/IDs cross the boundary; use a fixed reference year.
        X = [[2026 - int(r["BIRTHDATE"][:4]), float(r["GENDER"] == "F")] for r in patients]
        return Table(name, np.array(X), np.array([int(r["Id"] in positive) for r in patients]),
                     np.array([r["Id"] for r in patients]), ("age_at_2026", "female"),
                     ((0, 120), (0, 1)), "any recorded diabetes condition (synthetic)", (p, c))
    if name == "mimic-demo":
        p = one("pdf-datasets/mimic-iv-demo/**/hosp/patients.csv.gz")
        a = one("pdf-datasets/mimic-iv-demo/**/hosp/admissions.csv.gz")
        patients, admissions = read_csv(p), read_csv(a)
        deaths = {r["subject_id"] for r in admissions if r["hospital_expire_flag"] == "1"}
        X = [[float(r["anchor_age"]), float(r["gender"] == "F")] for r in patients]
        return Table(name, np.array(X), np.array([int(r["subject_id"] in deaths) for r in patients]),
                     np.array([r["subject_id"] for r in patients]), ("anchor_age", "female"),
                     ((0, 120), (0, 1)), "any in-hospital mortality in DEMO (not full MIMIC)", (p, a))
    if name == "har":
        p = one("pdf-datasets/uci-har/**/train/X_train.txt")
        base = p.parent.parent
        paths = tuple(base / part / f"{field}_{part}.txt"
                      for part in ("train", "test") for field in ("X", "y", "subject"))
        arrays = [np.loadtxt(path) for path in paths]
        return Table(name, np.vstack([arrays[0][:, :6], arrays[3][:, :6]]),
                     (np.r_[arrays[1], arrays[4]] <= 3).astype(int),
                     np.r_[arrays[2], arrays[5]].astype(int).astype(str),
                     tuple(f"har_feature_{i}" for i in range(6)), ((-1, 1),) * 6,
                     "locomotion activities 1-3 vs stationary 4-6; subject-disjoint split", paths)
    if name == "bidmc":
        from scipy.io import loadmat
        p = DATA / "pdf-datasets/bidmc/bidmc_data.mat"
        rows = loadmat(p, simplify_cells=True)["data"]
        def median(row, field):
            values = np.asarray(row["ref"]["params"][field]["v"], dtype=float)
            return float(np.nanmedian(values))
        # One row per record, never adjacent waveform windows split across sets.
        valid = [r for r in rows if all(np.isfinite(median(r, f)) for f in ("hr", "spo2", "rr"))]
        return Table(name, np.array([[median(r, "hr"), median(r, "spo2")] for r in valid]),
                     np.array([int(median(r, "rr") > 20) for r in valid]),
                     np.array([str(r["fix"]["id"]) for r in valid]), ("median_hr", "median_spo2"),
                     ((20, 240), (50, 100)), "record median respiratory rate > 20 (benchmark only)", (p,))
    raise ValueError(f"No clinical training adapter for {name}")


TRAINING_DATASETS = ("diabetes", "synthea", "mimic-demo", "har", "bidmc")


def partition(table, seed=42):
    """Group-held-out test set and four disjoint owner silos, balanced by groups."""
    rng = np.random.default_rng(seed)
    groups = rng.permutation(np.unique(table.groups))
    if len(groups) < 8:
        raise ValueError("at least eight independent groups required")
    ntest = max(2, int(np.ceil(len(groups) * .2)))
    test = np.flatnonzero(np.isin(table.groups, groups[:ntest]))
    sites = [np.flatnonzero(np.isin(table.groups, groups[ntest:][i::4])) for i in range(4)]
    return sites, test


def batches_for_sites(sites, steps, seed=42):
    if steps < len(sites) or any(len(s) == 0 for s in sites):
        raise ValueError("at least one update per nonempty silo required")
    rng = np.random.default_rng(seed)
    return [rng.choice(sites[i % 4], 8, replace=len(sites[i % 4]) < 8) for i in range(steps)]


def file_hash(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def inventory():
    entries = []
    for name in TRAINING_DATASETS:
        try:
            table = load(name)
            _, clipped = table.normalized()
            entries.append({"dataset": name, "status": "training_and_queries_ready",
                            "rows": len(table.y), "groups": len(np.unique(table.groups)),
                            "positive_labels": int(table.y.sum()), "features": table.features,
                            "clipped_values": clipped, "contract": table.contract(),
                            "source_sha256": {str(p.relative_to(ROOT)): file_hash(p) for p in table.source_paths}})
        except (FileNotFoundError, ValueError) as error:
            entries.append({"dataset": name, "status": "unavailable", "reason": str(error)})
    for name, rel in [("hca", "additional/hca/projects.json"), ("gdc", "additional/gdc/tcga_brca_metadata.json")]:
        path = DATA / rel
        if path.exists():
            data = json.loads(path.read_text())
            hits = data["hits"] if name == "hca" else data["data"]["hits"]
            entries.append({"dataset": name, "status": "metadata_only", "records": len(hits),
                            "source_sha256": file_hash(path), "clinical_training": False})
        else:
            entries.append({"dataset": name, "status": "unavailable"})
    entries.extend([
        {"dataset": "wesad", "status": "metadata_wrapper_only_no_signals"},
        {"dataset": "cell-line-collection", "status": "external_not_imported_or_verified",
         "reason": "Separate project; do not infer 12 independent datasets from a prior description."},
    ])
    return {"entries": entries, "training_ready": sum(e["status"] == "training_and_queries_ready" for e in entries),
            "note": "Five clinical/sensor tables plus two metadata snapshots; no full credentialed MIMIC or WESAD."}
