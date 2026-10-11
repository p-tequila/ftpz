"""Optional Modal-shaped adapter; intentionally has no Modal dependency.

Wrap ``modal_training_entry`` with ``@app.function(...)`` after adding Modal to the
deployment project.  B receives only the compiled server archive, evk, and ciphertext bytes.
"""

from __future__ import annotations

from pathlib import Path
import tempfile

from .protocol import CiphertextBundle, EncryptedTrainingData, b_train_encrypted


def modal_training_entry(
    server_zip: bytes,
    serialized_evaluation_keys: bytes,
    encrypted_examples: tuple[tuple[bytes, ...], ...],
    encrypted_parameters: tuple[bytes, ...],
) -> tuple[bytes, ...]:
    """Deserialize a Modal request, evaluate on B, and return ciphertext bytes only."""
    from concrete import fhe

    with tempfile.TemporaryDirectory(prefix="modal-fhe-server-") as directory:
        archive = Path(directory) / "server.zip"
        archive.write_bytes(server_zip)
        server = fhe.Server.load(archive)
        result = b_train_encrypted(
            server,
            serialized_evaluation_keys,
            EncryptedTrainingData(tuple(CiphertextBundle(example) for example in encrypted_examples)),
            CiphertextBundle(encrypted_parameters),
        )
    return result.values
