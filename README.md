# Diabetes · final FHE demo

Open **`outputs/final/report.html`** for the measured comparison and full illustrated
client/server pipeline. All final models and keys live under `outputs/final/models/`.

| Model | Plaintext path | FHE path | Predictive quality |
| --- | --- | --- | --- |
| Linear regression | Plaintext OLS training and inference | Same plaintext-trained coefficients; encrypted inference | R², RMSE, MAE |
| Logistic regression | Plaintext SGD training and inference | Encrypted SGD training and encrypted inference | Accuracy, ROC-AUC, F1 |

**Concrete ML 1.9 has built-in encrypted logistic training, not encrypted linear training.**
The linear FHE row is explicitly an inference demonstration. Its training time is repeated
from the same shared model, not an encrypted-training measurement. Supporting encrypted
linear training would require a custom training circuit outside this built-in-model demo.

## Run

```sh
source .venv-concrete/bin/activate
python -m diabetes_demo
```

The command produces four progress messages and one report path. It refuses to overwrite
an existing final directory, protecting its saved key. For another run, choose a new
`--output-dir outputs/another-run`. The default is 15 logistic minibatch updates of 8 records,
not 15 epochs. `--steps 2` is a short functionality check. `--bits` controls inference
quantization (default 8); encrypted training uses the built-in 6-bit circuit.

Python 3.11 and `requirements.txt` are required; `.venv-concrete` already contains them.
On this Mac, native Concrete execution needs access to OS shared-memory facilities.

## Reuse the saved weights

```sh
python -m diabetes_demo.predict outputs/final/models --model logistic --row 287
python -m diabetes_demo.predict outputs/final/models --model linear --row 287
```

These predict in plaintext without training or compilation. Logistic loads its saved
ciphertexts and secret key, decrypts and dequantizes the coefficients, then predicts.
Linear loads its plaintext-trained weights. Both restore the original training scaler.
Use `--features` with ten raw values instead of `--row`, in this order:

```text
age sex bmi bp s1 s2 s3 s4 s5 s6
```

A row index is zero-based (0–441). The report uses a held-out example. The CLI prints the
prediction and restore/preprocess/predict timings. These cold single-call measurements
are different from the report's warm inference benchmark.

## Dataset and pipeline

1. Load 442 patients with ten baseline measurements. Split once into 353 training and
   89 test records. Fit min/max scaling to [-1, 1] on training records only and clip test
   inputs with the same bounds.
2. Linear regression predicts the continuous one-year progression score. Logistic predicts
   whether it exceeds the training-set median (142 for seed 42). This binary label is an
   illustrative threshold, not a medical diagnosis or a percent change in disease severity.
3. Train the linear OLS baseline. Train the logistic floating-point baseline with the same
   zero initialization, minibatches, learning rate 1 and update count as encrypted SGD.
4. On the trusted client, Concrete ML calibrates and compiles a quantized logistic training
   program. Calibration uses plaintext training data. Quantization is finite-precision
   integer representation; encryption is a separate operation.
5. Generate a secret key and evaluation keys. Encrypt features, labels, starting weights
   and bias. Send only ciphertexts, evaluation keys and `server.zip` to the worker.
6. The separate server process runs encrypted SGD updates. Intermediate weights stay
   encrypted. Evaluation keys enable computation, not secret-key decryption. Return and
   save the final encrypted weights and bias.
7. The client decrypts/dequantizes the parameters. A fresh client reloads the saved key and
   verifies recovery. Compile those coefficients for logistic inference; compile the
   plaintext-trained coefficients for linear inference.
8. For each FHE model, encrypt all 89 test records, evaluate on the worker, and decrypt the
   returned scores. Logistic applies sigmoid and a 0.5 class threshold on the client.
9. Compare timing and predictive quality. Check each FHE inference result against the same
   quantized computation without encryption. Keep that reference internal, not as another
   result row. Preserve saved models for reuse.

For inference, **both sets of model coefficients are embedded in the compiled circuit**;
they are not hidden from the server. Patient inputs remain encrypted during computation.
Only logistic training in this demo operates on encrypted weights between updates.

## Timing definitions

- Training total sums measured stages: fitting for plaintext; calibration/compilation,
  key generation, encryption, server process and final decryption for encrypted training.
  File export, persistence, saved-key checks and privacy checks are excluded. It is not the
  complete command wall time. Training computation alone appears in expanded details.
- Inference setup is conversion + compilation + key generation, shown separately.
- Inference latency is per patient: median of three single-record passes for plaintext;
  average encryption + server compute + decryption across 89 records for FHE. Setup,
  server startup, IPC and preprocessing are excluded. This is not network request latency.
- Linear R² is higher-is-better; RMSE and MAE are lower-is-better, in target-score units.
  Regression has no classification accuracy percentage. Compare metrics within each model.

This is a short capability demonstration, not a tuned or converged clinical model.
No model settings are selected using test outcomes. Quantization and approximate encrypted
training can change results. Cryptographic randomness is independent of the reproducible
split/batch seed, so subsequent FHE training results and timings can vary.

## Files and security checks

```text
outputs/final/
  report.html
  models/linear_model.json
  models/logistic/
    encrypted/weights.bin
    encrypted/bias.bin
    server/server.zip
    client-private/client.zip
    client-private/secret.keys
    client-private/model_info.json
    client-private/decrypted_model.json
    client-private/plaintext_model.json
```

The logistic JSON exports hold ten coefficients, a bias, feature order, scaler and target
metadata. To explicitly decrypt and export again:

```sh
python -m diabetes_demo.weights outputs/final/models/logistic
```

The key is saved **without password encryption**, inside an owner-only directory with key
file mode `0600`. Never send `client-private` to the server. Outputs are excluded from Git.
Hash checks catch accidental corruption or mismatches, not malicious bundle replacement.

Checks cover randomized re-encryption, failure of an unrelated key to recover a tested
result, saved-key recovery, exact quantized/FHE prediction agreement, and the worker's
request fields, process identity and artifact inventory. These validate the implementation,
not anonymity or a cryptographic security proof. Client and worker share a Mac account;
there is no OS isolation. Shapes, metadata, released models and decrypted outputs may leak
information. The client and its key are trusted.

## Code and tests

- `data.py`: dataset and preprocessing.
- `experiments.py`: model training, FHE inference and measurements.
- `crypto.py`, `server.py`: encrypted client/server execution.
- `weights.py`, `predict.py`: persistence and reusable prediction.
- `report.py`, `__main__.py`: final report and command.

```sh
python -m unittest discover -s tests -v
```

[Dataset](https://scikit-learn.org/stable/datasets/toy_dataset.html#diabetes-dataset) ·
[Encrypted training](https://docs.zama.org/concrete-ml/built-in-models/training) ·
[Linear models](https://docs.zama.org/concrete-ml/built-in-models/linear) ·
[Deployment](https://docs.zama.org/concrete-ml/guides/client_server)

## Project documentation

- [Platform plan](plan.md)
- [Product architecture](product-architecture.md)
- [Key management and model release](key-exchange.md)
- [Business case](business-case.md)
- [Dataset inventory](data.md)
- [Adversarial testing](adversarial-testing/README.md)
