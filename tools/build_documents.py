#!/usr/bin/env python3
"""Build plain research documents and an editable deck from released material.

This generates presentation files only. It never changes a scientific input or
runs a new analysis. PDF conversion is a separate, documented LibreOffice step.
"""
from __future__ import annotations
import argparse
import json
import re
from pathlib import Path
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.enum.text import WD_ALIGN_PARAGRAPH
from pptx import Presentation
from pptx.util import Inches as SI, Pt as SP
from pptx.dml.color import RGBColor as SC

ROOT=Path(__file__).resolve().parents[1]


def inline(paragraph, text, size=None):
    """Lightweight readable Markdown inline rendering; exact text remains in .md."""
    text=re.sub(r'\[([^\]]+)\]\(([^)]+)\)',r'\1',text)
    for part in re.split(r'(\*\*.*?\*\*|`[^`]+`|(?<!\*)\*[^*]+\*(?!\*))',text):
        if not part:continue
        bold=part.startswith('**') and part.endswith('**')
        code=part.startswith('`') and part.endswith('`')
        italic=not bold and part.startswith('*') and part.endswith('*')
        value=part[2:-2] if bold else part[1:-1] if code or italic else part
        run=paragraph.add_run(value);run.bold=bold;run.italic=italic
        if size:run.font.size=Pt(size)
        if code:run.font.name='DejaVu Sans Mono';run.font.size=Pt(8.2 if size is None else min(size,8.2))


def setup(title,brief=False):
    doc=Document();sec=doc.sections[0]
    sec.page_width=Inches(8.27);sec.page_height=Inches(11.69)
    sec.left_margin=sec.right_margin=Inches(.85)
    sec.top_margin=Inches(.73);sec.bottom_margin=Inches(.68)
    sec.header_distance=Inches(.27);sec.footer_distance=Inches(.30)
    for key in ['Normal','Body Text']:
        style=doc.styles[key];style.font.name='Liberation Serif';style.font.size=Pt(10.5 if brief else 10.8)
        style.paragraph_format.line_spacing=1.08
        style.paragraph_format.space_after=Pt(5)
        style.paragraph_format.keep_together=True
    for key,size in [('Title',22 if not brief else 24),('Heading 1',13.5),('Heading 2',11.5),('Heading 3',11)]:
        style=doc.styles[key];style.font.name='DejaVu Sans';style.font.size=Pt(size)
        style.font.color.rgb=RGBColor(20,20,20)
        style.paragraph_format.space_before=Pt(9);style.paragraph_format.space_after=Pt(5)
        style.paragraph_format.keep_with_next=True
    for style in doc.styles:
        for border in list(style._element.iter(qn('w:pBdr'))):border.getparent().remove(border)
    cap=doc.styles['Caption'];cap.font.name='DejaVu Sans';cap.font.size=Pt(8)
    cap.font.color.rgb=RGBColor(45,45,45);cap.paragraph_format.line_spacing=1.04
    cap.paragraph_format.space_after=Pt(8);cap.paragraph_format.keep_together=True
    hp=sec.header.paragraphs[0];hp.text='DDR TargetBridge · Public-data research case study'
    hp.style=doc.styles['Caption']
    fp=sec.footer.paragraphs[0];fp.alignment=WD_ALIGN_PARAGRAPH.RIGHT
    run=fp.add_run('Public edition 1.0.1  |  ');run.font.name='DejaVu Sans';run.font.size=Pt(8)
    field=OxmlElement('w:fldSimple');field.set(qn('w:instr'),'PAGE');fp._p.append(field)
    doc.core_properties.title=title;doc.core_properties.author='';doc.core_properties.last_modified_by=''
    doc.core_properties.subject='Computational functional-genomics case study'
    doc.core_properties.comments='';doc.core_properties.keywords='';doc.core_properties.revision=1
    return doc


def add_table(doc,lines):
    rows=[[c.strip() for c in line.strip().strip('|').split('|')] for line in lines]
    rows=[row for row in rows if not all(re.fullmatch(r':?-+:?',cell or '-') for cell in row)]
    table=doc.add_table(rows=0,cols=len(rows[0]));table.autofit=True
    for i,row in enumerate(rows):
        cells=table.add_row().cells
        for j,value in enumerate(row):
            p=cells[j].paragraphs[0];inline(p,value,8.5)
            for run in p.runs:
                run.font.name='DejaVu Sans';run.bold=i==0
            p.paragraph_format.space_before=Pt(3);p.paragraph_format.space_after=Pt(3)
            p.paragraph_format.line_spacing=1.04
        prop=table.rows[-1]._tr.get_or_add_trPr();prop.append(OxmlElement('w:cantSplit'))
        if i==0:prop.append(OxmlElement('w:tblHeader'))
    # Short tables stay together; their exact row order is not changed.
    for row in table.rows[:-1]:
        for cell in row.cells:
            for paragraph in cell.paragraphs:paragraph.paragraph_format.keep_with_next=True
    # A restrained top/header/bottom rule, rather than a colored spreadsheet.
    pr=table._tbl.tblPr;borders=OxmlElement('w:tblBorders')
    for name in ['top','bottom']:
        edge=OxmlElement('w:'+name);edge.set(qn('w:val'),'single');edge.set(qn('w:sz'),'6');borders.append(edge)
    pr.append(borders)
    doc.add_paragraph().paragraph_format.space_after=Pt(0)


def markdown_document(source: Path, output: Path,brief=False):
    lines=source.read_text(encoding='utf-8').splitlines()
    doc=setup(lines[0].lstrip('# '),brief)
    i=0;in_code=False;in_references=False
    while i<len(lines):
        text=lines[i].strip();i+=1
        if not text or text=='<!-- PAGEBREAK -->':continue
        if text.startswith('```'):in_code=not in_code;continue
        if in_code:
            p=doc.add_paragraph();run=p.add_run(text);run.font.name='DejaVu Sans Mono';run.font.size=Pt(8.2);continue
        if text.startswith('|'):
            block=[text]
            while i<len(lines) and lines[i].lstrip().startswith('|'):block.append(lines[i]);i+=1
            add_table(doc,block);continue
        image=re.fullmatch(r'!\[([^\]]*)\]\(([^)]+)\)',text)
        if image:
            path=(source.parent/image.group(2)).resolve()
            if not path.is_relative_to(ROOT) or not path.is_file():raise ValueError('Unresolved image: '+text)
            p=doc.add_paragraph();p.paragraph_format.keep_with_next=True;p.paragraph_format.keep_together=True
            p.paragraph_format.space_after=Pt(3)
            shape=p.add_run().add_picture(str(path),width=Inches(6.1))
            shape._inline.docPr.set('descr',image.group(1))
            continue
        if text.startswith('# '):
            p=doc.add_paragraph(style='Title');inline(p,text[2:]);continue
        if text.startswith('### '):
            p=doc.add_paragraph(style='Heading 2');inline(p,text[4:]);continue
        if text.startswith('## '):
            p=doc.add_paragraph(style='Heading 1');inline(p,text[3:]);in_references=text[3:]=='References';continue
        p=doc.add_paragraph(style='Caption' if text.startswith('**Figure') else 'Normal')
        inline(p,text)
        if in_references:
            p.paragraph_format.line_spacing=1.0;p.paragraph_format.space_after=Pt(4)
            for run in p.runs:run.font.size=Pt(9.5)
    doc.save(output)


def deck(output: Path):
    prs=Presentation();prs.slide_width=SI(13.333);prs.slide_height=SI(7.5)
    notes=[]
    def text(slide,x,y,w,h,value,size=23,bold=False):
        shape=slide.shapes.add_textbox(SI(x),SI(y),SI(w),SI(h));tf=shape.text_frame;tf.word_wrap=True
        tf.margin_left=tf.margin_right=0;tf.margin_top=tf.margin_bottom=0
        for i,line in enumerate(value.split('\n')):
            p=tf.paragraphs[0] if i==0 else tf.add_paragraph();p.text=line
            p.font.name='DejaVu Sans';p.font.size=SP(size);p.font.bold=bold;p.font.color.rgb=SC(20,20,20)
            p.space_after=SP(12)
        return shape
    def slide(title,note):
        s=prs.slides.add_slide(prs.slide_layouts[6]);text(s,.65,.45,12.1,.7,title,30,True)
        text(s,.65,7.04,11.7,.20,'DDR TargetBridge · Computational functional-genomics case study',10)
        text(s,12.1,7.04,.45,.2,str(len(prs.slides)),10)
        s.notes_slide.notes_text_frame.text=note;notes.append(note);return s
    def picture(s,name,y=1.55,w=8.4,x=.65):s.shapes.add_picture(str(ROOT/'figures'/name),SI(x),SI(y),width=SI(w))
    s=slide('When the comparator population changes',
        '研究的是一个通路比较的对象组成，不是宣称发现新靶点。原实验不是本人完成；本项目是AI辅助二次分析。')
    text(s,.85,1.65,11.5,1.25,'Does a pathway priority survive a change in which perturbations are analyzed?',33,True)
    text(s,.85,3.3,11.5,2.5,'Public A549 WT / PRDX1-KO × vehicle / AZD7648 screen\nFixed mitochondrial and translation-elongation sets\nFinding: the comparator changes; the mitochondrial component is nearly stable.',25)
    s=slide('One experiment; three analysis populations',
        '16条是真实样本记录，不是16个独立建系。S1固定原基因，只扩展靶向单位；S2再扩展基因。双guide构建体仍是一种试剂。')
    text(s,.85,1.55,11.5,1.05,'16 sample records: four endpoint groups × 3, plus two T0 records per background.',27)
    text(s,.85,3.0,11.5,2.8,'S0   Original genes and targeting units                 M 89 / E 23\nS1   Same genes; expanded targeting units            M 89 / E 23\nS2   All T0-qualified support                                M 94 / E 91',24)
    text(s,.85,6.15,11.5,.48,'M: Mitochondrial translation. E: Eukaryotic Translation Elongation.',18)
    s=slide('The comparator component changes',
        '显示两种变换。横轴不是时间。M基本不变，E随着支持集合变化。没有置信区间；不能称为线粒体机制反转。')
    picture(s,'01_components.png',1.45,8.6)
    text(s,9.55,2.1,3.0,3.4,'M is nearly stable.\nE increases with restored support.\nBoth transforms show this pattern.',23)
    s=slide('Added comparator genes shift the mixture',
        '每个点是基因，不是培养重复。全体23个原成员和68个新增成员均展示。均值线不是误差条。这是混合分解，不是候选靶点筛选。')
    picture(s,'02_comparator_members.png',1.45,8.6)
    text(s,9.55,2.1,3.0,3.4,'Zero-only means\n23 retained: +0.567\n68 added: +3.574\nAll members retained in the display.',22)
    s=slide('More coverage is not automatically better evidence',
        '四组完整展示。扩展E有97构建体乘3样本=291项。新增覆盖与低计数同时变化，所以S2不能叫纠正后的真值。')
    picture(s,'03_count_floor.png',1.45,8.6)
    text(s,9.55,2.15,3.0,3.45,'Qualification uses vehicle.\nThe response subtracts vehicle.\nCoverage, growth and count floors remain entangled.',22)
    s=slide('A finite conclusion, not a target mechanism',
        '决策不升级这一项特异性主张。两种不同总体的描述不等于同一个生物学效应的独立重复。旧失败命题不被改写。')
    text(s,.85,1.55,11.6,1.8,'The original positive M − E contrast does not provide a membership-insensitive basis for a mitochondrial-specific priority.',30,True)
    text(s,.85,3.9,11.6,2.5,'The expanded negative contrast is not biological truth.\nClone, growth and perturbation-specific effects are not isolated.\nEarlier unsuccessful comparisons remain separate case histories.',23)
    s=slide('Contribution and reproducible scope',
        '本人责任应实事求是。项目提供具体比较、分解和可运行记录；标准统计及母研究实验不是本人的新方法或新湿实验。当前公开core从派生观测开始，不是原始counts。')
    text(s,.85,1.55,11.5,2.3,'Project: fixed comparisons, component decomposition, source-linked code.\nOriginal investigators: laboratory experiments and published mechanisms.\nAI assistance: discussion, implementation, testing, figures and writing.',23)
    text(s,.85,4.55,11.5,1.35,'Public core: transformed gene/sample records → pathway summaries → six comparisons.\nHistorical source tables require separate retrieval.',23,True)
    s=slide('Backup: the quantity being compared',
        '所有量是相对log丰度的描述。共同中心在同一样本的M-E中抵消，不会抵消基因特异误差、计数下限或成员选择。三组S0-S2非独立实验。')
    text(s,.85,1.55,11.5,2.3,'β(P, b) = mean drug(P, b) − mean vehicle(P, b)\nθ(P) = β(P, KO) − β(P, WT)\nPathway contrast = θ(M) − θ(E)',28,True)
    text(s,.85,4.55,11.5,1.6,'A common additive center cancels.\nMembership, count floors and clone effects do not.',25)
    s=slide('Backup: inspect, reproduce, then interpret',
        '三个命令范围不同。verify检查文件和程序，core从已公开变换值重算，historical需要外部源表。公开未包含全count矩阵，不对外说FASTQ端到端复现。')
    text(s,.85,1.45,11.7,3.8,'Report: reports/DDR_TargetBridge_Case_Study.pdf\nClaims: docs/SCIENTIFIC_CLAIM_LEDGER.md\nVerify: python tools/run.py verify\nPublic core: python tools/run.py core --output .build/demo\nHistorical tables: python tools/run.py historical --output .build/history',20)
    text(s,.85,5.95,11.6,.65,'github.com/jiangboyan0129/DDR-TargetBridge',22,True)
    prs.core_properties.title='DDR TargetBridge — comparator membership';prs.core_properties.author='';prs.core_properties.last_modified_by=''
    prs.save(output)
    return '\n\n'.join(f'## Slide {i+1}\n\n{note}' for i,note in enumerate(notes))+'\n'


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);args=p.parse_args()
    out=args.output.resolve()
    if out.exists():raise SystemExit('Choose a fresh document output directory')
    out.mkdir(parents=True)
    markdown_document(ROOT/'reports/CASE_STUDY.md',out/'DDR_TargetBridge_Case_Study.docx')
    markdown_document(ROOT/'reports/CONTEXTUAL_SUPPLEMENT.md',out/'CONTEXTUAL_SUPPLEMENT.docx')
    markdown_document(ROOT/'portfolio/PROJECT_BRIEF.md',out/'PROJECT_BRIEF.docx',brief=True)
    (out/'SLIDE_NOTES_CN.md').write_text(deck(out/'DDR_TargetBridge.pptx'))
    (out/'BUILD_SCOPE.json').write_text(json.dumps({'new_science':False,'public_core':'transformed per-gene/per-sample values, not count preprocessing','slides':9,'pdf_conversion':'separate LibreOffice step'},indent=2)+'\n')
    print(out)

if __name__=='__main__':main()
