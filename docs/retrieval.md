# Exact historical source retrieval

These three files are not tracked or attached to releases. Retrieval is explicit and optional; CI never runs it. The historical computation requires the exact original bytes. The third-party workbooks contain publisher save-path metadata, which must remain local.

```sh
mkdir -p data/historical_sources/stage0/raw
curl --fail --location --proto '=https' --tlsv1.2 'https://media.springernature.com/original/springer-static/esm/art%3A10.1038%2Fs41586-025-08815-4/MediaObjects/41586_2025_8815_MOESM5_ESM.csv' --output 'data/historical_sources/stage0/raw/SPIDR_Table3_GEMINI.csv'
curl --fail --location --proto '=https' --tlsv1.2 'https://media.springernature.com/original/springer-static/esm/art%3A10.1038%2Fs41589-026-02312-z/MediaObjects/41589_2026_2312_MOESM3_ESM.xlsx' --output 'data/historical_sources/stage0/raw/DDRi_Dataset1_v2.xlsx'
curl --fail --location --proto '=https' --tlsv1.2 'https://media.springernature.com/original/springer-static/esm/art%3A10.1038%2Fs41589-026-02312-z/MediaObjects/41589_2026_2312_MOESM5_ESM.xlsx' --output 'data/historical_sources/stage0/raw/DDRi_Dataset3_v3.xlsx'
```

Expected SHA-256 values:

```text
341e2625e3383c8ba7e446bd230eae7502c066da95a91563311cda16dcd34d13  data/historical_sources/stage0/raw/SPIDR_Table3_GEMINI.csv
d71242b0a5c18f4eeb53e1f5d4db5580432f8ecf2d5e9c88d66977e30220f367  data/historical_sources/stage0/raw/DDRi_Dataset1_v2.xlsx
1a6dc8dfdd36b7b9fedb2cc4f878e7ec362845c6a4c714fb61f6e5f9f6edd7fc  data/historical_sources/stage0/raw/DDRi_Dataset3_v3.xlsx
```

Verify the three files with `shasum -a 256 data/historical_sources/stage0/raw/*` (macOS) or `sha256sum` (Linux), then run:

```sh
python tools/run.py historical --output .build/historical-1
```

The workflow also enforces hashes itself. Do not strip workbook metadata, rename genes, impute missing values or substitute exports. If a future publisher download differs, stop and report the mismatch. No new scientific analysis is authorized.

## Raw-count archive is a separate, unbundled layer

Original v3 matrix: `A549_PRDX1_CRISPRi_v3.h5ad.gz`, SHA-256 `ad63ac63ce484377252cd62e7f3162a275aae4e21e88e5ad123b1e5c75a320d4`, inside the immutable [Zenodo 21302988](https://doi.org/10.5281/zenodo.21302988) code archive. It has an HDF5 signature despite its suffix. Do not download FASTQ or infer complete preprocessing availability. The derived complete integer export expected by the preserved legacy `reproduce_final.py` is a different object (hash in `data_metadata/final_input_manifest.json`) held in the original local project archive. This public repository does not offer a verified raw-matrix-to-export reconstruction recipe or a public URL for that project export. Its absence does not affect the explicitly downstream public `core` command.
