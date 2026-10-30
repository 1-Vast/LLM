# R204-M3.1 轻量复核（task-161）：v0.2 决策反馈信用

2026-10-28。角色：同一独立挑战者（非提案者、未参与 M3、不运行效果/不拟合/不读真实响应）。对象：[PROBLEM_M3_v0_2.md](PROBLEM_M3_v0_2.md)（SHA `15DFE82C…`）、[DESIGN_M3_v0_2.md](DESIGN_M3_v0_2.md)（`033D67CB…`）、[formalism_M3_v0_2.py](formalism_M3_v0_2.py)（`3E709B81…`）、[formalism_M3_v0_2.json](formalism_M3_v0_2.json)（`299E5B03…`）、[schema_M3_v0_2.json](schema_M3_v0_2.json)（`E2E641BC…`）、[timing_M3_pilot_v0_2.json](timing_M3_pilot_v0_2.json)、report/record/usage v0.2、ERRATA。**只读；只写本文件与 `tmp/`。**

## 0. 结论先行

**总判决：approve_m3_stage1_v0_2_to_lead（仅批准 M3 Stage 1 合成实现：支撑研究、机制账、compute-only、0 wells；不批效果/真实决策/药理/Stage2–3）。**

v0.2 已修掉 v0.1 的三项：
- **标准基线补全**：`standard_baselines.baselines_required` 含 **optimal_experimental_design + decision_AL**；Stage2 arms=shared-score/random/GP/decision_AL/optimal_experimental_design/DR+MLE；Stage3 arms=candidate/full-history/IW/DR/TMLE/optimal_experimental_design/decision_AL；同信息/反馈/调参≤20/caps/合法实验包；等预算复制/超过→no_increment/撤 ✓。
- **失败类别补全**：failure 全集/schema/failure_template 含 **`design_invalid: nonidentifiable`**、**`design_invalid: two_run_mismatch`**；Stage1 共线/分离/无有限唯一 ε→nonidentifiable、两跑不一致→two_run_mismatch；失败只写类别 ✓。
- **Fisher-z 标注**：6,282.1038/1,572.7759 标 `non_integer=true/not_a_gate=true/not_paired_DR_formula=true/not_universal_decision_gate=true`；round 6282/1573、ceil 6283/1573；决策用 MDE .047982685/n_req278/headroom/cluster ✓。
- **保留项**：DR gap0；clipping bias −.026407185629；ε root −.562633036711、score≈0；共线 rank1；分配 full≥noise ratio 1.217/1.167；π=b→H=1；19 checks PASS；两跑 `299E5B03…` 逐字节；pilot .000150s/rep、wall .001503s；caps 1800s/2h/8GB/0 wells；JSON 无 telemetry ✓。
- **边界**：支撑研究/机制账 only；Stage1 不报效果；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定；不恢复停止实验；Stage1 执行另立预注册+挑战+Lead 批准；Stage2/3 data_unavailable；N1 no_increment 不作 M3 证据 ✓。

**结论：可提交 Lead 批准 M3 Stage 1 合成实现（支撑研究、机制账/compute-only/0 wells）。**

## 1. 逐条判决

| # | 项 | 判决 | 理由/证据 |
|---|---|---|---|
| ① | 标准基线/Stage2/3 arms | **PASS** | `baselines_required` 含 optimal_experimental_design/decision_AL；Stage2 6 arms、Stage3 7 arms 均含二者；同信息/反馈/调参≤20/caps/合法实验包；等预算复制/超过→no_increment/撤 ✓。 |
| ② | 失败类别补全 | **PASS** | failure 全集/schema/template 含 `design_invalid: nonidentifiable`、`design_invalid: two_run_mismatch`；Stage1 checks 写明对应触发；失败只写类别 ✓。 |
| ③ | Fisher-z 标注 | **PASS** | 6,282.1038/1,572.7759 标 non_integer/not_a_gate/not_paired_DR/not_universal；round 6282/1573、ceil 6283/1573；决策用 MDE .04798/n_req278/headroom/cluster ✓。 |
| ④ | 保留项/自检/两跑/pilot | **PASS** | DR gap0；bias −.026407185629；root −.562633036711；rank1；ratios 1.217/1.167；π=b；19 checks PASS；两跑 299E5B03；pilot .000150/.001503；caps；JSON 无 telemetry ✓。 |
| ⑤ | 边界 | **PASS** | 支撑研究/机制账；Stage1 不报效果；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定；不恢复停止实验；Stage1 执行另立预注册+挑战+Lead 批准；Stage2/3 data_unavailable；N1 no_increment 不作 M3 证据 ✓。 |
| ⑥ | 总判决 | **approve_m3_stage1_v0_2_to_lead** | 仅 Stage1 合成实现；不批效果/真实决策/药理/Stage2–3。 |

## 2. 非阻塞实现备注（写入执行记录；不改变批准范围）

1. **`failure_categories` 位置**：`formalism_M3_v0_2.json` 顶层无 `failure_categories` 键（在 `three_stage_plan.failure_categories`），但 `schema_M3_v0_2.json` 有顶层列表；执行实现应统一读取 schema 的 `failure_categories`/`failure_template`，避免顶层缺失导致漏路由。
2. **Fisher-z round/ceil**：`round_delta_0.10=1573`、`ceil_delta_0.10=1573` 相同；`delta_0.05` round 6282/ceil 6283 不同，属连续规划取整差异；仍只作 Fisher-z 参考，不能进入 M3 decision/MDE。
3. **Pilot**：`.000150s/rep、wall .001503s` 远低 caps；执行前用最终实现重跑并冻结 canonical timing；两跑结果 JSON 逐字节。
4. **Stage1 实现**：按 schema 的 19 checks / S1-a–e / DR/clipping/root/collinearity/allocation/π=b 逐项实现；失败只写类别（nonidentifiable/two_run_mismatch 等），不报效果；目标样本不作标签、评价样本独立、propensity/支持/截断规则冻结。
5. **边界**：Stage2/3 不执行；真实数据 data_unavailable；不称药理/真实决策/迁移/机制/新颖性；N1 no_increment 不作 M3 证据；M2/M1 不混同。

## 3. Lead M3 Stage1 合成实现批准文本（建议）

> **批准范围**：批准 R204-M3 **Stage 1 合成实现**（支撑研究、仅机制账、compute-only、0 new wells）；不批准效果/真实决策/药理/迁移/机制/新颖性；不批准 Stage2/3 真实数据执行；不批代码晋升；不改旧判定/门槛；不恢复停止实验。
>
> **冻结**：一步 DR `H_k=π_k/b`、`δ_k`、`V_k`；评价样本独立；更新 `logit m_{θ,ε}=logit mθ+Σε_kH_k`；概率/权重截断 C；共线/分离/无支持→nonidentifiable；只更新功能均值≠细胞动力学；无完整序贯历史/propensity/删失不称序贯 DR；分配二阶项 `Σπ_k²[Var+(E−m)²]/b`、错设不能只按 Var；π=b→H=1；DR gap0；clip bias −.026407185629；ε root −.562633036711；rank1；ratios1.217/1.167；19 checks；MDE .047982685/n_req278/headroom/cluster；6,282 仅 Fisher-z（non_integer/not_a_gate/not_paired_DR）；标准基线含 **optimal_experimental_design/decision_AL**（同信息/反馈/调参≤20/caps/合法实验包）；失败类别含 nonidentifiable/two_run_mismatch；caps 1800s/2h/8GB/0 wells；两跑/schema/无 telemetry；Stage1 只做诊断、不报效果/增益。
>
> **禁止**：Stage2/3 真实数据/湿实验；效果/真实决策/药理/迁移/新颖性；把标准 DR/TMLE+最优分配等价写成 M3 增量；把功能头校准升级为细胞规律；改公式/阈值/端点救结果；晋升代码；改旧判定；恢复停止实验。

## 4. 声明

- **本轮不运行效果/不拟合/不读真实响应**：只读 M3 v0.2 预注册/formalism JSON/schema/timing/report；只写本文件与 `tmp/`；未改 M3 产物。
- **总判决：approve_m3_stage1_v0_2_to_lead**。标准基线/Stage2-3 arms、失败类别 nonidentifiable/two_run_mismatch、Fisher-z 标注、保留项/两跑/pilot/边界均核验通过；仅 failure_categories 位置、Fisher-z 取整、pilot 重跑、Stage1 实现细节为非阻塞执行备注。仅批准 Stage1 合成实现（支撑研究、机制账/compute-only/0 wells）；不批效果/真实决策/药理/Stage2–3。

**一句话：v0.2 已把 optimal_experimental_design/decision_AL 加入 baselines_required/Stage2-3 arms，补 nonidentifiable/two_run_mismatch 失败类别，并把 6,282.1038/1,572.7759 标为 Fisher-z 连续参考（round/ceil，非 gate/非 paired DR）；DR/clipping/root/rank/ratios/π=b/MDE/两跑/pilot/边界保留——判 approve_m3_stage1_v0_2_to_lead（仅 M3 Stage1 合成实现：支撑研究、机制账/compute-only/0 wells；不批效果/真实决策/药理/Stage2–3）。**
