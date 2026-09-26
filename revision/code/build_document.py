#!/usr/bin/env python3
"""Build a readable DOCX from the revised, source-linked Markdown manuscript."""
from pathlib import Path
import re
from docx import Document
from docx.shared import Inches,Pt,RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
ROOT=Path(__file__).resolve().parents[1]

def inline(p,text):
    # All links here are source descriptions, not hidden content.
    text=re.sub(r'\[([^\]]+)\]\(([^)]+)\)',r'\1',text)
    for part in re.split(r'(\*\*.*?\*\*|`[^`]+`)',text):
        if not part:continue
        run=p.add_run(part[2:-2] if part.startswith('**') else part[1:-1] if part.startswith('`') else part)
        if part.startswith('**'):run.bold=True
        if part.startswith('`'):run.font.name='Liberation Mono';run.font.size=Pt(8.5)

def table(doc,rows):
    cells=[[x.strip() for x in r.strip().strip('|').split('|')] for r in rows]
    cells=[r for r in cells if not all(re.fullmatch(r':?-+:?',x.replace(' ','')) for x in r)]
    t=doc.add_table(rows=1,cols=len(cells[0]));t.style='Light Shading Accent 1';t.autofit=True
    for i,h in enumerate(cells[0]):inline(t.rows[0].cells[i].paragraphs[0],h)
    props=t.rows[0]._tr.get_or_add_trPr();repeat=OxmlElement('w:tblHeader');props.append(repeat)
    for row in cells[1:]:
        c=t.add_row().cells
        for i,text in enumerate(row):inline(c[i].paragraphs[0],text)
    for row in t.rows:
        props=row._tr.get_or_add_trPr();no=OxmlElement('w:cantSplit');props.append(no)
        for cell in row.cells:
            for p in cell.paragraphs:
                p.paragraph_format.space_after=Pt(3);p.paragraph_format.space_before=Pt(3)
                for r in p.runs:r.font.size=Pt(8.5)
    doc.add_paragraph().paragraph_format.space_after=Pt(1)

def build():
    src=ROOT/'manuscript/DDR_TargetBridge_Revised_Case_Study.md'
    doc=Document();s=doc.sections[0];s.page_width=Inches(8.5);s.page_height=Inches(11)
    s.top_margin=Inches(.65);s.bottom_margin=Inches(.65);s.left_margin=Inches(.70);s.right_margin=Inches(.70)
    s.header_distance=Inches(.25);s.footer_distance=Inches(.28)
    st=doc.styles['Normal'];st.font.name='Liberation Sans';st.font.size=Pt(10.5)
    st.paragraph_format.line_spacing=1.06;st.paragraph_format.space_after=Pt(7)
    for name,size in [('Title',22),('Heading 1',17),('Heading 2',14),('Heading 3',12)]:
        st=doc.styles[name];st.font.name='Liberation Sans';st.font.size=Pt(size);st.font.color.rgb=RGBColor.from_string('1E4157')
        st.paragraph_format.keep_with_next=True;st.paragraph_format.space_after=Pt(8)
    h=s.header.paragraphs[0];h.text='DDR TARGETBRIDGE  |  REVISED COMPUTATIONAL CASE STUDY';h.style='Caption'
    for r in h.runs:r.font.size=Pt(8);r.font.color.rgb=RGBColor.from_string('596673')
    footer=s.footer.paragraphs[0];footer.alignment=WD_ALIGN_PARAGRAPH.RIGHT
    footer.add_run('Revision 2 · 22 September 2026  |  ')
    field=OxmlElement('w:fldSimple');field.set(qn('w:instr'),'PAGE');footer._p.append(field)
    for r in footer.runs:r.font.size=Pt(8)
    lines=src.read_text().splitlines();i=0
    while i<len(lines):
        line=lines[i].strip()
        if not line:i+=1;continue
        if line=='<!-- PAGEBREAK -->':doc.add_page_break();i+=1;continue
        if line.startswith('|'):
            rr=[]
            while i<len(lines) and lines[i].strip().startswith('|'):rr.append(lines[i]);i+=1
            table(doc,rr);continue
        image=re.match(r'!\[([^\]]*)\]\(([^)]+)\)',line)
        if image:
            f=(src.parent/image.group(2)).resolve();p=doc.add_paragraph();p.alignment=WD_ALIGN_PARAGRAPH.CENTER
            # Sample panels are shown together on one page, at the same scale.
            width=6.7 if f.name.startswith('F3') else 6.7
            p.add_run().add_picture(str(f),width=Inches(width));p.paragraph_format.space_after=Pt(5)
            for blip in p._p.xpath('.//wp:docPr'):blip.set('descr',image.group(1))
            i+=1;continue
        if line.startswith('# '):p=doc.add_paragraph(style='Title');inline(p,line[2:]);i+=1;continue
        if line.startswith('## '):p=doc.add_paragraph(style='Heading 1');inline(p,line[3:]);i+=1;continue
        if line.startswith('### '):p=doc.add_paragraph(style='Heading 2');inline(p,line[4:]);i+=1;continue
        para=[line];i+=1
        while i<len(lines) and lines[i].strip() and not lines[i].strip().startswith(('#','|','![','<!--')):
            para.append(lines[i].strip());i+=1
        text=' '.join(para);p=doc.add_paragraph();inline(p,text)
        if text.startswith('**Figure'):
            p.paragraph_format.space_after=Pt(8)
            for r in p.runs:r.font.size=Pt(8.5)
    doc.core_properties.title='Comparator selection changes a pathway contrast in a DNA-PK inhibitor screen'
    doc.core_properties.subject='Revised public-data computational functional-genomics case study'
    doc.core_properties.author='';doc.core_properties.last_modified_by='';doc.core_properties.comments=''
    out=src.with_suffix('.docx');doc.save(out);print(out)
if __name__=='__main__':build()
