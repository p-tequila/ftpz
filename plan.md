# Concrete ML Fork: FHE Autograd and Optimizer Platform

## Summary

Fork [Concrete ML](https://github.com/zama-ai/concrete-ml) at the signed `v1.9.0` release and extend it from its current encrypted binary logistic-regression trainer into a PyTorch-first encrypted training platform.

The existing trainer provides the architectural starting point: it compiles a manually written SGD update into one FHE circuit, repeatedly composes encrypted weights between batches, and supports `disable`, `simulate`, and `execute` modes. The fork will generate this update circuit from PyTorch forward, loss, backward, and optimizer graphs instead of requiring handwritten gradients.

The mandatory POC will use WESAD and compare:

1. Plaintext training using one data silo.
2. Plaintext training using all silos.
3. Simulated-FHE training using all silos.
4. Real-FHE training using all silos.
5. Key-holder decryption of the resulting model.
6. Ordinary plaintext PyTorch inference on held-out subjects.

The POC is research-only. Concrete ML's repository permits research/prototyping under BSD-3-Clause-Clear but states that commercial use requires a separate Zama patent license. Commercial deployment is therefore an explicit release gate, not an assumption.

## Architecture and implementation

### 1. Fork and compatibility boundary

- Pin Concrete ML, Concrete compiler, PyTorch, and TFHE-rs versions in a reproducible lockfile and container image.
- Add the new implementation under `concrete.ml.training`; preserve existing sklearn models and `SGDClassifier(fit_encrypted=True)` behavior.
- Maintain a small upstream-facing patch series:
  - generic training graph generation;
  - arbitrary encrypted parameter/state composition;
  - public-key owner encryption;
  - encrypted checkpoint and model export.
- Treat Concrete ML's quantized-module representation and compiler as the v1 backend. Do not introduce a separate framework-neutral compiler in the POC.
- Hide experimental PyTorch export/AOT APIs behind one version-pinned adapter so that PyTorch changes do not leak into the public API.

### 2. Public training API

Provide a PyTorch-style functional API:

```python
trainer = FHETrainer(
    model=model,
    loss=FHEMSELoss(),
    optimizer=FHESGD(lr=0.125, momentum=0.75),
    config=TrainingConfig(
        batch_size=10,
        parameter_bits=6,
        data_bits=6,
        steps=12,
        p_error=0.01,
    ),
)

program = trainer.compile(
    representative_inputset=calibration_data,
    parameter_ranges=declared_ranges,
)

encrypted_result = program.fit(
    encrypted_batches,
    mode="execute",  # disable | simulate | execute
)
```

Core interfaces:

- `FHETrainer`: validates and compiles a complete train step.
- `TrainingConfig`: static shapes, quantization, step count, optimizer constants, error probability, and overflow policy.
- `CompiledTrainingProgram`: exposes `fit`, cost estimates, graph diagnostics, and deployment export.
- `EncryptedTrainingResult`: encrypted parameters, optimizer state, circuit fingerprint, executed step count, and provenance.
- `decrypt_training_result(...)`: key-holder-only conversion into ordinary PyTorch parameters.
- `export_pytorch_model(...)`: writes `model.safetensors`, model specification, preprocessing metadata, and provenance.

The compiler-facing train-step contract is:

```text
(features, targets, parameters..., optimizer_state...)
    -> (updated_parameters..., updated_optimizer_state..., encrypted_metrics...)
```

Parameters and optimizer state remain explicit immutable inputs and outputs. No mutable `torch.optim` object appears inside the circuit.

### 3. FHE-compatible autograd

Implement a graph-generation pipeline:

1. Convert the PyTorch model to a functional model with explicit parameter tensors using `torch.func.functional_call`.
2. Construct a pure forward-and-loss function.
3. Use PyTorch AOTAutograd to derive the backward graph.
4. Materialize the joint forward/backward result as a normal FX graph containing tensor operations rather than runtime autograd primitives.
5. Append a functional optimizer graph.
6. Lower the complete graph through Concrete ML's existing Torch/ONNX quantization and compilation path.
7. Compile one fixed-shape update step and repeatedly feed its encrypted parameter/state outputs into the next encrypted batch, following Concrete ML's current logistic-training design.

Initial supported operation set:

- Linear/matrix multiplication.
- Addition, subtraction, and constant multiplication.
- Sum and mean reductions.
- Reshape, transpose, slicing, and concatenation needed by supported models.
- Square activation.
- Small lookup-table activations when compilation cost remains within budget.
- MSE loss with one-hot targets.
- SGD, weight decay, momentum, and Nesterov momentum.

Explicitly reject unsupported graphs before compilation, including dynamic shapes, convolutions, attention, batch normalization, dropout, Adam, data-dependent control flow, gradient clipping, and unsupported transcendental operations.

### 4. Quantization and optimizer behavior

- Quantize features, targets, parameters, gradients, and momentum buffers independently.
- Default to signed six-bit feature and parameter representations, matching the scale of Concrete ML's current encrypted trainer.
- Require declared parameter and optimizer-state ranges at compilation.
- Propagate conservative range envelopes across the configured number of composed updates.
- Run a simulation canary over all training batches before real FHE execution.
- Fail compilation or execution on predicted overflow, saturation, unsupported accumulator width, or excessive programmable-bootstrapping cost.
- Use public, compile-time optimizer constants. For the POC, learning rates are selected from power-of-two-friendly values and momentum defaults to `0.75`.
- Store all scales, zero points, ranges, and rounding rules in the training artifact so decrypted models can be reconstructed exactly.

### 5. Generic encrypted composition

Generalize the existing logistic-specific implementation:

- Replace its fixed feature/target/weight/bias mapping with arbitrary flattened parameter and optimizer-state tuples.
- Build composition mappings automatically from each output parameter/state tensor to the corresponding next-step input.
- Support encrypted checkpoint serialization after any completed batch.
- Validate the circuit fingerprint, key identifier, schema, tensor order, shapes, scales, and training-step counter before resuming.
- Keep optional metrics such as loss encrypted by default; permit decryption only through an explicit key-holder operation.

### 6. Key and deployment architecture

Reuse Concrete ML's client/server artifact concept while separating data-owner encryption from decryption.

Artifacts:

- `training-client.zip`
  - preprocessing and quantization specification;
  - tensor and batch schemas;
  - public encryption parameters;
  - public-key identifier;
  - compatible circuit fingerprint.
- `training-server.zip`
  - compiled update circuit;
  - composition mapping;
  - range contracts;
  - architecture and dependency metadata.
- `training-result.zip`
  - final encrypted parameters and optimizer state;
  - training provenance and integrity manifest;
  - no secret key.

Roles:

- **Consortium key authority:** creates the secret/client key, compact public encryption key, and server evaluation material. It alone can decrypt the trained model.
- **Data owners:** preprocess locally and encrypt their batches using only the public key.
- **Training worker:** evaluates the circuit, composes encrypted state, and stores encrypted checkpoints. It cannot decrypt data or the model.
- **Model recipient:** receives a plaintext model only after the key authority authorizes and performs final decryption.

Use [TFHE-rs compact public-key encryption](https://docs.zama.org/tfhe-rs/fhe-computation/advanced-features/public-key) and [Concrete's TFHE-rs interoperability](https://docs.zama.org/concrete/2.8/guides/tfhers) for owner-side encryption. Add a small Rust encryptor with Python bindings rather than distributing Concrete client secret keys to owners.

If generic training tensors cannot cross the Concrete/TFHE-rs interoperability boundary, the research POC may use an encryption gateway inside the key authority's trust boundary. This fallback must never place the secret key on the training worker and does not satisfy the productization security gate.

### 7. Service-ready platform

Run the POC locally through Docker Compose with:

- Control API for job creation, compilation, artifact registration, execution, status, and export.
- Training compiler worker.
- CPU FHE execution worker.
- PostgreSQL metadata store.
- S3-compatible encrypted artifact/checkpoint store.
- Key-authority CLI kept outside the worker containers.
- Owner encryption CLI.
- Prometheus-compatible runtime counters for FHE operations, batch latency, checkpoint size, memory, and failures.

Job states are:

```text
CREATED -> CALIBRATING -> COMPILED -> AWAITING_DATA
-> RUNNING -> ENCRYPTED_COMPLETE -> DECRYPTED -> EXPORTED
```

Compilation and training records must include dependency versions, source commit, circuit fingerprint, dataset manifest hashes, subject split, random seed, preprocessing version, model definition, quantization configuration, and optimizer configuration.

## WESAD full-cycle POC

Use the [WESAD wearable stress dataset](https://archive.ics.uci.edu/dataset/465/wesad), partitioned horizontally by subject.

### Data preparation

- Use wrist BVP, EDA, temperature, and accelerometer magnitude.
- Produce 60-second windows with a 30-second stride.
- Extract six local statistics per channel: mean, standard deviation, minimum, maximum, median, and interquartile range, producing 24 features.
- Standardize using statistics derived only from training subjects.
- Fix seed `20261010`.
- Assign 10 subjects to training, two to validation, and three to final testing.
- Divide the 10 training subjects into five silos of two subjects each.
- Preserve a versioned subject-level split to prevent window leakage.

To make real FHE training feasible while allowing every eligible raw window to contribute, split each subject/state sequence into early and late halves and average the window-level feature vectors in each half. This produces:

- Four binary examples per subject for baseline-versus-stress.
- Six three-class examples per subject for baseline, stress, and amusement.
- Forty all-silo binary training examples.
- Sixty all-silo three-class training examples.

Plaintext evaluation is performed on the unaggregated held-out windows.

### Stage 1: existing Concrete ML reference

Train binary baseline-versus-stress logistic regression with Concrete ML's existing encrypted `SGDClassifier` path.

Run:

- One-silo plaintext training for each of the five silos; report median and interquartile range.
- All-silo plaintext training.
- All-silo FHE simulation.
- All-silo real FHE execution.

This validates the environment, keys, data packaging, Concrete runtime, artifact flow, and reference numerical behavior before testing the fork's new autograd path.

### Stage 2: generated autograd and optimizer

Train:

```text
Linear(24, 4) -> Square -> Linear(4, 3)
```

Configuration:

- One-hot targets.
- MSE loss.
- Functional encrypted SGD with momentum `0.75`.
- Static batch size `10`.
- Two deterministic, subject-balanced epochs: 12 encrypted update steps.
- Learning rate chosen on validation data from `{1/16, 1/8, 1/4, 1/2}`.
- Shared initialization and fixed batch ordering across all comparison arms.

If compilation predicts more than eight hours for Stage 2, reduce hidden width from four to two without changing the experiment or API. If width two still exceeds the budget, record a failed feasibility gate rather than silently replacing the nonlinear model with linear regression.

Run the same four comparison arms as Stage 1:

- `subset_clear`: one silo at a time.
- `all_clear`: all five silos in plaintext.
- `all_sim`: all five silos with quantized FHE simulation.
- `all_fhe`: all five silos with real encrypted execution.

The primary product comparison is median `subset_clear` versus `all_fhe`. The other arms isolate the effects of additional data, quantization, and FHE execution.

### Decryption and inference

After training:

1. The worker returns `training-result.zip` containing only encrypted model state.
2. The key authority verifies the circuit, key, schema, and provenance.
3. The key authority decrypts parameters offline.
4. The exporter reconstructs an ordinary PyTorch module and writes:
   - `model.safetensors`;
   - `model_spec.json`;
   - `preprocessing.json`;
   - `provenance.json`;
   - evaluation report.
5. Load the exported model without Concrete ML and perform plaintext inference on all held-out windows.
6. Compile an inference circuit for the same model and compare plaintext and FHE predictions on a small encrypted test sample.

Report macro-F1, balanced accuracy, per-class recall, confusion matrix, calibration error, training wall time, compilation time, peak memory, encrypted checkpoint size, and per-update latency.

## Verification and acceptance

### Correctness tests

- Compare generated gradients against ordinary PyTorch autograd before quantization.
- Compare functional SGD and momentum updates against `torch.optim.SGD`.
- Verify parameter flattening/unflattening and composition mappings for multiple tensors.
- Test serialization and resume after every update boundary.
- Confirm deterministic output for identical seed, batch order, and configuration.
- Preserve all existing Concrete ML tests and encrypted `SGDClassifier` behavior.

### Numerical tests

For supported toy models:

- `disable` must match native PyTorch within floating-point tolerance.
- `simulate` must match the quantized reference implementation exactly or within one quantization unit.
- `execute` and `simulate` must have at least 99% Stage 1 prediction agreement.
- Stage 2 must achieve at least 98% execute/simulate label agreement and dequantized-logit MAE no greater than `0.02`, unless the compiler-reported output quantum is larger, in which case one output quantum is the limit.
- Exported PyTorch inference must reproduce decrypted-reference predictions exactly.

### Security tests

- Assert that data-owner and worker artifacts contain no secret key material.
- Demonstrate that public-key owners cannot decrypt their own or another owner's ciphertext.
- Verify ciphertext/key/circuit mismatches fail closed.
- Confirm no plaintext features, targets, gradients, parameters, or metrics are logged or persisted by the worker.
- Scan container layers, process environments, checkpoints, and service logs for key leakage.
- Document that FHE protects data during computation but does not prevent information leakage from a released plaintext model; differential privacy is outside this POC.

### POC success criteria

- Complete Stage 1 and Stage 2 real-FHE runs within 12 hours total on one 16-32-core, 128-GB RAM CPU server.
- Produce an encrypted final model that only the consortium key authority can decrypt.
- Load the decrypted model in stock PyTorch and run held-out plaintext inference.
- Show end-to-end provenance from owner datasets to exported model.
- Treat utility as a measured hypothesis:
  - target `all_fhe` macro-F1 at least `0.03` above median one-silo plaintext training;
  - target `all_fhe` within `0.05` of `all_sim`.
- Numerical, security, and artifact-flow criteria are mandatory; failure to reach the utility target is reported as an experimental result rather than concealed.

## Delivery phases and gates

1. **Reference reproduction:** reproduce Concrete ML encrypted logistic training and deployment artifacts.
2. **Autograd generation:** export forward, MSE, and backward graphs and validate them against PyTorch.
3. **Optimizer composition:** add encrypted SGD, momentum state, arbitrary parameter tuples, and checkpoints.
4. **Public-key ingestion:** integrate TFHE-rs owner encryption and confirm worker-side interoperability.
5. **Service integration:** package compiler, worker, artifact store, and control API in Docker Compose.
6. **Stage 1 benchmark:** complete logistic comparison and establish operational baselines.
7. **Stage 2 benchmark:** complete generated-autograd MLP training, decrypt, export, and infer.
8. **Productization review:** require a Zama commercial patent license, cryptographic review, dependency/security audit, production key-management design, and successful public-key interoperability before any commercial or multi-tenant release.

Defaults: PyTorch only, WESAD only for the mandatory POC, CPU execution, horizontal subject silos, one consortium key authority, static-shape models, SGD-family optimizers, no differential privacy, no Adam, no GPUs, and no client-assisted decrypt/re-encrypt during training.
