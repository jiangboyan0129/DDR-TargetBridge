# DDR Target-Bridge Stage 0

**RESOURCE_READY_FOR_SCIENTIFIC_LOCK** — qualified for an exact published-gene-symbol, original-record join. This does not establish biological support, independent replication, power or an analysis protocol. PRKDC / DNA-PK and AZD7648 remain fixed.

Exactly three complete publisher files were acquired: **48,026,192 bytes**, one network download request per file. Recorded article HTML adds 569,434 bytes; recorded transfer is 48,595,626 bytes, below 250 MB. An R1 local dependency failure occurred before any network request. Publisher-page tool access did not expose transport byte counts and is outside this recorded file-transfer total. Raw files are read-only (0444), hash checked and unchanged. Both XLSX files have valid ZIP signatures/CRCs. Every sheet and row was parsed; author GSEA sheets received structural inspection only.

| Resource | Actual complete table |
|---|---|
| R1 | 149,787 unique scored pairs; 548 genes; 3 columns; no duplicate pair keys |
| R2 | 37,368 rows × 81 columns: 18,626 genes plus 18,742 pseudocontrols; 10 endpoint groups |
| R3 | 20,451 rows × 33 columns: 19,430 gene records / 17,907 gene symbols plus 1,021 controls; 6 endpoint groups |

R1 has **547 PRKDC partners**, including 36 under the published sensitive-score ≤ −1 threshold and 511 other scored partners. Across all R1 pairs, 5,131 satisfy that historical threshold. No source calls were compared with destination calls. The article's reported design count (149,878), figure count (147,787), and actual CSV count (149,787) differ; the file count governs qualification and the discrepancy remains documented.

| Exact identity coverage | R1→R2 | R1→R3 WT | Three-way |
|---|---:|---:|---:|
| All R1 genes, including PRKDC | 453 | 420 | 420 |
| PRKDC partner genes | 452 | 419 | 419 |

**400 partner genes** have finite source, both WT rho, both matched gamma, and all three R2 specificity endpoints. R2 supplies finite DNAPKi, gamma, ATMi, ATRi and WEE1i scores for all 452 matched partners. R3 supplies 441 matched partner records, of which 421 are finite across 400 genes; 20 records retain missing scores. There are 22 partner genes with multiple R3 records. In the full WT table, 537 gene records lack scores, and 17,420 genes have at least one finite WT score. KO remains separate (17,862 genes with finite KO scores).

The gene-level complete-support count is not a same-perturbation count. R2 transcript labels differ across the five retained endpoints for 20 matched partners. Requiring the same published R2 transcript label leaves 432 R2 partners and **380** three-way finite partners. These are structural alternatives for a future lock, not selected analysis cohorts. Equal P1/P2 labels across libraries do not prove identical TSSs or guides. All six duplicated R3 target/transcript keys and their guide IDs remain distinct; no averaging or favorable selection occurred.

The endpoints are explicit: GEMINI sensitive measures adverse genetic interaction; rho is drug versus matched vehicle; gamma is vehicle versus T0. Absolute treated fitness (tau) was not substituted. R2 uses parental A549 v2.1, AZD7648 1,000 nM, 14 days, two reported treatment replicates, and no growth normalization. R3 core uses parental A549 WT v3, 625 nM, 11 days, three reported replicates, and growth-normalized scores. The alternative R3 vehicle::gamma object is not used to backfill missing parent::gamma scores. No other-DDRi specificity screens are provided in R3; the prespecified specificity panel is R2 only.

There are **three screen campaigns**, two parental lineages overall, and **one core destination parental background (A549)**. Including excluded PRDX1-KO yields three genotype backgrounds. R1 reports two biological replicates; R2 reports ten treatment/vehicle arms; R3 reports four genotype×treatment arms, two in WT. The files contain aggregate scores, not separate replicate scores. R3 exposes 20,451 dual-guide element IDs / 40,902 component ID strings, not additional biological samples. R1/R2 unique guide counts and cross-study guide overlap cannot be established from these score tables.

Unmatched partners remain explicit: 95 against R2, 128 against R3. No alias mapping was invented, so absence cannot distinguish an old symbol, unscored design or other omission. ANKRD49/MRE11 and DZIP3/CIP2A attribution caveats are retained; only ANKRD49 and DZIP3 occur under those exact names in the crosswalk, neither in the R1 PRKDC slice. No absence of a named flag is treated as proof of attribution.

No hidden sheets, formulas, external links or required workbook objects were detected. No additional model, predictor weights or raw sequencing is required for the bounded join. Constituent guides, replicate-level scores, cross-library TSS equivalence and the R2 transcript-selection rule remain unavailable. Related guide libraries, shared investigators and processing assumptions limit independence; v3 is not another donor or clinical validation. DDRi submission predates final SPIDR publication, so publication order does not establish temporal blinding. Distinct interventions and cell backgrounds preclude causal attribution of differences to pharmacology.

Deliverables: [manifest and receipts](manifest.csv), [raw hashes](SHA256SUMS), [schema](schema_map.json), [screen metadata](screen_metadata.csv), [gene crosswalk](gene_crosswalk.csv), [common support](qualified_support.csv), [unaltered long score panel](linked_score_panel.csv), [exact counts](qualification_counts.json), [independence ledger](independence_ledger.csv), and [integrity checks](provenance/join_integrity_audit.json). The score panel contains 3,873 long records, including 731 explicit unmatched placeholders; these are not independent biological observations. Scripts reproduce extraction and qualification from the three local raw files. Source definitions are documented in [method evidence](provenance/methods_evidence.json) from the two supplied publisher pages.

**STOP: resource qualification is complete. F-B1 was not read, modified or run. No correlations, enrichment, recovery, new rankings, predictive performance or target prioritization were computed. Biological analysis requires a separate lock using this actual support structure.**
