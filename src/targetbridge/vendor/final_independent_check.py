"""Independent scalar implementation; does not import production functions.
Verifies the new six fixed balances from integer count exports using common-center cancellation.
"""
from pathlib import Path
import csv, gzip, math, statistics, json, zipfile, argparse
ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser()
parser.add_argument('--output',type=Path,default=ROOT/'reproduction_independent')
OUT=parser.parse_args().output.resolve()
if OUT.exists(): raise ValueError('Use a new output directory; delivered evidence is read-only')
OUT.mkdir(parents=True)
with zipfile.ZipFile(ROOT/'inputs/ReactomePathways.gmt.zip') as z:
    sets={f[1]:f[2:] for l in z.read('ReactomePathways.gmt').decode().splitlines() if len(f:=l.split('\t'))>2}
with gzip.open(ROOT/'inputs/full_v3_design_construct_ledger.tsv.gz','rt') as f:
    reader=csv.DictReader(f,delimiter='\t');rows=[r for r in reader if r['matrix_present']=='True' and r['target_type']=='gene']
rawcols=[k for k in rows[0] if k.startswith('count__')]
og={r['target'] for r in rows if r['original_eligible']=='True'}
pg={}
with (ROOT/'results/pathway_sample_values.tsv').open() as f:
    for r in csv.DictReader(f,delimiter='\t'):pg[r['transform'],r['support'],r['sample_id']]=float(r['L_M_minus_C'])
checks=[]
for mode in ['zero_only_0.5','count_plus_1']:
    for view in ['S0_old_genes_old_transcripts','S1_old_genes_T0_transcripts','S2_T0_genes_T0_transcripts']:
        selected=[r for r in rows if (r['original_eligible']=='True' if view.startswith('S0') else r['T0_only_eligible']=='True' and (r['target'] in og if view.startswith('S1') else True))]
        grouped={}
        for r in selected:grouped.setdefault(r['target'],{}).setdefault(r['transcript'],[]).append(r)
        for col in rawcols:
            values={}
            for pid in ['R-HSA-5368287','R-HSA-156842']:
                vals=[]
                for g in sets[pid]:
                    if g not in grouped:continue
                    tv=[]
                    for guides in grouped[g].values():
                        gl=[]
                        for r in guides:
                            x=int(r[col]);y=(.5 if x==0 else x) if mode=='zero_only_0.5' else x+1
                            gl.append(math.log2(y))
                        tv.append(math.fsum(gl)/len(gl))
                    vals.append(math.fsum(tv)/len(tv))
                values[pid]=math.fsum(vals)/len(vals)
            L=values['R-HSA-5368287']-values['R-HSA-156842'];expected=pg[mode,view,col[7:]]
            checks.append({'transform':mode,'support':view,'sample_id':col[7:],'independent_L':L,'saved_L':expected,'absolute_error':abs(L-expected)})
maxerr=max(r['absolute_error'] for r in checks)
with (OUT/'independent_fixed_balances.tsv').open('w') as f:
    w=csv.DictWriter(f,fieldnames=list(checks[0]),delimiter='\t');w.writeheader();w.writerows(checks)
assert maxerr<1e-10,maxerr
(OUT/'INDEPENDENT_CHECK.json').write_text(json.dumps({'new_fixed_sample_balances':len(checks),'max_absolute_error':maxerr,'implementation':'csv+math.fsum, no production imports and no NTC centering; cancellation verified against normalized output','interpretation':'numerical verification, not independent biological evidence'},indent=2))
print(len(checks),maxerr)
