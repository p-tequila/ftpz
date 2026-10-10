# Attack catalog

Status values:

- **P0**: implement for the first privacy benchmark;
- **P1**: implement after the core benchmark;
- **P2**: integrity/security extension;
- **reference**: paper is used to define the method, but implementation may be adapted.

The canonical paper is listed for each distinct method so that benchmark
results remain attributable and reproducible. Foundational papers are retained
when they define the attack family; newer papers are preferred for the actual
implementation where a stronger or more realistic method exists.

## Risk-category legend

The tags below classify what the attack threatens, not merely where it is
executed:

- **IND — individual privacy:** record membership, identity, or person/sample-level facts;
- **BIO — biological privacy:** disease, tissue, cell line, perturbation, phenotype, ancestry, or other biological properties;
- **ORG — institutional/business privacy:** site participation, cohort composition, proprietary programs, study design, or site-specific results.

The `surface` column in the mapping below identifies the channel being attacked:
query output, released record, model output, gradient/update, embedding,
metadata, or protocol transcript.

## Complete risk-category mapping

This table is normative: every catalog ID must have at least one risk tag and
one attack surface. Multiple tags are intentional because a single attack can
leak more than one kind of information.

| ID | Risk tags | Attack surface | Primary question |
|---|---|---|---|
| MIA-01 | IND, BIO, ORG | model output | Was this record, biological state, or site cohort used in training? |
| MIA-02 | IND, BIO, ORG | model parameters / gradients / outputs | Does white-box access reveal membership or properties? |
| MIA-03 | IND, BIO, ORG | active client model responses | Can a malicious coordinator probe membership or attributes? |
| MIA-04 | IND, BIO, ORG | multi-round gradients | Do temporal update patterns reveal membership or site properties? |
| MIA-05 | IND, BIO | generated records / samples | Does a generated biomedical output reveal training membership? |
| INV-01 | IND, BIO, ORG | client gradients | Can inputs, labels, or site-specific samples be reconstructed? |
| INV-02 | IND, BIO, ORG | client gradients | How much of the original profile and label can be recovered? |
| INV-03 | IND, BIO | final-layer gradients | Can labels or sensitive biological classes be recovered directly? |
| INV-04 | IND, BIO, ORG | shared global model | Can a participant invert other sites’ data from the global model? |
| INV-05 | IND, BIO, ORG | model-weight deltas | Do weight updates leak local records or proprietary site data? |
| INV-06 | IND, BIO | gradients | Can an exact batch be recovered under favorable conditions? |
| INV-07 | IND, BIO, ORG | realistic training updates | Does inversion survive realistic training-mode conditions? |
| INV-08 | IND, BIO, ORG | secure-aggregation transcript | Can Sybil clients isolate an individual or site contribution? |
| ATTR-01 | BIO, ORG | collaborative updates | Can an attacker infer hidden biological or institutional properties? |
| ATTR-02 | BIO, ORG | aggregated gradients | Can rare labels or site composition be recovered despite aggregation? |
| ATTR-03 | IND, BIO, ORG | temporal gradients | Can update trajectories reveal sensitive attributes or site behavior? |
| ATTR-04 | BIO, ORG | model behavior under shift | Are confounders masking leakage of biological or institutional properties? |
| LINK-01 | IND, BIO, ORG | transformed records / embeddings | Can a released object be matched to an auxiliary record or site? |
| LINK-02 | IND, BIO | aggregate genomic answers | Can summary statistics reconstruct participant genomes? |
| LINK-03 | IND, BIO, ORG | quasi-identifiers / metadata | Can repeated metadata identify a patient, sample, or institution? |
| LINK-04 | IND, BIO, ORG | metadata / released records | Can external auxiliary data re-identify protected records? |
| AGG-01 | IND, BIO | aggregate genomic statistics | Can a target’s membership be inferred from aggregate results? |
| AGG-02 | IND, BIO, ORG | query results | Can two or more answers isolate a record, cohort, or site result? |
| AGG-03 | IND, BIO, ORG | counts / means / histograms / rankings | Do small cells or rare categories reveal sensitive facts? |
| AGG-04 | IND, BIO, ORG | repeated query transcript | Does composition across releases amplify leakage? |
| EMB-01 | IND, BIO, ORG | embeddings | Can an obfuscated representation be inverted to its source? |
| EMB-02 | IND, BIO | embeddings | Can auxiliary paired data recover the original biomedical input? |
| EMB-03 | BIO, ORG | embeddings / probes | Does the representation preserve biological or proprietary site identity? |
| SPLIT-01 | IND, BIO, ORG | intermediate activations | Can a server reconstruct inputs, labels, or client functionality? |
| SPLIT-02 | IND, BIO | intermediate activations | Can feature-space representations be inverted? |
| INT-01 | BIO, ORG | training data / model behavior | Can poisoned biomedical data corrupt biological outputs or programs? |
| INT-02 | BIO, ORG | client updates / global model | Can a malicious site alter or exfiltrate through model behavior? |

The integrity attacks `INT-01` and `INT-02` are not confidentiality tests by
themselves. They are tagged `BIO + ORG` because their primary business impact
is corrupted biological conclusions or compromised institutional workflows;
they should be reported in a separate integrity scorecard.

## A. Membership inference

| ID | Method / paper | Attacker and leakage | Proposed test | Priority |
|---|---|---|---|---|
| MIA-01 | **Membership inference attacks against machine-learning models** — Shokri et al., 2017. [Paper](https://doi.org/10.1109/SP.2017.41) | Black-box model access; infer whether a target record was in training data using shadow models and attack classifiers. | Train shadow models on public/holdout data; attack prediction vectors for member/non-member records. | P0 / reference |
| MIA-02 | **Comprehensive privacy analysis of deep learning: passive and active white-box attacks** — Nasr et al., 2019. [Paper](https://doi.org/10.1109/SP.2019.00065) | White-box access to model parameters, gradients, and outputs; stronger membership signal than output-only attacks. | Compare black-box, gray-box, and white-box attacks against every released model/update surface. | P0 |
| MIA-03 | **Active Membership Inference Attack under Local Differential Privacy in Federated Learning** — Nguyen et al., 2023. [Paper](https://proceedings.mlr.press/v206/nguyen23e.html) | Malicious server actively modifies the model sent to a client to amplify membership signals, even under LDP. | Send target-specific probe models/heads; measure membership advantage as a function of epsilon, rounds, and client size. | P0 |
| MIA-04 | **An Efficient Gradient-Based Inference Attack for Federated Learning** — Montaña-Fernández & Ortega-Fernández, 2025. [Paper](https://arxiv.org/abs/2512.15143) | Multi-round last-layer gradients; shadow attack uses temporal gradient evolution and supports attribute inference. | Train a temporal attack over client updates; evaluate membership and sensitive-attribute inference without private attacker training data. | P0 |
| MIA-05 | **Biologically-Informed Hybrid Membership Inference Attacks on Generative Genomic Models** — Belfiore et al., 2025. [Paper](https://arxiv.org/abs/2511.07503) | Black-box membership attack augmented with domain/biological similarity signals. | For synthetic or generated biomedical outputs, combine likelihood/rank signals with biological similarity and evaluate member/non-member separation. | P1 |

## B. Gradient, update, and model inversion

| ID | Method / paper | Attacker and leakage | Proposed test | Priority |
|---|---|---|---|---|
| INV-01 | **Deep Leakage from Gradients** — Zhu et al., 2019. [Paper](https://arxiv.org/abs/1906.08935) | Honest-but-curious coordinator reconstructs inputs and labels by optimizing dummy data to match a gradient. | Reconstruct small batches from exposed client gradients; report feature correlation, label accuracy, and recovery rate. | P0 / reference |
| INV-02 | **Inverting Gradients — How easy is it to break privacy in federated learning?** — Geiping et al., 2020. [Paper](https://proceedings.neurips.cc/paper/2020/hash/c4ede56bbd1c0a2a-Abstract.html) | Improved gradient matching with image priors and signed gradients; demonstrates practical recovery beyond toy settings. | Run cosine-gradient inversion with known/unknown labels, batch size, clipping, and noise. Adapt image metrics to gene-expression correlation and marker recovery. | P0 / reference |
| INV-03 | **iDLG: Improved Deep Leakage from Gradients** — Zhao et al., 2020. [Paper](https://github.com/mit-han-lab/dlg) | Exploits the final-layer gradient to infer labels before optimization. | Test label recovery from the final layer and use recovered labels to initialize full reconstruction. | P0 / reference |
| INV-04 | **FedInverse: Evaluating Privacy Leakage in Federated Learning** — Wang et al., ICLR 2024. [Paper](https://proceedings.iclr.cc/paper_files/paper/2024/hash/c225136cfe52a8fd66658bbcf9d894ab-Abstract-Conference.html) | A benign-looking participant inverts the shared global model using a generator and HSIC regularization. | Add a participant-side model inversion test against the global model, including non-IID site splits. | P0 |
| INV-05 | **Deep Leakage from Model in Federated Learning** — Zhao, Luo & Ding, 2024. [Paper](https://proceedings.mlr.press/v234/zhao24b.html) | Reconstructs local data from transmitted model weights rather than explicit gradients; DLM/DLM+ reduces unrealistic auxiliary assumptions. | Attack weight deltas under FedAvg and other update rules; vary knowledge of optimizer, learning rate, and local steps. | P0 |
| INV-06 | **SPEAR: Exact Gradient Inversion of Batches in Federated Learning** — 2024. [Paper](https://openreview.net/forum?id=lPDxPVS6ix) | Exact batch recovery in favorable settings, targeting limitations of approximate gradient inversion. | Include as a high-severity stress test for small batches and overparameterized models; separately record when assumptions do not hold. | P1 |
| INV-07 | **From Research to Reality: Feasibility of Gradient Inversion Attacks in Federated Learning** — Valadi et al., 2025. [Paper](https://arxiv.org/abs/2508.19819) | Tests inversion under realistic training mode, dropout, normalization, and production-like architectures. | Use as the realism protocol: repeat inversion with training-mode clients, unknown normalization state, dropout, and architecture variations. | P0 |
| INV-08 | **Reconstructing Individual Data Points in Federated Learning Hardened with Differential Privacy and Secure Aggregation** — Fowl et al., 2023. [Paper](https://doi.org/10.1109/SPW59333.2023.00021) | Malicious server uses Sybil devices to isolate an individual contribution despite secure aggregation and DP assumptions. | Add Sybil clients, minimum cohort-size violations, and colluding participants; measure isolation and reconstruction under secure aggregation. | P0 |

## C. Label, attribute, and property inference

| ID | Method / paper | Attacker and leakage | Proposed test | Priority |
|---|---|---|---|---|
| ATTR-01 | **Exploiting Unintended Feature Leakage in Collaborative Learning** — Melis et al., 2019. [Paper](https://www.usenix.org/conference/atc19/presentation/melis) | Infers properties of another participant’s local data from updates, including properties not needed for the task. | Train an attacker to infer cell line, tissue, disease state, perturbation class, or batch from site updates. | P0 |
| ATTR-02 | **Breaking Secure Aggregation: Label Leakage from Aggregated Gradients in Federated Learning** — 2024. [Paper](https://doi.org/10.1109/INFOCOM52122.2024.10621090) | Stealthy label inference designed to bypass secure aggregation. | Test whether aggregated updates still reveal rare labels or site-level label composition; vary number of clients and cohort size. | P0 |
| ATTR-03 | **An Efficient Gradient-Based Inference Attack for Federated Learning** — 2025. [Paper](https://arxiv.org/abs/2512.15143) | Attribute inference from temporal last-layer-gradient patterns. | Reuse the temporal attack for sensitive biological attributes and compare against one-round baselines. | P0 |
| ATTR-04 | **Alleviating Privacy Attacks via Causal Learning** — Tople et al., 2020. [Paper](https://proceedings.mlr.press/v119/tople20a.html) | Property/membership attacks exploit associational shortcuts; causal structure changes attack transferability. | Stress-test attacks across shifted site distributions and report whether biological confounders make leakage look smaller or larger than it is. | P1 |

## D. Record linkage and re-identification

| ID | Method / paper | Attacker and leakage | Proposed test | Priority |
|---|---|---|---|---|
| LINK-01 | **Record linkage / nearest-neighbor re-identification** — standard linkage threat; use public auxiliary data and held-out records. | Attacker matches a protected record or embedding to a known auxiliary record using distance, rank, or assignment. | Build auxiliary reference sets from held-out cell profiles, public expression data, or synthetic clinical records; report top-k linkage and uniqueness. | P0 |
| LINK-02 | **Beacon Reconstruction Attack: Reconstruction of genomes in genomic data-sharing beacons using summary statistics** — 2025. [Paper](https://pubmed.ncbi.nlm.nih.gov/40388204/) | Optimization using beacon responses, allele frequencies, and SNP correlations reconstructs participant genomes and enables downstream membership inference. | For aggregate/query interfaces, issue allowed summary queries and test reconstruction of sparse/high-dimensional biomedical profiles. | P0 / genomics-specific |
| LINK-03 | **Privacy-Preserving Record Linkage in the National COVID Cohort Collaborative** — 2024. | Linkage leakage arises from quasi-identifiers and repeated identifiers even when direct identifiers are removed. | Evaluate linkage using combinations of time, site, phenotype, and technical metadata; test k-anonymity and minimum-cohort policies. | P1 |
| LINK-04 | **Patient matching / de-identification linkage attacks** — use as an evaluation family rather than a single implementation. | Attacker combines quasi-identifiers and external auxiliary data to re-identify records. | Run linkage at increasing auxiliary-data strength and report re-identification risk separately from model attacks. | P0 |

## E. Aggregate, query, and repeated-release attacks

| ID | Method / paper | Attacker and leakage | Proposed test | Priority |
|---|---|---|---|---|
| AGG-01 | **Reconstruction attacks on aggregate genomic statistics** — Homer et al., 2008; formalized in later genomic privacy work. [Paper](https://doi.org/10.1038/ng.385) | Uses a target’s genotype plus reference-population statistics to infer whether they contributed to an aggregate study. | Test membership and allele/profile reconstruction from aggregate releases; include related individuals and population structure. | P0 / reference |
| AGG-02 | **Differencing attack** — canonical statistical disclosure attack. | Subtracts two permitted answers whose populations differ by one or a few records. | Generate overlapping and nested queries; search adaptively for isolating query pairs; report isolated-record rate and query count. | P0 |
| AGG-03 | **Small-cell and rare-category inference** — disclosure-control attack family. | Infers protected categories from counts, means, histograms, or ranked results when cohorts are small or rare. | Sweep cohort sizes, minimum thresholds, suppression, rounding, and repeated releases; measure rare-label inference. | P0 |
| AGG-04 | **Composition/repeated-release attack** — privacy-budget composition threat. | Combines many individually safe releases to amplify information about one record or site. | Maintain a release ledger, replay adaptive query sequences, and compare empirical leakage with declared privacy accounting. | P0 |

## F. Embedding and representation inversion

| ID | Method / paper | Attacker and leakage | Proposed test | Priority |
|---|---|---|---|---|
| EMB-01 | **An Inversion Attack Against Obfuscated Embedding Matrix in Language Model Inference** — Lin et al., EMNLP 2024. [Paper](https://aclanthology.org/2024.emnlp-main.126/) | Element-wise Differential Nearest Neighbor (EDNN) recovers inputs from obfuscated embeddings when the transformation preserves exploitable structure. | Apply learned and analytic inversion to gene, clinical-note, and multimodal embeddings; report nearest-record recovery, feature recovery, and sensitive-label inference. | P0 |
| EMB-02 | **Embedding inversion attack** — Qu et al., 2021. [Paper](https://arxiv.org/abs/2109.10554) | Trains an inverse map from leaked embeddings to original inputs using auxiliary paired data. | Train attacker on public/auxiliary paired embeddings; test cross-site and distribution-shifted inversion. | P1 / reference |
| EMB-03 | **Biologically-informed embedding leakage** — domain adaptation of EMB-01/02. | Even if exact records are not recovered, embeddings may preserve cell identity, disease, donor, or perturbation. | Train probes for every sensitive biological attribute and compare against raw-feature and random-embedding controls. | P0 |

## G. Split-learning and intermediate-activation attacks

| ID | Method / paper | Attacker and leakage | Proposed test | Priority |
|---|---|---|---|---|
| SPLIT-01 | **Functionality and Data Stealing by Pseudo-Client Attack** — 2024/2025. [Paper](https://doi.org/10.1109/TDSC.2024.3387396) | Semi-honest server reconstructs inputs and labels and learns the client-side functionality without knowing the client network structure. | If the architecture exposes intermediate activations, run pseudo-client training against non-IID biomedical sites. | P1 |
| SPLIT-02 | **Activation reconstruction / feature-space inversion** — modern split-learning attack family. | Intermediate representations reveal enough structure to recover inputs or sensitive attributes. | Evaluate inversion at every cut layer; include linear probes, generative inversion, and nearest-neighbor linkage. | P1 |

## H. Integrity attacks that can exfiltrate or corrupt data

These are not substitutes for confidentiality tests, but they matter if clients can
submit updates or data-derived models.

| ID | Method / paper | Attacker and leakage | Proposed test | Priority |
|---|---|---|---|---|
| INT-01 | **Backdoor attacks in single-cell pretrained models** — Feng et al., 2024. [Paper](https://www.nature.com/articles/s41421-024-00753-1) | Poisoned cells or models create hidden triggers that alter cell-type annotation while preserving clean performance. | Use biologically plausible triggers; report clean utility, attack success rate, trigger stealth, and downstream pathway corruption. | P2 |
| INT-02 | **Federated backdoor / model-poisoning attacks** — Bagdasaryan et al., 2020. [Paper](https://proceedings.mlr.press/v108/bagdasaryan20a.html) | Malicious client submits updates that implant targeted behavior while evading naive aggregation. | Evaluate robust aggregation, clipping, anomaly detection, and whether defenses create new privacy leakage. | P2 |

## Recommended first implementation set

The first working benchmark should implement these ten families:

1. MIA-01/MIA-02: black-box and white-box membership inference;
2. MIA-03: active membership inference;
3. INV-02: gradient inversion;
4. INV-05: model-weight inversion;
5. INV-07: realistic training-mode inversion;
6. INV-08: Sybil isolation against secure aggregation;
7. ATTR-01/ATTR-02: property and label inference;
8. LINK-01: auxiliary-data record linkage;
9. AGG-02/AGG-04: adaptive differencing and repeated-release composition;
10. EMB-01/EMB-03: embedding inversion and biological probing.

This set covers the platform’s likely surfaces: raw transformed records,
aggregate query results, embeddings, model weights, gradients, secure
aggregation, and multi-round interaction.

## Interpretation rules

1. Failure of an empirical attack does not prove privacy.
2. Success of an attack is evidence of leakage under the stated threat model;
   it must not be generalized beyond that access level.
3. Secure aggregation protects individual updates from the coordinator only if
   the minimum cohort and collusion assumptions hold.
4. Differential privacy must be reported with its accounting parameters
   `(epsilon, delta, sampling model, composition)` and not replaced by an
   empirical attack score.
5. Utility must be measured on the same workload used to measure leakage;
   otherwise the benchmark can reward a useless but “private” system.
