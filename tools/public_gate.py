#!/usr/bin/env python3
"""Public package identity, links, size, and privacy gate; no network or scientific inference."""
from pathlib import Path
import csv,gzip,hashlib,json,re,zipfile
ROOT=Path(__file__).resolve().parents[1]
def main():
 issues=[];checked=0;maxbytes=0
 rows=list(csv.DictReader((ROOT/'provenance/RELEASE_MANIFEST.tsv').open(),delimiter='\t'))
 for r in rows:
  p=ROOT/r['path'];rel=r['path'];maxbytes=max(maxbytes,p.stat().st_size);checked+=1
  if p.stat().st_size>=100000000:issues.append('Oversize: '+rel)
  if any(x in p.parts for x in ['__pycache__','.env','.DS_Store']):issues.append('Private artifact: '+rel)
  chunks=[]
  if p.suffix in {'.md','.json','.tsv','.csv','.py','.txt','.svg','.yml','.yaml','.cff','.template'} or p.name in {'Makefile','.gitignore','.gitattributes'}:chunks=[p.read_bytes()]
  elif p.suffix in {'.pptx','.docx','.xlsx'}:
   with zipfile.ZipFile(p) as z:chunks=[z.read(n) for n in z.namelist() if n.endswith(('.xml','.rels'))]
  elif p.suffix=='.gz':
   with gzip.open(p,'rb') as f:chunks=[f.read()]
  forbidden=[rb'/' + rb'Users/',rb'/' + rb'private/var/folders/',b'jiang' + b'boyan',rb'-----BEGIN '+rb'(?:RSA |EC |OPENSSH )?PRIVATE KEY-----',rb'ghp_'+rb'[A-Za-z0-9]{36}',rb'sk-proj-'+rb'[A-Za-z0-9_-]{30,}']
  # Public GitHub account/URLs are intentional public metadata, not the local username.
  for text in chunks:
   text=text.replace(b'jiangboyan0129',b'PUBLIC_GITHUB_OWNER')
   if any(re.search(pat,text) for pat in forbidden):issues.append('Private pattern: '+rel)
 for p in [ROOT/'README.md',* (ROOT/'docs').glob('*.md')]:
  for target in re.findall(r'!?\[[^\]]*\]\(([^)]+)\)',p.read_text()):
   if target.startswith(('https://','http://','#','mailto:')):continue
   q=(p.parent/target.split('#')[0]).resolve()
   if not q.is_relative_to(ROOT) or not q.exists():issues.append('Broken relative link: '+str(p.relative_to(ROOT))+' -> '+target)
 public_paths={r['path'] for r in rows}
 for p in [ROOT/'README.md',*(ROOT/'docs').glob('*.md')]:
  for target in re.findall(r'!?\[[^\]]*\]\(([^)]+)\)',p.read_text()):
   if target.startswith(('https://','http://','#','mailto:')):continue
   q=(p.parent/target.split('#')[0]).absolute()
   import os
   rel=os.path.relpath(os.path.normpath(q),ROOT)
   if (ROOT/rel).is_file() and rel not in public_paths:issues.append('Link case mismatch: '+rel)
 facts=json.loads((ROOT/'config/portfolio_facts.json').read_text())
 grid=ROOT/'results/canonical/support_views/decision_grid.tsv'
 if hashlib.sha256(grid.read_bytes()).hexdigest()!=facts['source_sha256']:issues.append('Canonical scientific result changed')
 if issues:raise SystemExit('\n'.join(issues))
 print(json.dumps({'status':'PUBLIC_PACKAGE_GATE_PASS','files':checked,'max_file_bytes':maxbytes,'scientific_result_sha256_unchanged':True}))
if __name__=='__main__':main()
