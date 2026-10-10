# nftpz platform benchmark

This is encrypted **cloud** training, not hospital-side federated training or
FedAvg. The teammate's Concrete ML deployment code is reused, with a new
signed-job worker, data adapters, query circuit, release authority and harness.

For actual measurements (including failures), see the
[executed-results summary](results/2026-10-10/README.md).

## Run

Use Python 3.12 and `requirements-platform.txt` in an existing compatible
environment. On this Mac the ignored `.runtime/python312` dependency directory
is used by `bash scripts/platform.sh`; no conda environment was replaced.
In an existing Python 3.12 environment, install `requirements-platform.txt`.
The pinned ONNX optimizer can require CMake and a C++ compiler. For Linux x86-64
CPU-only installs, additionally pin `torch==2.3.1+cpu` using the official PyTorch
CPU index, as in `deployment/bootstrap-worker.sh`.

```bash
bash scripts/platform.sh --mode baseline
bash scripts/platform.sh --mode quantized
bash scripts/platform.sh --mode execute --datasets diabetes --steps 4 --inference-rows 2
bash scripts/platform.sh --mode execute
python -m pytest tests -q
```

`baseline` runs floating-point training. `quantized` additionally runs Concrete
ML's quantized arithmetic **without encryption**. `execute` generates keys,
encrypts each site's minibatches, evaluates SGD in a separate ciphertext-only
worker process, decrypts the final weights at the customer authority, tests
encrypted inference, and executes an encrypted four-site count.

Outputs go into a new `outputs/platform/<run-id>/` directory: a machine-readable
report, readable summary and private local release ledger. Failed workloads
are recorded as failures and the command exits nonzero. It never substitutes
plaintext execution for an FHE failure. Do not commit the authority ledger.

## Implemented flow

1. Owner boundary: load a purpose-limited real-data table; normalize with fixed
   public bounds; partition by patient/subject before splitting into four sites.
   No hospital trains a model. A dataset is split into four homogeneous silos;
   unrelated HAR/HCA/GDC objects are not treated as one training schema.
2. Customer encryption gateway: encrypt each site's batch under one approved
   key, stage immutable ciphertext objects, and approve the exact request,
   program hash, dataset-contract hash, evaluation key, sites, purpose and expiry.
3. Cloud worker: verify the pinned authority signature; reject tampering,
   missing sites, plaintext fields and replay; apply Concrete ML encrypted
   logistic updates while weights remain encrypted between sites.
4. Customer authority: decrypt the final result internally; enforce principal,
   minimum-cohort and persistent release-count limits before delivering it.
5. Queries: allowlisted numerical predicates run at the owner gateway; each
   owner encrypts its count; a Concrete circuit sums four ciphertexts. The
   cloud sees no plaintext site count. Only the final approved total is released.

Set `NFTPZ_AZURE_CONFIG` to route training and count jobs to the isolated Azure
worker instead of a local subprocess. Azure stores each owner's encrypted
contribution in a distinct blob before reassembling the signed computation.
The encrypted inference probe reuses `diabetes_demo.crypto.infer` internally;
it is **not** a production authorized prediction API. Count queries are the
implemented query family; arbitrary SQL, means and histograms are not claimed.
Inference protects the patient input, **not the model coefficients**: those
coefficients are embedded in the compiled inference program. Encrypted training
keeps weights hidden from the worker during updates; deliberately releasing a
model for inference is a separate disclosure decision, not model-private FHE.

## Workloads and metrics

| Workload | Adapter and label | Primary evaluation |
|---|---|---|
| Diabetes, 442 records | BMI/BP; progression >150 | Matched float/quantized/FHE utility, membership |
| Synthea, 108 synthetic patients in this archive | Age/sex; diabetes condition | Query counts, policy attacks, membership |
| MIMIC-IV **demo**, 100 patients | Anchor age/sex; any hospital mortality | Clinical cohort semantics; small/imbalanced utility |
| HAR, 10,299 windows/30 subjects | First six features; locomotion vs stationary | Subject-disjoint holdout; fixed-range normalization |
| BIDMC, 53 records/46 distinct local IDs | Median HR/SpO2; median RR >20 | Conservative ID-group holdout; physiological features |
| HCA, 20 projects; GDC, 100 cases | Metadata only | Inventory/provenance; not clinical prediction |

Report AUROC, AUPRC, F1, accuracy, Brier score, probability differences, exact
quantized/FHE parameter parity, count error, latency by stage, serialized
request/output/evaluation-key bytes, membership AUC/CI/advantage and empirical
TPR at 1% FPR (with attainable FPR resolution). Missing-class AUROC is null.

Counts in this harness are **record counts**: patient rows for the three
tabular clinical datasets, windows for HAR and recordings for BIDMC. They are
not cross-hospital identity resolution or distinct-patient counts on repeated
sensor records. Real overlapping hospital populations require an approved
entity-resolution contract before a count can be called a unique-patient count.

The suite also runs 32 paired logistic shadow models for a Gaussian LiRA
adaptation. It uses one candidate per group and disjoint threshold-calibration
and evaluation candidates, but float surrogates and tiny samples limit the
result. Saved customer-private models can be re-tested without encryption:

```bash
python -m nftpz_platform.shadow_benchmark --dataset diabetes \
  --model outputs/platform/RUN/customer-private/MODEL.npz \
  --output outputs/platform/shadow-recheck.json
```

Four updates of eight records are deliberately an **engineering smoke test**,
not a converged model. Members in the attack are records actually used in
updates, not every record in the training pool. All comparisons reuse the same
split, initialization and batch schedule. Repeated records stay in the same
subject group. The loss attack's IID bootstrap is not valid evidence of a
subject-level confidence bound on HAR/BIDMC; larger grouped evaluations remain.

Concrete ML compiles using public synthetic feature extremes; no private
pooled calibration set is used. Defaults retain 6-bit encrypted training and
set PBS `p_error=1e-6` (override with `--p-error`). Concrete ML's library default
`0.01` was tested separately and produced parameter mismatches in several
workloads. This is an operation-level probabilistic error setting,
not a run-level privacy/security guarantee. Bounds, clipping and quantization
loss must be revalidated for a new workload.

Run one encrypted benchmark process at a time on memory-constrained machines.
Two concurrent jobs at `p_error=1e-6` caused severe swapping on the development
Mac and were explicitly stopped, not counted as completed FHE tests. Serialized
evaluation keys and base64 transport increase peak memory; production should
use bounded binary transport and measure peak RSS under its actual cgroup limit.

## Trust boundary and unimplemented guarantees

- A **customer-trusted shared-key gateway** currently sees records and holds
  the decryption key. Independently encrypted owners, multi-key FHE and
  threshold key custody are not implemented. Do not host this gateway inside
  the untrusted platform and then claim platform blindness.
- Local processes demonstrate the message boundary, not OS isolation. They
  share a user and machine. Azure runs use the distinct VM boundary and measured
  access-denial probes; see `deployment/` and the recorded cloud evidence.
- The cloud sees site identities, batch counts, dimensions and ciphertext
  lengths. ORG metadata privacy is not provided.
- Exact result release can leak individual or biological properties. Minimum
  cohorts and release caps are **not DP** and do not stop all differencing.
- Signatures protect approved requests against modification, but FHE is
  malleable and does not prove a malicious worker computed the intended
  function. Do not expose an arbitrary ciphertext-decryption oracle. Malicious
  workers, poisoned owners and compromised key authorities remain out of scope
  of the honest-but-curious computation confidentiality claim.
- No production RBAC/SSO, HSM, attestation, threshold decryption, resumable
  encrypted checkpoints, external audit anchoring or compliance certification.
- Audit hash chains detect local edits when the chain is intact; an attacker
  controlling the ledger can rewrite the entire chain without external anchoring.
- The CLI creates a fresh authority ledger for each benchmark run. Release caps
  therefore apply within that run, not across arbitrary runs or customer accounts.
  A production authority must reuse a durable, shared budget ledger. These caps
  are not epsilon accounting, and the system does not claim differential privacy.

See `adversarial-testing/implemented-methods.md` for exactly what runs versus
what is still only catalogued. Statistical attack failure does not prove FHE
security or HIPAA/GDPR compliance.
