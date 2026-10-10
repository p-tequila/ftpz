# MDClone and Run: product and architecture comparison

_Reviewed October 2026. This analysis is based on public materials and does
not claim access to MDClone's private architecture, contracts, or roadmap._

## Executive conclusion

MDClone and Run address the same economic problem—valuable healthcare data is
difficult to use across organizational boundaries—but they make different
technical products.

**MDClone** is a healthcare-specific data and analytics platform. Its ADAMS
Platform organizes longitudinal clinical data, supports self-service cohort
exploration, and creates synthetic derivatives that can be analyzed or shared
more broadly. It also permits original-data analysis when the user's
permissions allow it. Its advantage is an established healthcare workflow:
data ingestion, semantic organization, cohort construction, exploration,
visualization, operational improvement, and a network of health-system data.

**Run** is an FHE-native governed-computation platform. A customer submits a
frozen program; data holders locally prepare and encrypt real records; Run
Engine executes the approved program over ciphertext; and data-holder
guardians release only the approved result to the customer. Run does not make
a synthetic copy available for open-ended exploration. Its advantage is a
cryptographic separation between access to source data and the right to run a
specific computation on that data.

The concise positioning is:

> MDClone lets a user explore a privacy-protected representation of healthcare
> data. Run lets a customer execute an approved computation against encrypted
> real data without disclosing the source records to Run or the customer.

This is not a claim that Run is categorically "more private." The systems
protect different objects and expose different outputs. MDClone's privacy
depends on the synthetic-data method, disclosure-risk review, permissions, and
deployment. Run's confidentiality depends on the FHE protocol, key custody,
implementation, metadata controls, and output-release policy. A released Run
model can still memorize or reveal information.

## What MDClone publicly offers

MDClone describes the ADAMS Platform as a self-service healthcare data
exploration environment. Its public product material identifies these core
capabilities:

- a healthcare-oriented, longitudinal data lake connected to source systems;
- ingestion of structured and unstructured clinical, operational, genomic,
  financial, social, and wearable data;
- semantic harmonization and healthcare-oriented natural-language processing;
- cohort definition and dynamic exploration without requiring database or
  programming expertise;
- analysis of synthetic or original data, according to permissions;
- integrated third-party analytics and AI-assisted exploration;
- operational workflows organized around Ask, Discover, Act, Measure, and
  Share; and
- controlled collaboration between health systems and external life-science
  organizations through an invite-in virtual environment.

MDClone states that its life-science platform is connected to more than 20
global sites, covers more than 30 years, and includes more than 50 million
unique patient records. These are vendor-reported figures, not independently
verified measurements.

Its central privacy mechanism for external collaboration is synthetic data.
MDClone describes a synthetic derivative as a new artificial population that
preserves useful statistical characteristics and correlations without
retaining a one-to-one mapping to real patients. Its platform also supports a
permissioned transition from synthetic exploration to validation on original
data.

Published evaluations provide evidence that this approach can be useful. A
2020 JAMIA Open study compared MDClone-generated derivatives with real data in
three use cases and reached statistically similar conclusions. A separate
five-study evaluation reported that synthetic analyses reproduced the main
conclusions of several observational studies. These results support synthetic
data as a valuable research and hypothesis-development tool; they do not imply
that every future dataset, rare cohort, feature interaction, or ML objective
will have equivalent fidelity.

## Side-by-side comparison

| Dimension | MDClone | Run |
|---|---|---|
| Primary product | Healthcare data platform and self-service analytics environment | Governed encrypted-computation platform and FHE runtime |
| Main abstraction | Cohort, longitudinal patient timeline, synthetic dataset, analysis workspace | Dataset contract, immutable program, ciphertext job, approved result |
| Privacy method | Synthetic derivatives, permissions, controlled workspaces, and governance | Fully homomorphic encryption, holder-controlled keys, signed manifests, and threshold result release |
| Data used by external computation | Usually a synthetic derivative or permissioned original-data environment | Ciphertexts encoding approved real-data tensors |
| User interaction | Dynamic and exploratory; users iteratively define cohorts and analyses | Deliberately constrained; a program is compiled, reviewed, signed, and then executed |
| Output | Synthetic patient-level data, analysis, cohort insight, workflow action, or permissioned original-data result | Named aggregate, encrypted computation result, or trained model released under policy |
| Computation model | Broad analytics and integrated tools over organized healthcare data | Only operations supported by the selected FHE backend and Run capability profile |
| AI/ML role | Explore data, build or validate models, and use synthetic data in AI workflows | Train or evaluate an approved model directly over encrypted real contributions |
| Cross-site model | Network and invite-in subscription around healthcare data environments | Customer-data-holder agreement plus independently controlled Run Nodes and key guardians |
| Operator visibility | Depends on deployment, permissions, and whether original or synthetic data is selected | Run Engine receives ciphertext, evaluation material, and metadata but no FHE secret key |
| Data-holder control | Source integration, platform permissions, project governance, and synthetic-data policy | Local preprocessing, contribution signature, guardian key share, and result-release approval |
| Customer access | Interactive access to the permitted environment or derivative | No source-data access; receives only the specifically approved result |
| Performance | Interactive analytics is a central product promise | FHE is materially slower and supports a narrower operation set |
| Domain scope | Deeply healthcare-specific | Intended to be cross-industry, with healthcare as an initial vertical |
| Maturity | Deployed commercial platform with named health-system customers | Architecture and POC-stage product direction |

## The central technical difference

### MDClone substitutes a privacy-reviewed representation

Synthetic data changes the artifact on which the external user works. The
synthetic population can support rapid, row-level exploration without exposing
the corresponding real patient rows. This is well suited to hypothesis
generation, education, cohort feasibility, workflow development, and analyses
whose important distributions and relationships survive synthesis.

The tradeoff is that privacy and fidelity must be evaluated for the generated
artifact. MDClone's own validation study observed that some outliers were
censored and maximum values were generally lower in its synthetic derivatives,
even when the tested conclusions remained statistically similar. Independent
research also shows that synthetic data does not automatically provide a
universal privacy guarantee: risk varies between full and partial synthesis,
and membership, attribute, and singling-out attacks must be tested. Stronger
formal privacy controls such as differential privacy can reduce utility.

Run should not imply that these findings invalidate MDClone. They identify the
cases in which computation over the original distribution may be preferable to
releasing a reusable approximation of it.

### Run keeps the real-data representation encrypted

Run changes the execution mechanism instead of substituting the dataset. The
approved computation operates on encrypted encodings of actual contributed
records. In the target design:

1. the customer and data holders directly sign the program, purpose, output,
   recipient, and release agreement;
2. data-holder guardians jointly establish the collaboration key;
3. holder-controlled Run Nodes preprocess and encrypt approved records;
4. Run Engine evaluates only the compiled FHE program;
5. Run cannot decrypt inputs, state, or output and cannot originate an accepted
   contribution without a data-holder signature; and
6. guardians release the exact approved result to the customer's separate
   recipient key.

This model is useful when the computation must use the real records and the
data holder is unwilling to expose either those records or a reusable
patient-level derivative. It is particularly relevant to joint model training,
rare-event calculations, proprietary scientific data, and computations whose
utility under synthesis has not been established.

The tradeoff is severe computational and product constraint. FHE requires
compilation, quantization, bounded shapes and ranges, a supported operation
set, significant execution cost, and a fixed release contract. Run cannot
initially match MDClone's fast, fluid, open-ended exploration experience.

## Privacy claims that Run should make carefully

Run should differentiate with precise guarantees rather than attack synthetic
data generally.

Safe claims:

- Source records are not disclosed to Run Engine or the model customer during
  an FHE job.
- Run does not require a patient-level synthetic dataset to be released to the
  customer.
- The customer receives only an output approved by the data-holder release
  policy.
- Computation uses encrypted encodings of contributed real records rather than
  records sampled from an estimated distribution.

Claims to avoid:

- "Synthetic data is insecure." Fully synthetic methods can substantially
  reduce disclosure risk and have demonstrated utility in real studies.
- "FHE solves privacy." It does not prevent metadata leakage, malicious local
  preprocessing, model memorization, membership inference from released
  outputs, or collusion at the configured guardian threshold.
- "The result is identical to plaintext computation." Quantization and
  FHE-compatible approximations can introduce error and must be benchmarked.
- "Run prevents anyone from encrypting." An FHE public encryption key is
  public by design. Run instead rejects contributions that lack an authorized
  data-holder signature.
- "Run replaces hospital data platforms." It does not initially provide
  MDClone's longitudinal data model, terminology layer, NLP, cohort interface,
  operational-change workflow, or installed network.

## Where MDClone is stronger

MDClone has important advantages that Run should treat as product lessons:

1. **Healthcare data readiness.** It starts with normalized longitudinal
   clinical information rather than tensors supplied to a computation engine.
2. **Exploration UX.** A clinician can refine questions and cohorts without
   writing or compiling an FHE program.
3. **Breadth of workflow.** Ask-to-discovery-to-operational-action is broader
   than encrypted execution.
4. **Time to insight.** Synthetic exploration can be interactive; general FHE
   training can take hours or longer.
5. **Installed network and credibility.** MDClone reports production health
   systems, life-science collaborations, and tens of millions of records.
6. **Organizational operating model.** The ADAMS Center includes adoption,
   governance, measurement, and clinical-change practices—not just software.

Run should not spend its first product cycles rebuilding these capabilities.
Its defensible entry point is a computation that existing synthetic-data and
analytics platforms cannot satisfy under the required fidelity or custody
terms.

## Where Run can be meaningfully different

1. **Training on encrypted real contributions.** Run targets gradients, model
   state, and optimizer updates under encryption rather than training only on a
   synthetic export or moving raw records into a buyer-controlled environment.
2. **Program-level rights.** The commercial object is the right to execute one
   versioned program and receive one output class, not general access to a data
   environment.
3. **Cryptographic separation of duties.** Data holders keep collaboration-key
   shares; Run coordinates but cannot decrypt or approve; the customer holds a
   separate recipient key.
4. **General computation substrate.** The same protocol can eventually support
   non-healthcare workloads, including defense, financial, biological, and
   industrial data.
5. **Compute-linked marketplace.** Run Exchange can meter both the data-use
   right and the serverless encrypted computation required to exercise it.
6. **No reusable row-level artifact by default.** The customer receives a
   model or bounded result, not a synthetic patient table that can be queried
   indefinitely outside the original release decision.

These advantages are conditional on proving backend interoperability,
numerical utility, threshold-key security, acceptable performance, and strong
output governance.

## Competitive and partnership strategy

The strongest near-term strategy is not to position Run as an ADAMS clone.
Run should own the final high-assurance computation step.

### Recommended wedge

Target projects with all of these characteristics:

- two or more institutions hold complementary data;
- the buyer needs a trained model, validation metric, or bounded analysis—not
  unrestricted patient-level exploration;
- the result must be derived from actual records because synthetic fidelity is
  uncertain or contractually unacceptable;
- records cannot be centralized in the buyer's or Run's environment; and
- the expected scientific or commercial value justifies FHE cost and latency.

Examples include rare-disease models, multi-hospital risk models, treatment
response models, model validation across institutions, and sensitive biomarker
or omics computations.

### Complementary workflow

MDClone-like synthetic platforms and Run can form a useful two-stage workflow:

1. researchers use a synthetic environment to discover cohorts, develop code,
   estimate feasibility, and debug the analysis;
2. the final data contract and program are frozen and approved;
3. Run Nodes execute that program over encrypted real records at each holder;
4. guardians release only the final validated result; and
5. discrepancies between synthetic and real-data execution become part of the
   study report.

A future Run Node connector could read an institution's ADAMS Data Lake or an
approved cohort export locally. This would make MDClone a source-system and
discovery partner rather than requiring Run to duplicate healthcare ingestion
and semantic harmonization.

## Product implications for Run

1. **Lead with encrypted execution, not another data lake.** Connect to FHIR,
   OMOP, warehouses, and established platforms instead of initially replacing
   them.
2. **Support a synthetic-development mode.** Let customers build and simulate a
   workload on public or synthetic data before submitting its digest for
   holder approval and real FHE execution.
3. **Produce a fidelity delta report.** When a synthetic development dataset is
   available, compare synthetic simulation, holder-local clear validation, FHE
   simulation, and encrypted execution.
4. **Make program rights legible.** The UI should show the exact data fields,
   transformations, model, output, recipient, run count, expiry, and price that
   both sides sign.
5. **Keep release narrow.** Models and aggregates should have minimum-cohort,
   repeated-release, extraction, and membership-inference controls.
6. **Price the scarce outcome.** Monetize the right to compute against
   inaccessible real data plus metered FHE execution, rather than charging only
   for generic analytics seats.
7. **Measure the right comparison.** The POC should compare a customer model
   trained on its accessible subset with a Run model trained on all encrypted
   contributions, while also reporting an all-data plaintext upper bound and
   FHE simulation result.

## Bottom line

MDClone validates the business premise that hospitals and life-science
companies will pay for governed access to otherwise difficult healthcare data.
It also sets a high bar for clinical data organization, usability, and
institutional adoption.

Run is differentiated only if it proves a narrower but harder proposition:
multiple holders can execute an approved model-training or computation job on
real data, under holder-controlled keys, without giving Run or the customer
access to the records. Run should treat MDClone as a strong adjacent incumbent,
a source of product lessons, and a potential discovery/data-layer integration—not
as evidence that synthetic data and FHE are interchangeable.

## Sources

### MDClone public materials

- [MDClone home and ADAMS overview](https://mdclone.com/)
- [ADAMS Platform brief](https://www.mdclone.com/wp-content/uploads/2024/02/MDClone_ADAMS_Platform.pdf)
- [MDClone synthetic-data workflow](https://mdclone.com/services/synthetic-data/)
- [MDClone life-sciences offering](https://mdclone.com/services/life-sciences/)
- [ADAMS Center and Data Lake model](https://mdclone.com/services/adamscenterexperience/)

### Research

- [Foraker et al., “Spot the difference: comparing results of analyses from
  real patient data and synthetic derivatives,” JAMIA Open
  (2020)](https://pmc.ncbi.nlm.nih.gov/articles/PMC7886551/)
- [Benaim et al., “Analyzing Medical Research Results Based on Synthetic Data
  and Their Relation to Real Data Results,” JMIR Medical Informatics
  (2020)](https://pmc.ncbi.nlm.nih.gov/articles/PMC7059086/)
- [Zhang et al., “Membership Inference Attacks Against Synthetic Health Data,”
  Journal of Biomedical Informatics
  (2022)](https://pmc.ncbi.nlm.nih.gov/articles/PMC8766950/)
- [Kaabachi et al., “A scoping review of privacy and utility metrics in medical
  synthetic data,” npj Digital Medicine
  (2025)](https://www.nature.com/articles/s41746-024-01359-3)
