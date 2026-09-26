"""Read-only walkthrough of the accepted comparison; no new scientific result."""
from pathlib import Path
import csv
r=Path(__file__).resolve().parents[1]
print('Source: results/canonical/support_views/decision_grid.tsv')
for d in csv.DictReader((r/'results/canonical/support_views/decision_grid.tsv').open(),delimiter='\t'):
 print(f"{d['transform']:>13} | {d['support']:>29} | M={float(d['M_theta_KO_minus_WT']):+.3f} E={float(d['C_theta_KO_minus_WT']):+.3f} balance={float(d['theta_KO_minus_WT']):+.3f} | genes {d['M_observed_n']}/{d['C_observed_n']}")
print('\nM is approximately stable. E changes with the analyzed population. Neither support view is biological truth.')
print('This is a finite descriptor, not absolute survival, causal selection-bias correction or target validation.')
