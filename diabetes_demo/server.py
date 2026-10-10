"""Local FHE worker: compiled circuit + evaluation keys + ciphertexts only.

This process is a data-flow demonstration, not an OS security sandbox.
It never loads the dataset, the client artifact, or a secret key.
"""

import base64
import json
import os
from pathlib import Path
import sys
from time import perf_counter


def validate_request(request):
    expected = {
        "training": {"operation", "evaluation_keys", "batches", "state"},
        "inference": {"operation", "evaluation_keys", "inputs"},
    }
    operation = request.get("operation")
    if operation not in expected or set(request) != expected[operation]:
        raise ValueError("Only the defined ciphertext protocol is accepted")
    return operation


def encode(value):
    return base64.b64encode(value).decode("ascii")


def decode(value):
    return base64.b64decode(value, validate=True)


def serve(request, directory):
    # Load Torch/ML before the compiler runtime, as in the client process.
    import concrete.ml.sklearn  # noqa: F401
    from concrete.ml.deployment import FHEModelServer

    operation = validate_request(request)
    inventory = sorted(path.name for path in directory.iterdir())
    if inventory != ["server.zip"]:
        raise ValueError("Worker directory must contain only server.zip")
    start = perf_counter()
    server = FHEModelServer(str(directory))
    load_seconds = perf_counter() - start
    keys = decode(request["evaluation_keys"])
    durations = []
    if operation == "training":
        state = tuple(decode(value) for value in request["state"])
        for batch in request["batches"]:
            inputs = tuple(decode(value) for value in batch)
            start = perf_counter()
            state = server.run((*inputs, *state), keys)
            durations.append(perf_counter() - start)
        outputs = [encode(value) for value in state]
    else:
        outputs = []
        for value in request["inputs"]:
            ciphertext = decode(value)
            start = perf_counter()
            result = server.run(ciphertext, keys)
            durations.append(perf_counter() - start)
            outputs.append(encode(result))
    return {
        "outputs": outputs,
        "compute_seconds": durations,
        "load_seconds": load_seconds,
        "pid": os.getpid(),
        "artifact_inventory": inventory,
        "request_fields": sorted(request),
    }


if __name__ == "__main__":
    result = serve(json.load(sys.stdin), Path.cwd())
    json.dump(result, sys.stdout)
