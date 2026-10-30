# DESIGN_N1_v0_3 —— R203-N1.2 执行设计（非静态 S-add + plan-pair conflict；v0.3 修正预注册，不运行效果）

2026-10-28。修正 v0.2（[DESIGN_N1_v0_2.md](DESIGN_N1_v0_2.md) `1B179AB9…`，保留不改）。依据：N1.1-C1 复核（5 必改）、[PROBLEM_N1_v0_3.md](PROBLEM_N1_v0_3.md)、`generator_n1_v0_3.json`、`timing_n1_pilot_v0_3.json`、R203-P1 链。
**状态：预注册草案 v0.3（未执行效果）。N1 效果执行须另立执行预注册 + 独立挑战 + Lead 批准；本文件不含效果结论。**

## 0. v0.2 → v0.3 修正摘要

| 必改 | v0.3 落实 |
|---|---|
| ① full-h 摘要统一 | **只用一套维数**：compact 6-pair **107/312/rank95/nullity12**（参数 gauge 3+结构 9）；full 12-pair（执行宇宙）**143/600/rank140/nullity3（参数 gauge=3）**；函数空间冗余单列 compact **129**/full **255**；G3 只依 full 143/600/140/3；**不再出现 359/288/gauge129 的 full 摘要** |
| ② pilot telemetry 一致 | 统一引用 canonical pilot snapshot（`timing_n1_pilot_v0_3.json`，实现同 v0.2）：**per-rep .02603 s、main 11.72 s、memory .037 GB**；逐方法 **B1 .00109/B2 .00133/B3 .001/B4 .01731/B5 .00083/B6 .00139/M .00308**；G7/预算同一套数字 |
| ③ G1 point 门收紧 | **point≤.05**（实测 .0488 PASS）且 **Wilson 95% upper≤.075**（实测 .05187）；`mc_tol=.00308` 仅 CI/敏感性说明，不作 point 放宽；失败→`calibration_failed`/`rename_static_Sadd` |
| ④ V4 实际运行 | **已实测 PASS**：200 reps、seed=20261061、T_hold=2、static ridge vs nonstatic filter（soft responsibilities/weighted ridge）；mean ΔELPD=**306.1577**、SE=**65.4612**、95% CI=**[177.856, 434.459]**；失败→`rename_static_Sadd`、不进效果 |
| ⑤ 其余冻结 | n_units=300/MDE80=.04798/n_req278、G2、B1–B6 等预算、B2 等价审计、caps 1800 s/2 h/8 GB/0 wells、边界/两跑/schema/失败类别不变 |

## 1. 冻结对象

- **n_units=300**（唯一值）；S=3、T=6（fit 4 / held-out 2）、m=5、plans=12（A=3×B=4）、4×4 剂量、σ=.15、f/g 三基、h 两活跃基（double-centered）、state-specific β_s/γ_s 转移。
- ground truths：GT-static（S=1,β=γ=0,h=0）→ G1；GT-nonstatic（S=3,β_s/γ_s≠0,h≠0,Δ_f/σ=2）→ G2/V4。
- 主终点：paired held-out regret `D_i=R_i(M)−R_i(B2)`，δ=.05 normalized；U∈[0,1]；菜单 m=5；held-out 不更新；成功 ⇔ mean ΔR≤−δ 且 95% CI upper<0。
- 预算：n_units=300、R=50、methods=7、T=6；wall≤1800 s、CPU≤2 h、内存≤8 GB；0 wells/compute-only。

## 2. 预检（先于效果）

- headroom：GT-nonstatic 目标 0.10≥δ=.05；GT-static≈0；执行前 calibration pilot 估 headroom/SD(D)。
- MDE：`MDE80=2.801585·SD/√n_eff`，n_eff=136.36；SD=.20→**0.04798≤.05**；n_req(cluster)=**278≤300**；SD=.30→623>300→precision_insufficient。
- 不通过：headroom<δ→unreachable_gate；MDE>δ/n_req>300→precision_insufficient；不降 δ、不静默加 n、不换端点。

## 3. 可辨识性/gauge（v0.3 唯一维数；执行前 gate）

- compact 6-pair：107/312/rank95/nullity12（参数 gauge 3+结构 9）。
- full 12-pair（执行宇宙）：**143/600/rank140/nullity3（参数 gauge=3）**；可辨识维 140；函数空间冗余 compact 129/full 255（交互加性方向非参数方向）。
- **G3**：full 设计 rank140/nullity3；参数恢复门（状态核差相关≥.90、transition TV≤.10、β_s/γ_s CI 不含 0、interaction 相关≥.90）；仅可辨识子空间判定；目标不可辨识→`design_invalid: nonidentifiable`。

## 4. V4（已实际运行 PASS；执行前 gate）

- static ridge vs nonstatic filter（soft responsibilities + weighted ridge）；held-out T_hold=2；n_rep=200、seed=20261061；`ΔELPD=ELPD_nonstatic−ELPD_static`；`SE=sd/√200`。
- **实测 mean ΔELPD=306.1577、SE=65.4612、95% CI=[177.856, 434.459] → PASS**；若失败→`design_invalid: rename_static_Sadd`、不进入效果；V1–V4 全 PASS 才进入效果。

## 5. 方法/基线（等 compute/query；B2 等价审计）

统一 prior/初始数据/feedback（每轮 1 次）/query T=6/调参≤20/特征信息/seed/wall：**B1 full retrain；B2 static S-add（关键强基线）；B3 hierarchical/EB；B4 GP；B5 random plan-pair；B6 decision AL；M=N1 method**。
**B2 等价审计 PASS**（canonical pilot）：initial-data hash、menus、query count=6、prior、tuning=20、shared seed；审计失败→`generator_misspecified`；任何基线等效→`no_increment`。

## 6. 校准/资格门 G1–G7 + V4（先于效果；失败只写 design_invalid）

| 门 | v0.3 规则 | 失败类别 |
|---|---|---|
| G1 | point≤.05（实测 .0488）且 Wilson upper≤.075（实测 .05187）；mc_tol 仅敏感性 | `calibration_failed`/`rename_static_Sadd` |
| G2 | GT-nonstatic power（state/interaction/history）≥.80−mc_tol；实测 1.000/1.000/1.000 | `calibration_failed` |
| G3 | full 143/600/140/3 + 参数恢复门 | `nonidentifiable` |
| G4 | 无泄漏 | `leakage` |
| G5 | 两跑逐字节 | `design_invalid` |
| G6 | schema/失败模板 | `design_invalid` |
| G7 | **canonical pilot telemetry**（.02603 s/rep、11.72 s main、.037 GB）≤caps | `compute_budget_exceeded` |
| V4 | 已实测 PASS（§4） | `rename_static_Sadd` |

## 7. 预算与运行

- **pilot telemetry**：canonical v0.2 real-pilot snapshot（实现未变）：per-rep **.02603 s**、projected main **11.72 s**、memory **.037 GB**；逐方法 B1 .00109/B2 .00133/B3 .001/B4 .01731/B5 .00083/B6 .00139/M .00308 s；G7 引用同一 snapshot；执行前须用最终实现重跑 pilot 并冻结预算。
- **主预算**：n_units=300、R=50、methods=7、T=6、每轮 1 反馈；caps wall≤1800 s、CPU≤2 h、内存≤8 GB；0 wells/compute-only；不使用 A/B 资源。
- 两跑逐字节一致（结果 JSON 无 telemetry；timing/telemetry 单独文件）；schema 与失败模板预注册。
- **失败类别**：`design_invalid: rename_static_Sadd`、`generator_misspecified`、`calibration_failed`、`nonidentifiable`、`leakage`、`compute_budget_exceeded`、`unreachable_gate`、`precision_insufficient`、`no_increment`、`inconclusive`。
- **任何 N1 效果执行**：须另立执行预注册 + 独立挑战 + Lead 批准；本文件不运行。

## 8. 批准清单

1. 5 必改落实：full 143/600/140/3 唯一维数（compact 107/312/95/12；函数空间 129/255）；pilot telemetry .02603/11.72/.037 一致；G1 point≤.05；V4 实测 PASS。
2. 生成器/两套 GT/V1–V4/`rename_static_Sadd`；可辨识/参数恢复门。
3. 主终点/U/regret/菜单/held-out/δ=.05；MDE .04798/n_req278；headroom 预检。
4. B1–B6 等预算+B2 审计；G1–G7/V4；失败类别/停止；caps/两跑/schema。
5. 机制账边界：不称药理/真实决策/迁移/机制/新颖性；不晋升代码；不恢复停止实验；不改旧判定；0 wells。
