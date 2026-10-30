# R204-M3 Stage3.3 轻量复核（task-188）：v0.4 evaluation/Q 冻结

2026-10-28。角色：同一独立挑战者（非提案者、未参与 M3、不运行效果/训练/真实数据）。对象：[PROBLEM_M3_S3_EXEC_v0_4.md](PROBLEM_M3_S3_EXEC_v0_4.md)（SHA `EAB4E85D…`）、[DESIGN_M3_S3_EXEC_v0_4.md](DESIGN_M3_S3_EXEC_v0_4.md)（`5C6CFF4A…`）、[exec_plan_m3_s3_v0_4.py](exec_plan_m3_s3_v0_4.py)（`3338F70D…`）、[exec_plan_m3_s3_v0_4.json](exec_plan_m3_s3_v0_4.json)（`9FB57C5B…`）、[schema_m3_s3_exec_v0_4.json](schema_m3_s3_exec_v0_4.json)（`3DEFD258…`）、report/record/usage、M3 Stage1/Stage2/Lead 决定。**只读；只写本文件与 `tmp/`。**

## 0. 结论先行

**总判决：approve_exec_v0_4_to_lead（仅批准 M3 Stage3 合成学习比较执行：支撑研究/机制账、compute-only、0 wells；不批真实数据/湿实验/效果/药理/真实决策/迁移/新颖性）。**

v0.4 已修掉 v0.3 的两个可复现缺口：
- **evaluation stream 写死**：每 replicate **evaluation seed=20261701+r（20261701–10）**，独立于 feedback 20261601+r；300 units 固定 j=0..299（h_j~p(h) 第一随机数、a_j~shared-score w 第二随机数）；canonical `"h,a\n"`；evaluation utility 用 known-truth μ(h,a) 精确值（无噪声 Y 标签）；评价不用于拟合/更新/选择；7 arms 复用同评价流；`sample_semantics`/`stage3`/schema 字段 `feedback_seed_rule/evaluation_seed_base/evaluation_seed_rule/evaluation_stream_rule` 齐全 ✓。
- **shared-score allocation 写死**：`Q(h,a)=p(h)·π2(a|h)^2·[Var+(μ−m_wrong)^2]/b(a|h)`，`w=Q/Σ_legal Q`，`Var=μ(1−μ)`；p/μ/b/π2/m_wrong/C_H=20/b_min=1e-6 取自 Stage2 冻结值；采样顺序 h→a→Y、固定 RNG 流/7 arms 同流；support `b>0,b≥1e-6,Q finite`；C_H=20 仅 H clipping 诊断、不用于 weights；unsupported→support/positivity；引用 Stage2/C213 `m3_stage2.json` `36C4DF12…`/schema `0E46DEC0…` ✓。
- **per-arm 16 字段/三 SHA**：`feedback_stream_sha`/`evaluation_stream_sha`/`allocation_policy_sha` 在 arm_fields/per-arm；7 arms 两 SHA 必须逐字节一致，否则 leakage/stop；`unit_checks` 布尔保留但不替代；**toy canonical SHA 我按同一规则复算一致**（feedback `0696F595…`、evaluation `01063FFF…`、policy `6A976C3C…`）✓。
- **保持项**：35 文件链/Stage1/Stage2（chain_pass=true、C209/C213 PASS）；seeds（env 20261601、feedback 20261601–10、evaluation 20261701–10、arms 20261611–80、headroom 20261681–90；overlap=[]/unique）；R=10/300/300/总3,000/3,000；7 arms 纯 learner/固定 shared-score/无 optimal allocation；primary candidate vs A_standard_DR_TMLE、family6、δ=.05、MDE .04798268/n_req278/headroom/cluster/6,282；G1–G6/13 失败/caps 1800s/2h/8GB/0 wells/schema 先写/pilot 实测冻结/闭环/停止/边界 ✓。
- **边界**：支撑研究/机制账；不执行真实数据/湿实验；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定；不恢复停止实验；M3 不与 M1/M2 混同；N1 不作证据；data readiness open；不把 learner 写成 allocation 或反之 ✓。

**非阻塞执行备注**：
1. **evaluation action `a_j~w` 是 shared-score 共同样本**，不是每个 arm 自己的 policy 样本；primary “decision utility/regret” 应报告为**同一 held-out 评价样本上的共同样本诊断**，不能写成任意 arm policy 的无偏 population policy value；所有 arms 共用同一 `h,a` 流，比较仍是配对/同评价。
2. **C_H=20 只用于 H clipping 诊断**，不进入 allocation weights；Q 只用 b_min/support/μ/π2/m_wrong；报告需区分“clipped H 诊断”与“allocation Q”。
3. **final pilot**：Stage2 pilot 仅历史参考；执行前 final-implementation Stage3 pilot（2 reps×7 arms×300 units）实测 wall/CPU/memory 冻结 canonical；Stage3 main=caps 1800s/2h/8GB/0 wells。
4. **toy canonical** 已复算；执行时 toy 两跑/结果 JSON 无 telemetry 保持。

## 1. 逐条判决

| # | 项 | 判决 | 理由/证据 |
|---|---|---|---|
| ① | evaluation stream | **PASS** | seed 20261701+r 独立于 feedback 20261601+r；300 units 顺序/canonical `"h,a\n"`；utility=μ(h,a) 精确；不用于拟合/选择；7 arms 复用；字段齐全 ✓。 |
| ② | shared-score Q/采样/support | **PASS** | Q 公式/w=Q/ΣQ/Var=μ(1−μ)；Stage2 冻结 p/μ/b/π2/m_wrong/C_H/b_min；h→a→Y；support b>0/≥1e-6/Q finite；C_H 仅诊断；Stage2 C213 SHA；toy SHA 复算 ✓。 |
| ③ | schema/sample_semantics/toy | **PASS** | 字段齐全；per-arm 三 SHA；7 arms 同流；不一致→leakage/stop；toy feedback/evaluation/policy SHA 一致；无 optimal allocation ✓。 |
| ④ | 保持项 | **PASS** | 35 链/Stage1/Stage2；seeds/R=10/300/300/3,000；7 纯 learner；primary/family6/δ=.05/MDE .04798/n_req278/headroom/cluster/6,282；G1–G6/13 失败/caps/schema/pilot/闭环/停止/边界 ✓。 |
| ⑤ | 边界 | **PASS** | 支撑研究/机制账；不执行真实数据/湿实验；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定；不恢复停止实验；M3 不与 M1/M2 混同；N1 不作证据；data readiness open；不把 learner 写成 allocation 或反之 ✓。 |
| ⑥ | 总判决 | **approve_exec_v0_4_to_lead** | 仅 Stage3 合成学习比较；不批真实数据/效果。 |

## 2. Lead M3 Stage3 合成学习比较执行批准文本（建议）

> **批准范围**：批准 R204-M3 **Stage3 合成学习比较执行**（支撑研究/机制账、compute-only、0 wells）；不批真实数据/湿实验/效果/药理/真实决策/迁移/机制/新颖性；不批代码晋升；不改旧判定/门槛；不恢复停止实验。
>
> **冻结**：35 文件链/Stage1/C209/Stage2/C213；seeds（env 20261601、feedback 20261601–10、evaluation 20261701–10、arms 20261611+10a+r、headroom 20261681–90；禁用集/overlap=[]/unique；两跑同 seeds 独立进程/逐字节/telemetry 分离）；R=10、每 replicate 300 共享反馈+300 评价、总3,000/3,000、7 arms 同 feedback/eval；**feedback seed=20261601+r；evaluation seed=20261701+r 独立；evaluation 300 units 固定顺序/canonical `"h,a\n"`/μ 精确；shared-score Q 公式/采样/support 写死；7 arms 全部固定 shared-score（无 optimal allocation arm）；per-arm `feedback_stream_sha`/`evaluation_stream_sha`/`allocation_policy_sha` 必须一致，否则 leakage/stop**；调参≤20/caps/合法包；primary candidate vs A_standard_DR_TMLE、δ=.05、mean≤−δ ∧ CI upper<0 ∧ Holm p<.05、family6；MDE .04798268/n_req278/cluster/headroom/6,282 仅 Fisher-z；G1–G6/13 失败/caps 1800s/2h/8GB/0 wells；schema 先写；final-implementation Stage3 pilot（2 reps×7 arms×300 units）实测冻结 canonical；JSON 无 telemetry；闭环成本同账；停止/边界；不执行真实数据/效果。
>
> **禁止**：真实数据/湿实验/效果/真实决策/药理/迁移/机制/新颖性；把 learner 比较写成 allocation 比较或反之；把 evaluation 共同样本写成任意 policy 的 population value；把 allocation/feedback 优势算进 primary；改旧判定/阈值/端点；放宽容差；晋升代码；恢复停止实验。

## 3. 声明

- **本轮不运行效果/训练/真实数据**：只读 M3 Stage3 v0.4 exec prereg/JSON/schema/Stage1/Stage2 链；只写本文件与 `tmp/`；未改 exec prereg 产物。
- **总判决：approve_exec_v0_4_to_lead**。evaluation seed/派生、shared-score Q/采样/support、sample_semantics/schema 三 SHA、toy canonical、35 链/Stage1/Stage2、seeds、R=10/300/300/3,000、7 纯 learner、primary/family6、MDE/n_req278/headroom/cluster/6,282、G1–G6/13/caps/schema/pilot/闭环/停止/边界均核验通过；仅 evaluation 共同样本解释、C_H 诊断、final pilot、toy 复算为非阻塞执行备注。仅批准 Stage3 合成学习比较执行（支撑研究/机制账、compute-only、0 wells）；不批真实数据/湿实验/效果/药理/真实决策/迁移/新颖性。

**一句话：v0.4 已写死 evaluation seed 20261701+r/300 units/canonical、shared-score Q 公式/采样/support、sample_semantics/schema 三 SHA，toy SHA 我复算一致；35 链/Stage1/Stage2、R=10/300/300/3,000、7 纯 learner、primary/family6、MDE/n_req278/headroom/cluster/6,282、G1–G6/13/caps/pilot/边界均通过——判 approve_exec_v0_4_to_lead（仅 M3 Stage3 合成学习比较执行：支撑研究/机制账、compute-only/0 wells；不批真实数据/湿实验/效果/药理/真实决策/迁移/新颖性）。**
