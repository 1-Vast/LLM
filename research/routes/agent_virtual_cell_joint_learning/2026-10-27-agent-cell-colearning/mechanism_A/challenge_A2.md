# R201-A.2 独立挑战（task-119）：零模型/σ 尺度修正预注册

2026-10-28。角色：独立挑战者（非提案者、未参与 A/A.1/A.2、不运行 P1/不拟合/不读 O'Neil 响应做效应）。对象：[PROBLEM_A2.md](PROBLEM_A2.md)（SHA `93C7613B…`）、[DESIGN_A2.md](DESIGN_A2.md)（`6BB3460E…`）、[null_design_A2.json](null_design_A2.json)（`7BCBA58D…`）、[report_A2.md](report_A2.md)（`CAC37748…`）、[record_A2.md](record_A2.md)（`DB1F8BE1…`）、`p0p1/a_p0p1.json`、A.1 设计/挑战、R201 BRIEF。**只读；只写本文件与 `tmp/`。**

## 0. 结论先行

**总判决：revise（不是 approve_a2_to_lead，也不是 stop）。**

C192 复述、候选 null 合成校准/选择规则（N0/N1/N3/N5 eligible；N2 FPR .165 不 eligible；N4 .947 invalid）、primary=N0 + per-cell=N1、A.2 诊断门/预算/边界**大部分正确**；但 **σ 的 S2 公式有一个可解析的因子 2 错误**，与 A.1 的原始错误同型——若不修，A.2 会再次把 F_pair 的尺度缩到一半，而 D2 的"F_self"检验因用半拆差做分子反而恒等于 1，无法发现。**A.2 预注册不能按当前 S2/F_self 冻结。**

最致命 3 条：
1. **S2 因子 2**：`σ_pair²_A2 = mean ||P⊥(f_h1−f_h2)||²/(K−1)`。H0 下半拆 profile 各用 2 wells×M=4：`Var(h)=σ_w²/8`；`f_h1−f_h2` 方差 = `σ_w²/4 = 2σ_pair²`（而 full profile pair difference 方差 = `σ_w²/8 = σ_pair²`）。所以 **S2 估计的是 2σ_pair²，不是 σ_pair²**；把它当 `σ_pair²_A2` 会使 `F_pair` 的期望变成 **0.5**（不是 1），`F_crit=2.60` 下的实际 FPR/功效全部偏；这正是 A.1 `σ_pair²=2×S1` 的同一错误，只是换了一个名字。正确应为 **`σ_pair²_A2 = 0.5 × mean ||P⊥(f_h1−f_h2)||²/(K−1)`**（或把 F_pair 分母同时改为 S2/2，并明确等价）。
2. **F_self 归一化门是恒等式，无法检出该尺度错误**：D2/D3 用**同一个半拆差**的 `||P⊥(f_h1−f_h2)||²/(K−1)` 除以 S2；按 S2 的定义这个比值恒≈1，所以 `F_self∈[0.5,2]`/FPR 门会在 F_pair 已半尺度的情况下**自动通过**。A.1 的 F_self 中位 .4579 本来就能被这一恒等式掩盖。必须把自检改成**与 F_pair 分子同方差**的统计量（full profile pair difference 的 H0 模拟/重拟合零分布，或至少 `0.5×` 乘子后的 F_self），并重新预注册 D2/D3/F_crit 条件。
3. **A.2 的合法 pair 规则与 σ 变更的交互未写死**：A.1 的单独合法规则是 `RMS ≤1.96·σ_obs/2`；A.2 改 σ 方案后，阈值应用 S2 还是 S1、σ_w_hat 还是 σ_obs，DESIGN §1 说"不变/其中 σ_obs 定义见 §2；改用 A.2 σ 方案后按新 σ 重算阈值属 A.2 的一部分"——**前后矛盾**（PROBLEM §1 说规则不变）。合法 pair 集合 |legal| 会随 σ 改变，进而影响 n_legal、pooled、T_c、BH；必须预先写死 A.2 的合法规则公式/σ 来源，不能执行时再选。

## 1. 逐条判决

| # | 项 | 判决 | 理由/证据 |
|---|---|---|---|
| ① | C192 复述/A.1 negative 不可解释性 | **PASS** | 我核对 `null_design_A2.json → c192_recap`：null pooled 中位 **0.74567285≫obs 0.15369652**；null median T **146.30887≫obs 73.42974**；`σ_obs_frozen=0.06570366` vs `σ_obs_alt=0.092919`；`F_self_median=0.457881`；frozen `σ_pair²=0.00215849`；U=340,088、n_legal=110,523、half_split_fpr=0.08348。A.1 negative 只能写"本资源/本族/本设计（冻结 null）下未检出"，不是机制阴性——正确。 |
| ② | 候选 null 合成校准与选择规则 | **PASS（但受 ③ 的尺度错误影响）** | `null_design_A2.json → candidate_nulls.table` 与 Lead 一致：N0 FPR .04825/power .2956 eligible；N1 .05407/.2889 eligible；N2 .16519/.1933 不 eligible；N3 .042/.2956 eligible；N4 .94741 invalid 对照；N5 .0485/.2956 eligible；选择规则（FPR∈[.02,.10]、非 N4、power 最高、并列 N0>N3>N2>N1>N5）在**合成校准**上预注册，primary=N0、per-cell=N1 bootstrap；未用 A.1/A.2 observed 选 primary（N4 排除来自 A.1 已观察事实，属已登记对照）——规则本身可接受。**但**合成校准用的是"F 归一化 E=1"的合成 F；若 S2 仍为 2σ_pair²，实际 F_pair 是半尺度，N0 的 FPR/power 不能直接搬到 A.2（见 ③）。 |
| ③ | σ 修正/S1/S2/F_self/F_crit | **FAIL（S2 因子 2 + 自检恒等）** | 推导：R=4、M=4；`Var(f)=σ_w²/16`；`Var(f_p−f_q)=σ_w²/8=σ_pair²`；半拆 `Var(f_h1−f_h2)=2×σ_w²/8=2σ_pair²`。S2 定义正是半拆差的投影平方均值 ⇒ **E[S2]=2σ_pair²**；把它当 σ_pair² 使用 ⇒ `E[F_pair]=0.5`。设计同时用 `F_self=||P⊥(f_h1−f_h2)||²/(K−1)/S2`，按定义恒≈1；D2/D3 门因此**测的不是 F_pair 尺度**。正确 S2 需乘 0.5；F_self 需另立（full profile pair 的 H0 模拟/重拟合，或等价乘子），不能沿用当前公式。 |
| ④ | A.2 执行设计/诊断门/预算/失败类别 | **WEAK/FAIL** | 不变项、F_pair/T_c/pooled、BH q=0.05、N_perm=500、F_crit=2.60 条件、阳性三条件、D1–D7、失败类别、data-only/0 wells/wall≤900s/CPU≤2h/8GB/两跑/JSON 无 telemetry 基本写清 ✓；N1 per-cell 与 N0 pooled 的分工合理 ✓。**但**：(a) S2 尺度错误使 D2/D3 失效（见 ③）；(b) 合法 pair 规则的 σ 来源/阈值在 PROBLEM 与 DESIGN 间矛盾（见致命 3）；(c) N1 参数化 bootstrap 的 per-cell 500 次模拟是否与"≈2,500 模拟"预算一致、是否每次拟合 shared f+g 的耗时在 900s 内，需要执行前预算测试；(d) 失败类别 `noise_calibration` 在 PROBLEM 的列表里没有、DESIGN D3 才出现，需统一。 |
| ⑤ | 边界 | **PASS** | 阳性仅"本资源/本族/本设计下存在联合矛盾（开发性）"；阴性仅 `no_joint_contradiction`；不写"矛盾不存在"；pair 级描述性；不进入 P2/S2/H_A2；non-blind/peeked；不称生物学/机制/迁移/决策收益/新颖性 ✓。 |
| ⑥ | 总判决 | **revise** | 见 §3。 |

## 2. 关键推导与后果（可复核）

### 2.1 S2 的真实期望
记单孔方差 σ_w²，R=4 技术重复，M=4 伙伴剂量：
- full profile `f = mean(4 wells)·mean(M rows)`：`Var(f)=σ_w²/(4·4)=σ_w²/16`；
- full pair difference `f_p−f_q`：`Var=σ_w²/8 = σ_pair²`；
- 半拆 profile `f_h1,f_h2` 各用 2 wells（每行 2 孔）再对 M 取均值：`Var(h)=σ_w²/(2·4)=σ_w²/8`；
- `f_h1−f_h2`（两半独立）：`Var=2σ_w²/8=σ_w²/4 = 2σ_pair²`。
- 投影残差 `P⊥` 有 (K−1)=3 维，`E||P⊥d||²=(K−1)Var(d)`；所以 `E[S2]/ (K−1)` 的归一化 = **2σ_pair²**。
- 若 `σ_pair²_A2 = S2`，则 `E[F_pair] = σ_pair²/(2σ_pair²)=0.5`；而 `F_self` = (2σ_pair²)/(2σ_pair²)=1——**自检恒等，F_pair 半尺度**。
- 正确：`σ_pair²_A2 = 0.5·mean ||P⊥(f_h1−f_h2)||²/(K−1)`；或 `σ_pair²_A2=S2` 但 F_pair 分母用 S2/2（等价，须写清）。**A.1 的 `σ_pair²_frozen=2×S1` 就是 2σ_pair²；当前 S2 公式会得到同一个 2×量，A.2 名义上"修 σ"但 F_pair 仍会是 A.1 的半尺度。**

### 2.2 为什么 D2/D3 掩盖
- `F_self` 的分子是 `||P⊥(f_h1−f_h2)||²/(K−1)`，分母是 S2（同一个量），所以 `F_self≈1` 是定义恒等，不是 F_pair 的归一化证据。
- 正确的自检应使用**与 F_pair 分子同方差**的量：例如用 N1 拟合 shared f/g 后模拟 full profile pair `f_p−f_q` 的 H0 F 分布（E=1 检查），或使用 **`0.5×`** 乘子后的 self 统计量；D2/D3 必须重写。
- 若不修：A.2 的 observed F_pair 会是 A.1 的半尺度；N0 χ² null（E=1）会系统性高于 observed，**A.2 可能得到 no_joint_contradiction**，但那是尺度错误造成的，不是证据。

### 2.3 合法 pair 规则
- A.1：`RMS ≤1.96·σ_obs/2`（σ_obs 冻结 .06570366）；A.2 若改 σ，合法集合与 |U=340,088| 内的 legal pairs=110,523 都会变；**必须写死 A.2 用哪个 σ（S2 校正量还是 S1）、阈值公式、是否保持 A.1 的 legal 集合不变**。PROBLEM §1 说"规则不变"，DESIGN §1 又写"按新 σ 重算阈值属 A.2 的一部分"——执行前必须二选一，不能到执行时再定。

## 3. 必改（≤5，A.2 执行前完成）

1. **修正 S2**：`σ_pair²_A2 = 0.5 × mean ||P⊥(f_h1−f_h2)||²/(K−1)`（或等价地 F_pair 分母用 S2/2），并重算 `σ_pair²_A2`/`F_pair`；在 A.2 预注册中写明 S2 与 S1、A.1 frozen 的倍数关系（预期 S2 校正后≈0.00107924，而不是 0.00215849）。
2. **重写 F_self/D2/D3 自检**：自检统计量必须与 F_pair 分子同方差（full profile pair difference 的 H0 模拟/重拟合，或明确的 0.5 乘子）；D2 目标应验证 `E[F_pair]≈1`（不是半拆差/S2 的恒等 1）；重算 F_self FPR@F_crit（≤0.10）与 F_crit=2.60 的条件；若不通过→`design_invalid: scale_mismatch`，不缩放 A.1、不改阈值。
3. **重算候选 null 的 FPR/power**：用修正后的 F 尺度重新合成校准 N0/N1/N3/N5，确认 FPR∈[.02,.10] 且 power；若 N0 不再 eligible/低于其他候选，按预注册选择规则重选（仍不看 A.2 observed）；若没有合格者→`design_invalid: null_calibration`。
4. **写死合法 pair 规则**：明确 A.2 用哪个 σ（S2 校正量或 S1）与阈值公式；是否保持 A.1 legal 集合不变；n_legal 会变时预注册 pooled/BH 的口径；不得执行时按 observed 选。
5. **预算/失败类别统一**：N1 per-cell 500 次 bootstrap 的拟合次数/耗时与 N0 pooled 500、候选诊断 2,000 的总模拟数写入预算测试；确认 ≤900s/2h/8GB；统一 `noise_calibration` 与 `null_calibration/scale_mismatch/compute_budget_exceeded` 的失败类别；两跑/schema 保持不变。

## 4. 若完成必改 1–5，建议 Lead 批准文本（仅 A.2 data-only P1 重跑）

> **批准范围**：仅批准 R201-A.2 的 **data-only P1 重跑**（0 新 wells、不读新响应、不做效应/机制/迁移/决策主张）；不批准 P2/S2/H_A2、不批准 A.1 改判、不批准任何生物学/机制/新颖性声明。
>
> **冻结**：数据/target30/|U|=340,088/合法 pair 规则（按 A.2 预注册 σ 公式）/F_pair/T_c/pooled/F_crit=2.60（仅在 S2 修正与 D2/D3 重写后通过时保留）/N_perm=500/BH q=0.05/阳性三条件；S2 采用**半拆差的 0.5× 修正**；F_self/D2/D3 用与 F_pair 同方差的 H0 自检；primary null=N0、per-cell=N1；D1–D7 先于 P1；失败类别统一；预算 wall≤900s/CPU≤2h/8GB/≈2,500 模拟/两跑逐字节；A.2 通过前不进 P2/S2/H_A2。
>
> **禁止**：用 A.1 结果改 null/σ/阈值；用 observed A.2 选 null/legal 规则；把 A.2 negative 写成"矛盾不存在"；把 A.2 阳性写成机制/生物学/迁移/决策收益；改数据/加 wells/减 N_perm。

## 5. 声明

- **本轮不运行 P1/不拟合/不读 O'Neil 响应做效应**：只读 A2 产物、null_design JSON、p0p1 C192 记录；只写本文件与 `tmp/`；未改 A/A.1/A.2 产物。
- **总判决：revise**。C192 复述与候选 null 选择规则 PASS；但 **S2 半拆差估计的是 2σ_pair²，不是 σ_pair²；F_self 用同一半拆差/S2 恒等于 1，无法发现 F_pair 半尺度；且合法 pair 规则的 σ 来源未写死**——不修则 A.2 会重复 A.1 的因子 2 错误，不能批准执行。修完必改 1–5 后可提交 Lead 批准 data-only P1 重跑（0 新 wells；不进入 P2/S2/H_A2）。

**一句话：A.2 的 null 选择（N0/N1/N3/N5 合成校准、N2/N4 排除、N0 primary+N1 per-cell）和 C192 复述是对的；但 S2 = mean||P⊥(f_h1−f_h2)||²/(K−1) 估计的是 2σ_pair²（半拆差方差=2×full pair 差），把它当 σ_pair² 会让 F_pair 期望=0.5，而 F_self 用同一半拆差/S2 恒≈1 掩盖错误——这是 A.1 因子 2 的重演。必须把 S2 乘 0.5、重写与 F_pair 同方差的自检、重算 N0/N1 校准，并写死合法 pair 规则的 σ；判 revise，修完可批准 A.2 data-only P1 重跑（0 新 wells，不进 P2/S2/H_A2）。**
