#!/usr/bin/env python3
"""Build presentation documents from current, source-bound texts. No science computation."""
from __future__ import annotations
import argparse, re, json
from pathlib import Path
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from pptx import Presentation
from pptx.util import Inches as PI, Pt as PP
from pptx.dml.color import RGBColor as PC
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
R=Path(__file__).resolve().parents[1]
FONT='Noto Sans'
DARK='18344A'; ACCENT='287B89'; MUTED='536571'

def inline(p, text, size=None):
    # Preserve readable text for repository-relative links in print, without exposing an invented URL.
    text=re.sub(r'\[([^\]]+)\]\(([^)]+)\)',r'\1',text)
    for token in re.split(r'(\*\*.*?\*\*|`[^`]+`)',text):
        if not token: continue
        bold=token.startswith('**') and token.endswith('**')
        code=token.startswith('`') and token.endswith('`')
        token=token[2:-2] if bold else token[1:-1] if code else token
        r=p.add_run(token);r.bold=bold
        if size:r.font.size=Pt(size)
        if code:r.font.name=FONT;r.font.size=Pt(min(size or 10.6,9.1))
    return p

def setup(title, brief=False):
    d=Document();s=d.sections[0]
    s.page_width=Inches(8.27);s.page_height=Inches(11.69)
    s.top_margin=Inches(.66 if brief else .72);s.bottom_margin=Inches(.62)
    s.left_margin=s.right_margin=Inches(.78)
    s.header_distance=Inches(.24);s.footer_distance=Inches(.28)
    for name in ['Normal','Body Text']:
        st=d.styles[name];st.font.name=FONT;st.font.size=Pt(9.7 if brief else 10.6)
        st.paragraph_format.line_spacing=1.13 if brief else 1.16
        st.paragraph_format.space_after=Pt(6 if brief else 7)
        st._element.rPr.rFonts.set(qn('w:eastAsia'),'Noto Sans CJK SC')
    for name,sz in [('Title',25 if not brief else 25),('Heading 1',18 if not brief else 16),('Heading 2',13),('Heading 3',11.5)]:
        st=d.styles[name];st.font.name=FONT;st.font.size=Pt(sz);st.font.color.rgb=RGBColor.from_string(DARK)
        st.paragraph_format.space_before=Pt(9);st.paragraph_format.space_after=Pt(6)
        st.paragraph_format.keep_with_next=True
    st=d.styles['Caption'];st.font.name=FONT;st.font.size=Pt(8.5);st.font.color.rgb=RGBColor.from_string(MUTED)
    st.paragraph_format.space_after=Pt(7);st.paragraph_format.line_spacing=1.05
    hp=s.header.paragraphs[0];hp.text='DDR TARGETBRIDGE  /  RESEARCH CASE STUDY';hp.style=d.styles['Caption']
    footer=s.footer.paragraphs[0];footer.alignment=WD_ALIGN_PARAGRAPH.RIGHT
    r=footer.add_run('Portfolio 3.0  ·  Public-data secondary analysis  |  ');r.font.name=FONT;r.font.size=Pt(8)
    fld=OxmlElement('w:fldSimple');fld.set(qn('w:instr'),'PAGE');footer._p.append(fld)
    d.core_properties.title=title;d.core_properties.subject='Completed public-data functional-genomics case study'
    d.core_properties.author='';d.core_properties.last_modified_by='';d.core_properties.keywords='';d.core_properties.comments=''
    d.core_properties.revision=1
    return d

def table(d, rows):
    rows=[[x.strip() for x in row.strip().strip('|').split('|')] for row in rows]
    rows=[r for r in rows if not all(re.fullmatch(r':?-+:?',v or '-') for v in r)]
    t=d.add_table(rows=1,cols=len(rows[0]));t.alignment=WD_TABLE_ALIGNMENT.CENTER;t.autofit=True
    t.style='Light Shading Accent 1'
    for j,h in enumerate(rows[0]):
        p=t.rows[0].cells[j].paragraphs[0];inline(p,h,8.8)
        for r in p.runs:r.bold=True;r.font.color.rgb=RGBColor.from_string(DARK)
    repeat=OxmlElement('w:tblHeader');t.rows[0]._tr.get_or_add_trPr().append(repeat)
    for row in rows[1:]:
        cells=t.add_row().cells
        for j,c in enumerate(row):inline(cells[j].paragraphs[0],c,8.8)
    for row in t.rows:
        trPr=row._tr.get_or_add_trPr();cant=OxmlElement('w:cantSplit');trPr.append(cant)
        for cell in row.cells:
            cell.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER
            for p in cell.paragraphs:
                p.paragraph_format.space_after=Pt(4);p.paragraph_format.space_before=Pt(4);p.paragraph_format.line_spacing=1.06
    d.add_paragraph().paragraph_format.space_after=Pt(0)

def markdown_doc(src, dest, brief=False, supplement=False):
    text=src.read_text(encoding='utf-8');d=setup(text.splitlines()[0].lstrip('# '),brief)
    lines=text.splitlines();i=0; pending_break=False
    while i<len(lines):
        line=lines[i].strip();i+=1
        if not line: continue
        if line=='<!-- PAGEBREAK -->':pending_break=True;continue
        if line.startswith('|'):
            rs=[line]
            while i<len(lines) and lines[i].lstrip().startswith('|'):rs.append(lines[i]);i+=1
            table(d,rs);continue
        im=re.fullmatch(r'!\[([^]]*)\]\(([^)]+)\)',line)
        if im:
            p=d.add_paragraph();p.alignment=WD_ALIGN_PARAGRAPH.CENTER
            path=(src.parent/im.group(2)).resolve()
            width=5.30 if brief else (6.20 if '04_samples' in path.name else 6.55)
            shape=p.add_run().add_picture(str(path),width=Inches(width))
            shape._inline.docPr.set('descr',im.group(1));p.paragraph_format.space_after=Pt(3);continue
        if line.startswith('# '):p=d.add_paragraph(style='Title');inline(p,line[2:]);continue
        if line.startswith('## '):
            # The companion supplement uses deliberate page starts to avoid orphan headings.
            if supplement and (line.startswith('## 3.') or line.startswith('## 5.')):pending_break=True
            p=d.add_paragraph(style='Heading 1');inline(p,line[3:])
            if pending_break:p.paragraph_format.page_break_before=True;pending_break=False
            continue
        if line.startswith('### '):p=d.add_paragraph(style='Heading 2');inline(p,line[4:]);continue
        p=d.add_paragraph()
        if line.startswith('**Figure '):p.style='Caption'
        if line.startswith('[1]') or re.match(r'^\[[2-5]\]',line):p.style='Caption'
        inline(p,line)
    d.save(dest)

# Deck: editable text and tables; graphs remain images with SVG + source script provided.
def build_deck(dest):
    prs=Presentation();prs.slide_width=PI(13.333);prs.slide_height=PI(7.5)
    def text(sl,x,y,w,h,t,size=23,bold=False,color=DARK):
        box=sl.shapes.add_textbox(PI(x),PI(y),PI(w),PI(h));tf=box.text_frame;tf.word_wrap=True
        tf.margin_left=tf.margin_right=0;tf.margin_top=tf.margin_bottom=0
        for k,line in enumerate(t.split('\n')):
            p=tf.paragraphs[0] if k==0 else tf.add_paragraph();p.text=line;p.font.name=FONT;p.font.size=PP(size);p.font.bold=bold;p.font.color.rgb=PC.from_string(color);p.space_after=PP(10)
        return box
    def slide(title,note):
        s=prs.slides.add_slide(prs.slide_layouts[6]);s.background.fill.solid();s.background.fill.fore_color.rgb=PC(255,255,255)
        rule=s.shapes.add_shape(MSO_SHAPE.RECTANGLE,PI(.48),PI(.35),PI(.11),PI(.55));rule.fill.solid();rule.fill.fore_color.rgb=PC.from_string(ACCENT);rule.line.fill.background()
        text(s,.76,.38,11.95,.72,title,27,True)
        text(s,.6,7.15,11.4,.18,'DDR TargetBridge  |  Completed public-data case study  |  AI-assisted implementation and analysis',9,color=MUTED)
        text(s,12.2,7.1,.6,.24,str(len(prs.slides)),10,color=MUTED)
        s.notes_slide.notes_text_frame.text=note
        return s
    def image(s,name,x,y,w):s.shapes.add_picture(str(R/'figures'/name),PI(x),PI(y),width=PI(w))
    def callout(s,x,y,w,h,label,body):
        shape=s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE,PI(x),PI(y),PI(w),PI(h));shape.fill.solid();shape.fill.fore_color.rgb=PC.from_string('F0F5F6');shape.line.fill.background()
        text(s,x+.2,y+.14,w-.4,.48,label,21,True);text(s,x+.2,y+.71,w-.4,h-.77,body,19)
    s=slide('When the comparison population changes the conclusion',
        '开场约40秒：我研究的不是线粒体靶点是否有效，而是一个公开CRISPR筛选中的通路比较，是否依赖实际纳入的成员。全程区分数据由原作者产生与项目的AI辅助再分析。本报告不宣称新机制或通用模型。')
    text(s,.8,1.35,11.7,1.13,'Can a pathway-prioritization argument survive a change in who was measured?',34,True)
    callout(s,.8,3.0,5.6,2.62,'Evidence','One archived A549 WT/PRDX1-KO × vehicle/AZD7648 screen. Fixed pathways; three support views; two transforms.')
    callout(s,6.75,3.0,5.75,2.62,'Result','The balance reverses mainly through the comparator. The mitochondrial arm remains nearly stable. Wider coverage includes low counts.')
    text(s,.82,6.03,11.6,.65,'Scope: a finite empirical diagnosis and reproducible research record—not target validation.',21)
    s=slide('The same pathway label can hide a different population',
        '先讲数据和单位：16个真实样本记录；四个终点组各3个，两背景各2个T0。一个双guide构建体不是两次独立干预。S0到S1换的是靶向单位；S1到S2再加入基因。E是精确的真核翻译延伸集合，不是所有胞质翻译。')
    text(s,.8,1.35,11.65,.8,'64,237 physical constructs · 16 real sample records · one source programme',24,True)
    rows=[['View','Genes','Targeting units','M / E'],['S0','Original supported','Original qualified','89 / 23'],['S1','Same as S0','Expanded T0 support','89 / 23'],['S2','All T0-supported','Expanded T0 support','94 / 91']]
    shp=s.shapes.add_table(4,4,PI(.8),PI(2.45),PI(11.7),PI(2.25));tb=shp.table
    for i,row in enumerate(rows):
        for j,val in enumerate(row):
            c=tb.cell(i,j);c.text=val;c.margin_left=PI(.14);c.margin_top=PI(.12)
            for p in c.text_frame.paragraphs:p.font.name=FONT;p.font.size=PP(19);p.font.bold=i==0
    text(s,.83,5.1,11.5,1.32,'M: Mitochondrial translation (137 directory genes)\nE: Eukaryotic Translation Elongation (99 directory genes)\nMore covered members do not automatically mean more reliable measurements.',20)
    s=slide('The comparator changes; the mitochondrial arm is stable',
        '主结果约一分钟：先看M再看E，不要只看差值。零替换下M约1.043到1.052，E约0.183到2.814，差值正变负。count+1同样反转，两种都保留。横轴是不同分析总体而不是时间。它不是线粒体作用反转。')
    image(s,'01_components.png',2.12,1.2,9.1)
    s=slide('Restored comparator members drive the observed shift',
        '这些是全部旧和新增的E基因。23个旧成员的均值约0.567，68个新增约3.574。它们按人数混合给出2.814。这是算术分解，不是识别了多少生物学效应由过滤造成，也不把新增基因列为新靶点。')
    image(s,'02_comparator_members.png',.75,1.3,8.55)
    text(s,9.63,1.56,2.9,.4,'Zero-only means',15,color=MUTED)
    text(s,9.63,2.0,2.9,2.6,'23 retained\n+0.567\n\n68 added\n+3.574',25,True)
    text(s,.85,6.47,11.6,.45,'All members retained. The mixture is arithmetic—not a causal attribution or a new target nomination.',17)
    s=slide('Coverage and count-floor risk increase together',
        '恢复覆盖同时增加测量下限。四组都展示：零数59、63、63、2；每组291个构建体样本单元。资格使用vehicle，效应也减vehicle。因此不能说S2是真实生物学，不能把相对富集写成绝对保护。')
    image(s,'03_count_floor.png',.82,1.38,9.0)
    text(s,10.1,1.8,2.43,3.85,'Selection uses vehicle.\n\nResponse also subtracts vehicle.\n\nThe archive cannot fully separate composition, growth and measurement effects.',18)
    s=slide('One local decision—not three layers of validation',
        '这里收束：不把原正对比升级成稳定的线粒体特异优先级。原PRKDC只评到12/36，crossing要求一正一负而两者都正，各自都是有限历史结果。父研究损伤和铁实测不能借给整个通路。后面的结果没有证明早期失败的原因。')
    callout(s,.8,1.55,11.7,1.55,'Decision','Do not use the original positive balance as membership-insensitive support for a mitochondrial-specific target claim.')
    callout(s,.8,3.38,5.65,2.6,'Separate histories','PRKDC: 12 of 36 source calls evaluated.\nCrossing: +0.324 / +0.154; the required negative WEE1 sign failed.')
    callout(s,6.75,3.38,5.75,2.6,'Not established','A reversed mitochondrial mechanism; the opposite target; general nontransportability; an absolute survival benefit.')
    s=slide('Contribution, attribution and responsibility',
        '最后约45秒：公开实验不是我的实验；标准log、排名、匹配不是新算法。项目新增具体比较、成员分解和可复算工作流。我只能对自己实际承担、理解和能维护的部分负责。AI参与设计讨论编码核查图表写作，不能说完全独立手写。需要具体个人责任说明而非比例。')
    callout(s,.8,1.52,5.63,3.6,'Project contribution','A local empirical comparison.\nTargeting-unit / gene decomposition.\nSource-table and count-export reproduction.\nExplicit failed hypotheses and limits.')
    callout(s,6.75,1.52,5.75,3.6,'Original data and assistance','All experiments: cited investigators.\nStandard methods: prior work.\nAI: design discussion, code, tests and writing.\nPersonal responsibility: documented separately.')
    text(s,.85,5.64,11.6,.9,'Core work can be reproduced from bundled inputs. No FASTQ replay, new mechanism or production AIDD platform is claimed.',22)
    s=slide('Backup • The exact comparison and its assumptions',
        '公式页用于追问。先构建体到靶向单位到基因等权，再各通路平均。每样本M−E共同中心抵消。背景中的药物差值先分别算再相减。不能用随机抽基因或81次重复删样本当作培养误差。')
    text(s,.9,1.6,11.5,1.25,'β(P, background) = mean drug − mean vehicle\nθ(P) = β(P, KO) − β(P, WT)',28,True)
    text(s,.9,3.24,11.5,.7,'θ(balance) = θ(M) − θ(E)',32,True)
    text(s,.9,4.35,11.4,2.1,'Common additive centering cancels; membership and count floors do not.\nTwo count transforms are separate sensitivity views, not independent experiments.\nCulture records do not remove clone/establishment confounding.\nNo biological P values or confidence intervals are inferred.',21)
    s=slide('Backup • Inspect the result, then follow the source',
        '演示路线：README到结果表到explain_result.py，再看reproduce_final.py。三个复现层级区分。源码与输入哈希不等于独立生物学验证。个人署名和发布许可要本人确认，不自动上传。')
    text(s,.9,1.6,11.5,3.8,'Read: reports/CASE_STUDY.pdf\nTrace: docs/SCIENTIFIC_CLAIM_LEDGER.json\nExplain: python tools/explain_result.py\nVerify: python tools/run.py verify\nReproduce counts: python tools/run.py core --output .build/demo\nReproduce source tables: python tools/run.py historical --output .build/history',21)
    text(s,.9,5.8,11.5,.8,'Data: O’Loughlin et al., Nature Chemical Biology (2026), doi:10.1038/s41589-026-02312-z. Full attribution and unchanged result tables are bundled.',16)
    prs.core_properties.author='';prs.core_properties.last_modified_by='';prs.core_properties.title='DDR TargetBridge — comparator membership and pathway priority';prs.core_properties.subject='Completed computational functional-genomics case study'
    prs.save(dest)
    notes=[]
    for i,s in enumerate(prs.slides,1):notes.append(f'## Slide {i}\n\n'+s.notes_slide.notes_text_frame.text+'\n')
    return '\n'.join(notes)

def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();o=a.output.resolve()
    if o.exists():raise SystemExit('Use a fresh document output directory')
    o.mkdir(parents=True)
    markdown_doc(R/'reports/CASE_STUDY.md',o/'CASE_STUDY.docx')
    markdown_doc(R/'reports/CONTEXTUAL_SUPPLEMENT.md',o/'CONTEXTUAL_SUPPLEMENT.docx',supplement=True)
    markdown_doc(R/'portfolio/PROJECT_BRIEF.md',o/'PROJECT_BRIEF.docx',brief=True)
    (o/'SLIDE_NOTES_CN.md').write_text(build_deck(o/'DDR_TargetBridge.pptx'),encoding='utf-8')
    (o/'BUILD_SCOPE.json').write_text(json.dumps({'new_science':False,'inputs':['reports/CASE_STUDY.md','reports/CONTEXTUAL_SUPPLEMENT.md','portfolio/PROJECT_BRIEF.md','figures/'],'outputs':['CASE_STUDY.docx','CONTEXTUAL_SUPPLEMENT.docx','PROJECT_BRIEF.docx','DDR_TargetBridge.pptx','SLIDE_NOTES_CN.md'],'slides':9},indent=2)+'\n')
    print(o)
if __name__=='__main__':main()
