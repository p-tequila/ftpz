import unittest

from nftpz_platform.metrics import relative_error, rmse
from nftpz_platform.queries import Query, owner_count
from nftpz_platform.storage import LocalBlobStore


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


if __name__ == "__main__":
    unittest.main()
