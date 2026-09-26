#!/usr/bin/env python3
"""One fixed, retrospective decision test. No hit search, model fitting or p-values.
Inputs are complete raw-count exports, not source HDF5 in this runtime.
"""
from __future__ import annotations
from pathlib import Path
import argparse, hashlib, json, itertools, zipfile, sys, time
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
VIEWS=['S0_old_genes_old_transcripts','S1_old_genes_T0_transcripts','S2_T0_genes_T0_transcripts']
TRANSFORMS=['zero_only_0.5','count_plus_1']

def transformed(x, mode):
    x=np.asarray(x, dtype=float)
    if not np.isfinite(x).all() or (x<0).any() or (x!=np.floor(x)).any():
        raise ValueError('Need finite nonnegative integer counts')
    if mode=='zero_only_0.5': return np.log2(np.where(x==0,.5,x))
    if mode=='count_plus_1': return np.log2(x+1)
    raise ValueError(mode)

def group_indices(samples):
    out={}
    for b in ['parent','PRDX1KO']:
        for c in ['T0','vehicle','DNAPKi']:
            out[b,c]=[j for j,s in enumerate(samples) if s.startswith('A549_'+b+'__') and ('__'+c+'__') in s]
            if len(out[b,c])!=(2 if c=='T0' else 3): raise ValueError((b,c,out[b,c]))
    return out

def contrasts(a,ix):
    a=np.asarray(a,float)
    gamma={b:float(a[ix[b,'vehicle']].mean()-a[ix[b,'T0']].mean()) for b in ['parent','PRDX1KO']}
    beta={b:float(a[ix[b,'DNAPKi']].mean()-a[ix[b,'vehicle']].mean()) for b in ['parent','PRDX1KO']}
    return {'beta_WT':beta['parent'],'beta_KO':beta['PRDX1KO'],
            'theta_KO_minus_WT':beta['PRDX1KO']-beta['parent'],
            'gamma_WT':gamma['parent'],'gamma_KO':gamma['PRDX1KO']}

def group_gene_values(frame, cols):
    # Explicit equal-cassette -> equal-transcript -> equal-gene hierarchy.
    units=frame.groupby(['target','transcript'],sort=True,dropna=False)[cols].mean()
    genes=units.groupby(level='target',sort=True).mean()
    return units,genes

def sign(x): return 0 if abs(x)<=1e-10 else (1 if x>0 else -1)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,default=ROOT);ap.add_argument('--output',type=Path)
    args=ap.parse_args();root=args.root.resolve();out=(args.output or root/'reproduction_output').resolve()
    if out.exists(): raise ValueError('Output already exists; use a fresh directory')
    if out==root or out==root/'inputs' or out==root/'results': raise ValueError('Do not overwrite delivered evidence')
    out.mkdir(parents=True)
    t=time.perf_counter();manifest=json.loads((root/'INPUT_MANIFEST.json').read_text())
    for r in manifest:
        p=root/r['local'];b=p.read_bytes()
        if len(b)!=r['bytes'] or hashlib.sha256(b).hexdigest()!=r['sha256']:raise ValueError('Input changed: '+str(p))
    d=pd.read_csv(root/'inputs/full_v3_design_construct_ledger.tsv.gz',sep='\t',keep_default_na=False,na_values=[''])
    if d['construct_id'].duplicated().any():raise ValueError('Duplicate physical ID')
    rawcols=[c for c in d if c.startswith('count__')];samples=[c[7:] for c in rawcols];ix=group_indices(samples)
    # Source export uses literal NA for absent-design numerical cells; never fill zero.
    for col in rawcols+['WT_T0_mean_count','KO_T0_mean_count','WT_vehicle_mean_count','KO_vehicle_mean_count']:
        d[col]=pd.to_numeric(d[col].replace('NA',np.nan),errors='raise')
    present=d.matrix_present.astype(bool);raw=d.loc[present,rawcols].to_numpy(float)
    transformed(raw,TRANSFORMS[0]) # count type check only
    if d.loc[~present,rawcols].notna().any().any():raise ValueError('Absent records must not be filled')
    nids=pd.read_csv(root/'inputs/fixed_old_NTC_list.tsv',sep='\t')['construct_id'].tolist()
    if len(nids)!=1024 or len(set(nids))!=len(nids):raise ValueError('Unexpected fixed NTC IDs')
    ntci=np.flatnonzero(d.loc[present,'construct_id'].isin(nids).to_numpy())
    if len(ntci)!=1024:raise ValueError('NTC identity loss')
    unique=d.structural_sequence_unique.astype(bool)
    tmask=present & unique & (d.WT_T0_mean_count>=40)&(d.KO_T0_mean_count>=40)
    old=tmask & (d.WT_vehicle_mean_count>=40)&(d.KO_vehicle_mean_count>=40)
    if not np.array_equal(tmask.to_numpy(),d.T0_only_eligible.to_numpy()):raise ValueError('T0 qualification differs')
    if not np.array_equal(old.to_numpy(),d.original_eligible.to_numpy()):raise ValueError('Old qualification differs')
    gene=d.target_type.eq('gene');og=set(d.loc[old & gene,'target']);ng=set(d.loc[tmask & gene,'target'])
    sets={}
    with zipfile.ZipFile(root/'inputs/ReactomePathways.gmt.zip') as z:
        lines=z.read('ReactomePathways.gmt').decode('utf8').splitlines()
        for line in lines:
            f=line.split('\t')
            if f[1] in {'R-HSA-5368287','R-HSA-156842'}:sets[f[1]]={'name':f[0],'members':sorted(set(f[2:]))}
    if sorted(len(s['members']) for s in sets.values())!=[99,137]:raise ValueError('Pathway changed')
    M=sets['R-HSA-5368287']['members'];C=sets['R-HSA-156842']['members']
    if set(M)&set(C):raise ValueError('Overlapping pathways require existing protocol, not guessed exclusion')
    support=[old&gene,tmask&gene&d.target.isin(og),tmask&gene]
    oldlock=json.loads((root/'inputs/RECEIVED_EXPLORATORY_BALANCE_LOCK.json').read_text())
    legacy=pd.read_csv(root/'inputs/v3_received_common_projection_UNCHANGED.tsv',sep='\t').set_index('background')
    grid=[];sample_rows=[];member_rows=[];floor_rows=[];loo=[];joint=[];regression=[];membership=[];transcriptrows=[]
    allgenes={}; matrices={}
    for mode in TRANSFORMS:
        logs=transformed(raw,mode);centres=np.median(logs[ntci],axis=0);logs-=centres[None,:]
        y=d[['target','transcript']].copy();y[rawcols]=np.nan;y.loc[present,rawcols]=logs
        for view,mask in zip(VIEWS,support):
            units,g=group_gene_values(y.loc[mask],rawcols);allgenes[mode,view]=g;matrices[mode,view]=units
            mm=[k for k in M if k in g.index];cc=[k for k in C if k in g.index]
            mg=g.loc[mm].to_numpy();cg=g.loc[cc].to_numpy();ma=mg.mean(0);ca=cg.mean(0);L=ma-ca
            row={'transform':mode,'support':view,'M_original_n':len(M),'C_original_n':len(C),'M_observed_n':len(mm),'C_observed_n':len(cc),**contrasts(L,ix)}
            row.update({'M_'+k:v for k,v in contrasts(ma,ix).items()});row.update({'C_'+k:v for k,v in contrasts(ca,ix).items()});grid.append(row)
            for j,sid in enumerate(samples):sample_rows.append({'transform':mode,'support':view,'sample_id':sid,'M':ma[j],'C':ca[j],'L_M_minus_C':L[j]})
            for label,members,vals in [('M',mm,mg),('C',cc,cg)]:
                for k,gs in zip(members,vals):
                    for j,sid in enumerate(samples):member_rows.append({'transform':mode,'support':view,'pathway':label,'gene':k,'sample_id':sid,'value':gs[j]})
                    rr=contrasts(gs,ix);ur=units.loc[k];nr=len(ur)
                    transcriptrows.append({'transform':mode,'support':view,'pathway':label,'gene':k,'transcript_n':nr,**rr})
                    vnew=(len(members)*vals.mean(0)-gs)/(len(members)-1)
                    LL=(vnew-ca) if label=='M' else (ma-vnew)
                    loo.append({'transform':mode,'support':view,'removed_pathway':label,'removed_gene':k,**contrasts(LL,ix)})
                sub=d.loc[mask&d.target.isin(members)]
                for b in ['parent','PRDX1KO']:
                    for cond in ['T0','vehicle','DNAPKi']:
                        cr=[rawcols[j] for j in ix[b,cond]];arr=sub[cr].to_numpy(float)
                        floor_rows.append({'transform':mode,'support':view,'pathway':label,'background':b,'condition':cond,'constructs':len(sub),'cells':arr.size,'zero_cells':int((arr==0).sum()),'below40_cells':int((arr<40).sum()),'minimum':float(arr.min()),'median_count':float(np.median(arr))})
            for omit in itertools.product(*[ix[b,c] for b,c in [('parent','vehicle'),('parent','DNAPKi'),('PRDX1KO','vehicle'),('PRDX1KO','DNAPKi')]]):
                ix2={key:[j for j in inds if j not in omit] for key,inds in ix.items()}
                joint.append({'transform':mode,'support':view,'omitted':';'.join(samples[j] for j in omit),**contrasts(L,ix2)})
            # Verify invariance to an arbitrary, nonconstant common sample offset.
            offsets=np.arange(16)*.1729-1.31
            shift=(mg+offsets).mean(0)-(cg+offsets).mean(0)
            if not np.allclose(shift,L,atol=1e-12,rtol=0):raise ValueError('Common centre did not cancel')
            if mode==TRANSFORMS[0] and view==VIEWS[0]:
                ol=g.loc[oldlock['mitochondrial_observed_members']].mean().to_numpy()-g.loc[oldlock['comparator_observed_members']].mean().to_numpy()
                cres=contrasts(ol,ix)
                for b,k in [('parent','WT'),('PRDX1KO','KO')]:
                    for new,oldcol in [('beta_','mito_minus_comparator_drug_vehicle'),('gamma_','mito_minus_comparator_vehicle_T0')]:
                        delta=abs(cres[new+k]-float(legacy.loc[b,oldcol]));regression.append({'metric':new+k,'absolute_error':delta})
                        if delta>1e-10:raise ValueError('Old result regression failure')
        for label,orig in [('M',M),('C',C)]:
            for gn in orig:
                membership.append({'transform':mode,'pathway':label,'gene':gn,'old_supported':gn in og,'T0_supported':gn in ng,'old_transcripts':';'.join(matrices[mode,VIEWS[0]].loc[gn].index.astype(str)) if gn in og else '', 'T0_transcripts':';'.join(matrices[mode,VIEWS[2]].loc[gn].index.astype(str)) if gn in ng else ''})
    pd.DataFrame(grid).to_csv(out/'decision_grid.tsv',sep='\t',index=False)
    for name,rr in [('pathway_sample_values',sample_rows),('member_sample_values',member_rows),('count_floor',floor_rows),('single_member_influence',loo),('joint_sample_influence',joint),('old_regression',regression),('pathway_membership',membership),('gene_transcript_effects',transcriptrows)]:
        pd.DataFrame(rr).to_csv(out/(name+('.tsv.gz' if len(rr)>2000 else '.tsv')),sep='\t',index=False)
    # Additive decomposition is explicit path-specific arithmetic, not causal attribution.
    df=pd.DataFrame(grid);dec=[]
    for mode in TRANSFORMS:
        gg=df[df['transform']==mode].set_index('support')
        for metric in ['beta_WT','beta_KO','theta_KO_minus_WT']:
            a,b,c=[float(gg.loc[v,metric]) for v in VIEWS]
            dec.append({'transform':mode,'metric':metric,'S0':a,'S1':b,'S2':c,'transcript_step_S1_minus_S0':b-a,'member_step_S2_minus_S1':c-b,'total_S2_minus_S0':c-a})
    pd.DataFrame(dec).to_csv(out/'sequential_decomposition.tsv',sep='\t',index=False)
    summary={'executed':True,'input_mode':'complete raw-count export; NOT a new HDF5 read','raw_present_constructs':int(present.sum()),'raw_samples':len(samples),'fixed_ntc_n':len(ntci),'old_eligible_units':int((old&gene).sum()),'T0_eligible_units':int((tmask&gene).sum()),'old_supported_genes':len(og),'T0_supported_genes':len(ng),'six_grid_rows':len(grid),'old_regression_max_error':max(r['absolute_error'] for r in regression),'seconds':time.perf_counter()-t,'formula':'fixed zero-only 0.5 continuity and +1 sensitivity; equal transcript then gene weights','original_sources_unchanged':True,'no_target_validated':True,'no_pvalues':True,'python':sys.version,'numpy':np.__version__,'pandas':pd.__version__}
    (out/'EXECUTION_RECEIPT.json').write_text(json.dumps(summary,indent=2))
    print(df[['transform','support','M_observed_n','C_observed_n','beta_WT','beta_KO','theta_KO_minus_WT']].to_string(index=False));print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
