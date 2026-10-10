"""Run shadow attacks independently of expensive cryptographic execution.

Targets either the matched float baseline or an explicitly supplied customer-
private model. Never write model parameters or candidate records into reports.
"""
import argparse
import json
from pathlib import Path
import numpy as np
from diabetes_demo.experiments import fitted_model, float_training
from .attacks import shadow_lira_probe
from .datasets import TRAINING_DATASETS, batches_for_sites, load, partition
from .security import digest


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", choices=TRAINING_DATASETS, required=True)
    parser.add_argument("--model", type=Path)
    parser.add_argument("--steps", type=int, default=4)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    table = load(args.dataset)
    X, _ = table.normalized()
    sites, test = partition(table, args.seed)
    batches = batches_for_sites(sites, args.steps, args.seed)
    if args.model:
        with np.load(args.model, allow_pickle=False) as stored:
            if str(stored["schema_hash"]) != digest(table.contract()):
                raise ValueError("saved model contract differs from dataset")
            model = fitted_model(stored["weights"], stored["bias"])
    else:
        model = float_training(X, table.y, batches)
    report = shadow_lira_probe(model, X, table.y, table.groups, batches, test, args.seed)
    report.update({"dataset": args.dataset, "target": "customer-supplied model" if args.model else "matched float baseline",
                   "steps": args.steps, "seed": args.seed})
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x") as stream:
        json.dump(report, stream, indent=2, allow_nan=False)
    print(args.output)


if __name__ == "__main__":
    main()
