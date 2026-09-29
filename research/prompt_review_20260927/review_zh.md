# MAESTRO prompt 修改判断

审阅日期：2026-09-27。对照本地提交 `e5ad68f` 的相关文档与代码进行了静态核查。本次任务是修改 prompt，没有运行研究实验、重跑测试或修改系统实现。

## 总体判断

原 prompt 的研究方向应保留：先确认任务是否有可利用的信息，再讨论模型和 planner；模拟不能替代实测；最终贡献必须落在实验选择和决策上。

主要问题不是内容不够，而是把研究愿景、现有缺口、实现要求和验收标准混在一起。直接执行容易重复建设、提前消耗测试集，或者因数据不支持而被迫做出名义上的完整系统。

修订版将其改成“核实现状 → 最小补缺 → 数据与任务准入 → 有条件实验 → 冻结确认”的执行合同。默认交付审计和计划，与原文末尾 Expected Output 一致；明确选择 MINIMAL_IMPLEMENTATION 时才实施最小改动。

## 必须调整的内容

| 原文问题 | 修改方式及原因 |
|---|---|
| 多处要求创建已有能力 | 先列 SATISFIED / PARTIAL / MISSING / CONTRADICTED / UNVERIFIED，复用现有代码。`protocol_v2/contracts.py` 已有状态、白名单视图、truth-free episodes 和独立评分；`registry.py`、`calibration.py`、`headroom.py` 已存在。存在不代表覆盖充分，也不能直接判定全缺失。 |
| “重建 Evidence Graph”容易扩大工程范围 | `models.py` 已有 evidence kinds，`outcome.py` 已有证据准入与更新，`provenance.py` 已有 SourceClusterIndex。应补完整链路和缺失约束，不预设新数据库或第二套类型体系。 |
| 把历史结果写成普遍定论 | 保留数字，但要求绑定任务、分母、规则、时间、区间与暴露状态。345–813 是特定历史设定的功效估计；不能作为所有新任务固定样本量。 |
| 把所有 external 都等同 unseen study | `protocol_v2/DIAGNOSIS.md` 第 2 节第 4 项说明 GSE70138 的模型和验证器使用同研究内参考化合物拟合。应分别标注 unseen compound、scaffold、context、study，以及是否做 target-study adaptation。 |
| 新 MeasurementState 与已有枚举混在一起 | “是否计划/执行/QC 合格”与“undetected/ambiguous/eliminating”不是同一维度。先做无损映射或分字段，不能简单替换枚举丢失信息。 |
| 防泄漏只管标签字段 | 补上 QC 筛选、归一化、batch correction、PCA、reference pool、缓存、预训练模型和知识库答案泄漏。metadata 名称不保证字段真的与结果无关。 |
| 所有阶段都禁止 outcome-derived construction，过于绝对 | 禁止 held-out/sealed outcomes 影响构建；允许训练折内结果生成参考规则和假设池。必须说清楚数据来源、拟合阶段和允许用途。 |
| RNA + morphology 默认可以合并 | 加配对与可比性准入：化合物一致仍不足，还要核对细胞、剂量、时间、对照和 assay。无真实配对不能拼成回放 episode；插补只能是预测。 |
| r(t) 被当作免费可用特征 | 明确 measured / estimated / unknown；新测 engagement 或 proximal function 要计成本与等待时间。不能从待预测终点反推 r(t) 再预测同一终点。缺资料时 NOT_READY，不强制实现 latent head。 |
| 确定性规则被误读为确定的机制真相 | 增加噪声、检出能力、假阴性、重复测量和 episode 级错误剔除风险。规则可重复不代表生物学上无误；阴性结果未必可以排除机制。 |
| H 的含义与监督来源未规定 | 要定义 H 是候选机制、类标签还是参数化假设，以及数据支持什么条件分布。给模型输入 H 不等于识别了因果干预分布。 |
| 只维护有限机制集合，未落实不完备性 | 增加 UNKNOWN/OTHER、非互斥/多靶点假设、空集矛盾处理、证据版本与修复。只剩一个候选不自动等于证实它。 |
| p_correct/p_wrong 容易需要隐藏真值 | 优先预测观测或注册的读数类别，再由假设和规则推导错误风险。不能在推理阶段借助测试真值定义模型输出。 |
| Robust score 看起来安全，但风险项也不可信 | 保留作待验证启发式，明确校准、权重、量纲和敏感性。set-valued state 或 risk penalty 本身都不提供安全保证。 |
| Calibration 被排到最后 | 现有 forecast 的 E-CAL1 应早做；新模型再重新校准。评价 frozen policy 实际选中的 action、覆盖率和整个 episode 的累计风险，不只看总体 Brier。 |
| Headroom gate 可能导致先打开最终测试集 | headroom 选任务只能用 development；sealed cohort 的 headroom 在最终揭盲后报告，不允许因结果不好而换 cohort。oracle 的事后全知优势要说明。 |
| 模态只有提高 ceiling 才能保留 | 改为预注册的 discrimination / risk / cost / time 贡献。更便宜且不损害正确性的测量也有价值，即使绝对 ceiling 不变。 |
| KB 负责生成 action，却要求所有消融 menu 相同 | 拆成两个实验：固定 menu 测排序，允许 menu 变化且预算相同测生成。否则把 KB 的目标贡献人为屏蔽。 |
| G0–G4 名称可能覆盖旧协议定义 | 新命名 WM-G0–WM-G4，且必须注册数值门槛。区分 FAIL、INCONCLUSIVE、NOT_READY，不把无显著差异一律当模型无用。 |
| G3 “任意指标改善”允许事后挑成功指标 | 提前选一个主 estimand。正确率主张与成本优势主张分开注册，后者要求决策质量非劣；保留错误风险和资源约束。 |

## 建议删减或降级

1. 删掉强制“至少创建八个模块”的结构要求，保留八类职责和验证要求。
2. 把“三个 head”改成三个可审计职责，不指定神经网络架构。
3. 不要求首轮同时接入所有数据库、跑完所有 calibrator 和全部消融。按已修改组件和数据支持决定。
4. 将大型 JEPA、通用 RL、多 agent、全量图像处理和 combination benchmark 留在后续候选，不进入首轮交付。
5. 不把“任何弱 headroom 任务都不用”写成绝对禁令：它们仍可测安全、退化、成本和合理 defer。
6. 合并重复的审计清单与交付表。中文材料开头称“10 个工作包”，正文实际列到 15 项，容易被当成新的独立工作范围。
7. 将“最终测试数据在系统层面不可访问”改成 evaluator-only，并说明可执行的权限边界；哈希或 Python 属性封装不足以阻止同权限任意代码读取文件。

## 首轮建议执行顺序

1. 静态审计及必要的已有结果复现：确认实际缺口、现有默认路径和历史结果性质。
2. 补最小数据/证据/评分边界：建立可验证的合同，而不是全仓重构。
3. E-DATA1：先确认同一批真实可比数据是否支持更有信息量的 action menu。
4. E-CAL1：利用已有预测检查跨研究与选择后风险，界定哪些风险承诺目前不能做。
5. E-WM1：只有时间和干预强度数据、推理时可得性及样本量过关才进入。
6. 一个最小的 second-measurement planner，完成对应消融后再考虑外部确认。

E-CAL1 的探索性分析可与数据资格核查并行；这不意味着必须启用多个 agent。外部样本可先做 metadata census，但不能提前用 outcome 检查它“好不好用”。

## 本次核查依据

- `research/protocol_v2/README.md`：已有模块、headroom、校准与 attribution 结果。
- `research/protocol_v2/PROTOCOL.md`：estimand、scoring subset、public view、现有 gate 定义与外部数据状态。
- `research/protocol_v2/DIAGNOSIS.md`：历史污染、GSE70138 的 38/673 选择范围和同研究参考拟合限定。
- `research/protocol_v2/contracts.py`：MeasurementState、PublicContext、reference_pool、truth_free_episodes、mechanism_endpoint。
- `src/maestro/models.py`、`outcome.py`、`provenance.py`：类型化证据、准入规则、状态更新和证据来源聚类。
- `src/virtual_cell/interface.py`、`src/maestro/planning.py`：现有预测/拒绝契约与规划路径。

这些是用于修改 prompt 的重点核查，不构成对整个仓库“已无泄漏”或“所有测试通过”的保证。完整可复制的英文替代稿见同目录 `revised_prompt.md`。
