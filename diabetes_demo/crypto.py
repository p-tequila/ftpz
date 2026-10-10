"""Client-side encryption and a separate-process Concrete ML server."""

import json
import os
from pathlib import Path
import secrets
import shutil
import subprocess
import sys
import tempfile
from time import perf_counter

import numpy as np

from .server import decode, encode, validate_request


def timed(function, *args, **kwargs):
    start = perf_counter()
    result = function(*args, **kwargs)
    return result, perf_counter() - start


class ClientServer:
    """Temporary session artifacts; optional persistence is handled by weights.py."""

    def __init__(self, model, mode="inference"):
        self.model = model
        self.mode = mode

    def __enter__(self):
        from concrete.ml.deployment import FHEModelClient, FHEModelDev

        self.temporary = tempfile.TemporaryDirectory(prefix="diabetes-fhe-")
        try:
            root = Path(self.temporary.name)
            exported = root / "export"
            FHEModelDev(str(exported), self.model).save(mode=self.mode)
            self.client_directory = root / "client"
            self.server_directory = root / "server"
            self.client_directory.mkdir()
            self.server_directory.mkdir()
            shutil.move(exported / "client.zip", self.client_directory / "client.zip")
            shutil.move(exported / "server.zip", self.server_directory / "server.zip")
            self.client = FHEModelClient(str(self.client_directory))
            _, self.keygen_seconds = timed(self._new_keys, self.client)
            self.evaluation_keys = self.client.get_serialized_evaluation_keys()
        except BaseException:
            self.temporary.cleanup()
            raise
        return self

    @staticmethod
    def _new_keys(client):
        # The dataset seed must never be used for cryptographic keys.
        client.client.keygen(
            secret_seed=secrets.randbits(128),
            encryption_seed=secrets.randbits(128),
        )

    def __exit__(self, *_):
        self.temporary.cleanup()

    def run(self, **payload):
        request = {
            "operation": self.mode,
            "evaluation_keys": encode(self.evaluation_keys),
            **payload,
        }
        validate_request(request)
        try:
            response, wall_seconds = timed(
                subprocess.run,
                [sys.executable, str(Path(__file__).with_name("server.py"))],
                input=json.dumps(request), text=True, capture_output=True,
                cwd=self.server_directory, check=True, timeout=900,
            )
        except subprocess.CalledProcessError as error:
            raise RuntimeError(f"FHE worker failed: {error.stderr[-2000:]}") from error
        result = json.loads(response.stdout)
        if result["pid"] == os.getpid():
            raise AssertionError("Server did not run in a separate process")
        if result["artifact_inventory"] != ["server.zip"]:
            raise AssertionError("Unexpected server artifacts")
        result["process_wall_seconds"] = wall_seconds
        result["warnings"] = response.stderr
        return result

    def wrong_key_check(self, encrypted_outputs):
        from concrete.ml.deployment import FHEModelClient

        correct = self.client.deserialize_decrypt(*encrypted_outputs)
        other = FHEModelClient(str(self.client_directory))
        self._new_keys(other)
        try:
            wrong = other.deserialize_decrypt(*encrypted_outputs)
        except (ValueError, RuntimeError, AssertionError):
            return True
        correct = correct if isinstance(correct, tuple) else (correct,)
        wrong = wrong if isinstance(wrong, tuple) else (wrong,)
        return not (
            len(correct) == len(wrong)
            and all(np.array_equal(a, b) for a, b in zip(correct, wrong))
        )


def infer(model, X):
    """Predict on ciphertexts; return only client-decrypted results and audit facts."""
    with ClientServer(model) as session:
        encrypted, encrypt_seconds = timed(
            lambda: [session.client.quantize_encrypt_serialize(row[None, :]) for row in X]
        )
        repeated = session.client.quantize_encrypt_serialize(X[:1])
        response = session.run(inputs=[encode(value) for value in encrypted])
        outputs = [decode(value) for value in response["outputs"]]
        predictions, decrypt_seconds = timed(
            lambda: np.concatenate([
                session.client.deserialize_decrypt_dequantize(value) for value in outputs
            ])
        )
        checks = {
            "separate_server_process": True,
            "server_has_only_compiled_artifact": response["artifact_inventory"] == ["server.zip"],
            "repeat_encryption_differs": encrypted[0] != repeated,
            "unrelated_key_did_not_recover_result": session.wrong_key_check([outputs[0]]),
        }
        if not all(checks.values()):
            raise AssertionError(f"Privacy demonstration check failed: {checks}")
        return predictions, {
            "checks": checks,
            "seconds": {
                "key_generation": session.keygen_seconds,
                "encrypt_all": encrypt_seconds,
                "server_compute_all": sum(response["compute_seconds"]),
                "decrypt_all": decrypt_seconds,
                "server_process_total": response["process_wall_seconds"],
                "server_load": response["load_seconds"],
            },
            "input_ciphertext_bytes": len(encrypted[0]),
            "output_ciphertext_bytes": len(outputs[0]),
            "evaluation_key_bytes": len(session.evaluation_keys),
            "server_request_fields": response["request_fields"],
            "warnings": response["warnings"],
        }


def train(model, X, y, batches, save_weights=None, model_info=None):
    """Keep weights encrypted between SGD updates in the server process."""
    with ClientServer(model, mode="training") as session:
        def encrypt_training():
            encrypted_batches = []
            for indices in batches:
                features = X[indices].reshape(1, 8, X.shape[1])
                labels = y[indices].astype(float).reshape(1, 8, 1)
                x_enc, y_enc, _, _ = session.client.quantize_encrypt_serialize(
                    features, labels, None, None
                )
                encrypted_batches.append([encode(x_enc), encode(y_enc)])
            _, _, weights, bias = session.client.quantize_encrypt_serialize(
                None, None, np.zeros((1, X.shape[1], 1)), np.zeros((1, 1, 1))
            )
            return encrypted_batches, [encode(weights), encode(bias)]

        (encrypted_batches, state), encrypt_seconds = timed(encrypt_training)
        response = session.run(batches=encrypted_batches, state=state)
        outputs = [decode(value) for value in response["outputs"]]
        (weights, bias), decrypt_seconds = timed(
            session.client.deserialize_decrypt_dequantize, *outputs
        )
        if save_weights is not None:
            from .weights import save_bundle
            save_bundle(save_weights, session, outputs, weights, bias, model_info)
        return weights.reshape(-1), bias.reshape(-1), {
            "seconds": {
                "key_generation": session.keygen_seconds,
                "encrypt_all": encrypt_seconds,
                "server_compute_all": sum(response["compute_seconds"]),
                "decrypt_final_weights": decrypt_seconds,
                "server_process_total": response["process_wall_seconds"],
                "server_load": response["load_seconds"],
            },
            "checks": {
                "separate_server_process": True,
                "server_has_only_compiled_artifact": True,
                "weights_remain_encrypted_between_updates": True,
                "unrelated_key_did_not_recover_weights": session.wrong_key_check(outputs),
            },
            "server_request_fields": response["request_fields"],
            "warnings": response["warnings"],
        }
