"""Ciphertext-only worker. Public trust anchor is provisioned independently.

Subprocess execution demonstrates protocol separation, NOT host isolation.
Never mount owner data or customer keys in this worker's cloud environment.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
from time import perf_counter
from .security import Denied, Ledger, digest, verify


def validate_request(request):
    fields = {
        "training": {"operation", "evaluation_keys", "batches", "state", "site_order"},
        "aggregate": {"operation", "evaluation_keys", "inputs"},
    }
    operation = request.get("operation")
    if operation not in fields or set(request) != fields[operation]:
        raise Denied("only ciphertext protocol fields accepted")
    if operation == "training":
        order = request["site_order"]
        if len(order) != len(request["batches"]) or set(order) != {"site-a", "site-b", "site-c", "site-d"}:
            raise Denied("missing contributor or schedule mismatch")
        if len(request["state"]) != 2 or any(len(batch) != 2 for batch in request["batches"]):
            raise Denied("invalid encrypted SGD state")
    elif len(request["inputs"]) != 4:
        raise Denied("all four encrypted contributions required")


def execute(envelope, directory, public_key, ledger_path):
    if set(envelope) != {"request", "approval"}:
        raise Denied("unexpected envelope fields")
    request = envelope["request"]
    validate_request(request)
    directory = Path(directory)
    if sorted(p.name for p in directory.iterdir()) != ["server.zip"]:
        raise Denied("worker artifact directory must contain only server.zip")
    program_hash = hashlib.sha256((directory / "server.zip").read_bytes()).hexdigest()
    manifest = verify(envelope["approval"], public_key, request, program_hash)
    ledger = Ledger(ledger_path)
    try:
        ledger.claim(manifest)
        import concrete.ml.sklearn  # noqa: F401; load ML before compiler on Apple Silicon
        from diabetes_demo.server import decode, encode
        from concrete.ml.deployment import FHEModelServer
        start = perf_counter()
        if request["operation"] == "training":
            server = FHEModelServer(str(directory))
            keys = decode(request["evaluation_keys"])
            state = tuple(decode(v) for v in request["state"])
            load_seconds = perf_counter() - start
            durations = []
            for index, batch in enumerate(request["batches"]):
                step_start = perf_counter()
                state = server.run((*[decode(v) for v in batch], *state), keys)
                durations.append(perf_counter() - step_start)
                ledger.event({"kind": "update", "job": manifest["job_id"], "index": index,
                              "site": request["site_order"][index],
                              "state_hash": digest([encode(v) for v in state])})
            outputs = [encode(v) for v in state]
        else:
            from concrete import fhe
            server = fhe.Server.load(directory / "server.zip")
            keys = fhe.EvaluationKeys.deserialize(decode(request["evaluation_keys"]))
            values = [fhe.Value.deserialize(decode(v)) for v in request["inputs"]]
            load_seconds = perf_counter() - start
            step_start = perf_counter()
            result = server.run(*values, evaluation_keys=keys)
            durations = [perf_counter() - step_start]
            outputs = [encode(result.serialize())]
        ledger.complete(manifest["job_id"], digest(outputs))
        return {"job_id": manifest["job_id"], "manifest_hash": digest(manifest),
                "outputs": outputs, "pid": os.getpid(), "artifact_inventory": ["server.zip"],
                "request_fields": sorted(request), "seconds": {"load": load_seconds, "updates": durations},
                "audit_chain_valid": ledger.audit_valid()}
    finally:
        ledger.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--directory", required=True)
    parser.add_argument("--public-key", required=True)
    parser.add_argument("--ledger", required=True)
    args = parser.parse_args()
    json.dump(execute(json.load(sys.stdin), args.directory, args.public_key, args.ledger), sys.stdout)


if __name__ == "__main__":
    main()
