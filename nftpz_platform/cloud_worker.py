"""One-shot Azure worker: download approved ciphertext job, execute, upload result.

Managed identity scope: ciphertext-jobs Reader + ciphertext-results Contributor.
No owner-source containers or key-authority directories are read by this module.
The durable ledger mount must survive container restarts and be single-writer.
"""
import argparse
import json
from pathlib import Path
import tempfile
from .storage import AzureBlobStore, object_name
from .worker import execute
from .security import canonical
from .wire import SITES, hydrate_silos


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--account", required=True)
    parser.add_argument("--job", required=True)
    parser.add_argument("--public-key", required=True, help="Pinned customer approver key, never loaded from job")
    parser.add_argument("--ledger", required=True, type=Path)
    parser.add_argument("--identity-client-id")
    args = parser.parse_args()
    job = object_name(args.job)
    if "/" in job:
        parser.error("job must be one opaque path component")
    source = AzureBlobStore(args.account, "ciphertext-jobs", args.identity_client_id)
    destination = AzureBlobStore(args.account, "ciphertext-results", args.identity_client_id)
    envelope = json.loads(source.read(f"{job}/envelope.json"))
    if envelope["approval"]["manifest"]["job_id"] != job:
        raise ValueError("queue identity differs from approved job")
    if "layout" in envelope:
        objects = {site: json.loads(source.read(f"{job}/{site}.json")) for site in SITES}
        envelope = hydrate_silos(envelope, objects)
    with tempfile.TemporaryDirectory(prefix="ciphertext-worker-") as temp:
        directory = Path(temp)
        (directory / "server.zip").write_bytes(source.read(f"{job}/server.zip"))
        result = execute(envelope, directory, args.public_key, args.ledger)
        destination.write(f"{job}/result.json", canonical(result))
    print(json.dumps({"job": job, "status": "encrypted_result_written"}))


if __name__ == "__main__":
    main()
