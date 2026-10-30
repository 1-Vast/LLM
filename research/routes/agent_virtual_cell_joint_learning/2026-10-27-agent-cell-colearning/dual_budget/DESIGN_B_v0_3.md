# DESIGN_B_v0_3 —— 双预算 T1 模拟器预注册 v0.3（R201-B.2；仅 T1 实现+资格门，不执行结果）

2026-10-28 · 角色：ON1/ON2/ON2.2/ON3 执行者（非提案者）。依据：v0.2 文件、`challenge_B_v0_2.md`（revise 5 必改）、`design_B_v0_3.json`（SHA `50E6EE30959CACD9894F799276BE907388189BCFF9B225DC7E6C68611E8A27D9`）、`design_B_revision_v0_3.py`（SHA `AA49E4C8…`）。**本文件是 T1 预注册冻结候选（未运行）；请求 Lead 批准“T1 模拟器实现 + 资格门”，不批准结果/T2/T3 执行；不运行效果/不拟合/不读响应/无湿实验；不称新颖性/决策收益/迁移/机制。**

## 0. 批准范围（请求）

- **批准**：T1 合成模拟器**实现** + **资格门**（先于任何 T1 结果）。
- **不批准**：T1 结果解释/决策收益主张；T2/T3 执行；任何 O'Neil/真实响应读取；任何新颖性/机制/迁移/资源足够/独立确认。
- T1 只作**计算证据**（合成效用），不外推生物/真实决策收益。

## 1. primary 配置与 500 replicate 归属（冻结）

- **primary 配置**：`B_C=1200s`、`B_E=16 integer keys`、`κ=1.0 s/CU`、`σ=0.10`。
- **primary 500 个独立 replicate = 500 decision units**；seed=`20261130+replicate_id`（0..499）；**主 H_B 只用这 500 个**。
- **MDE**：`2.8015852181×sqrt(0.5/500)=0.088594 ≤ δ_min=0.10`（PASS；500 固定，不得看结果增减）。
- **敏感性配置**：其余 **17 格**（3 固定预算对 ×3κ×2σ = 18 格减 primary），每格 **50 replicate**（共 850），seed=`20261131+cell_index*1000+replicate_id`；**仅描述性/`cost_sensitive`**，不得用于主 H_B/Holm。
- 固定预算对：`(300s,4 keys)/(1200s,16 keys)/(3600s,64 keys)`；κ∈{0.1,1,10}；σ∈{0.05,0.10}；网格在 JSON 中唯一，不再有 B_C 网格不一致。

## 2. 等总成本可执行（整数 keys + 无信息 filler）

- 合成总成本 `T=B_C+κ·B_E_CU`（s/CU 场景；T2/T3 无报价→`cost_uncalibrated`）。
- **experiment-only**：`n0 = B_E + floor((B_C/κ)/363.6)`（整数 keys）；`keys_CU=n0×363.6`；残余 `filler_CU=T−keys_CU` 用 **blank/QC/已知标准品**填充（不进入学习器、不更新模型、无目标信息）；`|spend−T|≤1 well-equivalent`。
- **compute-only**：`B_C_eff=T`（连续秒）；无实验 keys；compute filler=无信息随机计算步骤（不产证书/不更新模型），仅当离散化需要。
- **dual**：在 `(B_C,B_E)` 内分配，残余用上述 filler 补到 T；所有臂账本逐项报 compute s/key 数/CU/wells/plates/rounds/filler。
- **primary 例**：`B_C=1200s, B_E=16 keys, κ=1` → T=7017.6s；experiment-only `n0=19 keys=6908.4 CU` + blank/QC filler **109.2 CU**；compute-only `B_C_eff=7017.6s`；dual 1200s+5817.6 CU——三臂等 T，keys 全整数。
- **无泄漏断言**：filler 不进入学习器/训练数据/模型更新/证书；blank/QC 不产目标 plan 响应；compute filler 不产证书；单测断言成本账含 filler 且模型状态不变。

## 3. H_B 判定（AND；主检验仅 primary）

- 两主对比：`Δ1 = acc_dual − acc_compute-only-filler`；`Δ2 = acc_dual − acc_experiment-only-filler`；两对比 Holm α=0.05、配对 bootstrap CI。
- **H_B 支持 iff Δ1、Δ2 均为正且 Holm 显著，且两点估计均 ≥δ_min=0.10**。
- 只赢一个 → `partial_decision_benefit`；都不成立 → `no_decision_benefit`；显著但低于 δ → `below_delta`；敏感性配置只 `cost_sensitive`/描述，不能声称 H_B。
- best-single：inner validation 选；测试集不 max；max 仅描述（同时 CI）；主检验只在 primary。

## 4. T1 冻结旋钮（全部写死；不可事后改）

- **Plan 宇宙 40**；观测 **O=20**；留出菜单 **M=10**；菜单 hash=SHA256(canonical sorted metadata)，运行前冻结。
- **σ**：primary 0.10；敏感性 0.05；按配置表分配。
- **共享算子**：`f=θ0+θ1x1+θ2x2+θ3x1x2+θ4·dose`；θ 固定 `[0.5,0.3,0.2,0.1,-0.1]`；`γ_v~N(0,τ²)`, **τ=0.20**（hidden plan-difference，不进特征）；噪声 `ε~N(0,σ²)`。
- **效用**：`u=clip(f+γ_v+ε,0,1)`；合成 oracle=真实 u 的 top-1/top-k。
- **证书阶梯**：初始宽度 0.40；宽度序列 `[0.40,0.20,0.10,0.05,0.025]`；每 compute step 成本 120s；`min_compute_unit=120s`；`Δ_utility=0.10`；g_C 按 §5 判定树。
- **实验动作库**：每动作 = 一个 anchored key（363.6 CU；34–68 wells；测一个 plan 的响应/效用）；无额外 plan 标签/额外信息。
- **EV 枚举**：在固定离散世界网格（θ/γ/噪声格）上精确枚举；不采样近似。
- **R_max=5** 实验轮次；每 replicate 最多 5 轮。
- **seed**：primary 20261130+r；sensitivity 20261131+cell_index*1000+r；世界不复用。
- **两跑**：完整 T1 两跑 JSON **逐字节一致**（sorted keys、无时间戳）；输出 SHA。
- **schema**（每 replicate×arm）：`replicate_id, cell_index, arm, selection_accuracy, topk_hit, normalized_regret, chosen_plan, oracle_plan, cost_ledger{compute_s,CU,wells,plates,keys,rounds,filler}, compute_steps, experiments, filler, failure_class`；汇总按 arm/config。
- **C0–C7 等价实现**：C0 固定计算+随机实验；C1 固定实验+更多计算；C2 全历史重训；C3 普通决策 AL；C4 GP/BOED；C5 通用求解器；C6 随机预算分配；C7 单预算+整数 key 换算/filler；同 update/信息/调参/seed，无额外数据/模型。
- **null 校准**：γ=0 近似无信号、菜单效用 shuffle、随机决策、随机预算、solver-seed shuffle、label shuffle；FP≤α；只校准，不选策略。

## 5. 唯一判定树（T1 可算；T2/T3 默认不可用）

```
0) 无 utility/证书（T2/T3；GP/树/BOED 无证书）-> certificate_unavailable / blocked；不判 H_B、不买实验
1) compute: while g_C>1 and remaining B_C>=120s: 花一个 compute step（收缩证书；计费）
2) g_C>1 且 B_C<120s -> compute_budget_exceeded（未决；不自动买实验、不静默停）
3) g_C<=1:
   3a) 证书集内决策唯一 -> compute_sufficient -> 停（不买）
   3b) evidence-limited:
       headroom 未知 -> oracle_unknown -> 停（不买）
       MDE_decision(B_E)>δ_min 或 power<0.80 或 headroom<Δ_utility -> evaluation_cannot_distinguish -> 停
       否则买 EV/CU 最大实验包；更新；下一轮
4) 轮次耗尽 -> unresolved
```
- T1 合成判据不可外推；T2/T3 在 utility/证书冻结前不得下结论。

## 6. Wall/预算/资格门（先于结果）

- **pilot**：先跑 10 个 primary replicate（不读结果/只计时）外推；不得看 selection accuracy 调整。
- primary arm-runs 500×8=4,000；sensitivity 17×50×8=6,800；总 10,800 arm-runs。
- **单次 T1 ≤45 min；两跑 ≤90 min**（CPU-only）。
- **fallback（写死）**：若 pilot 外推 primary-only >45min → `design_invalid: compute_budget_exceeded`，不报结果；若总计 >45min 但 primary ≤45min → 只跑 primary、跳过敏感性（不报敏感性结论）；**不得减少 primary 500/configs**。
- **资格门（先于任何 T1 结果读取/报告）**：oracle 无限计算可恢复；null FP≤α；成本账整数 keys+filler 可审计；无泄漏单测全过（filler 不进学习器）；C0–C7 等价；两跑逐字节一致；schema；wall 在预算；菜单 hash/seed 复现。
- **资格失败**：只写 `design_invalid`，不报 selection_accuracy/topk/regret，不写算法有效/无效。

## 7. T2/T3/边界

- **T2**：仅描述/操作，不判 H_B；n=6/30 decision units 的 MDE 0.8087/0.3617 >0.10 → `evaluation_cannot_distinguish`；必须附 `PEEK_DISCLOSURE_ON3.md` `B4CAD955…`（ON3 non-blind/peeked）；技术重复≠独立培养；不得当主检验。
- **T3**：`data_unavailable/cost_uncalibrated`；r primary=5，T3 393 decision units ×5 keys ×363.6 = **714,474.0 CU**；r=1/10 仅敏感性；无报价/LOI/湿预算/独立培养 → 不执行；前瞻 oracle 未知 → `oracle_unknown`。
- **全轮**：T1 仅计算证据；不称新颖性/机制/迁移/决策收益/资源足够/独立确认；冻结≠资源足够/关系成立/Stage 1/效果；D1/D3/A1/C187 不重复。
