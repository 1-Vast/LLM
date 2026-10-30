# record_N1_design_v0_2.md —— R203-N1.1 修正预注册执行记录（设计/算术/真实 pilot；不运行效果）

角色：独立设计/审计员（未参与 R197/R200/203 模型开发）· 任务 task-132（R203-N1.1，机制账）· 日期 2026-10-28
只写 `research/2026-10-28-n1-synthetic-prereg/` 下 v0.2 文件与 `tmp/`；**未改 v0.1 产物/A-B-D 线/R203-P1 产物**；未运行效果/方法比较；未读 O'Neil 响应；0 wells/compute-only。

## 0. 要求与完成对照（N1-C1 5 必改）

| 必改 | 状态 |
|---|---|
| ① n_units/MDE 统一 | ✅ **n_units=300 冻结**于 PROBLEM/DESIGN/JSON/pilot（无 360）；MDE 公式 `2.801585·SD/√n_eff`、n_eff=136.36；**MDE80=0.04798≤.05**；n_req(SD=.20,cluster)=**278≤300** |
| ② G1 FPR 修复 | ✅ 预注册 MC 规则：χ²_3 crit=7.8147、α=.05、n_mc=20000、mc_tol=.00308、Wilson upper≤.075；**实测 k=976/20000、point=.0488、Wilson=.0519 → PASS**；`chosen_amplitudes_meet_gates` 由实测 G1/G2 决定；失败→calibration_failed/rename |
| ③ gauge/Jacobian 重算 | ✅ 显式参数化+有限差分代码；compact 6-pair：107/312/rank95/nullity12（3 参数 gauge+9 结构冗余）；**full 12-pair（执行宇宙）：143/600/rank140/nullity3=加性参数 gauge**；函数空间冗余加性3+交互126=**129**（compact）/252+3=255（full）；参数 gauge 与函数空间冗余分开 |
| ④ V4 冻结 | ✅ static vs nonstatic ELPD 规则：held-out T_hold=2、n_rep=200、seed=20261061、SE=sd/√200、判定 mean ΔELPD>0 ∧ ≥2SE ∧ 95% CI lower>0；失败→rename_static_Sadd；执行前 gate |
| ⑤ 真实 pilot+B2 等价 | ✅ 真实 generator+7 方法（含 B2）pilot：**per-rep 0.0282 s、投影 main≈12.7 s、内存 0.038 GB**；B2 等价审计 PASS（initial-data hash/menus/query count/prior/tuning/seed）；caps 1800 s/2 h/8 GB/0 wells；G7 用实测投影 |
| 边界 | ✅ 机制账 only；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定；N1 效果另立预注册+挑战+Lead 批准 |
| 标 completed + send_message | ✅ |

## 1. 时间线（Asia/Shanghai，2026-10-28）

| 时间 | 事件 |
|---|---|
| ~10:33 | 读 task-132 并 claim；读 N1-C1 challenge、v0.1 N1 产物、R203-P1 链 |
| ~10:35 | 写 `PROBLEM_N1_v0_2.md`（5 必改落实、n_units=300、G1 MC 规则、gauge 区分、V4、真实 pilot/B2 审计） |
| ~10:36 | 写 `DESIGN_N1_v0_2.md`；写 `generator_n1_v0_2.py` |
| ~10:38 | 修 bug：identifiability 从 full-h（饱和不可辨）改为 **2-basis h**；transition 观测块改为 4 条件（baseline/response/action/both）使 β_s/γ_s 可辨识 → full 12-pair rank140/nullity3；N1Method `obs_by_state` 初始化；GP 核矩阵维度；结果 JSON 去除 pilot 实测时间（改由 timing 文件承载） |
| ~10:40 | 两跑 `generator_n1_v0_2.json` 逐字节一致（`045DEE05…`；wall 0.5/0.4 s）；docs 更新最终 ident/pilot 数字 |
| ~10:44 | report/record/usage 完成；标 completed + send_message |

## 2. 实现与披露

1. **设计算术修正（已披露）**：v0.1 的 identifiability 使用 full-h 参数化导致观测被 h 饱和（不可辨）；v0.2 采用 **2 活跃基 h** 与显式 Jacobian；紧凑 6-pair 设计 nullity 12（3 加性参数 gauge + 9 结构冗余），执行宇宙 full 12-pair 设计 **rank 140/nullity 3=加性 gauge**。transition 观测块需 4 条件才能分离 β_s/γ_s（否则 4 个 transition 参数不可辨），已修。
2. **G1 修正**：v0.1 的 `.05023` 来自 200k MC 抽样却标 n_rep=200，且 >门；v0.2 预注册 n_mc=20000 + MC 容差 + Wilson 上界规则，实测 .0488/.0519 PASS；`chosen_amplitudes_meet_gates` 由实测决定。
3. **真实 pilot**：实现 generator + 7 方法（M/B1–B6）真实更新计算；pilot n_units=20/R=2/T=6；仅计时+等价审计，**不比较任何方法效果指标**；B2 等价审计通过；pilot 时间为真实实现（非 stub），投影 main≈12.7 s。
4. **V4**：只冻结规则（模型/held-out/SE/n_rep/seed/判定），执行在 N1 校准期；本任务不运行 V4。
5. **确定性**：结果 JSON 不含 pilot 实测时间（telemetry 在 timing 文件）；两跑逐字节一致；JSON 键排序/无时间戳；文档 SHA 写入 JSON。
6. **边界**：机制账 only；无 O'Neil 响应；无 A/B 资源；0 wells；不晋升代码；不改旧判定；未运行效果。

## 3. 关键结果（与 report 一致）

- n_units=300（单一值）；n_eff=136.36；MDE80=.04798≤.05；n_req 278≤300。
- G1 实测 point .0488（976/20000）、Wilson upper .0519、mc_tol .00308 → PASS；G2 powers 1.000/1.000/1.000 → PASS；`chosen_amplitudes_meet_gates=true` 由实测决定。
- Gauge/Jacobian：compact 107/312/rank95/nullity12；full 143/600/rank140/nullity3（=加性 gauge）；函数空间冗余 129（compact）/255（full）。
- V4 规则冻结（n_rep=200、seed=20261061、ΔELPD≥2SE）。
- 真实 pilot：per-rep .0282 s、投影 main 12.7 s、内存 .038 GB；B2 审计 PASS；caps 1800 s/2 h/8 GB。

## 4. 产物与哈希

| 文件 | SHA256 |
|---|---|
| `PROBLEM_N1_v0_2.md` | `C66FD8F43BBD54F26C60DBDC35A94285E3B882B7ABC7ACE8D052B270259D81D6` |
| `DESIGN_N1_v0_2.md` | `1B179AB9AE44143C54C6FBC80A54F538DED43D594F855DCDD7EF516FED69BEE3` |
| `generator_n1_v0_2.py` | `F1EFD8D8C749AAB5EB36A5E5A99B2F9BF76091F3B3988B0BD39843AF7CE1864A` |
| `generator_n1_v0_2.json` | `045DEE0575C7AC2DCCCDCDEE40FD018156D6F983FE54C2EC7B757C754CA9CFBE` |
| `timing_n1_pilot_v0_2.json` | telemetry（末次 `7F57BB1D…`） |
| report/record/usage | 见 `usage_N1_design_v0_2.json` |
| v0.1 只读引用 | PROBLEM_N1 `23F4668A…`、DESIGN_N1 `8FAAC491…`、generator_n1.py `F509708E…`、generator_n1.json `21BA30AA…` |

## 5. 缺口与下一步

- **未运行 N1 效果**（设计/算术/真实 pilot 计时 only）；N1 效果执行须另立执行预注册 + 独立挑战 + Lead 批准。
- V4 为规则冻结，尚未执行（N1 校准期执行）。
- 机制账 only；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；不恢复停止实验；不改旧判定。
