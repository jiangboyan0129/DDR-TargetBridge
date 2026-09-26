# Presentation builds

The report is a research case study, not a submitted or accepted journal Article. Figure organization is informed by the explicit comparisons in Dempster et al. (2019), not an imitation of their scientific claims. No author, journal logo or endorsement is borrowed.

## Rebuild

Use the optional presentation environment and an existing LibreOffice installation:

```bash
python -m pip install -r environment/requirements-presentation.txt
python tools/build_figures.py --output .build/figures-1
python tools/build_documents.py --output .build/documents-1
python tools/export_pdf.py --input .build/documents-1/DDR_TargetBridge_Case_Study.docx --output .build/report-1.pdf
python tools/export_pdf.py --input .build/documents-1/DDR_TargetBridge.pptx --output .build/slides-1.pdf
```

The document builder uses the released figures in `figures/`; it does not silently substitute a newly generated directory. Compare new figure outputs with that directory before a maintainer deliberately updates the release. The PDF export writes a fresh file and does not download or install software. Python package versions and LibreOffice may affect pagination; render and inspect every page before publication.

## Figure rules

White background, legible sans-serif axis text, no 3D/shadows, clear units and consistent series meanings. Complete observations and both declared transformations remain shown; no significance stars or inferred confidence intervals are added. SVG retains `<text>` objects; PDF uses editable TrueType text. Do not include font files in a release.

Long conclusions and limitations belong in captions and prose, not repeatedly inside each image. Colors are the existing Matplotlib default cycle, complemented by marker and line distinctions; color alone is not used to encode transformations. The sample figures remain in the supplement rather than being discarded.

Main report: three evidence figures. README: the component plot plus exact result table. The separate balance plot is available for reuse. Each chart has its own saved object and sources in `figures/FIGURE_SOURCES.json`.

## Presentation is not computation

The public core starts after count qualification, normalization and transcript aggregation. Neither the PDF nor rebuilt slides may call that command raw-count reconstruction. Rendering does not establish biological validity or broader novelty.
