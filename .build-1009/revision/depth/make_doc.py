from pathlib import Path
import json
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

ROOT=Path(r'D:\MAESTRO\.build-1009\revision\depth')
data=json.loads((ROOT/'display_document.json').read_text(encoding='utf-8'))
doc=Document()
sec=doc.sections[0]
sec.page_width=Inches(8.5);sec.page_height=Inches(11)
sec.top_margin=Inches(.65);sec.bottom_margin=Inches(.65)
sec.left_margin=Inches(.8);sec.right_margin=Inches(.8)
for name in ['Normal','Title','Subtitle','Heading 1','Heading 2','Heading 3']:
    st=doc.styles[name]
    st.font.name='Microsoft YaHei';st.font.color.rgb=RGBColor(0,0,0)
    st.element.get_or_add_rPr().get_or_add_rFonts().set(qn('w:eastAsia'),'Microsoft YaHei')
normal=doc.styles['Normal'];normal.font.size=Pt(10.5)
normal.paragraph_format.line_spacing=1.15
normal.paragraph_format.space_after=Pt(5)
doc.styles['Title'].font.size=Pt(24)
doc.styles['Heading 1'].font.size=Pt(17)
doc.styles['Heading 1'].paragraph_format.space_after=Pt(8)
doc.styles['Heading 2'].font.size=Pt(12)
doc.styles['Heading 2'].paragraph_format.space_before=Pt(7)
doc.styles['Heading 2'].paragraph_format.space_after=Pt(4)

def p(text,size=None,bold=False):
    par=doc.add_paragraph()
    r=par.add_run(text);r.bold=bold
    if size:r.font.size=Pt(size)
    return par
doc.add_paragraph(data['title'],'Title')
p('MAP 与 Robin 的研究背景 方法及实验验证',13)
p('中文组会汇报    建议时长 30 至 35 分钟',11)
p('两篇论文分别讨论知识如何改善新药物响应预测，以及真实实验如何推动智能体更新候选。本稿逐页解释研究动机、模型实现与实验证据，最后讨论独立的设计建议和项目核心发现。')
doc.add_heading('讲解顺序',1)
for k,v in data['comprehension_brief'].items():
    p(k,11,True);p(v)
doc.add_heading('时长与使用方式',1)
p('口述正文约 4,600 个中文字，另含标准模型名称、公式和数值。按每分钟 165 字，计入技术名称、停顿与换页约 31 分钟，预留 12% 缓冲后约 35 分钟。实际速度可通过一次朗读校准。')
p('每页先读口述正文；“延伸理解”帮助准备问答，不计入口述时长。PPT 备注内含同一份正文与来源。两张论文封面保留，用于说明论文出处，无需逐字朗读摘要。')
p('对应演示文件：1009.pptx。项目资料截至 2026 年 10 月 11 日。',9)

for s,t in zip(data['slides'],data['timing']):
    heading=doc.add_heading(f"第 {s['slide']:02} 页  {s['title']}",1)
    heading.paragraph_format.page_break_before=True
    p(f"建议口述 {t['time']}    正文 {t['word_count']} 个中文字",9)
    par=doc.add_paragraph()
    par.alignment=1
    par.paragraph_format.space_after=Pt(7)
    par.add_run().add_picture(str(ROOT/f"slide-{s['slide']:02}.png"),width=Inches(3.8))
    doc.add_heading('口述正文',2)
    # Pause and transition markers belong to rehearsal, not clean PPT notes.
    spoken=s['display_notes'].split('\n\n衔接：')[0]
    for paragraph in spoken.split('\n\n'):
        if paragraph=='[停顿]':
            continue
        p(paragraph)
    if s['extra']:
        doc.add_heading('延伸理解',2)
        p(s['extra'],9.5)
    p('衔接：'+s['display_notes'].split('\n\n衔接：')[-1],9)
    if s['source']:
        if 2<=s['slide']<=7:source='Feng et al., Nature Machine Intelligence, 2026. DOI: 10.1038/s42256-026-01286-w.'
        elif 8<=s['slide']<=13:source='Ghareeb et al., Nature, 2026. DOI: 10.1038/s41586-026-10652-y.'
        elif s['slide']==15:source='项目 mechanism_routing_20261011 的 PROTOCOL、RESULTS、VERIFIED_SUPPLEMENT；截至 2026-10-11。'
        else:source=s['source']
        p('来源：'+source,8)

for offset in [0,11]:
    heading=doc.add_heading('术语与方法释义' if offset==0 else '术语与方法释义续',1)
    heading.paragraph_format.page_break_before=True
    table=doc.add_table(rows=1,cols=3)
    table.autofit=False
    widths=[1.6,.55,4.65]
    for cell,w,label in zip(table.rows[0].cells,widths,['术语','页码','含义及在本汇报中的用途']):
        cell.width=Inches(w);cell.text=label
        tcPr=cell._tc.get_or_add_tcPr()
        shading=OxmlElement('w:shd');shading.set(qn('w:fill'),'F1F3F3');tcPr.append(shading)
    for item in data['key_parameters_methods'][offset:offset+11]:
        cells=table.add_row().cells
        for cell,w,val in zip(cells,widths,[item['term'],item['slides'],item['definition']]):
            cell.width=Inches(w);cell.text=val
    for ri,row in enumerate(table.rows):
        for cell in row.cells:
            for par in cell.paragraphs:
                par.paragraph_format.space_after=Pt(5)
                par.paragraph_format.space_before=Pt(5)
                for run in par.runs:run.font.size=Pt(9.5);run.bold=(ri==0)

heading=doc.add_heading('汇报时间安排',1)
heading.paragraph_format.page_break_before=True
p('方法页和实验页预留较多时间。下表为口述正文的分配，术语表、来源与延伸理解不纳入时长。')
table=doc.add_table(rows=1,cols=5)
table.autofit=False
timing_widths=[.45,3.65,.7,1.15,.65]
for c,w in zip(table.rows[0].cells,timing_widths):c.width=Inches(w)
for c,label in zip(table.rows[0].cells,['页码','主题','口述时间','正文／预算字数','停顿次数']):c.text=label
for item in data['timing']:
    cells=table.add_row().cells
    for c,w,val in zip(cells,timing_widths,[str(item['slide']),item['title'],item['time'],f"{item['word_count']} / {item['budget']}",str(item['pauses'])]):c.width=Inches(w);c.text=val
for row in table.rows:
    for c in row.cells:
        for par in c.paragraphs:
            par.paragraph_format.space_after=Pt(2)
            par.paragraph_format.line_spacing=1.0
            for run in par.runs:run.font.size=Pt(9)
doc.add_heading('图与证据的解读',2)
p('图轴、颜色、关键数值和公式变量已在对应正文中解释。Robin 原示意图与方法段落的孵育时间标注存在差异，已在第 11 页保留说明。表达预测、通路关联、功能命中与临床疗效属于不同证据层次。')
for part in [doc.element,doc.styles.element]:
    for border in part.xpath('.//w:pBdr'):border.getparent().remove(border)
doc.save(ROOT/'1009-逐页讲解稿.docx')

review={
1:'白底封面与三段目录，主题是未测药物响应和实验反馈。',
2:'用户原封面：Nature Machine Intelligence、MAP 题目与作者；正文无需朗读全部摘要。',
3:'四行从实验覆盖、已有进展、机制缺口到作者假设；底部区分蛋白抑制与 RNA 下调。',
4:'上方两阶段；中间输入输出；下方两个泛化任务；基准范围注明数据集内部。',
5:'原 Fig.1a-b 展示实体、属性编码与知识共享空间；右侧有序拼接公式与对比目标。',
6:'原 Fig.1c 上半训练三输入、两种损失，下半预测应用；右侧三步骤与群体均值公式。',
7:'横向条形长度对应相对提升 11.8、19.8、10.4%；右侧消融与计算排序；范围注明无新湿实验。',
8:'用户原封面：Robin 标题与 Nature DOI，作者与摘要可见。',
9:'四行疾病功能、已有工具、反馈需求与论文贡献；底部两轮研究路线。',
10:'原 Fig.1a 裁切展示疾病、假设、实验、分析、反馈与候选输出；右侧 BTL 公式变量及轨迹解释。',
11:'原 Fig.2b 时间与流式示意；原 Fig.3b 火山图横轴 log2变化、纵轴校正P值负对数；ABCA1 红色上调。原图4h与Methods3h差异已注明。',
12:'原 Fig.4b-c：左柱相对MFI，绿色显著、蓝色非显著、灰色DMSO；右曲线粉色ripasudil与蓝色Y-27632；原代复核单供者4孔。',
13:'条形正确率22.8±1.7与1.6±1.2；右侧引用、排序和流程边界；百分比与标准误含义注明。',
14:'独立设计建议，机制条件化与实验反馈两列；下面受控比较；不混入MAESTRO。',
15:'L1000实测到PRISM迁移，四块确认、边界、代理、后续；关键r与区间来源核查。'}
inventory=json.loads((ROOT/'visual_inventory.json').read_text(encoding='utf-8'))
for s in inventory['slides']:
    s['rendered_image']=str(ROOT/'rendered_slides'/f"slide-{s['slide']:02}.png")
    s['vision_reading']=review[s['slide']]
(ROOT/'visual_inventory.json').write_text(json.dumps(inventory,ensure_ascii=False,indent=2),encoding='utf-8')
(ROOT/'vision_review.json').write_text(json.dumps([{'slide':i,'review':review[i],'uncertain_elements':(['图2b的4h与方法3h有差异，已保留说明'] if i==11 else [])} for i in range(1,16)],ensure_ascii=False,indent=2),encoding='utf-8')
print(ROOT/'1009-逐页讲解稿.docx')
