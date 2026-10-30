# R203-N1.2（v0.3）报告：N1 预注册 5 必改修正（设计/算术/V4 实测；不运行效果比较）

2026-10-28。对象：R203-N1（机制账）。依据：N1.1-C1 复核（revise，5 必改）、[challenge_N1_v0_2.md](challenge_N1_v0_2.md)、R203-P1 链、A 线停止记录。
**只做设计/算术/pre-effect 校准：未运行效果比较、未报告方法效果指标、未读 O'Neil 响应、未用 A/B 资源；机制账 only；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定/门槛；0 wells/compute-only。**
- 修正问题定义：[PROBLEM_N1_v0_3.md](PROBLEM_N1_v0_3.md)（`E404C5FE…`）
- 修正执行设计：[DESIGN_N1_v0_3.md](DESIGN_N1_v0_3.md)（`A65158D7…`）
- 生成器/算术：[generator_n1_v0_3.py](generator_n1_v0_3.py)（`B4E93415…`）→ [generator_n1_v0_3.json](generator_n1_v0_3.json)（`1577DDD1…`）
- canonical pilot telemetry snapshot：[timing_n1_pilot_v0_3.json](timing_n1_pilot_v0_3.json)（`94A3646E…`）
- 记录/用量：[record_N1_design_v0_3.md](record_N1_design_v0_3.md)、[usage_N1_design_v0_3.json](usage_N1_design_v0_3.json)
- **v0.1/v0.2 产物未改**。

## 0. 5 必改落实（N1.1-C1）

| # | 复核问题 | v0.3 落实（实测/冻结） |
|---|---|---|
| ① **full-h 摘要两套维数** | PROBLEM §1/DESIGN §0 残留 full 359/288/gauge129 | **全文统一唯一维数**：compact 6-pair **107/312/rank95/nullity12**（参数 gauge 3 + 结构 9）；**full 12-pair（执行宇宙）143/600/rank140/nullity3（参数 gauge=3）**；**函数空间冗余 compact 3+126=129、full 3+252=255**；G3 只依 full 143/600/140/3；**不再出现 359/288/gauge129 作为 full 摘要** |
| ② **pilot 文本 vs telemetry 不一致** | 文本 .0282/12.7/.038 vs timing JSON 实际 | 统一引用 canonical real-pilot snapshot（实现未变）：**per-rep .02603 s、main 11.72 s、memory .037 GB**；逐方法 **B1 .00109 / B2 .00133 / B3 .001 / B4 .01731 / B5 .00083 / B6 .00139 / M .00308 s**；文本/JSON/timing 同一套数字；G7 引用同一 snapshot；旧 .0282/12.7/.038 废弃 |
| ③ **G1 point 门放宽** | v0.2 允许 point≤.05308 | **收紧：point≤.05 且 Wilson 95% upper≤.075**；实测 **point=.0488（976/20000）→ PASS**、**Wilson=.05187≤.075**；**mc_tol=.00308 仅 CI/敏感性说明**，不作 point 放宽；失败→`calibration_failed`/`rename_static_Sadd` |
| ④ **V4 未实际运行** | v0.2 仅规则，"to be measured" | **V4 已实际运行并 PASS**：200 reps、seed=20261061、T_hold=2、static ridge vs **nonstatic filter（soft state responsibilities + weighted ridge）**；**mean ΔELPD=306.1577、SE=65.4612、95% CI=[177.856, 434.459] → PASS**（mean>0 ∧ mean≥2SE ∧ CI lower>0）；失败路径仍为 `design_invalid: rename_static_Sadd`、不进入效果 |
| ⑤ 其余冻结 | — | **n_units=300/MDE80=.04798/n_req278、G2 power=1.000、B1–B6 等预算、B2 等价审计 PASS、caps 1800 s/2 h/8 GB/0 wells、边界/两跑/schema/失败类别不变** |

## 1. 可辨识性/gauge（v0.3 唯一一套维数）

- **参数化**：f 27 + g 36 + h（2 活跃基 per (pair,state)；compact 36/full 72）+ transition 8；显式有限差分 Jacobian 代码在脚本。
- **compact 6-pair（v0.1 代表设计，非执行）**：params **107**、obs **312**、rank **95**、nullity **12**（参数 gauge 3 + 结构冗余 9）。
- **full 12-pair（N1 执行宇宙）**：params **143**、obs **600**、rank **140**、nullity **3 = 参数 gauge 3** → 可辨识维 **140**。
- **gauge 区分**：参数空间加性 gauge = **S=3**（full nullity=3 解释）；函数空间交互加性冗余 = `(2K−1)·pairs·S`：compact **126**（+3=**129**）、full **252**（+3=**255**）；在 2-h-basis 下不作为参数方向；离散状态标签 S! 由 Var 排序固定。
- **G3（只依 full 143/600/140/3）**：参数恢复门（状态核差相关≥.90、transition TV≤.10、β_s/γ_s CI 不含 0、interaction 相关≥.90）；只可在可辨识子空间（140 维）判定；目标量不可辨识→`design_invalid: nonidentifiable`。

## 2. V4 实际运行（pre-effect gate；PASS）

- **模型**：static S-add ridge vs nonstatic state-dependent filter（soft state responsibilities + weighted ridge）；held-out 仅 T_hold=2 轮；GT-nonstatic **200 reps、seed=20261061**。
- **规则**：`ΔELPD=ELPD_nonstatic−ELPD_static`；`SE=sd/√200`；PASS ⇔ mean ΔELPD>0 ∧ mean≥2SE ∧ 95% CI lower>0。
- **实测**：**mean ΔELPD=306.1577**、**SE=65.4612**、**95% CI=[177.856, 434.459]**、**PASS**；分位 p5 −861.3 / p50 206.3 / p95 1502.7。
- **披露**：首版 nonstatic filter 把观测等权分配给三状态（无 soft responsibility）导致 V4 首轮 FAIL（mean ΔELPD=−456.6）；经 oracle-state 诊断（mean +4147.6，确认生成器状态信号强）后修复为**soft-responsibility 加权 ridge**；V4 实际 PASS。该修复属 V4 校准模型实现纠错，已披露；**未调整 V4 规则/阈值/seed**；不涉及效果比较。

## 3. 主终点/headroom/MDE（不变）

- **Primary**：paired held-out decision regret `D_i=R_i(M)−R_i(B2)`（lower better）；δ=**0.05** normalized；菜单 m=5、U∈[0,1]、held-out 仅评价；成功 ⇔ mean ΔR≤−δ 且 95% CI upper<0。
- **MDE**：`MDE80=2.801585·SD/√n_eff`，n_eff=n_units/deff=300/2.2=**136.36**；SD=.20 → **MDE80=0.04798≤.05**；n_req(SD=.20,cluster)=**278≤300**。
- **headroom**：GT-nonstatic 目标 0.10≥δ；GT-static≈0；headroom<δ→`unreachable_gate`；近满分→另立 budget-to-target；**不静默换端点/不降 δ**。

## 4. 基线/审计/预算（不变）

- **B1 full retrain；B2 static S-add（关键强基线）；B3 hierarchical/EB；B4 GP；B5 random plan-pair；B6 decision AL；M=N1 method**；统一 prior/初始数据/feedback/query/调参/特征/seed/wall。
- **B2 等价审计 PASS**：same initial-data hash、menus/round、query count=6、prior、tuning=20、shared generator seed；审计失败→`generator_misspecified`；任何基线等效→`no_increment`。
- **预算**：canonical pilot telemetry per-rep **.02603 s**、main **11.72 s**、memory **.037 GB**；caps wall≤1800 s、CPU≤2 h、内存≤8 GB；0 wells/compute-only；两跑逐字节、结果 JSON 无 telemetry。

## 5. 资格门/失败类别

- **G1** point .0488≤.05 且 Wilson .05187≤.075 → PASS；**G2** powers 1.000/1.000/1.000 → PASS；**G3** full 143/600/140/3 + 参数恢复门；**G4** 无泄漏；**G5** 两跑逐字节；**G6** schema；**G7** 预算（canonical pilot ≤caps）；**V4** 实测 PASS。
- **失败类别统一**：`design_invalid: rename_static_Sadd`、`generator_misspecified`、`calibration_failed`、`nonidentifiable`、`leakage`、`compute_budget_exceeded`、`unreachable_gate`、`precision_insufficient`、`no_increment`、`inconclusive`；失败仅写 `design_invalid`、不报 regret/效果。

## 6. 边界

机制账 only；不称药理/真实决策/迁移/机制/新颖性；合成≠药理；不晋升代码；不恢复停止实验；不改旧门槛/判定；N1 效果执行须另立执行预注册 + 独立挑战 + Lead 批准；本任务不运行效果。

## 7. 产物/确定性/SHA

| 文件 | SHA256 |
|---|---|
| `PROBLEM_N1_v0_3.md` | `E404C5FE529A2432C166B7072D0B5939D9927F37E74A2E620B4AB061F618534C` |
| `DESIGN_N1_v0_3.md` | `A65158D7D226DC8E62B5BD7F43AC9D581239E7D22AF4E9EA55BA3CDDC4B37611` |
| `generator_n1_v0_3.py` | `B4E93415215174239B974651D53AAF282EFCE703B49B84088B9C0EB4A9E6FCF5` |
| `generator_n1_v0_3.json` | `1577DDD187AB25726B6E15EAEF587CA85631F295CF14E28E76D7D62392586B32` |
| `timing_n1_pilot_v0_3.json` | `94A3646E8BB186A53E4DA8D7C8885666EEE56F4ABCABB1988FAC339E1448C53D` |
| report/record/usage | 见 `usage_N1_design_v0_3.json` |

**确定性**：`generator_n1_v0_3.json` 两跑逐字节一致（`1577DDD1…`；wall 3.9/4.9 s）；结果 JSON 无 telemetry（canonical pilot telemetry 在 timing 文件）；文档 SHA 写入 JSON 且一致。

## 8. 建议

1. **提交 v0.3 做独立复核/再挑战**（重点：full 143/600/140/3 唯一维数；pilot telemetry .02603/11.72/.037 一致；G1 point≤.05；V4 实测 PASS 306.16/65.46/[177.86,434.46]；B2 审计与 caps）。
2. 复核通过后请 Lead 批准 **N1 执行预注册**（仅合成机制账；不批效果外推/药理/真实决策/迁移/机制/新颖性）；N1 效果执行另立执行预注册 + 独立挑战 + Lead 批准。
3. **不做**：效果比较/结论、代码晋升、旧判定修改、合成升级为药理。
