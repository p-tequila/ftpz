# Executed prototype results — 2026-10-10

The implemented path is customer-gateway encryption → separate cloud encrypted
training/counting → customer-authorized decryption. No hospital trains a model.
These are measured engineering smoke tests, not clinical validation or proof
that released models and aggregate answers cannot leak information.

## What ran

- **Five datasets, real FHE locally:** diabetes, Synthea, MIMIC-IV demo, HAR and
  BIDMC. At training `p_error=1e-6`, every dataset had zero parameter difference
  from matched quantized training, zero tested inference difference and zero
  encrypted-count error. See [local results](local-evidence.md) and
  [machine-readable evidence](local-evidence.json).
- **Real Azure training and counting:** diabetes was split into four owners;
  four distinct encrypted owner blobs were uploaded for each workload. The
  private VM ran four encrypted SGD updates; weights and count matched exactly.
  Training computation took **66.98 s**; upload/dispatch/response took **299.65 s**
  including that computation. Evaluation keys were **500,014,656 bytes** and
  the canonical JSON request was **666,693,943 bytes**. These are not separate
  additive latency measurements. The inference probe in this run remained local.
  See [cloud results](cloud-evidence.md) and [cloud evidence](cloud-evidence.json).
- **Independent query:** Synthea `age_at_2026 >= 65` returned **12 records**
  across four logical sites, without training a model. This earlier query used
  an inline envelope; the later cloud benchmark verified separate silo blobs.
- **Security checks:** 18 protocol/control probes, released-model loss and
  Gaussian LiRA-style membership probes, a clear-gradient reconstruction
  positive control, and an exact-count differencing control. Six deployed Azure
  access/path probes passed. See [Azure verification](azure-verification.json)
  and [method scope](../../../adversarial-testing/implemented-methods.md).
- **Final unit/regression suite:** 24 passed, 6 dependency deprecation warnings.
  The last change makes inference mismatch fail the engineering gate, with two
  regression tests. Historical reports retain their original source hashes and
  checks; none were retroactively rewritten as runs of the final commit.

The Azure worker is **deallocated**. Its runtime and ciphertext storage remain
available for subsequent tests; retained disks/storage/networking may still cost
money. The original source-data account remains closed. No raw datasets,
customer secret keys, personal Azure credentials or SAS links were uploaded to
the worker account or committed with this evidence.

## Failures and limits that matter

Concrete ML's training default `p_error=0.01` produced numerical mismatches on
four of the five measured workloads. Those failed runs are retained alongside
the stricter successful runs. Passing once at `1e-6` is not a run-level error
guarantee. Mac-native count circuit export also failed on Linux before the
portable-MLIR fix. Concurrent local encrypted jobs caused swapping and were
stopped; they are not counted as completed tests.

Four updates × eight records test the plumbing, not a converged clinical model.
The BIDMC group-held-out test has no positive labels, so its AUROC/AUPRC is null;
the tiny MIMIC-demo demographic model has AUROC 0.5. HAR is subject-disjoint but
its label/features make this a much easier task. Do not compare these as
clinical product scores. The full credentialed MIMIC and WESAD signal datasets
were not tested.

The customer-trusted gateway sees plaintext and uses one shared owner key;
independent-owner key custody and threshold/multi-key FHE are not implemented.
Counts are records, not deduplicated people across hospitals. Exact-count
differencing remains **open**; release caps/minimum cohorts are not differential
privacy. Signatures bind inputs but do not prove malicious-worker correctness.
HSM/SSO, attestation and compliance certification are not claimed.

For commands and deployment prerequisites, use the
[benchmark guide](../../README.md) and
[deployment guide](../../../deployment/README.md).
