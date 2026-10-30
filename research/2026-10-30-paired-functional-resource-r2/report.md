# 论文迁移与配对资源审计报告 — 2026-10-30

## 结论先行

用户提供的 You et al. 预印本（*Virtual-cell verification enables self-auditing AI discovery for immune rejuvenation*，DOI `10.64898/2026.08.04.742916`）适合作为虚拟细胞研究的**设计参考**：它把方向性表型、紧凑状态表示和外部功能反馈放进同一个审计闭环。它不能直接作为当前项目的可复现实验数据，也不能把“Analyzer–Planner–Auditor”或 `mean → min` 规则当作新机制。

本轮对唯一可能桥接资源的独立审计显示，`bridge_transcriptome_viability.csv` 是跨资源的 derived join。684 行的转录条件都写成 `24h|10000nM`，而 PRISM 端是多剂量 pooled-viability 曲线的 AUC；桥表没有匹配暴露时间、vehicle、preparation/plate、独立生物重复或原始曲线来源。它不满足独立功能配对契约。因此本轮结论为：`data_unavailable`、`NO_EXPERIMENT`、`NO_PROMOTION`。

## 从论文中可以迁移的三项操作

1. **保留方向性轴。** PACE 将细胞类型和模块的改善/恶化方向分开记录，避免用一个平均分掩盖“某一轴改善、另一轴恶化”。在药筛中可把生长抑制、应激、分化、死亡或分泌功能分别作为带方向的轴；聚合规则必须在功能数据解锁前冻结。
2. **使用可审计的紧凑状态。** CellQ 的 token 数量和语言模型不是迁移重点。可迁移的是：每个 `(cell, drug, dose, time)` 保存能回溯到原始测量的模块状态、置信度、QC 和更新日志，而不是只保存一个排名。
3. **让外部功能读出约束更新。** Analyzer–Planner–Auditor 的价值在于模型代理不能自证。一次独立功能结果应明确触发哪条局部规则的更新、隔离或 abstain，并记录失败替代解释。这个操作层面的闭环已经被 DrugReflector、BATCHIE 和 MDA 等工作分别覆盖，不能作为本项目的宽泛首创主张。

## 现有先例如何限制新意

- **DrugReflector（Science 2025）** 已将转录代理、独立表型反馈和后续筛选 signature 修订连成药物发现闭环。
- **BATCHIE（Nature Communications 2025）** 已用 posterior uncertainty 选择下一批真实组合 viability 测量，并做外部验证，是药筛中不确定性选测的强普通基线。
- **MDA（2026 preprint）** 已覆盖 LLM 机制提议、预测失败触发模型扩展、后验更新和 VoI 选实验的通用模式。
- **CellQ/PACE（2026 preprint）** 最接近“虚拟细胞状态 + 外部功能 + 规则更新”，但当前无法核实完整配对矩阵、代码、日志和等预算的整药/整背景 holdout。

因此，单纯加入 Agent 角色、把平均分改为最小值、把 transcriptome 与 viability 按药名/细胞名连接，均不足以形成项目主机制。

## 684 行 bridge 的数据契约结果

| 条件 | 结果 |
|---|---|
| 药物×细胞身份 | 部分具备（296 个化合物、A549/MCF7/PC3），但只是跨库连接 |
| 剂量 | 不满足：转录端为 10,000 nM；PRISM AUC 汇总多剂量曲线 |
| 时间 | 不满足：转录端为 24 h；PRISM bridge 没有匹配时间 |
| vehicle/control | 不满足：桥表丢失同条件 control 键 |
| preparation/plate | 不满足：PRISM 原始表有 plate/well，但桥表未保留；转录 preparation 不可追溯 |
| 独立重复 | 不满足：MTS010 是 technical redo，且桥表无 biological replicate ID |
| 独立功能终点 | 不满足：pooled viability 仍是另一种筛选读出，不是 washout recovery、clonogenicity、apoptosis 或分泌功能 |
| 靶点/遗传参照 | 不满足：MoA/target 是注释，不是同条件 engagement 或遗传干预 |
| 原始 provenance | 不满足：SciPlex prepared 文件和 PRISM 曲线参数来源当前不可追溯 |

这项审计只证明资源不具备当前主张所需的信息，不证明 transcript–viability 关系不存在，也不否定 PRISM 或 LINCS 作为普通开发数据的价值。

## 保留的窄候选：耐久功能门

Astra 分支提出一个比 I304 更窄的问题：廉价短期 growth/viability 是否能在限定的 cell×drug×dose 域内，保守地证实洗脱后不可恢复的功能损失。令 `z` 为 cheap response，`q` 为洗脱后固定恢复窗口内的 clonogenic recovery，令 `r=1-q`。虚拟细胞只维护可审计状态：

```text
S(c) = {z curve, frozen bins, calibrated interval for r,
        independent-preparation count, safe/unsafe/unknown flag, budget}
```

Agent 的三类动作固定为 `measure_q`、`update_local_certificate`、`abstain/quarantine`。它只在一次 `q` 结果可能翻转阈值决定时购买匹配功能测量；反馈只改变预先声明的 cell/bin 范围，失败时收缩安全域。验证必须与直接 q、cheap-only、hierarchical two-endpoint、conformal/selective prediction、fixed/random panel 和标准 VOI 同预算比较，并按整药物、整细胞背景和必要时 scaffold 留出。

这是一个待验证的功能限制问题，不是现成算法或已证实的 Agent 优势。只要普通层级模型或 conformal rule 达到同样的决策效用，结论就应降级为 assay calibration；若没有合格的 `z,q` 配对矩阵，应停止该线。

## 当前可执行边界

- 不把 bridge 的 `discordance` 当作机制错误标签。
- 不把 PRISM/LINCS/GDSC/DepMap 的药物和细胞交集当成同条件配对。
- 不打开 sealed/confirmation 数据，不用文件存在、测试通过或辅助 Agent 的 PASS 代替科学证据。
- 不修改 `src/` 或 `tools/`；当前没有独立验证成果可晋升核心代码。

下一次重开只接受能逐行提供 drug、cell/background、physical dose、exposure time、vehicle、preparation/plate、独立生物重复、cheap proxy 和独立功能终点的公开资源，并在解锁测试结果前冻结阈值、预算、整药/整背景 holdout 和普通强基线。
