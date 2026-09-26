#!/usr/bin/env python3
"""Reproduce the frozen comparison from public, already-transformed observations.

Eligibility, raw-count transformation and transcript aggregation happened upstream
and are NOT repeated by this entry point. Every scientific formula is inherited
unchanged; the additional checks enforce the identities of its released inputs.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from targetbridge.paths import fresh_output
from targetbridge.vendor.final_execute_decision import contrasts, group_indices

KEYS = ['transform', 'support', 'pathway', 'gene', 'sample_id']
SAMPLE_KEYS = ['transform', 'support', 'sample_id']
SUPPORT_FLAGS = {
    'S0_old_genes_old_transcripts': 'old_supported',
    'S1_old_genes_T0_transcripts': 'old_supported',
    'S2_T0_genes_T0_transcripts': 'T0_supported',
}


def verify_inputs(root: Path) -> None:
    """Check fixed scientific inputs even when users run `core` before `verify`."""
    root = root.resolve()
    lock = json.loads((root / 'config/public_core_inputs.json').read_text())
    for item in lock['files']:
        path = (root / item['path']).resolve()
        if not path.is_relative_to(root) or not path.is_file():
            raise ValueError(f"Missing or unsafe fixed input: {item['path']}")
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if path.stat().st_size != item['bytes'] or digest != item['sha256']:
            raise ValueError(f"Fixed input changed: {item['path']}")


def calculate(frame: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Apply the existing equal-gene means and four-group contrast, without fitting."""
    required = KEYS + ['value']
    if set(required) - set(frame.columns):
        raise ValueError('Missing required gene/sample columns')
    if frame.empty or frame[KEYS].isna().any().any():
        raise ValueError('Empty data or missing identity')
    if frame[KEYS].astype(str).apply(lambda s: s.str.strip().eq('')).any().any():
        raise ValueError('Blank identity')
    if frame.duplicated(KEYS).any():
        raise ValueError('Duplicate fixed gene/sample identity')
    if not np.isfinite(frame.value.to_numpy(float)).all():
        raise ValueError('Missing/nonfinite transformed observation')

    # A fixed pathway must have the same genes at every sample within a view.
    # Equal denominators alone would not detect a consistently renamed member.
    for _, block in frame.groupby(['transform', 'support', 'pathway'], sort=True):
        member_sets = block.groupby('sample_id', sort=True)['gene'].agg(frozenset)
        first = member_sets.iloc[0]
        if any(members != first for members in member_sets):
            raise ValueError('Pathway membership changes across samples')

    means = frame.groupby(SAMPLE_KEYS + ['pathway'], sort=True).value.mean().unstack('pathway')
    if set(means.columns) != {'M', 'C'} or means.isna().any().any():
        raise ValueError('Incomplete fixed pathway/sample support')
    means['L_M_minus_C'] = means.M - means.C
    means.columns.name = None
    samples = means.reset_index()
    rows = []
    for (mode, view), block in samples.groupby(['transform', 'support'], sort=True):
        indices = group_indices(block.sample_id.tolist())
        row = {'transform': mode, 'support': view}
        for arm, prefix in [('L_M_minus_C', ''), ('M', 'M_'), ('C', 'C_')]:
            row.update({prefix + key: value for key, value in contrasts(block[arm].to_numpy(), indices).items()})
        rows.append(row)
    return samples, pd.DataFrame(rows)


def validate_fixed_membership(frame: pd.DataFrame, membership: pd.DataFrame,
                              expected_samples: pd.DataFrame) -> None:
    """Verify actual member sets, not just counts, against frozen membership data."""
    expected_groups = set(map(tuple, expected_samples[SAMPLE_KEYS].to_numpy()))
    observed_groups = set(map(tuple, frame[SAMPLE_KEYS].drop_duplicates().to_numpy()))
    if observed_groups != expected_groups:
        raise ValueError('Fixed transform/support/sample identities differ')
    if set(frame.support) != set(SUPPORT_FLAGS):
        raise ValueError('Unknown support view')
    for (mode, view, arm, sample), block in frame.groupby(
            ['transform', 'support', 'pathway', 'sample_id'], sort=True):
        source = membership[membership['transform'].eq(mode) & membership.pathway.eq(arm)]
        flag = source[SUPPORT_FLAGS[view]]
        # Do not use astype(bool) on string "False".
        values = flag.astype(str).str.lower()
        if not values.isin(['true', 'false']).all():
            raise ValueError('Invalid frozen membership flag')
        expected = set(source.loc[values.eq('true'), 'gene'])
        if set(block.gene) != expected:
            raise ValueError(f'Frozen gene identities differ: {mode}/{view}/{arm}/{sample}')


def run(out: Path) -> None:
    out = fresh_output(ROOT, out)
    verify_inputs(ROOT)
    frame = pd.read_csv(ROOT / 'results/extended/support_views/member_sample_values.tsv.gz', sep='\t')
    reference = pd.read_csv(ROOT / 'results/canonical/support_views/pathway_sample_values.tsv', sep='\t')
    membership = pd.read_csv(ROOT / 'results/canonical/support_views/pathway_membership.tsv', sep='\t')
    validate_fixed_membership(frame, membership, reference)
    samples, grid = calculate(frame)
    actual = samples.sort_values(SAMPLE_KEYS).reset_index(drop=True)
    expected = reference.sort_values(SAMPLE_KEYS).reset_index(drop=True)
    pd.testing.assert_frame_equal(actual[expected.columns], expected, check_exact=False, rtol=0, atol=1e-10)
    reference_grid = pd.read_csv(ROOT / 'results/canonical/support_views/decision_grid.tsv', sep='\t')
    keys = ['transform', 'support']
    actual = grid.sort_values(keys).reset_index(drop=True)
    expected = reference_grid.sort_values(keys).reset_index(drop=True)
    pd.testing.assert_frame_equal(actual, expected[actual.columns], check_exact=False, rtol=0, atol=1e-10)
    counts = frame.groupby(['transform', 'support', 'pathway', 'sample_id']).gene.nunique()
    for row in reference_grid.itertuples():
        for arm in ['M', 'C']:
            if not (counts.loc[row.transform, row.support, arm] == getattr(row, arm + '_observed_n')).all():
                raise ValueError('Frozen gene denominator differs')
    out.mkdir(parents=True)
    samples.to_csv(out / 'pathway_sample_values.tsv', sep='\t', index=False)
    grid.to_csv(out / 'terminal_contrasts.tsv', sep='\t', index=False)
    receipt = {
        'status': 'PUBLIC_DERIVED_CORE_REPRODUCTION_PASS',
        'input_layer': 'Frozen transformed per-gene/per-sample records after prior qualification, normalization and transcript aggregation',
        'fixed_input_hashes_match': True,
        'fixed_gene_membership_matches': True,
        'input_records': len(frame), 'pathway_sample_rows': len(samples),
        'fixed_comparisons': len(grid), 'numeric_metrics_per_comparison': 15,
        'all_expected_values_match': True, 'tolerance': 1e-10,
        'raw_count_qualification_or_normalization_reexecuted': False,
        'new_scientific_analysis': False, 'independent_biological_validation': False,
    }
    (out / 'CORE_RECEIPT.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps(receipt))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    run(parser.parse_args().output)
