# Run business case

## Investment thesis

The highest-value data for AI is often the data that cannot be copied into an
AI company's cloud account: longitudinal hospital records, proprietary
biological experiments, defense telemetry, production workflows, customer
interactions, and expert decisions. Contracts, regulation, national-security
rules, competitive sensitivity, and breach risk prevent these datasets from
being pooled even when all parties would benefit from a joint model or analysis.

**Run** makes those datasets computable without making them transferable. Data
owners keep plaintext inside their infrastructure, approve a specific program
and output policy, and allow an approved privacy-preserving execution path. In
the strongest target trust model, Run Nodes encrypt the inputs and an FHE
service computes directly on ciphertext. The buyer receives only the
authorized result or trained model.

The company combines two economic engines:

1. **Run Exchange:** buyers pay for the right to run an approved workload
   against otherwise inaccessible data. Data providers earn revenue without
   delivering raw records.
2. **Run Engine:** every approved access request consumes metered compilation,
   CPU/GPU FHE execution, encrypted storage, and transfer.

Enterprise governance subscriptions, dedicated deployments, and support are a
third recurring layer. The result is a two-sided data network attached to a
usage-based infrastructure business.

Run does not depend on licensing a novel cryptographic algorithm. The durable
commercial asset is the network and transaction layer: discover supply,
specify a computation right, negotiate terms, meter execution, govern release,
settle payment, and compensate providers. Run Engine is a fulfillment layer.
It should support interchangeable FHE or other privacy backends when they meet
the signed security and output contract. Algorithm improvements reduce cost of
goods; they are not the primary unit sold.

## The problem

### AI demand is constrained by access, not only by model architecture

Organizations can often identify the data needed to improve a model but cannot
obtain legal, security, or commercial approval to centralize it. This produces:

- models trained on one institution or a narrow convenience sample;
- slow bilateral data-license negotiations and bespoke integrations;
- de-identification that removes useful signal without eliminating all risk;
- fragmented analytics that cannot measure population-level effects;
- federated systems that still expose updates, require online coordination,
  and do not govern the final model or repeated outputs;
- clean-room projects tied to one cloud, hardware trust model, or narrow query
  interface.

The cost is not merely infrastructure spend. It is the opportunity cost of
clinical studies that recruit slowly, models that fail on new populations,
defense systems trained on incomplete observations, and AI products that lack
real domain data.

### Data owners lack a controlled way to monetize useful data

Hospitals, laboratories, enterprises, and public-sector organizations hold
valuable data but usually face a binary choice: refuse access or negotiate a
copy under a complex data-use agreement. The copy creates ongoing loss of
control, breach exposure, and uncertainty about secondary use.

Run changes the object being sold. The provider licenses a narrow right to
compute:

- named data categories;
- one immutable program;
- one purpose and recipient;
- bounded runs or time period;
- an explicit output type and release policy;
- no right to possess or reuse the underlying records.

The data remains in the provider's environment until locally transformed and
encrypted. The remote executor cannot decrypt it.

## Product

Run is an FHE-native collaboration and execution platform, not a raw-data
broker and not only a cryptography SDK.

The public product family has four parts:

1. **Run** is the complete collaboration and encrypted-compute platform.
2. **Run Engine** is the FHE compiler and runtime.
3. **Run Exchange** is the governed data-access marketplace.
4. **Run Nodes** are participant-hosted data-plane agents, normally controlled
   by the data holder whose records they process.

The OSS repository, Python package, and CLI retain the technical name `nftpz`.

### For computation buyers

- Discover datasets through non-sensitive catalog metadata.
- Publish a typed data contract and Python/PyTorch workload.
- Test in clear mode and FHE simulation.
- Receive compatibility, precision, latency, and cost estimates before buying.
- Invite data providers and negotiate output rights.
- Execute the approved program as a serverless encrypted job.
- Receive the authorized aggregate, model, embedding, or evaluation artifact.

### For data providers

- Deploy Run Nodes to connect existing systems without moving plaintext to the
  vendor.
- Implement the local mapping into the buyer's contract.
- Review requested fields, program digest, participants, output, recipient,
  retention, and compensation.
- Enforce consent, purpose, cohort, and institutional policy locally.
- Encrypt and upload only approved batches.
- Approve or reject final result release.
- Receive payment and a complete audit trail.

### For security, legal, and governance teams

- Immutable workload and schema versions.
- Explicit data-use and release policies.
- A directly signed customer-data-holder agreement; Run manages the workflow
  but cannot replace either side's consent.
- Organization-controlled key custody.
- Multi-party approvals and revocation.
- Retention, deletion, and incident-response controls.
- Evidence showing exactly which code ran against which committed inputs.

The current technical proof is encrypted simple-regression training using
Concrete ML. The product roadmap expands from that proof to encrypted analytics,
small neural networks, FHE-compatible autograd and optimizers, GPU workers, and
hybrid large-model adaptation. Broad computation and general AI training are
the north star, with a public certified/preview/research capability matrix.

## Why now

### The data market is becoming an explicit part of the AI economy

[Mercor describes itself](https://www.mercor.space/mission/) as a layer between
human expertise and frontier models. Its enterprise offering now explicitly
includes opt-in
[data monetization](https://www.mercor.space/enterprise/): identifying data
valuable to AI labs and managing preparation, sourcing, and licensing while
the enterprise controls what is licensed.

That model demonstrates willingness on both sides of a marketplace: AI labs
pay for scarce, domain-specific training signal, and knowledge holders expect
to be compensated. Run Exchange applies the same economic pattern to
institutional datasets that are too regulated or sensitive to transfer.
Mercor organizes experts and licensable data; Run organizes permissioned
computation over data that remains encrypted and under provider control.

### Cloud vendors have validated confidential collaboration as a category

- [AWS Clean Rooms ML](https://docs.aws.amazon.com/clean-rooms/latest/userguide/machine-learning.html)
  allows multiple parties to contribute data to approved custom ML workflows.
- [Azure Confidential Clean Rooms](https://learn.microsoft.com/en-us/azure/confidential-computing/confidential-clean-rooms)
  describes multi-party analytics and ML with code approval, output controls,
  audit, and confidential-computing enclaves.
- [Google Confidential Space](https://docs.cloud.google.com/docs/security/confidential-space)
  targets collaborations where parties do not trust each other or the workload
  operator.

These products validate the buyer, workflow, and governance need. Run
differentiates through FHE: the execution service operates on ciphertext rather
than making plaintext available inside a hardware-protected environment.

### FHE is becoming deployable infrastructure

Concrete supports client/server circuit artifacts and CPU/GPU execution.
[Concrete ML documents GPU acceleration](https://docs.zama.org/concrete-ml/guides/using_gpu)
and [hybrid encrypted LoRA fine-tuning](https://docs.zama.org/concrete-ml/llms/lora_training).
OpenFHE supports multiple schemes and threshold extensions. This does not make
arbitrary encrypted AI training cheap, but it is enough to productize bounded
analytics, quantized ML, and selected hybrid workloads now.

### Regulation is pushing toward governed secondary use

The European Commission describes the
[European Health Data Space](https://health.ec.europa.eu/ehealth-digital-health-and-care/reuse-health-data_en)
as a framework for secure secondary use of health data for research,
innovation, policy, and personalized medicine, with authorization, secure
processing, minimization, and governance requirements.

FHE can reduce who can view data during computation, but it is not a regulatory
exemption. [HHS cloud guidance](https://www.hhs.gov/hipaa/for-professionals/special-topics/health-information-technology/cloud-computing/index.html)
states that a provider maintaining encrypted ePHI remains a business associate
even when it lacks the key. Run should sell reduced exposure and stronger
technical control, not automatic compliance.

## Priority markets and use cases

The platform is horizontal. Go-to-market uses vertical solution packages with
repeatable contracts, connectors, workload templates, and proof metrics.

### Healthcare and biopharma

**Participants:** hospitals, health systems, clinical research networks,
biopharma sponsors, medical-device companies, and research institutes.

**Use cases:**

- multi-hospital risk and outcome models;
- trial-feasibility and eligible-cohort analytics;
- rare-disease research across institutions;
- post-market safety and treatment-effect analysis;
- biological and omics model training;
- cross-site model validation and bias analysis.

**Commercial transaction:** the sponsor pays participating institutions for
approved computational access and pays Run for marketplace coordination,
governance, and encrypted compute. The approved output might be a trained model
or aggregate report; patient-level data is never a deliverable.

**Buyer:** head of data partnerships, clinical development, translational
medicine, R&D data science, or external innovation.

**Provider approvers:** privacy office, research governance, security, legal,
institutional review, and data steward.

### Defense and public sector

**Participants:** agencies, commands, coalition partners, defense primes,
subcontractors, and operators of critical infrastructure.

**Use cases:**

- cross-organization anomaly and threat detection;
- joint logistics and readiness analytics;
- supplier-risk models;
- telemetry analysis across organizational boundaries;
- evaluation or training where each organization protects its observations.

The launch target is unclassified and CUI-like data. Systems that process CUI
must be designed against requirements such as
[NIST SP 800-171 Rev. 3](https://csrc.nist.gov/pubs/sp/800/171/r3/final).
Classified use, CMMC claims, and FedRAMP claims remain out of scope until the
specific deployment and operating organization are assessed.

This segment may use internal chargeback or contract-level access rights rather
than an open marketplace. Revenue is weighted toward sovereign licensing,
dedicated capacity, serverless compute, and support.

### Frontier AI labs and model providers

**Participants:** frontier labs, enterprises with proprietary workflows,
domain-data companies, expert networks, model evaluators, and software vendors.

**Use cases:**

- fine-tuning or evaluating models against private enterprise workflows;
- customer-corpus adaptation without corpus transfer;
- sensitive safety, incident, and red-team telemetry;
- proprietary code or document evaluation;
- cross-enterprise benchmarks;
- encrypted linear-layer execution for hybrid LoRA workflows.

The business opportunity resembles expert-data platforms: labs pay for scarce,
high-value signal. The difference is that Run enables use of existing
institutional records and workflows without giving the lab a reusable copy.
Full FHE pretraining of frontier models is not a near-term product claim.

### Adjacent expansion

- Cross-bank fraud and anti-money-laundering analytics.
- Insurance risk and claims collaboration.
- Telecommunications abuse and network-security models.
- Retail and media measurement where participants do not want to disclose
  customer-level data.

## Monetization model

### 1. Run Exchange: governed data-access marketplace

The primary transaction is the right to run a named workload, not the sale of a
raw dataset.

#### Buyer payment

A buyer funds:

- provider access or license fees;
- the platform marketplace fee;
- FHE compilation and execution;
- optional validation, security, and integration services.

Access can be priced as:

- a fixed fee for one approved run;
- a time-limited license for a fixed workload and output class;
- a recurring subscription to an approved data collaboration;
- a milestone fee tied to usable cohort size or successful delivery;
- an internal chargeback in defense or enterprise consortia.

Per-record pricing should not be the default. It creates incentives to maximize
volume rather than consent, quality, representativeness, and scientific value.

#### Provider payout

Run Exchange collects the buyer payment, retains a marketplace take rate, and
distributes the provider pool according to the signed commercial terms. A deal
can combine:

- a minimum participation payment;
- a quality- and usability-based contribution pool;
- premiums for unique cohorts, modalities, labels, or longitudinal depth;
- completion payments after valid encrypted contribution;
- renewal royalties for repeated approved use.

No automated contribution score should determine payment until providers have
approved the formula. Model-utility or Shapley-style attribution can be offered
as an auditable option, but must not reveal site-level sensitive properties.

#### Marketplace revenue

```text
data-access marketplace revenue =
    buyer access payment
  - contracted provider payouts
  - pass-through taxes or regulated fees
```

The platform should describe its retained portion transparently as a take rate
for discovery, contracting workflow, policy enforcement, technical access,
payment administration, and auditability. Initial pilots validate the rate;
the business plan should not assume one universal percentage across verticals.

#### Rights and ethics

- The provider represents that it has the required rights and approvals.
- Every license is purpose-, program-, recipient-, output-, and time-bound.
- Providers can revoke future runs; revocation cannot erase an already released
  lawful result.
- Patient, employee, consumer, classified, or contract-restricted data is not
  monetized merely because it can be encrypted.
- Where law, consent, ethics, or public policy prohibits commercial use, the
  marketplace transaction is unavailable even if the computation is feasible.
- Run should avoid taking ownership of source data. It brokers rights,
  execution, payment, and evidence.

### 2. Run Engine: serverless FHE computation

Every workload receives a pre-run quote and a hard budget limit. Billable units
are customer-readable infrastructure quantities rather than obscure
cryptographic primitives:

- compilation and optimization time;
- CPU worker-seconds;
- GPU worker-seconds by accelerator class;
- encrypted storage byte-hours;
- ciphertext ingress and egress;
- premium checkpoint retention;
- dedicated or sovereign capacity.

Expose these as normalized **FHE Compute Units** while retaining the underlying
measurements on the invoice. Separate compilation from execution because a
compiled circuit can be reused across many approved runs with the same
fingerprint.

Offer:

- on-demand batch execution;
- reserved capacity for repeat collaborations;
- dedicated customer-VPC workers;
- sovereign/self-hosted annual licenses with support;
- volume commitments for model providers or research networks.

Serverless revenue is:

```text
compute revenue =
    compilation charges
  + FHE Compute Units
  + encrypted storage and transfer
  + dedicated-capacity premiums
```

Cloud worker cost, upstream FHE licensing, and support are direct COGS. Gross
margin improves through circuit caching, batching, packing, GPU utilization,
reserved cloud capacity, backend optimization, and accurate scheduling.

### 3. Run platform subscription

The annual subscription covers the durable control layer:

- organizations, collaborations, and role management;
- SSO/SCIM and policy workflows;
- Run Nodes and connectors;
- workload registry and approval UI;
- audit export and compliance evidence;
- budgets, quotas, release ledgers, and support;
- a contracted amount of collaboration and metadata capacity.

Enterprise, dedicated-VPC, and sovereign tiers differ by isolation, deployment,
support, retention, regional control, and compliance evidence rather than by
weakening the cryptographic model.

### Combined transaction

For a commercial multi-hospital training run:

```text
buyer invoice =
    institutional data-access fees
  + Run Exchange fee
  + serverless FHE compute and storage
  + allocated enterprise subscription
  + optional services
```

```text
Run contribution margin =
    marketplace fee
  + compute revenue
  + subscription allocation
  + service margin
  - cloud and storage COGS
  - upstream license allocation
  - variable support and payment costs
```

Provider payouts are pass-through marketplace volume, not platform revenue,
unless accounting policy and contract structure require gross presentation.
Investor reporting should always show gross transaction value, provider
payouts, net marketplace revenue, compute revenue, and subscription revenue
separately.

## Run Exchange workflow

1. A buyer publishes a private data request describing purpose, target schema,
   workload, output, eligibility, geography, duration, and budget.
2. The platform matches catalog metadata and qualified providers without
   exposing row-level data.
3. Providers return availability, quality, policy, and commercial terms.
4. The parties approve a standard or negotiated data-compute license.
5. The buyer publishes the immutable workload and funds an escrow or purchase
   commitment.
6. Providers validate, approve, encrypt, and commit their data.
7. The serverless FHE job executes.
8. The release policy is satisfied and the customer authority decrypts the
   authorized output.
9. Providers are paid and all parties receive signed receipts.
10. Renewal or another workload requires the rights specified in the contract;
    no secondary use is implied.

The marketplace catalog exposes enough metadata to match demand and estimate
utility without leaking rare cohorts, proprietary programs, exact site counts,
or sensitive institutional activity.

## Go-to-market

### Land with paid design partnerships

Each first engagement should involve a buyer and at least two independent data
providers. A paid pilot proves four things:

1. the data was not otherwise accessible on acceptable terms;
2. the workload can compile and complete within a defensible budget;
3. the output has measurable value over a buyer's existing data;
4. security, legal, and data stewards accept the operating model.

The pilot includes a fixed access budget, compute budget, integration scope,
success criteria, and conversion terms. Free cryptography demonstrations do not
validate the business.

### Vertical packages on one platform

- **Hospital-to-biopharma training:** FHIR/tabular connectors, cohort policy,
  encrypted regression/classification, model release.
- **Secure clinical analytics:** cohort counts, stratification, outcomes, and
  controlled aggregate release.
- **Sovereign collaboration:** self-hosted control and execution, offline
  promotion, CUI-oriented controls.
- **Private AI adaptation:** customer-hosted Run Node, hybrid encrypted linear
  layers, approved adapter/model export.

Packages provide repeatability without fragmenting the platform or compiler.

### Sales motion

- Demand-side buyers: heads of AI/data partnerships, R&D, clinical development,
  external innovation, research, and mission programs.
- Supply-side sponsors: chief data officers, research networks, hospitals,
  data businesses, enterprises, and expert/data platforms.
- Required approvers: privacy, legal, security, procurement, governance, and
  institutional leadership.
- Channels: cloud marketplaces, systems integrators, clinical research
  networks, data platforms, and public-sector primes.

The strongest expansion path is from one paid workload to additional data
providers, then additional workloads under the same governance deployment.

## Competitive landscape

| Category | Strength | Limitation relative to Run |
|---|---|---|
| Raw-data licensing | Maximum compute flexibility | Provider loses technical control after transfer |
| Expert/data networks such as Mercor | Proven demand for scarce training signal and managed supply | Usually create or license data rather than execute over institution-controlled ciphertext |
| Data exchanges such as AWS Data Exchange | Catalog, commercial offers, entitlements, subscriptions, and metered access | Primarily sells access to data assets or APIs rather than one protected computation and approved result |
| Duality Technologies | FHE/MPC collaboration, governed analytics, model training and inference, and a stated data-monetization use case | Public materials reviewed do not expose a self-service two-sided exchange with standardized computation-right offers, settlement, and multi-provider payouts |
| Cloud clean rooms | Mature governance and cloud integration | Often cloud-specific and reliant on service or enclave trust |
| Federated learning | Raw records stay local | Iterative coordination and potential gradient/update leakage |
| MPC | Strong multi-party protocols | Communication-heavy and workload-specific |
| De-identification and synthetic data | Familiar workflow and broad tool support | Utility loss and residual linkage or membership risk |
| FHE libraries | Strong cryptographic building blocks | Lack two-sided marketplace, connectors, policy, billing, and enterprise workflow |
| Run | Governed computation-right exchange plus metered privacy-preserving execution | Must build both market liquidity and reliable fulfillment; FHE jobs have higher cost and a constrained program envelope |

FHE, TEEs, MPC, federated learning, and DP can be complementary. The product
should win workloads where hiding data from the central executor justifies FHE
cost, not claim that FHE is optimal for every collaboration.

## Defensibility

The base cryptography is not the moat. Durable advantages come from:

- the network of approved data providers and repeat buyers;
- standardized computation-rights contracts and transaction history;
- a library of certified, economically valuable workloads;
- compiler diagnostics and cost models trained on production execution data;
- graph partitioning and FHE runtime optimization;
- connectors, local governance enforcement, and enterprise deployment;
- data-quality, provenance, and contribution evidence;
- adversarial benchmarks covering model, output, metadata, and collaboration
  leakage;
- accumulated trust with security, legal, and data stewards.

The marketplace and infrastructure reinforce each other:

```text
more governed data supply
    -> more valuable buyer workloads
    -> more protected-computation volume
    -> more provider revenue and platform optimization
    -> more governed data supply
```

## Unit economics and investor metrics

Report marketplace and infrastructure economics separately.

### Marketplace metrics

- Gross data-access transaction value.
- Provider payouts.
- Net marketplace take rate.
- Requests that reach signed agreement.
- Median time from request to approved run.
- Repeat use of the same provider and collaboration.
- Number of active buyers, providers, and multi-party collaborations.
- Share of supply that was previously inaccessible to the buyer.

### Compute metrics

- FHE Compute Units and revenue by workload class.
- CPU/GPU worker utilization.
- Compilation cache hit rate.
- Estimate-to-actual cost and duration error.
- Cloud and upstream-license COGS.
- Compute gross margin.
- Job success, retry, and checkpoint-recovery rates.

### Product and value metrics

- Time to first simulated and encrypted run.
- Workload compile success by capability tier.
- Data-owner onboarding time.
- Model or analysis improvement over buyer-only data.
- Raw records unlocked for approved computation without transfer.
- Expansion revenue per collaboration.
- Security and privacy incidents, including prevented policy violations.

### Bottom-up market model

Do not rely on a generic privacy-tech TAM. Build the model from:

```text
annual platform revenue =
    active enterprise deployments * annual subscription

annual Run Exchange revenue =
    completed paid collaborations * average access value * net take rate

annual compute revenue =
    completed workloads * average FHE Compute Units * unit price

total revenue = platform + marketplace + compute + services
```

Every input must be labeled as sourced, observed in pilots, or hypothetical.
Sensitivity analysis should vary collaboration conversion, annual workload
frequency, provider payout, FHE cost, and gross margin.

## Milestones

1. Reproduce the encrypted regression POC with measured cost and utility.
2. Run one job across three independent Run Nodes.
3. Demonstrate customer-controlled keys, exact workload approval, and governed
   output release.
4. Close a paid pilot where the buyer cannot otherwise access the contributed
   data on acceptable terms.
5. Pay at least two independent data providers for one completed encrypted
   computation.
6. Convert the pilot into a recurring platform and compute contract.
7. Launch certified encrypted analytics and small-model workload packages.
8. Demonstrate GPU economics and a quote within 30% of actual cost.
9. Sign a hybrid AI/LoRA design partner.
10. Obtain the required commercial FHE license and independent security review.
11. Repeat the transaction pattern in a second vertical.

## Key risks and mitigations

### Performance and cost

FHE can make an otherwise valuable workload economically infeasible. Require
simulation, cost estimation, a budget cap, workload-specific benchmarks, and a
clear alternative analysis before data owners perform integration work.

### Overpromising general AI training

General computation is the platform direction, not the launch state. Publish
certified, preview, and research tiers. Do not market full frontier-model
pretraining under FHE until measured production evidence exists.

### Data marketplace rights

Encryption does not create the right to use data. Require purpose-bound
contracts, provider warranties, local policy enforcement, approval records,
and vertical legal review. Do not treat technically accessible data as
commercially licensable data.

### Output leakage

An approved model or aggregate can reveal members, properties, sites, or rare
cohorts. Use minimum cohorts, output limits, release budgets, optional DP, and
the repository's adversarial tests. FHE protects computation, not arbitrary
release.

### Key-holder trust

The engine-validation POC may use one customer-controlled secret key, but this
does not cryptographically protect captured input ciphertexts from that
customer. The product design uses data-holder-controlled threshold key shares
and a separate customer recipient key. Run manages agreement signatures,
ceremony rounds, message relay, and audit evidence while holding no key share
and having no authority to release. Commercial multi-owner claims remain
blocked until a compatible maliciously secure threshold backend is validated.

### Upstream dependency and licensing

Concrete ML states that commercial use requires a Zama patent license. Secure
commercial terms before product revenue depends on the backend, maintain a
versioned compatibility layer, and evaluate OpenFHE for long-term crypto
agility.

### Cloud competition

Cloud vendors can bundle clean rooms with storage and ML. Differentiate through
Run Exchange, computation-level rights, provider payouts, cross-cloud and
on-prem portability, and a backend-neutral runtime. FHE is a decisive
fulfillment option when the parties reject enclave or operator trust, but the
commercial moat is the transaction network rather than the algorithm.

### Enterprise sales cycles

Multi-party deals multiply security, legal, and procurement reviews. Start with
standardized paid pilots, reusable contracts, a narrow workload, explicit
economic value, and one accountable collaboration sponsor.

## Funding rationale

Capital primarily funds:

- Run Exchange, provider onboarding, standard contracts, metering, settlement,
  and payout operations;
- privacy-backend integration plus selective FHE compiler, ML, and runtime
  engineering where existing backends leave product-critical gaps;
- data-plane connectors and secure deployment;
- GPU performance and cost modeling;
- security review, key management, and enterprise controls;
- forward-deployed engineering for the first repeatable vertical packages.

The company should not scale marketplace supply ahead of executable demand.
Each provider cohort should be recruited against funded buyer requests, and
each new workload category should pass technical and unit-economic gates before
becoming a standard product.

## Source notes

- [Concrete ML repository and commercial-use notice](https://github.com/zama-ai/concrete-ml)
- [Concrete ML GPU support](https://docs.zama.org/concrete-ml/guides/using_gpu)
- [Concrete ML encrypted LoRA fine-tuning](https://docs.zama.org/concrete-ml/llms/lora_training)
- [TFHE-rs public-key encryption](https://docs.zama.org/tfhe-rs/fhe-computation/advanced-features/public-key)
- [HomomorphicEncryption.org implementation security guidelines](https://homomorphicencryption.org/security-guidelines/)
- [HHS guidance on HIPAA and cloud computing](https://www.hhs.gov/hipaa/for-professionals/special-topics/health-information-technology/cloud-computing/index.html)
- [European Commission guidance on secondary use of health data](https://health.ec.europa.eu/ehealth-digital-health-and-care/reuse-health-data_en)
- [NIST SP 800-171 Rev. 3](https://csrc.nist.gov/pubs/sp/800/171/r3/final)
- [AWS Clean Rooms ML](https://docs.aws.amazon.com/clean-rooms/latest/userguide/machine-learning.html)
- [AWS Data Exchange products, grants, and entitlements](https://docs.aws.amazon.com/data-exchange/latest/userguide/what-is.html)
- [AWS Data Exchange API and metered-pricing model](https://docs.aws.amazon.com/data-exchange/latest/userguide/publish-API-product.html)
- [Duality FHE collaboration, model training, and data monetization](https://dualitytech.com/platform/technology-fully-homomorphic-encryption/)
- [Azure Confidential Clean Rooms](https://learn.microsoft.com/en-us/azure/confidential-computing/confidential-clean-rooms)
- [Google Confidential Space](https://docs.cloud.google.com/docs/security/confidential-space)
- [Mercor mission and expert-data model](https://www.mercor.space/mission/)
- [Mercor enterprise data monetization](https://www.mercor.space/enterprise/)

This document is a product and investment thesis, not legal, regulatory,
accounting, or cryptographic assurance.
