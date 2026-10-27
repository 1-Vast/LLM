# Reference library: Agent×VC 条件药理预测定向证据

**当前（R3，2026-10-27）：** 15条来源、10份原文（9 HTML＋1 PDF）、4 restricted、1 pending（BATCHIE XML另存R1）；论文6.1MB。源码1个官方模板快照、9 not_verified＋5 not_yet_checked，0 changed snapshots。verify退出0、errors0/warnings0，完整收据见[本轮核验](../research/2026-10-26-agent-cell-evidence-r3/library_verify.json)。新增2606.06562、2506.07805、2605.04895和窗外基础对照2407.00175；阅读范围逐条登记，未全篇阅读/复现。累计确认至少27条新研究query，审查中断部分无最终收据；不是系统穷尽。下文统计均为历史过程快照，以本段为当前汇总。

三药选择性论文官方ZIP仅模板，commit和许可未知，未执行；未存完整仓库/数据。PDF的R RF200/1000与模板Python RF200存在差异；不能凭快照声称完整复现。HTML2506.07805的title标签为1INTRODUCTION，已人工核对正文p1.1题名和p2三位作者。来源、条件与局限见[R3报告](../research/2026-10-26-agent-cell-evidence-r3/report.md)。研究时间窗现为2025-01-01—2026-10-27，2024来源仅作基础近邻。

**R2快照（2026-10-26）：** 11条来源、6份原始HTML、4篇restricted、1条pending（BATCHIE原始XML另存episode）；3.5MB，code 9 not_verified＋2 not_yet_checked，0 snapshots；verify退出0、0 errors、0 warnings。新增arXiv:2605.02611与2506.15893，均P级，相关范围见[算子开发](../research/2026-10-26-agent-cell-evidence-r2/operator_development.md)。累计6pass/21条新query；下载已指名来源不追加检索。源码未运行，未做全领域穷尽。

| Item | Value |
|---|---|
| Domain and boundary | Agent×VC 条件药理预测；两轮共六pass内11个关键来源，不是系统综述 |
| Window | 2025-01-01 ~ 2026-10-26 (inclusive). Older papers appear only when needed as foundations or prior art, with the reason in date_basis |
| Created | 2026-10-26 |

`papers.tsv` has one row per stored file (the paper's own row has file_role=main) and `repositories.tsv` one row per
paper and repository; lit-survey `scripts/reference_library.py` defines their columns and status words. `manifests/`
lists every file of each code snapshot with its SHA-256. Run `reference_library.py verify` before using the library
and paste its summary under Counts.

## Coverage

2026-10-26：原生 web__run，第一侦察 pass，2 检索式组共8 query。准确查询及读取位置见 [primary_evidence.md](../research/2026-10-26-agent-cell-evidence/primary_evidence.md)。最多5篇决策关键来源，是定向核验，不是完整领域资料库。多 query 搜索结果合并输出有裁剪，不声称完整召回。Nature认证跳转、ScienceDirect403均停止该页面，未重试受限来源。先检查 data/external/literature_surveys 和 research_sources 的公开题录，相关 DOI 命中 local_repair 的题录文件，未找到本次五篇可直接复用的正文文件；未进入sealed/reserve/vault数据。

## Counts

**最终状态（下文5篇及8篇为历史快照）：** `reference_library.py verify --json`退出0，unique=9，files=4，downloaded_html=4，restricted=4，pending=1；code not_verified=9，official stored=0，snapshots=0；2.6MB，errors/warnings均空。BATCHIE题录已入库，原始XML及receipt在[episode sources](../research/2026-10-26-agent-cell-evidence/sources/PMC11696745.xml)，不是工具登记的PDF/HTML，故其manifest行仍pending，不能算第5份入库HTML。Europe PMC认证其发表2025-01-02、PMID39746987；相关方法P级。此更新取代下文“发表日期待核、未入库”的过程状态。

`reference_library.py verify --json`，2026-10-26，退出0：unique=5，files=1，downloaded_html=1，restricted=4；code not_verified=5，official code stored=0，snapshots=0；papers=0.4MB；errors=[]，warnings=[]。表头、状态与文件路径/hash由技能脚本维护。

## Gaps

AROMA v1合法公开HTML已保存，阅读层级P，未读全附录；TxPert/PDGrapher仅R级，State/Tahoe摘要A级，正文受限。AROMA论文给出官方代码链接，但仓库未下载、训练入口/许可未核；其余4篇源码未核，不能说不存在。停在分配的8 query预算；续取应先核独立viability、重复及同条件元数据，不扩大成全领域下载。BATCHIE DOI年份不能代替发表日期，尚未在此库收录，需后续原始题录核验。

A stored file is not a read paper, and stored code has not been run, reproduced or cleared for reuse.

## Independent reassessment sources (2026-10-27)

有限主张重审，复用既有库，新增Heo `arxiv-2605.20885` v1、Yang等 `arxiv-2502.05372` v2、DeepSynBa `doi-10.1093-bioinformatics-btag416` 正文HTML三份；只读与问题相关的段落，均P级，非全部细节核查。检索与版本边界见[本轮来源记录](../research/2026-10-27-independent-reassessment/evidence_notes.md)。末次verify：18篇唯一论文、13份正文文件（12 HTML、1 PDF）、1 pending、4 restricted；官方源码已存1份模板快照，新三篇源码未完成核验。errors=[]、warnings=[]；下载/哈希不等于复现。旧统计作为历史快照保留。

全轮范围补充：pass1一手worker8 query（其子任务上限5篇）＋scout4 query；pass2协调者3 query；pass3独立审查2 query，共17条新搜索，不含同资源打开/格式恢复。当前9篇是在这些既定问题内的增量，不是新增检索pass。逐式/读取层级/访问限制见episode四份来源记录；下文旧“最多5篇/协调者需更新”仅为worker过程快照。3篇arXiv与AROMA P级，TxPert/PDGrapher R级，State/Tahoe A级。9篇代码均未核验，零复现；不能据此排除全部近邻或认证功能/机制收益。

## Cross-domain direction reassessment (2026-10-27)

截至本次核验：30篇唯一论文，21份入库正文（19 HTML、2 PDF），3 pending、6 restricted；另有2份本轮原始JATS XML已核相关方法并保存在episode，不冒充HTML/PDF计数。官方源码已存仍为1份旧模板快照；本轮仅核作者代码链接，未执行或复现。verify的errors=[]、warnings=[]。查询预算为4个有界pass/16条，P4原样查询因服务故障未落盘，已在研究记录披露；不是系统穷尽查新。正文partial reading与具体边界见[本轮原文记录](../research/2026-10-27-cross-domain-directions/evidence_notes.md)，数字与文件验证见[verify收据](../research/2026-10-27-cross-domain-directions/library_verify.json)。本段是新快照，旧Counts保留为历史。

## Incremental principle-scout sources (2026-10-26)

新增三篇原始 arXiv v1 正文 HTML：2602.05340、2605.26093、2603.14094；均已核对本地 HTML 的题名、h1 与第一作者，reading_level=P，精确范围已由 reference_library.py 写入 reading_scope，源码均 not_verified。此前五篇统计作为原始快照保留。新增与 verify 账本见 [scout_library.md](../research/2026-10-26-agent-cell-evidence/scout_library.md)。协调者需在本轮整合时更新顶部“最多5篇”边界及 Counts 总数；此刻 verify 快照为 unique=8、files=4、downloaded_html=4、restricted=4、code not_verified=8、official code stored=0、errors=[]、warnings=[]，退出0。新增三篇下载不增加本轮搜索 query 或 pass。


## Core mechanism design extension (2026-10-27)

新增 Compositional Behavioral Semantics (2606.25357v2)、Generalised Transportability (2608.15645v1)、Task-Aware Exploration (2602.18724v1) 三篇原始HTML并部分阅读，定位和不能借用的生物前提见[证据记录](../research/2026-10-27-core-module-design/evidence_notes.md)。作者正文链接的TraCA代码快照已存commit30eb685ac6725efd3cbc15abdd5c53998182a0be（79文件，未运行、许可unknown）。最终verify：33篇、24正文文件（22HTML+2PDF）、2份官方链接代码，仍3pending/6restricted，errors=[]、warnings=[]。新增5条查询，非系统查新；之前统计保留为历史快照。

## Direction and mechanism expansion (2026-10-27, latest snapshot)

本轮新增7篇：DrEval、无神经网络扰动校准、跨study协同基准、2025活细胞kinase参与及2012/2013/2017在线的直接先例。6份原始HTML已入库并核题名，Lee2012仅摘要（XML500，恢复页为验证码）；实际读取为相关部分P或摘要A。原始JATS、查询、读取定位和访问边界见[本轮证据](../research/2026-10-27-direction-mechanism-expansion/evidence_notes.md)。新增DrEval作者代码265文件，commit c5a7274e9c843dc4f24797986446d39d22124195，MIT LICENSE已核，只读未运行，当前development分支与论文版本关系未知。

最新verify：40篇唯一论文、30正文文件（28HTML+2PDF）、1 abstract_only、3 pending、6 restricted；3份官方链接代码快照；errors/warnings均空。新主题检索14/16条，部分宽query未翻完，未完成完整引用链和全部源码收集，不是系统穷尽调研。旧Counts保留为历史快照，以本段及[最终收据](../research/2026-10-27-direction-mechanism-expansion/library_verify_final.json)为当前状态。下载、哈希和独立逻辑复核不认证科学机制或效果。
