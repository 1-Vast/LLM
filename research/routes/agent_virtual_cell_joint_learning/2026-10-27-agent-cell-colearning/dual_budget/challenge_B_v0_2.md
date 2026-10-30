# R201-B.1 再挑战（task-107）：v0.2 双预算设计

2026-10-28。角色：同一独立挑战者（非提案者、未参与 B、不运行效果/不拟合/不读响应）。对象：[PROBLEM_B_v0_2.md](PROBLEM_B_v0_2.md)（SHA `618C6EDA…`）、[DESIGN_B_v0_2.md](DESIGN_B_v0_2.md)（`6E30C98D…`）、[design_B_v0_2.json](design_B_v0_2.json)（`128E129D…`）、[report_B_v0_2.md](report_B_v0_2.md)（`9F6AD80D…`）、[record_B_v0_2.md](record_B_v0_2.md)（`D974E59A…`）、v0.1 [challenge_B.md](challenge_B.md)、R201 BRIEF、A5/ON2-EX/ON3/PEEK/CH187/C190。**只读；只写本文件与 `tmp/`。**

## 0. 结论先行

**总判决：revise（不是 approve_mvp_to_lead，也不是 stop）。v0.2 已实质修复 v0.1 的 5 条必改，但 T1 预注册仍有三处会直接决定 MDE/等成本含义的未冻结项；修完即可提交 `approve_mvp_to_lead`（仅 T1 预注册）。**

已确认的修复（PASS）：
- **等总成本**：`T=B_C+κ·B_E_CU`、`compute-only B_C_eff=B_C+κ·B_E`、`experiment-only B_E_eff=B_E+B_C/κ`、filler/账本/`|spend−T|≤最小单元` 写死；`best-single` 只在 inner validation 选，测试集两主对比+Holm、max 仅描述 ✓。
- **判定树**：T1 合成 `u/[h_in,h_out]/Δ_utility/headroom/EV`，无证书→`certificate_unavailable`、B_C 耗尽且 g_C>1→`compute_budget_exceeded`、headroom 未知→`oracle_unknown`、MDE>δ/power<0.8/headroom<Δ→`evaluation_cannot_distinguish`、轮次耗尽→`unresolved`，写死 ✓；T2/T3 默认不可用 ✓。
- **primary/MDE/δ**：primary=top-1 selection accuracy，MDE=`2.801585√(0.5/n)`，δ_min=0.10 操作阈值、blocked 仅 secondary；decision unit=独立 held-out cell/fold 菜单；393 decision units≠393 keys、r∈{1,5,10} 成本写死 ✓。
- **T1 预注册/资格门**：世界生成/共享算子/隐藏 γ/500 replicate/seed/oracle/null/无泄漏/C0–C7/等成本/两跑/schema/pilot wall≤45min/资格门均列 ✓。
- **T2/T3/边界**：T2 描述+PEEK、T3 data_unavailable/cost_uncalibrated、不称新颖性/决策收益/迁移 ✓。
- **SHA/算术**：v0.2 五份 SHA 与 report 一致；T1 0.0886、T2 0.8087/0.3617、T3 142,894.8/714,474.0/1,428,948.0 CU、393×r×363.6 均与 JSON/报告一致（我逐项重算）；B_C/ON3 锚相容 ✓。

**但 T1 预注册仍不能冻结，原因见 §2：**

## 2. 仍缺（≤5 必改，T1 预注册前完成）

### 必改 1｜T1 的 primary 成本/噪声配置与 500 replicate 的归属未写死 → MDE 0.0886 无法绑定到设计
- v0.2 同时预注册 **3 个预算对**（JSON `equal_cost.budget_pairs`: (300s,4 keys)/(1200s,16 keys)/(3600s,64 keys)）、**3 个 κ**（0.1/1/10）、**2 个噪声 σ**（DESIGN §2.1 {0.05,0.10}）、以及 **500 独立 replicate**；但 **没有说这 500 replicate 是"每个配置 500"还是"所有配置合计 500"**，也没有 primary 配置。
- MDE 0.0886 只在 **n=500 个独立 decision units 对应同一主对比**时成立；若 500 被 3×3×2 配置分摊，每格 n≈28–56，MDE≈0.235–0.33，**T1 预注册门 `MDE≤0.10` 就不成立**；若 500/配置，则 500×18=9,000 replicate×多臂，wall≤45min 与两跑≤90min 很可能不成立。
- 必须写死：**primary 配置**（建议 `(B_C=1200s, B_E=16 keys), κ=1, σ=0.10 或 0.05` 中预先指定一个），primary 配置 **500 个独立 replicate = 500 decision units**；其余 κ/预算对/σ 只作敏感性（数量、seed、Holm/描述规则、不得用于主 H_B）。若坚持全配置 500，则必须把 wall/two-run 预算按 9,000×臂重算，且说明主检验的多重性（18 配置 Holm 会大大降 power，MDE 需重算）。
- 同时修复 **DESIGN §2.4 的 B_C 网格（300/600/1200/2400）与 JSON（300/1200/3600）不一致**；`B_E` 的整数 keys/离散采购也要写死（见必改 2）。

### 必改 2｜等成本表里有**分数 keys**，实验维度 filler 不是"无信息" → 等成本仍不可执行
- JSON equal_cost 例：`B_E_eff_keys=12.251/4.825/4.083`；**key 是离散采购单位**，不能买 0.825 key。必须写死：实验预算换算后按**整数 keys + 空白/QC filler 成本**（或连续 CU 成本面）结算，并给出舍入规则/±1 key 容差；filler 若为"随机实验"会提供真实数据（有信息），必须改为 **blank/QC/重复已知标准品等不进入学习器的无信息动作**，并在无泄漏单测中断言 filler 不进训练/不改变模型；否则 experiment-only 臂会靠 filler 获得额外信息，H_B 不公平。
- 同理 compute-only 的 filler 应是**无信息随机计算步骤**（不产证书/不更新模型）；两维 filler 都必须计入账本且不进入策略信息。
- 目前"随机无信息动作"是文字，没有可执行定义；T1 预注册不能冻结。

### 必改 3｜H_B 的"两个主对比"与配置级多重性未写死
- H_B 说"高于两个单预算对照"；DESIGN 说两独立主对比 + Holm。但 **没写**：是否要求 **两个都显著/为正**？若一个通过、一个不通过，H_B 是成立/部分/不成立？
- 必须写死：H_B 成立 = **两个 Holm 校正后的对比都为正且显著**（或明确预注册的 AND 规则）；只赢一个 → `partial/no_decision_benefit`，不称 H_B。
- 若 primary 配置之外还有 κ/预算/σ 敏感性，必须写死**主检验只在 primary 配置**做 Holm（两个对比）；其他配置只作 `cost_sensitive` 描述，不得用"某个配置赢了"来声称 H_B。否则 3κ×3预算×2σ 的多重选择会严重膨胀。

### 必改 4｜T1 预注册的其余"如/示例"仍未冻结
- `O=20/M=10` 在 DESIGN §2.1 用"如"；必须固定观测/留出菜单大小、plan 宇宙规模、菜单哈希算法；`σ` 的具体分配（哪个是 primary、每格 replicate 数）；`γ` 分布与 τ、`f` 的阶数/特征块、θ 先验；compute step 的精度阶梯/证书收缩表（每 step 成本、区间收缩量）、实验动作库/每动作 CU/信息量、EV 枚举方式、rounds 上限 R_max。没有这些，判定树和 g_C 不可复现。
- 同时固定 **T1 wall/pilot**：500×臂×configs 的估计、pilot 10 replicate 外推、单次≤45min、两跑≤90min；若按 primary 500 + 敏感性配置，说明敏感性配置的 replicate/预算；不得在 wall 超限后减 500/减配置救结果（已写，但要给 primary/sensitivity 的明确数）。

### 必改 5｜T1 结果/批准范围与资格门的文字收紧
- 资格门已列，但需明确 **资格门先于任何 T1 结果读取/报告**；资格失败只写 `design_invalid`，不报 selection accuracy/top-k/regret，不写"算法有效/无效"。
- T1 批准仅限 **模拟器实现 + 资格门**，不等于批准执行结果/效应/决策收益；`T2` 仍 descriptive/PEEK、`T3` 仍 data_unavailable/cost_uncalibrated；不称新颖性/机制/迁移/决策收益/资源足够。
- T1 的 `primary` 是 top-1 selection accuracy **合成效用**；不得外推到 O'Neil/真实决策；T3 397 decision units=393 keys 的 r 敏感性已写，但 **r 的 primary 值**也要预注册（建议 r=5 或 1 明确，其他 sensitivity），否则成本区间可事后选。

## 3. 若完成必改 1–5，建议的 Lead 批准文本（仅 T1 预注册）

> **批准范围**：仅批准 R201-B.1 **T1 合成模拟器预注册的实现与资格门**；不批准 T2/T3 执行、不批准任何效果结果/决策收益/迁移/机制主张；T1 只作计算证据。
>
> **冻结项**：primary 配置 `(B_C=1200s, B_E=16 keys), κ=1, σ=___`，primary **500 独立 replicate = 500 decision units**；其余配置仅敏感性；`T=B_C+κ·B_E_CU` 等成本、整数 keys+filler 账本、H_B 两对比 Holm 且需两者同时为正、max 仅描述；primary=MDE 0.0886≤0.10 的 top-1 selection accuracy；T1 世界/γ/θ/σ/菜单/hash/证书阶梯/实验动作/C0–C7/两跑/schema/wall（单次≤45min、两跑≤90min）按 v0.2+修订冻结；资格门先于任何结果，失败→`design_invalid` 不报结果。
>
> **禁止**：T2/T3 执行；O'Neil/Validation 响应读取；新数据/湿实验；改 primary/δ/MDE/预算/配置后救结果；从 T1 外推真实决策收益/迁移/机制/新颖性；把 T1 结果当 O'Neil/生物证据；把 T2 描述当主检验。

## 4. 判决与边界

- **总判决：revise**。v0.2 已把 v0.1 的 5 条必改实质修好（等成本框架、判定树、primary/MDE/δ、T1 预注册清单、T2/T3/PEEK/边界），算术/SHA 均核验一致；但 **T1 仍有 primary 配置/500 replicate 归属、整数 keys/filler 无信息定义、H_B 两对比的 AND/配置多重性、其余"如"项、资格门/批准范围** 五个未冻结点，冻结后会直接使 MDE 0.0886、等成本、H_B 不可复核。
- **完成必改 1–5 后**：可提交 `approve_mvp_to_lead`（仅 T1 预注册）；**不建议 T2/T3 执行**（T2 descriptive/PEEK、T3 data_unavailable/cost_uncalibrated）。
- **本轮不运行效果/不拟合/不读响应/无湿实验**：只读 v0.2 与 v0.1 产物；只写本文件与 `tmp/`；未改 B 产物。
- **边界**：T1 仅合成计算证据，不外推生物/决策收益；O'Neil/ON3 的 non-blind/peek 不因 T1 改变；不称新颖性/机制/迁移/决策收益/资源足够/独立确认；D1/D3/A1/C187 不重复。

**一句话：v0.2 方向正确、修复 5 条必改的大部分（等成本 κ 换算/嵌套 best-single/判定树/primary top-1+MDE/δ/T1 资格门/T2–T3 边界），SHA 与算术一致；但 T1 仍缺"primary 配置与 500 replicate 归属"（否则 0.0886 不绑定）、整数 keys+filler 无信息定义（experiment-only 等成本不可执行）、H_B 两对比的 AND/配置多重性、以及 O/M/σ/γ/θ/证书阶梯/动作库/EV 的冻结值——判 revise：修完可提交 approve_mvp_to_lead（仅 T1 预注册），T2/T3 不执行。**
