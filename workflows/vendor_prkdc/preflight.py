"""Freeze authorized inputs and structural cohorts BEFORE outcome comparisons."""
import csv
import hashlib
import json
import math
import shutil
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
S0 = BASE.parent / 'ddr_target_bridge_stage0'
WORK = BASE.parents[1] / 'work/ddr_target_bridge_stage0'
SUPPLIED = BASE / 'supplied_lock'  # portable path only; overridden by wrapper
BIND = {
    'rho_R2':'rho:DNAPKi_vs_DMSO', 'gamma_R2':'gamma:DMSO_vs_T0',
    'rho_ATMi_R2':'rho:ATMi_vs_DMSO', 'rho_ATRi_R2':'rho:ATRi_vs_DMSO',
    'rho_WEE1i_R2':'rho:WEE1i_vs_DMSO',
    'rho_R3':'parent::rho:DNAPKi_vs_vehicle', 'gamma_R3':'parent::gamma:vehicle_vs_T0'}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path):
    with path.open(newline='') as f:
        return list(csv.DictReader(f))


def write(path, rows):
    keys = list(dict.fromkeys(k for r in rows for k in r))
    with path.open('x', newline='') as f:
        w=csv.DictWriter(f, fieldnames=keys); w.writeheader(); w.writerows(rows)


def finite(v):
    try: return math.isfinite(float(v))
    except (TypeError, ValueError): return False


def main():
    assert not (BASE/'lock/preflight_data_checks.json').exists(), 'STOP: data preflight already frozen'
    lock=json.loads((SUPPLIED/'DDR_TargetBridge_Stage1_Analysis_Lock.json').read_text())
    assert sha(S0/'Stage0_Report.md')==lock['source_stage0_report_sha256'], 'STOP: report hash conflict'
    before={str(p.relative_to(S0)):{'sha256':sha(p),'bytes':p.stat().st_size,'mode':oct(p.stat().st_mode&0o777)}
            for p in sorted(S0.rglob('*')) if p.is_file()}
    (BASE/'lock/stage0_before_inventory.json').write_text(json.dumps(before,indent=2)+'\n')
    for name in ['DDR_TargetBridge_Stage1_Protocol.md','DDR_TargetBridge_Stage1_Analysis_Lock.json','CODEX_EXECUTE_STAGE1.md']:
        shutil.copyfile(SUPPLIED/name, BASE/'lock'/name)
    manifest=load(S0/'manifest.csv')
    assert len(manifest)==3
    for r in manifest:
        assert sha(S0/r['local_path'])==r['sha256'], 'STOP: raw hash conflict'
    cached_hashes=json.loads((S0/'provenance/join_integrity_audit.json').read_text())['inputs_sha256']
    for rid in ['R2','R3']:
        p=WORK/f'{rid}_phenotypes.csv'
        assert sha(p)==cached_hashes[str(p)], 'STOP: parsed phenotype hash conflict'
    source=load(S0/'raw/SPIDR_Table3_GEMINI.csv')
    partners={}
    allgenes=set(); allpairs=set()
    for rownum,r in enumerate(source,2):
        a,b=r['gene_combination'].split(';')
        allgenes.update([a,b]); key=tuple(sorted([a,b])); assert key not in allpairs
        allpairs.add(key)
        if 'PRKDC' in (a,b):
            g=b if a=='PRKDC' else a
            assert g not in partners and finite(r['sens.score'])
            partners[g]={'gene':g,'source_row_id':f'R1:{rownum}','gene_combination':r['gene_combination'],
                         'gemini_sensitive':r['sens.score'],'source_called':float(r['sens.score'])<=-1}
    assert (len(source),len(allgenes),len(partners),sum(r['source_called'] for r in partners.values()))==(149787,548,547,36)
    schema=json.loads((S0/'schema_map.json').read_text())
    expected={'R2_core':BIND['rho_R2']+'|score','R2_drug_free':BIND['gamma_R2']+'|score',
              'R3_core':BIND['rho_R3']+'|score','R3_drug_free':BIND['gamma_R3']+'|score'}
    assert all(schema['chosen_endpoints'][k]==v for k,v in expected.items())
    assert set(schema['chosen_endpoints']['R2_specificity'])=={BIND[k]+'|score' for k in ['rho_ATMi_R2','rho_ATRi_R2','rho_WEE1i_R2']}
    metadata=load(S0/'screen_metadata.csv')
    for rid, group, dose, days in [('R2',BIND['rho_R2'],'1000','14'),('R3',BIND['rho_R3'],'625','11')]:
        meta=[r for r in metadata if r['resource_id']==rid and r['published_endpoint_group']==group]
        assert len(meta)==1 and meta[0]['concentration_nM']==dose and meta[0]['exposure_days']==days
        assert meta[0]['genotype_background']=='Parental A549 WT'
    r2rows=load(WORK/'R2_phenotypes.csv'); r3rows=load(WORK/'R3_phenotypes.csv')
    r2=defaultdict(dict); r3=defaultdict(list)
    for r in r2rows:
        for field,group in BIND.items():
            if not field.endswith('R2'): continue
            g=r[group+'|target']
            if g not in partners: continue
            assert field not in r2[g], 'STOP: unexpected R2 gene collapse requirement'
            r2[g][field]=r
    allrecords=[]; identities=[]; seen=set()
    for r in r3rows:
        identity=(r['__excel_row'],r['sgID_AB'])
        assert identity not in seen; seen.add(identity)
        complete=finite(r[BIND['rho_R3']+'|score']) and finite(r[BIND['gamma_R3']+'|score'])
        entry={'record_id':f'R3:{r["__excel_row"]}', **r,
               'WT_rho_parent_gamma_paired_complete':complete,
               'is_source_PRKDC_partner':r['target'] in partners,
               'WT_context_only_for_analysis':True}
        allrecords.append(entry)
        identities.append({k:entry[k] for k in ['record_id','__excel_row','sgID_AB','target','transcript','WT_rho_parent_gamma_paired_complete','is_source_PRKDC_partner']})
        if r['target'] in partners: r3[r['target']].append(entry)
    assert len(allrecords)==20451 and sum(len(v)>1 for v in r3.values())==22
    write(BASE/'processed/original_r3_records.csv',allrecords)
    write(BASE/'lock/r3_record_identity_manifest.csv',identities)
    support={r['partner']:r for r in load(S0/'qualified_support.csv')}
    masks=[]
    for g,s in sorted(partners.items()):
        complete_records=[r for r in r3.get(g,[]) if r['WT_rho_parent_gamma_paired_complete']]
        r2complete=len(r2[g])==5 and all(finite(r[group+'|score']) for field,r in r2[g].items() for group in [BIND[field]])
        consistent=len(r2[g])==5 and len({r[BIND[field]+'|transcript'] for field,r in r2[g].items()})==1
        exact=len(r2[g])==5 and bool(r3.get(g))
        in400=r2complete and bool(complete_records)
        in380=in400 and consistent
        assert (support[g]['three_way_symbol_support']=='True')==exact
        assert (support[g]['three_way_all_required_endpoints_finite_gene_level']=='True')==in400
        assert (support[g]['three_way_finite_with_R2_controls_same_transcript']=='True')==in380
        masks.append(dict(s,in_exact419=exact,in_support400=in400,in_primary380=in380,
            in_S2_single_R3_record=in380 and len(r3[g])==1 and len(complete_records)==1,
            in_S3_no_missing_R3_records=in380 and len(r3[g])==len(complete_records),
            r2_transcript_consistent=consistent,
            r2_transcripts=json.dumps({k:r[BIND[k]+'|transcript'] for k,r in r2[g].items()},sort_keys=True),
            r2_original_rows=json.dumps({k:r['__excel_row'] for k,r in r2[g].items()},sort_keys=True),
            r3_n_records=len(r3.get(g,[])),r3_n_complete=len(complete_records),
            r3_record_ids=';'.join(r['record_id'] for r in r3.get(g,[])),
            r3_complete_record_ids=';'.join(r['record_id'] for r in complete_records),
            attribution_caveat=support[g]['attribution_flag'],
            exclusion_reason=('included_primary' if in380 else 'R2_transcript_inconsistent' if in400 else
                              'no_paired_complete_R3_record' if exact and not complete_records else
                              'missing_required_finite_endpoint' if exact else 'not_in_exact_three_way_symbol_support')))
    assert [sum(r[k] for r in masks) for k in ['in_exact419','in_support400','in_primary380']]==[419,400,380]
    for name,rows in [('hypothesis_membership.csv',masks),('primary380_manifest.csv',[r for r in masks if r['in_primary380']]),
                      ('support400_manifest.csv',[r for r in masks if r['in_support400']])]:
        write(BASE/'lock'/name,rows)
    for sid,key in [('S1','in_support400'),('S2','in_S2_single_R3_record'),('S3','in_S3_no_missing_R3_records')]:
        write(BASE/'processed'/f'{sid}_manifest.csv',[r for r in masks if r[key]])
    flow=[]
    for label,key in [('source547',None),('exact419','in_exact419'),('support400','in_support400'),('primary380','in_primary380'),
                      ('S2_single_R3_record','in_S2_single_R3_record'),('S3_no_missing_R3_records','in_S3_no_missing_R3_records')]:
        rows=[r for r in masks if key is None or r[key]]
        flow.append({'stage':label,'n_genes':len(rows),'source_called':sum(r['source_called'] for r in rows),
                     'source_not_called':sum(not r['source_called'] for r in rows)})
    write(BASE/'processed/support_flow.csv',flow)
    bindings={'canonical_fields':{k:{'resource':'R2' if k.endswith('R2') else 'R3','group':g,'raw_column':g+'|score','value_policy':'published value unchanged'} for k,g in BIND.items()},
        'source_called':{'resource':'R1','column':'sens.score','operator':'<=','threshold':-1},
        'directions':{'Y2':'-rho_R2','Y3':'-rho_R3_median','fragility_untreated':'-gamma; matching only'},
        'r3_pairing':'Same Excel row + sgID_AB; parent rho and parent gamma; no vehicle gamma/KO backfill.',
        'r3_summary':'Separate unweighted component medians on same paired-complete original-record set; not a single measured intervention.',
        'r3_sign_discordance':'More than one of strict negative / exactly zero / strict positive among paired-complete rho. Store full sign set; missing has no sign.',
        'cohort_selection':'Only exact identities, finiteness and original transcript/record structure; no destination hit/magnitude filter.',
        'tie_and_caliper_arithmetic':'Midrank rational coordinates; inclusive .20 caliper; exact squared-distance ties broken by gene symbol.',
        'original_r3_records_scope':'All20451 published rows and all original columns retained; only parent WT fields used in analysis. Controls and genes outside source panel are flagged, never used as source-partner comparators.',
        'mechanical_deviations':['shasum failed due host locale; hashlib used instead','Bundled scipy/matplotlib absent; pure Python/numpy metrics and existing R graphics selected; no downloads or installs.']}
    (BASE/'lock/source_binding.json').write_text(json.dumps(bindings,indent=2)+'\n')
    inputs={str(S0/r['local_path']):{'sha256':r['sha256'],'bytes':int(r['received_bytes'])} for r in manifest}
    for p in [WORK/'R2_phenotypes.csv',WORK/'R3_phenotypes.csv']:
        inputs[str(p)]={'sha256':sha(p),'bytes':p.stat().st_size}
    (BASE/'lock/source_hashes.json').write_text(json.dumps(inputs,indent=2)+'\n')
    outcome={'status':'DATA_PREFLIGHT_PASS_PENDING_SYNTHETIC_TESTS','utc':datetime.now(timezone.utc).isoformat(),
        'protocol_report_hash_match':True,'raw_and_parsed_hashes_match':True,'field_bindings_unambiguous':True,
        'structural_masks_reconstructed':True,'all_R3_records_retained':len(allrecords), 'source_stage0_files_snapshotted':len(before),
        'support_flow':flow,'no_cross_source_effects_computed':True,'runtime':sys.version,
        'protocol_conflict_audit':'Independent second agent found no semantic conflict.'}
    (BASE/'lock/preflight_data_checks.json').write_text(json.dumps(outcome,indent=2)+'\n')
    print(json.dumps(outcome,indent=2))


if __name__=='__main__':
    main()
