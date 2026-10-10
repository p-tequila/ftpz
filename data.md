# Data inventory

This is the running inventory for the `nftpz` privacy benchmark. It records
what is available locally, what is tracked in Git, and what each dataset is
intended to test.

Raw third-party datasets are intentionally kept out of this public repository.
The local copies can be reproduced from the source URLs and verified with the
checksums below.

## Local datasets from `FTPZ.pdf`

| Dataset | Local path | Approx. size | Git status | Main purpose |
|---|---|---:|---|---|
| UCI Human Activity Recognition | `data/pdf-datasets/uci-har/` | 58 MB archive + extracted files | local-only | Subject identity and reconstruction smoke tests |
| MIMIC-IV Clinical Database Demo 2.2 | `data/pdf-datasets/mimic-iv-demo/` | 16 MB archive + extracted files | local-only | Clinical cohort, rare-category, and differencing tests |
| BIDMC PPG and Respiration | `data/pdf-datasets/bidmc/bidmc_data.mat` | 29 MB | local-only | Physiological signal reconstruction and identity/source leakage |
| WESAD | `data/pdf-datasets/wesad/` | metadata only | metadata tracked; full data not acquired | Cross-device identity leakage |
| Google private-ML examples | not acquired | — | reference only | Reproduction target pending exact dataset identification |
| 12-cell-line perturbation collection | outside repo: parent `f15-vcell` workspace | existing local collection | not copied | Biological and institutional leakage; centralized/federated utility |

## Additional datasets acquired

| Dataset | Local path | Scope | Git status | Main purpose |
|---|---|---|---|---|
| Synthea | `data/additional/synthea/` | 108 synthetic patients in this local archive, CSV | local-only | Individual membership, linkage, and query-differencing tests |
| Human Cell Atlas | `data/additional/hca/projects.json` | 20-project metadata snapshot | tracked | Donor/tissue/project/lab provenance planning |
| GDC / TCGA-BRCA | `data/additional/gdc/tcga_brca_metadata.json` | 100 case/project identifiers only | tracked | Metadata/provenance; no clinical-attribute prediction from this snapshot |
| Diabetes | `data/diabetes/` | 442 records, 10 original features | tracked | Executable encrypted training/inference and count benchmark |

## Reproduction sources

- UCI HAR: https://archive.ics.uci.edu/dataset/240/human+activity+recognition+using+smartphones
- WESAD: https://archive.ics.uci.edu/dataset/465/wesad+wearable+stress+and+affect+detection
- MIMIC-IV demo: https://physionet.org/content/mimic-iv-demo/2.2/
- BIDMC: https://physionet.org/content/bidmc/1.0.0/
- Synthea: https://synthetichealth.github.io/downloads.html
- Human Cell Atlas API: https://data.humancellatlas.org/apis/api-documentation/data-browser-api
- GDC API: https://gdc.cancer.gov/developers/gdc-application-programming-interface-api

## Local artifact checksums

SHA-256 checksums for the downloaded local artifacts:

```text
c00b803081a5c797cd5e4b83700a9810b38d53d9d84e01917e090e1fdbc81031  data/pdf-datasets/uci-har/UCI_HAR_Dataset.zip
97301a03820e8f41af211cf3462ddc19aefe75bbed05f11753859affaafeb8ec  data/pdf-datasets/mimic-iv-demo/mimic-iv-demo-2.2.zip
91865c2fffff70868875545f897542003d376a53262c7c0ead5b6e9109e884db  data/pdf-datasets/bidmc/bidmc_data.mat
14663b3b5e2516773d2001d38bdb258e91ee6f3c927002d6b963aa7e0c12aef9  data/pdf-datasets/wesad/WESAD_uci_metadata.zip
d61417b551e5b0997c33851b339c157421751f0ea68c18ea686ceb1850907c35  data/additional/synthea/synthea_sample_data_csv_latest.zip
e2c74e207b01f04ded7806ed83063b782e9deed07d865b7d5152d1580ed6cd8d  data/additional/hca/projects.json
3b6786fcc6eab109419a528b692037d8291f13d6a6ffda42437a6f0f59362039  data/additional/gdc/tcga_brca_metadata.json
```

## Benchmark readiness

The runnable adapters now cover diabetes, Synthea, MIMIC demo, HAR and BIDMC:
**five training/query datasets** plus **two metadata-only snapshots**. HAR has
10,299 windows from 30 subjects. BIDMC has 53 records and 46 distinct local
record IDs; identical IDs are conservatively grouped together. WESAD's wrapper
is not the actual signal dataset. The separately held cell-line collection is
not imported or verified here and must not be counted as 12 ready datasets.

`nftpz_platform.datasets.inventory()` computes actual shapes, availability and
source hashes. `benchmarks/README.md` describes executable tests; the precise
attack implementation status is in `adversarial-testing/implemented-methods.md`.
The original paper catalog contains planned methods beyond this runnable subset.
