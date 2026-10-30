# R204-M3-P1 独立挑战（task-159）：决策反馈信用 DR/TMLE 支撑预注册

2026-10-28。角色：同一独立挑战者（非提案者、未参与 M3、不运行效果/不拟合/不读真实响应）。对象：[PROBLEM_M3.md](PROBLEM_M3.md)（SHA `EDC66222…`）、[DESIGN_M3.md](DESIGN_M3.md)（`D839DACD…`）、[formalism_M3.py](formalism_M3.py)（`F578180A…`）、[formalism_M3.json](formalism_M3.json)（`2256BDA2…`）、[schema_M3.json](schema_M3.json)（`10A8814B…`）、[report_M3.md](report_M3.md)（`946B4533…`）、[record_M3.md](record_M3.md)（`99DB7D88…`）、R204 BRIEF/report、ERRATA C197/C199/C201/C207、R203-P1 链。**只读；只写本文件与 `tmp/`。**

## 0. 结论先行

**总判决：revise（不能 approve_m3_stage1_to_lead；也不是 stop）。**

M3 的一步 DR 形式化与全部形式化算术核验通过：DR 恒等 gap 0.0；零支持未识别；截断 bias −.026407185629（max raw H=167、cap20）；score-tilt ε root −.562633036711、score≈0；共线 rank1；分配 full≥noise ratio 1.217/1.167；π=b→H=1；MDE .047982685/n_req278；6,282.10/1,572.78 仅 Fisher-z；两跑、pilot/caps 均一致。**但机器可读 JSON/schema 与 DESIGN 不一致**：
- **DESIGN/PROBLEM 的标准基线包含“最优实验设计/决策 AL”**（DESIGN §3 表），**JSON `standard_baselines.baselines_required` 没有这两项**，Stage2/3 arms 也不完整；M3 的分配主张与最优实验设计/决策 AL 直接重叠，**必须显式列入同预算强基线，否则 `no_increment`/撤主张无法判定**。
- **Stage1 检查使用 `nonidentifiable`**，但 **失败类别全集/schema 缺 `design_invalid: nonidentifiable`**；两跑要求也缺 `design_invalid: two_run_mismatch`。**检查/失败模板不一致**。
- 另有小项：Fisher-z `N_req=6,282.1038/1,572.7759` 为非整数规划参考（仅 Fisher-z，不是决策门/paired DR 公式），应在 schema/report 标注 round/ceil 与“非 gate”；不影响 MDE .04798/n_req278 的决策规划。

**结论：先修 §2 的 1–2，再提交 Lead 批准 M3 Stage1 合成实现（支撑研究、机制账/compute-only/0 wells）。**

## 1. 逐条判决

| # | 项 | 判决 | 理由/证据 |
|---|---|---|---|
| ① | 一步 DR 形式化 | **PASS** | `H_k=π_k/b`；`δ_k=E[H_k(Y−mθ)]`；`V_k=E_hΣπ_k mθ+δ_k`；评价样本独立；标准 DR/重要性校正、不称新；更新 `logit m_{θ,ε}=logit mθ+Σε_kH_k`；概率/权重截断；共线/分离/无支持→nonidentifiable；只更新功能均值≠细胞动力学；无完整序贯历史/propensity/删失不称序贯 DR ✓。 |
| ② | 分配二阶项 | **PASS** | `Σπ_k²[Var+(E−mθ)²]/b`；冻结 m 下 full/noise；错设不能只按 Var，须估计/保守界；支持/概率下限/极端权重规则 ✓。 |
| ③ | 形式化检查算术 | **PASS** | DR max gap 0.0（true/wrong m，π1/π2）；零支持未识别；截断 bias **−.026407185629**（max raw H=167、cap20、1 clipped）；ε root **−.562633036711**、score≈0、score@0=−.18；共线 rank1；分配 ratios **1.217228464/1.166867632**；π=b→H=1；n300/deff2.2/n_eff136.36/MDE **.047982685**/n_req278；6,282.1038/1,572.7759 仅 Fisher-z；两跑 2256BDA2；pilot .000174；caps ✓。 |
| ④ | 标准基线/边界 | **FAIL/PARTIAL** | DESIGN §3 表有**最优实验设计/决策 AL**、DR/TMLE、IW、value-aware、层级 GP、BATCHIE；但 JSON `standard_baselines.baselines_required` **缺最优实验设计/决策 AL**；Stage2 arms 有 decision-AL/DR+MLE 但**无显式 optimal design**，Stage3 arms 无 optimal/AL。分配主张与这些基线直接重叠，**必须显式同预算比较**。 |
| ⑤ | 三阶段 | **PASS** | Stage1 一步合成已知真值（DR/截断/低支持/错设/共线；无方法比较/增益）；Stage2 固定更新器比较分配（shared-score vs random/GP/决策 AL/DR+MLE）；Stage3 固定反馈比较学习+闭环成本（candidate vs 全历史/IW/DR/TMLE；主端点 δ=.05/headroom/MDE/cluster/6,282 仅 Fisher-z；次端点 secondary）✓。 |
| ⑥ | 失败/停止/预算/数据 | **FAIL/PARTIAL** | 类别含 support/positivity/propensity/leakage/calibration/compute_budget_exceeded、unreachable_gate/precision_insufficient/no_increment/inconclusive；**缺 `design_invalid: nonidentifiable`**（Stage1 共线/分离检查使用该词）与 **`design_invalid: two_run_mismatch`**（两跑要求）；停止/预算 1800s/2h/8GB/0 wells/data_unavailable 写清 ✓。 |
| ⑦ | 边界 | **PASS** | 支撑研究/机制账 only；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定；不恢复停止实验；执行另立预注册+挑战+Lead 批准；N1 no_increment 不作 M3 证据 ✓。 |
| ⑧ | 总判决 | **revise** | 见 §2。 |

## 2. 必改（≤5）

1. **补齐标准基线**：在 `formalism_M3.json → standard_baselines.baselines_required`、`schema_M3.json`、Stage2/3 arms 中加入 **`optimal_experimental_design`** 与 **`decision_AL`**（若已含 decision AL，补 optimal design；二者均同信息/同反馈/调参≤20/caps/合法实验包）；明确标准 DR/TMLE+最优分配等预算复制/超过→`no_increment`/撤。DESIGN §3 已有文字，JSON/schema 必须同步，否则机器执行会漏掉核心强基线。
2. **补齐失败类别**：在 failure category 全集/schema/失败模板加入 **`design_invalid: nonidentifiable`** 与 **`design_invalid: two_run_mismatch`**；Stage1 共线/分离/无有限解、两跑不一致时写入对应类别；不报效果。
3. **Fisher-z 规划值标注**：6,282.1038/1,572.7759 为连续规划参考；在 schema/report 明确 “only Fisher-z, non-integer planning, not universal decision gate, not paired DR formula”，决策仍用 MDE .04798/n_req278/headroom/cluster；不要把它当 M3 的样本量公式。
4. **保持其余冻结**：DR/截断/ε root/共线/分配二阶项/π=b/两跑/pilot/caps；Section 1 形式化/更新/边界；三阶段；data_unavailable；支撑研究/机制账；N1 no_increment 不作 M3 证据；不改旧判定/门槛。

## 3. 修完后建议的 Lead M3 Stage1 批准文本（支撑研究、仅机制账/compute-only/0 wells）

> **批准范围**：在必改 1–2 完成并复核后，批准 **M3 Stage 1 合成实现**（支撑研究、仅机制账、compute-only、0 new wells）；不批准效果/真实决策/药理/迁移/机制/新颖性；不批准 Stage2/3 真实数据执行；不批代码晋升；不改旧判定/门槛；不恢复停止实验。
>
> **冻结**：一步 DR `H_k=π_k/b`、`δ_k`、`V_k`、评价样本独立；更新 `logit m_{θ,ε}=logit mθ+Σε_kH_k`；概率/权重截断 C 预注册；共线/分离/无支持→nonidentifiable；只更新功能均值≠细胞动力学；无完整序贯历史/propensity/删失不称序贯 DR；分配二阶项 `Σπ_k²[Var+(E−m)²]/b`、错设不能只按 Var；π=b→H=1 退化；DR gap0/clip bias −.026407/root −.562633/rank1/ratios1.217/1.167；MDE .04798/n_req278/headroom；6,282 仅 Fisher-z；**B1–B5/标准基线（含 optimal design/decision AL）同预算**；失败类别（含 nonidentifiable/two_run_mismatch）；caps 1800s/2h/8GB/0 wells；两跑/schema/无 telemetry；Stage1 只做诊断、不报效果/增益。
>
> **禁止**：Stage2/3 真实数据/湿实验；效果/真实决策/药理/迁移/新颖性；把标准 DR/TMLE+最优分配等价写成 M3 增量；把功能头校准升级为细胞规律；改公式/阈值/端点救结果；晋升代码；改旧判定；恢复停止实验。

## 4. 声明

- **本轮不运行效果/不拟合/不读真实响应**：只读 M3 预注册/formalism JSON/schema/report；只写本文件与 `tmp/`；未改 M3 产物。
- **总判决：revise**。DR 形式化/更新/截断/共线/分配/π=b/MDE/两跑/pilot 全部核验通过；但 **JSON/schema 标准基线漏 optimal design/decision AL、失败类别漏 nonidentifiable/two_run_mismatch、Fisher-z 连续值需标注**。修完 1–2 后可提交 Lead 批准 M3 Stage1 合成实现（支撑研究、机制账/compute-only/0 wells；不批效果/真实决策/药理/Stage2–3）。

**一句话：M3 的 DR 恒等 0.0、截断 bias −.026407、ε root −.562633、共线 rank1、分配 ratio1.217/1.167、π=b→H=1、MDE .04798/n_req278/6,282 仅 Fisher-z 都正确；但 JSON `standard_baselines` 漏 optimal design/decision AL、失败类别漏 nonidentifiable/two_run_mismatch——判 revise：补齐基线与失败类别、标注 Fisher-z 非整数仅参考，再提交 Lead 批准 Stage1 合成实现（支撑研究/机制账/compute-only/0 wells）。**
