# record_m3_s3b_run —— R204-M3-S3b 候选 learner 比较执行记录

2026-10-28 · 角色：独立实现者（endpoint-auditor）。
**任务：R204-M3-S3B-EXEC（机制账、compute-only、0 wells；不报真实效果）。** 只写 `research/2026-10-28-m3-s3b-run/` 与 tmp/；未改 prereg/M3 Stage1/2/3/M1/M2/N1/A-B-D/旧门槛/旧判定/代码；未执行真实数据/湿实验。

## 0. 时间线

| 时间（Asia/Shanghai） | 事件 |
|---|---|
| — | 读 task-210、Lead DECISION、v0.2 PROBLEM/DESIGN/headroom/schema、Stage3/C218、C220、C208 |
| — | 新建 `2026-10-28-m3-s3b-run/`；先写 `schema_m3_s3b_run.json`（链/环境/learner/六比较/201 seeds/caps） |
| — | 实现 `run_m3_s3b.py`：高 regret 环境、真实 ε NLL/L-BFGS、standard analytic DR、六比较/Holm、headroom、DR 恒等、两跑 |
| — | 执行：headroom .126783≥.10；DR gap0；六比较 D 全 0 → 等价审计命中 → `no_increment`；两跑 result `FAF440F6…` 一致 |
| — | 写 report/record/usage |

## 1. 链/环境/合同

- v0.2 7 文件 + Lead 决定 SHA match；chain.pass=True；无 chain_mismatch。
- H=3/A=3/Y binary；p=[.3,.4,.3]；μ/b Stage2；m_wrong=.5；C_H=20；b_min=1e-6；π2' 对角 .82/非对角 .09；w 冻结；H=π2/w；H_max=18.917777≤20。
- 201 seeds：env 20262200；headroom 20262201–20；feedback 20262221–40；eval 20262241–60；arms 20262261–2400（7×20=140）；未用 181 口径。
- candidate：per-cell weighted Bernoulli NLL、offset logit(m_hat)、weights H、L-BFGS、score<1e-6、收敛；standard：same m analytic DR/TMLE 无 ε；未用禁用的伪变换/缩放/λ/类名。
- secondary：P_empirical_mean/P_importance_weighting/P_full_history_retrain/P_DR_targeting/P_value_aware。

## 2. 执行结果

- **DR 恒等**：gap **0.0**<1e-10；H_max 18.917777≤20；无 clipping。
- **headroom**：P_empirical_mean/P_standard **.126783** CI [.083972,.169594]；均≥.10；未触发 unreachable_gate；未降 δ/换 seed/环境。
- **pilot**：wall .12628 s/CPU .125 s/mem .07843 GB；**main** wall .12483 s/CPU .25 s/mem .07855 GB；caps PASS。
- **六比较**：D 全 **0.000000**；Holm 1.0；primary 不通过 → **no_increment**；candidate raw .129333=standard raw .129333。
- **等价审计**：candidate 与 standard/各基线策略逐点相同 → equivalence；停止增量主张；未从实现差异制造成功。
- **两跑** result `FAF440F6…`；replicates CSV `FB420C4E…`；diagnostics `619CC5E0…`；timing 单独；JSON 无 telemetry。
- **verdict no_increment**；failure no_increment；旧 Stage3/C220/C208 不变。

## 3. 产出

| 文件 | 说明 |
|---|---|
| `run_m3_s3b.py` | S3b 实现 |
| `m3_s3b_result.json` | 两跑一致结果（无 telemetry） |
| `m3_s3b_replicates.csv` | 20 reps×7 planners raw/D |
| `m3_s3b_diagnostics.json` | 链/DR/headroom/比较 |
| `schema_m3_s3b_run.json` | schema/失败模板（先写） |
| `timing_m3_s3b_run.json` | pilot/main canonical telemetry |
| `report_m3_s3b_run.md` | 报告 |
| `record_m3_s3b_run.md` | 本记录 |
| `usage_m3_s3b_run.json` | 命令/SHA/attestation，最后写出 |

## 4. 边界

- 旧 Stage3 `no_increment` 冻结保留；C220 解释不成立；S3b 新预注册、非重跑；C208 一步投影仍撤；旧判定/阈值/输出不变。
- 仅合成机制账；不执行真实数据/湿实验；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；M3 不与 M1/M2 混同；N1 不作证据；data readiness open；用户 public-only。
