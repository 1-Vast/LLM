# report_m3_s3b_run —— R204-M3-S3b 候选 learner 比较执行报告（机制账；不报真实效果）

2026-10-28 · 角色：独立实现者（endpoint-auditor）。依据：Lead `DECISION_R204_M3_S3B_EXEC.md`；v0.2 预注册；Stage3/C218；C220；C208。
**状态：S3b 执行一次完成；机制账 only；compute-only；0 wells；未执行真实数据/湿实验；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定。**

## 0. 判定（一屏）

- **verdict = `no_increment`；failure_category = `no_increment`**。
- **候选与 standard 及各基线策略逐点相同**（六比较 D 全为 0）；等价审计命中；按预注册 **停止增量主张/`no_increment`**，不把 S3b 写成 Stage3 修正/通过。
- **headroom 执行核对**：P_empirical_mean **.126783** CI [.083972,.169594]；P_standard_DR_TMLE **.126783** 同 CI；均≥**.10（2δ）**；未触发 `unreachable_gate`；未降 δ/换 seed/环境。
- **DR 恒等预检**：gap **0.0**<1e-10 PASS；H_max **18.917777**≤C_H=20，无 clipping。
- **pilot 20 reps**：wall **0.12628 s**、CPU **0.125 s**、memory **0.07843 GB**；caps PASS。
- **main 20 reps**：wall **0.12483 s**、CPU **0.25 s**、memory **0.07855 GB**；caps PASS。
- 两跑 result JSON 逐字节 **`FAF440F6…A7DFE11`**；replicates/diagnostics 一致；timing 单独；JSON 无 telemetry。
- 旧 Stage3 `no_increment`、C220 解释、C208 一步投影撤全部不变；未改旧文件。

## 1. 链/环境/合同

- v0.2 链 7 文件 + Lead 决定全部 SHA 匹配；`chain.pass=True`；无 chain_mismatch。
- H=3/A=3/Y binary；p=[.3,.4,.3]；μ/b Stage2；m_wrong=.5；C_H=20；b_min=1e-6；π2' 对角 .82/非对角 .09；w 按 headroom 冻结；H=π2/w；**H_max=18.917777≤20，无 clipping**。
- **201 exec seeds**：env 20262200、headroom 20262201–20、feedback 20262221–40、eval 20262241–60、arms 20262261–2400（7×20=140）；未用 181 口径；未改 seed。
- **candidate**：per-cell weighted Bernoulli NLL、offset logit(m_hat)、weights H、**L-BFGS**、score 残差<1e-6、收敛；**standard**：same m 的 analytic DR/TMLE，无 ε。未用 0.5+0.5*score/sigmoid(2*score)/无 NLL 变换/缩放/λ/类名。
- secondary：P_empirical_mean/P_importance_weighting/P_full_history_retrain/P_DR_targeting/P_value_aware。

## 2. 六比较（D=regret_cand−regret_base；δ=.05；Holm family=6；单侧下尾）

| baseline | mean D | 95% CI | raw base | Holm p | 判定 |
|---|---:|---|---:|---:|---|
| **P_standard_DR_TMLE（primary）** | **0.000000** | [0,0] | .129333 | 1.0 | 不通过 |
| P_empirical_mean | 0.000000 | [0,0] | .129333 | 1.0 | 等价 |
| P_importance_weighting | 0.000000 | [0,0] | .129333 | 1.0 | 等价 |
| P_full_history_retrain | 0.000000 | [0,0] | .129333 | 1.0 | 等价 |
| P_DR_targeting | 0.000000 | [0,0] | .129333 | 1.0 | 等价 |
| P_value_aware | 0.000000 | [0,0] | .129333 | 1.0 | 等价 |

- candidate raw regret **.129333**；standard raw **.129333**；所有 D=0。
- primary 成功门 mean≤−.05 ∧ CI upper<0 ∧ Holm<.05 **不满足** → **no_increment**；不是把失败写成通过。
- **等价审计**：candidate 与 standard/各基线策略逐点相同，判 **equivalence/no_increment**；停止增量主张；未用实现差异制造成功。
- raw 与 paired D 分存；CI 按 R=20 cluster=replicate，t df=19；未用 MDE 当已证功效。

## 3. 两跑/预算/产出

- pilot（20 reps）wall .12628 s/CPU .125 s/mem .07843 GB；main wall .12483 s/CPU .25 s/mem .07855 GB；caps 1800/2h/8GB/0 wells PASS。
- 两跑 result JSON 逐字节 **`FAF440F6C5789E96745B6782965C884AC48FCAF3DA43600F76BAC00A6A7DFE11`**；replicates CSV **`FB420C4E…`**；diagnostics **`619CC5E0…`**；timing 单独；JSON 无 telemetry。
- 未输出真实数据/效果/真实决策/药理/迁移/机制/新颖性。

## 4. 产物 SHA

| 文件 | SHA256 |
|---|---|
| `run_m3_s3b.py` | 见 usage |
| `m3_s3b_result.json`（两跑一致） | `FAF440F6C5789E96745B6782965C884AC48FCAF3DA43600F76BAC00A6A7DFE11` |
| `m3_s3b_replicates.csv` | `FB420C4E801168893314773FE6FB165CF5F1C69C4B2DE3909E48B0D920600B4E` |
| `m3_s3b_diagnostics.json` | `619CC5E0757E54B85BF2C0784F93E1194FC31E41C72A78B28D91A78B7CA5CD0D` |
| `schema_m3_s3b_run.json` | 见 usage |
| `timing_m3_s3b_run.json` | 见 usage；result SHA `FAF440F6…` |
| report/record/usage | 见各文件 |

## 5. 旧状态/边界

- 旧 Stage3 **`no_increment` 冻结保留**；C220 原“合格 M3/TMLE 比较”解释不成立；S3b 是新预注册、非重跑旧 Stage3；C208 一步投影仍撤；旧判定/阈值/输出不变。
- 仅合成机制账；不是真实数据/药理/真实决策/迁移/机制/新颖性证据；compute-only、0 wells；不晋升代码；M3 不与 M1/M2 混同；N1 不作证据；data readiness open；用户 public-only。
