# nftpz product architecture

## Executive summary

`nftpz` is an FHE-native platform for computing across sensitive datasets that
cannot be pooled in plaintext. A workload author specifies a data contract and
a computation. Each data owner maps local data into that contract, reviews the
exact workload and release policy, encrypts the resulting tensors locally, and
sends only ciphertext to a remote execution service. The result remains
encrypted until the authorized recipient decrypts it inside a customer-owned
trust boundary.

The product separates orchestration from computation:

1. **Owner data planes** connect to private data, preprocess it, and encrypt it.
2. **The SaaS control plane** coordinates identities, contracts, policies,
   approvals, jobs, metering, and audit metadata.
3. **The FHE execution plane** runs approved circuits over ciphertext in a
   public cloud or customer VPC.
4. **The customer release authority** controls keys and decrypts approved
   outputs.

The long-term product supports broad computation and general ML/AI training.
Every release must publish a capability matrix that distinguishes certified,
preview, and research workloads. The platform must never silently move an
unsupported operation into plaintext.

## Product principles

- Plaintext stays in the data owner's environment.
- The control plane does not execute sensitive computations.
- The execution plane never receives an FHE secret key.
- Every run binds exact code, schemas, contributors, keys, policies, and output
  rights into an immutable manifest.
- Every contributing organization approves the exact workload and result
  policy before its data is used.
- FHE protects computation, not the safety of a released result. Models,
  aggregates, embeddings, and repeated queries remain disclosure surfaces.
- A program that cannot meet its declared security, correctness, and cost
  constraints fails before data upload.
- The developer experience should feel like constrained Python and PyTorch,
  while exposing enough information to make FHE cost and precision predictable.

## System context

```mermaid
flowchart LR
    WA[Workload author] -->|contract + program| CP[Control plane]
    CP -->|immutable review bundle| DP1[Owner data plane A]
    CP -->|immutable review bundle| DP2[Owner data plane B]
    CP -->|immutable review bundle| DPN[Owner data plane N]

    KA[Customer release authority] -->|public + evaluation keys| CP
    CP -->|approved key material| DP1
    CP -->|approved key material| DP2
    CP -->|approved key material| DPN

    DP1 -->|signed ciphertext batches| ES[(Encrypted object store)]
    DP2 -->|signed ciphertext batches| ES
    DPN -->|signed ciphertext batches| ES

    CP -->|signed execution plan| EP[FHE execution plane]
    ES --> EP
    EP -->|encrypted checkpoints + result| ES
    CP -->|result digest + approvals| KA
    ES -->|encrypted result| KA
    KA -->|approved plaintext artifact| RR[Result recipient]
```

Ciphertext objects move directly between owner agents, execution storage, and
workers. The control plane receives object references, hashes, sizes, statuses,
and policy metadata, not payload bytes.

## Roles and trust boundaries

| Role | Responsibilities | Must not access |
|---|---|---|
| Workload author | Defines the input contract, computation, expected output, and acceptance tests | Owner source systems and unapproved outputs |
| Data steward | Maps local sources, reviews requested fields, validates rights and consent, approves participation | Other owners' records or keys |
| Collaboration administrator | Invites organizations, configures roles, freezes run membership, and manages budgets | Plaintext owner data |
| Security/privacy reviewer | Reviews code digest, data-use purpose, output policy, security profile, and retention | Data outside the approved local review path |
| Result recipient | Receives only the output named in the release policy | Raw contributor data and intermediate state |
| Customer release authority | Generates and protects secret keys and performs approved decryption | Unapproved outputs |
| Platform operator | Operates control and execution services | Secret keys, plaintext inputs, intermediates, and results |
| Auditor | Reads immutable manifests, approvals, receipts, and security evidence | Plaintext unless separately authorized |

The execution service is assumed to be honest-but-curious for confidentiality
and potentially faulty or malicious for availability and integrity. FHE hides
plaintext from it, but FHE alone does not prove that it ran the intended program
or included every input. Signed manifests, deterministic simulation, input
commitments, restricted workers, and optional redundant execution address this
operationally. Verifiable execution is a later cryptographic workstream.

## Planes and services

### Owner data plane

The data-plane agent is installed on a VM, bare-metal host, or Kubernetes
cluster controlled by each contributing organization. It uses outbound-only
mTLS to communicate with the control plane and encrypted storage.

Core components:

- **Connector runtime:** Parquet, CSV, S3-compatible storage, PostgreSQL, and
  initial FHIR/tabular healthcare connectors. DICOM, omics stores, warehouses,
  and additional enterprise systems are plugins.
- **Local transform runner:** executes owner-authored preprocessing in a
  rootless, resource-limited container with an explicit source allowlist and
  no outbound network by default.
- **Contract validator:** enforces types, shapes, units, bounds, missingness,
  consent, purpose, and policy tags before encryption.
- **FHE client:** quantizes, batches, pads, encrypts, serializes, and signs data
  using collaboration-scoped public parameters.
- **Upload manager:** performs resumable multipart uploads with checksums and
  idempotency tokens.
- **Local evidence store:** records source versions, transform digest, rejected
  rows, validation summaries, and upload receipts without exposing values to
  the vendor.

The agent never downloads and runs mutable code from the control plane. It runs
only a content-addressed transform bundle that the owner has installed or
explicitly approved.

### SaaS control plane

The managed control plane contains:

- **Identity and organization service:** OIDC/SAML, SCIM, RBAC, service
  identities, and organization boundaries.
- **Collaboration service:** membership, purpose, contracts, regional settings,
  budgets, and lifecycle.
- **Schema and metadata catalog:** dataset contracts, fields, units,
  modalities, consent and use restrictions, quality summaries, and lineage.
- **Workload registry:** immutable program bundles, compiler reports,
  signatures, capability tier, and version history.
- **Policy and approval service:** contributor approvals, release quorum,
  minimum-site requirements, output restrictions, expiry, and revocation.
- **Compiler coordinator:** schedules managed compilation or verifies locally
  compiled artifacts.
- **Job orchestrator:** freezes manifests, issues scoped credentials, schedules
  workers, tracks checkpoints, and handles retries.
- **Audit ledger:** append-only signed events suitable for customer export to a
  SIEM or archive.
- **Metering and billing:** collaboration subscription, data-access rights,
  compilation, worker use, storage, and transfer.

Control-plane databases hold metadata only. Sensitive metadata is minimized,
pseudonymous identifiers are preferred, and customer-visible audit events must
show what the platform operator could observe.

### FHE execution plane

Execution planes are regional and can run in the vendor account, a dedicated
customer VPC, or a sovereign/self-hosted environment. Each collaboration gets
isolated storage prefixes, queues, cryptographic contexts, caches, workload
identities, and network policy.

Core components:

- **Worker scheduler:** selects CPU, GPU, memory, and locality profiles from the
  signed execution plan.
- **Circuit cache:** content-addressed compiled artifacts keyed by program,
  backend, security profile, and hardware target.
- **Evaluation-key cache:** encrypted-at-rest, collaboration-scoped, revocable,
  and never reused across incompatible contexts.
- **Execution workers:** default-deny egress, read-only program image, ephemeral
  scratch space, and no interactive shell in production.
- **Checkpoint service:** stores only encrypted parameters, optimizer state,
  partial aggregates, and signed step metadata.
- **Result packager:** emits the encrypted result, provenance, worker receipts,
  cost data, and all hashes required for release verification.

Jobs are batch-oriented. A retry resumes from the last committed encrypted
checkpoint and cannot apply a batch twice. A worker must reject mismatched
program, key, schema, batch, or context identifiers.

### Customer release authority

The release authority runs in the result owner's environment and supports an
HSM/KMS-backed online service or an offline key host.

- Generate one versioned key context per collaboration or per job, according
  to policy.
- Keep the secret key non-exportable where the selected cryptographic client
  permits it.
- Publish compact public encryption material and evaluation/server keys.
- Verify approvals, program digest, input Merkle root, execution receipt,
  result digest, recipient, and expiry before decryption.
- Decrypt and post-process without returning plaintext through vendor services.
- Record a signed release receipt without storing the result in the control
  plane.

The initial approval quorum is enforced by policy and audit. It does not stop a
malicious administrator who controls the sole secret key and bypasses the
release service. Workloads requiring cryptographic protection from that party
must wait for threshold FHE or use an independently controlled key custodian.

## Versioned artifacts and contracts

All public schemas use versioned JSON Schema/Pydantic models and stable content
digests.

### `DatasetContract`

Defines logical fields, encoded dtypes, tensor shapes, units, allowed ranges,
privacy tags, permitted missingness, batching, padding, and contribution
minimums. Compilation uses synthetic or public representative data plus these
declared bounds. Private calibration samples do not leave an owner.

### `TransformBundle`

Contains an owner-specific preprocessing image digest, entry point, connector
permissions, output contract, and reproducibility metadata. The source may
remain private to the owner; the collaboration records the executable digest.

### `ProgramBundle`

Contains the typed FHE graph, source digest, compiler/backend versions,
operator report, clear and simulated tests, numerical-error report, and output
schema. Proprietary workload authors may compile locally and upload only this
signed artifact.

### `ExecutionPlan`

Binds the program and data contract to a backend, security profile, hardware
target, static dimensions, parameter ranges, key specification, estimated
runtime, memory, ciphertext size, and cost envelope.

### `ReleasePolicy`

Names permitted recipients, required approvers, minimum contributors, output
types, result-size limits, query/release budget, retention, expiry, and any
suppression, rounding, or differential-privacy requirement.

### `RunManifest` and `ResultEnvelope`

The run manifest freezes exact contributors, batch commitments, artifact
digests, key ID, compiler parameters, and dependency versions. The result
envelope contains encrypted outputs, checkpoints or final model state,
provenance, measured cost, and signed execution receipts.

Changing code, schema, contributors, outputs, keys, parameters, or policy
creates a new version and invalidates prior approvals.

## FHE compiler and runtime

### Typed intermediate representation

Programs lower into an FHE IR with:

- static tensor shapes and bounded loops;
- explicit signedness, bit width, scale, and numeric range;
- encrypted, public, and locally held values;
- privacy and provenance labels;
- deterministic operations without network, filesystem, reflection, or dynamic
  code loading;
- placement labels for local preprocessing, remote FHE, and local
  post-processing.

The compiler must return actionable source-linked diagnostics for unsupported
operators, unsafe ranges, overflow, excessive programmable bootstrapping,
incompatible hardware, and estimated cost beyond the author's budget.

### Backend interface

The internal `FHEBackend` contract supports:

```text
analyze(graph, contract, target) -> CompatibilityReport
simulate(graph, fixtures) -> SimulationResult
estimate(graph, contract, target) -> CostEstimate
compile(graph, contract, target) -> ProgramBundle
client_spec(program) -> ClientSpecification
encrypt(client_spec, batch) -> CiphertextBatch
execute(program, evaluation_keys, ciphertexts) -> CiphertextResult
decrypt(client_spec, secret_key, result) -> PlainResult
```

Concrete and Concrete ML are the first backend for exact integer arithmetic,
lookup tables, quantized ML, small encrypted training, and hybrid model
partitioning. The commercial product must secure the required Zama patent
license. OpenFHE is evaluated later for CKKS approximate arithmetic, alternate
packing, and threshold BFV/BGV/CKKS.

### Workload capability tiers

**Certified:**

- bounded integer and quantized arithmetic;
- sum, count, mean, comparison, filter masks, histograms, and fixed-shape
  tabular computations;
- linear and logistic regression training and inference;
- small fixed-shape quantized MLPs with supported activations, losses, and
  SGD-family optimizers;
- multi-owner batch concatenation under one collaboration key.

**Preview:**

- restricted NumPy-style programs;
- generated PyTorch autograd and functional optimizers;
- GPU and multi-GPU execution;
- hybrid neural-network inference and LoRA fine-tuning;
- output suppression, minimum-cohort rules, and optional DP post-processing.

**Research:**

- full encrypted training of large neural networks;
- shared multi-owner LoRA state without exposing adapters to sites;
- arbitrary optimizer graphs and transformer pretraining;
- private cross-owner entity resolution;
- cryptographic threshold release and verifiable FHE execution.

Arbitrary Python, arbitrary containers, unbounded data-dependent control flow,
and full frontier-model pretraining are not launch capabilities.

## Hybrid ML and AI execution

The graph partitioner uses three placements:

- `LOCAL_CLEAR`: owner-side preprocessing, unsupported layers, loss, or local
  adapter updates.
- `REMOTE_FHE`: encrypted linear algebra and supported nonlinear kernels.
- `LOCAL_POSTPROCESS`: approved dequantization, formatting, and export.

Current Concrete ML hybrid approaches can outsource expensive linear layers
while keeping nonlinear layers or LoRA state client-side. This makes large
model adaptation a viable product direction, but it is interactive and does
not by itself create one pooled multi-owner model. Hybrid LoRA is therefore
certified first for a single owner or independent per-owner fine-tunes.
Multi-owner shared adaptation remains research until shared state and optimizer
updates stay encrypted or use a separately reviewed aggregation protocol.

## Two-sided developer experience

### Workload author

```python
from nftpz import DatasetContract, FHETrainer, fhe


class PatientFeatures(DatasetContract):
    x: Tensor["batch", 64, "int8"]
    y: Tensor["batch", 1, "int8"]


@fhe.program(inputs=[PatientFeatures], output="encrypted_model")
def train(batch):
    return FHETrainer(
        model=RiskModel(),
        loss="mse",
        optimizer={"name": "sgd", "lr": 0.125},
    ).fit(batch.x, batch.y)
```

The SDK produces clear tests, quantized simulation, unsupported-operation
diagnostics, overflow and precision analysis, CPU/GPU compatibility, key and
ciphertext sizes, runtime and cost estimates, and an immutable review bundle.

### Data owner

```python
from nftpz import fhe


@fhe.local_transform(output=PatientFeatures)
def prepare(source: FHIRConnection) -> PatientFeatures:
    ...
```

Before approval, the owner sees requested fields, local source, transformed
row count, rejected or clipped values, bounds, batch sizes, workload digest,
human-readable computation summary, participants, result recipient, output
rights, retention, estimated upload, and release policy.

### CLI

```text
nftpz init
nftpz doctor
nftpz test --clear
nftpz simulate
nftpz estimate
nftpz publish
nftpz collaboration invite
nftpz agent install
nftpz dataset validate
nftpz dataset approve
nftpz run start
nftpz run status
nftpz result approve
nftpz result decrypt
```

The portal exposes the same lifecycle for collaboration administrators, data
stewards, reviewers, result recipients, and auditors.

## End-to-end workflow

1. The workload author publishes a dataset contract, computation, tests, and
   release policy.
2. Clear execution, FHE simulation, compatibility analysis, and cost estimation
   must pass.
3. Compilation emits an immutable program and execution plan.
4. Each data owner reviews and approves the exact digest and implements its
   local mapping.
5. The release authority generates the collaboration keys.
6. Agents validate, preprocess, encrypt, sign, and upload data.
7. The control plane freezes a run manifest after required contributions arrive.
8. Workers execute and checkpoint encrypted state.
9. The result packager publishes an encrypted result and signed receipt.
10. Required organizations approve the exact result and run digests.
11. The customer release authority decrypts and exports the approved artifact.
12. Retention removes ciphertexts, evaluation keys, and temporary artifacts
    while preserving permitted evidence.

Contributor changes, a dropped required site, range violations, expired
approval, key rotation, or artifact changes require a new manifest and renewed
approval. There is no automatic plaintext fallback.

## Security and privacy model

The core claim is that an approved remote workload can execute without the
cloud operator or executor learning plaintext inputs, intermediate values, or
encrypted outputs.

FHE does not address every risk:

- Poisoned or fraudulent owner data remains possible.
- A decrypted model or aggregate may leak membership, attributes, institutions,
  or rare cohorts.
- Contributor identity, timing, payload size, and access patterns may leak.
- A malicious worker can withhold or corrupt a result.
- A compromised owner endpoint can leak plaintext before encryption.
- A sole key custodian can bypass a policy quorum unless threshold cryptography
  or an independent custodian is used.

Required controls include signed artifacts, owner-side digest enforcement,
minimum-contributor policies, fixed payload classes where practical, release
ledgers, repeated-query budgets, optional DP, key rotation and revocation,
malware and supply-chain controls, and the repository's adversarial benchmark.

For healthcare, encryption does not remove contractual or regulatory duties.
[HHS guidance](https://www.hhs.gov/hipaa/for-professionals/special-topics/health-information-technology/cloud-computing/index.html)
states that a cloud provider maintaining encrypted ePHI is still a business
associate even without the key. For defense workloads, the initial target is
unclassified/CUI-like data with controls mapped to
[NIST SP 800-171 Rev. 3](https://csrc.nist.gov/pubs/sp/800/171/r3/final).
The product must not claim HIPAA, CMMC, FedRAMP, classified, or similar status
until the complete deployment and operating organization have been assessed.

## Reliability, observability, and cost

- All write operations use idempotency keys.
- Encrypted checkpoints are committed atomically with the applied batch index.
- Jobs are resumable across worker loss and cannot double-apply work.
- Control-plane APIs target conventional SaaS availability; FHE job completion
  SLOs are workload-specific and derived from the compiler estimate.
- Metrics include queue time, compilation time, FHE operation counts, worker
  time, memory, key-cache use, ciphertext bytes, checkpoint size, and failures.
- Logs contain identifiers and reason codes, never values or secret material.
- The estimator initially targets measured cost and duration within 30% and is
  tightened as production benchmark data grows.
- Compile artifacts are reused only when every fingerprinted input is equal.
- GPU execution is selected only when compatible parameters exist and measured
  cost is better than CPU execution.

## Deployment profiles

### Managed hybrid SaaS

Vendor control plane, owner-hosted data agents, and vendor or customer-VPC FHE
workers. This is the default commercial profile.

### Dedicated customer VPC

Managed control plane with single-customer execution, storage, networking, and
keys in the customer's cloud account. Intended for regulated enterprises.

### Sovereign/self-hosted

All planes run in customer-controlled infrastructure with offline artifact
promotion and optional disconnected operation. This is required before serious
defense adoption and carries separate licensing and support.

## Product roadmap and exit gates

1. **Productize the regression POC:** expose the existing Concrete ML flow
   through versioned artifacts, one data agent, execution worker, and offline
   result decryption.
2. **Multi-owner pilot:** three agents contribute under one collaboration key;
   complete approval, ciphertext upload, encrypted execution, release, and
   audit flow.
3. **General computation:** introduce the typed IR, core encrypted analytics,
   compatibility reports, and benchmark-backed cost estimator.
4. **ML expansion:** generated autograd, functional optimizers, encrypted model
   state, small MLPs, checkpoints, and ordinary PyTorch export.
5. **GPU and hybrid AI:** CUDA worker profiles, partitioned model execution, and
   single-owner LoRA workflows.
6. **Enterprise hardening:** SSO/SCIM, audit export, regional execution,
   retention, backup, disaster recovery, incident response, and independent
   security reviews.
7. **Crypto agility:** OpenFHE experiments, threshold release, approximate
   arithmetic, and verifiable-execution research.

## Product acceptance tests

- Three organizations contribute differently sized datasets to one encrypted
  job without plaintext or a secret key reaching vendor systems.
- An agent rejects a control-plane attempt to substitute unapproved code.
- Wrong-key, wrong-schema, expired, duplicate, corrupted, and replayed batches
  fail closed.
- Worker interruption resumes without applying a batch twice.
- Clear, simulated, CPU-FHE, and GPU-FHE results meet declared numerical
  tolerances.
- Result decryption fails without all required approvals and succeeds only for
  the named recipient and exact result digest.
- Logs, metrics, support bundles, images, and storage metadata contain no
  plaintext values or secret keys.
- Membership, inversion, site-attribution, differencing, repeated-release, and
  poisoning tests integrate with `adversarial-testing/`.
- A developer can run a sample in less than 30 minutes, and a prepared data
  owner can validate and encrypt a first batch in less than two hours,
  excluding organizational review.

## Product boundaries

- The execution engine is FHE; local clear work is restricted to owner-approved
  preprocessing, hybrid client operations, and post-processing.
- Private joins and entity resolution are not assumed. Initial multi-owner
  training concatenates independently prepared records under a common schema.
- Differential privacy is optional output protection, not a replacement for
  FHE or a default claim.
- Threshold decryption is not present in the initial Concrete backend.
- Commercial release is blocked on patent licensing, independent cryptographic
  review, production key management, and successful public-key multi-owner
  interoperability.
