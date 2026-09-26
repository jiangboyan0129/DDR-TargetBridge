# Data provenance and publication boundary

The wet-lab experiments and parent-study mechanisms belong to the original investigators. This repository publishes the frozen project analysis and its evidence boundaries; it does not claim to have generated those experiments.

| Family | Attribution and official rights evidence | Public handling |
|---|---|---|
| DDRi score and follow-up data | O’Loughlin et al., DOI [10.1038/s41589-026-02312-z](https://www.nature.com/articles/s41589-026-02312-z); publisher Rights and permissions: [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) | Project-derived linkage, normalized-source descriptions and aggregates retain attribution. Raw workbooks are retrieved separately; byte-identical source identity is required. |
| SPIDR | Fielden et al., DOI [10.1038/s41586-025-08815-4](https://www.nature.com/articles/s41586-025-08815-4); publisher CC BY 4.0 | Derived comparisons included; original complete CSV retrieved separately. No file-specific exception was identified in the existing source record. |
| Reactome | [Official license](https://reactome.org/license): database data and derived files are [CC0](https://creativecommons.org/publicdomain/zero/1.0/) | Frozen pathway data and identity metadata retained with source attribution. |
| SUM | Zimmermann et al. original experiments; Colic/drugZ [Figshare 8799215 v2](https://doi.org/10.6084/m9.figshare.8799215.v2), provider metadata CC BY 4.0 | Only existing project-transformed values and comparisons; source experiments remain attributed. |
| DDRi embedded raw-count matrices | [Zenodo 21302988](https://doi.org/10.5281/zenodo.21302988) declares MIT for the code archive | Separate redistribution scope for embedded scientific matrices remains unresolved. Raw matrices and the raw-count-preserving export are not published here. Code-archive licensing is not silently extended to data. |
| HAP1 / ChemicalMatrix | Frozen source identities in `data_metadata/source_studies.tsv` | No full original dataset or full discovery module registry is redistributed. Fixed project comparisons and their already selected limited member definitions are preserved. |
| Project code, derived results and narrative | Explicitly authorized owner publication; AI-assisted computational workflow | Project permission to publish is recorded; no blanket reuse license or unconfirmed personal byline is imposed. |

License checks were limited to these exact existing sources on 2026-09-26, not a new scientific literature search. Attribution, license links and modifications are identified here. Project-derived files represent linkage, transformation, aggregation or visualization; original scientific results and endpoints were not changed for publication. Material bearing separate source-specific terms remains governed by those terms.

`PUBLIC_FILE_MANIFEST.tsv` classifies every V3 input file. `data_metadata/sources.tsv` lists exact public source identities, URLs and retrieval instructions. Raw source files are intentionally not part of Git, CI, Release assets or the public ZIP. Nothing is recreated from rounded report values.
