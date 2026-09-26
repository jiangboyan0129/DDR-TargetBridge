# Public-edition patch: 1.0.1

Science is unchanged. Canonical numerical tables, derived scientific inputs and inherited mathematical functions retain their prior bytes.

## Corrections

1. `core` now checks a fixed input manifest and exact pathway/gene/sample membership before averaging. The previous wrapper recommended `verify` first, but direct `core` could accept a consistent gene relabel with unchanged values. The published unmodified data are not shown to be wrong by this counterexample.
2. Public-release checks enumerate tracked and nonignored new files, rather than only the historical manifest. Newly added files cannot bypass review simply by being absent from that manifest. Pattern matching remains bounded, not an exhaustive secret detector.
3. `make core` and `make historical` no longer pass an empty output path when OUTPUT is omitted.
4. Report, brief, claim ledger, PI summary and document builder now consistently identify the public transformed-data input layer. The internal count-export workflow remains a distinct layer requiring its exact archive.
5. Figures remove repeated conclusion text and keep editable SVG text; both transformations are exposed in the component plot. Six result/observation figures are retained across main and supplementary material.
6. Markdown report, editable DOCX, public PDF, PPTX and slide PDF are rebuilt from aligned sources. Duplicate report copies and public career-practice notes leave the main tree; their previous versions remain in v1.0.0 and the local source archive.
7. CI uses pinned official checkout v6.0.2 and setup-python v6.1.0 commits, a fixed Ubuntu 24.04 image and read-only repository permissions. The candidate still requires a real GitHub-hosted CI run after push.

## Scope

No new dataset, model, selection threshold, module, hypothesis or biological test. No license or author identity chosen on the owner's behalf. Privacy/links are checked over the public payload; this does not determine legal data rights or guarantee absence of every secret representation.
