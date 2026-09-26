#!/usr/bin/env python3
"""Verify release content; file identity is not biological validation."""
from pathlib import Path
import csv,hashlib,json
ROOT=Path(__file__).resolve().parents[1]
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def main():
 manifest=ROOT/'provenance/RELEASE_MANIFEST.tsv'
 if not manifest.is_file():raise SystemExit('Release manifest missing.')
 rows=list(csv.DictReader(manifest.open(),delimiter='\t'))
 for r in rows:
  p=(ROOT/r['path']).resolve()
  if not p.is_relative_to(ROOT) or not p.is_file():raise ValueError(r['path'])
  if p.stat().st_size!=int(r['bytes']) or sha(p)!=r['sha256']:raise ValueError('Changed: '+r['path'])
 print(json.dumps({'status':'RELEASE_BYTES_MATCH','files':len(rows)}))
if __name__=='__main__':main()
