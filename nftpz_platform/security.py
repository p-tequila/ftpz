"""Signed execution approval and persistent fail-closed local policy ledger.

Signatures authorize exact bytes; they do NOT prove malicious workers evaluated
FHE correctly. The authority/worker stores must be isolated in deployment.
"""
import base64
import hashlib
import json
import math
from pathlib import Path
import sqlite3
import time
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
from cryptography.exceptions import InvalidSignature


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


class Denied(ValueError):
    pass


class Authority:
    def __init__(self):
        self.key = Ed25519PrivateKey.generate()

    @property
    def public_key(self):
        return self.key.public_key().public_bytes_raw().hex()

    def approve(self, manifest):
        return {"manifest": manifest, "signature": self.key.sign(canonical(manifest)).hex()}


def verify(approval, public_key, request, program_hash, now=None):
    if set(approval) != {"manifest", "signature"}:
        raise Denied("unexpected approval fields")
    manifest = approval["manifest"]
    try:
        Ed25519PublicKey.from_public_bytes(bytes.fromhex(public_key)).verify(
            bytes.fromhex(approval["signature"]), canonical(manifest))
    except (InvalidSignature, ValueError, TypeError) as error:
        raise Denied("invalid authority signature") from error
    required = {"version", "job_id", "operation", "expires_at", "request_hash", "program_hash",
                "key_id", "schema_hash", "contributors", "purpose", "release"}
    if set(manifest) != required or manifest["version"] != 1:
        raise Denied("invalid execution manifest")
    if not math.isfinite(manifest["expires_at"]) or manifest["expires_at"] <= (time.time() if now is None else now):
        raise Denied("expired approval")
    if manifest["operation"] != request.get("operation") or manifest["request_hash"] != digest(request):
        raise Denied("ciphertext request changed")
    if manifest["program_hash"] != program_hash:
        raise Denied("compiled program changed")
    actual_key = hashlib.sha256(base64.b64decode(request["evaluation_keys"], validate=True)).hexdigest()
    if manifest["key_id"] != actual_key:
        raise Denied("wrong evaluation key")
    owners = manifest["contributors"]
    if len(owners) != 4 or len(set(owners)) != 4:
        raise Denied("four distinct contributors required; no silent dropout")
    return manifest


def make_manifest(request, program_hash, schema_hash, job_id, release, purpose="benchmark"):
    return {"version": 1, "job_id": job_id, "operation": request["operation"],
            "expires_at": time.time() + 3600, "request_hash": digest(request),
            "program_hash": program_hash, "key_id": hashlib.sha256(base64.b64decode(request["evaluation_keys"])).hexdigest(),
            "schema_hash": schema_hash, "contributors": [f"site-{i}" for i in "abcd"],
            "purpose": purpose, "release": release}


class Ledger:
    def __init__(self, path):
        path = Path(path)
        self.path = path
        path.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(path, isolation_level=None, timeout=30)
        path.chmod(0o600)
        self.db.executescript("""
            CREATE TABLE IF NOT EXISTS jobs(id TEXT PRIMARY KEY, manifest TEXT NOT NULL, status TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS releases(job TEXT PRIMARY KEY, scope TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS events(seq INTEGER PRIMARY KEY, event TEXT NOT NULL, previous TEXT NOT NULL, hash TEXT NOT NULL);
        """)

    def close(self):
        self.db.close()

    def event(self, value):
        row = self.db.execute("SELECT hash FROM events ORDER BY seq DESC LIMIT 1").fetchone()
        previous = row[0] if row else "0" * 64
        encoded = canonical(value).decode()
        self.db.execute("INSERT INTO events(event,previous,hash) VALUES(?,?,?)",
                        (encoded, previous, digest([previous, value])))

    def claim(self, manifest):
        try:
            self.db.execute("INSERT INTO jobs VALUES(?,?,?)", (manifest["job_id"], digest(manifest), "running"))
        except sqlite3.IntegrityError as error:
            raise Denied("replayed job; use a new signed attempt after failure") from error
        self.event({"kind": "accepted", "job": manifest["job_id"], "manifest": digest(manifest)})

    def complete(self, job, output_hash):
        self.db.execute("UPDATE jobs SET status='complete' WHERE id=?", (job,))
        self.event({"kind": "completed", "job": job, "output_hash": output_hash})

    def release(self, manifest, *, cohort_size=None, caller="benchmark-client"):
        """Run ONLY in the key authority, after decrypting internally, before delivery.

        Query budgets are per principal + dataset, not caller-chosen purposes.
        These controls reduce exposure but do not provide differential privacy.
        """
        policy = manifest["release"]
        if (type(policy["max_releases"]) is not int or policy["max_releases"] < 1
                or type(policy["min_cohort"]) is not int or policy["min_cohort"] < 5):
            raise Denied("invalid release policy")
        if caller != policy["principal"]:
            raise Denied("result principal is not authorized")
        if manifest["operation"] == "aggregate" and (cohort_size is None or cohort_size < policy["min_cohort"]):
            raise Denied("small cohort release suppressed")
        scope = digest([caller, manifest["schema_hash"]])
        self.db.execute("BEGIN IMMEDIATE")
        try:
            if self.db.execute("SELECT 1 FROM releases WHERE job=?", (manifest["job_id"],)).fetchone():
                raise Denied("result already released")
            count = self.db.execute("SELECT COUNT(*) FROM releases WHERE scope=?", (scope,)).fetchone()[0]
            if count >= policy["max_releases"]:
                raise Denied("release budget exhausted")
            self.db.execute("INSERT INTO releases VALUES(?,?)", (manifest["job_id"], scope))
            self.event({"kind": "released", "job": manifest["job_id"], "scope": scope})
            self.db.execute("COMMIT")
        except BaseException:
            self.db.execute("ROLLBACK")
            raise

    def audit_valid(self):
        previous = "0" * 64
        for event, prev, actual in self.db.execute("SELECT event,previous,hash FROM events ORDER BY seq"):
            if prev != previous or digest([prev, json.loads(event)]) != actual:
                return False
            previous = actual
        return True
