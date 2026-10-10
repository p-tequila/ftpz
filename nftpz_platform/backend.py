"""Concrete ML encrypted cloud training and Concrete encrypted cohort totals.

POC: all owners use a customer-controlled encryption gateway with one key.
This is NOT multi-key FHE, threshold decryption, or hospital-side training.
"""
import hashlib
import itertools
import json
import os
from pathlib import Path
import secrets
import subprocess
import sys
import tempfile
from time import perf_counter
import uuid
import numpy as np

from diabetes_demo.crypto import ClientServer, timed
from diabetes_demo.server import decode, encode
from .security import Authority, Denied, Ledger, canonical, digest, make_manifest
from .storage import LocalBlobStore


def invoke(request, server_directory, authority, schema_hash, authority_ledger, *, purpose, cohort=None):
    """Dispatch an exact approved request; return ciphertexts, not released plaintext."""
    program = hashlib.sha256((server_directory / "server.zip").read_bytes()).hexdigest()
    policy = {"principal": "benchmark-client", "min_cohort": 5, "max_releases": 20}
    manifest = make_manifest(request, program, schema_hash, uuid.uuid4().hex, policy, purpose)
    approval = authority.approve(manifest)
    envelope = {"request": request, "approval": approval}
    package_root = str(Path(__file__).resolve().parents[1])
    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join([package_root, env.get("PYTHONPATH", "")])
    # No Azure/user API secrets propagated. Same-user process is still not a sandbox.
    for key in list(env):
        if any(token in key.upper() for token in ("TOKEN", "SECRET", "PASSWORD", "API_KEY", "SAS")):
            env.pop(key)
    command = [sys.executable, "-m", "nftpz_platform.worker", "--directory", str(server_directory),
               "--public-key", authority.public_key, "--ledger", str(server_directory.parent / "worker.sqlite")]
    start = perf_counter()
    result = subprocess.run(command, input=canonical(envelope).decode(), text=True, capture_output=True,
                            cwd=server_directory, env=env, timeout=1800)
    if result.returncode:
        raise RuntimeError(f"ciphertext worker failed: {result.stderr[-2500:]}")
    response = json.loads(result.stdout)
    if response["pid"] == os.getpid() or response["manifest_hash"] != digest(manifest) or response["job_id"] != manifest["job_id"]:
        raise Denied("mismatched result envelope")
    response["process_seconds"] = perf_counter() - start
    response["request_bytes"] = len(canonical(envelope))
    response["output_bytes"] = sum(len(decode(v)) for v in response["outputs"])
    response["program_hash"] = program
    # Decryption caller enforces release after inspecting approved result internally.
    return response, manifest


def compile_trainer(nfeatures, seed=42, p_error=0.01):
    from concrete.ml.sklearn import SGDClassifier
    from concrete import fhe
    # Public synthetic extremes, never pooled private records for compilation.
    rng = np.random.default_rng(seed)
    calibration = np.vstack([-np.ones(nfeatures), np.ones(nfeatures), rng.uniform(-1, 1, (14, nfeatures))])
    targets = np.tile([0, 1], 8)
    trainer = SGDClassifier(fit_encrypted=True, parameters_range=(-1., 1.), max_iter=1,
                            random_state=seed, early_stopping=False, verbose=0)
    trainer.training_fhe_configuration = fhe.Configuration()
    trainer.training_p_error = p_error
    _, seconds = timed(trainer.fit, calibration, targets, fhe="disable",
                       coef_init=np.zeros((1, nfeatures)), intercept_init=np.zeros(1))
    return trainer, calibration, seconds


def quantized_training(trainer, X, y, batches):
    module = trainer.training_quantized_module
    _, _, weights, bias = module.quantize_input(None, None, np.zeros((1, X.shape[1], 1)), np.zeros((1, 1, 1)))
    for indices in batches:
        features = X[indices].reshape(1, 8, X.shape[1])
        labels = y[indices].astype(float).reshape(1, 8, 1)
        qx, qy, _, _ = module.quantize_input(features, labels, None, None)
        weights, bias = module.quantized_forward(qx, qy, weights, bias, fhe="disable")
    weights, bias = module.dequantize_output(weights, bias)
    return weights.ravel(), bias.ravel()


def encrypted_training(trainer, X, y, batches, schema_hash, authority_ledger):
    authority = Authority()
    print("  Concrete ML: exporting training circuit and generating keys", flush=True)
    with ClientServer(trainer, mode="training") as session:
        start = perf_counter()
        encrypted_batches = []
        stores = [LocalBlobStore(session.server_directory.parent / f"site-{letter}") for letter in "abcd"]
        for index, indices in enumerate(batches):
            # Encrypt at the customer gateway, one owner's batch at a time.
            x, label, _, _ = session.client.quantize_encrypt_serialize(
                X[indices].reshape(1, 8, X.shape[1]), y[indices].astype(float).reshape(1, 8, 1), None, None)
            store = stores[index % 4]
            store.write(f"batches/{index}.json", canonical([encode(x), encode(label)]))
            encrypted_batches.append(json.loads(store.read(f"batches/{index}.json")))
        _, _, weights, bias = session.client.quantize_encrypt_serialize(
            None, None, np.zeros((1, X.shape[1], 1)), np.zeros((1, 1, 1)))
        request = {"operation": "training", "evaluation_keys": encode(session.evaluation_keys),
                   "batches": encrypted_batches, "state": [encode(weights), encode(bias)],
                   "site_order": [f"site-{'abcd'[i % 4]}" for i in range(len(batches))]}
        encrypt_seconds = perf_counter() - start
        print(f"  Concrete ML: dispatching {len(batches)} encrypted updates", flush=True)
        response, manifest = invoke(request, session.server_directory, authority, schema_hash,
                                    authority_ledger, purpose="logistic-training")
        outputs = [decode(v) for v in response.pop("outputs")]
        (weights, bias), decrypt_seconds = timed(session.client.deserialize_decrypt_dequantize, *outputs)
        authority_ledger.release(manifest)
        private_model_dir = authority_ledger.path.parent / "customer-private"
        private_model_dir.mkdir(mode=0o700, exist_ok=True)
        model_path = private_model_dir / f"{manifest['job_id']}.npz"
        with os.fdopen(os.open(model_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), "wb") as handle:
            np.savez(handle, weights=weights, bias=bias, schema_hash=np.array(schema_hash))
        # A wrong-key probe is empirical; FHE is not authenticated encryption.
        wrong_key = session.wrong_key_check(outputs)
        response.update({"keygen_seconds": session.keygen_seconds, "encrypt_seconds": encrypt_seconds,
                         "decrypt_seconds": decrypt_seconds, "evaluation_key_bytes": len(session.evaluation_keys),
                         "wrong_key_recovery_failed": wrong_key, "training_backend": "Concrete ML SGDClassifier",
                         "private_weights_released_to": "customer authority only",
                         "customer_model_artifact": f"customer-private/{model_path.name}"})
        print("  Concrete ML: final model decrypted at customer authority", flush=True)
        return weights.ravel(), bias.ravel(), response


def encrypted_count(counts, schema_hash, authority_ledger, bound=16383, query_spec=None):
    """Each owner contributes one encrypted scalar, cloud computes only the sum."""
    if len(counts) != 4 or any(type(c) is not int or c < 0 or c > bound for c in counts):
        raise ValueError("four nonnegative counts within declared public capacity required")
    import concrete.ml.sklearn  # noqa: F401
    from concrete import fhe
    def add(a, b, c, d):
        return a + b + c + d
    start = perf_counter()
    compiler = fhe.Compiler(add, {key: "encrypted" for key in ("a", "b", "c", "d")})
    circuit = compiler.compile(itertools.product([0, bound], repeat=4))
    compile_seconds = perf_counter() - start
    _, keygen_seconds = timed(circuit.client.keygen, secret_seed=secrets.randbits(128), encryption_seed=secrets.randbits(128))
    inputs = []
    start = perf_counter()
    for index, count in enumerate(counts):
        values = [None] * 4
        values[index] = count
        inputs.append(circuit.encrypt(*values)[index].serialize())
    encrypt_seconds = perf_counter() - start
    repeat = circuit.encrypt(counts[0], None, None, None)[0].serialize()
    with tempfile.TemporaryDirectory(prefix="nftpz-query-") as temp:
        server_dir = Path(temp) / "cloud"
        server_dir.mkdir()
        circuit.server.save(server_dir / "server.zip")
        request = {"operation": "aggregate", "evaluation_keys": encode(circuit.client.evaluation_keys.serialize()),
                   "inputs": [encode(v) for v in inputs]}
        response, manifest = invoke(request, server_dir, Authority(), schema_hash, authority_ledger,
                                    purpose={"operation": "approved-cohort-count", "query": query_spec})
        encrypted_result = fhe.Value.deserialize(decode(response.pop("outputs")[0]))
        total, decrypt_seconds = timed(circuit.decrypt, encrypted_result)
        total = int(total)
        authority_ledger.release(manifest, cohort_size=total)
    response.update({"compile_seconds": compile_seconds, "keygen_seconds": keygen_seconds,
                     "encrypt_seconds": encrypt_seconds, "decrypt_seconds": decrypt_seconds,
                     "randomized_ciphertexts": inputs[0] != repeat,
                     "evaluation_key_bytes": len(circuit.client.evaluation_keys.serialize()),
                     "count_backend": "Concrete encrypted integer circuit", "dp": False,
                     "public_max_rows_per_site": bound})
    return total, response
