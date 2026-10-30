# R204-M3 Stage3.1 轻量复核（task-184）：v0.2 方案A

2026-10-28。角色：同一独立挑战者（非提案者、未参与 M3、不运行效果/训练/真实数据）。对象：[PROBLEM_M3_S3_EXEC_v0_2.md](PROBLEM_M3_S3_EXEC_v0_2.md)（SHA `814AE8BE…`）、[DESIGN_M3_S3_EXEC_v0_2.md](DESIGN_M3_S3_EXEC_v0_2.md)（`F7E525A6…`）、[exec_plan_m3_s3_v0_2.py](exec_plan_m3_s3_v0_2.py)（`9E0449E4…`）、[exec_plan_m3_s3_v0_2.json](exec_plan_m3_s3_v0_2.json)（`7E51CBA5…`）、[schema_m3_s3_exec_v0_2.json](schema_m3_s3_exec_v0_2.json)（`F6AC87B9…`）、report/record/usage、M3 Stage1/Stage2/Lead 决定。**只读；只写本文件与 `tmp/`。**

## 0. 结论先行

**总判决：revise（不能 approve_exec_v0_2_to_lead；也不是 stop）。**

v0.2 已按方案A修掉 v0.1 的 learner×allocation 复合矛盾：
- **7 arms 全纯 learner/固定 shared-score**：`A_candidate_score_tilt`、`A_full_history_retrain`、`A_importance_weighting`、`A_DR_targeting`、`A_TMLE_targeting`、`A_value_aware`、`A_standard_DR_TMLE`；**无 optimal allocation arm**（`no_optimal_allocation_arm=true`）；**primary=candidate vs A_standard_DR_TMLE**（固定 allocation 下标准 DR/TMLE learner）；secondary 5；family=6 Holm ✓。
- **固定反馈**：每 replicate 固定 seed/policy 生成 300 共享 (h,a,Y)；7 arms 复用同一反馈流/同一 300 评价；评价独立/target 不作标签；任何 arm 不得改 feedback；`all_arms_same_feedback_stream=true`/`all_arms_same_allocation_policy=true` ✓。
- **样本/预算**：R=10、300 feedback+300 eval/replicate、总3,000/3,000、7 arms、调参≤20、caps 1800s/2h/8GB/0 wells；闭环成本同账 ✓。
- **主端点/分析**：primary=candidate vs A_standard_DR_TMLE；δ=.05；mean≤−δ ∧ CI upper<0 ∧ Holm p<.05；family6；n_units300/deff2.2/n_eff136.36/MDE .04798268≤.05/n_req278；headroom；cluster；6,282 仅 Fisher-z；次端点 secondary ✓。
- **链/Stage1/Stage2**：35 文件链/Stage1 C209/Stage2 C213 PASS；seeds 20261601+（env/reps/arms/headroom，overlap=[]/unique）；两跑同 seeds 独立进程/逐字节/telemetry ✓。
- **G1–G6/13 失败/caps/schema/pilot 冻结/停止/边界**基本写清 ✓。

**但任务 ③ 明确要求的 per-arm 固定反馈 SHA 校验没有落到 schema/结果字段：**
- DESIGN/PROBLEM 写“结果 per-arm `feedback_stream_sha`/`evaluation_stream_sha` 相同，否则 leakage/stop”；但 `schema_m3_s3_exec_v0_2.json → arm_fields` **没有** `feedback_stream_sha`/`evaluation_stream_sha`；`stage3.arms` 也没有每 arm 的 stream SHA；`unit_checks` 只有布尔 `all_arms_same_feedback_stream=true`，**无 per-arm SHA 字段**。
- 执行时无法按 schema 记录/核对“7 arms 看到同一反馈流/同一评价样本”；固定反馈的核心可审计性只靠布尔 flag，不是 hash。**必须把 `feedback_stream_sha`/`evaluation_stream_sha` 写入 per-arm/schema，并规定不等→`design_invalid: leakage`/stop。**

**结论：先修 §2 的 1–2，再提交 Lead 批准 M3 Stage3 合成学习比较执行（支撑研究/机制账、compute-only、0 wells）。**

## 1. 逐条判决

| # | 项 | 判决 | 理由/证据 |
|---|---|---|---|
| ① | 方案A/纯 learner | **PASS** | 7 arms 全 shared-score/固定反馈/同评价；`A_standard_DR_TMLE` 固定 allocation；`no_optimal_allocation_arm=true`；primary 纯 learner；family6 ✓。 |
| ② | primary/secondary/Holm | **PASS** | primary candidate vs A_standard_DR_TMLE；secondary5；family6 Holm；成功 mean≤−δ ∧ CI upper<0 ∧ Holm p<.05；δ=.05；MDE .04798/n_req278/headroom/cluster/6,282 仅 Fisher-z；不换端点 ✓。 |
| ③ | 固定反馈实现/校验 | **FAIL/PARTIAL** | 固定 seed/policy/300 共享反馈+300 评价/7 arms 复用/评价独立/target 不作标签/无 arm 改 feedback；`all_arms_same_feedback_stream=true`/`all_arms_same_allocation_policy=true` ✓。**但 schema/arm_fields 无 `feedback_stream_sha`/`evaluation_stream_sha`，per-arm 结果无 SHA，无法按任务 ③ 做“相同否则 leakage/stop”的审计**（§0）。 |
| ④ | 保持项 | **PASS** | 35 链/Stage1/Stage2；seeds（env 20261601/reps 20261601–10/arms 20261611–80/headroom 20261681–90；overlap=[]/unique）；R=10/300/300/3,000；G1–G6/13 失败含 chain_mismatch；caps/schema/pilot 冻结/闭环/停止/边界 ✓。 |
| ⑤ | 边界 | **PASS** | 支撑研究/机制账；不执行真实数据/湿实验；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定；不恢复停止实验；M3 不与 M1/M2 混同；N1 不作证据；data readiness open；不把 learner 写成 allocation 或反之 ✓。 |
| ⑥ | 总判决 | **revise** | 见 §2。 |

## 2. 必改（≤5）

1. **在 schema/per-arm 结果中加入 `feedback_stream_sha`/`evaluation_stream_sha`**（并同步 `stage3_arms`/arm fields）：每 arm 每条 replicate 记录两条 SHA；规定 canonical 计算（对固定 (h,a,Y) 序列/评价 unit 序列排序后 SHA256）；**7 arms 两条 SHA 必须逐字节一致**；不一致→`design_invalid: leakage`/stop，不报学习比较。`unit_checks` 保留布尔，但不能替代 per-arm SHA。
2. **在 `stage3`/schema 中明确固定反馈生成 seed/policy**：每 replicate 的 300 反馈/300 评价由哪个 seed/policy 生成、评价独立于拟合/选择、target 不作标签；`A_standard_DR_TMLE` 的 allocation 固定为 shared-score（不再称 optimal allocation）；任何 arm 不得改 feedback/分配；失败只写类别。
3. **补 schema 的 per-arm 输出字段**：除 n_feedback/n_eval/tuning/cost_ledger/per_replicate_regret/mean_DeltaR/CI95/holm_p/pass 外，加入 `feedback_stream_sha`/`evaluation_stream_sha`（如适用，`allocation_policy_sha`）；两跑结果 JSON 逐字节；JSON 无 telemetry。
4. 保持 35 链/Stage1/Stage2、seeds/两跑、R=10/300/300/3,000、7 arms、primary/family6、MDE .04798/n_req278/headroom/cluster/6,282、G1–G6/13 失败/caps/schema/pilot 实测冻结/闭环/停止/边界；不执行真实数据/效果。
5. 禁止把 learner 比较写成 allocation 比较或反之；把任何 allocation/feedback 优势算进 primary；改旧判定/阈值；放宽容差/换端点；晋升代码；真实数据/湿实验；称药理/真实决策/迁移/机制/新颖性。

## 3. 修完后建议的 Lead M3 Stage3 批准文本（支撑研究/机制账、compute-only、0 wells）

> **批准范围**：在必改 1–3 完成并复核后，批准 **M3 Stage3 合成学习比较执行**（支撑研究/机制账、compute-only、0 wells）；不批真实数据/湿实验/效果/药理/真实决策/迁移/机制/新颖性；不批代码晋升；不改旧判定/门槛；不恢复停止实验。
>
> **冻结**：35 文件链/Stage1/C209/Stage2/C213；seeds（env 20261601、reps 20261601–10、arms 20261611+10a+r、headroom 20261681–90；禁用集/overlap=[]/unique；两跑同 seeds 独立进程/逐字节/telemetry 分离）；R=10、每 replicate 300 共享反馈+300 评价、总3,000/3,000、7 arms 同 feedback/eval；**7 arms 全部固定 shared-score（无 optimal allocation arm）；per-arm `feedback_stream_sha`/`evaluation_stream_sha` 必须相同，否则 leakage/stop**；调参≤20/caps/合法包；primary candidate vs A_standard_DR_TMLE、δ=.05、mean≤−δ ∧ CI upper<0 ∧ Holm p<.05、family6；MDE .04798268/n_req278/cluster/headroom/6,282 仅 Fisher-z；G1–G6/13 失败/caps 1800s/2h/8GB/0 wells；schema 先写；final-implementation Stage3 pilot（2 reps×7 arms×300 units）实测冻结 canonical；JSON 无 telemetry；闭环成本同账；停止/边界；不执行真实数据/效果。
>
> **禁止**：真实数据/湿实验/效果/真实决策/药理/迁移/机制/新颖性；把 learner 比较写成 allocation 比较或反之；把 allocation/feedback 优势算进 primary；改旧判定/阈值/端点；放宽容差；晋升代码；恢复停止实验。

## 4. 声明

- **本轮不运行效果/训练/真实数据**：只读 M3 Stage3 v0.2 exec prereg/JSON/schema/Stage1/Stage2 链；只写本文件与 `tmp/`；未改 exec prereg 产物。
- **总判决：revise**。方案A（7 纯 learner arms/固定 shared-score/无 optimal allocation）、primary/family6、样本/G1–G6/13/caps/schema/pilot/闭环/边界基本正确；但 **schema/per-arm 结果缺 `feedback_stream_sha`/`evaluation_stream_sha`，无法按任务 ③ 审计“7 arms 同一反馈流/评价样本，相同否则 leakage/stop”**。修完 1–3 后可提交 Lead 批准 M3 Stage3 合成学习比较执行（支撑研究/机制账、compute-only、0 wells）。

**一句话：v0.2 已按方案A把 7 arms 全部改成固定 shared-score 的纯 learner 比较（无 optimal allocation arm），primary/family6/样本/预算/边界都对；但任务 ③ 要求的 per-arm `feedback_stream_sha`/`evaluation_stream_sha` 没有写进 schema/arm 字段，固定反馈只剩布尔 flag，无法做“相同否则 leakage/stop”的审计——判 revise：补 SHA 字段/生成规则/失败映射，再提交 Lead 批准 M3 Stage3 合成学习比较执行。**
