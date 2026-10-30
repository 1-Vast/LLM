# report_m3_s3_exec_v0_3 —— R204-M3-S3.2 修订预注册报告（per-arm 流 SHA/输出字段；不运行）

2026-10-28。对象：R204-M3 Stage3 合成执行预注册 v0.3。依据：M3-S3.1-C1 复核（revise，必改 1–3）、M3 v0.2 链、Lead Stage1/Stage2 决定、Stage1/C209、Stage2/C213、R204 BRIEF/report、ERRATA C197/C199/C201/C207/C209/C213/C215/C216。
**状态：预注册修订草案；未运行 Stage3 训练/效果/真实数据；仅规划/算术/骨架单测；支撑研究/机制账 only；compute-only、0 wells；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定；Stage3 执行须另立独立挑战+Lead 批准。**

## 0. 交付物（v0.3 新文件；v0.1/v0.2 保留不改）

- 问题定义：[PROBLEM_M3_S3_EXEC_v0_3.md](PROBLEM_M3_S3_EXEC_v0_3.md)（`3D8B2E4B…`）
- 执行设计：[DESIGN_M3_S3_EXEC_v0_3.md](DESIGN_M3_S3_EXEC_v0_3.md)（`B98D4A30…`）
- 规划/骨架：[exec_plan_m3_s3_v0_3.py](exec_plan_m3_s3_v0_3.py)（`FC40E25D…`）→ [exec_plan_m3_s3_v0_3.json](exec_plan_m3_s3_v0_3.json)（`0A8D2DD2…`）
- schema：[schema_m3_s3_exec_v0_3.json](schema_m3_s3_exec_v0_3.json)（`D408D1DC…`）
- 记录/用量：[record_m3_s3_exec_v0_3.md](record_m3_s3_exec_v0_3.md)、[usage_m3_s3_exec_v0_3.json](usage_m3_s3_exec_v0_3.json)

## 1. 必改落实

| # | 挑战问题 | v0.3 落实 |
|---|---|---|
| ① **per-arm stream SHA 仅布尔** | schema `arm_fields`/`stage3.arms`/per-arm 结果加入 **`feedback_stream_sha`、`evaluation_stream_sha`、`allocation_policy_sha`**；**canonical 写死**：反馈记录 `"h,a,Y\n"`、评价记录 `"h,a\n"`、UTF-8 固定顺序拼接、**SHA256 uppercase**；policy token SHA；**每 replicate 7 arms 两 SHA 必须逐字节一致**；不一致→`design_invalid: leakage`/stop、不报学习比较；`unit_checks` 布尔保留但不替代 per-arm SHA |
| ② **固定反馈 seed/policy 写死** | 每 replicate 固定 seed（20261601+r）/policy 生成 300 反馈+300 评价；评价独立、target 不作标签；`A_standard_DR_TMLE` allocation 固定 shared-score（不再称 optimal allocation）；任何 arm 不得改 feedback/分配；失败只写类别 |
| ③ **补 per-arm 输出字段** | `arm_fields`=**16 字段**：arm_id、replicate_id、update_rule、allocation_policy、**n_feedback、n_eval、tuning_configs、cost_ledger、per_replicate_regret、mean_DeltaR、CI95、holm_p、pass、feedback_stream_sha、evaluation_stream_sha、allocation_policy_sha**；两跑 JSON 逐字节；无 telemetry |
| ④ 保持 | 35 文件链/Stage1/Stage2；seeds/两跑；R=10/300/300/3,000；7 纯 learner arms/固定 shared-score/无 optimal allocation；primary vs A_standard_DR_TMLE、family=6 Holm、δ=.05、MDE .04798268/n_req278/headroom/cluster/6,282；G1–G6/13 失败/caps/schema/pilot 冻结/闭环/停止/边界 |

## 2. 链/Stage1/Stage2（已通过）

- **35 文件 SHA 全匹配**（chain_pass=true、mismatches=0）：M3 v0.2 8+Lead Stage1；Stage1/C209 8；Stage2 exec v0.2 8+Lead Stage2；Stage2/C213 9（`36C4DF12…`、60/60 per-arm、failure_category null）；Stage1/Stage2 状态 PASS。
- 不匹配→`design_invalid: chain_mismatch`；执行时重核。

## 3. per-arm 16 字段 / canonical / leakage 判定

- 字段：arm_id、replicate_id、update_rule、allocation_policy、n_feedback、n_eval、tuning_configs、cost_ledger、per_replicate_regret、mean_DeltaR、CI95、holm_p、pass、**feedback_stream_sha**、**evaluation_stream_sha**、**allocation_policy_sha**。
- canonical：反馈 `"h,a,Y\n"`、评价 `"h,a\n"`（整数固定顺序）；UTF-8 拼接；SHA256 uppercase；policy `SHA256("shared_score_fixed_same_feedback_stream")`。
- **每 replicate 7 arms 的 feedback/evaluation SHA 必须一致**；不一致→`design_invalid: leakage`/stop，不报学习比较。
- 本轮以固定 toy 序列重算两次一致（示例 feedback `[(0,1,1),(1,2,0),(2,0,1),(0,2,0)]` → `0696F595…`；evaluation `[(0,1),(1,0),(2,1),(1,2)]` → `01063FFF…`；policy → `6A976C3C…`），不训练。

## 4. 样本/arms/端点（保持）

- seeds：env 20261601；reps 20261601–10；arms 20261611–80；headroom 20261681–90；overlap=[]、unique=true；两跑同 seeds/独立进程/逐字节/telemetry 单独。
- 样本：R=10；每 replicate 300 反馈+300 评价；总 3,000/3,000；7 arms（A_candidate_score_tilt、A_full_history_retrain、A_importance_weighting、A_DR_targeting、A_TMLE_targeting、A_value_aware、**A_standard_DR_TMLE**）；全部纯 learner/固定 shared-score/无 optimal allocation。
- primary=candidate vs A_standard_DR_TMLE；δ=.05；成功 mean≤−δ ∧ CI upper<0 ∧ Holm p<.05；family=6 Holm；MDE .04798268≤.05、n_req278；headroom 先检；6,282/1,573 仅 Fisher-z；不换端点。

## 5. G1–G6/失败/预算/闭环

- G1 支持→support/positivity；G2 截断→calibration；G3 投影/拟合→calibration/nonidentifiable；G4 无泄漏（**SHA 不一致→leakage**）；G5 两跑→two_run_mismatch；G6 schema/预算→compute_budget_exceeded；13 类失败（含 chain_mismatch）。
- caps 1800 s/2 h/8 GB/0 wells；schema 先写；执行前最终实现 Stage3 pilot（2×7×300）实测冻结；Stage2 pilot 仅历史参考；JSON 无 telemetry；失败只写类别。
- 闭环成本：每 arm 300 feedback/300 eval/≤20/caps；7 arms 同预算；培养/板/对照/失败/重复/标定/计算/调参同账；超限 stop。

## 6. 边界

支撑研究/机制账 only；不执行真实数据/湿实验；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定；不恢复停止实验；M3 不与 M1/M2 混同；N1 不作证据；data readiness open（C203/C205/C210/C214）；Stage3 执行须另立独立挑战+Lead 批准；**禁止把 learner 比较写成 allocation 比较或反之、把任何 allocation/feedback 优势算进 primary**。

## 7. 产物 SHA/确定性

| 文件 | SHA256 |
|---|---|
| `PROBLEM_M3_S3_EXEC_v0_3.md` | `3D8B2E4BFB6D39598CA4DADAC9CE118442D076DE3BD319E38C2318187B2552B8` |
| `DESIGN_M3_S3_EXEC_v0_3.md` | `B98D4A302CFB5DFD7123B8FBAB87C57AAE34117397602F40FBA0106714BE8618` |
| `exec_plan_m3_s3_v0_3.py` | `FC40E25D9D840494C416D9A1346E232B5A24B571FD4FC80DF95838F5D0C040F6` |
| `exec_plan_m3_s3_v0_3.json` | `0A8D2DD252019AF98F325AF2E4505DA52A44A6F2EA42030E20DDFFC3C05B7499` |
| `schema_m3_s3_exec_v0_3.json` | `D408D1DC981B2B24FBACEE2AC28F81C0484ADFA0FB78FCA2AAE3BC956F36144F` |
| report/record/usage | 见 `usage_m3_s3_exec_v0_3.json` |

**确定性**：`exec_plan_m3_s3_v0_3.json` 与 `schema_m3_s3_exec_v0_3.json` 两跑逐字节一致；JSON 无 telemetry。

## 8. 建议

1. **建议轻量复核**：per-arm 两 SHA 是否落到 schema/per-arm 结果且 canonical/leakage 判定可执行；固定反馈 seed/policy 写死；per-arm 16 字段完整；方案A/7 arms/primary/family6/样本/预算/链/边界保持不变。
2. 复核通过 + Lead 批准后才可执行 **Stage3 合成学习比较**（支撑研究/机制账、compute-only、0 wells）；执行前重核 35 文件链、最终实现 pilot 实测冻结、per-arm feedback/eval SHA 一致检查、两跑/schema/失败模板核验。
3. **不做**：训练/效果/真实数据/湿实验/代码晋升/旧判定修改/恢复停止实验；不把 learner 比较写成 allocation 比较或反之。
