# R204-M3 Stage2 合成执行预注册独立挑战（task-175）

2026-10-28。角色：同一独立挑战者（非提案者、未参与 M3、不运行效果/训练/真实数据）。对象：[PROBLEM_M3_S2_EXEC.md](PROBLEM_M3_S2_EXEC.md)（SHA `4690A50A…`）、[DESIGN_M3_S2_EXEC.md](DESIGN_M3_S2_EXEC.md)（`AD18DC25…`）、[exec_plan_m3_s2.py](exec_plan_m3_s2.py)（`83EFB2CD…`）、[exec_plan_m3_s2.json](exec_plan_m3_s2.json)（`92D00E0C…`）、[schema_m3_s2_exec.json](schema_m3_s2_exec.json)（`A0A43078…`）、report/record/usage、M3 v0.2/Stage1 C209/Lead 决定。**只读；只写本文件与 `tmp/`。**

## 0. 结论先行

**总判决：revise（不能 approve_exec_to_lead；也不是 stop）。**

核验 PASS：
- **链/Stage1**：17/17 SHA 匹配；`chain_pass=true/mismatches={}`；Stage1 `failed_checks=[]`、`all_checks_pass=true`、`check19_pass=true`、`no_effect_results=true`；M3 v0.2 八件 + Lead 决定 `9743CF2E…` + Stage1 八件 ✓。
- **seeds/两跑**：data **20261401**、6 arms **20261410–15**、two-run reps **20261420–29**；与 M3 Stage1 20261200、M1 Stage1 20261112/13、M1 v0.2 20261201–03、M1 Stage2 20261301–49、M2 Stage2 20261200–39、M2 Stage3 20262100–39、N1 20261030/61/62/63 交集 **[]**；两跑同 seeds 独立进程/逐字节/telemetry 分离 ✓。
- **Stage2 环境**：一步 DR H=3/A=3/Y∈{0,1}；p(h)=[.3,.4,.3]、μ/b 冻结、π1 确定性置换、π2 混合、m_true=μ/m_wrong=.5、C_H=20；H_k/δ/V/score-tilt/allocation-Q 冻结；诊断用例（正/零支持/截断/共线/分离/π=b）；评价独立/target 不作标签/分配不复用评价；六 arms 同 learner/updater 仅分配；同预算；不输出 decision utility/regret/top-k/学习效果比较 ✓。
- **G1–G6/停止**：G1 support/positivity、G2 截断、G3 分配二阶项、G4 无泄漏、G5 两跑、G6 schema/预算；caps 1800s/2h/8GB/0 wells；pilot Stage1 参考 .00016347/.001635/.007137；schema 先写；单测 DR gap0/clipping bias −.026407185629/rank1/π=b H−1 0/ratios 1.217/1.167/六 arms/overlap=[] ✓。
- **边界**：支撑研究/机制账；只更新功能均值≠细胞动力学；无序贯→不称序贯 DR；不执行 Stage3/真实数据/湿实验；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定；M3 不与 M1/M2 混同；N1 不作 M3 证据；data readiness open ✓。

**但机器可读预注册仍有两个阻断：**
1. **失败类别 12 项，不是任务要求的 13 项**：`failure_categories` 缺 **`design_invalid: chain_mismatch`**（`stop_boundaries` 里有 chain mismatch，但 failure list/schema 没有）；任务 ④ 明确 13 项完整。需补全并同步 schema/失败模板。
2. **“六 arms 分配诊断”没有 per-arm 输出/端点/schema**：`stage2.arms` 只登记 arm 元数据；`schema` 的 `arm_fields` 只有 `arm_id/role/allocation_rule/same_budget_audit`，`checks_fields` 只有 DR identity/clipping/collinear/π=b/ratios/two-run/budget；**没有任何 per-arm 分配诊断输出**（如 allocation weights、H/δ、allocation-Q/variance、clipping count、equal-budget audit），也没有“六 arms 何时算通过/失败”的判据。Stage2 名为“仅分配比较”，但 schema 无法承载分配比较结果；执行者只能跑 checks，六 arms 实际不可判。

**结论：先修 §2 的 1–3，再提交 Lead 批准 M3 Stage2 合成分配诊断执行（支撑研究/机制账、compute-only、0 wells）。**

## 1. 逐条判决

| # | 项 | 判决 | 理由/证据 |
|---|---|---|---|
| ① | 链/Stage1 | **PASS** | 17/17 SHA；mismatches={}；Stage1 failed_checks=[]/all_checks_pass/check19/no_effect ✓。 |
| ② | seeds/两跑 | **PASS** | data 20261401/arms 20261410–15/reps 20261420–29；禁用集交集[]/unique；两跑同 seeds 独立进程/逐字节/telemetry ✓。 |
| ③ | Stage2 环境/六 arms | **FAIL/PARTIAL** | H=3/A=3/Y binary；p/μ/b/π/m/C_H 冻结；六 arms 含 decision_AL/optimal design；同 learner/updater/预算；不输出 effect ✓。**但 schema 无 per-arm 分配诊断输出/通过判据**（§0-2）。 |
| ④ | G1–G6/失败/预算 | **FAIL/PARTIAL** | G1–G6 规则/失败映射写清；caps/schema/单测/pilot 参考 ✓。**failure list 12 项，缺 chain_mismatch（应13）**（§0-1）。 |
| ⑤ | 停止/边界 | **PASS** | π=b 退化/共线/分离/支持/截断/评价复用/两跑/链/预算按类别；不放宽/改阈值/换端点；只更新功能均值≠细胞动力学；无序贯不称序贯 DR；支撑研究/机制账；不执行 Stage3/真实数据；边界 ✓。 |
| ⑥ | 总判决 | **revise** | 见 §2。 |

## 2. 必改（≤5）

1. **补 `design_invalid: chain_mismatch`**：加入 `failure_categories`、schema 失败模板/stop 映射；使 13 项完整（support/positivity/propensity/leakage/calibration/compute_budget_exceeded/nonidentifiable/two_run_mismatch/**chain_mismatch**/unreachable_gate/precision_insufficient/no_increment/inconclusive）；与 stop_boundaries 的 chain 一致。
2. **定义 per-arm Stage2 分配诊断输出/判据**：在 schema 增加 `per_arm`/`arm_result` 字段（至少：arm_id、allocation_weights、H/δ 摘要、allocation-Q 或 variance、clipping count/bias bound、equal-budget audit、two-run SHA、pass/fail）；明确六 arms 的“仅分配诊断”输出口径（**不输出 decision utility/regret/top-k/学习效果比较**），并写明通过/失败类别（G1–G6/13 类）。若 Stage2 只是 contract-check、不做分配比较，则应删掉“六 arms 分配诊断”与“同 learner 仅分配”的表述，改为“环境/合同检查”。
3. **冻结 Stage2 的 replicate/sample 语义**：明确 data seed 20261401 对应多少个 contexts/units/replicates（当前只有 R=10 reps 与 H=3/A=3/Y binary；无 n/units/重复结构）；固定每 arm 的 R/分配次数与 equal-budget 账；执行前最终实现 pilot 实测并冻结 canonical（不能只引用 Stage1 pilot .00016347/.001635/.007137）。
4. **保持**：17 文件链/Stage1、独立 seeds/两跑、H=3/A=3/Y binary、p/μ/b/π/m/C_H、六 arms（含 decision_AL/optimal design）、G1–G6、caps 1800s/2h/8GB/0 wells、schema 先写、无 telemetry、单测算术、π=b/截断/共线/分离/支持规则、边界；不执行效果/Stage3/真实数据。
5. **禁止**：把 Stage2 分配诊断写成 Stage3 效果/学习比较；把 per-arm 输出做成 decision utility/regret/top-k；改旧判定/阈值；放宽容差；晋升代码；真实数据/湿实验。

## 3. 修完后建议的 Lead M3 Stage2 合成分配诊断执行批准文本（支撑研究/机制账、compute-only、0 wells）

> **批准范围**：在必改 1–3 完成并复核后，批准 **M3 Stage2 合成分配诊断执行**（支撑研究/机制账、compute-only、0 wells）；不批 Stage3/真实数据/湿实验/效果/药理/真实决策/迁移/机制/新颖性；不批代码晋升；不改旧判定/门槛；不恢复停止实验。
>
> **冻结**：17 文件链/Stage1（failed_checks=[]/all_checks_pass/check19/no_effect）；seeds（data 20261401、arms 20261410–15、reps 20261420–29；禁用集交集[]/unique；两跑同 seeds 独立进程/逐字节/telemetry 分离）；Stage2 环境 H=3/A=3/Y∈{0,1}、p/μ/b/π/m/C_H=20、六 arms（含 decision_AL/optimal design）、同 learner/updater/预算；G1–G6；per-arm 分配诊断字段/判据；13 失败类别（含 chain_mismatch）；caps 1800s/2h/8GB/0 wells；schema 先写；最终实现 pilot 实测冻结；JSON 无 telemetry；π=b/截断/共线/分离/支持规则；不输出 decision utility/regret/top-k/学习效果比较。
>
> **禁止**：Stage3/真实数据/湿实验/效果/真实决策/迁移/机制/新颖性；把分配诊断写成学习效果比较；把标准 DR/TMLE+最优分配等预算复制/超过写成本轮结论（留 Stage3）；改公式/阈值/端点救结果；晋升代码；改旧判定；恢复停止实验。

## 4. 声明

- **本轮不运行效果/训练/真实数据**：只读 M3 Stage2 exec prereg/JSON/schema/Stage1 链；只写本文件与 `tmp/`；未改 exec prereg 产物。
- **总判决：revise**。17 文件链/Stage1、独立 seeds/两跑、DR 环境/六 arms、G1–G6/停止/边界基本正确；但 **failure list 缺 chain_mismatch（12 vs13）**、**六 arms 无 per-arm 分配诊断输出/判据/schema**、**Stage2 replicate 语义与 final pilot 未冻结**。修完 1–3 后可提交 Lead 批准 M3 Stage2 合成分配诊断执行（支撑研究/机制账、compute-only、0 wells；不批 Stage3/真实数据/效果/药理）。

**一句话：M3 Stage2 exec 预注册的 17 文件链/Stage1、seeds、H=3/A=3 一步 DR 环境、六 arms（含 decision_AL/optimal design）、G1–G6/caps/边界都核验通过；但 failure list 只有12项缺 chain_mismatch、schema 没有 per-arm 分配诊断输出/判据、Stage2 replicate 语义与 final pilot 未冻结——判 revise：补 chain_mismatch、定义 per-arm 分配诊断字段/判据、冻结 replicate/pilot，再提交 Lead 批准 M3 Stage2 合成分配诊断执行。**
