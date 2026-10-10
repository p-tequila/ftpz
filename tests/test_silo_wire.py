import copy
import unittest
from nftpz_platform.security import Authority, Denied, make_manifest, verify
from nftpz_platform.wire import split_silos, hydrate_silos


class SiloWireTests(unittest.TestCase):
    def envelope(self, operation):
        request = {"operation": operation, "evaluation_keys": "AA=="}
        if operation == "training":
            request.update({"site_order": [f"site-{s}" for s in "abcdabcd"],
                            "batches": [["AA==", "AQ=="] for _ in range(8)], "state": ["AA==", "AA=="]})
        else:
            request["inputs"] = ["AA==", "AQ==", "Ag==", "Aw=="]
        authority = Authority()
        manifest = make_manifest(request, "program", "schema", "job", {})
        return authority, {"request": request, "approval": authority.approve(manifest)}

    def test_each_operation_roundtrips_across_four_separate_objects(self):
        for operation in ("training", "aggregate"):
            authority, envelope = self.envelope(operation)
            transfer, objects = split_silos(envelope)
            self.assertEqual(len(objects), 4)
            reconstructed = hydrate_silos(transfer, objects)
            self.assertEqual(reconstructed, envelope)
            verify(reconstructed["approval"], authority.public_key, reconstructed["request"], "program")

    def test_changed_contribution_fails_authority_signature_binding(self):
        authority, envelope = self.envelope("aggregate")
        transfer, objects = split_silos(envelope)
        objects["site-b"]["input"] = "CQ=="
        reconstructed = hydrate_silos(transfer, objects)
        with self.assertRaises(Denied):
            verify(reconstructed["approval"], authority.public_key, reconstructed["request"], "program")

    def test_missing_or_substituted_owner_is_rejected(self):
        _, envelope = self.envelope("training")
        transfer, objects = split_silos(envelope)
        missing = copy.deepcopy(objects)
        del missing["site-c"]
        with self.assertRaises(ValueError):
            hydrate_silos(transfer, missing)
        objects["site-d"]["site"] = "site-a"
        with self.assertRaises(ValueError):
            hydrate_silos(transfer, objects)
