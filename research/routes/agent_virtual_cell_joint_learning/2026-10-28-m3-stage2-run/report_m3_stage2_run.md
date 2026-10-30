# report_m3_stage2_run —— R204-M3 Stage2 合成分配诊断执行报告（支撑研究；不报效果）

2026-10-28 · 角色：ON1/ON2/ON3/D1/D3/D5/A/B 线同一独立审计/实现者（endpoint-auditor）。
**状态：Stage2 合成分配诊断执行一次完成；支撑研究/机制账 only；compute-only；0 wells；不报 decision utility/regret/top-k/学习效果比较；Stage3/真实数据/湿实验未执行；不称药理/真实决策/迁移/机制/新颖性。**

依据：Lead `DECISION_R204_M3_S2_EXEC.md`；冻结 v0.2 链（17 文件 + Lead 决定）；M3 Stage1/C209；ERRATA C197/C199/C201/C207/C209/C210。

## 1. 链核验

- 17 文件 SHA + Lead 决定 **全部实算 match**；`chain_ok=True`；无 `design_invalid: chain_mismatch`。
- Stage1 状态：failed_checks=[]、all_checks_pass=true、check19_pass=true、no_effect_results=true。

## 2. 执行前 final-implementation pilot（canonical）

- **2 reps × 6 arms × 300 alloc**；**Stage1 pilot 仅历史参考，未当执行 pilot**。
- **wall .100688 s**；**CPU .078125 s**；**memory .001249 GB**；caps 1800s/2h/8GB/0 wells → **PASS**。
- 主执行：**R=10**；wall **.204259 s**；CPU **.203125 s**；memory **.001293 GB**；PASS。
- 样本语义：每 replicate **initial/behavior 300** + **6×300 allocation** = **2,100**；总 **21,000 units**；allocation/feedback **18,000**；每 arm n_alloc=300/feedback=300/tuning≤20/caps/合法包。

## 3. 环境/arms

- 一步 DR：H=3、A=3、Y∈{0,1}；p=[.3,.4,.3]；b/μ/π2/m_wrong 冻结；C_H=20。
- 六 arms（同 learner/updater/预算，仅分配规则不同）：
  1. S_shared_score（candidate）：`w∝p·π²(Var+(μ−m)²)/b`
  2. S_random：uniform legal
  3. S_gp_uncertainty：`w∝√(Var/b)`
  4. S_decision_AL：`w∝p·π|μ−m|/b`
  5. S_optimal_experimental_design：`w∝b(1−b)`
  6. S_DR_MLE_allocation：`w∝p·π²Var/b`
- **不比较学习效果**；仅登记分配诊断。

## 4. per-arm 13 字段摘要

- **60/60 arm records**（10 replicates ×6 arms）；13 字段齐全：arm_id、replicate_id、allocation_weights、realized_allocation_frequency、H_summary、delta_summary、allocation_Q、variance_term、clipping、equal_budget_audit、two_run_sha、pass、failure_category。
- **60/60 pass=true**；**failed_arms=0**；`failure_category=null`；无 design_invalid。
- **H/δ**：所有 arm H/δ finite；**clipping n=0**（max raw H=1.6667 << C_H=20；C_H 不绑定；仍报告 cap/bound）。
- **allocation_Q**：所有 arm `full_ge_noise=true`；full/noise/bias-square 已报告。
- **weights/frequency**：simplex/support PASS；**equal_budget_audit** PASS。
- **two_run_sha**：每 arm 有 64-hex SHA；全结果两跑随后核验。
- **仅诊断字段**；**不解释为收益/学习效果/决策效果**。

## 5. G1–G6

| 门 | 状态 | 说明 |
|---|---|---|
| G1 支持/程序 | **PASS** | b>0、weights simplex/support |
| G2 截断 | **PASS** | C_H=20；n_clipped=0；cap/bound 报告；clipped≠exact value |
| G3 分配二阶项 | **PASS** | allocation_Q full≥noise 全部 |
| G4 无泄漏 | **PASS** | 无 decision/evaluation 输出；target 不作标签 |
| G5 两跑 | **PASS（外部核验）** | 两独立进程 result JSON 逐字节 |
| G6 schema/预算 | **PASS** | schema 先写；caps 与 0 wells 满足 |

**13 失败类别**已登记（含 chain_mismatch/two_run_mismatch/nonidentifiable 等）；本轮未触发。

## 6. 两跑/预算/产出

- **两独立进程** `m3_stage2.json` 逐字节 **`36C4DF1291EEB17D5FE31D3E3DC32509A1A366254396EFE9F9F08A0C146CE7FE`**；per-arm CSV、diagnostics、schema 亦一致；timing 单独。
- 结果 JSON 无 telemetry；timing 单独；schema/失败模板先写。
- 未输出 decision utility/regret/top-k/方法比较/学习效果。

## 7. 产物 SHA

| 文件 | SHA256 |
|---|---|
| `m3_stage2.json`（两跑一致） | `36C4DF1291EEB17D5FE31D3E3DC32509A1A366254396EFE9F9F08A0C146CE7FE` |
| `m3_stage2_per_arm.csv` | `ACAF46352CB4FB8AB86375EBA57B0D3CB51C5E06D125A30DB42C193EA228E5A1` |
| `m3_stage2_diagnostics.json` | `4A742BA087E1F3807C278B4EBFF762A7FE98657CC4C9C993A9370688D7BD8176` |
| `schema_m3_stage2_run.json` | `0E46DEC026DB42E8887296E7365C22466132ADC40DCF675C5FF543CDD4A2F499` |
| `timing_m3_stage2_run.json` | 见文件；result SHA `36C4DF12…` |
| `run_m3_stage2.py` / report / record / usage | 见 usage |

## 8. Stage3 建议/边界

- Stage2 分配诊断完成；仅支撑/机制账/检查性，**不构成学习效果/决策收益/药理/真实决策/迁移/机制/新颖性证据**。
- **DR/TMLE+最优分配等预算复制/超过的等价判定留 Stage3**；本轮不做。
- **Stage3/真实数据不执行**；data readiness open（C203/C205/C210），需独立预注册+挑战+Lead 批准；不得用合成/RNA 替代独立功能决策。
- 未改 exec prereg/M3 Stage1/M1/M2/N1/A-B-D/旧门槛/旧判定/代码；不晋升代码；不恢复停止实验；技术重复≠独立培养；不拼 ΔEMAX；M3 不与 M1/M2 混同；N1 不作 M3 证据。
