"""One authorized finite-panel pilot; read immutable locks, never mutate Stage0."""
import csv
import hashlib
import json
import math
import platform
import sys
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from statistics import median

from metrics import basic_effects, specificity, matched_diagnostic, deletion_ranges, summarize_records

BASE=Path(__file__).resolve().parents[1]
S0=BASE.parent/'ddr_target_bridge_stage0'
WORK=BASE.parents[1]/'work/ddr_target_bridge_stage0'


def load(path):
    with path.open(newline='') as f: return list(csv.DictReader(f))


def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def true(v): return v is True or v=='True'
def finite(v):
    try: return math.isfinite(float(v))
    except (ValueError,TypeError): return False


def write(name,rows):
    if not rows: return
    keys=list(dict.fromkeys(k for r in rows for k in r))
    with (BASE/name).open('x',newline='') as f:
        w=csv.DictWriter(f,fieldnames=keys);w.writeheader();w.writerows(rows)


def main():
    start=time.monotonic()
    pre=json.loads((BASE/'lock/preflight_pass.json').read_text())
    assert pre['status']=='PREFLIGHT_PASS'
    for name,digest in pre['frozen_sha256'].items():
        assert sha(BASE/name)==digest, f'STOP frozen input changed: {name}'
    assert not (BASE/'results/execution_started.json').exists(), 'STOP: authorized analysis already started'
    (BASE/'results/execution_started.json').write_text(json.dumps({'utc':datetime.now(timezone.utc).isoformat(),'preflight_sha256':sha(BASE/'lock/preflight_pass.json'),'status':'STARTED'},indent=2)+'\n')
    members=load(BASE/'lock/hypothesis_membership.csv')
    binding=json.loads((BASE/'lock/source_binding.json').read_text())
    groups={k:v['group'] for k,v in binding['canonical_fields'].items()}
    original_r3=load(BASE/'processed/original_r3_records.csv')
    records=defaultdict(list)
    for r in original_r3:
        records[r['target']].append(r)
    r2=defaultdict(dict)
    for r in load(WORK/'R2_phenotypes.csv'):
        for key,group in groups.items():
            if key.endswith('R2') and r[group+'|target']!='negative_control':
                g=r[group+'|target'];assert key not in r2[g];r2[g][key]=r
    incident=defaultdict(lambda:[0,0])
    for r in load(S0/'raw/SPIDR_Table3_GEMINI.csv'):
        a,b=r['gene_combination'].split(';')
        if a==b or 'PRKDC' in [a,b] or not finite(r['sens.score']): continue
        for g in [a,b]:
            incident[g][1]+=1
            incident[g][0]+=float(r['sens.score'])<=-1
    fragility=[]; canonical=[]
    for m in members:
        g=m['gene']; numerator,denominator=incident[g]
        assert denominator>0, f'STOP source fragility denominator unavailable {g}'
        sf=dict(gene=g,source_degree_numerator=numerator,source_degree_denominator=denominator,
                source_generic_fragility=numerator/denominator)
        fragility.append(sf)
        r={**m,**sf,'gemini_sensitive':float(m['gemini_sensitive']),'source_called':true(m['source_called'])}
        for key in ['in_exact419','in_support400','in_primary380','in_S2_single_R3_record','in_S3_no_missing_R3_records','r2_transcript_consistent']:
            r[key]=true(m[key])
        for field,group in groups.items():
            if not field.endswith('R2'): continue
            d=r2.get(g,{}).get(field)
            r[field]=float(d[group+'|score']) if d and finite(d[group+'|score']) else None
            for f in ['score','transcript','ttest pvalue','BH adj_pvalue','number_of_guide_elements','combined_score','label']:
                r[field+'__published_'+f.replace(' ','_')]=d[group+'|'+f] if d else ''
            r[field+'__original_excel_row']=d['__excel_row'] if d else ''
        rr=records.get(g,[])
        if rr:
            rs=summarize_records([{'record_id':d['record_id'],'rho':d[groups['rho_R3']+'|score'],
                                  'gamma':d[groups['gamma_R3']+'|score']} for d in rr])
            r.update({k:v for k,v in rs.items() if k not in ['records','paired_complete','r3_rho_sign_set']})
            r['r3_rho_sign_set']=json.dumps(rs['r3_rho_sign_set'])
            r['r3_transcripts']=json.dumps([d['transcript'] for d in rr])
            r['r3_element_ids']=json.dumps([d['sgID_AB'] for d in rr])
        else:
            r.update(r3_n_records=0,r3_n_complete=0,r3_any_missing=None,r3_sign_discordance=None,
                     r3_rho_sign_set='[]',r3_all_observed_rho_negative=None,r3_transcripts='[]',r3_element_ids='[]')
            for endpoint in ['rho','gamma']:
                for agg in ['min','median','max']:r[f'{endpoint}_R3_{agg}']=None
        assert r['r3_n_records']==int(m['r3_n_records']) and r['r3_n_complete']==int(m['r3_n_complete'])
        for endpoint in ['rho_R2','rho_R3_median']:
            r[endpoint+'_negative']=r[endpoint]<0 if r[endpoint] is not None else None
        r['R2_R3_central_signs_disagree']=(
            (r['rho_R2']>0)-(r['rho_R2']<0)!=(r['rho_R3_median']>0)-(r['rho_R3_median']<0)
            if r['rho_R2'] is not None and r['rho_R3_median'] is not None else None)
        r['R3_original_records_table']='processed/original_r3_records.csv'
        canonical.append(r)
    write('processed/source_fragility.csv',fragility)
    write('processed/canonical_all_source_partners.csv',canonical)
    write('processed/canonical_primary_panel.csv',[r for r in canonical if r['in_primary380']])
    write('processed/canonical_support400_panel.csv',[r for r in canonical if r['in_support400']])
    selectors={'P380':'in_primary380','S1_P400':'in_support400','S2_single_R3_record':'in_S2_single_R3_record','S3_no_missing_R3_records':'in_S3_no_missing_R3_records'}
    summary={'status':'FIRST_EVIDENCE_COMPLETE','cohorts':{},'effect_reference_grid':[.5,.55,.6,.65,.7],
             'scope':'finite published gene-labelled panel; no p values, confidence intervals, resampling or model training'}
    pairwise=[];matches=[];specific=[];envelopes=[];influence=[];references=[];matched_cases=[]
    for cohort,mask in selectors.items():
        panel=[r for r in canonical if r[mask]]
        positive=[r for r in panel if r['source_called']]; negative=[r for r in panel if not r['source_called']]
        if not positive or not negative:
            summary['cohorts'][cohort]={'status':'NO_SOURCE_CLASS_CONTRAST','N':len(panel),'source_called_N':len(positive),'source_not_called_N':len(negative)}
            if cohort=='P380':summary['status']='NO_SOURCE_CLASS_CONTRAST'
            continue
        effects=basic_effects(panel)
        sp,sg=specificity(panel)
        ms,mp=matched_diagnostic(panel)
        deletion=deletion_ranges(panel)
        for key in ['degree','gamma_R2','gamma_R3']:
            ms[f'mean_matched_{key}_rank_absolute_difference']=(
                math.fsum(p['within_case_weight']*p[f'{key}_rank_gap'] for p in mp)/ms['matched_source_called_N']
                if ms['matched_source_called_N'] else None)
        by_gene={r['gene']:r for r in panel}
        for s in sg:
            r=by_gene[s['gene']]
            s.update({k:r[k] for k in ['gemini_sensitive','rho_R2','rho_ATMi_R2','rho_ATRi_R2','rho_WEE1i_R2']})
            for drug in ['ATMi','ATRi','WEE1i']:
                s['DNAPKi_rank_exceeds_'+drug]=s['q_DNAPKi_minus_'+drug]>0
        for drug in ['ATMi','ATRi','WEE1i']:
            for cls in [True,False]:
                selected=[s['q_DNAPKi_minus_'+drug] for s in sg if s['source_called']==cls]
                sp[f'median_DNAPKi_minus_{drug}_'+('source_called' if cls else 'source_not_called')]=median(selected)
        direction={}
        for label,rs in [('all',panel),('source_called',positive),('source_not_called',negative)]:
            direction[label]={
                'N':len(rs),'R2_negative':sum(r['rho_R2']<0 for r in rs),
                'R3_median_negative':sum(r['rho_R3_median']<0 for r in rs),
                'both_negative':sum(r['rho_R2']<0 and r['rho_R3_median']<0 for r in rs),
                'R2_R3_central_signs_disagree':sum(r['R2_R3_central_signs_disagree'] for r in rs),
                'R3_all_observed_paired_rho_negative':sum(r['r3_all_observed_rho_negative'] for r in rs),
                'R3_sign_discordant':sum(r['r3_sign_discordance'] for r in rs),
                'R3_any_original_missing':sum(r['r3_any_missing'] for r in rs),
                'R3_multi_original_records':sum(r['r3_n_records']>1 for r in rs),
                'R3_original_record_N':sum(r['r3_n_records'] for r in rs),
                'R3_paired_complete_record_N':sum(r['r3_n_complete'] for r in rs)}
        alternative={}
        for variable in ['source_generic_fragility','gamma_R2','gamma_R3_median']:
            alternative[variable]={'source_called_median':median(r[variable] for r in positive),
                                    'source_not_called_median':median(r[variable] for r in negative)}
        most={}
        for key in ['A_R2','A_R3_median']:
            valid=[d for d in deletion['deletions'] if d['status']=='computed']
            maxchange=max(d['absolute_delta_'+key] for d in valid)
            most[key]=[{'gene':d['deleted_gene'],'source_called':d['source_called'],'delta':d['delta_'+key],
                        'after_deletion':d[key]} for d in valid if d['absolute_delta_'+key]==maxchange]
        summary['cohorts'][cohort]={'status':'COMPUTED','effects':effects,'matching':ms,'specificity':sp,
            'direction_counts':direction,'alternative_covariate_medians':alternative,
            'influence_ranges':{k:deletion[k] for k in ['all_genes','source_called_only']},'most_influential':most}
        pairwise.append({'cohort':cohort,**effects})
        envelopes.append({'cohort':cohort,'N':len(panel),'source_called_N':len(positive),
                          'lower':effects['A_R3_observed_record_lower'],'median':effects['A_R3_median'],
                          'upper':effects['A_R3_observed_record_upper'],'scope':'observed-record resolution envelope, not CI; missing values unbounded'})
        for row in mp: matches.append({'cohort':cohort,**row})
        for row in sg:specific.append({'cohort':cohort,**row})
        for row in deletion['deletions']:influence.append({'cohort':cohort,**row})
        for ref in summary['effect_reference_grid']:
            references.append({'cohort':cohort,'reference':ref,**{k:effects[k] for k in ['A_R2','A_R3_median','A_R3_observed_record_lower','A_R3_observed_record_upper']},
                **{k+'_at_or_above_reference':effects[k]>=ref for k in ['A_R2','A_R3_median','A_R3_observed_record_lower','A_R3_observed_record_upper']},
                'meaning':'descriptive reference only; no selected success threshold'})
        for case in positive:
            prs=[p for p in mp if p['source_called_gene']==case['gene']]
            matched_cases.append({'cohort':cohort,'gene':case['gene'],'source_called':True,'matching_available':bool(prs),
                'comparator_N':len(prs),'control_genes':json.dumps([p['control_gene'] for p in prs]),
                'A_R2_within_case':math.fsum(p['within_case_weight']*p['R2_tie_credit'] for p in prs) if prs else None,
                'A_R3_within_case':math.fsum(p['within_case_weight']*p['R3_tie_credit'] for p in prs) if prs else None})
    for name,rows in [('pairwise_effects',pairwise),('matched_control_pairs',matches),('matched_source_cases',matched_cases),
                      ('specificity_diagnostics',specific),('record_envelopes',envelopes),('influence_diagnostics',influence),('effect_reference_grid',references)]:
        write('results/'+name+'.csv',rows)
    for r in canonical:
        for cohort,mask in selectors.items():
            s=next((s for s in specific if s['cohort']==cohort and s['gene']==r['gene']),None)
            prefix=cohort+'__'
            r[prefix+'eligible']=r[mask]
            if not r[mask]:continue
            for k,v in s.items():
                if k.startswith('q_') or k.startswith('DNAPKi_') or k=='S_R2':r[prefix+k]=v
            if r['source_called']:
                case=next(c for c in matched_cases if c['cohort']==cohort and c['gene']==r['gene'])
                for k in ['matching_available','comparator_N','control_genes','A_R2_within_case','A_R3_within_case']:r[prefix+k]=case[k]
                r[prefix+'matching_role']='source_called_case'
            else:
                uses=[p for p in matches if p['cohort']==cohort and p['control_gene']==r['gene']]
                r[prefix+'matching_role']='eligible_source_not_called_comparator'
                r[prefix+'matched_to_source_cases']=json.dumps([p['source_called_gene'] for p in uses])
                r[prefix+'used_as_control_N']=len(uses)
                r[prefix+'total_control_weight']=math.fsum(p['within_case_weight'] for p in uses)
    write('results/gene_evidence_table.csv',canonical)
    elapsed=time.monotonic()-start
    summary['runtime_seconds']=elapsed
    (BASE/'results/analysis_summary.json').write_text(json.dumps(summary,indent=2,allow_nan=False)+'\n')
    runtime={'python':sys.version,'executable':sys.executable,'platform':platform.platform(),'metric_library':'Python standard library; no ML/statistical test package',
             'elapsed_analysis_seconds':elapsed,'completed_utc':datetime.now(timezone.utc).isoformat(),
             'new_downloads':0,'model_training':False,'new_pvalues':False,'gene_resampling':False}
    (BASE/'results/runtime_versions.json').write_text(json.dumps(runtime,indent=2)+'\n')
    print(json.dumps({k:{'effects':v.get('effects'),'matching':v.get('matching'),'specificity':v.get('specificity')} for k,v in summary['cohorts'].items()},indent=2))


if __name__=='__main__':main()
