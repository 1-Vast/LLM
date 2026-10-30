# DESIGN_B_v0_4 —— T1 模拟器预注册 v0.4（R201-B.3；仅实现+资格门）

2026-10-28 · 角色：ON1/ON2/ON2.2/ON3 执行者（非提案者）。依据 v0.3、`challenge_B_v0_3.md`（revise 5 必改）、`design_B_v0_4.json`（SHA `A2D0CC1A01A9EF29FC7B2F0ACDC21658AFCEF6EE9D1F1FDC0829E3CC16601AA1`）、`design_B_revision_v0_4.py`（SHA `E4968C70…`）。**本文件是 T1 预注册冻结候选；请求 Lead 批准“T1 模拟器实现+资格门”，不批结果/T2/T3；未运行/未拟合/未读响应/无湿实验；不称新颖性/决策收益/迁移/机制。**

## 0. 批准范围

- **批准**：T1 合成模拟器**实现** + **资格门**（先于任何结果）。
- **不批准**：T1 结果解释/决策收益；T2/T3 执行；O'Neil/真实响应读取；新颖性/机制/迁移/资源足够/独立确认。
- T1 仅计算证据；资格失败只写 `design_invalid`，不报 selection accuracy/top-k/regret。

## 1. primary 配置/arms（冻结）

- **primary**：`(B_C=1200s, B_E=16 integer keys), κ=1.0, σ=0.10`；**500 独立 replicate=500 decision units**；seed=`20261130+r`；**MDE=0.088594≤δ_min=0.10 PASS**；主 H_B 只用这 500。
- 敏感性：17 格 ×50=850 replicate，只描述/`cost_sensitive`、不进 H_B/Holm。
- **10 arms/replicate**：`π_dual`、C0、C1、C2、C3、C4、C5、C6、**C7_compute_only**、**C7_experiment_only**。
  - C0 固定计算+随机实验；C1 固定实验+更多计算；C2 全历史重训；C3 普通决策 AL；C4 GP/BOED；C5 通用求解器；C6 随机预算分配；C7 两单预算臂（未用预算换算+filler）。
  - 同 update/信息/调参/seed；无额外数据/模型；C7 两臂分别输出。
- **arm-runs**：primary 500×10=**5,000**；sensitivity 17×50×10=**8,500**；total **13,500**；pilot=10×10=**100** arm-runs（只计时）。

## 2. 等总成本（整数 key + 无信息 filler；单位修正）

- 合成总成本：`T_seconds=B_C+κ·B_E_CU`；实验侧 CU 等价：`T_CU=B_E_CU+B_C/κ`。
- experiment-only：`n0=B_E+floor((B_C/κ)/363.6)` 整数 keys；**`residual_CU=T_CU−n0×363.6`**；filler=blank/QC/已知标准品整数 wells=`ceil(residual_CU)`；`spend_CU=n0×363.6+ceil(residual_CU)`；要求 `0≤residual_CU<363.6`、`|spend_CU−T_CU|≤1`。
- compute-only：`spend_seconds=T_seconds`（连续）；无信息 filler 仅当离散化需要。
- dual：在 `(B_C,B_E)` 内分配，残余以 blank/QC（实验侧）或无信息 compute steps 补到 T。
- **primary 例**：T=7017.6 CU；n0=19 keys=6908.4 CU；**residual 109.2 CU**；filler=110 blank/QC wells；spend=7018.4 CU；diff **0.8≤1**。
- **κ=0.1 例**（300s,4 keys）：T_CU=4454.4；n0=12 keys=4363.2；residual **91.2**；filler 92 wells；diff 0.8。
- **18 格全校验**：`spend_validation.all_pass=true`；negative filler=0；rows outside tolerance=0；表见 JSON `equal_cost.rows`。
- **无泄漏断言**：blank/QC/已知标准品 filler 不进入学习器/训练/模型更新/证书；compute filler 不产证书；单测断言模型状态不变。

## 3. x1/x2 特征映射（冻结；40-plan 宇宙）

- plan p∈0..39：`cell_u=p//10`（0..3）；`context_j=p%10`（0..9）；
  `x1=(j%3)−1`（−1/0/1）；`x2=((j//3)%3)−1`（−1/0/1）；`dose=0.5 if j<5 else 1.0`；split：`p<20 O`，`20≤p<30 M`，`p≥30 reserve`。
- **θ 固定** `[0.5,0.3,0.2,0.1,−0.1]`；`f=θ0+θ1x1+θ2x2+θ3x1x2+θ4·dose`；`γ_g~N(0,τ²)` per x2 group g∈{−1,0,1}，τ=0.20；观测噪声 `ε~N(0,σ²)`。
- **完整 40-plan 表**（plan_id/cell_u/context_j/x1/x2/dose/split）在 JSON `x_mapping.plan_table`；菜单 M=10 的 hash=SHA256(canonical sorted metadata)，运行前冻结；O/M/reserve 不得交换。

## 4. EV 网格（有限离散近似；非精确）

- **不再称精确枚举**；EV 用有限世界近似：
  - **γ 网格**：每 x2 group 5 点 `{-2τ,−τ,0,τ,2τ}={-0.4,-0.2,0,0.2,0.4}`；权重（标准化离散正态）`[0.054488685,0.244201342,0.402619947,0.244201342,0.054488685]`；3 groups → **125 γ worlds**。
  - **噪声网格（观测）**：σ=0.10 时 `{-0.2,-0.1,0,0.1,0.2}`，同权重；用于观测/评估。
  - **EV 定义**：在 125 γ worlds 上按权重求期望；动作排序时噪声用零均值期望效用，观测时加 Gaussian ε。
  - **误差门（预注册）**：在 calibration replicate 上比较 `EV_approx` 与 5-point noise-grid EV；**max selection-accuracy difference ≤0.02**；超过→`design_invalid: EV_approximation_error`，不报结果。
- 完整网格/权重表在 JSON `EV_grid`；实现者不得改点集/权重/误差门。

## 5. 判定树（与 v0.3 一致；冻结）

```
0) 无 utility/证书（T2/T3；GP/树/BOED）-> certificate_unavailable/blocked；不判 H_B、不买实验
1) compute while g_C>1 and B_C>=120s: spend one step (shrink certificate; charge)
2) g_C>1 and B_C<120s -> compute_budget_exceeded（未决；不买实验/不静默停）
3) g_C<=1:
   3a) decision unique in certificate set -> compute_sufficient -> stop
   3b) evidence-limited:
       headroom unknown -> oracle_unknown -> stop（不买）
       MDE>δ or power<0.8 or headroom<Δ -> evaluation_cannot_distinguish -> stop
       else buy EV/CU-max experiment; update; next round
4) rounds exhausted -> unresolved
```
- 证书阶梯：宽度 `[0.40,0.20,0.10,0.05,0.025]`；每 step 120s；min unit 120s；`Δ_utility=0.10`；`R_max=5`；实验动作=anchored key（363.6 CU；34–68 wells）。

## 6. H_B 判定（AND；仅 primary）

- 两主对比：`Δ1=dual−C7_compute_only`、`Δ2=dual−C7_experiment_only`；Holm α=0.05；配对 bootstrap CI。
- **H_B 成立 iff Δ1、Δ2 均正且 Holm 显著，且两点估计均≥δ_min=0.10**；只赢一个→`partial_decision_benefit`；无→`no_decision_benefit`；显著但低于 δ→`below_delta`；敏感性配置只描述；best-single 仅 inner validation 选，测试集不 max。

## 7. wall/pilot/资格门（与 10 arms 同步）

- primary 5,000 + sensitivity 8,500 = **13,500 arm-runs**；pilot 100 arm-runs（10 primary replicate×10 arms）只计时。
- **单次 T1 ≤45min；两跑 ≤90min**（CPU-only）。
- **fallback 写死**：pilot 外推 primary >45min → `design_invalid: compute_budget_exceeded`，不报结果；总计 >45min 但 primary ≤45min → 只跑 primary、跳过敏感性（不报敏感性结论）；**不得减少 primary 500/10 arms/configs**。
- **资格门先于任何结果读取/报告**：oracle 无限计算可恢复；null FP≤α；**EV 近似误差≤0.02**；成本账整数 key+filler 且 18 格 spend 校验；无泄漏（filler 不进学习器）；10 arms 等价实现；两跑逐字节一致；schema；wall；菜单 hash/seed 复现。失败只 `design_invalid`，不报 selection accuracy/top-k/regret。

## 8. T2/T3/边界

- T2：仅描述/操作，不判 H_B；n=6/30 decision units MDE 0.8087/0.3617>0.10→`evaluation_cannot_distinguish`；必须附 `PEEK_DISCLOSURE_ON3.md` `B4CAD955…`（non-blind/peeked）；技术重复≠独立培养。
- T3：`data_unavailable/cost_uncalibrated`；r primary=5（393×5×363.6=714,474.0 CU）；r=1/10 仅敏感性；不执行；前瞻 oracle 未知→`oracle_unknown`。
- T1 仅计算证据；不称新颖性/机制/迁移/决策收益/资源足够/独立确认；冻结≠资源足够/关系成立/Stage 1/效果；D1/D3/A1/C187 不重复。
