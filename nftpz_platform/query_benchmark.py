"""Independent governed encrypted count query, without training a model."""
import argparse
import json
from pathlib import Path
import numpy as np
from .backend import encrypted_count
from .datasets import TRAINING_DATASETS, load
from .queries import Query, owner_count
from .security import Denied, Ledger, digest


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", required=True, choices=TRAINING_DATASETS)
    parser.add_argument("--field", required=True)
    parser.add_argument("--comparison", choices=["ge", "le", "eq"], default="ge")
    parser.add_argument("--value", type=float, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--ledger", type=Path, default=Path("outputs/authority/query-ledger.sqlite"))
    args = parser.parse_args()
    if args.output.exists():
        parser.error("output already exists; use a new result filename")
    table = load(args.dataset)
    table.normalized()  # enforce data contract before computing an approved predicate
    query = Query(args.field, args.comparison, args.value)
    query.validate(table.features)
    groups = np.unique(table.groups)
    sites = [np.flatnonzero(np.isin(table.groups, groups[i::4])) for i in range(4)]
    counts = [owner_count(table, site, query) for site in sites]
    report = {"dataset": args.dataset, "query": query.to_dict(), "unit": "records",
              "sites": 4, "note": "Record counts, not global patient deduplication; exact results are not DP."}
    ledger = Ledger(args.ledger)
    try:
        total, audit = encrypted_count(counts, digest(table.contract()), ledger, query_spec=query.to_dict())
        report.update({"status": "released", "total": total, "oracle_absolute_error": abs(total-sum(counts)),
                       "audit": audit})
    except Denied as error:
        report.update({"status": "suppressed", "reason": str(error)})
    finally:
        ledger.close()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x") as handle:
        json.dump(report, handle, indent=2, allow_nan=False)
    print(args.output)
    if report["status"] != "released":
        raise SystemExit(2)
    if report["oracle_absolute_error"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
