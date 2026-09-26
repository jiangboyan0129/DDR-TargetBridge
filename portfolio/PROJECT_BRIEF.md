# DDR TargetBridge

**Comparator membership in a DNA-PK inhibitor screen**

## Research question

Can a pathway-prioritization argument retain its direction when the genes and annotation-defined targeting units included in the comparison change?

## Approach

This public-data case study examines an A549 WT/PRDX1-KO × vehicle/AZD7648 screen. It compares fixed mitochondrial-translation (M) and translation-elongation (E) sets under three support views and two transformations, separating targeting-unit changes from additional genes.

## Main result

M was nearly stable. E changed as its supported population expanded from 23 to 91 genes; the M−E contrast changed from **+0.861 to −1.761** under zero-only replacement. Count+1 gave the same sign reversal. The added E population also included many low-count observations.

## Interpretation

The initial positive contrast is not a membership-insensitive basis for a mitochondrial-specific priority. Expanded coverage is not a corrected biological truth. The result is a local empirical diagnosis, not target validation or a new mechanism.

## Contribution and attribution

The project adds source-linked analyses, a decomposition of comparator composition, and tested reproduction paths. Original investigators performed the experiments. AI assisted analysis discussion, code, testing, figures and writing; personal contribution claims should reflect actual involvement.

## Inspect and reproduce

Report: `reports/DDR_TargetBridge_Case_Study.pdf`.

Public core: `python tools/run.py core --output .build/core-1`.

The public command begins with released transformed gene/sample records; it does not redo count qualification or normalization. Historical workbook workflows require separately retrieved source files.

Repository: https://github.com/jiangboyan0129/DDR-TargetBridge

Original screen: O'Loughlin et al., *Nature Chemical Biology* (2026), DOI: 10.1038/s41589-026-02312-z.
