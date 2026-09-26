# Public release audit

Date: 2026-09-26. State: local preflight passed; remote publication checks pending.

| Gate | State | Evidence |
|---|---|---|
| G1 Science | PASS | 96 scientific result/input/vendor-code files match V3 bytes; report and brief unchanged; all six public-core comparisons match the frozen grid. |
| G2 Privacy | PASS, curated files | Text, gzip, OOXML and PDF content/metadata inspected; private paths, raw source objects, reviews, logs and internal archives excluded. The explicitly requested public GitHub handle is permitted public account metadata. |
| G3 Rights | PASS within declared boundary | Source-specific attribution and rights in `docs/data_provenance.md`; unclear raw objects excluded, exact metadata retained in `data_metadata/sources.tsv`. Public visibility is not a blanket software license. |
| G4 Size | PASS | Largest curated file below 14 MB; no regular object reaches 100 MB. |
| G5 Reproduction | PASS | 71 unit tests; public-core 13,088 records → 96 sample/pathway records and six fixed comparisons; historical 16 tables and 99,294 workbook records reproduced exactly. |
| G6 CI | PENDING remote | Push/PR workflow executes package verification, unit tests and deterministic downstream smoke test; no scientific download. |
| G7 Links | PASS local | README/document links checked, including case-sensitive path membership for Linux/GitHub. Original `reports/CASE_STUDY.pdf` alias retained for printed V3 references. |
| G8 Visual | PASS local; remote pending | All eight report pages, one brief page and nine slide pages rendered and inspected. Public slides 7/9 updated only for distribution instructions and inspected again. |
| G9 Ownership | PASS | No invented byline, institution, ORCID or software license. Citation stays a template; source experiments and AI assistance attributed. |
| G10 Archive | PASS | Original ZIP remains SHA-256 `4cee672f6b2c3518c18dfa92995b340f694ce3191d7edea41bbb8253b06e2f82`. |

## Scope and engineering changes

The public core reproduces the terminal comparison from frozen, transformed gene/sample observations. It does not rerun raw-count qualification or normalization. The existing integer-export workflow is archived code with an external input gap, clearly documented. Source-score reproduction was rerun locally from exact original files; these local files are ignored and excluded from Git, CI, Release assets and the public ZIP.

Packaging repairs were limited to a pandas column-axis label in the new downstream adapter; case-sensitive public documentation names; private path redaction in a protocol example with original hash preserved; the integrity test's source count (15 scientific files, excluding one private review); and public slide paths/execution descriptions. Scientific definitions, thresholds, transformations, identities, result tables and failed conclusions remain unchanged. Report/brief retain their V3 historical scope, explained by the current reproduction guide.

The source-file inventory classifies all 257 V3 files; generated public adapters and documents have separate entries. `provenance/RELEASE_MANIFEST.tsv` binds all public payloads. A manifest cannot hash itself; its Git object binds its bytes.

## Frozen decisions

Old DNA-PK/AZD7648 NO-GO, the failed crossing hypothesis, Wilson BLOCKED and A REJECTED remain unchanged. Final pathway escalation is NO-GO because direction depends on the analyzable support set. This is not target validation; no new scientific analysis was performed.

## Owner metadata still optional

Confirm the public citation author name(s), individual contribution declarations and a software reuse license if desired. None was guessed and none blocks the explicitly authorized public portfolio release.
