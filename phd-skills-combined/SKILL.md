---
name: phd-skills
description: >
  Comprehensive PhD research assistant covering the full research lifecycle.
  Use for: comparing ML runs (wandb/neptune/tensorboard/mlflow), dataset bias and
  curation, debugging failing/diverging/OOM/hanging experiments, designing ablation
  studies and experiment matrices, LaTeX environment setup, launching long GPU jobs
  with pre-flight checks, literature review and gap identification, verifying paper
  claims against code/data, writing or revising academic paper sections, reproducing
  papers end-to-end from arxiv, preparing code for open-source release, and
  anticipating reviewer questions or preparing rebuttals.
  Triggers on: "compare runs", "dataset bias", "stratified sample", "debug run",
  "why is training failing", "design ablation", "plan experiment", "setup latex",
  "launch training", "find papers on", "related work", "verify claims",
  "write abstract", "write methods", "reproduce paper", "publish code",
  "reviewer questions", "rebuttal", "paper weaknesses".
---

# PhD Skills — Unified Research Assistant

This skill covers the full PhD research lifecycle. Jump to the relevant section based on the user's request.

---

## 1. COMPARE — Same-Epoch Run Comparison

The most common comparison error is reporting "run A is 4 pp behind baseline" when run A is at epoch 11 of 100 and the baseline is from epoch 100. This section enforces same-epoch alignment.

### When to run
- "compare run A to baseline / to run B"
- "is my run improving / catching up / falling behind"
- "rank these experiments"
- "X vs Y wandb / neptune"
- "track lag against baseline"

### Auto-detect the tracker
1. `WANDB_API_KEY` env var set, or `wandb` imports → **wandb**
2. `NEPTUNE_API_TOKEN` env var set → **neptune**
3. `MLFLOW_TRACKING_URI` set, or `mlruns/` dir → **mlflow**
4. `runs/` or `lightning_logs/` dir → **tensorboard**
5. `*results*.json` / `*meta*.json` files in run dirs → **local file format**

If none, ask the user where metrics live before guessing.

### Protocol

**1. Identify the runs** — Get full names (no shortcodes). Clarify project + entity + run-id if ambiguous.

**2. Fetch metric history (not just final value)** — You need the full curve, not the last reported value.

```python
import wandb
api = wandb.Api()
run = api.run("entity/project/run-id")
history = run.history(samples=10000)  # full history, not summary
```

**3. Find the student's current step** — Get current epoch/step from the latest history row.

**4. Slice the baseline at the same step** — This is the critical step.

```python
student_step = student_history['epoch'].max()
baseline_at_same_step = baseline_history[baseline_history['epoch'] == student_step]
```

If no exact match, interpolate or pick nearest. State which.

**5. Separate proxy metrics from downstream** — Proxy (kNN accuracy, loss, perplexity) vs target downstream (linear probe, task F1). Report both separately:

```
                        | student (ep 11) | baseline (ep 11) | delta |
| proxy (kNN top-1)     | 36.4%           | 38.9%            | -2.5  |
| downstream (linear)   | not yet         | 42.1%            | n/a   |
```

**6. Run names in output** — Always full run names, never shortcodes.

### Anti-patterns
- Reporting delta without saying at what step
- Declaring "converged" without showing last 5 epochs
- Single-seed comparison treated as definitive

### Output
Compact comparison table per metric pair aligned at student's current step. Each cell traceable to tracker run-id and step. End with 1–2 sentences interpreting the comparison.

---

## 2. DATASET CURATION — Bias, Fairness, and Quality

### When to run
- "dataset bias", "stratified sample", "class imbalance"
- "data distribution", "fairness analysis", "ethical review"

### Step 1: Distribution Analysis

**Per-Class Distribution**
- Count instances per class/label/tag
- Compute imbalance ratio (max_count / min_count)
- Identify severely underrepresented classes (< 5% of max class)
- Visualize: bar chart of class frequencies sorted by count

**Co-occurrence Analysis**
- Build co-occurrence matrix: which labels appear together
- Identify spurious correlations (e.g., "violence" always co-occurs with "male")
- Check for label leakage between splits

**Metadata Distribution**
- Source diversity, temporal distribution, content diversity

### Step 2: Bias Assessment

For each imbalance or correlation:
1. Is it real-world reflective?
2. Is it harmful?
3. Is it fixable?

**Fairness Dimensions**: gender, racial/ethnic, age, geographic/cultural representation.

**Bias Metrics**: demographic parity, equalized odds, representation ratio.

### Step 3: Stratified Sampling

1. Primary stratification: by label/class distribution
2. Secondary stratification: by source (prevent source leakage)
3. Validation: chi-squared test, no source overlap between splits

Split ratios:
- Large (>50k): 80/10/10 or 90/5/5
- Medium (5k–50k): 70/15/15 or 80/10/10
- Small (<5k): k-fold cross-validation preferred

### Step 4: Quality Assessment

- Inter-annotator agreement: Cohen's kappa, Fleiss' kappa, Krippendorff's alpha
- Label noise estimation: sample and manually verify N labels
- Consistency checks: automated rules for label validity

### Step 5: Expansion Recommendations

1. Priority classes (most benefit from more data)
2. Source suggestions for underrepresented classes
3. Collection strategy: active learning, targeted scraping, synthetic augmentation
4. Cost estimation

### Step 6: Ethical Review Checklist

- [ ] Content sensitivity: does data contain sensitive material?
- [ ] Consent: was data collected with appropriate consent?
- [ ] Privacy: are individuals identifiable? Is anonymization needed?
- [ ] Licensing: are sources used within their license terms?
- [ ] Potential harms: could the dataset be misused?
- [ ] Documentation: is the dataset documented with a datasheet/data card?

### Output
1. Distribution report (per-class counts, imbalance ratios, co-occurrence matrix)
2. Bias findings (severity, actionability)
3. Split recommendation (stratification strategy with validation results)
4. Expansion plan (prioritized suggestions)
5. Ethics checklist (completed with notes)

---

## 3. DEBUG — Evidence-Before-Action Investigation

The most expensive class of mistake is asserting a cause based on plausibility, then "fixing" it without evidence. This section enforces: probe → hypothesis → smoke → controls → claim.

### When to run
- "why is X failing / diverging / NaN / OOM / hung / slow / crashed"
- "the loss is going up", "metrics look weird", "GPU util is 0"
- "debug this", "diagnose", "troubleshoot", "investigate this run"
- pasted a log excerpt asking what's wrong

### Five-Step Protocol

**Step 1: Cheap probes** — Gather evidence before forming any hypothesis.

```bash
# Process state
ps aux | grep -E '(python|train|torchrun|accelerate)' | grep -v grep

# Kernel / system events
dmesg | tail -100
journalctl -xe --since "1 hour ago" | tail -50

# GPU state
nvidia-smi
nvidia-smi --query-gpu=utilization.gpu,memory.used,temperature.gpu --format=csv

# Disk / filesystem
df -h /path/to/run-dir
du -sh /path/to/run-dir/*

# Checkpoint state
ls -la /path/to/run-dir/checkpoints/
```

Also read the last few hundred lines of the training log. Look for: exception tracebacks, repeated "loss=NaN" or "grad_norm=Inf", early-stop announcements, the last successful epoch/step.

**Step 2: Hypothesis (labeled as hypothesis)** — State what might be happening, explicitly framed as a hypothesis. Never skip to "the cause is X."

> "Hypothesis: the run is OOMing because dmesg shows `oom-kill` 3 minutes ago and the process is gone. Alternative hypotheses I haven't ruled out: (a) NFS write timeout, (b) explicit kill from a sibling process."

**Step 3: Smoke run** — The cheapest way to confirm or refute a hypothesis:
- OOM hypothesis: rerun with `batch_size=1` for 1 step
- Data hypothesis: rerun with a synthetic in-memory dataset
- Model hypothesis: forward pass only on a single batch with `eval()` mode
- Optimizer hypothesis: rerun with `lr=0`; if loss still explodes, loss itself is broken
- Distributed hypothesis: rerun on 1 GPU; if it works, DDP/NCCL is implicated

**Step 4: Controls** — Change exactly one variable from the failing config and rerun the smoke.

Common control axes (change one at a time): single-source vs multi-source data, default workers vs adjusted workers, mixed-precision on vs off, gradient checkpointing on vs off, torch.compile on vs off.

**Step 5: Claim cause** — Only after evidence stacks up (probe + smoke + control) do you assert a cause. Cite the specific tool output that proves it.

### What to avoid
- "It's probably X, let me try Y" → No. Probe first.
- Restarting the run with a small change as the diagnostic.
- Citing only the user's narrative as evidence.
- Stopping at the first plausible cause when artifacts contradict it.

### Output
(1) What probes showed, (2) the hypothesis, (3) smoke outcome, (4) cause-or-uncertain verdict, (5) recommended next action. Each claim cites the tool output that backs it.

---

## 4. EXPERIMENT DESIGN — Rigorous Ablation Planning

### When to run
- "design ablation", "plan experiment", "what experiments should I run"
- "baseline comparison", "experiment matrix"

### Step 1: Understand the Research Question
- What hypothesis should the experiment support?
- What is the dependent variable (metric) and independent variables (factors)?
- What is the baseline?

### Step 2: Single-Variable Isolation

Every ablation changes exactly ONE variable at a time.

```
| Run ID | Factor | Value | Fixed Config | Expected Outcome |
|--------|--------|-------|-------------|-----------------|
```

### Step 3: Experiment Matrix

1. **Full factorial** — ≤3 factors, ≤3 levels each
2. **Sequential elimination** — many factors: run single-factor ablations first, combine winners
3. **Latin square** — full factorial is too expensive

Always calculate total runs:
```
Total runs = product of all factor levels
GPU hours = total runs × hours_per_run
```

### Step 4: Resource Estimation
- GPU hours, API costs (tokens × price), wall clock time, storage

### Step 5: Config Stub Generation
Read existing configs first to match file format, key naming conventions, directory structure, and logging/tracking integration.

### Step 6: Execution Plan
1. Order runs by dependency (baselines first, then ablations)
2. Identify runs that can be parallelized
3. Create a shell script/batch runner matching existing patterns
4. Include checkpointing strategy for long runs

### Step 7: Analysis Plan (define before running)
- Which metrics to compare (primary + secondary)
- Statistical significance test (paired t-test, bootstrap CI)
- How to handle failed/crashed runs
- Visualizations: comparison tables, bar charts, learning curves

### Verification Checkpoints
- [ ] Each ablation changes exactly one variable
- [ ] Baseline clearly defined, run with same setup
- [ ] Resource estimate within budget
- [ ] Config stubs match existing project format
- [ ] Analysis plan defined before execution begins
- [ ] Seeds fixed for reproducibility

### Output
1. Experiment matrix table
2. Resource estimate
3. Execution script (ready-to-run)
4. Analysis plan

---

## 5. LATEX SETUP — Environment and Compilation

### When to run
- "setup latex", "biber vs bibtex", "latex compilation error"
- "install latex packages", "venue template", "texlive setup"

### Step 1: Detect Current State

```bash
which pdflatex && pdflatex --version
which xelatex && xelatex --version
which lualatex && lualatex --version
which biber && biber --version
which bibtex && bibtex --version
which tlmgr && tlmgr --version
```

### Step 2: Analyze the Project

Read the main .tex file to determine:
1. Document class
2. Bibliography system: `\usepackage{biblatex}` → biber; `\usepackage{natbib}` or `\bibliographystyle{...}` → bibtex
3. Required packages from all `\usepackage{...}` declarations
4. Special requirements: TikZ, minted (needs pygments), algorithm2e, etc.

### Step 3: Venue Template Detection

| Venue | Class | Bib system | Notes |
|-------|-------|-----------|-------|
| CVPR/ECCV | Custom class file | bibtex | Usually provided in template |
| NeurIPS | neurips_20XX.sty | natbib + bibtex | Style file changes yearly |
| ICLR | iclr20XX_conference.sty | natbib + bibtex | OpenReview format |
| ACL/EMNLP | acl.cls | bibtex | ACL Anthology format |
| IEEE | IEEEtran.cls | bibtex | Column formatting specific |
| Springer | llncs.cls | bibtex or biblatex | Depends on series |

### Step 4: Install Missing Components

**Ubuntu/Debian:**
```bash
sudo apt install texlive-base texlive-latex-recommended
sudo apt install texlive-latex-extra
sudo apt install texlive-fonts-recommended texlive-fonts-extra
sudo apt install texlive-bibtex-extra biber  # if biblatex used
sudo apt install texlive-science  # algorithm2e, etc.
```

**macOS:**
```bash
brew install --cask mactex  # Full installation (recommended)
# or
brew install --cask basictex && sudo tlmgr update --self && sudo tlmgr install <package>
```

### Step 5: Configure Compilation

**For bibtex projects:**
```bash
pdflatex main.tex && bibtex main && pdflatex main.tex && pdflatex main.tex
```

**For biblatex/biber projects:**
```bash
pdflatex main.tex && biber main && pdflatex main.tex && pdflatex main.tex
```

**Common issues:**
- Missing .bib file: check `\bibliography{...}` path
- Undefined citations: run bibtex/biber + pdflatex twice
- Missing packages: install via tlmgr, not apt
- Font errors: install texlive-fonts-extra
- TikZ externalize errors: ensure write18 is enabled

### Output
1. Current state (installed, missing)
2. Project requirements
3. Installation commands (OS-specific, only what's needed)
4. Compilation command (exact pipeline)
5. Verification result

---

## 6. LAUNCH — Pre-Flight Checklist for Long ML Jobs

Long training jobs are expensive to fail. A 12-hour run that crashes on epoch 3 from a missing dataset path or a wrong `workers=8` on NFS is a full day lost.

### When to run
- "launch / kick off / start / fire up a training run"
- "restart a run that died"
- "kill a current run"
- About to run: `python train.py`, `accelerate launch`, `torchrun`, `deepspeed`, `sbatch train.sh`, `wandb sweep`

### The Checklist

**1. Config diff against a reference run**

```bash
find configs/ recipes/ experiments/ -maxdepth 3 \( -name '*.yaml' -o -name '*.yml' -o -name '*.json' -o -name '*.toml' \) -mtime -30 2>/dev/null | head
diff -u configs/baseline_v1.yaml configs/intended.yaml
```

Walk every diff line. Common silent regressors:
- `num_workers` / dataloader workers (default 8 is wrong on NFS)
- `batch_size` (per-device vs global mismatch under DDP)
- `learning_rate` (must scale if batch size changed)
- `optimizer` betas / weight decay
- `mixed_precision` (`fp16` vs `bf16`)
- `gradient_accumulation_steps`
- `seed`

**2. Run name discipline**

The run name lives in wandb / checkpoint dirs forever. It must describe the experiment:
- Bad: `run-1`, `wave-2`, `cs-ad`, `phase2-internal`
- Good: `7src-fastvit-s-featmap-mlp-dinov3`, `coco-baseline-bs256-lr3e-4`

Pattern: `<dataset/task>-<model>-<key-config>-<distinctive-recipe-piece>`

**3. Path verification**

```bash
ls -la /path/to/dataset | head
ls -la /path/to/checkpoint.pt
ls -la /path/to/runs/
cat configs/intended.yaml | head
```

Never trust a path recalled from memory.

**4. Monitoring setup**

Auto-detect tracker:
- `WANDB_API_KEY` set or `wandb` import → wandb
- `NEPTUNE_API_TOKEN` set → neptune
- `MLFLOW_TRACKING_URI` set or `mlflow` in launcher → mlflow
- `runs/` or `lightning_logs/` dir → tensorboard
- None → ask the user; "no monitoring" is rarely correct for multi-hour runs

**5. ETA in local timezone**

Estimate: `epochs × seconds_per_epoch / 3600 = hours`. State ETA in system TZ. If run straddles a meeting/sleep/OOO, decide whether to defer or split.

### Restart and Kill Cleanup

Purge stale artifacts in this exact order:
1. Local checkpoint dir: `rm -rf /local/runs/<run-name>` (verify path first)
2. Remote artifact dir on cluster/NFS/object store
3. Experiment tracker run: delete via API
4. Scheduler reservation: cancel the SLURM job, lambda reservation, etc.

### Output
Walk the five checks (or three + cleanup if killing) and report which passed/failed. Block the launch on any failure unless the user explicitly waives the check. For a clean launch, end with the launch command in a fenced block.

---

## 7. LITERATURE RESEARCH — Systematic Survey and Gap Analysis

### When to run
- "find papers on", "related work", "literature review"
- "what papers exist", "open source implementation", "papers with code"

### Step 1: Scope Definition
- Clarify the exact research question or topic boundary
- Identify key terms and synonyms
- Define inclusion/exclusion criteria (year range, venue type, methodology)
- Ask if the user has seed papers

### Step 2: Systematic Search

**2a. Direct Search** — Google Scholar, Semantic Scholar, arXiv, DBLP. Vary search terms.

**2b. Citation Chaining**
- Forward: who cited this paper?
- Backward: what does this paper cite?

**2c. Venue Mining** — Check recent proceedings of top venues + workshops.

**2d. Open Source Discovery** — GitHub, Papers With Code, "awesome-X" lists.

### Step 3: Categorization

```
| Paper | Year | Venue | Approach | Key Result | Code? | Relevance |
|-------|------|-------|----------|-----------|-------|-----------|
```

Group by methodology/approach type, not chronologically.

### Step 4: Gap Identification

1. Coverage matrix: rows = problem aspects, columns = existing approaches
2. Empty cells = potential gaps
3. For each candidate gap: search with different terms before declaring it real

### Step 5: Gap Validation

- [ ] Searched with at least 3 different phrasings
- [ ] Checked proceedings of top-3 venues from last 2 years
- [ ] No preprint on arXiv addressing this gap
- [ ] The gap is technically feasible to address
- [ ] Filling the gap would be a meaningful contribution

Rate confidence: HIGH / MEDIUM / LOW.

### Citation Integrity
Every paper mentioned must have verified metadata: author names (cross-check DBLP), venue and year (confirmed published version), numerical claims traced to specific table/figure. Flag uncertainty rather than guessing.

### Output
1. Topic summary (2–3 sentences)
2. Paper table (categorized)
3. Gap table (with confidence levels and evidence)
4. Recommended readings (top 5–10)
5. Candidate citations (BibTeX, verified against DBLP)

---

## 8. PAPER VERIFICATION — Claims vs Code and Data

### When to run
- "verify claims", "check numbers", "do the numbers match"
- "formula vs code", "audit the paper", "cross-check results"

### 1. Numerical Accuracy Audit

For every number in the paper:

```
| Paper claim | Location (.tex) | Source file/code | Source value | Match? |
|-------------|-----------------|-----------------|-------------|--------|
| "13,999 frames" | abstract L3 | len(glob(labels/*.json)) | ? | ? |
| "4.2% improvement" | Table 2 | eval_results.json | ? | ? |
```

Common errors: rounding inconsistencies, stale numbers, percentage vs absolute confusion, off-by-one in dataset counts.

### 2. Terminology Consistency Audit
1. Extract all defined terms from methods section
2. Search each term across ALL sections
3. Flag inconsistent usage (same concept different names, or same name different meanings)

### 3. Code-Paper Alignment

For each method described:
1. Find the corresponding code
2. Compare paper description with actual implementation
3. Check: algorithm steps, hyperparameters, architecture descriptions, loss functions, training procedures

### 4. Formula-Code Verification

For each equation:
1. Identify equation and variables
2. Find the code implementing it
3. Map each mathematical operation to code equivalent
4. Verify: summation bounds, division edge cases, normalization factors, gradient flow, reduction operations (mean vs sum)

### 5. Citation Fact-Checking Protocol

**Step 1**: Extract claim and cited paper.
**Step 2**: Verify BibTeX metadata against DBLP (author names, title, venue, year).
**Step 3**: For cited claims with specific numbers, locate the exact table/figure in the cited paper.
**Step 4**: Check for common citation errors: citing preprint when published version exists, wrong year, author name misspellings, citing for a claim the paper doesn't actually make.

### Output
1. Summary (X issues: Y high, Z medium, W low)
2. Numerical audit table
3. Terminology issues (with locations)
4. Code-paper mismatches
5. Citation issues
6. Suggested fixes (specific text replacements)

---

## 9. PAPER WRITING — Academic Paper Sections and Notation

### When to run
- "write the abstract", "structure the methods", "improve this section"
- "notation consistency", "figure refinement", "paper structure"

### Core Principles
1. Precision over elegance — every sentence verifiable against code or data
2. Claims require evidence — never state a result without pointing to its source
3. Notation consistency — define once, use identically everywhere
4. Conciseness — remove words that don't add information

### Section-Specific Guidance

**Abstract**: problem → approach → key result → significance. Include 1–2 concrete numbers, all traceable to specific experiments. No citations unless venue requires.

**Introduction**: (1) Problem and motivation, (2) Why existing approaches are insufficient, (3) Your approach and why it addresses the gap, (4) Contributions list (concrete, falsifiable). Each contribution must map to a section providing evidence.

**Related Work**: Organize by theme/approach. For each group: what they do, what's missing, how your work differs. End each paragraph with how your work addresses the limitation.

**Methods**: Define all notation in a single place. Each component independently understandable. Enough detail to reimplement. Cross-reference equations with code.

**Experiments**: dataset (size, splits, preprocessing), metrics (defined formally), baselines (justified, fairly compared), results table (highlight best, include std dev or CI), ablations (one factor at a time).

**Conclusion**: Summarize contributions, state limitations honestly, specific feasible future work.

### Notation Consistency Protocol
1. Read existing notation definitions in the paper
2. Use EXACTLY the same symbols — no synonyms
3. If a new symbol is needed, check it doesn't clash

Common pitfalls: using $x$ and $\mathbf{x}$ for the same concept; $N$ in methods but $n$ in experiments; inconsistent subscript conventions.

### Figure Refinement Methodology

**1. Specification Capture** — Before generating/modifying:
- What data does it show (exact source file/variable)?
- What message should the reader take away?
- What are the hard constraints (font size ≥ 8pt, column width, color scheme)?
- What must be preserved from the current version?

**2. Constraint Preservation**
```
Constraints for Figure N:
- [KEEP] Y-axis range 0-100
- [KEEP] Color scheme: blue=ours, gray=baselines
- [CHANGE] Legend position: inside → outside
- [ADD] Error bars from std_results.json
```

**3. Variant Generation** — Generate 2–3 variants, each changing ONE visual aspect. Let the user compare.

**4. Visual Verification** — ALWAYS inspect the generated image. Check data values, labels, legends, annotations. Confirm takeaway is clear.

### Writing Process
1. Read first — always read existing section before writing
2. Identify the claim — what is this paragraph trying to say?
3. Find the evidence — where does this come from?
4. Write the text — claim, evidence, interpretation
5. Verify — re-read against source

### Output
LaTeX-ready output matching the paper's existing style. Comments for claims needing verification: `% TODO: verify this number`. Flag notation inconsistencies. Suggest improvements with before/after comparisons.

---

## 10. REPRODUCE — End-to-End Paper Reproduction

### When to run
- "reproduce / implement / replicate / re-run paper X"
- pasted an arxiv URL with reproduction intent
- "the paper has no code, can we build it"

### Working Directory Layout

```
repro/<paper-arxiv-id>/
├── paper.md              # structured extract from stage 1
├── inventory.md          # what exists / missing from stage 2
├── gaps_filled.md        # hyperparam table with provenance from stage 3
├── code/                 # implementation from stage 4
├── data/                 # dataset symlinks or actual data from stage 5
├── dataset_substitution.md  # if public dataset stood in for private one
├── smoke_logs/           # outputs from stage 6
└── results.md            # replication outcomes from stage 7
```

### Seven-Stage Workflow

**Stage 1: Paper Acquisition**
- Fetch the arxiv HTML (prefer HTML over PDF for parsing)
- Extract: abstract, method description, hyperparameter tables, dataset details, evaluation protocol
- Save as structured `paper.md`

**Stage 2: Code Discovery**
- Search the official author repo (check paper's footnotes, GitHub username patterns)
- Check Papers With Code for the task/dataset
- Search GitHub by paper title and keywords
- Document inventory: what's provided, what's missing

**Stage 3: Gap Analysis**
Extract every missing detail from the prose:
- All hyperparameters mentioned anywhere in paper/appendix
- Architecture specifics not in a table
- Augmentation, regularization details
- Dataset splits, preprocessing steps
- Evaluation protocol (beam size, ensembling, etc.)

Save as `gaps_filled.md` with provenance (which paper section).

**Stage 4: Implementation**
- Create a `uv` virtual environment
- Fill each gap with a justified default; commit per gap
- Each commit message references the paper section that justified the value
- Never fill a gap silently; document every choice

**Stage 5: Dataset Acquisition**
- Try HuggingFace datasets first
- If private/restricted: find a similar public dataset; document in `dataset_substitution.md`
- Validate: data statistics should match or be close to paper's reported numbers

**Stage 6: Smoke Runs**
In order:
1. Forward pass: one batch through model, check output shape
2. One step: forward + backward + optimizer step, check loss is finite
3. 20 iterations: check loss is decreasing and metrics are reasonable

Any smoke failure routes to the **debug** skill.

**Stage 7: Replication Runs**
- Pass through the **launch** checklist before any multi-hour run
- Run at the paper's reported number of epochs/steps
- Compare via the **compare** skill at the paper's reported epochs (never current-vs-final)

### Cross-References
- After stage 3: hand gap analysis to **paper-verification** skill
- Stage 4: small, reviewable commits per gap
- Stage 6 failures: route to **debug** skill
- Stage 7 launches: through **launch** checklist
- Stage 7 comparisons: through **compare** skill

### Output
`results.md` with absolute deltas and one of three labels per metric:
- `[matched within 0.X pp]` — within paper's reported variance
- `[gap, hypothesis: ...]` — measurable underperformance with stated hypothesis
- `[fundamental disagreement, see X]` — result and paper's claim inconsistent; needs investigation

---

## 11. RESEARCH PUBLISHING — Code Release and Reproducibility

### When to run
- "publish code", "open source release", "reproducibility"
- "research repository", "code release", "prepare for publication"

### Step 1: Repository Assessment

1. **Sensitive content scan** (grep for):
   - API keys, tokens, credentials
   - Hardcoded paths specific to the researcher's machine
   - Internal URLs or private infrastructure references
   - PII in comments or data

2. **Dependency audit**:
   - List all dependencies with pinned versions
   - Identify proprietary or restricted-license dependencies
   - Check for abandoned/unmaintained dependencies

3. **Code organization**:
   - Dead code, debugging artifacts, scratch files
   - Duplicated code
   - Overly complex code that can be simplified

### Step 2: Repository Structure

```
project/
  README.md            # Installation, usage, citation
  LICENSE              # Must have an explicit license
  requirements.txt     # or pyproject.toml with pinned deps
  setup.py / setup.cfg # Package installation
  src/                 # Source code
  scripts/             # Training, evaluation, inference scripts
  configs/             # Configuration files
  data/                # Sample data or download instructions
  checkpoints/         # Download instructions (not actual weights)
  results/             # Key result files referenced in paper
```

### Step 3: Reproducibility Checklist

For each experiment in the paper:
- [ ] Configuration file exists and matches paper's hyperparameters
- [ ] Random seeds set and documented
- [ ] Training command documented end-to-end
- [ ] Evaluation command produces reported numbers
- [ ] Data preprocessing steps are scripted (not manual)
- [ ] Hardware requirements documented (GPU type, memory, time)
- [ ] Dependencies version-pinned

### Step 4: README Structure

1. Title + one-line description
2. Paper link (arXiv, venue page)
3. Visual (architecture diagram, key result, demo GIF)
4. Installation (step-by-step, tested on clean environment)
5. Quick start (inference on single example, < 5 commands)
6. Training (full reproduction commands)
7. Evaluation (reproduce paper numbers)
8. Model zoo / checkpoints (download links with expected metrics)
9. Citation (BibTeX block)
10. License

### Step 5: Code Cleanup
1. Remove debugging prints, commented-out code, scratch experiments
2. Replace hardcoded paths with configurable paths (env vars or args)
3. Add docstrings to public functions only
4. Document main entry points clearly
5. Do NOT refactor working code for style — adds risk for no benefit

### Step 6: License Selection

| License | Commercial use | Attribution | Copyleft |
|---------|---------------|-------------|----------|
| MIT | Yes | Yes | No |
| Apache 2.0 | Yes | Yes | No (patent grant) |
| GPL 3.0 | Yes | Yes | Yes |
| CC BY 4.0 | Yes | Yes | No (non-code) |
| CC BY-NC 4.0 | No | Yes | No (non-code) |

Default recommendation: MIT for code, CC BY 4.0 for datasets/models.

### Step 7: Pre-Release Testing
1. Clone into a fresh directory
2. Follow README installation steps exactly
3. Run quick start commands
4. Run evaluation to verify numbers match paper
5. Check git history for sensitive information

### Output
1. Audit report (sensitive content, dependency issues, dead code)
2. Action list (specific files to modify/remove/add)
3. README draft
4. Reproducibility checklist (per-experiment verification status)

---

## 12. REVIEWER DEFENSE — Anticipating and Responding to Review

### When to run
- "reviewer questions", "anticipate reviewers", "rebuttal"
- "paper weaknesses", "defend the paper", "strengthen the paper"

### Step 1: Vulnerability Analysis

**Technical Weaknesses**:
- Missing baselines reviewers would expect
- Evaluation metrics that don't fully capture the contribution
- Assumptions stated without justification
- Scalability concerns not addressed
- Missing error analysis or failure case discussion

**Presentation Weaknesses**:
- Claims stronger than evidence supports
- Missing related work a reviewer in the area would know
- Unclear methodology (could someone reimplement from the paper alone?)
- Figures that don't clearly convey the intended message
- Inconsistencies between sections

**Experimental Weaknesses**:
- Small dataset without justification
- Missing statistical significance tests
- No comparison with SOTA on standard benchmarks
- Hyperparameter sensitivity not explored
- No computational cost comparison

### Step 2: Venue-Specific Anticipation

**Top-tier ML/CV (CVPR, NeurIPS, ICLR, ECCV)**: extensive ablations, strong baselines, clear novelty articulation, reproducibility valued.

**Workshops**: more tolerant of work-in-progress; interesting ideas valued over exhaustive evaluation.

**Journals**: thorough related work, deeper analysis and more experiments, writing quality matters more.

### Step 3: Question Generation

Generate at least 10 likely reviewer questions, ranked by probability:

```
Q: [Reviewer question]
Motivation: [Why this would be asked]
Answerable: [Yes — cite Table X / No — would need experiment Y]
Draft response: [If answerable, 2-3 sentences]
```

### Step 4: Ablation Selection

From all available experiments, select the subset that:
1. Proves the core contribution (the single most important ablation)
2. Shows each component's value (incremental additions)
3. Addresses anticipated weaknesses (preemptively)
4. Tells a coherent story

Ranking criteria: impact magnitude, narrative strength, uniqueness, cost (main paper vs appendix).

### Step 5: Negative Results

Frame as: "We explored X but found it did not improve over Y because Z."
- Shows thoroughness and provides insight
- Frame as "analysis" not "failure"
- Include in supplementary if not in main paper

### Step 6: Rebuttal Preparation

If responding to actual reviews:
1. Read ALL reviews before responding to any
2. Identify common concerns across reviewers
3. Prioritize: factual errors → major concerns → minor ones
4. Be respectful and specific (point to exact sections, tables, figures)
5. Only promise new experiments you can deliver in the rebuttal period

Rebuttal structure:
```
We thank Reviewer X for their thoughtful feedback.

**[Major concern]**: [Direct response with evidence]

**[Specific question]**: [Concrete answer]

**[Suggestion]**: [How we will incorporate it]
```

### Output
1. Weakness table (categorized with severity)
2. Top 10 anticipated questions (with answerability and draft responses)
3. Recommended ablation subset (with justification)
4. Suggested text edits (specific paragraphs to strengthen before submission)
