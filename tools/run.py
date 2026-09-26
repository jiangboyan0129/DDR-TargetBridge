#!/usr/bin/env python3
"""Public verification and explicitly scoped reproduction; never downloads data."""
from __future__ import annotations
import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PROTECTED=['data','data_metadata','src','workflows','tests','results','revision','config',
           'reports','figures','portfolio','presentation','provenance','docs','environment',
           'tools','public_tests']


def external_missing() -> list[dict]:
    sources=json.loads((ROOT/'data_metadata/external_inputs.json').read_text())
    return [source for source in sources if not (ROOT/source['public_path']).is_file()]


def main() -> None:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode',choices=['verify','core','historical'])
    parser.add_argument('--output',type=Path)
    args=parser.parse_args()
    if sys.flags.optimize:
        raise SystemExit('Do not use python -O: preserved checks use assertions.')
    env=os.environ.copy()
    env.update(PYTHONDONTWRITEBYTECODE='1',OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',
               PYTHONPATH=str(ROOT/'workflows/vendor_prkdc'))
    if args.mode=='verify':
        commands=[['tools/verify_release.py'],['tools/public_gate.py']]
        commands += [['-m','unittest','discover','-s',folder,'-v'] for folder in
                     ['tests','revision/tests','workflows/vendor_prkdc/tests','public_tests']]
    else:
        out=(args.output or Path('.build')/(args.mode+'-1')).resolve()
        for folder in PROTECTED:
            directory=(ROOT/folder).resolve()
            if out==directory or out.is_relative_to(directory):
                raise SystemExit('Refusing output inside preserved content')
        if out==ROOT or out.exists():
            raise SystemExit('Choose a fresh output directory')
        missing=external_missing() if args.mode=='historical' else []
        if missing:
            print(json.dumps({'status':'EXTERNAL_INPUTS_REQUIRED',
                              'missing':[item['public_path'] for item in missing],
                              'instructions':'docs/retrieval.md','automatic_download':False}))
            raise SystemExit(3)
        script='workflows/reproduce_public_core.py' if args.mode=='core' else 'workflows/reproduce_historical.py'
        commands=[[script,'--output',str(out)]]
    for command in commands:
        completed=subprocess.run([sys.executable,*command],cwd=ROOT,env=env)
        if completed.returncode:
            raise SystemExit(completed.returncode)


if __name__=='__main__':main()
