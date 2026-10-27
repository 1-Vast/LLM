# 一手证据与数据条件：第一侦察 pass

检索日期：2026-10-26，Asia/Shanghai。角色 primary_evidence；独立于候选开发，没有充任候选挑战者。requested_model / requested_effort：派发字段未向本 worker 暴露，unknown；effective_model / effective_effort：unknown。未更改模型配置、调用外部模型 API、安装依赖或训练。

## 发现

知识增强、拓扑检索、可解释扰动预测和跨细胞转录响应已有明确近邻。不能把“Agent 读知识后预测 VC 响应”本身当主创新。当前最能改变机制主张的是 AROMA：原文明确预测表达三分类；关联图谱和标签一致的合成推理轨迹不能独立证明功能作用或药物 engagement。

本次未确认任何一个 2025—2026 公开资源同时满足药×细胞交叉、遗传扰动或 engagement、独立 viability 和可识别的生物重复。“未确认”仅适用于本次预算，不表示不存在。应先核定可评分交集，不能用增添模型模块填补缺失测量。

## 实际查询

本次分配预算：第一 pass 的 2 个检索式组，每组 4 query；实际 8 query，未扩展。全轮共享 3 pass、每候选最多 2 次实质修订由协调者管理。原生工具 `web__run` 实测可搜索及读取公开 arXiv/GitHub/PubMed；无可视浏览器。多 query 合并输出有裁剪，未保留逐式完整命中列表，因此不报告每式总数或零命中。

Q1 逻辑式：`(2025 OR 2026) AND (perturbation prediction OR virtual cell OR drug response) AND (knowledge graph OR mechanism OR causal OR target engagement)`。决定：知识增强是否已有近邻、输出是否独立功能。

1. `2025 2026 perturbation prediction knowledge graph mechanism virtual cell drug genetic perturbation`
2. `2025 2026 Tahoe 100M drug perturbation viability cell lines`
3. `2025 2026 perturbation response prediction causal mechanism CellOT State scGPT`
4. `2025 2026 drug target engagement proteomics kinobeads viability dataset cell lines`

Q2 逻辑式：`(2025 OR 2026) AND (drug perturbation OR chemical genetic perturbation OR target engagement) AND (cell lines OR crossed) AND (viability OR replicate OR dose response)`。决定：是否存在可独立证伪药理判断的数据。

1. `2025 2026 drug perturbation atlas matched viability genetic perturbation target engagement dataset replicates PRISM DepMap`
2. `2025 2026 Tahoe 100M data biological replicates cell viability assay CellTiter Glo`
3. `2025 2026 systematic drug target engagement cell lines chemoproteomic dataset viability dose response`
4. `2025 2026 JUMP Cell Painting drug genetic perturbations viability replicates public dataset`

检索前反例条件：知识图谱增强表达预测已存在则“加知识”不是主差异；同一 RNA 数据导出的结局不是独立验证；数据库靶点注释不等于处理条件下的实际结合。

## 来源与读取层级

R=题录/搜索正文片段；A=实际完整摘要；P=实际部分方法或官方数据说明；F=相关原文与必要补充完整核验。本次无 F 级论文，无复现。

| 来源 | 日期/身份与 URL | 实际读取与定位 | 支持及限制 |
|---|---|---|---|
| AROMA | 预印本 2026-04-22；[arXiv v1](https://arxiv.org/html/2604.20263v1) | P；§3.1 行106–111：基因×基因×细胞的 Up/Down/Non-diff；§3.2 行115–117：图边为关联、DeepSeek-R1 生成标签一致推理；§3.3 行124–126：功能摘要、最短路径、细胞描述检索；部分§3.4–3.5，未读全附录 | 已有知识/拓扑/多模态扰动解释近邻；表达类别和生成解释不证明独立功能或 engagement |
| TxPert | Nature Biotechnology，搜索返回 2026-05-01；[DOI](https://doi.org/10.1038/s41587-026-03113-4) | R；返回涉及新细胞系预测、STRING+PxMap 和 Fig.5 偏差分析；open 转 Nature cookie authorize，500 non-retryable | 必查近邻，不能升级成方法等价已确认；跨细胞预测不自动是功能决策 |
| State | Cell，搜索返回 online 2026-08-31；[出版社](https://www.sciencedirect.com/science/article/pii/S0092867426009219)，DOI 10.1016/j.cell.2026.07.052 | A；搜索实际返回完整 Summary；open 403 | 跨数据集/细胞异质性表达预测、Cell-Eval 与假说生成；功能读数未核验 |
| PDGrapher | 2025 Nature Biomedical Engineering；[出版社](https://www.nature.com/articles/s41551-025-01481-x) | R；搜索返回 Fig.1：发现靶点集合、响应模型及代理因果图；open 被 cookie authorize 阻断，500 non-retryable | 反推干预对象已有近邻；未核实其独立功能/engagement，不能完成 F 级等价判定 |
| Tahoe-100M | Cell 2026-09-17，PMID42753697；[PubMed](https://pubmed.ncbi.nlm.nih.gov/42753697/)，[出版社](https://www.sciencedirect.com/science/article/pii/S0092867426010081)，DOI 10.1016/j.cell.2026.08.035 | A；PubMed Abstract 行244–247；出版社搜索片段 R，标题 Relative survival shifts；open 403 | 50 细胞系×1,100药物剂量条件、100M转录组有摘要支持；搜索片段以细胞相对丰度归一化作 survival。独立 viability assay、原始重复标识及 engagement 未核验，不能断言全文没有 |
| JUMP 官方说明 | [Broad hub](https://github.com/broadinstitute/jump_hub/blob/main/explanations/data_description.md)，main 未固定 commit；不是全属2025—2026的新资源 | P；Dataset Collection 行195–201；Perturbation Types 行221–231；JUMP-Target 行234–238；Available Components 行252–260 | U2OS 主集，药物/CRISPR/ORF，约5重复跨中心；306药与160对应遗传扰动依据 annotated targets。不是广泛药×多细胞交叉；注释不是 engagement，说明未建立独立viability |
| 2026跨研究药敏可重复性 | [bioRxiv原文](https://www.biorxiv.org/content/10.64898/2026.04.29.721574v1.full)，路径日期2026-04-29，未独立核题录 | R；题名 Improving reproducibility in pharmacogenomic screens through cross-study benchmarking；open 403 | 搜索称保留至少两个研究测过的药×细胞对；跨研究不是同条件生物重复，未确认遗传/engagement交集 |
| PPC | [官方站](https://panpreclinical.org/)；未核具体论文日期 | R，仅官网搜索返回资料段 | ex vivo/细胞系药敏外部功能线索；未读字典，不认证其同条件交集 |

访问受限页面均停止，未换身份/工具重取受保护原文。没有把 find 失败理解为全文无该字段。旧 gwaybio/jump-datasets 搜索称某些重复/QC缺失，与当前 hub 的关系未核；不把旧警告推广到全部现行数据。

## 最小取证与实验分叉

以下为判定建议，不是已观察结果或候选开发：

| 必须核定的条件 | 改变哪项结论 | 当前状态 |
|---|---|---|
| 同一药物、细胞、剂量、时间、批次的条件级连接 | 是否实际在预测同一干预 | Tahoe交叉有摘要；逐行metadata未核 |
| 独立 assay 的 viability，保留原始及重复结果 | 表达预测能否支持功能选择 | 未确认；RNA相对丰度不能自动替代 |
| 技术、生物、跨研究重复分别识别及负控 | 相反结论是噪声/批次还是可重复条件差异 | JUMP说明有重复；独立功能重复未确认 |
| 同条件药物 engagement 或合适近端功能测量 | 区分未打中与打中后补偿/下游脱钩 | 未确认；名义药靶只作假说 |
| 匹配遗传干预及效率/方向 | 辅助区分靶点依赖和化学离靶 | JUMP有对应扰动；多细胞功能交集未核 |
| 留出药×细胞交叉、冻结检索可见信息 | 泛化还是近邻记忆与资料回流 | 未取数据、未划分、未实验 |

如只有同一 RNA 采样导出的相对丰度，结论必须限于该测量下的状态/相对存活预测。如独立功能及重复确可匹配，才能检验功能判断会否被独立读数推翻。遗传相似性不直接等价于药物结合；缺少 engagement 时，不一致不得自动归因为结合失败。活细胞与裂解液 affinity/kinobeads 的测量条件必须分开。

需求证据：JUMP官方设计基因–化合物连接性；Tahoe摘要提供多细胞药物反应建模。拟议用户是做药物选择/机制排查的研究分析人员；“区分转录改变与可重复功能作用”是本轮提出的应用，不宣称已有临床收益或需求访谈验证。

## 复用、限制与后续

先检查根目录，无已有 reference；发现 `data/external/literature_surveys/dual_core_reference_20261021` 及 `data/external/research_sources/20261021`–`20261023`。只在这些公开资料路径搜索文件名/题录，不读 sealed/reserve/vault 数据；可见 tahoe_phenotype_20261010、pisa_living_cells、jump_target 等目录但未读数据。资料库后续由 reference_library.py 固定格式建立，最终状态另见 reference/README.md。

8 query 的单渠道侦察、输出裁剪、原文访问失败构成覆盖缺口，不能支持“无先例”。最小下一步是公开条件级 metadata 的连接核验：独立viability、重复、再确认 engagement/遗传对照；没有交集则保留有条件假说与取证设计，不升级功能或机制因果主张。BATCHIE DOI 中024不能确定发表年；其2025先例地位待协调者按原始题录核验，本worker未另检索。

资料库最终状态：已用技能 `reference_library.py init/record/paper/verify` 建立 `D:/MAESTRO/reference/`，最多5篇。AROMA合法公开HTML原文444707 bytes，SHA256 `1ec1090e9c3720a240a5f8558597308f087bd8ddd481bf64bc98d60be25bbb7e`；工具 text 输出核对题名，方法定位仍引§3.1–3.3。其余4篇正文受限，阅读级别与原因已入表。5篇源码均 not_verified，AROMA仅有论文指向官方仓库的证据、未下载源码。最终verify退出0：5 unique、1 files、downloaded_html 1、restricted 4、code snapshots 0、0 errors、0 warnings。首次给HTML text加 `--pages` 返回“HTML has no pages”，已改为无页码读取，未增加检索。详情见 [reference/README](../../reference/README.md)。
