"""Fast non-FHE checks for the role boundary and polynomial raw model."""

import unittest

import numpy as np

from fhe_polynomial_training.model import initial_parameters, synthetic_data, training_step
from fhe_polynomial_training.protocol import CiphertextBundle, b_send_final_encrypted_weights, c_run_raw_inference


class PolynomialProtocolTests(unittest.TestCase):
    def test_training_step_has_expected_parameter_shapes(self):
        x_train, y_train, _, _ = synthetic_data()
        state = training_step(x_train[0], y_train[0], *initial_parameters())
        self.assertEqual([item.shape for item in state], [(2, 2), (2,), (2, 1), (1,)])
        self.assertFalse(np.array_equal(state[2], initial_parameters()[2]))

    def test_raw_inference_uses_held_out_records(self):
        _, _, x_test, _ = synthetic_data()
        prediction = c_run_raw_inference(x_test, initial_parameters())
        np.testing.assert_array_equal(prediction, np.array([[0], [1], [1]]))

    def test_b_returns_exact_ciphertext_bundle_without_decryption(self):
        encrypted = CiphertextBundle((b"w1", b"b1", b"w2", b"b2"))
        self.assertIs(b_send_final_encrypted_weights(encrypted), encrypted)


if __name__ == "__main__":
    unittest.main()
