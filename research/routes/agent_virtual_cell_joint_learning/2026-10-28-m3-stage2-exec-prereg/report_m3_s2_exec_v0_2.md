# report_m3_s2_exec_v0_2 —— R204-M3-S2.1 修订预注册报告（3 必改；不运行）

2026-10-28。对象：R204-M3 Stage2 合成执行预注册 v0.2。依据：M3-S2-EXEC-C1 挑战（revise/3 必改）、M3 v0.2 链、Lead Stage1 决定、M3 Stage1/C209、R204 BRIEF/report、ERRATA C197/C199/C201/C207/C209/C210。
**状态：预注册修订草案；未运行 Stage2 训练/效果/真实数据；仅规划/算术/骨架单测；支撑研究/机制账 only；compute-only、0 wells；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定；Stage2 执行须另立独立挑战+Lead 批准。**

## 0. 交付物（v0.2 新文件；v0.1 保留不改）

- 问题定义：[PROBLEM_M3_S2_EXEC_v0_2.md](PROBLEM_M3_S2_EXEC_v0_2.md)（`FE9180FA…`）
- 执行设计：[DESIGN_M3_S2_EXEC_v0_2.md](DESIGN_M3_S2_EXEC_v0_2.md)（`2569079C…`）
- 规划/骨架：[exec_plan_m3_s2_v0_2.py](exec_plan_m3_s2_v0_2.py)（`C85C1AEA…`）→ [exec_plan_m3_s2_v0_2.json](exec_plan_m3_s2_v0_2.json)（`F16D1C04…`）
- schema：[schema_m3_s2_exec_v0_2.json](schema_m3_s2_exec_v0_2.json)（`987089F8…`）
- 记录/用量：[record_m3_s2_exec_v0_2.md](record_m3_s2_exec_v0_2.md)、[usage_m3_s2_exec_v0_2.json](usage_m3_s2_exec_v0_2.json)

## 1. 3 必改落实

| # | 挑战问题 | v0.2 落实 |
|---|---|---|
| ① **失败类别 12≠13，缺 chain_mismatch** | **补全 13 项**：support/positivity/propensity/leakage/calibration/compute_budget_exceeded/nonidentifiable/two_run_mismatch/**chain_mismatch**/unreachable_gate/precision_insufficient/no_increment/inconclusive；schema/failure template/stop 映射同步（单测 `chain_mismatch_present=true`、count=**13**） |
| ② **六 arms 无 per-arm 输出/端点/schema** | 定义 **`per_arm`/`arm_result` 13 字段**：arm_id、replicate_id、allocation_weights、realized_allocation_frequency、H_summary、delta_summary、allocation_Q、variance_term、clipping、equal_budget_audit、two_run_sha、pass、failure_category；每 arm 通过判据（simplex/support、H/δ 有限、Q 报告、等预算、two-run SHA、无禁输出）与失败映射；**仍不输出 decision utility/regret/top-k/学习效果比较**；保留"分配诊断"（非学习效果比较），标准 DR/TMLE+最优分配等价判定留 Stage3 |
| ③ **sample 语义未冻结；pilot 仅引用 Stage1** | 冻结 **R=10**；data seed **20261401**；replicate seeds **20261401–10**；每 replicate **300 initial/behavior units** + **每 arm 300 alloc units**（6 arms）；**total units=21,000**、**allocation/feedback=18,000**；arm seed=**20261411+10a+r**；每 arm 等预算账写死；**执行前必须跑最终实现 pilot（2 reps×6 arms×300）实测并冻结 canonical timing**；Stage1 .00016347/.001635/.007137 **仅历史参考、不得当执行 pilot** |

## 2. 链核验/Stage1 状态（已通过）

- **17 文件 SHA 全匹配**（chain_pass=true、mismatches=0）：M3 v0.2 八件 + Lead 决定 `9743CF2E…` + Stage1/C209 八件；不匹配→`design_invalid: chain_mismatch`（已入 13 类）；执行时重核。
- Stage1：failed_checks=[]、all_checks_pass=true、check19_pass=true、no_effect_results=true；19 checks/S1 全 PASS。

## 3. 冻结样本/预算语义

| 项 | 值 |
|---|---|
| R | **10** |
| data seed / replicate seeds | **20261401** / **20261401–10** |
| 每 replicate initial units | **300** |
| 每 arm 分配 units/replicate | **300** |
| arms | **6** |
| 每 replicate 总 units | **2,100** |
| 全部总 units | **21,000** |
| allocation/feedback 总数 | **18,000** |
| arm seed | **20261411+10a+r**（a=0..5,r=0..9） |
| 每 arm 等预算 | n_alloc=300/feedback=300/tuning≤20/caps/合法包 |
| 两跑 | 同 seeds/独立进程/结果 JSON 逐字节/telemetry 单独 |

- 禁用 seeds：M3 Stage1 20261200、M1 Stage1 20261112/13、M1 v0.2 20261201–03、M1 Stage2 20261301–49、M2 Stage2 20261200–39、M2 Stage3 20262100–39、N1 20261030/61/62/63；本地 overlap=[]、unique=true。

## 4. 环境/六 arms/per-arm 判据

- 环境：H=3/A=3/Y binary；p(h)/μ/b/π_1/π_2/m_true/m_wrong/C_H=20 冻结；评价独立、target 不作标签、分配不复用评价；诊断用例（正/零支持、截断、共线、分离、π=b）。
- 六 arms：S_shared_score（候选）、S_random、S_gp_uncertainty、**S_decision_AL**、**S_optimal_experimental_design**、S_DR_MLE_allocation；同 learner/updater、仅分配诊断；不输出效果/regret/top-k/学习比较；等价判定留 Stage3。
- per-arm 13 字段与通过/失败判据见 PROBLEM §3/DESIGN §3；G1–G6 继承。

## 5. 失败/预算/schema/单测

- **失败类别 13 项**（含 chain_mismatch）；失败只写类别；不改旧判定/门槛。
- caps **1800 s/2 h/8 GB/0 wells**；pilot 最终实现实测冻结（Stage1 pilot 仅历史参考）；schema 先写；JSON 无 telemetry；两跑逐字节。
- **骨架单测（仅算术/不训练）全 PASS**：DR gap **1.1e-16**；clipping detected bias **−0.026407185629**；collinear rank **1**；π=b H−1 **0.0**；allocation ratios **[1.21722846, 1.16686763]**；failure_categories 13/含 chain_mismatch；per-arm 13 字段；sample 21,000/18,000；seeds overlap=[]。

## 6. 边界

支撑研究/机制账 only；不执行 Stage3/真实数据/湿实验；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定；不恢复停止实验；M3 不与 M1/M2 混同；N1 不作证据；data readiness open（C203/C205/C210）；Stage2 执行须另立独立挑战+Lead 批准；Stage3 另立预注册。

## 7. 产物 SHA/确定性

| 文件 | SHA256 |
|---|---|
| `PROBLEM_M3_S2_EXEC_v0_2.md` | `FE9180FA4A82A71ABA77F7080A848BEBD7C6CA24482DD3BE397F6B5138398F32` |
| `DESIGN_M3_S2_EXEC_v0_2.md` | `2569079C63320EC0518D913B26A65A2CCA7E35D6DB47D178B48AE904AF7ED89F` |
| `exec_plan_m3_s2_v0_2.py` | `C85C1AEA651E844D4D9B26EC793D10037960B3B516BC97FA6F48C5942B1192C4` |
| `exec_plan_m3_s2_v0_2.json` | `F16D1C04F5E63ECDA082F10FD5EB4AEC486B902829DA1FCAD027CA92BF0184C8` |
| `schema_m3_s2_exec_v0_2.json` | `987089F84330DF97338513163570DDA47E91ABA3B26E73981DF44E0FC188B3B1` |
| report/record/usage | 见 `usage_m3_s2_exec_v0_2.json` |

**确定性**：`exec_plan_m3_s2_v0_2.json` 与 `schema_m3_s2_exec_v0_2.json` 两跑逐字节一致；JSON 无 telemetry。

## 8. 建议

1. **提交轻量复核**：13 类失败类别（含 chain_mismatch）、per-arm 13 字段/判据/schema、R=10/sample 21,000/18,000 语义、每 arm 等预算、最终实现 pilot 实测冻结要求、其余不变项。
2. 复核通过后请 Lead 批准 **M3 Stage2 合成分配诊断执行**（仅支撑研究/机制账、compute-only、0 wells）；执行前重核链、跑最终实现 pilot 冻结 canonical、两跑/schema/失败模板核验。
3. **不做**：训练/效果/真实数据/Stage3/代码晋升/旧判定修改/恢复停止实验。
