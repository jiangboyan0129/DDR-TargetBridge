"""Transparent deterministic count-level kernels; no fitted predictor or target calls.

Parent point-score equations audited against ScreenPro2 v0.4.14/v0.4.15.
This is NOT the full historical top-guide/pseudogene/TSS-pvalue pipeline.
Alternative: fixed reference-qualified constructs, NTC-centred per-sample logs,
then equal median aggregation within target×transcript (no best-TSS selection).
"""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import csv, gzip, hashlib, itertools, json, math
from collections import defaultdict
from typing import Any
import numpy as np
import h5py

class DataContractError(ValueError): pass

@dataclass
class CountData:
    counts: np.ndarray
    sample_ids: list[str]
    obs: dict[str, np.ndarray]
    ids: list[str]
    var: dict[str, np.ndarray]


def hash_file(path: Path) -> str:
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(1<<20), b''): h.update(b)
    return h.hexdigest()


def checked_path(root: Path, relative: str, sha256: str|None=None, size: int|None=None) -> Path:
    root=Path(root).resolve(strict=True)
    relative_path=Path(relative)
    if relative_path.is_absolute() or '..' in relative_path.parts:
        raise DataContractError('Only contained relative paths are accepted')
    p=(root/relative_path).resolve(strict=True)
    if p==root or root not in p.parents or not p.is_file():
        raise DataContractError('Input escapes allowed root or is not a file')
    if size is not None and p.stat().st_size!=size: raise DataContractError('Input byte-size mismatch: '+relative)
    if sha256 is not None and hash_file(p)!=sha256: raise DataContractError('Input SHA-256 mismatch: '+relative)
    return p


def text_value(v: Any) -> Any:
    if isinstance(v, (bytes,np.bytes_)): return bytes(v).decode('utf-8')
    if isinstance(v,np.generic): return v.item()
    return v


def h5_vector(node: Any) -> np.ndarray:
    if isinstance(node,h5py.Dataset):
        a=np.asarray(node[()])
        if a.ndim!=1: raise DataContractError('Metadata vector must have one dimension')
        return np.asarray([text_value(x) for x in a],dtype=object)
    if not isinstance(node,h5py.Group): raise DataContractError('Unsupported metadata node')
    if {'codes','categories'}.issubset(node.keys()):
        codes=np.asarray(node['codes'][()]); cats=h5_vector(node['categories'])
        if codes.ndim!=1 or not np.issubdtype(codes.dtype,np.integer): raise DataContractError('Invalid categorical codes')
        if np.any(codes < -1) or np.any(codes>=len(cats)): raise DataContractError('Categorical code out of range')
        # -1 is missing; NEVER python negative indexing to last category.
        return np.asarray([None if int(k)==-1 else cats[int(k)] for k in codes],dtype=object)
    if {'mask','values'}.issubset(node.keys()):
        vals=h5_vector(node['values']); mask=np.asarray(node['mask'][()],bool)
        if mask.shape!=vals.shape: raise DataContractError('Nullable vector shape mismatch')
        vals[mask]=None; return vals
    raise DataContractError('Unsupported AnnData metadata encoding')


def h5_frame(group: h5py.Group) -> tuple[list[str],dict[str,np.ndarray]]:
    idxname=text_value(group.attrs.get('_index','_index'))
    if idxname not in group:
        # The prior v2 schema names the true var index sgID; not a guessed numeric index.
        if group.name.endswith('/var') and 'sgID' in group: idxname='sgID'
        else: raise DataContractError('Missing explicit AnnData row index')
    idx=h5_vector(group[idxname])
    if any(x is None or not isinstance(x,str) or not x for x in idx): raise DataContractError('Invalid row identity')
    if len(set(idx))!=len(idx): raise DataContractError('Duplicate row identity')
    cols={k:h5_vector(v) for k,v in group.items() if k!=idxname and k!='__categories'}
    if any(len(x)!=len(idx) for x in cols.values()): raise DataContractError('Metadata length mismatch')
    return list(idx),cols


def validate_counts(x: np.ndarray) -> None:
    if x.ndim!=2 or not x.size: raise DataContractError('Counts must be a nonempty sample×construct matrix')
    if not np.issubdtype(x.dtype,np.number): raise DataContractError('Nonnumeric counts')
    if not np.isfinite(x).all(): raise DataContractError('Missing/nonfinite raw counts')
    if (x<0).any(): raise DataContractError('Negative raw counts')
    if not np.equal(x,np.floor(x)).all(): raise DataContractError('Noninteger raw counts; do not treat normalised scores as counts')


def read_counts(path: Path, expected_shape: tuple[int,int]|None=None, max_bytes: int=1_000_000_000) -> CountData:
    with Path(path).open('rb') as f: magic=f.read(8)
    if magic!=b'\x89HDF\r\n\x1a\n':
        raise DataContractError('Expected HDF5 signature, even when filename ends .gz; do not gunzip by extension')
    with h5py.File(path,'r') as f:
        if not {'X','obs','var'}.issubset(f.keys()): raise DataContractError('Missing X/obs/var')
        node=f['X']
        if not isinstance(node,h5py.Dataset): raise DataContractError('Sparse/unexpected X not part of verified dense source schema')
        if len(node.shape)!=2 or np.prod(node.shape)*8>max_bytes: raise DataContractError('Count shape/memory exceeds contract')
        if expected_shape and tuple(node.shape)!=tuple(expected_shape): raise DataContractError('Count dimensions changed')
        obsids,obs=h5_frame(f['obs']); varids,var=h5_frame(f['var'])
        if (len(obsids),len(varids))!=node.shape: raise DataContractError('Matrix orientation disagrees with explicit indices')
        x=np.asarray(node[()],dtype=np.float64)
    validate_counts(x)
    for k in ['condition','replicate']:
        if k not in obs or any(v is None for v in obs[k]): raise DataContractError('Missing required sample field '+k)
    reps=np.asarray(obs['replicate'],dtype=float)
    if not np.isfinite(reps).all() or np.any(reps<1) or not np.equal(reps,np.floor(reps)).all(): raise DataContractError('Invalid replicate labels')
    for k in ['target','targetType']:
        if k not in var or any(v is None for v in var[k]): raise DataContractError('Missing required construct field '+k)
    if not set(var['targetType']).issubset({'gene','negative_control'}): raise DataContractError('Unexpected control type')
    return CountData(x,obsids,obs,varids,var)


def read_reference(path: Path) -> dict[str,dict[str,str]]:
    with gzip.open(path,'rt',encoding='utf-8',newline='') as f:
        rows=list(csv.DictReader(f,delimiter='\t'))
    out={r['original_label']:r for r in rows}
    if len(out)!=len(rows): raise DataContractError('Reference IDs not unique')
    return out


def bind_reference(d: CountData, ref: dict[str,dict[str,str]]) -> list[dict[str,str]]:
    rows=[]
    for i,k in enumerate(d.ids):
        if k not in ref: raise DataContractError('Construct missing reference: '+k)
        r=ref[k]
        if r['gene_symbol_as_published']!=d.var['target'][i]: raise DataContractError('Target mismatch for '+k)
        rows.append(r)
    return rows


def subset_samples(d: CountData, indices: list[int]|np.ndarray) -> CountData:
    ix=np.asarray(indices,dtype=int)
    return CountData(d.counts[ix].copy(),[d.sample_ids[i] for i in ix],{k:v[ix].copy() for k,v in d.obs.items()},d.ids.copy(),{k:v.copy() for k,v in d.var.items()})


def condition_indices(d: CountData, condition: str) -> np.ndarray:
    ix=np.flatnonzero(d.obs['condition']==condition)
    if not len(ix): raise DataContractError('Missing condition '+condition)
    return ix # preserve true deposited ordering for historical reconstruction


def append_parent_pseudo_t0(d: CountData) -> CountData:
    ix=condition_indices(d,'T0')
    if len(ix)!=2 or set(int(x) for x in d.obs['replicate'][ix])!={1,2}:
        raise DataContractError('Historical pseudo-T0 requires exactly two real T0 records')
    x=np.vstack([d.counts,np.mean(d.counts[ix],axis=0).astype(np.int64)])
    obs={k:np.append(v,v[ix[0]]) for k,v in d.obs.items()}
    obs['replicate'][-1]=3
    sid=d.sample_ids[ix[0]].rsplit('rep',1)[0]+'rep3_SYNTHETIC_PARENT_ONLY'
    return CountData(x,d.sample_ids+[sid],obs,d.ids.copy(),{k:v.copy() for k,v in d.var.items()})


def zero_replace(x: np.ndarray, value: float=.5) -> np.ndarray:
    if not np.isfinite(value) or value<=0: raise DataContractError('Invalid pseudocount')
    y=np.array(x,dtype=float,copy=True);y[y==0]=value;return y


def median_log_ratio_normalize(x: np.ndarray) -> tuple[np.ndarray,np.ndarray]:
    if x.ndim!=2 or x.shape[1]==0 or not np.isfinite(x).all() or np.any(x<=0): raise DataContractError('Positive finite counts required for size factors')
    logs=np.log(x); logmeans=logs.mean(axis=0)
    sf=np.exp(np.median(logs-logmeans,axis=1))
    return x/sf[:,None],sf


def normalised_keep(ref: np.ndarray,drug: np.ndarray,kind: str,threshold: float=40) -> np.ndarray:
    allx=np.concatenate([ref,drug],axis=0)
    if kind=='mean': return np.mean(allx,axis=0)>=threshold
    if kind in {'both','all'}: return np.min(allx,axis=0)>=threshold
    if kind in {'either','any'}: return np.max(allx,axis=0)>=threshold
    raise DataContractError('Unknown historical count-filter rule')


def parent_delta(ref: np.ndarray,drug: np.ndarray,control: np.ndarray,keep: np.ndarray,growth: float=1.) -> tuple[np.ndarray,np.ndarray]:
    """Historical compare_reps point scores; source positional replicate convention.
    Returns per-positional-pair scores and row mean. No inference from pseudo units.
    """
    if ref.shape!=drug.shape or ref.ndim!=2: raise DataContractError('Parent positional score requires equal replicate dimensions')
    if np.any(ref<=0) or np.any(drug<=0): raise DataContractError('Parent score expects positive normalised counts')
    keep=np.asarray(keep,bool)
    if keep.shape!=(ref.shape[1],) or np.asarray(control).shape!=(ref.shape[1],): raise DataContractError('Control/retention mask shape mismatch')
    ctr=np.asarray(control,bool)&keep
    if not ctr.any(): raise DataContractError('No retained negative controls')
    if not np.isfinite(growth) or growth<=0: raise DataContractError('Undefined growth denominator')
    logratio=np.log2(drug)-np.log2(ref)
    centre=np.median(logratio[:,ctr],axis=1)
    scores=(logratio-centre[:,None])/growth
    scores[:,~keep]=np.nan
    return scores,np.mean(scores,axis=0)


def ntc_sample_logs(x: np.ndarray,controls: np.ndarray) -> np.ndarray:
    controls=np.asarray(controls,bool)
    if controls.shape!=(x.shape[1],): raise DataContractError('NTC mask shape mismatch')
    if not controls.any(): raise DataContractError('No qualified controls')
    logx=np.log2(zero_replace(x))
    return logx-np.median(logx[:,controls],axis=1)[:,None]


def reference_eligibility(x: np.ndarray,t0: np.ndarray,vehicle: np.ndarray,threshold: float=40) -> np.ndarray:
    if not len(t0) or not len(vehicle): raise DataContractError('Real T0 and vehicle required')
    return (np.mean(x[t0],axis=0)>=threshold)&(np.mean(x[vehicle],axis=0)>=threshold)


def working_se(ref: np.ndarray,drug: np.ndarray) -> tuple[float,float,float,int]:
    """Working independent-culture SE and all possible paired-SE range.
    A pairing sensitivity, NOT CI, null distribution or extra replicate count.
    """
    ref=np.asarray(ref,float);drug=np.asarray(drug,float)
    if min(len(ref),len(drug))<2: return float('nan'),float('nan'),float('nan'),0
    u=math.sqrt(float(np.var(ref,ddof=1)/len(ref)+np.var(drug,ddof=1)/len(drug)))
    if len(ref)!=len(drug) or len(ref)>6:return u,float('nan'),float('nan'),0
    vals=[float(np.std(drug-ref[list(p)],ddof=1)/math.sqrt(len(ref))) for p in itertools.permutations(range(len(ref)))]
    return u,min(vals),max(vals),len(vals)


def aggregate_reference_fixed(d: CountData,mapping: list[dict[str,str]],threshold: float=40,min_controls: int=20) -> tuple[list[dict],dict]:
    v='DMSO' if 'DMSO' in set(d.obs['condition']) else 'vehicle'
    ti=condition_indices(d,'T0'); vi=condition_indices(d,v)
    base_eligible=reference_eligibility(d.counts,ti,vi,threshold)
    eligible=base_eligible.copy()
    sequence_ok=np.array([int(r['reference_sequence_gene_count'])==1 for r in mapping])
    eligible &= sequence_ok
    ctr=eligible&(d.var['targetType']=='negative_control')
    if int(ctr.sum())<min_controls:raise DataContractError('Too few qualified NTC constructs; do not relax threshold automatically')
    logs=ntc_sample_logs(d.counts,ctr)
    groups=defaultdict(list)
    for i,r in enumerate(mapping):
        if d.var['targetType'][i]=='negative_control':continue
        # Missing transcript stays its own explicit UNKNOWN stratum; not merged with known TSS.
        tr=r['transcript_id'] if r['transcript_id'] not in {'','UNKNOWN','NOT_APPLICABLE'} else 'UNKNOWN_TRANSCRIPT'
        groups[(r['gene_symbol_as_published'],tr)].append(i)
    wanted=['Pi','Ri','Mi','Wi','Ki'] if v=='DMSO' else ['DNAPKi']
    results=[];detail=[]
    for (gene,tr),allix in sorted(groups.items()):
        use=[i for i in allix if eligible[i]]
        sample=np.median(logs[:,use],axis=1) if use else np.full(len(d.sample_ids),np.nan)
        for j,sid in enumerate(d.sample_ids):
            if str(d.obs['condition'][j]) not in [v,'T0']+wanted:continue
            detail.append({'target':gene,'transcript':tr,'sample_id':sid,'condition':d.obs['condition'][j],'reference_eligible_construct_N':len(use),'sample_gene_log_NTC':sample[j]})
        for cond in wanted:
            di=condition_indices(d,cond)
            ref=sample[vi];drug=sample[di]
            beta=float(np.mean(drug)-np.mean(ref)) if use else float('nan')
            gamma=float(np.mean(ref)-np.mean(sample[ti])) if use else float('nan')
            u,lo,hi,npair=working_se(ref,drug) if use else (float('nan'),)*3+(0,)
            results.append({'target':gene,'transcript':tr,'drug_condition':cond,'reference_condition':v,'all_matrix_construct_N':len(allix),'reference_eligible_construct_N':len(use),'raw_low_reference_N':sum(not base_eligible[i] for i in allix),'multigene_sequence_N':sum(not sequence_ok[i] for i in allix),'drug_culture_records':len(di),'vehicle_culture_records':len(vi),'real_T0_records':len(ti),'status':'ESTIMABLE_REFERENCE_QUALIFIED' if use else 'NOT_ESTIMABLE','log2_count_contrast_NTC':beta,'untreated_log2_contrast_NTC':gamma,'working_SE_independent_cultures':u,'possible_pairing_SE_min':lo,'possible_pairing_SE_max':hi,'enumerated_pairings_not_extra_N':npair,'drug_zero_cells_retained':int(np.sum(d.counts[np.ix_(di,use)]==0)) if use else 0,'selected_construct_ids':';'.join(d.ids[i] for i in use)})
    meta={'threshold_reference_mean_raw':threshold,'control_constructs':int(ctr.sum()),'reference_eligible_constructs':int(eligible.sum()),'all_constructs':len(mapping),'analysis':'target×transcript; fixed guide set; no top-guide or best-p TSS selection','uncertainty':'working SE assumes independent endpoint cultures; possible pairings are assumption sensitivity, NOT confidence intervals','details':detail,'eligible_mask':eligible}
    return results,meta
