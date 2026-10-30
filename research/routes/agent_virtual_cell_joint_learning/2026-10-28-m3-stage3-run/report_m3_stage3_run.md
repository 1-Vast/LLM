# report_m3_stage3_run —— R204-M3 Stage3 合成学习比较执行报告（支撑研究；不报真实效果）

2026-10-28 · 角色：ON1/ON2/ON3/D1/D3/D5/A/B 线同一独立审计/实现者（endpoint-auditor）。
**状态：Stage3 合成学习比较执行一次完成；支撑研究/机制账 only；compute-only；0 wells；未执行真实数据/湿实验；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定。**

依据：Lead `DECISION_R204_M3_S3_EXEC.md`；冻结 v0.4 链（35 文件 + Lead 决定）；M3 Stage1/C209；Stage2/C213；ERRATA C207/C209/C213/C215/C216/C217。

## 0. 判定（一屏）

- **verdict = `no_increment`；failure_category = `no_increment`**（primary 未达冻结成功门；标准 DR/TMLE 等预算未被超过）。
- **链核验**：35 文件 SHA + Lead 决定 match；`chain.pass=True`；无 chain_mismatch。
- **final pilot**（2 reps×7 arms×300 units）：wall **0.183393 s**、CPU **0.1875 s**、memory **0.0012501 GB**；caps PASS。
- **main**（R=10）：wall **0.669204 s**、CPU **0.859375 s**、memory **0.0015297 GB**；caps PASS。
- **primary**：mean ΔR=**0.0100**，95% CI **[−0.0096, 0.0296]**，Holm p=**1.0**；**未满足 mean≤−.05 ∧ CI upper<0 ∧ Holm p<.05**。
- **G1–G6 全 PASS**；7 arms 全部 **16 字段有效**；两跑逐字节；三 SHA 一致；**未输出真实效果/药理/决策/迁移/新颖性**。

## 1. 链核验/冻结设置

- 35 文件 SHA（M3 v0.2 + Stage1/C209 + Stage2 exec v0.2 + Stage2/C213 + Lead 决定）全部实算 match；`chain.pass=True`；seeds overlap=[]、unique=true。
- env seed 20261601；feedback 20261601–10；evaluation **20261701–10** 独立；arms 20261611–80；headroom 20261681–90。
- 7 arms 全部 **固定 shared-score allocation**、同 feedback/evaluation、同预算；**无 optimal allocation arm**、**不做 allocation 比较**。
- shared-score：`Q=p(h)π2²[Var+(μ−m_wrong)²]/b`，`w=Q/Σlegal Q`；b_min=1e-6；C_H=20 **仅 H clipping 诊断，不进 weights**。
- 环境 H=3/A=3/Y binary；p/μ/b/π2/m_wrong/C_H=20 冻结；100% synthetic、0 wells。

## 2. 样本/三 SHA/leakage

- 每 replicate：**300 shared feedback (h,a,Y)** + **300 shared evaluation (h,a)**；R=10；总 **3,000/3,000**；7 arms 复用同一 feedback/evaluation。
- canonical：feedback `"h,a,Y\n"`、evaluation `"h,a\n"`、policy token `shared_score_fixed_same_feedback_stream`；SHA256 uppercase。
- **toy**：feedback `0696F595…`、evaluation `01063FFF…`、policy `6A976C3C…` **重算一致**。
- 每 replicate 7 arms 的 feedback/evaluation SHA **逐字节一致**；无 leakage；全部 10 个 replicate 的 stream SHA 列表在结果 `stream_shas`。
- **evaluation action a_j 是 shared-score 共同样本**；per-arm regret 用 held-out `h_j` + known-truth μ + arm 自己的 argmax policy；**a_j 不被写成任何 arm 的 population policy value**。

## 3. per-arm 16 字段（7/7 有效）

| arm | update rule | mean ΔR | CI95 | Holm p | valid |
|---|---|---:|---|---:|---|
| A_candidate_score_tilt | one-step score-tilt | **0.0100** | [−0.0096, 0.0296] | 1.000 | true |
| A_full_history_retrain | full-history retrain | 0.0000 | [0,0] | 1.000 | true |
| A_importance_weighting | importance-weighted | 0.0000 | [0,0] | 1.000 | true |
| A_DR_targeting | DR targeting | 0.0100 | [−0.0096, 0.0296] | 0.9519 | true |
| A_TMLE_targeting | TMLE targeting | 0.0100 | [−0.0096, 0.0296] | 0.9519 | true |
| A_value_aware | value-aware | 0.0000 | [0,0] | 1.000 | true |
| A_standard_DR_TMLE | standard DR/TMLE | 0.0000 | [0,0] | 1.000 | true |

- 16 字段齐全：arm_id/replicate_id/update_rule/allocation_policy/n_feedback/n_eval/tuning_configs/cost_ledger/per_replicate_regret/mean_DeltaR/CI95/holm_p/pass/feedback_stream_sha/evaluation_stream_sha/allocation_policy_sha。
- 7 arms 的 feedback/evaluation/policy SHA 相同（同共享流）；三 SHA 均存在。
- **`pass`=per-arm 有效性**（有限/10 reps/stream SHA/成本），不表示效果；**primary 另行判定**。

## 4. 主端点/功效

- primary：**A_candidate_score_tilt vs A_standard_DR_TMLE**；δ=.05；成功=mean ΔR≤−.05 ∧ CI upper<0 ∧ Holm p<.05；family=6 Holm。
- 实际：mean **0.0100**、CI upper **0.0296**、Holm p **1.0** → **primary 未通过**，登记 **`no_increment`**；**不称 candidate 优于标准**。
- headroom=**0.9797**≥.05；MDE80=**.04798268**≤.05；n_req_cluster=**278**；cluster=独立 replicate；**6,282/1,573 仅 Fisher-z**，非决策门。
- **不把 allocation/feedback 优势算进 primary**；不做 allocation 比较；不换端点。

## 5. G1–G6

| 门 | 结果 |
|---|---|
| G1 支持/程序 | PASS（b>0、b≥b_min、合法动作） |
| G2 截断 | PASS（C_H=20 仅诊断） |
| G3 learner 拟合 | PASS（7 pure learner arms；固定 shared-score） |
| G4 无泄漏 | PASS（同反馈/评价、评价不用于拟合/选择；三 SHA 一致） |
| G5 两跑 | PASS（两独立进程逐字节） |
| G6 schema/预算 | PASS（schema 先写；caps 1800s/2h/8GB/0 wells） |

13 失败类别已登记；本轮 `failure_category=no_increment`（非 design_invalid）。

## 6. 两跑/预算/产出

- 两独立进程 `m3_stage3.json` 逐字节 **`609283453042B9A64C2CD3822725C0BEB1E2730CCAC8B342AC32001A536EB68C`**；per-arm CSV、diagnostics 一致；timing 单独；JSON 无 telemetry。
- pilot/main 实测 caps PASS；未用 Stage2 pilot 作执行 pilot；未用 planning/单测数字代替。
- 结果 JSON 无 telemetry；schema/失败模板先写；toy canonical 重算。

## 7. 产物 SHA

| 文件 | SHA256 |
|---|---|
| `run_m3_stage3.py` | 见 usage |
| `m3_stage3.json`（两跑一致） | `609283453042B9A64C2CD3822725C0BEB1E2730CCAC8B342AC32001A536EB68C` |
| `m3_stage3_per_arm.csv` | `05BE1D69BEF4E33C845C1CE623DB1A7C1C1CF652B98A8D9C302C6B62695A10DF` |
| `m3_stage3_diagnostics.json` | `A5DD86831D802AADFE73C24C0E7B8876AEE6A9585FAA7DD5F63F071321CA043B` |
| `schema_m3_stage3_run.json` | 见 usage |
| `timing_m3_stage3_run.json` | 见 usage；result SHA `60928345…` |

## 8. 结论/边界

- Stage3 synthetic learning comparison **primary no_increment**；**不构成真实效果/药理/真实决策/迁移/机制/新颖性证据**；不称 M3 增量。
- **不把 standard DR/TMLE 等预算复制/超过写成其他结论**；primary 未通过；无 allocation 比较；无真实数据。
- 真实数据/湿实验/Stage3 真实确认未执行；data readiness open（C203/C205/C210/C214）；需独立预注册+挑战+Lead 批准；不得用合成/RNA 替代独立功能决策。
- 机制账 only；不晋升代码；不改旧判定；不恢复停止实验；M3 不与 M1/M2 混同；N1 不作 M3 证据。
