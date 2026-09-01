# 🔍 Detectra AI — Offline Intelligent Network Diagnostic Assistant

An offline AI/ML system that monitors your local network, detects abnormal
behaviour with an Isolation Forest model, diagnoses the probable problem
using explainable rules, scores severity/confidence/health, and recommends
fixes — **without any cloud AI API**.

---

## 1. Project structure

```
Detectra_ai/
├── app.py                # Streamlit dashboard (entry point)
├── network_monitor.py    # Collects real metrics (psutil + ping)
├── ml_model.py            # Isolation Forest training/inference
├── diagnosis.py           # Rules + severity + health score + confidence + evidence
├── troubleshooting.py     # Offline knowledge base + Q&A assistant
├── database.py            # SQLite persistence
├── config.py               # Paths, thresholds, demo scenarios
├── requirements.txt
├── README.md
├── .gitignore
├── data/                  # synthetic_training_data.csv (auto-generated)
├── models/                # isolation_forest.joblib, scaler.joblib (auto-generated)
└── database/               # Detectra.db (auto-created on first run)
```

---

## 2. How it works (architecture)

1. **Collect** (`network_monitor.py`) — pings a reference host for
   latency/packet-loss/jitter, samples `psutil.net_io_counters()` twice to
   estimate throughput → network usage %, and reads CPU usage + active
   connections. Every measurement is wrapped so a failure never crashes the app.
2. **Detect** (`ml_model.py`) — a locally-trained **Isolation Forest**
   (scikit-learn) scores the 6-feature vector
   `[latency, packet_loss, network_usage, active_connections, cpu_usage, network_errors]`
   and returns normal/anomaly + a 0-100 anomaly strength.
3. **Diagnose** (`diagnosis.py`) — explainable threshold rules turn the raw
   metrics + ML verdict into exactly one of six diagnoses, a severity level,
   a 0-100 health score, and a confidence percentage.
4. **Explain** — every diagnosis lists the *actual* metric values that
   triggered it plus the ML model's contribution ("Why was this detected?").
5. **Recommend** (`troubleshooting.py`) — an offline knowledge base maps
   each diagnosis to causes + concrete actions, and a small keyword-matching
   assistant answers natural-language questions from that same base.
6. **Store & visualize** (`database.py`, Analytics page) — every run is
   saved to SQLite and charted with Plotly.

### How confidence is calculated

```
confidence = 0.6 × rule_evidence_strength + 0.4 × ml_agreement_strength
```

- `rule_evidence_strength` (0-1): how far current metrics sit past their
  Warning/High/Critical thresholds.
- `ml_agreement_strength` (0-1): the Isolation Forest's anomaly strength,
  boosted when it agrees with the rule verdict and dampened when it
  disagrees.
- Capped at 99% (never absolute certainty), floored at 40% whenever any
  abnormal signal is present.

This is **deterministic** — never a random number.

---

## 3. Installation (Windows, beginner-friendly)

### Step 1 — Install Python
1. Go to https://www.python.org/downloads/ and download **Python 3.10 or 3.11**.
2. Run the installer. **Check "Add python.exe to PATH"** before clicking Install.
3. Verify: open **Command Prompt** and run:
   ```
   python --version
   ```
   You should see `Python 3.10.x` or `3.11.x`.

### Step 2 — Install VS Code
1. Download from https://code.visualstudio.com/ and install with default options.
2. Open VS Code, go to Extensions (Ctrl+Shift+X), install **Python** (by Microsoft).

### Step 3 — Get the project onto your machine
- If you received a ZIP: right-click it → **Extract All** → choose a folder
  (e.g. `C:\Users\<you>\Documents\netguard_ai`).
- In VS Code: **File → Open Folder…** → select the extracted `netguard_ai` folder.

### Step 4 — Open a terminal in VS Code
- Menu: **Terminal → New Terminal** (opens PowerShell/Command Prompt at the
  project root — you should see `Detectra_ai>` as the prompt).

### Step 5 — Create a virtual environment
```
python -m venv venv
```
This creates a `venv\` folder (already excluded via `.gitignore`).

### Step 6 — Activate the virtual environment
```
venv\Scripts\activate
```
Your prompt should now start with `(venv)`.
> If PowerShell blocks the script with an execution-policy error, run:
> `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` then retry.

### Step 7 — Install requirements
```
pip install -r requirements.txt
```
This installs Streamlit, scikit-learn, pandas, numpy, psutil, plotly, joblib.

### Step 8 — Run the app
```
streamlit run app.py
```
Your browser should open automatically at `http://localhost:8501`. If not,
open that URL manually.

> **First run note:** the app automatically generates synthetic training
> data, trains the Isolation Forest, and saves it to `models/` — this takes
> a few seconds the very first time only. Subsequent runs load the saved
> model instantly.

### Step 9 — Test Demo Mode
1. In the sidebar, turn **Demo Mode** ON.
2. Pick **"Network Congestion"** from the scenario dropdown.
3. Click **▶ Run Demo Diagnostic**.
4. Go to the **Dashboard** page — you should see a `DEMO / SIMULATED DATA`
   banner, metric cards, a "Network Congestion" diagnosis, severity,
   confidence, and evidence.

### Step 10 — Test real mode
1. Turn **Demo Mode** OFF.
2. Click **▶ Run Real Diagnostic** (takes ~2 seconds — it's actively pinging
   and sampling throughput).
3. Check the Dashboard — you should see your actual local latency/packet
   loss/etc. and a live diagnosis.

### Step 11 — Debugging common errors

| Symptom | Fix |
|---|---|
| `'streamlit' is not recognized` | The venv isn't activated — re-run `venv\Scripts\activate`, or reinstall with `pip install -r requirements.txt`. |
| PowerShell blocks `venv\Scripts\activate` | Run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` in that terminal, then retry. |
| App opens but Dashboard says "no data" | You haven't clicked **Run Real Diagnostic** / **Run Demo Diagnostic** yet — do that first. |
| Real mode shows very high latency / 100% packet loss | Normal on machines with no internet access, restrictive firewalls, or blocked ICMP (common on corporate/campus Wi-Fi and inside sandboxes/VMs) — Demo Mode is unaffected and always works for judging. |
| `PermissionError` on active connections | Some OS configurations restrict `psutil.net_connections()` — the app automatically falls back to a per-process count or `0`; it will not crash. |
| Charts empty on Analytics page | Run at least one diagnostic (real or demo) first — charts read from history. |
| Port 8501 already in use | Run `streamlit run app.py --server.port 8502` instead. |

---

## 4. Testing checklist

Run each Demo Mode scenario and confirm sensible output before presenting:

| Scenario | Expected diagnosis | Expected severity |
|---|---|---|
| Normal Network | Network Healthy | Normal |
| High Latency | High Latency | High |
| Packet Loss | High Packet Loss | High |
| Network Congestion | Network Congestion | Critical |
| Connection Failure | Connection Failure | Critical |
| Unstable Network | Unstable Network | High |

For each, verify:
- ✅ Prediction (anomaly/normal) makes sense given the metrics
- ✅ Severity matches the metric magnitudes
- ✅ Confidence is not identical/random across scenarios
- ✅ "Why was this detected?" evidence matches the displayed metric values
- ✅ Recommended actions match the diagnosis
- ✅ Record appears in History after running
- ✅ Analytics charts update after multiple runs
- ✅ App does not crash on repeated runs or with no internet

*(All six scenarios above were verified end-to-end during development —
see the Testing section notes in this repo's commit history.)*

---

## 5. Pushing to GitHub

```
git init
git add .
git commit -m "Initial commit: NetGuard AI offline network diagnostic assistant"
```

Then on GitHub.com:
1. Click **New repository**, name it `netguard-ai`, leave it empty (no README/gitignore — you already have them), click **Create repository**.
2. Copy the commands GitHub shows under "…or push an existing repository from the command line", or run:
```
git branch -M main
git remote add origin https://github.com/<your-username>/netguard-ai.git
git push -u origin main
```

`venv/`, the generated SQLite database, the trained model files, and Python
cache are all excluded via `.gitignore`, so your repo stays clean and small.

---

## 6. Deployment

### Local deployment (recommended for real monitoring)
```
streamlit run app.py
```
This is the **correct way to demo real network monitoring** — it measures
the laptop/PC it's running on.

### Streamlit Community Cloud (for a shareable public link)
1. Push the project to GitHub (see above).
2. Go to https://share.streamlit.io and sign in with GitHub.
3. Click **Create app** → **From existing repo**.
4. Select your repository and the `main` branch.
5. Set **Main file path** to `app.py`.
6. Click **Deploy**. You'll get a public `https://<something>.streamlit.app` URL.

> ⚠️ **Important:** a cloud deployment measures **Streamlit's cloud
> server's** network, not the visitor's laptop. Real Mode on the public URL
> will show cloud-server metrics, not the judge's own Wi-Fi. For that
> reason, **Demo Mode is the primary feature to showcase on the public
> deployment**, while **Real Mode should be demonstrated by running the app
> locally** on your own machine during the live presentation.

---

## 7. Hackathon live demo script (2–3 minutes)

1. **Normal Network** (Demo Mode → "Normal Network" → Run Demo Diagnostic)
   → Dashboard shows *Network Healthy*, health score ~100, low confidence-of-problem talk — "here's what a healthy baseline looks like."
2. **Network Congestion** (Demo Mode → "Network Congestion" → Run Demo Diagnostic)
   → Point out, in order:
   - AI anomaly status flips to 🚨 Anomalous
   - Detected Problem: **Network Congestion**
   - Severity: **Critical**
   - Confidence: **~98%**
   - "Why was this detected?" — read 2 evidence bullets aloud (usage %, latency, ML strength)
   - "Recommended Action" — read 1-2 actions aloud
3. Switch to **Analytics** — show the latency/packet-loss/usage charts updating across the runs you just did.
4. Switch to **History** — show the stored SQLite record for this run.
5. *(Optional closer)* Switch **Demo Mode off**, click **Run Real Diagnostic** to show it also works on live local metrics.

---

## 8. Anticipated judge questions & answers

**Q: Why do you need AI/ML at all — couldn't you just use if/else thresholds?**
A: Thresholds alone catch known, single-metric problems, but they can't
express *combinations* of mild signals that are jointly unusual (e.g.
slightly elevated latency + slightly elevated errors + unusual connection
count together). Isolation Forest learns the overall "shape" of normal
traffic and flags multivariate outliers that pure thresholds would miss. We
deliberately keep the thresholds too, so every AI flag is still explainable.

**Q: Why Isolation Forest specifically?**
A: It's unsupervised (we don't need labeled "this was congestion" data,
which we don't have), fast to train, works well on tabular numeric data,
and — unlike deep models — needs no GPU, is trivially serializable with
joblib, and runs instantly offline on a laptop.

**Q: How is confidence calculated? Is it random?**
A: No — it's `0.6 × rule_evidence_strength + 0.4 × ml_agreement_strength`,
both deterministic functions of the current metrics and model output. See
the "How is confidence calculated?" expander in the app.

**Q: Why offline? Why not just call an LLM API?**
A: Network diagnostics are inherently local and sometimes run in exactly
the situation where internet is unreliable — the moment you most need
diagnostics may be the moment you can't reach a cloud API. Offline also
means zero API cost, zero latency, and no telemetry leaving the user's
machine (privacy).

**Q: What's the difference between rule-based detection and AI anomaly detection here?**
A: Rules check each metric independently against fixed thresholds (fast,
transparent, but blind to novel combinations). The Isolation Forest looks
at all 6 features together and flags statistically unusual combinations
even if no single metric crosses a hard threshold. NetGuard combines both:
rules choose the specific diagnosis label (so it's always explainable),
while the ML model contributes anomaly strength as supporting evidence and
a confidence input.

**Q: What dataset did you train on?**
A: A synthetic dataset (~3000 samples) generated to resemble typical
home/office network conditions — mostly "normal" traffic with a small,
labeled-by-construction fraction of latency spikes, packet loss, congestion,
failures, and error bursts. This makes the project runnable immediately
without needing a real labeled network-incident dataset, which doesn't
publicly exist in a convenient form.

**Q: Doesn't training on synthetic data limit real-world accuracy?**
A: Yes — this is a known limitation. In a production version, we'd
periodically retrain on the user's own accumulated SQLite history (which
we already store) so the model adapts to *that specific* network's normal
baseline instead of a generic one.

**Q: How do you protect privacy?**
A: All processing — collection, ML inference, and storage — happens
locally. Nothing is sent to any cloud AI API. History lives in a local
SQLite file the user fully controls.

**Q: What's the future scope?**
A: Retraining on the user's own history for personalized baselines,
Windows Task Scheduler integration for continuous background monitoring,
alerting/notifications, exporting reports, and multi-interface support
(e.g. per-adapter monitoring, VPN detection).

**Q: What are the current limitations?**
A: Network usage % is estimated against an assumed link capacity, not a
real ISP figure; ping-based latency depends on the chosen reference host
and its own load; the ML model's "normal" baseline is generic/synthetic
rather than learned from this specific network; and cloud-deployed Demo
Mode measures the cloud server, not the visitor's own machine.

---

## 9. Privacy

- 100% local processing — no OpenAI, Gemini, or other cloud AI API is used or required.
- Metrics are collected locally via `psutil` and the OS ping command.
- The Isolation Forest model runs locally via scikit-learn.
- Diagnostic history is stored in a local SQLite file (`database/netguard.db`) that never leaves the machine unless you choose to share it.
