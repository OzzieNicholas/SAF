# SAF Chinese Manuscript Rewrite Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produce a scientifically traceable, anonymous Chinese SAF manuscript package whose text, equations, tables, figures, bibliography, LaTeX, and compiled PDF are mutually consistent and ready for later adaptation to a specific journal.

**Architecture:** Treat experiment artifacts as the source of numerical truth, freeze one canonical rewrite run in a manifest, and derive every manuscript representation from that evidence set. Keep scientific content in an anonymous general-journal manuscript, keep unknown author/journal metadata in a separate submission checklist, and retain the previous manuscript in a recoverable archive.

**Tech Stack:** Python 3.12 (`saf` conda environment), PyTorch, NumPy, Matplotlib, project experiment CLIs, Markdown, XeLaTeX/ctex, BibTeX with GB/T 7714 numeric style, Poppler/PDF inspection tools, Git.

---

## File Map

- `deliverables/archive/paper/2026-08-14-pre-rewrite/`: recoverable copy of the retired manuscript, PDF, LaTeX, and figures.
- `artifacts/archive/paper-rewrite/2026-08-14-pre-rewrite/`: snapshots of the baseline, ablation, failure, regression, and figure-QA evidence before canonical reruns.
- `artifacts/runs/paper_rewrite/latest.json`: machine-readable canonical run identifiers, hashes, statistics, and source paths for this manuscript.
- `governance/results.md`: project result ledger synchronized to the chosen canonical runs.
- `deliverables/paper/paper.md`: complete anonymous Chinese manuscript with English title and bilingual abstracts.
- `deliverables/paper/tables.md`: six publication tables with evidence paths and statistical definitions.
- `deliverables/paper/evidence_manifest.md`: human-readable claim-to-artifact and number-to-command map.
- `deliverables/paper/submission_checklist.md`: later-stage journal, author, affiliation, funding, and declarations interface; no administrative placeholders remain in the manuscript.
- `deliverables/paper/figures/captions.md`: self-contained bilingual-ready figure captions and evidence provenance.
- `deliverables/paper/figures/fig01_*.{png,pdf}` through `fig10_*.{png,pdf}`: final 600 dpi and vector figures.
- `tools/figures/style.py`: final physical dimensions, fonts, semantic colors, and export settings.
- `tools/figures/fig01_framework.py` through `tools/figures/fig10_failure.py`: evidence-backed figure composition.
- `tools/figures/README.md`: final figure rebuild and QA procedure.
- `deliverables/paper/latex/main.tex`: anonymous two-column Chinese engineering-journal shell.
- `deliverables/paper/latex/body.tex`: manuscript body, equations, tables, figures, and citations.
- `deliverables/paper/latex/references.bib`: verified bibliographic records only.
- `deliverables/paper/SAF_中文论文匿名稿.pdf`: compiled manuscript delivered to the user.
- `tools/paper/qa_manuscript.py`: deterministic checks for missing assets, stale numbers, citation coverage, administrative placeholders, red-line claims, and Markdown/LaTeX consistency.
- `tests/test_paper_qa.py`: focused tests for manuscript QA failure modes.

### Task 1: Preserve the Existing Manuscript and Evidence

**Files:**
- Move: `deliverables/paper/**` to `deliverables/archive/paper/2026-08-14-pre-rewrite/`
- Copy: `artifacts/runs/baselines/latest.json`
- Copy: `artifacts/runs/ablation/latest.json`
- Copy: `artifacts/runs/failure_audit/failure.json`
- Copy: `artifacts/runs/failure_audit/fig10_case.npz`
- Copy: `artifacts/runs/regression/latest.json`
- Copy: `artifacts/runs/figure_qa/**`
- Create: `artifacts/archive/paper-rewrite/2026-08-14-pre-rewrite/README.md`

- [ ] **Step 1: Resolve and validate archive paths**

Run:

```powershell
$repo = (Resolve-Path '.').Path
$oldPaper = (Resolve-Path 'deliverables/paper').Path
$paperArchive = Join-Path $repo 'deliverables/archive/paper/2026-08-14-pre-rewrite'
$runArchive = Join-Path $repo 'artifacts/archive/paper-rewrite/2026-08-14-pre-rewrite'
@($oldPaper, $paperArchive, $runArchive) | ForEach-Object {
  if (-not $_.StartsWith($repo, [System.StringComparison]::OrdinalIgnoreCase)) { throw "Archive path escaped repository: $_" }
}
```

Expected: command exits with code `0`; all three absolute paths remain under `D:\Work\SAF`.

- [ ] **Step 2: Move the old paper tree and snapshot overwrite-prone run artifacts**

Run once with PowerShell `Move-Item`/`Copy-Item`, retaining original filenames and directory structure. Do not include or modify `docs/other/GPT_SAF.md`.

Expected: `deliverables/paper` no longer contains the retired active稿; the archive contains `draft.md`, `SAF_中文论文初稿.pdf`, LaTeX, and all ten PNG/PDF pairs; all current `latest.json` files remain in place and have archive copies.

- [ ] **Step 3: Record archive provenance**

Write `README.md` with the source commit `c95cf00`, archive timestamp, original relative paths, and SHA-256 hashes from:

```powershell
Get-ChildItem 'deliverables/archive/paper/2026-08-14-pre-rewrite','artifacts/archive/paper-rewrite/2026-08-14-pre-rewrite' -File -Recurse |
  Get-FileHash -Algorithm SHA256
```

Expected: every archived file has a reproducible hash and the old manuscript is recoverable.

- [ ] **Step 4: Recreate only the active directory skeleton**

Run:

```powershell
New-Item -ItemType Directory -Force 'deliverables/paper/figures','deliverables/paper/latex' | Out-Null
```

Expected: active directories exist but contain no retired manuscript artifacts.

### Task 2: Rerun the Canonical Conflicting Experiments

**Files:**
- Regenerate: `artifacts/runs/baselines/latest.json`
- Regenerate: `artifacts/runs/ablation/latest.json`
- Regenerate: `artifacts/runs/failure_audit/failure.json`
- Regenerate: `artifacts/runs/failure_audit/fig10_case.npz`
- Preserve: immutable run-ID JSON siblings emitted by `tools.artifacts.write_result`

- [ ] **Step 1: Verify runtime, datasets, and GPU before training**

Run sequentially:

```powershell
conda run -n saf python -c "import torch; print(torch.__version__); print(torch.cuda.is_available()); print(torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU')"
conda run -n saf python -c "from pathlib import Path; required=['data/processed/fusion360_full','data/processed/procedural_v1']; assert all(Path(p).exists() for p in required); print('datasets ready')"
```

Expected: Python uses the `saf` environment, CUDA is available on the RTX 4060, and both materialized datasets exist. Stop rather than silently switching a canonical paper run to CPU if CUDA is unavailable.

- [ ] **Step 2: Rerun the five-method baseline on one frozen split**

Run:

```powershell
conda run -n saf python tools/eval_baselines.py --max-models 400 --epochs 80 --seed 0
```

Expected: exit `0`; JSON reports 80 held-out models, 6,033 points for the current frozen dataset, five method rows, bootstrap configuration, a nonempty `run_id`, and a positive paired ConvONet-minus-ray confidence interval.

- [ ] **Step 3: Rerun the shape-context ablation**

Run:

```powershell
conda run -n saf python tools/eval_ablation.py --max-models 400 --epochs 60 --seed 0
```

Expected: exit `0`; JSON contains exactly `no_shape`, `local`, `lite`, and `pooled`, with `lite` outperforming `no_shape`; do not impose the old rounded values as acceptance criteria.

- [ ] **Step 4: Rerun five-seed failure analysis**

Run:

```powershell
conda run -n saf python tools/failure_cases.py --max-models 400 --epochs 80 --seed 0 --seeds 5 --figure-case 116082_b59d8605_0002
```

Expected: exit `0`; aggregate means/stds, the four `n_viable` bins, retained run envelope, and the fixed held-out Figure 10 case are present.

- [ ] **Step 5: Validate artifact envelopes and internal arithmetic**

Run a read-only Python assertion script that checks each `latest.json` has `artifact_schema_version`, `kind`, `run_id`, `git_commit`, `input_digest`, and that `error_rate = false_pos_rate + false_neg_rate` within stored rounding tolerance.

Expected: all assertions pass; no paper number is selected from terminal logs or old screenshots.

### Task 3: Freeze the Manuscript Evidence Set

**Files:**
- Create: `artifacts/runs/paper_rewrite/latest.json`
- Modify: `governance/results.md`
- Create: `deliverables/paper/evidence_manifest.md`

- [ ] **Step 1: Collect canonical and stable results**

Read baseline, ablation, failure, regression, true-area, E5, H1/H2/H3/H5/E8, label-audit, and dataset-statistics artifacts. For stable ledger-only results, record the reproducer command and the exact `governance/results.md` row; for JSON-backed results, record path, `run_id`, SHA-256, split, seed count, sample count, aggregation unit, and rounding rule.

- [ ] **Step 2: Write the machine-readable paper run manifest**

Use `tools.artifacts.write_result` to emit a schema with these top-level keys:

```json
{
  "manuscript_version": "2026-08-14-rewrite-v1",
  "scope": "semantic-C, part-body occlusion, finite spherical tool, discrete straight approaches",
  "canonical_runs": {},
  "stable_results": {},
  "rounding": {"f1": 3, "rates_percent": 1, "correlation": 3},
  "administrative_metadata": "intentionally external to anonymous manuscript"
}
```

Expected: `latest.json` and an immutable run-ID sibling exist; paths and hashes resolve to current artifacts.

- [ ] **Step 3: Synchronize `governance/results.md`**

Replace only the baseline, ablation, and failure values and their statistical descriptions if reruns differ. Preserve frozen semantics and unrelated ledger content. Explicitly distinguish point-pooled F1, per-model mean/std, seed-level mean/std, and paired bootstrap confidence intervals.

Expected: the ledger contains no stale `0.925`, old ablation tuple, or old FP/FN decomposition when they disagree with the canonical run.

- [ ] **Step 4: Write the human-readable evidence map**

For every abstract/conclusion claim and every table/figure number, list: claim ID, displayed value, metric definition, sample, source artifact/run ID, reproducer command, and limitation. Include explicit rows for proxy-not-certification, count-proxy versus true area, finite-radius versus ray, cross-domain scope, and implementation-specific `~112x` timing.

Expected: a reviewer can trace every quantitative sentence without reading Git history.

- [ ] **Step 5: Commit the evidence checkpoint**

Run:

```powershell
git add deliverables/archive/paper/2026-08-14-pre-rewrite artifacts/archive/paper-rewrite/2026-08-14-pre-rewrite artifacts/runs/baselines artifacts/runs/ablation artifacts/runs/failure_audit artifacts/runs/paper_rewrite governance/results.md deliverables/paper/evidence_manifest.md
git commit -m "docs(paper): freeze canonical manuscript evidence"
```

Expected: commit includes only manuscript evidence files and excludes `docs/other/GPT_SAF.md`.

### Task 4: Verify and Curate the Bibliography

**Files:**
- Create: `deliverables/paper/latex/references.bib`
- Create: `deliverables/paper/reference_audit.md`
- Read: `docs/references/references_cn.md`
- Read: archived `latex/references.bib`

- [ ] **Step 1: Define reference inclusion roles**

Assign each retained work exactly one role: AM support/removal motivation, geometric accessibility/IMF, learning-based manufacturing accessibility, neural shape representation, or dataset. Remove citations that are only generic background and never support a manuscript sentence.

- [ ] **Step 2: Verify bibliographic records against primary pages**

For every DOI, compare title, full author list, venue, year, volume, issue, pages/article number, and DOI with the publisher or DOI landing page. For arXiv/dataset records, verify version-independent title/authors and stable URL. Record access date only for online-only items.

Expected: no metadata is inferred from an incomplete secondary citation.

- [ ] **Step 3: Handle incomplete Chinese candidates conservatively**

Include C2/C3/C4 from `docs/references/references_cn.md` only if all required fields are verified from an authoritative journal/DOI page. Otherwise record them under “检索过但未采用” in `reference_audit.md`, including the missing fields and search source.

- [ ] **Step 4: Write valid BibTeX and audit it**

Use stable ASCII citation keys, preserve Chinese titles/authors in UTF-8, and include DOI/URL only when verified. Run:

```powershell
rg -n "TBD|TODO|待补|unknown|et al\." deliverables/paper/latex/references.bib
```

Expected: no matches; each entry has sufficient fields for GB/T 7714 numeric output.

### Task 5: Rewrite the Scientific Manuscript and Tables

**Files:**
- Create: `deliverables/paper/paper.md`
- Create: `deliverables/paper/tables.md`
- Create: `deliverables/paper/submission_checklist.md`
- Create: `deliverables/paper/figures/captions.md`

- [ ] **Step 1: Write title, bilingual abstracts, and keywords**

The title names support-contact regions, finite-tool geometric accessibility, and shape-conditioned prediction without claiming “first”. The Chinese abstract follows objective-method-results-conclusion in one coherent paragraph; the English abstract carries the same numbers and boundaries. Use only canonical numbers from `evidence_manifest.md`.

Expected: no author, affiliation, funding, journal, email, or corresponding-author placeholder appears in `paper.md`.

- [ ] **Step 2: Write Introduction and Related Work**

Build the argument from post-processing accessibility to the insufficiency of support quantity, then state three bounded contributions: formal proxy semantics, auditable two-stage labeling, and shape-conditioned point/direction prediction. Compare directly with IMF, DeepMill, PARC, and Surfel CNN by object, output, supervision, and generalization mode; do not claim universal novelty.

- [ ] **Step 3: Write Problem Definition with complete notation**

Define part `P`, boundary, build direction, normals, overhang threshold, support-contact set, tool radius, candidate directions, line length, point-direction accessibility, point inaccessibility, and directional field before use. Include:

```tex
\mathcal S(P,\hat{\mathbf d})=\{p\in\partial P\mid \mathbf n(p)\cdot\hat{\mathbf d}< -\cos\theta_c\},
```

```tex
a(p,\mathbf v;r)=\mathbb I\!\left[\left((p+[0,L]\mathbf v)\oplus B_r\right)\cap\operatorname{int}(P)=\varnothing\right],
```

```tex
y(p)=1-\max_{\mathbf v\in\mathcal V}a(p,\mathbf v;r).
```

State explicitly that `y=1` is inaccessible and that point accessibility is existential over the discrete direction set.

- [ ] **Step 4: Write Method and reproducible pseudo-code**

Describe normalization, contact extraction, occupancy/distance field, Fibonacci lower-hemisphere directions, conservative screening, exact capsule-mesh boundary refinement, label audit, ConvONet-lite point head, direction head, loss, split, and inference. Distinguish frozen registry values from runtime wiring because `configs/params.yaml` is partly documentary.

- [ ] **Step 5: Write Data and Evaluation Protocol**

Report Fusion materialization (8,590), both-class count (1,553), imbalance, procedural role, Thingi10K selection (137 both-class, max 400 points/model), model-level splits, metric positive class, aggregation units, seeds, bootstrap, hardware, and configuration. Explain why point-pooled and per-model statistics answer different questions.

- [ ] **Step 6: Write Results in hypothesis order**

Present quantity/true-area contrast, matched pair, finite-radius effect, label quality, point prediction, baselines, ablation, cross-domain, directional field, timing magnitude, and failure boundary bins. Every paragraph ends with an interpretation no stronger than its evidence.

- [ ] **Step 7: Write Discussion, Limitations, and Conclusion**

Separate practical interpretation from six exclusions: build plate, support-support occlusion/removal sequence, holder/fixture, material mechanics, surface quality, and physical validation. Describe `~112x` only as an implementation-level amortized query magnitude. Conclude with the geometric-proxy contribution and concrete evidence, not a manufacturing certification claim.

- [ ] **Step 8: Write six publication tables and ten self-contained captions**

Tables cover nearest work, semantics, datasets, label quality, point baselines, and cross-domain/directional results. Captions identify dataset, sample, metric, color semantics, and key limitation without repeating results prose.

- [ ] **Step 9: Isolate unknown submission metadata**

Put journal choice, author order, affiliations, corresponding author, funding, author contributions, conflict statement, data/code URL, and AI-use statement in `submission_checklist.md` as later decisions. The anonymous scientific files contain finalized generic declarations only where facts are already known (for example, ethics not applicable to public geometry data).

- [ ] **Step 10: Commit the scientific text**

Run:

```powershell
git add deliverables/paper/paper.md deliverables/paper/tables.md deliverables/paper/evidence_manifest.md deliverables/paper/submission_checklist.md deliverables/paper/figures/captions.md deliverables/paper/latex/references.bib deliverables/paper/reference_audit.md governance/results.md
git commit -m "docs(paper): rewrite SAF manuscript and evidence tables"
```

Expected: commit excludes generated figures/PDF and `docs/other/GPT_SAF.md`.

### Task 6: Implement Manuscript QA Before Rendering

**Files:**
- Create: `tools/paper/qa_manuscript.py`
- Create: `tests/test_paper_qa.py`

- [ ] **Step 1: Write failing tests for high-risk manuscript defects**

Tests use temporary miniature paper trees and assert failure for: a missing figure pair, a citation used but absent from BibTeX, an unused BibTeX entry, `[作者]`/`待补` in scientific files, stale forbidden result tokens supplied by a deny-list, and prohibited claims such as `工艺认证`, `首创`, or `构建方向优化` when not inside an explicit negation/limitation context.

- [ ] **Step 2: Run focused tests and confirm failure**

Run:

```powershell
conda run -n saf python -m pytest tests/test_paper_qa.py -q
```

Expected: FAIL because `tools.paper.qa_manuscript` does not yet exist.

- [ ] **Step 3: Implement deterministic QA**

The CLI accepts `--paper-dir`, `--manifest`, and optional `--strict`; parses Markdown/TeX citation keys and BibTeX entry keys; verifies ten unique PNG/PDF pairs; checks administrative placeholders and red-line phrases in `paper.md`, `tables.md`, captions, and TeX; compares manifest-declared display strings across Markdown/TeX; and emits JSON diagnostics without modifying manuscript files.

- [ ] **Step 4: Run focused tests to green**

Run:

```powershell
conda run -n saf python -m pytest tests/test_paper_qa.py -q
```

Expected: all manuscript-QA tests pass.

### Task 7: Restyle and Regenerate All Ten Figures

**Files:**
- Modify: `tools/figures/style.py`
- Modify: `tools/figures/fig01_framework.py`
- Modify: `tools/figures/fig02_direction_dependence.py`
- Modify: `tools/figures/fig03_criterion.py`
- Modify: `tools/figures/fig04_two_stage.py`
- Modify: `tools/figures/fig05_network.py`
- Modify: `tools/figures/fig06_area_vs_access.py`
- Modify: `tools/figures/fig07_prediction_heatmap.py`
- Modify: `tools/figures/fig08_baselines_ablation.py`
- Modify: `tools/figures/fig09_direction_field.py`
- Modify: `tools/figures/fig10_failure.py`
- Modify: `tools/figures/README.md`
- Regenerate: `deliverables/paper/figures/fig01_*.{png,pdf}` through `fig10_*.{png,pdf}`

- [ ] **Step 1: Reload and apply the visualization skill requirements**

Before visual edits, re-read the complete `visualize` skill. Fix 175 mm full-width composition, 85 mm stress-preview behavior, 7.5 pt minimum type, Chinese font fallback, 600 dpi PNG, embedded-font vector PDF, semantic colors, and perceptually uniform continuous maps.

- [ ] **Step 2: Remove stale and presentation-only content from figure scripts**

Delete hard-coded baseline/ablation/failure numbers. Make Figures 8 and 10 fail closed unless canonical artifact schemas and run IDs match `artifacts/runs/paper_rewrite/latest.json`. Remove large internal titles, redundant prose boxes, decorative backgrounds, and repeated legends.

- [ ] **Step 3: Enforce one argument per figure**

Compose the ten figures exactly as: overall pipeline; build-direction contact change; semantic counterexamples; two-stage oracle and label stability; network architecture; quantity versus inaccessible fraction; held-out heatmaps; baseline and ablation; direction field; failure boundary-band analysis.

- [ ] **Step 4: Run the face-mapping test before expensive rendering**

Run:

```powershell
conda run -n saf python -m pytest tests/acceptance/test_figure_face_mapping.py -q
```

Expected: PASS; qualitative labels/predictions map to original mesh faces exactly.

- [ ] **Step 5: Generate figures sequentially**

Run each `fig01` through `fig10` script in numeric order, passing original Fusion/Thingi roots where required. Do not substitute procedural geometry when original meshes/checkpoints are unavailable.

Expected: exactly ten PNG/PDF pairs; PNGs report 600 dpi; PDFs have the intended physical width and embedded non-Type-3 fonts.

- [ ] **Step 6: Run automated figure QA and inspect the contact sheet**

Run:

```powershell
conda run -n saf python tools/figures/qa_figures.py --strict
```

Expected: `warnings=0`, `blank_images=0`. Visually inspect every row of `contact_sheet.png` at both widths for clipping, semantic color consistency, illegible labels, distorted geometry, and unsupported claims.

- [ ] **Step 7: Commit figure sources and outputs**

Run:

```powershell
git add tools/figures deliverables/paper/figures artifacts/runs/figure_qa tests/acceptance/test_figure_face_mapping.py
git commit -m "docs(paper): rebuild publication figures"
```

Expected: ten evidence-backed figure pairs and their QA report are committed; disposable checkpoints remain under `artifacts/cache` and are not staged.

### Task 8: Author the Anonymous LaTeX Manuscript

**Files:**
- Create: `deliverables/paper/latex/main.tex`
- Create: `deliverables/paper/latex/body.tex`
- Modify: `deliverables/paper/latex/references.bib`

- [ ] **Step 1: Build a generic anonymous journal shell**

Use `ctexart`, A4 two-column body, restrained margins, `amsmath`, `booktabs`, `graphicx`, `caption`, `algorithm2e`, `hyperref`, and `gbt7714` numeric bibliography. Omit author/affiliation/funding blocks rather than rendering placeholders. Keep the first page compact enough to expose the beginning of the introduction.

- [ ] **Step 2: Translate Markdown structure exactly into LaTeX**

Reproduce title, bilingual abstracts, equations, notation, algorithm, six tables, ten figures, discussion, declarations, and every citation. Use vector figure PDFs. Use `table*`/`figure*` only where full width materially improves legibility.

- [ ] **Step 3: Run source-level parity checks**

Compare section headings, displayed values from the evidence manifest, figure filenames, table titles, and citation keys between `paper.md` and TeX.

Expected: no scientific content exists only in one representation; line wrapping/layout markup may differ.

- [ ] **Step 4: Run manuscript QA before compile**

Run:

```powershell
conda run -n saf python tools/paper/qa_manuscript.py --paper-dir deliverables/paper --manifest artifacts/runs/paper_rewrite/latest.json --strict
```

Expected: no missing assets, citation mismatch, stale value, placeholder, or red-line claim.

### Task 9: Compile and Visually Verify the Final PDF

**Files:**
- Generate: `deliverables/paper/SAF_中文论文匿名稿.pdf`
- Generate temporary page renders under: `artifacts/cache/paper_pdf_qa/`
- Create: `artifacts/runs/paper_pdf_qa/latest.json`

- [ ] **Step 1: Run the required PDF artifact marker once**

Before the first PDF authoring operation, execute the exact marker command specified by the `pdf` skill with the bundled Node runtime. Record successful completion in the PDF QA artifact.

- [ ] **Step 2: Compile through the LaTeX workflow**

Use the bundled LaTeX compiler workflow from `deliverables/paper/latex/main.tex`, including enough passes for references and cross-references, then copy the successful output to `deliverables/paper/SAF_中文论文匿名稿.pdf`.

Expected: zero LaTeX errors, all citations resolved, no missing glyphs/images, and no overfull box that visibly intrudes into a margin/column.

- [ ] **Step 3: Render every page to PNG**

Use the PDF skill's Poppler rendering procedure at a legible inspection resolution. Record page count, page dimensions, file hashes, font inventory, and text-extraction status.

- [ ] **Step 4: Inspect every rendered page**

Check title/abstract balance, two-column flow, equation breaks, table rules, figure scale, captions, references, page numbers, Chinese and Latin fonts, widows/orphans, blank areas, overlap, crop, and final-page declarations. Recompile after every correction and re-render all affected pages.

- [ ] **Step 5: Run PDF structural checks**

Expected checks: one A4 page size throughout; embedded fonts; no Type 3 font; nonempty text extraction on text pages; exactly ten cited figures; no blank page; bookmarks/links do not cover text.

### Task 10: Final Scientific and Engineering Verification

**Files:**
- Modify as defects require: manuscript, tables, captions, figures, TeX, bibliography, QA artifacts

- [ ] **Step 1: Run stale-number and red-line scans**

Run targeted `rg` checks for archived/conflicting values and overclaim terms across active paper files. Manually inspect every match in a negation/limitation context; do not accept a raw keyword count as semantic validation.

- [ ] **Step 2: Run paper, figure, and focused repository tests**

Run sequentially:

```powershell
conda run -n saf python -m pytest tests/test_paper_qa.py tests/acceptance/test_figure_face_mapping.py tests/test_artifacts.py -q
conda run -n saf python tools/figures/qa_figures.py --strict
conda run -n saf python tools/paper/qa_manuscript.py --paper-dir deliverables/paper --manifest artifacts/runs/paper_rewrite/latest.json --strict
```

Expected: all checks pass.

- [ ] **Step 3: Run the complete project suite and acceptance gate**

Run sequentially:

```powershell
conda run -n saf python -m pytest -q
conda run -n saf python tests/gate.py --format md
```

Expected: tests pass. If `control_plane_spec` remains the sole gate failure, report it explicitly as a pre-existing governance/documentation blocker and do not misstate the project DoD as green; all scientific gates must remain passing.

- [ ] **Step 4: Review the final Git diff and file inventory**

Run:

```powershell
git status --short
git diff --check
git diff --stat c95cf00..HEAD
```

Expected: no whitespace errors, no accidental edit/stage of `docs/other/GPT_SAF.md`, no retired files in the active paper tree, and all required deliverables exist.

- [ ] **Step 5: Commit the final manuscript package**

Run:

```powershell
git add deliverables/paper tools/paper tests/test_paper_qa.py artifacts/runs/paper_pdf_qa
git commit -m "docs(paper): deliver anonymous SAF manuscript"
```

Expected: the commit contains Markdown, LaTeX/BibTeX, figures, PDF, checklists, and QA evidence; user-owned unrelated changes remain unstaged.

### Task 11: Delivery Audit

**Files:**
- Read: all active deliverables and verification outputs

- [ ] **Step 1: Confirm deliverable completeness**

Verify the final inventory includes `paper.md`, `tables.md`, `evidence_manifest.md`, `submission_checklist.md`, `reference_audit.md`, `latex/main.tex`, `latex/body.tex`, `latex/references.bib`, captions, ten PNG/PDF figure pairs, contact sheet, and compiled anonymous PDF.

- [ ] **Step 2: Report manuscript readiness honestly**

Summarize the scientific contribution, canonical evidence version, PDF page count, tests/QA run, and any residual limitations. Separate later metadata adaptation from research gaps: journal template, author list, affiliations, and funding are administrative; physical validation and broader geometry coverage are scientific extensions and are not fabricated in this draft.

- [ ] **Step 3: Provide direct local links**

Link the final PDF, Markdown, LaTeX entrypoint, evidence manifest, submission checklist, figure contact sheet, and archived old manuscript using absolute workspace paths.
