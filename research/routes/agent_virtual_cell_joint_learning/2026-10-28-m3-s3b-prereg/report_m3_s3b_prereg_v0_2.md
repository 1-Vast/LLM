# report_m3_s3b_prereg_v0_2 —— R204-M3-S3B.1 修订预注册报告（seed 201/7 arms；不运行候选）

2026-10-28。对象：R204-M3-S3b 预注册 v0.2。依据：M3-S3B-C1 挑战（revise，seed 计数 181 vs 201）；Stage3 no_increment（C218）+ C220/C221、NEXT_EXPERIMENT、M3 Stage1/C209、Stage2/C213。
**状态：预注册修订草案；仅设计期 headroom（合成、机制账）；未训练/未运行候选、未报效果、未读真实数据；compute-only、0 wells；不称真实数据/药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定；执行须另立独立挑战+Lead 批准。**

## 0. 交付物（v0.2 新文件；v0.1 保留不改）

- 问题定义：[PROBLEM_M3_S3B_v0_2.md](PROBLEM_M3_S3B_v0_2.md)（`5EAB7A51…`）
- 执行设计：[DESIGN_M3_S3B_v0_2.md](DESIGN_M3_S3B_v0_2.md)（`73245C43…`）
- headroom 设计：[headroom_design_m3_s3b_v0_2.py](headroom_design_m3_s3b_v0_2.py)（`F63135BD…`）→ [headroom_design_m3_s3b_v0_2.json](headroom_design_m3_s3b_v0_2.json)（`E7D9EC3D…`）
- schema：[schema_m3_s3b_v0_2.json](schema_m3_s3b_v0_2.json)（`CBD748B7…`）
- 记录/用量：[record_m3_s3b_prereg_v0_2.md](record_m3_s3b_prereg_v0_2.md)、[usage_m3_s3b_prereg_v0_2.json](usage_m3_s3b_prereg_v0_2.json)

## 1. 必改落实

| # | 挑战问题 | v0.2 落实 |
|---|---|---|
| ① **seed 计数 181 vs 201** | v0.1 `all_exec_seeds_count=181`；7 arms×20=140 应为 env1+headroom20+feedback20+eval20+arm140=**201** | **EXEC_SEEDS 补入 headroom 20**：env 20262200 + headroom 20262201–20 + feedback 20262221–40 + eval 20262241–60 + arms 20262261–2400（7×20）= **201**；`all_exec_seeds_count=201`；保留 7 arms/family=6；181 作废；不删 arm |
| ② **schema/JSON 可判字段** | — | 新增 **`n_arms=7`、`n_arm_seeds=140`、`n_exec_seeds=201`**；`all_exec_seeds_count` 由 blocks 程序化生成；`seed_block_counts={env:1,headroom:20,feedback:20,evaluation:20,arms:140}`；schema/report/record 同步；`unique=true`、`overlap=[]` 保持 |
| ③ 保持 | — | 分离/纠正；高 regret 环境；DR gap=0；headroom **P_empirical_mean/P_standard_DR_TMLE .14841667 CI [.10382916,.19300417]**；learner 合同；六比较/Holm6/δ=.05/单侧下尾/raw-paired/CI R=20/等价审计；seeds env20262200/headroom20262201–20/feedback20262221–40/eval20262241–60/arms20262261–2400；两跑/caps/schema/13 失败/停止/边界 |

## 2. Seed blocks / counts（关键修正）

| block | seeds | count |
|---|---|---|
| env | 20262200 | 1 |
| headroom | 20262201–20262220 | 20 |
| feedback | 20262221–20262240 | 20 |
| evaluation | 20262241–20262260 | 20 |
| arms | 20262261–20262400（20262261+20a+r；a=0..6，r=0..19） | 140 |
| **total** | — | **201** |

- `all_exec_seeds_count = len(EXEC_SEEDS) = 201`；`n_arms=7`、`n_arm_seeds=140`、`n_exec_seeds=201`；`seed_block_counts` 对账；`unique=true`、`overlap=[]`。
- 旧 181（漏 headroom 20）作废；不得同时保留 7 arms/140 seeds 与 181；不采用删 arm 方案；family=6 不变。

## 3. 高 regret/headroom（保持）

- H=3/A=3/Y binary；p=[.3,.4,.3]；μ/b Stage2；m_wrong=.5；C_H=20；b_min=1e-6；π2' 对角 .82/非对角 .09；H=π2/w；H_max=18.9178<C_H（无 clipping）；support/positivity 通过。
- 设计期 headroom（R=20 seeds 20262201–20；300 feedback；300 eval；known truth）：**P_empirical_mean .14841667 CI [.10382916,.19300417]**；**P_standard_DR_TMLE .14841667 同 CI**；均≥.10 → executable；未重设；设计期实测、不用候选结果反选；<.10→重设/冻结或 unreachable_gate；不降 δ/不换 seed/环境。
- DR identity：m=μ、H=π2/w；exact gap **0.0<1e-10**；H 用实际 w、不用旧 b。

## 4. Learner 合同/六比较/等价（保持）

- Candidate 真实 logit-fluctuation ε：per-cell weighted Bernoulli NLL（offset logit m_hat、weights H=π2/w）、L-BFGS、score residual<1e-6、收敛；standard same m analytic DR/TMLE no ε；禁 `0.5+0.5*score`/`sigmoid(2*score)`/无 NLL 变换/缩放/λ/类名。
- Family=6 planned：primary candidate vs P_standard_DR_TMLE；secondary P_empirical_mean/P_importance_weighting/P_full_history_retrain/P_DR_targeting/P_value_aware；D<0、δ=.05、Holm family=6、单侧下尾；raw/paired 分存；CI R=20 cluster=replicate t(df=19)；不用 planning MDE 当功效；等价审计→equivalence/no_increment。
- 13 失败类别、停止条件、caps 1800 s/2 h/8 GB/0 wells、pilot 冻结、schema 先写、JSON 无 telemetry；本任务不训练/不运行候选。
- 边界：机制账 only；不称真实数据/药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定；Stage3 no_increment 保留；M3 不与 M1/M2 混同；N1 不作证据；data readiness open（C203/C205/C210/C214）。

## 5. 产物 SHA/确定性

| 文件 | SHA256 |
|---|---|
| `PROBLEM_M3_S3B_v0_2.md` | `5EAB7A5188438B6875F77C5866FF3821A69B1992AE471E6F33FC0F6F9E38AEFB` |
| `DESIGN_M3_S3B_v0_2.md` | `73245C43F6E21CABD88E38B7371DB8374F76E0F4DF9E74F1F89B294C859C84B5` |
| `headroom_design_m3_s3b_v0_2.py` | `F63135BD90D852657F13473A9AAF38877E310D765E1C0BF785D0FAF848BA5327` |
| `headroom_design_m3_s3b_v0_2.json` | `E7D9EC3DFE07E6BD4217E5AABE165960F6FCAACA8BCE56F07695117DD95F1EC5` |
| `schema_m3_s3b_v0_2.json` | `CBD748B79E6D3A8B0BF499D2866B3EF7A310A451CE7B7A08F1FE3B20DE33F17D` |
| report/record/usage | 见 `usage_m3_s3b_prereg_v0_2.json` |

**确定性**：`headroom_design_m3_s3b_v0_2.json` 两跑逐字节一致；JSON 无 telemetry；headroom wall≈0.1–0.2 s 仅 usage/报告。

## 6. 建议

1. **建议轻量复核**：重点 seed blocks 201（env1+headroom20+feedback20+eval20+arms140）、n_arms=7/n_arm_seeds=140/n_exec_seeds=201、`all_exec_seeds_count` 程序化、unique/overlap、headroom/DR/learner 合同/六比较/等价/边界保持。
2. 复核通过 + Lead 批准后才可执行 **M3-S3b 候选 learner 比较**（执行时才训练/拟合；本任务不运行）；**不批真实数据/湿实验/效果/药理/真实决策/迁移/机制/新颖性**。
3. **不做**：训练/运行候选/效果/代码晋升/旧判定修改；不把 Stage3 旧配置当 S3b；不把 no_increment 改写为通过。
