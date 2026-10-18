"""Data construction, replication and a pre-specified ownership extension.

Every outcome is constructed from raw survey fields. Published values below are
comparison targets only; they never enter an estimator or sample-selection rule.
"""
from __future__ import annotations
import hashlib
import io
import json
from pathlib import Path
import zipfile

import numpy as np
import pandas as pd
import scipy.stats as st
import statsmodels.api as sm

CHAINS = {1: 'Burger King', 2: 'KFC', 3: 'Roy Rogers', 4: "Wendy's"}
CONTROLS = ['bk', 'kfc', 'roys', 'CO_OWNED']
REGIONS = ['CENTRALJ', 'SOUTHJ', 'PA1', 'PA2']
SEED = 6067


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(df, root, name):
    df.to_csv(root / 'outputs/tables' / f'{name}.csv', index=False, float_format='%.10g')



def construct(raw, alpha=.5, managers=True, temporary_zero=False):
    d = raw.copy()
    if 'SHEET' in d:
        # SHEET 407 occurs once in each state; do not drop either restaurant.
        d['store_id'] = d.STATE.astype(str) + '_' + d.SHEET.astype(str)
    for wave, suf in [(0, ''), (1, '2')]:
        # No skip-na row sums: one missing component makes FTE missing.
        d[f'fte{wave}'] = d['EMPFT'+suf] + alpha*d['EMPPT'+suf]
        if managers:
            d[f'fte{wave}'] += d['NMGRS'+suf]
    d.loc[d.STATUS2.eq(3), 'fte1'] = 0.
    d.loc[d.STATUS2.isin([0, 2, 4, 5]), 'fte1'] = np.nan
    if temporary_zero:
        d.loc[d.STATUS2.isin([2, 4, 5]), 'fte1'] = 0.
    d['delta'] = d.fte1 - d.fte0
    d['gap'] = np.where(d.STATE.eq(0), 0., np.maximum((5.05-d.WAGE_ST)/d.WAGE_ST, 0.))
    d['sym_change'] = 2*d.delta/(d.fte0+d.fte1)
    d.loc[d.STATUS2.eq(3), 'sym_change'] = -1.
    if temporary_zero:
        d.loc[d.STATUS2.isin([2, 4, 5]), 'sym_change'] = -1.
    for key, code in [('bk', 1), ('kfc', 2), ('roys', 3)]:
        d[key] = d.CHAIN.eq(code).astype(int)
    d['NJ_company'] = d.STATE*d.CO_OWNED
    closure_exception = d.STATUS2.eq(3)
    if temporary_zero:
        closure_exception = closure_exception | d.STATUS2.isin([2,4,5])
    d['reg_sample'] = d.delta.notna() & ((d.WAGE_ST.notna() & d.WAGE_ST2.notna()) | closure_exception)
    return d


def fit(d, y, xs, cov='nonrobust', weights=None):
    cols = list(dict.fromkeys([y]+xs+([weights] if weights else [])))
    g = d.dropna(subset=cols)
    x = sm.add_constant(g[xs].astype(float), has_constant='add')
    klass = sm.WLS if weights else sm.OLS
    kw = {'weights': g[weights]} if weights else {}
    result = klass(g[y].astype(float), x, **kw).fit(cov_type=cov, use_t=True)
    return result, g


def coefficient(r, name, **metadata):
    ci = r.conf_int().loc[name]
    return dict(metadata, coefficient=float(r.params[name]), se=float(r.bse[name]),
                pvalue=float(r.pvalues[name]), ci_low=float(ci.iloc[0]),
                ci_high=float(ci.iloc[1]), n=int(r.nobs), rmse=float(np.sqrt(r.mse_resid)))


def table2(d, root):
    """All 20 paper rows; boolean wage indicators follow author SAS missing=0."""
    g=d.copy()
    g['frac0']=100*g.EMPFT/g.fte0
    g['frac1']=100*(g.EMPFT2/g.fte1).where(g.fte1.gt(0))
    g['meal0']=g.PSODA+g.PFRY+g.PENTREE
    g['meal1']=g.PSODA2+g.PFRY2+g.PENTREE2
    for name,expr in [('bk_pct',g.CHAIN.eq(1)),('kfc_pct',g.CHAIN.eq(2)),
                      ('roy_pct',g.CHAIN.eq(3)),('wen_pct',g.CHAIN.eq(4)),
                      ('owned_pct',g.CO_OWNED.eq(1)),('min0',g.WAGE_ST.eq(4.25)),
                      ('oldmin1',g.WAGE_ST2.eq(4.25)),('newmin1',g.WAGE_ST2.eq(5.05))]:
        g[name]=100*expr.astype(float)
    g['bonus0']=100*g.BONUS; g['bonus1']=100*g.SPECIAL2
    specs=[
        ('1a','Store types','Burger King (%)','bk_pct',41.1,44.3,-.5,1),
        ('1b','Store types','KFC (%)','kfc_pct',20.5,15.2,1.2,1),
        ('1c','Store types','Roy Rogers (%)','roy_pct',24.8,21.5,.6,1),
        ('1d','Store types',"Wendy's (%)",'wen_pct',13.6,19.,-1.1,1),
        ('1e','Store types','Company-owned (%)','owned_pct',34.1,35.4,-.2,1),
        ('2a','Wave 1','FTE employment','fte0',20.4,23.3,-2.,1),
        ('2b','Wave 1','Full-time employees (%)','frac0',32.8,35.,-.7,1),
        ('2c','Wave 1','Starting wage ($)','WAGE_ST',4.61,4.63,-.4,2),
        ('2d','Wave 1','Wage = $4.25 (%)','min0',30.5,32.9,-.4,1),
        ('2e','Wave 1','Full meal price ($)','meal0',3.35,3.04,4.,2),
        ('2f','Wave 1','Hours open','HRSOPEN',14.4,14.5,-.3,1),
        ('2g','Wave 1','Recruiting bonus (%)','bonus0',23.6,29.1,-1.,1),
        ('3a','Wave 2','FTE employment','fte1',21.,21.2,-.2,1),
        ('3b','Wave 2','Full-time employees (%)','frac1',35.9,30.4,1.8,1),
        ('3c','Wave 2','Starting wage ($)','WAGE_ST2',5.08,4.62,10.8,2),
        ('3d','Wave 2','Wage = $4.25 (%)','oldmin1',0.,25.3,None,1),
        ('3e','Wave 2','Wage = $5.05 (%)','newmin1',85.2,1.3,36.1,1),
        ('3f','Wave 2','Full meal price ($)','meal1',3.41,3.03,5.,2),
        ('3g','Wave 2','Hours open','HRSOPEN2',14.4,14.7,-.8,1),
        ('3h','Wave 2','Recruiting bonus (%)','bonus1',20.3,23.4,-.6,1)]
    original_se={
        '2a':(.51,1.35),'2b':(1.3,2.7),'2c':(.02,.04),'2d':(2.5,5.3),
        '2e':(.04,.07),'2f':(.2,.3),'2g':(2.3,5.1),
        '3a':(.52,.94),'3b':(1.4,2.8),'3c':(.01,.04),'3d':(0.,4.9),
        '3e':(2.,1.3),'3f':(.04,.07),'3g':(.2,.3),'3h':(2.3,4.9)}
    rows=[]
    for rid,section,label,var,pnj,ppa,pt,decimals in specs:
        a=g.loc[g.STATE.eq(1),var].dropna(); b=g.loc[g.STATE.eq(0),var].dropna()
        se=np.hypot(a.sem(),b.sem())
        welch=(a.mean()-b.mean())/se if se>0 else np.nan
        pooled=st.ttest_ind(a,b,equal_var=True).statistic
        row=dict(row=rid,section=section,variable=label,source_variable=var,
                 NJ_mean=a.mean(),NJ_se=a.sem(),NJ_n=len(a),PA_mean=b.mean(),PA_se=b.sem(),PA_n=len(b),
                 t_welch=welch,t_pooled=pooled,published_NJ=pnj,published_PA=ppa,published_t=pt,
                 published_NJ_se=original_se.get(rid,(np.nan,np.nan))[0],
                 published_PA_se=original_se.get(rid,(np.nan,np.nan))[1],mean_decimals=decimals)
        row['NJ_difference']=row['NJ_mean']-pnj; row['PA_difference']=row['PA_mean']-ppa
        row['t_difference']=welch-pt if pt is not None else np.nan
        rows.append(row)
    out=pd.DataFrame(rows); save(out,root,'table2_replication'); save(out,root,'table2_comparison')
    return out


def main(root, input_file, bootstrap=4999):
    raw = pd.read_csv(input_file)
    assert raw.shape == (410, 46), f'Unexpected schema {raw.shape}'
    assert not raw.duplicated(['STATE','SHEET']).any()
    assert set(raw.STATE.unique()) == {0, 1}
    assert raw[['EMPFT', 'EMPPT', 'NMGRS', 'EMPFT2', 'EMPPT2', 'NMGRS2']].min().min() >= 0
    author_zip = root/'input/external/njmin_author.zip'
    provenance = {'course_csv_sha256': sha(input_file), 'shape': list(raw.shape),
                  'source_check': 'author archive unavailable', 'unequal_cells': None}
    if author_zip.exists():
        with zipfile.ZipFile(author_zip) as z:
            author = pd.read_csv(io.BytesIO(z.read('public.dat')), sep=r'\s+', names=raw.columns, na_values='.')
            unequal = ~(raw.eq(author) | (raw.isna() & author.isna()))
            provenance.update(source_check='all cells compared with author public.dat',
                              unequal_cells=int(unequal.sum().sum()),
                              author_zip_sha256=sha(author_zip))
            assert provenance['unequal_cells'] == 0
    d = construct(raw)
    d.to_csv(root/'data/processed/analysis_store.csv', index=False)
    long = pd.concat([d[['store_id', 'SHEET', 'STATE', 'CHAIN', 'CO_OWNED', f'fte{t}']].rename(columns={f'fte{t}': 'fte'}).assign(post=t) for t in [0, 1]], ignore_index=True)
    long['NJ_post'] = long.STATE*long.post
    long.to_csv(root/'data/processed/analysis_panel.csv', index=False)
    audit = []
    for label, mask in [
        ('Raw stores', pd.Series(True, index=d.index)),
        ('Wave 1 FTE observed', d.fte0.notna()), ('Wave 2 FTE observed', d.fte1.notna()),
        ('Balanced FTE sample', d.delta.notna()), ('Table 4 wage-complete sample', d.reg_sample),
        ('Permanent closure', d.STATUS2.eq(3)), ('Temporary closure', d.STATUS2.isin([2, 4, 5])),
        ('Second-wave refusal', d.STATUS2.eq(0))]:
        audit.append({'sample': label, 'PA': int((mask & d.STATE.eq(0)).sum()),
                      'NJ': int((mask & d.STATE.eq(1)).sum()), 'total': int(mask.sum())})
    audit = pd.DataFrame(audit); save(audit, root, 'sample_flow')
    missing = pd.DataFrame({'variable': raw.columns, 'missing_count': raw.isna().sum().values})
    save(missing, root, 'missingness')
    t2=table2(d,root)

    # Full Table 3 point estimates: 5 rows x 8 columns.
    groups = {'PA': d.STATE.eq(0), 'NJ': d.STATE.eq(1),
              'NJ_low': d.STATE.eq(1) & d.WAGE_ST.eq(4.25),
              'NJ_mid': d.STATE.eq(1) & d.WAGE_ST.between(4.26, 4.99),
              'NJ_high': d.STATE.eq(1) & d.WAGE_ST.ge(5.)}
    tmp = construct(raw, temporary_zero=True)
    rows = []
    for row, label in [(1, 'FTE before all available'), (2, 'FTE after all available'),
                       (3, 'Change in available means'), (4, 'Change balanced sample'),
                       (5, 'Temporary closures set to zero')]:
        values = {}
        for name, mask in groups.items():
            g = d.loc[mask]
            if row in [1, 2]:
                v = g[f'fte{row-1}'].dropna(); mean=v.mean(); se=v.sem(); n=len(v)
            elif row == 3:
                mean = g.fte1.mean()-g.fte0.mean()
                # Influence-function variance keeps same-store cross-wave covariance.
                # n/(n-1) is a finite-sample correction; paper only prints 2 decimals.
                psi = (g.fte1-g.fte1.mean()).fillna(0)/g.fte1.count()-(g.fte0-g.fte0.mean()).fillna(0)/g.fte0.count()
                se=np.sqrt((psi**2).sum()*len(g)/(len(g)-1)); n=len(g)
            else:
                v = (tmp if row == 5 else d).loc[mask, 'delta'].dropna()
                mean=v.mean(); se=v.sem(); n=len(v)
            values[name] = (float(mean), float(se), int(n))
        for label2, a, b in [('NJ_minus_PA', 'NJ', 'PA'), ('low_minus_high', 'NJ_low', 'NJ_high'), ('mid_minus_high', 'NJ_mid', 'NJ_high')]:
            values[label2]=(values[a][0]-values[b][0], np.hypot(values[a][1],values[b][1]), values[a][2]+values[b][2])
        for name, (value, se, n) in values.items():
            rows.append({'row': row, 'description':label, 'group':name, 'estimate':value, 'se':se, 'n':n})
    table3=pd.DataFrame(rows); save(table3,root,'table3_replication')
    originals = {
        'PA':[23.33,21.17,-2.16,-2.28,-2.28], 'NJ':[20.44,21.03,.59,.47,.23],
        'NJ_minus_PA':[-2.89,-.14,2.76,2.75,2.51],
        'NJ_low':[19.56,20.88,1.32,1.21,.90], 'NJ_mid':[20.08,20.96,.87,.71,.49],
        'NJ_high':[22.25,20.21,-2.04,-2.16,-2.39],
        'low_minus_high':[-2.69,.67,3.36,3.36,3.29], 'mid_minus_high':[-2.17,.75,2.91,2.87,2.88]}
    comp3=table3.copy()
    comp3['published']= [originals[g][r-1] for r,g in zip(comp3.row,comp3.group)]
    comp3['difference']=comp3.estimate-comp3.published
    comp3['within_001']=comp3.difference.abs() <= .01
    original_se3={
        'PA':[1.35,.94,1.25,1.25,1.25],'NJ':[.51,.52,.54,.48,.49],
        'NJ_minus_PA':[1.44,1.07,1.36,1.34,1.35],
        'NJ_low':[.77,1.01,.95,.82,.87],'NJ_mid':[.84,.76,.84,.69,.69],
        'NJ_high':[1.14,1.03,1.14,1.01,1.02],
        'low_minus_high':[1.37,1.44,1.48,1.30,1.34],
        'mid_minus_high':[1.41,1.27,1.41,1.22,1.23]}
    comp3['published_se']=[original_se3[g][r-1] for r,g in zip(comp3.row,comp3.group)]
    comp3['se_difference']=comp3.se-comp3.published_se
    comp3['variance_rule']=np.where(comp3.row.eq(3),'Available-means influence function; not claimed historical SE', 'Sample SEM; independent group contrasts')
    save(comp3,root,'table3_comparison')

    # Headline coefficients and inference from each original Table 4 column.
    reg=d.loc[d.reg_sample].copy()
    specifications=[('i','STATE',[]), ('ii','STATE',CONTROLS), ('iii','gap',[]),
                    ('iv','gap',CONTROLS), ('v','gap',['bk','kfc','roys']+REGIONS)]
    table4=[]; reg_results={}
    for label, term, controls in specifications:
        r,g=fit(reg,'delta',[term]+controls); reg_results[label]=r
        rec=coefficient(r,term,model=label,term=term,controls=', '.join(controls) or 'constant only',covariance='Conventional OLS')
        if controls:
            restriction=np.zeros((len(controls),len(r.params)))
            for i,c in enumerate(controls): restriction[i,r.params.index.get_loc(c)]=1
            rec['controls_F_pvalue']=float(r.f_test(restriction).pvalue)
        else: rec['controls_F_pvalue']=np.nan
        table4.append(rec)
    table4=pd.DataFrame(table4); save(table4,root,'table4_replication')
    comp4=table4[['model','term','coefficient','se','n','rmse']].copy()
    comp4['published_coefficient']=[2.33,2.30,15.65,14.92,11.91]
    comp4['published_se']=[1.19,1.20,6.08,6.21,7.39]
    comp4['coefficient_difference']=comp4.coefficient-comp4.published_coefficient
    comp4['se_difference']=comp4.se-comp4.published_se
    comp4['published_rmse']=[8.79,8.78,8.76,8.76,8.75]
    comp4['published_controls_F_pvalue']=[np.nan,.34,np.nan,.44,.40]
    comp4['replicated_controls_F_pvalue']=table4.controls_F_pvalue
    comp4['rmse_difference']=comp4.rmse-comp4.published_rmse
    comp4['F_pvalue_difference']=comp4.replicated_controls_F_pvalue-comp4.published_controls_F_pvalue
    save(comp4,root,'table4_comparison')
    r_literal,_=fit(reg,'delta',['gap']+CONTROLS+REGIONS)
    region_audit=[]
    for result,label in [(reg_results['v'],'Author check.sas; ownership omitted'),(r_literal,'Literal paper label; ownership included')]:
        names=[n for n in result.params.index if n not in ['const','gap']]
        rr=np.zeros((len(names),len(result.params)))
        for i,n in enumerate(names): rr[i,result.params.index.get_loc(n)]=1
        region_audit.append(coefficient(result,'gap',specification=label,controls_F_pvalue=float(result.f_test(rr).pvalue)))
    save(pd.DataFrame(region_audit),root,'regional_specification_audit')

    # Table 2 style summary, including observed wage increases.
    summary=[]
    for var in ['fte0','fte1','WAGE_ST','WAGE_ST2','HRSOPEN','HRSOPEN2']:
        for state in [0,1]:
            a=d.loc[d.STATE.eq(state),var].dropna()
            summary.append({'variable':var,'state':'NJ' if state else 'PA','mean':a.mean(),'se':a.sem(),'n':len(a)})
    save(pd.DataFrame(summary),root,'descriptive_statistics')

    # Selected, fully identified Table 5 specifications. Do not invent ZIP codes.
    robust=[]
    variants=[('Base',{}),('Temporary zero',{'temporary_zero':True}),
              ('Exclude managers',{'managers':False}),('Part-time weight 0.4',{'alpha':.4}),
              ('Part-time weight 0.6',{'alpha':.6}),('Exclude NJ shore',{}),('At most 2 callbacks',{})]
    for label,kw in variants:
        v=construct(raw,**kw)
        # Redefining FTE must not silently add records with missing manager counts.
        mask=v.reg_sample if kw.get('temporary_zero') else (v.reg_sample & d.reg_sample)
        v=v.loc[mask]
        if label=='Exclude NJ shore': v=v.loc[v.SHORE.eq(0)]
        if label=='At most 2 callbacks': v=v.loc[v.NCALLS.le(2)]
        for y in ['delta','sym_change']:
            for term in ['STATE','gap']:
                r,_=fit(v,y,[term]+CONTROLS)
                robust.append(coefficient(r,term,specification=label,outcome=y,term=term))
    for term in ['STATE','gap']:
        r,_=fit(reg,'sym_change',[term]+CONTROLS,weights='fte0')
        robust.append(coefficient(r,term,specification='Initial-employment WLS',outcome='sym_change',term=term))
    # Paper's PA-only falsification, using a hypothetical positive gap in PA.
    pa=reg.loc[reg.STATE.eq(0)].copy(); pa['placebo_gap']=np.maximum((5.05-pa.WAGE_ST)/pa.WAGE_ST,0)
    for y in ['delta','sym_change']:
        r,_=fit(pa,y,['placebo_gap']+CONTROLS)
        robust.append(coefficient(r,'placebo_gap',specification='PA-only wage-gap falsification',outcome=y,term='placebo_gap'))
    robust=pd.DataFrame(robust); save(robust,root,'robustness')

    # Independent extension: ownership interaction rather than subgroups' p-values.
    extension=[]
    for sample,label in [(reg,'Wage-complete 357'),(d.loc[d.delta.notna()],'All balanced 384')]:
        xs=['STATE','CO_OWNED','NJ_company','bk','kfc','roys']
        r,g=fit(sample,'delta',xs,cov='HC3')
        for term in ['STATE','NJ_company']:
            extension.append(coefficient(r,term,sample=label,effect='Franchise NJ effect' if term=='STATE' else 'Company minus franchise interaction',covariance='HC3'))
        contrast=np.zeros(len(r.params)); contrast[r.params.index.get_loc('STATE')]=1; contrast[r.params.index.get_loc('NJ_company')]=1
        test=r.t_test(contrast); ci=np.asarray(test.conf_int()).ravel()
        extension.append({'sample':label,'effect':'Company-owned NJ effect','covariance':'HC3',
                          'coefficient':float(np.asarray(test.effect).item()),'se':float(np.asarray(test.sd).item()),
                          'pvalue':float(np.asarray(test.pvalue).item()),'ci_low':ci[0],'ci_high':ci[1],'n':len(g)})
    extension=pd.DataFrame(extension); save(extension,root,'ownership_extension')
    own_counts=reg.groupby(['STATE','CO_OWNED'],as_index=False).agg(n=('SHEET','size'),baseline_fte=('fte0','mean'),change_fte=('delta','mean'),initial_wage=('WAGE_ST','mean'))
    save(own_counts,root,'ownership_cell_summary')

    # Complementary decomposition. Use the same stores for additive consistency.
    decomposition=[]
    common=reg.copy()
    for component,before,after,weight in [('Full-time','EMPFT','EMPFT2',1.),('Part-time FTE','EMPPT','EMPPT2',.5),('Managers','NMGRS','NMGRS2',1.)]:
        after_values=common[after].where(~common.STATUS2.eq(3),0.)
        common[component]=weight*(after_values-common[before])
    for component in ['Full-time','Part-time FTE','Managers']:
        r,_=fit(common,component,['STATE']+CONTROLS,cov='HC3')
        decomposition.append(coefficient(r,'STATE',component=component))
    decomposition=pd.DataFrame(decomposition); save(decomposition,root,'employment_components')
    assert np.isclose(decomposition.coefficient.sum(),reg_results['ii'].params['STATE'])

    influence=[]
    for code,label in CHAINS.items():
        v=reg.loc[reg.CHAIN.ne(code)]
        xs=['STATE']+[c for c in CONTROLS if v[c].nunique()>1]
        x=sm.add_constant(v[xs].astype(float))
        # Omit one remaining chain dummy to avoid dummy-variable collinearity.
        while np.linalg.matrix_rank(x.to_numpy()) < x.shape[1]:
            candidates=[c for c in ['roys','kfc','bk'] if c in x]
            x=x.drop(columns=candidates[-1])
        r=sm.OLS(v.delta,x).fit(cov_type='HC3',use_t=True)
        influence.append(coefficient(r,'STATE',excluded_chain=label))
    save(pd.DataFrame(influence),root,'leave_one_chain_out')
    rinfer=reg_results['ii']
    inference=[coefficient(rinfer,'STATE',method='Conventional OLS')]
    r_hc,_=fit(reg,'delta',['STATE']+CONTROLS,cov='HC3')
    inference.append(coefficient(r_hc,'STATE',method='Restaurant-level HC3'))

    rng=np.random.default_rng(SEED)
    x=sm.add_constant(reg[['STATE']+CONTROLS].astype(float)).to_numpy(); y=reg.delta.to_numpy()
    state_arr=reg.STATE.to_numpy(); i0=np.flatnonzero(state_arr==0); i1=np.flatnonzero(state_arr==1)
    draws=np.empty(bootstrap)
    for b in range(bootstrap):
        ids=np.r_[rng.choice(i0,len(i0),True),rng.choice(i1,len(i1),True)]
        draws[b]=np.linalg.lstsq(x[ids],y[ids],rcond=None)[0][1]
    lo,hi=np.quantile(draws,[.025,.975])
    inference.append({'method':f'Within-state restaurant bootstrap B={bootstrap}',
                      'coefficient':float(rinfer.params.STATE),'se':float(draws.std(ddof=1)),
                      'ci_low':float(lo),'ci_high':float(hi),'pvalue':np.nan,'n':len(reg)})
    inference=pd.DataFrame(inference); save(inference,root,'inference_comparison')
    np.save(root/'data/processed/bootstrap_draws.npy',draws)

    # Independent numerical and algebraic verification.
    checks=[]
    def check(name, ok, detail):
        checks.append({'check':name,'passed':bool(ok),'detail':str(detail)})
    check('raw shape',raw.shape==(410,46),raw.shape)
    check('author cell comparison',provenance['unequal_cells']==0,provenance['unequal_cells'])
    check('unique composite restaurant identifier',d.store_id.is_unique,d.store_id.nunique())
    check('permanent closure zero',d.loc[d.STATUS2.eq(3),'fte1'].eq(0).all(),6)
    check('temporary closure missing',d.loc[d.STATUS2.isin([2,4,5]),'fte1'].isna().all(),4)
    check('refusal remains missing',d.loc[d.STATUS2.eq(0),'fte1'].isna().all(),1)
    check('balanced sample n',int(d.delta.count())==384,int(d.delta.count()))
    check('regression sample n',len(reg)==357,len(reg))
    check('Table 3 40 point estimates within 0.01 FTE',bool(comp3.within_001.all()),float(comp3.difference.abs().max()))
    check('Table 4 coefficient agreement',bool((comp4.coefficient_difference.abs()<.006).all()),float(comp4.coefficient_difference.abs().max()))
    check('Table 4 SE agreement',bool((comp4.se_difference.abs()<.006).all()),float(comp4.se_difference.abs().max()))
    coef_numpy=np.linalg.lstsq(x,y,rcond=None)[0]
    check('independent NumPy OLS',np.max(abs(coef_numpy-rinfer.params.to_numpy()))<1e-10,float(np.max(abs(coef_numpy-rinfer.params.to_numpy()))))
    balanced_ids=d.loc[d.delta.notna(),'store_id']
    panel=long.loc[long.store_id.isin(balanced_ids)].dropna()
    rlong,_=fit(panel,'fte',['STATE','post','NJ_post'])
    mean_did=d.loc[d.STATE.eq(1),'delta'].mean()-d.loc[d.STATE.eq(0),'delta'].mean()
    check('balanced long DID equals first difference',np.isclose(rlong.params.NJ_post,mean_did),float(rlong.params.NJ_post))
    check('employment component identity',np.isclose(decomposition.coefficient.sum(),rinfer.params.STATE),float(decomposition.coefficient.sum()))
    check('gap zero in PA',d.loc[d.STATE.eq(0),'gap'].eq(0).all(),0)
    check('no negative wage gaps',d.gap.dropna().ge(0).all(),float(d.gap.min()))
    check('bootstrap finite',np.isfinite(draws).all(),bootstrap)
    check('Table 2 complete row coverage',len(t2)==20,len(t2))
    check('Table 2 full-time definition',np.isclose(t2.loc[t2.row.eq('2b'),'NJ_mean'].iloc[0],32.84886993281503),'EMPFT / FTE, not headcount share')
    check('Table 2 missing wage indicator denominator',int(t2.loc[t2.row.eq('2d'),'NJ_n'].iloc[0])==331,'all 331 NJ restaurants')
    check('Table 3 SE comparison complete',comp3.published_se.notna().all(),len(comp3))
    checks=pd.DataFrame(checks); save(checks,root,'validation_checks')
    if not checks.passed.all():
        print(checks.loc[~checks.passed].to_string(index=False))
        raise AssertionError('Validation failure; outputs not ready')
    results={'provenance':provenance,'bootstrap_reps':bootstrap,'seed':SEED,
             'balanced_did':float(mean_did),'unbalanced_did':float(comp3.loc[(comp3.row==3)&comp3.group.eq('NJ_minus_PA'),'estimate'].iloc[0]),
             'main_adjusted_did':float(rinfer.params.STATE), 'regional_literal_coefficient':float(r_literal.params.gap),
             'paper_comparison_table3_max_diff':float(comp3.difference.abs().max()),
             'validation_passed':int(checks.passed.sum()),'table4':table4.to_dict('records'),
             'extension':extension.to_dict('records'),'inference':inference.to_dict('records')}
    def finite_json(value):
        if isinstance(value,dict): return {k:finite_json(v) for k,v in value.items()}
        if isinstance(value,list): return [finite_json(v) for v in value]
        if isinstance(value,(float,np.floating)) and not np.isfinite(value): return None
        return value
    results=finite_json(results)
    (root/'outputs/logs/results.json').write_text(json.dumps(results,indent=2,allow_nan=False),encoding='utf-8')
    print(json.dumps(results,indent=2,allow_nan=False))
    return d, results
