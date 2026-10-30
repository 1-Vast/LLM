# Q1：同研究信号—功能资源资格核查

2026-10-28。范围仅限 BRIEF 指定的 2015 年研究及其同文公开附件、原文明确链接的作者资源。`effective_model: unknown`。未调用外部模型 API，未训练，未读现有 sealed，未新增候选，未改共享索引。原始功能矩阵只下载、保留字节并计算 hash；没有解码、读取功能行、排序或分析功能值。

**结论：这篇研究确实改变“缺少同研究、名义条件对应的信号与后续功能”这一前提，但还不能宣布本轮预测试验或跨药程序试验的数据资格通过。** 正文明确称所有功能测量与蛋白测量采用相同扰动条件，RPPA 为给药后 24 h，resazurin 为 72 h；这比跨库按药名拼接有直接的一手方法依据。它是平行培养物的条件对应，未提供同细胞纵向配对。逐样本重复、原始矩阵与条件索引的完整对应、剂量编码、无泄漏输入生成仍有缺口；当前不启动训练。

## 身份、查询与实际读取范围

- 题名：*Perturbation biology nominates upstream–downstream drug combinations in RAF inhibitor resistant melanoma cells*。
- eLife，2015-08-18；DOI `10.7554/eLife.04640`；PMID `26284497`；PMCID `PMC4539601`。EPMC 日期与 JATS `<pub-date>` 的 18/8/2015 一致。2015 年论文用作资源和强先例，不能当作 2025–2026 年创新。
- Q1 精确查询：`TITLE:"Perturbation biology nominates upstream-downstream drug combinations in RAF inhibitor resistant melanoma cells"`，`resultType=core`，命中 1 条。
- 精确请求 URL：`https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=TITLE%3A%22Perturbation%20biology%20nominates%20upstream-downstream%20drug%20combinations%20in%20RAF%20inhibitor%20resistant%20melanoma%20cells%22&format=json&resultType=core&pageSize=10`。
- 已实读 JATS 的相关段落：`s2-1-1/2`、`s2-2-1`、`s3-1`、`s4-1-2/3/4` 中与模型及输入来源相关的段落、`s4-2-1…4`、`s4-3-1…3`、`s6/6-1`；补充文件只核 A/C 条件与剂量表，以及文档结构；复制原文中涉及重复的句子和对应图/作者答复位置。没有把取得完整 JATS 等同于全文通读。证据阅读级别为相关部分原文 P。
- 会话没有暴露原生网页搜索工具；本轮使用真实 EPMC 核心 API 与同文官方 HTTP GET，不伪造原生搜索调用。后续请求均为已知同文/显式来源链接读取，不是新增主题查询。

身份响应、JATS、出版社正文/附件页、作者资源及四个公开静态文件共 11 个原始响应体，合计 **1,465,832 bytes**，低于本分支 15 MiB 限额；每请求 timeout 45 s，均返回 HTTP 200，curl exit 0。每个请求的精确 URL、UTC 起止时间、状态、Content-Type、原始字节数及 SHA256 均在 [q1_fetch_manifest.json](sources/q1_fetch_manifest.json) 和 [q1_fetch_log.tsv](sources/q1_fetch_log.tsv)，11/11 原文件已重算 hash 相符。

主要原始来源：

| 原始文件 | bytes | SHA256 | 来源 |
|---|---:|---|---|
| [q1_epmc_search.json](sources/q1_epmc_search.json) | 9,841 | `51fb691604a2749a9f5cb24a7a274309a0682a58e735306a93081c120f01424e` | EPMC Q1，fetch 2026-10-28T08:39:46–48Z |
| [q1_pmc4539601_jats.xml](sources/q1_pmc4539601_jats.xml) | 302,385 | `9290da76c1b42f03195966cf4d7925204ae0b6873a0a083cfacb05eaa537c6a9` | `https://www.ebi.ac.uk/europepmc/webservices/rest/PMC4539601/fullTextXML` |
| [q1_elife_supp1.docx](sources/q1_elife_supp1.docx) | 90,221 | `9d2166ce38716e7048fc304d8226ab42708626207be9348c6c499db9d3a016f1` | 出版社同文 figures 页的 Supplementary file 1 公共链接，DOI `10.7554/eLife.04640.029` |
| [q1_pertbio_project.html](sources/q1_pertbio_project.html) | 32,993 | `831f8b67c6ffe933c11451cb01d2a1bd5023014e7b6a246009dde5ca4f2de206` | 原文作者站显式 meta 重定向至 `http://projects.sanderlab.org/pertbio/` |

作者站公开 HTML 含 Name/Organization/Purpose 联系表单，也公开返回静态文件链接。本轮仅对这些文件做无需认证的 GET，均直接 HTTP 200；未提交表单、POST、联系信息或消息，未执行网页 JS 或下载的研究代码。公开可下载不等于字段资格已经确认。

## 条件与测量合同

| 资格字段 | 已核证据 | 仍未知或限制 |
|---|---|---|
| 背景 | `s4-2-1`：所有扰动实验为 RAFi-resistant SkMel-133；身份经遗传指纹检查 | 一种背景；不支持跨背景已通过 |
| 培养/载体 | 完整 RPMI-1640、10% heat-inactivated FBS、100 units/ml each penicillin/streptomycin、37°C/5% CO2；约 40% confluence 时给药；6-well plates；DMSO vehicle control | DMSO 最终浓度、逐样本批次/孔、72 h 功能实验的播种量及补药/换液记录未单独核到 |
| 扰动 | 12 种定向药物；单药与成对组合；正文 89 条件；成对剂量用 Western blot 的 presumed target/downstream effector IC40 校准 | 校准不是所有药物的靶点直接结合证据；部分化学名称只是简称，未核目录号/结构/批号 |
| 实测信号 | `s4-2-2`：给药后 24 h 裂解，RPPA；正文 138 total/phosphoprotein readouts，QC 后 100，再按响应筛至 82 入模 | 24 h 是本研究相对 72 h 的较早观测，不是即时信号；完整 138 及逐重复原始强度表未核到 |
| 独立功能测量方式 | `s4-2-4`：resazurin 72 h；44 µM、1 h 染色，530/590 nm，标准曲线估细胞数；另有 flow cytometry DNA content | resazurin 是生长/存活细胞量代理；独立实验方式不自动等于独立评价数据或已证机制 |
| 同条件对应 | 原文原句：**“All phenotypic measurements are made in perturbation conditions identical to those of proteomic measurements.”**；`s2-1-2` 也称在全部 89 条件平行测量 | RPPA 破坏性裂解；没有同一单细胞或同一培养物逐细胞纵向追踪 ID。不能写同细胞配对 |
| 细胞周期时间 | `s4-2-4` 开头写 flow cytometry 为 24 h | 同一段后半又写给药 **72 h** 后收集细胞做 flow cytometry。原文内部冲突未解决，不选一个当确定时间 |
| 重复 | `s4-2-2` 原称 “Three biological replicates are spotted for each sample”；图 6 局部验证及图补充称 3 replicates/biological replicates；作者答复 SA2 称 cell-cycle arrest experiments run in triplicates | 未确认所有 89 条件的 resazurin 重复数、独立培养/批次、逐重复 ID 或原始观测；图 6 局部验证重复不能推广到整个屏。没有从技术孔生成生物 CI |

选定原文阅读摘录见 [q1_jats_selected_reading.txt](sources/q1_jats_selected_reading.txt)，重复句及来源位置见 [q1_replication_evidence.txt](sources/q1_replication_evidence.txt)。

## 已到位原表、索引及保留缺口

1. **补充 A/C 是条件表，不是逐重复功能原始表。** 原始附件 A 表有 12 个药物标签及 presumed target、downstream effector、两个剂量字段（表头 nM；RY 的 Dose2 为 NA）。C 表有 Index、Perturbation1、Dose1(nM)、Perturbation2、Dose2(nM)，左右各一组列。本轮只提取这两个表，见 [q1_supp1_table_A_conditions.tsv](sources/q1_supp1_table_A_conditions.tsv)、[q1_supp1_table_C_conditions.tsv](sources/q1_supp1_table_C_conditions.tsv)。D/F 是预测结果，不能当独立实测功能；未读取这些表的数据行。

2. **补充 C 实际是 88 个条件记录，缺 Index 45。** 左栏 1–44，右栏 46–89。作者公开 `exp_index.txt` 有 89 个不重复条件标签，第 45 个非空标签为 `PLX|60,HN|6`。这可提示缺项的可能意图，却不等于来源已给出一条完整可合并的原表记录；没有自动补齐。逐项结构计数见 [q1_conditions_count_audit.json](sources/q1_conditions_count_audit.json)。

3. **公开条件索引可下载，但标签不含一致的剂量单位。** [q1_pertbio_exp_index.txt](sources/q1_pertbio_exp_index.txt) 有 89 条唯一标签：23 单药、66 成对、12 个药物代码；成对集合覆盖 12 选 2 的全部组合。其后两个无表头整数的含义未核，不能说是重复 ID 或随机划分。索引无显式 no-drug/DMSO 条件记录。`AK|10` 对应 C 表 AKTi `10,000` nM，而 `901|1.5` 对应 MEKi `1.5` nM；不能把全部标签统一当 nM 或 µM。A 表 AKTi 剂量原字符为 `5.000`/`10.000`，C 表为 `5,000`/`10,000`；两个版本均原样保留，不自动小数点校正。

4. **节点索引能区分变量角色，不能拿全部节点当实测信号。** [q1_pertbio_node_index.txt](sources/q1_pertbio_node_index.txt) 有 99 个唯一标签；尾字段分组 82/5/12，与正文 82 蛋白、5 功能、12 activity nodes 相符。功能标签是 `G2M/G1arrest/G2arrest/Sarrest/cellviab`；12 个 `a...` 标签代表药物作用节点。后两类不是独立的实测蛋白程序特征。见 [q1_index_structure.json](sources/q1_index_structure.json)。

5. **`pert.txt` 是模型扰动编码，不能晋升为无泄漏原始输入。** 文件 [q1_pertbio_pert.txt](sources/q1_pertbio_pert.txt) 89 行，每行 99 个字段；本轮只核形状及作用节点角色，没有把其数值当功能。正文 `s4-1-4` 对 activity nodes 的量化仅指向 Molinelli et al. 2013；当前已取 2015 正文/附件没有逐值生成规则、校准集合或是否使用响应/全数据拟合的可核说明。是否含全数据信息仍未知；本轮不追另文，不将它当原始药物身份/剂量输入。原句位置见 [q1_activity_input_provenance_reading.txt](sources/q1_activity_input_provenance_reading.txt)。

6. **`data.txt` 的可下载性已验证，内容资格仍未知。** 公开链接 `http://projects.sanderlab.org/pertbio/files/data.txt`，HTTP 200，`text/plain`，51,546 bytes，SHA256 `98c97581c8edcc4a35709bb650df358c09603a496d422c569aed00218e1374e1`，原字节在 [q1_pertbio_data.txt](sources/q1_pertbio_data.txt)。本轮按父任务约束没有解码或解析它，没有看功能行；因此未确认它是否逐重复、是否只含筛后 82 节点、矩阵方向、缺失、功能值或归一化锚点，也不宣称其维度或与 89 个条件一一映射已经通过。hash 读取只核字节，不是科研内容审查。

7. **靶点层面的跨化学实现不能区分，实测 checkpoint 程序仍有可检验线索。** A 表 12 个 presumed target 各一个药物标签；这只限制 target-level chemical transfer，不能外推为不存在共享程序。A 表明确有重复 downstream effector：AKTi/PI3Ki → AKTpS473，MEKi/BRAFi → MAPK1pT202，mTORi/PKCi → S6pS240，JAKi/SRCi → GSK3pS21。这些是可供未来预定义 checkpoint 语义的原表线索，但 IC40 的 Western blot 校准不等于 24 h 实测状态相同，上游差异仍可对应不同功能；当前不定义新机制、不读取响应、不拟合。验证实验另用 (+)JQ1、PLX4032，训练药表为 PLX4720；这些额外化学品没有因此进入已核 89 条件的同合同网格，更不能据此声明可做整药留出后的同程序替代性确认。

## 既有方法是强先例

这篇论文已经把实测蛋白与功能共同放进可执行、带生物先验的网络：82 蛋白 + 5 功能 + 12 药物 activity nodes；用带稀疏项及先验项的目标函数、belief propagation 概率分布、BP-guided decimation 产生模型，执行 ODE 到稳态，预测未测扰动并实验验证组合。相关来源为 `s2-2-1`、`s4-1-2/3/4`、`s4-1-4-3-1/2`。原论文称生成 4,000 个可执行网络模型；这是其方法描述，不是本轮复现。

因此，“蛋白—功能联合网络”“先验与扰动数据更新网络概率”“模型提出新组合”“可执行机制假设”均已有强先例，不能作为我们新增创新。其 12 个活动节点仍携带药物身份，且训练联合使用功能端点，不能直接冒充“预定义实测程序已充分、药物身份无剩余信息”。其跨细胞先验迁移在讨论中主要是展望，论文也明确本研究只建一个细胞系模型；本轮不把这一展望写成已证迁移。

论文按全部条件的响应及 QC 选出 82 个节点，亦不能不审校准边界就当作预先独立冻结的程序定义。若以后试验，信号选择、归一化、程序定义及 activity input 生成的边界都应先冻结并与同信息基线共享；这不是本轮已完成的步骤。

## 本轮前提更新与停止点

**可以更新的前提：** 有一手方法依据的“同研究、同名义给药条件、24 h 实测 RPPA 与 72 h resazurin 功能”局部资源存在，且作者公开静态文件实际可取。无需继续用跨库药名交集冒充这种条件对应。

**保持未知：** 可逐行复核的完整剂量/载体/培养/时间及重复合同、功能原表与条件索引对齐、重复独立性、原始与派生字段区分、`pert.txt` 输入来源、每一程序的不同化学实现和可执行的整药确认划分。它暂可作为单背景开发资源线索；不能声明预测、跨药程序、机制、决策或迁移已经合格/成立。

下一项缺失证据是**不看结果好坏的原始观测—条件—重复映射**：在事先记录的读取协议下明确数据文件的行列角色、原始/汇总层级、样本和批次 ID、DMSO 锚点、剂量映射与原始信号/功能分离，并解释 S1C 缺失的 45 及 cell-cycle 时间矛盾。若只能取得已经联合拟合/汇总的无重复模型矩阵，则应明确将可做主张降为受限单背景预测开发，不能用补模块消除资格缺口。

本分支至此停止：Q1 一次主题查询、一个核心研究、原始响应约 1.40 MiB；不再查引文，不改端点/剂量，不挑功能值，不训练，不晋升 src，不发布 Git。
