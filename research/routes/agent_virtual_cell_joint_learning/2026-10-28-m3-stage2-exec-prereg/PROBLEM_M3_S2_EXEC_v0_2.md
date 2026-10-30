# PROBLEM_M3_S2_EXEC_v0_2 —— R204-M3-S2.1 Stage2 合成执行预注册（3 必改；不运行）

2026-10-28。对象：R204-M3 Stage2 合成执行预注册（固定更新器分配诊断）。修正 v0.1（[PROBLEM_M3_S2_EXEC.md](PROBLEM_M3_S2_EXEC.md)，保留不改），落实 M3-S2-EXEC-C1 三项必改：**失败类别补全 13 项**、**per-arm 分配诊断字段/判据/schema**、**冻结 Stage2 replicate/sample 语义并明确 pilot 实测要求**。依据：M3 v0.2 链、Lead `DECISION_R204_M3_STAGE1.md`（`9743CF2E…`）、M3 Stage1/C209、R204 BRIEF/report、ERRATA C197/C199/C201/C207/C209/C210、R203 decision/power。
**状态：预注册修订草案 v0.2；未运行 Stage2 训练/效果/真实数据；仅规划/算术/骨架单测；支撑研究/机制账 only；compute-only、0 wells；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定；M3 不与 M1/M2 混同；N1 不作证据；data readiness open（C203/C205/C210）。**

## 0. 3 必改落实

| # | 挑战问题 | v0.2 修正 |
|---|---|---|
| ① **失败类别 12≠13，缺 chain_mismatch** | **`failure_categories` 补全 13 项**：`design_invalid: support|positivity|propensity|leakage|calibration|compute_budget_exceeded|nonidentifiable|two_run_mismatch|chain_mismatch` + `unreachable_gate|precision_insufficient|no_increment|inconclusive`；schema/失败模板/stop 映射同步（chain mismatch→`design_invalid: chain_mismatch`） |
| ② **六 arms 无 per-arm 输出/端点/schema** | 定义**仅分配诊断**口径：`per_arm`/`arm_result` 字段=**arm_id、replicate_id、allocation_weights、realized_allocation_frequency、H_summary、delta_summary、allocation_Q、variance_term、clipping、equal_budget_audit、two_run_sha、pass、failure_category**（13 字段）；每 arm 通过判据（simplex/support、H/δ 有限、allocation-Q 报告、等预算审计、two-run SHA、无禁输出）与失败类别映射；**不得输出 decision utility/regret/top-k/学习效果比较**；保留"分配诊断"而非学习效果比较；标准 DR/TMLE+最优分配等价判定留 Stage3 |
| ③ **replicate/sample 语义未冻结；pilot 仅引用 Stage1** | **冻结**：R=**10** replicates；data seed **20261401** 定义冻结环境；replicate r seed=**20261401+r**（r=0..9）；每 replicate **initial/behavior units=300** + **每 arm 分配 units=300**（6 arms）；**total units=10×(300+6×300)=21,000**；**total allocation/feedback units=10×6×300=18,000**；每 arm 等预算账（n_alloc=300/feedback=300/tuning≤20/caps/合法包）；arm a,r seed=**20261411+10a+r**；**执行前必须跑最终实现 pilot（2 reps×6 arms×300 alloc）实测 wall/CPU/memory 并冻结 canonical timing，Stage1 pilot 数字仅历史参考、不得当执行 pilot 引用** |
| ④ 保留 | 17 文件链/Stage1、独立 seeds/两跑、H=3/A=3/Y binary、p/μ/b/π/m/C_H=20、六 arms（含 decision_AL/optimal design）、G1–G6、caps 1800 s/2 h/8 GB/0 wells、schema 先写、无 telemetry、单测算术、π=b/截断/共线/分离/支持规则、边界 |

## 1. 链核验（执行前；不匹配→stop）

`exec_plan_m3_s2_v0_2.py` 只读核验 **17 文件 SHA 全部匹配（chain_pass=true、mismatches=0）**：M3 v0.2 八件 + Lead 决定 `9743CF2E…` + Stage1/C209 八件。不匹配→`design_invalid: chain_mismatch`（现已在失败类别/schema/stop 同步）；执行时重核。Stage1 状态：failed_checks=[]、all_checks_pass=true、check19_pass=true、no_effect_results=true。

## 2. 独立执行 seeds

| 用途 | seeds |
|---|---|
| 冻结环境 data seed | **20261401** |
| replicate seeds（R=10） | **20261401–20261410**（r=0..9） |
| arm seeds（a=0..5,r=0..9） | **20261411 + 10a + r** → **20261411–20261470** |
| 两跑 | 同 seeds、独立进程、结果 JSON 逐字节、telemetry 单独 |

禁用：M3 Stage1 20261200；M1 Stage1 20261112/13；M1 v0.2 20261201–03；M1 Stage2 20261301–49；M2 Stage2 20261200–39；M2 Stage3 20262100–39；N1 20261030/61/62/63。本地 **overlap=[]、unique=true**；执行时不得改 seed。

## 3. Stage2 合成设置（仅分配诊断）

- 一步 DR 环境：H=**3** contexts、A=**3** actions、Y∈[0,1] binary；p(h)=[.3,.4,.3]；μ/b/π_1/π_2/m_true/m_wrong 冻结；C_H=**20**；`H=π/b`、δ/V/score-tilt/allocation-Q 公式冻结；评价独立、target 不作标签、分配不复用评价。
- 诊断用例：正/零支持、截断（clipped≠exact，报 bias/bound）、共线（rank<2→nonidentifiable）、分离（root −inf）、π=b→H=1 退化（保留等价/不称新意）。
- **六 arms（同 learner/updater；仅分配诊断）**：S_shared_score（候选）、S_random、S_gp_uncertainty、**S_decision_AL**、**S_optimal_experimental_design**、S_DR_MLE_allocation。
- **per-arm 字段 13 项**见 §0；每 arm 通过/失败类别写死；**不输出 decision utility/regret/top-k/学习效果比较**；标准 DR/TMLE+最优分配等预算复制/超过→`no_increment`/撤判定留 Stage3。

## 4. G1–G6 / 失败类别

- G1 支持/程序→support/positivity；G2 截断→calibration；G3 分配二阶项→calibration；G4 无泄漏→leakage；G5 两跑→two_run_mismatch；G6 schema/预算→compute_budget_exceeded。
- **失败类别 13 项**（含 chain_mismatch）：`design_invalid: support|positivity|propensity|leakage|calibration|compute_budget_exceeded|nonidentifiable|two_run_mismatch|chain_mismatch`、`unreachable_gate`、`precision_insufficient`、`no_increment`、`inconclusive`。

## 5. 预算/两跑/schema

- caps **1800 s/2 h/8 GB/0 wells**；每 arm 等预算账见 §0③；**执行前最终实现 pilot 实测并冻结 canonical timing**（Stage1 pilot 仅历史参考）；结果 JSON 无 telemetry；失败只写类别。
- `schema_m3_s2_exec_v0_2.json` 先写：top keys 含 `per_arm`/`sample_semantics`、per-arm 13 字段、判据/失败映射、13 失败类别、forbidden fields；两跑逐字节。

## 6. 停止/边界

- π=b→H=1 退化；共线/分离/无支持→nonidentifiable；零支持/极端权重→support/positivity；截断→calibration（clipped 非精确 value）；评价复用→leakage；两跑/链/预算→对应类别；**任何失败不改旧判定/门槛**；不放宽/改阈值/换端点。
- 只更新功能均值 ≠ 细胞动力学兼容更新；无完整序贯 history/propensity/删失→不称序贯 DR/TMLE。
- 支撑研究/机制账 only；不执行 Stage3/真实数据/湿实验；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定；不恢复停止实验；M3 不与 M1/M2 混同；N1 不作证据；data readiness open（C203/C205/C210）；Stage2 执行须另立独立挑战+Lead 批准；Stage3 另立预注册。
