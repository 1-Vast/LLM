# report_d3 —— R200-D3 单一剂量资源资格 + 固定反馈未查询泛化设计（设计报告）

2026-10-27 · 角色：ON1/ON2/ON2.2/ON3 执行者（非提案者）· **状态：DESIGN ONLY / NOT EXECUTED**。
本报告只交付 **资源资格（metadata-only）与预注册设计**；**未运行效果、未拟合预测、未比较 acquisition、未读原始响应值做统计**。不称独立确认/迁移/决策收益/机制/新颖性；不与 Jaaks ΔEMAX 拼接。

## 1. 结论先行

- **资源资格：`qualified_with_conditions`**。O'Neil complete-case batch1 target30 的**单一 anchor 剂量层**有 **340,088 units / 2,149 contexts / 30 target cells / 5 folds（6 cells each）**；每 unit 4 technical reps/member（Δ 的 4 replicate-level differences）、8 wells，**独立 culture=1**；足够做开发性固定反馈比较。
- **设计**：固定反馈包 **24 units/fold（120 total；1 轮；无 acquisition）**；同一包给所有 updater/control；主终点 = held-out 细胞未查询成员×伙伴的 **Spearman ρ**；主对照 = **全历史重训（C2）**；唯一主假设：**U_conflict − C2 ≥ δ_min=0.10**。
- **可执行性条件未闭合**：本设计尚未独立挑战/Lead 批准；执行前必须测 MDE；**本报告不含效果结果**。
- **Jaaks 备选：`not_qualified_for_D3_endpoint`**：A0/Q2 matching 以 **SYNERGY_DELTA_EMAX** 为主端点，D3 禁止 ΔEMAX 拼接；若无独立 viability 端点+A0 匹配，不能用作备选。

## 2. 资源资格（metadata-only）

来源：`research/2026-10-27-core-module-design/oneil_dev/on2.json`（ON2 v2.2 frozen metadata；O'Neil complete-case，batch1 target30，`design_frozen_qualified_with_conditions`）。

### 2.1 单剂量层与单元定义

- 从 frozen 4×4 成员剂量网格中**预先固定** member dose index=4 × partner dose index=4 的 anchor 行；每个 member context 取该行；不按响应选剂量、不插值。
- `Δ(c; a,a';b) = mean_viability(a,b,anchor,4 reps) − mean_viability(a',b,anchor,4 reps)`，同 cell/partner/role。
- 一个 member pair/context 一个 unit；**这是 full-grid 派生的 single-anchor 层，不是独立 single-dose screen**。
- Technical replicates = precision only；每 unit 的 independent culture 数 = **1**；按 cell/partner/member-pair 聚类，不做伪重复放大 n。

### 2.2 资格数字

| 指标 | 值 |
|---|---|
| 单剂量 units（target30） | **340,088** |
| 上下文 | **2,149** |
| 目标细胞 | **30**（5 folds × 6 cells） |
| 每折 units | 68,152 / 66,743 / 66,556 / 69,738 / 68,899 |
| 每折 contexts | 432 / 427 / 427 / 432 / 431 |
| 每 unit technical reps/member | **4**（replicate-level differences=4） |
| 每 unit wells | **8**（2 member × 4 reps） |
| 每 unit independent cultures | **1** |
| complete-case rows all4 | 363,090 / 368,832 = **98.44%** |
| batch3 | **0 / 5,040**（全失） |
| 702 个 15-row pair-cell | **披露** |
| 缺失 | viability2=78, viability3=198, viability4=5,742 |
| batch2 | disclosure-only（1,129 units/136 contexts；不进 primary） |
| Jaaks overlap 排除 | 9 cells |

**判定理由**：units/contexts/cells/folds 足够；但仅开发性、单 anchor 派生、complete-case、技术重复不是独立培养、batch3 全失、702 个 15 行 pair-cell、无双药参照；因此 **qualified_with_conditions**，不是 `qualified`。

### 2.3 明确限制

- O'Neil 仅开发性；**不是 independent confirmation / migration / decision benefit / mechanism**。
- 技术重复只做 precision/calibration；n_eff=held-out cells（6，保守）。
- 缺失机制未知；无 MCAR/MAR 假设；complete-case primary。
- **单剂量层派生自 full 4×4 grid**，不是独立单剂量资源；不能把 anchor 层当外部独立证据。
- 无双药/单药参照；只有 viability；**不拼 ΔEMAX**。
- ON2 v2.2 本身是 post-observation 资格修订，不是预注册；D3 须独立挑战。

## 3. 固定反馈与对照设计

### 3.1 切分/目标

- 5 折继承 ON2 target30（每折 6 held-out cells；24 support cells）；不重分、不换 seed。
- 反馈只在 support cells 中购买；**held-out 细胞不测量、不做反馈**。
- 目标 = held-out 细胞的**全部单剂量单位**（未查询成员×伙伴）；每折 66,556–69,738 units，总 340,088；不回测目标。

### 3.2 固定反馈预算（所有方法同包同成本）

| 项 | 值 |
|---|---|
| k units/fold | **24**（总 120） |
| 选择 | deterministic hash/stratified（cell/partner/member；seed=20261130）；response-independent；同包给所有方法 |
| 轮次 | **1**；无 acquisition/多轮 |
| 每 unit wells | 2 member × 4 reps = **8** |
| 每折 wells/plates | 192 wells = 2 × 96-well plates |
| 失败板 | 10%（2.2 plate-equiv/fold） |
| 总 plate-equiv | **11.0**（5 folds；不含 query 测量） |
| query measurements | **0** |
| 同信息/等预算 | 所有 updater/control 同包、同历史/特征、同调参/计算预算；全历史重训也只用同一 support history + feedback |

### 3.3 Updater 与强对照

**Updaters**：`U_conflict`（关系冲突；primary）、`U_residual`（残差/距离）、`U_posterior`（后验方差）、`U_leverage`（leverage）。
**强对照**：C0 global mean/no update；C1 static additive（no feedback）；**C2 full-history retrain（primary control）**；C3 ordinary adaptation（fine-tune/bias）；C4 hierarchical/EB；C5 GP；C6 projected-kernel/ridge equivalent。不得给 U_conflict 额外数据/特征/调参；对照不得被人为冻结本可更新的结构。

## 4. 终点、MDE、零模型

- **Primary**：held-out Spearman ρ（pooled + per fold；不能只报一个全局 rho）。
- **Secondary**：MAE（描述性；不设 MAE MDE 门）；top-k k∈{1,3,5}（附录/描述性，无决策含义）；配对 CI、失败折/失败背景。
- **δ_min=0.10**；**MDE80 先验 = 0.0287644381**（ON2-EX 借用 σ_e=0.1422665081、SE_unit=0.0251494031、n_eff=6）；MDE80≤δ_min prior pass。
- **measured MDE 是执行前强制门**：MDE80>0.10 → `design_invalid / precision_insufficient`，不跑效果。
- **MDE 只对 mean-Δ/MAE 尺度**，不是 Spearman 的 power 保证；rank 用 null/bootstrap，CI 不能排除 0 → `evaluation_cannot_distinguish`；不把 CI 宽当 MDE。
- **Null**：N1 feedback label permutation（1,000；seed=20261130）primary；N2 random pack（1,000）；N3 no-feedback static/global。
- **Failure categories**：`data_unavailable` / `design_invalid` / `evaluation_cannot_distinguish` / `no_increment`。
- **Stop**：只纠已测点→停 feedback-generalization 主张；普通方法等效/更好→撤 unique-operator；MDE>δ_min→design_invalid；泄漏/端点混用→design_invalid。

## 5. 缺口/风险（提交独立挑战前）

1. **Single-dose layer 是派生的**，不是独立 single-dose screen；只能称开发性单 anchor 资源。
2. **n_eff=6**（held-out cells）保守；feedback pack 只有 24/fold；rank 精度有限；measured MDE 必须实测。
3. **Technical replicates 不是独立培养**；batch3 全失/702 15-row pair-cell/缺失机制未知；不能补成独立确认。
4. **强对照（全历史重训/层级/GP）可能完全解释收益**；若等效→撤 U_conflict 独有算子；本设计不预设成立。
5. **Jaaks 备选未 qualified**（A0 ΔEMAX 端点/D3 不拼端点）；若未来要用，须另立 viability 端点 + A0 匹配/端点可比 + 独立挑战。
6. **本任务未执行效果/未比较 acquisition**；acquisition 是第 2 阶段，另立协议；不称迁移/决策收益/机制/独立确认/新颖性。

## 6. 建议

- **建议提交同一独立挑战者（endpoint-auditor）复核**本设计 + `d3.json`；通过后由 Lead 批准是否另立 D3 执行协议。
- 执行前先做 **measured MDE + feedback pack 固定/切分/对照预检**；不通过则停（`data_unavailable`/`design_invalid`）。
- 结果只写 O'Neil 内部开发性描述、带完整限制；不晋升核心代码/不称机制/迁移/独立确认。

> 本报告不含效果结果；资格数字来自 `d3.py`/`d3.json`（metadata-only，仅读 ON2 frozen metadata，未读 workbook/响应值，未拟合）。
