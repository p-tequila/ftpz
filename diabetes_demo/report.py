"""One self-contained report. Detailed diagnostics stay collapsed."""

import html
import json
from pathlib import Path


def write_report(path, result):
    escape = html.escape
    sections = []
    timings = []
    for experiment in result["experiments"]:
        kind = experiment["kind"]
        audits = [experiment["inference_audit"]]
        if "training_audit" in experiment:
            audits.append(experiment["training_audit"])
        if not all(all(audit["checks"].values()) for audit in audits):
            raise ValueError("Cannot publish a report with failed encryption checks")
        table = ""
        for row in experiment["rows"]:
            metrics = row["metrics"]
            quality = (f"R² {metrics['r2']:.3f}<small>RMSE {metrics['rmse']:.2f} · MAE {metrics['mae']:.2f}</small>"
                       if kind == "linear" else
                       f"{metrics['accuracy']:.1%}<small>AUC {metrics['auc']:.3f} · F1 {metrics['f1']:.3f}</small>")
            table += (
                f"<tr><th scope='row'>{escape(row['name'])}<small>{escape(row['training'])}</small></th>"
                f"<td>{row['train_seconds']:.4f}<small>seconds</small></td>"
                f"<td>{row['inference_setup_seconds']:.3f}<small>seconds</small></td>"
                f"<td><strong>{row['inference_ms']:.3f}</strong><small>ms / patient</small></td>"
                f"<td>{quality}</td></tr>"
            )
            timings.append(f"<tr><td>{escape(experiment['model'])} / {escape(row['name'])}</td>"
                           f"<td>{row['train_compute_seconds']:.4f} s</td></tr>")
        note = ("The same ordinary least-squares model is used in both rows; its training time is repeated for context. "
                "Built-in FHE training is unavailable for linear regression in Concrete ML 1.9. "
                "This section demonstrates encrypted inference. R² is higher-is-better; RMSE and MAE are lower-is-better, in target-score units."
                if kind == "linear" else
                f"Class 1 means progression above {result['threshold']:g}, the training-set median; class 0 means at or below. "
                "This is a demo threshold, not a clinical diagnosis. Both models use the same batches, zero initialization and learning rate. "
                "The FHE row includes encrypted training and encrypted inference using its learned weights.")
        sections.append(f"<section class='panel'><h2>{escape(experiment['model'])}</h2>"
                        f"<p>{escape(experiment['task'])}</p><div class='scroll'><table><thead><tr>"
                        "<th>Path / training</th><th>Training total</th><th>Inference setup</th>"
                        "<th>Inference latency</th><th>Predictive quality</th></tr></thead>"
                        f"<tbody>{table}</tbody></table></div><p class='note'>{note}</p></section>")
    comparison = "".join(sections)
    timing_rows = "".join(timings)
    weights_path = escape(result["models_directory"])
    max_difference = max(e["max_quantized_fhe_difference"] for e in result["experiments"])
    diagnostic = escape(json.dumps(result, indent=2, allow_nan=False))
    document = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Diabetes · FHE comparison</title>
<style>
:root{{--ink:#192823;--muted:#65736d;--line:#e3e8e4;--accent:#157158}}
*{{box-sizing:border-box}}body{{margin:0;background:#f7f8f5;color:var(--ink);font:15px/1.6 system-ui,-apple-system,sans-serif}}
main{{max-width:1100px;margin:64px auto;padding:0 28px 48px}}header{{margin-bottom:36px}}
.eyebrow{{font-size:11px;letter-spacing:.16em;text-transform:uppercase;font-weight:700;color:var(--accent)}}
h1{{font-size:clamp(28px,5vw,43px);line-height:1.15;letter-spacing:-.04em;font-weight:600;margin:14px 0}}
h2{{font-size:18px;font-weight:600;margin:0 0 14px}}p{{margin:8px 0;color:var(--muted)}}
.meta{{font-size:13px;margin-top:20px}}section{{margin:28px 0}}
.panel{{background:white;border:1px solid var(--line);border-radius:12px;padding:24px}}
table{{width:100%;border-collapse:collapse;font-variant-numeric:tabular-nums}}th,td{{text-align:left;padding:16px 12px;border-bottom:1px solid var(--line)}}
thead th{{font-size:11px;text-transform:uppercase;letter-spacing:.07em;color:var(--muted);font-weight:600}}
tbody th{{font-weight:500}}tbody tr:last-child>*{{border-bottom:0}}strong{{font-size:25px;font-weight:550;letter-spacing:-.03em}}
small{{display:block;color:var(--muted);font-size:12px}}.note{{font-size:12px;line-height:1.65;margin-top:14px}}
.flow{{display:grid;grid-template-columns:1fr 30px 1fr 30px 1fr;align-items:center;gap:10px}}
.flow b{{font-size:13px;font-weight:600}}.flow p{{font-size:12px;margin:4px 0}}.arrow{{color:var(--accent);text-align:center}}
.checks{{display:flex;flex-wrap:wrap;gap:10px 22px;margin-top:18px;font-size:12px;color:var(--accent)}}
details{{border-top:1px solid var(--line);padding:16px 0}}summary{{cursor:pointer;font-size:13px;font-weight:550}}
pre{{background:#eef1ee;padding:16px;max-height:380px;overflow:auto;font:11px/1.6 ui-monospace,monospace}}
button{{border:1px solid var(--line);background:white;padding:7px 12px;border-radius:5px;color:var(--ink);cursor:pointer;margin:12px 0}}
.scroll{{overflow-x:auto}}footer{{font-size:11px;color:var(--muted);margin-top:30px}}a{{color:var(--accent)}}
@media(max-width:600px){{main{{margin-top:30px;padding:0 16px 30px}}.panel{{padding:16px}}th,td{{padding:12px 8px}}.flow{{grid-template-columns:1fr}}.arrow{{transform:rotate(90deg)}}}}
</style></head><body><main>
<header><div class="eyebrow">Diabetes / Concrete ML / Actual FHE</div>
<h1>Plaintext vs FHE.</h1>
<p>Linear and logistic regression. Real encrypted execution on the same held-out patients.</p>
<div class="meta">{result['train_rows']} training patients · {result['test_rows']} test patients · {result['steps']} matched updates · 10 features</div></header>
{comparison}
<p class="note">Training total sums measured computation and FHE setup stages, including the training server process; file saving and verification are excluded. Inference setup is conversion + compilation + key generation. Per-patient latency is warm execution: encryption + server compute + decryption for FHE, and prediction calls for plaintext. It excludes startup, IPC and setup, and is not network request latency.</p>
<section class="panel"><h2>What does the server receive?</h2>
<div class="flow"><div><b>Client</b><p>Prepares and encrypts measurements.<br>Keeps the secret key.</p></div><span class="arrow" aria-hidden="true">→</span>
<div><b>Separate server process</b><p>Receives ciphertext and evaluation keys.<br>Runs training updates or prediction.</p></div><span class="arrow" aria-hidden="true">→</span>
<div><b>Client</b><p>Decrypts learned weights or predictions.<br>Applies prediction postprocessing.</p></div></div>
<div class="checks"><span>✓ No secret-key artifact sent</span><span>✓ Re-encryption produced different ciphertext</span><span>✓ Unrelated key did not recover the test result</span></div>
<p class="note">These checks verify this demo's data flow, not a cryptographic proof or anonymity. Both processes run on one Mac; this is not an OS sandbox. FHE does not hide request metadata or prevent leakage from a released model or decrypted output.</p></section>
<section class="panel"><h2>The complete pipeline</h2>
<ol>
<li><b>Prepare on the client.</b> Split 442 public benchmark records into 353 training and 89 test patients. Fit scaling and the classification threshold on training records only.</li>
<li><b>Train the baselines.</b> Fit linear regression to the continuous score. Fit logistic regression with {result['steps']} minibatch updates of eight records.</li>
<li><b>Compile encrypted logistic training.</b> On the trusted client, Concrete ML calibrates a 6-bit integer training circuit using plaintext training data. Quantization represents real numbers with finite-precision integers; it is not encryption.</li>
<li><b>Encrypt and send.</b> The client generates a secret key and evaluation keys, then encrypts the logistic training features, labels, initial weights and bias. Only ciphertexts, evaluation keys and the compiled program are sent to the worker.</li>
<li><b>Update encrypted weights on the server.</b> The worker executes SGD updates without decrypting. Weights and bias remain encrypted between updates. It returns the final ciphertexts, which are saved in the logistic bundle.</li>
<li><b>Recover the model on the client.</b> The client decrypts and dequantizes the ten weights and bias. A fresh client reloads the saved key and verifies it recovers the same parameters.</li>
<li><b>Predict with FHE.</b> Compile the plaintext-trained linear coefficients and the FHE-trained logistic coefficients into separate 8-bit inference circuits. Encrypt each test patient's inputs. The server returns an encrypted score; the client decrypts it and, for logistic regression, applies sigmoid and a 0.5 decision threshold.</li>
<li><b>Compare and reuse.</b> Measure time and predictive quality. Verify encrypted predictions equal the matching quantized plaintext calculation. Saved coefficients and scalers can be reused without training again.</li>
</ol>
<p class="note"><b>Encryption scope:</b> only logistic training has encrypted weights during updates. For inference, both models' coefficients are embedded in the compiled server circuit and are not hidden from the server. New inputs stay encrypted. The current worker is a separate process on the same Mac, not a remote isolated machine.</p></section>
<section class="panel"><h2>Reuse the saved models</h2>
<pre>python -m diabetes_demo.predict {weights_path} --model logistic --row {result['metadata']['test_row_ids'][0]}
python -m diabetes_demo.predict {weights_path} --model linear --row {result['metadata']['test_row_ids'][0]}</pre>
<p class="note">These commands predict in plaintext without retraining. Logistic reloads and decrypts its actual training ciphertexts. Linear loads its plaintext-trained coefficients. Use --features followed by ten raw measurements to supply another record.</p>
<details><summary>Where the weights and keys live</summary>
<pre>models/linear_model.json                          Plaintext linear weights + scaler
models/logistic/encrypted/weights.bin             Encrypted logistic weights
models/logistic/encrypted/bias.bin                Encrypted logistic bias
models/logistic/server/server.zip                Training circuit
models/logistic/client-private/secret.keys       Owner's saved key material
models/logistic/client-private/client.zip        Client specification + quantizers
models/logistic/client-private/model_info.json   Scaling + integrity metadata
models/logistic/client-private/decrypted_model.json  Decrypted logistic coefficients
models/logistic/client-private/plaintext_model.json  Logistic baseline coefficients</pre>
<p class="note">The private directory is owner-only and outputs are excluded from Git. The saved key is not password-encrypted on disk. Never give client-private to the server. Hash checks detect accidental mismatches, not malicious replacement of the entire bundle.</p></details></section>
<details><summary>Timing, numerical precision and limits</summary>
<table><thead><tr><th>Model / path</th><th>Training computation only</th></tr></thead><tbody>{timing_rows}</tbody></table>
<p class="note">Plaintext inference is the median of three passes of single-patient calls. FHE latency is the average over {result['test_rows']} encrypted predictions. Maximum difference from the matching quantized plaintext inference: {max_difference:.3g}. The floating-point model can differ because of quantization. FHE training uses approximate arithmetic and can vary between runs; dataset and minibatch seeds do not fix cryptographic randomness. Times are measurements of this run, not performance guarantees.</p>
<p class="note">No parameters are tuned on test outcomes. Logistic training is a short {result['steps']}-update demonstration, not a convergence claim. Calibration takes place on a trusted client. Shapes, request metadata, published models and decrypted outputs can reveal information; FHE is not anonymity. No raw ciphertexts or keys are embedded in this report.</p></details>
<details><summary>Reproducibility and diagnostics</summary>
<p class="note">Seed, split, batches, metrics, timings and version information. Public benchmark data only.</p>
<button id="download" type="button">Download results JSON</button><pre id="diagnostics">{diagnostic}</pre></details>
<footer>Research demonstration · <a href="https://scikit-learn.org/stable/datasets/toy_dataset.html#diabetes-dataset">Dataset</a> · <a href="https://docs.zama.org/concrete-ml/built-in-models/training">Encrypted training</a></footer>
</main><script>
document.getElementById('download').addEventListener('click',()=>{{
const blob=new Blob([document.getElementById('diagnostics').textContent],{{type:'application/json'}});
const url=URL.createObjectURL(blob);const link=document.createElement('a');
link.href=url;link.download='diabetes-fhe-results.json';link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
}});
</script></body></html>"""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".pending.html")
    temporary.write_text(document, encoding="utf-8")
    temporary.replace(path)
