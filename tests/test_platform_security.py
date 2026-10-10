import tempfile
import unittest
from pathlib import Path
import numpy as np
from nftpz_platform.attacks import policy_attacks, differencing_control, gaussian_likelihood_ratio, shadow_lira_probe
from nftpz_platform.datasets import Table, batches_for_sites, partition
from nftpz_platform.metrics import binary_attack_advantage, rmse
from nftpz_platform.storage import LocalBlobStore


class SecurityTests(unittest.TestCase):
    def test_lira_likelihood_ratio_direction(self):
        scores = gaussian_likelihood_ratio(np.array([2., -2.]), np.array([[1.9, 1.9], [2.1, 2.1]]),
                                           np.array([[-2.1, -2.1], [-1.9, -1.9]]))
        self.assertGreater(scores[0], 0)
        self.assertLess(scores[1], 0)

    def test_shadow_attack_has_disjoint_calibration_and_evaluation(self):
        from diabetes_demo.experiments import float_training
        rng = np.random.default_rng(42)
        X = rng.uniform(-1, 1, (100, 2))
        y = (X[:, 0] > 0).astype(int)
        batches = np.arange(32).reshape(4, 8)
        model = float_training(X, y, batches)
        result = shadow_lira_probe(model, X, y, np.arange(100), batches, np.arange(60, 100), shadows=4)
        self.assertEqual(result["target_queries"], 64)
        self.assertEqual(result["metrics"]["member_count"], 16)
        self.assertEqual(result["metrics"]["calibration_nonmembers"], 16)

    def test_all_policy_probes_block_and_controls_pass(self):
        for result in policy_attacks():
            self.assertTrue(result.get("blocked", result.get("passed")), result["id"])

    def test_min_cohort_is_not_dp(self):
        self.assertEqual(differencing_control()["residual_risk"], "OPEN")

    def test_metrics_handle_generators_ties_and_shape(self):
        self.assertEqual(binary_attack_advantage(iter([0, 1]), iter([.5, .5])), 0)
        self.assertEqual(binary_attack_advantage([0, 1], [.1, .9]), 1)
        with self.assertRaises(ValueError):
            rmse([1, 2], [1])
        with self.assertRaises(ValueError):
            binary_attack_advantage([0, 1], [float("nan"), .5])

    def test_group_partition_prevents_patient_and_site_overlap(self):
        table = Table("test", np.zeros((60, 2)), np.tile([0, 1], 30),
                      np.repeat(np.arange(20).astype(str), 3), ("a", "b"), ((0, 1), (0, 1)), "test", ())
        sites, test = partition(table)
        all_indices = np.concatenate([*sites, test])
        self.assertEqual(len(set(all_indices)), 60)
        all_groups = [set(table.groups[s]) for s in [*sites, test]]
        for i, group in enumerate(all_groups):
            for other in all_groups[i+1:]:
                self.assertFalse(group & other)
        batches = batches_for_sites(sites, 4)
        for indices, site in zip(batches, sites):
            self.assertTrue(set(indices) <= set(site))

    def test_normalization_uses_fixed_bounds(self):
        table = Table("test", np.array([[2., -1.]]), np.array([0]), np.array(["p"]),
                      ("a", "b"), ((0, 1), (0, 1)), "test", ())
        X, clipped = table.normalized()
        np.testing.assert_array_equal(X, [[1, -1]])
        self.assertEqual(clipped, 2)

    def test_local_store_rejects_escape_and_overwrite(self):
        with tempfile.TemporaryDirectory() as temp:
            store = LocalBlobStore(Path(temp) / "silo")
            store.write("input/a.bin", b"ciphertext")
            self.assertEqual(store.read("input/a.bin"), b"ciphertext")
            with self.assertRaises(FileExistsError):
                store.write("input/a.bin", b"changed")
            for path in ["../x", "/etc/passwd", "a/../../x", "a\\x", "a//b"]:
                with self.assertRaises(ValueError):
                    store.read(path)
            (store.root / "outside").symlink_to(Path(temp))
            with self.assertRaises(ValueError):
                store.read("outside/anything")


if __name__ == "__main__":
    unittest.main()
