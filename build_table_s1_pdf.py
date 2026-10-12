"""Independent PDF layout from the verified S1 CSV; not a DOCX renderer."""
from pathlib import Path
import argparse,csv,hashlib,json,re
from xml.sax.saxutils import escape
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,LongTable,TableStyle
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER,TA_LEFT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.pagesizes import letter
from pypdf import PdfReader
from docx import Document

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--directory',type=Path,required=True);args=ap.parse_args();out=args.directory
    src=out/'Supplementary_Table_S1_full_precision.csv'
    with src.open(encoding='utf-8-sig',newline='') as f:rows=list(csv.DictReader(f))
    assert len(rows)==64 and all(r['series']=='NEW_D1' for r in rows)
    for name,file in [('TNR','times.ttf'),('TNR-Bold','timesbd.ttf'),('TNR-Italic','timesi.ttf')]:
        pdfmetrics.registerFont(TTFont(name,str(Path('C:/Windows/Fonts')/file)))
    pdfmetrics.registerFontFamily('TNR',normal='TNR',bold='TNR-Bold',italic='TNR-Italic',boldItalic='TNR-Bold')
    styles={
      'title':ParagraphStyle('title',fontName='TNR-Bold',fontSize=13,leading=16,spaceAfter=5),
      'body':ParagraphStyle('body',fontName='TNR',fontSize=10.5,leading=12.8,spaceAfter=5),
      'note':ParagraphStyle('note',fontName='TNR',fontSize=9.5,leading=11.7,spaceAfter=5,keepTogether=True),
      'cell':ParagraphStyle('cell',fontName='TNR',fontSize=9.5,leading=11,alignment=TA_CENTER),
      'left':ParagraphStyle('left',fontName='TNR',fontSize=9.5,leading=11,alignment=TA_LEFT),
      'head':ParagraphStyle('head',fontName='TNR-Bold',fontSize=9.5,leading=11,alignment=TA_CENTER)}
    # Use already-approved wording; PDF data are read solely from the verified CSV.
    table_docx=out/'Supplementary_Table_S1.docx'
    if not table_docx.exists():table_docx=out/'editable_sources/Supplementary_Table_S1.docx'
    doc=Document(table_docx)
    paragraphs=[p.text for p in doc.paragraphs if p.text]
    note_index=paragraphs.index('Table notes')
    intro=paragraphs[1:note_index];notes=paragraphs[note_index+1:]
    story=[Paragraph('Supplementary Table S1',styles['title'])]
    for p in intro:story.append(Paragraph(escape(p),styles['body']))
    heads=['Sample','BSDF','Wavelength<br/>(nm)','System<br/><i>Q</i><sub size="7" rise="2">CD, sys</sub>',
      'Reference<br/><i>Q</i><sub size="7" rise="2">CD, ref</sub>','Signed relative<br/>discrepancy (%)','Low<br/>signal']
    cells=[[Paragraph(h,styles['head']) for h in heads]]
    for row in rows:
        values=[row['Sample'],row['BSDF type'],row['Wavelength (nm)'],
          format(float(row['System integral Q_CD_sys']),'.8g'),format(float(row['Reference integral Q_CD_ref']),'.8g'),
          f"{float(row['Signed relative discrepancy (%)']):+.4f}",row['Low-signal flag']]
        cells.append([Paragraph(escape(str(v)),styles['left' if i==0 else 'cell']) for i,v in enumerate(values)])
    table=LongTable(cells,colWidths=[70,38,68,80,80,120,48],repeatRows=1,hAlign='CENTER')
    table.setStyle(TableStyle([
      ('BACKGROUND',(0,0),(-1,0),colors.HexColor('#E8E8E8')),
      ('GRID',(0,0),(-1,-1),.35,colors.HexColor('#D9D9D9')),
      ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
      ('LEFTPADDING',(0,0),(-1,-1),5),('RIGHTPADDING',(0,0),(-1,-1),5),
      ('TOPPADDING',(0,0),(-1,-1),2),('BOTTOMPADDING',(0,0),(-1,-1),2),
      ('TOPPADDING',(0,0),(-1,0),4),('BOTTOMPADDING',(0,0),(-1,0),6)]))
    story.extend([table,Spacer(1,8),Paragraph('<b>Table notes</b>',styles['body'])])
    for n in notes:story.append(Paragraph(escape(n),styles['note']))
    # Plain text extraction from DOCX has flattened simple subscript runs; replace in PDF notes.
    for obj in story:
        if isinstance(obj,Paragraph) and obj.style.name=='note':
            text=obj.text
            text=re.sub(r'QCD, sys',r'<i>Q</i><sub size="7" rise="2">CD, sys</sub>',text)
            text=re.sub(r'QCD, ref',r'<i>Q</i><sub size="7" rise="2">CD, ref</sub>',text)
            obj.__init__(text,obj.style)
    def footer(canvas,document):
        canvas.setFont('TNR',8);canvas.drawCentredString(306,25,f'Supplementary Table S1 · NEW_D1 · {document.page}')
    pdf=out/'Supplementary_Table_S1.pdf'
    SimpleDocTemplate(str(pdf),pagesize=letter,leftMargin=36,rightMargin=36,topMargin=40,bottomMargin=42,
      title='Supplementary Table S1',author='').build(story,onFirstPage=footer,onLaterPages=footer)
    rd=PdfReader(pdf);txt='\n'.join(p.extract_text() or '' for p in rd.pages)
    # Repeated sample/wavelength keys appear once for each row; check PDF tokens against all displayed signed discrepancies.
    for row in rows:
        v=f"{float(row['Signed relative discrepancy (%)']):+.4f}"
        assert v in txt,(row['case_id'],v)
    check={'renderer':'Independent ReportLab PDF from full-precision CSV','pages':len(rd.pages),
      'source_csv_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'pdf_sha256':hashlib.sha256(pdf.read_bytes()).hexdigest(),
      'displayed_signed_discrepancies_all_present':True,'docx_render_verified':False,
      'data_rows':64,'layout_verified':False}
    (out/'pdf_layout_checks.json').write_text(json.dumps(check,indent=2),encoding='utf-8')
    print(json.dumps(check,indent=2))

if __name__=='__main__':main()

