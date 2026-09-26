import importlib.util,json,sys,tempfile,unittest
from pathlib import Path
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from targetbridge.vendor.final_execute_decision import transformed,group_gene_values,contrasts,group_indices
from targetbridge.paths import contained,fresh_output
spec=importlib.util.spec_from_file_location('reproduce',ROOT/'workflows/reproduce_final.py');reproduce=importlib.util.module_from_spec(spec);spec.loader.exec_module(reproduce)
class FrozenMathTests(unittest.TestCase):
    def test_zero_only(self):np.testing.assert_equal(transformed([0,1,2,4],'zero_only_0.5'),[-1,0,1,2])
    def test_plus_one(self):np.testing.assert_allclose(transformed([0,1,3,7],'count_plus_1'),[0,1,2,3])
    def test_positive_unchanged(self):np.testing.assert_equal(transformed([2,4,8],'zero_only_0.5'),[1,2,3])
    def test_invalid_counts(self):
        for x in [[-1],[.5],[np.nan],[np.inf]]:
            with self.assertRaises(ValueError):transformed(x,'zero_only_0.5')
    def test_unknown_transform(self):
        with self.assertRaises(ValueError):transformed([1],'other')
    def test_equal_construct_then_transcript_weights(self):
        df=pd.DataFrame({'target':['G','G','G','H'],'transcript':['T1','T1','T2','T1'],'s':[0,2,9,4]})
        units,genes=group_gene_values(df,['s']);self.assertEqual(genes.loc['G','s'],5);self.assertEqual(genes.loc['H','s'],4)
    def test_equal_gene_not_construct_weighting(self):
        df=pd.DataFrame({'target':['G','G','H'],'transcript':['T1','T2','T1'],'s':[0,4,10]})
        _,genes=group_gene_values(df,['s']);self.assertEqual(genes.s.mean(),6)
    def test_missing_transcript_identity_preserved(self):
        df=pd.DataFrame({'target':['G','G'],'transcript':['T1',None],'s':[2.,6.]})
        units,genes=group_gene_values(df,['s']);self.assertEqual(len(units),2);self.assertEqual(genes.loc['G','s'],4)
    def test_missing_not_converted_to_zero(self):
        df=pd.DataFrame({'target':['G','H'],'transcript':['T1','T1'],'s':[np.nan,6.]})
        units,genes=group_gene_values(df,['s']);self.assertTrue(np.isnan(genes.loc['G','s']))
    def test_center_cancellation(self):
        x=np.array([[1,2,3],[4,5,6.]]);y=np.array([[7,8,9.]]);off=np.array([42,-5,.5]);np.testing.assert_allclose((x+off).mean(0)-(y+off).mean(0),x.mean(0)-y.mean(0))
    def test_factorial_sign(self):
        ix={('parent','T0'):[0,1],('parent','vehicle'):[2,3,4],('parent','DNAPKi'):[5,6,7],('PRDX1KO','T0'):[8,9],('PRDX1KO','vehicle'):[10,11,12],('PRDX1KO','DNAPKi'):[13,14,15]}
        a=np.array([0,0,1,1,1,3,3,3,0,0,4,4,4,9,9,9]);r=contrasts(a,ix);self.assertEqual(r['beta_WT'],2);self.assertEqual(r['beta_KO'],5);self.assertEqual(r['theta_KO_minus_WT'],3)
    def test_invalid_sample_groups(self):
        with self.assertRaises(ValueError):group_indices(['invented'])
    def test_actual_sample_groups(self):
        d=pd.read_csv(ROOT/'results/canonical/support_views/pathway_sample_values.tsv',sep='\t');ix=group_indices(d.sample_id.drop_duplicates().tolist());self.assertEqual(sum(map(len,ix.values())),16)
    def test_six_support_grid(self):
        d=pd.read_csv(ROOT/'results/canonical/support_views/decision_grid.tsv',sep='\t');self.assertEqual(len(d),6);self.assertEqual(d[['transform','support']].duplicated().sum(),0)
    def test_two_fixed_transforms_in_protocol(self):
        d=json.loads((ROOT/'config/final_support_decision.json').read_text());self.assertIn('zero by 0.5',d['primary_continuity_transform']);self.assertIn('count+1',d['named_sensitivity'])
class PathAndParityTests(unittest.TestCase):
    def test_spaces_and_chinese(self):
        with tempfile.TemporaryDirectory(prefix='DDR 空 格 ') as tmp:
            root=Path(tmp);p=root/'数 据.tsv';p.write_text('x');self.assertEqual(contained(root,p),p.resolve())
    def test_symlinked_root_and_child_allowed(self):
        with tempfile.TemporaryDirectory() as tmp:
            base=Path(tmp);root=base/'actual';root.mkdir();p=root/'x';p.write_text('x');alias=base/'alias';alias.symlink_to(root,target_is_directory=True);self.assertEqual(contained(alias,alias/'x'),p.resolve())
    def test_symlink_escape_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            base=Path(tmp);root=base/'actual';root.mkdir();outside=base/'outside';outside.write_text('x');(root/'link').symlink_to(outside)
            with self.assertRaises(ValueError):contained(root,root/'link')
    def test_prefix_collision_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            base=Path(tmp)
            with self.assertRaises(ValueError):contained(base/'a',base/'ab'/'x')
    def test_existing_output_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):fresh_output(ROOT,tmp)
    def test_canonical_output_rejected(self):
        with self.assertRaises(ValueError):fresh_output(ROOT,ROOT/'results'/'new')
    def test_symlink_canonical_output_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            alias=Path(tmp)/'linked_results';alias.symlink_to(ROOT/'results',target_is_directory=True)
            with self.assertRaises(ValueError):fresh_output(ROOT,alias/'new')
    def test_parity_accepts_existing_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            a=Path(tmp)/'a.tsv';b=Path(tmp)/'b.tsv';a.write_text('gene\tx\nG\tNA\nH\t2\n');b.write_bytes(a.read_bytes());self.assertEqual(reproduce.compare_table(a,b)['rows'],2)
    def test_parity_rejects_missing_zero_substitution(self):
        with tempfile.TemporaryDirectory() as tmp:
            a=Path(tmp)/'a.tsv';b=Path(tmp)/'b.tsv';a.write_text('gene\tx\nG\tNA\nH\t2\n');b.write_text('gene\tx\nG\t0\nH\t2\n')
            with self.assertRaises(ValueError):reproduce.compare_table(a,b)
    def test_parity_rejects_identity_replacement(self):
        with tempfile.TemporaryDirectory() as tmp:
            a=Path(tmp)/'a.tsv';b=Path(tmp)/'b.tsv';a.write_text('gene\tx\nG\t2\n');b.write_text('gene\tx\nH\t2\n')
            with self.assertRaises(ValueError):reproduce.compare_table(a,b)
    def test_parity_rejects_numeric_change(self):
        with tempfile.TemporaryDirectory() as tmp:
            a=Path(tmp)/'a.tsv';b=Path(tmp)/'b.tsv';a.write_text('gene\tx\nG\t2\n');b.write_text('gene\tx\nG\t3\n')
            with self.assertRaises(ValueError):reproduce.compare_table(a,b)
    def test_independent_checker_reads_fresh_output(self):
        source=(ROOT/'workflows/reproduce_final.py').read_text();self.assertIn('(context / "results").symlink_to(calculated',source);self.assertIn('independent_checker_reads_new_output',source)
if __name__=='__main__':unittest.main()
