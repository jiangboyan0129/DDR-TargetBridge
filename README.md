# DDR TargetBridge

[![CI](https://github.com/jiangboyan0129/DDR-TargetBridge/actions/workflows/ci.yml/badge.svg)](https://github.com/jiangboyan0129/DDR-TargetBridge/actions/workflows/ci.yml)

**Which genes enter a pathway comparison can change the conclusion drawn from a CRISPR screen.**

A computational functional-genomics case study using public DNA-damage-response screening data. The laboratory experiments belong to the original investigators; this project is an AI-assisted secondary analysis.

[Read the report](reports/DDR_TargetBridge_Case_Study.pdf) · [One-page brief](portfolio/PROJECT_BRIEF.pdf) · [Slides](presentation/DDR_TargetBridge.pdf) · [Reproduce the public core](#reproduce-the-public-core)

## Question

Does a pathway-prioritization argument remain stable when the supported genes and annotation-defined targeting units change?

## Why it matters

A pathway label can conceal unequal coverage. A comparison used to justify follow-up needs to distinguish a pathway's observed behavior from the composition of its comparator.

## Approach

The same A549 WT/PRDX1-KO × vehicle/AZD7648 experiment was summarized under three specified support views and two count transformations. The analysis separates the mitochondrial-translation component (M), the translation-elongation comparator (E), and their difference; individual members, samples and count floors remain available.

## Key result

**M was nearly stable; E changed substantially as targeting units and genes were restored. Their contrast reversed under both transformations.**

![M is nearly stable while E changes across three support views; both transformations are shown.](figures/01_components.png)

M: Mitochondrial translation. E: Eukaryotic Translation Elongation. S0 uses original support; S1 retains the same genes with expanded targeting-unit support; S2 includes all T0-qualified support. Lines connect analysis views, not timepoints. These are descriptive log-abundance contrasts, with no biological confidence intervals.

| Support view | M / E genes | M − E: zeros → 0.5 | M − E: count + 1 |
|---|---:|---:|---:|
| Original support (S0) | 89 / 23 | +0.861 | +0.854 |
| Same genes, expanded targeting units (S1) | 89 / 23 | +0.477 | +0.518 |
| All T0-qualified support (S2) | 94 / 91 | −1.761 | −1.437 |

[Full-precision results](results/canonical/support_views/decision_grid.tsv) · [Members and count-floor evidence](docs/FIGURES.md)

## Decision and limitation

The initial positive contrast is not sufficient evidence for a support-insensitive mitochondrial-specific priority. The expanded comparison is **not** a corrected biological truth: it includes low-count observations, and the analysis cannot separate all growth, selection, clone and perturbation effects. This case does not establish a new mechanism, target validation or a general predictive method.

## Project contribution

The contribution is a source-linked implementation and a finite empirical diagnosis: the support-dependent reversal is driven chiefly by the comparator population. Original experiments and published mechanisms remain prior work; ranking, averaging and sensitivity analysis are standard methods. [Contribution map](docs/contribution_map.md) · [Claims and limits](docs/SCIENTIFIC_CLAIM_LEDGER.md)

AI assisted analysis discussion, code, testing, figures and writing. Personal roles and citation metadata must reflect the owner's actual involvement; neither an unaided-work claim nor a software license is inferred from this repository.

## Reproduce the public core

CI configuration: Python 3.12 on Ubuntu 24.04. The updated workflow still requires its own hosted run; local checks do not establish a new remote CI result. Use an isolated environment:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r environment/requirements-core.txt
python tools/run.py verify
python tools/run.py core --output .build/core-1
```

Choose a fresh output directory on each run. `make core` uses `.build/core-1` by default; `make core OUTPUT=.build/core-2` chooses another directory.

**What `core` reproduces:** 13,088 released, already-transformed gene/sample records → 96 pathway/sample summaries → six fixed comparisons. It verifies input hashes and full membership before calculating. It does **not** repeat raw-count eligibility, normalization, transcript aggregation, HDF5 parsing or FASTQ processing.

**Historical source-table reproduction:** retrieve the three exact public workbooks listed in [retrieval instructions](docs/retrieval.md), then run:

```bash
python tools/run.py historical --output .build/historical-1
```

Without these workbooks, the command exits with `EXTERNAL_INPUTS_REQUIRED`; it neither downloads substitutes nor fabricates source data. [Reproduction levels](docs/reproducibility.md)

## Repository guide

| Location | Purpose |
|---|---|
| `reports/`, `figures/` | Research report, contextual supplement, editable figure exports |
| `src/`, `workflows/`, `tools/` | Preserved analysis functions and explicit execution/build entry points |
| `config/`, `results/` | Fixed input identities, permitted derived observations and reference results |
| `tests/`, `revision/tests/`, `public_tests/` | Numerical, historical and public-release regression checks |
| `data_metadata/`, `provenance/` | Source identities, rights notes and release records |
| `docs/` | Methods, contribution, claims, decision history and reproduction scope |

No single folder is a general-purpose target-discovery platform. Source-specific historical code remains labeled as such. See [methods](docs/METHODS.md) and [decision history](docs/decision_history.md).

## Rebuild presentation files

Install the separate [presentation dependencies](environment/requirements-presentation.txt). Figure generation reads accepted tables only. It does not repeat science or select new results.

```bash
python tools/build_figures.py --output .build/figures-1
python tools/build_documents.py --output .build/documents-1
```

The document builder writes DOCX and editable PPTX. PDF export requires LibreOffice; see [presentation build instructions](docs/PRESENTATION_BUILD.md). SVG text is retained as text, not converted to glyph outlines.

## Data, rights and citation

Original data: O'Loughlin et al., *Nature Chemical Biology* (2026), DOI [10.1038/s41589-026-02312-z](https://doi.org/10.1038/s41589-026-02312-z). The [source registry](data_metadata/sources.tsv) includes the separate historical studies and exact retrieval identifiers.

The public repository excludes original workbooks, raw-count archives and full matrices where redistribution permission has not been established. Public visibility is not an open-source license. [Rights](docs/LICENSE_DECISION_REQUIRED.md) · [Citation template](CITATION.cff.template)

The `v1.0.0` release remains the original public snapshot. Subsequent publication-engineering changes do not alter the scientific results.
