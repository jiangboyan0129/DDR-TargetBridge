"""Regression cases for public packaging, not biological hypothesis tests."""
from __future__ import annotations
import hashlib
import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from public_inventory import candidates

def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module
core=load('hardening_public_core',ROOT/'workflows/reproduce_public_core.py')
public=load('hardening_public_gate',ROOT/'tools/public_gate.py')

class InputContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.frame=pd.read_csv(ROOT/'results/extended/support_views/member_sample_values.tsv.gz',sep='\t')
        cls.members=pd.read_csv(ROOT/'results/canonical/support_views/pathway_membership.tsv',sep='\t')
        cls.samples=pd.read_csv(ROOT/'results/canonical/support_views/pathway_sample_values.tsv',sep='\t')
    def test_actual_inputs_hash(self):core.verify_inputs(ROOT)
    def test_actual_full_membership(self):core.validate_fixed_membership(self.frame,self.members,self.samples)
    def test_renamed_gene_rejected(self):
        f=self.frame.copy();f.loc[f.gene.eq(f.gene.iloc[0]),'gene']='SYNTHETIC_OTHER'
        with self.assertRaisesRegex(ValueError,'gene identities'):
            core.validate_fixed_membership(f,self.members,self.samples)
    def test_missing_sample_identity_rejected(self):
        f=self.frame[self.frame.sample_id.ne(self.frame.sample_id.iloc[0])]
        with self.assertRaisesRegex(ValueError,'sample identities'):
            core.validate_fixed_membership(f,self.members,self.samples)
    def test_same_count_different_member_per_sample_rejected(self):
        f=self.frame.copy();f.loc[f.index[0],'gene']='SYNTHETIC_OTHER'
        with self.assertRaisesRegex(ValueError,'membership changes'):
            core.calculate(f)
    def test_null_gene_rejected(self):
        f=self.frame.iloc[:10].copy();f.loc[f.index[0],'gene']=None
        with self.assertRaisesRegex(ValueError,'missing identity'):core.calculate(f)
    def test_blank_gene_rejected(self):
        f=self.frame.iloc[:10].copy();f.loc[f.index[0],'gene']=' '
        with self.assertRaisesRegex(ValueError,'Blank identity'):core.calculate(f)
    def test_modified_fixed_input_fails_before_calculation(self):
        with tempfile.TemporaryDirectory() as d:
            r=Path(d);(r/'config').mkdir();(r/'value.txt').write_text('wrong')
            (r/'config/public_core_inputs.json').write_text(json.dumps({'files':[{'path':'value.txt','bytes':5,'sha256':hashlib.sha256(b'right').hexdigest()}]}))
            with self.assertRaisesRegex(ValueError,'Fixed input changed'):core.verify_inputs(r)
    def test_empty_frame_rejected(self):
        with self.assertRaises(ValueError):core.calculate(self.frame.iloc[:0])

class PackagingTests(unittest.TestCase):
    def test_plain_tree_lists_new_file(self):
        with tempfile.TemporaryDirectory() as d:
            r=Path(d);(r/'new_note.txt').write_text('test')
            self.assertIn('new_note.txt',candidates(r)[0])
    def test_tracked_ignored_file_is_not_hidden(self):
        if not shutil.which('git'):self.skipTest('git not installed')
        with tempfile.TemporaryDirectory() as d:
            r=Path(d);subprocess.run(['git','init','-q'],cwd=r,check=True)
            (r/'.gitignore').write_text('*.txt\n');(r/'new_note.txt').write_text('test')
            subprocess.run(['git','add','-f','new_note.txt'],cwd=r,check=True)
            self.assertIn('new_note.txt',candidates(r)[0])
    def test_dotenv_not_hidden_in_extracted_release(self):
        with tempfile.TemporaryDirectory() as d:
            r=Path(d);(r/'.env').write_text('synthetic')
            self.assertIn('.env',candidates(r)[0])
    def test_build_directory_excluded_in_plain_tree(self):
        with tempfile.TemporaryDirectory() as d:
            r=Path(d);(r/'.build').mkdir();(r/'.build/tmp.txt').write_text('local')
            self.assertNotIn('.build/tmp.txt',candidates(r)[0])
    def test_pattern_detects_synthetic_private_path(self):
        import re
        text=('/'+'Users/synthetic_user/local').encode()
        self.assertTrue(any(re.search(p,text) for p in public.PATTERNS))
    def test_public_account_is_not_a_secret(self):
        import re
        text=b'https://github.com/jiangboyan0129/DDR-TargetBridge'
        self.assertFalse(any(re.search(p,text) for p in public.PATTERNS))
    def test_make_default_does_not_pass_empty_output(self):
        if not shutil.which('make'):self.skipTest('make not installed')
        p=subprocess.run(['make','-n','core'],cwd=ROOT,capture_output=True,text=True,check=True)
        self.assertNotIn('--output ""',p.stdout)
    def test_ci_never_regenerates_manifest(self):
        self.assertNotIn('refresh_release_manifest',(ROOT/'.github/workflows/ci.yml').read_text())


class DeliveredPresentationTests(unittest.TestCase):
    def test_all_svg_labels_remain_editable(self):
        for p in (ROOT/'figures').glob('*.svg'):
            self.assertIn('<text',p.read_text(),p.name)
    def test_builder_does_not_call_public_core_count_reconstruction(self):
        text=(ROOT/'tools/build_documents.py').read_text()
        self.assertNotIn('Reproduce counts: python tools/run.py core',text)
        self.assertIn('Public core: python tools/run.py core',text)
    def test_claim_ledger_public_scope(self):
        ledger=json.loads((ROOT/'docs/SCIENTIFIC_CLAIM_LEDGER.json').read_text())
        claim=next(x for x in ledger if x['id']=='CL09')
        self.assertIn('Public derived observations',claim['claim'])
    def test_single_report_pdf_name(self):
        self.assertTrue((ROOT/'reports/DDR_TargetBridge_Case_Study.pdf').is_file())
        self.assertFalse((ROOT/'reports/CASE_STUDY.pdf').exists())
    def test_editable_deck_contains_nine_slides(self):
        import zipfile,re
        with zipfile.ZipFile(ROOT/'presentation/DDR_TargetBridge.pptx') as z:
            files=[n for n in z.namelist() if re.fullmatch(r'ppt/slides/slide\d+\.xml',n)]
            self.assertEqual(len(files),9)
            text=''.join(z.read(n).decode() for n in files)
            self.assertNotIn('Reproduce counts:',text)
            self.assertIn('Public core:',text)
    def test_ci_actions_are_pinned(self):
        import re
        text=(ROOT/'.github/workflows/ci.yml').read_text()
        refs=re.findall(r'uses:\s*(\S+)',text)
        self.assertEqual(len(refs),2)
        self.assertTrue(all(re.search(r'@[0-9a-f]{40}$',v) for v in refs))
        self.assertIn('ubuntu-24.04',text)

class GateMutationTests(unittest.TestCase):
    def seed(self,root):
        import csv
        (root/'provenance').mkdir();(root/'config').mkdir()
        d=root/'results/canonical/support_views';d.mkdir(parents=True)
        (d/'decision_grid.tsv').write_text('synthetic\n')
        digest=hashlib.sha256((d/'decision_grid.tsv').read_bytes()).hexdigest()
        (root/'config/portfolio_facts.json').write_text(json.dumps({'source_sha256':digest}))
        (root/'README.md').write_text('# Synthetic fixture\n')
        self.manifest(root)
    def manifest(self,root):
        import csv
        rows=[]
        for p in root.rglob('*'):
            if p.is_file() and p.name!='RELEASE_MANIFEST.tsv':
                rows.append({'path':str(p.relative_to(root)),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
        with (root/'provenance/RELEASE_MANIFEST.tsv').open('w') as h:
            w=csv.DictWriter(h,fieldnames=['path','bytes','sha256'],delimiter='\t');w.writeheader();w.writerows(rows)
    def test_unmanifested_private_addition_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            r=Path(d);self.seed(r)
            (r/'new_note.txt').write_text('/'+'Users/synthetic_user/example')
            result=public.inspect(r)
            self.assertEqual(result['status'],'PUBLIC_PACKAGE_GATE_FAIL')
            self.assertTrue(any('Unmanifested' in x for x in result['issues']))
            self.assertTrue(any('Private pattern' in x for x in result['issues']))
    def test_link_checks_include_reports(self):
        with tempfile.TemporaryDirectory() as d:
            r=Path(d);self.seed(r);(r/'reports').mkdir();(r/'reports/report.md').write_text('[missing](missing.pdf)')
            self.manifest(r)
            self.assertTrue(any('Broken relative link' in x for x in public.inspect(r)['issues']))
    def test_clean_fixture_passes(self):
        with tempfile.TemporaryDirectory() as d:
            r=Path(d);self.seed(r);self.assertEqual(public.inspect(r)['status'],'PUBLIC_PACKAGE_GATE_PASS')


if __name__=='__main__':unittest.main()
