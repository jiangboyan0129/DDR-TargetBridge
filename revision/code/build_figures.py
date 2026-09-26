"""Render disclosures from unchanged result snapshots. No effect fitting or selection."""
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

VIEWS=['S0_old_genes_old_transcripts','S1_old_genes_T0_transcripts','S2_T0_genes_T0_transcripts']

def save(fig,out,name):
    fig.savefig(out/(name+'.png'),dpi=190,bbox_inches='tight')
    fig.savefig(out/(name+'.svg'),bbox_inches='tight')
    plt.close(fig)

def build(root):
    root=Path(root);out=root/'figures';out.mkdir(exist_ok=True)
    g=pd.read_csv(root/'data/terminal/decision_grid.tsv',sep='\t')
    fig,ax=plt.subplots(figsize=(9.2,4.9))
    for mode,label,ls,marker in [('zero_only_0.5','zero-only 0.5','-','o'),('count_plus_1','count + 1','--','s')]:
        z=g[g['transform'].eq(mode)].set_index('support').loc[VIEWS]
        for arm,aname in [('M','M: mitochondrial translation'),('C','E: eukaryotic translation elongation')]:
            ax.plot(range(3),z[arm+'_theta_KO_minus_WT'],linestyle=ls,marker=marker,linewidth=1.8,label=aname+' | '+label)
    ax.set_xticks(range(3),['S0\nOld genes / old units','S1\nOld genes / T0 units','S2\nT0 genes / T0 units'])
    ax.set_ylabel('Component (KO drug − vehicle) − (WT drug − vehicle)')
    ax.set_ylim(-0.05,3.15);ax.set_xlim(-.12,2.13);ax.axhline(0,linestyle=':',linewidth=.8)
    ax.set_title('The comparator changes; the mitochondrial component is nearly unchanged',fontsize=12)
    ax.legend(fontsize=8,loc='upper left');fig.tight_layout()
    save(fig,out,'F1_components')
    z=pd.read_csv(root/'results/revision/retained_added_gene_values.tsv',sep='\t')
    fig,ax=plt.subplots(figsize=(9.2,4.9))
    groups=[('M','retained_T0_transcripts'),('M','added_T0_genes'),('C','retained_T0_transcripts'),('C','added_T0_genes')]
    for mode,delta,mark,label in [('zero_only_0.5',-.10,'o','Zeros only → 0.5'),('count_plus_1',.10,'x','Count + 1')]:
        xs=[];ys=[];means=[]
        for i,(arm,group) in enumerate(groups):
            f=z[z['transform'].eq(mode)&z.pathway.eq(arm)&z.population.eq(group)].sort_values('gene')
            # Deterministic spacing for legibility, not data-based selection or uncertainty.
            xs.extend(i+delta+np.linspace(-.07,.07,len(f)));ys.extend(f.theta_KO_minus_WT)
            means.append(float(f.theta_KO_minus_WT.mean()))
        ax.scatter(xs,ys,s=18,marker=mark,alpha=.55,label=label)
        ax.scatter(np.arange(4)+delta,means,s=330,marker='_')
    ax.set_xticks(range(4),['M retained\n89 genes','M added\n5 genes','E retained\n23 genes','E added\n68 genes'])
    ax.axhline(0,linestyle=':',linewidth=.8);ax.set_ylabel('Gene-level conditional contrast in S2')
    ax.set_title('Added comparator members have a different observed distribution',fontsize=12)
    ax.legend(fontsize=9);fig.tight_layout();save(fig,out,'F2_retained_added')
    samples=pd.read_csv(root/'data/terminal/pathway_sample_values.tsv',sep='\t')
    group_keys=[('parent','T0'),('parent','vehicle'),('parent','DNAPKi'),('PRDX1KO','T0'),('PRDX1KO','vehicle'),('PRDX1KO','DNAPKi')]
    for arm,title in [('M','M: mitochondrial translation'),('C','E: eukaryotic translation elongation')]:
        fig,ax=plt.subplots(figsize=(9.2,4.1))
        for v,offset,marker in zip(VIEWS,[-.19,0,.19],['o','s','^']):
            f=samples[samples['transform'].eq('zero_only_0.5')&samples.support.eq(v)]
            xs=[];ys=[]
            for j,(bg,condition) in enumerate(group_keys):
                sel=f[f.sample_id.str.startswith('A549_'+bg+'__')&f.sample_id.str.contains('__'+condition+'__',regex=False)].sort_values('sample_id')
                xs.extend(j+offset+np.linspace(-.038,.038,len(sel)));ys.extend(sel[arm])
            ax.scatter(xs,ys,s=27,marker=marker,label=v[:2])
        ax.set_xticks(range(6),['WT\nT0','WT\nvehicle','WT\ndrug','KO\nT0','KO\nvehicle','KO\ndrug'])
        ax.set_ylabel('NTC-centred mean log2 count')
        ax.set_title(title+' — individual sample records',fontsize=12)
        ax.legend(fontsize=9,ncol=3);fig.tight_layout();save(fig,out,'F3_'+arm+'_samples')
    f=pd.read_csv(root/'data/terminal/count_floor.tsv',sep='\t')
    f=f[f['transform'].eq('zero_only_0.5')&f.support.eq(VIEWS[2])&f.pathway.eq('C')]
    vals=[]
    for bg,c in [('parent','vehicle'),('parent','DNAPKi'),('PRDX1KO','vehicle'),('PRDX1KO','DNAPKi')]:
        vals.append(f[f.background.eq(bg)&f.condition.eq(c)].iloc[0])
    fig,ax=plt.subplots(figsize=(8.8,4.5));x=np.arange(4)
    b1=ax.bar(x-.17,[r.zero_cells for r in vals],.34,label='Count = 0')
    b2=ax.bar(x+.17,[r.below40_cells for r in vals],.34,label='Count < 40 (includes zeros)')
    for bars in [b1,b2]:
        for b in bars:ax.annotate(str(int(b.get_height())),(b.get_x()+b.get_width()/2,b.get_height()),xytext=(0,4),textcoords='offset points',ha='center',fontsize=9)
    ax.set_xticks(x,['WT vehicle','WT drug','KO vehicle','KO drug']);ax.set_ylim(0,240)
    ax.set_ylabel('Count entries out of 291 per endpoint group')
    ax.set_title('Expanded comparator: count floors in all four groups',fontsize=12,pad=40)
    ax.legend(fontsize=8,loc='lower left',bbox_to_anchor=(0,1.01),ncol=2);fig.tight_layout();save(fig,out,'F4_comparator_count_floor')
    c=pd.read_csv(root/'results/revision/R2_member_locations_reranked.tsv',sep='\t')
    for cond,label in [('PARPi','Olaparib'),('WEE1i','AZD1775')]:
        z=c[c.condition.eq(cond)];fig,ax=plt.subplots(figsize=(7.5,6.2));j=0;labs=[]
        for mod in ['HAP1.L2.32','HAP1.L2.139']:
            sub=z[z.module_id.eq(mod)].sort_values('gene');yi=np.arange(j,j+len(sub))
            ax.scatter(sub.q_minus_half,yi,s=30,label=mod)
            labs.extend(sub.gene);j+=len(sub)
        ax.set_yticks(range(j),labs);ax.invert_yaxis();ax.axvline(0,linestyle=':',linewidth=.8)
        ax.set_xlabel('Within-background sensitivity percentile − 0.5');ax.set_xlim(-.52,.52)
        ax.set_title(label+': all fixed module members in R2',fontsize=12,pad=38);ax.legend(fontsize=9,loc='lower left',bbox_to_anchor=(0,1.01),ncol=2)
        fig.tight_layout();save(fig,out,'E1_'+cond+'_members')
    print('Saved 7 figure pairs (PNG + SVG); all curves use unchanged source values or disclosed arithmetic.')

if __name__=='__main__':build(Path(__file__).resolve().parents[1])
