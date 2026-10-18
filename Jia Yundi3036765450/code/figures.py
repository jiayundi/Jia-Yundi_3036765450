from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

BLUE='#24587a'; RED='#b45e42'; GRAY='#647482'

def main(root,d):
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,
                         'axes.spines.right':False,'axes.titleweight':'bold','figure.dpi':150,
                         'savefig.dpi':180,'axes.grid':True,'axes.axisbelow':True,'grid.alpha':.18})
    out=root/'outputs/figures'
    def finish(fig,name):
        fig.tight_layout()
        fig.savefig(out/f'{name}.png',bbox_inches='tight',metadata={'Software':'ECON6067 deterministic replication'})
        plt.close(fig)
    bal=d.loc[d.delta.notna()]
    fig,ax=plt.subplots(figsize=(7.4,3.8))
    for s,label,c in [(0,'Pennsylvania',GRAY),(1,'New Jersey',BLUE)]:
        g=bal.loc[bal.STATE.eq(s)]; means=[g.fte0.mean(),g.fte1.mean()]
        ax.plot([0,1],means,'o-',color=c,label=f'{label} (n={len(g)})',lw=2)
        for x,y in enumerate(means):
            offset=-15 if s==1 and x==1 else 9
            ax.annotate(f'{y:.2f}',(x,y),xytext=(0,offset),textcoords='offset points',ha='center')
    pa_change=bal.loc[bal.STATE.eq(0),'delta'].mean(); nj0=bal.loc[bal.STATE.eq(1),'fte0'].mean()
    ax.plot([0,1],[nj0,nj0+pa_change],'--',color=RED,label='NJ counterfactual under parallel trends')
    ax.set(xticks=[0,1],xticklabels=['February-March 1992','November-December 1992'],ylabel='FTE employees per restaurant',title='Balanced-sample employment comparison')
    ax.legend(frameon=False,fontsize=8,loc='lower left'); finish(fig,'figure1_did')

    bins=np.array([4,4.25,4.5,4.75,5,5.05,5.25,5.5,5.75,6,6.5,7,8])
    fig,axes=plt.subplots(1,2,figsize=(8,3.3),sharey=True)
    # Discrete counts, rather than different bin widths, make the minimum spike visible.
    cats=['<4.25','4.25','4.26-4.99','5.00','5.05','5.06-5.49','>=5.50']
    records=[]
    for t,ax in enumerate(axes):
        for s,c,label,shift in [(0,GRAY,'PA',-.18),(1,BLUE,'NJ',.18)]:
            a=d.loc[d.STATE.eq(s),'WAGE_ST'+('2' if t else '')].dropna()
            counts=[(a<4.25).sum(),a.eq(4.25).sum(),a.between(4.26,4.99).sum(),a.eq(5.).sum(),a.eq(5.05).sum(),a.between(5.06,5.49).sum(),a.ge(5.5).sum()]
            # Values such as 5.01-5.04 are possible; retain an explicit residual audit.
            other=len(a)-sum(counts)
            assert other==0, f'Unbinned wage values: {other}'
            ax.bar(np.arange(len(cats))+shift,np.array(counts)/len(a)*100,width=.35,color=c,label=label)
            records += [{'wave':t,'state':label,'wage_category':cat,'count':int(n),'denominator':len(a),'percent':n/len(a)*100} for cat,n in zip(cats,counts)]
        ax.set(xticks=range(len(cats)),xticklabels=cats,title='Before' if t==0 else 'After',xlabel='Starting wage ($ per hour)'); ax.tick_params(axis='x',rotation=55); ax.legend(frameon=False)
    axes[0].set_ylabel('Percent of nonmissing wage observations')
    finish(fig,'figure2_wages')
    pd.DataFrame(records).to_csv(root/'outputs/tables/wage_distribution_counts.csv',index=False)

    # Required original Figure 1: ten-cent ranges, two stacked periods.
    # Integer cents prevent binary floating-point edges from moving exact values.
    # Edges: [420,430), [430,440), ..., [540,550), and [550,+infinity).
    # The article labels centers but does not publish exact endpoint code.
    fig,axes=plt.subplots(2,1,figsize=(7.4,7.4),sharex=True)
    labels=[f'{(425+10*i)/100:.2f}' for i in range(14)]
    edges=np.arange(430,551,10)
    original_records=[]
    for wave,ax in enumerate(axes):
        for state,label,shift in [(1,'New Jersey',-.19),(0,'Pennsylvania',.19)]:
            wages=d.loc[d.STATE.eq(state),'WAGE_ST'+('2' if wave else '')].dropna()
            cents=np.rint(wages.to_numpy()*100).astype(int)
            assert np.all(cents>=420)
            categories=np.searchsorted(edges,cents,side='right')
            counts=np.bincount(categories,minlength=14)
            assert counts.sum()==len(wages)
            bars=ax.bar(np.arange(14)+shift,counts/len(wages)*100,width=.36,
                        color='black' if state else 'white',edgecolor='black',
                        hatch=None if state else '////',label=label,linewidth=.9)
            original_records += [dict(wave=wave,state=label,wage_range_label=labels[i],
                lower_inclusive_cents=int(420+10*i),upper_exclusive_cents=int(430+10*i) if i<13 else None,
                count=int(n),denominator=len(wages),percent=float(n/len(wages)*100)) for i,n in enumerate(counts)]
        ax.set_title('February 1992' if wave==0 else 'November 1992')
        ax.set_ylabel('Percent of stores'); ax.set_xlabel('Wage range ($ per hour)')
        ax.set_ylim(0,35 if wave==0 else 90)
        ax.set_yticks(np.arange(0,36,5) if wave==0 else np.arange(0,91,10))
        ax.set_xticks(range(14),labels); ax.tick_params(axis='x',labelbottom=True,labelsize=8)
    axes[1].legend(frameon=False,loc='upper center',bbox_to_anchor=(.5,-.20),ncol=2)
    finish(fig,'figure1_original_wage_distribution')
    pd.DataFrame(original_records).to_csv(root/'outputs/tables/figure1_original_bins.csv',index=False)

    ext=pd.read_csv(root/'outputs/tables/ownership_extension.csv')
    ext=ext.loc[ext['sample'].eq('Wage-complete 357')]
    fig,ax=plt.subplots(figsize=(7.6,3.4)); ys=np.arange(len(ext))
    ax.errorbar(ext.coefficient,ys,xerr=np.vstack([ext.coefficient-ext.ci_low,ext.ci_high-ext.coefficient]),fmt='o',color=BLUE,capsize=4)
    ax.axvline(0,color=GRAY,lw=1); ax.set(yticks=ys,yticklabels=ext.effect,xlabel='FTE effect and restaurant-level HC3 95% interval',title='Independent extension: ownership heterogeneity'); ax.invert_yaxis()
    finish(fig,'figure3_ownership')

    inf=pd.read_csv(root/'outputs/tables/leave_one_chain_out.csv')
    base=pd.read_csv(root/'outputs/tables/inference_comparison.csv').iloc[1]
    fig,ax=plt.subplots(figsize=(7.2,3.5)); ys=np.arange(len(inf))
    ax.errorbar(inf.coefficient,ys,xerr=np.vstack([inf.coefficient-inf.ci_low,inf.ci_high-inf.coefficient]),fmt='o',capsize=4,color=BLUE)
    ax.axvline(0,color=GRAY,lw=1); ax.axvline(base.coefficient,ls='--',color=RED,label=f'All chains = {base.coefficient:.2f}')
    ax.set(yticks=ys,yticklabels=['Without '+s for s in inf.excluded_chain],xlabel='Adjusted NJ effect (FTE)',title='Sensitivity to leaving out one chain'); ax.legend(frameon=False,fontsize=8); ax.invert_yaxis()
    finish(fig,'figure4_chain_influence')

    comp=pd.read_csv(root/'outputs/tables/employment_components.csv')
    fig,ax=plt.subplots(figsize=(6.8,3.3)); y=np.arange(len(comp))
    ax.errorbar(comp.coefficient,y,xerr=np.vstack([comp.coefficient-comp.ci_low,comp.ci_high-comp.coefficient]),fmt='o',color=BLUE,capsize=4)
    ax.axvline(0,color=GRAY,lw=1); ax.set(yticks=y,yticklabels=comp.component,xlabel='Contribution to adjusted NJ FTE effect',title='Employment composition on the common sample'); ax.invert_yaxis()
    finish(fig,'figure5_components')
