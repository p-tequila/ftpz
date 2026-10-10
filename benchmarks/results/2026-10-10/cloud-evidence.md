# Measured benchmark evidence

Engineering smoke tests, 4 updates of 8 records; not clinical validation or proof of privacy.

Library-default failures and stricter numerical-error runs are separate measurements; see local-evidence.json for both.

| Dataset | PBS error | Status | Float AUROC | FHE AUROC | Weight error | Count error | Training compute (s) |
|---|---:|---|---:|---:|---:|---:|---:|
| diabetes | 1e-06 | completed | 0.78788 | 0.79318 | 0 | 0 | 66.98 |

All numerical failures are kept visible. A passing correctness check is not a privacy certification.

The full JSON includes membership-attack metrics, source hashes, versions and communication sizes.
