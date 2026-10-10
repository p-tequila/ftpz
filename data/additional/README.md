# Additional datasets collected from the benchmark discussion

These are bounded, public acquisitions; the full HCA and GDC repositories are
not mirrored locally.

| Source | Local artifact | Scope | Intended benchmark use |
|---|---|---|---|
| Synthea | `synthea/synthea_sample_data_csv_latest.zip` and `synthea/extracted/` | 100 current-version synthetic patient records in CSV | Controlled individual-level membership, linkage, and query-differencing tests |
| Human Cell Atlas | `hca/projects.json` | HCA project metadata index, 20-page request | Donor/tissue/project/lab provenance and biological-attribute attack planning |
| NCI GDC / TCGA-BRCA | `gdc/tcga_brca_metadata.json` | 100 open API case metadata records | Cancer cohort/site/clinical-attribute query tests; no raw controlled genomics downloaded |

## Sources

- Synthea downloads: https://synthetichealth.github.io/downloads.html
- HCA Data Browser API: https://data.humancellatlas.org/apis/api-documentation/data-browser-api
- GDC API: https://gdc.cancer.gov/developers/gdc-application-programming-interface-api

The Synthea files are synthetic and not patient records. HCA and GDC
artifacts are metadata-first fixtures; before downloading expression matrices or
other larger objects, select one specific public project and verify its access
and data-use terms.
