# Measured benchmark evidence

Engineering smoke tests, 4 updates of 8 records; not clinical validation or proof of privacy.

Library-default failures and stricter numerical-error runs are separate measurements; see local-evidence.json for both.

| Dataset | PBS error | Status | Float AUROC | FHE AUROC | Weight error | Count error | Training compute (s) |
|---|---:|---|---:|---:|---:|---:|---:|
| diabetes | 0.01 | failed_engineering_check | 0.78788 | 0.79419 | 0.15096 | 0 | 80.067 |
| synthea | 0.01 | completed | 0.89524 | 0.90476 | 0 | 0 | 62.115 |
| mimic-demo | 0.01 | failed_engineering_check | 0.5 | 0.5 | 0.030672 | 0 | 86.597 |
| har | 0.01 | failed_engineering_check | 0.99903 | 0.99902 | 0.063492 | 0 | 86.119 |
| bidmc | 0.01 | failed_engineering_check | — | — | 0.030672 | 0 | 44.19 |
| diabetes | 1e-06 | completed | 0.78788 | 0.79318 | 0 | 0 | 312.38 |
| synthea | 1e-06 | completed | 0.89524 | 0.90476 | 0 | 0 | 222.76 |
| mimic-demo | 1e-06 | completed | 0.5 | 0.5 | 0 | 0 | 178.53 |
| har | 1e-06 | completed | 0.99903 | 0.99906 | 0 | 0 | 343.32 |
| bidmc | 1e-06 | completed | — | — | 0 | 0 | 273.44 |

All numerical failures are kept visible. A passing correctness check is not a privacy certification.

The full JSON includes membership-attack metrics, source hashes, versions and communication sizes.
