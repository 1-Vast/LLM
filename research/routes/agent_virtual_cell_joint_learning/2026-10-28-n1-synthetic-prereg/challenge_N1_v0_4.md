# R203-N1.3 最终确认（task-138）：v0.4 修正预注册

2026-10-28。角色：同一独立挑战者（非提案者、未参与 N1、不运行效果结论/不拟合/不读 O'Neil）。对象：[PROBLEM_N1_v0_4.md](PROBLEM_N1_v0_4.md)（SHA `5C513D94…`）、[DESIGN_N1_v0_4.md](DESIGN_N1_v0_4.md)（`94BAB805…`）、[generator_n1_v0_4.py](generator_n1_v0_4.py)（`AA5D454A…`）、[generator_n1_v0_4.json](generator_n1_v0_4.json)（`35E41136…`）、[V4_validation_v0_4.json](V4_validation_v0_4.json)（`254BEBAB…`）、[timing_n1_pilot_v0_4.json](timing_n1_pilot_v0_4.json)（`A4C7E0F6…`）、report/record/usage v0.4、R203-P1 链。**只读；只写本文件与 `tmp/`。**

## 0. 结论先行

**总判决：approve_n1_v0_4_to_lead（仅批准 N1 执行预注册：合成机制账、compute-only、0 wells；不批效果外推/药理/真实决策/迁移/新颖性）。**

v0.4 已修掉 v0.3 的三项阻断：
- **V4 独立验证 PASS**：`V4_MODEL_SPEC` 运行前冻结（spec SHA `A69B845D…`）；static ridge 21 特征 λ=1e-2 vs nonstatic 33 特征、soft responsibilities 权重、weighted ridge λ=1.0、forward posterior、init 1/S、无调参、T_hold=2；**独立 seed=20261062、n=200 新样本**：mean **503.0425**、SE **64.4214**、95% CI **[376.779, 629.306]**，mean>0、mean≥2SE（503.04≥128.84）、CI lower>0 → PASS；gate mode=`V4_independent`。
- **首轮/开发披露**：首轮 FAIL **−456.6**（等权 filter）、oracle 诊断 **+4147.6**、dev seed=20261061 的 **306.1577** 明确标为 **post-hoc 诊断，不作 gate**；独立 seed=20261062 为 gate；fallback oracle seed=20261063（4988.236/248.226/[4501.72,5474.75]）仅备用；失败→rename_static_Sadd；无同 seed post-hoc 作 gate/迭代到通过。
- **代码残留修复**：`generator_n1_v0_4.py` 注释/摘要为 full 143/600（h72）；grep 无 359/288 作为 full 摘要；129 仅在明确 v0.1 历史算术上下文；与 §3/JSON 一致。
- **披露完整**：PROBLEM §4/DESIGN §4 写首轮 FAIL、oracle、filter 改动、post-hoc 性质、独立 PASS 数字；不是只写最终 PASS。
- **其余冻结**：n_units=300/MDE .04798/n_req278；G1 .0488/.05187；G2 1.000；G3 full 143/600/rank140/nullity3；B1–B6；B2 审计 PASS；caps 1800s/2h/8GB/0 wells；final-implementation pilot .05622 s/rep、main 25.3 s、memory .037 GB（逐方法一致）；两跑/schema/失败类别/边界不变。

**结论：可提交 Lead 批准 N1 执行预注册（合成机制账、compute-only、0 wells；不批效果/药理）。**

## 1. 逐条判决

| # | 项 | 判决 | 证据/理由 |
|---|---|---|---|
| ① | V4 独立 gate/披露 | **PASS** | spec SHA A69B845D；static 21/λ1e-2 vs nonstatic33 soft-responsibility/weighted ridge λ1.0/forward/init1/S/no tuning/T2；独立 seed20261062 n200：503.0425/64.4214/[376.779,629.306] PASS；首轮 −456.6、oracle +4147.6、dev 306.1577 post-hoc 不作 gate；fallback oracle seed20261063 4988.236/248.226/[4501.72,5474.75]；失败→rename_static_Sadd ✓。 |
| ② | 代码残留 | **PASS** | `generator_n1_v0_4.py` 注释/摘要 full 143/600（h72）；grep 无 359/288 作为 full 摘要；129 仅在 v0.1 历史算术上下文；文档/JSON 一致 ✓。 |
| ③ | PROBLEM/DESIGN 披露 | **PASS** | 两处 V4 节均含首轮 FAIL −456.6、oracle +4147.6、等权→soft-responsibility/weighted ridge、规则/阈值/seed/n_rep/held-out 未改但模型实现改变、dev 306.1577 post-hoc、独立 seed20261062 PASS 作 gate ✓。 |
| ④ | 其余冻结 | **PASS** | n_units=300/MDE .04798/n_req278；G1 .0488/.05187；G2 1.000；G3 full 143/600/140/3；B1–B6；B2 审计 PASS；caps 1800s/2h/8GB/0 wells；两跑/schema/失败类别/边界不变 ✓。 |
| ⑤ | 最终 pilot | **PASS（附非阻塞算术备注）** | `.05622 s/rep、main 25.3 s、memory .037 GB`；逐方法 B1 .00376/B2 .00254/B3 .00251/B4 .03587/B5 .00038/B6 .00275/M .00841；B2 审计 PASS；G7 ≤caps ✓。注意 `.05622×375=21.08` 与 projected 25.3 有约20%差（可能 overhead），文档未说明；不影响 caps/批准，建议注明。 |
| ⑥ | 总判决 | **approve_n1_v0_4_to_lead** | 仅 N1 执行预注册；效果执行另批。 |

## 2. 非阻塞实现备注（写入执行记录；不改变批准范围）

1. **Pilot 投影算术**：`per_replicate_total .05622 s × scale_factor375 = 21.08 s`，但 `main_projection.projected_wall_seconds=25.3`；约20% overhead/取整未在 timing JSON 说明。**G7 仍远低于 caps（25.3≪1800），不影响批准**；执行记录应写清 overhead/投影定义，避免 G7 数字不可复算。
2. **V4_MODEL_SPEC 归档**：spec SHA `A69B845D…` 已嵌在 `V4_validation_v0_4.json → model_spec`；建议执行预注册把该 spec 作为独立冻结文件/字段引用（含 static 21 特征/λ1e-2、nonstatic33/soft responsibilities/λ1.0/forward/init/no tuning/T2），以便执行者逐项实现；不得执行时再改 λ/特征/初始化。
3. **V4 唯一 gate 口径**：`V4_independent`（seed20261062）是唯一 gate；dev seed20261061 的 306.1577 仅 post-hoc；oracle seed20261063 仅 fallback；不得把 dev/post-hoc PASS 当 gate，不得同 seed 迭代。
4. **最终实现 pilot**：执行前用最终实现重跑 G7 pilot 并冻结；当前 v0.4 telemetry 只作预注册预算证据；caps 1800s/2h/8GB/0 wells 不变。
5. **执行边界**：N1 执行预注册仍只批机制账；不批效果/药理/真实决策/迁移/新颖性；不晋升代码；不改旧门槛/判定；不恢复停止实验；N1 效果执行须另立预注册+独立挑战+Lead 批准。

## 3. Lead N1 执行预注册批准文本（建议）

> **批准范围**：批准 R203-N1 **执行预注册**（机制账、合成、compute-only、0 new wells）；不批准效果结论/外推、不批准药理/真实决策/迁移/机制/新颖性；N1 效果执行本身须另立预注册+独立挑战+Lead 批准。
>
> **冻结**：n_units=300；MDE80=2.801585·SD/√n_eff（n_eff=136.36；SD .20→.04798≤.05；n_req278≤300）；δ=.05 paired held-out regret `D_i=R_i(M)−R_i(B2)`；U∈[0,1]；m=5；held-out 不更新；GT-static/nonstatic；V1–V4+`rename_static_Sadd`；**V4_MODEL_SPEC（static 21 特征 λ1e-2；nonstatic 33 特征/soft responsibilities/weighted ridge λ1.0/forward/init 1/S/no tuning/T_hold=2）运行前冻结；独立 seed=20261062/n=200 为唯一 gate，dev 20261061 306.1577 仅 post-hoc，oracle 20261063 仅 fallback**；G1–G7（G1 .0488/.05187；G2 1.000；G3 full 143/600/rank140/nullity3；G4–G7）；B1–B6 等预算+B2 等价审计；最终实现 pilot（.05622s/rep、25.3s main、.037GB；caps 1800s/2h/8GB/0 wells）；两跑逐字节/schema/无 telemetry；失败类别统一。
>
> **禁止**：效果外推/药理/真实决策/迁移/新颖性；用 A/B 资源；改旧门槛/判定；恢复停止实验；晋升代码；在 V4 独立验证/G1–G7 未 PASS 前报 regret；用 dev/post-hoc 306.16 或 oracle fallback 替代独立 V4 gate；N1 效果执行在本批准之外。

## 4. 声明

- **本轮不运行效果结论/不拟合/不读 O'Neil**：只读 N1 v0.4 预注册/代码/V4 validation/pilot 与 report/record；只写本文件与 `tmp/`；未改 N1 产物。
- **总判决：approve_n1_v0_4_to_lead**。V4 已按独立 seed=20261062 新样本 PASS（503.04/64.42/[376.78,629.31]），首轮 FAIL/oracle/dev post-hoc 已披露；代码/文档维数一致；n_units/MDE/G1/G2/G3/B1–B6/B2/caps 冻结；仅 pilot 投影 .05622×375=21.08 vs25.3 需在执行记录注明 overhead（非阻塞）。仅批准 N1 执行预注册（机制账、0 wells）；不批效果/药理/真实决策/迁移/新颖性。

**一句话：v0.4 用运行前冻结的 V4_MODEL_SPEC 在独立 seed=20261062/新样本上得到 503.04/64.42/[376.78,629.31] PASS，首轮 −456.6/oracle +4147.6/dev 306.16 post-hoc 均已披露且 dev 不作 gate；代码无 359/288 残留、PROBLEM/DESIGN 披露完整、n_units/MDE/G1/G2/G3/B1–B6/B2/caps 冻结——判 approve_n1_v0_4_to_lead（仅 N1 执行预注册：合成机制账、compute-only、0 wells；不批效果/药理/真实决策/迁移/新颖性）。**
