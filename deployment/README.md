# Isolated Azure worker (deployment scaffold)

The local FHE pipeline runs today. This directory is a deployment scaffold,
not evidence that Azure compute, RBAC or private networking has been exercised.

Current project source account was checked read-only: public access is disabled,
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

## Building and dispatching

Build the image in a trusted build environment using `deployment/Dockerfile.worker`.
The Docker context explicitly excludes all data, outputs, credentials and Git
history. Run as UID 10001 with a read-only root filesystem, a bounded tmpfs for
temporary ciphertexts and a durable writable ledger volume. Supply the pinned
customer approval public key independently of the job.

```bash
docker build -f deployment/Dockerfile.worker -t nftpz-worker:prototype .
# Within the private network, with the dedicated managed identity available:
python -m nftpz_platform.cloud_worker \
  --account YOUR_CIPHERTEXT_ACCOUNT --job APPROVED_JOB_ID \
  --public-key PINNED_ED25519_PUBLIC_KEY_HEX \
  --identity-client-id WORKER_IDENTITY_CLIENT_ID \
  --ledger /var/lib/nftpz/worker.sqlite
```

Owner/key-authority tooling stages `<job>/envelope.json` and `<job>/server.zip`
in `ciphertext-jobs`; outputs appear at `<job>/result.json`. Only ciphertexts,
public compiled artifacts, evaluation keys and approved metadata belong here.
The trusted gateway needs its own identity and private network path; this
template deliberately does not grant the worker access to owner containers.

## Deployment gates still required

- Validate the template and inspect an Azure what-if under the chosen dedicated
  resource group before deployment. The template creates billable resources.
- The default worker NSG allows blob-private-endpoint traffic and platform DNS,
  and denies other outbound traffic. Stage a prebuilt worker image/runtime using
  an approved management path; it cannot `pip install` from the Internet as-is.
  No bootstrap extension or image-pull workaround weakens that default.
- A customer-owned gateway must prepare/upload signed encrypted jobs. The local
  runner currently dispatches a subprocess; it is not wired to an Azure queue.
- Verify managed-identity denial against every source container and unrelated
  project; verify private DNS, denied Internet egress, ledger persistence and
  failed-job recovery. Do not infer isolation merely from Bicep compilation.
- Grant teammates project-specific VM access, if needed, through their actual
  Entra identities; never share personal credentials or subscription access.
- Keep the key authority on a separate trust boundary. Same-VM containers alone
  are not enough if the platform administrator can read the owner's secrets.
- Stop/deallocate unused compute. No VM is provisioned automatically by tests.

The prototype assumes honest-but-curious computation. Remote attestation,
malicious-computation verification, stable customer key management and a
production result-release service are not yet implemented.
