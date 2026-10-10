# Datasets from `FTPZ.pdf`

This directory collects the datasets named in `/Users/pberlizov/Downloads/FTPZ.pdf`.
Archives are kept alongside extracted files when practical. Do not commit these
archives to Git; they are local benchmark inputs and may have separate
attribution/license requirements.

## Acquisition status

| Dataset | Status | Local material | Intended use |
|---|---|---|---|
| UCI Human Activity Recognition | **Collected** | `uci-har/UCI_HAR_Dataset.zip` and `uci-har/extracted/` | Subject identity and reconstruction attack smoke tests |
| MIMIC-IV Clinical Database Demo 2.2 | **Collected** | `mimic-iv-demo/mimic-iv-demo-2.2.zip` and `mimic-iv-demo/extracted/` | Clinical query, cohort, and differencing tests |
| BIDMC PPG and Respiration | **Partial** | `bidmc/bidmc_data.mat` downloading; `bidmc-1.0.0.partial.zip` is an interrupted full archive | Physiological signal reconstruction and identity/source leakage |
| WESAD | **Metadata collected** | `wesad/WESAD_uci_metadata.zip` and `wesad/extracted/` | Cross-device identity leakage; full archive is linked by the metadata file |
| Google private-ML examples | **Reference only** | Dataset is referenced by the PDF paper, but no canonical downloadable archive was specified | Reproduction/reference, pending exact dataset identification |
| 12 cell-line perturbation collection | **Existing outside this repo** | Local source remains in the parent `f15-vcell` workspace | Biological and institutional leakage; centralized/federated utility comparison |

## Source records

- UCI HAR: https://archive.ics.uci.edu/dataset/240/human+activity+recognition+using+smartphones
- WESAD: https://archive.ics.uci.edu/dataset/465/wesad+wearable+stress+and+affect+detection
- MIMIC-IV demo: https://physionet.org/content/mimic-iv-demo/2.2/
- BIDMC: https://physionet.org/content/bidmc/1.0.0/

## Important handling notes

- MIMIC-IV demo is openly downloadable under its specified terms, but it is
  still clinical de-identified data. Preserve the dataset license and citation.
- WESAD's UCI archive is a metadata wrapper pointing to the original host;
  the actual download link should be verified manually before acquisition.
- BIDMC's full archive is about 208 MB and is intentionally not required for
  the first benchmark; the single `bidmc_data.mat` file is sufficient for an
  initial signal-level experiment.
- These datasets should be transformed into benchmark-specific fixtures rather
  than imported wholesale into Git.
