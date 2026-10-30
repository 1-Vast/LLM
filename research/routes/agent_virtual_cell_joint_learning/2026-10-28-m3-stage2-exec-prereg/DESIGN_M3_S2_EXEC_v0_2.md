# DESIGN_M3_S2_EXEC_v0_2 —— R204-M3-S2.1 Stage2 执行设计（冻结样本语义/per-arm 诊断；不运行）

2026-10-28。依据：[PROBLEM_M3_S2_EXEC_v0_2.md](PROBLEM_M3_S2_EXEC_v0_2.md)、`exec_plan_m3_s2_v0_2.json`、`schema_m3_s2_exec_v0_2.json`、M3 v0.2 链、Lead Stage1 决定、M3 Stage1/C209。
**状态：预注册修订设计 v0.2；未运行 Stage2 训练/效果/真实数据；支撑研究/机制账 only；compute-only、0 wells；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定；Stage2 执行须另立独立挑战+Lead 批准。**

## 0. 执行前核验/门顺序

1. **SHA 链**：17 文件（M3 v0.2 八件+Lead 决定+Stage1 八件）全部匹配（本地 chain_pass=true）；执行时重核；失败→`design_invalid: chain_mismatch`。
2. **Stage1 状态**：C209 failed_checks=[]、all_checks_pass=true、check19_pass=true、no_effect_results=true。
3. **seeds 独立核验**：replicate seeds 20261401–10、arm seeds 20261411–70；与禁用集交集 []；执行时重核、不得改 seed。
4. **pilot 冻结**：执行前跑**最终实现 pilot**（2 replicates×6 arms×300 alloc units）实测 wall/CPU/memory，冻结 canonical timing；**不得只引用 Stage1 pilot**（Stage1 .00016347/.001635/.007137 仅历史参考）；超 caps→`compute_budget_exceeded`。
5. **schema/失败模板先写**：`schema_m3_s2_exec_v0_2.json` 运行前冻结。
6. **Stage2 通过后**：Stage3/真实数据/湿实验不批；Stage3 另立预注册+独立挑战+Lead 批准。

## 1. Stage2 样本/预算语义（冻结）

| 项 | 冻结值 |
|---|---|
| R replicates | **10** |
| data seed | **20261401**（冻结环境；不产生效果） |
| replicate seeds | **20261401–20261410**（r=0..9） |
| 每 replicate initial/behavior units | **300** |
| 每 arm 分配 units（每 replicate） | **300** |
| arms | **6** |
| 每 replicate 总 units | 300+6×300=**2,100** |
| 全部 replicates 总 units | 10×2,100=**21,000** |
| allocation/feedback 总 units | 10×6×300=**18,000** |
| arm a, replicate r seed | **20261411+10a+r**（a=0..5,r=0..9） |
| 每 arm 等预算账 | n_alloc=300、feedback=300、tuning≤20 configs、caps 1800 s/2 h/8 GB/0 wells、同合法实验包（H=3/A=3/Y binary） |
| 两跑 | 同 seeds、独立进程、结果 JSON 逐字节、telemetry 单独 |

- **环境**：H=3/A=3/Y binary；p(h)=[.3,.4,.3]；μ/b/π_1/π_2/m_true/m_wrong 冻结；C_H=20；评价独立、target 不作标签、分配不复用评价。
- 每 replicate 先用 initial/behavior 300 units（h~p、a~b、Y~Bernoulli μ）供固定 updater；每 arm 再抽 300 allocation units（h~p、a~arm allocation weights、Y~Bernoulli μ），用于分配诊断；**不计算效果/学习比较**。

## 2. 六 arms（仅分配诊断）

| id | 角色 | 规则 |
|---|---|---|
| S_shared_score | candidate | shared-score Q_k(b) 分配 |
| S_random | baseline | 随机合法分配 |
| S_gp_uncertainty | baseline | GP/不确定性分配 |
| S_decision_AL | **显式等预算强基线** | decision active learning |
| S_optimal_experimental_design | **显式等预算强基线** | optimal experimental design |
| S_DR_MLE_allocation | standard baseline | DR+MLE 最优分配 |

- 同 learner/updater；只改分配；**不输出 decision utility/regret/top-k/学习效果比较**；标准 DR/TMLE+最优分配等预算复制/超过→`no_increment`/撤判定留 Stage3。

## 3. per-arm 输出（13 字段）/判据/失败类别

- **字段**：`arm_id, replicate_id, allocation_weights, realized_allocation_frequency, H_summary, delta_summary, allocation_Q, variance_term, clipping, equal_budget_audit, two_run_sha, pass, failure_category`。
- **通过判据**：① allocation weights 在单纯形、b≥b_min、支持合法动作；② H/δ 摘要有限（无 NaN/inf），clipping count/bias bound 报告；③ allocation-Q（full/noise/bias²）报告、不作效果解释；④ 等预算审计（n_alloc=300/feedback=300/tuning≤20/caps/合法包）通过；⑤ per-arm two-run SHA 一致；⑥ 无禁输出。
- **失败映射**：支持/正性→`support/positivity`；H/δ 非有限→`nonidentifiable`；Q/截断报告→`calibration`；等预算→`compute_budget_exceeded`；two-run→`two_run_mismatch`；评价复用/禁输出→`leakage`；链→`chain_mismatch`。

## 4. G1–G6 / 失败类别 13

| 门 | 规则 | 失败类别 |
|---|---|---|
| G1 | b>0 on π support、b≥b_min、动作支持、随机化记录 | support/positivity |
| G2 | C_H=20；clipped≠exact；报 bias/bound | calibration |
| G3 | Q full≥noise；错设 bias² 非零/未知 | calibration |
| G4 | 评价独立、target 不作标签、分配不复用评价 | leakage |
| G5 | 两跑结果 JSON 逐字节 | two_run_mismatch |
| G6 | schema 先写、caps 1800 s/2 h/8 GB/0 wells | compute_budget_exceeded |

**13 项失败类别**：`design_invalid: support|positivity|propensity|leakage|calibration|compute_budget_exceeded|nonidentifiable|two_run_mismatch|chain_mismatch`、`unreachable_gate`、`precision_insufficient`、`no_increment`、`inconclusive`。

## 5. 两跑/预算/schema/单测

- **两跑**：run1/run2 独立进程、同 seeds；结果 JSON（无 telemetry）逐字节；`run_shas` 记录；不一致→`two_run_mismatch`。
- **预算**：caps 1800 s/2 h/8 GB/0 wells；执行前最终实现 pilot 实测冻结 canonical；main=10×(300+6×300)=21,000 units；projected wall 必须由 pilot 验证≤caps。
- **schema**：top keys 含 `per_arm`/`sample_semantics`；per-arm 13 字段/判据/失败映射/13 类别/forbidden fields 冻结；JSON 无 telemetry。
- **骨架单测（本轮仅算术，不训练/不比较）**：DR identity gap 0.0；clipping detected bias −0.026407185629；collinear rank 1；π=b H−1 0.0；allocation ratios [1.21722846, 1.16686763]；failure_categories=13（含 chain_mismatch）；per-arm 13 字段；sample 21,000/18,000；seeds overlap=[]。

## 6. 停止/边界/批准清单

- 停止：π=b→H=1 退化；共线/分离/无支持→nonidentifiable；零支持/极端权重→support/positivity；截断→calibration；评价复用→leakage；两跑/链/预算→对应类别；不改旧判定/门槛；不放宽/改阈值/换端点。
- 边界：只更新功能均值≠细胞动力学；无完整序贯 history/propensity/删失→不称序贯 DR；支撑研究/机制账 only；不执行 Stage3/真实数据/湿实验；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定；不恢复停止实验；M3 不与 M1/M2 混同；N1 不作证据；data readiness open（C203/C205/C210）。
- **批准清单**：① 17 文件链+Stage1 状态；② seeds/样本语义（R=10/300 initial/6×300 alloc/21,000/18,000）；③ per-arm 13 字段/判据/失败映射；④ 13 失败类别含 chain_mismatch；⑤ 六 arms 同预算；⑥ G1–G6/caps/pilot 实测冻结/schema/两跑；⑦ 边界。Stage2 执行须另立独立挑战+Lead 批准。
