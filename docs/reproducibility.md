# Reproduction scope

The public commands are deliberately separated by the input layer. Neither successful software tests nor agreement with frozen values adds a biological replicate.

| Layer | Command | Public input / behavior | Boundary |
|---|---|---|---|
| Packaged evidence | `python tools/run.py verify` | Check frozen scientific bytes, links, privacy, sizes and synthetic tests | No effect estimation or download |
| Terminal comparison | `python tools/run.py core --output .build/core-1` | Included transformed gene/sample records → equal-gene pathway means → existing WT/KO drug-minus-vehicle contrasts | Qualification, count transforms and NTC centering were upstream; not rerun |
| Original published score sources | `python tools/run.py historical --output .build/historical-1` | After exact retrieval: SPIDR + R2/R3 workbooks → original PRKDC linkage/matching and 16,549-gene R2 background | Requires externally retrieved source files; no new confirmation |
| Original full integer-export workflow | `workflows/reproduce_final.py` | Historical code retained; raw count export intentionally not in Git due unresolved embedded-data redistribution scope | Not the public `core` command; requires the exact privately archived export, not summary reconstruction |
| FASTQ / full ScreenPro2 / whole discovery | Not provided as an executed public entrypoint | Outside this release | Not claimed |

## Run locally

```sh
python -m pip install -r environment/requirements-core.txt
python tools/run.py verify
python tools/run.py core --output .build/core-1
```

Each output directory must be new. `.build/` is ignored. Never use `python -O`, because retained historical validation uses assertions. CI runs the package gate, synthetic suites and one deterministic public-core smoke test. It downloads Python dependencies only, never scientific datasets.

For historical reproduction, follow [retrieval.md](retrieval.md). The input gate reports missing filenames and instructions before starting calculations. A file with the right name but wrong hash is rejected. Private publisher workbook save-location metadata stays only in the ignored local source files, not Git or release assets.

## What is unchanged

The original numeric functions in `src/targetbridge/vendor/` and the original historical readers remain source-bound. The public core adapter calls the existing sample grouping and contrast definitions and verifies every reproduced metric against the unchanged canonical grid. Both transformations, all support populations, negative results, omissions and low-count summaries remain preserved.

The original V3 document records prior completed reproduction from integer counts. Those prior receipts are historical evidence, not claims that every workflow was rerun for GitHub publication. Original public-release checks are recorded in `provenance/releases/v1.0.0/PUBLIC_RELEASE_RECEIPT.json`. The 1.0.1 candidate records local checks separately; remote CI must be checked on its actual commit. The 14 inherited revision tests now check 15 scientific/identity files instead of also requiring a private simulated-review DOCX; this is a packaging-only integrity change, not a statistical or scientific change.
