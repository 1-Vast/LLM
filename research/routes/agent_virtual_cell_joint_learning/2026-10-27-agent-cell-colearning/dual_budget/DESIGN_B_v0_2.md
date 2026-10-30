# DESIGN_B_v0_2 —— 双预算决策预注册草案 v0.2（R201-B.1；仅设计，不执行）

2026-10-28 · 角色：ON1/ON2/ON2.2/ON3 执行者（非提案者）。依据：v0.1 `DESIGN_B.md`、`challenge_B.md`（R201-B-C1，revise 5 必改）、`PROBLEM_B_v0_2.md`、`design_B_v0_2.json`（SHA `128E129D953FEAF1852A5EBC971A976B9576B4A66A131AF9AE56773FA65128BC`）。**本文件是 T1 模拟器预注册草案（未冻结、未执行）；T2/T3 不执行；不运行效果/不拟合/不读响应；不称新颖性/决策收益/迁移/机制。**

## 0. 范围与判决

- **只申请 T1 模拟器预注册**（仅计算证据，算法证伪）；**不申请 T2/T3 执行**。
- T2：仅回顾性操作/描述，**不得判 H_B**，必须附 `PEEK_DISCLOSURE_ON3.md` `B4CAD955…`（ON3 non-blind/peeked）。
- T3：`data_unavailable / cost_uncalibrated`（无报价/LOI/湿预算/独立培养）；393 keys≠393 decision units（见 §5）。
- T1 结果前必须过模拟器资格门；资格不过 → `design_invalid`，不得报告 T1 结果/决策收益。

## 1. 主假设 H_B（同总成本、可核查）

**H_B**：在**同一合成总成本 T**（T1 合成成本面；见 §5）下，`π_dual` 的**top-1 selection accuracy**（留出未测菜单）高于两个单预算对照（compute-only-filler、experiment-only-filler），且不是预测提分替代。

- **两个独立主对比**：`Δ1 = acc_dual − acc_compute_only_filler`；`Δ2 = acc_dual − acc_experiment_only_filler`；Holm 校正 α=0.05；分别报告点估计+配对 bootstrap CI。
- **best-single**：只在 inner validation 选；测试集不取 max；max 仅描述（同时 CI）。
- **预测非替代**：预测指标为辅助/阴性对照；只有预测改善而 selection accuracy 不改善 → `no_decision_benefit`（停决策主张）。

## 2. T1 设计（预注册细节）

### 2.1 世界生成（每个 replicate 独立）

- **Plan** `p=(cell u, pair v, dose-context c)`；特征 `x_p` 为元数据（不含隐藏量/响应）。
- **共享算子**：`f(x_p; θ)` 为预注册阶数的共享函数（如低维线性/低秩 + 剂量项）；**同一 θ 跨所有 plan**；真实效用
  `u_p = clip(f(x_p;θ) + γ_{v(p)} + ε_p, 0, 1)`，其中 `γ_v` 为隐藏 plan-difference（pair-level，**永不进入特征**），`ε_p ~ N(0,σ²)`。
- **隐藏计划差**：`γ_v` 服从预注册分布（如 N(0, τ²)）；部分 plan 只被 shared operator 覆盖，另一些需实测 γ；这是"跨计划共同算子 + 计划差"的最小合成实例。
- **观测/未测**：每 replicate 预注册观测计划集 O（如 20 个）与留出菜单 M（如 10 个，**未测**）；策略可用 O 与已购买实验，M 只在评估/判定使用。
- **噪声**：σ 预注册 {0.05, 0.10}（作为设计因子，不作为结果选）；每 replicate 固定 σ 或按预注册设计格。
- **计划菜单**：固定 plan 宇宙与菜单构造规则（纯元数据、无响应依赖）；菜单哈希预注册；不得按结果/headroom 选菜单。

### 2.2 独立 replicate/seed

- **500 个独立 replicate**：每个 replicate 重新生成 `θ, γ, ε, O/M split`，世界独立（不是技术重复）。
- seed：`seed = 20261130 + replicate_id`（预注册）；任何 arm 不得复用另一 replicate 的世界；两跑使用同一 seed 表。
- 500 是预注册 replicate 数；不得看结果增减；若资格/预算门不过 → 未决并按门停。

### 2.3 Oracle/top-k/null

- **Oracle**：由真实 `u_p` 算 top-1/top-k；仅评估用，策略不可见；oracle 在 T1 可复算。
- **Null 校准**：① γ=0 且菜单效用差≤噪声（近似无信号）世界；② 菜单效用 shuffle；③ 随机决策；④ 随机预算分配；⑤ solver-seed shuffle；⑥ 菜单 label shuffle。用这些生成 selection accuracy/top-k/regret 的 null 分布；校准 false-positive ≤ α、null MDE/SE；**零模型不用于选策略**。
- **T1 合成证书**：对决策差 `d=q−p`，模型族输出区间 `[h_in,h_out]` 含真实差；compute 预算按预注册精度阶梯收缩宽度；`g_C(d)=(h_out−h_in)/Δ_utility`，`Δ_utility=0.10`（T1 合成效用尺度；与 primary δ_min=0.10 accuracy 分开）；T1 可精确算 `headroom=oracle−static` 与实验 EV。

### 2.4 成本/预算（等总成本）

- **合成成本面**：`κ` = compute-second per CU，场景 {0.1,1,10} s/CU；总成本 `T=B_C+κ·B_E_CU`。
- **预算格**：`(B_C,B_E)` 预注册网格（如 B_C∈{300,600,1200,2400}s × B_E∈{4,16,64} keys），所有臂同一格；每格独立算总成本 T；三 κ 场景分别重跑（排序不一致→`cost_sensitive`）。
- **双预算策略 π_dual**：先用计算收缩证书，再按 §2.5 判定树买实验/停止；每笔计算/实验/重认证/填充计费。
- **单预算转换/filler**：compute-only `B_C_eff=B_C+κ·B_E`、实验=0；experiment-only `B_E_eff=B_E+B_C/κ`、计算=0；残余用同维随机无信息 filler 填满，计入账本；所有臂 `|花费−T|≤一个最小动作/计算单元`；账本逐项报 compute s/CU/wells/plates/keys/rounds/filler。
- **T2/T3**：无报价/LOI → 不做成本结论（`cost_uncalibrated`）；A5 CU 仅 planning。

### 2.5 唯一判定树（T1 可算；T2/T3 默认不可用）

```
0) 若某臂无 utility/证书（T2/T3；GP/树/BOED 无证书）:
   -> certificate_unavailable / blocked_by_utility_definition；不判 H_B；不买实验
1) compute 阶段:
   while g_C > 1 and remaining B_C >= min_compute_unit:
       花一个预注册 compute step（收缩证书；计费）
2) 若 g_C > 1 且 B_C < min_compute_unit:
   -> compute_budget_exceeded（未决；不自动买实验；不静默停）
3) 若 g_C <= 1:
   3a) 证书集内所有世界同一决策 -> compute_sufficient -> 停止（不买）
   3b) evidence-limited:
       headroom 未知 -> oracle_unknown -> 停止（不买）
       MDE_decision(B_E)>δ_min 或 power<0.80 或 headroom<Δ_utility -> evaluation_cannot_distinguish -> 停止
       否则买 EV/CU 最大实验包；更新；下一轮
4) 轮次耗尽 -> unresolved（记录，不判收益）
```

- **fallback**：B_C 耗尽且 g_C>1 → `compute_budget_exceeded`；headroom 未知（T3）→ `oracle_unknown`；无证书模型 → `certificate_unavailable`（仅对照臂）；T2/T3 在 utility/证书冻结前不得下结论。
- **T1 判据不可外推**：T1 的合成 utility/certificate/headroom/EV 只在该模拟器内有效；T2/T3 的真实结论须另立效用/证书预注册。

### 2.6 C0–C7 等价实现（T1）

| id | 实现（T1） | 同信息/同更新 |
|---|---|---|
| C0 | 固定计算 + 随机实验（同 T） | 同 O/update/菜单；随机实验包 |
| C1 | 固定实验 + 更多计算（同 T） | 同 O/update；B_C 转换加满 |
| C2 | 全历史重训 | 同 O；无主动实验/预算分配 |
| C3 | 普通决策 AL | 按决策不确定性选实验；同 update/调参 |
| C4 | GP/BOED | 同信息；决策损失近似；超参 trials 计入 |
| C5 | 通用求解器 | 同证书缓存/计算计费；强对照 |
| C6 | 随机预算分配 | 同 T；随机分 B_C/B_E |
| C7 | compute-only / experiment-only | 未用预算换算+filler；分别报告 |

- 所有臂共用**同一更新器/学生**、同一信息、同一调参 trials/seed/计算 cap；不得自带额外模型/数据/LLM；C7 两臂分别报告；C0/C1 不混入 best-single 主定义。

### 2.7 输出 schema/两跑/wall/资格门

- **每 replicate×arm×budget 输出**：`selection_accuracy`、`topk_hit`、`normalized_regret`、`chosen_plan`、`oracle_plan`、成本账 `{compute_s, CU, wells, plates, keys, rounds, filler}`、`compute_steps`、`experiments`、`failure_class`；汇总按 arm/budget/κ。
- **两跑逐字节一致**（JSON sorted keys、无时间戳）；输出 SHA。
- **T1 wall/预算测试**：先做 pilot 预算测试（10 replicate 外推）；单次 T1 ≤45 min CPU-only、两跑 ≤90 min；超限 → `design_invalid: compute_budget_exceeded`，不报结果；不得减少 500 replicate 或预算格事后救。
- **模拟器资格门（先于任何 T1 结果）**：① oracle 可用无限计算恢复；② null FP≤α/校准；③ 成本账等总成本可审计；④ 无泄漏单测全过；⑤ C0–C7 等价实现、同一 update；⑥ 两跑一致；⑦ schema 校验；⑧ wall 在预算内。任一 fail → `design_invalid`，无 T1 结果。
- **无泄漏单测**：隐藏 γ 不进特征；未测 plan 不进训练；oracle 只评估；成本账含所有计算/实验/filler；arm 无额外数据/模型；菜单哈希/seed 复算一致。

## 3. Primary/Secondary/δ/MDE（统一尺度）

- **Primary**：top-1 selection accuracy（[0,1]），每个独立 decision unit 一个选择；两对比 §1。
- **MDE**：`MDE80 = 2.8015852181 × sqrt(0.5/n_dec_units)`；n=6→0.808748、30→0.361683、393→0.099929、500→0.088594、1573→0.049949。
- **δ_min=0.10 为操作阈值**（不是业务效用）；不再 trigger `blocked_by_utility_definition`；blocked 只用于 secondary regret/EV/headroom 与真实世界价值主张。
- **Decision unit**：独立 held-out cell/fold 菜单；**不是** well/key/row；T2 的 n=6/30 是 decision units（MDE 如上，仍>0.10 → `evaluation_cannot_distinguish`，不作主检验）。
- **T3 key→CU**：r keys/decision unit ∈{1,5,10}；393 units → 393×r keys；r=1 142,894.8 CU、r=5 714,474.0 CU、r=10 1,428,948.0 CU；wells/setup/重复/失败板另计；无报价→cost_uncalibrated。
- **Secondary**：top-k hit (k=5)、normalized regret、预测辅助；top-k/regret null/MDE **T1 模拟器校准**（不直接用 selection-accuracy 公式）；T2/T3 不作主推断。
- **多重性**：两主对比 Holm；secondary 用 BH/描述；不得选最佳后报 CI；测试集不 max。

## 4. T2/T3 边界（一致）

- **T2**：仅回顾性操作/描述；`evaluation_cannot_distinguish`（decision MDE n=6 0.8087、n=30 0.3617 >0.10）；不得判 H_B；必须附 `PEEK_DISCLOSURE_ON3.md` `B4CAD955…`；ON3 non-blind/peeked；不称盲验/独立确认/预注册确认；技术重复≠独立培养。
- **T3**：`data_unavailable / cost_uncalibrated`（无 quotes/LOI/湿预算/独立培养）；393 decision units ≠ 393 keys；成本按 r∈{1,5,10} keys/unit 计；前瞻 oracle 未知 → `oracle_unknown`；不执行。
- **停止条件（全轮）**：普通方法同预算等效 → 撤新意；仅预测改善 → `no_decision_benefit`；只在模拟器成立 → 停现实主张；MDE>δ/utility 未定 → 未决；资源不可得 → data_unavailable；泄漏/实现偏差 → design_invalid；D1/D3/A1/C187 不重复。

## 5. 与 AL/BOED/COPEx 关系（不称新颖性）

一般概念（decision-focused AL、BOED/EVSI/ENBS、COPEx 动态约束、约束生成、计算决策、GP/BO）已覆盖；CoMap/LAWM/MDA/COPEx 已有联合/任务摘要/动态约束。本设计差别仅限定为具体共享对象（跨计划共同反事实/约束算子 + 计算认证状态）与更新运算（计算证书收紧 + 真实反馈统一修订），以及可审计双预算成本账；**不主张**新算法/首次双预算/预测分歧采样；若同信息/同预算普通方法等效 → 撤新意。

## 6. 边界（写死）

- **本轮只设计**：未运行 T1/T2/T3、未拟合、未读响应、未湿实验；不称新颖性/机制/迁移/决策收益/资源足够/独立确认；冻结≠资源足够/关系成立/Stage 1/效果。
- T1 仅计算证据；不得外推生物/临床/真实决策收益；O'Neil 限制不变；技术重复≠独立培养。
- 必须独立挑战 + Lead 批准后才可冻结 T1 预注册；T2/T3 不批执行。
