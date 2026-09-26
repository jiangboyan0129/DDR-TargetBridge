# DDR TargetBridge
## When a pathway comparison changes because its members change
**Completed computational functional-genomics case study · Public-data secondary analysis**

**Question.** Does a proposed pathway priority survive changes in the genes and targeting units actually represented in a CRISPR screen?

**Approach.** Reanalyse one A549 WT/PRDX1-KO × vehicle/AZD7648 experiment. Keep pathway definitions, three support views and two count transforms fixed; separate the mitochondrial-translation arm from the Eukaryotic Translation Elongation comparator; preserve every sample and the low-count limitations.

![The comparator changes, not the mitochondrial component](../figures/01_components.png)

**Key result.** The conditional balance changes from **+0.861 to −1.761**. The mitochondrial arm remains near **+1.05**, while the comparator changes from **+0.183 to +2.814**. Restoring comparator coverage also restores many low-count observations. The analysis does not establish which population represents biological truth.

**What this project adds.** A specific empirical diagnosis of comparator-population dependence, a transparent decomposition of targeting-unit versus gene membership, and runnable source-table/count-export workflows. Earlier failed transfer predictions remain separate histories, not validation of the main result.

**Decision and limit.** Do not elevate the original positive balance to a mitochondrial-specific target claim from this archive. This is not a new mechanism, clinical biomarker or universal correction method.

**Responsibility.** Original investigators generated the experiments. The project used AI-assisted scientific discussion, coding, testing and writing. Project-level contributions and the personal-responsibility boundary are documented separately.

**Inspect.** Read `reports/CASE_STUDY.pdf`; start reproduction with `python tools/run.py verify`. The README links methods, contributions and exact sources. Primary data: O’Loughlin et al., Nature Chemical Biology (2026), doi:10.1038/s41589-026-02312-z.
