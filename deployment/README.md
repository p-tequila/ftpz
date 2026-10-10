# Isolated Azure encrypted worker

This directory contains the deployed-worker template, installer, code updater
and measured isolation probes. Aggregate-only benchmark evidence is recorded
under `benchmarks/results/2026-10-10/`; do not confuse template validation with
an actually executed cloud workload.

The existing owner-data account was checked read-only: public access is disabled,
anonymous blob access is disabled, and there is no private endpoint. The existing
SAS links remain revoked. Do not re-enable public access to make the demo work.
MIMIC/BIDMC containers previously removed at the user's request are not recreated.

`isolated-worker.bicep` creates **new** resources in a dedicated nftpz-only
resource group: ciphertext storage, private endpoint/DNS, an unpeered VNet,
private-only CPU VM, NSG, and a dedicated managed identity. It does not read or
modify VCC resources, the existing owner-data account, subscription-level
assignments, or teammates' identities.

The worker identity gets Blob Data Reader on `ciphertext-jobs` and Blob Data
Contributor on `ciphertext-results` only. It has no raw-data role, no customer
key, no account keys, no SAS, and no resource-management role. Contributor on
results includes delete; tighten to a custom write-only role for production.

## Running the benchmark against Azure

`nftpz_platform.azure_transport` stages four separate encrypted owner objects
(`site-a.json` through `site-d.json`), the public program and signed execution
envelope. The worker hydrates those objects, verifies the original request hash
and signature, and only then computes. Missing/substituted/tampered silo objects
fail validation. Training is performed on the VM, not at the data owners.

The customer gateway uses its own local Azure CLI login. The VM receives no
personal credentials and uses only its container-scoped managed identity.
Use a local, uncommitted configuration with exactly these fields:

```json
{
  "account": "YOUR_CIPHERTEXT_ACCOUNT",
  "subscription": "YOUR_PROJECT_SUBSCRIPTION_UUID",
  "resource_group": "YOUR_NFTPZ_RESOURCE_GROUP",
  "vm": "YOUR_NFTPZ_WORKER_VM",
  "identity_client_id": "YOUR_WORKER_IDENTITY_CLIENT_UUID"
}
```

```bash
export NFTPZ_AZURE_CONFIG=/absolute/path/to/project-only-config.json
bash scripts/platform.sh --mode execute --datasets diabetes --p-error 0.000001
# Independent cohort query; no model training is required:
python -m nftpz_platform.query_benchmark --dataset synthea \
  --field age_at_2026 --comparison ge --value 65 \
  --output outputs/azure/cohort-query.json
```

The default query ledger is reused across separate query CLI calls. Training
benchmark runs intentionally get fresh authority ledgers. Neither is DP.
The dispatcher uses Azure Run Command for this prototype; its management-plane
latency is reported separately from actual FHE computation. A production service
needs a persistent worker/queue and a real identity-backed key authority.

## Building and dispatching the worker

Build the image in a trusted build environment using `deployment/Dockerfile.worker`.
The Docker context explicitly excludes all data, outputs, credentials and Git
history. Run as UID 10001 with a read-only root filesystem, a bounded tmpfs for
temporary ciphertexts and a durable writable ledger volume. Supply the pinned
customer approval public key independently of the job.

```bash
docker build --platform linux/amd64 -f deployment/Dockerfile.worker -t nftpz-worker:prototype .
# Within the private network, with the dedicated managed identity available:
python -m nftpz_platform.cloud_worker \
  --account YOUR_CIPHERTEXT_ACCOUNT --job APPROVED_JOB_ID \
  --public-key PINNED_ED25519_PUBLIC_KEY_HEX \
  --identity-client-id WORKER_IDENTITY_CLIENT_ID \
  --ledger /var/lib/nftpz/worker.sqlite
```

Owner/key-authority tooling stages `<job>/envelope.json`, `<job>/server.zip`
and four `<job>/site-*.json` objects in `ciphertext-jobs`; outputs appear at
`<job>/result.json`. Only ciphertexts,
public compiled artifacts, evaluation keys and approved metadata belong here.
The trusted gateway needs its own identity and private network path; this
template deliberately does not grant the worker access to owner containers.

## Deployment gates still required

- Validate the template and inspect an Azure what-if under the chosen dedicated
  resource group before deployment. The template creates billable resources.
- The default worker NSG allows the blob private endpoint and denies other
  outbound traffic; Azure platform DNS remains available. Optional
  `bootstrapInternetAccess=true` permits temporary HTTPS package installation.
  Set its rule back to Deny before running jobs, and run `verify-worker.py`.
  The installer uses Ubuntu's official HTTPS mirror and CMake for ONNX optimizer.
- Storage public ingress is disabled by default. If an external customer gateway
  needs it, `gatewayIpAddress` permits only that exact IP while retaining
  deny-by-default networking and disabled shared-key authentication. Verify the
  actual Azure-path egress IP: generic IP-discovery endpoints can disagree.
  Do not enable unrestricted access or change the existing owner-data account.
- A customer-owned gateway prepares/uploads signed encrypted jobs. Owner and
  worker credentials remain separate; four logical hospitals currently share
  the customer's encryption key through that trusted gateway.
- Verify managed-identity denial against every source container and unrelated
  project; verify private DNS, denied Internet egress, ledger persistence and
  failed-job recovery. Do not infer isolation merely from Bicep compilation.
- Grant teammates project-specific VM access, if needed, through their actual
  Entra identities; never share personal credentials or subscription access.
- Keep the key authority on a separate trust boundary. Same-VM containers alone
  are not enough if the platform administrator can read the owner's secrets.
- Stop/deallocate unused compute. No VM is provisioned automatically by tests.

Native Concrete count circuits must be saved with `via_mlir=True` for a Mac
gateway and Linux worker. Exporting a native Mac shared library failed the first
cloud query; the portable-IR export fixed it. Concrete ML's deployment exporter
already defaults to portable MLIR for the training circuit.

The prototype assumes honest-but-curious computation. Remote attestation,
malicious-computation verification, stable customer key management and a
production result-release service are not yet implemented.
