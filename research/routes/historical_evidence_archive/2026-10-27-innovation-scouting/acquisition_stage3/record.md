# record —— R198-A5 取证策略设计（过程 / 纪律 / 边界 / 限制）

2026-10-27。角色：独立设计/执行审计员（R198-A5）。工作目录 `D:\MAESTRO`；解释器 `D:\anaconda\envs\maestro\python.exe`（Python 3.11.16 / pandas / numpy）。本文件记录**过程与纪律**；设计与数字见 [spec.md](spec.md) / [cost_model.md](cost_model.md) / [prior_art.md](prior_art.md) / [protocol_draft.md](protocol_draft.md)；hashes 见 [usage.json](usage.json)。

## 1. 范围与纪律（写死）

- **只做设计、成本模型与先例核验**：未运行 acquisition、未训练模型、未回放、未模拟 acquisition 收益；**没有新的生物效果/决策收益数字**。文中所有成本、wells、keys、headroom 数字均为**规划算术**或他人已发表描述，已逐处标注。
- 只写 `research/2026-10-27-innovation-scouting/acquisition_stage3/`（`spec.md`、`cost_model.md`、`prior_art.md`、`protocol_draft.md`、`record.md`、`usage.json`）与 `tmp/`（`a5_cost_arithmetic.py`、`a5_cost_arithmetic.json`、运行日志）；**未改**其它目录、INDEX、SYNTHESIS、git、其它 sibling 子目录（只读引用 `conflict_signal/spec.md` 的 A1 更新器与 DPG 接口）。
- **不是 A1/A2 的复活或换聚合**；不启动 B/C/acquisition；不换端点/分层/δ；不按 Q 大小挑层；不用 Q 结果反推模型选择（本任务未读 Q 效果、未跑 Q 分析）。
- 与 R198-A1 的边界：A1 的 M1（PRU-CC 更新器）只作为**固定更新器候选 U1**引用；A1 的 M2（DPG）只作为**候选 acquisition 策略**（S5 可选）；**A5 不评价 A1 机制收益**（那是 A1 的 P4/P5）。

## 2. 读取的输入（只读；hashes 见 usage.json）

**必读/背景**：`research/2026-10-27-cross-domain-directions/{report.md,directions_v2.md,evidence_notes.md}`（用户建议第 3 步与 H3；BATCHIE/GoBOED/PDBoED 先例；不可外推边界）；`research/SYNTHESIS.md`（C136/C144/C154/C155/C156/C167/C171/C172 段落）；`research/2026-10-27-handoff-method-audit/report.md`（R163/R187 的可引用范围校正）；R2 整板/KG 回放（`research/2026-10-26-agent-cell-evidence-r2/{report.md,PROTOCOL.md,data_mapping.md,baseline_action_metrics.csv}`）；R187 药对 AL（`research/2026-10-27-agent-cell-identifiability-r187/{report.md,record.md}`）；R189-I003 先例核验（`research/2026-10-27-detectability-acquisition/evidence.md`，F01–F16 逐字引文清单，本轮引用其锚点、未重跑其原文核对）；R198-A1 机制规格（`research/2026-10-27-innovation-scouting/conflict_signal/spec.md`，只读 U1/DPG 接口）。

**物理锚点的一手核对**：Jaaks 2022 Methods（本地 `data/external/research_sources/20261022/intervention_program_renewal/data_auditor/jaaks_primary_lineage.body`）用于 1,536-well、2×7 anchored、每板 5 anchor-alone/4 library-alone、播种优化 6×224 wells、day=1 板、QC 阈值（CV<0.18、Z>0.3、RMSE<0.2、~1.5% 排除）、3,106 板、生物重复 n=2–18。**只读方法文本，不读响应值。**

## 3. 实际执行（只有规划算术；无 acquisition）

| 步骤 | 内容 | 结果 |
|---|---|---|
| 成本算术脚本 | `tmp/a5_cost_arithmetic.py`：物理锚点 → 动作 wells → 三场景 CU → C136 规模（1,600 keys）路径 → 100,000 CU 等成本拟合 → ±50% 敏感性 → R2 headroom 记录 | 输出 `tmp/a5_cost_arithmetic.json`；**连续两次运行 SHA256 相同**（`1C27DA82…FCF9D9F`） |
| 设计写作 | spec / cost_model / prior_art / protocol_draft / record | 见本目录；所有规划数字标注为 planning |
| 有界检索 | 2 个 pass、共 ~7 条查询（见 prior_art §3）；命中 BATCHIE/SHIFT-DRP/多保真度 BO/inference set design/VOI 样本量等近邻；**未命中**"controls/单药参照/失败/重复/批次全计价 + menu-oracle 门槛 + 决策损失"的直接比较 | 记录于 prior_art.md；不声称新颖性 |
| **未执行** | acquisition、训练、回放、收益模拟、新数据下载、任何 QC/评分类计算 | 明确边界 |

## 4. 关键设计决定（以及为什么）

1. **成本用 planning cost units（CU），不用美元**：项目没有认证的采购成本记录（R2 已声明"货币成本未认证"）；给出系数区间与三场景，要求冻结前用报价/LOI 替换。避免把编造的货币数字写成事实。
2. **物理锚点优先**：GDSC 1,536-well/2×7/对照/播种优化、BATCHIE 384-well/2 板 766 wells、DrugComb 剂量矩阵、BeatAML 7×1、R2 3,106 板/5 细胞/30 动作——全部来自一手方法或本项目实测，成本算术只在其上叠加系数。
3. **等成本不是等行数**：给出等成本核查算法（打包规则、残余预算 ≤ 最小动作、三场景一致性、禁止等 wells/keys），并给出 100,000 CU 同一预算下 46 个整板动作 vs 20,985 个单剂量 key 的示例，说明"同一预算可买形状差 450 倍"。
4. **cell-line 广度是隐藏的支配性成本**：C136 的 1,600 keys ≈ 13 对 × 125 细胞；每新细胞 setup（播种优化 1,344 + day1 1,536 wells）在 125 细胞下 ≈ 3.6×10^5 wells，使 central CU 在 setup charged 与 sunk 之间差 2.5–5.2 倍 → 冻结时必须写死 setup 会计规则，否则不同 cell 广度的策略不可比。
5. **成本与检定力分开**：成本模型只给 wells/CU；`n_eff`/MDE/δ_min/headroom 属于统计/菜单层（C136 1,600 keys→80%；200→0.46；C144 分配近中性；C154/R187 饱和；C171 n_eff≈189 教训）。写死门槛 `MDE_decision ≤ δ_min ≤ headroom`，并明确**不得**用 wells/keys 冒充独立单元、不得用相关指标替代决策指标。
6. **菜单接近 oracle 的准入闸**：R2 的 5 细胞菜单 headroom 仅 **0.004343**，而 R2 的 KG−random CI 宽 ~0.145 → 该菜单不可检验 acquisition；A5 要求每个候选菜单先算 headroom 与 MDE，headroom < MDE 直接停（`menu_near_oracle`），换菜单需独立理由。
7. **固定更新器先于采样**：比较在冻结更新器（U1 A1-M1 / U2 层级 EB / U3 GP）+ 同信息 + 同算力下进行；禁止策略自带更新器/调参；基线也要正常更新（不能冻结）。
8. **先例：不声称新颖性**。decision-focused BOED、BATCHIE 整板选择、GP-KG、EVSI/ENBS、成本/保真度感知采集均有覆盖；未发现的是"完整成本账 + headroom 闸 + 决策损失"的组合，属评估/工程修正，不构成新算法（与 R189 线 B 结论一致）。

## 5. 偏离/限制（披露）

- **未做**任何 acquisition 收益模拟：本任务的"必须交付"只要求设计/成本/先例/协议草案；**没有跑任何策略、也没有模拟 NB/后悔值**。
- 成本系数为 planning 区间（非货币实测）；`eta`（板利用率）、`fail_frac`（失败率）、`replicates`（技术 vs 生物重复）未认证；cell setup 记账（charged/sunk）未定——这些都会在冻结前补齐（protocol_draft §P9）。
- 先例检索有界、非穷尽；部分条目仅题录/摘要级（prior_art §3）；"未发现"不等于不存在。
- 成本算术中的"C136 规模 = 1,600 keys ≈ 13 对 × 125 细胞"是 C136 的规划锚点，不是本次 acquisition 任务的效应量；不同端点/任务下所需 keys 另算。
- 未读任何 acquisition 相关响应值/终端数据；不构成效果证据。

## 6. 产物（hashes 见 [usage.json](usage.json)）

| 文件 | 说明 |
|---|---|
| [spec.md](spec.md) | 菜单/动作/不可购买项、固定更新器契约、比较器、指标、停止规则、泄漏防护、边界 |
| [cost_model.md](cost_model.md) | 物理锚点、动作 wells、三场景 CU、C136 规模路径、等成本拟合与核查算法、±50% 敏感性、成本↔检定力分离、限制 |
| [prior_art.md](prior_art.md) | 先例逐条覆盖（已覆盖/部分覆盖/未发现）+ 锚点 + 有界检索记录；不声称新颖性 |
| [protocol_draft.md](protocol_draft.md) | 若冻结须写死的 P0–P11（占位 `<...>` 待填）、失败类别、停止条件、挑战者问题 |
| [record.md](record.md) | 本文件 |
| [usage.json](usage.json) | 运行时账 + 输入/交付 SHA256 |
| `tmp/a5_cost_arithmetic.py/.json` | 确定性成本算术（两次运行哈希相同） |

## 7. 下一轮接口

- 若 Lead 决定推进：先补齐 protocol_draft §P9 的全部数字（成本报价、菜单、headroom/MDE、δ_min、更新器选择与等价性检查、预算、挑战者意见），再冻结 `PROTOCOL_Q3.md`；**第 2 步未成立则不执行**。
- 若本设计被挑战者推翻：记录推翻理由（headroom/MDE/成本/泄漏/边界），不换名重提同一比较；A5 的保留物 = 可审计的成本/菜单/等成本核查设计 + 先例覆盖结论。
- 总目标状态不变：未达成、无机制/临床主张、B/C/RSI 未启动。
