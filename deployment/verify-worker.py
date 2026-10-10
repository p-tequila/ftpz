"""Run as the unprivileged worker to measure the deployed network/IAM boundary."""
import argparse
import json
from pathlib import Path
import urllib.request
from azure.core.exceptions import HttpResponseError, ServiceRequestError, ServiceResponseError
from azure.identity import ManagedIdentityCredential
from azure.storage.blob import ContainerClient

parser = argparse.ArgumentParser()
parser.add_argument("--account", required=True)
parser.add_argument("--source-account", required=True)
parser.add_argument("--identity", required=True)
args = parser.parse_args()
credential = ManagedIdentityCredential(client_id=args.identity)
def container(account, name):
    return ContainerClient(f"https://{account}.blob.core.windows.net", name, credential=credential,
                           connection_timeout=3, read_timeout=3, retry_total=0)

checks = {}
jobs = container(args.account, "ciphertext-jobs")
jobs.get_container_properties()
checks["ciphertext_inputs_readable"] = True
try:
    jobs.upload_blob("security-probes/job-writes-must-fail.txt", b"nonsensitive permission probe", overwrite=False)
    checks["worker_cannot_modify_approved_jobs"] = False
except HttpResponseError as error:
    checks["worker_cannot_modify_approved_jobs"] = error.status_code == 403
try:
    container(args.source_account, "site-a").get_container_properties()
    checks["owner_source_account_inaccessible"] = False
except HttpResponseError as error:
    checks["owner_source_account_inaccessible"] = error.status_code == 403
except (ServiceRequestError, ServiceResponseError):
    checks["owner_source_account_inaccessible"] = True
try:
    urllib.request.urlopen("https://example.com", timeout=5)
    checks["internet_https_egress_denied"] = False
except (OSError, TimeoutError):
    checks["internet_https_egress_denied"] = True
checks["no_owner_dataset_mount"] = not Path("/opt/nftpz/app/data").exists()
checks["no_customer_private_output_mount"] = not Path("/opt/nftpz/app/outputs").exists()
print(json.dumps({"checks": checks, "note": "Measured probes plus separately verified role scopes; not a penetration test or attestation."}))
raise SystemExit(0 if all(checks.values()) else 1)
