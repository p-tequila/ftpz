# Adversarial testing

This directory defines the red-team benchmark for `nftpz`: a platform for
computing over sensitive biomedical data without unnecessarily exposing the
underlying records.

The benchmark does **not** treat “the data were shuffled” or “the data stayed
at the client” as a privacy guarantee. Each protection mechanism must be
tested against an attacker with an explicit access level, auxiliary knowledge,
and query budget.

The catalog in [`attack-catalog.md`](attack-catalog.md) is the source of truth
for the attacks and papers that the benchmark will implement or adapt.

The executable subset and exact limitations are tracked in
[`implemented-methods.md`](implemented-methods.md). The running platform uses
Concrete ML encrypted cloud training, not hospital-side training or plaintext
gradient sharing. Gradient attacks in the broader catalog are positive controls
or future-protocol tests; a missing plaintext-gradient surface is not an
empirical cryptographic-security result. Released models/counts and visible
site/schedule metadata remain relevant attack surfaces.

## Security claim under test

For each mechanism and workload, measure the joint frontier:

```text
scientific utility  <->  attacker success  <->  latency / bandwidth / cost
```

The system should report attack success rather than a binary “private” label.
Formal differential-privacy guarantees, when present, must be reported
separately from empirical attack resistance.

## Risk categories

Every attack in the catalog is tagged against these three product risks. An
attack surface (for example, gradients or query results) is not itself a risk
category: it is the channel through which the risk may be exposed.

| Code | Risk category | What must remain hidden |
|---|---|---|
| **IND** | Individual privacy | Record membership, identity, genotype/expression, diagnosis, treatment, outcome, or other person/sample-level facts |
| **BIO** | Biological privacy | Cell line, tissue, disease state, perturbation, responder status, ancestry, phenotype, pathway, or other sensitive biological property |
| **ORG** | Institutional/business privacy | Site identity, cohort existence/size, proprietary study or compound, experimental program, site-specific result, batch, or research activity |

An attack may have multiple tags. For example, genomic reconstruction is
`IND + BIO`, while site attribution is usually `ORG + BIO`.

## Threat-model matrix

| Attacker | Observes | May do | Priority |
|---|---|---|---|
| External observer | public outputs, released aggregates, embeddings | issue repeated queries; use public auxiliary data | P0 |
| Curious coordinator | client updates, model weights, metadata, timing | correlate rounds; train shadow models; choose targets | P0 |
| Malicious coordinator | protocol messages and client responses | send tailored models/queries; isolate clients; use Sybil clients | P0 |
| Curious participant | global model, public outputs, its own records | probe inference API; infer other sites | P1 |
| Colluding sites | their own records plus protocol transcript | subtract their contributions; attack residuals | P1 |
| Compromised storage/query layer | encrypted or transformed payloads, indexes, logs | offline inversion/linkage; exploit metadata | P1 |
| Malicious data owner | own training data and submitted updates | poison data/model; insert triggers; exfiltrate via outputs | P2 |

## Required reporting fields

Every attack implementation should record:

- attack ID and paper/method name;
- attacker role and access level;
- auxiliary-data assumptions;
- target type: record, site, membership, label, attribute, ranking, or model;
- risk category tags: `IND`, `BIO`, and/or `ORG`;
- query/update budget;
- attack success and confidence interval;
- utility of the protected workload;
- compute, communication, and wall-clock cost;
- whether the attack is adaptive, active, colluding, or multi-round;
- reproducibility seed and exact configuration.

## Metrics

### Confidentiality

- membership-inference ROC-AUC, PR-AUC, advantage, and TPR at fixed FPR;
- origin/site attribution accuracy and macro-F1;
- record-linkage precision, recall, F1, top-k hit rate, and re-identification rate;
- attribute/property inference accuracy, macro-F1, and calibrated log loss;
- reconstruction MSE, cosine similarity, Pearson correlation, SSIM where relevant,
  feature recovery rate, and exact/near-exact recovery rate;
- biological leakage: cell-line/tissue/disease/perturbation inference,
  pathway recovery, and sensitive-label inference;
- aggregate reconstruction error and the fraction of individuals or small
  cohorts isolated by differencing.

### Utility and system cost

- query-answer error versus a centralized oracle;
- rank correlation, Recall@k, nDCG, differential-expression overlap, pathway
  enrichment overlap, AUROC/AUPRC, calibration, ARI/NMI;
- latency, bandwidth, number of rounds, memory, CPU/GPU time, and cryptographic
  overhead;
- robustness under non-IID sites, small cohorts, client dropouts, and repeated
  releases.

## Implementation order

1. P0 passive attacks against released query results and transformed records.
2. P0 coordinator attacks against federated updates and model weights.
3. P0 active attacks: tailored queries, malicious model updates, and Sybil
   isolation.
4. P1 attacks against embeddings, indexes, metadata, and repeated releases.
5. P2 poisoning and backdoor attacks for platform integrity.

All experiments must use synthetic, public, or explicitly authorized data.
