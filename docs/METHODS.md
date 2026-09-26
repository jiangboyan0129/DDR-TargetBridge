# Methods: what is estimated, and at which level

## Scope and input
The main case starts from the unchanged complete v3 count export (`data/derived/final_count_export.tsv.gz`). It has 64,237 physical constructs and 16 actual sample records. WT and PRDX1-KO each have two real T0 records and three records in each vehicle/drug endpoint group. The source study reports A549 CRISPRi, 625 nM AZD7648 and an 11-day exposure. This is not a new independent clone experiment or an absolute cell-count assay.

## Identity and support
Keep exact source gene labels and unique physical mappings. A physical dual-guide cassette is one reagent. `transcript` identifies an annotation-defined targeting unit; it does not measure transcript abundance or isoform-specific repression. T0 qualification is mean raw count ≥40 across each background’s two real T0 records. S0 also requires mean terminal vehicle count ≥40 in both backgrounds. S1 preserves the S0 genes but admits all T0-qualified units for those genes. S2 admits all T0-qualified genes/units. Source pathway definitions remain M=R-HSA-5368287 (137 members), E=R-HSA-156842 (99 members). C in legacy fields maps to E; it is not renamed in immutable files.

## Transform and hierarchy
For the continuity branch, replace only exact zeros by 0.5 and take log2; positive counts are unchanged before log2. For the named sensitivity, add 1 to all counts and take log2. Use the same 1,024 fixed NTC identities for centering. Average constructs within a targeting unit, then units within gene, then supported genes within pathway. Thus multiple targeting units can change a gene’s value, but genes remain equally weighted within a supported pathway.

For sample s, L_s = mean_M(x_s) − mean_E(x_s). A common additive centering value c_s cancels: mean_M(x_s−c_s)−mean_E(x_s−c_s)=L_s. This identity does not confer invariance to changed members, unequal weights, gene-specific effects or count floors.

For background b, β(P,b)=mean_drug(P,b)−mean_vehicle(P,b); θ(P)=β(P,KO)−β(P,WT); θ(balance)=θ(M)−θ(E). No pairing is inferred from similarly numbered labels. Values are finite relative-log-count descriptors, not pathway-wide causal effects.

## Component and mixture disclosure
All six pre-existing support×transform results are retained. The S2 E component is a weighted mean of the 23 retained and 68 added genes under S2 targeting support. The mixture identity reveals the arithmetic effect of population composition. S0→S1 isolates the already specified change in targeting support along this descriptive path; S1→S2 changes gene membership. These are sequential calculations, not causal effect proportions.

## Selection and measurement
The vehicle observations determine eligibility and occur in the response denominator. A drug-outcome-blind filter can therefore still depend on a component of the response. Removing it changes both the analyzed population and the prevalence of low-count observations. No model here separates those processes. For count-floor plots, zero is a subset of <40; stacked display categories are zero, 1–39 and ≥40 so they do not double count.

## Local sensitivity, not population uncertainty
Single-member deletions and 81 joint endpoint omissions reuse the same observations. Their ranges are not confidence intervals, and genes are not independent culture replicates. The described data do not identify independent clone/perturbation variation. Broader inference would require justified units and assumptions, not post-hoc gene bootstraps or a significance threshold retrofitted to this result.

## Separate historical analyses
The original rule uses the unchanged GEMINI sensitive≤−1 cutoff. It retains 12 source calls and 368 source-not-called comparators after exact linkage and completeness. Pairwise A assigns 1 when a called record is more sensitizing, 0.5 for a tie and 0 otherwise. Matching uses three rank coordinates, maximum coordinate gap 0.20, up to five nearest comparators, lexicographic ties, no reuse within a case, allowed reuse across cases and equal total case weights. It is descriptive, not causal adjustment.

For the fixed crossing, rank −score among all 16,549 background genes with average ties, divide by N+1 and average across the unchanged module members, then subtract 0.5. Repair-minus-metabolism must be positive for olaparib and negative for AZD1775; the second sign is absent. Historical exposure and context changes remain explicit.

## Software and reuse
The source-specific scientific functions in `src/targetbridge/vendor/`, `workflows/vendor_*` and `revision/code/revise_existing_outputs.py` are preserved. New `tools/run.py` is orchestration only. New presentation code reads accepted tables without filtering results or changing estimators. Reproduction levels and the tested environment are documented separately. No new scientific data, model, hypothesis test or candidate search is authorized by this release.
