"""Export frozen common-domain integrals; never recompute BSDF maps.

Python requirements: python-docx. Only standard-library CSV/numerical processing.
Default output is NEW_D1, explicitly selected for the supplementary publication table.
"""
from pathlib import Path
import argparse, csv, hashlib, json, math, shutil, re
from datetime import datetime, timezone
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SOURCE = ROOT/'batch_integral_recompute/runs/zero_incidence_v1_2/integrals_64cases.csv'
DEFAULT_AGGREGATES = DEFAULT_SOURCE.with_name('aggregate_summary.csv')
DEFAULT_FLAGS = ROOT/'route2_paired_BSDF_data/sample_channel_quality_flags.csv'
SAMPLES = ['red','green','yellow','blue','4','5','6','7']
CHANNELS = [430,460,490,520,550,590,630,660]
LABELS = {'red':'Red tile','green':'Green tile','yellow':'Yellow tile','blue':'Blue tile',
          '4':'PMMA 4','5':'PMMA 5','6':'PMMA 6','7':'PMMA 7'}

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def load(path):
    with path.open(encoding='utf-8-sig',newline='') as f: return list(csv.DictReader(f))
def save_csv(path,rows):
    with path.open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
def elem(tag,attrs):
    e=OxmlElement(tag)
    for k,v in attrs.items():e.set(qn(k),str(v))
    return e
def q_text(p,prefix='',sub='CD, sys',suffix=''):
    p.add_run(prefix)
    r=p.add_run('Q');r.italic=True
    r=p.add_run(sub);r.font.subscript=True
    p.add_run(suffix)
def notation_text(p,text):
    for part in re.split('(Q_CD,sys|Q_CD,ref)',text):
        if part in ['Q_CD,sys','Q_CD,ref']:q_text(p,sub=part[2:].replace(',',', '))
        else:p.add_run(part)
def table_style(t):
    t.alignment=WD_TABLE_ALIGNMENT.CENTER;t.autofit=False
    props=t._tbl.tblPr
    borders=OxmlElement('w:tblBorders')
    for name in ['top','left','bottom','right','insideH','insideV']:
        borders.append(elem('w:'+name,{'w:val':'single','w:sz':4,'w:color':'D9D9D9'}))
    props.append(borders)
    margins=OxmlElement('w:tblCellMar')
    for side in ['top','bottom']:margins.append(elem('w:'+side,{'w:w':48,'w:type':'dxa'}))
    for side in ['left','right']:margins.append(elem('w:'+side,{'w:w':75,'w:type':'dxa'}))
    props.append(margins)

def make_docx(rows,series,aggs,path):
    d=Document();sec=d.sections[0]
    sec.page_width=Inches(8.5);sec.page_height=Inches(11)
    sec.top_margin=sec.bottom_margin=Inches(.65)
    sec.left_margin=sec.right_margin=Inches(.6)
    for name in ['Normal','Title','Heading 1','Heading 2']:
        st=d.styles[name];st.font.name='Times New Roman';st.font.color.rgb=RGBColor(0,0,0)
    normal=d.styles['Normal'];normal.font.size=Pt(10.5)
    normal.paragraph_format.space_after=Pt(5)
    normal.paragraph_format.line_spacing=1.05
    title=d.add_paragraph('Supplementary Table S1',style='Title')
    title.paragraph_format.space_after=Pt(4)
    for r in title.runs:r.font.size=Pt(13);r.bold=True
    p=d.add_paragraph('Common-domain integrated BSDF results for the validation samples across eight spectral channels.')
    p.paragraph_format.keep_with_next=True
    p=d.add_paragraph(f'Data series {series}. Normal incidence; four BRDF tiles and four BTDF PMMA samples. All integrals are dimensionless. ' +
        ('NEW_D1 processed data.' if series=='NEW_D1' else 'Original signed system data on the original shared valid domain.'))
    p.paragraph_format.keep_with_next=True
    t=d.add_table(rows=1,cols=7);table_style(t)
    widths=[1.0,.52,.7,1.12,1.12,1.87,.77]
    for col,w in zip(t.columns,widths):col.width=Inches(w)
    heads=['Sample','BSDF','Wavelength\n(nm)',None,None,'Signed relative\ndiscrepancy (%)','Low signal']
    for i,c in enumerate(t.rows[0].cells):
        c.width=Inches(widths[i]);p=c.paragraphs[0]
        if i in [3,4]:q_text(p,'System\n' if i==3 else 'Reference\n','CD, sys' if i==3 else 'CD, ref')
        else:p.add_run(heads[i])
        c._tc.get_or_add_tcPr().append(elem('w:shd',{'w:fill':'E8E8E8'}))
        for r in p.runs:r.bold=True
    t.rows[0]._tr.get_or_add_trPr().append(elem('w:tblHeader',{'w:val':'true'}))
    for row in rows:
        cells=t.add_row().cells
        values=[row['Sample'],row['BSDF type'],row['Wavelength (nm)'],
                format(float(row['System integral Q_CD_sys']),'.8g'),format(float(row['Reference integral Q_CD_ref']),'.8g'),
                f"{float(row['Signed relative discrepancy (%)']):+.4f}",row['Low-signal flag']]
        for i,(c,v) in enumerate(zip(cells,values)):
            c.width=Inches(widths[i]);c.paragraphs[0].add_run(str(v))
        t.rows[-1]._tr.get_or_add_trPr().append(elem('w:cantSplit',{}))
    for row in t.rows:
        for i,c in enumerate(row.cells):
            c.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER
            for p in c.paragraphs:
                p.alignment=WD_ALIGN_PARAGRAPH.LEFT if i==0 else WD_ALIGN_PARAGRAPH.CENTER
                p.paragraph_format.space_after=Pt(0);p.paragraph_format.space_before=Pt(0)
                p.paragraph_format.line_spacing=1.05
                for r in p.runs:r.font.size=Pt(9.5)
    p=d.add_paragraph('Table notes');p.runs[0].bold=True;p.paragraph_format.space_before=Pt(7)
    notes=[
      'The integration uses the same sample–channel validity mask for the system and reference within 10° ≤ θ ≤ 70°, with cos(θ) dΩ weights. No normalization to a full hemisphere is applied. The reference azimuthal distribution is reconstructed from principal-plane scans under the normal-incidence rotational-symmetry approximation for diffuse samples.',
      'The signed relative discrepancy in each row is 100 × (Q_CD,sys / Q_CD,ref − 1). Positive values indicate a larger system integral. The source permits this ratio only when |Q_CD,ref| > 10⁻¹²; all 64 rows meet that criterion. Signed system integrals, including negative low-signal estimates, are retained.',
      'The signal-weighted absolute discrepancy for any group is E = 100 × Σ|Q_CD,sys − Q_CD,ref| / Σ|Q_CD,ref|. It is not the arithmetic mean of the signed row percentages. All cases, including the low-signal flags, enter these sums. '+f"BRDF: {aggs['BRDF']['E_pct']:.2f}% (32 cases); BTDF: {aggs['BTDF']['E_pct']:.2f}% (32 cases); aggregate: {aggs['all']['E_pct']:.2f}% (64 cases).",
      '“Yes” marks the six prior low-signal cases. Cells below the earlier 20.5 DN criterion account for at least 50% of the original-domain cos(θ) dΩ weight. All flagged cases enter the aggregate calculations.',
      'The system common-domain integrals are reported after denoising and other data processing (NEW_D1 processed data), alongside the reference integrals. Full-precision values, low-signal flags and source hashes accompany the table in CSV and README files.'
    ]
    for n in notes:
        p=d.add_paragraph();notation_text(p,n)
        for r in p.runs:r.font.size=Pt(9.5)
    footer=sec.footer.paragraphs[0];footer.alignment=WD_ALIGN_PARAGRAPH.CENTER
    footer.add_run('Supplementary Table S1 · '+series+' · ')
    footer._p.append(elem('w:fldSimple',{'w:instr':'PAGE'}))
    for r in footer.runs:r.font.size=Pt(8)
    d.save(path)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--source',type=Path,default=DEFAULT_SOURCE)
    ap.add_argument('--aggregates',type=Path,default=DEFAULT_AGGREGATES)
    ap.add_argument('--flags',type=Path,default=DEFAULT_FLAGS)
    ap.add_argument('--series',choices=['BASE_D0','NEW_D1'],default='NEW_D1')
    ap.add_argument('--output-dir',type=Path,required=True);args=ap.parse_args()
    out=args.output_dir;out.mkdir(parents=True,exist_ok=True)
    data=load(args.source);flags=load(args.flags);aggregates=load(args.aggregates)
    selected=[r for r in data if r['series']==args.series]
    keys=lambda r:(r['sample'],r['geometry'],int(r['wavelength_nm']))
    assert len(selected)==64 and len(set(map(keys,selected)))==64
    assert {(r['sample'],int(r['wavelength_nm'])) for r in selected}=={(s,w) for s in SAMPLES for w in CHANNELS}
    q={keys(r):r for r in flags};assert len(q)==len(flags)==64
    selected.sort(key=lambda r:(SAMPLES.index(r['sample']),int(r['wavelength_nm'])))
    rows=[];max_relative_diff=0;low_cases=[]
    for r in selected:
        assert r['status']=='COMPLETE' and r['relative_status']=='PASS' and int(r['incident_deg'])==0
        x=float(r['I_sys']);g=float(r['I_GT']);assert math.isfinite(x) and math.isfinite(g) and abs(g)>1e-12
        rel=100*(x/g-1);max_relative_diff=max(max_relative_diff,abs(rel-float(r['signed_relative_pct'])))
        f=q[keys(r)];frac=float(f['weighted_fraction_below_prior_20_5DN_criterion'])
        low=f['signal_quality_description']=='most_cells_below_prior_signal_criterion';assert low==(frac>=.5)
        assert float(r['weighted_fraction_below_prior_20_5DN_criterion'])==frac
        if low:low_cases.append(r['case_id'])
        rows.append({'Sample':LABELS[r['sample']],'BSDF type':r['geometry'],'Wavelength (nm)':r['wavelength_nm'],
          'System integral Q_CD_sys':r['I_sys'],'Reference integral Q_CD_ref':r['I_GT'],
          'Signed relative discrepancy (%)':r['signed_relative_pct'],'Low-signal flag':'Yes' if low else 'No',
          'series':r['series'],'case_id':r['case_id'],'sample_id':r['sample'],
          'weighted_fraction_below_prior_20_5DN_criterion':f['weighted_fraction_below_prior_20_5DN_criterion'],
          'signal_quality_description':f['signal_quality_description'],'processing_QA':r['processing_QA'],
          'processing_policy':r['processing_policy'],'target_GT_used_in_values':r['target_GT_used_in_values'],
          'domain_cells':r['domain_cells'],'D0_cells':r['D0_cells'],'added_cells':r['added_cells']})
    assert max_relative_diff<=1e-10 and len(low_cases)==6
    computed={};max_aggregate_difference=0
    for group in ['BRDF','BTDF','all']:
        rs=[r for r in selected if group=='all' or r['geometry']==group]
        num=sum(abs(float(r['I_sys'])-float(r['I_GT'])) for r in rs)
        den=sum(abs(float(r['I_GT'])) for r in rs);e=100*num/den
        orig=next(a for a in aggregates if a['series']==args.series and a['group']==group)
        delta=abs(e-float(orig['E_pct']));max_aggregate_difference=max(delta,max_aggregate_difference)
        assert delta<=1e-9
        computed[group]={'n':len(rs),'numerator':num,'denominator':den,'E_pct':e,'source_E_pct':float(orig['E_pct']),'difference_pp':delta}
    csvpath=out/'Supplementary_Table_S1_full_precision.csv';save_csv(csvpath,rows)
    recovered=load(csvpath);assert recovered==rows
    save_csv(out/'Supplementary_Table_S1_source_rows.csv',selected)
    save_csv(out/'Supplementary_Table_S1_aggregate_results.csv',[dict(series=args.series,group=k,**v) for k,v in computed.items()])
    save_csv(out/'data_series_comparison.csv',[a for a in aggregates if a['series'] in ['BASE_D0','NEW_D1']])
    inputs=out/'source_inputs';inputs.mkdir(exist_ok=True)
    for src in [args.source,args.aggregates,args.flags]:shutil.copy2(src,inputs/src.name)
    make_docx(rows,args.series,computed,out/'Supplementary_Table_S1.docx')
    checks={'series':args.series,'rows':64,'unique_sample_channel_keys':64,'complete_8_by_8_grid':True,
      'all_source_values_preserved_as_csv_strings':True,'full_precision_csv_roundtrip_exact':True,
      'max_per_case_signed_relative_difference_pp':max_relative_diff,'per_case_tolerance_pp':1e-10,
      'max_aggregate_difference_pp':max_aggregate_difference,'aggregate_tolerance_pp':1e-9,
      'low_signal_case_count':len(low_cases),'low_signal_case_ids':low_cases,
      'negative_system_integrals':sum(float(r['I_sys'])<0 for r in selected),'aggregates':computed,
      'sources':[{ 'path':str(p),'sha256':sha(p)} for p in [args.source,args.aggregates,args.flags]],
      'script_sha256':sha(Path(__file__)),'built_utc':datetime.now(timezone.utc).isoformat()}
    (out/'reproduction_checks.json').write_text(json.dumps(checks,indent=2),encoding='utf-8')
    readme=f'''# Supplementary Table S1

NEW_D1 processed data for64normal-incidence sample-channel combinations. System and rotationally reconstructed reference Q_CD integrals use identical masks within10–70 degrees and cos(theta)dOmega weights. Signed per-row discrepancy=100*(Qsys/Qref-1); group discrepancy=100*sum(abs(Qsys-Qref))/sum(abs(Qref)). BRDF={computed['BRDF']['E_pct']:.2f}%, BTDF={computed['BTDF']['E_pct']:.2f}%, all={computed['all']['E_pct']:.2f}%. Full-precision CSV, prior low-signal flags, source identifiers and hashes accompany the table.'''
    (out/'README.md').write_text(readme,encoding='utf-8')
    if Path(__file__).resolve()!= (out/'build_table_s1.py').resolve():shutil.copy2(__file__,out/'build_table_s1.py')
    print(json.dumps({k:checks[k] for k in ['series','rows','low_signal_case_count','negative_system_integrals','max_aggregate_difference_pp','aggregates']},indent=2))

if __name__=='__main__':main()
