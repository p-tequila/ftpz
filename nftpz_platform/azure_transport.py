"""Customer-side Azure dispatch. The cloud identity never receives CLI credentials."""
import json
from pathlib import Path
import re
import shlex
import subprocess
import uuid
from azure.identity import AzureCliCredential
from azure.storage.blob import ContainerClient
from .security import canonical
from .wire import split_silos


def dispatch(config_path, envelope, server_directory, public_key):
    config = json.loads(Path(config_path).read_text())
    required = {"account", "subscription", "resource_group", "vm", "identity_client_id"}
    if set(config) != required:
        raise ValueError("invalid project-only Azure transport config")
    if not re.fullmatch(r"[a-z0-9]{3,24}", config["account"]):
        raise ValueError("invalid Azure storage hostname")
    uuid.UUID(config["subscription"])
    uuid.UUID(config["identity_client_id"])
    # Credentials stay in the trusted customer's local process. The VM uses its
    # own managed identity scoped only to ciphertext input/output containers.
    credential = AzureCliCredential(subscription=config["subscription"])
    jobs = ContainerClient(f"https://{config['account']}.blob.core.windows.net", "ciphertext-jobs", credential=credential)
    results = ContainerClient(f"https://{config['account']}.blob.core.windows.net", "ciphertext-results", credential=credential)
    job = envelope["approval"]["manifest"]["job_id"]
    transfer, objects = split_silos(envelope)
    for site, value in objects.items():
        jobs.upload_blob(f"{job}/{site}.json", canonical(value), overwrite=False)
    jobs.upload_blob(f"{job}/server.zip", (server_directory / "server.zip").read_bytes(), overwrite=False)
    jobs.upload_blob(f"{job}/envelope.json", canonical(transfer), overwrite=False)
    command = ["sudo", "-u", "nftpzoperator", "env", "PYTHONPATH=/opt/nftpz/runtime:/opt/nftpz/app",
               "OMP_NUM_THREADS=4", "/usr/bin/python3", "-m", "nftpz_platform.cloud_worker",
               "--account", config["account"], "--job", job, "--public-key", public_key,
               "--identity-client-id", config["identity_client_id"], "--ledger", "/var/lib/nftpz/worker.sqlite"]
    result = subprocess.run(["az", "vm", "run-command", "invoke", "--subscription", config["subscription"],
                             "--resource-group", config["resource_group"], "--name", config["vm"],
                             "--command-id", "RunShellScript", "--scripts", shlex.join(command), "-o", "json"],
                            capture_output=True, text=True, timeout=1800)
    if result.returncode:
        raise RuntimeError(f"Azure dispatch failed: {result.stderr[-1000:]}")
    try:
        response = json.loads(results.download_blob(f"{job}/result.json").readall())
    except Exception as error:
        raise RuntimeError(f"Azure worker did not publish its encrypted result: {result.stdout[-1800:]}") from error
    response["execution_environment"] = "Azure private VM; ciphertext-only managed identity"
    response["azure_vm"] = config["vm"]
    response["encrypted_silo_blob_count"] = len(objects)
    return response
