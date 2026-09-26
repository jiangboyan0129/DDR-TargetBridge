#!/usr/bin/env python3
"""Public verification and explicitly scoped reproduction; never downloads data."""
from pathlib import Path
import argparse,json,os,subprocess,sys
ROOT=Path(__file__).resolve().parents[1]
def external_missing():
 m=json.loads((ROOT/'data_metadata/external_inputs.json').read_text())
 return [x for x in m if not (ROOT/x['public_path']).is_file()]
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('mode',choices=['verify','core','historical']);p.add_argument('--output',type=Path);a=p.parse_args()
 if sys.flags.optimize:raise SystemExit('Do not use python -O: preserved checks use assertions.')
 env=os.environ.copy();env.update(PYTHONDONTWRITEBYTECODE='1',OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',PYTHONPATH=str(ROOT/'workflows/vendor_prkdc'))
 if a.mode=='verify':
  cmds=[['tools/verify_release.py'],['tools/public_gate.py'],['-m','unittest','discover','-s','tests','-v'],['-m','unittest','discover','-s','revision/tests','-v'],['-m','unittest','discover','-s','workflows/vendor_prkdc/tests','-v'],['-m','unittest','discover','-s','public_tests','-v']]
 else:
  out=(a.output or Path('.build')/(a.mode+'-1')).resolve()
  for folder in ['data','data_metadata','src','workflows','tests','results','revision','config','reports','figures','portfolio','presentation','provenance','docs','environment','tools','public_tests']:
   d=(ROOT/folder).resolve()
   if out==d or out.is_relative_to(d):raise SystemExit('Refusing output inside preserved content')
  if out==ROOT or out.exists():raise SystemExit('Choose a fresh output directory')
  if a.mode=='historical' and external_missing():
   missing=external_missing();print(json.dumps({'status':'EXTERNAL_INPUTS_REQUIRED','missing':[x['public_path'] for x in missing],'instructions':'docs/retrieval.md','automatic_download':False}));raise SystemExit(3)
  cmds=[['workflows/reproduce_public_core.py' if a.mode=='core' else 'workflows/reproduce_historical.py','--output',str(out)]]
 for cmd in cmds:
  r=subprocess.run([sys.executable,*cmd],cwd=ROOT,env=env)
  if r.returncode:raise SystemExit(r.returncode)
if __name__=='__main__':main()
