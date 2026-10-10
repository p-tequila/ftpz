"""Install a checksum-pinned project source package; no personal credentials."""
import argparse
import hashlib
import io
import json
import re
import tarfile
import urllib.parse
import urllib.request

parser = argparse.ArgumentParser()
parser.add_argument("--account", required=True)
parser.add_argument("--identity", required=True)
parser.add_argument("--blob", required=True)
parser.add_argument("--sha256", required=True)
args = parser.parse_args()
if not re.fullmatch(r"[a-z0-9]{3,24}", args.account) or not re.fullmatch(r"[a-f0-9]{64}", args.sha256):
    raise ValueError("invalid pinned package configuration")
query = urllib.parse.urlencode({"api-version": "2018-02-01", "resource": "https://storage.azure.com/", "client_id": args.identity})
request = urllib.request.Request("http://169.254.169.254/metadata/identity/oauth2/token?" + query, headers={"Metadata": "true"})
token = json.load(urllib.request.urlopen(request))["access_token"]
url = f"https://{args.account}.blob.core.windows.net/ciphertext-jobs/" + urllib.parse.quote(args.blob, safe="/")
request = urllib.request.Request(url, headers={"Authorization": "Bearer " + token, "x-ms-version": "2023-11-03"})
data = urllib.request.urlopen(request).read()
if hashlib.sha256(data).hexdigest() != args.sha256:
    raise ValueError("source package checksum mismatch")
with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as archive:
    archive.extractall("/opt/nftpz/app", filter="data")
print("Verified worker source package", args.sha256)
