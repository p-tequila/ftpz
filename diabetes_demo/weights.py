"""Persist training ciphertexts and restore them with the owner's saved key."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import tempfile

import numpy as np


def fingerprint(weights, bias):
    values = np.concatenate([np.asarray(weights).ravel(), np.asarray(bias).ravel()])
    return hashlib.sha256(values.astype("<f8").tobytes()).hexdigest()


def private_json(path, value):
    path = Path(path)
    descriptor, temporary = tempfile.mkstemp(dir=path.parent, prefix=".model-")
    try:
        with os.fdopen(descriptor, "w") as stream:
            json.dump(value, stream, indent=2, allow_nan=False)
            stream.write("\n")
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def save_bundle(destination, session, ciphertexts, weights, bias, information):
    """Never send this bundle to the worker: client-private contains the key."""
    destination = Path(destination)
    if destination.exists():
        raise FileExistsError(f"Weight bundle already exists: {destination}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=destination.parent, prefix=".weights-") as temporary:
        root = Path(temporary) / "bundle"
        root.mkdir(mode=0o700)
        for name in ("client-private", "encrypted", "server"):
            (root / name).mkdir(mode=0o700)
        private = root / "client-private"
        shutil.copyfile(session.client_directory / "client.zip", private / "client.zip")
        session.client.client.keys.save(private / "secret.keys")
        for name in ("client.zip", "secret.keys"):
            (private / name).chmod(0o600)
        shutil.copyfile(session.server_directory / "server.zip", root / "server/server.zip")
        for name, value in zip(("weights.bin", "bias.bin"), ciphertexts):
            (root / "encrypted" / name).write_bytes(value)
        private_json(private / "model_info.json", {
            **information,
            "decrypted_parameters_sha256": fingerprint(weights, bias),
            "ciphertext_sha256": {
                name: hashlib.sha256(value).hexdigest()
                for name, value in zip(("weights.bin", "bias.bin"), ciphertexts)
            },
        })
        # Load entirely new objects: verify that the persisted bundle is sufficient.
        restored_weights, restored_bias, _ = load_bundle(root)
        np.testing.assert_array_equal(restored_weights, np.asarray(weights).ravel())
        np.testing.assert_array_equal(restored_bias, np.asarray(bias).ravel())
        export_model(root, restored_weights, restored_bias, information)
        root.rename(destination)


def load_bundle(directory):
    # Preserve the native-library import order used by the pipeline on macOS.
    import concrete.ml.sklearn  # noqa: F401
    from concrete.ml.deployment import FHEModelClient

    directory = Path(directory)
    private = directory / "client-private"
    info = json.loads((private / "model_info.json").read_text())
    ciphertexts = [(directory / "encrypted" / name).read_bytes()
                   for name in ("weights.bin", "bias.bin")]
    for name, value in zip(("weights.bin", "bias.bin"), ciphertexts):
        if hashlib.sha256(value).hexdigest() != info["ciphertext_sha256"][name]:
            raise ValueError(f"Saved ciphertext changed: {name}")
    client = FHEModelClient(str(private))
    client.client.keys.load(private / "secret.keys")
    weights, bias = client.deserialize_decrypt_dequantize(*ciphertexts)
    if fingerprint(weights, bias) != info["decrypted_parameters_sha256"]:
        raise ValueError("Decrypted parameters do not match this training run")
    return weights.ravel(), bias.ravel(), info


def export_model(directory, weights, bias, info):
    output = Path(directory) / "client-private/decrypted_model.json"
    private_json(output, {
        "model": "logistic regression", "training": "FHE",
        "feature_order": info["features"],
        "weights": dict(zip(info["features"], weights.tolist())),
        "bias": float(bias[0]), "preprocessing": info["preprocessing"],
        "target": info["target"],
        "verified_against_saved_run": True,
    })
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bundle", type=Path)
    args = parser.parse_args()
    weights, bias, info = load_bundle(args.bundle)
    output = export_model(args.bundle, weights, bias, info)

    print(f"Decrypted and verified {len(weights)} weights + bias → {output.resolve()}")


if __name__ == "__main__":
    main()
