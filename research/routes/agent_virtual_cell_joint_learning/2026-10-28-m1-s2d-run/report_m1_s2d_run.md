# report_m1_s2d_run —— R204-M1-S2d 错配/背景漂移规划比较执行报告（机制账；不报真实效果）

2026-10-28 · 角色：独立实现者（endpoint-auditor）。依据：Lead `DECISION_R204_M1_S2D_EXEC.md`；v0.3 预注册；S2c/C223；H1b；C216/C217；C208。
**状态：S2d 合成错配/背景漂移规划比较执行一次完成；机制账 only；compute-only；0 wells；未执行真实数据/湿实验；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定。**

## 0. 判定（一屏）

- **verdict = `planning_comparison_pass_T1`**；`failure_category=None`（主成功仅 T1）。
- 执行时 headroom：T1 **.485465**、T2 **.564308**、T3 **.396520**，均≥**.10（2δ）**；未触发 `unreachable_gate`；未降 δ/未换 seed/环境。
- **T1 primary**（candidate vs P_empirical_mean_source）：mean D **−.147824**、95% CI **[−.163759,−.131890]**、Holm p **2.11e-73**、mean≤−δ(.05) → **PASS**。
- **T2/T3 不合并、不 pool；各自 target 内 Holm**；T2 source D −.006979（CI 跨 0）、adapted D −.015901（Holm .77，不显著）；T3 source D −.084667（Holm 9.78e-18）但仅 secondary；**主成功仍仅 T1**。
- **pilot 60 cells**：wall **419.491 s**、CPU **971.531 s**、memory **1.08057 GB**；caps 1800s/2h/8GB/0 wells PASS。
- **main 60 cells**：wall **411.332 s**、CPU process cumulative **1950.0 s**、memory **1.08124 GB**；caps PASS。
- 两跑 result JSON 逐字节 **`20DD8347…8CED83`**；replicates/diagnostics 一致；timing 单独；JSON 无 telemetry。
- 旧 S2c/C216/C217/H1b/C208 状态不变；目标数据未用于候选训练/调参；未改旧文件。

## 1. 链/环境/合同

- v0.3 链 7 文件 + Lead 决定全部 SHA 匹配；`chain.pass=True`；无 chain_mismatch。
- 源 Pθ 同 H1b/S2c；T1 c'~N(0,1.0²) seed 20262001；T2 M'~N(0,.2²) seed 20262002；T3 X'~N(0,1.5²I)。
- X d=64、A=4、r=wᵀy−λ||y||²（w=[.4,.3,.2,.1]、λ=.2）、π0 full；S=4096/动作；known-truth 目标解析。
- **候选仅源 Pθ 训练**；目标数据只评价 + adapted baseline（512/动作标定，3584 source+512 target/动作）；未用目标数据训练/调参。
- 数据 seed 20262031；eval 20262032；headroom 20262011–30；T1 cells 20262041–60、T2 20262061–80、T3 20262141–60；**20262100 未用**。
- **T2 valid_eval_rows=4093 冻结**（headroom/目标数据行数；候选规划 eval 子sample 64，见 §4 说明）。

## 2. 执行时 headroom（2δ 门）

| target | mean | 95% CI | rows | 判定 |
|---|---:|---|---:|---|
| T1 | .485465 | [.485465,.485466] | 4096 | ≥.10 PASS |
| T2 | .564308 | [.564308,.564308] | **4093** | ≥.10 PASS |
| T3 | .396520 | [.396520,.396520] | 4096 | ≥.10 PASS |

- headroom 是执行时最终实现/冻结 seeds 重算的 P_empirical_mean_source baseline；CI 退化为单点（baseline 选择动作固定），仍> .10；未触发 unreachable_gate；未降 δ/换 seed/环境。

## 3. T1 六比较（primary；T1 内 Holm family=6）

| baseline | mean D | 95% CI | raw base | Holm p |
|---|---:|---|---:|---:|
| **P_empirical_mean_source（primary）** | **−.147824** | [−.163759,−.131890] | .632855 | **2.11e-73** |
| P_target_adapted_empirical_mean | +.018718 | [.002784,.034653] | .466313 | 1.0 |
| P_max_entropy | +.109666 | [.087019,.132313] | .375365 | 1.0 |
| P_conditional_density_MC | .000000 | [0,0] | .485031 | 1.0 |
| P_random | +.112661 | [.089734,.135589] | .372370 | 1.0 |
| P_softmax_expected_reward | +.079249 | [.056723,.101774] | .405782 | 1.0 |

- **primary PASS**；raw candidate .485031，source baseline .632855。
- T1 secondary 中 max-entropy/random/softmax/adapted 的 D **为正**（candidate 不如这些 baseline）；**如实报告**，不写成全面优于所有 baseline。
- P_conditional_density_MC 与 candidate 共用 C-MDN（D=0）；不称独立改善。

## 4. T2/T3（各 target 内 Holm；不合并、不 pool）

### T2（M' shift；valid_eval_rows=4093）
- source primary D **−.006979** CI [−.034448,.020491] Holm 1.0；adapted D **−.015901** CI [−.043371,.011569] Holm .77；maxent/random/softmax/conditional 未显著；**T2 主比较不通过**。
- 仅 secondary/诊断；不因 target 次级豁免 CI；不合并 T1。

### T3（X' scale 1.5）
- source D **−.084667** CI [−.103737,−.065597] Holm 9.78e-18；maxent −.086808；random −.083223；softmax −.093003；adapted −.035911（Holm 2.23e-4）；conditional 0。
- T3 内多个 secondary 显著，但 **primary 主成功仅 T1**；不把 T3 写成真实数据/迁移/机制证据；不 pool。

## 5. 等价审计

- candidate 与 **P_empirical_mean_source** 逐点动作**不等价**；与 **P_max_entropy** **不等价**；与 **P_conditional_density_MC** 共用 C-MDN（D=0，非独立改善）。
- 未用目标数据训练/调参制造差异；未从实现差异制造增量。
- T1 secondary 中 candidate 不如 max-entropy/random/softmax/adapted，已如实披露；primary 仅对 P_empirical_mean_source 通过。

## 6. 两跑/预算/产出

- 两跑 result JSON 逐字节 **`20DD834738166FE1429AAAEA2F326303C4D777257DB026DFA28D425CB58CED83`**；replicates CSV **`33D6E75D…`**；diagnostics **`E87059AC…`**；timing 单独；JSON 无 telemetry。
- pilot/main 实测 caps PASS；未减 R/60 cells/S=4096；未改 seeds/grid。
- **未输出**真实数据/效果/药理/真实决策/迁移/机制/新颖性；机制账 only。

## 7. 产物 SHA

| 文件 | SHA256 |
|---|---|
| `run_m1_s2d.py` | 见 usage |
| `m1_s2d_result.json`（两跑一致） | `20DD834738166FE1429AAAEA2F326303C4D777257DB026DFA28D425CB58CED83` |
| `m1_s2d_replicates.csv` | `33D6E75DA363F7125DE5EBE8B64D9325BC8E51B152815B1C503A3D6DD09CCDF1` |
| `m1_s2d_diagnostics.json` | `E87059AC36619143E75ECA727AE97D602FBEC573564D2EF7A49F08DBDD24F5EE` |
| `schema_m1_s2d_run.json` | 见 usage |
| `timing_m1_s2d_run.json` | 见 usage；result SHA `20DD8347…` |
| report/record/usage | 见各文件 |

## 8. 旧状态/边界

- 旧 S2c 不改；C216 旧 H1 **0/16 FAIL、design_invalid: projection** 不变；C217 归因不变；H1b **16/16 仅密度可分辨，不是旧 H1 通过**；一步投影仍撤（C208）。未改旧文件/旧容差/旧判定。
- 本 S2d 仅**合成错配/背景漂移规划比较**；不是真实数据/药理/真实决策/迁移/机制/新颖性证据；机制账 only；0 wells；data readiness open；用户 public-only。
- 不晋升代码；M1 不与 M2/M3 混同；N1 不作证据；不恢复停止实验。
