# R204-M3 Stage3.2 轻量复核（task-186）：v0.3 per-arm stream SHA

2026-10-28。角色：同一独立挑战者（非提案者、未参与 M3、不运行效果/训练/真实数据）。对象：[PROBLEM_M3_S3_EXEC_v0_3.md](PROBLEM_M3_S3_EXEC_v0_3.md)（SHA `3D8B2E4B…`）、[DESIGN_M3_S3_EXEC_v0_3.md](DESIGN_M3_S3_EXEC_v0_3.md)（`B98D4A30…`）、[exec_plan_m3_s3_v0_3.py](exec_plan_m3_s3_v0_3.py)（`FC40E25D…`）、[exec_plan_m3_s3_v0_3.json](exec_plan_m3_s3_v0_3.json)（`0A8D2DD2…`）、[schema_m3_s3_exec_v0_3.json](schema_m3_s3_exec_v0_3.json)（`D408D1DC…`）、report/record/usage、M3 Stage1/Stage2/Lead 决定。**只读；只写本文件与 `tmp/`。**

## 0. 结论先行

**总判决：revise（不能 approve_exec_v0_3_to_lead；也不是 stop）。**

v0.3 已修掉 v0.2 的 per-arm SHA 缺口：
- `arm_fields`/per-arm 结果含 **`feedback_stream_sha`/`evaluation_stream_sha`/`allocation_policy_sha`**（16 字段）；canonical 写死（反馈 `"h,a,Y\n"`、评价 `"h,a\n"`、UTF-8、固定顺序、SHA256 uppercase）；policy SHA=`shared_score_fixed_same_feedback_stream`；7 arms 两 SHA 必须逐字节一致，否则 `design_invalid: leakage`/stop；`unit_checks` 布尔保留但不能替代 SHA ✓。
- **toy canonical 可复算**：feedback `0696F595FAA29BF9B9F1BC59E96E74FBFDB9CB415ED68B671BDA3B9FAA2F7913`、evaluation `01063FFF647C04CB3D1E1A01FDC32114C424EFF86C5F69E3405479CEC832CBAA`、policy `6A976C3CC10B244F6EEF498ACAD4850F74689F0F554161A4872E975C3469F8EF`；我按同一 canonical 重算一致 ✓。
- **固定反馈**：每 replicate 反馈 seed=20261601+r；7 arms 复用同反馈/同评价；评价独立/target 不作标签；`A_standard_DR_TMLE` 固定 shared-score；无 optimal allocation arm；任何 arm 不得改 feedback/分配 ✓。
- **保持项**：35 链/Stage1/Stage2、seeds/R=10/300/300/3,000、7 arms 纯 learner、primary/family6、MDE .04798/n_req278/headroom/cluster/6,282、G1–G6/13 失败/caps/schema/pilot 冻结/闭环/停止/边界 ✓。

**但还有一个可复现缺口：**
- DESIGN §1 写“评价流 seed=**20261601+r 的独立子流/固定派生**”——**“独立子流/固定派生”没有写死具体 seed/派生规则**；`sample_semantics`/`stage3`/schema 只有 `feedback seed=20261601+r`、`fixed_feedback_rule`，**没有 `evaluation_seed`/派生公式**。因此 `evaluation_stream_sha` 在 7 arms 相同这一点无法由预注册独立复算。
- 同样，**feedback 的“固定 shared-score allocation policy”只给了 token/名字**（`shared_score_fixed_same_feedback_stream`），**没有写死 Q_k(b) 的分配概率公式、采样顺序/随机数与 support 规则**；`feedback_stream_sha` 可复算性依赖执行者自行实现，和 Stage2 的 shared-score 口径可能不一致。
- task ② 要求“固定反馈 seed/policy 写死”；当前只有 feedback seed 写死，evaluation seed/派生和 shared-score 分配公式仍开放。

**结论：先修 §2 的 1–2，再提交 Lead 批准 M3 Stage3 合成学习比较执行（支撑研究/机制账、compute-only、0 wells）。**

## 1. 逐条判决

| # | 项 | 判决 | 理由/证据 |
|---|---|---|---|
| ① | per-arm SHA 落 schema/结果 | **PASS** | arm_fields/per-arm 16 字段含两 SHA+policy SHA；canonical 格式/顺序/UTF-8/SHA256 uppercase；7 arms 必须一致→leakage/stop；布尔不替代；toy SHA 复算一致 ✓。 |
| ② | 固定反馈 seed/policy | **FAIL/PARTIAL** | feedback seed=20261601+r、7 arms 同反馈/评价、评价独立/target 不作标签、A_standard_DR_TMLE 固定 shared-score、无 optimal arm ✓；**evaluation stream 只写“独立子流/固定派生”未写死；shared-score 分配概率公式/采样/support 未写死**（§0）。 |
| ③ | per-arm 16 字段 | **PASS** | arm_id/replicate_id/update_rule/allocation_policy/n_feedback/n_eval/tuning_configs/cost_ledger/per_replicate_regret/mean_DeltaR/CI95/holm_p/pass/feedback_stream_sha/evaluation_stream_sha/allocation_policy_sha；两跑/无 telemetry ✓。 |
| ④ | 保持项 | **PASS** | 35 链/Stage1/Stage2；seeds（env20261601/reps20261601–10/arms20261611–80/headroom20261681–90；overlap=[]/unique）；R=10/300/300/3,000；7 arms 纯 learner/固定 shared-score/无 optimal allocation；primary candidate vs A_standard_DR_TMLE、family6、δ=.05、MDE .04798/n_req278/headroom/cluster/6,282；G1–G6/13 失败/caps/schema/pilot/闭环/停止/边界 ✓。 |
| ⑤ | 边界 | **PASS** | 支撑研究/机制账；不执行真实数据/湿实验；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定；不恢复停止实验；M3 不与 M1/M2 混同；N1 不作证据；data readiness open；不把 learner 写成 allocation 或反之 ✓。 |
| ⑥ | 总判决 | **revise** | 见 §2。 |

## 2. 必改（≤5）

1. **写死 evaluation stream 的 seed/派生规则**：明确每 replicate 评价流用哪个 seed（例如 `20261701+r` 或 `feedback_seed + 1000`）、如何独立于反馈流/拟合/选择、300 units 的生成顺序与 canonical 记录；加入 `sample_semantics`/`stage3`/schema 字段（至少 `evaluation_seed_rule`/`evaluation_stream_rule`）。**不能只写“独立子流/固定派生”。**
2. **写死 shared-score feedback allocation policy**：给出 `Q_k(b)`/allocation 概率的精确公式、从 Stage2 冻结的 p/μ/b/π/m/C_H 计算方式、采样顺序/随机数、support/截断规则；确保 7 arms 的 feedback stream 由同一 policy 生成且 feedback SHA 可独立复算；建议引用 Stage2/C213 的 shared-score 定义与 SHA。
3. **在 `sample_semantics`/schema 中明确 feedback/evaluation 的 seed 与 policy 字段**：feedback seed=20261601+r；evaluation seed/派生；allocation policy token/公式；per-arm `feedback_stream_sha`/`evaluation_stream_sha`/`allocation_policy_sha`；不一致→`design_invalid: leakage`/stop；toy canonical 复算保持一致。
4. **保持** 35 链/Stage1/Stage2、seeds/两跑、R=10/300/300/3,000、7 arms 纯 learner/固定 shared-score/无 optimal allocation、primary/family6、MDE .04798/n_req278/headroom/cluster/6,282、G1–G6/13 失败/caps/schema/pilot 实测冻结/闭环/停止/边界；不执行真实数据/效果。
5. **禁止**：把 learner 比较写成 allocation 比较或反之；把 allocation/feedback 优势算进 primary；改旧判定/阈值；放宽容差/换端点；晋升代码；真实数据/湿实验；称药理/真实决策/迁移/机制/新颖性。

## 3. 修完后建议的 Lead M3 Stage3 批准文本（支撑研究/机制账、compute-only、0 wells）

> **批准范围**：在必改 1–3 完成并复核后，批准 **M3 Stage3 合成学习比较执行**（支撑研究/机制账、compute-only、0 wells）；不批真实数据/湿实验/效果/药理/真实决策/迁移/机制/新颖性；不批代码晋升；不改旧判定/门槛；不恢复停止实验。
>
> **冻结**：35 文件链/Stage1/C209/Stage2/C213；seeds（env 20261601、reps 20261601–10、arms 20261611+10a+r、headroom 20261681–90；禁用集/overlap=[]/unique；两跑同 seeds 独立进程/逐字节/telemetry 分离）；R=10、每 replicate 300 共享反馈+300 评价、总3,000/3,000、7 arms 同 feedback/eval；**feedback seed=20261601+r、evaluation seed/派生规则写死；shared-score allocation 概率公式/采样/support 写死；7 arms 固定 shared-score（无 optimal allocation arm）；per-arm `feedback_stream_sha`/`evaluation_stream_sha`/`allocation_policy_sha` 必须一致，否则 leakage/stop**；调参≤20/caps/合法包；primary candidate vs A_standard_DR_TMLE、δ=.05、mean≤−δ ∧ CI upper<0 ∧ Holm p<.05、family6；MDE .04798268/n_req278/cluster/headroom/6,282 仅 Fisher-z；G1–G6/13 失败/caps 1800s/2h/8GB/0 wells；schema 先写；final-implementation Stage3 pilot（2 reps×7 arms×300 units）实测冻结 canonical；JSON 无 telemetry；闭环成本同账；停止/边界；不执行真实数据/效果。
>
> **禁止**：真实数据/湿实验/效果/真实决策/药理/迁移/机制/新颖性；把 learner 比较写成 allocation 比较或反之；把 allocation/feedback 优势算进 primary；改旧判定/阈值/端点；放宽容差；晋升代码；恢复停止实验。

## 4. 声明

- **本轮不运行效果/训练/真实数据**：只读 M3 Stage3 v0.3 exec prereg/JSON/schema/Stage1/Stage2 链；只写本文件与 `tmp/`；未改 exec prereg 产物。
- **总判决：revise**。per-arm 16 字段/两 SHA/policy SHA、toy canonical 复算、方案A/7 纯 learner/primary/family6/样本/预算/链/边界基本正确；但 **evaluation stream seed/派生规则未写死、shared-score feedback allocation 概率公式/采样/support 未写死**，feedback/evaluation SHA 仍不能由预注册独立复算。修完 1–3 后可提交 Lead 批准 M3 Stage3 合成学习比较执行（支撑研究/机制账、compute-only、0 wells）。

**一句话：v0.3 已把 per-arm `feedback_stream_sha`/`evaluation_stream_sha`/`allocation_policy_sha` 写进 schema/per-arm 16 字段，canonical toy SHA 我复算一致，7 纯 learner/固定 shared-score/primary/family6/边界都对；但 evaluation stream 只写“独立子流/固定派生”没有具体 seed/派生，shared-score allocation 概率公式/采样/support 也未写死，feedback/evaluation SHA 仍不可独立复算——判 revise：补 evaluation seed/派生 + shared-score 分配公式/采样/support，再提交 Lead 批准 M3 Stage3 合成学习比较执行。**
