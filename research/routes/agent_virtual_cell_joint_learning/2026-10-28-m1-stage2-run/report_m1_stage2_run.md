# report_m1_stage2_run —— R204-M1 Stage2 合成诊断执行报告（机制账；**不报效果**）

2026-10-28 · 角色：ON1/ON2/ON2.2/ON3 执行者（非提案者）。依据 Lead `DECISION_R204_M1_S2_EXEC.md`（批准 M1 Stage2 合成诊断一次）与冻结执行预注册（PROBLEM `F7ED4520…`、DESIGN `503618F4…`、exec_plan.py `CFF1C734…`、json `3DC88FEF…`、schema `181A77E3…`）。**仅机制账、compute-only、0 new wells；未执行 Stage3/真实数据/湿实验；未报告效果/decision utility/regret/top-k/方法比较；不称 M1 增量、不称药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定/门槛；N1 不作 M1 Stage2 证据；data readiness open（C203/C205/C210）。**

## 0. 判定（一屏）

- **Stage2 合成诊断执行完成；verdict = `qualification_pass`；failure_category = `none`。**
- 执行前链核验 **12/12 PASS**；Stage1 状态 PASS（`no_effect_results`、B2 max-ent 等价已撤、无一步投影增量主张）；执行 seeds 与禁用区间 overlap=[]、unique=true。
- 实测 pilot（最终实现，2 reps，含 H1 16 个 C-MDN + Q_g GL64/dim + H3 GL128/dim）：wall **116.36 s**（rep1 129.90/rep2 102.82）、main run **98.33 s**、CPU **322.66 s**、内存 **0.056 GB**；caps **1800 s/2 h/8 GB/0 wells** PASS（未用 planning/单测数字代替）。
- **H1 16/16 cell 全 PASS**（TV ≤ 冻结容差）；**H2 5/5 ε 全收敛**（max marginal error ≤1e-8）；**H3 TV 0.01244 ≤.05**（仅 small-case 诊断，非高维 oracle）。
- **G1–G6 全 PASS**；G5 两跑结果 JSON/诊断/CSV 逐字节一致 SHA **`90DE7498C75710CC944A8617D3812F08F728EDC5C97734289533021177422C57`**。
- **未输出效果/增益/方法比较**；B1–B5 仅规格登记，未执行比较。

## 1. 执行前链/实现范围

- 冻结链 12 文件 SHA 核验 PASS（M1 Stage2 v0.2 八件 + Lead 接受决定 + Stage1 json/report/decision）；执行时重核；无 mismatch。
- 冻结 Pθ：X~N(0,I_64)、A=4、Y∈[-2,2]^4；唯一 3 分量截断 GMM（权重 [.5,.3,.2]）、对角协方差、条件异方差、**无 Student-t**；train 4096/eval 2048；param/train/eval seeds **20261301/02/03**。
- target Q：r=wᵀy−λ||y||²、w=[.4,.3,.2,.1]、λ=.2、r∈[−5.2,.375]；τ∈{.5,1}；tensor Gauss-Legendre **64 nodes/dim**；target 样本不作标签；Doob 不可执行。
- C-MDN：K=3 logits + mean(4) + diag log-scale(4)，hidden 128/2 ReLU，NLL/Adam lr=1e-3/wd=1e-5/batch=256/epochs=200；采样 4096/action；**不称一步投影**。
- **实现披露**：Pθ 的 c/M/d 抽样尺度在冻结链中只给形状、未给分布；本执行冻结为 `c~N(0,0.05²)`, `M~N(0,0.005²)`, `d~N(0,0.05²)`（param_seed 20261301），未改 H1 容差/顺序/seed；C-MDN 训练中使用 y 标准化与梯度裁剪（≤10）作为数值稳定实现，不改网络结构/NLL/优化器/epochs；已记录于 record。未据结果放宽容差/改阈值。
- B1–B5 仅规格：random MPC、max-entropy、conditional density+MC、constrained Schrödinger bridge、same-info Diffusion Forcing；**不执行比较**。

## 2. H1 近似随 d/N（256-bin TV）

| d \ N | 512 | 1024 | 2048 | 4096 |
|---|---:|---:|---:|---:|
| 8 | .0806 (<.12) | .0654 (<.10) | .0654 (<.08) | .0552 (<.07) |
| 16 | .1089 (<.14) | .1055 (<.11) | .0742 (<.09) | .0679 (<.08) |
| 32 | .1309 (<.16) | .1035 (<.13) | .0723 (<.11) | .0938 (<.10) |
| 64 | .1309 (<.18) | .0596 (<.15) | .0698 (<.13) | .0703 (<.12) |

- 16/16 PASS；顺序固定 d=8→64、N=512→4096；全部 TV≤冻结容差；无 `design_invalid: projection`。
- H1 仅近似诊断；不是效果/决策收益。

## 3. H2 Sinkhorn / constrained SB

| ε | iterations | max marginal error | converged |
|---:|---:|---:|---|
| .1 | 26 | 6.1e-09 | true |
| .25 | 11 | 2.9e-09 | true |
| .5 | 7 | 1.3e-09 | true |
| 1.0 | 5 | 7e-10 | true |
| 2.0 | 4 | 0.0 | true |

- log-domain Sinkhorn，maxiter 2000、marginal tol 1e-8；**至少一 ε 收敛**满足且实际 5/5 收敛；action marginal π0、target y-marginal Q_g；非另一错误目标条件化。
- H2 仅规划/传输诊断；不作效果。

## 4. H3 small-case oracle 诊断

- small-case d_X=2/A=2/Y=2；oracle 用 tensor GL **128 nodes/dim** 精确 target Q/action；候选 C-MDN target-action 分布 vs oracle，256 eval x 的 mean TV = **0.0124368294 ≤ .05** → PASS。
- **H3 仅 small-case，不是高维 exact oracle**；高维误差由 H1 判；H3 不作效果/方法比较。

## 5. G1–G6

| 门 | 结果 |
|---|---|
| G1 条件药效保持 | PASS（target 样本不作标签；Pθ 不被 target 更新；可执行 Rπ 保持 P(y|a)=Pθ，结构检查） |
| G2 支持/程序 | PASS（4 动作全支持；π0 严格正；无 unsupported program） |
| G3 近似/投影 | PASS（H1 16/16、H2 5/5、H3 .01244≤.05） |
| G4 无泄漏 | PASS（train/eval seeds 独立；target 永不标签；评估独立于拟合/策略选择） |
| G5 两跑 | PASS（两跑结果 JSON/诊断/CSV 逐字节一致 SHA `90DE7498…`；telemetry 单独） |
| G6 schema/预算 | PASS（schema 先写；caps 1800s/2h/8GB/0 wells；pilot/main 实测通过） |

- 失败类别全集：`design_invalid: projection|support|calibration|leakage|compute_budget_exceeded|rename_maxent|two_run_mismatch|chain_mismatch`、`unreachable_gate`、`precision_insufficient`、`no_increment`、`inconclusive`；本次失败类别 none。
- B2 等价/一步投影已在 Stage1 撤；**本报告不写 M1 增量**。

## 6. 两跑/预算/边界

- 两跑（同 seeds、独立进程）：`m1_stage2.json` SHA **`90DE7498C75710CC944A8617D3812F08F728EDC5C97734289533021177422C57`**；诊断 JSON、checks CSV 亦逐字节一致。
- telemetry：pilot wall **116.36 s**（2 reps，含 H1 16 C-MDN/Qg GL64/H3 GL128）、main run **98.33 s**、CPU **322.66 s**、mem **0.056 GB**；caps PASS；结果 JSON 无 telemetry。
- **边界**：机制账 only；合成 compute-only、0 new wells；不执行 Stage3/真实数据/湿实验；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定/门槛；M1 不与 M2/M3 混同；N1 不作证据；data readiness open（C203/C205/C210）。
- **Stage3 条件（仅建议）**：Stage2 诊断通过**只表示合成近似/约束/规划诊断合格**，不等于 Stage3 可执行；真实数据当前 `data_unavailable`（C203/C205/C210）；Stage3 须另立执行预注册+独立挑战+Lead 批准；本任务不批准/不执行。

## 7. 产物 SHA

| 文件 | SHA256 |
|---|---|
| `run_m1_stage2.py` | `9ED4042CD6E8B613A006B2AA7BC2073272C9076E4FB3EA6BEB1022F4A9650613` |
| `m1_stage2.json`（两跑一致） | `90DE7498C75710CC944A8617D3812F08F728EDC5C97734289533021177422C57` |
| `m1_stage2_diagnostics.json` | `B2F39E915EA6CC819272F2526A3ED9D6DB5B0BDC84D6020C8290EEE207AF4CA5` |
| `m1_stage2_checks.csv` | `D0341E1E9724F0D740D78651AE092652B8784BF9049D5CDD46749DBE7C001AC0` |
| `schema_m1_stage2_run.json` | `C1EC42FAB31C95CA1455241E818C83BAF2A9BDEA0B5919E3AED1971F05E4A459` |
| `timing_m1_stage2_run.json` | `D4B2A028AA9B0B5BB991C7F12C76DC22A8461E5F13BCAB66E803889A1AE8F18E` |
| `report_m1_stage2_run.md` / `record_m1_stage2_run.md` / `usage_m1_stage2_run.json` | 见各文件 |

## 8. 结论边界（写死）

仅合成机制证据；H1–H3 是近似/校准/规划诊断，不是效果；H3 仅 small-case，非高维 oracle；B1–B5 仅规格未比较；不称 M1 增量/药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定；Stage3/真实数据/湿实验未执行。
