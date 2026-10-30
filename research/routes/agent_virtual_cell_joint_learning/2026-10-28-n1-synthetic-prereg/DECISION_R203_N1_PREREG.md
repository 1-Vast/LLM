# Lead 批准：N1 执行预注册（仅合成机制账；不批效果执行/外推）

2026-10-28。依据：R203-N1.3-C1（i003）判 **approve_n1_v0_4_to_lead**；V4 独立验证 PASS（独立 seed 20261062：mean ΔELPD 503.0425、SE 64.4214、95% CI[376.779,629.306]；gate mode=V4_independent）；首轮 FAIL/oracle/dev post-hoc 披露完整；代码残留修复；PROBLEM/DESIGN 披露；其余冻结 PASS。

## 批准范围（仅执行预注册冻结；不批效果执行）
- 批准 N1 执行预注册（**机制账、合成、compute-only、0 wells**），冻结 v0.4 链：
  PROBLEM_N1_v0_4 `5C513D94…FA0649A`；DESIGN_N1_v0_4 `94BAB805…7C029C`；generator_n1_v0_4.py `AA5D454A…EDCC97`；generator_n1_v0_4.json `35E41136…D610263`；V4_validation_v0_4.json `254BEBAB…DC8E2ECF`；timing_n1_pilot_v0_4.json `A4C7E0F6…5586C7`；report `C99A50D4…15CD04`；record `8CB2C1ED…6821B86`；usage `9CA4A321…FF380E2`。
- 冻结：n_units=300、MDE80=.04798、n_req278、δ=.05 paired held-out decision regret、U∈[0,1]、m=5、held-out 不更新；GT-static/nonstatic；V1–V4+`rename_static_Sadd`；**V4_MODEL_SPEC 运行前冻结（spec SHA A69B845D…）：static ridge 21 特征 λ=1e-2；nonstatic 33 特征、soft responsibilities、weighted ridge λ=1.0、forward posterior、init 1/S、无调参、T_hold=2**；**独立 seed=20261062/n=200 为唯一 V4 gate**（dev seed 20261061 的 306.1577 仅 post-hoc 诊断；oracle fallback seed=20261063 仅备用）；G1 point≤.05/.0488 且 Wilson upper≤.075/.05187；G2 powers 1.000；G3 full 143/600/rank140/nullity3（参数 gauge=3）；G4–G7；B1–B6 等预算+B2 等价审计；canonical pilot per-rep .05622s/projected main 25.3s/memory .037GB；caps 1800s/2h/8GB/0 wells；两跑/schema/无 telemetry；失败类别（rename_static_Sadd/generator_misspecified/calibration_failed/nonidentifiable/leakage/compute_budget_exceeded/unreachable_gate/precision_insufficient/no_increment/inconclusive）。

## 下一步（本批准后）
1. **仅批准实现+资格门阶段**：实现最终 generator + B1–B6/M 七方法（按冻结 spec）；跑 V1–V4（V4 用独立 seed 20261062 作 gate）、G1–G7、最终实现 pilot/G7、两跑逐字节；失败只写 `design_invalid` 不报效果。
2. **N1 效果执行（方法比较/regret 报告）须另立执行预注册 + 独立挑战 + Lead 批准**；本批准不包含效果执行。
3. 非阻塞执行备注：pilot 投影 .05622×375=21.08s vs timing 25.3s 需在实现记录写清 overhead/投影定义；V4_MODEL_SPEC 作为独立冻结字段引用并逐项实现（不得执行时改 λ/特征/初始化）；V4 唯一 gate=独立 seed20261062（dev/post-hoc/oracle fallback 不得替代）；执行前用最终实现重跑 G7 pilot 并冻结。

## 不批准
- 效果结论/外推、药理/真实决策/迁移/机制/新颖性；用 A/B 线资源；改旧门槛/旧判定；恢复已停止实验；晋升代码；在 V4/G1–G7 未 PASS 前报 regret；用 dev/post-hoc/oracle fallback 替代独立 V4 gate；同 seed 迭代到通过。
