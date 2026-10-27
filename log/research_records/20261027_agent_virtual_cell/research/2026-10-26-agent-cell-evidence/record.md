# Agent × 虚拟细胞共同学习：证据条件与最小检验

日期：2026-10-26（Asia/Shanghai）。状态：进行中；不是已验证创新。

## 研究简报与预算

研究问题：对早期肿瘤药物候选/背景选择，能否将有适用条件的竞争性功能预测、最小可执行取证、条件边界修订连接起来，改善独立药物决策并迁移到未见细胞与药物？机制结论需要正交参照，名义靶点及表达响应不能代替参与/因果证据。

用户授权：审计、2025—2026 一手证据检索、在 research/ 中最小实现/实验；所有测试使用 D:/anaconda/envs/maestro/python.exe。不晋升未经验证代码，不重做已失败的有限交互选择、预测分歧采样或有限搜索冒充 RSI。

本轮上限：一次有界侦察＋两次定向补查（共三 pass，所有 agent 共用）；每候选初版后最多两次实质修订。探索替代原则占侦察的一部分。默认最小实验 CPU、单个可复跑研究脚本；没有证据条件就执行资格/可辨识性检查并停相应主张。物理费用未知时只报告逻辑查询，不声称等物理成本或等实际算力。

验收：先核实药物×细胞交叉、靶点参与/遗传参照、独立功能终点、重复层级。防止跨任务/来源与同标签泄漏。与同信息、同反馈的强预测器、重训练、层级模型，以及随机、GP、决策主动学习分开比较更新与采样贡献。主要评价决策效用，细胞/独立任务为统计单位，区间与停止条件预先写明。无法执行项写明缺口，不用模拟阳性补足。只有独立决策和跨任务迁移成立才研究元学习/RSI，并与等预算程序搜索比较。

## 初始审计

Git HEAD：6d7b9e61（开始时）。原有修改：log/STUDY_INDEX.tsv、research/STUDIES.json；原有未跟踪：log/RESEARCH_IDEAS.md、两份 knowledge_reality sealed CSV、research/eight_directions_20261026/。不暂存、不提交、不读取 sealed 数据。

工作区未找到实体 AGENTS.md（根目录、D:/、research/ 与 rg --files --hidden 查询）；本聊天提供的 karpathy-guidelines 是适用指令。采用最小可验变更，保留旧证据。

已读：README.md、research/README.md、eight_directions_20261026/report.md。前轮交互修订和分歧采样未获必要决策收益；方向4/5受证据资格限制；方向6/8未达元学习/RSI定义。前轮原始字段与旧派生 PRISM 矩阵不一致，当前研究不能直接相信旧缓存。PRISM 已暴露，重划分不能成为独立确认。

## 执行记录

- 请求创建 /goal 时工具报告已有未完成目标；保留用户更新后的活动目标，不重置预算或状态。
- 详细证据、检索、候选冻结与独立审查将在本目录记录。元数据层模型有效设置与 token/费用没有遥测时记 unknown。

## 本轮最终记录

状态：ROUND_CLOSED_WITH_QUALIFICATION_FINDINGS；总目标ACTIVE / NOT_ACHIEVED。未训练/晋升候选，未执行元学习/RSI。交付[report.md](report.md)。

研究线选择依据：按整个历史的条件缺口，而非只追最新得分；保留旧方向1正交参照、方向5重复/暴露溯源的可重启问题；不重复旧有限交互选择、预测分歧或有限搜索RSI。原始BATCHIE方法提供duplicate/random validation/CRISPR新可核设计证据，但不自动解除培养独立性和机制识别缺口。

候选：I001.v1见candidate.md，I001.v2见candidate_v2.md（一次实质修订，未用满2次上限）。由“资源未资格化”转为分开独立采集验证、同源功能补全、跨实体与跨任务迁移；算法更新算子尚未区别于层级模型＋决策实验设计。没有将下一代命名当作学习。

### 观察与决定

- E001 observed：maestro执行原始设计普查。PRISM2.5μM有1281相同完整药物批次ID，568为STR metadata身份交集；无响应矩阵规模主张。BATCHIE43198无向药物剂量对中29202只一个细胞标签；30499条件有两个文件，367个观测plate group不等于可购买动作菜单。
- E001探索性追加诊断：原文辨认random-validation阶段后，未读响应情况下核实3448条QC合格combo、3412唯一标签剂量键、15训练交集、3397非交集。没有新药/细胞标签。原始名称与剂量无向化不是化学实体/同义名归一；独立Decimal与NFKC/strip/casefold敏感性结果一致。
- 15键皆为MSKEWS-33838的Axitinib0.1μM组合，训练14轮板231/232对validation板267。有向交集仍15。库位置/实体关系待核，不称论文错误。
- P006 reported/inspected：BATCHIE正式发表2025-01-02，11—15轮duplicate，原文写72h处理＋24h读出、另采随机验证、DepMap遗传解释；有这些实验不等于本候选条件级正交识别已完成。失败QC部分由响应差产生，前瞻不能免费给策略，所有失败测量须计成本。
- H002/H003/H004 planned，不曾拟合/比较，不报告虚构增益/区间；本轮CI=null，因为只有确定性计数。科学失败分类为识别证据未齐，不是药理规律被否定。

### 人员、独立性与来源范围

| handle | 职责 | requested model/effort | effective |
|---|---|---|---|
| /root | 审计、候选开发、执行和综合 | 父会话配置，未修改 | unknown |
| /root/primary_evidence | 一手证据及生物信息需求 | gpt-6.1-sol/medium | unknown |
| /root/principle_scout | 未曝光初始候选的跨域原则侦察 | gpt-6.1-sol/high | unknown |
| /root/independent_challenge | 冻结后最小上下文审查、独立复算 | gpt-6-astra/high | unknown |

primary_evidence文件说派发设置未向worker暴露；上表仅是协调者实际spawn参数，不是运行确认。审查者先写初评，再收到协调者措辞修正/后续说明，时序已存审查文件；未参与核心候选开发。官方模型指引URL已实际打开（发生跳转），运行可用handles以工具schema为准，未据网页认定有效执行设置。未外调模型、未改全局配置。

实际检索3/3 pass：侦察8＋4 query（含替代原则），协调者定向3 query，独立最终2 query，共17；没有以agent/下载重置上限。逐式来源/日期/读取范围见primary_evidence.md、principle_scout.md、source_notes.md、independent_review.md；4篇受限，没有给元数据升级为全文。reference工具verify：9条目、4 HTML、4 restricted、1 pending（BATCHIE原始XML另存sources）；代码9 not_verified，零复现。

### 验证、偏差与停止

在D:/anaconda/envs/maestro/python.exe执行audit.py和独立independent_verify.py，exit均0；独立复算全部关键计数及10项输入/代码/协议hash一致。最终audit复跑qualification.json字节相同，SHA256 fc1eead4a2d1c5c197847486030233fdc530574050c91af73f9f14ee9a2343f9。哈希只证明该产物一致，不代替语义审查。

首次断言把控制孔缺失剂量当错误，失败后显式保留missing token，仍要求真实组合剂量已知；这是工程修复，未读响应/调效应阈值。初稿候选“规范化”已按审查改为真实实现的标签/剂量无向化。随机阶段检查是来源驱动探索诊断，不声称全部预注册。协议、脚本各有确切hash，后续修改应新版本，不能无痕覆盖已审实验。

停止对应机制主实验和收益主张；重启需条件级身份、stage/protocol、独立培养/终点、正交参照、动作与成本映射，以及确定且不同于层级更新的候选算子。现有数据并非全部不可用，可另研究严格限定的同源功能补全；但不能用该题代替原目标的独立收益与迁移门槛。没有充分证据标记goal complete。
