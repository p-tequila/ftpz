"""Run the complete A -> B <- C encrypted-training protocol locally."""

from __future__ import annotations

from pathlib import Path
import tempfile

import numpy as np

from .model import initial_parameters, synthetic_data, training_step
from .protocol import (
    a_send_encrypted_training_data,
    b_send_final_encrypted_weights,
    b_train_encrypted,
    c_decrypt_weights,
    c_run_raw_inference,
    c_send_encrypted_parameters,
    create_c_key_material,
    c_share_client_keyset_with_a,
)


def compile_training_server(x_train, y_train, parameters):
    """Developer compilation.  Actual values form the safe calibration inputset."""
    from concrete import fhe

    compiler = fhe.Compiler(
        training_step,
        {
            "x": "encrypted", "y": "encrypted", "w1": "encrypted",
            "b1": "encrypted", "w2": "encrypted", "b2": "encrypted",
        },
    )
    calibration = []
    state = parameters
    for x, y in zip(x_train, y_train, strict=True):
        calibration.append((x, y, *state))
        state = training_step(x, y, *state)
    # Concrete must be compiled for a bounded input range.  The data owner would
    # normally supply approved bounds/representative values without disclosing data.
    # Output ciphertexts become the next call's parameter ciphertexts, so this circuit
    # must be compiled for self-composition; otherwise the output/input key types can
    # differ and B would need C to decrypt between SGD steps.
    circuit = compiler.compile(calibration, configuration=fhe.Configuration(composable=True))
    return circuit, state


def run_demo() -> None:
    from concrete import fhe

    x_train, y_train, x_test, y_test = synthetic_data()
    initial = initial_parameters()
    circuit, expected = compile_training_server(x_train, y_train, initial)

    with tempfile.TemporaryDirectory(prefix="polynomial-fhe-") as directory:
        archive = Path(directory) / "server.zip"
        circuit.server.save(archive)
        server = fhe.Server.load(archive)
        client_specs = server.client_specs.serialize()
        c_keys = create_c_key_material(client_specs)
        a_client = c_share_client_keyset_with_a(c_keys, client_specs)

        encrypted_data = a_send_encrypted_training_data(a_client, x_train, y_train)
        encrypted_initial = c_send_encrypted_parameters(c_keys, initial)
        encrypted_final = b_train_encrypted(
            server, c_keys.serialized_evaluation_keys, encrypted_data, encrypted_initial
        )
        final_parameters = c_decrypt_weights(
            c_keys, b_send_final_encrypted_weights(encrypted_final)
        )

    for actual, reference in zip(final_parameters, expected, strict=True):
        np.testing.assert_array_equal(actual, reference)
    raw_predictions = c_run_raw_inference(x_test, final_parameters)
    expected_predictions = c_run_raw_inference(x_test, expected)
    np.testing.assert_array_equal(raw_predictions, expected_predictions)

    print("Encrypted A -> B <- C training completed.")
    print("C decrypted final parameters:")
    for name, value in zip(("W1", "b1", "W2", "b2"), final_parameters, strict=True):
        print(f"  {name} = {value.tolist()}")
    print("C raw inference on held-out examples:")
    for x, y, prediction in zip(x_test, y_test, raw_predictions, strict=True):
        print(f"  x={x.tolist()} target={y.tolist()} prediction={prediction.tolist()}")


if __name__ == "__main__":
    run_demo()
