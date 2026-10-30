# report_m3_s2_exec —— R204-M3 Stage2 合成执行预注册报告（支撑研究；不运行）

2026-10-28。对象：R204-M3 Stage2 合成执行预注册（固定更新器分配比较）。依据：M3 v0.2 链、Lead Stage1 决定、M3 Stage1/C209、R204 BRIEF/report、ERRATA C197/C199/C201/C207/C209/C210。
**状态：预注册草案；未运行 Stage2 训练/效果/真实数据；仅规划/算术/骨架单测；支撑研究/机制账 only；compute-only、0 wells；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定；Stage2 执行须另立独立挑战+Lead 批准。**

## 0. 交付物

- 问题定义：[PROBLEM_M3_S2_EXEC.md](PROBLEM_M3_S2_EXEC.md)（`4690A50A…`）
- 执行设计：[DESIGN_M3_S2_EXEC.md](DESIGN_M3_S2_EXEC.md)（`AD18DC25…`）
- 规划/骨架：[exec_plan_m3_s2.py](exec_plan_m3_s2.py)（`83EFB2CD…`）→ [exec_plan_m3_s2.json](exec_plan_m3_s2.json)（`92D00E0C…`）
- schema：[schema_m3_s2_exec.json](schema_m3_s2_exec.json)（`A0A43078…`）
- 记录/用量：[record_m3_s2_exec.md](record_m3_s2_exec.md)、[usage_m3_s2_exec.json](usage_m3_s2_exec.json)

## 1. 链核验（已通过）

`exec_plan_m3_s2.py` 只读核验 **17 文件 SHA 全部匹配（chain_pass=true、mismatches=0）**：M3 v0.2 八件（PROBLEM `15DFE82C…`、DESIGN `033D67CB…`、formalism py `3E709B81…`、formalism json `299E5B03…`、schema `E2E641BC…`、timing `BA261FA7…`、report `039B1A98…`、record `47042AD6…`）+ **Lead 决定 `9743CF2E…`** + Stage1/C209 八件（json `60845EFA…`、diagnostics `D0816802…`、checks.csv `2E6E3C8F…`、schema `B0DC56A8…`、timing `7432135D…`、report `3FCAC827…`、record `EDB0AC38…`、usage `7F8E2E6A…`）。不匹配→`design_invalid: chain_mismatch`；执行时重核。
**Stage1 状态**：failed_checks=[]、all_checks_pass=true、check19_pass=true、no_effect_results=true、19 checks/S1 全 PASS。

## 2. 独立执行 seeds（overlap=[]）

| 用途 | seeds |
|---|---|
| Stage2 数据/环境 | **20261401** |
| 6 arms | **20261410–20261415** |
| 两跑 reps | **20261420–20261429** |

**禁用/不复用**：M3 Stage1 20261200；M1 Stage1 20261112/13；M1 v0.2 20261201–03；M1 Stage2 执行 20261301–49；M2 Stage2 20261200–39；M2 Stage3 20262100–39；N1 gate/dev 20261030/61/62/63。本地 **overlap=[]、unique=true**；两跑同 seeds 独立进程、结果 JSON 逐字节、telemetry 单独。

## 3. Stage2 合成设置（仅分配比较）

- **一步 DR 环境**：H=3/A=3/Y∈[0,1]；p(h)=[.3,.4,.3]、μ/b 冻结；π_1/π_2；m_true=μ、m_wrong=.5；C_H=20；H_k=π/b、δ/ V/score-tilt/allocation-Q 公式冻结；**评价独立、target 不作标签、分配不复用评价**。
- **诊断用例**：正支持、零支持（b=0 & π mass=1→未识别）、截断（clipped≠exact，报 bias/bound）、共线（rank<2→nonidentifiable）、分离（root −inf）、π=b→H=1 退化（保留等价/不称新意）。
- **六 arms（同 learner/updater；仅分配）**：S_shared_score（候选）、S_random、S_gp_uncertainty、**S_decision_AL（显式等预算强基线）**、**S_optimal_experimental_design（显式等预算强基线）**、S_DR_MLE_allocation。同信息/反馈/调参≤20/caps/合法实验包。
- **不输出** decision utility/regret/top-k/学习效果比较；标准 DR/TMLE+最优分配等预算复制/超过→`no_increment`/撤的判定**留 Stage3**；本轮仅规格/可复现性。

## 4. G1–G6 / 失败/停止

- G1 支持/程序→support/positivity；G2 截断（C_H=20，clipped≠exact，报 bias/bound）→calibration；G3 分配二阶项（full≥noise、错设 bias² 非零/未知、不按 noise-only）→calibration；G4 无泄漏→leakage；G5 两跑→two_run_mismatch；G6 schema/预算→compute_budget_exceeded。
- 失败类别 13 项：`design_invalid: support|positivity|propensity|leakage|calibration|compute_budget_exceeded|nonidentifiable|two_run_mismatch|chain_mismatch`、`unreachable_gate`、`precision_insufficient`、`no_increment`、`inconclusive`。
- 停止/分类：共线/分离/无支持→nonidentifiable；零支持/极端权重→support/positivity；截断→calibration（clipped 非精确 value）；评价复用→leakage；π=b→H=1 退化不称新意；不变量/不放宽/不换端点；只更新功能均值≠细胞动力学；无序贯→不称序贯 DR。

## 5. 预算/两跑/schema/骨架单测

- caps **1800 s/2 h/8 GB/0 wells**；执行前最终实现实测 pilot 并冻结 canonical timing；结果 JSON 无 telemetry；失败只写类别。
- Stage1 pilot 参考（非执行实测）：per-rep **.00016347 s**、projected **.001635 s**、wall **.007137 s**（SHA `7432135D…`）；执行必须重测。
- **schema**：`schema_m3_s2_exec.json` 先写（top/arm/checks/forbidden fields：decision utility/regret/topk/method comparison/learning effect/gain/pharmacology/real decision/transfer/mechanism/novelty/real data/sequential DR claim）；两跑逐字节。
- **骨架单测（仅算术/不训练/不比较）全 PASS**：DR identity gap **0.0**（≤1e-12）；clipping detected（bias **−0.026407185629**，max raw H 167，1 clipped）；collinear rank **1**；π=b H−1 **0.0**；allocation ratios **[1.21722846, 1.16686763]**（full≥noise）；六 arms 含 decision_AL/optimal design；seeds overlap=[]；**无训练/无效果比较**。

## 6. 边界

支撑研究/机制账 only；合成 compute-only、0 wells；**不执行 Stage3/真实数据/湿实验**；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定；不恢复停止实验；**M3 不与 M1/M2 混同**；N1 不作 M3 证据；data readiness open（C203/C205/C210）；Stage2 执行须另立预注册+独立挑战+Lead 批准；Stage3 另立预注册。

## 7. 产物 SHA/确定性

| 文件 | SHA256 |
|---|---|
| `PROBLEM_M3_S2_EXEC.md` | `4690A50ACCCE901334E06522E7BDB1D2281770EA2E1AED883A0BEBD646D3077B` |
| `DESIGN_M3_S2_EXEC.md` | `AD18DC25EE6F504AFE8824581B88AEEA79F06FF47137B8740E0015E2491F5D77` |
| `exec_plan_m3_s2.py` | `83EFB2CD4A9EE447DAA0EDDDFA1857A5CDB52331C127F23798F47CF8DB70B350` |
| `exec_plan_m3_s2.json` | `92D00E0CF979CC900D43028C9EA49A00D3B9AE54D7C765A8E9DA483C26A6A7BF` |
| `schema_m3_s2_exec.json` | `A0A43078DBF9BD5942951F3506085E0739EAD6712D251990E99481D95863BC36` |
| report/record/usage | 见 `usage_m3_s2_exec.json` |

**确定性**：`exec_plan_m3_s2.json` 与 `schema_m3_s2_exec.json` 两跑逐字节一致；JSON 无 telemetry；计时参考来自只读 Stage1 timing 文件。

## 8. 建议

1. **提交本执行预注册做独立挑战**：重点 17 文件链/Stage1 状态、独立 seeds+两跑、DR 环境/六 arms/同预算、G1–G6、失败/停止/截断/共线/分离/π=b、caps/pilot 重测冻结、schema、边界。
2. 挑战通过 + Lead 批准后才可执行 Stage2 合成分配诊断（仅支撑研究、compute-only、0 wells）；执行前重核链、最终实现 pilot 实测冻结 canonical timing；**不批 Stage3/真实数据/湿实验/效果/药理/真实决策/迁移/机制/新颖性**。
3. **不做**：训练/效果比较/结果解读/代码晋升/旧判定修改/恢复停止实验。
