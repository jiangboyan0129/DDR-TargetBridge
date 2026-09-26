# DDR TargetBridge

[![CI](https://github.com/jiangboyan0129/DDR-TargetBridge/actions/workflows/ci.yml/badge.svg)](https://github.com/jiangboyan0129/DDR-TargetBridge/actions/workflows/ci.yml)

A reproducible computational functional-genomics case study on evidence boundaries in genetic-to-pharmacological target prioritization.

![The comparator changes while the mitochondrial component remains comparatively stable](figures/01_components.png)

## Question

Does a fixed mitochondrial-translation versus eukaryotic-translation-elongation contrast retain its interpretation when the analyzable genes and targeting units change?

## Why it matters

Genetic perturbation and a pharmacological intervention are different experiments. Screen signals also depend on growth, measurement, and the population that survives eligibility rules. A relative pathway contrast cannot, by itself, establish a specific druggable mechanism.

## Approach

- Public functional-genomics datasets.
- Perturbation/sample identity reconstruction.
- Fixed comparisons and support-population analysis.
- Reproducible source-to-result workflows with explicit input boundaries.

## Key result

The mitochondrial-translation component remained comparatively stable, whereas changes in the analyzable comparator population substantially changed the eukaryotic-translation-elongation component and reversed the pathway contrast.

Under zero-only replacement, the contrast changes from **+0.861 to −1.761**. The mitochondrial component stays approximately stable; 23 retained and 68 added comparator genes have different observed means. Both frozen transformations and all three support views remain visible. Expanded S2 support is **not corrected biological truth**.

## Decision

The present evidence does not justify escalation to a stable mitochondrial-specific pharmacological target claim.

## My contribution

This section describes the documented project contribution; it does not certify unaided personal authorship or assign unconfirmed individual roles.

| Layer | Contribution and ownership |
|---|---|
| Original experiments / published biology | Generated and established by the cited investigators, not this project. |
| Standard methodology | Existing rank comparisons, matching, log transforms and aggregation; no new statistical method claimed. |
| Project engineering implementation | Exact source identities, parsers, reproducible workflows, tests and traceable figures. |
| Project analytical contribution | Fixed support views, component disclosure, retained/added-member decomposition and explicit failure retention. |
| New finite scientific evidence | A source-bound diagnosis of this particular comparison and a bounded no-escalation decision. |

**AI-assisted computational research workflow:** assistance included implementation, checks and synthesis. No human/AI percentages, institutional affiliations or unverified personal roles are asserted. [Contribution map](docs/contribution_map.md).

## Important limitation

This is a computational functional-genomics evidence-evaluation case study, not experimental target validation or a newly established biological mechanism.

**[Read the case study](reports/DDR_TargetBridge_Case_Study.pdf)** · **[View main figures](figures/)** · **[Reproduce core result](docs/reproducibility.md)** · **[Methods / provenance](docs/data_provenance.md)** · **[Contribution map](docs/contribution_map.md)**

[One-page brief](portfolio/PROJECT_BRIEF.pdf) · [Slides](presentation/DDR_TargetBridge.pdf) · [Contextual supplement](reports/CONTEXTUAL_SUPPLEMENT.pdf) · [Scientific claims](docs/scientific_claims.md)

## Reproduction

Use Python 3.12 or 3.13 with the recorded core dependencies:

```sh
python -m pip install -r environment/requirements-core.txt
python tools/run.py verify
python tools/run.py core --output .build/core-1
python tools/run.py historical --output .build/historical-1
```

1. **Verify packaged canonical results:** hashes, fixed values, synthetic tests and public-package checks. No scientific downloads.
2. **Reproduce the terminal decision:** the public `core` entrypoint starts from included, already transformed per-gene/per-sample values. It reconstructs pathway means and all six fixed contrasts. It does **not** rerun raw-count qualification or normalization.
3. **Historical/source reproduction:** requires three externally retrieved publisher files. Before retrieval, `historical` exits clearly with `EXTERNAL_INPUTS_REQUIRED`. Follow [exact retrieval instructions](docs/retrieval.md); the full frozen hashes must match. This mode is not run in CI.

The report retains the scientific record of the completed V3 study. Its prior integer-count-export reproduction is a different layer from this public distribution's downstream core. No FASTQ end-to-end reproduction is claimed. See [reproduction scope](docs/reproducibility.md).

## Sources, rights and project history

The original [negative decisions](docs/decision_history.md) remain unchanged. The scientific outputs are frozen; publication changes packaging and access only.

[Data provenance](docs/data_provenance.md) distinguishes project-derived results, licensed annotations and externally retrieved source files. A public software reuse license has not been chosen: [license decision](docs/LICENSE_DECISION_REQUIRED.md). Public visibility does not grant a blanket reuse license. Citation authorship remains a [template](CITATION.cff.template), not an invented byline.
