# Lead 批准：R204-M3 Stage3 合成学习比较执行（支撑研究/机制账；compute-only；0 wells）

2026-10-28。依据：R204-M3-S3.3-C1（i003）判 **approve_exec_v0_4_to_lead**；evaluation seed/派生、shared-score 分配公式、per-arm 三 SHA/16 字段、toy canonical、35 文件链/Stage1/Stage2、样本/预算/主端点/停止/边界均 PASS。

## 批准范围（仅 Stage3 合成学习比较执行一次）
- 批准 M3 Stage3 **合成学习比较执行**（支撑研究/机制账、compute-only、0 wells）；**不批真实数据/湿实验/效果/药理/真实决策/迁移/机制/新颖性**；不批代码晋升；不改旧判定/门槛；不恢复停止实验。
- 冻结 v0.4 链：PROBLEM_M3_S3_EXEC_v0_4 `EAB4E85D…`、DESIGN_M3_S3_EXEC_v0_4 `5C6CFF4A…`、exec_plan_m3_s3_v0_4.py `3338F70D…`、json `9FB57C5B…`、schema `3DEFD258…`、report `493E53A4…`、record `EEE5ED6B…`；执行前重核 35 文件 SHA（含 Stage1/Stage2），不匹配→`design_invalid: chain_mismatch`。
- seeds：env **20261601**、feedback **20261601+r**、evaluation **20261701+r**（独立）、arms **20261611+10a+r**、headroom **20261681–90**；与禁用集交集 []/unique；两跑同 seeds 独立进程、结果 JSON 逐字节、telemetry 单独；不得改 seed。
- 环境/样本：H=3/A=3/Y binary、p/μ/b/π2/m_wrong/C_H=20 冻结；R=10；每 replicate **300 共享反馈 (h,a,Y)+300 评价 units**；总 3,000/3,000；7 arms 全部固定 shared-score（无 optimal allocation arm）；primary candidate vs A_standard_DR_TMLE；δ=.05；mean ΔR≤−δ ∧ 95% CI upper<0 ∧ Holm p<.05；family=6；MDE .04798268/n_req278/headroom/cluster/6,282 仅 Fisher-z；次端点仅 secondary；不换端点。
- **evaluation stream**：seed=20261701+r；300 units 固定顺序（h_j→a_j 两随机数）、canonical `"h,a\n"`；evaluation utility 用 known-truth μ(h,a) 精确值（无噪声 Y）；评价不用于拟合/更新/选择；7 arms 复用同一评价流。
- **shared-score allocation**：Q=p(h)π2(a|h)^2[Var+(μ−m_wrong)^2]/b(a|h)、w=Q/Σ_legal Q、Var=μ(1−μ)；p/μ/b/π2/m_wrong/C_H=20/b_min=1e-6 取 Stage2 冻结；采样 h→a→Y 固定；support b>0/≥1e-6/Q finite；C_H 仅 H clipping 诊断、不用于 weights；unsupported→support/positivity；引用 Stage2/C213 `m3_stage2.json` 36C4DF12…/schema 0E46DEC0…。
- **per-arm 16 字段/三 SHA**：feedback_stream_sha/evaluation_stream_sha/allocation_policy_sha；7 arms 两 SHA 必须逐字节一致→`design_invalid: leakage`/stop；toy canonical 保持（`0696F595…`/`01063FFF…`/`6A976C3C…`）。
- G1–G6；13 失败类别（含 chain_mismatch）；caps 1800s/2h/8GB/0 wells；schema 先写；**final-implementation Stage3 pilot（2 reps×7 arms×300 units）实测并冻结 canonical**；JSON 无 telemetry；闭环成本同账。
- 非阻塞执行备注：evaluation action a_j~w 是 **shared-score 共同样本**，不是每个 arm 自己的 policy 样本；primary 结果应报告为**同一 held-out 评价样本上的共同样本诊断**，**不得写成任意 arm policy 的无偏 population policy value**；比较仍是配对/同评价；C_H 只用于 H clipping 诊断、不进入 allocation weights。

## 不批准
- 真实数据/湿实验；效果/真实决策/药理/迁移/机制/新颖性；把 learner 比较写成 allocation 比较或反之；把 evaluation 共同样本写成任意 policy 的 population value；把 allocation/feedback 优势算进 primary；改旧判定/阈值/端点/放宽容差；代码晋升；恢复停止实验。
