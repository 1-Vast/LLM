# record_m3_stage3_run —— R204-M3 Stage3 合成学习比较执行记录

2026-10-28 · 角色：ON1/ON2/ON3/D1/D3/D5/A/B 线同一独立审计/实现者。
**任务：R204-M3-S3-EXEC（支撑研究/机制账、compute-only、0 wells；不报真实效果）。** 只写 `research/2026-10-28-m3-stage3-run/` 与 tmp/；未改 exec prereg/M3 Stage1/Stage2/M1/M2/N1/A-B-D/旧门槛/旧判定/代码；未执行真实数据/湿实验；0 wells。

## 0. 时间线

| 时间（Asia/Shanghai） | 事件 |
|---|---|
| — | 读 task-189、Lead DECISION、v0.4 PROBLEM/DESIGN/exec plan/schema、Stage1/C209、Stage2/C213、ERRATA |
| — | 新建 `2026-10-28-m3-stage3-run/`；先写 `schema_m3_stage3_run.json`（16 字段/三 SHA/primary/失败/caps） |
| — | 实现 `run_m3_stage3.py`：35 链核验、toy canonical、固定反馈/评价、shared-score 分配、7 纯 learner arms、common evaluation、Holm family6、pilot/main、两跑/timing |
| — | canonical 结果：primary mean ΔR .01、CI [−.0096,.0296]、Holm 1.0 → **no_increment**；G1–G6 PASS；7/7 per-arm 有效 |
| — | 两独立进程 result/CSV/diagnostics 逐字节一致；写 report/record/usage |

## 1. 输入（只读）

| 文件 | 用途 |
|---|---|
| `DECISION_R204_M3_S3_EXEC.md` | Stage3 批准范围/边界 |
| `PROBLEM/DESIGN_M3_S3_EXEC_v0_4.md` | 固定反馈/评价/7 arms/primary/失败 |
| `exec_plan_m3_s3_v0_4.json` | 35 文件链、seeds、streams、allocation、endpoints、caps |
| `schema_m3_s3_exec_v0_4.json` | 16 字段/三 SHA/13 失败/toy |
| M3 Stage1/C209、Stage2/C213 | 前序 PASS/引用 SHA |
| ERRATA C207/C209/C213/C215/C216/C217 | 边界/口径 |

## 2. 执行/结果

- **链**：35 文件 + Lead 决定 match；chain.pass=True；seeds overlap=[]、unique=true；无 chain_mismatch。
- **toy**：feedback `0696F595…`、evaluation `01063FFF…`、policy `6A976C3C…` 重算一致。
- **pilot**：2 reps×7 arms×300 units；wall **.183393 s**、CPU **.1875 s**、memory **.0012501 GB**；caps PASS。
- **main**：R=10；wall **.669204 s**、CPU **.859375 s**、memory **.0015297 GB**；caps PASS。
- **样本**：300 shared feedback+300 shared evaluation/replicate；总 3,000/3,000；7 arms 同流；10 个 replicate 的 stream SHA 在结果。
- **per-arm**：7/7 有效（16 字段齐全；三 SHA 相同；10 个 per-replicate regret；成本；tuning 0）。
- **primary**：mean ΔR **.0100**、CI **[−.0096,.0296]**、Holm **1.0** → 未通过；failure **no_increment**；不称 candidate 优于标准。
- **G1–G6**：全 PASS。
- **两跑**：`m3_stage3.json` `60928345…`；CSV `05BE1D69…`；diagnostics `A5DD8683…`；timing 单独。
- **未输出**真实效果/药理/决策/迁移/新颖性；无 allocation 比较。

## 3. 产出

| 文件 | 说明 |
|---|---|
| `run_m3_stage3.py` | Stage3 实现（固定反馈/7 learner） |
| `m3_stage3.json` | 结果（两跑一致；无 telemetry） |
| `m3_stage3_per_arm.csv` | 7 arms ×16 字段 |
| `m3_stage3_diagnostics.json` | 链/toy/G/primary/per-arm |
| `schema_m3_stage3_run.json` | schema/失败模板（先写） |
| `timing_m3_stage3_run.json` | pilot/main canonical telemetry |
| `report_m3_stage3_run.md` | 报告 |
| `record_m3_stage3_run.md` | 本记录 |
| `usage_m3_stage3_run.json` | 命令/SHA/attestation，最后写出 |

## 4. 边界

- 支撑研究/机制账 only；未执行真实数据/湿实验；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定；不恢复停止实验；M3 不与 M1/M2 混同；N1 不作证据；data readiness open（C203/C205/C210/C214）。
- **no_increment** 仅为该预注册 synthetic primary 的判定；不推广为标准 DR/TMLE/学习无效；不把 allocation/feedback 优势算进 primary；不做 allocation 比较。
- 评价 action 共同样本不作任意 arm policy 的 population value；per-arm regret 用 held-out h+known-truth μ+arm policy。
- 未改公式/阈值/端点/seed 救结果；未换端点；未晋升代码。
