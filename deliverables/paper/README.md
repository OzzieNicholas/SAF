# SAF Paper Package

This directory is the single source of truth for the downstream paper
deliverable. SAF engineering code remains in src/, tests/, and tools/;
the paper pipeline consumes those interfaces and never defines engineering
semantics.

- manuscript/ contains Markdown/LaTeX sources.
- pipeline/ contains paper-only figure, PDF, QA, evidence, and Zotero tools.
- figures/ contains only the final canonical figure PNG/PDF pairs.
- outputs/ contains the final manuscript/submission PDFs.
- evidence/ contains small, sanitized canonical result manifests.
- reviews/ contains review and revision records.
- zotero/ contains the collection/key contract; PDFs and references.bib
  are intentionally external/generated.
- build/ is disposable and ignored.

The strict build entrypoint is `pipeline/build_paper.py --strict-zotero`.  It
freezes the machine evidence manifest, regenerates figures/QA, rebuilds the
integrity sidecar, compiles LaTeX, and copies the PDF to `outputs/`.  Use
`--skip-figures` or `--skip-latex` only for a staged local check; the final
paper gate remains strict.

Literature attachments live in the Zotero collection
几何可达与神经预测 (F5ITM9M6), not in this repository.
