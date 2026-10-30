# PROBLEM_M3_S3_EXEC_v0_3 —— R204-M3-S3.2 Stage3 合成执行预注册（per-arm 流 SHA/输出字段；不运行）

2026-10-28。对象：R204-M3 Stage3 合成执行预注册（固定反馈纯 learner 比较 + 闭环成本）。本文件修正 v0.1/v0.2（保留不改），落实 M3-S3.1-C1 必改 1–3：**per-arm `feedback_stream_sha`/`evaluation_stream_sha`** 落到 schema/per-arm 结果、**canonical 计算写死**、**补 per-arm 输出字段**。方案A（7 arms 全部纯 learner/固定 shared-score/同反馈同评价；无 optimal allocation arm）保持不变。依据：M3 v0.2 链、Lead Stage1/Stage2 决定、Stage1/C209、Stage2/C213（`36C4DF12…`）、R204 BRIEF/report、ERRATA C197/C199/C201/C207/C209/C213/C215/C216。
**状态：预注册修订草案 v0.3；未运行 Stage3 训练/效果/真实数据；仅规划/算术/骨架单测；支撑研究/机制账 only；compute-only、0 wells；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定；M3 不与 M1/M2 混同；N1 不作证据；data readiness open（C203/C205/C210/C214）。Stage3 执行须另立独立挑战+Lead 批准。**

## 0. M3-S3.1-C1 必改落实

| # | 挑战问题 | v0.3 修正 |
|---|---|---|
| ① **per-arm stream SHA 只靠布尔** | `schema arm_fields/stage3.arms/per-arm 结果` 加入 **`feedback_stream_sha`、`evaluation_stream_sha`、`allocation_policy_sha`**；每 arm 每 replicate 记录；**canonical 计算写死**：反馈记录 `"h,a,Y\\n"`、评价记录 `"h,a\\n"`，UTF-8、固定顺序拼接，SHA256 uppercase；policy token `shared_score_fixed_same_feedback_stream` 的 SHA256；**7 arms 两条 SHA 必须逐字节一致**；不一致→`design_invalid: leakage`/stop，不报学习比较；`unit_checks` 布尔保留但不能替代 per-arm SHA |
| ② **固定反馈 seed/policy 写死** | 每 replicate 固定 seed（20261601+r）/分配 policy 生成 300 反馈/300 评价；评价独立于拟合/选择、target 不作标签；`A_standard_DR_TMLE` allocation 固定 shared-score（**不再称 optimal allocation**）；任何 arm 不得改 feedback/分配；失败只写类别 |
| ③ **补 per-arm 输出字段** | `arm_fields` = arm_id、replicate_id、update_rule、allocation_policy、**n_feedback、n_eval、tuning_configs、cost_ledger、per_replicate_regret、mean_DeltaR、CI95、holm_p、pass、feedback_stream_sha、evaluation_stream_sha、allocation_policy_sha**（16 字段）；两跑结果 JSON 逐字节；JSON 无 telemetry |
| ④ 保持 | 35 文件链/Stage1/Stage2；seeds（env 20261601、reps 20261601–10、arms 20261611–80、headroom 20261681–90；overlap=[]/unique）；R=10/300/300/总 3,000/3,000；7 arms 纯 learner/固定 shared-score/无 optimal allocation；primary candidate vs A_standard_DR_TMLE、family=6 Holm、δ=.05、MDE .04798268/n_req278/headroom/cluster/6,282 仅 Fisher-z；G1–G6/13 失败/caps 1800 s/2 h/8 GB/0 wells/schema 先写/pilot 最终实现冻结/闭环成本/停止/边界 |

## 1. 链核验（执行前；不匹配→stop）

`exec_plan_m3_s3_v0_3.py` 只读核验 **35 文件 SHA 全匹配（chain_pass=true、mismatches=0）**：M3 v0.2 8+Lead Stage1；Stage1/C209 8；Stage2 exec v0.2 8+Lead Stage2；Stage2/C213 9（`36C4DF12…`，60/60 per-arm、failure_category null、no_effect_results=true）。不匹配/状态不符→`design_invalid: chain_mismatch`；执行时重核。

## 2. 独立 seeds / 样本语义（保持）

- seeds：env **20261601**；replicates **20261601–20261610**；arms **20261611+10a+r（20261611–20261680）**；headroom **20261681–20261690**；禁用 M3 Stage1 20261112/13、20261200；M3 Stage2 20261401–20261470；M1 Stage1/Stage2、M2、N1 禁用集；overlap=[]、unique=true；两跑同 seeds/独立进程/结果 JSON 逐字节/telemetry 单独。
- 样本：R=**10**；每 replicate **300 条反馈 (h,a,Y)** + **300 评价 units**；总反馈/评价 **3,000/3,000**；7 arms；每 arm 300/300/replicate；调参≤20；caps 1800 s/2 h/8 GB/0 wells。
- **固定反馈生成（写死）**：每 replicate 反馈流由固定 seed（20261601+r）与固定 shared-score allocation policy 生成；评价流由固定 seed 生成；**评价独立于拟合/更新/选择**；target 不作标签；**7 arms 复用同一反馈/同一评价**；任何 arm 不得改变 feedback/分配。
- **A_standard_DR_TMLE allocation 固定 shared-score**；不存在 optimal allocation arm/比较。

## 3. per-arm 输出字段（16）与 stream SHA（写死）

| 字段 | 说明 |
|---|---|
| arm_id、replicate_id、update_rule、allocation_policy | 身份/方法/固定共享分配 |
| **n_feedback**、**n_eval** | 每 arm 每 replicate 300/300 |
| **tuning_configs** | ≤20 |
| **cost_ledger** | 反馈/评价/计算/调参成本同账 |
| **per_replicate_regret** | 每 replicate 决策后悔（用于配对 ΔR） |
| **mean_DeltaR**、**CI95**、**holm_p**、**pass** | 预注册端点/多重性/判定 |
| **feedback_stream_sha** | 该 replicate 全部 arm 必须相同 |
| **evaluation_stream_sha** | 该 replicate 全部 arm 必须相同 |
| **allocation_policy_sha** | 固定 shared-score policy token SHA256 |

**canonical 计算（冻结）**：反馈记录格式 `"h,a,Y\n"`（整数，固定生成顺序）；评价记录 `"h,a\n"`（整数，固定评价顺序）；UTF-8 字节按序拼接；**SHA256 uppercase**；`allocation_policy_sha=SHA256("shared_score_fixed_same_feedback_stream")`。**每 replicate 所有 7 arms 的 feedback/evaluation SHA 必须逐字节一致；不一致→`design_invalid: leakage`/stop，不报学习比较。** `unit_checks` 布尔保留，但不替代 per-arm SHA；canonical 示例在本轮以固定 toy 序列重算两次一致（不训练）。

## 4. primary/secondary/Holm（保持）

- **Primary comparison**：A_candidate_score_tilt vs **A_standard_DR_TMLE**。
- Primary endpoint=独立功能决策效用/后悔 normalized、δ=**0.05**；成功=mean ΔR≤−δ ∧ 95% CI upper<0 ∧ **Holm p<.05**。
- **family=6 Holm**（primary + full-history/IW/DR/TMLE/value-aware）；次端点=预测校准/DR 分数误差/RNA（仅 secondary）。
- n_units=300、deff=2.2、n_eff=136.36、MDE80=.04798268≤.05、n_req=278≤300；cluster 按 replicate/背景/任务；headroom=U_max−U0 先检；**6,282.1038/1,572.7759 仅 Fisher-z**；不换端点/不把 allocation/feedback 优势算进 primary。

## 5. G1–G6/失败/预算/schema/闭环

- G1 支持→support/positivity；G2 截断→calibration；G3 投影/拟合→calibration/nonidentifiable；G4 无泄漏（含 **stream SHA 不一致→leakage**）→leakage；G5 两跑→two_run_mismatch；G6 schema/预算→compute_budget_exceeded；**13 类失败类别**（含 chain_mismatch）。
- caps 1800 s/2 h/8 GB/0 wells；schema 先写；执行前最终实现 Stage3 pilot（2 reps×7 arms×300 units）实测冻结 canonical；Stage2 pilot 仅历史参考；结果 JSON 无 telemetry；失败只写类别。
- 闭环成本：每 arm 300 feedback/300 eval/≤20/caps；7 arms 同预算；培养/板/对照/失败/重复/标定/计算/调参同账；超限 stop。

## 6. 停止/边界

- 标准 DR/TMLE learner（固定分配）等预算复制/超过→`no_increment`/撤；π=b→H=1；共线/分离/无支持→nonidentifiable；零支持/极端权重→support/positivity；截断→calibration；评价复用/**stream SHA 不一致**→leakage；两跑/链/预算→对应类别；不改旧判定/门槛；不放宽/改阈值/换端点。
- **禁止**把 learner 比较写成 allocation 比较或反之；把任何 allocation/feedback 优势算进 primary；改旧判定/阈值；放宽容差/换端点；晋升代码；真实数据/湿实验。
- 只更新功能均值≠细胞动力学；无序贯→不称序贯 DR；支撑研究/机制账 only；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定；不恢复停止实验；M3 不与 M1/M2 混同；N1 不作证据；data readiness open（C203/C205/C210/C214）；Stage3 执行须另立独立挑战+Lead 批准。
