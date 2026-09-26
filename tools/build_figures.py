#!/usr/bin/env python3
"""Publication-style replot of the unchanged, released observations.

No new analysis, inferential intervals, outcome selection or source retrieval.
Text remains editable in SVG/PDF. All source tables are recorded alongside plots.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parents[1]
VIEWS=['S0_old_genes_old_transcripts','S1_old_genes_T0_transcripts','S2_T0_genes_T0_transcripts']


def build(out: Path) -> list[str]:
    if out.exists():
        raise FileExistsError('Use a fresh figure output directory')
    out.mkdir(parents=True)
    # No custom color palette: the Matplotlib default cycle is used consistently
    # within each plotted quantity. Shape and line style distinguish transforms.
    plt.rcParams.update({
        'font.family':'DejaVu Sans', 'font.size':10, 'axes.labelsize':10,
        'axes.titlesize':11, 'legend.fontsize':9,
        'axes.spines.top':False, 'axes.spines.right':False,
        'axes.linewidth':0.7, 'xtick.major.width':0.7,'ytick.major.width':0.7,
        'svg.fonttype':'none','pdf.fonttype':42,'ps.fonttype':42,
        'svg.hashsalt':'DDR-TargetBridge-v1.0.1',
        'savefig.dpi':220,
    })
    grid=pd.read_csv(ROOT/'results/canonical/support_views/decision_grid.tsv',sep='\t')
    paths={}
    def save(fig,name,sources):
        fig.tight_layout(pad=1.25)
        fig.savefig(out/(name+'.png'),bbox_inches='tight')
        fig.savefig(out/(name+'.svg'),bbox_inches='tight',metadata={'Date':None})
        fig.savefig(out/(name+'.pdf'),bbox_inches='tight',metadata={'CreationDate':None,'ModDate':None})
        plt.close(fig)
        paths[name]=sources
    def support_axis(ax):
        ax.set_xticks(range(3),['S0\n89 M / 23 E','S1\n89 M / 23 E','S2\n94 M / 91 E'])
        ax.set_xlim(-.15,2.15)
        ax.set_xlabel('Analysis support (not time)')

    fig,ax=plt.subplots(figsize=(6.5,4.0))
    for transform,style,fill,desc in [('zero_only_0.5','-','full','zero-only'),('count_plus_1','--','none','count + 1')]:
        ax.set_prop_cycle(None)
        block=grid[grid['transform'].eq(transform)].set_index('support').loc[VIEWS]
        for col,arm,marker in [('M_theta_KO_minus_WT','M','o'),('C_theta_KO_minus_WT','E','s')]:
            ax.plot(range(3),block[col],linestyle=style,marker=marker,fillstyle=fill,
                    markersize=5,linewidth=1.3,label=f'{arm}, {desc}')
    support_axis(ax);ax.set_ylabel('Conditional component, θ\n(log-abundance units)')
    ax.set_ylim(-.08,3.35);ax.legend(frameon=False,ncol=2,loc='upper left')
    save(fig,'01_components',['results/canonical/support_views/decision_grid.tsv'])

    fig,ax=plt.subplots(figsize=(6.5,3.8))
    for transform,desc,marker,style in [('zero_only_0.5','Zeros → 0.5','o','-'),('count_plus_1','Count + 1','s','--')]:
        block=grid[grid['transform'].eq(transform)].set_index('support').loc[VIEWS]
        ax.plot(range(3),block.theta_KO_minus_WT,marker=marker,linestyle=style,markersize=5,linewidth=1.3,label=desc)
    ax.axhline(0,linestyle=':',linewidth=.7)
    support_axis(ax);ax.set_ylabel('Pathway contrast, θ(M) − θ(E)\n(log-abundance units)')
    ax.set_ylim(-2.05,1.4);ax.legend(frameon=False,ncol=2,loc='upper right')
    save(fig,'01_balance',['results/canonical/support_views/decision_grid.tsv'])

    genes=pd.read_csv(ROOT/'revision/results/revision/retained_added_gene_values.tsv',sep='\t')
    fig,ax=plt.subplots(figsize=(6.5,4.0))
    labels=[]
    for t,transform in enumerate(['zero_only_0.5','count_plus_1']):
        ax.set_prop_cycle(None)
        for k,(pop,n,label) in enumerate([('retained_T0_transcripts',23,'Retained'),('added_T0_genes',68,'Added')]):
            x=2*t+k;f=genes[genes['transform'].eq(transform)&genes.pathway.eq('C')&genes.population.eq(pop)].sort_values('gene')
            if len(f)!=n:raise ValueError('Frozen comparator membership count differs')
            y=f.theta_KO_minus_WT.to_numpy()
            jitter=np.array([int(hashlib.sha256(v.encode()).hexdigest()[:8],16)/0xffffffff-.5 for v in f.gene])*.34
            # One plot call per population; no random downsampling or selected genes.
            ax.plot(x+jitter,y,linestyle='none',marker='o' if t==0 else 's',markersize=3.4,alpha=.70,label=label if t==0 else None)
            ax.annotate(f'{y.mean():+.3f}',(x,y.mean()),xytext=(20,0),textcoords='offset points',fontsize=8,va='center')
            ax.hlines(y.mean(), x-.21, x+.21, linewidth=1.0)
            # Mean marks are not uncertainty intervals.
            labels.append(f'{label}\nn = {n}')
    ax.axhline(0,linestyle=':',linewidth=.7)
    ax.set_xticks(range(4),labels);ax.set_ylabel('Gene-level conditional contrast\n(log-abundance units)')
    ax.set_xlabel('Zero-only transformation                 Count + 1')
    ax.set_xlim(-.5,3.65)
    save(fig,'02_comparator_members',['revision/results/revision/retained_added_gene_values.tsv'])

    floor=pd.read_csv(ROOT/'results/canonical/support_views/count_floor.tsv',sep='\t')
    f=floor[floor['transform'].eq('zero_only_0.5')&floor.support.eq(VIEWS[2])&floor.pathway.eq('C')]
    ordered=[f[f.background.eq(b)&f.condition.eq(c)].iloc[0] for b,c in [('parent','vehicle'),('parent','DNAPKi'),('PRDX1KO','vehicle'),('PRDX1KO','DNAPKi')]]
    zeros=np.array([r.zero_cells for r in ordered]);low=np.array([r.below40_cells-r.zero_cells for r in ordered]);high=np.array([r.cells-r.below40_cells for r in ordered])
    fig,ax=plt.subplots(figsize=(6.5,4.0));x=np.arange(4)
    ax.bar(x,zeros,width=.64,label='0');ax.bar(x,low,width=.64,bottom=zeros,label='1–39');ax.bar(x,high,width=.64,bottom=zeros+low,label='≥40')
    for i,r in enumerate(ordered):ax.text(i,r.cells+6,f'{int(r.zero_cells)} zero',ha='center',fontsize=8.5)
    ax.set_xticks(x,['WT\nvehicle','WT\nAZD7648','KO\nvehicle','KO\nAZD7648'])
    ax.set_ylabel('Construct × sample entries');ax.set_ylim(0,365)
    ax.legend(frameon=False,ncol=3,loc='upper center',title='Raw count',fontsize=9,title_fontsize=9)
    save(fig,'03_count_floor',['results/canonical/support_views/count_floor.tsv'])

    samples=pd.read_csv(ROOT/'results/canonical/support_views/pathway_sample_values.tsv',sep='\t')
    samples=samples[samples['transform'].eq('zero_only_0.5')]
    groups=[('parent','T0'),('parent','vehicle'),('parent','DNAPKi'),('PRDX1KO','T0'),('PRDX1KO','vehicle'),('PRDX1KO','DNAPKi')]
    for arm in ['M','C']:
        fig,ax=plt.subplots(figsize=(6.5,3.8))
        for k,view in enumerate(VIEWS):
            f=samples[samples.support.eq(view)];xs=[];ys=[]
            for j,(background,condition) in enumerate(groups):
                q=f[f.sample_id.str.contains('A549_'+background+'__',regex=False)&f.sample_id.str.contains('__'+condition+'__',regex=False)].sort_values('sample_id')
                if len(q)!=(2 if condition=='T0' else 3):raise ValueError('Unexpected sample count')
                for h,value in enumerate(q[arm]):xs.append(j+(k-1)*.20+(h-(len(q)-1)/2)*.045);ys.append(value)
            ax.plot(xs,ys,linestyle='none',marker=['o','s','^'][k],markersize=4.5,label=['S0','S1','S2'][k])
        ax.set_xticks(range(6),['WT\nT0','WT\nvehicle','WT\ndrug','KO\nT0','KO\nvehicle','KO\ndrug'])
        ax.set_ylabel(('M' if arm=='M' else 'E')+': centred mean log abundance')
        ax.legend(frameon=False,ncol=3,loc='upper right');ax.axhline(0,linestyle=':',linewidth=.7)
        save(fig,'04_samples_'+arm,['results/canonical/support_views/pathway_sample_values.tsv'])
    (out/'FIGURE_SOURCES.json').write_text(json.dumps(paths,indent=2)+'\n')
    return list(paths)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True)
    print(build(parser.parse_args().output.resolve()))
