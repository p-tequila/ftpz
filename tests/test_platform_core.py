import unittest

from nftpz_platform.metrics import relative_error, rmse
from nftpz_platform.queries import Query, owner_count
from nftpz_platform.storage import LocalBlobStore
from nftpz_platform.benchmark import engineering_checks


class PlatformCoreTests(unittest.TestCase):
    def test_owner_predicate_is_allowlisted(self):
        Query("age", "ge", 50).validate(["age"])
        with self.assertRaises(ValueError):
            Query("secret", "ge", 50).validate(["age"])
        with self.assertRaises(ValueError):
            Query("age", "eval", 50).validate(["age"])

    def test_local_store_blocks_path_escape(self):
        store = LocalBlobStore(".")
        with self.assertRaises(ValueError):
            store.read("../outside")

    def test_metrics(self):
        self.assertAlmostEqual(relative_error(11, 10), 0.1)
        self.assertAlmostEqual(rmse([1, 3], [1, 1]), 2 ** 0.5)

    def test_inference_failure_is_an_engineering_failure(self):
        result = {"max_weight_difference_vs_quantized": 0,
                  "training_audit": {"wrong_key_recovery_failed": True},
                  "inference": {"max_difference_vs_quantized": .01}}
        self.assertFalse(all(engineering_checks(result, {"absolute_error": 0}).values()))
        result["inference"]["max_difference_vs_quantized"] = 0
        self.assertTrue(all(engineering_checks(result, {"absolute_error": 0}).values()))

    def test_skipped_inference_is_not_reported_as_passed(self):
        result = {"max_weight_difference_vs_quantized": 0,
                  "training_audit": {"wrong_key_recovery_failed": True}}
        checks = engineering_checks(result, {"absolute_error": 0})
        self.assertNotIn("exact_inference_quantized_parity", checks)


if __name__ == "__main__":
    unittest.main()
