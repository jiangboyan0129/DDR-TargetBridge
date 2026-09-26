# DDR Target-Bridge — Stage 1 first-evidence protocol v1.0

Date: 19 September 2026. Status: **PI_LOCKED_FIRST_EVIDENCE_PILOT**.

## 00. Authority, scope and actual knowledge

This protocol authorizes the **first bounded analysis of the qualified functional scores**, not predictive model development, a new project search, or a claim of therapeutic validation. F-B1 remains active and untouched. Stage 0 is completed and is not to be restarted.

The protocol author read the complete uploaded `Stage0_Report.md` (SHA-256 `b26ed627d40a969c80cac812635314c9663669794e826a8da7e4b74cf367d49d`) and revisited the two primary-study methods. The author did **not** obtain the user's local `linked_score_panel.csv`, source workbooks, full Stage-0 code, or individual score values in this task. No cross-source biological result was computed. `[LOCAL_PATH]` paths identify the user's computer, not files accessible to the author. Consequently exact local-column spelling is to be bound mechanically from the already-qualified Stage-0 schema; it is not invented here.

The accompanying JSON expresses parameters in machine-readable form; this protocol supplies scientific meaning. Any conflict between them is a STOP, not a license to pick the preferred interpretation. Stage-0 code and raw files remain immutable.

This is a prespecified **finite-panel evidence pilot**. We explicitly do not pretend that aggregate scores identify experimental error distributions. A future confirmatory or expanded claim needs its own protocol; the present outcomes must not be used later while claiming they were never seen.

## 01. Question and permitted interpretation

**Question:** Do published PRKDC-partner adverse genetic-interaction hypotheses show concordant AZD7648-conditioned sensitization in the two parental-A549 experiments, and is their prioritization distinguishable from generic genetic fragility, untreated fitness, and the available R2 DDR-drug sensitivity controls?

The fixed target is PRKDC/DNA-PKcs; the compound is AZD7648. We evaluate published hypotheses, not discover the best target among many candidates. The source intervention is dual CRISPRi during unperturbed RPE-1 TP53-KO growth. The destination is partner-gene CRISPRi under drug in parental A549. Different backgrounds and interventions mean that a failed transfer cannot be causally attributed to pharmacology, TP53, lineage, or knockdown depth separately.

The direct R&D use is deciding which **pre-existing target-context hypotheses deserve further functional review**. A hypothesized context is experimentally reducing a partner gene. This is not a clinically validated mutation, natural low-expression subgroup, patient stratum, safe therapeutic window, or demonstrated on-target drug mechanism.

Use “adverse genetic interaction / source-called hypothesis” for GEMINI-sensitive <= -1. The source threshold is not a new p-value or a measurement of complete cell killing.

## 02. Read-only sources and run creation

Default Stage-0 root:
`[LOCAL_PATH]/ddr_target_bridge_stage0`

Read only:
- `Stage0_Report.md`
- `manifest.csv` and `SHA256SUMS`
- `schema_map.json` and `screen_metadata.csv`
- `gene_crosswalk.csv`, `qualified_support.csv`, `linked_score_panel.csv`
- `qualification_counts.json`, `independence_ledger.csv`
- `provenance/join_integrity_audit.json`, `provenance/methods_evidence.json`
- already-downloaded R1/R2/R3 files, only to recover source-only context variables or record structure absent from the linked panel.

Create sibling `ddr_target_bridge_stage1/`. Never modify or change permissions on Stage-0 files. Never inspect F-B1 outcomes. Write protocol, JSON, source bindings, hashes and source-defined hypothesis membership in `lock/` before calling analysis routines. If the directory exists, stop rather than overwrite an earlier run; use an explicitly distinct run ID only after verifying it is a new authorized run. Do not re-download the 48 MB or rerun a qualification builder that overwrites Stage 0.

Expected facts: R1 149,787 scored pairs/548 genes; PRKDC 547 partners/36 source-called; three-way exact-symbol support 419; finite endpoint support 400; R2 transcript-consistent finite support 380. The actual file count governs; preserve the source paper's discrepant design/figure counts as already documented.

The number of source-called hypotheses **within 380** is not known from the uploaded report. Compute it using source scores and the structural mask before outcomes are compared. It is a measured denominator, not an adjustable design choice. If either source class is empty, report `NO_SOURCE_CLASS_CONTRAST`; do not move the threshold or target.

## 03. Primary universe and immutable hypotheses

Primary universe P380 is exactly the 380 partner genes meeting Stage-0 complete-endpoint support plus identical R2 transcript labels across the five retained endpoint groups: DNAPKi rho, matched gamma, ATMi rho, ATRi rho and WEE1i rho. Resolve field names from `schema_map.json`/`methods_evidence.json` and record the binding. No gene alias remapping, TSS inference, or P1/P2 equivalence across libraries.

`source_called(g) = (R1 GEMINI sensitive(PRKDC,g) <= -1)`.
All other source-scored partners are **source-not-called comparators**, not known biological negatives. Preserve all 547 source partners, the 419 join and all exclusions in a flow table. Missing values never become zero or non-hits. No destination hit label, p-value, phenotype magnitude, mechanism plausibility or expected result affects inclusion.

Primary destination evidence is R2 parental A549 v2.1, 1,000 nM AZD7648, 14 days, non-growth-normalized rho and its matched gamma. Confirmation is R3 parental WT v3, 625 nM, 11 days, growth-normalized rho and **parent::gamma**. Never substitute R3 vehicle::gamma; never include PRDX1-KO or PARPi combinations.

These are two separately generated campaigns in one destination parental background, not two donors or two external cancer cohorts. Full replicate-level score estimates and cross-library guide/TSS equivalence are unavailable. Publication sequence is not temporal blinding.

## 04. R3 multiplicity and missing-record policy

Maintain one original-record table with gene, transcript, original source-row/element ID, guide IDs as supplied, WT rho, matched parent gamma, and completeness. Duplicate gene/transcript labels with distinct element IDs are retained. No best transcript, smallest p-value, strongest sensitivity, or matching P1/P2 convenience selection.

A record is paired-complete only if both its WT rho and matched parent gamma are finite **in that same record**. Gene-level finite support means at least one such record, consistent with Stage 0.

For the primary descriptive gene-labelled summary, take the unweighted median of rho across paired-complete records, and separately the median of gamma across the same record set. This is an explicitly authorized **statistical summary of available gene-labelled elements**, not an assertion that they are technical replicates, the same TSS, or a single joint intervention. Do not interpret the two component medians as one measured element.

Retain rho/gamma minimum, median and maximum; original-record N, paired-complete N; any-missing and sign-discordant flags. A missing paired record does not become a measured neutral effect. Existing partially measured genes remain in the primary finite-support universe, with sensitivity S3 addressing their ascertainment.

Additionally compute an **observed-record resolution envelope** for source-set separation: least-sensitive observed positive records versus most-sensitive observed comparator records yield a lower envelope; reverse the choices for the upper envelope. These monotonic extrema show sensitivity to choosing among *observed* records. They are not confidence intervals, and they say nothing about the unknown missing-record values. A central median result contradicted by this envelope must not be reported as transcript/element-robust.

## 05. Canonical panel and variables

Write one row per P380 gene, with at least:
`gene`, `gemini_sensitive`, `source_called`, `source_degree_numerator`, `source_degree_denominator`, `source_generic_fragility`, `rho_R2`, `gamma_R2`, `rho_ATMi_R2`, `rho_ATRi_R2`, `rho_WEE1i_R2`, `rho_R3_median`, `rho_R3_min`, `rho_R3_max`, `gamma_R3_median`, `gamma_R3_min`, `gamma_R3_max`, `r3_n_records`, `r3_n_complete`, `r3_any_missing`, `r3_sign_discordance`, `r2_transcript_consistent`, original row/transcript identifiers or a link to the complete original-record table.

Source generic fragility for gene g is the fraction of its finite R1 interactions with sensitive <= -1, excluding self and the PRKDC pair. Compute using the full R1 score universe; preserve numerator/denominator. Do not use R2/R3 to define this covariate. This captures interaction promiscuity, not untreated single-gene fitness in RPE-1; the latter is not supplied by the three-column R1 table.

Report rho as drug-versus-matched-vehicle and gamma as vehicle-versus-T0. A decrease means greater adverse effect in the stated contrast. Tau is prohibited as a substitute. Because rho and gamma share a vehicle measurement, gamma adjustment is a diagnostic and can have mathematical coupling; it is not clean causal adjustment.

## 06. Main finite-panel comparisons — no trained prediction model

For every eligible gene let `Y2=-rho_R2` and `Y3=-rho_R3_median`, so larger means stronger sensitization. Do not pool raw magnitudes between R2 and R3 or between different inhibitors.

For e=2,3, calculate the source-set pairwise separation:

`A_e = mean_{g in source_called, h in source_not_called} [I(Y_e(g)>Y_e(h)) + 0.5 I(Y_e(g)=Y_e(h))]`.

Also report `A_e-0.5`, exact class sizes, class-specific raw medians, fractions with rho < 0, and all gene-labelled observations. Mathematically A is a common-language rank-separation statistic; no classifier was trained. 0.5 is a no-separation reference, not proof of a random experimental assignment or an exact null distribution.

Compute R3 lower/upper envelopes by using `-rho_R3_max` for each positive and `-rho_R3_min` for each comparator (lower), with the converse for upper. Equal gene weighting is preserved. No source-positive gene receives more weight because it has extra R3 element records.

Report all prespecified reference values `{0.50,0.55,0.60,0.65,0.70}` in a small table for A2, A3 and the envelope. These describe effect magnitude; they are not pharmaceutical utility cutoffs or significance thresholds. Do not select one post hoc as the study's success definition.

Store source scores continuously and provide scatter/rank displays for all P380 genes. No alternate GEMINI threshold, top-k chosen from destination scores, or continuous-score model tuning is authorized.

## 07. Strong simple alternative explanations

### 07A. Generic fragility / untreated-fitness matching

Define q(x) = `(ascending midrank(x)-0.5)/n` in the relevant complete gene universe, with ties averaged. Match each source-called gene to up to five source-not-called genes using three coordinates: q(source_generic_fragility), q(-gamma_R2), q(-gamma_R3_median).

A control is eligible if its absolute difference is <=0.20 in **each** coordinate. Choose the five nearest by squared Euclidean distance, breaking exact ties by lexicographic gene symbol. Use distinct controls within a case; reuse is allowed between cases. If fewer than five qualify, use them all; if none qualify, mark that case unmatched. Never widen the caliper or move to a different matching model.

Each matched positive has total weight one, divided equally among its controls. Compute pairwise separation separately in R2 and R3, then average over matched positives. Report match coverage, reused controls/effective unique comparator count, covariate differences and the matched source class. Primary all-gene effects do not change when matching is incomplete. This is a **retrospective conditional diagnostic**, not an out-of-sample predictor; destination gamma is intentionally used to investigate an alternative explanation.

If no eligible matches exist, mark the diagnostic unavailable and stop short of claiming “beyond general fitness.” Partial coverage restricts the claim to that subset; it does not justify dropping unmatched positives silently.

### 07B. Broad DDR sensitivity

Within the SAME P380 universe, separately rank -rho for R2 DNAPKi, ATMi, ATRi and WEE1i. For every gene compute:
`S = q_DNAPKi - median(q_ATMi,q_ATRi,q_WEE1i)`.

Report S by source class, the difference in class medians, the three pairwise rank differences, raw score signs and full distributions. This compares relative priority across tested panels, **not equipotent pharmacology**. The doses/pressure are not matched. Absence of an author hit call for another drug does not prove specificity. R3 has no corresponding other-DDRi measurements, so drug-specificity preference cannot be called independently replicated.

Both pharmacological outcomes and gamma are interpretation controls; do not call them inputs to a prospectively available target predictor. Do not recalculate rho by subtracting gamma a second time.

## 08. Required robustness, evidence and uncertainty boundaries

The released tables contain aggregate scores, not replicate-level phenotypes. Therefore this first pilot performs **no newly computed hypothesis-test p-values, no FDR claims for new genes, and no assay-population confidence intervals**. Source author labels/p-values may be retained verbatim with scope; they are not replicated statistical evidence.

Do not bootstrap 380 genes and call that uncertainty across experiments, patients or independent lineages. DDR genes may share pathways and source interactions. No new gene-clustering network is to be developed to manufacture a biological replication unit.

Instead report deterministic sensitivity of the finite score comparison: recompute A2/A3 after deleting each gene in turn, plus ranges after deleting each source-called gene; report the most influential genes by the prespecified absolute change. Recompute medians/effects for each deletion as required, not new cohorts for selective reporting. These ranges are **influence diagnostics, not jackknife standard errors or confidence intervals**.

The paired-record envelope and three fixed sensitivities below are compulsory. This pilot can state that the frozen set does or does not separate the published measured scores in these conditions. It cannot make the stronger equivalence claim that DNA-PK inhibition lacks useful biology or that an experimental effect has been precisely excluded.

## 09. Exactly three sensitivity panels

S1 — P400: all 400 finite-endpoint genes. Recompute all eligible rank/matching analyses identically. Mark the 20 transcript-inconsistent genes. This cannot rescue a same-perturbation specificity conclusion; it measures dependence on that identity restriction.

S2 — Single-element R3: subset of P380 with exactly one ORIGINAL eligible-WT-context R3 element record, paired-complete. “Only one finite record” among multiple original records does not qualify. Report actual gene and source-positive N. Recompute the same calculations; no substitutions if empty.

S3 — Fully observed R3 records: subset of P380 for which every ORIGINAL eligible-WT-context record is paired-complete. This addresses partial-record ascertainment. Preserve all elements within each gene and use the same summary/envelope rules.

If a sensitivity has an empty source class, report NA with denominator and reason. Do not invent a different subset. Do not silently describe transcript consistency in R2 as transcript/guide equivalence to R3.

## 10. Gene evidence table — not a new biomarker list

For every gene (including non-source-called comparators), publish source score/class, degree, every endpoint, record ranges and identifiers, missingness, matched-control details, R2 specificity contrasts, and eligibility in every sensitivity.

Use separate factual flags, not a single opaque composite score:
- source-called or not;
- R2 rho < 0;
- R3 median rho < 0;
- all observed paired-complete R3 rho < 0;
- any original R3 records missing;
- observed R3 signs differ;
- R2 and R3 central directions disagree;
- R2 DNAPKi rank exceeds each other tested inhibitor rank (list separately);
- known attribution caveat from Stage 0;
- matching available and supported comparator count.

“Directionally concordant” is not “statistically validated,” “on-target proven,” or “clinically useful.” Broad-DDR sensitivity is not inherently false biology. A nonsignificant or unavailable measurement is not a validated negative.

No target is nominated as new. No gene-specific literature search is authorized to Codex in this run. The PI may later select at most two explanatory cases using a recorded rule that includes a discordant/failed case, alongside the complete table. That would be an interpretive follow-up, not retroactive confirmatory evidence.

## 11. Four figures and a short scientific checkpoint

F1: source 547/36 -> exact419 -> complete400 -> primary380; show source-called denominators at each stage. Alongside, display the source and two destination backgrounds, dose, duration, normalization and aggregate-score limitations.

F2: separate R2 and R3 source-set comparisons, A values, raw score distributions and R3 observed-record envelope. Keep raw scales separate. Influence ranges must be labelled as sensitivity, not CI.

F3: source-set matched-control comparison and R2 drug-panel rank contrasts. Plot all primary genes or use fixed source-score order; never choose a favorable heatmap subset after observing the outcome. No figure implies comparable drug potencies.

F4: P380, P400, single-element and fully-observed-record results, with exact source-positive/comparator counts and missing analysis reasons. Include directional and element-discordance counts.

Use ordinary matplotlib/R graphics already installed. No dashboard, new agent framework, cloud service, or presentation deck is required. Export PNG and SVG when possible. Do not use graphics to hide non-hits or missing records.

## 12. Decision and stopping logic

The run outcome is `FIRST_EVIDENCE_COMPLETE`, `NO_SOURCE_CLASS_CONTRAST`, or `IMPLEMENTATION_OR_VALIDITY_STOP`. Completion is not biological success.

For the substantive result, expose a vector of evidence rather than a forced binary win:
1. source-set separation in each experiment and at every fixed reference level;
2. matched-control separation and coverage;
3. R2 relative DDR preference;
4. record/sensitivity/influence robustness;
5. missing evidence and limits.

The PI's next bounded decision is:
- **GO to targeted biological review:** a nontrivial concordant pattern persists in both experiments and the controls/record sensitivities do not explain it away. This authorizes inspecting a small number of mechanisms, not clinical claims or new model development.
- **NO-GO for escalation of the current priority rule:** the source-called set has no stable observed prioritization, or any apparent advantage depends on favorable record choice/uncorrected broad fragility. Finish the honest negative/limited result; do not change target, cohort, threshold or model to rescue it.
- **INCONCLUSIVE:** the matched hypothesis support, record identity, scores or sensitivity are too limited to discriminate the explanations. Report the precise reason and stop.

There is deliberately no automatic p<0.05 or clinical usefulness threshold in this pilot. Its fixed effect-size grid, denominators and robustness results are the evidence used for the decision. “No stable pattern in these measured scores” must not become a claim of equivalence or proof of no biological effect.

## 13. Local preflight and deviations

Before effect calculations: validate source hashes; bind schema semantics; reconstruct and hash P380/P400 and source membership; verify only parental WT; validate rho/gamma record correspondence and all signs; test the pure calculations on synthetic fixtures. A finite endpoint is an identity/support condition, not an observed hit filter.

Mechanical differences (CSV column spelling, existing installed library use, relative path relocation) can be resolved from unambiguous Stage-0 metadata with a logged binding. A contradictory count, multiple plausible endpoint mappings, unknown score direction, unexpected record-collapse requirement, or a conflict in this lock triggers STOP. The executor may not solve a scientific ambiguity by choosing the variant that runs.

After successful preflight, execute once through all defined comparisons and sensitivities. A numerical bug may be fixed with pre/post logs and complete affected-output regeneration; preserve earlier outputs and version the correction. Never silently rewrite source files or hide an unsuccessful run.

## 14. Required outputs and budget

Write `lock/`, `processed/`, `results/`, `figures/`, `tests/`, and a short `Stage1_First_Evidence_Report.md` in the new analysis directory. Minimum outputs:
- `source_binding.json`, source and protocol hashes, `primary380_manifest.csv`, `support400_manifest.csv`, `hypothesis_membership.csv`;
- `original_r3_records.csv`, `canonical_primary_panel.csv`, three sensitivity manifests;
- `source_fragility.csv`, `matched_control_pairs.csv`, `pairwise_effects.csv`, `specificity_diagnostics.csv`, `record_envelopes.csv`, `influence_diagnostics.csv`;
- `gene_evidence_table.csv`, all four figures, runtime/package versions and read-only-source verification;
- a report of question, empirical results, failed explanations, unsolved limitations, and next bounded decision.

Reuse the already-parsed files and existing environment. No downloads, raw FASTQ/BAM, full repo clone, new biological model, GPU, or unrelated package rebuild. The companion metric helper is optional; if used, keep its formulas unchanged and verify it against independent small fixtures. Do not force its column names onto Stage-0 data without a recorded binding.

Stop after these results. Do not search for other projects, perform a target tournament, or alter F-B1.

## 15. Source receipt

Controlling resource evidence: uploaded `Stage0_Report.md`, 19 September 2026; immutable hash above. The raw result package lives on the user's machine and was not re-audited by the protocol author.

Primary methods checked to interpret the report:
1. Fielden et al. (2025), *Comprehensive interrogation of synthetic lethality in the DNA damage response*. DOI 10.1038/s41586-025-08815-4. https://www.nature.com/articles/s41586-025-08815-4
2. O'Loughlin et al. (2026), *Chemogenomic maps reveal a PRDX1-dependent iron–damage axis in the DNA damage response*. DOI 10.1038/s41589-026-02312-z. https://www.nature.com/articles/s41589-026-02312-z

The quantitative pilot choices in this document are new PI decisions made before cross-source analysis. They are not descriptions of what the original authors already did. No claim of new global novelty was certified by this protocol-delivery task.
