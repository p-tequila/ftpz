#!/usr/bin/env bash
# Run ONLY on the dedicated new nftpz VM via the Azure management plane.
set -euo pipefail
nftpz_account="$1"
nftpz_identity="$2"
nftpz_code_sha="$3"
[[ "$nftpz_account" =~ ^[a-z0-9]{3,24}$ ]]
[[ "$nftpz_code_sha" =~ ^[a-f0-9]{64}$ ]]
export DEBIAN_FRONTEND=noninteractive
sed -i 's|http://|https://|g' /etc/apt/sources.list.d/ubuntu.sources
sed -i 's|https://azure.archive.ubuntu.com/ubuntu|https://archive.ubuntu.com/ubuntu|g' /etc/apt/sources.list.d/ubuntu.sources
apt-get update -qq
apt-get install -y -qq --no-install-recommends python3-pip python3-dev libgomp1 build-essential cmake ninja-build
install -d -m 0755 /opt/nftpz/app /opt/nftpz/runtime
install -d -o nftpzoperator -g nftpzoperator -m 0700 /var/lib/nftpz
# Managed-identity token stays inside this process; never echo it or persist it.
python3 - "$nftpz_account" "$nftpz_identity" "$nftpz_code_sha" <<'PY'
import hashlib, io, json, sys, tarfile, urllib.parse, urllib.request
from pathlib import Path
account, identity, expected = sys.argv[1:]
staged = Path('/opt/nftpz/bootstrap.tar.gz')
if staged.exists():
    data = staged.read_bytes()
else:
    query = urllib.parse.urlencode({"api-version": "2018-02-01", "resource": "https://storage.azure.com/", "client_id": identity})
    request = urllib.request.Request("http://169.254.169.254/metadata/identity/oauth2/token?" + query, headers={"Metadata": "true"})
    token = json.load(urllib.request.urlopen(request))["access_token"]
    request = urllib.request.Request(f"https://{account}.blob.core.windows.net/ciphertext-jobs/bootstrap/code.tar.gz",
                                     headers={"Authorization": "Bearer " + token, "x-ms-version": "2023-11-03"})
    data = urllib.request.urlopen(request).read()
if hashlib.sha256(data).hexdigest() != expected:
    raise SystemExit("bootstrap code hash mismatch")
with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as archive:
    archive.extractall("/opt/nftpz/app", filter="data")
print("Verified project code package", expected)
PY
python3 -m pip install --target /opt/nftpz/runtime -r /opt/nftpz/app/requirements-platform.txt \
  'torch==2.3.1+cpu' --extra-index-url https://download.pytorch.org/whl/cpu > /var/log/nftpz-bootstrap.log 2>&1
sudo -u nftpzoperator env PYTHONPATH=/opt/nftpz/runtime:/opt/nftpz/app \
  python3 -c 'import concrete.ml.sklearn; from concrete import fhe; print("Concrete ML CPU worker runtime ready")'
