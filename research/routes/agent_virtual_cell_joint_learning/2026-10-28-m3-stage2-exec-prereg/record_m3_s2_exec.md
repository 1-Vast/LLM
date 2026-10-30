# record_m3_s2_exec.md —— R204-M3 Stage2 合成执行预注册记录（支撑研究；不运行）

角色：独立执行设计/审计员（未参与 R197/R200/203 模型开发）· 任务 task-173（R204-M3-S2-EXEC-PREREG）· 日期 2026-10-28
只写 `research/2026-10-28-m3-stage2-exec-prereg/` 与 `tmp/`；**未改 M3 预注册/Stage1/M1/M2/N1/A-B-D**；**未运行 Stage2 训练/效果/真实数据**；支撑研究/机制账 only；compute-only、0 wells。

## 0. 要求与完成对照

| 要求 | 状态 |
|---|---|
| ① 链核验（M3 v0.2+Stage1 链+Lead 决定；不匹配→chain_mismatch） | ✅ 只读核验 **17 文件 SHA 全匹配**（chain_pass=true、mismatches=0）：M3 v0.2 八件+Lead 决定 `9743CF2E…`+Stage1 八件；不匹配→`design_invalid: chain_mismatch`；执行时重核 |
| ② 独立执行 seeds（不复用 M3 Stage1/M1 Stage2/M2/N1；两跑同 seeds 独立进程逐字节；telemetry 分开） | ✅ data **20261401**、arms **20261410–15**、reps **20261420–29**；禁用 M3 Stage1 20261200、M1 Stage1 20261112/13、M1 v0.2 20261201–03、**M1 Stage2 20261301–49**、M2 Stage2 20261200–39、M2 Stage3 20262100–39、N1 20261030/61/62/63；**overlap=[]、unique=true**；两跑同 seeds/独立进程/结果 JSON 逐字节/telemetry 单独 |
| ③ Stage2 设置（一步 DR 环境 h/Y/b/π/mθ；m_true/m_wrong、正/零支持、截断 C、共线/分离；仅分配：shared vs random/GP/decision_AL/optimal design/DR+MLE；同信息反馈调参≤20/caps/合法实验包；不输出效果/regret/top-k/学习比较；DR/TMLE+最优分配等价判定留 Stage3） | ✅ 环境/诊断用例/六 arms/共同预算写死；**无效果/regret/top-k/学习效果比较**；等价判定明确留后续 Stage3，本轮只登记规格与可复现性 |
| ④ G1–G6 支持/截断/分配二阶项/无泄漏/两跑/schema·预算；失败类别；caps/pilot/schema/JSON 无 telemetry | ✅ G1–G6 写死；失败类别 12 项；caps **1800 s/2 h/8 GB/0 wells**；执行前最终实现 pilot 实测冻结 canonical；schema 先写；JSON 无 telemetry |
| ⑤ 停止/边界 | ✅ π=b→H=1 退化/共线/分离/无支持/截断按类别；只更新功能均值≠细胞动力学；无完整序贯 history/propensity/删失→不称序贯 DR；机制账 only；不执行 Stage3/真实数据/湿实验；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定；M3 不与 M1/M2 混同；N1 不作证据；data readiness open C203/C205/C210 |
| ⑥ report/record/usage+schema；标 completed + send_message | ✅ |

## 1. 时间线（Asia/Shanghai，2026-10-28）

| 时间 | 事件 |
|---|---|
| ~13:27 | 读 task-173 并 claim；读 M3 v0.2 设计/接受决定、Stage1/C209、formalism/schema/timing、ERRATA、R203 |
| ~13:31 | 写 `exec_plan_m3_s2.py`（链核验、独立 seeds、环境/六 arms、G1–G6/失败/预算、schema、算术单测） |
| ~13:33 | 首跑 clipping 提取路径错误（S1_diagnostics 是嵌套 dict）→ 修 `S1_b_clipping`，重跑 all_pass=true |
| ~13:35 | 两跑 `exec_plan_m3_s2.json`（`92D00E0C…`）与 `schema_m3_s2_exec.json`（`A0A43078…`）逐字节一致；写 PROBLEM/DESIGN/report/record/usage；标 completed + send_message |

## 2. 实现与披露

1. **只做规划/算术/骨架单测**：链核验、独立 seeds、Stage2 环境/六 arms/共同预算、G1–G6/失败/停止、caps/schema、DR 恒等/截断/共线/π=b/分配 ratios 算术；**不训练、不采样方法、不执行分配比较、不计算效果/regret/top-k**。
2. **链核验**：17/17 SHA 匹配；Stage1 `failed_checks=[]`、`all_checks_pass=true`、`check19_pass=true`、`no_effect_results=true`。
3. **seeds**：20261401+ 独立区间；禁用集交集 []；执行时重核。
4. **Stage2**：六 arms 含 **decision_AL/optimal_experimental_design 显式等预算强基线**；同 learner/updater；只比较分配；标准 DR/TMLE+最优分配等预算复制/超过→no_increment/撤判定留 Stage3。
5. **预算**：caps 1800 s/2 h/8 GB/0 wells；Stage1 pilot 参考 .00016347 s/rep、.001635 s、.007137 s（非执行实测）；执行前必须最终实现重跑 pilot 并冻结 canonical；JSON 无 telemetry。
6. **边界**：支撑研究/机制账；Stage2 不执行；未读真实数据；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定；M3 不与 M1/M2 混同；N1 不作证据；data readiness open（C203/C205/C210）。
7. **确定性**：plan/schema 两跑逐字节一致；JSON 无时间戳；无 telemetry。

## 3. 关键结果

- 链：17/17 SHA、chain_pass=true；Stage1 19 checks PASS。
- seeds：17 个执行 seeds unique、overlap=[]；区间 20261401+。
- 环境：H=3/A=3/Y∈[0,1]；p(h)/μ/b/π_1/π_2/m_true/m_wrong/C_H=20 冻结；诊断用例（零支持/截断/共线/分离/π=b）写死。
- 六 arms：S_shared_score、S_random、S_gp_uncertainty、**S_decision_AL**、**S_optimal_experimental_design**、S_DR_MLE_allocation；同信息/反馈/调参≤20/caps/合法包。
- 算术单测：DR identity gap **0.0**；clipping detected bias **−0.026407185629**（1 clipped，max raw H 167）；collinear rank **1**；π=b H−1 diff **0.0**；allocation ratios **[1.21722846, 1.16686763]**（full≥noise）。
- 失败类别 13；caps/0 wells；schema 先写；pilot 参考仅 Stage1。
- 无训练/无效果；本轮仅预注册草案。

## 4. 产物与哈希

| 文件 | SHA256 |
|---|---|
| `PROBLEM_M3_S2_EXEC.md` | `4690A50ACCCE901334E06522E7BDB1D2281770EA2E1AED883A0BEBD646D3077B` |
| `DESIGN_M3_S2_EXEC.md` | `AD18DC25EE6F504AFE8824581B88AEEA79F06FF47137B8740E0015E2491F5D77` |
| `exec_plan_m3_s2.py` | `83EFB2CD4A9EE447DAA0EDDDFA1857A5CDB52331C127F23798F47CF8DB70B350` |
| `exec_plan_m3_s2.json` | `92D00E0CF979CC900D43028C9EA49A00D3B9AE54D7C765A8E9DA483C26A6A7BF` |
| `schema_m3_s2_exec.json` | `A0A43078DBF9BD5942951F3506085E0739EAD6712D251990E99481D95863BC36` |
| report/record/usage | 见 `usage_m3_s2_exec.json` |
| 只读链（未改） | M3 v0.2 八件+Lead 决定+Stage1 八件（见 exec_plan JSON） |

## 5. 缺口与下一步

- **Stage2 尚未执行**；本文件仅预注册草案，未训练/未读真实数据/无效果。
- 执行前：独立挑战 + Lead 批准 + 重核 17 文件链 + 最终实现 pilot 实测冻结 canonical timing + seed/两跑/schema/失败模板核验。
- Stage3 另立预注册；真实功能数据仍 `data_unavailable`（C203/C205/C210）；支撑研究/机制账；不晋升代码/不改旧判定/不恢复停止实验。
