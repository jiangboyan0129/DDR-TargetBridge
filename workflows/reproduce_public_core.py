#!/usr/bin/env python3
"""Reconstruct the frozen terminal comparison from released transformed gene/sample values.
This is a downstream reproduction layer, not raw-count qualification or normalization.
"""
from pathlib import Path
import argparse,json,sys
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from targetbridge.paths import fresh_output
from targetbridge.vendor.final_execute_decision import contrasts,group_indices

def calculate(frame):
 keys=['transform','support','pathway','gene','sample_id']
 if frame.duplicated(keys).any():raise ValueError('Duplicate fixed gene/sample identity')
 if not np.isfinite(frame.value.to_numpy(float)).all():raise ValueError('Missing/nonfinite transformed observation')
 means=frame.groupby(['transform','support','sample_id','pathway'],sort=True).value.mean().unstack('pathway')
 if set(means.columns)!={'M','C'}:raise ValueError('Expected both fixed pathways')
 if means.isna().any().any():raise ValueError('Incomplete pathway/sample support')
 means['L_M_minus_C']=means.M-means.C
 means.columns.name=None
 samples=means.reset_index();rows=[]
 for (mode,view),f in samples.groupby(['transform','support'],sort=True):
  ix=group_indices(f.sample_id.tolist());r={'transform':mode,'support':view}
  for arm,prefix in [('L_M_minus_C',''),('M','M_'),('C','C_')]:r.update({prefix+k:v for k,v in contrasts(f[arm].to_numpy(),ix).items()})
  rows.append(r)
 return samples,pd.DataFrame(rows)

def run(out):
 out=fresh_output(ROOT,out)
 src=ROOT/'results/extended/support_views/member_sample_values.tsv.gz'
 f=pd.read_csv(src,sep='\t');sample,grid=calculate(f)
 ref=pd.read_csv(ROOT/'results/canonical/support_views/pathway_sample_values.tsv',sep='\t')
 cols=['transform','support','sample_id'];a=sample.sort_values(cols).reset_index(drop=True);b=ref.sort_values(cols).reset_index(drop=True)
 pd.testing.assert_frame_equal(a[b.columns],b,check_exact=False,rtol=0,atol=1e-10)
 refgrid=pd.read_csv(ROOT/'results/canonical/support_views/decision_grid.tsv',sep='\t');keys=['transform','support'];a=grid.sort_values(keys).reset_index(drop=True);b=refgrid.sort_values(keys).reset_index(drop=True)
 pd.testing.assert_frame_equal(a,b[a.columns],check_exact=False,rtol=0,atol=1e-10)
 # Verify equal-gene denominators independently for every released view/sample.
 counts=f.groupby(['transform','support','pathway','sample_id']).gene.nunique()
 for r in refgrid.itertuples():
  for arm in ['M','C']:
   if not (counts.loc[r.transform,r.support,arm]==getattr(r,arm+'_observed_n')).all():raise ValueError('Frozen gene denominator differs')
 out.mkdir(parents=True);sample.to_csv(out/'pathway_sample_values.tsv',sep='\t',index=False);grid.to_csv(out/'terminal_contrasts.tsv',sep='\t',index=False)
 receipt={'status':'PUBLIC_DERIVED_CORE_REPRODUCTION_PASS','input_layer':'Frozen transformed per-gene/per-sample records after prior qualification, normalization and transcript aggregation','input_records':len(f),'pathway_sample_rows':len(sample),'fixed_comparisons':len(grid),'numeric_metrics_per_comparison':15,'all_expected_values_match':True,'tolerance':1e-10,'raw_count_qualification_or_normalization_reexecuted':False,'new_scientific_analysis':False,'independent_biological_validation':False}
 (out/'CORE_RECEIPT.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt))
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);run(p.parse_args().output)
