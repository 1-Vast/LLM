# report_m1_s2c_run —— R204-M1-S2c 候选规划比较执行报告（机制账；不报真实效果）

2026-10-28 · 角色：独立实现者（endpoint-auditor）。依据：Lead `DECISION_R204_M1_S2C_EXEC.md`；v0.2 预注册；H1b/C222；C216/C217；C208。
**状态：S2c 合成规划比较执行一次完成；机制账 only；compute-only；0 wells；未执行真实数据/湿实验；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定。**

## 0. 判定（一屏）

- **verdict = `planning_comparison_pass`**；`failure_category=None`。
- **执行时 headroom**：full **.220878** CI [.218982,.222774]；constrained **.254295** CI [.252584,.256006]；均≥**.10（2δ）**，**unreachable_gate 未触发**；未降 δ/未换 seed/环境。
- **primary**（candidate vs P_empirical_mean）：mean ΔR **−.055231**、95% CI **[−.068569,−.041892]**（upper<0）、**Holm p=4.826e-16**<.05、mean≤−δ(.05) → **PASS**。
- **pilot 20 reps**：wall **347.687 s**、CPU **712.156 s**、memory **0.67076 GB**；caps 1800s/2h/8GB/0 wells PASS。
- **main 20 reps**：wall **326.841 s**、CPU process cumulative **1400.953 s**、memory **0.67147 GB**；caps PASS。
- 两跑 result JSON 逐字节 **`4977B74E…15A27B36`**；replicates/diagnostics 一致；timing 单独；JSON 无 telemetry。
- **旧 C216/C217/H1b/C208 状态全部不变**；H1b 仅密度；一步投影仍撤；未改旧文件。

## 1. 链/环境/合同

- v0.2 链 7 文件 + Lead 决定全部 SHA 匹配；`chain.pass=True`；无 chain_mismatch。
- Pθ 同 H1b：c .5²/M .1²/d .1²；σ=.1+.4sigmoid(dᵀx)；box[-2,2]^4；K=3/[.5,.3,.2]；param/train/eval seeds 20261301/02/03。
- X~N(0,I_d)，主 d=64（次 d=16）；A=4；r=wᵀy−λ||y||²（w=[.4,.3,.2,.1]、λ=.2）、τ=1；π0 full/constrained；S=4096/动作；known-truth 解析独立。
- 数据 seed **20261921**；eval **20261922**；cells **20261931–54**；headroom seeds **20261901–20**；两跑同 seeds。

## 2. 执行时 headroom（2δ 门）

- baseline = P_empirical_mean（4,096 samples/legal action，x-independent）；独立 eval X=4096；known truth。
- full **.22087767** CI [.21898153,.22277381]；constrained **.25429506** CI [.25258376,.25600636]。
- 均≥**.10**；**executable**；未重设环境；未用候选结果反选 headroom；未触发 `design_invalid: unreachable_gate`。

## 3. 六比较（D=regret_cand−regret_base；D<0 改善；δ=.05；Holm family=6）

| baseline | mean D | 95% CI | raw base | Holm p | 判定 |
|---|---:|---|---:|---:|---|
| **P_empirical_mean（primary）** | **−.055231** | [−.068569,−.041892] | .245348 | **4.83e-16** | **PASS** |
| P_max_entropy | −.121548 | [−.134887,−.108210] | .311665 | 4.77e-71 | 改善 |
| P_conditional_density_MC | .000000 | [0,0] | .190117 | 1.0 | 同候选（D=0） |
| P_constrained_SB | −.156064 | [−.169402,−.142725] | .346181 | 5.50e-116 | 改善 |
| P_random | −.156421 | [−.169759,−.143082] | .346538 | 1.98e-116 | 改善 |
| P_softmax_expected_reward | −.102394 | [−.115732,−.089055] | .292511 | 5.49e-51 | 改善 |

- candidate raw mean regret **.190117**；P_empirical_mean raw **.245348**；primary D **−.055231**。
- 6 比较统一 Holm；primary 成功门 **mean≤−.05 ∧ CI upper<0 ∧ Holm p<.05** 满足。
- 仅用同评价/配对；raw regret 与 D 分开保存；CI 按 independent replicate R=20；**不用规划 MDE 当已证功效**。
- secondary d=16 仅 **4 reps**（candidate mean .02904），**not powered/secondary**，不用于 primary 判定。

## 4. 等价审计

- candidate 与 **P_empirical_mean** 逐点动作 **不等价**；与 **P_max_entropy** 逐点动作 **不等价**。
- P_conditional_density_MC 与 candidate 共用 C-MDN，D=0；**属同一模型规划，不称独立改善**。
- 未从实现差异制造增量；标准方法等预算复制/超过的等价判定保持；本次 primary 超过 empirical-mean baseline。

## 5. G/失败/预算/两跑

- **失败类别 11**已写死；本轮 `failure_category=None`，**verdict planning_comparison_pass**。
- caps 1800s/2h/8GB/0 wells PASS；pilot 20 reps 实测；main R=20；未改 seeds/grid/S；未降 δ。
- 两跑 result JSON 逐字节 **`4977B74E68C6189687F7D78AFB78C7A2D2EE0F5420B39DDE79C361CD15A27B36`**；replicates CSV **`E9C3D012…`**；diagnostics **`83588098…`**；timing 单独；JSON 无 telemetry。
- 未输出真实 effect/decision utility/regret 之外的方法比较；不称 M1 增量/药理/真实决策/迁移/机制/新颖性。

## 6. 产物 SHA

| 文件 | SHA256 |
|---|---|
| `run_m1_s2c.py` | 见 usage |
| `m1_s2c_result.json`（两跑一致） | `4977B74E68C6189687F7D78AFB78C7A2D2EE0F5420B39DDE79C361CD15A27B36` |
| `m1_s2c_replicates.csv` | `E9C3D01298914FF7D23D3500A5C554B405D703B051A7CFD4F35A791DAFE833F2` |
| `m1_s2c_diagnostics.json` | `835880985F6260A69BB3D15058C9CDBA5BA95AC260D4EED63711B709CD65A1FC` |
| `schema_m1_s2c_run.json` | 见 usage |
| `timing_m1_s2c_run.json` | 见 usage；result SHA `4977B74E…` |
| report/record/usage | 见各文件 |

## 7. 旧状态/边界

- 旧 C216 旧 H1 **0/16 FAIL、design_invalid: projection** 不变；C217 归因不变；H1b **16/16 仅密度可分辨，不是旧 H1 通过**；一步投影仍撤（C208）。未改旧文件/旧容差/旧判定。
- 本 S2c 仅合成 known-truth 规划比较；**不是真实数据/药理/真实决策/迁移/机制/新颖性证据**；机制账 only；0 wells；data readiness open（C203/C205/C210/C214）；用户 public-only。
- 不晋升代码；M1 不与 M2/M3 混同；N1 不作证据；不恢复停止实验。
