#!/usr/bin/env python3
"""Portable, bounded replay of the frozen historical source linkage and crossover.
No discovery, source thresholds, match definitions or endpoints are redesigned.
The original analysis main is sliced at statement boundaries BEFORE specificity,
deletions and other previously completed analyses; its canonical assembly is unchanged.
"""
from pathlib import Path
import argparse, ast, csv, hashlib, importlib.util, json, math, shutil, sys
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def module(name,path):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def compare_csv(a,b):
 # Every literal identity, missing cell and full-precision stored value is checked.
 with a.open(newline='') as f:x=list(csv.reader(f))
 with b.open(newline='') as f:y=list(csv.reader(f))
 if x!=y:
  for i,(u,v) in enumerate(zip(x,y)):
   if u!=v:raise ValueError(f'Historical table conflict: {a.name}, row {i+1}')
  raise ValueError('Historical table dimension conflict: '+a.name)
 return {'table':a.name,'rows':len(x)-1,'columns':len(x[0]),'comparison':'every CSV cell identical'}

def run(out):
 if out.exists():raise FileExistsError('Choose a new output directory')
 for r in json.loads((ROOT/'data_metadata/historical_input_manifest.json').read_text()):
  p=ROOT/r['path'];assert p.stat().st_size==r['bytes'] and sha(p)==r['sha256'],r['path']
 out.mkdir(parents=True);src=ROOT/'data/historical_sources';work=out/'parsed';work.mkdir()
 stage0=out/'stage0';shutil.copytree(src/'stage0',stage0)
 base=out/'prkdc';
 for d in ['lock','processed','results']:(base/d).mkdir(parents=True,exist_ok=True)
 vendor=ROOT/'workflows/vendor_prkdc';sys.path.insert(0,str(vendor))
 extract=module('original_extract',vendor/'extract_xlsx.py');extract.BASE=stage0;extract.WORK=work
 parsed_expected={'R2':'8b653d829adec8d975697a70e48bf5d1ac70cb9534ac3cd7ad4da9b4f504fcdf','R3':'e7a2f95517936cc307d04b144c24ad565e0688dcaa83c979177449231a637910'}
 parsed_checks=[]
 for rid,name in [('R2','DDRi_Dataset1_v2.xlsx'),('R3','DDRi_Dataset3_v3.xlsx')]:
  info=extract.extract(rid,name);p=work/(rid+'_phenotypes.csv');assert sha(p)==parsed_expected[rid],rid+' parsed bytes conflict'
  record=next(s['extraction'] for s in info['sheets'] if s['name']=='Gene Level Phenotypes')
  parsed_checks.append({'resource':rid,'rows':record['data_rows'],'columns':record['columns_including_excel_row'],'sha256':sha(p),'all_literal_cells_match_original':True})
 # Original preflight expects a cached-hash dictionary keyed by its working path.
 # Adapt only those path keys to this fresh run; the expected hashes are unchanged.
 (stage0/'provenance').mkdir();(stage0/'provenance/join_integrity_audit.json').write_text(json.dumps({'inputs_sha256':{str(work/(r+'_phenotypes.csv')):h for r,h in parsed_expected.items()}}))
 pre=module('original_preflight',vendor/'preflight.py');pre.BASE=base;pre.S0=stage0;pre.WORK=work;pre.SUPPLIED=src/'supplied_lock';pre.main()
 analyze=module('original_analyze',vendor/'analyze.py');analyze.BASE=base;analyze.S0=stage0;analyze.WORK=work
 tree=ast.parse((vendor/'analyze.py').read_text());main=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='main')
 def assign_name(n,name):return isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id==name for t in n.targets)
 begin=next(i for i,n in enumerate(main.body) if assign_name(n,'members'))
 end=next(i for i,n in enumerate(main.body) if assign_name(n,'selectors'))
 main.name='assemble_frozen_canonical';main.body=main.body[begin:end]+[ast.Return(value=ast.Name(id='canonical',ctx=ast.Load()))]
 sliced=ast.fix_missing_locations(ast.Module(body=[main],type_ignores=[]));exec(compile(sliced,'frozen_canonical_slice','exec'),analyze.__dict__)
 canonical=analyze.assemble_frozen_canonical();checks=[]
 for folder in ['lock','processed']:
  for p in sorted((src/'expected'/folder).iterdir()):checks.append(compare_csv(base/folder/p.name,p))
 metrics=module('metrics_frozen',vendor/'metrics.py');expected=json.loads((src/'expected/results/analysis_summary.json').read_text())
 matches=[];cases=[];pairwise=[];summaries={}
 selectors={'P380':'in_primary380','S1_P400':'in_support400','S2_single_R3_record':'in_S2_single_R3_record','S3_no_missing_R3_records':'in_S3_no_missing_R3_records'}
 for cohort,key in selectors.items():
  panel=[r for r in canonical if r[key]];effects=metrics.basic_effects(panel);ms,mp=metrics.matched_diagnostic(panel)
  for k in ['degree','gamma_R2','gamma_R3']:
   ms[f'mean_matched_{k}_rank_absolute_difference']=math.fsum(p['within_case_weight']*p[f'{k}_rank_gap'] for p in mp)/ms['matched_source_called_N'] if ms['matched_source_called_N'] else None
  assert effects==expected['cohorts'][cohort]['effects'],cohort+' effects conflict'
  assert ms==expected['cohorts'][cohort]['matching'],cohort+' matching conflict'
  summaries[cohort]={'effects':effects,'matching':ms};pairwise.append({'cohort':cohort,**effects})
  matches.extend({'cohort':cohort,**p} for p in mp)
  for case in [r for r in panel if r['source_called']]:
   prs=[p for p in mp if p['source_called_gene']==case['gene']]
   cases.append({'cohort':cohort,'gene':case['gene'],'source_called':True,'matching_available':bool(prs),'comparator_N':len(prs),'control_genes':json.dumps([p['control_gene'] for p in prs]),'A_R2_within_case':math.fsum(p['within_case_weight']*p['R2_tie_credit'] for p in prs) if prs else None,'A_R3_within_case':math.fsum(p['within_case_weight']*p['R3_tie_credit'] for p in prs) if prs else None})
 for name,rows in [('matched_control_pairs',matches),('matched_source_cases',cases),('pairwise_effects',pairwise)]:
  analyze.write('results/'+name+'.csv',rows);checks.append(compare_csv(base/'results'/(name+'.csv'),src/'expected/results'/(name+'.csv')))
 (base/'results/reproduced_effects_and_matching.json').write_text(json.dumps(summaries,indent=2)+'\n')
 # All retained/omitted historical calls, using the reconstructed source identity map.
 analyze.write('results/retained_source_called12.csv',[r for r in canonical if r['source_called'] and r['in_primary380']])
 analyze.write('results/omitted_source_called24.csv',[r for r in canonical if r['source_called'] and not r['in_primary380']])
 sys.path.insert(0,str(ROOT/'workflows/vendor_crossover'));xr=module('frozen_xlsx_crossover',ROOT/'workflows/vendor_crossover/xlsx_readonly.py')
 cross=ROOT/'revision/data/crossover';bg=pd.read_csv(cross/'common_background.tsv',sep='\t',keep_default_na=False)
 identities={c:{r.gene:{'row':int(getattr(r,c+'_xlsx_row')),'transcript':str(getattr(r,c+'_transcript'))} for r in bg.itertuples()} for c in ['PARPi','WEE1i']}
 vectors,raw,meta=xr.read_allowed(stage0/'raw/DDRi_Dataset1_v2.xlsx',identities,bg.gene)
 assert len(vectors)==6 and not meta['issues'],'Frozen endpoint availability conflict'
 actual=pd.DataFrame([r for rows in raw.values() for r in rows]);reference=pd.read_csv(cross/'R2_frozen_background_values.tsv.gz',sep='\t',keep_default_na=False,float_precision='round_trip')
 keys=['condition','gene'];actual=actual.sort_values(keys).reset_index(drop=True);reference=reference.sort_values(keys).reset_index(drop=True)
 assert list(actual.columns)==list(reference.columns) and actual.shape==reference.shape,(actual.columns,reference.columns)
 for col in actual:
  assert actual[col].equals(reference[col]),'Source workbook/export conflict in '+col
 cout=out/'crossover';cout.mkdir();actual.to_csv(cout/'R2_frozen_background_values_reextracted.tsv.gz',sep='\t',index=False)
 rev=module('revision_numerics',ROOT/'revision/code/revise_existing_outputs.py');spec=json.loads((cross/'PROTOCOL_LOCK.json').read_text());refmods=pd.read_csv(cross/'R2_modules.tsv',sep='\t').set_index(['condition','module_id']);refcons=pd.read_csv(cross/'R2_contrasts.tsv',sep='\t').set_index('condition')
 reconstructed=[];comparisons=[]
 for cond,f in actual.groupby('condition'):
  assert len(f)==16549;assert hashlib.sha256(('\n'.join(sorted(f.gene))+'\n').encode()).hexdigest()==spec['common_background_sha256_newline']
  ts={}
  for mod,mem in spec['modules'].items():
   t,median,z=rev.module_values(f,mem);ts[mod]=t
   for field,value in [('T',t),('raw_median',median)]:
    err=abs(value-refmods.loc[(cond,mod),field]);assert err<=1e-10;comparisons.append({'condition':cond,'module_id':mod,'field':field,'absolute_error':err})
   reconstructed.append({'condition':cond,'module_id':mod,'T':t,'raw_median':median,'background_n':len(f)})
  delta=ts['HAP1.L2.32']-ts['HAP1.L2.139'];err=abs(delta-refcons.loc[cond,'contrast_HR_minus_metabolic']);assert err<=1e-10;comparisons.append({'condition':cond,'module_id':'contrast','field':'contrast','absolute_error':err})
 pd.DataFrame(reconstructed).to_csv(cout/'R2_modules_from_workbook.tsv',sep='\t',index=False);pd.DataFrame(comparisons).to_csv(cout/'rank_parity.tsv',sep='\t',index=False)
 receipt={'status':'HISTORICAL_SOURCE_LINKAGE_MATCHING_AND_WORKBOOK_REPRODUCTION_PASS','parsed_workbooks':parsed_checks,'prkdc_table_checks':checks,'prkdc_cohorts':summaries,'source_partners':547,'source_called':36,'exact_support':419,'finite_support':400,'primary_support':380,'primary_called':12,'primary_not_called':368,'matched_pair_rows':len(matches),'matched_case_rows':len(cases),'R2_workbook_export_rows':len(actual),'R2_gene_background':16549,'R2_conditions':6,'every_raw_value_gene_transcript_row_exact':True,'reranking_checks':len(comparisons),'reranking_max_absolute_error':max(r['absolute_error'] for r in comparisons),'whole_study_reproduction':False,'new_biological_analysis':False,'original_scripts_used':'Stage0 XLSX extractor; Stage1 preflight + unchanged canonical-assembly AST slice + frozen metrics; original crossover XLSX reader','path_adaptations':'preflight SUPPLIED constant and cached parsed-path dictionary only'}
 (out/'HISTORICAL_REPRODUCTION_RECEIPT.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps({'status':receipt['status'],'table_checks':len(checks),'rows_compared':len(actual),'matched_pairs':len(matches)},indent=2))

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();run(a.output.resolve())
