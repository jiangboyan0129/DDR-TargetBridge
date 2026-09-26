#!/usr/bin/env python3
"""Run unchanged terminal arithmetic from a frozen integer export, then independent parity.
This does not reopen HDF5, historical discovery, source assays, or target selection.
"""
from pathlib import Path
import argparse, csv, hashlib, json, os, shutil, subprocess, sys, datetime
import numpy as np
import pandas as pd
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from targetbridge.paths import fresh_output
INPUTS = {
    "inputs/full_v3_design_construct_ledger.tsv.gz": "data/derived/final_count_export.tsv.gz",
    "inputs/fixed_old_NTC_list.tsv": "data_metadata/fixed_ntc.tsv",
    "inputs/ReactomePathways.gmt.zip": "data/annotations/reactome_frozen.gmt.zip",
    "inputs/RECEIVED_EXPLORATORY_BALANCE_LOCK.json": "provenance/locks/received_exploratory_balance.json",
    "inputs/v3_received_common_projection_UNCHANGED.tsv": "results/extended/support_views/old_common_projection.tsv",
    "inputs/SUM_fixed_member_gene_sample_values.tsv.gz": "data/derived/SUM_fixed_gene_sample_values.tsv.gz",
    "inputs/SUM_balance_all_branches_and_times.tsv": "results/canonical/temporal/fixed_balance_all_times.tsv",
    "inputs/SUM_all_fixed_pathway_members.tsv": "data_metadata/SUM_all_fixed_pathway_members.tsv",
}
REFERENCES = {
    "decision_grid.tsv": "results/canonical/support_views/decision_grid.tsv",
    "pathway_sample_values.tsv": "results/canonical/support_views/pathway_sample_values.tsv",
    "pathway_membership.tsv": "results/canonical/support_views/pathway_membership.tsv",
    "count_floor.tsv": "results/canonical/support_views/count_floor.tsv",
    "member_sample_values.tsv.gz": "results/extended/support_views/member_sample_values.tsv.gz",
    "gene_transcript_effects.tsv": "results/extended/support_views/gene_transcript_effects.tsv",
    "sequential_decomposition.tsv": "results/extended/support_views/sequential_decomposition.tsv",
    "single_member_influence.tsv": "results/extended/support_views/single_member_influence.tsv",
    "joint_sample_influence.tsv": "results/extended/support_views/joint_sample_influence.tsv",
    "old_regression.tsv": "results/extended/support_views/old_projection_regression.tsv",
}

def compare_table(new, accepted):
    a = pd.read_csv(new, sep="\t", keep_default_na=False)
    b = pd.read_csv(accepted, sep="\t", keep_default_na=False)
    if list(a.columns) != list(b.columns) or a.shape != b.shape:
        raise ValueError("Schema or dimensions differ: " + new.name)
    checked = 0; maximum = 0.0
    for col in a:
        if pd.api.types.is_numeric_dtype(a[col]) and pd.api.types.is_numeric_dtype(b[col]):
            x = a[col].to_numpy(float); y = b[col].to_numpy(float)
            if not np.allclose(x, y, rtol=0, atol=1e-10, equal_nan=True):
                raise ValueError("Numerical mismatch: " + new.name + ":" + col)
            finite = np.isfinite(x) & np.isfinite(y)
            if finite.any(): maximum = max(maximum, float(np.max(np.abs(x[finite] - y[finite]))))
            checked += len(x)
        elif not a[col].equals(b[col]):
            raise ValueError("Identity/missing-value mismatch: " + new.name + ":" + col)
    return dict(table=new.name, rows=len(a), columns=len(a.columns), numerical_cells=checked, max_absolute_error=maximum)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", type=Path)
    args = ap.parse_args()
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    out = fresh_output(ROOT, args.output or ROOT / ".build" / ("final-" + stamp))
    manifest = json.loads((ROOT / "data_metadata/final_input_manifest.json").read_text())
    for r in manifest:
        source = ROOT / INPUTS[r["local"]]
        data = source.read_bytes()
        if len(data) != r["bytes"] or hashlib.sha256(data).hexdigest() != r["sha256"]:
            raise ValueError("Frozen input identity mismatch: " + r["local"])
    protocol = ROOT / "config/final_support_decision.json"
    if hashlib.sha256(protocol.read_bytes()).hexdigest() != "e2a62613947816aa99b657559944bcecac8f748418b1e33e6e85cb322243aa12":
        raise ValueError("Final protocol changed")
    out.mkdir(parents=True)
    context = out / "reference_context"; (context / "inputs").mkdir(parents=True); (context / "code").mkdir()
    shutil.copy2(ROOT / "data_metadata/final_input_manifest.json", context / "INPUT_MANIFEST.json")
    for local, staged in INPUTS.items(): shutil.copy2(ROOT / staged, context / local)
    # Preserve independent implementation exactly. Its relative ROOT reads the new run via a link.
    checker = context / "code/independent_check.py"
    shutil.copy2(ROOT / "src/targetbridge/vendor/final_independent_check.py", checker)
    calculated = out / "calculation"
    env = os.environ.copy(); env.update(PYTHONDONTWRITEBYTECODE="1", OPENBLAS_NUM_THREADS="1", OMP_NUM_THREADS="1")
    run = subprocess.run([sys.executable, str(ROOT / "src/targetbridge/vendor/final_execute_decision.py"), "--root", str(context), "--output", str(calculated)], env=env, capture_output=True, text=True)
    if run.returncode: raise RuntimeError("Frozen calculation failed: " + run.stderr)
    (out / "calculation.log").write_text(run.stdout)
    (context / "results").symlink_to(calculated, target_is_directory=True)
    checked = subprocess.run([sys.executable, str(checker), "--output", str(out / "independent")], env=env, capture_output=True, text=True)
    if checked.returncode: raise RuntimeError("Independent calculation failed: " + checked.stderr)
    comparisons = [compare_table(calculated / n, ROOT / p) for n, p in REFERENCES.items()]
    receipt = {
        "status": "FROZEN_FINAL_EXPORT_REPRODUCTION_PASS", "input_source": "bundled complete integer export; no new HDF5 read",
        "scientific_definition_changed": False, "independent_checker_reads_new_output": True,
        "independent_check": json.loads((out / "independent/INDEPENDENT_CHECK.json").read_text()),
        "table_comparisons": comparisons,
        "exact_input_hashes": {r["local"]: r["sha256"] for r in manifest},
        "protocol_sha256": hashlib.sha256(protocol.read_bytes()).hexdigest(),
        "interpretation": "Computational parity only; no additional biological replication or validation",
    }
    (out / "REPRODUCTION_RECEIPT.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps(receipt, indent=2))
if __name__ == "__main__": main()
