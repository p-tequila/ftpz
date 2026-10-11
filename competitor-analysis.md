# Run competitor analysis

_Reviewed October 2026. This analysis is based on public materials and does
not claim access to any competitor's private architecture, contracts, customer
results, or roadmap._

## Executive conclusion

Run sits at the intersection of three existing product categories:

**MDClone** is a healthcare-specific data and analytics platform. Its ADAMS
Platform organizes longitudinal clinical data, supports self-service cohort
exploration, and creates synthetic derivatives that can be analyzed or shared
more broadly. It also permits original-data analysis when the user's
permissions allow it. Its advantage is an established healthcare workflow:
data ingestion, semantic organization, cohort construction, exploration,
visualization, operational improvement, and a network of health-system data.

**LatticaAI** is an accelerated FHE-as-a-service platform. Its public product
surface centers on deploying a model or workload, letting an end user encrypt a
query locally, evaluating that query on a GPU-backed worker, returning an
encrypted response, and letting the end user decrypt it. Its website also
positions the runtime for encrypted database predicates, similarity search,
and analytics. Lattica is the closest technical competitor to Run Engine, but
its publicly documented workflow is inference- and query-oriented rather than
multi-data-holder model training.

**Run** is an FHE-native governed-computation platform. A customer submits a
frozen program; data holders locally prepare and encrypt real records; Run
Engine executes the approved program over ciphertext; and data-holder
guardians release only the approved result to the customer. Run does not make
a synthetic copy available for open-ended exploration. Its advantage is a
cryptographic separation between access to source data and the right to run a
specific computation on that data.

The concise positioning is therefore:

> MDClone lets a user explore a privacy-protected representation of healthcare
> data. Lattica lets an end user privately query a deployed model or encrypted
> workload. Run is intended to let multiple data holders jointly train or
> execute an approved program on encrypted real data and release only the
> agreed result.

This is not a claim that Run is categorically "more private." The systems
protect different objects and expose different outputs. MDClone's privacy
depends on the synthetic-data method, disclosure-risk review, permissions, and
deployment. Lattica and Run both depend on FHE parameters, implementation, key
custody, metadata controls, and output handling. A released inference answer,
query result, or trained model can still reveal sensitive information.

Run does not have an uncontested category. Duality publicly offers secure
querying, federated analytics, and collaborative model training using a mix of
HE, MPC, federated learning, differential privacy, and TEEs. Enveil offers
cross-silo encrypted search, analytics, and machine learning. Sherpa.ai offers
multi-party federated training, while Opaque offers confidential AI using
hardware-isolated execution. Run's differentiation must therefore come from
the complete product combination—not merely from using FHE:

- FHE-compatible autograd and optimizer execution, not only inference;
- direct customer-data-holder agreements and program-level usage rights;
- data-holder-controlled collaboration keys and recipient-specific release;
- a two-sided data-access marketplace; and
- metered serverless encrypted computation.

## Competitive landscape

| Category | Representative companies/projects | Primary buyer need | Relationship to Run |
|---|---|---|---|
| Synthetic healthcare data and self-service analytics | MDClone | Explore cohorts and share useful healthcare derivatives quickly | Commercial workflow competitor and potential upstream discovery/data partner |
| Accelerated FHE inference and querying | LatticaAI | Serve models and queries without exposing the end user's input or output | Closest Run Engine competitor; potential infrastructure supplier if its runtime becomes sufficiently general |
| Multi-PET data collaboration | Duality Technologies | Query, analyze, or train across organizations using the best available PET | Broadest direct product competitor to Run's collaboration plane |
| Encrypted search and cross-silo analytics | Enveil | Search, cross-match, analyze, and use AI without exposing the query or source data | Strong competitor for government, finance, and operational analytics |
| Federated model training | Sherpa.ai | Train across data silos while records remain behind each firewall | Direct substitute for multi-holder training where federated learning is acceptable |
| Confidential-computing AI | Opaque and other TEE platforms | Run general AI workloads with hardware isolation and attestation | Faster, more general architectural substitute with a hardware trust assumption |
| FHE libraries and compilers | Zama Concrete/TFHE-rs, OpenFHE, Lattigo | Build encrypted applications and runtimes | Suppliers, build-versus-buy alternatives, and potential future platform competitors |

This market map reflects publicly described products, not verified private
capabilities. Several companies use multiple PETs, and their boundaries can
change quickly.

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

## What LatticaAI publicly offers

Lattica describes itself as an FHE-as-a-service platform built around an
accelerated compiler and runtime. Its documented actors and flow are:

1. an **AI provider** uploads and manages a model, access tokens, worker
   capacity, and prepaid compute credits;
2. Lattica converts the model into a homomorphic-ready pipeline;
3. an **end user** generates a secret key and evaluation key locally;
4. the end user uploads the evaluation key and submits encrypted queries;
5. a Lattica worker evaluates the deployed model and returns an encrypted
   response; and
6. the end user decrypts the response locally.

The public SDK supports Python and JavaScript query clients. Lattica's
open-source client core includes CKKS, RBGV, and GSW-like components, while the
remote backend performs the actual homomorphic evaluation. Lattica markets its
HEAL layer as a hardware abstraction that lowers CKKS and BGV primitives into
tensor operations for GPUs and, eventually, other accelerators. Its public
materials emphasize AI inference, SQL predicates, similarity search, vector
queries, and analytics. It meters active worker time using credits and allows
multiple workers to serve one deployed model.

Lattica's terms state that the platform is currently beta and that customers
or end users exclusively hold their keys. Its documentation does not currently
describe:

- encrypted backpropagation, autograd, optimizer-state updates, or model
  training as a product workflow;
- several independent data holders encrypting into one collaboration key;
- a customer-data-holder agreement and data-rights marketplace;
- distributed key generation among holder guardians;
- threshold approval of one exact result; or
- recipient-specific release that prevents the result customer from holding
  the input-data decryption key.

These are observations about the public product, not claims about Lattica's
private roadmap. Its compiler, accelerator support, and runtime make expansion
into broader encrypted computation a credible competitive risk.

## Core comparison

| Dimension | MDClone | LatticaAI | Run |
|---|---|---|---|
| Primary product | Healthcare data platform and self-service analytics environment | Accelerated FHE-as-a-service for encrypted model and query serving | Governed encrypted-computation and data-access platform |
| Main abstraction | Cohort, longitudinal patient timeline, synthetic dataset, analysis workspace | Deployed model, end-user token, encrypted query, worker | Dataset contract, immutable program, multi-holder ciphertext job, approved result |
| Privacy method | Synthetic derivatives, permissions, controlled workspaces, and governance | Client-held FHE key and encrypted request/response execution | FHE collaboration key, signed manifests, holder guardians, and recipient-specific threshold release |
| Data used by computation | Synthetic derivative or permissioned original-data environment | Encrypted end-user query or input sent to a deployed workload | Ciphertexts encoding real contributions from multiple holders |
| Primary computation | Interactive cohort exploration and analytics | Inference, predicates, similarity/vector search, and query processing | Training and bounded general computation, with inference also possible |
| ML lifecycle | Explore data, build or validate models, and use synthetic data in AI workflows | Deploy a prepared model and serve encrypted inference | Compile forward/backward graphs, train encrypted state, release and export a model |
| Key owner | Depends on deployment and permission model | End user holds the secret key for its request and response | Data-holder guardians control the collaboration key; customer holds a separate recipient key |
| Multi-holder governance | Healthcare network, institutional agreements, workspace permissions | AI provider manages end-user model access tokens | Customer and holders directly sign program rights; holders approve exact result release |
| Operator visibility | Depends on deployment and whether original or synthetic data is selected | Backend receives model, evaluation material, encrypted queries, and metadata but not the end-user secret key | Run receives compiled work, evaluation material, ciphertext, and metadata but no complete input or recipient secret |
| User interaction | Dynamic and exploratory | Repeated encrypted queries to a deployed model | Deliberately constrained, versioned jobs approved before execution |
| Output | Synthetic data, cohort insight, analysis, workflow action, or permissioned original-data result | Encrypted inference or query response decryptable by the end user | Named aggregate, computation result, or trained model released to the approved customer |
| Monetization | Platform/network subscription and healthcare collaboration | Prepaid credits and metered active worker time | Data-access rights, metered serverless FHE computation, and enterprise governance |
| Domain scope | Healthcare-specific | Cross-industry encrypted AI and querying | Cross-industry, initially focused on healthcare and other high-value collaborations |
| Public maturity | Deployed commercial platform with named health-system customers | Beta platform with public SDK, documentation, demos, and benchmark work | Architecture and POC-stage product direction |

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

### Lattica keeps each inference query encrypted

Lattica changes the serving mechanism. The model provider deploys a prepared
model, and each end user encrypts a query under its own client key. The FHE
worker executes the model or predicate without learning the query or response.
This is a strong fit for private model APIs, medical inference, fraud scoring,
encrypted similarity search, private vector lookup, and bounded database
queries.

This design solves a different lifecycle stage from Run's initial wedge. The
model already exists, one request owner controls the request key, and the
service returns a response to that same end user. The hard product problems are
model compilation, low-latency serving, accelerator utilization, batching,
access tokens, and metered worker capacity.

Run's target collaboration begins before a shared model exists. Several data
holders must approve one training program, contribute encrypted batches,
maintain encrypted model and optimizer state across many steps, and authorize
release to a separate customer. That adds expensive circuits plus governance,
distributed key management, provenance, checkpointing, and output-control
requirements absent from a conventional encrypted inference call.

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
- "Lattica only does inference." Its publicly documented product currently
  centers on inference and querying, but its compiler and accelerated FHE
  runtime may support or expand toward broader workloads.
- "Run has a faster FHE engine." That must be established with reproducible,
  workload-level benchmarks. Lattica explicitly competes on acceleration and
  publishes inference and vector-search benchmark work.

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

## Where LatticaAI is stronger

Lattica has several advantages that are directly relevant to Run Engine:

1. **Narrow production surface.** Model deployment and encrypted querying are
   easier to productize and benchmark than a full encrypted training lifecycle.
2. **Acceleration-first architecture.** HEAL, GPU workers, batching, and a
   hardware-abstraction story are central to the product rather than roadmap
   items.
3. **Working provider/end-user DX.** The platform documents model onboarding,
   tokens, Python and JavaScript query clients, local key generation, workers,
   credits, monitoring, and decryption.
4. **Metered FHE operations.** Prepaid credits and worker-runtime billing make
   the serverless encrypted-compute model concrete.
5. **Open client core.** Public client cryptography makes the local key and
   request path more inspectable and lowers integration friction.
6. **Clear initial use cases.** Private inference, image processing, similarity
   search, and predicates are easier for buyers to understand than a general
   encrypted-computation platform.

Run should assume that Lattica can move up-stack from encrypted serving toward
general computation. Run cannot rely on "we use FHE" as differentiation.

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

### Competitive priority

| Competitor | Current overlap | Strategic threat | Run response |
|---|---|---|---|
| Duality | Multi-party governance, secure query, analytics, and collaborative ML | Highest full-platform overlap | Differentiate on FHE-native training DX, transparent program rights, exchange liquidity, and reproducible performance |
| LatticaAI | FHE compiler, runtime, acceleration, SDK, and metered cloud execution | Highest Run Engine overlap; can expand from inference into training | Benchmark honestly, consider runtime partnership, and own multi-holder training and release governance |
| Sherpa.ai | Multi-holder model training and regulated-industry sales | Federated learning is cheaper and more mature for many training jobs | Target workloads where exposing local updates or trusting aggregation is unacceptable; quantify the added cost |
| MDClone | Healthcare data access, buyer workflows, and institutional network | Can satisfy many healthcare projects without expensive FHE | Integrate as a discovery/source layer and focus on real-data computations that synthesis cannot validate |
| Enveil | Encrypted search, analytics, cross-silo workflows, government and finance | Strong enterprise credibility in Run's target verticals | Avoid generic encrypted-search positioning; lead with training, marketplace economics, and holder-governed result release |
| Opaque/TEE platforms | General confidential AI with much lower computational friction | Buyers may accept hardware trust in exchange for model breadth and speed | State the trust-model difference precisely and reserve FHE for cases where hardware/operator trust is unacceptable |

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

### LatticaAI partnership or competition

Lattica could be either a runtime supplier or a direct engine competitor. A
partnership is plausible only if its backend can expose the primitives Run
needs: long-lived encrypted state, training graph composition, deterministic
checkpointing, multi-holder-compatible encryption, maliciously secure
threshold key generation, and recipient-specific release. Its current
single-query client/server flow does not establish those properties.

Run should define a backend interface and test Lattica against it rather than
coupling product identity to one cryptographic implementation. If Lattica can
execute Run's compiled training circuit under the required key protocol, Run
could buy acceleration and focus on the exchange, collaboration workflow, and
training compiler. If it cannot, Run Engine needs an independent backend. In
either case, Run should publish comparable workload-level numbers for latency,
throughput, memory, ciphertext size, precision, and total job cost.

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
8. **Treat Run Engine as a replaceable backend boundary.** Preserve the option
   to use Concrete/TFHE-rs, Lattica, OpenFHE, or another runtime when it meets
   Run's key and execution contracts.
9. **Prototype the inference path too.** Training is the differentiation, but
   ordinary encrypted inference is needed to validate exported models and
   prevents Lattica from owning the entire post-training lifecycle.
10. **Make governance the durable moat.** Compiler and runtime performance can
    be matched or purchased. Signed data rights, holder onboarding, threshold
    release, audit evidence, marketplace liquidity, and repeatable regulated
    workflows are harder to copy as one feature.

## Bottom line

MDClone validates the business premise that hospitals and life-science
companies will pay for governed access to otherwise difficult healthcare data.
Lattica validates the shape of an accelerated, metered FHE cloud product with
client-held keys. Duality, Enveil, Sherpa.ai, and confidential-computing
platforms demonstrate that buyers have several ways to collaborate on
sensitive data without adopting Run's exact architecture.

Run is differentiated only if it proves a narrower but harder proposition:
multiple holders can execute an approved model-training or computation job on
real data, under holder-controlled keys, without giving Run or the customer
access to the records. Its moat must combine training-specific compiler
capability, two-sided data rights, distributed key governance, narrow output
release, and serverless execution. FHE alone is not a company-level
differentiator.

## Sources

### MDClone public materials

- [MDClone home and ADAMS overview](https://mdclone.com/)
- [ADAMS Platform brief](https://www.mdclone.com/wp-content/uploads/2024/02/MDClone_ADAMS_Platform.pdf)
- [MDClone synthetic-data workflow](https://mdclone.com/services/synthetic-data/)
- [MDClone life-sciences offering](https://mdclone.com/services/life-sciences/)
- [ADAMS Center and Data Lake model](https://mdclone.com/services/adamscenterexperience/)

### LatticaAI public materials

- [LatticaAI platform](https://lattica.ai/)
- [LatticaAI FHE and acceleration architecture](https://lattica.ai/fhe)
- [LatticaAI architecture overview](https://platformdocs.lattica.ai/architecture-overview)
- [LatticaAI secure-query workflow](https://platformdocs.lattica.ai/how-to-guides/secure-query-processing)
- [Lattica FHE client core](https://github.com/Lattica-ai/lattica_fhe_core)
- [LatticaAI platform terms](https://lattica.ai/terms-of-use)

### Other competitor materials

- [Duality privacy-preserving data collaboration platform](https://dualitytech.com/platform/)
- [Enveil privacy-enhancing technology platform](https://www.enveil.com/)
- [Sherpa.ai federated learning platform](https://sherpa.ai/)
- [Opaque confidential AI platform](https://www.opaque.co/)

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
