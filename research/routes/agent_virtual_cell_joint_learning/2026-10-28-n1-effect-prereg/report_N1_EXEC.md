# report_N1_EXEC —— R203-N1 效果执行预注册报告（机制账；不运行效果）

2026-10-28。对象：R203-N1 效果执行（M vs B1–B6；primary=held-out decision regret）。依据：`DECISION_R203_N1_PREREG.md`（仅批准执行预注册）、C204 `qualification_pass`、N1 v0.4 链、R203-P1 链、ERRATA C197/C199/C201/C203。
**状态：预注册草案；未运行效果比较/未报告方法差异/未读真实响应；机制账 only；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定；0 wells/compute-only。**

## 0. 交付物

- 问题定义：[PROBLEM_N1_EXEC.md](PROBLEM_N1_EXEC.md)（`9993F0BA…`）
- 执行设计：[DESIGN_N1_EXEC.md](DESIGN_N1_EXEC.md)（`29F784E7…`）
- 规划算术/种子/SHA 校验：[exec_plan.py](exec_plan.py)（`843DEC39…`）→ [exec_plan.json](exec_plan.json)（`BECEE7F8…`）
- 记录/用量：[record_N1_EXEC.md](record_N1_EXEC.md)、[usage_N1_EXEC.json](usage_N1_EXEC.json)

## 1. 执行前链核验（已通过）

`exec_plan.py` 本地核验：**chain_pass=true / full_pass=true**，15 个链文件 SHA 全部匹配；V4_MODEL_SPEC SHA `A69B845D…` 匹配；V4 独立 gate（seed 20261062：503.04246827/64.42138097/[376.77888173,629.30605481]）；G1 k=976/20000、point .0488、Wilson .05187354；G2 1.000/1.000/1.000；G3 full 143/600/140/3；G7 pilot .0455 s/rep、20.48 s main、.04 GB、B2 audit PASS。**任一不匹配 → stop `design_invalid: chain_mismatch`。**

## 2. 执行种子/样本（独立于 gate seeds）

| 项 | 冻结值 |
|---|---|
| 禁用 seeds | 20261030、20261061、20261062、20261063（gate/dev）；执行时不得复用 |
| 执行 replicate seeds | `20261070 + r`，r=0..49 → **20261070–20261119**（R=**50**） |
| headroom 预检 seeds | `20261130 + r`，r=0..19（**20** reps；独立） |
| 方法随机 seeds | `20262000 + r*10 + method_index`（method idx 0..6） |
| n_units | **300**/replicate |
| 两跑 | run1/run2 独立进程、**同 seeds**；结果 JSON（无 telemetry）逐字节一致；否则 `design_invalid: two_run_mismatch` |
| 重合检查 | 与 gate seeds 重叠 **[]**；全 seed 唯一 **true**（exec_plan.json） |

## 3. 方法/等预算

M（N1）vs **B1 full retrain、B2 static S-add（关键强基线）、B3 hierarchical/EB、B4 GP、B5 random plan-pair、B6 decision AL**。统一：T=6（fit 4/held-out 2）、每轮 1 次 feedback、query 数同、特征信息同、prior/初始数据同、调参≤**20**、同 compute/wall/内存 cap；B5/B6 随机性用预注册 method seeds。**B2 等价审计**（执行时最终 runner 再确认：initial-data hash/menus/query=6/prior/tuning=20/shared dataset seed）；失败→`design_invalid: leakage`/`generator_misspecified`。执行只读导入冻结 `generator_n1_v0_4.py`（SHA `AA5D454A…`），不改冻结代码。

## 4. Primary / 多重性 / headroom

- **Primary**：paired held-out decision regret `D_i=R_i(M)−R_i(B2)`（lower better，δ=**0.05** normalized）；`U∈[0,1]`，held-out 轮不更新。
- **成功（全部满足）**：mean ΔR≤−δ ∧ 95% CI upper<0 ∧ **Holm 校正后 p<.05**。
- **多重性**：family=**6**（M vs B1–B6；primary=M vs B2）；**Holm** α=.05；secondary 同 family；primary 失败时 secondary 仅描述性。
- **不得换端点**：primary 固定为 held-out regret；headroom 预检（独立 20 reps×300 units）：`headroom=U_max−U0(B2)`；headroom<δ → `unreachable_gate`（不解释为算法失败；B2 近满分 → 另立 budget-to-target，不静默换端点/降 δ）。

## 5. 分析/单位/MDE

- 执行规模：**n_units=300 × R=50 × 7 methods × T=6**；paired 决策单元共 R·n_units=**15,000**。
- 分析：全部 paired `D_i` 的均值 ΔR；**cluster-robust SE 按 replicate（G=50）**；95% CI（t_{49}）；报告每基线 mean/CI/Holm p。
- **保守 MDE**：单 replicate 口径 n_units=300、deff=1+(5−1)×.30=**2.2**、n_eff=**136.36**、SD(D) 保守 .20 → **MDE80=0.04798≤.05**；n_req(cluster)=**278≤300**；实际分析含 50 replicates，精度不差于保守值（报告两者）。
- 若实际 cluster-robust SD 使 MDE>δ → `precision_insufficient`（停/扩资源，不算法失败）；不事后加 n/降 δ。

## 6. 预算/资源/两跑

main 300×50×7、T=6；**wall≤1800 s/run、CPU≤2 h、内存≤8 GB**；**0 wells/compute-only**；不用 A/B 资源。C204 pilot：**per-rep .0455 s、main 20.48 s、memory .04 GB**（执行前最终 runner 重跑 2-rep pilot；若投影超 caps → `design_invalid: compute_budget_exceeded`，不得减 n_units/R/methods）。两跑结果 JSON 无 telemetry；wall/CPU/内存只写 `timing_n1_effect.json`；result SHA 写 `run_shas`。

## 7. Schema/失败类别

- top keys：`task_id/status/frozen_chain/seeds/design/per_replicate/summary/headroom/cost_ledger/run_shas/failure_category/verdict`。
- per_replicate/per_method：`replicate_id/dataset_seed/method_seeds/method/n_units/heldout_regret_mean/heldout_selected_U_mean/oracle_U_mean/n_queries/n_feedback/tuning_configs`。
- summary：`primary_mean_DeltaR/primary_CI95/primary_holm_p/secondary_effects/secondary_holm_p/n_units_total/n_replicates`。
- **禁列**：`prediction_accuracy/topk_hit/budget_to_target_effect/exploratory_endpoint` + 药理/真实决策/迁移/机制/新颖性字段；无未预注册终点。
- 失败类别：`design_invalid: chain_mismatch|schema_mismatch|two_run_mismatch|leakage|compute_budget_exceeded|generator_misspecified|calibration_failed|nonidentifiable`；`unreachable_gate`；`precision_insufficient`；`no_increment`；`inconclusive`。失败只写类别、**不报方法差异**。

## 8. 边界

机制账 only（合成、compute-only、0 wells）；不称药理/真实决策/迁移/机制/新颖性；合成≠药理；技术重复≠独立培养；不拼 ΔEMAX；不使用 A/B 资源；不晋升代码；不改旧门槛/判定；不恢复已停止实验；**效果执行须另立独立挑战 + Lead 批准**；本任务未运行效果、未报告方法差异。

## 9. 产物 SHA/确定性

| 文件 | SHA256 |
|---|---|
| `PROBLEM_N1_EXEC.md` | `9993F0BA259AD22CEDC63D816DB168449D0E8806E8B995903D941A6DF16D0B7B` |
| `DESIGN_N1_EXEC.md` | `29F784E7E71CEBEC3873097BFAAD1A080FCB26F49F4D6C78D2A14D16A538F5F6` |
| `exec_plan.py` | `843DEC399D88DF88FE733D2A286CC75E8655E73CD1A7A483B250048AB0346E27` |
| `exec_plan.json` | `BECEE7F8B64A0919CE435AAE614A911E73D01AA0C9BD6347DF1CFF1E1BFBBA39` |
| report/record/usage | 见 `usage_N1_EXEC.json` |

**确定性**：`exec_plan.json` 两跑逐字节一致（`BECEE7F8…`；wall 0.0/0.1 s）；JSON 键排序/无时间戳；无 telemetry。

## 10. 建议

1. **提交本执行预注册做独立挑战**（重点：种子独立性/禁用 seeds、等预算与 B2 强基线、primary 成功三项/Holm family、cluster-robust 分析/保守 MDE、两跑/预算/schema/失败类别、链核验）。
2. 挑战通过后请 Lead 明确批准 **N1 效果执行**（仍为机制账：合成、compute-only、0 wells；不批药理/真实决策/迁移/机制/新颖性）；执行须按本预注册逐条执行，不得改 seeds/端点/多重性/预算。
3. **不做**：效果比较/结论、代码晋升、旧判定修改、恢复已停止实验。
