# Executed methods versus research catalog

The original paper catalog is a research backlog, not a claim that every
listed method is implemented. `nftpz_platform.attacks` and the tests below are
the currently executable subset. Risk tags retain IND / BIO / ORG definitions.

| ID / method | Surface and attacker | Risk | Measurement | Status |
|---|---|---|---|---|
| MIA-loss-threshold | Customer-released model, known candidate labels | IND/BIO | ROC-AUC, stratified IID bootstrap CI, advantage, TPR at 1% FPR, FPR resolution | Implemented; preliminary adaptation of Yeom et al. |
| MIA-LiRA-logistic-adaptation | Released model, known candidate features/labels, auxiliary same-distribution records | IND/BIO | Gaussian in/out likelihood ratio, held-out AUC/CI and calibrated-threshold TPR/FPR | Implemented 32-shadow adaptation, one record per group, separate calibration/evaluation candidates |
| single-example-gradient-ratio | Plaintext logistic gradient and bias gradient | IND/BIO | Exact reconstruction RMSE | Implemented positive control, **not DLG/Geiping** |
| adjacent-cohort-differencing | Two exact aggregate results | IND/BIO/ORG | Target recovery; both queries pass k-minimum | Implemented residual-risk control; remains OPEN |
| Signed-manifest tampering | Active requester/coordinator | IND/ORG | Purpose/schema/key/request/program/expiry/untrusted-signer rejection | Implemented protocol probes |
| Replay / contributor dropout | Active requester/coordinator | IND/ORG | Replayed jobs and missing contributions rejected | Implemented |
| Unauthorized/duplicate/over-budget release | Caller at key-authority API | IND/ORG | Denial count | Implemented local policy layer |
| Small cohort suppression | Approved count with insufficient support | IND/BIO/ORG | Denial | Implemented; not a DP guarantee |
| Plaintext/secret-field injection | Worker protocol | IND/BIO | Unexpected sensitive fields rejected | Implemented |
| Wrong-key recovery / randomized encryption | Ciphertexts | IND/BIO | Unrelated key fails empirical recovery, ciphertext repeat differs | Implemented Concrete probes, not cryptographic proofs |
| Artifact inventory / subprocess boundary | Execution worker | IND/ORG | Worker directory has only server.zip, distinct process | Implemented; **not OS sandbox testing** |
| Blob traversal / immutable object names | Object store client | IND/ORG | Escape and accidental overwrite rejection | Unit-tested |
| Local audit-chain edit | Ledger | ORG | Modified event detected | Unit-tested; whole-chain rewrite remains possible |
| Site/schedule/size metadata exposure | Curious cloud | ORG/BIO | Site labels and update counts appear in approved protocol | Known OPEN surface; no metadata anonymity claim |

Source for the loss-based membership approach: [Yeom et al., *Privacy Risk in
Machine Learning: Analyzing the Connection to Overfitting*](https://arxiv.org/abs/1709.01604).
This implementation scores negative per-record log loss; its best threshold
is descriptive on the evaluated samples, not a trained, held-out attack model.
It is not a state-of-the-art privacy bound.

The separate shadow probe adapts [Carlini et al., *Membership Inference Attacks
From First Principles*](https://arxiv.org/abs/2112.03570): paired in/out shadow
models, per-example Gaussian distributions over true-class log odds, and their
log-likelihood ratio. Each shadow uses the target's update count, zero start,
batch size and learning rate, but float logistic surrogates instead of costly
Concrete quantized shadow training. Shadow membership is assigned only to
records actually included in updates. Thirty-two shadows and small biomedical
samples are not a full reproduction or a reliable extreme-low-FPR bound.
Attack-threshold calibration and evaluated candidates are disjoint; one record
per group avoids treating overlapping HAR windows as independent subjects.

Still unimplemented: exact Concrete-trained LiRA shadows; [RMIA (ICML 2024)](https://arxiv.org/abs/2312.03262)
with a disjoint reference population; auxiliary biological attribute/site inference; waveform reconstruction,
cross-modal linkage, adaptive database reconstruction, poisoning/backdoors,
malicious-FHE-worker integrity, protocol collusion and production IAM/network
penetration testing. Those must remain separate from completed test counts.

No gradients are released by the encrypted cloud-training protocol. Gradient
reconstruction should therefore be a positive control against a deliberately
unprotected baseline, not reported as a failed attack on an absent FHE surface.
