# Comparator membership changes a pathway contrast in a DNA-PK inhibitor screen

DDR TargetBridge | Computational functional-genomics case study

## Abstract

Pathway comparisons in pooled genetic screens depend on which perturbations remain measurable. We examined this dependence in one public A549 WT/PRDX1-KO screen with vehicle or AZD7648. Fixed mitochondrial-translation and translation-elongation gene sets were summarized under three support views that separated additional targeting units from additional genes. With zeros replaced by 0.5 before log transformation, the conditional pathway contrast changed from +0.861 to +0.477 to −1.761; count+1 gave the same sign reversal. The mitochondrial component remained nearly constant, whereas the comparator component increased from +0.183 to +2.814. Restoring comparator coverage also admitted observations near the count floor. The result identifies a support-dependent prioritization argument in this archive, not a reversed mitochondrial mechanism or a corrected biological estimate. The public code reproduces the final comparison from released transformed observations; historical source-table reproduction is available after separate input retrieval.

## Introduction

Pooled CRISPR screens provide evidence about the relative representation of perturbations during an experiment. This evidence is useful for prioritizing follow-up, but a pathway name does not specify the actual population contributing to its summary. Qualification rules can remove different fractions of two pathways, and the same gene can be represented by different annotation-defined targeting units. A stable interpretation therefore requires examination of both the pathway components and the observations entering them.

The source experiment compared parental A549 and PRDX1-knockout backgrounds during vehicle or DNA-PK inhibitor treatment [1]. Its published biological findings and experiments remain the work of the source investigators. Here, we ask a narrower secondary-analysis question: does a relative comparison between Mitochondrial translation and Eukaryotic Translation Elongation retain its direction when analyzable support changes under fixed rules? Growth and measurement are established concerns in screening [2,3]; this study contributes a particular empirical diagnosis rather than a new theory of those effects.

## Results

### Support views change the comparator population

The archived count export contains 64,237 physical constructs and 16 sample records. Each of the four endpoint groups contains three culture records; each background also has two real T0 records. A dual-guide cassette is one physical reagent, not two independent reagents. The reported drug exposure was 625 nM AZD7648 for 11 days [1].

We retained the original Reactome definitions: Mitochondrial translation (M; 137 directory genes) and Eukaryotic Translation Elongation (E; 99 directory genes). E is this specific set, not all cytosolic translation. The analysis distinguishes three support views. All retain exact identity and unique physical mappings and require the mean of the two real T0 counts to be at least 40 in each background. The original support additionally requires mean terminal-vehicle counts of at least 40 in both backgrounds.

| View | Genes | Annotation-defined targeting units | M / E genes |
|---|---|---|---:|
| S0 | Original qualified genes | Original qualified units | 89 / 23 |
| S1 | Same genes as S0 | All T0-qualified units for those genes | 89 / 23 |
| S2 | All T0-qualified genes | All T0-qualified units | 94 / 91 |

The sample-level quantity is the mean transformed abundance of M minus that of E. Drug response is drug minus vehicle within a background; the final contrast is the KO response minus the WT response. Thus the comparison can change through either pathway component or through their membership.

### The comparator component drives the sign reversal

The M component was +1.043, +1.043 and +1.052 in S0, S1 and S2 under zero-only replacement. In contrast, E increased from +0.183 to +0.567 to +2.814. Their difference changed sign (Fig. 1). The count+1 sensitivity retained this pattern.

![Pathway components under both transformations](../figures/01_components.png)

**Figure 1 | Components of the conditional pathway contrast.** Both transformations and all three specified support views are shown. M denotes mitochondrial translation and E the translation-elongation comparator. Lines connect analysis populations, not timepoints. Solid/filled symbols use zero-only replacement; dashed/open symbols use count+1. The values are descriptive log-abundance contrasts, not survival effects; no biological uncertainty interval is implied. Source: `results/canonical/support_views/decision_grid.tsv`.

| Transformation | View | θ(M) | θ(E) | θ(M) − θ(E) |
|---|---|---:|---:|---:|
| Zero → 0.5 | S0 | +1.043 | +0.183 | +0.861 |
| Zero → 0.5 | S1 | +1.043 | +0.567 | +0.477 |
| Zero → 0.5 | S2 | +1.052 | +2.814 | −1.761 |
| Count+1 | S0 | +1.040 | +0.186 | +0.854 |
| Count+1 | S1 | +1.040 | +0.522 | +0.518 |
| Count+1 | S2 | +1.045 | +2.482 | −1.437 |

S0 to S1 preserves the gene set but adds targeting-unit support for five retained E genes: EEF2, RPL13A, RPS29, RPS3 and UBA52. This is a change in targeting annotation, not a measured change in expressed isoforms. S1 to S2 changes the M component by approximately +0.009 and E by +2.247. These are arithmetic partitions of the observed contrast, not causal percentages.

### Restored E genes account for the changed mixture

Under S2 targeting-unit support, the 23 retained E genes have a mean conditional component of +0.567, compared with +3.574 for the 68 added genes (Fig. 2). Their weighted mixture is:

**θ(E,S2) = (23/91) × 0.566563 + (68/91) × 3.574051 = 2.813917.**

Count+1 gives an added-gene mean of +3.144 and an overall E component of +2.482. The five added M genes shift their component much less. The added subgroup is shown to explain the mixture; it is not a newly selected therapeutic target set.

![All retained and added E genes](../figures/02_comparator_members.png)

**Figure 2 | Comparator composition under expanded targeting-unit support.** Every retained (n=23) and added (n=68) E gene is shown under both transformations. The small deterministic horizontal offsets prevent overlap and do not encode data. Horizontal marks and labels are arithmetic means, not intervals. Genes are not independent culture replicates. Source: `revision/results/revision/retained_added_gene_values.tsv`.

### Expanded coverage also reaches the count floor

The expanded E set has 97 physical constructs representing 91 genes. Each endpoint group contributes 291 construct-by-sample entries. These contain 59 zeros in WT vehicle, 63 in WT drug, 63 in KO vehicle and 2 in KO drug (Fig. 3). Expanding support therefore does not merely recover additional high-precision measurements.

![Count support in all four endpoint groups](../figures/03_count_floor.png)

**Figure 3 | Count-floor observations in the expanded comparator.** Counts refer to constructs multiplied by three sample records per group, not numbers of cells or independent experiments. The 0, 1–39 and ≥40 bins are disjoint; no entries are removed from the display. Both transformations use the same underlying integer observations. Source: `results/canonical/support_views/count_floor.tsv`.

The E vehicle-to-T0 descriptions are −5.051 in WT and −5.637 in KO, whereas KO drug minus vehicle is +2.952. Relative enrichment can coexist with substantial relative depletion from baseline. In addition, the original eligibility condition uses terminal vehicle counts that also enter the response denominator. Outcome-blindness to drug counts alone does not remove this overlap.

All sample observations are available in Supplementary Fig. S1. The archived member deletions and 81 joint endpoint-omission configurations preserve the sign within each support view. They measure local influence on the same observations, not replication across independently established clones or biological populations.

## Discussion

This case identifies a precise limitation of a pathway-prioritization argument. The M−E contrast reverses chiefly because the comparator population changes, while the M component stays nearly constant. The original positive contrast therefore cannot be treated as a membership-insensitive justification for a mitochondrial-specific priority. The result does not support prioritizing the opposite pathway instead.

The three views summarize different populations, not three independent estimates of one latent effect. Restoring T0-qualified genes changes biological composition and admits low-count observations simultaneously. Reduced accumulation of negative selection, sampling floors, relative composition and treatment-specific effects remain compatible explanations. The available data do not identify a causal selection-bias correction or its magnitude. Background and clone establishment are also not independently separated. No fitted growth correction is used to label a residual as mechanism.

Two earlier project results are separate case histories. A PRKDC analysis retained 12 of 36 source-called partners and found inconsistent ordering within that observed subset. A later fixed repair-versus-metabolism crossing did not satisfy its required pair of signs in a historically exposed external program. Neither is causally explained by the present M/E decomposition. Likewise, source-study damage and iron assays address selected reagents, and the SUM time series uses a different experimental program. They are retained in the contextual supplement, not presented as sequential validation of the complete pathway comparison.

The contribution is a finite empirical analysis with explicit populations, component decomposition and executable evidence paths. Standard averaging and sensitivity methods, original experiments and published source mechanisms remain prior work. The result supports a local decision not to escalate this contrast; it is not a calibrated pharmaceutical decision system or a new general method.

## Methods

### Transformations, aggregation and contrast

Two unchanged transformations are reported: replace only zeros by 0.5 before log2, or add 1 to every count before log2. Both use the same 1,024 non-targeting-control identities for sample centering. Construct values are averaged within targeting unit, targeting units within gene, and genes within the supported pathway. Missing designs and ambiguous identities are not imputed. No strongest-guide or best-transcript selection is introduced for this comparison.

For pathway P and background b, β(P,b) = mean drug(P,b) − mean vehicle(P,b). The conditional component is θ(P) = β(P,KO) − β(P,WT), and the pathway contrast is θ(M) − θ(E). A common additive sample center cancels in the M−E balance. This does not remove gene-specific effects, count floors or membership changes. Machine files use C for the pathway called E in the text.

### Interpretation and uncertainty

The analysis is a retrospective description of this archive. Culture records, reagents, genes, annotations and omission configurations are not interchangeable units of replication. Independent-clone effects, perturbation efficacy and population uncertainty are not established. Individual sample values and deterministic influence checks are reported without gene-bootstrap intervals, post-hoc significance thresholds or biological confidence intervals.

### Public reproduction and data access

The public `core` workflow starts from 13,088 released transformed gene/sample records, after upstream count qualification, normalization and transcript aggregation. It verifies their byte identities and complete member sets, then reconstructs 96 pathway/sample summaries and six fixed comparisons. It does not reconstruct raw count preprocessing. Count-floor summaries and membership tables are archived evidence, not outputs re-created from raw counts by that public command.

Historical source-table workflows require the three external CSV/XLSX inputs listed in the repository retrieval manifest. Their absence produces an explicit `EXTERNAL_INPUTS_REQUIRED` status. The original internal V3 archive contains a fuller count-export reproduction layer, which is distinct from this reduced public release. Fresh HDF5/FASTQ processing and complete historical ScreenPro2 API replay are not claimed. Input versions, commands and reference tables are provided in the repository.

### Attribution

Original investigators performed all laboratory experiments [1,4]. This project is an AI-assisted secondary analysis; AI contributed to scientific discussion, implementation, testing, figures and writing. Project-level analytical contributions and personal role confirmation are described separately in the contribution map. No new experimental or clinical validation is claimed.

## References

1. O'Loughlin et al. Chemogenomic maps reveal a PRDX1-dependent iron–damage axis in the DNA damage response. *Nature Chemical Biology* (2026). DOI: 10.1038/s41589-026-02312-z.

2. Colic et al. Identifying chemogenetic interactions from CRISPR screens with drugZ. *Genome Medicine* (2019). DOI: 10.1186/s13073-019-0665-3.

3. Hafner et al. Growth rate inhibition metrics correct for confounders in measuring sensitivity to cancer drugs. *Nature Methods* (2016). DOI: 10.1038/nmeth.3853.

4. Fielden et al. Comprehensive interrogation of synthetic lethality in the DNA damage response. *Nature* (2025). DOI: 10.1038/s41586-025-08815-4. Source of the separate historical genetic nominations.

