# R203-N1 独立挑战（task-131）：非静态 S-add 合成预注册

2026-10-28。角色：独立挑战者（非提案者、未参与 N1、不运行效果结论/不拟合/不读 O'Neil）。对象：[PROBLEM_N1.md](PROBLEM_N1.md)（SHA `23F4668A…`）、[DESIGN_N1.md](DESIGN_N1.md)（`8FAAC491…`）、[generator_n1.py](generator_n1.py)（`F509708E…`）、[generator_n1.json](generator_n1.json)（`21BA30AA…`）、[report_N1_design.md](report_N1_design.md)（`117F89E7…`）、[record_N1_design.md](record_N1_design.md)（`650BB552…`）、`timing_n1_pilot.json`、R203-P1 链、A 线停止记录。**只读；只写本文件与 `tmp/`。**

## 0. 结论先行

**总判决：revise（不是 approve_n1_to_lead，也不是 stop）。**

N1 的**方向/机制边界**基本正确：静态 S-add 有明确退化关系（S=1,P=I,β=γ=0,h=0）；N1 生成含隐藏状态转移、历史/动作依赖、plan-pair 共享动态核、状态依赖 f/g/h、一次反馈统一修订；V1–V4 + `rename_static_Sadd` 的设计方向成立；主终点 held-out regret、headroom/MDE、B1–B6 等预算基线、两本账/边界也基本写清。**但预注册里有 3 个必须先修的硬不一致**：① n_units 在 PROBLEM（300）与 DESIGN/JSON/pilot（360）间冲突，且 MDE 公式写成 `√n_units` 而数值 .0438 实际来自 `n_eff`；② G1 的 GT-static FPR 设计值 **.05023 > 门 .05**，且 `n_rep_calibration=200` 不可能产生 .05023 这一比例，`chosen_amplitudes_meet_gates=true` 与门值矛盾；③ gauge/Jacobian 算术不一致（`n_gauge_constraints=147` vs 陈述的加性常数 gauge 仅 S=3、交互 126→129；params107/rank90/nullity17/G3 不可复算）。另有 V4 仍 "to be measured"、pilot 只是 stub 下界、B2 等价性未实现等需补齐项。

**结论：不能提交 Lead 批准进入 N1 执行预注册；修完必改 1–5 后可提交。**

## 1. 逐条判决

| # | 项 | 判决 | 理由/证据 |
|---|---|---|---|
| ① | 实质区别/V1–V4/rename | **PASS（方向）** | 静态 S-add 退化关系明确：S=1、P=I、β=γ=0、h=0、f/g 不随轮次变；N1 含 s_t∈{1,2,3}、state-specific 历史/动作依赖 softmax、计划对共享同轮 state、状态依赖 f/g/h、一次反馈统一修订、held-out regret；V1（Δ_f/σ≥2、LRT power≥.80）、V2（KL≥.10、β/γ CI 不含 0）、V3（E_h≥.20、interaction power≥.80）、V4（static ELPD 低≥2SE）+ `design_invalid: rename_static_Sadd` 写死；V1–V3 设计 power≈1.00 是设计算术（GT 已知、非 observed），方向可接受。**但 V4 仍 "to be measured"，见 ④/⑤。** |
| ② | 生成器/可辨识/gauge/Jacobian | **FAIL** | 生成器参数 S=3/T=6（fit4/hold2）/m=5/plans12/4×4/σ=.15、f/g 三基、h 两活跃基、双中心化写清 ✓；但 **Jacobian 107×288 rank90/nullity17 与 `n_gauge_constraints=147` 不一致**：陈述的加性常数 gauge `f+c_s, g−c_s` 只有 **S=3** 个约束（不是 `A*S+B*S=21`），交互 gauge `(2K−1)*pairs*S=7*6*3=126`，合计应为 **129**，不是147；params107/rank90/nullity17/G3 "gauge-fixed Jacobian full rank" 需要给出显式参数化/Jacobian/code 才能复算。 |
| ③ | 主终点/headroom/MDE | **FAIL** | 主终点 paired held-out regret `D_i=R_i(M)−R_i(B2)`、δ=.05、U∈[0,1]、m=5、held-out 不更新、成功 mean≤−δ 且 95% CI upper<0 写清 ✓；但 **n_units 不一致**：PROBLEM §2/§8 写 n_units=**300**，DESIGN/generator JSON/timing 写 **360**；**MDE 公式** PROBLEM 写 `2.801585×SD/√(n_units)`，而 .0438 实际来自 `√(n_eff)=√163.6`（n_units=360/deff2.2）。若 n_units=300：n_eff=136.36、MDE≈.0480（≤.05，n_req278≤300仍然过）；若 n_units=360：MDE=.0438。**两套数字不能同时冻结；公式与数值必须统一。** headroom .10≥δ、n_req278、deff2.2 等其余算术正确。 |
| ④ | B1–B6 等预算 | **PASS（需实现）** | B1 full retrain、B2 static S-add（同信息同预算强基线）、B3 EB、B4 GP、B5 random plan-pair、B6 decision AL、M=N1；统一 prior/初始数据/feedback/query T=6/调参≤20/特征信息/wall；任何基线等效→no_increment，方向防选择性比较 ✓；**B2 的"同信息同预算"目前只是文字，须给出与 M 相同的特征/prior/调参/更新次数/seed 实现，并在校准中验证 B2 不被 M 多拿信息**。 |
| ⑤ | 资格门/失败类别/预算诚实性 | **FAIL** | G1 **GT-static FPR 设计 .05023 > 门 .05**；`GT_static_FPR_gate_max=.05`、`chosen_amplitudes_meet_gates=true` 自相矛盾；且 `n_rep_calibration=200` **不可能**产生 .05023（200 reps 的 FPR 只能是 1/200 的整数倍；10/200=.05、11/200=.055；.05023 需非整数计数/更多 reps）。G2 power≈1.000、G5/G6/G7 方向写清；**G1 实际 fail/不可判**，必须重算。G3 受 ② 影响；V4 仍 "to be measured"；pilot `timing_n1_pilot.json` 只是 stub（per_replicate .00041s、scale1575、projected .77s，main≈0.95s 下界），不是真实 generator/7 方法/B2 的 pilot，G7 不能以此冻结预算。 |
| ⑥ | 边界 | **PASS** | 机制账 only；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；不恢复停止实验；不改旧判定/门槛；N1 执行须另立预注册+Lead 批准；0 wells/compute-only；不用 A/B 资源 ✓。 |
| ⑦ | 总判决 | **revise** | 见 §2。 |

## 2. 三个最致命问题（可复核）

### 2.1 n_units/MDE 双重不一致
- `PROBLEM_N1.md` §2/§8：`n_units=300`；`DESIGN_N1.md` §1/§2、`generator_n1.json → budget.main`、`timing_n1_pilot.json → main`：`n_units=360`。
- `PROBLEM_N1.md` §4 写 `MDE80=2.801585×SD(D)/√(n_units)`；`DESIGN_N1.md` §2.2 写 `√(n_eff)`，`n_eff=n_units/deff=360/2.2=163.636`，`.0438` 正是 `2.801585×.20/√163.636`。**若按 PROBLEM 的 √n_units 公式**，n_units=360 时 MDE=.0295、300 时 .0323，均不是 .0438。
- 后果：N1 预注册的 n/功效/预算/`n_req` 三个表不能同时成立；执行前必须选一个 n_units 并把所有文件（PROBLEM/DESIGN/JSON/pilot/schema）统一；若选 300，MDE 应重算为 **≈.0480**（仍≤.05、n_req278≤300），若选 360 则保持 .0438。**不能按 300 写、按 360 算。**

### 2.2 G1 FPR 实际超过门，且 200 reps 与 .05023 不自洽
- `generator_n1.json → calibration_power`: `GT_static_FPR=.05023`, `GT_static_FPR_gate_max=.05`, `n_rep_calibration=200`, `chosen_amplitudes_meet_gates=true`。
- **.05023 > .05**，按字面 G1（≤.05）**FAIL**；同时 200 次校准的 FPR 只能是 0、.005、.010…（10/200=.05、11/200=.055），**不可能等于 .05023**。这不是四舍五入可解释的差异（10/200=.0500，不是 .05023）。
- 必须修：要么预注册 **Monte Carlo 容差**（例如 FPR 的 95% 上界≤.05，或 n_rep 足够大并给 MC SE），要么把门改为可判定的精确值并重算；**在修复前不得写 `chosen_amplitudes_meet_gates=true` 或让 G1 PASS**。

### 2.3 gauge/Jacobian 算术不一致
- `generator_n1.json → identifiability`: `n_parameters_unconstrained=107`, `n_observations=288`, `rank_jacobian=90`, `nullity=17`, `n_gauge_constraints=147`, `rank_after_additive_gauge_projection=90`。
- 陈述的 gauge 是 `f_{a,s}+c_s, g_{b,s}−c_s`：**每状态一个 c_s，共 S=3 个**，不是 `A*S+B*S=3*3+4*3=21`。交互 `h+φ(d_a)+ψ(d_b)` 的 gauge 为 `(2K−1)*pairs*S=7*6*3=126`。合计 **129**，不是147。
- 107 params、rank90、nullity17 与 147 gauge 不能同时作为同一个 Jacobian 的自由度核算；G3 "gauge-fixed Jacobian full rank" 现在不可复算。必须给出显式参数向量/观测方程/Jacobian 代码，重算 params/obs/rank/nullity/gauge，并明确哪些是参数 gauge、哪些是函数空间冗余；否则参数恢复门（状态核相关≥.90、transition TV≤.10、β/γ CI、interaction 相关≥.90）没有可执行前提。

## 3. 必改（≤5，N1 执行预注册前）

1. **统一 n_units 与 MDE 公式**：冻结 300 或 360；统一 PROBLEM/DESIGN/JSON/pilot；MDE 用 `n_eff=n_units/[1+(m−1)ICC]`；重算 `MDE/headroom/n_req`；若选 300，写 **MDE≈.0480** 而不是 .0438；`n_req=278≤n_units` 仍成立；不得双口径。
2. **修 G1 校准门**：`.05023>.05` 不得 PASS；重算 GT-static FPR，预注册校准 n_rep（足够大）与 MC 容差/上界规则；`chosen_amplitudes_meet_gates` 由实际计算决定；G1 失败→`calibration_failed`/`rename_static_Sadd`，不报效果。
3. **重算 gauge/Jacobian**：按 `f+c_s,g−c_s`（S=3）+ 交互 `(2K−1)*pairs*S=126` 得到 129，或给出为什么仍是147的显式约束；重算 params107/obs288/rank90/nullity17；提供 Jacobian 代码/参数化；G3 的满秩/参数恢复门基于重算结果。
4. **V4 预注册**：目前 `V4 pass="to be measured"`；必须写死 static S-add 的 ELPD 估计（模型、held-out、SE、n_rep、seed）与 ΔELPD≥2SE 判定；V4 是执行前 gate，不是"以后再说"；V1–V4 全 PASS 才进入效果。
5. **真实 pilot/预算 + B2 等价**：`timing_n1_pilot.json` 是 stub（.00041s/rep、scale1575、projected .77s、main≈0.95s 下界），需用真实 generator + 7 方法（含 B2 static S-add）做 pilot，测 wall/CPU/内存；G7 用实测投影，不能用 stub 下界；B2 必须与 M 同特征/prior/初始化/feedback/query/调参/seed，并做等价审计（否则 no_increment 不能判断）；预算 caps（1800s/2h/8GB/0 wells）保留。

## 4. 修完后建议的 Lead 批准文本（仅 N1 执行预注册，不是效果执行）

> **批准范围**：在必改 1–5 完成并通过独立复核后，批准 R203-N1 **执行预注册**（机制账、合成、compute-only、0 new wells），不批准效果结论/外推；不批药理/真实决策/迁移/机制/新颖性。
>
> **冻结**：静态退化关系与 N1 生成器（S=3/T=6 fit4/hold2/m=5/plans12/4×4/σ=.15/f/g 三基/h 两活跃基/双中心化/两套 GT）；V1–V4+`rename_static_Sadd`；单一 n_units（300 或360）与 `MDE=2.801585·SD/√n_eff`（n_eff=n_units/deff；若300则MDE≈.0480）；headroom .10、δ=.05、n_req278；G1–G7（G1 需按修正后的 FPR 门真实 PASS；V4 必须先测）；B1–B6 等预算（B2 同信息同预算强基线）；两跑/schema/失败类别；caps wall≤1800s/CPU≤2h/8GB/0 wells；机制账边界。
>
> **禁止**：效果外推/药理/决策收益/迁移/新颖性；用 A/B 资源；改旧门槛/判定；恢复停止实验；晋升代码；在 G1–G7/V1–V4 未全 PASS 前报 regret；用 stub pilot 代替真实预算；用 6,282 或合成替代真实 decision；任何 N1 效果执行须另立预注册+独立挑战+Lead 批准。

## 5. 声明

- **本轮不运行效果结论/不拟合/不读 O'Neil**：只读 N1 预注册与 generator JSON/pilot、R203-P1 链、A 线停止记录；只写本文件与 `tmp/`；未改 N1 产物。
- **总判决：revise**。N1 的实质区别/生成器方向/V1–V4 判据/主终点/headroom/MDE/B1–B6/边界基本正确；但 **n_units 300 vs360 与 MDE 公式（√n_units vs √n_eff）、G1 FPR .05023>.05 且 200 reps 不自洽、gauge/Jacobian 147 vs 129/rank90/nullity17、V4 未测、pilot 只是 stub** 这五类必须先修；修完可提交 Lead 批准 **N1 执行预注册**（不是效果执行）。修完之前 **不能 approve_n1_to_lead**。

**一句话：N1 不是静态 S-add 改名（退化关系 S=1/P=I/β=γ=0/h=0；N1 有 S=3 状态转移/历史动作依赖/plan-pair 共享核/状态依赖 f,g,h/held-out regret），V1–V4 方向成立；但 n_units 在 PROBLEM（300）与 DESIGN/JSON/pilot（360）冲突且 MDE 公式写 √n_units 而 .0438 来自 √n_eff、G1 的 GT-static FPR .05023>.05 且 n_rep200 不可能产生该比例、gauge 147 vs 129/rank90/nullity17 不可复算、V4 未测、pilot 只是 stub——判 revise：修完 1–5 后可提交 Lead 批准 N1 执行预注册（机制账、0 wells、不批效果/药理/决策收益）。**
