#!/usr/bin/env python3
"""Optional local LibreOffice export. No download, installation or scientific calculation."""
from pathlib import Path
import argparse,shutil,subprocess,tempfile

def main():
 p=argparse.ArgumentParser();p.add_argument('--input',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 src=a.input.resolve();out=a.output.resolve()
 if src.suffix.lower() not in {'.docx','.pptx'} or not src.is_file():raise SystemExit('Input must be an existing DOCX or PPTX.')
 if out.exists() or out.suffix.lower()!='.pdf':raise SystemExit('Output must be a NEW .pdf path.')
 exe=shutil.which('libreoffice') or shutil.which('soffice')
 if not exe:raise SystemExit('LibreOffice is not installed; the release already includes readable PDFs.')
 with tempfile.TemporaryDirectory(prefix='ddr-pdf-') as tmp:
  tmp=Path(tmp);profile=(tmp/'profile').as_uri();dest=tmp/'export';dest.mkdir()
  run=subprocess.run([exe,'-env:UserInstallation='+profile,'--headless','--convert-to','pdf','--outdir',str(dest),str(src)],capture_output=True,text=True,timeout=180)
  pdf=dest/(src.stem+'.pdf')
  if run.returncode or not pdf.is_file() or not pdf.read_bytes().startswith(b'%PDF-'):raise RuntimeError('PDF export failed: '+run.stderr)
  out.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(pdf,out)
 print(out)
if __name__=='__main__':main()
