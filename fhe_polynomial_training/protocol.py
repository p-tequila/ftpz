"""Role-separated serialized-ciphertext protocol.

A and C share a ``concrete.fhe.Client`` keyset under this experiment's key policy.
B is passed a ``concrete.fhe.Server`` plus evaluation-key and ciphertext byte strings only.
"""

from __future__ import annotations

from dataclasses import dataclass
import numpy as np


@dataclass(frozen=True)
class CiphertextBundle:
    """Network-safe serialized Concrete values; never contains a key or plaintext."""

    values: tuple[bytes, ...]


@dataclass(frozen=True)
class EncryptedTrainingData:
    """A's encrypted (x, y) examples in their intended SGD order."""

    examples: tuple[CiphertextBundle, ...]


@dataclass(frozen=True)
class CKeyMaterial:
    """C's client and public evaluation keys; share the client keyset only with A, never B."""

    client: object
    serialized_evaluation_keys: bytes


def _as_tuple(values):
    return values if isinstance(values, tuple) else (values,)


def _serialize(values) -> CiphertextBundle:
    return CiphertextBundle(tuple(value.serialize() for value in _as_tuple(values)))


def _deserialize(bundle: CiphertextBundle):
    from concrete import fhe

    return tuple(fhe.Value.deserialize(value) for value in bundle.values)


def create_c_key_material(client_specs_bytes: bytes) -> CKeyMaterial:
    """C creates sk_C locally and returns only its public evaluation keys for B."""
    from concrete import fhe

    client = fhe.Client(fhe.ClientSpecs.deserialize(client_specs_bytes))
    client.keys.generate()
    return CKeyMaterial(client, client.evaluation_keys.serialize())


def c_share_client_keyset_with_a(c_keys: CKeyMaterial, client_specs_bytes: bytes):
    """Let A use C's keyset under the explicitly shared-key policy.

    A can now encrypt data compatible with C's parameters and can technically decrypt
    any compatible ciphertext it obtains.  Never share this object or its serialized
    keys with B; B receives only ``serialized_evaluation_keys``.
    """
    from concrete import fhe

    a_client = fhe.Client(fhe.ClientSpecs.deserialize(client_specs_bytes))
    a_client.keys = fhe.Keys.deserialize(c_keys.client.keys.serialize())
    return a_client


def a_send_encrypted_training_data(
    a_client: object,
    x_train: np.ndarray,
    y_train: np.ndarray,
) -> EncryptedTrainingData:
    """A encrypts each integer record with the A/C shared client keyset for B."""
    if x_train.ndim != 2 or y_train.shape != (len(x_train), 1):
        raise ValueError("Expected x_train=(records, features), y_train=(records, 1)")
    return EncryptedTrainingData(tuple(
        _serialize(a_client.encrypt(x.astype(np.int64), y.astype(np.int64)))
        for x, y in zip(x_train, y_train, strict=True)
    ))


def c_send_encrypted_parameters(
    c_keys: CKeyMaterial,
    parameters: tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray],
) -> CiphertextBundle:
    """C encrypts W1, b1, W2, b2 and sends their serialized ciphertexts to B."""
    return _serialize(c_keys.client.encrypt(*parameters))


def b_train_encrypted(
    server: object,
    serialized_evaluation_keys: bytes,
    encrypted_data: EncryptedTrainingData,
    encrypted_parameters: CiphertextBundle,
) -> CiphertextBundle:
    """B evaluates one encrypted SGD step per record and never decrypts anything.

    This pure request/response boundary is suitable for a Modal worker: construct or
    cache ``server`` from ``server.zip`` in the worker, call this function, and return
    the resulting bytes to C.
    """
    from concrete import fhe

    evaluation_keys = fhe.EvaluationKeys.deserialize(serialized_evaluation_keys)
    state = _deserialize(encrypted_parameters)
    for encrypted_example in encrypted_data.examples:
        x, y = _deserialize(encrypted_example)
        state = _as_tuple(server.run(x, y, *state, evaluation_keys=evaluation_keys))
    return _serialize(state)


def b_send_final_encrypted_weights(final_state: CiphertextBundle) -> CiphertextBundle:
    """B's outbound message is ciphertext-only; this copy performs no transformation."""
    return final_state


def c_decrypt_weights(
    c_keys: CKeyMaterial,
    final_state: CiphertextBundle,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """C alone decrypts W1, b1, W2, b2 into ordinary integer arrays."""
    return tuple(np.asarray(value) for value in _as_tuple(c_keys.client.decrypt(*_deserialize(final_state))))


def c_run_raw_inference(
    raw_features: np.ndarray,
    parameters: tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray],
) -> np.ndarray:
    """C runs the released/decrypted model on ordinary, non-training raw records."""
    from .model import forward

    w1, b1, w2, b2 = parameters
    return np.vstack([forward(row.astype(np.int64), w1, b1, w2, b2) for row in raw_features])
