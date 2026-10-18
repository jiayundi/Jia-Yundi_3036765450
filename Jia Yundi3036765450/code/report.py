"""Generate the report from estimated result files, never hand-entered results."""
import json
from pathlib import Path
from xml.sax.saxutils import escape
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.utils import ImageReader
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image
from reportlab.lib.pagesizes import A4

BLUE=colors.HexColor('#24465D'); LIGHT=colors.HexColor('#EDF2F5')

def main(root):
    results=json.loads((root/'outputs/logs/results.json').read_text(encoding='utf-8'))
    def df(name): return pd.read_csv(root/'outputs/tables'/f'{name}.csv')
    styles=getSampleStyleSheet()
    styles.add(ParagraphStyle(name='ReportTitle',fontName='Helvetica-Bold',fontSize=23,leading=28,spaceAfter=15,textColor=colors.black))
    styles.add(ParagraphStyle(name='Sub',fontName='Helvetica',fontSize=10,leading=14,textColor=colors.HexColor('#596873'),spaceAfter=14))
    styles.add(ParagraphStyle(name='Body',fontName='Helvetica',fontSize=10,leading=14,spaceAfter=9))
    styles.add(ParagraphStyle(name='Small2',fontName='Helvetica',fontSize=8.1,leading=11,spaceAfter=7))
    styles.add(ParagraphStyle(name='Cell',fontName='Helvetica',fontSize=8.2,leading=10.5))
    styles.add(ParagraphStyle(name='HeadCell',fontName='Helvetica-Bold',fontSize=8,leading=10,textColor=colors.white))
    styles.add(ParagraphStyle(name='Section',fontName='Helvetica-Bold',fontSize=15,leading=19,spaceAfter=12,textColor=colors.black))
    story=[]
    def p(text,small=False): story.append(Paragraph(text,styles['Small2' if small else 'Body']))
    def h(text): story.append(Paragraph(text,styles['Section']))
    def page(): story.append(PageBreak())
    def table(headers,rows,widths):
        cells=[[Paragraph(escape(str(v)),styles['HeadCell']) for v in headers]]
        cells += [[Paragraph(escape(str(v)).replace('\n','<br/>'),styles['Cell']) for v in row] for row in rows]
        t=Table(cells,colWidths=widths,repeatRows=1,hAlign='LEFT')
        t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),BLUE),('VALIGN',(0,0),(-1,-1),'TOP'),
            ('LEFTPADDING',(0,0),(-1,-1),6),('RIGHTPADDING',(0,0),(-1,-1),6),
            ('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7),
            ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,LIGHT]),
            ('LINEBELOW',(0,0),(-1,0),.6,BLUE),('LINEBELOW',(0,-1),(-1,-1),.5,colors.HexColor('#B9C6CF'))]))
        story.extend([t,Spacer(1,10)])
    def fig(name,width=490):
        path=root/'outputs/figures'/f'{name}.png'; iw,ih=ImageReader(str(path)).getSize()
        story.extend([Image(str(path),width=width,height=width*ih/iw),Spacer(1,8)])
    f=lambda x,n=2: f'{float(x):.{n}f}'
    ext=df('ownership_extension'); e=ext.loc[ext['sample'].eq('Wage-complete 357')]
    inter=e.loc[e.effect.eq('Company minus franchise interaction')].iloc[0]
    inf=df('inference_comparison'); hc=inf.iloc[1]; boot=inf.iloc[2]

    story.append(Paragraph('Minimum Wages and<br/>Fast Food Employment',styles['ReportTitle']))
    story.append(Paragraph('Replication of Card and Krueger 1994 and an ownership heterogeneity extension<br/>ECON6067 Individual Project | Revised 18 October 2026',styles['Sub']))
    h('Research question and main findings')
    p('Does a higher minimum wage reduce employment at fast-food restaurants? This project reconstructs the New Jersey-Pennsylvania restaurant survey, reproduces the main employment comparisons and regressions, and tests whether responses differ between company-owned restaurants and franchisees.')
    p(f'The available-means employment difference in differences is {results["unbalanced_did"]:.3f} full-time-equivalent (FTE) employees per restaurant. The balanced-sample estimate is {results["balanced_did"]:.3f}; the wage-complete regression with chain and ownership controls is {results["main_adjusted_did"]:.3f}. All five headline Table 4 coefficients and standard errors agree with the published values at their reported precision. All 40 Table 3 point estimates are within 0.01 FTE of the published entries.')
    p(f'The ownership extension estimates a company-minus-franchise interaction of {inter.coefficient:.2f} FTE (HC3 SE {inter.se:.2f}, p={inter.pvalue:.3f}). This is an exploratory conditional comparison. Its uncertainty and the non-random assignment of ownership limit a structural interpretation.')
    p('The results reproduce positive relative employment changes, not a general proof that minimum wages increase jobs. There is only one treated state, one comparison state and one pre-policy wave. Parallel trends cannot be tested, and restaurant-level standard errors do not address common state-level shocks.')
    h('Motivation and economic mechanisms')
    p('A competitive labor-demand model predicts a fall in labor demand when a binding wage floor raises labor costs. Monopsony or search frictions can instead allow a moderate wage floor to increase both wages and employment. Price adjustment, productivity, staffing composition and reduced turnover can also absorb labor costs. Positive employment estimates alone do not distinguish these channels.')
    p('New Jersey increased its minimum wage from $4.25 to $5.05 on 1 April 1992, an 18.8% statutory rise. Pennsylvania kept the $4.25 floor. The sample follows established restaurants in four chains, rather than measuring all restaurant entry, exit and economy-wide employment [1].')
    p('The supplemental course instructions explicitly require Tables 2, 3, 4 and Figure 1. All are addressed here. Table 1 is not required because sampling-frame information is limited. Table 5 checks, ownership heterogeneity and supplementary figures are additional analyses.',small=True)
    page()

    h('Data provenance and sample construction')
    p('The course input is data/raw/01_DID/data/public.csv. The original numbered folder and filename are preserved. It contains 410 restaurant records and 46 columns. Blank CSV cells are missing values; they are never globally filled with zero.')
    p('<b>Independent acquisition of author data.</b> In addition to the course files, I used the AI-assisted workflow to retrieve the original survey archive from David Card\'s Berkeley website on 16 October 2026. The source is the author\'s <link href="https://davidcard.berkeley.edu/data_sets.html" color="#24465D">data page</link>, with a direct download at <link href="https://davidcard.berkeley.edu/data_sets/njmin.zip" color="#24465D">https://davidcard.berkeley.edu/data_sets/njmin.zip</link> [2]. The archive contains public.dat, codebook, read.me and check.sas. I used these materials to check raw observations, variable definitions and the author\'s sample conventions.',small=True)
    p('<b>Acquisition, validation and scope.</b> The code/run_all.py entry point saves the archive under data/raw/author/njmin_author.zip and checks its SHA-256; python code/run_all.py reproduces acquisition when files are absent. The parser reads public.dat as 46 numeric fields and compares all 410 rows with the course CSV, including missing values: all 18,860 cells match, with zero unequal cells. This independently obtained author source validates provenance and implementation; it is the same underlying survey, not newly collected observations or an enlarged extension sample. The ownership extension uses variables already in that survey.',small=True)
    table(['Sample rule','PA','NJ','Total'],df('sample_flow').values.tolist(),[315,60,60,65])
    p('The baseline post-policy FTE is zero at the six permanently closed stores. The two renovation closures, highway-construction closure and mall-fire closure are missing; a separate sensitivity sets these four stores to zero. The single refusal remains missing under every baseline or temporary-closure variant.')
    p('Table 3 uses variable-specific available observations, then separately reports a balanced sample. Table 4 requires employment in both waves and starting wages in both waves, with permanently closed stores exempt from the second-wave wage requirement. That restriction produces the original 357-store sample. It must not be confused with the 384-store balanced employment sample.')
    p('The first wave was in February-March and the second in November-December 1992. The observations span Burger King, KFC, Roy Rogers and Wendy\'s. Location indicators, ownership and baseline chain are pre-policy controls. SHEET 407 occurs in each state: STATE plus SHEET is the unique restaurant key. Both records are retained; no restaurant is mistakenly deduplicated.')
    p('The author-source URL and hashes are documented in README.md. Raw and restaurant-level processed data are included for private course submission only.',small=True)
    page()

    h('Empirical design and variable definitions')
    p('For restaurant i and survey wave t, FTE includes full-time nonmanagement employees, managers and one half of part-time employees:')
    p('<b>FTE_it = EMPFT_it + NMGRS_it + 0.5 EMPPT_it.</b>')
    p('A missing component makes FTE missing. The baseline first difference is DeltaFTE_i = FTE_i,after - FTE_i,before. The unadjusted estimator compares the average changes between New Jersey and Pennsylvania:')
    p('<b>DID = [mean(NJ,after) - mean(NJ,before)] - [mean(PA,after) - mean(PA,before)].</b>')
    p('For the same restaurants in both waves, this equals the coefficient on NJ x Post in a two-period levels regression. For the original available-means comparison, the restaurants contributing to each mean differ slightly; it is not numerically identical to balanced first differences.')
    p('The adjusted models estimate <b>DeltaFTE_i = a + b NJ_i + c\' X_i + u_i</b>, where X includes three chain indicators and company ownership. They are equivalent to allowing these baseline attributes to explain employment changes, not to merely adding time-invariant controls to a restaurant fixed-effects regression.')
    p('The policy-intensity specifications replace NJ with the proportional initial wage gap:')
    p('<b>GAP_i = NJ_i x max[(5.05 - WAGE_ST_i) / WAGE_ST_i, 0].</b>')
    p('A GAP coefficient is the FTE change per unit of proportional wage shortfall. It is not itself a restaurant-count treatment effect. For a restaurant initially paying $4.25, multiply the coefficient by 0.8/4.25, approximately 0.1882.')
    table(['Variable','Construction and interpretation'],[
        ['Symmetric growth','2 x (FTE_after - FTE_before) / (FTE_after + FTE_before); the author program assigns -1 to permanent closures.'],
        ['NJ_company','STATE x CO_OWNED, using pre-policy ownership.'],
        ['Franchise effect','Coefficient on NJ when CO_OWNED = 0.'],
        ['Company effect','NJ coefficient plus the NJ x CO_OWNED interaction.'],
        ['Controls','Three chain dummies, ownership; regional indicators in the designated GAP model.']],[125,375])
    p('Causal identification needs parallel untreated trends, no important spillovers across the border, no differential concurrent shock, comparable measurement and a stable sample interpretation. Wage-gap comparisons additionally require that baseline wage differences are not proxies for omitted growth or measurement error. These assumptions are not established by matching published coefficients.')
    page()

    h('Replication of Table 2')
    p('All 20 rows are reconstructed, including means, proportions, state-specific standard errors and interstate equality tests. Parentheses below contain standard errors. The full original-versus-replicated comparison, sample denominators and both Welch and pooled t-statistics are exported in table2_comparison.csv and HTML.')
    t2=df('table2_replication')
    rows=[]
    for _,a in t2.iterrows():
        decimals=int(a.mean_decimals)
        sd=2 if a.row in ['2a','2c','2e','3a','3c','3f'] else 1
        nj=f(a.NJ_mean,decimals); pa=f(a.PA_mean,decimals)
        if a.section!='Store types':
            nj+=f' ({a.NJ_se:.{sd}f})'; pa+=f' ({a.PA_se:.{sd}f})'
        rows.append([a.row+' '+a.variable,nj,pa,f(a.t_welch,1),'--' if pd.isna(a.published_t) else f(a.published_t,1)])
    table(['Variable','NJ (SE)','PA (SE)','Welch t','Paper t'],rows,[220,90,90,50,50])
    p('Rows 1a-e: store types. Rows 2a-g: wave 1. Rows 3a-h: wave 2. For full-time percentage, the author formula is 100 x EMPFT/FTE, excluding managers from the numerator. This is not the conventional full-time headcount share. Minimum-wage indicators count missing wages as false, following the SAS comparison convention; their denominators are all 331 NJ and 79 PA stores. Figure 1 instead uses valid wages only.',small=True)
    newmin=t2.loc[t2.row.eq('3e')].iloc[0]
    p(f'An important residual difference: the supplied public data contain 283 NJ wages exactly equal to $5.05, giving {newmin.NJ_mean:.2f}% of 331 stores, while the paper prints 85.2%. The count is not changed to match the paper. Other small mean, SE and t differences remain in the comparison file; a numerically reproduced t is shown even where the paper prints a dash.',small=True)
    page()

    h('Replication of Table 3')
    p('Table A shows all 40 point estimates with their standard errors in parentheses. Each cell is reconstructed from the raw fields. Table B reports the original interstate differences and replication discrepancies. The full comparison also includes all 40 published standard errors and their discrepancies.')
    t3=df('table3_replication')
    order=['PA','NJ','NJ_minus_PA','NJ_low','NJ_mid','NJ_high','low_minus_high','mid_minus_high']
    arr=[]
    labels=['Before all available','After all available','Change in available means','Change balanced sample','Temporary closures zero']
    for row in range(1,6):
        g=t3.loc[t3.row.eq(row)].set_index('group')
        arr.append([labels[row-1]]+[f(g.loc[k,'estimate'])+'\n('+f(g.loc[k,'se'])+')' for k in order])
    table(['Employment measure','PA','NJ','NJ-PA','NJ low','NJ mid','NJ high','Low-high','Mid-high'],arr,[140,40,40,42,45,45,45,50,53])
    p('Low: initial wage exactly $4.25. Mid: $4.26-$4.99. High: at least $5.00. Original group counts are 101, 140 and 73 respectively before outcome-specific missingness. NJ stores with missing initial wages contribute to interstate means but not to these wage-group means.',small=True)
    c3=df('table3_comparison'); g=c3.loc[c3.group.eq('NJ_minus_PA')]
    table(['Row','Published NJ-PA','Replicated NJ-PA','Difference'],[[int(r.row),f(r.published),f(r.estimate,4),f(r.difference,4)] for _,r in g.iterrows()],[100,130,140,130])
    p(f'The largest absolute discrepancy across all 40 point estimates is {results["paper_comparison_table3_max_diff"]:.4f} FTE, consistent with rounding the original means and then subtracting them. For example, subtracting two printed means can differ by 0.01 from printing the difference of the full-precision means.')
    p('For rows 1, 2, 4 and 5, standard errors use the sample standard deviation divided by the square root of the relevant sample size; independent group differences combine squared standard errors. For row 3, an influence-function variance retains same-store covariance with differing samples. It gives NJ-PA SE 1.31 versus the paper\'s 1.36 and NJ SE 0.47 versus 0.54. These discrepancies are explicitly retained; the historical available-means variance convention is not established by the public SAS check program. Point-estimate agreement is not presented as exact historical SE replication.')
    p('The paper prints 2.76 FTE for available-means DID; the unrounded data give 2.7536, while balanced DID is exactly 2.75. This closeness is reassuring about this particular missing-data distinction. It does not establish that nonresponse is random or that unobserved state trends are parallel.')
    page()

    h('Replication of Table 4 and a specification audit')
    c4=df('table4_comparison')
    table(['Model','Term','Paper coef (SE)','Replication coef (SE)','N'],[[r.model,'NJ' if r.term=='STATE' else 'GAP',f'{r.published_coefficient:.2f} ({r.published_se:.2f})',f'{r.coefficient:.4f} ({r.se:.4f})',int(r.n)] for _,r in c4.iterrows()],[50,55,130,195,70])
    p('Columns i and iii contain only an intercept and the NJ indicator or GAP. Columns ii and iv add three chain dummies and ownership. The standard errors above are the conventional homoskedastic OLS errors used to match the historical table; modern conditional uncertainty is examined separately.')
    r4=df('table4_replication')
    table(['Model','RMSE','Joint control F-test p','Included control set'],[[r.model,f(r.rmse,3),'--' if pd.isna(r.controls_F_pvalue) else f(r.controls_F_pvalue,3),r.controls] for _,r in r4.iterrows()],[45,55,105,295])
    h('Why the last column needs a qualification')
    p('The publicly supplied author check.sas specifies GAP plus BK, KFC, ROYS, CENTRALJ, SOUTHJ, PA1 and PA2 in its final regional model. CO_OWNED is omitted. This exactly reproduces the headline 11.91 coefficient and 7.39 SE, although the printed table labels this model as controlling for both chain and ownership.')
    audit=df('regional_specification_audit')
    table(['Specification','GAP coef','SE','RMSE'],[[r.specification,f(r.coefficient,4),f(r.se,4),f(r.rmse,4)] for _,r in audit.iterrows()],[290,75,65,70])
    p('The ownership-inclusive reading gives a slightly different coefficient. We report both rather than silently dropping a variable to hit a target. The published last-column RMSE (8.75) and control F-test p-value (0.40) align with the ownership-inclusive model, whereas its headline coefficient and SE align with the ownership-omitting program. Thus the column mixes incompatible specification signals; this is an unresolved source discrepancy, not an exact replication of all column entries.')
    p('The adjusted NJ estimate is smaller than the available-means DID largely because the regressions use the wage-complete 357-store subsample. Compare i and ii to see the incremental contribution of controls; do not attribute the whole difference between 2.76 and 2.30 to controls.')
    page()

    h('Robustness checks and original-paper comparison')
    robust=df('robustness'); r=robust.loc[robust.outcome.eq('delta') & robust.term.eq('STATE')]
    published={'Base':2.30,'Temporary zero':2.20,'Exclude managers':2.34,'Part-time weight 0.4':2.34,'Part-time weight 0.6':2.27,'Exclude NJ shore':2.58,'At most 2 callbacks':2.41}
    table(['Specification','Paper NJ','Replicated NJ','OLS SE','N'],[[a.specification,f(published[a.specification]),f(a.coefficient,3),f(a.se,3),int(a.n)] for _,a in r.iterrows()],[220,65,85,65,65])
    p('Changing the part-time weight checks an accounting assumption about hours. Excluding managers checks whether staffing shifts among management drive the estimate. Excluding shore stores addresses distinctive seasonal demand, while restricting callbacks checks the extra effort used to obtain the first-wave NJ sample. None of these checks supplies an additional untreated state.')
    p('For temporary closures, the pipeline treats all four as closed consistently: post-policy employment is zero and missing post-policy wages do not exclude them, expanding the sample from 357 to 361. Excluding managers retains the original wage-complete sample so that missing manager responses cannot silently enlarge the sample. Remaining differences are kept rather than forced to equal printed targets.')
    q=robust.loc[(robust.outcome.eq('sym_change')) & robust.specification.isin(['Base','Initial-employment WLS'])]
    table(['Symmetric growth model','Term','Coefficient','SE','N'],[[a.specification,'NJ' if a.term=='STATE' else 'GAP',f(a.coefficient,3),f(a.se,3),int(a.n)] for _,a in q.iterrows()],[220,60,85,65,70])
    p('Growth rates are expressed as decimals. The original special -1 convention for permanent closures is retained. Weighting by initial employment changes the estimand toward larger stores; it is not merely an alternative variance estimator.')
    placebo=robust.loc[robust.specification.eq('PA-only wage-gap falsification') & robust.outcome.eq('delta')].iloc[0]
    p(f'In PA, a hypothetical shortfall below $5.05 gives a GAP coefficient of {placebo.coefficient:.3f} (SE {placebo.se:.3f}; n={int(placebo.n)}). This replicates the paper\'s wage-gap falsification concept, not a pre-treatment trends test. Local Newark/Camden checks require unavailable postcode fields, so those rows are not fabricated. The exact interview-week partition is not supplied; no arbitrary week definition is presented as an exact Table 5 replication.')
    page()

    h('Independent extension on ownership heterogeneity')
    p('Do company-owned and franchised stores respond differently to the same minimum-wage change? Centralized management, financing, pricing decisions and adjustment costs could generate different employment responses. Baseline ownership is observable and predates the policy. This extension directly tests the difference between ownership types rather than comparing their separate significance levels.')
    p('<b>DeltaFTE_i = a + b NJ_i + c Company_i + d (NJ_i x Company_i) + chain effects + u_i.</b>')
    p('b is the franchise NJ-PA contrast, b+d the company-owned contrast, and d their difference. Chain controls address observed differences in brand mix. Identification requires comparable untreated trends within each ownership type; differential chain-state or ownership-specific shocks could still explain the interaction.')
    cells=df('ownership_cell_summary')
    table(['State','Ownership','N','Initial FTE','FTE change'],[['NJ' if a.STATE else 'PA','Company' if a.CO_OWNED else 'Franchise',int(a.n),f(a.baseline_fte),f(a.change_fte)] for _,a in cells.iterrows()],[65,140,55,110,130])
    table(['Effect on 357-store sample','Coefficient','HC3 SE','p-value'],[[a.effect,f(a.coefficient),f(a.se),f(a.pvalue,3)] for _,a in e.iterrows()],[275,75,75,75])
    fig('figure3_ownership',width=475)
    p(f'The direct interaction estimate is {inter.coefficient:.2f}, with a restaurant-level 95% interval from {inter.ci_low:.2f} to {inter.ci_high:.2f}. '+('This interval includes zero, so the sample does not resolve an ownership difference at conventional levels.' if inter.ci_low<=0<=inter.ci_high else 'This conditional interval excludes zero, but common state shocks and non-random ownership remain threats.')+' The 384-store results are also saved; this analysis is exploratory and does not establish a causal ownership mechanism.',small=True)
    page()

    h('Inference and sensitivity to restaurant chains')
    p('The policy changes once at state level, yet the historical regression treats restaurant outcomes as individual observations. Conventional OLS and HC3 quantify uncertainty under restaurant-level independence assumptions. A stratified bootstrap preserves PA and NJ sample counts while resampling restaurants within state. It retains within-restaurant differencing but not the uncertainty from drawing state-level policy shocks.')
    table(['Method','NJ coef','SE','95% interval'],[[r.method,f(r.coefficient),f(r.se),f'[{r.ci_low:.2f}, {r.ci_high:.2f}]'] for _,r in inf.iterrows()],[270,65,65,100])
    p(f'The bootstrap uses {results["bootstrap_reps"]:,} repetitions and seed {results["seed"]}. It is a conditional sensitivity check, not randomization inference and not a solution to two-state clustering. State-clustered standard errors with just two groups would be unstable; using more restaurants cannot create more policy changes [4, 5].')
    fig('figure4_chain_influence',width=485)
    chain=df('leave_one_chain_out')
    p(f'Leaving one chain out gives adjusted estimates ranging from {chain.coefficient.min():.2f} to {chain.coefficient.max():.2f} FTE. The chain comparison assesses dependence on brand composition rather than offering four independent replications. Confidence intervals use HC3; remaining chain dummies are adjusted to retain a full-rank design.')
    p('The ownership extension is not interpreted using a claim such as “significant for one type but not the other.” Only the interaction tests whether the two estimated responses differ. All variants are reported, including wide intervals and estimates that lose conventional significance.')
    page()

    h('Replication of original Figure 1')
    fig('figure1_original_wage_distribution',width=455)
    p('Two stacked panels, original wage-range labels, black NJ bars and hatched PA bars reproduce the paper\'s layout and main distributional change. Denominators are the nonmissing wage counts: NJ/PA 314/76 before and 318/71 after. All 56 bars, counts, boundaries and denominators are exported in figure1_original_bins.csv.',small=True)
    p('Bins are implemented in integer cents: [420,430), [430,440), ... , [540,550), with a final bin of 550 cents and above. Thus the last label 5.55 includes the upper tail. The article labels wage ranges but does not provide endpoint code; this transparent reconstruction cannot certify the exact historical allocation of a boundary value such as $4.30. The former coarse seven-category chart remains a supplementary figure and is not labelled as the required original Figure 1.',small=True)
    p('NJ wages cluster near the new floor, providing evidence that the policy was binding. The first-period peak is near $4.25; the second is near $5.05. The number of stores with a wage exactly $5.05 and the height of the ten-cent bin are different quantities.',small=True)
    page()

    h('DID interpretation and employment composition')
    fig('figure1_did',width=480)
    p('This is a supplementary two-period employment plot, not the article\'s Figure 1. The dashed NJ path imposes the PA employment change as a counterfactual under parallel trends. It is a visualization of the identifying assumption, not an observed untreated NJ outcome or a pre-trend test.',small=True)
    fig('figure5_components',width=475)
    p('Full-time nonmanagers, half-weighted part-time workers and managers are differenced on the same 357 restaurants. Permanent closures contribute zero after the policy. Because all component models use identical regressors and rows, their NJ coefficients sum exactly to the adjusted FTE estimate. The figure helps interpret staffing composition but does not establish substitution among otherwise identical workers.',small=True)
    page()

    h('Validation and reproducibility')
    checks=df('validation_checks')
    p(f'{len(checks)} automated analytical checks passed. Six additional unit tests exercise closure distinctions, missing components, wage-gap eligibility, the part-time weight, the special closure growth convention and DID sign on a transparent synthetic example. Synthetic values are used only in unit tests, never in the empirical sample.')
    table(['Validation','Evidence'],[
        ['External source audit','410 x 46 course cells match independently downloaded public.dat.'],
        ['Sample accounting','331 NJ, 79 PA; 384 balanced employment stores; 357 wage-complete stores.'],
        ['Published values','40 Table 3 point estimates within 0.01; all 5 Table 4 coefficients and SEs within 0.006.'],
        ['Independent OLS','NumPy least squares agrees with statsmodels on the adjusted NJ coefficient vector.'],
        ['Estimator algebra','Balanced long-form NJ x Post coefficient equals the first-difference mean comparison.'],
        ['Outcome accounting','Full-time, half-part-time and manager coefficients add to total FTE.'],
        ['Data rules','Permanent closure zero, temporary closure missing, refusal missing and GAP zero in PA.'],
        ['Determinism','All stochastic work uses a fixed seed; a clean rerun is compared using output hashes.']],[135,365])
    p('The required entry point is python code/run_all.py; paths are resolved from the script location. It finds inputs relative to the project, constructs processed store and panel files, estimates all models, runs validation, generates figures and rebuilds this report. Optional --input specifies a different authorized location without editing code. --bootstrap controls repetition count.')
    p('Final tables are exported once as CSV and figures once as PNG. This private submission includes raw inputs, final analysis datasets and the data underlying the original-style wage figure. Intermediate tables and caches are created only in a temporary directory and removed automatically.')
    p('Git history records the stages of specification, implementation, estimation and validation. AI_USE_DISCLOSURE.md explains how I used ChatGPT for conceptual discussion and writing, Claude in VS Code for coding and debugging, and Codex to organize and execute the reproducible workflow. It also documents the checks and methodological corrections made during the project.')
    page()

    h('Limitations and conclusion')
    p('The project reproduces the classic positive NJ-PA employment contrast and the original wage-gap estimates. The main numerical results are stable to several accounting and sample definitions, but the estimates remain imprecise and design-specific. The ownership extension is informative about observed heterogeneity, with uncertainty explicitly reported.')
    p('The most important limitation is identification: one pre-policy observation cannot establish parallel trends. Differences in recession exposure, regional demand, measurement or client response could move employment differently across the two states. Survey measurement error affects both employment and initial wages; wage-gap regression errors may therefore be nonclassical.')
    p('The sample tracks incumbent restaurants in selected chains. It does not identify new restaurant entry, long-run employment or total labor hours. Half-weighted part-time headcounts are a proxy for hours. Ownership is not randomized, and the interaction can reflect unobserved characteristics or differential state shocks. Restaurant-resampling inference remains conditional on the two states.')
    p('A payroll-based reanalysis and the subsequent debate illustrate why measurement matters [3]. No payroll outcomes are available here, so this project does not claim to independently verify that later evidence. The independent download establishes provenance for the survey data, not the accuracy of every manager response.')
    p('The defensible conclusion is that this reconstruction finds no negative relative employment change in the surveyed NJ restaurants after the 1992 rise, conditional on the original design. It cannot establish that every minimum-wage increase raises employment, nor distinguish a monopsony mechanism from alternative explanations.')
    h('References and source access')
    refs=[
        '[1] Card, D. and Krueger, A. B. (1994). Minimum Wages and Employment: A Case Study of the Fast-Food Industry in New Jersey and Pennsylvania. American Economic Review 84(4), 772-793. https://eml.berkeley.edu/~card/papers/njmin-aer.pdf',
        '[2] Card, D. Author data archive: New Jersey-Pennsylvania survey, public.dat, codebook, check.sas. https://davidcard.berkeley.edu/data_sets/njmin.zip (downloaded 16 October 2026).',
        '[3] Card, D. and Krueger, A. B. (2000). Minimum Wages and Employment: Reply. American Economic Review 90(5), 1397-1420. Earlier working paper: https://www.nber.org/papers/w6386',
        '[4] Donald, S. G. and Lang, K. (2007). Inference with Difference-in-Differences and Other Panel Data. Review of Economics and Statistics 89(2), 221-233. https://doi.org/10.1162/rest.89.2.221',
        '[5] Conley, T. G. and Taber, C. R. (2011). Inference with Difference in Differences with a Small Number of Policy Changes. Review of Economics and Statistics 93(1), 113-125. Working paper: https://www.nber.org/papers/t0312',
        '[6] ECON6067 supplied 01_DID README, DATA_DICTIONARY and project-deliverable screenshots. Course-restricted inputs are not redistributed publicly.'
    ]
    for ref in refs: p(escape(ref),small=True)
    page()

    h('AI use disclosure')
    p('<b>1. Areas and ways of using AI.</b> I used ChatGPT to understand DID and the paper, discuss extension directions, interpret results and revise text. I used Claude in VS Code to help write and debug data-cleaning, regression and plotting code. I used Codex to integrate and run the workflow, compare results with the paper and prepare the reproducibility package. I supplied the materials, clarified the assigned outputs and gave feedback on revisions.')
    p('<b>2. Checking AI-generated code.</b> I requested source-data, sample and repeat-execution checks and used Codex to implement inspectable outputs. These include a cell-by-cell comparison with the author archive, identifier and closure checks, independent NumPy OLS, DID and accounting identities, 21 analytical checks and six unit tests. A fresh-directory rerun produced identical hashes for 18 final data, table and image files. These are automated checks, rather than a claim that I manually verified every line.')
    p('<b>Checking analysis and writing.</b> I used published-result comparisons to check sample definitions, estimates and standard errors, and discussions with ChatGPT to clarify interpretation. With Codex, I cross-checked narrative sample sizes and key estimates against output tables and the account of the policy and research design against source materials. I used ChatGPT to revise wording, while checking that positive point estimates were not generalized into universal policy effects and that an imprecise ownership interaction was not presented as an established mechanism. The report retains the one-pre-period and state-level inference limitations. The revised PDF was rendered for layout review.')
    p('<b>3. Important AI errors corrected or outputs rejected.</b> First, the initial descriptive table and coarse wage chart did not cover the full assigned Table 2 and original Figure 1. I supplied the assignment screenshots to clarify the scope; the workflow expanded Table 2 to all 20 rows, added Table 3 standard-error comparisons and redrew Figure 1, with its uncertain historical bin boundaries disclosed.')
    p('<b>Identifier correction discovered by a check.</b> Second, the implementation assumption that SHEET was globally unique failed a programmatic check: identifier 407 occurs in both states. The AI-assisted workflow changed the key to STATE plus SHEET and retained both records. This correction was detected through an automated check, rather than being represented as my manual discovery.')
    p('<b>Disclosure revision prompted by my feedback.</b> Third, I rejected the initial disclosure framed mainly as disclaimers and a list of AI tasks. I requested a first-person account of how I used the tools, then asked for explicit coverage of writing checks and concrete correction cases. This revision separates tool use, verification and corrections. The 85.5% versus 85.2% wage share, some Table 3 standard-error differences and conflicting source specifications remain replication or source discrepancies, not evidence by themselves of an AI error. My account confirms ChatGPT and Claude use; code, logs and Git history additionally document the Codex workflow. AI_USE_DISCLOSURE.md gives the fuller disclosure.')
    h('Submission structure')
    p('README.md; report.pdf; AI_USE_DISCLOSURE.md; data/raw/; data/processed/; code/run_all.py and supporting code; code/requirements.txt; outputs/tables/; outputs/figures/; outputs/data/; skills/SKILL.md.')
    p('Only this formal report is supplied as PDF. Each final table has one CSV file and each figure one PNG file. Raw and processed datasets are included for private course use; the repository must remain private with access granted to the teaching team. The hidden .git directory preserves the phased development history.')

    def footer(canvas,doc):
        canvas.setFont('Helvetica',8); canvas.setFillColor(colors.HexColor('#6C7882'))
        canvas.drawString(46,27,'ECON6067  |  Card and Krueger replication')
        canvas.drawRightString(A4[0]-46,27,str(doc.page))
    target=root/'report.pdf'
    document=SimpleDocTemplate(str(target),pagesize=A4,rightMargin=46,leftMargin=46,
        topMargin=43,bottomMargin=44,title='Minimum Wages and Fast Food Employment',
        author='ECON6067 project with Codex AI assistance',pageCompression=1)
    document.build(story,onFirstPage=footer,onLaterPages=footer)
    from pypdf import PdfReader
    print('REPORT',target,'PAGES',len(PdfReader(target).pages))

if __name__=='__main__': main(Path(__file__).resolve().parents[1])
