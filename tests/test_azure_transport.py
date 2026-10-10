import json
from pathlib import Path
import tempfile
import unittest
from nftpz_platform.azure_transport import dispatch


class AzureTransportValidationTests(unittest.TestCase):
    def test_config_cannot_redirect_storage_credentials_to_nonazure_host(self):
        config = {"account": "evil.example/path?", "subscription": "00000000-0000-0000-0000-000000000000",
                  "resource_group": "nftpz-test", "vm": "worker",
                  "identity_client_id": "00000000-0000-0000-0000-000000000000"}
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "config.json"
            path.write_text(json.dumps(config))
            with self.assertRaisesRegex(ValueError, "hostname"):
                dispatch(path, {}, Path(temp), "public-key")

    def test_unrecognized_transport_fields_are_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "config.json"
            path.write_text(json.dumps({"sas": "forbidden"}))
            with self.assertRaisesRegex(ValueError, "project-only"):
                dispatch(path, {}, Path(temp), "public-key")


if __name__ == "__main__":
    unittest.main()
