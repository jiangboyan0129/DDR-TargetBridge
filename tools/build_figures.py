#!/usr/bin/env python3
"""Replot accepted tables only. No refitting, new selection, or biological inference."""
from pathlib import Path
import argparse,json,hashlib
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
R=Path(__file__).resolve().parents[1]
def build(out):
 if out.exists():raise FileExistsError('Use a new figure output directory')
 out.mkdir(parents=True)
 grid=pd.read_csv(R/'results/canonical/support_views/decision_grid.tsv',sep='\t')
 g=grid[grid['transform'].eq('zero_only_0.5')]
 figs=[]
 def save(fig,name):
  fig.savefig(out/(name+'.png'),dpi=180,bbox_inches='tight')
  fig.savefig(out/(name+'.svg'),bbox_inches='tight')
  plt.close(fig);figs.append(name)
 # Plain labels before code names; three components on one unchanged scale.
 fig,ax=plt.subplots(figsize=(9.4,5.6))
 for col,label,mark in [('M_theta_KO_minus_WT','M: mitochondrial translation','o'),('C_theta_KO_minus_WT','E: translation-elongation comparator','s'),('theta_KO_minus_WT','M − E: pathway balance','D')]:
  vals=g[col].to_numpy();ax.plot(range(3),vals,marker=mark,linewidth=2,label=label)
  for x,y in enumerate(vals):
   offset = ((29, -2) if x==0 else ((0, 9) if x==2 else (0, -18))) if col=='theta_KO_minus_WT' else (0, 9)
   ax.annotate(f'{y:+.3f}',(x,y),xytext=offset,textcoords='offset points',ha='center',fontsize=10)
 ax.axhline(0,linestyle=':',linewidth=1)
 ax.set_xticks(range(3),['S0: original support\nM 89 / E 23','S1: same genes,\nmore targeting units\nM 89 / E 23','S2: T0-qualified support\nM 94 / E 91'])
 ax.set_ylabel('Conditional drug-response contrast (log-count description)')
 ax.set_title('The comparator changes; the mitochondrial component is nearly stable',pad=58,fontsize=13)
 ax.legend(loc='lower left',bbox_to_anchor=(0,1.01),fontsize=9)
 ax.set_xlim(-.2,2.2);ax.set_ylim(-2.15,3.35)
 fig.text(.10,.015,'Zero-only replacement: zeros → 0.5; positive counts unchanged. No biological confidence intervals.\nDifferent support views summarize different populations. Count+1 gives the same sign reversal (all six values in the report).',fontsize=8.5)
 fig.tight_layout(rect=(0,.11,1,1));save(fig,'01_components')
 genes=pd.read_csv(R/'revision/results/revision/retained_added_gene_values.tsv',sep='\t')
 fig,ax=plt.subplots(figsize=(9.2,4.7));labels=[]
 for x,(tr,pop,n) in enumerate([('zero_only_0.5','retained_T0_transcripts',23),('zero_only_0.5','added_T0_genes',68),('count_plus_1','retained_T0_transcripts',23),('count_plus_1','added_T0_genes',68)]):
  f=genes[genes['transform'].eq(tr)&genes.pathway.eq('C')&genes.population.eq(pop)].sort_values('gene');ys=f.theta_KO_minus_WT.to_numpy();assert len(ys)==n
  jit=np.array([int(hashlib.sha256(v.encode()).hexdigest()[:8],16)/0xffffffff-.5 for v in f.gene])*.34
  ax.scatter(x+jit,ys,s=17,alpha=.65)
  ax.plot([x-.20,x+.20],[ys.mean()]*2,linewidth=2)
  labels.append(('Retained' if n==23 else 'Added')+f' E genes\nn={n}\n'+('Zero → 0.5' if tr.startswith('zero') else 'Count+1'))
 ax.axhline(0,linestyle=':',linewidth=1);ax.set_xticks(range(4),labels)
 ax.set_ylabel('Gene-level conditional log-count contrast')
 ax.set_title('The added comparator members have a different observed distribution',fontsize=13,pad=14)
 fig.text(.10,.015,'All E genes under S2 targeting-unit support are shown. Short lines are means, not uncertainty intervals.\nGroups follow the frozen eligibility records. Genes are not independent biological replicates.',fontsize=8.5)
 fig.tight_layout(rect=(0,.12,1,1));save(fig,'02_comparator_members')
 floors=pd.read_csv(R/'results/canonical/support_views/count_floor.tsv',sep='\t')
 f=floors[floors['transform'].eq('zero_only_0.5')&floors.support.eq('S2_T0_genes_T0_transcripts')&floors.pathway.eq('C')]
 records=[f[f.background.eq(b)&f.condition.eq(c)].iloc[0] for b,c in [('parent','vehicle'),('parent','DNAPKi'),('PRDX1KO','vehicle'),('PRDX1KO','DNAPKi')]]
 z=np.array([x.zero_cells for x in records]);low=np.array([x.below40_cells-x.zero_cells for x in records]);high=np.array([x.cells-x.below40_cells for x in records])
 fig,ax=plt.subplots(figsize=(8.9,4.8));x=np.arange(4)
 ax.bar(x,z,label='Zero');ax.bar(x,low,bottom=z,label='1–39');ax.bar(x,high,bottom=z+low,label='≥40')
 for i,rr in enumerate(records):ax.text(i,rr.cells+4,f'{int(rr.zero_cells)} zero\n{int(rr.below40_cells)} <40',ha='center',fontsize=9)
 ax.set_xticks(x,['WT vehicle','WT AZD7648','KO vehicle','KO AZD7648']);ax.set_ylim(0,360)
 ax.set_ylabel('Construct × sample count entries');ax.set_title('Broader comparator coverage also reaches the count floor',fontsize=13,pad=35)
 ax.legend(ncol=3,loc='lower left',bbox_to_anchor=(0,1.01),fontsize=9)
 fig.text(.10,.015,'Expanded E set: 91 genes, 97 constructs, three endpoint records per group. Each bar totals 291 entries.\nCategories are disjoint; the “<40” label includes zeros. Counts are not cell numbers or independent experiments.',fontsize=8.5)
 fig.tight_layout(rect=(0,.12,1,1));save(fig,'03_count_floor')
 s=pd.read_csv(R/'results/canonical/support_views/pathway_sample_values.tsv',sep='\t')
 samples=s[s['transform'].eq('zero_only_0.5')].copy()
 gr=[('parent','T0'),('parent','vehicle'),('parent','DNAPKi'),('PRDX1KO','T0'),('PRDX1KO','vehicle'),('PRDX1KO','DNAPKi')]
 for arm,name in [('M','M: mitochondrial translation'),('C','E: translation-elongation comparator')]:
  fig,ax=plt.subplots(figsize=(9.5,4.9))
  for k,view in enumerate(g.support):
   f=samples[samples.support.eq(view)];xs=[];ys=[]
   for j,(b,c) in enumerate(gr):
    chunk=f[f.sample_id.str.contains('A549_'+b+'__',regex=False)&f.sample_id.str.contains('__'+c+'__',regex=False)].sort_values('sample_id')
    assert len(chunk)==(2 if c=='T0' else 3)
    for h,(_,rr) in enumerate(chunk.iterrows()):xs.append(j+(k-1)*.20+(h-(len(chunk)-1)/2)*.045);ys.append(rr[arm])
   ax.scatter(xs,ys,s=30,marker=['o','s','^'][k],label=['S0','S1','S2'][k])
  ax.axhline(0,linestyle=':',linewidth=1);ax.set_xticks(range(6),['WT T0','WT vehicle','WT drug','KO T0','KO vehicle','KO drug']);ax.set_ylabel('NTC-centred mean log-count description');ax.set_title(name+' — every real sample record',fontsize=13,pad=12);ax.legend(ncol=3)
  fig.text(.10,.015,'Each support view reuses the same 16 sample identities: two real T0 per background and three records per endpoint.\nPoints are culture records, not independent clones. Zero-only transformation; all count+1 sample values remain in the tables.',fontsize=8.5)
  fig.tight_layout(rect=(0,.12,1,1));save(fig,'04_samples_'+arm)
 mapping={
 '01_components':['results/canonical/support_views/decision_grid.tsv'],
 '02_comparator_members':['revision/results/revision/retained_added_gene_values.tsv'],
 '03_count_floor':['results/canonical/support_views/count_floor.tsv'],
 '04_samples_M':['results/canonical/support_views/pathway_sample_values.tsv'],
 '04_samples_C':['results/canonical/support_views/pathway_sample_values.tsv']}
 (out/'FIGURE_SOURCES.json').write_text(json.dumps(mapping,indent=2)+'\n')
 return figs
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();print(build(a.output.resolve()))
