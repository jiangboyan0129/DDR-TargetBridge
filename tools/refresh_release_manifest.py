#!/usr/bin/env python3
"""Deliberately refresh packaging hashes after reviewing a diff.

Never call this from verify or CI. It cannot modify the independent scientific
input lock. A changed frozen input remains an error even after re-indexing files.
"""
from __future__ import annotations
import argparse,csv,hashlib,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from public_inventory import candidates,MANIFEST

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--acknowledge-reviewed-diff',action='store_true')
    args=p.parse_args()
    if not args.acknowledge_reviewed_diff:
        raise SystemExit('Review the diff first; pass --acknowledge-reviewed-diff explicitly.')
    files,scope=candidates(ROOT)
    rows=[]
    for name in files:
        if name==MANIFEST:continue
        path=ROOT/name
        if path.is_symlink() or not path.is_file() or not path.resolve().is_relative_to(ROOT):
            raise SystemExit('Unsafe/missing payload: '+name)
        rows.append({'path':name,'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
    with (ROOT/MANIFEST).open('w',newline='',encoding='utf-8') as h:
        w=csv.DictWriter(h,fieldnames=['path','bytes','sha256'],delimiter='\t',lineterminator='\n');w.writeheader();w.writerows(rows)
    print(f'Indexed {len(rows)} files from {scope}; scientific input lock unchanged.')
if __name__=='__main__':main()
