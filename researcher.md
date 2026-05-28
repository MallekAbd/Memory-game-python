---
name: researcher
description: "Combined reference of all research skills — literature review, LaTeX, peer review, project management, bibliography validation, and more. Use as a lookup when you need the instructions for any research-related skill."
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, WebSearch, WebFetch
---

# Research Skills Reference

A combined reference of all available research skills.

---

## audit-paper-book

**Source:** `skills/audit-paper-book/SKILL.md`

---
name: audit-paper-book
description: "Use when you need to detect drift between an existing paper-book companion and a revised version of its source paper, then sync the mechanical pieces (new bib entries, new/changed figures) and report the substantive drift (renamed sections, changed numbers, new theorems, new contributions) for the user to triage. Counterpart to /init-paper-book. Read-only by default; --apply flag opts in to mechanical fixes."
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
argument-hint: "<slug> [--apply] [--dry-run]"
---

# Audit Paper Book

A book companion goes stale the moment its source paper revises. This skill walks the gap between the paper and the book, classifies each drift item by mechanical-vs-substantive, and produces a single report. With `--apply`, the mechanical drift (new bib entries, new figures) is fixed in place; substantive drift always requires user judgement.

For NEW books, use `/init-paper-book`. This skill never creates a book that doesn't already exist.

## Hard rules

1. **Never edit chapter prose without explicit user approval.** Mechanical fixes touch `references.bib` and `figures/*` only. Section content drift is reported, not fixed.
2. **Numeric changes always block.** If the paper changed a result number (mean gap, accuracy, theorem constant), the book reports it but does NOT auto-update. The user verifies the new number is intentional.
3. **Atlas slug match.** The book's slug must equal the atlas topic filename. Drift in either is a `/init-project-research`-level concern, not this skill's job.
4. **Read-only is the default.** `--apply` is opt-in; without it, this skill produces a report and changes nothing.
5. **Accessibility floor.** The book must remain readable by someone with an undergraduate degree in a quantitative field (linear algebra, probability, basic optimisation/statistics — not necessarily Bayesian methods or domain-specific machinery). Concretely:
    - Every acronym must be expanded at first use within each chapter (e.g. "expected hypervolume improvement (EHVI)").
    - Every display equation gets a one-line plain reading within 2 sentences.
    - No jargon-on-jargon sentences (≥3 specialised terms without inline definition).
    - Intuition before formal definition.

    The audit runs an accessibility check on every chapter (see Phase 2) and reports violations alongside other drift. Violations are reported in the `accessibility` drift bucket (see Phase 3), never auto-fixed. The user decides whether to revise prose or accept the violation.

## When to use

- Camera-ready version of a submitted paper (post-acceptance revisions)
- After a major revision in response to reviewer comments
- When you've added or removed figures from the paper
- When you've added or replaced bib entries
- Before sharing the book URL externally — sanity check that it still matches the paper

## When NOT to use

- The book doesn't exist yet (`/init-paper-book`)
- The paper hasn't actually changed (no point)
- You want a full re-write, not a sync (delete the book + `/init-paper-book` is faster)

## Inputs accepted

```
/audit-paper-book <slug>              # report only, no writes (default)
/audit-paper-book <slug> --apply      # apply mechanical fixes (bib + figures); report substantive drift
/audit-paper-book <slug> --dry-run    # alias for default; explicit no-write
```

## Pre-flight (block-on-fail)

```bash
SLUG="<resolved-slug>"

# 1. Book must exist in vault
[[ -d ~/Research-Vault/books/"$SLUG" ]] || die "No book at vault. Use /init-paper-book."

# 2. Registry entry must exist
grep -q "^${SLUG}:" ~/Research-Vault/books/index.yaml \
    || die "${SLUG} not in books/index.yaml. Add a registry entry first."

# 3. Atlas topic + project_path must resolve.
#    Hard Rule 4 (from /init-paper-book): book slug MUST equal atlas topic
#    filename. The registry's `atlas_topic:` field is the source of truth — its
#    leaf must match the book slug exactly. Drift here is an existential
#    failure; the book and atlas are no longer the same artefact.
ATLAS_TOPIC_REF=$(awk -v slug="$SLUG" '
    $0 ~ "^"slug":" {in_block=1; next}
    in_block && /^[a-z]/ {in_block=0}
    in_block && /^[[:space:]]+atlas_topic:/ {gsub(/[",'\'']/, ""); print $2; exit}
' ~/Research-Vault/books/index.yaml)
ATLAS_TOPIC_LEAF="${ATLAS_TOPIC_REF##*/}"
[[ "$ATLAS_TOPIC_LEAF" == "$SLUG" ]] \
    || die "SLUG DRIFT: book '${SLUG}' points at atlas topic '${ATLAS_TOPIC_LEAF}'. Rename one side so they match (Hard Rule 4). See /init-paper-book SKILL.md."

ATLAS_TOPIC=$(find ~/Research-Vault/atlas -name "${SLUG}.md" -type f | head -1)
[[ -n "$ATLAS_TOPIC" ]] \
    || die "No atlas topic file at ~/Research-Vault/atlas/*/${SLUG}.md. Either rename the book to match an existing atlas topic, or create the missing topic via /init-project-research."
PROJECT_PATH=$(grep -E "^project_path:" "$ATLAS_TOPIC" | cut -d' ' -f2- | tr -d "'\"")
RR=$(cat ~/.config/task-mgmt/research-root)
[[ -d "$RR/$PROJECT_PATH" ]] || die "project_path in atlas does not resolve."

# 3a. Project-path leaf should also match the slug (warn, don't block — some
#     projects have been renamed historically and only the book + atlas leaf
#     are required to match).
PROJECT_LEAF=$(basename "$PROJECT_PATH")
[[ "$PROJECT_LEAF" == "$SLUG" ]] \
    || warn "PROJECT-DIR DRIFT: project_path leaf '${PROJECT_LEAF}' differs from book slug '${SLUG}'. Not a hard violation but worth aligning if the book is being actively maintained."

# 4. Paper tex + bib must exist
PAPER_DIR=$(ls -d "$RR/$PROJECT_PATH"/paper-* 2>/dev/null | head -1)
PAPER_TEX="$PAPER_DIR/paper/main.tex"; [[ -f "$PAPER_TEX" ]] || PAPER_TEX="$PAPER_DIR/backup/main.tex"
PAPER_BIB=$(find "$PAPER_DIR" -maxdepth 3 -name "*.bib" | head -1)
[[ -f "$PAPER_TEX" ]] || die "No main.tex in paper dir."
[[ -f "$PAPER_BIB" ]] || warn "No bib in paper dir."
```

## Phases

```
Phase 1: Diff inventory    (compare paper assets to book vault)
Phase 2: Accessibility     (acronyms, equation-prose pairing, jargon density)
Phase 3: Classify          (mechanical / numeric / structural / accessibility / new-content)
Phase 4: Apply or report   (--apply: mechanical fixes; otherwise report-only)
Phase 5: Verify            (atlas reload + chapter smoke test if --apply ran)
```

### Phase 1: Diff inventory

See [`references/phase-1-diff-inventory.md`](references/phase-1-diff-inventory.md) for detailed diff protocols (bibliography, figures, numeric drift, section structure, Overleaf-link transitions, masthead format drift, citation-URL drift).

### Phase 2: Accessibility check

See [`references/phase-2-accessibility.md`](references/phase-2-accessibility.md) for detailed accessibility floor checks (acronym expansion, equation-prose pairing, jargon density, sentence length). This phase always runs (regardless of `--apply`).

### Deterministic implementation — `scripts/batch_audit.py`

Phase 1 + Phase 2's deterministic checks are implemented in `scripts/batch_audit.py`. It reads the book registry, resolves each book's `paper_tex` via the atlas topic's `project_path`, and produces a per-book report at `~/Research-Vault/books/<slug>/.audit-report-<date>.md`.

```bash
# Audit all 9 books
~/Task-Management/packages/atlas-workspace/.venv/bin/python \
    ~/.claude/skills/audit-paper-book/scripts/batch_audit.py

# Audit one book
~/Task-Management/packages/atlas-workspace/.venv/bin/python \
    ~/.claude/skills/audit-paper-book/scripts/batch_audit.py <slug>
```

What the script gets right:
- **Bib drift** is computed from `\cite{}` keys in `main.tex` (and any `\input{}`-expanded section files), not from a guessed `.bib` filename. Avoids the common "wrong scratch bib" false positive.
- **Numeric drift** normalises Unicode `±` ↔ LaTeX `\pm`, `%` ↔ `\%`, leading-zero variants (`.91` ↔ `0.91`), and whitespace around `±` before declaring a mismatch. Also skips tokens preceded by `§`, `Section`, `Eq.`, `Fig.`, `Table` (those are cross-references, not numeric claims).
- **Structural drift** parses paper section numbering by walking `\section{}` / `\subsection{}` linearly (handles `\appendix` reset). Extracts `§X.Y` refs from book chapters and flags any that don't resolve.
- **Accessibility** accepts both `Full Form (ACRONYM)` and `ACRONYM (Full Form)` expansion forms, and skips all-caps tokens that only appear inside markdown table rows (column headers).

What still needs human judgement:
- Numeric drift hits may still include formatting edge cases (e.g. paper uses `$\mathbf{2.82 \pm 1.4}$` vs book bare-text version).
- Accessibility allow-list is global; per-domain acronyms (e.g. MOO, MOEA, RVEA, SBX for evolutionary-algorithm books) may need extension. Edit `ACRONYM_ALLOW` at the top of the script.
- Semantic claim-scope check (paper §X.Y says something the book misstates) is **not** implemented here — that's a Phase 3.5-style LLM sub-agent call, not a regex pass.

### Phase 3: Classify

Each drift item lands in one of six buckets:

| Bucket | What it means | --apply behaviour |
|---|---|---|
| **Mechanical** | New bib entries; new figure files; identical-name figures with different content | Auto-applied |
| **Overleaf-link** | Add / remove / update the masthead Overleaf-source line per status | Auto-applied (one-line edit to `intro.md`) |
| **Format-convention** | Blockquote masthead → definition-list migration; redundant body H1 stripped; missing required field reported | Migration + H1 strip auto-applied; missing field reported |
| **Citation-URL** | Hand-constructed `/paper/<key>` link inside chapter prose | Reported with chapter+line; never auto-applied (replacement requires choosing cite-t vs cite-p form) |
| **Numeric** | A number in the book no longer appears in the paper, or vice versa | Reported, never auto-applied |
| **Structural** | Section heading renamed; new section added in paper; old section removed | Reported with suggested action ("Update `method.md` to mention §4.5 on the new selection rule") |
| **Accessibility** | Acronym not expanded; display equation with no prose reading; jargon-dense sentence | Reported with chapter+line; never auto-applied (prose edits require user judgement) |
| **New content** | Paper has a new theorem, definition, or claim with no echo in any book chapter | Reported with suggested chapter target |

**Overleaf-link is mechanical** because the rule is deterministic: status ∈ accepted-set → remove; status in-flight + link in atlas → ensure present; URL changed → propagate. No editorial judgement.

**Format-convention items are mechanical** because the transformations are deterministic: blockquote masthead → definition-list (preserving field values), body H1 → strip the line. They never touch claims or numbers, only structural markup.

### Phase 4: Apply (only with --apply) or report

See [`references/phase-4-apply-logic.md`](references/phase-4-apply-logic.md) for apply logic (bib copy, figure replacement, masthead updates, format-convention migrations). Write the audit report to `~/Research-Vault/books/<slug>/.audit-report-YYYY-MM-DD.md` so the user has a record of what was applied + what's still pending.

### Phase 5: Verify (if --apply ran OR --visual-check passed in)

See [`references/phase-5-verify-smoke-tests.md`](references/phase-5-verify-smoke-tests.md) for HTTP smoke-test and mandatory Playwright visual verification logic.

## Report format

See [`references/report-format-template.md`](references/report-format-template.md) for canonical audit report structure (summary table, mechanical fixes, drift buckets, next actions).

## Anti-patterns

- **Auto-applying numeric changes.** If a number changed, the user must decide whether the book's old explanation still applies. Auto-update silently corrupts the book.
- **Auto-renaming chapters.** Chapter renames cascade through the registry, atlas, and any external links. Always user-triaged.
- **Skipping the report when applying.** Even if `--apply` succeeds, the report logs what was changed (audit trail).

## Logging

Append outcome to `~/.claude/ecc/skill-outcomes.jsonl`:

```bash
mkdir -p ~/.claude/ecc && echo '{"skill":"audit-paper-book","timestamp":"'"$(date -u +%Y-%m-%dT%H:%M:%SZ)"'","outcome":"success","session":"'"${CLAUDE_SESSION_ID:-}"'","project":"'"$(basename "$PWD")"'","note":""}' >> ~/.claude/ecc/skill-outcomes.jsonl
```


---

## beamer-deck

**Source:** `skills/beamer-deck/SKILL.md`

---
name: beamer-deck
description: "Use when you need to create an academic Beamer presentation with original theme and multi-agent review."
allowed-tools: Bash(latexmk*), Bash(xelatex*), Bash(pdflatex*), Bash(biber*), Bash(bibtex*), Bash(mkdir*), Bash(ls*), Bash(R*), Bash(Rscript*), Bash(python*), Read, Write, Edit, Task
argument-hint: [topic, content-path, or project-name]
---

# Beamer Deck Skill

> Generate academic Beamer presentations with original themes, rhetoric-driven structure, and multi-agent review. Internalises Scott Cunningham's rhetoric framework and implements an adversarial review workflow.

## Purpose

Create polished, zero-warning Beamer decks for academic contexts: seminars, conference talks, teaching lectures, and working decks for coauthors. Every deck gets a custom theme, assertion-driven titles, and parallel review by rhetoric and graphics sub-agents.

**NOT for project status updates** — use `/project-deck` for those.

## When to Use

- Academic seminar presentations
- Conference talks (15–45 min)
- Teaching lectures (undergraduate or PhD)
- Working decks for coauthors or supervisors
- Any presentation that needs rhetoric discipline and visual quality

---

## Critical Rules

1. **Build artifacts go to `out/`, PDF stays in the source directory.** Create `.latexmkrc` with `$out_dir = 'out'` and an `END {}` block to copy the PDF back if missing. Use `/latex` for compilation — it handles error resolution automatically. See `/latex` for manual config details.
2. **Python:** Always use `uv run python`. Never bare `python`, `python3`, `pip`, or `pip3`.
2. **Fix ALL warnings.** Overfull hbox, underfull hbox, overfull vbox, underfull vbox — no matter how small. Parse the `.log` file. Recompile until clean.
3. **Titles are assertions, not labels.** "Distance increases abortion rates" — not "Results". Every frame title states a claim.
4. **One idea per slide.** Not a guideline. A law. If a slide has two ideas, split it.
5. **Use the unified template.** Always use `\usepackage[<institution>]{user-beamer}` from `templates/beamer/`. Options: `warwick`, `southampton`, `bath`, `lse`, `plain`. Never use default Beamer themes (Warsaw, Madrid, etc.) as-is, and never create one-off preambles. See [`templates/beamer/README.md`] for available custom commands and how to add institutions.
6. **Code-first figures.** Generate figures via R or Python scripts before inserting. Never use placeholder images. **Always save the script alongside the figures** — never generate a figure without preserving the code that created it.
7. **If a `.bib` file is used, validate it.** Cross-reference all `\cite{}` keys against the bibliography file. See `/bib-validate` for the full protocol.
8. **Never define parameterized TikZ styles inside a frame.** `#` inside a Beamer frame body is consumed by the frame parser before TikZ sees it, producing `Illegal parameter number` errors that cascade and resist all downstream fixes. Define ALL `\tikzset{...}` and `.style={..., #1}` entries in the preamble; use them inside frames. See [`../shared/tikz-rules.md`](../shared/tikz-rules.md) Rule 11.

---

## Rhetoric Principles

Full framework (Three Laws, MB/MC, Aristotelian Triad, Narrative Arc, Pyramid Principle, Devil's Advocate): [`../shared/rhetoric-principles.md`](../shared/rhetoric-principles.md)

Scott's original essay: `resources/academics/scott-cunningham/MixtapeTools/presentations/rhetoric_of_decks.md`

---

## Quality Scoring

Apply numeric quality scoring using the shared framework and skill-specific rubric:

- **Framework:** [`../shared/quality-scoring.md`](../shared/quality-scoring.md) — severity tiers, thresholds, verdict rules
- **Rubric:** [`references/quality-rubric.md`](references/quality-rubric.md) — issue-to-deduction mappings for this skill

Start at 100, deduct per issue found, apply verdict. Compute the score in Phase 7 and report it in the final output.

## Context-Specific Guidance

See [`../shared/rhetoric-principles.md`](../shared/rhetoric-principles.md) for the full Aristotelian Triad framework. Context-specific Ethos/Pathos/Logos balance and adjustments are applied in Phase 2 based on audience type (academic seminar, conference talk, teaching lecture, working deck).

---

## Workflow: 7 Phases

```
You (orchestrator)
├── Phase 1: Gather context        (direct)
├── Phase 2: Design structure       (direct)
├── Phase 3: Build deck             (direct)
├── Phase 4: Fix all warnings       (direct)
├── Phase 5: Rhetoric review        (sub-agent — Explore)
├── Phase 6: Graphics review        (sub-agent — Explore)  ← parallel with Phase 5
└── Phase 7: Apply & finalise       (direct)
```

### Phase 1: Gather Context (Direct)

Read project files, content sources, and audience brief. Ask the user clarifying questions:

- **Audience**: Who is this for? (seminar, conference, teaching, coauthors)
- **Duration**: How long is the talk?
- **Content source**: Paper draft? Notes? Existing slides? Code output?
- **Special requirements**: Specific figures, institutional branding, language?

Check for existing `.bib` files in the project. If citations are needed, note this for Phase 3.

### Phase 2: Design Structure (Direct)

1. **Choose rhetoric balance** based on audience (see table above)
2. **Outline slide sequence** with assertion titles — write each title as a claim
3. **Plan narrative arc** — consult [`docs/reference/talk-design.md`](../../docs/reference/talk-design.md) for format-specific arcs (empirical, structural, theory, descriptive) and audience calibration
4. **Choose institution option** for `user-beamer` — colours and fonts are set by the template
5. **Identify figures needed** — which need to be generated via code?

Present the outline to the user for approval before building.

### Phase 3: Build Deck (Direct)

1. **Generate figures first** — run R/Python scripts, save to `figures/`
2. **Write `.tex` file** using the unified template: `\documentclass[aspectratio=169,11pt]{beamer}` + `\usepackage[warwick]{user-beamer}` (or other institution option). Use `\fbinstitute` and `\fbemail` for metadata. Custom commands: `\contribcard`, `\phasecircle`, `\accentbox`, `\highlightbox`, `standoutframe` environment.
3. **Use 16:9 aspect ratio** (already in the documentclass above)
4. **Create `.latexmkrc`** if not present (`$out_dir = 'out'` + `END {}` block to copy PDF back)
5. **Compile using `/latex`** — this handles missing packages, font conflicts, citation key mismatches, and stale cache automatically
6. **If using citations**: add `\addbibresource{references.bib}` or `\bibliography{}` as appropriate

### Phase 4: Fix All Warnings (Direct)

After `/latex` resolves errors, address remaining **warnings** (which autofix does not fix):

1. Parse `out/*.log` for overfull/underfull hbox/vbox warnings
2. Fix every single one — adjust text, resize figures, tweak `\parbox`, etc.
3. Recompile
4. Repeat until the log is clean

**Circuit breaker — do not spiral.** If the same compile error persists after **3 different fix attempts**, STOP. Do not try a fourth approach. Instead:

1. Stop editing the `.tex` file.
2. Quote the exact error line from the `.log`.
3. List the 3 approaches tried and why each failed.
4. Ask the user how to proceed.

What counts as "the same error": any error that persists at the same line family after a fix (e.g., `Illegal parameter number` moving from line 568 to 572 is still the same error — that is the diagnostic signature in tikz-rules.md Rule 11). A fresh Overfull on a different slide after fixing the first is a *new* error — reset the counter.

The cost of stopping is 2 minutes; the cost of spiraling is an hour of edits that progressively obscure the original cause. This rule overrides "recompile until clean" — zero tolerance for warnings does not mean infinite attempts on the same fix.

**"Compilation success does not mean visual success."** Also check for silent visual errors:
- TikZ: shape constraints forcing label misplacement, coordinate misalignment. **If the deck contains TikZ diagrams**, run the 6-pass verification from [`../shared/tikz-rules.md`](../shared/tikz-rules.md) — compute Bezier depths, check gaps, verify label fit, check shape boundary clearance.
- matplotlib/ggplot: axis labels cut off, legend obscuring data, text sizing. **If figures use curved arrows (`arc3`)**, compute Bézier positions using the helper functions in `../shared/tikz-rules.md` § Matplotlib Extension — never guess where curves pass. Check label-to-shape clearance (Boundary Rule) and use anchor-based centering for text pairs.
- **PDF visual inspection**: Run `uv run python scripts/pdf-to-images.py <deck>.pdf` to convert pages to images, then inspect each image for text overflow, element overlap, font readability, and alignment issues that are invisible in the log

### Phase 5: Rhetoric Review (Sub-Agent — Explore)

Launch a sub-agent to review the `.tex` file against 7 criteria: narrative arc, MB/MC balance, title quality, one-idea-per-slide, transitions, Aristotelian balance, and pyramid principle.

Full prompt template: [`references/review-prompts.md`](references/review-prompts.md) § Rhetoric Review

### Phase 6: Graphics Review (Sub-Agent — Explore)

Launch **in parallel with Phase 5**. Reviews TikZ diagrams, figure sizing, table formatting, colour consistency, typography, and numerical accuracy.

Full prompt template: [`references/review-prompts.md`](references/review-prompts.md) § Graphics Review

### Phase 7: Apply and Finalise (Direct)

1. Read both reviewer reports
2. Incorporate feedback — prioritise Critical and Needs Work items
3. Recompile
4. Verify zero warnings in the log
5. **If using a `.bib` file**: validate all `\cite{}` keys resolve correctly (check log for `Citation .* undefined`). See `/bib-validate` for the full cross-referencing protocol.
6. If significant changes were made, loop back to Phase 5 for another review round
7. **Compute quality score** — read `references/quality-rubric.md`, log all issues from Phases 4-6, compute score and verdict
8. Confirm final PDF is in the source directory (copied from `out/` by `.latexmkrc`)

---

## Reference Palettes

Three starting palettes (Professional, Energetic, Academic) in both LaTeX and CSS formats: [`../shared/palettes.md`](../shared/palettes.md)

Use as inspiration — always create an original palette for each deck.

---

## Output Checklist

A completed deck directory should contain:

```
project/
├── deck.tex              # Main Beamer file (uses user-beamer.sty)
├── deck.pdf              # Compiled PDF (copied from out/ by .latexmkrc)
├── .latexmkrc            # Output directory config
├── out/                  # Build artifacts only
├── figures/              # Generated figures (if any)
│   ├── figure_1.png
│   └── ...
├── scripts/              # R/Python scripts that generated figures (if any)
│   ├── figure_1.R
│   └── ...
└── references.bib        # Bibliography (if citations used)
```

- [ ] PDF compiles with zero warnings
- [ ] All frame titles are assertions
- [ ] One idea per slide
- [ ] Narrative arc: Problem → Investigation → Resolution
- [ ] Rhetoric review completed (Phase 5)
- [ ] Graphics review completed (Phase 6)
- [ ] If `.bib` used: all `\cite{}` keys validated (see `/bib-validate`)
- [ ] Quality score computed and reported

---

## Cross-References

| Skill | When to use instead/alongside |
|-------|-------------------------------|
| `/project-deck` | For project status updates (supervisor meetings, coauthor handoffs) |
| `/latex` | **Default compiler** — used in Phase 3 for error resolution and citation audit |
| `/latex` | For manual compilation config details, `.latexmkrc` setup, engine selection |
| `/proofread` | For post-hoc review of text quality in the deck |
| `/bib-validate` | For thorough bibliography cross-referencing when citations are used |
| `/literature` | For finding and verifying citations to include |
| `/quarto-deck` | For HTML presentations (teaching, informal talks) instead of PDF |
| `/quarto-course` | For full course websites with multiple lectures, exercises, and navigation |

**Scott's full rhetoric essay:** `resources/academics/scott-cunningham/MixtapeTools/presentations/rhetoric_of_decks.md`
**Scott's deck generation prompt:** `resources/academics/scott-cunningham/MixtapeTools/presentations/create_deck_prompt.md`
**Scott's example decks:** `resources/academics/scott-cunningham/MixtapeTools/presentations/examples/`


---

## bib-validate

**Source:** `skills/bib-validate/SKILL.md`

---
name: bib-validate
description: "Cross-reference \\cite{} keys against .bib files or embedded \\bibitem entries. Finds missing, unused, and typo'd citation keys. Deep verification mode spawns parallel agents for DOI/metadata validation at scale. Fix mode auto-adds missing entries to Paperpile."
allowed-tools: Read, Glob, Grep, Task, Write, Bash(mkdir*), Bash(ls*), Bash(rm*), Bash(paperpile*)
argument-hint: "[project-path or tex-file] [--verify-doi] [--fix]"
---

# Bibliography Validation

**LIBRARY-FIRST RULE: ALWAYS cross-reference cited keys against Paperpile (`paperpile search-library`) during validation.** This catches drift between the `.bib` file and the reference manager. See the Reference Manager Cross-Reference section.

## Output Path

Per `rules/review-artefact-routing.md` (auto-loads in research projects (path-scoped to `paper-*/` and `paper/`)):

- **Source slug:** `bib-validate`
- **Write reports to:** `reviews/bib-validate/YYYY-MM-DD.md` inside the project. Path is relative to the research project root, not the Task-Management repo.
- **Never** at project root (`./CRITIC-REPORT.md`-style filenames are forbidden — pre-rule layout).
- **Idempotency:** if today's file exists, append a same-day descriptor (`{date}-revision.md`, `{date}-r2.md`, `{date}-pre-submission.md`) — never overwrite.
- **Index update:** if `reviews/INDEX.md` exists, write a one-line entry under "Latest per source" pointing at the new file. Otherwise `/review-recap` will rebuild the index next time it runs.
- **Infrastructure repos** (Task-Management, atlas-workspace, etc.): this section does not apply — the path-scoped rule won't load there.


## Modes

| Invocation | Behaviour |
|---|---|
| `/bib-validate` | Standard: cross-reference \cite{} ↔ .bib, library check, preprint staleness |
| `/bib-validate --verify-doi` | **Adds DOI resolution**: each `@article`/`@inproceedings` entry gets its DOI checked via `scholarly scholarly-verify-dois`. Bib entries with no DOI or unresolvable DOIs are flagged. Use before submission to catch fabricated/hallucinated entries. |
| `/bib-validate --fix` | Auto-adds missing entries to Paperpile via `paperpile create-entry` |
| Combine: `--verify-doi --fix` | Verify, then fix unverified entries by re-fetching from Crossref |

## When to Use

- Before compiling a final version of a paper
- After adding new citations to check nothing was missed
- When `biber`/`bibtex` reports undefined citations
- As part of a pre-submission checklist (pair with `/proofread`)

## When NOT to Use

- **Finding new references** — use `/literature` for discovery
- **Building a bibliography from scratch** — use `/literature` with `.bib` generation
- **General proofreading** — use `/proofread` (which also flags citation format issues)

## Phase 0: Session Log (Suggested)

Bibliography validation with preprint staleness checks can be context-heavy (OpenAlex lookups, web searches for published versions). Before starting, **suggest** running `/session-log` to capture prior work as a recovery checkpoint. If the user declines, proceed without it.

## Convention

**Default bibliography file is `references.bib`** — this is the standard across all projects (per the `/latex` skill convention). However, the skill also supports:

- Any `.bib` file found in the same directory as the `.tex` files being audited
- Embedded bibliographies using `\begin{thebibliography}` / `\bibitem{key}` blocks
- Both external and embedded simultaneously (rare but possible)

## Bibliography Detection

At the start of validation, detect which bibliography method the project uses:

### 1. External `.bib` file (standard)

Look for `.bib` files in the project directory. Priority order:
1. `references.bib` (preferred — standard naming convention across all projects)
2. Any other `.bib` file in the same directory as the `.tex` files

If **multiple `.bib` files** are found, validate all of them and produce a combined report. Note which file each issue belongs to. If a legacy-named `.bib` file (e.g., `paperpile.bib`) exists alongside `references.bib`, flag it as a potential cleanup opportunity (the project may have migrated from Paperpile).

Full validation applies: cross-reference checks **and** quality checks.

### 2. Embedded `\begin{thebibliography}` / `\bibitem{key}`

Some LaTeX documents define references inline rather than using an external `.bib` file. Detect by scanning `.tex` files for `\begin{thebibliography}`.

Extract keys from `\bibitem` entries:
- `\bibitem{key}` — standard form, key is the argument in braces
- `\bibitem[label]{key}` — optional label form (e.g., `\bibitem[Smith et al., 2020]{smith2020}`), key is in the **second** set of braces

Only **cross-reference checks** apply (missing keys, unused keys, typos). Quality checks (required fields, year, author formatting) are **skipped** because embedded bibliographies don't have structured metadata.

### 3. Both (rare)

If a project has both a `.bib` file and `\begin{thebibliography}` blocks, validate both:
- Run full validation on the `.bib` file
- Run cross-reference checks on `\bibitem` entries
- Merge both key sets when checking for missing citations

## Workflow

1. **Find files**: Locate all `.tex` files in the project
2. **Detect bibliography type**: Check for `.bib` files and/or `\begin{thebibliography}` blocks
3. **Extract citation keys from .tex**: Scan for all citation commands
4. **Extract entry keys from bibliography source(s)**:
   - External: Parse all `@type{key,` entries from `.bib` file(s)
   - Embedded: Parse all `\bibitem{key}` and `\bibitem[label]{key}` entries
5. **Cross-reference**: Compare the two sets
6. **Quality checks**: Validate `.bib` entry completeness (external only)
7. **Produce report**: Write results to stdout (or save if requested)

## Citation Commands to Scan

Scan `.tex` files for all of these patterns:

| Command | Example |
|---------|---------|
| `\cite{key}` | Basic citation |
| `\citet{key}` | Textual: Author (Year) |
| `\citep{key}` | Parenthetical: (Author, Year) |
| `\textcite{key}` | biblatex textual |
| `\autocite{key}` | biblatex auto |
| `\parencite{key}` | biblatex parenthetical |
| `\citeauthor{key}` | Author name only |
| `\citeyear{key}` | Year only |
| `\nocite{key}` | Include in bibliography without in-text citation |

Also handle **multi-key citations**: `\citep{key1, key2, key3}`

## Cross-Reference Checks

### Critical: Self-citation deanonymization (double-blind submissions only)

When `--double-blind` is set OR when a `paper-*` directory's vault submission frontmatter shows the venue is double-blind, run a self-citation scan in addition to the standard checks.

1. **Load submission author list.** Read `~/Research-Vault/submissions/<paper-slug>-<venue>-<year>.md` `authors:` / `coauthors:` field. If absent, prompt: `Submission author surnames (comma-separated):`. Refuse to proceed without a non-empty list.
2. **For each `.bib` entry, parse the `author = {...}` field.** Tokenize by `and` and extract surnames.
3. **Compare against the submission author list.** If the cited entry's author surnames are a *subset* of the submission's (or the cited entry has authors that exactly match), flag the citation.
4. **Severity: Critical.** Self-citation by name is a desk-reject trigger at every major double-blind security/ML venue (CCS, NDSS, S&P, USENIX, ICML, NeurIPS, ICLR). Third-person grammar in the body text alone does NOT cure the issue when the bib entry itself names the authors — see `_shared/double-blind-anonymity-checklist.md` §P4.
5. **Output format:**
   ```
   ⚠ SELF-CITATION DEANONYMIZATION (Critical)
     references.bib:42  burnat2026paradox
       authors:    the user A D Burnat and Brittany I [Collaborator]
       overlaps:   Burnat (1/1), [Collaborator] (1/1) → ALL submission authors named
       remediation:
         author = {Anonymized for double-blind review},
         title  = {Title withheld; preprint anonymized},
         note   = {Anonymized self-citation}
       AND in the body text, replace any "Burnat and [Collaborator] [N]" with
                            "Prior work by the authors [N]" or similar.
   ```
6. **Also scan `.tex` body** near each flagged `\cite{<key>}` for any of the cited entry's surnames within ±200 chars. Flag those occurrences with file:line so the user can de-name the prose alongside the bib fix.

This check is a desk-reject prevention gate (see incident log in `_shared/double-blind-anonymity-checklist.md`). Run it before the standard cross-reference checks so the user sees the most-severe finding first.

### Critical: Missing Entries

Citation keys used in `.tex` but not defined in the bibliography source (`.bib` file or `\bibitem` entries).

These will cause compilation errors.

### Warning: Unused Entries

Keys defined in the bibliography source but never cited in any `.tex` file.

Not errors, but may indicate:
- Forgotten citations (should they be `\nocite`?)
- Leftover entries from earlier drafts
- Entries intended for a different paper

### Warning: Possible Typos (Fuzzy Match)

For each missing key, check if a similar key exists in the bibliography using edit distance:
- Edit distance = 1: Very likely a typo
- Edit distance = 2: Possibly a typo
- Flag these with the suggested correction

Common typo patterns:
- Year off by one: `smith2020` vs `smith2021`
- Missing/extra letter: `santanna` vs `sant'anna` vs `santana`
- Underscore vs camelCase: `smith_jones` vs `smithjones`

## Reference Manager Cross-Reference

After the disk-based cross-reference, check each cited key against Paperpile. Produces a status table (HEALTHY / DRIFT / EXPORT_GAP / MISSING).

Full steps, MCP calls, and status categories: [`references/ref-manager-crossref.md`](references/ref-manager-crossref.md)

## Quality Checks on .bib Entries

**These checks apply only to external `.bib` files.** Embedded bibliographies lack structured metadata, so quality checks are skipped for them.

### Required Fields by Entry Type

| Entry Type | Required Fields |
|-----------|----------------|
| `@article` | author, title, journal, year |
| `@book` | author/editor, title, publisher, year |
| `@incollection` | author, title, booktitle, publisher, year |
| `@inproceedings` | author, title, booktitle, year |
| `@techreport` | author, title, institution, year |
| `@unpublished` | author, title, note, year |
| `@phdthesis` | author, title, school, year |

### Year Reasonableness

- Flag entries with year < 1900 or year > current year + 1
- Flag entries with no year at all

### Author Formatting

- Check for inconsistent author formats within the file
- **Flag entries where author field contains "and others" or "et al."** — this is never valid in BibTeX. All authors must be listed explicitly. Severity: **Warning**.
- Flag entries with organisation names that might need `{{braces}}` to prevent splitting

### DOI Verification & Fabrication Detection

See [`references/doi-verification.md`](references/doi-verification.md) for hard rules, resolution protocol, and LLM-hallucination detection.

### Preprint Staleness Check

**For every entry that looks like a preprint**, check whether a peer-reviewed version has since been published. Full detection signals, lookup protocol, and classification: [`references/preprint-check.md`](references/preprint-check.md)

## Severity Levels

| Level | Meaning |
|-------|---------|
| **Critical** | Missing entry for a cited key — will cause compilation error |
| **Warning** | Unused entry, possible typo, missing required field |
| **Info** | Year oddity, formatting suggestion, bibliography type note |

## Bibliography Output

After validation, offer these actions if applicable:

- **Embedded bibliography → offer to create `references.bib`**: If the project uses `\begin{thebibliography}`, offer to extract the references into a proper `references.bib` file (one `@misc` entry per `\bibitem`, with the full text as a `note` field). The author can then enrich the entries with proper metadata.
- **Non-standard `.bib` name → offer to rename**: If the existing `.bib` file is not named `references.bib`, offer to rename it to `references.bib` and update the `\bibliography{}` command in the `.tex` file.

These are **offers only** — do not make changes without explicit confirmation.

## Report Format

Full report template with all sections: [`references/report-template.md`](references/report-template.md)

Sections: Summary table → Critical (missing entries) → Warning (typos, unused, missing fields, DOI mismatches, stale preprints) → Info (year issues) → Limitations (for embedded bibliographies).

## Optional: Metadata Verification

See [`references/metadata-verification.md`](references/metadata-verification.md) for Paperpile and scholarly CLI lookup workflows.

## Deep Verification Mode (Parallel, Disk-Based)

See [`references/deep-verify-protocol.md`](references/deep-verify-protocol.md) for auto-trigger thresholds (≥40 entries) and sub-agent architecture.

## Council Mode (Optional)

For high-stakes submissions. Trigger: "council bib-validate", "thorough bib check". Full details: [`references/council-mode.md`](references/council-mode.md)

## Fix Mode

After producing the validation report, automatically fix resolvable issues (DRIFT → stage as BibTeX for Paperpile import, MISSING → search + add, MIGRATE → auto-add, metadata → correct BibTeX).

Full auto-fix actions, post-fix maintenance, and skip conditions: [`references/fix-mode.md`](references/fix-mode.md)

## Quality Scoring

When producing a full validation report, apply numeric quality scoring using the shared framework:

- **Framework:** [`../shared/quality-scoring.md`](../shared/quality-scoring.md) — severity tiers, thresholds, verdict rules

Map validation findings to the framework tiers:
- **Critical** (-15 to -25): Missing entry for a cited key (compilation error)
- **Major** (-5 to -14): DOI mismatch, **likely fabricated reference** (LLM-drafted hallucination), stale preprint with published version available, "et al." in author field
- **Minor** (-1 to -4): Missing optional fields, year oddities, unused entries

Compute the score and include the Score Block in the report after the summary table.

## Log to REVIEW-STATE.md (final step)

Write the bib-validate report to `reviews/bib-validate/<YYYY-MM-DD-HHMM>.md` (`mkdir -p reviews/bib-validate/` first). Then append a row to the project's `REVIEW-STATE.md`:

```bash
bash ~/.claude/skills/_shared/review-state-log.sh \
  --check bib-validate \
  --paper "<paper-{venue} dir>" \
  --verdict "<PASS|ISSUES FOUND>" \
  --score "<numeric score from quality-scoring framework, or —>" \
  --open-issues "<missing-plus-unused-plus-typo-count>/<missing-plus-unused-plus-typo-count>" \
  --report "reviews/bib-validate/<YYYY-MM-DD-HHMM>.md" \
  --notes "<one-line: e.g. '2 missing keys, 5 unused; 1 likely fabricated'>" \
  [--trigger "pre-submission-report|review-cluster"]
```

- Verdict: PASS if no missing/unused/typo'd citations; ISSUES FOUND otherwise.
- Score: the numeric quality score if computed; `—` otherwise.
- Open issues: total of (missing + unused + typo'd) at run time.
- Trigger: pass orchestrator name only if invoked via `/pre-submission-report` or `/review-cluster`. Otherwise omit.

Schema: `~/Task-Management/docs/reference/review-state-schema.md`.

## Cross-References

- **`/proofread`** — For overall paper quality including citation format
- **`/literature`** — For finding and adding new references (includes full OpenAlex workflows)
- **`/bib-coverage`** — Compare project `.bib` vs Paperpile label — find uncited papers and unfiled references
- **`/latex`** — For compilation with reference checking
- **`/latex`** — For compilation and error resolution. Run after fixing bibliography issues to verify citations compile cleanly.
- **`shared/reference-resolution.md`** — Canonical lookup + filing sequence used by Ref Manager Cross-Reference and Fix Mode


---

## code-archaeology

**Source:** `skills/code-archaeology/SKILL.md`

---
name: code-archaeology
description: "Use when you need to review and understand old code, data, or analysis files."
allowed-tools: Bash(ls*), Bash(cp*), Bash(mkdir*), Bash(git*), Read, Write, Edit, Glob, Grep
argument-hint: [project-path]
---

# Code Audit Skill

**CRITICAL RULE: Never delete data or code files.** Copy to legacy/, never move or delete originals.

> Systematically review and understand old code, data, and analysis files.

## Purpose

Based on Scott Cunningham's workflow of reviving old projects - understanding what exists, documenting it, and making it safe to work with.

**For formal audits with cross-language replication and referee reports, use the Referee 2 agent (`.claude/agents/referee2-reviewer.md`).** This skill is for understanding and documenting existing code, not formal verification.

## When to Use

- Returning to an old project after months/years
- Taking over code from a coauthor
- Before extending existing analysis
- R&R requiring you to revisit old work

## When NOT to Use

- **Brand new projects** — use project-safety skill instead to set up structure
- **Formal code verification** — use the Referee 2 agent for cross-language replication
- **Quick code questions** — just ask directly, no need for full audit

## Workflow

1. **Explore the directory**:
   - What files exist?
   - What's the structure?
   - When were things last modified?

2. **Understand the pipeline**:
   - What are the main scripts?
   - What order do they run in?
   - What data do they use?
   - What outputs do they produce?

3. **Document findings**:
   - Create/update README.md
   - Map data flows
   - Note dependencies

4. **Establish safety**:
   - Create legacy/ folder
   - Copy (don't move) originals
   - Set up version control if not present

5. **Create audit report**:
   - What the code does
   - Potential issues found
   - Recommendations for cleanup

## Safety Rules (from Scott Cunningham)

```markdown
1. Never delete data. Under no circumstances.
2. Never delete programs. No do-files, no R scripts, nothing.
3. Stay in this folder. Can go down, not up.
4. Use a legacy folder. Move originals there for safekeeping.
5. Copy, don't move. When reorganising, always copy from legacy.
```

## Prompt Template

```
I'm returning to an old project after [TIME]. Please help me understand what's here.

1. Explore the directory and tell me what you find
2. Identify the main analysis scripts and their order
3. Map the data pipeline (inputs → processing → outputs)
4. Note any potential issues (missing files, unclear code, etc.)
5. Create a README documenting everything

Before making ANY changes, create a legacy/ folder and copy everything there.
```

## Data Flow Mapping

Understand how data moves through the project:
- What raw data files exist?
- What cleaning/transformation scripts run?
- What intermediate files are created?
- What outputs are generated?

## Compare Datasets (if multiple versions exist)

When you find multiple versions of the same data:
- Side-by-side comparison of key variables
- Identify where datasets diverge
- Visualize differences geographically/temporally
- Document which version to use going forward

## Output Files

After a code audit, you should have:

```
project/
├── README.md           ← Project overview (generated)
├── AUDIT.md            ← Audit findings and issues
├── CLAUDE.md           ← Safety rules for this project
├── legacy/             ← Protected original files
├── docs/
│   └── data_dictionary.md
└── output/
    └── audit_deck.pdf  ← Visual summary
```

## Questions to Answer

- [ ] What is the research question?
- [ ] What data is used?
- [ ] What is the identification strategy?
- [ ] What are the main results?
- [ ] Are results reproducible from the code?
- [ ] What assumptions are made?
- [ ] What are the known limitations?
- [ ] What would need to change to extend this?

## Example Prompts

**Initial exploration:**
> "Read all the .do/.R/.py files in this project and create a summary of what each script does, including inputs and outputs."

**Data comparison:**
> "Compare dataset_v1.dta and dataset_v2.dta. Show me where they differ, with summary statistics and visualizations."

**Documentation:**
> "Create a README.md that documents this project's structure, data sources, and how to reproduce the main results."

## Example Use

"Audit my Brexit replication project - I haven't touched it in 8 months. Tell me what's there, what state it's in, and what I need to do to pick it back up."


---

## code-review

**Source:** `skills/code-review/SKILL.md`

---
name: code-review
description: "Use when you need a quality review of R, Python, or Julia research scripts. Multi-persona orchestrator with parallel specialist reviewers."
allowed-tools: Read, Glob, Grep, Agent, Bash(wc*)
argument-hint: "[script-path or project-path]"
---

# Research Code Review

**Report-only skill.** Never edit source files — produce `reviews/code-review/YYYY-MM-DD_CODE-REVIEW-REPORT.md` only.

## When to Use

- Before submitting a paper (check replication package quality)
- After writing analysis scripts and before sharing with coauthors
- When taking over someone else's research code
- As part of the Referee 2 agent's formal audit pipeline

## When NOT to Use

- **Understanding old code** — use `/code-archaeology` first to map out what exists
- **Formal verification** — use the Referee 2 agent for cross-language replication
- **General software projects** — this is for research scripts, not applications

---

## Architecture

**Orchestrator + parallel specialist reviewers.** The main context runs a baseline checklist, then spawns 3-6 specialist sub-agents in parallel. Each reviewer produces structured JSON findings. The orchestrator deduplicates, merges, and synthesizes a single report.

```
Phase 1: Scope → Phase 2: Baseline Checklist → Phase 3: Spawn Reviewers
→ Phase 4: Merge & Dedup → Phase 5: Synthesize Report
```

---

## Phase 1: Scope Detection

1. **Locate scripts:** Find all `.R`, `.py`, `.jl`, `.do` files in the project (or the specified path)
2. **Count and classify:** Report file count, languages, total lines of code
3. **Read project CLAUDE.md** (if it exists) for domain context, estimand, methodology

If no code files found, stop: "No code files found at [path]."

---

## Phase 2: Baseline Checklist (main context, fast pass)

Run through all 11 categories as a quick structural check. This catches mechanical issues that don't need specialist reviewers.

### 11 Checklist Categories

See [`references/checklist-categories.md`](references/checklist-categories.md) for detailed specifications of all 11 categories: Reproducibility, Script Structure, Output Hygiene, Function Quality, Domain Correctness, Figure Quality, Data Persistence, Dependencies, Python-Specific, R-Specific, and Cross-Language Verification.

Record checklist results (Pass/Fail/N/A per category) for the report. Continue to Phase 3 regardless of results.

---

## Phase 3: Spawn Specialist Reviewers

Read `references/persona-catalog.md` for the full persona definitions and selection logic.

### 3a. Select Reviewers

**Always spawn (3 reviewers):**
- `correctness-reviewer` — logic errors, bugs, state issues
- `reproducibility-reviewer` — seeds, paths, environment, portability
- `design-reviewer` — structure, naming, dead code, complexity

**Conditionally spawn (scan code to decide):**
- `domain-reviewer` — if statistical/econometric methods detected
- `performance-reviewer` — if loops over data, DB queries, or expensive operations detected
- `security-reviewer` — if user input handling, HTTP, SQL, shell commands, or credentials detected

### 3b. Announce Team

Before spawning, list the team:

```
Review team: correctness, reproducibility, design, domain (detected: lm() with cluster SEs)
```

### 3c. Spawn in Parallel

For each selected reviewer, launch a sub-agent (subagent_type: "general-purpose", model: "haiku") with:

1. Read `references/subagent-template.md` — substitute `{persona_name}` and `{persona_content}` from the catalog
2. Pass the file list and instruct the agent to read each file
3. Instruct: return ONLY JSON matching `references/findings-schema.json`

**All reviewers run in parallel** — launch them in a single message with multiple Agent tool calls.

---

## Phase 4: Merge & Deduplicate

After all reviewers return:

### 4a. Validate

- Parse each reviewer's JSON output
- Drop malformed findings (note count of dropped findings)
- Drop findings with confidence < 0.60 (exception: P0 at 0.50+ survives)

### 4b. Deduplicate

Fingerprint each finding:

```
fingerprint = normalize(file) + line_bucket(line, ±3) + normalize(title)
```

Where:
- `normalize()` = lowercase, strip whitespace
- `line_bucket(line, ±3)` = any line within ±3 of another is considered the same location

When fingerprints match across reviewers:
- Keep the **highest severity**
- Keep the **highest confidence** + union all evidence
- Record which reviewers agreed (e.g., "correctness, domain")
- **Cross-reviewer agreement bonus:** +0.10 confidence (capped at 1.0)

### 4c. Map to Quality Rubric

Map each merged finding to the closest entry in `references/quality-rubric.md` to determine the deduction. If no exact match, classify by severity tier and use the midpoint deduction.

### 4d. Sort

Sort findings: P0 first → P1 → P2 → P3, then by confidence (descending), then by file, then by line.

---

## Phase 5: Synthesize Report

Create `reviews/code-review/` if it does not exist (`mkdir -p`). Write `reviews/code-review/YYYY-MM-DD_CODE-REVIEW-REPORT.md` in the project directory (date-stamped so prior reports are preserved, matching the pattern used by `paper-critic`, `peer-reviewer`, `domain-reviewer`, `referee2-reviewer`, and `proofread`).

### Report Format

```markdown
# Code Review Report

**Project:** [path]
**Date:** YYYY-MM-DD
**Scripts reviewed:** [list with line counts]
**Languages:** R / Python / Julia / Both
**Review team:** [list of reviewers with conditional justifications]

## Quality Score

| Metric | Value |
|--------|-------|
| **Score** | XX / 100 |
| **Verdict** | Ship / Ship with notes / Revise / Revise (major) / Blocked |

### Deductions

| # | Issue | Tier | Deduction | Category | Reviewer(s) | Confidence |
|---|-------|------|-----------|----------|-------------|------------|
| 1 | [title] | P0 | -25 | Domain Correctness | domain, correctness | 0.92 |
| 2 | [title] | P1 | -15 | Reproducibility | reproducibility | 0.85 |
| ... | | | | | | |
| | **Total deductions** | | **-XX** | | | |

## Checklist Scorecard

| # | Category | Result | Notes |
|---|----------|--------|-------|
| 1 | Reproducibility | Pass/Fail | |
| 2 | Script structure | Pass/Fail | |
| ... | | | |
| 11 | Cross-language verification | Pass/Fail/N/A | |

**Checklist: X/11 Pass** (adjust denominator for N/A categories)

## Detailed Findings

### P0 — Blocker

| # | File | Issue | Reviewer(s) | Confidence | Evidence |
|---|------|-------|-------------|------------|----------|
| 1 | path:line | [title + why_it_matters] | [reviewers] | 0.92 | [evidence] |

### P1 — Critical
[same format, omit if empty]

### P2 — Major
[same format, omit if empty]

### P3 — Minor
[same format, omit if empty]

## Residual Risks

[Union of residual_risks from all reviewers — things that can't be verified from code alone]

## Priority Fixes

1. [Most impactful issue — what to fix first]
2. [Second]
3. [Third]

## Positive Observations

[Things done well — important for morale and learning]

## Review Metadata

- Reviewers spawned: [N]
- Findings before dedup: [N]
- Findings after dedup: [N]
- Findings suppressed (low confidence): [N]
- Cross-reviewer agreements: [N]
```

---

## Confidence Filtering

- Suppress findings below 0.60 confidence (exception: P0 at 0.50+)
- Consolidate identical patterns: 5 instances of the same issue = 1 finding with count in evidence
- Cross-reviewer agreement boosts confidence by +0.10 (capped at 1.0)
- Never pad the report with low-confidence observations

## Quality Scoring

Apply numeric quality scoring using the shared framework and skill-specific rubric:

- **Framework:** [`../shared/quality-scoring.md`](../shared/quality-scoring.md) — severity tiers, thresholds, verdict rules
- **Rubric:** [`references/quality-rubric.md`](references/quality-rubric.md) — issue-to-deduction mappings for this skill

Start at 100, deduct per issue found, apply verdict.

---

## Council Mode (Optional)

For complex codebases or high-stakes replication packages, run the code review across multiple LLM providers. Different models have different strengths: some excel at spotting statistical errors, others at code structure or reproducibility issues.

**Trigger:** "Council code review" or "thorough code review"

**How it works:**
1. Each model independently scores all 11 categories against the same scripts
2. Cross-review: models evaluate each other's findings — catching false positives and missed issues
3. Chairman synthesis: produces a single `reviews/code-review/YYYY-MM-DD_CODE-REVIEW-REPORT.md` with the union of confirmed findings

See `skills/shared/council-protocol.md` for the full orchestration protocol.

---

## Cross-References

- **`/code-archaeology`** — For understanding unfamiliar code before reviewing it
- **Referee 2 agent** — For formal cross-language replication and verification
- **`/proofread`** — For the paper that accompanies this code
- **`references/persona-catalog.md`** — Reviewer persona definitions and selection logic
- **`references/findings-schema.json`** — JSON output contract for sub-agents
- **`references/subagent-template.md`** — Prompt template for spawning reviewers


---

## consolidate-memory

**Source:** `skills/consolidate-memory/SKILL.md`

---
name: consolidate-memory
description: "Use when you need to prune duplicates and merge overlapping entries in MEMORY.md files."
allowed-tools: Read, Write, Edit, Glob, Grep, AskUserQuestion
argument-hint: "[project-path or 'all' for global consolidation]"
---

# Consolidate Memory

Periodic refinement of `MEMORY.md` files across projects. Prunes redundant entries, merges overlapping knowledge, generates higher-order abstractions from accumulated patterns, and removes stale or superseded entries.

Inspired by npcsh's knowledge graph sleep/dream cycles — memory consolidation applied to research project knowledge.

## When to Use

- Monthly maintenance (pair with `/system-audit`)
- When a `MEMORY.md` exceeds 100 entries
- After completing a major project milestone (e.g., paper submission)
- When starting a new session and `MEMORY.md` feels cluttered
- When the same correction keeps appearing across multiple projects

## When NOT to Use

- During active work sessions — consolidation is a maintenance task
- When `MEMORY.md` has fewer than 10 entries — not enough to consolidate
- Immediately after recording `[LEARN]` tags — let knowledge accumulate first

## Modes

Ask the user which mode to run:

| Mode | Scope | What it does |
|------|-------|-------------|
| **Project** (default) | Single project's `MEMORY.md` + `.claude/state/personal-memory.md` | Consolidate both tiers |
| **Global** | All `MEMORY.md` + personal-memory files across projects + Task Management | Consolidate all, cross-pollinate shared patterns |

## Workflow

### Phase 1: Sleep (Consolidation)

Read the target `MEMORY.md` file(s) and `.claude/state/personal-memory.md` (if it exists) and perform:

#### 1.1 Duplicate Detection

Find entries that say the same thing in different words.

**Signals:**
- Same correction direction (wrong → right) with different phrasing
- Same file/variable referenced in multiple entries
- Entries from different dates that record the same learning

**Action:** Merge into a single entry, keeping the most precise wording. Note the merge in a comment: `<!-- merged from 2 entries -->`.

#### 1.2 Contradiction Resolution

Find entries that contradict each other (e.g., "use X" in one entry, "don't use X" in another).

**Signals:**
- Opposite correction directions for the same variable/convention
- Entries where a later one supersedes an earlier one

**Action:** Keep the most recent/correct entry. Flag contradictions for user review if the resolution isn't obvious.

#### 1.3 Staleness Detection

Find entries that are no longer relevant.

**Signals:**
- References to files, variables, or conventions that no longer exist in the project
- Entries about bugs that have been fixed
- Entries about tools or APIs that have changed
- Entries marked with dates older than 6 months with no recent reinforcement

**Action:** Mark as `[STALE?]` and present to user for confirmation before removing. Never auto-delete.

#### 1.4 Tier Routing Check

Check whether entries are in the correct tier (see `learn-tags` rule for the two-tier system).

**Promotion candidates** (personal-memory → MEMORY.md):
- Entries in `.claude/state/personal-memory.md` that would help a collaborator on a different machine
- Local workarounds that turned out to be general conventions
- Tool quirks that apply to all machines (not just this one)

**Demotion candidates** (MEMORY.md → personal-memory):
- Entries in `MEMORY.md` that reference local paths, machine-specific tool versions, or environment quirks
- Workarounds that only apply to this specific setup

**Action:** Present promotion/demotion suggestions to the user. Move entries only after explicit approval.

#### 1.5 Strengthening

Entries that have been independently confirmed multiple times are high-confidence knowledge.

**Signals:**
- Same pattern recorded from different sessions
- Corrections reinforced by compilation errors or test failures
- Conventions confirmed by supervisor feedback

**Action:** Move to the top of their section. Add `[CONFIRMED]` marker if supported by 3+ independent occurrences.

### Phase 2: Dream (Abstraction)

Generate higher-order patterns from the accumulated entries.

#### 2.1 Cross-Entry Patterns

Look for patterns that span multiple entries:

- "Every time we work with X, we hit Y" → Record as a general rule
- "We always use convention A for project type B" → Record as a convention
- "Corrections in category C cluster around the same mistake" → Record the root cause

#### 2.2 Cross-Project Patterns (Global mode only)

When consolidating across all projects, look for knowledge that applies everywhere:

- Notation conventions used consistently across 3+ projects → Promote to global MEMORY.md
- The same code pitfall appearing in multiple projects → Record once with cross-references
- Citation corrections that apply to shared bibliography entries → Consolidate

#### 2.3 Abstraction Generation

For each pattern found, generate an abstraction:

```markdown
## Abstraction: [Name]

**Pattern:** [What keeps happening]
**Root cause:** [Why it happens]
**Prevention:** [How to avoid it in future]
**Evidence:** [Which entries support this]
```

Present abstractions to the user. Only write the ones they approve.

### Phase 3: Write

#### 3.1 Restructure

Rewrite `MEMORY.md` with:
1. **Abstractions** at the top (new section: `## Patterns`)
2. **Confirmed entries** next (high-confidence knowledge)
3. **Regular entries** in their standard sections (Notation Registry, Citations, Key Decisions, Anti-Patterns, Code Pitfalls)
4. **Stale entries removed** (only those confirmed by user)

If `.claude/state/personal-memory.md` exists, also rewrite it with consolidated machine-specific entries. Apply any user-approved promotions (move to MEMORY.md) and demotions (move from MEMORY.md to personal-memory).

#### 3.2 Diff Report

Before writing, show a summary:

```markdown
## Consolidation Summary

| Action | Count |
|--------|-------|
| Duplicates merged | X |
| Contradictions resolved | X |
| Stale entries flagged | X |
| Stale entries removed | X (user-confirmed) |
| Entries strengthened | X |
| Abstractions generated | X |
| Tier promotions (personal → generic) | X |
| Tier demotions (generic → personal) | X |
| Cross-project promotions | X (global mode) |

### Entries Before: XX
### Entries After: YY
### Net reduction: ZZ
```

#### 3.3 Confirmation

**Always show the full proposed MEMORY.md before writing.** Wait for explicit approval. The user may want to keep entries flagged as stale, adjust abstractions, or revert merges.

## MEMORY.md Sections (Reference)

Standard sections from the `learn-tags` rule:

| Section | Columns |
|---------|---------|
| **Patterns** | Pattern / Root cause / Prevention / Evidence (NEW — added by this skill) |
| **Notation Registry** | Variable / Convention / Anti-pattern |
| **Estimand Registry** | What we estimate / Identification / Key assumptions |
| **Citations** | One-liner corrections |
| **Key Decisions** | Decision / Rationale / Date |
| **Anti-Patterns** | What went wrong / Correction |
| **Code Pitfalls** | Bug / Impact / Fix |

## Global MEMORY.md Location

The Task Management MEMORY.md at the project root:
```
$TM/MEMORY.md
```

Also check the auto-memory directory (path varies by machine — glob for it):
```
~/.claude/projects/-Users-user-*Task-Management/memory/MEMORY.md
```

## Cross-References

- **`/system-audit`** — Run consolidation as part of periodic maintenance
- **`/learn`** — Creates the entries that this skill consolidates
- **`[LEARN]` tags** (rule) — The tagging system that feeds MEMORY.md
- **`/general-session-recap`** — May surface entries worth recording before consolidation


---

## context-status

**Source:** `skills/context-status/SKILL.md`

---
name: context-status
description: "Use when you need to check current context status and session health."
allowed_tools:
  - Read
  - Glob
  - Bash(ls*, cat*)
---

# Context Status: Session Health Check

On-demand diagnostic showing context usage, preservation state, and open work items. Fast and lightweight — no vault queries.

## What to Check

### 1. Context Usage Estimate

Read the context monitor state file to get the current tool call count:

```
~/.claude/sessions/{project-hash}/context-monitor-state.json
```

The project hash is a SHA-256 of `CLAUDE_PROJECT_DIR` (first 12 chars). If the state file doesn't exist, report "No context monitor data — hook may not be active."

Calculate:
- Tool calls so far
- Estimated percentage (calls / 150)
- Which thresholds have fired (from the `fired` array)
- Time since last warning

### 2. Active Plan

Find the latest file in `log/plans/`:
- If found: show filename, first 3 lines, and whether it contains "APPROVED" or is still "DRAFT"
- If none: report "No active plan"

### 3. Latest Session Log

Find the latest non-compact `.md` file in `log/` (skip files with `-compact` in the name):
- If found: show filename and first 3 lines
- If none: report "No session log found"

### 4. Focus Freshness

Check when `.context/current-focus.md` was last modified:
- Show the modification date
- If older than 3 days: warn "Focus file is stale — consider running `/update-focus`"
- Show the first 5 lines (headline)

### 5. Preservation Hooks

Verify these hooks are configured in `~/.claude/settings.json`:
- `PreCompact` → `precompact-autosave.py` (pre-compact state save)
- `SessionStart` compact → `postcompact-restore.py` (post-compact restore)
- `PostToolUse` → `context-monitor.py` (this monitor)

For each: report CONFIGURED or MISSING.

### 6. Open Loops

Count unchecked items (`- [ ]`) in `.context/current-focus.md`:
- Report the count
- If > 5: warn "Many open loops — consider triaging"

## Output Format

Present as a compact status panel:

```
## Session Health

| Metric | Value |
|--------|-------|
| Context usage | ~XX% (N/150 tool calls) |
| Thresholds fired | none / info / warning / critical |
| Active plan | filename (DRAFT/APPROVED) / none |
| Latest log | filename / none |
| Focus freshness | N days ago / stale warning |
| Open loops | N items |

### Preservation Hooks

| Hook | Status |
|------|--------|
| PreCompact auto-save | CONFIGURED / MISSING |
| Post-compact restore | CONFIGURED / MISSING |
| Context monitor | CONFIGURED / MISSING |

### Recommendations

[Only if there are issues — e.g., stale focus, missing hooks, high context usage]
```

### 7. Compaction Guidance

When context is high (>60%), include these reference tables in the output:

**When to compact:**

| Phase Transition | Compact? | Why |
|---|---|---|
| Research to Planning | Yes | Research context is bulky; plan is the distilled output |
| Planning to Implementation | Yes | Plan is in a file; free up context for code |
| Implementation to Testing | Maybe | Keep if tests reference recent code |
| Debugging to Next feature | Yes | Debug traces pollute context |
| Mid-implementation | No | Losing file paths and partial state is costly |
| After a failed approach | Yes | Clear dead-end reasoning |

**What survives compaction:**

| Persists | Lost |
|---|---|
| CLAUDE.md + rules | Intermediate reasoning |
| Task list | File contents previously read |
| MEMORY.md | Multi-step conversation context |
| Git state | Tool call history |
| Files on disk | Verbal preferences |
| precompact-autosave state | — |

## When to Use

- When the context monitor fires a warning
- Before starting a large task (to check remaining capacity)
- After resuming a session (to verify state was preserved)
- When unsure if preservation hooks are working


---

## creation-guard

**Source:** `skills/creation-guard/SKILL.md`

---
name: creation-guard
description: "Use when you need a pre-flight duplicate check before creating new skills or agents."
allowed_tools:
  - Read
  - Glob
  - Grep
  - AskUserQuestion
---

# Creation Guard: Pre-Flight Duplicate Check

Prevent duplicate functionality by analysing existing skills and agents before creating new ones. Intercepts creation intent, searches for overlap, and recommends one of 5 actions.

## When to Use

Invoke **before** creating ANY new:
- Skill (`skills/*/SKILL.md`)
- Agent (`.claude/agents/*.md`)

Trigger phrases:
- "Create a skill for..."
- "I want a new skill that..."
- "Let's add an agent for..."
- Any intent to create new automation/tooling

## Process

### Step 1: Identify the Proposal

Extract from the request:
- **Name**: Proposed name (kebab-case)
- **Type**: skill | agent
- **Purpose**: What it does (one sentence)
- **Key Functions**: 3-5 main capabilities
- **Keywords**: Searchable terms related to functionality

### Step 2: Search Existing Artifacts

Run these searches in parallel:

1. **Read [`skills/shared/skill-index.md`](../shared/skill-index.md)** — scan the categorised table for potential duplicates by name and purpose
2. **Keyword search** — grep skills and agents for each keyword:

```
Grep for each keyword across:
  - skills/*/SKILL.md (frontmatter + body)
  - .claude/agents/*.md (frontmatter + body)
```

3. **Agent scan** — read frontmatter of each agent to check purpose overlap:

```
Glob: .claude/agents/*.md
Read first 20 lines of each match
```

### Step 3: Analyse Overlap

For each potentially related artifact, assess:

| Criterion | Question |
|-----------|----------|
| Functional overlap | Does it do the same thing? (0-100%) |
| Naming confusion | Could names be confused? |
| Extension potential | Could the proposal extend this instead? |
| Composition | Could existing artifacts compose to achieve this? |

### Step 4: Generate Recommendation

Based on analysis, recommend ONE of:

| Recommendation | Criteria | Action |
|----------------|----------|--------|
| **PROCEED** | <20% overlap, genuinely new capability | Create new artifact |
| **EXTEND** | 50%+ overlap with single existing artifact | Modify existing instead |
| **COMPOSE** | Multiple artifacts cover 80%+ combined | Create thin wrapper or document workflow |
| **ITERATE** | 20-50% overlap, proposal needs refinement | Refine proposal to differentiate |
| **BLOCK** | Would create problematic duplication | Do not create |

### Step 5: Present and Confirm

Display the analysis and wait for explicit user approval before proceeding.

## Output Format

```
════════════════════════════════════════════════════════════════
CREATION GUARD ANALYSIS
════════════════════════════════════════════════════════════════

PROPOSAL:
  Type: [skill|agent]
  Name: [proposed-name]
  Purpose: [one sentence]

EXISTING ARTIFACTS ANALYSED: [count]

RELATED ARTIFACTS FOUND:

1. [artifact-name] ([type])
   Purpose: [what it does]
   Overlap: [X]% - [explanation]

2. [artifact-name] ([type])
   Purpose: [what it does]
   Overlap: [X]% - [explanation]

RECOMMENDATION: [PROCEED|EXTEND|COMPOSE|ITERATE|BLOCK]

RATIONALE:
[2-3 sentences explaining the recommendation]

SUGGESTED ACTION:
[Specific next step based on recommendation]

════════════════════════════════════════════════════════════════
```

## Recommendation Details

### PROCEED
- Artifact is genuinely new
- No significant overlap found
- Clear differentiation from existing tools
- Go ahead and create

### EXTEND
Present extension proposal:
```
Instead of creating [new-name], extend [existing-name]:

Current capabilities:
- [existing feature 1]
- [existing feature 2]

Proposed additions:
- [new feature 1]
- [new feature 2]
```

### COMPOSE
Present composition approach:
```
The proposed functionality can be achieved by combining:

1. [artifact-1] — handles [aspect]
2. [artifact-2] — handles [aspect]

Options:
A) Document this workflow (no new code)
B) Create thin orchestration skill
C) Add to existing skill's integration section
```

### ITERATE
Present refinement questions:
```
Overlap detected with [existing-artifact].

Differentiation needed:
1. [question about scope]
2. [question about use case]
3. [question about implementation]

Please clarify to proceed.
```

### BLOCK
Explain why creation should not proceed:
```
BLOCKED: Would create problematic duplication.

Existing artifact: [name]
- Already does: [capabilities]
- Your request: [same capabilities]

Alternatives:
1. Use existing: /[skill-name]
2. If missing features, extend the existing artifact
3. If different use case, explain how this differs
```

## Post-Match Action Table

When overlap IS found, use this table to decide the specific action:

| Situation | Action |
|-----------|--------|
| Nothing related found | Create new artifact |
| Same trigger + same fix as existing | Update existing (bump version, improve docs) |
| Same trigger, different root cause | Create new + add cross-links in both |
| Partial overlap (same domain, different trigger) | Add variant subsection to existing |
| Same domain, different problem | Create new + add "See also" references |
| Existing is stale or wrong | Mark deprecated + create replacement |

This complements the PROCEED/EXTEND/COMPOSE/ITERATE/BLOCK recommendation above. The recommendation decides *whether* to create; this table decides *how* to handle the relationship with existing artifacts.

## Self-Check Questions

Before creating ANY new artifact, ask:

1. Does something similar already exist?
2. Could this be added to an existing artifact?
3. Would a user know to look for this vs the existing one?
4. Am I creating this because it's needed or because it's easier than finding what exists?

## Naming Convention Enforcement

When creating a new skill, **always** name the definition file `SKILL.md` (uppercase). Never `skill.md`, `Skill.md`, or any other casing.

- The MCP server's skill discovery scans for `SKILL.md` explicitly
- Documentation generators and `/system-audit` use `find -name 'SKILL.md'`
- On case-insensitive filesystems (macOS APFS), lowercase files appear to work locally but fail in case-sensitive contexts (Linux CI, Docker, MCP server pattern matching)

**Check before writing:** If the target directory already contains a `skill.md` (lowercase), rename it to `SKILL.md` first.

## Anti-Patterns

| Anti-Pattern | Problem | Instead |
|--------------|---------|---------|
| Skip the check | "It's obviously new" — famous last words | Always run the analysis |
| Name-only matching | Names differ but functions overlap | Search by purpose and keywords |
| Create then merge | Merge debt accumulates fast | Check first, create once |
| Over-splitting | Two skills that always run together | Consider a single skill with phases |
| Lowercase `skill.md` | Invisible to MCP server, audit tools, and case-sensitive systems | Always use `SKILL.md` (uppercase) |

## Integration

This skill is invoked by `/learn` in Phase 2 to replace the old subset/partial/no-overlap check. When called from `/learn`, return the recommendation label (PROCEED/EXTEND/COMPOSE/ITERATE/BLOCK) so `/learn` can branch accordingly.


---

## devils-advocate

**Source:** `skills/devils-advocate/SKILL.md`

---
name: devils-advocate
description: "Use when you need to challenge research assumptions or stress-test arguments."
argument-hint: [paper-or-argument-description]
---

# Devil's Advocate Skill

> Challenge research assumptions and identify weaknesses in your arguments.

## Purpose

Based on Scott Cunningham's Part 3: "Creating Devil's Advocate Agents for Tough Problems" - addressing the "LLM thing of over-confidence in diagnosing a problem."

**For formal code audits with replication scripts and referee reports, use the Referee 2 agent instead (`.claude/agents/referee2-reviewer.md`).** This skill is for quick adversarial feedback on arguments, not systematic audits.

## When to Use

- Before submitting a paper
- When stuck on a research problem
- When you want to stress-test an argument
- During paper revision planning

## When NOT to Use

- **Code audits** — use the Referee 2 agent instead
- **Replication verification** — use the Referee 2 agent instead
- **Quick proofreading** — just ask for a read-through
- **When you want validation** — this skill is designed to challenge, not affirm

## Workflow

1. **Understand the claim** — Read the paper/argument being evaluated
2. **Generate competing hypotheses** — If evaluating a research question or design, load `references/competing-hypotheses.md` and generate 3-5 rival explanations before critiquing
3. **Run the debate** — Use the multi-turn debate protocol below (default) or single-shot mode for quick checks
4. **Deliver the verdict** — Synthesize surviving critiques with severity ratings

## Multi-Turn Debate Protocol (Default)

Inspired by the simulated scientific debates in Google's AI Co-Scientist. A one-shot critique is easy for an LLM to produce but often superficial. Multi-turn debates force each critique to survive a defense, filtering out weak objections and sharpening the strong ones.

### Round 1: Adversarial Critic

Adopt the persona of a hostile but competent reviewer. Challenge on:
1. **Theoretical foundations** — Are the assumptions justified?
2. **Methodology** — Limitations? Alternative approaches?
3. **Data** — Selection bias? Measurement issues? External validity?
4. **Causal claims** — Alternative explanations? Confounders?
5. **Contribution** — Novel enough? Does it matter?

Produce **numbered critiques** (aim for 5-8), each with a concrete statement of the problem.

### Round 2: Defense

Switch persona to the paper's author. For each numbered critique, provide the strongest possible defense:
- Cite evidence from the paper that addresses the concern
- Explain design choices that mitigate the issue
- Acknowledge limitations honestly where the defense is weak
- Propose concrete fixes where the critique has merit

### Round 3: Adjudication

Switch to an impartial senior reviewer. For each critique-defense pair, rule:
- **Critique stands** — the defense is insufficient; this is a real weakness
- **Critique partially addressed** — defense has merit but issue remains
- **Critique resolved** — the defense adequately addresses the concern

### Final Synthesis

Produce a structured report with only the surviving critiques (stands + partially addressed), ranked by severity:

```markdown
## Devil's Advocate Report

### Critical (must fix before submission)
1. [Critique] — [Why the defense failed] — [Suggested fix]

### Major (reviewers will likely raise)
2. [Critique] — [What remains after defense] — [Suggested fix]

### Minor (worth acknowledging)
3. [Critique] — [Residual concern] — [How to preempt]

### Dismissed
- [Critiques that were resolved in Round 2, listed briefly for transparency]
```

## Single-Shot Mode

For quick checks (e.g., "just poke holes in this argument"), skip the multi-turn protocol and produce a direct critique. Use when the user says "quick", "just challenge this", or the input is a paragraph rather than a full paper.

## Example Use

"Play devil's advocate on my research paper about preference drift - specifically challenge my identification strategy and the assumptions about utility functions."

---

## Council Mode (Optional)

For the highest-stakes arguments, run the devil's advocate debate across multiple LLM providers. Different models have genuinely different reasoning patterns — a critique that Claude finds weak, GPT may find devastating, and vice versa. This produces adversarial tension that a single model cannot replicate internally.

**Trigger:** "Council devil's advocate" or "thorough challenge"

**How it works:**
1. Each model independently plays Adversarial Critic (Round 1) using the same paper/argument
2. Cross-review: each model evaluates the others' critiques — identifying which challenges are strongest
3. Chairman synthesis: produces a single report with surviving critiques ranked by cross-model agreement

**Invocation (CLI backend):**
```bash
cd packages/council-cli
uv run python -m council_cli \
    --prompt-file /tmp/devils-advocate-prompt.txt \
    --context-file /tmp/paper-content.txt \
    --output-md /tmp/devils-advocate-council.md \
    --chairman claude \
    --timeout 180
```

See `skills/shared/council-protocol.md` for the full orchestration protocol.

**Value:** High — the multi-turn debate protocol (Round 1→2→3) becomes genuinely adversarial when different models play different roles. A critique that survives cross-model scrutiny is almost certainly a real weakness.

## Cross-References

| Skill | When to use instead/alongside |
|-------|-------------------------------|
| `/interview-me` | To develop the idea further through structured interview |
| `/multi-perspective` | For multi-perspective analysis with disciplinary diversity |
| `/proofread` | For language/formatting review rather than argument critique |


---

## handoff

**Source:** `skills/handoff/SKILL.md`

---
name: handoff
description: "Use when you need to pass state to the next session in the current working directory. Writes a handoff.md file that the next session's SessionStart hook will read and delete."
allowed-tools: Read, Write, Bash(pwd), Bash(ls*), Bash(git status*), Bash(git log*)
argument-hint: [optional-note]
---

# Handoff Skill

> Write a one-shot handoff note to the next session, in the current working directory.

## Purpose

Bridge state across a restart or `/exit` when a full session log is overkill. The next session's SessionStart hook (`handoff-read.sh`) reads `handoff.md`, injects its contents as additional context, then **deletes** the file. One read, gone.

Use this when:
- You need to restart (e.g., MCP server re-enable, permission change, context pressure)
- You want to hand off mid-task state to the next session without polluting `log/`
- A quick note is enough — not a full `/session-close`

## When NOT to Use

- End of a substantive work session → use `/session-close` (proper logs, git commit)
- Permanent decisions or learnings → use MEMORY.md with `[LEARN]` tags
- Cross-project notes → use `.context/agent-messages.md`

## Workflow

### Step 1: Gather state

Collect:
- **Current working directory** (`pwd`) — the handoff lives here
- **What was happening** — the immediate task, not a session recap
- **What's next** — the specific next action
- **Open loops** — files mid-edit, background processes, pending confirmations
- **Blockers** — why the session is ending (e.g., "Paperpile MCP needs restart")

### Step 2: Write `handoff.md` in cwd

Use this template:

```markdown
# Handoff — <YYYY-MM-DD HH:MM>

## Where we are
<1-3 sentences on current task state>

## Next action
<The single next thing to do — be specific>

## Open loops
- <file.py mid-edit at line N>
- <background job: description>
- <HPC job $SLURM_JOB_ID on your-hpc: submitted/running/completed; OUT_DIR=~/projects/<name>/out/<jobid>/>
- <pending user confirmation: question>

## Blockers / context the next session needs
<Why the handoff exists. API keys set? MCP restarted? Permission added?>

## Files touched this session
- <path:line> — <what changed>

## Scratch
<Anything else — half-formed thoughts, commands to try, URLs>
```

Keep it tight. The next session reads this once as SessionStart context — it should be skimmable in 10 seconds.

### Step 3: Confirm

Tell the user: "Handoff written to `<cwd>/handoff.md`. Next session in this directory will read and delete it."

## Hook Behavior

The companion hook `handoff-read.sh` fires on **every** SessionStart (startup + resume + compact). If `handoff.md` exists in the session's cwd:

1. Reads contents
2. Injects as `additionalContext` with the header `# Handoff from previous session`
3. Deletes `handoff.md` (scratch)

Zero token cost when no handoff exists.

## Important

- Handoff is **ephemeral** — one-shot. If you need durable state, write to `log/` or MEMORY.md instead.
- `handoff.md` should NOT be committed. Add to `.gitignore` if the directory has one.
- If the next session's cwd differs, the handoff won't fire — always `cd` to the same directory before restarting.


---

## init-paper-book

**Source:** `skills/init-paper-book/SKILL.md`

---
name: init-paper-book
description: "Use when you need to scaffold a NEW educational companion book for a LaTeX paper. Reads the paper, drafts 8 substantive chapters into the vault at ~/Research-Vault/books/{slug}/, copies bib + figures, registers the book, and verifies atlas serves it. Source-of-truth is the paper PDF/tex; the book is a reading companion, never a re-statement of new claims. For syncing an existing book to a paper revision, use /audit-paper-book."
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, Agent, Task
argument-hint: "<project-path-or-slug> [--dry-run]"
---

# Init Paper Book

Scaffold a runnable, browsable companion to a LaTeX paper. The book lives in the vault, atlas renders it, and direct URLs at `books.user.com/<slug>/<chapter>` make it shareable. There is **no separate build pipeline** — atlas is the renderer.

For syncing an existing book to a paper revision, use `/audit-paper-book` instead.

## Hard rules

### Existential — block writing

1. **No new claims.** The book may rephrase, scaffold, and explain, but never introduce results not in the paper. Numbers and theorems trace to the paper.
2. **Numeric invariant.** Every numeric claim in the book must match the paper. Mismatches block.
3. **Paper is canonical.** Source-of-truth is the paper PDF/tex. Edits to the book do not edit the paper. Edits to the paper require `/audit-paper-book` to propagate.
4. **Atlas slug match.** Book slug must equal atlas topic filename (lowercase, hyphenated). The project directory leaf under the research root should also match (warn, don't block). If any of these three disagree, stop and prompt — alignment is required at the source, not a workaround in the book. `/audit-paper-book` pre-flight aborts on book-slug ⇄ atlas-filename drift; the regenerate script aborts at runtime with "SLUG DRIFT".

### Format — catch in review

5. **Vault location.** Book chapters live at `~/Research-Vault/books/<slug>/`. Never in the project tree (atlas runs under launchd and File Provider paths hang).
6. **Registry entry.** `~/Research-Vault/books/index.yaml` must list the slug, title, atlas-topic pointer, bibliography file, and explicit chapter order.
7. **Eight chapters.** Default skeleton: `intro · background · setup · method · results · limitations · extend · appendix`. The `references` chapter is auto-appended when `bibliography:` is set.
8. **No-index by default.** atlas's base.html injects `noindex,nofollow` for book chapters. Books are direct-link-only — no discovery surface.
9. **Section headings descriptive, never numbered.** Use `## The selection rule`, not `## 4.5 The selection rule`. Cross-references to the paper carry the paper's own numbering inline.
10. **Mystmd-style callouts.** Use `` ```{important} ``, `` ```{tip} ``, `` ```{note} ``, `` ```{warning} ``, `` ```{caution} ``, `` ```{seealso} ``. Atlas's directive converter handles these. Pandoc-style `::: {.callout-X}` does NOT render — convert if you find it in source material.
11. **Figure paths are vault-relative.** `figures/<filename>` resolves to `~/Research-Vault/books/<slug>/figures/<filename>` served by atlas's `/book/<slug>/figures/{filename:path}` route.
12. **Citations resolve in-book first.** Mystmd `{cite:t}\`Key\`` converts to `[Key](/book/<slug>/references#ref-Key)` when `Key` is present in the book's local `references.bib` (anchors to the matching `<li id="ref-Key">` card in the auto-rendered `references` chapter). For keys not in the local bib, the converter falls back to `https://atlas.user.com/paper/Key` (the global Paperpile-backed route, behind CF Access). Don't construct citation URLs by hand.
13. **Affiliations from atlas.** Author affiliations come from the atlas topic's `institution:` field. Never hardcode.
14. **Accessibility floor.** Chapters must be readable by someone with an undergraduate degree in a quantitative field (linear algebra, probability, basic optimisation/statistics — not necessarily Bayesian methods or domain-specific machinery). Concretely:
    - Introduce every non-elementary notation/term inline at first use (e.g. "Gaussian process (GP) — a distribution over functions where any finite set of evaluations is jointly Gaussian").
    - State the intuition before the formal definition.
    - Avoid acronyms without expansion at first use within each chapter (e.g. "expected hypervolume improvement (EHVI)", not just "EHVI").
    - Math is allowed but never carries the whole load — every display equation gets a one-line plain reading.
    - Avoid jargon-on-jargon: don't define one undergraduate-opaque term using two others.

    The Phase 4 verifier checks this floor (see below). Each drafting sub-agent prompt in Phase 3 MUST include the accessibility floor verbatim.

## When to use

- Paper submitted, results stable, accepted or under review (no churn)
- Methods/benchmark/theory papers where reuse depends on understanding
- Papers with policy or practitioner audiences who don't read the venue proceedings
- the user explicitly asks for a "book" or "companion" for a paper

## When NOT to use

- Paper still in heavy revision (results moving) — wait or accept that you'll need `/audit-paper-book` immediately after submission
- Slide decks (`/beamer-deck`, `/quarto-deck`)
- Compilation only (`/latex`)
- Generic literature reviews (`/literature`)

## Inputs accepted

```
/init-paper-book <project-path>          # full path to project dir, e.g. /Volumes/SSD/Dropbox/Research/ASG/audit-gaming-benchmark
/init-paper-book <slug>                  # atlas slug; resolved via atlas topic file's project_path
/init-paper-book <slug> --dry-run        # plan only, no writes
/init-paper-book <slug> --autonomous     # or -y: 4 phases end-to-end, no inter-phase pauses (see Autonomy below)
```

## Autonomy

Per the global `--autonomous` / `-y` convention in `~/.claude/rules/phased-work.md` § "Autonomy flag convention". When set:

- **No mid-run `AskUserQuestion`** — every choice point uses the recommended default and logs the decision (chapter scope decisions, screenshot mode, atlas-reload trigger).
- **No inter-phase confirmation** — Phases 1 → 5 chain without stopping for `continue`, EXCEPT Phase 4 (verification) which can hard-block Phase 5 on any verifier failure (see "Hard correctness gates" below).
- **Phase 3 sub-agents still fire in parallel** (chapter drafting); they each carry the standard forbid-list (no git, no build outside the chapter file).
- **Phase 4 verifier runs mandatorily** — even in autonomous mode, the verifier dispatch and report are not skipped. Any verifier failure (numeric drift, missing citation key, claim outside paper scope, accessibility violation) BLOCKS Phase 5 and exits with a clear remediation list.
- **Pre-flight block-on-fail still applies** — missing atlas topic / project dir / `main.tex` aborts the run with a clear error (this is a correctness gate, not a phase pause).
- **Phase 5 register + smoke-test still runs** if and only if Phase 4 passed — registry entry, atlas reload, smoke probe; failures are reported at end, not blocked mid-run.
- **Single end-of-run report** as the only mandatory user-facing output — lists chapters created, verifier findings, registry registration, smoke-test results, any non-fatal warnings.

Hard correctness gates that still fire even with `--autonomous` (any of these aborts the run):

- Pre-flight checks 1–5 (atlas, project, paper-tex, bib, vault-not-already-present)
- Sub-agent forbid-list (Phase 3 drafters can't touch git, can't run latexmk, can't edit outside `~/Research-Vault/books/<slug>/`)
- **Phase 4 verifier failure** — any one of: numeric drift, missing citation key, claim outside paper scope, accessibility-floor violation (see Phase 4)
- After-flight verifier (registry entry exists, atlas serves the book URL)

Recommended invocations:

```
/init-paper-book article40-access-as-mechanism --autonomous
/init-paper-book -y article40-access-as-mechanism
```

Use `--dry-run` first if you want to see the chapter plan before letting it run.

## Pre-flight (block-on-fail)

```bash
SLUG="<resolved-slug>"

# 1. Atlas topic exists
find ~/Research-Vault/atlas -name "${SLUG}.md" -type f | head -1
[[ $? == 0 ]] || die "No atlas topic for ${SLUG}. Run /init-project-research first."

# 2. Project directory exists
PROJECT_PATH=$(grep -E "^project_path:" "$ATLAS_TOPIC" | cut -d' ' -f2- | tr -d "'\"")
RR=$(cat ~/.config/task-mgmt/research-root)
[[ -d "$RR/$PROJECT_PATH" ]] || die "project_path in atlas does not resolve."

# 3. Paper directory + tex file exist
PAPER_DIR=$(ls -d "$RR/$PROJECT_PATH"/paper-* 2>/dev/null | head -1)
PAPER_TEX="$PAPER_DIR/paper/main.tex"
[[ -f "$PAPER_TEX" ]] || PAPER_TEX="$PAPER_DIR/backup/main.tex"
[[ -f "$PAPER_TEX" ]] || die "No main.tex in $PAPER_DIR/{paper,backup}/."

# 4. Bibliography exists
BIB=$(find "$PAPER_DIR" -maxdepth 3 -name "*.bib" | head -1)
[[ -f "$BIB" ]] || warn "No .bib found — references chapter will be empty."

# 5. Vault book dir doesn't already exist
[[ -d ~/Research-Vault/books/"$SLUG" ]] && die "Book already exists. Use /audit-paper-book to sync."
```

## Phases

```
Phase 1: Read paper + plan        (direct read of paper tex + atlas topic)
Phase 2: Scaffold vault           (mkdir, copy bib + figures)
Phase 3: Draft chapters           (mixed — sub-agents for content-heavy chapters)
Phase 4: Verify chapters          (read-only sub-agent; HARD GATES Phase 5)
Phase 5: Register + smoke-test    (registry entry, atlas reload, smoke probe)
```

### Phase 1: Read + plan

See [`references/phase-1-read-plan.md`](references/phase-1-read-plan.md).

### Phase 2: Scaffold

See [`references/phase-2-scaffold.md`](references/phase-2-scaffold.md).

### Phase 3: Draft chapters

See [`references/phase-3-chapter-scaffolding.md`](references/phase-3-chapter-scaffolding.md) for chapter table and requirements.

**Intro masthead format.** See [`references/intro-masthead-format.md`](references/intro-masthead-format.md) for definition-list pattern, preserve marker, regenerate commands, and Overleaf-link handling.

### Phase 4: Verify chapters (MANDATORY; hard-gates Phase 5)

See [`references/phase-4-verify-chapters.md`](references/phase-4-verify-chapters.md) for deterministic checks, semantic checks, and hard-gate rules.

### Phase 5: Register + smoke-test

See [`references/phase-5-register.md`](references/phase-5-register.md) for registry append, atlas reload, HTTP smoke test, and Playwright visual check.

## Anti-patterns

- **Copy-pasting paper text verbatim.** The book is a reading companion, not a transcription. Paraphrase + scaffold; don't duplicate the proof prose.
- **Inventing numbers.** If the paper says "mean gap 0.884", the book says exactly that — never round, never re-derive, never average across runs not in the paper.
- **Adding new theorems or results.** Even an obvious corollary that the paper doesn't state must NOT appear. The book is a reading guide, not a sequel.
- **Pandoc `::: {.callout-X}` callouts.** Atlas's converter handles `` ```{X} `` only. If the paper or notes are in Pandoc, convert before drafting.
- **Hardcoded affiliations.** Pull from atlas topic `institution:` field; never type the institution name inline.
- **Section numbering on book headings.** Book sidebar provides ordinal; the heading itself stays descriptive.

## After-flight

If anything looks visually wrong (callouts not rendering, math not rendering, figures missing), the most common causes are:
- `:::` callout syntax not converted → grep, replace with `` ```{X} ``
- Math wasn't wrapped because of underscores in body — atlas's arithmatex handles this
- Figure path wrong — should be `figures/<filename>` relative to chapter
- Bib file missing or in wrong format — references chapter shows "No references" if `_parse_bib` returns []

When the rendered output is ready, suggest committing the vault changes (`git add ~/Research-Vault/books/<slug>` from the vault repo if it's tracked) and announce: "Live at https://books.user.com/<slug>/intro".

## Logging

Append outcome to `~/.claude/ecc/skill-outcomes.jsonl` per `skill-outcome-logging` rule:

```bash
mkdir -p ~/.claude/ecc && echo '{"skill":"init-paper-book","timestamp":"'"$(date -u +%Y-%m-%dT%H:%M:%SZ)"'","outcome":"success","session":"'"${CLAUDE_SESSION_ID:-}"'","project":"'"$(basename "$PWD")"'","note":""}' >> ~/.claude/ecc/skill-outcomes.jsonl
```


---

## init-project

**Source:** `skills/init-project/SKILL.md`

---
name: init-project
description: "Bootstrap a new research project. Interview for details, scaffold directory structure, create Overleaf symlink, initialise git, and create project context files."
allowed-tools: Bash(mkdir*), Bash(ln*), Bash(git*), Bash(ls*), Read, Write, Edit, Glob, Grep, AskUserQuestion
argument-hint: (no arguments — starts an interview)
---

# Init Project — Research Project Scaffolder

> Interactive project setup: answer questions, get a ready-to-use research project directory.

## Protocol

### Phase 1: Interview

Ask the user these questions using `AskUserQuestion` (adapt based on what's already known):

1. **Project name** — short name for the directory (e.g., `nudge-experiment`)
2. **Paper title** — working title for the paper
3. **Research question** — one sentence
4. **Target journal/venue** — where you plan to submit
5. **Co-authors** — names and affiliations (if any)
6. **Parent directory** — where to create the project (default: `~/Research/`)
7. **Overleaf path** — path to Overleaf-synced directory for symlink (optional)
8. **Methodology** — experimental, observational, theoretical, simulation, mixed

### Phase 2: Scaffold

Create the directory structure:

```
<project-name>/
├── CLAUDE.md               # Project-specific Claude instructions
├── README.md               # Project overview
├── MEMORY.md               # Knowledge base (seeded with template)
├── paper/                  # → Overleaf symlink (or empty dir)
├── code/
│   ├── python/             # Python scripts
│   └── R/                  # R scripts
├── data/
│   ├── raw/                # Original data (never modified)
│   └── processed/          # Cleaned/transformed data
├── results/                # Analysis outputs
├── figures/                # Generated figures
├── docs/                   # Project documentation
├── correspondence/         # Referee reports, cover letters
│   └── referee2/           # Referee 2 agent reports
├── log/                    # Session logs
│   └── plans/              # Saved plans
└── .gitignore
```

### Phase 3: Populate Files

**CLAUDE.md** — project-specific instructions:
- Paper title and research question
- Co-authors and target venue
- Methodology and key conventions
- Pointer to project context files

**README.md** — human-readable overview:
- Project title and description
- Directory structure explanation
- How to compile the paper
- Co-author information

**MEMORY.md** — seeded with research project template:
- Notation Registry (empty)
- Estimand Registry (empty)
- Key Decisions (empty)
- Citations (empty)
- Anti-Patterns (empty)
- Code Pitfalls (empty)

**.gitignore** — standard research project ignores:
- Build artifacts (`out/`, `*.aux`, `*.log`)
- Data files (`data/raw/*.csv`, `data/raw/*.xlsx`)
- Python/R artifacts (`__pycache__/`, `.Rhistory`)
- OS files (`.DS_Store`)

### Phase 4: Git & Symlinks

1. **Overleaf symlink** — if a path was provided:
   ```bash
   ln -s /path/to/overleaf/dir paper
   ```
2. **Git init** — initialise the repository:
   ```bash
   git init
   git add .
   git commit -m "Initial project scaffold"
   ```

### Phase 5: Context Update

Update the central context library:
1. Add the project to `.context/projects/_index.md`
2. Create `.context/projects/papers/<project-name>.md` with metadata

## Output

Print a summary of what was created:

```
Project created: ~/Research/<project-name>/
  Directories: 12
  Files: 4 (CLAUDE.md, README.md, MEMORY.md, .gitignore)
  Overleaf: linked / not configured
  Git: initialised with initial commit

Next steps:
  1. Start writing in paper/ (or link Overleaf)
  2. Add code to code/python/ or code/R/
  3. Run /session-log when you finish working
```


---

## init-project-course

**Source:** `skills/init-project-course/skill.md`

---
name: init-project-course
description: "Use when you need to bootstrap a university course or module folder."
allowed-tools: Bash(mkdir*), Bash(mv*), Bash(ls*), Bash(tree*), Bash(find*), Bash(rm*), Bash(cp*), Read, Write, Edit, Glob, Grep, AskUserQuestion
argument-hint: "[no arguments — runs in current directory]"
---

# Init Project Course

> Bootstrap a university course or module folder into a clean, navigable structure. Designed for taught modules with lectures, workshops, assessments, and optionally recordings.

## When to Use

- University modules with lectures + workshops + assessments
- Course folders that have accumulated files over a term
- When the user says "organise this module", "init course", "set up this module folder"
- Any taught course with recurring weekly components

## When NOT to Use — Escalate

- To `/init-project-light` if it's a one-off document collection (no lectures/workshops structure)
- To `/init-project-research` if it's a research project that happens to be for a course

---

## Phase 1: Scan

Read everything already in the directory before asking questions.

1. List all files and folders (excluding `.claude/`, `.DS_Store`)
2. Identify content types:
   - **Lecture PDFs** — files matching `Lecture*` or containing "lecture" in name
   - **Seminar materials** — files matching `Seminar*`, `Session*`, or containing "seminar" in name (discussion-based modules use seminars instead of lectures)
   - **Lecture recordings** — video files (`.mp4`, `.mov`, `.mkv`, `.webm`, `.avi`) or folders named `recordings`
   - **Workshop folders** — folders matching `Workshop*`, `Lab*`, `Week*`, or numbered folders with exercise content
   - **Assessment folders** — folders containing "group", "individual", "exam", "coursework", "assignment", "portfolio"
   - **Workshop PDFs** — PDFs inside workshop folders that are NOT lectures (exercise sheets, briefs)
   - **Code projects** — `node_modules/`, `package.json`, `.py`, `.js`, `.ts` files inside workshop folders
   - **Notes** — personal notes, reading lists, exercise solutions (common in student modules)
3. Detect duplicates: lecture PDFs that appear in multiple locations
4. Note workshop numbering gaps (normal — not every week has a workshop)
5. Check for existing organisation (already has `lectures/`, `workshops/`, etc.)

**Goal:** Build a complete inventory so the interview is short.

---

## Phase 2: Interview (4-5 questions max)

Use `AskUserQuestion`. Only ask what you couldn't infer from Phase 1.

Pick from these (skip any you can already answer):

1. **What module is this?** — code + name (e.g., "IB9PK Advances in Behavioural Science")
2. **Are you a student or instructor?** — determines template variant (see Phase 3)
3. **Who teaches it?** — name(s) and role(s) (for student modules: instructor name; for instructor modules: module leader if different)
4. **What components exist?** — lectures/seminars, workshops, group work, individual work, exams, recordings
5. **Status?** — still in progress (more content coming) or archived/complete

If Phase 1 gave you enough, confirm your understanding instead of asking:
> "This looks like [module code + name]. You're [student/instructor]. It has [N] workshops, [N] lecture PDFs, and [assessment types]. Still in progress. Correct?"

**Always interview** — even if scan is comprehensive. Course folders affect a full term of work; assumptions are expensive.

---

## Phase 3: Organise

Present the proposed structure and **wait for explicit approval** before moving anything.

Full templates (student + instructor directory structures), workshop naming, lecture/recording/assessment handling rules: [references/organise-templates.md](references/organise-templates.md)

---

## Phase 4: Create CLAUDE.md

Follow the `lean-claude-md` rule. Include only:

1. **Module overview** — code, name, institution, programme, credits, 1-2 sentence description
2. **People** — instructor(s) and/or student, role
3. **Assessment** — type(s), format, word count/page limit, deadline(s) if known
4. **Directory structure** — compact tree of the organised layout
5. **Conventions** — detectable patterns (LaTeX compilation, GitHub repo naming, submission format)
6. **Status note** — "in progress" or "complete/archived", with note on what's still to come

**Do NOT include:**
- Lecture-by-lecture notes
- Workshop solution details
- Full assessment criteria (those live in `docs/` or `assessments/`)
- Anything that duplicates global rules

---

## Phase 5: Seed MEMORY.md

Create `MEMORY.md` using the appropriate template (student or instructor). Templates, settings.local.json, and vault entry details: [references/memory-and-settings.md](references/memory-and-settings.md)

---

## Phase 6: Settings

Create `.claude/settings.local.json` if missing. Full details: [references/memory-and-settings.md](references/memory-and-settings.md)

---

## Phase 7: Vault Sync

Offer to create entries in the vault tracking for this module (Student or Instructor). Database IDs and field mappings: [references/memory-and-settings.md](references/memory-and-settings.md)

---

## Phase 8: Confirmation

Short report:

```
Set up course project: <module code + name>
Role: Student / Instructor

Created:
  - CLAUDE.md
  - MEMORY.md (seeded with [student/instructor] template)
  - lectures/ or seminars/ (N PDFs, deduplicated from M locations)
  - notes/ (student only, if applicable)
  - recordings/ (if applicable)
  - workshops/ (N workshops, renamed from original folders)
  - assessments/{types}/ (moved from original folders)
  - docs/ (module specification, guidelines)
  - [.claude/settings.local.json if created]
  - [vault entry created in Modules Pipeline (Student/Instructor)]

Workshop naming:
  "Workshop 1 - JavaScript Bootcamp" → workshops/01-javascript-bootcamp
  "Workshop 6" → workshops/06-cwe-vulnerability-analysis
  ...
```

---

## Cross-References

| Skill | Relationship |
|-------|-------------|
| `/init-project-light` | For non-course document collections |
| `/init-project-research` | For research projects within a course |
| `/audit-project-course` | Run later to check the structure is still clean |
| `/update-project-doc` | Run later to refresh CLAUDE.md if the module grows |


---

## init-project-light

**Source:** `skills/init-project-light/skill.md`

---
name: init-project-light
description: "Use when you need to bootstrap a lightweight project with minimal structure."
allowed-tools: Bash(mkdir*), Bash(ls*), Bash(touch*), Read, Write, Edit, Glob, Grep, AskUserQuestion
argument-hint: "[no arguments — runs in current directory]"
---

# Init Project Light

> Lightweight project bootstrapper for small projects that don't need the full `/init-project-research` scaffold.

## When to Use

- Small document collections (proposals, applications, meeting notes)
- One-off or short-lived projects
- Projects without a code pipeline or Overleaf link
- When the user says "set up something light", "quick init", "organise this folder"
- Any project that doesn't warrant `/init-project-research`

## When NOT to Use — Escalate to `/init-project-research`

- Research papers targeting a journal or conference
- Projects with code, data, or computational pipelines
- Anything that needs Overleaf, git, or a vault atlas entry

---

## Phase 1: Scan

Read everything already in the directory before asking questions.

1. List all files and folders (excluding `.claude/`, `.DS_Store`)
2. Read text files (`.md`, `.tex`, `.bib`, `.txt`) to understand content — respect file size (skip files > 500 lines, note them)
3. Build a mental model: what is this project, what's the main output, who's involved?

**Goal:** Minimise interview questions by inferring answers from existing files.

---

## Phase 2: Interview (2-3 questions max)

Use `AskUserQuestion`. Only ask what you couldn't infer from Phase 1.

Pick from these (skip any you can already answer):

1. **What is this project?** — one sentence (e.g., "PhD research proposal for [University]")
2. **What's the main output?** — document, application, collection of notes, etc.
3. **Anyone else involved?** — names and roles if relevant

If Phase 1 gave you enough, confirm your understanding instead of asking:
> "From the files, this looks like [X]. The main output is [Y]. Correct?"

---

## Phase 3: Create CLAUDE.md

Follow the `lean-claude-md` rule. Include only:

1. **Project overview** — 2-3 sentences from interview/scan
2. **People** — if collaborators/supervisors exist
3. **Directory structure** — compact tree of what exists
4. **Conventions** — only if detectable (e.g., LaTeX compilation, bibliography style)
5. **Key context** — anything a future session needs to know immediately

**Do NOT include:**
- Detailed literature notes or reference lists
- Action items or timelines (those go to vault)
- Anything that duplicates global rules

---

## Phase 4: Organise (suggest, don't force)

Based on what's in the directory, **suggest** lightweight organisation. Present options and wait for approval.

### Standard suggestions

| Folder | When to suggest |
|--------|----------------|
| `to-sort/` | Multiple unsorted documents exist |
| `docs/` | Reference materials, guidelines, or background reading present |
| `archive/` | Old versions or abandoned drafts detected |

### Rules

- Never create more than 2-3 folders — this is a light project
- Never move files without explicit approval
- If the existing structure already makes sense, say so and skip this phase
- If there's a `.claude/settings.local.json`, leave it. If not, create one with standard permissions.

### Standard permissions (`.claude/settings.local.json`)

```json
{
  "permissions": {
    "allow": [
      "Bash(latexmk *)",
      "Bash(ls:*)",
      "Bash(mkdir:*)",
      "Bash(tree:*)",
      "Edit",
      "Glob",
      "Grep",
      "Read",
      "Write"
    ],
    "deny": []
  }
}
```

Only create if missing. Never overwrite existing permissions.

---

## Phase 5: Confirmation

Short report:

```
Set up lightweight project: <name>

Created:
  - CLAUDE.md
  - [any folders created]
  - [.claude/settings.local.json if created]

Skipped (use /init-project-research if needed later):
  - Git, Overleaf, vault atlas, code scaffold
```

---

## Cross-References

| Skill | Relationship |
|-------|-------------|
| `/init-project-research` | Escalate to this for full research projects |
| `/update-project-doc` | Run later to refresh CLAUDE.md if the project grows |


---

## init-project-research

**Source:** `skills/init-project-research/SKILL.md`

---
name: init-project-research
description: "Use when you need to bootstrap a full research project with directory scaffold and Overleaf symlink."
allowed-tools: Bash(mkdir*), Bash(ln*), Bash(ls*), Bash(git*), Bash(touch*), Bash(jq*), Bash(uv*), Bash(curl*), Bash(wget*), Read, Write, Edit, Glob, Grep, Task, WebSearch, WebFetch, AskUserQuestion
argument-hint: "[project-name or no arguments for guided setup]"
---

# Init Project Research

Interview-driven skill that scaffolds a research project directory, creates an Atlas topic, syncs to vault (Atlas + Pipeline + Venues), and integrates with the user's Task Management system.

## When to Use

- Starting a new research paper or project from scratch
- When the user says "new project", "set up a project", "init project", "bootstrap project"
- After deciding to pursue a new research idea that needs its own folder

## Modes

| Invocation | Behaviour |
|-----------|-----------|
| `/init-project-research` (no args) | Guided: full interview, no auto-detection unless CWD already contains project files |
| `/init-project-research <name>` | Targeted: uses `<name>` as the proposed slug, runs auto-detection if the directory exists, still walks the interview |

Both modes execute Phases 1–10 in order. The argument only seeds the slug guess in Round 1.

## Overview

Ten phases, in order:

1. **Interview** — gather project details via three structured rounds
2. **Validate** — pre-scaffold checks (atlas dup, sibling directories, existing files)
3. **Scaffold** — create directory structure based on project type
4. **Seed files** — populate CLAUDE.md, README.md, .gitignore from interview answers
5. **Overleaf symlink** — link `paper/` to Overleaf folder via mkdir + symlink
6. **Git init** — initialise repo and make first commit (conditional)
7. **Atlas sync** — create Atlas topic file, vault atlas entry, venue links
8. **Task Management integration** — update context library files
9. **Literature & Discovery** — run `/literature` +  in parallel
10. **Confirmation** — report what was created

---

## Phase 1: Interview

Use `AskUserQuestion` for structured input. Three rounds to avoid overwhelming.

### Pre-Interview: Auto-Detection

Before asking questions, scan the project directory (if it already exists) for metadata:

- **LaTeX files** — extract `\title{}`, `\author{}`, `\begin{abstract}`, `\begin{keyword}` from `.tex` files
- **Markdown files** — check for `README.md`, `notes.md` with `# Title` headings
- **BibTeX files** — note `.bib` presence for later phases
- **Overleaf symlink** — if `paper/` is a symlink, follow and scan the target

Present detected values as the first option (marked "Detected from paper") in interview questions. Always allow override. If the directory doesn't exist yet, skip auto-detection.

### Round 1 — Core Identity

1. **Project slug** — kebab-case identifier (e.g., `costly-voice`). Folder name on disk is Title Case with spaces (`Costly Voice`). Confirm the derived folder name.
2. **Working title** — full paper/project title.
3. **Authors / collaborators** — names and affiliations.
4. **Research area** — which parent folder under Projects/. Scan for existing theme folders and present as options. Also offer "New topic folder" and "Other location".
5. **Target venue** — journal, conference, or preprint. Ranking lookup, deadline capture, and CSV paths: [`references/round-1-venue.md`](references/round-1-venue.md).
6. **Deadline** — submission deadline if known.

### Round 2 — Setup Details

1. **Overleaf project** — exists or create? Read root from `~/.config/task-mgmt/overleaf-root` (fallback `~/Apps/Overleaf/`). Creating a folder under that root auto-creates the Overleaf project. Symlink details deferred to Phase 5.
2. **LaTeX template** — scan `Task Management/templates/` for options. Default: Working Paper (`templates/latex-wp/`). Also offer "None".
3. **Overleaf external sharing link** — read-only URL for collaborators.
4. **Git repository?** — Local git (Recommended) / GitHub remote / No git.
5. **GitHub release repo?** — only ask for Experimental, Computational, or Mixed projects. Yes / No / Later. Convention details: [`references/round-2-github.md`](references/round-2-github.md).
6. **Project type** — Experimental (`code/`, `data/`, `output/`) / Computational (`src/`, `tests/`, `experiments/`, `results/`) / Theoretical (minimal) / Mixed.
7. **HPC scaffold?** — only ask for Experimental, Computational, or Mixed. Yes / No / Later. Sbatch templates, sync scripts, project conventions: [`references/round-2-hpc.md`](references/round-2-hpc.md).

### Round 3 — Research Content

Paper type, abstract, key research questions, then paper-type-specific questions (empirical/theoretical/methodological/mixed) adapted from Lopez-Lira's idea evaluation template.

Full question set: [`references/interview-round3.md`](references/interview-round3.md).

---

## Phase 2: Validate

Pre-scaffold checks. Run before any directory creation. If any near-match is found, present the list to the user and confirm whether to proceed, merge, or extend. Do not silently scaffold alongside a duplicate.

1. **Atlas topic search** — grep for near-matches by title, slug keywords, theme:
   ```bash
   grep -ril "<title-keyword>" ~/Research-Vault/atlas/ 2>/dev/null
   ```
2. **Sibling directory listing** — list siblings in the parent theme folder, flag near-duplicates (same keywords, same stem with different venue suffix, typo-distance ≤ 2):
   ```bash
   ls -d "$RESEARCH_ROOT/<theme>/"*/ 2>/dev/null
   ```
3. **Paper sub-project check** — if scaffolding a new `paper-{venue}/` inside an existing project, list existing `paper*/` dirs and check for manuscript-content overlap (not just venue) before creating.
4. **Existing-files reorganisation** — if the target directory already exists with files, scan (excluding `.claude/`), read documents, present a reorganisation plan: keep in place / move to `docs/` / move to `docs/readings/` / move to `paper/` / move to `to-sort/` / absorb into seed files. Wait for approval, execute, double-check before deletions. Use any extracted interview content to reduce Round 3 questions.

If the directory doesn't exist, create it and proceed.

---

## Phase 3: Scaffold Directory

### Naming Convention

- **Slug** (kebab-case): `example-project` — citation keys, git refs.
- **Folder name** (Title Case with spaces): `Example Project` — directory on disk.

### Hard Rules

- **`paper/` is for LaTeX source files ONLY.** No code, data, scripts, computational artifacts. See `.claude/rules/overleaf-separation.md`.
- **Research papers are drafted in LaTeX (`.tex`), never Markdown.** Seed `paper-{venue}/paper/main.tex` from the LaTeX working-paper template. No Markdown drafts under `paper*/` — papers compile via `/latex` and sync to Overleaf. Markdown is reserved for README, notes, and context files outside `paper*/`.

### Common Core + Conditional Structure

**Common core** (always created): `CLAUDE.md`, `README.md`, `MEMORY.md`, `.gitignore`, `.context/`, `.claude/`, `docs/` (literature-review, readings, venues), `log/`, `paper-{venue}/` (with symlink + `correspondence/referee-reviews/`), `github-repo/` (optional), `knowledge/`, `reviews/INDEX.md` (manifest only — per-source subdirs created lazily, per `rules/review-artefact-routing.md`), `correspondence/editorial/`, `correspondence/referee-reviews/`, `to-sort/`.

> **Note:** the legacy `REVIEW-STATE.md` at project root + `reviews/` empty dir + `correspondence/internal-reviews/` layout is superseded by `rules/review-artefact-routing.md`. New projects scaffold the new layout directly; existing projects retrofit via `/tidy-project-reviews`. Per-paper `backup/` directories are created lazily by the LaTeX-compile PostToolUse hook and are gitignored via `paper-*/backup/`.

| Project type | Adds |
|--------------|------|
| Experimental | `code/python/`, `code/R/`, `data/raw/`, `data/processed/`, `output/{figures,tables,logs}/` |
| Computational | `src/<project>/`, `tests/`, `experiments/configs/`, `results/`, `pyproject.toml`, `.python-version` |
| Theoretical | — |
| Mixed | Prompt user |

**HPC scaffold** (optional, when Round 2 Q7 = Yes): adds `hpc/{submit.sbatch,sweep.sbatch,env-setup.sh,sync-up.sh,sync-down.sh,README.md}`. Full template list and sbatch invariants: [`references/round-2-hpc.md`](references/round-2-hpc.md).

**Venues:** seed `docs/venues/<venue-slug>/submission/`; conference venues also get a submission checklist.

**Python tooling:** always `uv` — never bare `pip`, `python`, or `requirements.txt`.

Full scaffold tree, hook details, .gitkeep placement, implementation commands: [`references/scaffold-tree.md`](references/scaffold-tree.md).

---

## Phase 4: Seed Files

### CLAUDE.md vs README.md

- **CLAUDE.md** — instructions for Claude: safety rules, folder structure, conventions, symlink paths. Follow the `lean-claude-md` rule.
- **README.md** — human-readable overview: title, authors, abstract, status checklist, links.

Both overlap on basic metadata but diverge in purpose.

Full templates: [`templates/seed-files.md`](templates/seed-files.md).

| File | Purpose |
|------|---------|
| `CLAUDE.md` | Claude instructions: overview, venue, RQs, setup, conventions |
| `README.md` | Human overview: title, authors, abstract, links, status |
| `.gitignore` | Standard ignores: OS, IDE, data, paper, Python, R, LaTeX |
| `MEMORY.md` | Knowledge base: notation, estimands, decisions, pitfalls |
| `reviews/INDEX.md` | Review-artefact manifest. Header only at scaffold; populated by review-producing skills/agents writing to `reviews/<source>/YYYY-MM-DD.md`. Maintained by `/review-recap`. See `rules/review-artefact-routing.md`. **Supersedes the legacy `REVIEW-STATE.md` at project root.** |
| `.context/current-focus.md` | Initial "just initialised" state |
| `.context/field-calibration.md` | Per-project domain profile placeholder (`/interview-me` populates) |
| `.context/project-recap.md` | Research design notes |
| `.claude/hooks/copy-paper-pdf.sh` | PDF copy hook |
| `log/YYYY-MM-DD-HHMM-setup.md` | Initial setup log |
| `docs/pipeline-manifest.md` | **Experimental/Computational only** — script/data/figure manifest. Template: [`templates/pipeline-manifest.md`](templates/pipeline-manifest.md) |
| `run_all.sh` | **Experimental/Computational only** — multi-language pipeline executor. Template: [`templates/run-all.sh`](templates/run-all.sh). `chmod +x` after creation. |

### Permissions Sync

After writing `.claude/settings.local.json`, merge global permissions from `~/.claude/settings.json` into it so the new project starts with full permissions from day one. `jq` union command and deny-array handling: [`references/paper-directory.md`](references/paper-directory.md) § Permissions Sync.

---

## Phase 5: Overleaf Symlink & Template

**Nested pattern:** each paper submission is a real directory at project root (e.g., `paper-ccs/`) containing a `paper/` **symlink** to the Overleaf folder. Venue-specific files (checklists, cover letters, R&R responses) live alongside the symlink without being synced to Overleaf.

**Overleaf naming:** `Paper {THEME_PREFIX} {Title Cased Slug} ({VENUE})` — theme prefix AND venue suffix both required, even for single-venue papers. Examples: `Paper ASG Privacy Compliance Gaming (CCS)`, `Paper MechDes Strategic Compliance (NeurIPS 26)`.

**Create the Overleaf folder via `mkdir`** under the root from `~/.config/task-mgmt/overleaf-root`. Overleaf auto-creates a project from a new folder. Never rename or delete Overleaf folders — see `.claude/rules/overleaf-separation.md`.

**Backup:** create `backup/<paper-dir-name>/` for each paper. Daily `backup-overleaf-papers.sh` populates them.

Full nested structure, theme-prefix table, symlink commands, backup loop: [`references/paper-directory.md`](references/paper-directory.md).

---

## Phase 6: Git Init (conditional)

Skip entirely if the user chose "No git" in Round 2.

```bash
cd "<project-path>" && git init && git branch -m main && git add . && git commit -m "Initialize project: <working-title>"
```

If GitHub remote requested: `gh repo create "user/<project-name>" --private --source=. --remote=origin --push`.

If local git only: remind to push before switching machines. **Do NOT push unless a remote was explicitly requested.**

---

## Phase 7: Atlas Sync

Creates the research topic in all systems: local file → vault atlas → Venues → project folder → documentation.

Full steps, Atlas defaults, and Atlas anti-patterns ("Never Do These"): [`references/atlas-sync.md`](references/atlas-sync.md).

---

## Phase 8: Task Management Integration

Three sub-steps writing into the Task Management context library: index update, paper context file, current-focus integration.

Full sub-steps, templates, edit policies: [`references/task-mgmt-sync.md`](references/task-mgmt-sync.md).

---

## Phase 9: Literature & Discovery

After scaffolding and syncing, run `/literature` and  in parallel via sub-agents for initial literature review + novelty assessment.

Full steps and error handling: [`references/literature-discovery.md`](references/literature-discovery.md).

---

## Phase 10: Confirmation Report

Print the structured confirmation after all phases complete.

Full template: [`references/confirmation-report.md`](references/confirmation-report.md).

---

## Error Handling & Rollback

Per the `multi-system-completeness` rule, partial state is the dominant failure mode for this skill. Track which phases completed, surface incomplete state, do not silently move on.

| Error | Response |
|-------|----------|
| Overleaf path doesn't exist | Create symlink anyway (resolves when Overleaf syncs). Warn user. |
| `gh` CLI not available | Skip GitHub remote, note in Phase 10 report. |
| `taskflow` MCP server fails | Skip vault entry, offer to retry. Note as incomplete in Phase 10. |
| Directory already exists with files | Phase 2 handles via reorganisation plan, not an error. |
| Duplicate Atlas slug | Flag and skip Atlas creation — may need merge into existing topic. |
| Phase fails after a previous phase wrote to disk | Phase 10 must list which systems were touched (local dir / Overleaf / vault / atlas / git remote) and which were not, so manual cleanup is targeted, not a guess. |

---

## Cross-References

| Skill | Relationship |
|-------|-------------|
| `/literature` | Runs in Phase 9 — initial literature review |
|  | Runs in Phase 9 — novelty assessment |
| `/project-safety` | Already handled — `.gitignore` and settings created during init |
| `/save-context` | Context library entries created during Phase 8 |
| `/session-log` | Offer to create a session log after init completes |
| `/interview-me` | To develop the research idea before scaffolding |
| `packages/atlas-vault/generate_recap.py` | Optional after init — regenerates `RECAP.md` portfolio index. Not required for `atlas.user.com` (atlas-workspace reads vault directly via Syncthing). |
| `/atlas-deploy` | Manual-only skill — user can run for schema validation + Mac Mini launchd restart. NOT needed for atlas.user.com to surface a new topic; that's automatic via Syncthing. |
| `/audit-project-research` | **Must mirror this scaffold.** When init adds a new directory or convention, add a matching audit phase there and update `/atlas-audit` SA1. |
| `/atlas-audit` | **Drift trigger:** new projects change theme dir counts — see `atlas-audit/references/drift-checks.md`. SA1 structure checks must stay consistent with this scaffold. |
| [`references/domain-profile-template.md`](references/domain-profile-template.md) | Template for economics/field-specific domain profiles — copy to project's `docs/domain-profile.md` during init for economics papers. |


---

## insights-deck

**Source:** `skills/insights-deck/SKILL.md`

---
name: insights-deck
description: "Use when you need a timestamped Claude Code insights report and Beamer presentation."
allowed-tools: Bash(latexmk*), Bash(pdflatex*), Bash(xelatex*), Bash(mkdir*), Bash(ls*), Bash(cp*), Read, Write, Edit, Glob, Grep, Task
argument-hint: (no arguments)
---

# Insights Deck Skill

> Archive a Claude Code `/insights` HTML report and generate a Beamer presentation summarising the findings. All outputs go to `log/insights/` with date stamps.

## When to Use

- After running `/insights` to review your Claude Code usage patterns
- When you want a shareable deck summarising how you use Claude Code
- For periodic self-reflection on AI-assisted workflow

## Scope

This skill produces **two outputs only**: an archived HTML report and a Beamer deck. Do NOT use insights suggestions to create plans, rules, CLAUDE.md edits, or other follow-up actions during this skill's execution. If the user wants to act on suggestions, that happens after the deck is delivered — as a separate conversation.

---

## Phase 1 — Generate & Archive Insights

### Step 1: Prompt the user to run `/insights`

`/insights` is a built-in Claude Code command that cannot be invoked programmatically. Tell the user:

> Please run `/insights` now. Once the HTML report opens in your browser, let me know and I'll continue.

### Step 2: Locate the generated HTML

After `/insights` completes, find the most recent insights HTML file:

```bash
ls -t /tmp/claude-insights-*.html 2>/dev/null | head -1
```

If not found in `/tmp/`, check the user's home directory and common download locations. Ask the user for the path if it can't be located automatically.

### Step 3: Archive the HTML

Each insights run gets its own date folder:

```bash
mkdir -p log/insights/YYYY-MM-DD
cp <source-html> log/insights/YYYY-MM-DD/insights-YYYY-MM-DD-log.html
```

Use today's date for the timestamp.

---

## Phase 2 — Build Beamer Deck

### Step 1: Read and extract findings

Read the archived HTML file (`log/insights/YYYY-MM-DD/insights-YYYY-MM-DD-log.html`). Extract:

1. **Usage patterns** — most-used tools, session frequency, typical session length
2. **Strengths** — what's working well in the workflow
3. **Friction points** — repeated failures, slow patterns, underused features
4. **Recommendations** — suggested improvements

### Step 2: Design the deck structure

Apply rhetoric principles from the `beamer-deck` skill (condensed — no sub-agent reviews needed for an internal deck):

- **Assertion titles** — every frame title states a claim, not a label
- **One idea per slide** — split if a slide has two ideas
- **Three-act arc:**
  - Act I (Tension): Current usage snapshot — what does the data show?
  - Act II (Development): Patterns, strengths, friction points
  - Act III (Resolution): Recommendations and next steps
- **MB/MC balance** — vary dense and light slides deliberately
- **Pyramid principle** — lead with conclusions, then support

### Step 3: Generate the `.tex` file

Write to `log/insights/YYYY-MM-DD/insights-YYYY-MM-DD-deck.tex` with:

- `\documentclass[aspectratio=169,11pt]{beamer}`
- Original inline theme (no default Beamer themes)
- Professional colour palette:
  ```latex
  \definecolor{Midnight}{HTML}{1A1A2E}
  \definecolor{DeepBlue}{HTML}{16213E}
  \definecolor{RoyalBlue}{HTML}{0F3460}
  \definecolor{Coral}{HTML}{E94560}
  \definecolor{SoftGray}{HTML}{BDC3C7}
  \definecolor{CloudWhite}{HTML}{FAFBFC}
  ```
- Suggested structure (adapt based on findings):
  1. Title slide — "Claude Code Usage: [Month Year]"
  2. Opening claim — lead with the most striking finding
  3. Usage overview — session count, tool distribution, time patterns
  4. Top strengths (1–2 slides)
  5. Key friction points (1–2 slides)
  6. Recommendations (1–2 slides)
  7. Closing — single actionable takeaway

### Step 4: Compile

Create a `.latexmkrc` in the date folder if not present:

```perl
$out_dir = 'out';
# Copy PDF back to source directory after build
END { system("cp $out_dir/*.pdf . 2>/dev/null") if defined $out_dir; }
```

Then compile:

```bash
cd log/insights/YYYY-MM-DD && latexmk -pdf insights-YYYY-MM-DD-deck.tex
```

### Step 5: Fix all warnings

Parse `out/*.log` for overfull/underfull hbox/vbox warnings. Fix every one. Recompile until clean.

The `.latexmkrc` copies the PDF from `out/` back to the date folder automatically.

---

## Output

When complete, the date folder should contain:

```
log/insights/YYYY-MM-DD/
├── insights-YYYY-MM-DD-log.html     # Archived /insights HTML
├── insights-YYYY-MM-DD-deck.tex     # Beamer source
├── insights-YYYY-MM-DD-deck.pdf     # Compiled PDF
├── .latexmkrc                       # Build config
└── out/                             # Build artifacts
```

Each `/insights-deck` run creates a new date folder, keeping the parent `log/insights/` clean.

---

## Cross-References

| Skill | Relationship |
|-------|-------------|
| `/beamer-deck` | Full rhetoric framework and multi-agent review (this skill uses a condensed version) |
| `/latex` | **Default compiler** — use for compilation with auto error resolution |
| `/latex` | Manual compilation config details, `.latexmkrc` setup |
| `/session-log` | Complements insights with session-level detail |


---

## interview-me

**Source:** `skills/interview-me/SKILL.md`

---
name: interview-me
description: "Use when you need to conduct a structured interview to extract knowledge or preferences."
disable-model-invocation: true
argument-hint: "[brief topic or 'start fresh']"
allowed-tools: Read, Write, Edit
---

# Research Interview

Conduct a structured interview to help formalise a research idea into a concrete specification.

**Input:** `$ARGUMENTS` — a brief topic description or "start fresh" for open-ended exploration.

---

## How This Works

This is a **conversational** skill. Instead of producing a report immediately, you conduct an interview by asking questions one at a time, probing deeper based on answers, and building toward a structured research specification.

**Do NOT use AskUserQuestion.** Ask questions directly in your text responses, one or two at a time. Wait for the user to respond before continuing.

Before starting, read `.context/profile.md` and `.context/projects/_index.md` to understand the researcher's areas and active projects. If the topic relates to an existing project, read its context file too.

---

## Interview Structure

### Phase 1: The Big Picture (1–2 questions)
- "What phenomenon or puzzle are you trying to understand?"
- "Why does this matter? Who should care about the answer?"

### Phase 2: Theoretical Motivation (1–2 questions)
- "What's your intuition for why X happens / what drives Y?"
- "What would standard theory predict? Do you expect something different?"

### Phase 3: Data and Setting (1–2 questions)
- "What data do you have access to, or what data would you ideally want?"
- "Is there a specific context, time period, or institutional setting you're focused on?"

### Phase 4: Identification (1–2 questions)
- "Is there a natural experiment, policy change, or source of variation you can exploit?"
- "What's the biggest threat to a causal interpretation?"

### Phase 5: Expected Results (1–2 questions)
- "What would you expect to find? What would surprise you?"
- "What would the results imply for policy or theory?"

### Phase 6: Contribution (1 question)
- "How does this differ from what's already been done? What's the gap you're filling?"

---

## Adapting to the Research Area

the user's work spans multiple disciplines. Adapt the interview to the domain:

- **Human-AI collaboration / MCDM**: Focus on decision architecture, experimental design, behavioural measures, and what "better" decisions look like.
- **Multi-agent systems**: Focus on agent design, interaction protocols, equilibrium concepts, and simulation methodology.
- **Organisational behaviour**: Focus on mechanisms, field vs. lab settings, mediators/moderators, and internal validity.
- **Carbon markets / environmental**: Focus on policy variation, compliance data, market microstructure, and welfare implications.

If the research is non-quantitative (conceptual, design science, qualitative), adjust: replace "Identification" with "Analytical Framework" and "Data" with "Empirical/Evidence Strategy".

---

### Phase 7: Field Calibration (optional, auto-triggered)

**Auto-triggers when:** the project has no `.context/field-calibration.md`, or it exists but still contains `<placeholders>`.

**Skip when:** the file already exists with populated content, unless the user explicitly asks to update it.

Ask 2–3 targeted questions:

- "Which journals or conferences are you targeting? I can cross-reference venue rankings." (Use `.context/resources/venue-rankings.md` to validate and suggest alternatives.)
- "Which seminal papers would a reviewer in this subfield expect to see cited?"
- "What's the typical identification strategy in this subfield — and what do reviewers most often attack?"

After the interview, populate `.context/field-calibration.md` from answers combined with Research Spec content. Use the template at `skills/init-project-research/templates/field-calibration.md`.

If field-calibration already exists with content: ask the user whether to update specific sections or keep as-is.

---

## After the Interview

Once you have enough information (typically 5–8 exchanges), produce a **Research Specification Document**:

```markdown
# Research Specification: [Title]

**Date:** [YYYY-MM-DD]
**Researcher:** the user

## Research Question

[Clear, specific question in one sentence]

## Motivation

[2–3 paragraphs: why this matters, theoretical context, policy relevance]

## Hypothesis

[Testable prediction with expected direction]

## Empirical Strategy

- **Method:** [e.g., DiD, experiment, simulation, case study]
- **Treatment/Manipulation:** [What varies]
- **Control/Comparison:** [Comparison group or baseline]
- **Key identifying assumption:** [What must hold]
- **Robustness checks:** [Pre-trends, placebo, alternative specifications]

## Data

- **Primary dataset:** [Name, source, coverage]
- **Key variables:** [Treatment, outcome, controls]
- **Sample:** [Unit of observation, time period, N]

## Expected Results

[What the researcher expects to find and why]

## Contribution

[How this advances the literature — 2–3 sentences]

## Open Questions

[Issues raised during the interview that need further thought]
```

**Save to:** the project root or `docs/` if inside a research project, or present to the user for placement.

**Also produces** (if Phase 7 triggered): `.context/field-calibration.md` — the per-project domain profile that agents use to calibrate reviews.

---

## Interview Style

- **Be curious, not prescriptive.** Your job is to draw out the researcher's thinking, not impose your own ideas.
- **Probe weak spots gently.** If the identification strategy sounds fragile, ask "What would a sceptic say about...?" rather than "This won't work because..."
- **Build on answers.** Each question should follow from the previous response.
- **Know when to stop.** If the researcher has a clear vision after 4–5 exchanges, move to the specification. Don't over-interview.
- **Use British English** throughout (the user's preference).

---

## Cross-References

| Skill | When to use instead/alongside |
|-------|-------------------------------|
| `/devils-advocate` | After the spec is written — stress-test the idea |
| `/literature` | To find related work mentioned during the interview |
| `/init-project-research` | To scaffold a project once the spec is approved (seeds empty field-calibration) |


---

## latex

**Source:** `skills/latex/SKILL.md`

---
name: latex
description: "Use when you need to compile a LaTeX document — includes autonomous error resolution, citation audit, and quality scoring."
allowed-tools: Bash(latexmk*), Bash(xelatex*), Bash(pdflatex*), Bash(biber*), Bash(bibtex*), Bash(mkdir*), Bash(ls*), Bash(wc*), Bash(cp*), Read, Write, Edit, Grep, Glob
argument-hint: [tex-file-path]
---

# LaTeX Document Compilation

> Default compilation skill for all LaTeX documents. Compiles with autonomous error detection and resolution (up to 5 iterations), runs a citation audit on clean builds, and produces a quality score.

## When to Use

- **Default method** for all LaTeX compilation
- Any `.tex` file that should compile to PDF
- When compilation fails and you want automatic diagnosis and repair
- When you want a post-compilation citation audit

## When NOT to Use

- Markdown documents — use plain markdown, not LaTeX
- Quick notes or drafts — LaTeX overhead not worth it
- Documents that don't need citations, equations, or precise formatting
- Documents with exotic custom classes that need manual debugging

---

## Quality Scoring

Apply numeric quality scoring using the shared framework and skill-specific rubric:

- **Framework:** [`../shared/quality-scoring.md`](../shared/quality-scoring.md) — severity tiers, thresholds, verdict rules
- **Rubric:** [`references/quality-rubric.md`](references/quality-rubric.md) — issue-to-deduction mappings for this skill

Start at 100, deduct per issue found, apply verdict. Include the Score Block in the final report.

## Critical Rules

1. **Build artifacts go to `out/`, PDF stays in the source directory.** Ensure `.latexmkrc` exists with `$out_dir = 'out'` and an `END {}` block to copy the PDF back (see pre-flight below). For VS Code builds, `.latexmkrc` in subdirectories is **not picked up** — see "VS Code Integration" section for the required `.vscode/settings.json` config.
2. **NEVER write BibTeX entries from memory.** Always verify against web sources (CrossRef, Google Scholar, DOI lookup) before writing. See the `/literature` skill.
3. **Check document class before adding packages.** Some classes load packages internally (e.g., `elsarticle` loads `natbib` — adding `\usepackage{natbib}` causes errors).
4. **Maximum 5 fix iterations.** If the document still has errors after 5 auto-fix cycles, stop and report the unresolved errors to the user.
5. **Never silently swallow errors.** Every fix must be reported: what was wrong, what was changed, and which file was edited.
6. **Preserve user intent.** Auto-fixes should be minimal and conservative. Add packages or overrides — never remove user content.
7. **Citation audit requires clean compilation.** Only run the `\cite{}` vs `.bib` cross-check after zero errors.
8. **Run `/bib-validate` when new citations were added.** The citation audit only checks key cross-references. When `.bib` entries were added or modified since the last validation, also run `/bib-validate` for full metadata quality checks (preprint staleness, DOI presence, required fields, author formatting). This is mandatory.

---

## Protocol

### Phase 1: Pre-flight

1. **Locate the `.tex` file.** Resolve the path (absolute or relative to CWD).
2. **Identify the project directory** — the folder containing the `.tex` file.
3. **Ensure `.latexmkrc` exists** in the project directory with at minimum:
   ```perl
   $out_dir = 'out';
   # Copy PDF back to source directory after build
   END { system("cp $out_dir/*.pdf . 2>/dev/null") if defined $out_dir; }
   ```
   If a `.latexmkrc` already exists, verify it sets `$out_dir = 'out'` and has the `END {}` block. If either is missing, add it. Do not overwrite other settings.
4. **Create `out/` directory** if it doesn't exist: `mkdir -p <project-dir>/out`.
5. **Identify the `.bib` file(s)** referenced in the document (scan for `\bibliography{}`, `\addbibresource{}`, or `\bibinput{}`). Note their paths for Phase 4.

### Phase 2: Compile-Fix Loop

Run up to **5 iterations**. Each iteration:

#### Step 2a — Compile

```bash
cd <project-dir> && latexmk -interaction=nonstopmode <filename>.tex 2>&1
```

Capture the full output. The log file will be at `out/<filename>.log`.

#### Step 2b — Read the log

Read `out/<filename>.log` in full. Parse for errors and warnings.

#### Step 2c — Classify errors

Check the log against the known error patterns below. If an error matches, apply the fix and go to Step 2a. If no known pattern matches, record the error as **unresolved** and stop the loop.

**Same-error circuit breaker.** Independent of the 5-iteration cap: if the same error (same line family, same pattern signature) survives **3 consecutive fix attempts**, stop the loop early. Continued attempts on a stuck error compound damage rather than resolve it. Report what was tried, quote the log line, and ask the user how to proceed. A common signature: `Illegal parameter number` jumping between line numbers as you edit — that is the diagnostic for a parameterized TikZ style defined inside a Beamer frame; see `skills/shared/tikz-rules.md` Rule 11.

---

### Known Error Patterns & Auto-Fixes

Check the log against these patterns. Full fix instructions: [`references/known-errors.md`](references/known-errors.md)

| # | Pattern | Key log signature |
|---|---------|-------------------|
| 1 | Missing package | `File '<pkg>.sty' not found` or undefined command from known package |
| 2 | Font/symbol conflicts | `Command \<name> already defined` |
| 3 | Undefined citation | `Citation '<key>' ... undefined` or biblatex entry not found |
| 4 | Missing image/file | `File '<path>' not found` (pdftex.def or LaTeX) |
| 5 | Stale auxiliary files | Corrupted `.aux`/`.bbl`/`.bcf`, or `no \bibstyle command` |
| 6 | Beamer/enumitem clash | `Option clash for package enumitem` or `\item already defined` |
| 7 | xcolor option conflicts | `Option clash for package xcolor` or undefined `\rowcolor` |
| 8 | TikZ reserved keys | `I do not know the key '/tikz/<name>'` or pgfkeys error |

If an error matches, read the full fix from the reference and apply it. If no pattern matches, record as **unresolved** and stop the loop.

#### 2.4 PDF backup (paper directories only)

**Only run if the compile-fix loop above ended with a successful compilation (PDF exists).**

If the `.tex` file is inside a `paper-{venue}/paper/` structure (where `paper/` is a symlink to Overleaf):

1. **Identify the paper wrapper** — the parent of the `paper/` symlink (e.g., `paper-jbdm/`).
2. **Create the backup directory:** `mkdir -p <paper-wrapper>/backup`
3. **Copy the PDF:**
   ```bash
   cp <paper-wrapper>/paper/<filename>.pdf <paper-wrapper>/backup/<wrapper-name>_vcurrent.pdf
   ```

**Detection logic:**

- The project directory containing the `.tex` file is a symlink named `paper`.
- Its parent directory name starts with `paper-`.
- If either condition is false, skip this sub-step silently.

---

### Phase 3: Final Report

After the loop ends (either clean compilation or max iterations reached), report:

#### Compilation Status

| Field | Value |
|-------|-------|
| **Status** | Clean / Errors remaining |
| **Iterations** | N of 5 |
| **Pages** | (from log: `Output written on ... (N pages)`) |
| **Warnings** | Count of remaining warnings (overfull/underfull hbox, etc.) |
| **Fixes applied** | List each fix: what error, what was changed, which file |
| **Unresolved errors** | List any errors that couldn't be auto-fixed |

#### How to extract page count

```bash
grep -o "Output written on .* ([0-9]* page" out/<filename>.log | grep -o "[0-9]* page"
```

#### How to count warnings

```bash
grep -c "Warning" out/<filename>.log
```

**Breadcrumb:** Append to `.planning/state.md` (if exists) or `.context/current-focus.md`:
```
### [/latex] Compilation complete [YYYY-MM-DD HH:MM]
- **Done:** [Clean/Errors remaining, N iterations, N pages, N fixes applied]
- **Outputs:** [PDF at <path>]
- **Next:** [Citation audit (if clean) or manual error resolution]
```

---

### Phase 4: Citation Audit (clean builds only)

**Only run this phase if Phase 2 ended with zero errors.**

1. **Extract all `\cite` keys** from the `.tex` file (and any `\input`/`\include` files):
   - Match `\cite{...}`, `\citep{...}`, `\citet{...}`, `\textcite{...}`, `\parencite{...}`, `\autocite{...}`, and multi-key variants like `\cite{key1,key2}`.
2. **Extract all bib entry keys** from the `.bib` file(s): match `@<type>{<key>,`.
3. **Cross-reference:**

| Check | What it finds |
|-------|--------------|
| **Missing in .bib** | Keys cited in `.tex` but absent from `.bib` |
| **Unused in .tex** | Keys defined in `.bib` but never cited |
| **Possible typos** | Near-matches between missing cite keys and existing bib keys |

4. **Report** the results as a table. Do not modify any files during the audit — report only.

---

### Phase 5: Quality Score

After all phases complete, compute the quality score:

1. Read [`references/quality-rubric.md`](references/quality-rubric.md) for deduction mappings.
2. Log every issue from Phases 2-4 (unresolved errors, remaining warnings, citation mismatches).
3. Compute score (100 - total deductions), apply verdict per [`../shared/quality-scoring.md`](../shared/quality-scoring.md).
4. Append the Score Block to the compilation report:

```markdown
## Quality Score

| Metric | Value |
|--------|-------|
| **Score** | XX / 100 |
| **Verdict** | Ship / Ship with notes / Revise / Revise (major) / Blocked |

### Deductions

| # | Issue | Tier | Deduction | Category |
|---|-------|------|-----------|----------|
| 1 | [description] | [tier] | -X | [category] |
| | **Total deductions** | | **-XX** | |
```

#### 5.1 Output verification (before commit)

When the compile produced a PDF (and any backup copy), emit an outputs manifest and run the shared verifier per [`_shared/verify-outputs.md`](../_shared/verify-outputs.md):

1. Write manifest to `<project>/.claude/state/outputs-manifest-<UTC-timestamp>.json` listing every file written this invocation (PDF, backup PDF if 2.4 ran, log files).
2. Run:

   ```bash
   python3 "$HOME/.claude/skills/_shared/verify_outputs.py" \
       --manifest "$MANIFEST" \
       --project-root "$PROJECT_ROOT"
   ```

3. If the verifier exits non-zero, **do not commit**. Surface the missing-files list and stop.

Closes the "hallucinated outputs" failure class (commit `b2cff75`, 2026-04-18).

---

## Configuration Reference

### Output Directory

All LaTeX build artifacts (`.aux`, `.log`, `.bbl`, `.fls`, etc.) go to an `out/` subfolder relative to the source file. The **PDF is copied back** to the source directory after each successful build, so it lives alongside the `.tex` file for easy access.

The PDF-copy convention is enforced in **two places** — keep them in sync when making changes:

1. **`.latexmkrc`** (per-project) — Perl `END {}` block copies PDF after terminal/Claude Code builds
2. **VS Code `.vscode/settings.json`** (per-workspace) — explicit latexmk args in LaTeX Workshop tool definition

VS Code integration, engine auto-detection (pdfLaTeX/XeLaTeX/LuaLaTeX), manual override configs, reference checking scripts, and manual compilation commands:

**[references/latex-configs.md](references/latex-configs.md)**

### Overleaf-Synced Projects

When a project is synced to Overleaf (via Dropbox or Git):
- The `out/` directory will sync to Overleaf but Overleaf ignores it — this is fine
- Always use `.latexmkrc` to enforce `out/` — Overleaf ignores this file too
- Overleaf compiles independently on its server; local compilation is for verification only
- The `.bst` file (e.g., `elsarticle-harv.bst`) lives in the source directory, not `out/`

### Local-Only Projects (No Overleaf)

Not all projects sync to Overleaf. For local-only projects:
- The same `out/` and `.latexmkrc` conventions apply — this keeps the working directory clean regardless of sync method
- There is no `paper/` symlink — `.tex` files live directly in the project root or a subdirectory

---

## Templates

See [`references/templates.md`](references/templates.md) for working paper template location, files, citation style toggle, bibliography file naming conventions, and bibliography command reference.

---

## Related Skills

| Situation | Delegate to |
|-----------|-------------|
| Need to find or verify a bibliography entry | `/literature` |
| Full academic proofreading after clean compilation | `/proofread` |
| Detailed `.bib` validation beyond cite-key matching | `/bib-validate` |
| Beamer presentations specifically | `/beamer-deck` (which uses this skill internally for compilation) |
| Fleet-wide compilation health check | `/latex-health-check` (project discovery, 3 iterations per project, cross-project checks) |

---

## Examples

### Basic usage

> "Compile my paper at `~/papers/mcdm-survey/main.tex`"

Runs the full protocol: pre-flight → compile-fix loop → report → citation audit → quality score.

### After fixing a known issue

> "Recompile — I added the missing package manually"

Runs from Phase 2 directly (pre-flight can be skipped if `.latexmkrc` and `out/` already exist).

### Targeted fix

> "My paper won't compile — something about Bbbk"

Identifies as Pattern 2 (font conflict), applies the `\let\Bbbk\relax` fix, recompiles.


---

## latex-autofix

**Source:** `skills/latex-autofix/SKILL.md`

---
name: latex-autofix
description: "Use when you need to compile LaTeX with autonomous error resolution and citation audit."
allowed-tools: Bash(latexmk*), Bash(xelatex*), Bash(pdflatex*), Bash(biber*), Bash(bibtex*), Bash(mkdir*), Bash(ls*), Bash(wc*), Bash(cp*), Read, Write, Edit, Grep, Glob
argument-hint: [tex-file-path]
---

# LaTeX Auto-Fix Compilation

> Compile LaTeX documents with autonomous error detection and resolution. Wraps the standard `/latex` workflow with a fix-loop that handles the most common compilation failures without manual intervention.

## When to Use

- **Default method** for all LaTeX compilation — use this instead of `/latex` unless you need manual control
- Any `.tex` file that should compile to PDF
- When compilation fails and you want automatic diagnosis and repair
- When you want a post-compilation citation audit

## When NOT to Use

- Quick one-off compilations where you already know the document is clean — `/latex` is fine
- Documents with exotic custom classes that need manual debugging

---

## Quality Scoring

Apply numeric quality scoring using the shared framework and skill-specific rubric:

- **Framework:** [`../shared/quality-scoring.md`](../shared/quality-scoring.md) — severity tiers, thresholds, verdict rules
- **Rubric:** [`references/quality-rubric.md`](references/quality-rubric.md) — issue-to-deduction mappings for this skill

Start at 100, deduct per issue found, apply verdict. Include the Score Block in the Phase 5 report.

## Critical Rules

1. **Build artifacts go to `out/`, PDF stays in the source directory.** Ensure `.latexmkrc` exists with `$out_dir = 'out'` and an `END {}` block to copy the PDF back (see pre-flight below). For VS Code builds, `.latexmkrc` in subdirectories is **not picked up** — see `/latex` skill's "VS Code LaTeX Workshop Gotchas" section for the required `.vscode/settings.json` config (`-cd`, `-outdir=out`, `forceRecipeUsage: true`).
2. **Maximum 5 fix iterations.** If the document still has errors after 5 auto-fix cycles, stop and report the unresolved errors to the user.
3. **Never silently swallow errors.** Every fix must be reported: what was wrong, what was changed, and which file was edited.
4. **Preserve user intent.** Auto-fixes should be minimal and conservative. Add packages or overrides — never remove user content.
5. **Citation audit requires clean compilation.** Only run the `\cite{}` vs `.bib` cross-check after zero errors.
6. **Run `/bib-validate` when new citations were added.** The Phase 4 citation audit only checks key cross-references. When `.bib` entries were added or modified since the last validation, also run `/bib-validate` for full metadata quality checks (preprint staleness, DOI presence, required fields, author formatting). This is mandatory — do not skip it.

---

## Protocol

### Phase 1: Pre-flight

1. **Locate the `.tex` file.** Resolve the path (absolute or relative to CWD).
2. **Identify the project directory** — the folder containing the `.tex` file.
3. **Ensure `.latexmkrc` exists** in the project directory with at minimum:
   ```perl
   $out_dir = 'out';
   # Copy PDF back to source directory after build
   END { system("cp $out_dir/*.pdf . 2>/dev/null") if defined $out_dir; }
   ```
   If a `.latexmkrc` already exists, verify it sets `$out_dir = 'out'` and has the `END {}` block. If either is missing, add it. Do not overwrite other settings.
4. **Create `out/` directory** if it doesn't exist: `mkdir -p <project-dir>/out`.
5. **Identify the `.bib` file(s)** referenced in the document (scan for `\bibliography{}`, `\addbibresource{}`, or `\bibinput{}`). Note their paths for Phase 3.

### Phase 2: Compile–Fix Loop

Run up to **5 iterations**. Each iteration:

#### Step 2a — Compile

```bash
cd <project-dir> && latexmk -interaction=nonstopmode <filename>.tex 2>&1
```

Capture the full output. The log file will be at `out/<filename>.log`.

#### Step 2b — Read the log

Read `out/<filename>.log` in full. Parse for errors and warnings.

#### Step 2c — Classify errors

Check the log against the known error patterns below. If an error matches, apply the fix and go to Step 2a. If no known pattern matches, record the error as **unresolved** and stop the loop.

---

### Known Error Patterns & Auto-Fixes

Check the log against these patterns. Full fix instructions: [`references/known-errors.md`](references/known-errors.md)

| # | Pattern | Key log signature |
|---|---------|-------------------|
| 1 | Missing package | `File '<pkg>.sty' not found` or undefined command from known package |
| 2 | Font/symbol conflicts | `Command \<name> already defined` |
| 3 | Undefined citation | `Citation '<key>' ... undefined` or biblatex entry not found |
| 4 | Missing image/file | `File '<path>' not found` (pdftex.def or LaTeX) |
| 5 | Stale auxiliary files | Corrupted `.aux`/`.bbl`/`.bcf`, or `no \bibstyle command` |
| 6 | Beamer/enumitem clash | `Option clash for package enumitem` or `\item already defined` |
| 7 | xcolor option conflicts | `Option clash for package xcolor` or undefined `\rowcolor` |
| 8 | TikZ reserved keys | `I do not know the key '/tikz/<name>'` or pgfkeys error |

If an error matches, read the full fix from the reference and apply it. If no pattern matches, record as **unresolved** and stop the loop.

---

### Phase 2.5: PDF Backup (paper directories only)

**Only run if Phase 2 ended with a successful compilation (PDF exists).**

If the `.tex` file is inside a `paper-{venue}/paper/` structure (where `paper/` is a symlink to Overleaf):

1. **Identify the paper wrapper** — the parent of the `paper/` symlink (e.g., `paper-jbdm/`).
2. **Create the backup directory:** `mkdir -p <paper-wrapper>/backup`
3. **Copy the PDF:**
   ```bash
   cp <paper-wrapper>/paper/<filename>.pdf <paper-wrapper>/backup/<wrapper-name>_vcurrent.pdf
   ```
   Example: `paper-jbdm/paper/main.pdf` → `paper-jbdm/backup/paper-jbdm_vcurrent.pdf`

**Detection logic:**
- The project directory containing the `.tex` file is a symlink named `paper`
- Its parent directory name starts with `paper-`
- If either condition is false, skip this phase silently

**Skip if:** compilation failed, or the `.tex` file is not inside a paper directory structure.

---

### Phase 3: Final Report

After the loop ends (either clean compilation or max iterations reached), report:

#### Compilation Status

| Field | Value |
|-------|-------|
| **Status** | Clean / Errors remaining |
| **Iterations** | N of 5 |
| **Pages** | (from log: `Output written on ... (N pages)`) |
| **Warnings** | Count of remaining warnings (overfull/underfull hbox, etc.) |
| **Fixes applied** | List each fix: what error, what was changed, which file |
| **Unresolved errors** | List any errors that couldn't be auto-fixed |

#### How to extract page count

```bash
grep -o "Output written on .* ([0-9]* page" out/<filename>.log | grep -o "[0-9]* page"
```

#### How to count warnings

```bash
grep -c "Warning" out/<filename>.log
```

---

### Phase 4: Citation Audit (clean builds only)

**Only run this phase if Phase 2 ended with zero errors.**

1. **Extract all `\cite` keys** from the `.tex` file (and any `\input`/`\include` files):
   - Match `\cite{...}`, `\citep{...}`, `\citet{...}`, `\textcite{...}`, `\parencite{...}`, `\autocite{...}`, and multi-key variants like `\cite{key1,key2}`.
2. **Extract all bib entry keys** from the `.bib` file(s): match `@<type>{<key>,`.
3. **Cross-reference:**

| Check | What it finds |
|-------|--------------|
| **Missing in .bib** | Keys cited in `.tex` but absent from `.bib` |
| **Unused in .tex** | Keys defined in `.bib` but never cited |
| **Possible typos** | Near-matches between missing cite keys and existing bib keys |

4. **Report** the results as a table. Do not modify any files during the audit — report only.

---

### Phase 5: Quality Score

After all phases complete, compute the quality score:

1. Read [`references/quality-rubric.md`](references/quality-rubric.md) for deduction mappings.
2. Log every issue from Phases 2-4 (unresolved errors, remaining warnings, citation mismatches).
3. Compute score (100 - total deductions), apply verdict per [`../shared/quality-scoring.md`](../shared/quality-scoring.md).
4. Append the Score Block to the compilation report:

```markdown
## Quality Score

| Metric | Value |
|--------|-------|
| **Score** | XX / 100 |
| **Verdict** | Ship / Ship with notes / Revise / Revise (major) / Blocked |

### Deductions

| # | Issue | Tier | Deduction | Category |
|---|-------|------|-----------|----------|
| 1 | [description] | [tier] | -X | [category] |
| | **Total deductions** | | **-XX** | |
```

---

## Integration with Other Skills

| Situation | Delegate to |
|-----------|-------------|
| Need to find or verify a bibliography entry | `/literature` |
| Full academic proofreading after clean compilation | `/proofread` |
| Detailed `.bib` validation beyond cite-key matching | `/bib-validate` |
| Beamer presentations specifically | `/beamer-deck` (which uses this skill internally for compilation) |

---

## Examples

### Basic usage

> "Compile my paper at `~/papers/mcdm-survey/main.tex`"

Runs the full protocol: pre-flight → compile–fix loop → report → citation audit.

### After fixing a known issue

> "Recompile — I added the missing package manually"

Runs from Phase 2 directly (pre-flight can be skipped if `.latexmkrc` and `out/` already exist).

### Targeted fix

> "My paper won't compile — something about Bbbk"

Identifies as Pattern 2 (font conflict), applies the `\let\Bbbk\relax` fix, recompiles.


---

## latex-health-check

**Source:** `skills/latex-health-check/SKILL.md`

---
name: latex-health-check
description: "Use when you need to compile all LaTeX projects and check cross-project consistency."
allowed-tools:
  - Read
  - Edit
  - Write
  - Glob
  - Grep
  - Bash(latexmk*)
  - Bash(pdflatex*)
  - Bash(biber*)
  - Bash(bibtex*)
  - Bash(ls*)
  - Bash(mkdir*)
  - Bash(cp*)
  - Bash(ln*)
  - Bash(wc*)
  - Bash(readlink*)
argument-hint: "[project-path | 'all' | 'quick']"
---

# LaTeX Health Check: Self-Healing Build Agent

> Compile all LaTeX projects, auto-fix known errors iteratively, and verify cross-project consistency (symlinks, shared bibliographies, Overleaf separation).

## When to Use

- Periodically (weekly) to catch build rot before it becomes debugging sessions
- After major infrastructure changes (template updates, symlink reorganisation)
- Before submission season to verify all papers compile cleanly
- When the user says "check my LaTeX", "build health", "compile everything"

## Modes

| Mode | Trigger | What it does |
|------|---------|-------------|
| **Single project** | Path argument | Compile + fix + verify one project |
| **All projects** | `all` argument | Discover and compile every LaTeX project |
| **Quick** | `quick` argument | Compile only, no fixes, report errors |

## Phase 1: Discover LaTeX Projects

Find all directories containing a `\documentclass` in a .tex file:

Search locations (read from config, detect which exist):
- Research root from `~/.config/task-mgmt/research-root` (fallback: `~/Projects/`)
- `$TM/docs/`

For each discovered project, record:
- Project name (directory name)
- Main .tex file path
- Whether it has a `.latexmkrc`
- Whether it has an `out/` directory
- Whether it's inside a `paper/` subdirectory (Overleaf-linked)

## Phase 2: Build Loop (per project)

For each project:

### 2a. Pre-flight
- Check for `.latexmkrc` — create if missing (with `$out_dir = 'out'` and PDF copy-back)
- Create `out/` directory if missing

### 2b. Compile
```bash
cd <project-dir> && latexmk -interaction=nonstopmode <main.tex> 2>&1
```

**Engine selection:** Do NOT hardcode `-pdf`. The project's `.latexmkrc` (created in 2a) controls the engine — it auto-detects xelatex via `fontspec`, or defaults to pdflatex. Passing `-pdf` overrides this and breaks xelatex/lualatex projects. Let latexmk read `.latexmkrc`.

### 2c. Parse log
Extract from `out/*.log`:
- Error count (lines starting with `!`)
- Warning count (Overfull/Underfull hbox/vbox)
- Undefined citation count
- Missing package count

### 2d. Auto-fix (up to 3 iterations)

For each error, apply the known fix from the database:

| Error pattern | Fix |
|--------------|-----|
| Missing package `X` | Add `\usepackage{X}` — but NEVER try `xltabular` or `ltablex` (use `longtable` instead) |
| Undefined citation `key` | Check .bib file exists and is referenced; check for typos via edit distance |
| Overfull hbox | Flag location and width — do NOT auto-fix (requires human judgment) |
| tcolorbox `=` or `,` in title | Wrap title in braces: `title={...}` |
| Font encoding warning | Add `\usepackage[T1]{fontenc}` if missing |
| Missing `\begin{document}` | Check for corrupted preamble |
| Broken symlink in `\input{}` or `\includegraphics{}` | Find the target and report |
| Build artifacts in source dir | Flag — offer to move to `out/` |

After each fix, recompile. Max 3 iterations per project.

**Why 3 iterations (not 5)?** `/latex` runs up to 5 iterations on a single project with deep error analysis. This skill trades depth for breadth — 3 iterations is enough to catch the common fleet-wide issues (missing packages, broken symlinks, stale cache) without spending excessive time on any one project. If a project still has errors after 3 iterations, mark it as ERROR and recommend running `/latex` on it directly for deeper diagnosis.

### 2e. Record result
```json
{
  "project": "project-name",
  "path": "/full/path",
  "status": "OK | FIXED | ERROR",
  "errors_initial": 3,
  "errors_final": 0,
  "fixes_applied": ["added fontenc", "fixed tcolorbox title"],
  "warnings": 2,
  "undefined_citations": 0
}
```

## Phase 3: Cross-Project Checks

After all projects are compiled:

1. **Symlink integrity** — verify all symlinks in skills/, agents/, rules/, hooks/ resolve
2. **Shared .bib consistency** — if multiple projects reference the same .bib file (e.g., via symlink), verify they're all pointing to the same version
3. **Overleaf separation** — scan every `paper/` directory for forbidden file types (.py, .R, .csv, .ipynb, etc.)
4. **Template consistency** — check if projects using the working paper template have diverged from the current template version

## Phase 4: Report

Generate a summary report:

```
LaTeX Health Check — YYYY-MM-DD

Projects scanned:  N
Compiled OK:       N (list)
Fixed and OK:      N (list + fixes applied)
Still broken:      N (list + remaining errors)
Skipped:           N (list + reason)

Cross-project issues:
  Broken symlinks:        N
  Overleaf violations:    N
  Template drift:         N

Warnings (not auto-fixed):
  Overfull hboxes:        N across M projects
  Underfull hboxes:       N across M projects
```

Print to stdout. If `--save` flag or 10+ projects scanned, also write to `log/latex-health/YYYY-MM-DD.md`.

### 4.1 Output verification (before commit)

When writing the report file, emit an outputs manifest and run the shared verifier per [`_shared/verify-outputs.md`](../_shared/verify-outputs.md):

1. Write manifest to `<project>/.claude/state/outputs-manifest-<UTC-timestamp>.json` listing every file written this invocation, paths relative to the project root.
2. Run:

   ```bash
   python3 "$HOME/.claude/skills/_shared/verify_outputs.py" \
       --manifest "$MANIFEST" \
       --project-root "$PROJECT_ROOT"
   ```

3. If the verifier exits non-zero, **do not commit**. Surface the missing-files list and stop.

Closes the "hallucinated outputs" failure class (commit `b2cff75`, 2026-04-18). Skip this sub-step entirely if `--save` was not passed and no log file was written.

## What This Skill Does NOT Do

- Does NOT fix overfull/underfull boxes (requires human judgment on rewording)
- Does NOT modify paper content (only build configuration and missing packages)
- Does NOT push to git (compilation fixes should be reviewed first)
- Does NOT touch Overleaf-synced files without permission (per overleaf-separation rule)

## Cross-References

| Skill | Relationship |
|-------|-------------|
| `/latex` | Single-project deep fix (5 iterations). This skill runs a lighter version (3 iterations) at fleet scale. For ERROR projects, recommend running `/latex` directly. |
| `/latex` | Manual compilation config and `.latexmkrc` reference — health-check creates `.latexmkrc` files using the conventions defined there. |
| `/audit-project-research` | Checks project structure (directories, files). This skill checks build health. |
| `/bib-validate` | Validates bibliography entries. This skill checks if citations compile. |
| `/latex-template` | Checks preamble alignment with the working paper template. Complementary: run after health-check to ensure preamble consistency. |


---

## learn

**Source:** `skills/learn/SKILL.md`

---
name: learn
description: "Extract reusable knowledge from the current session into a persistent skill.\nUse when you discover something non-obvious, create a workaround, or develop\na multi-step workflow that future sessions would benefit from."
allowed_tools:
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - Bash(uv run python*)
  - AskUserQuestion
---

# Learn: Session Knowledge Extraction

Extract reusable workflows, workarounds, and multi-step procedures discovered during a session into persistent skills. Complementary to the `learn-tags` rule — while `[LEARN]` tags record one-liner corrections in MEMORY.md, `/learn` creates full skill definitions in `skills/`.

## When to Use

- You discovered a non-obvious multi-step procedure
- You built a workaround for a recurring problem
- You developed a workflow that future sessions would benefit from
- the user says "save this as a skill", "learn this", or "remember how to do this"

## Phase 1: Evaluate

Before creating anything, answer these 4 self-assessment questions:

1. **Non-obvious?** Would a future session figure this out without help, or would it waste time rediscovering it?
2. **Future benefit?** Will this come up again across sessions or projects?
3. **Repeatable?** Is this a procedure that can be followed step-by-step, or was it a one-off?
4. **Multi-step?** Does it involve 2+ non-trivial steps that benefit from being documented together?

**Decision rule:** If at least 3 of 4 answers are "yes", proceed to Phase 2. Otherwise, suggest recording as a `[LEARN]` tag in MEMORY.md instead (simpler, lower overhead).

If borderline, ask the user:
> "This seems useful but may not warrant a full skill. Should I create a skill or just add a [LEARN] tag to MEMORY.md?"

## Phase 2: Creation Guard + Read Patterns

Run the **creation-guard** analysis (see [`skills/creation-guard/SKILL.md`](../creation-guard/SKILL.md)):

1. Identify the proposal (name, type, purpose, key functions, keywords)
2. Search existing skills and agents for overlap (skill-index scan + keyword grep)
3. Analyse overlap and generate a recommendation:

| Recommendation | Criteria | Action |
|----------------|----------|--------|
| **PROCEED** | <20% overlap, genuinely new | Continue to Phase 3 |
| **EXTEND** | 50%+ overlap with one existing | Modify existing skill instead — stop here |
| **COMPOSE** | Multiple artifacts cover 80%+ | Create wrapper or document workflow — stop here |
| **ITERATE** | 20-50% overlap, needs refinement | Ask the user to clarify differentiation, then re-evaluate |
| **BLOCK** | Would create duplication | Do not create — stop here |

4. Present the creation-guard analysis to the user and get explicit approval before proceeding
5. **Read [`skills/shared/skill-design-patterns.md`](../shared/skill-design-patterns.md)** — choose the structural pattern that fits:
   - **Workflow-based** — multi-step with phases and review gates
   - **Task-based** — focused input/output with processing rules
   - **Agent-delegation** — multiple subagents, each handling one concern
   - **Reference-based** — augmenting with domain knowledge via `references/`

## Phase 3: Design the Skill

Before writing, make three decisions:

**1. Choose the structural pattern** (from Phase 2). State it explicitly:
> "This is a [workflow/task/agent-delegation/reference]-based skill."

**2. Identify resources needed:**
- Does the skill need `scripts/` for deterministic operations?
- Does it need `references/` for detailed specs, rubrics, or large examples?
- Does it need to delegate to subagents?

**3. Draft the architecture** — for non-trivial skills, sketch the flow:
```
Input → [Step A] → REVIEW GATE → [Step B] → Output
```

## Phase 4: Build the Skill

Write `skills/{name}/SKILL.md`:

### Frontmatter

```yaml
---
name: {kebab-case-name}
description: "{What it does. Concrete task types. Use when...}"
allowed_tools:
  - {minimum set of tools needed}
---
```

### Body Structure

The body varies by pattern, but always includes these elements:

```markdown
# {Skill Name}: {Short Description}

## When to Use
[Activation conditions — natural language triggers and /command]

## {Main Workflow / Processing Rules / Delegation Protocol}
[The core of the skill — structured per the chosen pattern]

## {Anti-Patterns / Never Do These}
[What NOT to do — agents default to generic without constraints]

## Output Format
[What the output looks like]

## Verification
[How to confirm it worked]
```

**Optional sections** (add when relevant):
- `## Defaults` — assumptions table to reduce friction
- `## Examples` — concrete before/after or good/bad snippets
- `## Notes` — edge cases, limitations

### Solution Pattern (for debugging/workaround skills)

When the skill captures a fix, workaround, or debugging procedure, use this body structure:

```markdown
# {Skill Name}: {Short Description}

## Problem
[Specific error message or symptom. Quote the exact text users would see.]

## Context / Triggers
[When this occurs — tool versions, file types, OS, configurations]

## Solution
[Step-by-step fix. Imperative form.]

## Verification
[How to confirm the fix worked]

## Example
[Concrete before/after or input/output]

## Notes
[Edge cases, alternative approaches, when this does NOT apply]
```

### Description Optimization

The `description:` field in frontmatter is what triggers skill discovery. Write it to match how a user would describe their problem:

- **Include specific error messages or symptoms** — "Fix `Package biblatex Error: File 'references.bib' not found`"
- **Include context markers** — file types, tools, situations where this applies
- **Include negative cases** — "Not for general proofreading (use /proofread instead)"
- **Use natural trigger phrases** — the exact words a user would type

### Extraction Checklist

During skill creation, mentally verify each point before finalising:

1. **Trigger coverage** — would a user find this skill from 3 different phrasings of the same problem?
2. **Self-contained** — can the skill be followed without reading other files (except `references/`)?
3. **Anti-patterns present** — at least 2 "don't do this" entries to prevent common mistakes?
4. **Verification step** — does the skill tell you how to confirm it worked?
5. **Scope bounded** — is it clear what this skill does NOT do?

### Writing Rules

- **Imperative form.** "Parse the input" not "You should parse the input."
- **Be specific about what NOT to do.** Anti-pattern lists are highly effective.
- **Include concrete examples.** Show expected input/output pairs.
- **Keep SKILL.md under 300 lines.** Move detail to `references/`.
- **Every instruction must be actionable.** No throat-clearing.
- **Use tables for structured data.** Faster to parse than prose.

### Naming Conventions

- **Directory and name:** `kebab-case`, descriptive, 2-4 words
- **Avoid generic names:** `fix-bug` is bad; `fix-overleaf-sync-conflict` is good
- **Match the trigger:** If the natural trigger is "compile my slides", the name should relate to slide compilation

### Allowed Tools

Follow principle of least privilege:

| Skill type | Tools |
|-----------|-------|
| Report-only | `Read`, `Glob`, `Grep` |
| File-creating | + `Write`, `Edit` |
| Shell-needing | + specific `Bash(command*)` patterns |
| Interactive | + `AskUserQuestion` |
| Delegating | + `Task` |

## Phase 5: Validate

Run the validation script on the new skill:

```bash
uv run python skills/learn/scripts/validate_skill.py skills/{name}
```

Fix all errors. Address warnings to improve quality. Use `--strict` to promote warnings to errors.

The validator checks: frontmatter validity, name format and directory match, description quality, body length, broken links, referenced directories, and placeholder text.

## Phase 6: Deploy and Confirm

1. Copy the skill to the deployed location (rsync won't run until next session start):
   ```bash
   cp -r skills/{name} ~/.claude/skills/{name}
   ```
2. Check that `~/.claude/skills/{name}/SKILL.md` exists
3. Tell the user: "Created `/{name}` — [one-line summary]. It's available immediately in all projects."
4. If the skill is substantial, suggest updating `docs/skills.md` with the new entry

## What This Skill Does NOT Do

- **Does not replace `[LEARN]` tags** — one-liner corrections still go in MEMORY.md via the `learn-tags` rule
- **Does not create agents** — agents need separate context and persistent memory
- **Does not modify existing skills** — if an existing skill needs updating, do that directly


---

## lessons-learned

**Source:** `skills/lessons-learned/SKILL.md`

---
name: lessons-learned
description: "Use when you need a structured post-mortem after incidents, mistakes, or stuck sessions."
allowed_tools:
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - AskUserQuestion
---

# Lessons Learned: Structured Retrospective

Analyse incidents using a structured framework, identify root causes, and encode preventive measures directly into skills, guards, or documentation. The goal is systematic improvement, not blame.

## When to Use

- After incidents, mistakes, rollbacks, or near-misses
- When the user says "what went wrong", "lessons learned", "post-mortem", "retrospective", or "how do we prevent this"
- After a stuck session where significant time was lost
- After a wrong-approach event (plan existed but execution diverged)

## Process

### Phase 1: Incident Definition

Capture the facts first, analysis later.

```markdown
## Incident Summary

**What happened:** [Factual description]
**When:** [Date/time]
**Impact:** [What was affected, scope]
**Resolution:** [How it was fixed/rolled back]
**Time to resolution:** [How long to fix]
```

### Phase 2: Timeline Reconstruction

Build a chronological sequence of events:

| Time | Action | Actor | Outcome |
|------|--------|-------|---------|
| HH:MM | [What was done] | [Claude/User] | [Result] |

Key questions:
- What was the trigger?
- Where did the sequence diverge from expected?
- What was the point of no return?

### Phase 3: Root Cause Analysis (5 Whys)

```
1. Why did [incident] happen?
   → Because [immediate cause]

2. Why did [immediate cause] happen?
   → Because [deeper cause]

3. Why did [deeper cause] happen?
   → Because [systemic issue]

4. Why did [systemic issue] exist?
   → Because [process gap]

5. Why did [process gap] exist?
   → Because [root cause]
```

Stop when you reach a cause that can be addressed by a concrete change to the system (skill, rule, hook, doc).

### Phase 4: Contributing Factors

Identify all factors, not just the root cause:

| Category | Factor | Contribution |
|----------|--------|--------------|
| **Process** | Missing checkpoint, unclear workflow | [How it contributed] |
| **Communication** | Ambiguous instructions, assumed consent | [How it contributed] |
| **Technical** | Missing guard, no validation | [How it contributed] |
| **Context** | Session continuation, prior assumptions | [How it contributed] |
| **Human** | Fatigue, time pressure, overconfidence | [How it contributed] |

### Phase 5: Fix Classification

Classify each fix by type:

| Fix Type | When to Use | How to Encode |
|----------|-------------|---------------|
| **Skill** | Recurring workflow needs structure | Create SKILL.md via `/learn` |
| **Guard** | Action requires mandatory checkpoint | Add approval gate to existing skill |
| **Rule** | Behavioural constraint needed globally | Create `.claude/rules/*.md` |
| **Documentation** | Knowledge gap caused the issue | Update CLAUDE.md, MEMORY.md, or docs/ |
| **Hook** | Manual step was forgotten | Create script in hooks/ |
| **Checklist** | Multiple steps need verification | Add to existing skill |

### Phase 6: Fix Implementation

**Implement fixes during the retrospective, not after.** This is the critical difference from a report-only post-mortem.

For each fix:
1. Implement it (create/edit the file)
2. Record what was done:

| Fix | Type | Location | Status |
|-----|------|----------|--------|
| [Description] | Skill/Guard/Rule/Doc/Hook | [File path] | Created/Updated |

Also record a `[LEARN]` tag in MEMORY.md for each key correction (per the `learn-tags` rule).

### Phase 7: Verification

Define how to verify the fix works:

```markdown
## Verification

**Test scenario:** [How to test the fix]
**Success criteria:** [What "fixed" looks like]
**Review date:** [When to check if fix is working — default: 2 weeks]
```

## Output

Write the report to `log/incidents/YYYY-MM-DD_short-description.md`:

```markdown
# Lessons Learned: [Incident Title]

**Date:** YYYY-MM-DD
**Severity:** [Low|Medium|High|Critical]
**Status:** [Resolved|Monitoring|Open]

## Incident Summary
[Brief description]

## Timeline
| Time | Action | Actor | Outcome |
|------|--------|-------|---------|

## Root Cause
[The fundamental issue]

## Contributing Factors
- [Factor 1]
- [Factor 2]

## Fixes Implemented
| Fix | Type | Location | Status |
|-----|------|----------|--------|

## Prevention
[How this prevents recurrence]

## Lessons
1. [Key takeaway 1]
2. [Key takeaway 2]
```

Create `log/incidents/` if it doesn't exist.

## Common Incident Patterns

| Pattern | Symptom | Root Cause | Typical Fix |
|---------|---------|------------|-------------|
| Premature action | Action taken before approval | Implied consent ≠ explicit | Add approval gate to skill |
| Sequence error | Steps in wrong order | Missing dependency chain | Encode sequence in skill |
| Missing validation | Bad data passed through | No checkpoint | Add pre-flight check |
| Context carryover | Stale assumptions from prior session | State assumed to persist | Explicit context verification |
| Scope creep | Did more than requested | Task scope too broad | Clarifying questions first |
| Planning loop | Re-planned instead of executing | Perfectionism / uncertainty | Execution stall detector |

## Anti-Patterns

| Anti-Pattern | Problem | Instead |
|--------------|---------|---------|
| Blame assignment | Creates defensiveness | Focus on process, not people |
| Single-cause thinking | Oversimplifies | Use 5 Whys, multiple factors |
| Recommend without acting | Lessons forgotten, recurs | Implement fixes during retro |
| Vague fixes ("be more careful") | Not verifiable | Encode specific changes |
| Skip verification | No way to know if fix worked | Define success criteria |

## Cross-References

- **`[LEARN]` tags** — record one-liner corrections in MEMORY.md (the quick complement to this skill)
- **`/learn`** — extract a full skill from a session (when the fix type is "Skill")
- **`/ideas`** — if a fix is too large for this session, capture as an idea for later

## Success Criteria

The retrospective is complete when:
- [ ] Incident clearly defined with timeline
- [ ] Root cause identified (not just symptoms)
- [ ] Contributing factors documented
- [ ] At least one fix implemented (not just recommended)
- [ ] Fix encoded in appropriate location (skill, rule, hook, doc)
- [ ] `[LEARN]` tags recorded in MEMORY.md
- [ ] Verification criteria defined
- [ ] Report written to `log/incidents/`


---

## literature

**Source:** `skills/literature/SKILL.md`

---
name: literature
description: "Use when you need academic literature discovery, synthesis, or bibliography management. Supports standalone searches and end-to-end project pipelines with vault sync and auto-commit."
allowed-tools: Bash(curl*), Bash(wget*), Bash(mkdir*), Bash(ls*), Bash(uv*), Bash(cd*), Bash(git*), Bash(cat*), Bash(date*), Bash(scholarly*), Bash(paperpile*), Bash(taskflow-cli*), Read, Write, Edit, Glob, Grep, WebSearch, WebFetch, Task, Agent
argument-hint: "[topic-query] or <topic-slug> for full pipeline"
---

# Literature Skill

Comprehensive academic literature workflow: discover, verify, organise, synthesise. Uses parallel sub-agents to search multiple sources, verify citations, and fetch PDFs concurrently.

> **Web alternative**: a lighter-weight version of this workflow runs at [literature.user.com](https://literature.user.com) (`packages/literature-workspace/`) — keyword/file-upload search across biblio-sources + RefPile, with Sonnet-driven synthesis. Useful for collaborators (CF Access auth) or quick discovery sessions where you don't need vault sync, DOI hard-gating, or pipeline mode. Use the CLI skill when you need verified citations entering a `.bib` file or full Phase 5 synthesis with negative-evidence + cross-cluster analysis.

## Hard Rules

### Existential — block submission

These rules protect against the highest-cost failure modes. Violation invalidates the output.

1. **Every citation must be verified to exist before inclusion.** Never include a paper you cannot find via web search. Hallucinated citations are worse than no citations.
2. **Every DOI must be programmatically verified before entering any `.bib` file.** Sub-agents hallucinate plausible-looking DOIs that resolve to wrong papers (correct journal prefix, wrong suffix). The only reliable verification is `scholarly scholarly-verify-dois` with title-matching (Phase 3). A DOI that resolves to a different title is WRONG — treat it the same as a missing DOI.
3. **The narrative synthesis ALWAYS lives at `docs/literature-review/literature_summary.md`.** Never in `paper/`, `paper-*/`, or any Overleaf-synced directory. The `paper/` directory is LaTeX-only. Markdown files there leak onto Overleaf and pollute the submission folder. Canonical filename: `literature_summary.md` (never `_synthesis.md`, `synthesis.md`, ad-hoc names).

---

### Format — catch in review

These rules govern style and consistency. Violation produces fixable artefacts, not invalid claims.

4. **Library-first.** Always check Paperpile via `paperpile search-library` BEFORE any external search (Phase 1). Papers already held should be reused, not re-discovered.
5. **Prefer the published version over preprints.** If a paper is found on arXiv, SSRN, NBER, or any working paper series, search for a published journal/conference version via `scholarly scholarly-search`. Cite a preprint only if no published version exists. Enforced in Phase 2 (discovery), Phase 3 (verify), and Phase 4 (`/bib-validate` runs the full preprint staleness check).
6. **Better BibTeX-format keys** (e.g., `Author2016-xx`). When merging into an existing `.bib`, match existing keys. Never generate custom keys (`AuthorYear`, `AuthorKamenica2017`, etc.) unless explicitly told otherwise.
7. **Match causal language to study design.** Reserve causal verbs ("causes", "increases", "reduces") for designs that warrant causal inference (experiments, RCTs, credible quasi-experiments). For observational work use "is associated with", "predicts", "correlates with". Match the language to the design — not the authors' own claims. State disagreements precisely; do not flatten into "the literature is mixed."
8. **Python: always `uv run python`.** Never bare `python`, `python3`, `pip`, `pip3`.

> Known corrections (notation, method, citation, domain) are auto-injected from `MEMORY.md` via the LEARN-tag-routing protocol at invocation. See `shared/learn-tag-routing.md`.

---

## Sprint Contract — Output Handoff



**Protocol:**

1. **Pre-commitment (Phase 1.4 hook).** Before generating the search plan, load the contract and paraphrase all 5 acceptance dimensions (D1 `bib_completeness`, D2 `dedup`, D3 `coverage_attestation`, D4 `venue_aligned`, D5 `freshness`). The paraphrase anchors output against the criteria rather than rationalising backwards. Skip in standalone mode where no downstream consumer is declared.


3. **Self-check (Phase 4.3 hook).** Before signalling pipeline completion, verify each dimension against its `verification_rule`. F1 (DOI verification fails, severity 90) or F2 (generated-key pattern with no DOI, severity 70) triggers `producer_decision=revise_before_handoff` — re-run Phase 3 verification, do not hand off.

4. **Failure-mode cross-reference** ([`docs/reference/failure-modes.md`](../../docs/reference/failure-modes.md)): contract F1 → taxonomy F1 fabricated citation (⛔ hard fail); contract F2 → taxonomy F4 invented bib key (⚠️ soft fail).

5. **Override ladder.** Round 1: re-run `paperpile search-library` + `scholarly scholarly-verify-dois`. Round 2: dispatch the `claim-verify` agent. Round 3: human review of the literature report.

Full schema + protocol: [`docs/reference/sprint-contract-protocol.md`](../../docs/reference/sprint-contract-protocol.md).

---

## Modes

| Mode | Invocation | What it does |
|------|-----------|-------------|
| **Standalone** | `/literature [topic query]` | Search + verify + bib + synthesis. No project context needed. |
| **Pipeline** | `/literature <topic-slug>` | Full cycle: resolve project → search → verify → bib → bib-validate gate → vault sync → auto-commit. |
| **Deep** | `/literature --deep [query]` | Standalone or pipeline + iterative gap-filling loop after Phase 3. Also triggered by "deep", "thorough", or "comprehensive review" in the query. |
| **Autonomous** | `/literature --autonomous <slug>` (or `-y`) | Pipeline + run end-to-end without inter-phase pauses. Stackable with `--deep`. Hard gates still run; defaults used at every choice point. See "Autonomy" below. |

**Mode detection:** if the argument matches an atlas topic slug (`~/Research-Vault/atlas/<slug>.md`), run in Pipeline mode. Otherwise, Standalone. When in doubt, ask. Deep is a flag on either base mode. Autonomous is a flag on either base mode.

**Pipeline mode — project context resolution:** find the atlas topic file (`find ~/Research-Vault/atlas/ -name "<topic-slug>.md"`), read frontmatter (`title`, `project_path`, `outputs`, `connected_topics`), resolve `PROJECT="$(cat ~/.config/task-mgmt/research-root)/<project_path>"`, locate the `.bib` file (ask if multiple). Report context and wait for confirmation before Phase 1 — **unless `--autonomous` is set**, in which case ambiguity is resolved by picking the largest `.bib` file in the project (typically `paper-*/paper/references.bib` or `docs/literature-review/literature_summary.bib`) and logging the choice.

## Autonomy

Per the global `--autonomous` / `-y` convention defined in `~/.claude/rules/phased-work.md` § "Autonomy flag convention". When set:

- **No Phase 1.4 search-plan confirmation** — emit the plan to the session log and proceed
- **No Phase 2.2 dedup/rank pause** — apply default filters and continue
- **No Phase 3.5 deep-loop "continue?" prompts** — run up to 3 iterations (default), stop when <3 new papers per iteration
- **No Phase 4.3 bib-validate "review and continue" pause** — `/bib-validate` still runs as a hard gate; warnings are logged and reported at the end; only `F1 fabricated citation` or `F2 invented bib key` block the run
- **No `AskUserQuestion` mid-run** — every choice point uses the recommended/default option and logs the decision
- **Auto-commit at end** in pipeline mode (subject to Phase 4.6 verifier)
- **Single end-of-run report** is the only mandatory user-facing output

Hard correctness gates that still fire even with `--autonomous`:
- DOI verification (Phase 3) with title-match — fabricated DOIs are F1/blocker
- Sprint-contract D1–D5 self-check (Phase 4.3 hook)
- Phase 4.6 outputs-manifest verifier (manifests must verify or commit is blocked)
- The forbid-list for sub-agents (still applied)

Recommended invocations:

```
/literature --autonomous effort-weighted-yield                # pipeline, end-to-end, standard depth
/literature --deep --autonomous effort-weighted-yield         # exhaustive, end-to-end
/literature -y effort-weighted-yield                          # short form
```

---

## Optional Enrichment

Five enrichment passes that fire conditionally. They do not get their own phase headers — each integrates into a base phase as noted.

| Enrichment | Trigger | Integrates after | Reference |
|-----------|---------|-----------------|-----------|
| **Perplexity grounding** | `OPENROUTER_API_KEY` set; advisory real-time grounding wanted | Phase 1.2 (pre-search) | [`references/perplexity-grounding.md`](references/perplexity-grounding.md) |
| **CLI council search** | Broad reviews (20+ papers) or interdisciplinary topics | Phase 2.1 (parallel search) | [`references/council-cli-search.md`](references/council-cli-search.md) |
| **Snowball search** | Phase 2 returned <15 papers OR broad review | Phase 2.1 (parallel search) | [`references/snowball-search.md`](references/snowball-search.md) |
| **SciSciNet enrichment** | `curl -sf http://localhost:8500/health` succeeds | Phase 2.3 (rank), before Phase 3 | [`references/scisciinet-enrichment.md`](references/scisciinet-enrichment.md) |
| **Iterative deep loop** | Deep mode (`--deep` or keyword); ≥5 verified papers | Phase 3 (verify), before Phase 4 | [`references/deep-loop-protocol.md`](references/deep-loop-protocol.md) |

Output from any enrichment must still pass the Phase 3 DOI gate before entering the `.bib`.

---

## Architecture

Sub-agents handle independent, parallelisable work (search, verification, PDF download). Merging, deduplication, and synthesis stay with the orchestrator because they need the full picture. Full agent prompt templates: [`references/agent-templates.md`](references/agent-templates.md).

---

## Phase 1: Prep

> standalone: yes (skip 1.3, 1.4) | pipeline: yes | deep: yes

### 1.1 Session log + checkpoint

Literature searches are context-heavy. Always run `/session-log` to create a recovery checkpoint per [`shared/checkpoint-resumability.md`](../shared/checkpoint-resumability.md). Pipeline mode writes a JSON checkpoint after each phase so a crash resumes from the last completed phase, not from scratch.

### 1.2 Pre-search check

Find existing `.bib` files in project root, `/references`, `/bib`, `/bibliography`. Then:

1. Parse existing entries to avoid duplicates and understand context.
2. Identify gaps — note if the bibliography skews toward certain years/methods.
3. Compile the list of existing citation keys to pass to sub-agents.
4. **Mandatory: check Paperpile.** Call `paperpile search-library` for the topic. Also call `paperpile get-items-by-label` if a relevant label exists. Mark hits as **ALREADY IN PAPERPILE** and reuse their citation keys. If `paperpile` CLI is unavailable, log a warning and continue.
5. **Resolve topic label** via `paperpile get-labels` for the current topic. Used in Phase 4 sync reporting.
6. **Check source availability** via `scholarly source-status --json` (OpenAlex always; Scopus/WoS if API keys are set). Report so search agents know coverage.
7. **Check scout-batch reports.** Glob `~/Research-Vault/reports/scout/portfolio/*<topic-slug>*.md` and `*<topic-keyword>*.md`. If a recent (≤90 days) report exists, parse the **Closest prior works** and **Most likely scoopers** sections — feed authors/papers/groups directly to Phase 2 search agents as seeds. This avoids re-discovering what scout already surfaced.
8. **Cold-start branch.** If steps 4–7 yield <3 papers AND project status is `Idea` or `Drafting` (read from atlas topic frontmatter or skip if standalone), enter **scaffold-seeded mode**:
   - Search the project for a canonical scaffold document (`to-sort/*scaffold*.md`, `to-sort/*sketch*.md`, or `docs/*scaffold*.md`). Read it for the canonical reference list.
   - For canonical CS/ML references explicitly named in the scaffold (e.g. "Ghorbani-Zou Data Shapley ICML 2019"), use `scholarly arxiv-get-paper --arxiv-id <id>` directly when arXiv IDs are known — broad `scholarly-search` returns high-citation noise (climate, hydrogen) on generic ML queries like "data shapley".
   - For DOI-only known references, use Crossref via `scholarly scholarly-verify-dois` (faster + more reliable than search for targeted lookups; see [`reference_mcp_scholarly_search.md`](../../memory/reference_mcp_scholarly_search.md)).
   - **Flag synthesis output** in `literature_summary.md` with a header banner: `> **Phase-1 seed synthesis** — scaffold-derived references only; broader external discovery deferred to next iteration.` This signals to downstream consumers that the bib is intentionally narrow.
   - Skip Phase 2's full parallel search; jump straight to Phase 3 verification on the scaffold-named references.

Steps 4–7 are not optional — every literature search must check the library AND scout reports before external discovery. Step 8 fires conditionally and bypasses Phase 2 noise for cold-start projects.

For parsing `scholarly` CLI JSON output (mixes stderr log lines with stdout JSON), use the helper in [`references/scholarly-output-parsing.md`](references/scholarly-output-parsing.md).

### 1.3 Concept validation gate (pipeline mode only)

Run [`shared/concept-validation-gate.md`](../shared/concept-validation-gate.md) on the topic concept plan. If the plan fails (missing RQ, no theoretical framing, generic AI voice, <300 words, <3 references), pause and request a stronger concept plan before proceeding. Standalone mode skips this — free-form queries don't have a concept plan to validate.

### 1.4 Search plan + method-fitness gate (pipeline mode only)


Present the search plan and wait for confirmation: restate the RQ, list 3-6 queries grouped by **Track A (Substantive) / Track B (Empirical comparanda) / Track C (Methodological precedents)**, list seed authors/venues, propose `year_min` / `year_max` filters (propagated to every search call via `--year-from/--year-to`), flag book coverage if topic has major book-length treatments. Full structure: [`references/search-plan.md`](references/search-plan.md).

After plan approval, run [`shared/method-fitness-gate.md`](../shared/method-fitness-gate.md). If the method does not fit the RQ, escalate per [`shared/escalation-protocol.md`](../shared/escalation-protocol.md) — do not proceed to expensive search until the gate passes. Standalone mode skips both: free-form queries imply exploratory intent.

---

## Phase 2: Search

> standalone: yes | pipeline: yes | deep: yes (later expanded by 4.5 loop)

### 2.1 Parallel search

CLI pre-fetch via `scholarly` commands (search, similar-works, author-papers, arxiv-search, exa-search-papers) writing to `/tmp/lit-search/*.json`, then spawn 2-3 Explore agents in parallel (Google Scholar, bibliometric, S2/arXiv, domain-specific). Both `scholarly` and `paperpile` CLIs work inside sub-agents — pre-fetch or let agents shell out. Full CLI list, output paths, configuration: [`references/phase-2-search.md`](references/phase-2-search.md). Agent prompts: [`references/agent-templates.md#phase-2-search-agent-templates`](references/agent-templates.md#phase-2-search-agent-templates).

If CLI council enrichment fires here, run it as an additional parallel agent. If snowball enrichment fires, run it after primary search, before 2.2.

### 2.2 Deduplicate, classify, rank

1. Merge results from all search agents.
2. Remove duplicates — match on title similarity and DOI.
3. **Field-framework extraction** for each candidate: Setting / Population / Method / Data / DV / IV / Key finding / Mechanism / Boundary. Always run, even if partial — feeds ranking, gap analysis, synthesis, and `/hypothesis-generation`. Definitions: [`references/field-framework.md`](references/field-framework.md).
4. Rank by relevance, citation count, recency.
5. Select top N to verify (typically 25-30 candidates for 20-25 verified).
6. Assign batches of ~5 for verification.

If SciSciNet enrichment fires, run it on the ranked pool: adds `disruption_score`, `novelty_score`, `is_hit_1pct` flags; re-rank to boost hits and high-disruption papers.

---

## Phase 3: Verify

> standalone: yes | pipeline: yes | deep: yes + iterative loop (4.5)

This phase IS the integrity gate per [`shared/integrity-gates.md`](../shared/integrity-gates.md). No reference may enter the `.bib` without passing here.

Six-step protocol:

1. **Batch DOI pre-verification** via `scholarly scholarly-verify-dois --json` — title-match check is mandatory (off-by-one DOI suffix hallucinations are the dominant failure mode). One CLI call accepts up to 50 DOIs; if you have more, see Dispatch Rule below before splitting.
2. **Find correct DOIs** for flagged papers via Crossref API → `scholarly-search` → web search (in order of reliability).
3. **Manual verification** of remaining papers — spawn general-purpose agents in parallel, ~5 papers each. Template: [`references/agent-templates.md#phase-4-verification-agent-template`](references/agent-templates.md#phase-4-verification-agent-template).
4. **Final DOI gate** — re-run `scholarly-verify-dois` on all DOIs entering the `.bib`. Papers without DOIs get `% NO DOI`. Subject to the same Dispatch Rule.
5. **Confidence grades** — A (DOI + full metadata), B (stable identifier, no DOI), C (single non-canonical source).
6. **Working paper inclusion test** — include only if ≥2 of: high citations, established author, top venue, sole source for concept, verifiable forthcoming status.

Full protocol: [`references/phase-4-verification.md`](references/phase-4-verification.md).

#### Dispatch Rule (Steps 1 & 4)

Per [`_shared/cli-dispatch-policy.md`](../_shared/cli-dispatch-policy.md): if Step 1 or Step 4 would require **2 or more** `scholarly-verify-dois` calls (i.e. >50 DOIs total), dispatch a single Bash sub-agent that runs all batched calls and writes merged JSON to `/tmp/lit-verify.json`. Main context reads only the merged result, never the raw CLI output. For the bulk-threshold rationale, see `~/.claude/rules/subagent-prompt-discipline.md` § Bulk-Operation Dispatch Rule.

### 3.5 Iterative deep loop (deep mode only)

Prerequisites: ≥5 verified papers. Each iteration: (1) gap analysis with era-gated checks for terminology/paradigm shifts, (2) targeted search via `scholarly` + Explore sub-agents, (3) merge + dedup, (4) verify new papers via the six-step protocol above. Convergence: 3 iterations OR <3 genuinely new papers per iteration OR user says "enough". Full protocol: [`references/deep-loop-protocol.md`](references/deep-loop-protocol.md). Agent prompts: [`references/agent-templates.md#phase-45-deep-loop-agent-templates`](references/agent-templates.md#phase-45-deep-loop-agent-templates).

---

## Phase 4: Finalise

> standalone: 4.1–4.4, 4.6 | pipeline: all | deep: same as base mode

### 4.1 PDF download

Check Paperpile via `paperpile search-library` — papers with attached PDFs are SKIP, others DOWNLOAD. Spawn Bash agents in parallel (3-5 papers each) for the DOWNLOAD set. Best-effort — many papers are paywalled. Template: [`references/agent-templates.md#phase-5-pdf-download-agent-template`](references/agent-templates.md#phase-5-pdf-download-agent-template).

### 4.2 Assemble bibliography

Two outputs required:

1. `docs/literature-review/literature_summary.bib` — always created, standalone, self-contained.
2. Project canonical bib (e.g. `paper/references.bib`) — merge into it if it exists.

Rules: Better BibTeX-format keys; reuse Paperpile keys for entries already held; only VERIFIED papers; list ALL authors (never "et al."); seed each entry via `scholarly scholarly-paper-detail`; add `% Confidence: A/B/C` and `% WP criteria:` comments where applicable; every entry needs a connection note in `literature_summary.md`. Full format: [`references/bibliography-format.md`](references/bibliography-format.md).

Each output gets a [`shared/material-passport.md`](../shared/material-passport.md) header (origin skill, mode, version, produced timestamp) so downstream consumers can detect staleness.


### 4.3 Validate bibliography (HARD GATE)

**Do not proceed to 4.4 or Phase 5 until `/bib-validate` has been invoked and the report reviewed.** Phase 3 verifies papers exist; `/bib-validate` catches a different class (missing BibTeX fields, preprint staleness, DOI problems, author formatting, unused entries). Running synthesis before validation means the narrative may reference entries with broken metadata that survive into the paper.

Mandatory on every `/literature` invocation (standalone, pipeline, deep) every time new entries are added.

**Sprint Contract self-check hook (pipeline mode).** After `/bib-validate` passes, run each contract dimension's `verification_rule` (D1–D5). Any F1 (DOI verification fails) or F2 (generated-key pattern with no DOI) triggers `producer_decision=revise_before_handoff` — go back to Phase 3, do NOT proceed to 4.4. Escalate via the 3-round override ladder if revision still fails.

### 4.4 Sync to reference managers

Sync new references to Paperpile (primary reference manager); handle migration candidates and post-run maintenance. Append a sync breadcrumb to `.planning/state.md` or `.context/current-focus.md`. Full steps + breadcrumb format: [`references/reference-manager-sync.md`](references/reference-manager-sync.md).

### 4.5 Pipeline completion (pipeline mode only)

After 4.3 passes (bib-validate clean) and 4.4 completes: (1) vault sync via `taskflow-cli`, (2) knowledge wiki filing if `knowledge/` exists. Standalone mode skips this entirely. Full steps: [`references/pipeline-completion.md`](references/pipeline-completion.md).

### 4.6 Output verification (before commit)

Before any auto-commit, emit an outputs manifest and run the shared verifier per [`_shared/verify-outputs.md`](../_shared/verify-outputs.md):

1. Write manifest to `<project>/.claude/state/outputs-manifest-<UTC-timestamp>.json` listing every file this skill claims to have written, paths relative to the project root.
2. Run:

   ```bash
   python3 "$HOME/.claude/skills/_shared/verify_outputs.py" \
       --manifest "$MANIFEST" \
       --project-root "$PROJECT_ROOT"
   ```

3. If the verifier exits non-zero, **do not commit**. Surface the missing-files list and stop. The verifier logs an `error` entry to `~/.claude/ecc/skill-outcomes.jsonl`.

Closes the "hallucinated outputs" failure class (commit `b2cff75`, 2026-04-18).

### 4.7 Auto-commit (pipeline mode only)

Hard gate: commit only if 4.3 (bib-validate clean) and 4.6 (outputs manifest verified) both passed. Standalone mode skips. Commit template: [`references/pipeline-completion.md`](references/pipeline-completion.md).

---

## Phase 5: Synthesise

> standalone: yes | pipeline: yes | deep: yes (informed by deep-loop findings)

Output: `docs/literature-review/literature_summary.md`. Never write synthesis to `paper/` (Hard Rule 3). If `docs/literature-review/` does not exist, `mkdir -p` first.

Seven steps: (1) identify themes, (2) map intellectual lineage, (3) note current debates, (4) structured gap analysis (methodological / population-context / conceptual, each with "why it matters"), (5) negative evidence per cluster (mandatory — state explicitly if absent), (6) cross-cluster synthesis (tensions + implications), (7) Priority Reading Order (5–7 papers: review → foundational → frontier → gap/controversy).

Output types: narrative summary, literature deck, annotated bibliography, concise field synthesis (~400 words for "quick synthesis" requests). Use `[VERIFY]` tags for uncertain attributions (resolve before publication). For comprehensive reviews, run through `council-cli` for multi-model synthesis. Full protocol: [`references/synthesis.md`](references/synthesis.md).

---

## Sub-Agent Guidelines

1. **Launch independent agents in a single message** for parallelism.
2. **Be explicit in prompts** — sub-agents have no context. Include skip lists of existing citation keys.
3. **Maximum 3 parallel agents at a time.** Spawn in waves, write results to disk between waves. Each agent writes to a temp file (e.g., `/tmp/lit-search/agent-N.json`) rather than returning large payloads in-context. Summarise from files to avoid context overflow.
4. **Right agent type:** `Explore` for search, `general-purpose` for verification, `Bash` for downloads.
5. **Batch sizes:** 5 papers per verification agent, 3-5 per PDF agent.
6. **Tolerate partial failures** — continue with what you have.

---

## Cross-References

See [`references/related-skills.md`](references/related-skills.md) for cross-references, bibliometric API guides, and arXiv full-text reading instructions.


---

## memory-cleanup

**Source:** `skills/memory-cleanup/SKILL.md`

---
name: memory-cleanup
description: "Use when you need to prune duplicates and merge overlapping entries in MEMORY.md files."
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, AskUserQuestion
argument-hint: "[project-path or 'all' for global consolidation]"
---

# Consolidate Memory

Periodic refinement of `MEMORY.md` files across projects. Prunes redundant entries, merges overlapping knowledge, generates higher-order abstractions from accumulated patterns, and removes stale or superseded entries.

Inspired by npcsh's knowledge graph sleep/dream cycles — memory consolidation applied to research project knowledge.

## When to Use

- Monthly maintenance (pair with `/system-audit`)
- When a `MEMORY.md` exceeds 100 entries
- After completing a major project milestone (e.g., paper submission)
- When starting a new session and `MEMORY.md` feels cluttered
- When the same correction keeps appearing across multiple projects

## When NOT to Use

- During active work sessions — consolidation is a maintenance task
- When `MEMORY.md` has fewer than 10 entries — not enough to consolidate
- Immediately after recording `[LEARN]` tags — let knowledge accumulate first

## Modes

Ask the user which mode to run:

| Mode | Scope | What it does |
|------|-------|-------------|
| **Project** (default) | Single project's `MEMORY.md` + `.claude/state/personal-memory.md` | Consolidate both tiers |
| **Global** | All `MEMORY.md` + personal-memory files across projects + Task Management | Consolidate all, cross-pollinate shared patterns |

## Workflow

### Phase 1: Sleep (Consolidation)

Read the target `MEMORY.md` file(s) and `.claude/state/personal-memory.md` (if it exists) and perform:

#### 1.1 Duplicate Detection

Find entries that say the same thing in different words.

**Signals:**
- Same correction direction (wrong → right) with different phrasing
- Same file/variable referenced in multiple entries
- Entries from different dates that record the same learning

**Action:** Merge into a single entry, keeping the most precise wording. Note the merge in a comment: `<!-- merged from 2 entries -->`.

#### 1.2 Contradiction Resolution

Find entries that contradict each other (e.g., "use X" in one entry, "don't use X" in another).

**Signals:**
- Opposite correction directions for the same variable/convention
- Entries where a later one supersedes an earlier one

**Action:** Keep the most recent/correct entry. Flag contradictions for user review if the resolution isn't obvious.

#### 1.3 Staleness Detection

Find entries that are no longer relevant.

**Signals:**
- References to files, variables, or conventions that no longer exist in the project
- Entries about bugs that have been fixed
- Entries about tools or APIs that have changed
- Entries marked with dates older than 6 months with no recent reinforcement

**Action:** Mark as `[STALE?]` and present to user for confirmation before removing. Never auto-delete.

#### 1.4 Tier Routing Check

Check whether entries are in the correct tier (see `learn-tags` rule for the two-tier system).

**Promotion candidates** (personal-memory → MEMORY.md):
- Entries in `.claude/state/personal-memory.md` that would help a collaborator on a different machine
- Local workarounds that turned out to be general conventions
- Tool quirks that apply to all machines (not just this one)

**Demotion candidates** (MEMORY.md → personal-memory):
- Entries in `MEMORY.md` that reference local paths, machine-specific tool versions, or environment quirks
- Workarounds that only apply to this specific setup

**Action:** Present promotion/demotion suggestions to the user. Move entries only after explicit approval.

#### 1.5 Strengthening

Entries that have been independently confirmed multiple times are high-confidence knowledge.

**Signals:**
- Same pattern recorded from different sessions
- Corrections reinforced by compilation errors or test failures
- Conventions confirmed by supervisor feedback

**Action:** Move to the top of their section. Add `[CONFIRMED]` marker if supported by 3+ independent occurrences.

### Phase 2: Dream (Abstraction)

Generate higher-order patterns from the accumulated entries.

#### 2.1 Cross-Entry Patterns

Look for patterns that span multiple entries:

- "Every time we work with X, we hit Y" → Record as a general rule
- "We always use convention A for project type B" → Record as a convention
- "Corrections in category C cluster around the same mistake" → Record the root cause

#### 2.2 Cross-Project Patterns (Global mode only)

When consolidating across all projects, look for knowledge that applies everywhere:

- Notation conventions used consistently across 3+ projects → Promote to global MEMORY.md
- The same code pitfall appearing in multiple projects → Record once with cross-references
- Citation corrections that apply to shared bibliography entries → Consolidate

#### 2.3 Abstraction Generation

For each pattern found, generate an abstraction:

```markdown
## Abstraction: [Name]

**Pattern:** [What keeps happening]
**Root cause:** [Why it happens]
**Prevention:** [How to avoid it in future]
**Evidence:** [Which entries support this]
```

Present abstractions to the user. Only write the ones they approve.

### Phase 3: Write

#### 3.1 Restructure

Rewrite `MEMORY.md` with:
1. **Abstractions** at the top (new section: `## Patterns`)
2. **Confirmed entries** next (high-confidence knowledge)
3. **Regular entries** in their standard sections (Notation Registry, Citations, Key Decisions, Anti-Patterns, Code Pitfalls)
4. **Stale entries removed** (only those confirmed by user)

If `.claude/state/personal-memory.md` exists, also rewrite it with consolidated machine-specific entries. Apply any user-approved promotions (move to MEMORY.md) and demotions (move from MEMORY.md to personal-memory).

#### 3.2 Diff Report

Before writing, show a summary:

```markdown
## Consolidation Summary

| Action | Count |
|--------|-------|
| Duplicates merged | X |
| Contradictions resolved | X |
| Stale entries flagged | X |
| Stale entries removed | X (user-confirmed) |
| Entries strengthened | X |
| Abstractions generated | X |
| Tier promotions (personal → generic) | X |
| Tier demotions (generic → personal) | X |
| Cross-project promotions | X (global mode) |

### Entries Before: XX
### Entries After: YY
### Net reduction: ZZ
```

#### 3.3 Confirmation

**Always show the full proposed MEMORY.md before writing.** Wait for explicit approval. The user may want to keep entries flagged as stale, adjust abstractions, or revert merges.

### Phase 4: Propagate to Shared Auto-Memory

**Why:** `scripts/sync-push-memory.sh` append-merges `MEMORY.md` and has no deletion logic. Without this phase, the next `/full-commit` would pull deleted entries and stale files back into local from the shared copy.

**When to run:** Whenever this skill deletes files or shortens `MEMORY.md` (not needed for pure additions). If only adding entries, the normal append-merge sync handles it.

**What to do:**

1. Identify the shared copy location(s) that correspond to the local scope:
   - Task Management auto-memory (`~/.claude/projects/-Users-user-*Task-Management/memory/`) → `$TM/.context/auto-memory/task-management/`
   - Global auto-memory (`~/.claude/projects/*/memory/` for non-TM projects) → `$TM/.context/auto-memory/global/`

2. Mirror local → shared for each location:
   - **MEMORY.md and MEMORY-ARCHIVE.md:** force-copy from local to shared (overwrites, bypasses append-merge)
   - **Individual entry files:** copy any local file that's newer; delete any shared file that no longer exists locally

3. Commit the shared-copy changes to the Task Management repo with a message explaining it's a cleanup propagation (so the log is clear about why entries vanished).

**Example (Task Management scope):**

```bash
local_dir=~/.claude/projects/-Users-user-Task-Management/memory
shared_dir="$TM/.context/auto-memory/task-management"

# Mirror MEMORY.md and MEMORY-ARCHIVE.md (force overwrite, not append-merge)
cp "$local_dir/MEMORY.md" "$shared_dir/MEMORY.md"
[ -f "$local_dir/MEMORY-ARCHIVE.md" ] && cp "$local_dir/MEMORY-ARCHIVE.md" "$shared_dir/MEMORY-ARCHIVE.md"

# Delete any shared entry files that no longer exist locally
for f in "$shared_dir"/*.md; do
  name=$(basename "$f")
  [ "$name" = "MEMORY.md" ] || [ "$name" = "MEMORY-ARCHIVE.md" ] && continue
  [ ! -f "$local_dir/$name" ] && rm "$f"
done

# Copy any locally-newer entry files
for f in "$local_dir"/*.md; do
  name=$(basename "$f")
  [ "$name" = "MEMORY.md" ] || [ "$name" = "MEMORY-ARCHIVE.md" ] && continue
  if [ ! -f "$shared_dir/$name" ] || [ "$f" -nt "$shared_dir/$name" ]; then
    cp "$f" "$shared_dir/$name"
  fi
done

# Commit
cd "$TM" && git add .context/auto-memory/task-management/ && git commit -m "memory: propagate cleanup to shared auto-memory"
```

**Skip Phase 4 if:** the consolidation only added entries (no deletions, no line removals from MEMORY.md). Append-merge handles additions correctly on its own.

## MEMORY.md Sections (Reference)

Standard sections from the `learn-tags` rule:

| Section | Columns |
|---------|---------|
| **Patterns** | Pattern / Root cause / Prevention / Evidence (NEW — added by this skill) |
| **Notation Registry** | Variable / Convention / Anti-pattern |
| **Estimand Registry** | What we estimate / Identification / Key assumptions |
| **Citations** | One-liner corrections |
| **Key Decisions** | Decision / Rationale / Date |
| **Anti-Patterns** | What went wrong / Correction |
| **Code Pitfalls** | Bug / Impact / Fix |

## Global MEMORY.md Location

The Task Management MEMORY.md at the project root:
```
$TM/MEMORY.md
```

Also check the auto-memory directory (path varies by machine — glob for it):
```
~/.claude/projects/-Users-user-*Task-Management/memory/MEMORY.md
```

## Cross-References

- **`/system-audit`** — Run consolidation as part of periodic maintenance
- **`/skill-extract`** — Creates the entries that this skill consolidates
- **`[LEARN]` tags** (rule) — The tagging system that feeds MEMORY.md
- **`/session-close`** — May surface entries worth recording before consolidation


---

## multi-perspective

**Source:** `skills/multi-perspective/SKILL.md`

---
name: multi-perspective
description: "Use when you need to explore a research question from multiple independent perspectives."
allowed-tools: Read, Write, Edit, Glob, Grep, Task, AskUserQuestion
argument-hint: "[research question, hypothesis, or design choice]"
---

# Multi-Perspective Exploration

Spawn 3-5 parallel agents, each with a distinct disciplinary lens and epistemic prior, to independently investigate a research question. Then synthesise their findings into a structured comparison that surfaces agreements, tensions, and blind spots.

The core insight: a single-perspective analysis inherits the biases of that perspective. Deliberately introducing cognitive diversity — grounded in real disciplinary traditions — produces more robust research designs.

## Output Path

Per `rules/review-artefact-routing.md` (auto-loads in research projects (path-scoped to `paper-*/` and `paper/`)):

- **Source slug:** `multi-perspective`
- **Write reports to:** `reviews/multi-perspective/YYYY-MM-DD.md` inside the project. Path is relative to the research project root, not the Task-Management repo.
- **Never** at project root (`./CRITIC-REPORT.md`-style filenames are forbidden — pre-rule layout).
- **Idempotency:** if today's file exists, append a same-day descriptor (`{date}-revision.md`, `{date}-r2.md`, `{date}-pre-submission.md`) — never overwrite.
- **Index update:** if `reviews/INDEX.md` exists, write a one-line entry under "Latest per source" pointing at the new file. Otherwise `/review-recap` will rebuild the index next time it runs.
- **Infrastructure repos** (Task-Management, atlas-workspace, etc.): this section does not apply — the path-scoped rule won't load there.


## When to Use

- Early-stage research design: "Is this the right question? Is this the right method?"
- When choosing between competing identification strategies
- When a paper needs to convince reviewers from different traditions
- Before committing to a theoretical framework
- When you suspect your approach has blind spots

## When NOT to Use

- **Quick feedback** — use `/devils-advocate` (single-perspective adversarial)
- **Literature search** — use `/literature` (discovery, not deliberation)
- **Generating new questions** — use `/scout generate` (this skill evaluates, not generates)
- **Paper proofreading** — use `/proofread` or `paper-critic` agent

## Workflow

### Phase 1: Frame the Question

Read `$ARGUMENTS` and any referenced files. Formulate a clear, debatable research question or design choice. Good inputs:

- "Should I use DiD or synthetic control for this policy evaluation?"
- "Is bounded rationality or information asymmetry the better theoretical lens for this phenomenon?"
- "What are the threats to my identification strategy for [paper X]?"
- "How would different disciplines approach [phenomenon Y]?"

If the input is vague, ask one clarifying question before proceeding.

### Phase 2: Generate Perspectives

Generate 3-5 distinct perspectives. Each perspective is defined by:

| Field | Description |
|-------|-------------|
| **Label** | Short name (e.g., "Behavioural Economist", "Organisational Theorist") |
| **Discipline** | Academic field and tradition |
| **Epistemic prior** | What this perspective takes as given, and what it questions |
| **Methodological preference** | Preferred empirical approach and evidence standards |
| **Likely concern** | What this perspective would worry about most |

For rules and templates, see [`references/perspective-templates.md`](references/perspective-templates.md).

Present the generated perspectives to the user and get approval before proceeding. The user may want to add, remove, or adjust perspectives.

### Phase 3: Investigate

Three sub-steps — parallel investigation, then user check-in, then anonymised cross-evaluation. The check-in is what differentiates this skill from a passive multi-perspective analysis.

#### 3.1 Parallel investigation

Spawn one sub-agent per perspective using the Task tool. Each agent receives:

```
You are a [LABEL] investigating this research question:

[QUESTION]

Your disciplinary background: [DISCIPLINE]
Your epistemic prior: [EPISTEMIC PRIOR]
Your methodological preference: [METHODOLOGICAL PREFERENCE]
Your primary concern: [LIKELY CONCERN]

Context about the project:
[Relevant project context — CLAUDE.md summary, paper abstract if available]

TASK: Analyse this question from your perspective. Address:
1. How would you frame this question in your discipline?
2. What theoretical framework would you apply?
3. What empirical strategy would you recommend, and why?
4. What are the main threats to validity from your perspective?
5. What would you find most/least convincing in the current approach?
6. What is the one thing the researcher is probably overlooking?

Be specific and grounded. Cite real methodological traditions and papers where relevant.
Write 300-500 words. Do not hedge — commit to your perspective's position.
```

**Agent configuration:**
- Use `subagent_type: general-purpose` for each
- Run all agents in parallel (up to 5 concurrent, per orchestration convention)
- Each agent writes to a temp file; collect results after all complete

#### 3.2 User check-in (interactive mode)

After collecting all perspective outputs, present them to the user as a structured summary and run an interactive check-in. This is the key differentiator from a passive multi-perspective analysis — the user participates as an active contributor, not a spectator.

**What to present:**
- Each perspective's key position (2-3 sentences, not the full output)
- The main disagreements visible so far
- Any assumptions the perspectives made about the research context

**Then ask (via AskUserQuestion):**

> "Here's where the perspectives stand so far. Before they peer-review each other, I want to check in:
>
> 1. **Reveal constraints:** Is there anything these perspectives don't know that would change their analysis? (e.g., data limitations, institutional constraints, supervisor preferences, timeline)
> 2. **Redirect:** Is any perspective completely off-base or exploring an irrelevant direction?
> 3. **Challenge:** Do you want to push back on any specific claim before cross-evaluation?"

**How the user's input feeds forward:**
- Constraints revealed here are injected into the cross-evaluation prompt as "Additional context from the researcher" — each evaluator sees them
- If a perspective is marked as off-base, it is still included in cross-evaluation (for completeness) but flagged: "The researcher considers this direction less relevant because [reason]"
- Challenges are posed directly to the relevant perspective in the cross-evaluation round as an additional evaluation criterion

**When to skip:** If the user says "skip check-in", "just run it", or "non-interactive", proceed directly to 3.3. The default is interactive.

#### 3.3 Anonymised cross-evaluation

Before synthesising, run a peer-review round where each perspective critiques all others — without knowing which lens produced which output. This forces content-based evaluation rather than tribal dismissal.

**Setup:** Anonymise each perspective's output by replacing the label with a neutral identifier (Perspective A, B, C, ...). Strip any self-identifying language (e.g., "as an econometrician, I...").

**Spawn one evaluator agent per perspective** using the Task tool. Each receives:

```
You are a [LABEL] ([DISCIPLINE]).

Below are [N] anonymous analyses of this research question:

[QUESTION]

---
[Perspective A output — anonymised]
---
[Perspective B output — anonymised]
---
[Perspective C output — anonymised]
---

TASK: Evaluate each perspective on these criteria (1-5 scale):
1. **Rigour** — Is the reasoning sound? Are claims supported?
2. **Relevance** — Does it address the core question?
3. **Novelty** — Does it surface something the others miss?
4. **Practicality** — Could the researcher act on this advice?

[IF USER PROVIDED INPUT IN PHASE 3.2, ADD:]
Additional context from the researcher:
- Constraints: [user-revealed constraints]
- Challenges: [user's pushback on specific claims]
- Relevance notes: [any perspectives the user flagged as less relevant, with reason]

Factor this researcher context into your evaluation — perspectives that ignore known constraints should score lower on Practicality.

For each perspective, provide:
- Scores (4 numbers)
- One strength (1 sentence)
- One weakness (1 sentence)
- Would you change your own analysis based on this? (yes/no + why)

Then rank all perspectives from most to least valuable for the researcher.
Be honest — evaluate the content, not the style. 200-300 words total.
```

**Agent configuration:**
- Use `subagent_type: general-purpose` for each
- Run all evaluator agents in parallel
- Each agent must NOT see which label produced which output

**What this produces:**
- A cross-evaluation matrix (each perspective rated by every other)
- Self-revision signals (perspectives that update their view after seeing others)
- Consensus rankings (which perspectives were rated highest across evaluators)

Include the cross-evaluation matrix in the final report (Section "Peer Evaluation") so the user can see where perspectives found each other compelling or weak.

### Phase 4: Synthesise

Read all agent outputs **and their peer evaluations** and produce a structured synthesis. Weight the synthesis by peer evaluation scores — perspectives rated highly across evaluators get more influence than those rated poorly:

#### 4.1 Agreement Map

What do all (or most) perspectives agree on? These are robust findings — if sceptics from different traditions converge, the point is likely sound.

#### 4.2 Tension Map

Where do perspectives disagree? For each tension:
- What is the disagreement about? (framing, method, assumption, evidence standard)
- Is it resolvable? (empirically testable vs. fundamentally different values)
- What would it take to resolve it?

#### 4.3 Blind Spot Detection

What did one perspective flag that no others mentioned? These are the most valuable findings — they reveal assumptions that are invisible within the primary discipline.

#### 4.4 Recommendations

Based on the synthesis:
1. **Strengthen:** What should the researcher do to address the most serious concerns?
2. **Acknowledge:** What limitations should be explicitly discussed in the paper?
3. **Test:** What additional analyses could resolve the key tensions?
4. **Reframe:** Should the question or approach be reconsidered?

### Phase 5: Output

Create `correspondence/internal-reviews/` if it does not exist (`mkdir -p`). Write the report to `correspondence/internal-reviews/PERSPECTIVES-REPORT.md` (or print to console for quick use).

## Output Format

```markdown
# Multi-Perspective Analysis

**Question:** [The research question or design choice]
**Date:** YYYY-MM-DD
**Perspectives:** [N] ([list of labels])

## Perspectives

### 1. [Label]: [Discipline]
**Prior:** [One sentence]
**Analysis:** [Agent's full response]

### 2. [Label]: [Discipline]
...

## Peer Evaluation

| Perspective | Avg Rigour | Avg Relevance | Avg Novelty | Avg Practicality | Overall Rank |
|-------------|-----------|--------------|------------|-----------------|--------------|
| [Label] | X.X | X.X | X.X | X.X | #N |

**Key cross-evaluation findings:**
- [Which perspectives updated their view after seeing others]
- [Where evaluators converged on a strength/weakness]

## Synthesis

### Agreements
- [Point 1 — which perspectives agree, and why this is robust]
- [Point 2]

### Tensions

| Tension | Perspectives | Nature | Resolvable? |
|---------|-------------|--------|-------------|
| [Description] | A vs. B | Methodological | Yes — via [test] |
| [Description] | C vs. D, E | Conceptual | No — different values |

### Blind Spots
- [Finding] — flagged by [perspective], missed by all others
- [Finding]

### Recommendations
1. **Strengthen:** [Most important action]
2. **Acknowledge:** [Limitation to discuss]
3. **Test:** [Additional analysis]
4. **Reframe:** [If applicable]

## Next Steps
- [ ] [Actionable item 1]
- [ ] [Actionable item 2]
```

## Council Mode Enhancement

In standard mode, Phase 3 spawns Claude sub-agents with different personas — but they all share the same underlying model. Council mode upgrades this to genuine model diversity: different LLM providers (Claude, GPT, Gemini) bring genuinely different reasoning patterns, training biases, and knowledge bases.

**Trigger:** "Council multi-perspective" or "thorough multi-perspective"

**What changes in council mode:**
- Phase 3 (Parallel Investigation): Each perspective is assigned to a different LLM provider via `council-cli`, not Claude sub-agents
- Phase 3.3 (Cross-Evaluation): Each model evaluates the others' perspectives without knowing which model produced which — genuine blind review
- Phase 4 (Synthesis): Chairman model reads all perspectives and cross-evaluations, weighted by peer scores

**Invocation (CLI backend):**
```bash
cd packages/council-cli
uv run python -m council_cli \
    --prompt-file /tmp/perspective-prompt.txt \
    --context-file /tmp/research-context.txt \
    --output-md /tmp/perspectives-council.md \
    --chairman claude \
    --timeout 180
```

See `skills/shared/council-protocol.md` for the full orchestration protocol.

**Value:** High — this skill is the natural fit for council mode. The whole point of multi-perspective analysis is cognitive diversity, and using genuinely different models instead of persona-differentiated instances of the same model is a strict upgrade.

## Cross-References

| Skill | When to use instead/alongside |
|-------|-------------------------------|
| `/devils-advocate` | Quick single-perspective adversarial feedback |
| `/literature` | Find the papers that perspectives reference |
| `/interview-me` | Develop the research idea through structured conversation |
| Referee 2 agent | Formal paper audit with code verification |
| `references/computational-many-analysts.md` | When combining qualitative perspectives with quantitative many-analysts |


---

## parse-reviews

**Source:** `skills/parse-reviews/SKILL.md`

---
name: parse-reviews
description: "Use when you need to process referee comments from a reviews PDF into tracking files."
allowed-tools: Read, Write, Edit, Glob, Grep, Bash(mkdir*), Bash(cp*), Bash(ls*), Bash(latexmk*), AskUserQuestion, Task
argument-hint: "[path-to-reviews-pdf or no arguments for guided setup]"
---

# Process Referee Comments

Read a reviews PDF and generate three standardised output files for managing an R&R response.

## When to Use

- Received reviewer reports for a paper (journal or conference)
- Starting an R&R cycle and need to set up tracking infrastructure
- Want to standardise an existing ad-hoc review response

## When NOT to Use

- Writing the actual response letter (use the generated `comment-tracker.md` response blocks as a starting point, then write the letter manually)
- Reviewing someone else's paper (use `/proofread` or the `peer-reviewer` agent)

## Inputs

Gather via interview if not provided:

1. **Reviews PDF path** — auto-discovered or user-provided (see below)
2. **Project path** — root of the research project (auto-detect from cwd if possible)
3. **Venue slug** — short identifier, e.g., `ejor`, `facct-2026`, `management-science`
4. **Revision round** — integer, default 1
5. **Response deadline** — date if known, otherwise "TBD"
6. **Coordinating author** — who is leading the response

### PDF Auto-Discovery

Search for the reviews PDF in this order. Use the first match; if multiple PDFs found at a location, list them and ask the user to pick.

1. `to-sort/*.pdf` — most likely landing spot after download
2. `correspondence/referee-reviews/{venue}-round{n}/*.pdf`
3. `correspondence/referee-reviews/*.pdf`
4. Ask the user for the path if nothing found

## Output Location

Review correspondence goes under `correspondence/referee-reviews/`, with an `analysis/` subfolder for derived work:

```
correspondence/referee-reviews/{venue}-round{n}/
├── reviews-original.pdf              (copy of input PDF — source is NEVER moved/deleted)
├── rebuttal.md                       (empty — for response draft)
├── reviews/                          (individual reviewer files)
│   ├── reviewer-1.md
│   ├── reviewer-2.md
│   └── ...
└── analysis/
    ├── comment-tracker.md            (atomic comment matrix)
    ├── review-analysis.md            (strategic overview)
    └── reviewer-comments-verbatim.tex (LaTeX transcription)
```

**Source PDF preservation:** The original reviews PDF is only ever **copied** to `reviews-original.pdf`. Never move, rename, or delete the source file from its original location (e.g., `to-sort/`, Downloads, etc.). The user decides when to clean up the original.

**Principle:** `correspondence/` holds exchanges with reviewers (their comments, your rebuttal). Internal review work (e.g., referee2 agent reports) goes in `docs/{venue}/internal-reviews/`.

If the round directory already exists (e.g., from manual setup), do NOT overwrite existing files. Instead:
- If `comment-tracker.md` already exists, name the new one `comment-tracker-v2.md` (or next version)
- If `reviewer-comments-verbatim.tex` already exists, name the new one `reviewer-comments-verbatim-v2.tex`
- Always flag existing files to the user before writing

## Protocol

### Phase 1: Setup

1. Confirm inputs (PDF path, project path, venue, round, deadline, lead author)
2. Create the directory structure under `correspondence/referee-reviews/{venue}-round{n}/`
3. Copy the reviews PDF to `correspondence/referee-reviews/{venue}-round{n}/reviews-original.pdf`

### Phase 2: Read the Reviews

1. Read the reviews PDF using the Read tool (supports PDF natively)
2. For large PDFs (>10 pages), read in page ranges (e.g., pages 1-10, then 11-20)
3. Extract for each reviewer:
   - Reviewer identifier (name, number, or anonymous ID)
   - Recommendation / score (if provided)
   - Whether revision is allowed
   - General assessment text
   - Individual comments (each as a separate item)

### Phase 3: Generate Individual Review Markdown Files

Create one markdown file per reviewer in `reviews/`:

1. Create the `reviews/` subdirectory
2. For each reviewer, write `reviews/reviewer-{n}.md` containing:
   - **Header:** reviewer identifier, recommendation/score, whether revision is allowed
   - **General Assessment:** full verbatim text of the reviewer's overall assessment
   - **Individual Comments:** each comment as a numbered item with its assigned ID (`R{n}-C{m}`), verbatim text, and section/page reference if mentioned
3. Use this template for each file:

```markdown
# Reviewer {N}

**Recommendation:** {recommendation or score}
**Revision allowed:** {Yes / No / Not stated}

## General Assessment

{verbatim general assessment text}

## Comments

### R{N}-C1 {optional: section/page reference}

{verbatim comment text}

### R{N}-C2 ...

{verbatim comment text}
```

4. If files already exist in `reviews/`, follow the same versioning convention as other outputs (flag and version)

### Phase 4: Generate LaTeX Verbatim Transcription

Using the template from `templates/referee-comments/reviewer-comments-verbatim.tex`:

1. Create one `\section{}` per reviewer with comment count and recommendation
2. Place general assessment in a `genbox` environment
3. For each specific comment:
   - Assign an ID: `R{reviewer}-C{comment}` (sequential within each reviewer)
   - Identify the section/page reference if the reviewer mentions one
   - Place the full verbatim text in the comment table
4. If a single reviewer paragraph contains multiple distinct concerns, split into separate IDs and add a `\textit{\footnotesize Split: ...}` note
5. If any IDs are derived (split from a larger comment or inferred), add them to a Derived IDs appendix section
6. Compile with `latexmk` to verify it builds cleanly

### Phase 5: Generate Comment Tracker

Using the template from `templates/referee-comments/comment-tracker.md`:

1. Fill in the Triage Summary table
2. Populate the Comment Matrix — one row per atomic comment:
   - **ID:** matching the LaTeX verbatim IDs
   - **Reviewer:** reviewer number
   - **Comment:** short verbatim quote (first ~100 chars in quotes)
   - **Type:** classify as Major / Minor / Editorial / Question / Praise
   - **R&R Classification:** classify as NEW ANALYSIS / CLARIFICATION / DISAGREE / MINOR (see `references/rr-routing.md` for decision rules and signal words)
   - **Priority:** assign Critical / High / Medium / Low based on:
     - Critical = threatens acceptance if not addressed
     - High = significant concern, must address
     - Medium = reasonable concern, should address
     - Low = minor or editorial
   - **Action:** leave blank (for the user to fill)
   - **Owner:** leave blank
   - **Status:** set all to "Pending"
   - **Section:** paper section referenced, if identifiable
3. Fill in the Status Dashboard counts
4. Generate a **Routing Summary** table grouping comments by R&R classification:
   - NEW ANALYSIS: list IDs + brief description of required analysis
   - CLARIFICATION: list IDs + target sections needing revision
   - DISAGREE: list IDs + flag for user review
   - MINOR: list IDs
5. Identify **Cross-Cutting Themes** — concerns raised by 2+ reviewers, tagged T1, T2, etc.
6. Leave Evidence Log, Patch Plan, Response Blocks, and Blockers empty (user fills during revision)

### Phase 6: Generate Review Analysis

Using the template from `templates/referee-comments/review-analysis.md`:

1. Fill in Scores & Recommendations table
2. Write a Reviewer Profile for each reviewer:
   - **Posture:** hostile / sceptical / constructive / supportive (infer from tone)
   - **What they liked:** bullet points
   - **What they want revised:** numbered list
   - **Assessment:** paragraph on how addressable their concerns are
   - **Risk:** None / Low / Medium / High with explanation
3. Identify Cross-Cutting Themes — concerns that appear across 2+ reviewers, tagged T1, T2, etc.
4. Estimate Acceptance Probability with factors for/against
5. Bucket comments into Priority 1/2/3 response categories
6. List Vulnerabilities (weaknesses in the paper that reviewers exposed)
7. Populate the Publication Strategy section:
   - **Strategy A (minimal revision):** venues that would accept the paper's strengths as-is, despite the weaknesses reviewers identified. Look for venues that value the descriptive/empirical contribution without demanding the specific improvements the current reviewers want.
   - **Strategy B (substantial revision):** venues worth targeting if the authors invest effort to address the major reviewer concerns. These should be equal or higher prestige than the current venue.
   - For conferences: check CORE rankings via `.context/resources/venue-rankings.md` (and the CSV at `.context/resources/venue-rankings/core_2026.csv`). Note upcoming deadlines.
   - For journals: check CABS AJG rankings via `.context/resources/venue-rankings.md` (and the CSV at `.context/resources/venue-rankings/abs_ajg_2024.csv`). For SJR score, query the Elsevier Serial Title API (see venue-rankings.md for snippet; requires `SCOPUS_API_KEY`). Flag journals below CABS 3 only if there's a strong fit rationale.
   - **Recommendation table:** rank 3-5 venues in priority order with rationale. First option should always be "revise for current venue" if acceptance probability is above ~30%.
   - **Key Decision:** frame the core trade-off the authors face (e.g., speed vs. impact, minimal vs. substantial revision effort).
   - Consider the paper's discipline and methodology when suggesting venues — a qualitative policy analysis fits different outlets than a computational study.
8. Leave Timeline empty (user fills)

### Phase 6.5: Strategic Coaching (Interactive)

For each **Major** or **Critical** comment, walk the user through a structured deliberation:

1. **Understanding:** "What is this reviewer's core concern — methodology, theory, or framing?"
2. **Position:** Classify as one of:
   - **Agree** — will revise as suggested
   - **Partially agree** — will address the spirit but not the exact suggestion. State which parts you accept and which you push back on.
   - **Disagree** — will rebut with evidence. Draft the core rebuttal argument.
3. **Risk assessment:** "If you push back on this, how likely is the reviewer to escalate? Is it worth the risk?"
4. **Response sketch:** One-sentence draft of the response direction (not the full response — just the strategy).

Record these in the Comment Matrix by adding two columns after `R&R Classification`:
- **Position:** Agree / Partially / Disagree
- **Strategy:** one-line response direction

**Rules:**
- Only Major and Critical comments get coaching. Minor/Editorial are auto-classified as "Agree" with no coaching.
- the user can say "skip coaching" to bypass and classify all remaining as Agree.
- Maximum 2 rounds of dialogue per comment — do not over-discuss.
- Do not write the actual response letter — that remains the user's job.

### Phase 7: Summary & Review

Present to the user:
- Total comments extracted (by reviewer)
- Breakdown by type and priority
- Key cross-cutting themes
- Position summary: N Agree / N Partially / N Disagree
- Any comments that were ambiguous or hard to classify
- Ask for corrections before finalising

## Critical Rules

1. **Verbatim means verbatim.** Never paraphrase reviewer text in the LaTeX transcription. Copy exactly.
2. **Every comment gets an ID.** No reviewer concern should be lost. If in doubt, give it its own ID.
3. **Don't write actions.** The Comment Matrix `Action` column stays blank — that's the user's job.
4. **Don't overwrite.** If files already exist at the target location, flag and version.
5. **Compile the LaTeX.** The verbatim document must build without errors before the skill completes.

## Templates

Located in `templates/referee-comments/`:
- `comment-tracker.md`
- `review-analysis.md`
- `reviewer-comments-verbatim.tex`

## Cross-References

- `/proofread` — for proofreading the response letter before submission
- `/bib-validate` — run after revision to check bibliography
- `/pre-submission-report` — full quality check before resubmission
- `paper-critic` agent — for self-review of the revised paper
- `references/rr-routing.md` — R&R classification system and routing logic for revision workflow


---

## pipeline-manifest

**Source:** `skills/pipeline-manifest/SKILL.md`

---
name: pipeline-manifest
description: "Use when you need to map scripts to their inputs, outputs, and paper figures/tables."
allowed-tools: Read, Write, Edit, Glob, Grep, AskUserQuestion
argument-hint: [project-path]
---

# Pipeline Manifest

Build and maintain a `pipeline.md` that maps every script in a research project to its inputs, outputs, and the paper figures/tables it feeds. Optionally add structured headers to scripts that lack them.

## When to Use

- When starting a multi-step empirical project (establish the pipeline early)
- Before sharing code with coauthors (makes the data flow legible)
- Before submission (ensures the replication package is traceable)
- After inheriting or reviving old code (pair with `/code-archaeology`)
- When you can't remember which script produces Figure 3

## When NOT to Use

- Pure theory projects with no empirical pipeline
- Single-script projects (no pipeline to map)
- **Code quality review** — use `/code-review` instead (this skill maps structure, not quality)

## Modes

Ask the user which mode to run:

| Mode | What it does | Writes to |
|------|-------------|-----------|
| **Scan** (default) | Read-only. Scans scripts, builds `pipeline.md` | `pipeline.md` only |
| **Add headers** | Scan + insert structured headers into scripts that lack them | `pipeline.md` + script files |

In **Add headers** mode, show the proposed header for each script and get confirmation before writing. Never overwrite an existing structured header — only add to scripts that lack one.

## Structured Script Header Format

Every research script should begin with a structured header block. The format adapts to the language:

### Python

```python
# ============================================================================
# PURPOSE: [One sentence describing what this script does]
# INPUTS:  [Comma-separated list of input files, relative to project root]
# OUTPUTS: [Comma-separated list of output files, relative to project root]
# DEPENDS: [Scripts that must run before this one, or "none"]
# PAPER:   [Figure/table references this feeds, e.g. "Figure 2, Table 1", or "none"]
# ============================================================================
```

### R

```r
# ============================================================================
# PURPOSE: [One sentence describing what this script does]
# INPUTS:  [Comma-separated list of input files, relative to project root]
# OUTPUTS: [Comma-separated list of output files, relative to project root]
# DEPENDS: [Scripts that must run before this one, or "none"]
# PAPER:   [Figure/table references this feeds, e.g. "Figure 2, Table 1", or "none"]
# ============================================================================
```

### Stata

```stata
* ============================================================================
* PURPOSE: [One sentence describing what this script does]
* INPUTS:  [Comma-separated list of input files, relative to project root]
* OUTPUTS: [Comma-separated list of output files, relative to project root]
* DEPENDS: [Scripts that must run before this one, or "none"]
* PAPER:   [Figure/table references this feeds, e.g. "Figure 2, Table 1", or "none"]
* ============================================================================
```

### Julia

```julia
# ============================================================================
# PURPOSE: [One sentence describing what this script does]
# INPUTS:  [Comma-separated list of input files, relative to project root]
# OUTPUTS: [Comma-separated list of output files, relative to project root]
# DEPENDS: [Scripts that must run before this one, or "none"]
# PAPER:   [Figure/table references this feeds, e.g. "Figure 2, Table 1", or "none"]
# ============================================================================
```

## Header Field Definitions

| Field | What it contains | How to populate |
|-------|-----------------|-----------------|
| **PURPOSE** | One sentence. What does this script do? | Read the script and summarise |
| **INPUTS** | Files this script reads. Paths relative to project root. | Grep for `read`, `load`, `import`, `open`, `use` patterns |
| **OUTPUTS** | Files this script writes. Paths relative to project root. | Grep for `write`, `save`, `export`, `ggsave`, `savefig`, `sink` patterns |
| **DEPENDS** | Other scripts that must run first (their outputs are this script's inputs). | Trace input files back to the scripts that produce them |
| **PAPER** | Which figures, tables, or sections in the paper use this script's output. | Match output filenames against `\includegraphics`, `\input`, `\include` in `.tex` files |

## Workflow

### Phase 1: Discover Scripts

Scan the project for research scripts:

```
code/**/*.{py,R,r,do,jl,m}
src/**/*.{py,R,r,do,jl,m}
scripts/**/*.{py,R,r,do,jl,m}
```

Exclude:
- `__pycache__/`, `.venv/`, `renv/`, `node_modules/`
- Test files (`test_*.py`, `*_test.R`)
- Setup/config scripts (`setup.py`, `conftest.py`)

Sort by filename (numerical prefixes like `01_`, `02_` determine natural order).

### Phase 2: Extract Pipeline Information

For each script:

1. **Check for existing header.** Look for the `PURPOSE:` / `INPUTS:` / `OUTPUTS:` / `DEPENDS:` / `PAPER:` pattern in the first 20 lines.

2. **If header exists:** Parse it directly. Trust the header as ground truth.

3. **If no header:** Read the full script and infer:
   - **Inputs:** File read operations (`pd.read_csv`, `read.csv`, `readRDS`, `load`, `use`, `open`, `import delimited`, `fread`, `arrow::read_parquet`, `readr::read_*`)
   - **Outputs:** File write operations (`to_csv`, `write.csv`, `saveRDS`, `save`, `ggsave`, `plt.savefig`, `export`, `sink`, `write_parquet`, `fwrite`, `outsheet`, `estout`)
   - **Dependencies:** Cross-reference — if script B reads a file that script A writes, then B depends on A
   - **Paper links:** Match output filenames against `\includegraphics{...}` and `\input{...}` in `.tex` files

### Phase 3: Build Dependency Graph

From the extracted information, construct:

1. **Execution order** — topological sort of the dependency graph. Flag cycles as errors.
2. **Orphan detection** — scripts whose outputs are never used by another script or the paper. These may be exploratory/deprecated.
3. **Missing link detection** — inputs that no script produces and that don't exist in `data/raw/`.

### Phase 4: Build Paper Linkage

Scan all `.tex` files in `paper/` for:
- `\includegraphics{path}` — figures
- `\input{path}` — tables or sub-documents
- `\include{path}` — chapters

Match these paths to script outputs. Build a reverse map: for each figure/table in the paper, which script(s) produce it?

### Phase 5: Write pipeline.md

Write `pipeline.md` to the project root using the format below.

### Phase 6 (Add Headers Mode Only): Insert Headers

For scripts missing structured headers:
1. Generate the header from Phase 2 analysis
2. Show the proposed header to the user
3. On confirmation, insert at the top of the file (after any shebang line or encoding declaration)

## pipeline.md Format

```markdown
# Pipeline Manifest

> Auto-generated by `/pipeline-manifest` on YYYY-MM-DD.
> Manually edit the PAPER column and any inferred values that are wrong.
> Re-run `/pipeline-manifest` to refresh after adding or modifying scripts.

## Pipeline Table

| # | Script | Purpose | Inputs | Outputs | Depends | Paper |
|---|--------|---------|--------|---------|---------|-------|
| 1 | `code/01_clean.R` | Clean raw survey data | `data/raw/survey.csv` | `data/processed/survey_clean.rds` | none | -- |
| 2 | `code/02_merge.R` | Merge survey with admin data | `data/processed/survey_clean.rds`, `data/raw/admin.csv` | `data/processed/merged.rds` | `01_clean.R` | -- |
| 3 | `code/03_analysis.R` | Run main regressions | `data/processed/merged.rds` | `results/main_results.rds`, `paper/figures/fig_coef.pdf` | `02_merge.R` | Figure 2 |
| 4 | `code/04_robustness.py` | Robustness checks | `data/processed/merged.rds` | `results/robustness.csv`, `paper/figures/fig_robust.pdf` | `02_merge.R` | Figure 3, Table A1 |

## Figure & Table Manifest

| Paper Reference | Producing Script | Output File |
|----------------|-----------------|-------------|
| Figure 2 | `code/03_analysis.R` | `paper/figures/fig_coef.pdf` |
| Figure 3 | `code/04_robustness.py` | `paper/figures/fig_robust.pdf` |
| Table A1 | `code/04_robustness.py` | `results/robustness.csv` |

## Dependency Graph

```
data/raw/survey.csv ─┐
                     ├─> 01_clean.R ─> data/processed/survey_clean.rds ─┐
data/raw/admin.csv ──┘                                                  ├─> 02_merge.R ─> data/processed/merged.rds ─┬─> 03_analysis.R
                                                                        │                                            └─> 04_robustness.py
```

## Diagnostics

### Orphan Scripts
Scripts whose outputs are not consumed by any other script or the paper.

### Missing Inputs
Files referenced as inputs but not produced by any script and not found in `data/raw/`.

### Execution Order
Recommended order based on dependency resolution:
1. `code/01_clean.R`
2. `code/02_merge.R`
3. `code/03_analysis.R`
4. `code/04_robustness.py` (can run in parallel with step 3)
```

## Updating an Existing pipeline.md

If `pipeline.md` already exists:

1. Read it and parse the existing table
2. Re-scan scripts (some may have been added, removed, or modified)
3. **Preserve manual edits** — if the user has edited the PAPER column or added notes, keep those values. Only update fields that can be re-derived from code (PURPOSE, INPUTS, OUTPUTS, DEPENDS).
4. Flag changes: "2 scripts added, 1 script removed, 3 entries updated"
5. Write the updated file

## Cross-References

- **`/code-review`** — Quality review for individual scripts (checks header presence in Category 2: Script Structure)
- **`/code-archaeology`** — For understanding unfamiliar code before building the manifest
- **`/pre-submission-report`** — Pipeline manifest helps verify the replication package is complete
- **`/init-project-research`** — New projects can run `/pipeline-manifest` once scripts exist


---

## postmortem

**Source:** `skills/postmortem/SKILL.md`

---
name: postmortem
description: "Use when you need a structured post-mortem after incidents, mistakes, or stuck sessions."
allowed-tools:
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - AskUserQuestion
---

# Lessons Learned: Structured Retrospective

Analyse incidents using a structured framework, identify root causes, and encode preventive measures directly into skills, guards, or documentation. The goal is systematic improvement, not blame.

## When to Use

- After incidents, mistakes, rollbacks, or near-misses
- When the user says "what went wrong", "lessons learned", "post-mortem", "retrospective", or "how do we prevent this"
- After a stuck session where significant time was lost
- After a wrong-approach event (plan existed but execution diverged)

## Process

### Phase 1: Incident Definition

Capture the facts first, analysis later.

```markdown
## Incident Summary

**What happened:** [Factual description]
**When:** [Date/time]
**Impact:** [What was affected, scope]
**Resolution:** [How it was fixed/rolled back]
**Time to resolution:** [How long to fix]
```

### Phase 2: Timeline Reconstruction

Build a chronological sequence of events:

| Time | Action | Actor | Outcome |
|------|--------|-------|---------|
| HH:MM | [What was done] | [Claude/User] | [Result] |

Key questions:
- What was the trigger?
- Where did the sequence diverge from expected?
- What was the point of no return?

### Phase 3: Root Cause Analysis (5 Whys)

```
1. Why did [incident] happen?
   → Because [immediate cause]

2. Why did [immediate cause] happen?
   → Because [deeper cause]

3. Why did [deeper cause] happen?
   → Because [systemic issue]

4. Why did [systemic issue] exist?
   → Because [process gap]

5. Why did [process gap] exist?
   → Because [root cause]
```

Stop when you reach a cause that can be addressed by a concrete change to the system (skill, rule, hook, doc).

### Phase 4: Contributing Factors

Identify all factors, not just the root cause:

| Category | Factor | Contribution |
|----------|--------|--------------|
| **Process** | Missing checkpoint, unclear workflow | [How it contributed] |
| **Communication** | Ambiguous instructions, assumed consent | [How it contributed] |
| **Technical** | Missing guard, no validation | [How it contributed] |
| **Context** | Session continuation, prior assumptions | [How it contributed] |
| **Human** | Fatigue, time pressure, overconfidence | [How it contributed] |

### Phase 5: Fix Classification

Classify each fix by type:

| Fix Type | When to Use | How to Encode |
|----------|-------------|---------------|
| **Skill** | Recurring workflow needs structure | Create SKILL.md via `/skill-extract` |
| **Guard** | Action requires mandatory checkpoint | Add approval gate to existing skill |
| **Rule** | Behavioural constraint needed globally | Create `rules/*.md` |
| **Documentation** | Knowledge gap caused the issue | Update CLAUDE.md, MEMORY.md, or docs/ |
| **Hook** | Manual step was forgotten | Create script in hooks/ |
| **Checklist** | Multiple steps need verification | Add to existing skill |

### Phase 6: Fix Implementation

**Implement fixes during the retrospective, not after.** This is the critical difference from a report-only post-mortem.

For each fix:
1. Implement it (create/edit the file)
2. Record what was done:

| Fix | Type | Location | Status |
|-----|------|----------|--------|
| [Description] | Skill/Guard/Rule/Doc/Hook | [File path] | Created/Updated |

Also record a `[LEARN]` tag in MEMORY.md for each key correction (per the `learn-tags` rule).

### Phase 7: Verification

Define how to verify the fix works:

```markdown
## Verification

**Test scenario:** [How to test the fix]
**Success criteria:** [What "fixed" looks like]
**Review date:** [When to check if fix is working — default: 2 weeks]
```

## Output

Write the report to `log/incidents/YYYY-MM-DD_short-description.md`:

```markdown
# Lessons Learned: [Incident Title]

**Date:** YYYY-MM-DD
**Severity:** [Low|Medium|High|Critical]
**Status:** [Resolved|Monitoring|Open]

## Incident Summary
[Brief description]

## Timeline
| Time | Action | Actor | Outcome |
|------|--------|-------|---------|

## Root Cause
[The fundamental issue]

## Contributing Factors
- [Factor 1]
- [Factor 2]

## Fixes Implemented
| Fix | Type | Location | Status |
|-----|------|----------|--------|

## Prevention
[How this prevents recurrence]

## Lessons
1. [Key takeaway 1]
2. [Key takeaway 2]
```

Create `log/incidents/` if it doesn't exist.

## Common Incident Patterns

| Pattern | Symptom | Root Cause | Typical Fix |
|---------|---------|------------|-------------|
| Premature action | Action taken before approval | Implied consent ≠ explicit | Add approval gate to skill |
| Sequence error | Steps in wrong order | Missing dependency chain | Encode sequence in skill |
| Missing validation | Bad data passed through | No checkpoint | Add pre-flight check |
| Context carryover | Stale assumptions from prior session | State assumed to persist | Explicit context verification |
| Scope creep | Did more than requested | Task scope too broad | Clarifying questions first |
| Planning loop | Re-planned instead of executing | Perfectionism / uncertainty | Execution stall detector |

## Anti-Patterns

| Anti-Pattern | Problem | Instead |
|--------------|---------|---------|
| Blame assignment | Creates defensiveness | Focus on process, not people |
| Single-cause thinking | Oversimplifies | Use 5 Whys, multiple factors |
| Recommend without acting | Lessons forgotten, recurs | Implement fixes during retro |
| Vague fixes ("be more careful") | Not verifiable | Encode specific changes |
| Skip verification | No way to know if fix worked | Define success criteria |

## Cross-References

- **`[LEARN]` tags** — record one-liner corrections in MEMORY.md (the quick complement to this skill)
- **`/skill-extract`** — extract a full skill from a session (when the fix type is "Skill")
- **`/ideas`** — if a fix is too large for this session, capture as an idea for later

## Success Criteria

The retrospective is complete when:
- [ ] Incident clearly defined with timeline
- [ ] Root cause identified (not just symptoms)
- [ ] Contributing factors documented
- [ ] At least one fix implemented (not just recommended)
- [ ] Fix encoded in appropriate location (skill, rule, hook, doc)
- [ ] `[LEARN]` tags recorded in MEMORY.md
- [ ] Verification criteria defined
- [ ] Report written to `log/incidents/`


---

## pre-submission-report

**Source:** `skills/pre-submission-report/SKILL.md`

---
name: pre-submission-report
description: "Use when you need all quality checks run before submission, producing a single dated report."
allowed-tools: Bash(latexmk*, mkdir*, ls*, wc*), Read, Write, Edit, Glob, Grep, Task, Skill
argument-hint: "[path/to/main.tex or no arguments to auto-detect]"
---

# Pre-Submission Report

> Aggregates all quality checks into one dated report. Run before submitting to a journal/conference or sharing with collaborators.

## Output Path

Per `rules/review-artefact-routing.md` (auto-loads in research projects (path-scoped to `paper-*/` and `paper/`)):

- **Source slug:** `pre-submission-report`
- **Write reports to:** `reviews/pre-submission-report/YYYY-MM-DD.md` inside the project. Path is relative to the research project root, not the Task-Management repo.
- **Never** at project root (`./CRITIC-REPORT.md`-style filenames are forbidden — pre-rule layout).
- **Idempotency:** if today's file exists, append a same-day descriptor (`{date}-revision.md`, `{date}-r2.md`, `{date}-pre-submission.md`) — never overwrite.
- **Index update:** if `reviews/INDEX.md` exists, write a one-line entry under "Latest per source" pointing at the new file. Otherwise `/review-recap` will rebuild the index next time it runs.
- **Infrastructure repos** (Task-Management, atlas-workspace, etc.): this section does not apply — the path-scoped rule won't load there.


## When to Use

- Before submitting a paper to a venue
- Before sharing a draft with supervisors or co-authors
- When the user says "pre-submission check", "is this ready?", "run everything"

## Input

- A `.tex` file path, or auto-detect `paper/main.tex` in the current project

## Critical Rule

**Python:** Always use `uv run python` or `uv pip install`. Never bare `python`, `python3`, `pip`, or `pip3`. Include this in any sub-agent prompts.

## Steps

### 1. Locate the Paper

If no argument provided, search for the main `.tex` file:
1. Check `paper/main.tex`
2. Check `paper/*.tex` for a file containing `\begin{document}`
3. Ask the user if ambiguous

### 2. Integrity Gate (hard gate — must pass before quality checks)

Run these checks first. If any fail, stop and report — do not proceed to quality checks.

1. **Placeholder scan** — grep the `.tex` file(s) for `TODO`, `FIXME`, `XXX`, `TBD`, `[INSERT`, `PLACEHOLDER`, `Lorem ipsum`. Any match is a FAIL.
2. **Citation integrity** — invoke `/bib-validate` in verify mode. Every `\cite{}` key must resolve to a `.bib` entry. Any missing key is a FAIL.
3. **Section completeness** — check that all standard sections exist and are non-empty (Abstract, Introduction, and at least one body section before Conclusion/References). An empty or missing section is a FAIL.
4. **Broken references** — grep for `??` in the compiled PDF output or `.log` file (undefined `\ref{}` or `\cite{}`). Any `??` in output is a FAIL.
5. **Anonymity gate (only if the venue is double-blind)** — load `_shared/double-blind-anonymity-checklist.md` and run **all** P1–P8 paper-side checks. Any FAIL is a hard stop. In particular: P4 (self-citation bib must be blinded if cited paper's author list overlaps the submission's) and P5 (body text must not name authors of self-cited works) — these are the CCS 2026 #1328 desk-reject triggers and require the submission's author list to be loaded from the vault submission frontmatter or prompted from the user. If the artifact has been minted via `/anonymous-artifact`, also confirm A1–A9 ran clean for that artifact (state file at `<project>/.anonymous-artifact-state.json`). Skip this entire step only when the user explicitly says "single-blind" or "non-blind".

**If any check fails:**
```
INTEGRITY GATE: FAIL

Blockers (must fix before quality checks):
  - [ ] 3 TODO placeholders found (lines 47, 112, 289)
  - [ ] 2 undefined references (\ref{fig:missing}, \cite{nonexistent2024})
  - [ ] Abstract section is empty

Fix these and re-run /pre-submission-report.
```

**If all pass:** proceed to Step 3.

### 3. Run Quality Checks

Two modes:

#### 3a. Sequential (default — fast, deterministic)

Run these in order — each depends on a clean state from the previous:

1. **Compilation** — invoke `/latex` on the main `.tex` file. Record pass/fail and any remaining warnings.
2. **Citation audit** — invoke `/bib-validate --verify-doi` (DOI resolution mode catches fabricated entries). Record missing, unused, suspect, and unresolved-DOI keys.
3. **Adversarial review** — launch `paper-critic` agent (via Task tool). Capture the CRITIC-REPORT.md score and findings.

#### 3b. Parallel 7-audit fan-out (`--parallel` flag)

Use when (a) the paper is near submission and you want a comprehensive scan, or (b) the user explicitly asks for the "full pre-submission swarm". Dispatches **7 read-only sub-agents in parallel** via the Task tool, then consolidates findings.

**Hard rules for parallel mode:**
1. **All sub-agents are read-only with respect to project files under review** — see `subagent-write-guard.md` rule. They do NOT modify the paper, bib, code, or any other artefact under review; the orchestrator (this skill) decides what to fix. **They DO write their own per-agent reports** to `reviews/<source-slug>/<YYYY-MM-DD-HHMM>.md` per each agent's "Log to REVIEW-STATE.md (final step)" instruction — this is the durable record + the INDEX.md stamp that `/review-recap` reads. The "read-only" scope is the artefact under review, NOT a prohibition on writing the review report itself.
2. **Each sub-agent gets the standard forbid-list** — no git, no latexmk, no edits to files outside their scope. The forbid-list explicitly carves out the `reviews/<source-slug>/` path as a permitted write target (the agent's logging step needs it).
3. **Findings consolidate into a P0/P1/P2 fix list** before any edits — single triage point, not 13 streams. Sub-agents return structured findings to the orchestrator in addition to writing their report file; the consolidate step uses the structured returns.
4. **No edit phase auto-runs** — the user reviews the consolidated report and approves which fixes to apply.

**The 7 sub-agents:**

**Always dispatched (13 sub-agents):**

| # | Agent | Scope | Output |
|---|---|---|---|
| 1 | **bib-verifier** | DOI resolution + Crossref/S2 verification of every bib entry via `bib-validate --verify-doi` mode; flag fabricated/unresolvable | List of unverified keys + suggested fixes |
| 2 | **claim-verifier** | Launch `claim-verify` agent — checks every cited claim against the source paper (citation fidelity, not just key existence) | Per-claim verdicts |
| 3 | **novelty-scout** | Run `scout novelty "<paper title>" --source openalex`; report score + threats not yet cited | Novelty score + missing-related-work list |
| 4 | **paper-critic** | Launch `paper-critic` agent — general adversarial CRITIC-REPORT (specialist mode for venue-calibrated review) | Scored CRITIC-REPORT.md |
| 5 | **domain-reviewer** | Launch `domain-reviewer` agent — math/derivations/assumptions/code-theory alignment | DOMAIN-REVIEW.md |
| 6 | **referee2-reviewer** | Launch `referee2-reviewer` agent — Reviewer 2 hostile read; top reviewer-attack-surface concerns | Adversarial concerns |
| 7 | **blindspot** | Launch `blindspot` agent — peripheral-vision audit (vices in plain sight + virtues being overlooked) | Blindspot report |
| 8 | **code-paper-auditor** | Launch `code-paper-auditor` agent — cross-check quantitative claims against source code outputs | Mismatch table |
| 9 | **artifact-coherence-auditor** | Launch `artifact-coherence-auditor` agent — paper prose vs replication outputs (catches hallucinated results) | Coherence report |
| 10 | **reproducibility-auditor** | Launch `reproducibility-auditor` agent — workflow rerunnability (hidden deps, absolute paths, env assumptions) | Reproducibility report |
| 11 | **anonymity / double-blind checker** | Apply paper-side checks P1-P8 from `_shared/double-blind-anonymity-checklist.md`; verify `[review]` mode if double-blind venue | Pass/fail + leak list |
| 12 | **page-limit + LaTeX validator** | Verify page count under venue limit; check for compile warnings; check `out/` is current | Page count + warning summary |

**Conditional follow-ups (run after parallel fan-out, opt-in):**

| Trigger | Skill |
|---|---|
| Paper has code (detect: non-tex/non-bib files in project) AND venue is double-blind | `/anonymous-artifact` — assemble + sanitize + push to anonymous repo, mint URL |
| Strategic-revision context (paper has referee comments) | `/strategic-revision` — revision plan after the swarm flags issues |

The conditional follow-ups are NOT in the parallel batch — they're sequential because they may modify files (and so violate the read-only invariant of the parallel sub-agents).

**Dispatch protocol:**

```python
# Pseudocode for orchestration — see Task tool docs for actual API
parallel_tasks = [
    Agent("bib-verifier", subagent_type="general-purpose",
          prompt=f"Read {paper_path}/references.bib. Run scholarly scholarly-verify-dois on all DOI-bearing entries (batch ≤50). Report unresolvable DOIs, missing DOIs, suspected fabricated entries. READ-ONLY. {forbid_list}"),
    Agent("novelty-scout", ...),
    # ... 5 more
]
# Wait all → consolidate
findings = consolidate_p0_p1_p2(parallel_tasks)
```

Sub-agents run concurrently — total wall-clock is bounded by the slowest (typically novelty-scout at ~2-3 min via OpenAlex).

**Consolidation:** the orchestrator merges findings from all 13 sub-agents into a single P0/P1/P2 fix list:
- **P0 (block submission):** anonymity leaks (#11), fabricated citations (#1, #2), compilation errors (#12), over-page-limit (#12), code-paper mismatches (#8), prose-replication divergence (#9)
- **P1 (must fix):** unresolved DOIs (#1), claim-verify failures (#2), novelty threats (#3), critic-report Major issues (#4), domain-review math errors (#5), reproducibility issues (#10), referee2-reviewer concerns (#6)
- **P2 (should consider):** blindspot virtues + minor vices (#7), AI-detect hot zones (#13), critic-report Moderate/Minor issues (#4), novelty positioning (#3)

**Code-bearing detection:** if the project has non-tex / non-bib files outside `paper-*/` and `notes/` (typical signal: `code/`, `data/`, `scripts/`, `analysis/`, `src/` directories), enable code-side sub-agents (#8 code-paper-auditor, #9 artifact-coherence-auditor, #10 reproducibility-auditor) and queue `/anonymous-artifact` as a conditional follow-up.

**Edit phase (separate, opt-in):** if the user approves any P0/P1 fixes, dispatch a *second* round of edit-agents with **explicit scoped permissions per file** — see `subagent-write-guard.md` for the forbid-list pattern. The orchestrator confirms each edit-agent's scope before dispatch.

**Why parallel:** the 13 audits are independent — sequential is ~10x slower for the same coverage. Reviewer-pool collision risk is zero (read-only sub-agents).

**Skip parallel mode if:** paper is in early drafting (use the sequential 3-audit instead — faster feedback for incomplete drafts), or sub-agents fail repeatedly (fall back to sequential).

### 4. Aggregate Report

Save to `log/audits/quality-reports/YYYY-MM-DD_<project-name>.md`:

```markdown
# Pre-Submission Quality Report

**Project:** <project name>
**Date:** YYYY-MM-DD
**File:** <path to main.tex>
**Target:** <venue from project CLAUDE.md, or "not specified">

---

## Integrity Gate: PASS / FAIL

- **Placeholders:** 0 found
- **Citation integrity:** all keys resolved
- **Section completeness:** all sections present
- **Broken references:** none

---

## Overall Score: XX/100 — [Verdict]

Verdict uses the quality scoring framework:
- 90-100: Publication-ready
- 80-89: Minor revisions needed
- 70-79: Significant revisions needed
- Below 70: Not ready

---

## Compilation

- **Status:** PASS / FAIL
- **Warnings:** <count>
- **Details:** <brief summary of any issues>

## Citations

- **Missing keys:** <count> — <list>
- **Unused keys:** <count> — <list>
- **Suspect entries:** <count> — <list>

## Adversarial Review

- **Score:** XX/100
- **Key findings:**
  - <finding 1>
  - <finding 2>
  - ...

## Research Quality Score

Load `skills/shared/research-quality-rubric.md` and report the weighted aggregate (X.X / 5.0) with verdict.

## Remaining Issues

| # | Severity | Category | Issue |
|---|----------|----------|-------|
| 1 | High/Medium/Low | Compilation/Citation/Content | <description> |

## Recommendation

**[Submit / Revise / Not ready]**

<1-2 sentence summary of what needs to happen before submission>
```

### 5. Present Summary

Display the report path and the summary table to the user. If the recommendation is "Submit", congratulate. If "Revise", list the top 3 issues to fix first.

## Error Handling

- If compilation fails after `/latex`, still run the remaining checks. Mark compilation as FAIL in the report.
- If `paper-critic` agent fails, note it in the report and base the overall score on compilation + citations only.
- Always produce the report file, even if some checks failed.

## Integration

| Skill/Agent | Role in this workflow |
|-------------|---------------------|
| `/latex` | Compilation + auto-fix |
| `/bib-validate` | Citation cross-reference + self-citation deanonymization scan |
| `paper-critic` agent | Adversarial content review |
| `quality-scoring.md` | Verdict thresholds |
| `_shared/double-blind-anonymity-checklist.md` | P1–P8 / A1–A9 anonymity gate (double-blind venues only) |

## REVIEW-STATE.md propagation (orchestrator-side stamping)

This skill is an **orchestrator** in the REVIEW-STATE.md schema. As of the 2026-05-19 architecture change, the orchestrator handles all stamping; sub-agents emit directives but do not call the helper themselves.

### Required orchestrator behaviour

When constructing prompts for any sub-agent that is a logging tool (paper-critic, referee2-reviewer, peer-reviewer, domain-reviewer, claim-verify, blindspot, fatal-error-check, code-paper-auditor, artifact-coherence-auditor, reproducibility-auditor, code-review), include this line in the sub-agent prompt:

> Emit a `review-state-stamp` directive at the end of your final response per `skills/_shared/stamp-directive-spec.md`. Set `trigger: pre-submission-report` (or omit — this orchestrator overrides). Do not call the stamping helper yourself.


### After each sub-agent returns

For each agent's return:

1. Write the agent's final response to a temp file (`/tmp/pre-submission-<agent>.md`).
2. Parse the directive:
   ```bash
   ARGS=$(bash ~/.claude/skills/_shared/parse-stamp-directive.sh /tmp/pre-submission-<agent>.md)
   ```
   If `parse-stamp-directive.sh` exits non-zero, log a warning ("Agent X return did not contain a review-state-stamp directive — INDEX.md not updated for this run") and continue.
3. **Verify the `.md` report file exists; reconstruct from return content if missing:**
   ```bash
   VERIFY=$(bash ~/.claude/skills/_shared/post-dispatch-verify.sh \
       --return-file /tmp/pre-submission-<agent>.md \
       --project "$PROJECT_ROOT" \
       --agent <agent>)
   ```
   If `VERIFY` starts with `RECONSTRUCTED`, append `(report reconstructed by orchestrator — agent skipped Write)` to the `--notes` value before stamping. Guards against the blindspot-class failure mode. See `log/2026-05-21-blindspot-write-fix.md`.
4. Stamp with the orchestrator's `--trigger` override:
   ```bash
   eval bash ~/.claude/skills/_shared/review-state-log.sh "$ARGS" \
       --trigger pre-submission-report \
       --source agent \
       --project "$PROJECT_ROOT"
   ```
5. Clean up the temp file.

All sub-agent stamps land in `<project>/reviews/INDEX.md` with `Trigger=pre-submission-report` and roughly the same `Last Run` timestamp.

### Why the orchestrator stamps (not the sub-agent)

Agents have inconsistent Bash tool grants at runtime (the 2026-05-19 harness investigation). The orchestrator always has Bash and always runs after the agents return. Moving stamping here decouples it from agent tool-surface uncertainty and fixes the burying problem (referee2-reviewer's stamping section used to live at line ~475 of a 518-line agent definition; agents reliably forgot to reach it).

Schema: `~/Task-Management/docs/reference/review-state-schema.md`.
Stamp directive format: `~/Task-Management/skills/_shared/stamp-directive-spec.md`.


---

## process-reviews

**Source:** `skills/process-reviews/SKILL.md`

---
name: process-reviews
description: "Use when you need to process referee comments from a reviews PDF into tracking files."
allowed-tools: Read, Write, Edit, Glob, Grep, Bash(mkdir*), Bash(cp*), Bash(ls*), Bash(latexmk*), AskUserQuestion, Task
argument-hint: "[path-to-reviews-pdf or no arguments for guided setup]"
---

# Process Referee Comments

Read a reviews PDF and generate three standardised output files for managing an R&R response.

## When to Use

- Received reviewer reports for a paper (journal or conference)
- Starting an R&R cycle and need to set up tracking infrastructure
- Want to standardise an existing ad-hoc review response

## When NOT to Use

- Writing the actual response letter (use the generated `comment-tracker.md` response blocks as a starting point, then write the letter manually)
- Reviewing someone else's paper (use `/proofread` or the `peer-reviewer` agent)

## Inputs

Gather via interview if not provided:

1. **Reviews PDF path** — auto-discovered or user-provided (see below)
2. **Project path** — root of the research project (auto-detect from cwd if possible)
3. **Venue slug** — short identifier, e.g., `ejor`, `facct-2026`, `management-science`
4. **Revision round** — integer, default 1
5. **Response deadline** — date if known, otherwise "TBD"
6. **Coordinating author** — who is leading the response

### PDF Auto-Discovery

Search for the reviews PDF in this order. Use the first match; if multiple PDFs found at a location, list them and ask the user to pick.

1. `to-sort/*.pdf` — most likely landing spot after download
2. `correspondence/referee-reviews/{venue}-round{n}/*.pdf`
3. `correspondence/referee-reviews/*.pdf`
4. Ask the user for the path if nothing found

## Output Location

Review correspondence goes under `correspondence/referee-reviews/`, with an `analysis/` subfolder for derived work:

```
correspondence/referee-reviews/{venue}-round{n}/
├── reviews-original.pdf              (copy of input PDF — source is NEVER moved/deleted)
├── rebuttal.md                       (empty — for response draft)
├── reviews/                          (individual reviewer files)
│   ├── reviewer-1.md
│   ├── reviewer-2.md
│   └── ...
└── analysis/
    ├── comment-tracker.md            (atomic comment matrix)
    ├── review-analysis.md            (strategic overview)
    └── reviewer-comments-verbatim.tex (LaTeX transcription)
```

**Source PDF preservation:** The original reviews PDF is only ever **copied** to `reviews-original.pdf`. Never move, rename, or delete the source file from its original location (e.g., `to-sort/`, Downloads, etc.). The user decides when to clean up the original.

**Principle:** `correspondence/` holds exchanges with reviewers (their comments, your rebuttal). Internal review work (e.g., referee2 agent reports) goes in `docs/{venue}/internal-reviews/`.

If the round directory already exists (e.g., from manual setup), do NOT overwrite existing files. Instead:
- If `comment-tracker.md` already exists, name the new one `comment-tracker-v2.md` (or next version)
- If `reviewer-comments-verbatim.tex` already exists, name the new one `reviewer-comments-verbatim-v2.tex`
- Always flag existing files to the user before writing

## Protocol

### Phase 1: Setup

1. Confirm inputs (PDF path, project path, venue, round, deadline, lead author)
2. Create the directory structure under `correspondence/referee-reviews/{venue}-round{n}/`
3. Copy the reviews PDF to `correspondence/referee-reviews/{venue}-round{n}/reviews-original.pdf`

### Phase 2: Read the Reviews

1. Read the reviews PDF using the Read tool (supports PDF natively)
2. For large PDFs (>10 pages), read in page ranges (e.g., pages 1-10, then 11-20)
3. Extract for each reviewer:
   - Reviewer identifier (name, number, or anonymous ID)
   - Recommendation / score (if provided)
   - Whether revision is allowed
   - General assessment text
   - Individual comments (each as a separate item)

### Phase 3: Generate Individual Review Markdown Files

Create one markdown file per reviewer in `reviews/`:

1. Create the `reviews/` subdirectory
2. For each reviewer, write `reviews/reviewer-{n}.md` containing:
   - **Header:** reviewer identifier, recommendation/score, whether revision is allowed
   - **General Assessment:** full verbatim text of the reviewer's overall assessment
   - **Individual Comments:** each comment as a numbered item with its assigned ID (`R{n}-C{m}`), verbatim text, and section/page reference if mentioned
3. Use this template for each file:

```markdown
# Reviewer {N}

**Recommendation:** {recommendation or score}
**Revision allowed:** {Yes / No / Not stated}

## General Assessment

{verbatim general assessment text}

## Comments

### R{N}-C1 {optional: section/page reference}

{verbatim comment text}

### R{N}-C2 ...

{verbatim comment text}
```

4. If files already exist in `reviews/`, follow the same versioning convention as other outputs (flag and version)

### Phase 4: Generate LaTeX Verbatim Transcription

Using the template from `templates/referee-comments/reviewer-comments-verbatim.tex`:

1. Create one `\section{}` per reviewer with comment count and recommendation
2. Place general assessment in a `genbox` environment
3. For each specific comment:
   - Assign an ID: `R{reviewer}-C{comment}` (sequential within each reviewer)
   - Identify the section/page reference if the reviewer mentions one
   - Place the full verbatim text in the comment table
4. If a single reviewer paragraph contains multiple distinct concerns, split into separate IDs and add a `\textit{\footnotesize Split: ...}` note
5. If any IDs are derived (split from a larger comment or inferred), add them to a Derived IDs appendix section
6. Compile with `latexmk` to verify it builds cleanly

### Phase 5: Generate Comment Tracker

Using the template from `templates/referee-comments/comment-tracker.md`:

1. Fill in the Triage Summary table
2. Populate the Comment Matrix — one row per atomic comment:
   - **ID:** matching the LaTeX verbatim IDs
   - **Reviewer:** reviewer number
   - **Comment:** short verbatim quote (first ~100 chars in quotes)
   - **Type:** classify as Major / Minor / Editorial / Question / Praise
   - **R&R Classification:** classify as NEW ANALYSIS / CLARIFICATION / DISAGREE / MINOR (see `references/rr-routing.md` for decision rules and signal words)
   - **Priority:** assign Critical / High / Medium / Low based on:
     - Critical = threatens acceptance if not addressed
     - High = significant concern, must address
     - Medium = reasonable concern, should address
     - Low = minor or editorial
   - **Action:** leave blank (for the user to fill)
   - **Owner:** leave blank
   - **Status:** set all to "Pending"
   - **Section:** paper section referenced, if identifiable
3. Fill in the Status Dashboard counts
4. Generate a **Routing Summary** table grouping comments by R&R classification:
   - NEW ANALYSIS: list IDs + brief description of required analysis
   - CLARIFICATION: list IDs + target sections needing revision
   - DISAGREE: list IDs + flag for user review
   - MINOR: list IDs
5. Identify **Cross-Cutting Themes** — concerns raised by 2+ reviewers, tagged T1, T2, etc.
6. Leave Evidence Log, Patch Plan, Response Blocks, and Blockers empty (user fills during revision)

### Phase 6: Generate Review Analysis

Using the template from `templates/referee-comments/review-analysis.md`:

1. Fill in Scores & Recommendations table
2. Write a Reviewer Profile for each reviewer:
   - **Posture:** hostile / sceptical / constructive / supportive (infer from tone)
   - **What they liked:** bullet points
   - **What they want revised:** numbered list
   - **Assessment:** paragraph on how addressable their concerns are
   - **Risk:** None / Low / Medium / High with explanation
3. Identify Cross-Cutting Themes — concerns that appear across 2+ reviewers, tagged T1, T2, etc.
4. Estimate Acceptance Probability with factors for/against
5. Bucket comments into Priority 1/2/3 response categories
6. List Vulnerabilities (weaknesses in the paper that reviewers exposed)
7. Populate the Publication Strategy section:
   - **Strategy A (minimal revision):** venues that would accept the paper's strengths as-is, despite the weaknesses reviewers identified. Look for venues that value the descriptive/empirical contribution without demanding the specific improvements the current reviewers want.
   - **Strategy B (substantial revision):** venues worth targeting if the authors invest effort to address the major reviewer concerns. These should be equal or higher prestige than the current venue.
   - For conferences: check CORE rankings via `.context/resources/venue-rankings.md` (and the CSV at `.context/resources/venue-rankings/core_2026.csv`). Note upcoming deadlines.
   - For journals: check CABS AJG rankings via `.context/resources/venue-rankings.md` (and the CSV at `.context/resources/venue-rankings/abs_ajg_2024.csv`). For SJR score, query the Elsevier Serial Title API (see venue-rankings.md for snippet; requires `SCOPUS_API_KEY`). Flag journals below CABS 3 only if there's a strong fit rationale.
   - **Recommendation table:** rank 3-5 venues in priority order with rationale. First option should always be "revise for current venue" if acceptance probability is above ~30%.
   - **Key Decision:** frame the core trade-off the authors face (e.g., speed vs. impact, minimal vs. substantial revision effort).
   - Consider the paper's discipline and methodology when suggesting venues — a qualitative policy analysis fits different outlets than a computational study.
8. Leave Timeline empty (user fills)

### Phase 6.5: Strategic Coaching (Interactive)

For each **Major** or **Critical** comment, walk the user through a structured deliberation:

1. **Understanding:** "What is this reviewer's core concern — methodology, theory, or framing?"
2. **Position:** Classify as one of:
   - **Agree** — will revise as suggested
   - **Partially agree** — will address the spirit but not the exact suggestion. State which parts you accept and which you push back on.
   - **Disagree** — will rebut with evidence. Draft the core rebuttal argument.
3. **Risk assessment:** "If you push back on this, how likely is the reviewer to escalate? Is it worth the risk?"
4. **Response sketch:** One-sentence draft of the response direction (not the full response — just the strategy).

Record these in the Comment Matrix by adding two columns after `R&R Classification`:
- **Position:** Agree / Partially / Disagree
- **Strategy:** one-line response direction

**Rules:**
- Only Major and Critical comments get coaching. Minor/Editorial are auto-classified as "Agree" with no coaching.
- the user can say "skip coaching" to bypass and classify all remaining as Agree.
- Maximum 2 rounds of dialogue per comment — do not over-discuss.
- Do not write the actual response letter — that remains the user's job.

### Phase 7: Summary & Review

Present to the user:
- Total comments extracted (by reviewer)
- Breakdown by type and priority
- Key cross-cutting themes
- Position summary: N Agree / N Partially / N Disagree
- Any comments that were ambiguous or hard to classify
- Ask for corrections before finalising

## Critical Rules

1. **Verbatim means verbatim.** Never paraphrase reviewer text in the LaTeX transcription. Copy exactly.
2. **Every comment gets an ID.** No reviewer concern should be lost. If in doubt, give it its own ID.
3. **Don't write actions.** The Comment Matrix `Action` column stays blank — that's the user's job.
4. **Don't overwrite.** If files already exist at the target location, flag and version.
5. **Compile the LaTeX.** The verbatim document must build without errors before the skill completes.

## Templates

Located in `templates/referee-comments/`:
- `comment-tracker.md`
- `review-analysis.md`
- `reviewer-comments-verbatim.tex`

## Cross-References

- `/proofread` — for proofreading the response letter before submission
- `/bib-validate` — run after revision to check bibliography
- `/pre-submission-report` — full quality check before resubmission
- `paper-critic` agent — for self-review of the revised paper
- `references/rr-routing.md` — R&R classification system and routing logic for revision workflow


---

## project-deck

**Source:** `skills/project-deck/SKILL.md`

---
name: project-deck
description: "Use when you need to create a presentation deck to communicate project status."
allowed-tools: Bash(latexmk*), Bash(xelatex*), Bash(pdflatex*), Bash(mkdir*), Read, Write, Edit
argument-hint: [project-name-or-path]
---

# Project Deck Skill

> Create beautiful presentation decks to communicate project status to your future self and collaborators.

## Purpose

Based on Scott Cunningham's Part 7: "Making Beautiful Decks For My Future Self" - using decks not for public speaking but to efficiently communicate work status across time and to coauthors.

## The Philosophy

"I use decks to help me keep track of the work I was doing so that I can communicate it to my coauthors and myself later in the week when we meet to go over our projects."

Claude has absorbed the "rhetoric of decks" - the tacit knowledge about what makes presentations effective:
- One idea per slide
- Titles are assertions, not labels
- Lead with conclusions
- Visual hierarchy signals importance
- Repeat for retention
- Transition explicitly

## When to Use

- Before a supervisor meeting
- At the end of a research sprint
- When handing off to a coauthor
- When returning to a dormant project
- Weekly project status updates

## Workflow

1. **Read project context** - Progress logs, current focus, recent work
2. **Design deck structure**:
   - Research question
   - What's been done (with figures/tables)
   - Key findings so far
   - Current blockers
   - Next steps
3. **Create beautiful output** - Clean design, good typography, optimal cognitive density
4. **Include visuals** - Figures, tables, diagrams that capture the work

## Deck Rhetoric Principles

```markdown
## Principles for Effective Decks

1. **One idea per slide** - Don't overload
2. **Titles are assertions** - "Distance increases abortion rates" not "Results"
3. **Lead with conclusions** - Don't bury the lede
4. **Visual hierarchy** - Most important things stand out
5. **Optimal cognitive density** - Smooth delivery, not overloaded
6. **Beautiful figures and tables** - Data visualisation matters
7. **Explicit transitions** - Guide the reader through the narrative
```

## Extended Rhetoric Principles

### For Research Decks
- **Motivation slides**: Why should anyone care? What's the gap?
- **Methods slides**: Identification strategy in plain English, visualize variation
- **Results slides**: Lead with main coefficient, visualize where possible
- **Figures**: Clear titles, labeled axes, no chartjunk

### For "Decks as Thinking Tools"
When making decks for yourself/coauthors:
1. **Document decisions** — Why did we choose this approach?
2. **Visualize data** — Patterns you've discovered
3. **Track progress** — What's done, what's next
4. **Summarize code** — What scripts do what
5. **Capture context** — So future-you remembers

### Beamer Tips
- Custom themes > recognizable templates
- Metropolis or Madrid themes as starting points
- Sans-serif fonts for readability
- Generous margins and whitespace
- Compile without warnings (fix overfull hboxes)

## Example Prompt

"Create a project deck for my Indifference Adjustments paper. Read my progress logs and the current state of the project, then make a 10-slide deck that I can use in my supervisor meeting next week. Include the key figures and a clear 'what's next' section."


---

## project-safety

**Source:** `skills/project-safety/SKILL.md`

---
name: project-safety
description: "Use when you need to set up safety rules and folder structures for a research project."
argument-hint: [project-path]
---

# Project Safety Skill

**CRITICAL RULE: Never delete data or code files. Never.** Use legacy/ folder for originals. Copy, don't move.

> Establish safety rules and structures before Claude makes changes to research projects.

## Purpose

Based on Scott Cunningham's workflow: prevent accidental data loss by establishing rules and using legacy folders before Claude reorganizes or modifies project files.

## When to Use

- Starting a new research project folder
- Before asking Claude to reorganize files
- When Claude will be running code or modifying data
- Setting up a project for collaborative work

---

## Safety Rules Template

Add this to any project's CLAUDE.md file:

```markdown
## Safety Rules

1. **Never delete data files** — No .csv, .dta, .xlsx, .parquet, or any data format
2. **Never delete code files** — No .py, .R, .do, .tex, .md or scripts
3. **Use legacy/ folder** — If reorganizing, move originals to legacy/ first
4. **Copy from legacy, don't move** — Always preserve the original

### If you need to reorganize:
1. Create a legacy/ folder if it doesn't exist
2. Move ALL original files into legacy/
3. Copy (not move) needed files into new structure
4. Never modify anything in legacy/
```

---

## Directory Structure

After safety setup:

```
project/
├── CLAUDE.md           ← Safety rules + project context
├── README.md           ← Project documentation
├── legacy/             ← PROTECTED: original files
│   └── [all originals]
├── code/
│   ├── R/
│   ├── python/
│   └── stata/
├── data/
│   ├── raw/            ← Copied from legacy, never modified
│   └── processed/
├── output/
│   ├── figures/
│   └── tables/
├── docs/
│   └── manuscript/
└── log/                ← Progress logs
```

---

## Dry Run Pattern

Before Claude executes potentially destructive operations, ask for a preview:

> "Tell me what commands you would run to reorganize this folder, but don't execute them yet."

> "Show me what files would be affected by this change before you make it."

> "Walk me through your plan for cleaning this data before you run any code."

**When to use dry runs:**
- File operations (move, delete, rename)
- Git operations (reset, clean, force push)
- Database operations
- Batch processing
- Any operation affecting multiple files

**After reviewing:**
- If correct: "Go ahead"
- If wrong: "Wait — don't do X, instead Y"

---

## Workflow

1. **Create CLAUDE.md** with safety rules
2. **Create legacy/ folder**
3. **Move all originals to legacy/**
4. **Copy needed files** into new structure
5. **Verify** legacy/ contains everything
6. **Proceed** with project work

---

## Prompt Template

```
I'm starting work on [PROJECT]. Before we do anything:

1. Create a CLAUDE.md with safety rules (never delete data/code, use legacy folder)
2. Create a legacy/ folder
3. Move all existing files into legacy/
4. Show me the proposed new directory structure before creating it

Do a dry run first — tell me what you would do before doing it.
```

---

## Why This Matters

- Claude operates at speed — mistakes happen fast
- You can't always verify what Claude will do before it does it
- Version control (git, Dropbox) helps but prevention is better
- The legacy/ folder is your safety net
- Dry runs give you a chance to catch mistakes

---

## Example Use

"Set up my new Carbon Markets project with proper safety rules. Create the CLAUDE.md, legacy folder, and recommended directory structure. Show me your plan before executing."


---

## proofread

**Source:** `skills/proofread/SKILL.md`

---
name: proofread
description: "Use when you need academic proofreading of a LaTeX paper (11 check categories)."
allowed-tools: Read, Glob, Grep
argument-hint: [project-path or tex-file]
---

# Academic Proofreading

**Report-only skill.** Never edit source files — produce `reviews/proofread/<YYYY-MM-DD-HHMM>.md` only.

## Output Path

Per `rules/review-artefact-routing.md` (auto-loads in research projects (path-scoped to `paper-*/` and `paper/`)):

- **Source slug:** `proofread`
- **Write reports to:** `reviews/proofread/YYYY-MM-DD.md` inside the project. Path is relative to the research project root, not the Task-Management repo.
- **Never** at project root (`./CRITIC-REPORT.md`-style filenames are forbidden — pre-rule layout).
- **Idempotency:** if today's file exists, append a same-day descriptor (`{date}-revision.md`, `{date}-r2.md`, `{date}-pre-submission.md`) — never overwrite.
- **Index update:** if `reviews/INDEX.md` exists, write a one-line entry under "Latest per source" pointing at the new file. Otherwise `/review-recap` will rebuild the index next time it runs.
- **Infrastructure repos** (Task-Management, atlas-workspace, etc.): this section does not apply — the path-scoped rule won't load there.


## When to Use

- Before sending a draft to supervisors
- Before submission to a journal/conference
- After major revisions to check consistency
- When you want a fresh-eyes check on writing quality

## When NOT to Use

- **Formal audits** — use the Referee 2 agent for systematic verification
- **Argument quality** — use `/devils-advocate` for logical scrutiny
- **Citation completeness** — use `/bib-validate` for bibliography cross-referencing (though this skill flags obvious citation format issues)

## Workflow

1. **Locate files**: Find all `.tex` files in the project (and `.log` files for LaTeX diagnostics)
2. **Read the document**: Read all `.tex` source files in order
3. **Run 11 check categories** (below)
4. **Produce report**: Write `reviews/proofread/<YYYY-MM-DD-HHMM>.md` under the project directory (create the directory if it does not exist: `mkdir -p reviews/proofread/`). Do NOT overwrite previous reports — each review is timestamped to the minute. Canonical convention: `~/Task-Management/docs/reference/review-state-schema.md`.

## Check Categories

### 1. Grammar & Spelling

- Spelling errors (including technical terms)
- Subject-verb agreement
- Sentence fragments or run-ons
- Misused words (e.g., "effect" vs "affect", "which" vs "that")
- American English is the default for all papers and conference articles. Flag any British English spellings (e.g., -ise, -our, -re, analyse, scepticism).

### 2. Notation Consistency

- Variable notation used consistently throughout (e.g., always `$x_i$` or always `$x_{i}$`, not both)
- Subscript/superscript style (e.g., `$\beta_1$` vs `$\beta_{OLS}$`)
- Matrix/vector formatting conventions (bold, uppercase, etc.)
- Consistent use of `\mathbb`, `\mathcal`, `\mathbf` for sets, operators, vectors
- Equation numbering: all referenced equations numbered, unreferenced ones unnumbered

### 3. Citation Format

- Consistent use of `\citet` (textual) vs `\citep` (parenthetical)
- No raw `\cite{}` when `\citet`/`\citep` is available
- Author name spelling matches between text mentions and citation keys
- Multiple citations in chronological or alphabetical order (check which convention)
- No "As shown by (Author, Year)" — should be "As shown by \citet{key}"

### 4. Academic Tone

- No informal contractions (don't, can't, won't → do not, cannot, will not)
- No first-person overuse (some "we" is fine; excessive "I think" is not)
- No casual hedging ("pretty much", "kind of", "a lot")
- Appropriate use of hedging language ("suggests" vs "proves")
- No exclamation marks in body text
- Consistent tense (present for established facts, past for specific studies)
- **Filler hedge phrases to flag** (delete on sight): "interestingly", "importantly", "it is worth noting", "it should be noted that", "needless to say", "of course", "obviously", "clearly" (unless something is literally clear from a figure)
- **Vague quantifiers to flag**: "very", "quite", "rather", "somewhat", "fairly" — replace with specific magnitudes or delete
- **Tautological constructions**: "significant and important", "novel and new", "unique and distinctive" — one adjective suffices

### 5. LaTeX-Specific Issues

- **Overfull hbox**: Check `.log` file for `Overfull \hbox` warnings — report line numbers and severity (badness)
- **Equation overflow**: Long equations that exceed column/page width
- **Float placement**: Check for `[h!]` or `[H]` overuse; prefer `[tbp]`
- **Missing labels**: Figures/tables/equations referenced but without `\label{}`
- **Orphan/widow lines**: Check for `\\` abuse that creates bad page breaks
- **Unresolved references**: `??` in output indicating broken `\ref{}` or `\cite{}`

### 6. Citation Voice Balance

Check the ratio of in-line (`\citet`) to parenthetical (`\citep`) citations:

- **Count in-line vs parenthetical citations** across the full document
- **Flag if ratio exceeds 1:1** (in-line should be the minority) — Major
- **Flag runs of 3+ consecutive in-line citations** in a paragraph or section — Major
- **Flag paragraphs that open with an in-line citation** when the author's identity isn't the point — Minor
- **Flag "As shown by \citet{}" patterns** where parenthetical would be more natural — Minor
- **Report the overall ratio** (e.g., "42 parenthetical, 28 in-line — ratio 1.5:1")

See `docs/reference/conventions.md` § Citation Voice Balance for the full convention.

### 7. TikZ Diagram Review

If the document contains TikZ code (`\begin{tikzpicture}` or `\tikz`):

- **Label positioning**: Labels not overlapping nodes or edges
- **Geometric accuracy**: Coordinates and angles consistent with intended layout
- **Visual semantics**: Arrow styles match meaning (solid = direct, dashed = indirect, etc.)
- **Spacing**: Nodes not too cramped or too spread out
- **Consistency**: Style matches across all diagrams in the document
- **Standalone compilability**: Each diagram should compile independently

For detailed spatial verification (Bezier depth calculations, gap minimums, shape boundary clearance), see [`../shared/tikz-rules.md`](../shared/tikz-rules.md).

### 8. Numeric Text↔Table Cross-Check

Cross-check every number mentioned in the prose against the corresponding table or figure. Flag ANY discrepancy, no matter how small.

- **Coefficient claims**: "a 3.2 percentage point increase" in text vs coefficient of 0.031 in the table — flag the mismatch
- **Sample sizes**: "N = 1,247" in text vs N row in table — must match exactly
- **Significance claims**: "statistically significant at the 5% level" in text vs the actual stars/p-value in the table
- **Summary statistics**: means, medians, standard deviations mentioned in prose must match the descriptive statistics table
- **Figure references**: claims about trends or magnitudes must be consistent with what the figure shows
- **Table/figure existence**: every table/figure referenced in text must exist; every table/figure in the document must be referenced in text
- **N consistency**: the number of observations should be consistent across related specifications unless there's an explained reason for differences

### 9. Causal Language Audit

Audit causal claims against the stated identification strategy. The strength of causal language must match the strength of the research design.

- **Flag "X causes Y"** or "the causal effect of X" when the identification strategy is observational (OLS with controls, correlational) — should be "is associated with" or "predicts"
- **Flag "proves"** — almost never appropriate; use "provides evidence consistent with"
- **Match language to design**:
  - DiD/RDD/IV → "we estimate the causal effect" is acceptable with qualifiers
  - OLS with controls → "we find a relationship" or "our estimates suggest"
  - Correlational → never use causal language
- **Flag "significant" ambiguity** — must always be clear whether "statistically significant" or "economically meaningful/large"
- **Flag coefficient descriptions without units or scale** — "a coefficient of 0.031" means nothing without knowing the units of X and Y
- **Flag correlation/causation conflation** — any statement that slides from an association to a causal claim without an identification argument

### 10. Equation Completeness

Verify that mathematical notation is complete and internally consistent.

- **Every variable in an equation must be defined** in the text (either before or immediately after the equation)
- **Error terms**: properly specified (ε_it vs u_i vs e_ij) and consistent with the econometric framework described
- **Equation numbering**: sequential, and all cross-references to equations are correct
- **Subscript/index structure must match the level of observation** — e.g., if the text describes individual-level variation, the equation should have individual subscripts, not county-level
- **Summation/expectation indices**: verify bounds match the described sample
- **Consistent notation across equations**: don't switch between β and b for the same coefficient, or between X_i and x_i

### 11a. Anonymity (double-blind venues only)

If the project's vault submission frontmatter or CLAUDE.md indicates a double-blind venue (CCS, NDSS, S&P, USENIX, ICML, NeurIPS, ICLR, FAccT, AAAI, etc.), run paper-side checks P1–P8 from `~/.claude/skills/_shared/double-blind-anonymity-checklist.md` and flag every FAIL as **Critical**:

- **P1** title page anonymized (no `\author{}` with real names)
- **P2** no `\thanks{}`, `\acknowledgements`, funding, or grant references in body
- **P3** body uses third-person self-reference (no "we previously showed", "in our prior work")
- **P4** **self-citation bib entries are blinded** when the cited paper's authors overlap the submission's — this is the CCS 2026 #1328 desk-reject trigger
- **P5** body text doesn't name authors of self-cited works (no "Burnat and [Collaborator] [N]")
- **P6** no identifying URLs (personal websites, GitHub repos with handles)
- **P7** PDF metadata clean (`pdfinfo` shows no Author / identifying Subject)
- **P8** figures/screenshots have no identifying watermarks

Skip this section only when the user explicitly says single-blind / non-blind.

### 11. Preprint Staleness

For every citation that looks like a preprint or working paper, check whether a peer-reviewed version has since been published. Flag stale preprints as Major issues.

- **Detection signals**: URL contains `arxiv.org`, `ssrn.com`, `nber.org`; journal field says "Working Paper", "mimeo"; entry type is `@techreport` or `@unpublished`
- **Action**: note the stale citation and suggest the published venue/year
- **This is a lighter version of `/bib-validate`'s preprint check** — only flag obvious cases visible from the `.bib` or `\bibitem` entries. For thorough preprint checking, recommend running `/bib-validate` separately.

## Severity Levels

| Level | Definition | Example |
|-------|-----------|---------|
| **Critical** | Will be noticed by reviewers, may cause rejection | Broken references, major grammar errors, inconsistent core notation, text↔table number mismatch, causal overclaiming with weak design |
| **Major** | Noticeable quality issue | Inconsistent citation style, tone issues, overfull hbox > 10pt, undefined variable in equation, stale preprint, ambiguous "significant" |
| **Minor** | Polish issue | Occasional British/American mix, minor spacing, missing equation number for referenced equation |

## Quality Scoring

Apply numeric quality scoring using the shared framework and skill-specific rubric:

- **Framework:** [`../shared/quality-scoring.md`](../shared/quality-scoring.md) — severity tiers, thresholds, verdict rules
- **Rubric:** [`references/quality-rubric.md`](references/quality-rubric.md) — issue-to-deduction mappings for this skill

Start at 100, deduct per issue found, apply verdict. Insert the Score Block into the report after the summary table.

## Recurring Pattern Grouping

When the same issue appears 3+ times, **group it as a single pattern finding** instead of listing each instance separately. This prevents reports bloated with 50 individual items when the real message is "you have 3 recurring problems."

**Format:**
```
### M3: Hedge phrase "interestingly" (8 instances)
- **Category:** Academic tone
- **Locations:** lines 42, 67, 103, 145, 189, 203, 267, 301
- **Problem:** Filler hedge phrase adds no content
- **Fix:** Delete all 8 instances
```

One deduction for the pattern (not 8 separate deductions). Escalation still applies: 5+ instances of the same minor issue → one Major deduction.

## Report Format

```markdown
# Proofread Report

**Document:** [filename]
**Date:** YYYY-MM-DD
**Pages:** [approximate]

## Summary

| Category | Critical | Major | Minor |
|----------|----------|-------|-------|
| Grammar & spelling | 0 | 0 | 0 |
| Notation consistency | 0 | 0 | 0 |
| Citation format | 0 | 0 | 0 |
| Academic tone | 0 | 0 | 0 |
| LaTeX-specific | 0 | 0 | 0 |
| Citation voice balance | 0 | 0 | 0 |
| TikZ diagrams | 0 | 0 | 0 |
| Numeric cross-check | 0 | 0 | 0 |
| Causal language | 0 | 0 | 0 |
| Equation completeness | 0 | 0 | 0 |
| Preprint staleness | 0 | 0 | 0 |
| **Total** | **0** | **0** | **0** |

## Critical Issues

[List each with file, line/section, and specific issue]

## Major Issues

[List each with file, line/section, and specific issue]

## Minor Issues

[List each with file, line/section, and specific issue]

## Quality Score

| Metric | Value |
|--------|-------|
| **Score** | XX / 100 |
| **Verdict** | Ship / Ship with notes / Revise / Revise (major) / Blocked |

### Deductions

| # | Issue | Tier | Deduction | Category |
|---|-------|------|-----------|----------|
| 1 | [description] | [tier] | -X | [category] |
| | **Total deductions** | | **-XX** | |

## Recommendations

[Optional: overall observations about the writing — prioritise fixes by deduction size]
```

## Council Mode (Optional)

For high-stakes pre-submission checks, run proofreading in council mode to get independent assessments from multiple LLM providers. Council mode surfaces formatting issues that any single model might miss.

**Trigger:** "Council proofread my paper" or "thorough proofread"

**How it works:**
1. The main session reads the document and constructs the proofreading prompt
2. The prompt is sent to 3 different models via `council-cli` (or `council-api` for API mode)
3. Each model independently runs the 7 check categories
4. Cross-review identifies agreements and disputes
5. Chairman synthesis produces a single `PROOFREAD-REPORT.md` with council notes

**Invocation (CLI backend — free with existing subscriptions):**
```bash
cd packages/council-cli
uv run python -m council_cli \
    --prompt-file /tmp/proofread-prompt.txt \
    --context-file /tmp/paper-content.txt \
    --output-md /tmp/proofread-council.md \
    --chairman claude \
    --timeout 180
```

See `skills/shared/council-protocol.md` for the full orchestration protocol.

**Value:** Diminishing returns for pure formatting — council mode is most valuable when combined with citation voice balance and notation consistency checks, where different models have genuinely different pattern recognition.

## Log to REVIEW-STATE.md (final step)

After writing the proofread report, append a row to the project's `REVIEW-STATE.md`:

```bash
bash ~/.claude/skills/_shared/review-state-log.sh \
  --check proofread \
  --paper "<paper-{venue} dir>" \
  --verdict "<PASS|ISSUES FOUND>" \
  --open-issues "<total-issues-across-categories>/<total-issues-across-categories>" \
  --report "reviews/proofread/<YYYY-MM-DD-HHMM>.md" \
  --notes "<one-line: e.g. '3 critical, 12 minor; mostly notation §3'>" \
  [--trigger "pre-submission-report|review-cluster"]
```

- Verdict: PASS if no issues found across any category; ISSUES FOUND otherwise.
- Open issues: total count across all 7 (or 11) check categories at run time.
- Trigger: pass orchestrator name only if invoked via `/pre-submission-report` or `/review-cluster`. Otherwise omit.

Schema: `~/Task-Management/docs/reference/review-state-schema.md`.

## Cross-References

- **`/bib-validate`** — For thorough bibliography cross-referencing
- **`/latex`** — For compilation and error resolution (run before proofreading to ensure the document compiles cleanly)
- **Referee 2 agent** — For formal code + paper auditing
- **`/devils-advocate`** — For argument quality and logical scrutiny


---

## python-env

**Source:** `skills/python-env/SKILL.md`

---
name: python-env
description: "Use when you need Python environment management with uv (install, create venv, manage deps)."
allowed-tools: Bash(uv*), Bash(python*), Bash(mkdir*), Bash(ls*)
---

# Python Environment Management

**CRITICAL RULE: Never use `pip` directly. Always use `uv`.** This applies to all Python package management.

## Golden Rule

**ALWAYS use `uv` for Python package and environment management. Never use `pip` directly.**

## Commands

| Task | Command |
|------|---------|
| Create venv | `uv venv` |
| Install package | `uv pip install <package>` |
| Install from requirements | `uv pip install -r requirements.txt` |
| Run script in project | `uv run python script.py` |
| Run with dependencies | `uv run --with pandas python script.py` |
| Install CLI tool globally | `uv tool install <tool>` |
| Sync project deps | `uv sync` |
| Add dependency | `uv add <package>` |

## Project Setup

For new projects:
```bash
uv init
uv add <dependencies>
uv sync
```

For existing projects with `pyproject.toml`:
```bash
uv sync
uv run python main.py
```

## Rules

1. **Never use `pip install`** — always `uv pip install` or `uv add`
2. **Never install globally** — use `uv tool install` for CLI tools
3. **Always work in a venv** — created by `uv venv` or `uv sync`
4. **Use `uv run`** — to execute scripts within the project environment

## This Project

The Task Management system uses uv:
```bash
cd "Task Management"
uv sync                           # Install dependencies
uv run python .scripts/tasks      # Run CLI tools
```

## On your HPC cluster HPC

Avon uses **Miniconda3 + Lmod** (not uv) because cluster users need to compose with `module load CUDA/12.6.0` and other pre-built modules. The project-specific pattern is `hpc/env-setup.sh` (conda create + pip install) — see [`docs/guides/hpc.md`](../../docs/guides/hpc.md) and reference implementations under `Projects/[your-project]/hpc/env-setup.sh`. The local dev env still uses uv; HPC gets its own conda env with identical pins. Don't try to port uv to Avon — the module system assumes conda.


---

## quarto-deck

**Source:** `skills/quarto-deck/SKILL.md`

---
name: quarto-deck
description: "Use when you need to generate a Reveal.js HTML presentation from Markdown."
allowed-tools: Bash(reveal-md*), Bash(npx*), Bash(mkdir*), Bash(ls*), Bash(cp*), Bash(open*), Bash(R*), Bash(Rscript*), Bash(python*), Read, Write, Edit, Task
argument-hint: [topic, content-path, or project-name]
---

# Reveal.js Deck Skill

> Generate HTML presentations from Markdown using reveal-md. Applies the same rhetoric framework as `/beamer-deck` but outputs browser-native slides ideal for teaching, informal talks, and web sharing.

## Purpose

Create polished Reveal.js presentations from Markdown files. Every deck gets assertion-driven titles, narrative arc, and rhetoric review. Output is an HTML presentation that runs in any browser — no LaTeX needed.

**Use this for:** Teaching, informal research talks, web-shareable presentations, interactive demos.
**Use `/beamer-deck` for:** Conference talks, formal seminars, supervisor meetings, anything that needs PDF-native output.

## When to Use

- Teaching lectures (undergraduate or PhD) — interactive, live in browser
- Informal research presentations or lab meetings
- Talks where you want to share a URL instead of a PDF
- Presentations with live code demos or embedded content
- Quick decks where LaTeX overhead isn't justified

**Python:** Always use `uv run python`. Never bare `python`, `python3`, `pip`, or `pip3`.

## Prerequisites

- `reveal-md` (installed globally): `npm install -g reveal-md`
- Node.js 18+ (via nvm)

---

## Critical Rules

0. **Python: ALWAYS use `uv run python` or `uv pip install`.** Never use bare `python`, `python3`, `pip`, or `pip3`. Include this instruction in any sub-agent prompts that may run Python.
1. **One Markdown file = one presentation.** All slides live in a single `.md` file with `---` separators.
2. **Titles are assertions, not labels.** "Distance increases abortion rates" — not "Results". Every slide title states a claim.
3. **One idea per slide.** Not a guideline. A law. If a slide has two ideas, split it.
4. **Speaker notes use the `Note:` keyword.** Place after slide content, before the next `---`.
5. **Custom CSS goes in a separate file.** Never inline styles in the Markdown.
6. **Figures first, slides second.** Generate figures via R or Python scripts before referencing them.
7. **Test in browser before finalising.** Run `reveal-md <file>.md` and check every slide.

---

## Rhetoric Principles

Same framework as `/beamer-deck`. Full reference (Three Laws, MB/MC, Aristotelian Triad, Narrative Arc, Pyramid Principle, Devil's Advocate, audience-specific guidance): [`../shared/rhetoric-principles.md`](../shared/rhetoric-principles.md)

---

## Quality Scoring

Apply numeric quality scoring using the shared framework and skill-specific rubric:

- **Framework:** [`../shared/quality-scoring.md`](../shared/quality-scoring.md) — severity tiers, thresholds, verdict rules
- **Rubric:** [`references/quality-rubric.md`](references/quality-rubric.md) — issue-to-deduction mappings for this skill

Start at 100, deduct per issue found, apply verdict. Compute the score in Phase 6 and report it in the final output.

## Reveal.js Markdown Format

Full format reference with basic structure, vertical slides, fragments, custom themes, and CSS examples: [`references/markdown-format.md`](references/markdown-format.md)

**Reference palettes** (Professional, Energetic, Academic) with both LaTeX and CSS variants: [`../shared/palettes.md`](../shared/palettes.md)

---

## Workflow: 6 Phases

```
You (orchestrator)
├── Phase 1: Gather context        (direct)
├── Phase 2: Design structure       (direct)
├── Phase 3: Build deck             (direct)
├── Phase 4: Preview & fix          (direct)
├── Phase 5: Rhetoric review        (sub-agent — Explore)
└── Phase 6: Apply & finalise       (direct)
```

### Phase 1: Gather Context (Direct)

Read project files, content sources, and audience brief. Ask the user:

- **Audience**: Teaching? Lab meeting? Informal talk?
- **Duration**: How long?
- **Content source**: Paper draft? Notes? Existing slides?
- **Special requirements**: Code demos? Interactive elements? Specific theme?
- **Export needs**: Browser only, or also need static HTML/PDF?

### Phase 2: Design Structure (Direct)

1. **Choose rhetoric balance** based on audience
2. **Outline slide sequence** with assertion titles
3. **Plan narrative arc** — identify Act I/II/III transitions
4. **Choose colour palette** — create `custom.css`
5. **Identify figures needed** — which need code generation?

Present outline to the user for approval.

### Phase 3: Build Deck (Direct)

1. **Generate figures first** — R/Python scripts, save to `figures/`
2. **Write the `.md` file** with YAML frontmatter and slide content
3. **Write `custom.css`** if custom theming is needed
4. **Test locally**: `reveal-md deck.md`
5. **Add speaker notes** using `Note:` blocks

### Phase 4: Preview and Fix (Direct)

1. Run `reveal-md deck.md` to preview in browser
2. Check every slide for:
   - Text overflow or cramped content
   - Figure sizing and alignment
   - Math rendering (MathJax)
   - Code highlighting
   - Transitions between slides
3. Fix issues and re-preview

### Phase 5: Rhetoric Review (Sub-Agent — Explore)

Launch the same rhetoric review as `/beamer-deck`, adapted for Markdown:

```
subagent_type: Explore
prompt: |
  You are a rhetoric reviewer for an academic Reveal.js presentation.

  Read the file at: [PATH TO .md FILE]

  Evaluate against these criteria:

  ## 1. Narrative Arc
  - Three-act structure (Problem → Investigation → Resolution)?
  - Opening: provocative question, statistic, or bold claim?
  - Closing: single memorable takeaway?

  ## 2. MB/MC Balance
  - Cognitive load distributed smoothly?
  - Overloaded or underloaded slides?

  ## 3. Title Quality
  - Every title an assertion (a claim), not a label?

  ## 4. One Idea Per Slide
  - Any slide trying to convey multiple ideas?

  ## 5. Transitions
  - Are transitions between slides explicit?
  - Does the audience know where they are in the argument?

  ## 6. Pyramid Principle
  - Conclusions before support?

  Return structured markdown with ratings and specific slide suggestions.
```

### Phase 6: Apply and Finalise (Direct)

1. Incorporate rhetoric review feedback
2. Re-preview in browser
3. **Compute quality score** — read `references/quality-rubric.md`, log all issues from Phases 4-5, compute score and verdict
4. **Export if needed:**
   - Static HTML: `reveal-md deck.md --static _site`
   - PDF: `reveal-md deck.md --print deck.pdf`
5. Confirm all files are in place

---

## Commands Reference

| Command | What it does |
|---------|-------------|
| `reveal-md deck.md` | Live preview with hot reload (default port 1948) |
| `reveal-md deck.md --css custom.css` | Preview with custom CSS |
| `reveal-md deck.md --static _site` | Export to static HTML (shareable folder) |
| `reveal-md deck.md --print deck.pdf` | Export to PDF (uses Puppeteer) |
| `reveal-md deck.md --port 3000` | Preview on custom port |
| `reveal-md deck.md --theme moon` | Use built-in theme (moon, night, serif, etc.) |

Press `s` during preview to open **speaker notes view**.
Press `f` for fullscreen. Press `o` for slide overview.

---

## Output Checklist

A completed deck directory should contain:

```
project/
├── deck.md               # Markdown presentation
├── custom.css             # Custom theme (if used)
├── figures/               # Generated figures (if any)
│   ├── figure_1.png
│   └── ...
├── scripts/               # R/Python scripts for figures (if any)
│   ├── figure_1.R
│   └── ...
├── _site/                 # Static HTML export (if generated)
└── deck.pdf               # PDF export (if generated)
```

- [ ] All slide titles are assertions
- [ ] One idea per slide
- [ ] Narrative arc: Problem → Investigation → Resolution
- [ ] Rhetoric review completed (Phase 5)
- [ ] Speaker notes present for key slides
- [ ] Math renders correctly (if used)
- [ ] Tested in browser — no overflow or layout issues
- [ ] Quality score computed and reported

---

## Cross-References

| Skill | When to use instead/alongside |
|-------|-------------------------------|
| `/beamer-deck` | For formal academic presentations (conferences, seminars) that need PDF-native output |
| `/project-deck` | For project status updates (supervisor meetings, coauthor handoffs) |
| `/proofread` | For post-hoc review of text quality |
| `/literature` | For finding and verifying citations to include |
| `/quarto-course` | For full course websites with multiple lectures, exercises, and navigation |


---

## save-context

**Source:** `skills/save-context/SKILL.md`

---
name: save-context
description: "Use when you need to save information from the current conversation to the context library."
allowed-tools: Read, Write, Edit
---

# Save to Context Library

Save information from the current conversation to the user's task management context files for future reference.

## Context Library Location

```
$TM/.context/
```

## Available Context Files

### 1. Profile (`profile.md`)
**Save here:** Personal details, roles, research areas, working style, preferences

**Triggers:**
- "Add this to my profile"
- "Remember that I prefer..."
- "Save my research interests"

**Format:** Update the relevant section, preserving existing content

### 2. Current Focus (`current-focus.md`)
**Save here:** What the user is actively working on, recent progress, next steps

**Triggers:**
- "Update my current focus"
- "I'm now working on..."
- "Save where I left off"

> **Preferred:** For structured end-of-session updates, use `/update-focus` instead. It preserves the full document structure and handles session rotation, open loops, and mental state. Use `/save-context` only for quick, targeted saves (e.g., adding a single note or updating one field). If `/update-focus` is not available, read the file first and merge carefully — never overwrite with a blank template.

**Format:** Read the existing file and update the relevant section. Do not use a template — the file has a rich structure that must be preserved.

### 3. Projects Index (`projects/_index.md`)
**Save here:** Project overviews, paper status, collaborations

**Triggers:**
- "Add this project"
- "Update my journal paper status"
- "Save this research idea"

**Format:** Update the appropriate table or section

### 4. Individual Project Files (`projects/papers/[name].md`)
**Save here:** Detailed notes on specific papers/projects

**Triggers:**
- "Save these notes to my [project] file"
- "Create a project file for [name]"

**Format:** Create new file if doesn't exist:
```markdown
# [Project Name]

## Overview
[Brief description]

## Status
[Current stage]

## Key Decisions
- [Important choices made]

## Notes
[Detailed notes]

## Action Items
- [ ] [Tasks]
```

### 5. People (`people/supervisors.md` or `people/collaborators.md`)
**Save here:** Information about supervisors, collaborators, contacts

**Triggers:**
- "Add [name] to my contacts"
- "Remember that [person] works on..."
- "Save [person]'s details"

**Format:**
```markdown
### [Name]
- **Institution:** [Where they work]
- **Role:** [Their position]
- **Collaboration:** [What you work on together]
- **Contact:** [Email/preferred method]
- **Notes:** [Relevant context]
```

### 6. Preferences (`preferences/`)
**Save here:** Task naming conventions, priority definitions, workflow preferences

**Triggers:**
- "Remember I prefer tasks named like..."
- "Save my priority rules"

### 7. Workflows (`workflows/`)
**Save here:** How the user wants certain processes to work

**Triggers:**
- "Update my daily review workflow"
- "Change how I want meetings processed"

## How to Save

### Step 1: Identify the target file
Based on the information type, determine which context file to update.

### Step 2: Read the existing file
Always read the current content first to preserve existing information.

### Step 3: Merge intelligently
- Don't overwrite existing content unless explicitly asked
- Add new information in the appropriate section
- Update timestamps where relevant

### Step 4: Write the updated file
Save the merged content back to the file.

### Step 5: Confirm
Tell the user what was saved and where:
> "Saved to `.context/[file]`: [brief summary of what was added]"

## Examples

**User:** "Remember that my supervisor is [Supervisor] [Supervisor], he specialises in multi-objective optimisation"

**Action:**
1. Read `.context/people/supervisors.md`
2. Find or create the Supervisor section
3. Update with: Name: [Supervisor] [Supervisor], Focus: Multi-objective optimisation
4. Save file
5. Respond: "Saved to `.context/people/supervisors.md`: Added [Supervisor] [Supervisor] as your supervisor (multi-objective optimisation)"

---

**User:** "Update my current focus - I'm now deep in the journal revision, specifically rewriting section 4"

**Action:**
1. Read `.context/current-focus.md`
2. Update "What I'm Working On" section
3. Add timestamp
4. Save file
5. Respond: "Updated `.context/current-focus.md`: Now working on journal revision, section 4 rewrite"

---

**User:** "Save this meeting summary to my context"

**Action:**
1. Determine if it's project-specific or general
2. If project-specific: save to `projects/papers/[project].md`
3. If general: save key points to `current-focus.md`
4. Extract any action items and offer to create vault tasks

## Integration with vault

After saving to context files, offer to:
- Create related tasks in vault tasks
- Update Research Pipeline if paper-related
- Link context to specific vault files

## Tips

- Always preserve existing content unless asked to replace
- Use timestamps for time-sensitive information
- Keep entries concise but complete
- Cross-reference between files when relevant


---

## session-health

**Source:** `skills/session-health/SKILL.md`

---
name: session-health
description: "Use when you need to check current context status and session health."
allowed-tools:
  - Read
  - Glob
  - Bash(ls*, cat*)
---

# Context Status: Session Health Check

On-demand diagnostic showing context usage, preservation state, and open work items. Fast and lightweight — no vault queries.

## What to Check

### 1. Context Usage Estimate

Read the context monitor state file to get the current tool call count:

```
~/.claude/sessions/{project-hash}/context-monitor-state.json
```

The project hash is a SHA-256 of `CLAUDE_PROJECT_DIR` (first 12 chars). If the state file doesn't exist, report "No context monitor data — hook may not be active."

Calculate:
- Tool calls so far
- Estimated percentage (calls / 150)
- Which thresholds have fired (from the `fired` array)
- Time since last warning

### 2. Active Plan

Find the latest file in `log/plans/`:
- If found: show filename, first 3 lines, and whether it contains "APPROVED" or is still "DRAFT"
- If none: report "No active plan"

### 3. Latest Session Log

Find the latest non-compact `.md` file in `log/` (skip files with `-compact` in the name):
- If found: show filename and first 3 lines
- If none: report "No session log found"

### 4. Focus Freshness

Check when `.context/current-focus.md` was last modified:
- Show the modification date
- If older than 3 days: warn "Focus file is stale — consider running `/update-focus`"
- Show the first 5 lines (headline)

### 5. Preservation Hooks

Verify these hooks are configured in `~/.claude/settings.json`:
- `PreCompact` → `precompact-autosave.py` (pre-compact state save)
- `SessionStart` compact → `postcompact-restore.py` (post-compact restore)
- `PostToolUse` → `context-monitor.py` (this monitor)

For each: report CONFIGURED or MISSING.

### 6. Open Loops

Count unchecked items (`- [ ]`) in `.context/current-focus.md`:
- Report the count
- If > 5: warn "Many open loops — consider triaging"

## Output Format

Present as a compact status panel:

```
## Session Health

| Metric | Value |
|--------|-------|
| Context usage | ~XX% (N/150 tool calls) |
| Thresholds fired | none / info / warning / critical |
| Active plan | filename (DRAFT/APPROVED) / none |
| Latest log | filename / none |
| Focus freshness | N days ago / stale warning |
| Open loops | N items |

### Preservation Hooks

| Hook | Status |
|------|--------|
| PreCompact auto-save | CONFIGURED / MISSING |
| Post-compact restore | CONFIGURED / MISSING |
| Context monitor | CONFIGURED / MISSING |

### Recommendations

[Only if there are issues — e.g., stale focus, missing hooks, high context usage]
```

### 7. Compaction Guidance

When context is high (>60%), include these reference tables in the output:

**When to compact:**

| Phase Transition | Compact? | Why |
|---|---|---|
| Research to Planning | Yes | Research context is bulky; plan is the distilled output |
| Planning to Implementation | Yes | Plan is in a file; free up context for code |
| Implementation to Testing | Maybe | Keep if tests reference recent code |
| Debugging to Next feature | Yes | Debug traces pollute context |
| Mid-implementation | No | Losing file paths and partial state is costly |
| After a failed approach | Yes | Clear dead-end reasoning |

**What survives compaction:**

| Persists | Lost |
|---|---|
| CLAUDE.md + rules | Intermediate reasoning |
| Task list | File contents previously read |
| MEMORY.md | Multi-step conversation context |
| Git state | Tool call history |
| Files on disk | Verbal preferences |
| precompact-autosave state | — |

## When to Use

- When the context monitor fires a warning
- Before starting a large task (to check remaining capacity)
- After resuming a session (to verify state was preserved)
- When unsure if preservation hooks are working


---

## session-log

**Source:** `skills/session-log/SKILL.md`

---
name: session-log
description: "Use when you need to create a timestamped progress log for a research session."
allowed-tools: Read, Write, Edit, Bash(mkdir*), Bash(ls*)
argument-hint: [project-name-or-path]
---

# Session Log Skill

> Automatically create timestamped progress logs for research sessions.

## Purpose

Based on Scott Cunningham's Claude Code workflow: "Progress logs are my autosave of the workflow." When sessions end or crash, the next Claude can read logs and pick up exactly where you left off.

## When to Use

At the end of any significant work session, or when asked to "log this session" or "update progress".

## Workflow

### Step 1: Identify Projects Touched

Before writing anything, inventory which projects were affected during this session. A "project" is any directory with its own `CLAUDE.md` or `log/` directory. Common splits:

| Scope | Where the log goes |
|-------|--------------------|
| Work inside a specific project | That project's `log/` |
| Global infrastructure (skills, hooks, rules, settings) | Task Management's `log/` |
| Course/module-level changes (reorganisation, new CLAUDE.md) | That module's `log/` |

**Signs of a multi-project session:**
- Files changed under `~/.claude/` (skills, hooks, settings) → global/infrastructure log
- Files changed in the CWD project → project-specific log
- Files changed in a parent or sibling directory → check if that's a separate project

### Step 2: Create One Log Per Project

For each project identified in Step 1:

1. **Read existing context** — check that project's `.context/current-focus.md` and recent `log/` entries
2. **Create `log/` directory** if it doesn't exist
3. **Write the log** to `log/YYYY-MM-DD-HHMM.md` within that project
4. **Scope the content** — each log only covers what happened in that project, not the whole session

If there's only one project, this reduces to a single log (the common case).

### Step 3: Cross-Reference

When multiple logs are created, add a brief cross-reference at the top of each:

```markdown
> Also logged: [other project name] — `[relative or absolute path to other log]`
```

This lets a future session in one project discover that related work happened elsewhere.

### Step 4: Offer Follow-Up

- **Offer to run `/update-focus`** for a structured update (session rotation, open loops), rather than making ad-hoc edits to `current-focus.md`
- If multiple projects were touched, offer to update focus for each

## Log Template

```markdown
# Session Log: [Date] [Time]

## Project: [Project Name]

## What We Did
- [Bullet points of accomplishments]

## Key Decisions
- [Any choices made and why]

## Problems/Blockers
- [Issues encountered]

## Next Steps
- [ ] [Actionable next items]

## Files Changed
- [List of modified files — only those in THIS project]
```

## Examples

### Single-project session
"Please log this session — we worked on the research paper, fixed the simulation code, and decided to target Journal B instead of Journal A."

→ One log in the MCDM project's `log/`

### Multi-project session
"Please log this session — we did Workshop 17, reorganised the module folder, and created two new global skills."

→ Three logs:
1. **Module project** `log/` — workshop completion, reorganisation, CLAUDE.md creation
2. **Task Management** `log/` — new skills (`init-project-course`, `audit-project-course`), new hook (`ensure-latexmkrc.sh`), settings.json changes


---

## skill-extract

**Source:** `skills/skill-extract/SKILL.md`

---
name: skill-extract
description: "Extract reusable knowledge from the current session into a persistent skill.\nUse when you discover something non-obvious, create a workaround, or develop\na multi-step workflow that future sessions would benefit from."
allowed-tools:
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - Bash(uv run python*)
  - AskUserQuestion
---

# Learn: Session Knowledge Extraction

Extract reusable workflows, workarounds, and multi-step procedures discovered during a session into persistent skills. Complementary to the `learn-tags` rule — while `[LEARN]` tags record one-liner corrections in MEMORY.md, `/skill-extract` creates full skill definitions in `skills/`.

## When to Use

- You discovered a non-obvious multi-step procedure
- You built a workaround for a recurring problem
- You developed a workflow that future sessions would benefit from
- the user says "save this as a skill", "learn this", or "remember how to do this"

## Phase 1: Evaluate

Before creating anything, answer these 4 self-assessment questions:

1. **Non-obvious?** Would a future session figure this out without help, or would it waste time rediscovering it?
2. **Future benefit?** Will this come up again across sessions or projects?
3. **Repeatable?** Is this a procedure that can be followed step-by-step, or was it a one-off?
4. **Multi-step?** Does it involve 2+ non-trivial steps that benefit from being documented together?

**Decision rule:** If at least 3 of 4 answers are "yes", proceed to Phase 2. Otherwise, suggest recording as a `[LEARN]` tag in MEMORY.md instead (simpler, lower overhead).

If borderline, ask the user:
> "This seems useful but may not warrant a full skill. Should I create a skill or just add a [LEARN] tag to MEMORY.md?"

## Phase 2: Creation Guard + Read Patterns

Run the **skill-preflight** analysis (see [`skills/skill-preflight/SKILL.md`](../skill-preflight/SKILL.md)):

1. Identify the proposal (name, type, purpose, key functions, keywords)
2. Search existing skills and agents for overlap (skill-index scan + keyword grep)
3. Analyse overlap and generate a recommendation:

| Recommendation | Criteria | Action |
|----------------|----------|--------|
| **PROCEED** | <20% overlap, genuinely new | Continue to Phase 3 |
| **EXTEND** | 50%+ overlap with one existing | Modify existing skill instead — stop here |
| **COMPOSE** | Multiple artifacts cover 80%+ | Create wrapper or document workflow — stop here |
| **ITERATE** | 20-50% overlap, needs refinement | Ask the user to clarify differentiation, then re-evaluate |
| **BLOCK** | Would create duplication | Do not create — stop here |

4. Present the skill-preflight analysis to the user and get explicit approval before proceeding
5. **Read [`skills/shared/skill-design-patterns.md`](../shared/skill-design-patterns.md)** — choose the structural pattern that fits:
   - **Workflow-based** — multi-step with phases and review gates
   - **Task-based** — focused input/output with processing rules
   - **Agent-delegation** — multiple subagents, each handling one concern
   - **Reference-based** — augmenting with domain knowledge via `references/`

## Phase 3: Design the Skill

Before writing, make three decisions:

**1. Choose the structural pattern** (from Phase 2). State it explicitly:
> "This is a [workflow/task/agent-delegation/reference]-based skill."

**2. Identify resources needed:**
- Does the skill need `scripts/` for deterministic operations?
- Does it need `references/` for detailed specs, rubrics, or large examples?
- Does it need to delegate to subagents?

**3. Draft the architecture** — for non-trivial skills, sketch the flow:
```
Input → [Step A] → REVIEW GATE → [Step B] → Output
```

## Phase 4: Build the Skill

Write `skills/{name}/SKILL.md`:

### Frontmatter

```yaml
---
name: {kebab-case-name}
description: "{What it does. Concrete task types. Use when...}"
allowed-tools:
  - {minimum set of tools needed}
---
```

### Body Structure

The body varies by pattern, but always includes these elements:

```markdown
# {Skill Name}: {Short Description}

## When to Use
[Activation conditions — natural language triggers and /command]

## {Main Workflow / Processing Rules / Delegation Protocol}
[The core of the skill — structured per the chosen pattern]

## {Anti-Patterns / Never Do These}
[What NOT to do — agents default to generic without constraints]

## Output Format
[What the output looks like]

## Verification
[How to confirm it worked]
```

**Optional sections** (add when relevant):
- `## Defaults` — assumptions table to reduce friction
- `## Examples` — concrete before/after or good/bad snippets
- `## Notes` — edge cases, limitations

### Solution Pattern (for debugging/workaround skills)

When the skill captures a fix, workaround, or debugging procedure, use this body structure:

```markdown
# {Skill Name}: {Short Description}

## Problem
[Specific error message or symptom. Quote the exact text users would see.]

## Context / Triggers
[When this occurs — tool versions, file types, OS, configurations]

## Solution
[Step-by-step fix. Imperative form.]

## Verification
[How to confirm the fix worked]

## Example
[Concrete before/after or input/output]

## Notes
[Edge cases, alternative approaches, when this does NOT apply]
```

### Description Optimization

The `description:` field in frontmatter is what triggers skill discovery. Write it to match how a user would describe their problem:

- **Include specific error messages or symptoms** — "Fix `Package biblatex Error: File 'references.bib' not found`"
- **Include context markers** — file types, tools, situations where this applies
- **Include negative cases** — "Not for general proofreading (use /proofread instead)"
- **Use natural trigger phrases** — the exact words a user would type

### Extraction Checklist

During skill creation, mentally verify each point before finalising:

1. **Trigger coverage** — would a user find this skill from 3 different phrasings of the same problem?
2. **Self-contained** — can the skill be followed without reading other files (except `references/`)?
3. **Anti-patterns present** — at least 2 "don't do this" entries to prevent common mistakes?
4. **Verification step** — does the skill tell you how to confirm it worked?
5. **Scope bounded** — is it clear what this skill does NOT do?

### Writing Rules

- **Imperative form.** "Parse the input" not "You should parse the input."
- **Be specific about what NOT to do.** Anti-pattern lists are highly effective.
- **Include concrete examples.** Show expected input/output pairs.
- **Keep SKILL.md under 300 lines.** Move detail to `references/`.
- **Every instruction must be actionable.** No throat-clearing.
- **Use tables for structured data.** Faster to parse than prose.

### Naming Conventions

- **Directory and name:** `kebab-case`, descriptive, 2-4 words
- **Avoid generic names:** `fix-bug` is bad; `fix-overleaf-sync-conflict` is good
- **Match the trigger:** If the natural trigger is "compile my slides", the name should relate to slide compilation

### Allowed Tools

Follow principle of least privilege:

| Skill type | Tools |
|-----------|-------|
| Report-only | `Read`, `Glob`, `Grep` |
| File-creating | + `Write`, `Edit` |
| Shell-needing | + specific `Bash(command*)` patterns |
| Interactive | + `AskUserQuestion` |
| Delegating | + `Task` |

## Phase 5: Validate

Run the validation script on the new skill:

```bash
uv run python skills/skill-extract/scripts/validate_skill.py skills/{name}
```

Fix all errors. Address warnings to improve quality. Use `--strict` to promote warnings to errors.

The validator checks: frontmatter validity, name format and directory match, description quality, body length, broken links, referenced directories, and placeholder text.

## Phase 6: Deploy and Confirm

1. Copy the skill to the deployed location (rsync won't run until next session start):
   ```bash
   cp -r skills/{name} ~/.claude/skills/{name}
   ```
2. Check that `~/.claude/skills/{name}/SKILL.md` exists
3. Tell the user: "Created `/{name}` — [one-line summary]. It's available immediately in all projects."
4. If the skill is substantial, suggest updating `docs/components/skills.md` with the new entry

## What This Skill Does NOT Do

- **Does not replace `[LEARN]` tags** — one-liner corrections still go in MEMORY.md via the `learn-tags` rule; `/skill-extract` is for multi-step procedures, not one-liners
- **Does not create agents** — agents need separate context and persistent memory
- **Does not modify existing skills** — if an existing skill needs updating, do that directly


---

## skill-preflight

**Source:** `skills/skill-preflight/SKILL.md`

---
name: skill-preflight
description: "Use when you need a pre-flight duplicate check before creating new skills or agents."
allowed-tools:
  - Read
  - Glob
  - Grep
  - AskUserQuestion
---

# Creation Guard: Pre-Flight Duplicate Check

Prevent duplicate functionality by analysing existing skills and agents before creating new ones. Intercepts creation intent, searches for overlap, and recommends one of 5 actions.

## When to Use

Invoke **before** creating ANY new:
- Skill (`skills/*/SKILL.md`)
- Agent (`.claude/agents/*.md`)

Trigger phrases:
- "Create a skill for..."
- "I want a new skill that..."
- "Let's add an agent for..."
- Any intent to create new automation/tooling

## Process

### Step 1: Identify the Proposal

Extract from the request:
- **Name**: Proposed name (kebab-case)
- **Type**: skill | agent
- **Purpose**: What it does (one sentence)
- **Key Functions**: 3-5 main capabilities
- **Keywords**: Searchable terms related to functionality

### Step 2: Search Existing Artifacts

Run these searches in parallel:

1. **Read [`skills/shared/skill-index.md`](../shared/skill-index.md)** — scan the categorised table for potential duplicates by name and purpose
2. **Keyword search** — grep skills and agents for each keyword:

```
Grep for each keyword across:
  - skills/*/SKILL.md (frontmatter + body)
  - .claude/agents/*.md (frontmatter + body)
```

3. **Agent scan** — read frontmatter of each agent to check purpose overlap:

```
Glob: .claude/agents/*.md
Read first 20 lines of each match
```

### Step 3: Analyse Overlap

For each potentially related artifact, assess:

| Criterion | Question |
|-----------|----------|
| Functional overlap | Does it do the same thing? (0-100%) |
| Naming confusion | Could names be confused? |
| Extension potential | Could the proposal extend this instead? |
| Composition | Could existing artifacts compose to achieve this? |

### Step 4: Generate Recommendation

Based on analysis, recommend ONE of:

| Recommendation | Criteria | Action |
|----------------|----------|--------|
| **PROCEED** | <20% overlap, genuinely new capability | Create new artifact |
| **EXTEND** | 50%+ overlap with single existing artifact | Modify existing instead |
| **COMPOSE** | Multiple artifacts cover 80%+ combined | Create thin wrapper or document workflow |
| **ITERATE** | 20-50% overlap, proposal needs refinement | Refine proposal to differentiate |
| **BLOCK** | Would create problematic duplication | Do not create |

### Step 5: Present and Confirm

Display the analysis and wait for explicit user approval before proceeding.

## Output Format

```
════════════════════════════════════════════════════════════════
CREATION GUARD ANALYSIS
════════════════════════════════════════════════════════════════

PROPOSAL:
  Type: [skill|agent]
  Name: [proposed-name]
  Purpose: [one sentence]

EXISTING ARTIFACTS ANALYSED: [count]

RELATED ARTIFACTS FOUND:

1. [artifact-name] ([type])
   Purpose: [what it does]
   Overlap: [X]% - [explanation]

2. [artifact-name] ([type])
   Purpose: [what it does]
   Overlap: [X]% - [explanation]

RECOMMENDATION: [PROCEED|EXTEND|COMPOSE|ITERATE|BLOCK]

RATIONALE:
[2-3 sentences explaining the recommendation]

SUGGESTED ACTION:
[Specific next step based on recommendation]

════════════════════════════════════════════════════════════════
```

## Recommendation Details

### PROCEED
- Artifact is genuinely new
- No significant overlap found
- Clear differentiation from existing tools
- Go ahead and create

### EXTEND
Present extension proposal:
```
Instead of creating [new-name], extend [existing-name]:

Current capabilities:
- [existing feature 1]
- [existing feature 2]

Proposed additions:
- [new feature 1]
- [new feature 2]
```

### COMPOSE
Present composition approach:
```
The proposed functionality can be achieved by combining:

1. [artifact-1] — handles [aspect]
2. [artifact-2] — handles [aspect]

Options:
A) Document this workflow (no new code)
B) Create thin orchestration skill
C) Add to existing skill's integration section
```

### ITERATE
Present refinement questions:
```
Overlap detected with [existing-artifact].

Differentiation needed:
1. [question about scope]
2. [question about use case]
3. [question about implementation]

Please clarify to proceed.
```

### BLOCK
Explain why creation should not proceed:
```
BLOCKED: Would create problematic duplication.

Existing artifact: [name]
- Already does: [capabilities]
- Your request: [same capabilities]

Alternatives:
1. Use existing: /[skill-name]
2. If missing features, extend the existing artifact
3. If different use case, explain how this differs
```

## Post-Match Action Table

When overlap IS found, use this table to decide the specific action:

| Situation | Action |
|-----------|--------|
| Nothing related found | Create new artifact |
| Same trigger + same fix as existing | Update existing (bump version, improve docs) |
| Same trigger, different root cause | Create new + add cross-links in both |
| Partial overlap (same domain, different trigger) | Add variant subsection to existing |
| Same domain, different problem | Create new + add "See also" references |
| Existing is stale or wrong | Mark deprecated + create replacement |

This complements the PROCEED/EXTEND/COMPOSE/ITERATE/BLOCK recommendation above. The recommendation decides *whether* to create; this table decides *how* to handle the relationship with existing artifacts.

## Self-Check Questions

Before creating ANY new artifact, ask:

1. Does something similar already exist?
2. Could this be added to an existing artifact?
3. Would a user know to look for this vs the existing one?
4. Am I creating this because it's needed or because it's easier than finding what exists?

## Naming Convention Enforcement

When creating a new skill, **always** name the definition file `SKILL.md` (uppercase). Never `skill.md`, `Skill.md`, or any other casing.

- The MCP server's skill discovery scans for `SKILL.md` explicitly
- Documentation generators and `/system-audit` use `find -name 'SKILL.md'`
- On case-insensitive filesystems (macOS APFS), lowercase files appear to work locally but fail in case-sensitive contexts (Linux CI, Docker, MCP server pattern matching)

**Check before writing:** If the target directory already contains a `skill.md` (lowercase), rename it to `SKILL.md` first.

## Anti-Patterns

| Anti-Pattern | Problem | Instead |
|--------------|---------|---------|
| Skip the check | "It's obviously new" — famous last words | Always run the analysis |
| Name-only matching | Names differ but functions overlap | Search by purpose and keywords |
| Create then merge | Merge debt accumulates fast | Check first, create once |
| Over-splitting | Two skills that always run together | Consider a single skill with phases |
| Lowercase `skill.md` | Invisible to MCP server, audit tools, and case-sensitive systems | Always use `SKILL.md` (uppercase) |

## Integration

This skill is invoked by `/skill-extract` in Phase 2 to replace the old subset/partial/no-overlap check. When called from `/skill-extract`, return the recommendation label (PROCEED/EXTEND/COMPOSE/ITERATE/BLOCK) so `/skill-extract` can branch accordingly.


---

## split-pdf

**Source:** `skills/split-pdf/SKILL.md`

---
name: split-pdf
description: "Use when you need to download, split, and deeply read an academic PDF that is NOT in Paperpile (for Paperpile items, prefer paperpile get-pdf-text directly)."
allowed-tools: Bash(python*), Bash(uv*), Bash(curl*), Bash(wget*), Bash(mkdir*), Bash(ls*), Bash(rm*), Read, Write, Edit, WebSearch, WebFetch, Agent, Bash(paperpile*)
argument-hint: [pdf-path-or-search-query]
---

# Split-PDF: Download, Split, and Deep-Read Academic Papers

**CRITICAL RULE: Never read a full PDF. Never.** Only read the 4-page split files, and only 3 splits at a time (~12 pages). Reading a full PDF will either crash the session with an unrecoverable "prompt too long" error — destroying all context — or produce shallow, hallucinated output. There are no exceptions.

## When This Skill Is Invoked

The user wants you to read, review, or summarize an academic paper. The input is either:
- A file path to a local PDF (e.g., `./articles/smith_2024.pdf`)
- A search query or paper title (e.g., `"Gentzkow Shapiro Sinkinson 2014 competition newspapers"`)

**Important:** You cannot search for a paper you don't know exists. The user MUST provide either a file path or a specific search query. If the user invokes this skill without specifying what paper to read, ask them. Do not guess.

**Prefer Paperpile when possible.** If the paper is in Paperpile, call `paperpile get-pdf-text(citekey=KEY)` directly — you get the full structured text without any splitting. Only fall through to this skill's page-split workflow when the PDF is NOT in Paperpile (preprints, referee materials, ad-hoc reading, third-party shared PDFs).

## Step 1: Acquire the PDF

**If a local file path is provided:**
- Verify the file exists
- **Use the PDF in place** — do not move or copy it. The folder containing the PDF becomes the working directory for splits and extracts.
- Proceed to Step 2

**If a search query or paper title is provided:**

Determine the download directory:
- **Inside a research project** (has `CLAUDE.md`, `data/`, `paper/`, etc.): use `./articles/` in the project directory (create if needed).
- **Outside a project** (e.g., ad-hoc reading from Task Management root): use `to-sort/downloads/` in the Task Management folder.

Then:
1. Use WebSearch to find the paper
2. If WebSearch doesn't yield a direct PDF link, try `scholarly scholarly-search` first. Fallback to Python OpenAlex client:
   ```python
   import sys
   sys.path.insert(0, ".scripts/openalex")
   from openalex_client import OpenAlexClient
   client = OpenAlexClient(email="user@example.edu")
   results = client.search_works(search="paper title here", per_page=5)
   # Check open_access.oa_url in results for direct PDF links
   ```
3. Use WebFetch or Bash (curl/wget) to download the PDF
4. Save it to the download directory
5. Proceed to Step 2

**CRITICAL: Always preserve the original PDF.** The source PDF must NEVER be deleted, moved, or overwritten at any point in this workflow. The split files are derivatives; the original is the permanent artifact. Do not clean up, do not remove, do not tidy.

## Step 2: Check for Cached Extract, then Split

**First, check for an existing extract.** Look for `<basename>_text.md` in the same folder as the PDF.

If found, ask:
> "An extract from a previous deep-read exists (`<basename>_text.md`). Use it for this request, or re-read the PDF from scratch?"
- **Use extract**: read `<basename>_text.md` and use it as the source notes — skip the rest of Steps 2 and 3 entirely.
- **Re-read**: proceed with splitting below.

This prevents redundant re-reading of papers you have already processed. The `_text.md` file is a structured plain-text extraction far cheaper to read than re-processing PDF page images.

**Second, check for existing splits.** Compute the build directory:

```python
import os
folder_path  = os.path.dirname(os.path.abspath(pdf_path))
foldername   = os.path.basename(folder_path)
pdf_basename = os.path.splitext(os.path.basename(pdf_path))[0]
build_dir    = os.path.join(folder_path, foldername + '_build')
split_dir    = os.path.join(build_dir, 'split_' + pdf_basename)
```

If `split_dir` already exists and contains `.pdf` files, ask:
> "Splits already exist for `<pdf-basename>` (N chunks in `<foldername>_build/split_<pdf-basename>/`). Reuse existing splits, or re-split from scratch?"
- **Reuse**: skip splitting, proceed to Step 3 using the existing files in `split_dir`.
- **Re-split**: delete the existing split folder, then split.

**Otherwise, split.** Create `<foldername>_build/split_<pdf-basename>/` and run:

```python
from PyPDF2 import PdfReader, PdfWriter
import os

def split_pdf(input_path, output_dir, pages_per_chunk=4):
    os.makedirs(output_dir, exist_ok=True)
    reader = PdfReader(input_path)
    total = len(reader.pages)
    prefix = os.path.splitext(os.path.basename(input_path))[0]

    for start in range(0, total, pages_per_chunk):
        end = min(start + pages_per_chunk, total)
        writer = PdfWriter()
        for i in range(start, end):
            writer.add_page(reader.pages[i])

        out_name = f"{prefix}_pp{start+1}-{end}.pdf"
        out_path = os.path.join(output_dir, out_name)
        with open(out_path, "wb") as f:
            writer.write(f)

    print(f"Split {total} pages into {-(-total // pages_per_chunk)} chunks in {output_dir}")
```

If PyPDF2 is not installed: `uv pip install PyPDF2`.

**Directory convention:**
```
articles/                             # any folder containing a PDF
├── smith_2024.pdf                    # original — NEVER DELETE
├── smith_2024_text.md                # persistent extract — created after deep-read
└── articles_build/                   # <foldername>_build/ — shared build folder
    └── split_smith_2024/             # split_<pdf-basename>/
        ├── smith_2024_pp1-4.pdf
        ├── smith_2024_pp5-8.pdf
        ├── smith_2024_pp9-12.pdf
        ├── notes.md                  # working copy — source for _text.md
        └── ...
```

The build directory (`<foldername>_build/`) keeps split artifacts separate from source material and finished outputs. Multiple PDFs in the same folder share one build directory, each with its own `split_<basename>/` subdirectory.

## Step 3: Read in Batches of 3 Splits

Read **exactly 3 split files at a time** (~12 pages). After each batch:

1. **Read** the 3 split PDFs using the Read tool
2. **Update** the running notes file (`notes.md` in the split subdirectory)
3. **Pause** and tell the user:

> "I have finished reading splits [X-Y] and updated the notes. I have [N] more splits remaining. Would you like me to continue with the next 3?"

4. **Wait** for the user to confirm before reading the next batch.

Do NOT read ahead. Do NOT read all splits at once. The pause-and-confirm protocol is mandatory.

## Step 4: Structured Extraction (8 dimensions)

As you read, collect information along these dimensions and write them into `notes.md`:

1. **Research question** — What is the paper asking and why does it matter?
2. **Audience** — Which sub-community of researchers cares about this?
3. **Method** — How do they answer the question? What is the identification strategy?
4. **Data** — What data? Where from? Unit of observation? Sample size? Time period?
5. **Statistical methods** — What econometric/statistical techniques? Key specifications?
6. **Findings** — Main results? Key coefficient estimates and standard errors?
7. **Contributions** — What's learned that we didn't know before?
8. **Replication feasibility** — Public data? Replication archive? Data appendix? URLs?

These extract what a researcher needs to **build on or replicate** the work.

## Step 5: Persist the Extract

**After all batches are complete**, write the final notes to `<basename>_text.md` in the same folder as the source PDF:

```
articles/smith_2024_text.md
```

Then notify the user:
> "Extract saved to `smith_2024_text.md` alongside the source PDF. Future requests on this paper can reuse it without re-reading."

This file is the persistent, reusable artifact. The `notes.md` in the build directory is the working copy. Both are kept — never delete either.

## Structured Mode (Paperpile)

If the paper IS in Paperpile (user provides a citekey), skip the page-split workflow entirely:

1. `paperpile get-item(citekey=KEY)` — title, authors, abstract, affiliations
2. `paperpile get-pdf-text(citekey=KEY)` — full text from Google Drive

Write the 8-dimension extraction directly to `<basename>_text.md` in the working directory. No splits needed.

**This skill's page-split workflow is for PDFs NOT in Paperpile.**

## Agent Isolation Protocol

**When split-pdf is invoked by another skill or workflow** (any process that continues working after the PDF has been read), the PDF reading MUST run inside a subagent to prevent context bloat in the parent conversation.

**Why:** Each PDF page rendered by the Read tool produces image data in the conversation context. A 35-page PDF (9 chunks) can add 10-20MB of image data that accumulates permanently. After reading one or two large PDFs on top of prior work, the conversation hits the API request size limit and becomes unrecoverable.

**Pattern:** The parent skill handles splitting (Step 2's Python script) in its own context — this is lightweight. Then it launches an Agent to perform all the reading:

```
Read PDF split files and produce structured extraction notes.

Split directory: <split_dir>
Files (read in this order, 3 at a time): <file_list>
Notes output:    <notes_path>  (working copy in split_dir)
Text output:     <text_path>   (persistent <basename>_text.md)

Process:
1. Read 3 PDF files at a time using the Read tool
2. After each batch, update notes.md with extracted content
3. Extract along the 8 dimensions (research question, audience, method,
   data, statistical methods, findings, contributions, replication feasibility)
4. Write the final structured extraction to <text_path>

Report when done: pages read, figures/tables found, one-sentence content summary.
```

After the agent returns, the parent reads the output files (plain markdown, not PDF images) and continues its workflow.

**Standalone invocations** (user calls `/split-pdf` directly) use the interactive protocol above with reads in the main conversation and the pause-and-confirm protocol.

## When NOT to Split

- Papers shorter than ~15 pages: read directly (still use the Read tool, not Bash)
- Policy briefs or non-technical documents: a rough summary is fine
- Triage only: read just the first split (pages 1-4) for abstract and introduction
- Paperpile items: use `paperpile get-pdf-text` directly

## Quick Reference

| Step | Action |
|------|--------|
| **Acquire** | Use local PDF in place, or download to `./articles/` (in-project) / `to-sort/downloads/` (ad-hoc) |
| **Check cache** | `<basename>_text.md` or existing splits — offer to reuse |
| **Split** | 4-page chunks into `<foldername>_build/split_<pdf-basename>/` |
| **Read** | 3 splits at a time, pause after each batch |
| **Notes** | Update `notes.md` with 8-dimension extraction |
| **Persist** | Save final extract to `<basename>_text.md` alongside source PDF |
| **Confirm** | Ask user before continuing to next batch |

## Acknowledgments

The in-place PDF handling, persistent `_text.md` extraction, split reuse, build directory convention, and agent isolation protocol are adapted from Scott Cunningham's [MixtapeTools](https://github.com/scunning1975/mixtape-tools) split-pdf skill (April 2026), which itself incorporated improvements from [Ben Bentzin](https://www.mccombs.utexas.edu) (McCombs School of Business, UT Austin). Structured Paperpile mode is the user's addition.


---

## strategic-revision

**Source:** `skills/strategic-revision/SKILL.md`

---
name: strategic-revision
description: "Use when you receive referee comments for a paper (R&R, revise-and-resubmit) and need a DAG-validated revision master plan — atomic task extraction, dependency mapping, computational critical-path analysis, execution blocks, venue strategy. Merges /parse-reviews ingestion with Sihvonen's strategic-revision architecture."
allowed-tools: Read, Write, Edit, Glob, Grep, Bash(mkdir*), Bash(cp*), Bash(ls*), Bash(latexmk*), Bash(python*), Bash(uv*), AskUserQuestion, Task
argument-hint: "[path-to-reviews-pdf or no arguments for guided setup]"
---

# Strategic Revision — From Referee PDF to DAG-Validated Master Plan

Read a referee comments PDF and produce:
1. Standardised tracking files (per-reviewer markdown, LaTeX verbatim, comment tracker, review analysis)
2. A computationally validated revision master plan (atomic tasks, DAG, execution blocks A-E, critical path, bottlenecks)

**Provenance:** DAG validation + critical-path architecture adapted from Jukka Sihvonen's strategic-revision skill (https://github.com/jusi-aalto/strategic-revision). the user's ingestion layer (correspondence scaffolding, LaTeX verbatim, R&R routing, venue strategy, coaching) retained.

## When to Use

- Received reviewer reports for a paper (journal or conference)
- Starting an R&R cycle and need to set up tracking + plan revision strategy
- Want both structured referee artifacts AND a dependency-mapped action roadmap

## When NOT to Use

- Writing the actual response letter (use generated response blocks as a starting point, then write manually)
- Reviewing someone else's paper (use `/proofread` or `peer-reviewer` agent)
- Internal review synthesis only — use `/synthesise-reviews` instead

## Inputs

Gather via interview if not provided:

1. **Reviews PDF path** — auto-discovered or user-provided (see below)
2. **Project path** — root of the research project (auto-detect from cwd if possible)
3. **Venue slug** — e.g., `ejor`, `facct-2026`, `management-science`
4. **Revision round** — integer, default 1
5. **Response deadline** — date if known, otherwise "TBD"
6. **Coordinating author** — who is leading the response

### PDF Auto-Discovery

Search for the reviews PDF in this order. Use the first match; if multiple PDFs found at a location, list them and ask the user to pick.

1. `to-sort/*.pdf` — most likely landing spot after download
2. `correspondence/referee-reviews/{venue}-round{n}/*.pdf`
3. `correspondence/referee-reviews/*.pdf`
4. Ask the user for the path if nothing found

## Output Location

```
correspondence/referee-reviews/{venue}-round{n}/
├── reviews-original.pdf              (copy of input PDF — source NEVER moved)
├── rebuttal.md                       (empty — for response draft)
├── reviews/                          (individual reviewer files)
│   ├── reviewer-1.md
│   └── ...
├── analysis/
│   ├── comment-tracker.md            (atomic comment matrix with R&R + 5-cat classification)
│   ├── review-analysis.md            (strategic overview + venue strategy)
│   └── reviewer-comments-verbatim.tex (LaTeX transcription)
└── plan/
    ├── REVISION_MASTER_PLAN.md       (six-phase Sihvonen plan — atomic tasks, DAG, blocks, risks)
    ├── revision_tasks.json           (DAG input — see references/task-schema.md)
    └── revision_dag_analysis.json    (computational output — parallel batches, critical path, bottlenecks)
```

**Source PDF preservation:** The original PDF is only ever **copied** to `reviews-original.pdf`. Never move, rename, or delete the source.

**Principle:** `correspondence/` holds exchanges with reviewers. Internal review work goes in `docs/{venue}/internal-reviews/`.

**No-overwrite rule:** If outputs already exist, version them (`comment-tracker-v2.md`, `REVISION_MASTER_PLAN-v2.md`). Always flag before writing.

## Protocol — 11 Phases

The skill runs 11 sequential phases. Detailed step-by-step procedure: [references/phases.md](references/phases.md).

| # | Phase | Output | Source |
|---|-------|--------|--------|
| 1 | **Setup** | Scaffolded directories + copied PDF | FB |
| 2 | **Read Reviews** | Structured per-reviewer data in memory | FB |
| 3 | **Individual Reviewer Files** | `reviews/reviewer-{N}.md` | FB |
| 4 | **LaTeX Verbatim Transcription** | `reviewer-comments-verbatim.tex` (compiled) | FB |
| 5 | **Atomic Parsing** | Every distinct request as own SourceID (`R1.a3`, `EiC.2b`) | JS |
| 6 | **Classification** | 5-cat (STRUCTURAL/ARGUMENTATIVE/EMPIRICAL/CLARIFICATION/EDITORIAL) + R&R routing (NEW ANALYSIS / CLARIFICATION / DISAGREE / MINOR) | Both |
| 7 | **Dependency Mapping (DAG)** | Upstream Blockers + Collateral Risks tables → `revision_tasks.json` | JS |
| 8 | **Structural DAG Validation** | `dag_validator.py --validate-only` gate check | JS |
| 9 | **Critical Path Sequencing** | Execution Blocks A-E + GO/NO-GO gate after Block A | JS |
| 10 | **Risk & Conflict Resolution + Coaching** | Reviewer conflicts, process risks, interactive coaching (Major/Critical only) | Both |
| 11 | **Computational Optimization + Review Analysis** | Parallel batches, critical path, bottlenecks + venue strategy (CABS/CORE/SJR) | Both |

**JS = Sihvonen phases. FB = the user phases. Both = merged.**

### Phase Dependencies

- Phases 1-4 (ingestion) must complete before Phase 5 begins
- Phase 8 is a **hard gate**: cycles → return to Phase 7, do not advance to Phase 9
- Phase 11 requires the Phase 9 block assignments before running full DAG analysis
- Phase 10 coaching runs only on Major/Critical comments (skip Minor/Editorial)

## DAG Validation Quick Reference

**Phase 8 (structural gate):**
```bash
cd correspondence/referee-reviews/{venue}-round{n}/plan
python dag_validator.py revision_tasks.json --validate-only
```

**Phase 11 (full analysis):**
```bash
python dag_validator.py revision_tasks.json
# Produces revision_dag_analysis.json
```

Copy `dag_validator.py` from `skills/strategic-revision/scripts/` into the plan directory before running. Requires `networkx` (`uv pip install networkx` if missing).

Full validator documentation: [references/dag-validation.md](references/dag-validation.md).
Task JSON schema: [references/task-schema.md](references/task-schema.md).
R&R routing rules: [references/rr-routing.md](references/rr-routing.md).

## Classification: Two Axes

Every atomic task gets **both** classifications recorded in the comment tracker:

**Category (5-cat, Sihvonen):** structural intent of the change
- 🔴 STRUCTURAL — moves, cuts, reorganizations
- 🟠 ARGUMENTATIVE — theory, narrative, logical framing
- 🟡 EMPIRICAL — new regressions, data work, robustness
- 🟢 CLARIFICATION — definitions, justifications, explanations
- 🔵 EDITORIAL — formatting, typos, figures, terminology

**R&R Routing (FB):** workflow routing
- **NEW ANALYSIS** — needs code/data work
- **CLARIFICATION** — textual fix only
- **DISAGREE** — author push-back with rebuttal
- **MINOR** — trivial or editorial

The two axes are orthogonal: a STRUCTURAL task is usually a CLARIFICATION routing; an EMPIRICAL task is usually NEW ANALYSIS; ARGUMENTATIVE with DISAGREE signals a rebuttal-heavy revision.

## Strategic Coaching (Phase 10)

For each **Major** or **Critical** comment, walk the user through:

1. **Understanding:** reviewer's core concern — methodology, theory, or framing?
2. **Position:** Agree / Partially agree / Disagree (with core rebuttal if Disagree)
3. **Risk:** likelihood of reviewer escalation if pushed back on
4. **Response sketch:** one-sentence strategy (not full response)

Record in the comment tracker with two new columns: **Position** + **Strategy**.

Rules:
- Only Major/Critical get coaching. Minor/Editorial auto-classify as Agree.
- the user can say "skip coaching" to auto-classify all remaining as Agree.
- Maximum 2 rounds of dialogue per comment.
- Do not write the actual response letter — that remains the user's job.

## Venue Strategy (Phase 11)

Populate the Publication Strategy section of `review-analysis.md`:

- **Strategy A (minimal revision):** venues that would accept the paper as-is despite reviewer concerns
- **Strategy B (substantial revision):** equal-or-higher prestige venues worth targeting if authors invest in addressing major concerns
- **Conferences:** check CORE rankings via `.context/resources/venue-rankings.md` (CSV: `.context/resources/venue-rankings/core_2026.csv`)
- **Journals:** check CABS AJG via `.context/resources/venue-rankings.md` (CSV: `.context/resources/venue-rankings/abs_ajg_2024.csv`). For SJR, query Elsevier Serial Title API (`SCOPUS_API_KEY` required). Flag journals below CABS 3 only with strong rationale.
- **Recommendation table:** 3-5 venues ranked with rationale. First option should always be "revise for current venue" if acceptance probability >~30%.
- **Key Decision:** frame the core trade-off (speed vs. impact, minimal vs. substantial effort).

## Critical Rules

1. **Verbatim means verbatim.** Never paraphrase reviewer text in `reviewer-comments-verbatim.tex`. Copy exactly.
2. **Every comment gets a SourceID.** No reviewer concern is lost. If in doubt, give it its own ID.
3. **Atomic tasks only.** If a paragraph contains 3 distinct requests, create 3 rows — never collapse.
4. **No invented requests.** Every task traces to a verbatim quote.
5. **Don't overwrite.** Version outputs if present.
6. **Compile the LaTeX.** `reviewer-comments-verbatim.tex` must build cleanly before Phase 5.
7. **Phase 8 is a hard gate.** Cycles block Phase 9. Fix the DAG, re-run validation.
8. **Phase 11 is mandatory.** Do not skip computational optimization — parallel batches and critical path override manual sequencing where they conflict.
9. **Don't write response letters.** The skill produces plans and trackers; writing the rebuttal is the user's job.
10. **GO/NO-GO gate after Block A.** If empirical foundation changes key conclusions, escalate to authors before advancing.

## Templates

Located in `templates/referee-comments/`:
- `comment-tracker.md` — atomic matrix with R&R columns
- `review-analysis.md` — strategic overview template
- `reviewer-comments-verbatim.tex` — LaTeX transcription template

## Cross-References

- `/proofread` — proofread the response letter before submission
- `/bib-validate` — run after revision to check bibliography
- `/pre-submission-report` — full quality check before resubmission
- `paper-critic` agent — self-review of the revised paper
- `/synthesise-reviews` — merge internal review agent reports (different use case — not referee comments)
- `references/phases.md` — detailed 11-phase protocol
- `references/rr-routing.md` — R&R routing signal words
- `references/dag-validation.md` — DAG validator usage + Phase 6 details
- `references/task-schema.md` — `revision_tasks.json` JSON schema
- `scripts/dag_validator.py` — NetworkX-based DAG validator (copy to plan dir before running)


---

## sync-notion

**Source:** `skills/sync-notion/SKILL.md`

---
name: sync-notion
description: "Use when you need to sync the current project's state to the context library and Notion."
allowed-tools: Read, Edit, Write, Glob, Grep, Bash(ls*), mcp__claude_ai_Notion__notion-search, mcp__claude_ai_Notion__notion-update-page, mcp__claude_ai_Notion__notion-fetch
argument-hint: [optional: summary of what changed]
---

# Update Notion Skill

> Sync the current project's state to the central task management context library and Notion Research Pipeline.

## Purpose

After working on a research project, this skill propagates the current state outward:
- **Project CLAUDE.md** (source of truth) → **`.context/projects/_index.md`** (central registry)
- **Recent session logs** → **`.context/current-focus.md`** (working memory)
- **Project metadata** → **Notion Research Pipeline** (tracking database)

This keeps all systems in sync without manual updates.

## When to Use

- At the end of a work session (often paired with `/session-log`)
- After changing a project's target journal, status, or stage
- When the user says "update project doc", "sync project", "update my project index"

## MCP Pre-Check

Before starting, probe Notion MCP availability with a lightweight search. If unavailable, skip Steps 3 and 5 and offer fallbacks per [`shared/mcp-degradation.md`](../shared/mcp-degradation.md).

## Workflow

### Step 1: Read the current project's CLAUDE.md

Extract key metadata:
- **Project name** (from header)
- **Target journal** (from `Target:` field)
- **Stage** (infer from content: Idea / Literature Review / Drafting / Data Collection / Analysis / Submitted / R&R / Published)
- **Co-authors** (if listed)
- **Working title**
- **Key next steps** (from Research Design or recent session log)

### Step 2: Read the most recent session log

Look in the project's `log/` directory for the latest `YYYY-MM-DD-HHMM.md` file. Extract:
- What was accomplished
- Current blockers
- Next steps

### Step 3: Update `.context/projects/_index.md`

Location: `$TM/.context/projects/_index.md`

Find the project's row in the "Papers in Progress" table. If it exists, update the Stage, Target Journal, and Status columns. If it doesn't exist, add a new row.

**Table format:**
```
| Project | Stage | Co-authors | Target Journal | Status |
```

### Step 4: Update `.context/current-focus.md`

Location: `$TM/.context/current-focus.md`

Update the "Recent Context" section with a brief summary of the latest session. Add any new open loops.

> **Note:** For full session-level updates (session rotation, open loop management, mental state), defer to `/update-focus`. This skill adds a brief summary only.

### Step 5: Update Notion Research Pipeline

Search the Research Pipeline database (`collection://YOUR-PIPELINE-DATABASE-ID-HERE`) for the project name. If found, update:
- **Status** (match to: Idea, Literature Review, Drafting, Submitted, R&R, Published)
- **Target Journal**
- **Priority** (if changed)

If not found, inform the user (don't auto-create — they may want to set properties manually).

### Step 6: Confirm

Report what was updated:
```
Updated project docs for [Project Name]:
- .context/projects/_index.md: [what changed]
- .context/current-focus.md: [what changed]
- Notion Research Pipeline: [what changed, or "no entry found"]
```

## Important Notes

- This skill **reads** the project CLAUDE.md and session logs — it never modifies them.
- It **writes** to the central context files and Notion only.
- Always read before writing to preserve existing content.
- If the user provides a summary argument, use that instead of inferring from logs.


---

## system-audit

**Source:** `skills/system-audit/SKILL.md`

---
name: system-audit
description: "Use when you need to run parallel audits across skills, hooks, agents, rules, and conventions."
allowed-tools: Bash(ls*), Bash(readlink*), Bash(wc*), Bash(git*), Bash(test*), Bash(stat*), Bash(find*), Read, Glob, Grep, Task
argument-hint: "[no arguments — runs full sweep]"
---

# Maintenance Sweep

> System-wide health check using agnix lint + 7 parallel sub-agents. Produces a consolidated report at `log/audits/system-audit-YYYY-MM-DD.md`. **Report-only — never modifies any files.**

## When to Use

- Periodic system hygiene (monthly or after major changes)
- When the user says "maintenance sweep", "system health check", "audit my setup"
- After adding/removing skills, hooks, agents, or rules
- Before presenting the system to others (ensure everything is consistent)

## Overview

1. **Lint** — run `npx agnix .` to validate skills, hooks, agents, and CLAUDE.md
2. **Dispatch** — launch 7 sub-agents in parallel via the Task tool
3. **Collect** — gather each sub-agent's findings
4. **Consolidate** — merge lint results + sub-agent findings into a single timestamped report
5. **Present** — show key findings to the user

**Python:** Always use `uv run python` or `uv pip install`. Never bare `python`, `python3`, `pip`, or `pip3`. Include this in sub-agent prompts.

## Autonomy

Per the global `--autonomous` / `-y` convention in `~/.claude/rules/phased-work.md` § "Autonomy flag convention". Invoke as `/system-audit --autonomous` (or `-y`). When set:

- **No inter-phase pauses** — Lint → Dispatch → Collect → Consolidate → Present chain end-to-end.
- **No `AskUserQuestion` mid-run** — sub-agent count defaults to 7 (the standard fan-out), all sub-agents launch in parallel without confirmation.
- **No interim "review and continue" pauses** between dispatch and consolidation.
- **Sub-agent forbid-list still applied** — all 7 sub-agents are read-only (no edits to skills/hooks/agents/rules during the audit).
- **Report-only invariant preserved** — `--autonomous` does NOT change the skill's read-only nature; it only suppresses confirmation prompts. No fixes are ever applied.
- **Single end-of-run report** at `log/audits/system-audit-YYYY-MM-DD.md` is the only mandatory user-facing output.

This is one of the safer skills to run autonomously — it's read-only by design, sub-agents have no write access to the system, and the output is a single timestamped report that you can review afterward. Recommended for scheduled monthly runs via `/scheduled-job`.

Recommended invocations:

```
/system-audit --autonomous                              # full sweep, end-to-end
/system-audit -y                                        # short form
```

---

## Phase 0: Pre-flight Lints

Two fast lint passes run in the main context before sub-agent dispatch. Both are summary-only — full findings feed into the final report.

### 0.1 agnix lint

Run `npx agnix .` and capture the summary line.

**Pass criteria:** 0 errors. Warnings are informational only.

If errors > 0, list them in the report under an **agnix Lint** section. These are structural issues in skill/hook/agent frontmatter that should be fixed.

Config lives in `.agnix.toml` at project root — known false positives are already suppressed.

### 0.2 skill-numbering lint

Run `uv run python scripts/lint-skills.py` and capture the summary line.

**Pass criteria:** 0 findings. Findings indicate phase-numbering smells, frontmatter typos, or stale cross-skill phase references. Reference: [`skills/_shared/skill-template.md`](../_shared/skill-template.md) § Anti-patterns.

If findings > 0, list them in the report under a **Skill-Numbering Lint** section. The linter explains each rule (R1–R9) inline.

### 0.3 review-agent logger-gate lint

Run:

```bash
grep -E "^After producing (DOMAIN-REVIEW|CODE-REVIEW|your verdict|your referee|the verification)" .claude/agents/*.md
```

**Pass criteria:** 0 matches. Any match means a review-agent definition is using the stale/fragile logger-gate intro pattern that was fixed by the 5-agent patch (commit `23ebcfff`, 2026-05-17). The fragile pattern conditions the `review-state-log.sh` call on producing a stale top-level filename (`DOMAIN-REVIEW.md`-style) or a soft generic phrase (`"your verdict"`, `"the verification"`); when orchestrators like `/review-cluster` send "Return findings as a structured list, NOT a file write", the gate fails and the helper never fires — leaving a logger gap detectable by `/review-recap`.

If matches > 0, list them in the report under a **Review-Agent Logger-Gate** section with the suggested replacement intro:

> Write [your <X> report] to `reviews/<source-slug>/<YYYY-MM-DD-HHMM>.md` (`mkdir -p reviews/<source-slug>/` first). Then append a row to the project's `REVIEW-STATE.md` so `/review-recap` can render the run. Use the shared helper:

Reference pattern: see `paper-critic.md` line ~432 (already patched).

---

## Phase 1: Dispatch Sub-Agents

Launch all 7 in a single message using parallel Task tool calls. Each sub-agent is `subagent_type: Explore`.

**Context overflow prevention:** Instruct each sub-agent to keep its returned output concise — summary tables and key findings only (under 500 words). If detailed findings are large, the sub-agent should write them to a temp file (e.g., `/tmp/system-audit/sa-N.md`) and return only the file path + summary.

All sub-agents receive shared context (Task Management root, research projects root, category directories). Full shared context block and all 6 sub-agent prompt templates:

**[references/sub-agent-prompts.md](references/sub-agent-prompts.md)**

Sub-agents at a glance:

| # | Name | What it checks |
|---|------|---------------|
| 1 | Inventory Auditor | Skill/hook/agent/rule counts, symlinks, MCP alignment |
| 2 | Bibliography & Project Hygiene | .bib files, naming, MEMORY.md presence |
| 3 | Convention Compliance | LaTeX out/, Overleaf separation, Python env, git health |
| 4 | Documentation Freshness | Stale counts, broken links, .context/ freshness |
| 5 | Ecosystem Health | MCP server refs, staleness, orphans, CLI tools |
| 6 | Skill Quality & Overlap | Bloat, staleness, cross-component overlap |
| 7 | Friends Repo Health | Skill/rule freshness vs upstream, anonymisation, install script |

---

## Phase 2: Collect and Consolidate

After all 7 sub-agents return, merge their findings into a single report.

### Report Template

Write to `log/audits/system-audit-YYYY-MM-DD.md`:

```markdown
# Maintenance Sweep — YYYY-MM-DD

## Dashboard

| Area | Status | Issues |
|------|--------|--------|
| agnix Lint | <OK/WARN/FAIL> | <count> |
| Inventory | <OK/WARN/FAIL> | <count> |
| Bibliography & Projects | <OK/WARN/FAIL> | <count> |
| Conventions | <OK/WARN/FAIL> | <count> |
| Documentation | <OK/WARN/FAIL> | <count> |
| Ecosystem Health | <OK/WARN/FAIL> | <count> |
| Skill Quality & Overlap | <OK/WARN/FAIL> | <count> |
| Friends Repo Health | <OK/WARN/FAIL> | <count> |

## agnix Lint
<Phase 0 results: error count, warning count, any specific errors>

## Inventory Audit
<Sub-agent 1 findings>

## Bibliography & Project Hygiene
<Sub-agent 2 findings>

## Convention Compliance
<Sub-agent 3 findings>

## Documentation Freshness
<Sub-agent 4 findings>

## Ecosystem Health
<Sub-agent 5 findings>

## Skill Quality & Cross-Component Overlap
<Sub-agent 6 findings>

## Friends Repo Health
<Sub-agent 7 findings>

## Recommended Actions
<Prioritised list of things to fix, grouped by effort level>

### Quick Fixes (< 5 min each)
- ...

### Medium Effort (5–30 min)
- ...

### Larger Tasks (> 30 min)
- ...
```

---

## Phase 3: Present

Show the user:
1. The dashboard table
2. Any FAIL-status areas with specifics
3. The quick fixes list
4. Ask if he wants to address any issues now

---

## Error Handling

- **Sub-agent timeout:** If a sub-agent doesn't return, note "timed out" in the report and continue with the others.
- **Missing directories:** If a category folder is empty or doesn't exist, note "no projects found" rather than erroring.
- **Permission issues:** If files can't be read, note "access denied" and continue.

## Integration with Other Skills

| Skill | Relationship |
|-------|-------------|
| `/bib-validate` | Run on projects flagged by the Bibliography Hygiene sub-agent |
| `/audit-project-research` | Complements Convention Compliance with deeper per-project checks |
| `/update-project-doc` | Fix documentation staleness found by Documentation Freshness |
| `/sync-permissions` | Fix symlink issues found by Inventory Auditor |
| `/atlas-audit` | Full cross-system audit (local + vault + Paperpile + pipeline) — deeper than this sweep |
| `/insights-deck` | Maintenance findings can feed into system insights presentations |
| `/repo-doc-audit friends` | Dedicated deep audit for friends-repo — Sub-agent 7 is a quick health check; the audit skill is the full version |
| `/sync-friends-repo` | Fix freshness issues found by Sub-agent 7 |


---

## task-management

**Source:** `skills/task-management/SKILL.md`

---
name: task-management
description: "Use when you need help with daily planning, weekly reviews, meeting actions, or vault task queries."
allowed-tools: Read, Write, Edit, AskUserQuestion
---

# the user's Task Management System

## MCP Pre-Check

Before any vault-dependent workflow, probe taskflow MCP availability with a lightweight search. If unavailable, skip vault queries and offer local-only fallbacks per [`shared/mcp-degradation.md`](../shared/mcp-degradation.md).

## System Overview

This is a hybrid vault + local context library system. Before taking action:

1. **Read context files** in `.context/` to understand current state
2. **Query vault** for dynamic task data
3. **Ask questions** before dumping lists (the user prefers this)
4. **Update context** after sessions

## Key Locations

### Context Library (`.context/`)
- `profile.md` — Who the user is, roles, research areas
- `current-focus.md` — What they're working on NOW (update this!)
- `projects/_index.md` — All active projects
- `workflows/` — How to help with specific tasks
- `preferences/` — Priority definitions, naming conventions
- `people/` — Supervisors and collaborators

### Vaults
- **Tasks Tracker**: Research Vault tasks database at `~/Research-Vault`
- **Research Pipeline**: Research Vault pipeline database at `~/Research-Vault`

## Workflows

### Daily Planning

When the user asks to plan their day:

1. **Read** `.context/current-focus.md` and `.context/workflows/daily-review.md`
2. **Query vault** for:
   - Overdue tasks (Due date < today, Status != Done)
   - Due today (Due date = today)
   - High priority items
3. **Ask orientation questions**:
   - "How's your energy today?"
   - "Any fixed commitments?"
   - "What were you working on yesterday?"
4. **Help prioritise** based on answers
5. **Update** `current-focus.md` at end of session

### Meeting Action Extraction

When the user asks to extract actions from a meeting:

1. **Read** `.context/workflows/meeting-actions.md`
2. **Find the meeting transcript** in vault (pages starting with @Date)
3. **Extract action items** looking for:
   - "I'll...", "I need to...", "I should..."
   - "Can you...", "Please..."
   - "We agreed to...", "Next step is..."
4. **Create tasks in vault** with full context:
   - Task name (action verb + object)
   - Project (infer from context)
   - Source: "Meeting"
   - Due date (if mentioned)
   - Description (meeting context)

### Weekly Review

When the user asks for weekly review:

1. **Read** `.context/workflows/weekly-review.md`
2. **Query vault** for:
   - Completed tasks this week
   - Overdue tasks
   - Upcoming deadlines
3. **Guide through reflection**:
   - What got done?
   - What didn't happen?
   - What emerged?
4. **Help plan next week's Big 3**
5. **Update** `current-focus.md` and `projects/_index.md`

### Task Creation

When creating tasks in vault:

**Required fields:**
- Task name (action verb + specific object)
- Status: "Not started"

**Recommended fields:**
- Project: Match to existing project
- Source: Meeting, Email, Supervisor request, Self-initiated, etc.
- Priority: High/Medium/Low (see `.context/preferences/priorities.md`)
- Due date: If known
- Task type: 📝 Writing, 📚 Reading, 🔬 Research, 📅 Meeting, 📋 Admin, 📧 Communication

### Research Pipeline

For paper-related queries:

1. **Query Research Pipeline database** for paper status
2. **Stages**: Idea → Literature Review → Drafting → Submitted → R&R → Published
3. **Link tasks to papers** via Project property

## the user's Preferences

- **Questions over lists** — Don't dump task lists, ask what to focus on
- **Full context for actions** — Include who, what, why, when in task descriptions
- **Flexible/reactive style** — They work on what feels right, help them navigate
- **Daily review preferred** — Short check-ins work better than big weekly sessions
- **multiple active projects** — Help manage cognitive load, don't add more

## Important Context

- PhD Year 1 at [University]
- Teaching
- 4 supervisors across institutions
- Research: [your research areas]
- Current papers: journal revision, [Project] theory, [Project]

## After Every Session

Update `.context/current-focus.md` with:
- What was worked on
- Where things were left off
- What's next


---

## update-focus

**Source:** `skills/update-focus/SKILL.md`

---
name: update-focus
description: "Use when you need to update current-focus.md with a structured session summary."
allowed-tools: Read, Edit, Bash(git log*), Bash(date*), Bash(ls*)
---

# Update Focus Skill

> Structured end-of-session update to `.context/current-focus.md` that preserves the document's full structure.

## Purpose

The stop hook nudges to update `current-focus.md` at session end, but ad-hoc edits risk flattening its rich structure. This skill handles session rotation, open loop management, and targeted questions — so the file stays useful as a working memory between sessions.

## When to Use

- At the end of a work session (triggered by stop hook or manually)
- When the user says "update my focus", "save where I left off", "update current focus"
- After `/session-log` if `current-focus.md` wasn't updated

## Canonical Document Structure

`current-focus.md` follows this structure — **always preserve it**:

```markdown
# Current Focus

> Update this file regularly...

## This Week's Focus (w/c YYYY-MM-DD)

### Primary Goal
[One sentence]

### Active Projects (Top 3)
1. **[Project]** - [Status/phase]
2. **[Project]** - [Status/phase]
3. **[Project]** - [Status/phase]

### Waiting On
- [ ] [Person] - [What] - [Since when]

### Upcoming Deadlines
| Deadline | What | Project |
|----------|------|---------|

## Recent Context

### Last Session Summary (YYYY-MM-DD — [Title])
- [Bullet points of what happened]

### Previous Session (YYYY-MM-DD — [Title])
- [Bullet points]

### Previous Session (YYYY-MM-DD — [Title])
- [Bullet points]

### Previous Session (YYYY-MM-DD — [Title])
- [Bullet points]

### Open Loops
Things I started but haven't finished:
- [ ] [Item]
- [x] [Completed item — remove on next update]

### Mental State
[Optional: How are you feeling about work?]

---

## Quick Reference

### Key Meetings This Week
- [Day]: [Meeting] with [Person] about [Topic]

### Papers in Active Revision
- [Paper title] - [Journal] - [Stage]

---
```

## Workflow

### Step 1: Read current state

Read these three sources to understand what happened:

1. `.context/current-focus.md` — current file contents
2. Latest file in `log/` — most recent session log (if one was created)
3. `git log --oneline -10` — recent commits for concrete evidence of work done

Also note today's date for week rollover detection.

### Step 2: Detect week rollover

Compare the `w/c` date in `## This Week's Focus (w/c YYYY-MM-DD)` against today's date.

- If today is in a **new week** (Monday-based), flag that weekly sections need updating.
- If same week, skip weekly section updates.

Week rollover means: Primary Goal, Active Projects Top 3, Waiting On, Upcoming Deadlines, and Key Meetings may all need refreshing.

### Step 3: Draft session summary

From the session context (conversation history, commits, log), draft a summary in the **same bullet-point format** as existing entries:

```markdown
### Last Session Summary (YYYY-MM-DD — [Short Title])
- [What was done, in bullet points]
- [Key decisions or outputs]
- [Files/commits if relevant]
```

Keep it concise — 3-6 bullet points. Match the style of existing entries.

### Step 4: Ask targeted questions (2-4 max)

Ask only what's needed. Skip questions where the answer is obvious from context.

**Always ask:**
1. "Does this session summary look right?" (show the draft)
2. "Any open loops to add or check off?" (show current list with proposed changes marked)

**Ask only if relevant:**
3. "How are you feeling about work?" — only if Mental State is still a placeholder (`[Optional: ...]`)
4. "Has your primary goal or top 3 changed?" — only on **week rollover**

Present questions concisely with proposed answers. Let the user confirm or adjust.

### Step 5: Apply the update

Use `Edit` to make targeted changes. **Never rewrite the whole file.**

#### Session rotation rules

- **Rename** the current `### Last Session Summary (...)` to `### Previous Session (...)`
- **Insert** the new `### Last Session Summary (...)` in its place
- **Keep a maximum of 4 session entries** in Recent Context (1 Last + 3 Previous)
- If there are already 4 entries, **delete the oldest** Previous Session
- Preserve the exact header format: `### Last Session Summary (YYYY-MM-DD — Title)` for the newest, `### Previous Session (YYYY-MM-DD — Title)` for older ones

#### Open loop management

- **Check off** items that were completed this session (change `- [ ]` to `- [x]`)
- **Remove** items marked `[x]` from previous sessions (they've been acknowledged)
- **Add** new open loops identified during the session
- Keep the intro line: `Things I started but haven't finished:`

#### Other updates

- Update **Mental State** if the user provided one
- Update **weekly sections** if week rollover was detected and the user confirmed changes
- Update **Quick Reference** if meetings or paper revisions changed
- Update **Waiting On** if new blockers emerged or old ones resolved

### Step 6: Confirm

Report what was changed:

```
Updated .context/current-focus.md:
- Session: [title] added to Recent Context
- Open loops: [N checked off, M added]
- [Any other changes]
```

If no session log was created this session, offer: "Want me to run `/session-log` too?"

## Integration with Other Skills

| Skill | Relationship |
|-------|-------------|
| `/session-log` | Creates the detailed log; `/update-focus` updates the working memory. Often run together. |
| `/save-context` | For ad-hoc saves to any context file. Defers to `/update-focus` for structured focus updates. |
| `vault sync (edit vault files directly)` | Updates `projects/_index.md` and vault. For full session-level focus updates, defers to `/update-focus`. |

## Example Interaction

**Claude:** Here's what I'd update in `current-focus.md`:

**Session summary:**
```
### Last Session Summary (2026-02-08 — Update Focus Skill)
- Created `/update-focus` skill for structured current-focus.md updates
- Updated stop hook, session-log, and update-context with cross-references
- Updated CLAUDE.md skills list (16 → 17)
```

**Open loops — proposed changes:**
- [x] ~~Commit all pending changes~~ (done this session)
- [ ] Test new skills on CAPE-MOBO or MRes paper *(keep)*
- [ ] Try replication protocol on a real paper *(keep)*
- **New:** [ ] Test `/update-focus` skill end-to-end

Does this look right? Any open loops to add or change?

**the user:** Looks good, also check off the replication one, I decided to skip it.

**Claude:** Got it. *[Applies edits]* Updated `.context/current-focus.md`:
- Session: "Update Focus Skill" added to Recent Context
- Open loops: 2 checked off, 1 added
- Previous sessions rotated (oldest dropped)

Want me to run `/session-log` too?


---

## update-project-doc

**Source:** `skills/update-project-doc/SKILL.md`

---
name: update-project-doc
description: "Use when you need to update a project's own CLAUDE.md, README.md, or docs/ to reflect current state."
allowed-tools: Read, Edit, Write, Glob, Grep, Bash(ls*), Bash(git log*), Bash(git diff*), Bash(readlink*), Bash(wc*), Bash(date*), AskUserQuestion
argument-hint: (no arguments)
---

# Update Project Doc — Refresh Stale Documentation

> Scan a project's documentation files and update sections that have drifted from reality: file trees, timestamps, bibliography counts, next steps, skill/hook tallies, and more.

## When to Use

- After significant project work (new files, completed milestones, structural changes)
- During `/session-close` when offered
- When the user says "update project docs", "refresh docs", "sync my docs", "update my README"
- Periodically to keep documentation accurate

## What It Does NOT Do

- Never rewrites research content (hypotheses, arguments, literature, design decisions)
- Never deletes sections — only updates factual/structural content within existing sections
- Never creates new documentation files — only updates existing ones

---

## Protocol

### Step 1: Detect Documentation Files

Find all documentation files in the project:

1. Check for `CLAUDE.md` in project root
2. Check for `README.md` in project root
3. Scan `docs/` and `docs/*/` for `.md` files containing file trees or counts
4. Note which files exist — only update what's present

**Special case:** Some projects (e.g., the political information paper) have no `CLAUDE.md` because they use a committed `README.md` as their primary project documentation instead. This is intentional for repos meant to be shared or published. In these cases, treat `README.md` as the main documentation file and apply all the same checks to it.

Read each detected file to understand its current content.

### Step 2: Gather Current State

Collect the actual state of the project:

1. **File tree** — use `ls -R` or `Glob` to build the actual directory structure (respect `.gitignore` patterns, skip `out/`, `__pycache__/`, `.venv/`, `node_modules/`)
2. **Recent git history** — `git log --oneline -20` for recent commits
3. **Session logs** — read the latest 1-2 files in `log/` (if the directory exists)
4. **Bibliography count** — count entries in any `.bib` file(s): `grep -c '@' *.bib`
5. **Symlink targets** — `readlink` on any documented symlinks
6. **Context files** — read `.context/current-focus.md` or `.context/project-recap.md` if present

**Task Management only** (detected by presence of `skills/` directory):
7. **Skill count** — count directories in `skills/` that contain `SKILL.md`
8. **Hook count** — count `.sh` files in `hooks/` (if present)
9. **Skill lengths** — `wc -l skills/*/SKILL.md` to identify bloated skills

**Leanness data** (all projects):
10. **CLAUDE.md line count** — `wc -l CLAUDE.md`
11. **CLAUDE.md section sizes** — count lines per `##` section
12. **README.md line count** — `wc -l README.md`
13. **SKILL.md line counts** — (Task Management only) `wc -l skills/*/SKILL.md`
14. **Duplication scan** — check if CLAUDE.md content duplicates what's already in README.md, docs/, or .context/ files
15. **Agent line counts** — `wc -l .claude/agents/*.md` (if present)
16. **Context file line counts** — `wc -l .context/*.md` (if present)

### Step 3: Run Staleness Checks

Compare gathered state against documented content. Flag any mismatches:

| Check | How to Detect |
|-------|--------------|
| **File tree** | Generate actual tree, compare against any tree/structure block in docs (look for ``` blocks or indented listings with file paths) |
| **Timestamps** | Flag "Last updated", "w/c", or date stamps older than 7 days |
| **Bibliography count** | Compare actual `.bib` entry count vs any documented count (e.g., "42 references") |
| **Next steps / roadmap** | Cross-reference items against recent commits and session logs — flag items that appear completed |
| **Manuscript status** | Flag sections marked "TODO", "incomplete", or "placeholder" that now have content |
| **Symlinks** | Verify documented symlink targets still resolve with `readlink` |
| **Skill/hook counts** | (Task Management only) Compare actual count vs documented numbers in CLAUDE.md, README.md, and `.tex` files |
| **Venue/target info** | If CLAUDE.md documents a target journal, check it matches `.context/projects/_index.md` (if accessible) |

### Step 3b: Leanness Audit

Using the data gathered in Step 2 (items 10-14), check infrastructure file sizes against thresholds. This applies to **all projects**, not just Task Management.

| File | Threshold | What to flag | Fix |
|------|-----------|-------------|-----|
| `CLAUDE.md` | > 200 lines total | Current line count | Extract reference sections to `docs/`, replace with pointers (see `lean-claude-md` rule) |
| `CLAUDE.md` sections | Any `##` section > 15 lines of reference material | Section name + line count | Extract to `docs/` with a one-line summary + link |
| `CLAUDE.md` duplication | Content duplicated from README/docs/.context | Which content is duplicated and where | Keep only the pointer in CLAUDE.md |
| `README.md` | > 300 lines total | Current line count | Extract long sections to `docs/` |
| `SKILL.md` files | > 300 lines each (TM only) | File name + line count | Move templates/examples/report formats to `references/` or `templates/` subdirectory |
| Project agents (`.claude/agents/*.md`) | > 400 lines each | File name + line count | Extract verbose prompt sections to companion files |
| Context files (`.context/*.md`) | > 200 lines each | File name + line count | Archive stale content, keep current |

**What counts as "reference material"** (extractable): assessment guidelines, detailed literature notes, long examples, report templates, checklists, reviewer feedback.

**What does NOT count** (keep in place): safety rules, conventions, folder structure trees, session continuity pointers.

Present leanness findings separately from staleness findings in Step 4.

### Step 4: Propose Changes

Present findings grouped by file:

```
Staleness report for [Project Name]:

CLAUDE.md:
  - File structure tree is outdated (missing: X, Y; removed: Z)
  - Skill count says 23, actual is 26
  - "Last updated" date is 3 weeks old

README.md:
  - Directory structure block needs updating
  - Next steps: "Write introduction" appears completed (commit abc1234)
  - Bibliography count says 38, actual is 42

docs/overview.md:
  - No issues detected

Leanness:
  - CLAUDE.md: 237 lines (threshold: 200) — ## Assessment section is 42 lines of guidelines
  - README.md: OK (189 lines)
```

If nothing is stale, report that and stop.

### Step 5: Ask for Confirmation

#### Step 5a: Staleness Fixes

Use `AskUserQuestion` to let the user approve, modify, or skip staleness fixes:

- **Apply all** — update everything proposed
- **Select by file** — choose which files to update
- **Skip** — make no changes

#### Step 5b: Offer Leanness Fixes

If Step 3b found leanness issues, present each as an individually actionable item:

```
Leanness fixes available:

| # | File | Issue | Current | Fix |
|---|------|-------|---------|-----|
| 1 | CLAUDE.md | >200 lines | 237 | Extract ## Assessment section → docs/ |
| 2 | skills/X/SKILL.md | >300 lines | 382 | Move checklists → references/ |
```

Use `AskUserQuestion` with `multiSelect: true`:
- **Question:** "Which leanness fixes do you want to apply?"
- One option per fix with current size and proposed outcome
- Include an **"All of them"** option as the first choice

**Do not defer or merely report leanness findings.** Always present them as actionable items alongside staleness fixes.

### Step 6: Apply and Report

For each approved change:

1. Use **targeted `Edit` operations** — never rewrite entire files
2. Preserve all surrounding content
3. When updating file trees, match the existing formatting style (├──, |--, indented, etc.)
4. When updating counts, find the exact number and replace it
5. When marking next-step items as done, use strikethrough (~~item~~) rather than deleting

After all edits, print a summary:

```
Updated project docs:
  CLAUDE.md:  file tree, skill count (23 → 26)
  README.md:  directory structure, bib count (38 → 42), 1 next-step marked complete
  Total: 5 edits across 2 files
```

---

## Key Rules

1. **Targeted edits only** — never rewrite entire files. Use `Edit` with precise `old_string` / `new_string`.
2. **Preserve research content** — hypotheses, questions, literature reviews, design decisions, and arguments are sacred. Only update factual/structural sections.
3. **Always show before applying** — never make silent edits. The proposal step is mandatory.
4. **Match existing style** — if the project uses `├──` trees, don't switch to `|--`. If counts use "X total", don't change to "X skills".
5. **Works in any project** — not just Task Management. Adapt checks to what's present.
6. **Idempotent** — running twice in a row should produce no changes the second time.

## Cross-References

- `/session-close` — offers to run this skill at Step 3.5
- `/sync-repo private` — Task Management-specific superset: propagates counts across all private TM docs including LaTeX files. Run after this skill when in the TM project.
- `vault sync (edit vault files directly)` — syncs state to the central context library (complementary; run after this)
- `/update-focus` — updates `current-focus.md` (different purpose: session state, not doc accuracy)


---

## validate-bib

**Source:** `skills/validate-bib/SKILL.md`

---
name: validate-bib
description: "Cross-reference \\cite{} keys against .bib files or embedded \\bibitem entries. Finds missing, unused, and typo'd citation keys. Deep verification mode spawns parallel agents for DOI/metadata validation at scale. Read-only in standard mode."
allowed-tools: Read, Glob, Grep, Task, Write, Bash(mkdir*), Bash(ls*), Bash(rm*)
argument-hint: [project-path or tex-file]
---

# Bibliography Validation

**Read-only skill.** Never edit source files — produce a categorised report only.

**Citation key rule:** the user's existing keys always take precedence. They come from Paperpile (his reference management system) and are canonical. When suggesting replacements (typo corrections, preprint upgrades, metadata fixes), always keep the user's key and update the `.bib` entry metadata around it — never suggest renaming a key to match some "standard" format.

## When to Use

- Before compiling a final version of a paper
- After adding new citations to check nothing was missed
- When `biber`/`bibtex` reports undefined citations
- As part of a pre-submission checklist (pair with `/proofread`)

## When NOT to Use

- **Finding new references** — use `/literature` for discovery
- **Building a bibliography from scratch** — use `/literature` with `.bib` generation
- **General proofreading** — use `/proofread` (which also flags citation format issues)

## Phase 0: Session Log (Suggested)

Bibliography validation with preprint staleness checks can be context-heavy (OpenAlex lookups, web searches for published versions). Before starting, **suggest** running `/session-log` to capture prior work as a recovery checkpoint. If the user declines, proceed without it.

## Convention

**Default bibliography file is `paperpile.bib`** — this is the standard across all projects (per the `/latex` skill convention). However, the skill also supports:

- Any `.bib` file found in the same directory as the `.tex` files being audited
- Embedded bibliographies using `\begin{thebibliography}` / `\bibitem{key}` blocks
- Both external and embedded simultaneously (rare but possible)

## Bibliography Detection

At the start of validation, detect which bibliography method the project uses:

### 1. External `.bib` file (standard)

Look for `.bib` files in the project directory. Priority order:
1. `paperpile.bib` (preferred — standard naming convention across all projects)
2. Any other `.bib` file in the same directory as the `.tex` files

If **multiple `.bib` files** are found, validate all of them and produce a combined report. Note which file each issue belongs to. If `paperpile.bib` exists alongside other `.bib` files, flag the extras as a potential cleanup opportunity (the project may have migrated from a different naming convention).

Full validation applies: cross-reference checks **and** quality checks.

### 2. Embedded `\begin{thebibliography}` / `\bibitem{key}`

Some LaTeX documents define references inline rather than using an external `.bib` file. Detect by scanning `.tex` files for `\begin{thebibliography}`.

Extract keys from `\bibitem` entries:
- `\bibitem{key}` — standard form, key is the argument in braces
- `\bibitem[label]{key}` — optional label form (e.g., `\bibitem[Smith et al., 2020]{smith2020}`), key is in the **second** set of braces

Only **cross-reference checks** apply (missing keys, unused keys, typos). Quality checks (required fields, year, author formatting) are **skipped** because embedded bibliographies don't have structured metadata.

### 3. Both (rare)

If a project has both a `.bib` file and `\begin{thebibliography}` blocks, validate both:
- Run full validation on the `.bib` file
- Run cross-reference checks on `\bibitem` entries
- Merge both key sets when checking for missing citations

## Workflow

1. **Find files**: Locate all `.tex` files in the project
2. **Detect bibliography type**: Check for `.bib` files and/or `\begin{thebibliography}` blocks
3. **Extract citation keys from .tex**: Scan for all citation commands
4. **Extract entry keys from bibliography source(s)**:
   - External: Parse all `@type{key,` entries from `.bib` file(s)
   - Embedded: Parse all `\bibitem{key}` and `\bibitem[label]{key}` entries
5. **Cross-reference**: Compare the two sets
6. **Quality checks**: Validate `.bib` entry completeness (external only)
7. **Produce report**: Write results to stdout (or save if requested)

## Citation Commands to Scan

Scan `.tex` files for all of these patterns:

| Command | Example |
|---------|---------|
| `\cite{key}` | Basic citation |
| `\citet{key}` | Textual: Author (Year) |
| `\citep{key}` | Parenthetical: (Author, Year) |
| `\textcite{key}` | biblatex textual |
| `\autocite{key}` | biblatex auto |
| `\parencite{key}` | biblatex parenthetical |
| `\citeauthor{key}` | Author name only |
| `\citeyear{key}` | Year only |
| `\nocite{key}` | Include in bibliography without in-text citation |

Also handle **multi-key citations**: `\citep{key1, key2, key3}`

## Cross-Reference Checks

### Critical: Missing Entries

Citation keys used in `.tex` but not defined in the bibliography source (`.bib` file or `\bibitem` entries).

These will cause compilation errors.

### Warning: Unused Entries

Keys defined in the bibliography source but never cited in any `.tex` file.

Not errors, but may indicate:
- Forgotten citations (should they be `\nocite`?)
- Leftover entries from earlier drafts
- Entries intended for a different paper

### Warning: Possible Typos (Fuzzy Match)

For each missing key, check if a similar key exists in the bibliography using edit distance:
- Edit distance = 1: Very likely a typo
- Edit distance = 2: Possibly a typo
- Flag these with the suggested correction

Common typo patterns:
- Year off by one: `smith2020` vs `smith2021`
- Missing/extra letter: `santanna` vs `sant'anna` vs `santana`
- Underscore vs camelCase: `smith_jones` vs `smithjones`

## Quality Checks on .bib Entries

**These checks apply only to external `.bib` files.** Embedded bibliographies lack structured metadata, so quality checks are skipped for them.

### Required Fields by Entry Type

| Entry Type | Required Fields |
|-----------|----------------|
| `@article` | author, title, journal, year |
| `@book` | author/editor, title, publisher, year |
| `@incollection` | author, title, booktitle, publisher, year |
| `@inproceedings` | author, title, booktitle, year |
| `@techreport` | author, title, institution, year |
| `@unpublished` | author, title, note, year |
| `@phdthesis` | author, title, school, year |

### Year Reasonableness

- Flag entries with year < 1900 or year > current year + 1
- Flag entries with no year at all

### Author Formatting

- Check for inconsistent author formats within the file
- **Flag entries where author field contains "and others" or "et al."** — this is never valid in BibTeX. All authors must be listed explicitly. Severity: **Warning**.
- Flag entries with organisation names that might need `{{braces}}` to prevent splitting

### DOI Resolution (optional — triggered by `--verify-dois` flag or when issues are suspected)

**Preferred method: biblio MCP `scholarly_verify_dois`.** Collect all DOIs from the `.bib` file and call `scholarly_verify_dois` (up to 50 per call). This batch-verifies each DOI against all enabled sources (OpenAlex, Scopus, WoS). Results:
- **VERIFIED** (2+ sources confirm) — DOI is valid, metadata can be trusted
- **SINGLE_SOURCE** (1 source only) — DOI exists but warrants a manual spot-check
- **NOT_FOUND** — DOI not found in any source; resolve manually via WebFetch

**Fallback for NOT_FOUND DOIs:** Resolve via `https://doi.org/[DOI]` and confirm the returned metadata matches the entry:

1. **Title match**: Does the DOI landing page title match the `.bib` title?
2. **Author match**: Does the first author on the landing page match the `.bib` first author?
3. **Journal match**: Does the venue match?

Flag mismatches as:
- **Warning: DOI mismatch** — DOI resolves to a different paper than claimed. This usually means the DOI is wrong (adjacent DOI in the same journal volume) or the authors are wrong (conflation of researchers in the same subfield).

This check catches:
- Wrong DOIs (e.g., off-by-one in the DOI suffix)
- Author conflation (real researchers incorrectly attributed to a paper)
- Metadata copied from secondary sources without verification

For manual WebFetch resolution, process in batches of 5 to avoid rate limiting. Only flag confirmed mismatches — if the DOI cannot be resolved (404, timeout), note it as "unresolvable" at Info level.

### Preprint Staleness Check

**For every entry that looks like a preprint**, check whether a peer-reviewed version has since been published. Full detection signals, lookup protocol, and classification: [`references/preprint-check.md`](references/preprint-check.md)

## Severity Levels

| Level | Meaning |
|-------|---------|
| **Critical** | Missing entry for a cited key — will cause compilation error |
| **Warning** | Unused entry, possible typo, missing required field |
| **Info** | Year oddity, formatting suggestion, bibliography type note |

## Bibliography Output

After validation, offer these actions if applicable:

- **Embedded bibliography → offer to create `paperpile.bib`**: If the project uses `\begin{thebibliography}`, offer to extract the references into a proper `paperpile.bib` file (one `@misc` entry per `\bibitem`, with the full text as a `note` field). The author can then enrich the entries with proper metadata.
- **Non-standard `.bib` name → offer to rename**: If the existing `.bib` file is not named `paperpile.bib`, offer to rename it to `paperpile.bib` and update the `\bibliography{}` command in the `.tex` file.

These are **offers only** — do not make changes without explicit confirmation.

## Report Format

Full report template with all sections: [`references/report-template.md`](references/report-template.md)

Sections: Summary table → Critical (missing entries) → Warning (typos, unused, missing fields, DOI mismatches, stale preprints) → Info (year issues) → Limitations (for embedded bibliographies).

## Optional: Metadata Verification via Biblio MCP

When missing entries or suspicious metadata are flagged, use the biblio MCP tools:

- **`scholarly_search`** — search by title to find the correct entry across OpenAlex + Scopus + WoS
- **`scholarly_verify_dois`** — batch-verify DOIs across all sources (preferred over manual DOI resolution)
- **`openalex_lookup_doi`** — look up full metadata for a specific DOI

For Python client fallback (citation networks, institution analysis): [`references/openalex-verification.md`](references/openalex-verification.md)

## Deep Verification Mode (Parallel, Disk-Based)

Triggered by: `--deep-verify` flag, 40+ entries, or "deep verify" / "verify all references". Spawns parallel sub-agents that verify batches and write results to disk. Full architecture, batch JSON format, and assembly: [references/deep-verify.md](references/deep-verify.md)

## Council Mode (Optional)

For high-stakes submissions. Trigger: "council validate-bib", "thorough bib check". Full details: [references/council-mode.md](references/council-mode.md)

## Quality Scoring

When producing a full validation report, apply numeric quality scoring using the shared framework:

- **Framework:** [`../shared/quality-scoring.md`](../shared/quality-scoring.md) — severity tiers, thresholds, verdict rules

Map validation findings to the framework tiers:
- **Critical** (-15 to -25): Missing entry for a cited key (compilation error)
- **Major** (-5 to -14): DOI mismatch, stale preprint with published version available, "et al." in author field
- **Minor** (-1 to -4): Missing optional fields, year oddities, unused entries

Compute the score and include the Score Block in the report after the summary table.

## Cross-References

- **`/proofread`** — For overall paper quality including citation format
- **`/literature`** — For finding and adding new references (includes full OpenAlex workflows)
- **`/latex`** — For compilation with reference checking
- **`/latex-autofix`** — For compilation and error resolution. Run after fixing bibliography issues to verify citations compile cleanly.

