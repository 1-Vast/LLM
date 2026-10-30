# record_m3_s3b_prereg.md —— R204-M3-S3b 预注册执行记录（headroom 设计；不运行候选）

角色：独立执行设计/审计员（未参与 R197/R200/203 模型开发）· 任务 task-206（R204-M3-S3B-PREREG）· 日期 2026-10-28
只写 `research/2026-10-28-m3-s3b-prereg/` 与 `tmp/`；**未改 M3 Stage1/2/3、C216/C217/H1b/S2c、M1/M2/N1/A-B-D**；**未训练/未运行候选、未报效果、未读真实数据**；机制账 only；compute-only、0 wells。

## 0. 要求与完成对照

| 要求 | 状态 |
|---|---|
| ① 分离/纠正 | ✅ Stage3 no_increment 冻结保留；C220 解释不成立；S3b 新预注册非重跑旧配置；旧判定不变；无真实数据/药理/真实决策/迁移/机制/新颖性 |
| ② 高 regret/headroom 先于候选 | ✅ π2' 对角 .82/非对角 .09；Q/w 公式；feedback 按实际 w；H=π2/w；H_max=18.9178<20 无 clipping；**P_empirical_mean/standard DR baseline regret=.14841667 CI [.10382916,.19300417]**，均≥.10 → executable；未重设；设计期实测 |
| ③ learner 合同 | ✅ candidate 真实 logit-fluctuation ε（weighted Bernoulli NLL、offset logit m_hat、weights H=π2/w、L-BFGS、score residual<1e-6、收敛）；standard 同 m analytic DR/TMLE no ε；禁 `0.5+0.5*score`/`sigmoid(2*score)`/无 NLL 变换；H 用实际 w；DR exact gap=0.0<1e-10 |
| ④ 等价去重 | ✅ candidate vs standard/各 baseline 策略/单调/正仿射/解析覆盖→equivalence、合并、no_increment；等价类预注册；不得实现差异制造独立成功 |
| ⑤ 六比较/统计 | ✅ primary candidate vs P_standard_DR_TMLE；secondary P_empirical_mean/P_importance_weighting/P_full_history_retrain/P_DR_targeting/P_value_aware；D<0、δ=.05、Holm family=6、单侧下尾；raw/paired 分存；CI R=20 cluster；不用 MDE 当功效 |
| ⑥ 执行/seeds/caps/schema/失败 | ✅ seeds 20262200+：env 20262200/headroom 20262201–20/feedback 20262221–40/eval 20262241–60/arms 20262261+20a+r；forbidden ranges/overlap=[]/unique；两跑逐字节/telemetry 单独；caps 1800 s/2 h/8 GB/0 wells；schema 先写；13 失败 |
| ⑦ 停止 | ✅ headroom<.10→重设/冻结或 unreachable_gate；等价→no_increment；DR gap≥1e-10→design_invalid: propensity/calibration；CI 无法排除 0/−δ→inconclusive；标准方法等预算复制/超过→no_increment/撤；超 caps→compute_budget_exceeded；任何失败不改旧判定 |
| ⑧ report/record/usage+schema+headroom；标 completed+send_message | ✅ |

## 1. 时间线（Asia/Shanghai，2026-10-28）

| 时间 | 事件 |
|---|---|
| ~18:18 | 读 task-206 并 claim；读 Stage3/C218/C220、C220/C221 corrections、NEXT_EXPERIMENT、M3 Stage2/Stage3 v0.4 |
| ~18:23 | 设计高 regret 环境（π2' 对角 .82/非对角 .09）；写 `headroom_design_m3_s3b.py`（env/headroom/DR identity/learner contract/seeds/schema） |
| ~18:26 | 首跑 headroom=.14841667（P_empirical_mean/standard DR）；DR gap=0.0；修 arm seeds 20a+r 唯一性；两跑 JSON/schema 逐字节一致 |
| ~18:31 | 写 PROBLEM/DESIGN/report/record/usage；标 completed + send_message |

## 2. 实现与披露

1. **只做设计期 headroom**：高 regret 环境 p/μ/b/π2'；allocation w；actual w 反馈；P_empirical_mean/standard analytic DR baseline regret；known-truth；R=20。
2. **高 regret 结果**：P_empirical_mean **.14841667** CI [.10382916,.19300417]；standard DR **.14841667** 同 CI；均≥.10 → executable；未重设；H_max 18.9178<C_H 无 clipping。
3. **DR 恒等**：m=μ、H=π2/w，correction expectation=0，exact gap **0.0<1e-10**；H 用实际 w，不用旧 b。
4. **Learner 合同**：真实 ε 的 weighted Bernoulli NLL/offset/logit、L-BFGS、score residual<1e-6；standard 同 m、analytic DR/TMLE no ε；禁假变换；不训练候选。
5. **六比较/等价**：family=6 planned；D<0、δ=.05、Holm、单侧下尾、raw/paired、CI R=20；等价类预注册；equivalence→no_increment。
6. **seeds/两跑**：20262200+；env/headroom/feedback/eval/arms 分块；forbidden ranges→overlap=[]、unique=true；两跑同 seeds/独立进程/逐字节；telemetry 单独。
7. **确定性**：`headroom_design_m3_s3b.json`（`77F113FF…`）两跑逐字节一致；JSON 无 telemetry；wall≈0.1 s 仅 usage/报告。
8. **边界**：机制账 only；未训练/未运行候选/未读真实数据；不改旧判定；不称真实数据/药理/真实决策/迁移/机制/新颖性；不晋升代码；Stage3 no_increment 保留；M3 不与 M1/M2 混同；N1 不作证据；data readiness open（C203/C205/C210/C214）。

## 3. 关键结果

- 高 regret env：π2' 对角 .82/非对角 .09；w=[[.9873,.0079,.0048],[.0116,.9651,.0233],[.0187,.0133,.968]]；H_max=18.9178<C_H=20；support b>0/b≥1e-6/Q finite/w>0 全通过。
- headroom：P_empirical_mean **.14841667** CI [.10382916,.19300417]；standard DR **.14841667** 同；均≥.10 → executable；未重设。
- DR identity exact gap **0.0<1e-10**；m=μ、H=π2/w。
- six comparisons/Holm family=6/δ=.05/one-sided lower/raw-paired/CI R=20；equivalence audit；13 failures；stop。
- seeds 20262200+；forbidden ranges→overlap=[]、unique=true；两跑/caps 1800/7200/8GB/0 wells；schema/pilot。
- 无候选训练/无效果；本轮仅 headroom+预注册。

## 4. 产物与哈希

| 文件 | SHA256 |
|---|---|
| `PROBLEM_M3_S3B.md` | `869690F912D92DDDBE8EB8372AA16E489F36610B9B7F8638AD40F4586AB8BF5E` |
| `DESIGN_M3_S3B.md` | `79E1E10971F09461E36531A3F46B8BAF88583B4C47448DB6C7B24CB13ACC0E9B` |
| `headroom_design_m3_s3b.py` | `68EF66988ABBC3E068C1BCCA230BB09C045FCE7019465F927468FA89436C829B` |
| `headroom_design_m3_s3b.json` | `77F113FF61649A5A5978B4EE3CA23673005CF9BDAA11E7B57D6AF6CCDE72DC12` |
| `schema_m3_s3b.json` | `29747B9C5E455B5E9738393938462B43FDD52289D82E5495DC1ED2501760D317` |
| report/record/usage | 见 `usage_m3_s3b_prereg.json` |
| 只读引用（未改） | Stage3 result `60928345…`；Stage2 `36C4DF12…`；corrections `87E667AC…` |

## 5. 缺口与下一步

- **S3b 尚未执行**；本文件仅设计期 headroom+预注册，未训练/未运行候选/无效果。
- 执行前：独立挑战 + Lead 批准 + 重核环境/headroom/DR identity/learner 合同/seeds/两跑/schema/失败模板 + 最终实现 pilot 冻结；不改旧判定。
- 机制账 only；不训练/不运行候选/不报效果；不晋升代码/不改旧判定/不恢复停止实验。
