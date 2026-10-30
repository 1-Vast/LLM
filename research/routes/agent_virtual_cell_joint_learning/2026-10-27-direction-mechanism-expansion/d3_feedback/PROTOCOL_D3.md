# PROTOCOL_D3 —— R200 方向 3：固定反馈后的未查询泛化（设计草案 v0.1）

2026-10-27 · 角色：ON1/ON2/ON2.2/ON3 执行者（非提案者）· **状态：DESIGN DRAFT，未执行。**
本文件只做 **单一剂量资源资格 + 固定反馈/更新器比较的预注册设计**；**不运行效果、不拟合预测、不比较 acquisition、不读原始响应值做统计**。须经独立挑战者只读复核 + Lead 批准后，另立执行协议；本文件不构成结果、独立确认、迁移或决策收益声明。

## 0. 一句话设计

在 O'Neil complete-case 的 **单一 anchor 剂量层**上，固定一小包功能反馈（每折 24 个单剂量单元，所有方法同包同成本），比较四类反馈更新器与强对照（全历史重训、普通适配、层级、GP、投影核），主终点是 **未查询 held-out 细胞中成员×伙伴的 Spearman ρ**；一个主假设：关系冲突更新器超过全历史重训 ≥ δ_min=0.10。**不做 acquisition 比较**；不拼接 Jaaks ΔEMAX。

## 1. 资源资格（metadata-only；verdict = `qualified_with_conditions`）

### 1.1 资源与单剂量层定义

- **来源**：`research/2026-10-27-core-module-design/oneil_dev/on2.json`（ON2 v2.2 frozen metadata；O'Neil complete-case、batch1 target30；`design_frozen_qualified_with_conditions`）。
- **单剂量层**：从冻结的完整 4×4 成员剂量网格中，**预先固定** member dose index=4 × partner dose index=4 的一行；每个 member context 取该 anchor 行；不插值、不按响应选剂量。**注意：这是从 full-grid 派生的 single-anchor 层，不是独立 single-dose screen。**
- **单元**：`Δ(c; a, a'; b) = mean_viability(a, b, anchor, 4 technical reps) − mean_viability(a', b, anchor, 4 technical reps)`，同 cell/partner/role/anchor；一个 member pair 一个 unit。
- **技术重复**：每个 member 4 个 technical replicates；一个 Δ unit 有 4 个 replicate-level differences；**technical replicates = precision only，不是独立培养/independent n**；每 unit 的独立 culture 数 = **1**；按 cell/partner/member-pair 聚类。

### 1.2 资格数字（metadata-only；无响应值）

| 指标 | 值 |
|---|---|
| 单剂量单元（target30） | **340,088** |
| 上下文（partner-role contexts） | **2,149** |
| 目标细胞 | **30** |
| 折数 | **5**；每折 **6** 细胞（继承 ON2，不重分） |
| 每折单元 | **68,152 / 66,743 / 66,556 / 69,738 / 68,899** |
| 每折上下文 | **432 / 427 / 427 / 432 / 431** |
| 每 unit technical reps/member | **4**（Δ 的 replicate-level differences=4） |
| 每 unit member wells / total wells | **2 / 8** |
| 每 unit 独立 culture | **1**（技术重复不得充 n） |
| target30 完整成员上下文 | 44,070 / 45,474 = **96.91%** |
| complete-case rows all4 | **363,090 / 368,832 = 98.44%** |
| batch3 complete-case rows | **0 / 5,040**（全失） |
| 15-row pair-cell | **702** |
| 缺失（viability2/3/4） | **78 / 198 / 5,742** |
| Jaaks overlap 排除细胞 | **9** |
| batch2 | **disclosure-only**（1,129 units/136 contexts，不进 primary） |

### 1.3 资格判定：`qualified_with_conditions`

原因：单 anchor 层有足够 units/contexts/target cells/folds 做**开发性**固定反馈比较；但必须带以下条件：

- **O'Neil 仅开发性**；不是 independent confirmation / migration / decision benefit / mechanism。
- **technical replicates 不是 independent cultures**；4 reps 只做 precision/calibration；n_eff=held-out cells (6, conservative)。
- **batch3 全失**；**702 个 15 行 pair-cell**；缺失机制未知、无 MCAR/MAR 假设；complete-case primary。
- **单剂量层是从 full-grid 派生**，不是独立 single-dose screen；不能声称这是独立剂量资源。
- **无双药/单药参照**；只有 combination viability；不拼 ΔEMAX。
- ON2 v2.2 本身是 post-observation 资格修订，不是 pre-registration；D3 设计须独立挑战后才可执行。
- **MDE80=0.0287644381 是 ON2-EX 借用先验**，不是本资源实测；执行前必须测 sigma_e/MDE；MDE>δ_min=0.10 → `design_invalid`。

### 1.4 备选 Jaaks 单一 anchor：`not_qualified_for_D3_endpoint`（本设计不用）

- A0/Q2 的 matching/conditions 是围绕 **`SYNERGY_DELTA_EMAX`** 端点；D3 明确禁止 ΔEMAX 拼接。
- 若用 Jaaks 单 anchor，必须有**独立的 viability 端点 + A0 匹配/剂量布局/端点可比性**；当前本地记录未认证。
- 因此本设计只走 O'Neil viability；Jaaks 仅作为未来独立测量桥/对照备选，不进入本设计。

## 2. 问题、切分与固定反馈预算

### 2.1 科学问题与主假设（唯一主假设）

**H_D3（唯一 primary）**：在**相同固定小反馈包**下，`U_conflict`（关系冲突更新器）在 **held-out 细胞的未查询成员×伙伴**上，Spearman ρ 比 **C2 全历史重训**高至少 **δ_min=0.10**。

- **算法差异**：U_conflict 使用反馈残差对冻结的 pair/partner 可加关系的**冲突**来更新 pair/partner/member 项；C2 用全部历史 + 反馈重新拟合。两者同数据、同特征、同反馈包、同调参/计算预算。
- **一个 primary contrast**：`Δρ = ρ(U_conflict) − ρ(C2)`；其余 updater/control 比较均为 secondary/描述性。
- 若只改善已测/反馈点、held-out 未查询不改善 → **停止 feedback-generalization 主张**；若普通强对照等效/更好 → **撤 unique-operator 主张**。

### 2.2 切分（cell holdout；继承 ON2 折）

- **5 折**：每折 **24 support cells** + **6 held-out/query cells**（继承 ON2 target30 的 5×6 分组，不重分、不换 seed）。
- **反馈**：只在 support cells 中购买固定小包；**held-out 细胞不测量、不作为反馈**。
- **目标**：held-out 细胞的**全部单剂量单元**（成员×伙伴），全部为未查询；每折 66,556–69,738 units，总 340,088。
- 不采用“仅随机留条目”；不做 item-level 随机泄漏；primary 是整细胞留出。

### 2.3 固定反馈包与成本（所有方法完全同包）

| 项 | 值 |
|---|---|
| 每折反馈单元 k | **24**（固定） |
| 总反馈单元 | **120**（5 折） |
| 选择 | 确定性 hash/分层（cell/partner/member；seed=20261130），**response-independent**；同一包给所有 updater/control |
| 反馈轮次 | **1**（不做 acquisition/多轮购买） |
| 每 unit 测量 | 2 member measurements × 4 technical wells = **8 wells** |
| 每折 wells | 24×8 = **192**（=2 × 96-well plates） |
| 失败板预留 | **10%**（每折 2.2 plate-equivalents） |
| 总 plate-equivalents | **11.0**（5 折，含 10% failure；不含 held-out query 测量） |
| held-out query measurements | **0**（不回测目标） |
| 所有 arm | **同信息、同反馈包、同测量数/成本、同调参/计算预算** |

> 全历史重训/普通适配/层级/GP/投影核都可使用**全部历史 support 数据 + 反馈**；U_conflict 也使用同样历史/特征/反馈。反馈包不按任何响应选择，避免把 acquisition 混入。

## 3. 更新器与强对照（固定反馈后比较）

### 3.1 更新器（四类；U_conflict 为 primary）

| id | 名称 | 更新信号 | 备注 |
|---|---|---|---|
| **U_conflict** | relational-conflict update | 反馈残差违反冻结 pair/partner 可加关系的程度 | **primary** |
| U_residual | residual-distance update | 残差/距离加权 | secondary |
| U_posterior | posterior-variance update | 后验方差/不确定性加权 | secondary |
| U_leverage | leverage update | 反馈单元 leverage/influence | secondary |

### 3.2 强对照（全部同信息/同预算；C2 为 primary control）

- **C0** global mean / no update。
- **C1** static additive pair/partner model（no feedback）。
- **C2** **全历史重训**（全部 support 历史 + 反馈）——primary control。
- **C3** ordinary adaptation（fine-tune bias / ridge offset）。
- **C4** hierarchical / empirical-Bayes partial pooling。
- **C5** multi-output / single-task GP。
- **C6** projected-kernel / ridge equivalent with same representation（同 P 投影核等价控制）。

不得给 U_conflict 额外数据、额外特征或更多调参/计算；不得让对照“人为冻结”本来能正常更新的结构；所有方法各自在相同预算内正常调参，记录搜索/计算成本。

## 4. 终点、度量、MDE 与零模型

### 4.1 终点/度量

- **Primary**：held-out 单剂量单元的 **Spearman ρ**（pooled across folds；同时报每折；不能只报一个全局 rho 代替用途）。
- **Secondary/descriptive**：
  - MAE（描述性；**不设 MAE MDE 门**，不用于“MAE 显著”结论）；
  - top-k precision，k∈{1,3,5}（仅附录/描述性，无决策含义）；
  - 每折、每个 update/control 的配对差与 CI；失败背景/失败折。
- 聚类：按 held-out cell/partner/member-pair；technical replicates 不作为独立 n。

### 4.2 MDE / δ_min / evaluation_cannot_distinguish

- **δ_min = 0.10**（描述性最小增量；不是决策效用阈值）。
- **MDE80 先验**：`2.8015852181 × SE_unit / sqrt(n_eff)`；借用 ON2-EX：σ_e=0.1422665081、SE_unit=0.0251494031、n_eff=6 → **MDE80=0.0287644381 ≤ 0.10**（design prior pass）。
- **执行前必须测量 MDE**；若 measured MDE80 > 0.10 → `design_invalid` / precision_insufficient，**不跑效果**。
- **MDE 只在 mean-Δ/MAE 尺度**，不是 Spearman 的 power 保证；rank 用 null/bootstrap，报告 95% CI/单侧 p；若 CI 不能排除 0 → **`evaluation_cannot_distinguish`**，不得说“无效/不存在”。
- 不把 CI 宽窄当 MDE；不在看结果后改 δ_min/指标/切分。

### 4.3 零模型（全部固定反馈包内）

- **N1（primary null）**：feedback labels 在固定 pack 内打乱（1,000 次，seed=20261130）；同包大小/成本。
- **N2**：response-independent random pack（同大小/成本，1,000 次，seed=20261130）。
- **N3**：no-feedback static/global 参考（描述性）。
- 报告 null Δρ 分布、单侧 p、null 95% 分位；不能把 null 打乱后的好表现当正结果。

## 5. 预注册表（D3）

| 项 | 冻结内容 |
|---|---|
| 主假设（唯一） | H_D3：U_conflict − C2 的 held-out Spearman Δρ ≥ δ_min=0.10 |
| 算法差异 | U_conflict（关系冲突更新）vs C2（全历史重训）；其余 secondary |
| 数据 | O'Neil complete-case batch1 target30，单 anchor 派生层；5 折继承；不重分 |
| 反馈 | 固定 24 units/fold（120 total），response-independent，同包同成本，1 轮；无 acquisition |
| 目标 | held-out 细胞全部未查询成员×伙伴；不回测 |
| Primary 终点 | held-out Spearman ρ（pooled + per fold） |
| Secondary | MAE（描述性）、top-k 1/3/5（附录）、配对 CI、失败折 |
| δ_min/MDE | δ_min=0.10；MDE80 先验 .0287644381；measured MDE gate；MDE>δ_min→design_invalid |
| 零模型 | N1 feedback label permutation 1,000；N2 random pack 1,000；N3 no-feedback |
| 失败类别 | `data_unavailable` / `design_invalid` / `evaluation_cannot_distinguish` / `no_increment` |
| 停止 | 只纠已测点→停 feedback-generalization 主张；普通方法等效/更好→撤 unique-operator；MDE>δ_min→design_invalid；泄漏/端点混用→design_invalid |
| 多重性 | 一个 primary；其余 secondary/描述性，不做“选最佳”正结果 |
| 执行 | 独立挑战者复核 + Lead 批准后另立执行协议；本文件不执行 |

## 6. 明确不做 / 边界

- **不做 acquisition 策略比较**（第 2 阶段另立协议）；不比较主动选择/整板购买。
- 不执行效果、不拟合预测、不加入训练/更新器结果；本文件只是设计与资格。
- 不称 **independent confirmation / migration / decision benefit / mechanism / novelty**；阴性只能写“本资源/本设计下无描述性增量”。
- **不与 Jaaks ΔEMAX 拼接**；O'Neil viability-only；不跨端点补值。
- 技术重复≠独立培养；batch3 全失、702 15-row pair-cell、无单药参照等限制不变；O'Neil 仅开发性。
- 冻结后不得改 mask/seed/fold/metrics/δ_min/feedback budget/primary contrast；若发现实现偏差→停并重新预注册。

## 7. 下一步

1. 本设计经独立挑战者（endpoint-auditor）只读复核；2. Lead 决定是否批准另立 D3 执行协议；3. 执行前测量 MDE、固定反馈包/切分/对照；4. 结果只写方向内开发性描述，不晋升核心、不称机制/迁移/独立确认。

> 设计数据来源：`d3.py` / `d3.json`（metadata-only；仅读 ON2 frozen metadata；未读 workbook/响应值；未拟合）。资格数字见 `d3.json`；本文件不构成执行结果。
