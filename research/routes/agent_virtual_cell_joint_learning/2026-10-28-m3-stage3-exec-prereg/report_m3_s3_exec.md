# report_m3_s3_exec —— R204-M3 Stage3 合成执行预注册报告（固定反馈学习比较；不运行）

2026-10-28。对象：R204-M3 Stage3 合成执行预注册（固定反馈比较学习 + 闭环成本）。依据：M3 v0.2 链、Lead Stage1/Stage2 决定、M3 Stage1/C209、Stage2/C213（`36C4DF12…`）、R204 BRIEF/report、ERRATA C197/C199/C201/C207/C209/C213/C215/C216。
**状态：预注册草案；未运行 Stage3 训练/效果/真实数据；仅规划/算术/骨架单测；支撑研究/机制账 only；compute-only、0 wells；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定；Stage3 执行须另立独立挑战+Lead 批准。**

## 0. 交付物

- 问题定义：[PROBLEM_M3_S3_EXEC.md](PROBLEM_M3_S3_EXEC.md)（`C7B91087…`）
- 执行设计：[DESIGN_M3_S3_EXEC.md](DESIGN_M3_S3_EXEC.md)（`C45925D0…`）
- 规划/骨架：[exec_plan_m3_s3.py](exec_plan_m3_s3.py)（`FF1A3FB4…`）→ [exec_plan_m3_s3.json](exec_plan_m3_s3.json)（`671F2617…`）
- schema：[schema_m3_s3_exec.json](schema_m3_s3_exec.json)（`B46D3249…`）
- 记录/用量：[record_m3_s3_exec.md](record_m3_s3_exec.md)、[usage_m3_s3_exec.json](usage_m3_s3_exec.json)

## 1. 链核验（已通过）

`exec_plan_m3_s3.py` 只读核验 **35 文件 SHA 全部匹配（chain_pass=true、mismatches=0）**：M3 v0.2 八件 + Lead Stage1 决定 `9743CF2E…`；Stage1/C209 八件；Stage2 exec v0.2 八件 + Lead Stage2 决定 `A29CBF7B…`；Stage2/C213 九件（`m3_stage2.json` `36C4DF12…`，60/60 per-arm、failure_category null、no_effect_results=true；per_arm.csv/diagnostics/schema/timing/report/record/usage/run script）。另核 Stage1 failed_checks=[]/all_checks_pass/check19_pass、Stage2 status completed_allocation_diagnostics/60 per-arm。不匹配→`design_invalid: chain_mismatch`；执行时重核。

## 2. 独立 seeds（overlap=[]、unique=true）

| 用途 | seeds |
|---|---|
| 环境 | **20261601** |
| replicates（R=10） | **20261601–20261610** |
| arms（a=0..6,r=0..9） | **20261611 + 10a + r** → 20261611–20261680 |
| headroom | **20261681–20261690** |
| 两跑 | 同 seeds/独立进程/结果 JSON 逐字节/telemetry 单独 |

禁用 M3 Stage1 20261112/13、20261200；**M3 Stage2 20261401–20261470**；M1 Stage1 20261112/13；M1 v0.2 20261201–03；M1 Stage2 20261301–49；M2 Stage2 20261200–39；M2 Stage3 20262100–39；N1 20261030/61/62/63；本地 overlap=[]、unique=true。

## 3. Stage3 设置（固定反馈比较学习；分配配套固定）

- **环境复用 Stage2 冻结**：一步 DR H=3/A=3/Y binary；p/μ/b/π_1/π_2/m_true/m_wrong/C_H=20；公式冻结；合成不推广真实。
- **固定反馈**：R=**10**；每 replicate **300 条共享反馈记录 (h,a,Y)** + **300 评价 units**；所有 arms 同反馈/评价；评价独立于拟合/更新/选择；**每 arm 不选择分配**（shared-score 固定）。
- **总样本**：评价 units=**3,000**、反馈=**3,000**；每 arm 反馈/评价 300/300/replicate；调参≤20；caps 1800 s/2 h/8 GB/0 wells。
- **7 arms**：A_candidate_score_tilt（候选）、A_full_history_retrain、A_importance_weighting、A_DR_targeting、A_TMLE_targeting、A_value_aware、**A_standard_DR_TMLE_optimal_allocation（标准 DR/TMLE+最优分配组合等预算基线）**；同信息/反馈/调参/caps/合法包；不比较分配；标准 DR/TMLE+最优分配等预算复制/超过→`no_increment`/撤写死；不称新颖性。

## 4. 主端点/分析/闭环成本

- Primary comparison=candidate vs `A_standard_DR_TMLE_optimal_allocation`；primary endpoint=独立功能决策效用/后悔（normalized），δ=**0.05**；成功=mean ΔR≤−δ ∧ 95% CI upper<0 ∧ **Holm p<.05**。
- **Holm family=6**（primary+5 secondary：full-history/IW/DR/TMLE/value-aware）；次端点=预测校准/DR 分数误差/RNA（仅 secondary）。
- **精度**：n_units=300、deff=2.2、n_eff=**136.36**、MDE80=**0.04798268≤.05**、n_req=**278≤300**；cluster 按 replicate/背景/任务；实际 R=10 报 cluster-robust SE；**6,282.1038/1,572.7759 仅 Fisher-z 参考**（非整数/非门/非 paired DR）；headroom=U_max−U0 先检（<δ→unreachable_gate；近满分→另立 budget-to-target；不换端点）。
- **闭环成本**：每 arm 反馈 300/评价 300/调参≤20/caps 1800 s/2 h/8 GB/0 wells；7 arms 同预算；培养/板/对照/失败/重复/标定/计算/调参同账；超限→`compute_budget_exceeded`/stop。

## 5. G1–G6 / 失败类别 / 预算/schema

- G1 支持→support/positivity；G2 截断→calibration；G3 投影/拟合→calibration/nonidentifiable；G4 无泄漏→leakage；G5 两跑→two_run_mismatch；G6 schema/预算→compute_budget_exceeded。
- **失败类别 13 项**（含 chain_mismatch）：support/positivity/propensity/leakage/calibration/compute_budget_exceeded/nonidentifiable/two_run_mismatch/chain_mismatch/unreachable_gate/precision_insufficient/no_increment/inconclusive。
- caps 1800 s/2 h/8 GB/0 wells；schema 先写；**执行前最终实现 Stage3 pilot（2 reps×7 arms×300 units）实测并冻结 canonical**；Stage2 pilot .100688/.078125/.001249 **仅历史参考、不得当执行 pilot**；JSON 无 telemetry；失败只写类别。
- **骨架单测（仅链核验/算术，不训练）全 PASS**：chain=35/35；Stage1/C209 PASS；Stage2/C213 PASS；failure=13（含 chain_mismatch）；family=6；arms=7（含 combined standard）；seeds overlap=[]；sample 3,000/3,000；MDE .04798268≤.05、n_req278；**无训练/无效果**。

## 6. 边界

支撑研究/机制账 only；合成 compute-only、0 wells；**不执行真实数据/湿实验**；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定；不恢复停止实验；M3 不与 M1/M2 混同；N1 不作证据；data readiness open（C203/C205/C210/C214）；Stage3 执行须另立独立挑战+Lead 批准；标准 DR/TMLE+最优分配等价判定写死在本预注册、执行后再判。

## 7. 产物 SHA/确定性

| 文件 | SHA256 |
|---|---|
| `PROBLEM_M3_S3_EXEC.md` | `C7B910875BD6C40C32B68E2F43582469AB50B0811A9177129354E1ECC77E5846` |
| `DESIGN_M3_S3_EXEC.md` | `C45925D0612A20559841E3D092948F398FF1633EFDE8E167A7735A337A1B6B65` |
| `exec_plan_m3_s3.py` | `FF1A3FB4C5D334655EC817560F86E8441C6F37F3CEADD29E2451BB394004C8C4` |
| `exec_plan_m3_s3.json` | `671F261736FA9AA57470292A2C44376FDD349268B83D2E1C9FCCB7290CD90705` |
| `schema_m3_s3_exec.json` | `B46D32490DE788BCE8FD8B93C04BE5475D0AAF4C585750BA46C6236F306DC81E` |
| report/record/usage | 见 `usage_m3_s3_exec.json` |

**确定性**：`exec_plan_m3_s3.json` 与 `schema_m3_s3_exec.json` 两跑逐字节一致；JSON 无 telemetry；计时参考来自只读 Stage2 timing。

## 8. 建议

1. **提交独立挑战**：重点 35 文件链/Stage1/Stage2、独立 seeds/两跑、固定反馈同 (h,a,Y)/评价样本、7 arms（含 combined standard DR/TMLE+最优分配）、primary/secondary/Holm/headroom/MDE/6,282 边界、闭环成本、G1–G6/13 失败类别、caps/pilot 实测冻结、schema、停止/边界。
2. 挑战通过 + Lead 批准后才可执行 **Stage3 合成学习比较**（仅支撑研究/机制账、compute-only、0 wells）；执行前重核链、最终实现 pilot 实测冻结 canonical、两跑/schema/失败模板核验。
3. **不做**：训练/效果/真实数据/湿实验/代码晋升/旧判定修改/恢复停止实验；真实 Stage3 另立资源/预注册。
