# Three-party encrypted polynomial-network experiment

This is a deliberately small, inspectable FHE training experiment.  It has a two-feature,
two-hidden-unit network with a square activation:

```text
x (2,) -> x @ W1 + b1 -> square -> h @ W2 + b2 -> prediction
```

`square(z) = z * z` is a **polynomial activation**.  It is nonlinear in the mathematical
sense, but this experiment uses no ReLU, sigmoid, softmax, comparison, max, or other
non-polynomial activation.

The training circuit is compiled as self-composable and evaluates one integer SGD update at a
time.  Its encrypted inputs are
`x`, `y`, `W1`, `b1`, `W2`, and `b2`; its encrypted outputs are the updated four parameter
tensors.  B sees only Concrete ciphertexts and C's serialized evaluation keys.

## Roles and protocol

```text
Developer: compile update circuit -> server.zip / ClientSpecs
C: creates the shared client keyset, evk, and initial encrypted parameters
A: receives the shared client keyset and encrypts training examples
B: Eval_evk(update, encrypted example, encrypted parameters) repeatedly
C: decrypts final parameters; evaluates raw test records normally
```

The reusable boundary functions are in `protocol.py`:

1. `a_send_encrypted_training_data`
2. `c_send_encrypted_parameters`
3. `b_train_encrypted`
4. `b_send_final_encrypted_weights`
5. `c_decrypt_weights`
6. `c_run_raw_inference`

All payloads that cross A/B/C boundaries are serialized bytes.  `b_train_encrypted` takes a
Concrete `Server`, serialized evaluation keys, and serialized ciphertexts only.  This is the
natural function to place behind a Modal function: load/cache `server.zip` in the Modal
container, call it with request bytes, and return its byte payload.  It has no access to a
Concrete client, secret key, or plaintext training data.

## Shared A/C key policy

This experiment implements your stated policy: C serializes and shares the same Concrete client
keyset with A.  Both can encrypt inputs for the compiled circuit and decrypt ciphertexts under
that key; B receives only the serialized evaluation keys and cannot decrypt.  The helper is
`c_share_client_keyset_with_a`.

This is a deliberate trust choice, not public-key encryption.  Technically, A can decrypt any
compatible C ciphertext it obtains, and C can decrypt A's ciphertexts.  FHE only prevents B from
reading the values.  Keep A and C's private key material away from B/Modal, use authenticated
transport, and ensure your storage/access controls prevent A and C from receiving each other's
ciphertexts when that is your application policy.

## Run

Install the root requirements in a Python 3.11 environment, then run:

```powershell
python -m fhe_polynomial_training.demo
```

The demo uses tiny synthetic integer data, not the diabetes dataset.  This keeps the encrypted
training circuit small enough to study and avoids implying that an FHE toy network is a useful
clinical model.  It trains on four records and runs raw inference on three separate test records.
It checks that FHE-decrypted parameters equal a clear integer reference update and that C's raw
inference equals the same clear polynomial model.

## Modal seam

Do not put `CKeyMaterial`, a Concrete `Client`, or `sk` in Modal.  `modal_adapter.py` contains
the shape of a Modal entry point: `server.zip` is loaded inside B's container and all requests
and responses remain bytes.  C's raw inference is a pure NumPy function and can be moved to a
separate Modal function by serializing the intentionally released plaintext parameter arrays.

This is an experiment, not a production protocol: it has no authentication, replay protection,
input-validity proofs, differential privacy, model-release policy, or protection against metadata
leakage through shapes and compilation bounds.
