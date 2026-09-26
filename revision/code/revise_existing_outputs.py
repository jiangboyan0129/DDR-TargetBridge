#!/usr/bin/env python3
"""Disclosure-only revision of frozen results. No new eligibility, targets or inference.
Reads previously exported sample/gene values and complete historical rank backgrounds.
Does NOT establish original HDF5/XLSX or whole-study source-to-result reproduction.
"""
from __future__ import annotations
import argparse, hashlib, json, platform
from pathlib import Path
import numpy as np
import pandas as pd

VIEWS=['S0_old_genes_old_transcripts','S1_old_genes_T0_transcripts','S2_T0_genes_T0_transcripts']
MODES=['zero_only_0.5','count_plus_1']
TOL=1e-10

def sha256(p: Path)->str:
    h=hashlib.sha256()
    with p.open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    return h.hexdigest()

def verify_sources(root: Path):
    root=root.resolve()
    records=json.loads((root/'provenance/source_manifest.json').read_text())
    for r in records:
        p=(root/r['path']).resolve()
        if not p.is_relative_to(root) or not p.is_file(): raise ValueError('Source path: '+r['path'])
        if p.stat().st_size!=r['bytes'] or sha256(p)!=r['sha256']: raise ValueError('Source changed: '+r['path'])
    return len(records)

def theta_from_samples(frame:pd.DataFrame,value:str)->float:
    means={}
    for bg in ['parent','PRDX1KO']:
        for cond in ['vehicle','DNAPKi']:
            mask=frame.sample_id.str.startswith('A549_'+bg+'__') & frame.sample_id.str.contains('__'+cond+'__',regex=False)
            x=frame.loc[mask,value].to_numpy(float)
            if len(x)!=3 or not np.isfinite(x).all(): raise ValueError((bg,cond,'Need 3 endpoint records'))
            means[bg,cond]=float(x.mean())
    return (means['PRDX1KO','DNAPKi']-means['PRDX1KO','vehicle'])-(means['parent','DNAPKi']-means['parent','vehicle'])

def weighted_mixture(n_old:int,old:float,n_added:int,added:float)->float:
    if n_old<1 or n_added<1:raise ValueError('Both populations must be present')
    return (n_old*old+n_added*added)/(n_old+n_added)

def module_values(frame:pd.DataFrame,members:list[str]):
    if frame.gene.duplicated().any(): raise ValueError('Duplicate gene')
    if not np.isfinite(frame.raw_score.to_numpy(float)).all():raise ValueError('Missing score')
    if len(members)!=len(set(members)):raise ValueError('Duplicate member')
    f=frame.set_index('gene')
    if not set(members)<=set(f.index):raise ValueError('Missing module member')
    f['q_minus_half']=(-f.raw_score).rank(method='average')/(len(f)+1)-0.5
    z=f.loc[members]
    return float(z.q_minus_half.mean()), float(z.raw_score.median()), z

def run(root:Path,out:Path):
    root=root.resolve();out=out.resolve()
    if out.exists():raise FileExistsError('Choose a NEW output directory: '+str(out))
    n_sources=verify_sources(root); out.mkdir(parents=True)
    checks=[]
    def check(label,observed,expected):
        err=abs(float(observed)-float(expected))
        checks.append({'check':label,'observed':observed,'expected':expected,'absolute_error':err})
        if not np.isfinite(err) or err>TOL:raise ValueError((label,observed,expected,err))
    d=root/'data/terminal'
    grid=pd.read_csv(d/'decision_grid.tsv',sep='\t')
    genes=pd.read_csv(d/'gene_transcript_effects.tsv',sep='\t')
    samples=pd.read_csv(d/'pathway_sample_values.tsv',sep='\t')
    if len(grid)!=6:raise ValueError('Six frozen results required')
    mixtures=[];decomp=[];splits=[]
    for mode in MODES:
        gm=grid[grid['transform'].eq(mode)].set_index('support')
        for view in VIEWS:
            r=gm.loc[view];s=samples[samples['transform'].eq(mode)&samples.support.eq(view)]
            for arm in ['M','C']:
                check(mode+'/'+view+'/'+arm+'/sample',theta_from_samples(s,arm),r[arm+'_theta_KO_minus_WT'])
                g=genes[genes['transform'].eq(mode)&genes.support.eq(view)&genes.pathway.eq(arm)]
                check(mode+'/'+view+'/'+arm+'/gene',g.theta_KO_minus_WT.mean(),r[arm+'_theta_KO_minus_WT'])
            check(mode+'/'+view+'/balance',r.M_theta_KO_minus_WT-r.C_theta_KO_minus_WT,r.theta_KO_minus_WT)
            check(mode+'/'+view+'/samples_balance',theta_from_samples(s,'L_M_minus_C'),r.theta_KO_minus_WT)
        for arm in ['M','C']:
            gg=genes[genes['transform'].eq(mode)&genes.pathway.eq(arm)]
            old_names=set(gg.loc[gg.support.eq(VIEWS[0]),'gene'])
            old_T0=gg[gg.support.eq(VIEWS[1])].set_index('gene')
            full=gg[gg.support.eq(VIEWS[2])].set_index('gene')
            retained=full.loc[sorted(old_names)]
            added=full.loc[sorted(set(full.index)-old_names)]
            check(mode+'/'+arm+'/retained',retained.theta_KO_minus_WT.mean(),old_T0.theta_KO_minus_WT.mean())
            val=weighted_mixture(len(retained),retained.theta_KO_minus_WT.mean(),len(added),added.theta_KO_minus_WT.mean())
            check(mode+'/'+arm+'/mixture',val,full.theta_KO_minus_WT.mean())
            mixtures.append({'transform':mode,'pathway':arm,'n_retained':len(retained),'n_added':len(added),'retained_theta':retained.theta_KO_minus_WT.mean(),'added_theta':added.theta_KO_minus_WT.mean(),'S2_theta':val,'S1_theta':old_T0.theta_KO_minus_WT.mean(),'added_weight':len(added)/len(full),'support_step':val-old_T0.theta_KO_minus_WT.mean()})
            for group,frame in [('retained_T0_transcripts',retained),('added_T0_genes',added)]:
                for gene,row in frame.iterrows():splits.append({'transform':mode,'pathway':arm,'population':group,'gene':gene,**row.to_dict()})
        for a,b,label in [(VIEWS[0],VIEWS[1],'transcript_support'),(VIEWS[1],VIEWS[2],'gene_membership')]:
            dm=gm.loc[b,'M_theta_KO_minus_WT']-gm.loc[a,'M_theta_KO_minus_WT']
            dc=gm.loc[b,'C_theta_KO_minus_WT']-gm.loc[a,'C_theta_KO_minus_WT']
            dl=gm.loc[b,'theta_KO_minus_WT']-gm.loc[a,'theta_KO_minus_WT']
            check(mode+'/'+label+'/identity',dm-dc,dl)
            decomp.append({'transform':mode,'step':label,'delta_M':dm,'delta_C':dc,'delta_balance':dl,'interpretation':'sequential algebra, not a causal fraction'})
    pd.DataFrame(mixtures).to_csv(out/'retained_added_mixture.tsv',sep='\t',index=False)
    pd.DataFrame(splits).to_csv(out/'retained_added_gene_values.tsv',sep='\t',index=False)
    pd.DataFrame(decomp).to_csv(out/'component_steps.tsv',sep='\t',index=False)
    grid.to_csv(out/'six_frozen_results_UNCHANGED.tsv',sep='\t',index=False)
    # Restore ranks using ALL 16,549 genes for every pre-existing R2 condition.
    base=root/'data/crossover'; spec=json.loads((base/'PROTOCOL_LOCK.json').read_text())
    for name,expected in spec['locked_files'].items():
        if sha256(base/name)!=expected:raise ValueError('Locked file changed '+name)
    bg=pd.read_csv(base/'R2_frozen_background_values.tsv.gz',sep='\t')
    expected_modules=pd.read_csv(base/'R2_modules.tsv',sep='\t').set_index(['condition','module_id'])
    expected_contrasts=pd.read_csv(base/'R2_contrasts.tsv',sep='\t').set_index('condition')
    recon=[];contrasts=[];mvals=[]
    for cond,f in bg.groupby('condition',sort=True):
        names=sorted(f.gene)
        if len(names)!=16549 or len(set(names))!=16549:raise ValueError('Incomplete background '+cond)
        hashed=hashlib.sha256(('\n'.join(names)+'\n').encode()).hexdigest()
        if hashed!=spec['common_background_sha256_newline']:raise ValueError('Wrong background '+cond)
        tt={}
        for mod,mem in spec['modules'].items():
            t,median,z=module_values(f,mem);tt[mod]=t
            ref=expected_modules.loc[cond,mod]
            check(cond+'/'+mod+'/T',t,ref['T']);check(cond+'/'+mod+'/median',median,ref.raw_median)
            recon.append({'condition':cond,'module_id':mod,'T':t,'raw_median':median,'module_n':len(mem),'background_n':len(f)})
            for gene,row in z.iterrows():mvals.append({'condition':cond,'module_id':mod,'gene':gene,'raw_score':row.raw_score,'q_minus_half':row.q_minus_half})
        c=tt['HAP1.L2.32']-tt['HAP1.L2.139']
        check(cond+'/contrast',c,expected_contrasts.loc[cond,'contrast_HR_minus_metabolic'])
        contrasts.append({'condition':cond,'contrast_HR_minus_metabolic':c})
    pd.DataFrame(recon).to_csv(out/'R2_modules_reranked.tsv',sep='\t',index=False)
    pd.DataFrame(contrasts).to_csv(out/'R2_contrasts_reranked.tsv',sep='\t',index=False)
    pd.DataFrame(mvals).to_csv(out/'R2_member_locations_reranked.tsv',sep='\t',index=False)
    pd.DataFrame(checks).to_csv(out/'revision_regression_checks.tsv',sep='\t',index=False)
    receipt={'status':'DISCLOSURE_REVISION_AND_BACKGROUND_RERANK_COMPLETE','source_snapshots_verified':n_sources,'numeric_checks':len(checks),'maximum_absolute_error':max(r['absolute_error'] for r in checks),'whole_study_reproduction':False,'source_HDF5_reopened':False,'source_R2_XLSX_reparsed':False,'historical_PRKDC_linkage_or_matching_rebuilt':False,'crossover_background_reconstruction':'full 16,549-gene exported score vectors -> ranks -> 2 fixed modules -> 6 fixed contrasts','new_targets_or_effect_tests':False,'python':platform.python_version(),'numpy':np.__version__,'pandas':pd.__version__}
    (out/'REVISION_RECEIPT.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(receipt,indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1]);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();run(a.root,a.output)
