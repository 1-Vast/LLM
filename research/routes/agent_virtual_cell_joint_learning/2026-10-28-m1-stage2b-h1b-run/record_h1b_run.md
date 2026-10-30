# record_h1b_run —— R204-M1 H1b 可分辨 TV 测量执行记录

2026-10-28 · 角色：独立实现者（endpoint-auditor）。
**任务：R204-M1-H1B-EXEC（机制账、compute-only、0 wells；不报效果）。** 只写 `research/2026-10-28-m1-stage2b-h1b-run/` 与 tmp/；未改 C215/C216/C217/H1b 预注册/M1 设计链/M2/M3/N1/A-B-D/旧门槛/旧判定/代码；未执行真实数据/湿实验。

## 0. 时间线

| 时间（Asia/Shanghai） | 事件 |
|---|---|
| — | 读 task-193、Lead DECISION、H1b PROBLEM/DESIGN/floor/schema、C215/C216/C217、M1 Stage2 链 |
| — | 新建 `2026-10-28-m1-stage2b-h1b-run/`；先写 `schema_h1b_run.json`（链/旧新分离/H1b 测量/16 字段/caps） |
| — | 实现 `run_h1b.py`：链核验、Pθ/C-MDN、hash 分箱 B=16/N_eval 32768、16 cells、pilot/main |
| — | 首跑 16/16 PASS；发现 result 含 pilot/main timing 导致两跑字节不同；移除 telemetry 后重跑两独立进程 |
| — | 最终两跑 result `2ECA912B…` 逐字节一致；cells/diag 一致；写 report/record/usage |

## 1. 冻结/链

- H1b 预注册：PROBLEM/DESIGN/floor.py/floor.json/schema/report/record；C215/C216/C217；Lead 决定；全部 SHA 实算 match；无 chain_mismatch。
- Pθ 尺度：**c .5²/M .1²/d .1²**；σ=.1+.4sigmoid(dᵀx)；box[-2,2]^4；K=3/[.5,.3,.2]；param seed 20261301。
- H1b 测量：hash 8-bit/维→code→cell=code mod B；B=16、N_eval=32768、K=1；fixed a=0；X~N(0,I_d)；oracle 独立同 N。
- C-MDN：K=3、hidden 128、2 ReLU、NLL/Adam lr1e-3/wd1e-5/batch256/epochs200；y 标准化/grad clip≤10 仅数值稳定，不改分布假设。

## 2. 执行结果

- **pilot（16 cells）**：wall 178.299 s、CPU 271.984 s、memory .23053 GB；caps PASS。
- **main（16 cells）**：wall 172.548 s、CPU process cumulative 541.125 s、memory .23173 GB；caps PASS。
- **16/16 cells PASS**；TV .00964–.02338≤tol_d .049/.050/.049/.048。
- **H1b verdict = `h1b_measurement_pass`**；failure None；无 design_invalid。
- **两跑** result `2ECA912BF74100674AF8E6B02FFCECD000E22ED3D44611FB5EB5FEB6B21F06C9`；cells CSV `D48A5022…`；diagnostics `C7D78F1B…`；timing 单独；JSON 无 telemetry。
- **未输出** effect/decision utility/regret/top-k/方法比较；不称旧 gate 通过。

## 3. 旧协议不变

- C216 旧 H1 **0/16 FAIL、design_invalid: projection** 不变；C217 归因不变；旧容差 d8 .12/.10/.08/.07、d16 .14/.11/.09/.08、d32 .16/.13/.11/.10、d64 .18/.15/.13/.12 不变。
- 未改 C216/C217 文件；未把 H1b 写成旧 H1 修正/重跑/通过。

## 4. 产出

| 文件 | 说明 |
|---|---|
| `run_h1b.py` | H1b 实现 |
| `h1b_result.json` | 两跑一致结果（无 telemetry） |
| `h1b_cells.csv` | 16 cells TV/tol/pass |
| `h1b_diagnostics.json` | 链/旧新分离/诊断 |
| `schema_h1b_run.json` | schema/失败模板（先写） |
| `timing_h1b_run.json` | pilot/main canonical telemetry |
| `report_h1b_run.md` | 报告 |
| `record_h1b_run.md` | 本记录 |
| `usage_h1b_run.json` | 命令/SHA/attestation，最后写出 |

## 5. 边界

机制账 only；不执行真实数据/湿实验；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定/旧容差；M1 不与 M2/M3 混同；N1 不作证据；data readiness open（C203/C205/C210/C214）；用户 public-only。
