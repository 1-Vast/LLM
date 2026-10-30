# record_m2_stage1 —— R204-M2 Stage 1 执行记录

2026-10-28 · 角色：ON1/ON2/ON3/D1/D3/D5/A/B 线同一独立审计/实现者。
**任务：R204-M2-STAGE1（仅机制账、受控真值检查、compute-only、0 wells）；未运行 Stage2/3/真实数据/湿实验/效果/增益/方法比较。**

## 0. 时间线

| 时间（Asia/Shanghai） | 事件 |
|---|---|
| 11:37 | 读 task-148、Lead DECISION、冻结 v0.2 PROBLEM/DESIGN/formalism/schema/timing、R204 BRIEF/ERRATA |
| 11:37–11:45 | 新建 `2026-10-28-m2-stage1/`；冻结 schema 先写；实现 `run_m2_stage1.py`（线性闭合测试床、非线性非闭合、部分支持、可辨识、gauge、随机化、frozen arithmetic、pilot/timing） |
| 11:45–11:48 | 调试/重跑 canonical；修正 balance（记录 X0 匹配随机化）与非线性尺度；最终 `failed_checks=[]` |
| 11:48 | 两个独立进程运行 → result/rows/diagnostics/schema 逐字节一致；canonical timing 0.00253 s/rep、full wall 0.0667 s |
| 11:48–11:50 | 写 report/record/usage；核对 SHA；确认只写本目录与 tmp/ |

## 1. 输入（只读）

| 文件 | 用途 |
|---|---|
| `2026-10-28-m2-operator-prereg/DECISION_R204_M2_STAGE1.md` | Stage1 批准/边界 |
| `PROBLEM_M2_v0_2.md` / `DESIGN_M2_v0_2.md` | p=5 冻结规格/三例/可辨识目标 |
| `formalism_M2_v0_2.py` / `formalism_M2_v0_2.json` | 冻结形式化/算术/非闭合示例 |
| `stage1_schema_v0_2.json` | schema/failure template（先复制为 `schema_m2_stage1.json`） |
| `timing_M2_pilot_v0_2.json` | 旧 pilot 参考；**本任务最终代码重新测 canonical**，不混用旧值 |
| `deep-coupling-redesign/{report.md,BRIEF_R204.md}` | M2 定位/边界 |
| ERRATA C197/C199/C201 | 决策/资源/两本账边界 |

## 2. 实现要点

- **冻结**：p=5、A=3、d=4、cohorts=200、T=3；X=[x,x²,x³,x⁴]；φ=[1,X]；闭合 `Eφ(X_T)|X0,a=K_aφ(X0)`；记录态估计式；禁止边际捷径；不改变 p/A/d/cohorts/T/阈值。
- **测试床**：30 pure groups（10/动作，6 cohorts/组）+20 mixed groups（1 cohort/组）共 200 cohorts。
- **线性闭合 positive**：随机 K_step，T=3；pure design 拟合 full K；residual/K error 近 0。
- **非线性非闭合 negative**：x′含 x² 递归；φ powers；p=5 testbed 残差显著；另复现冻结 p=2/p=3 独立算术（2.7e-15 / 3.7576893）。
- **部分支持 negative**：仅 action 0/1；rank50/nullity25；K_2 不可辨识。
- **可辨识**：full K 75/75；mixed 20 组 75/nullity0（构造性条件性）；same-U 3/3；U=5；gauge；无支持。
- **随机化**：记录 X0 匹配 pure blocks（π 先于结果；记录态估计式）；support/balance/counts/sisters contracts；主 testbed PASS。
- **pilot/timing**：最终代码 10 reps **0.00253 s/rep**；projected 0.0607 s；full wall **0.0667 s**；caps 600 s/2 h/8 GB；0 wells。
- **schema/failure template**先写；result JSON 无 telemetry；timing 单独。

## 3. 两跑/失败

| 运行 | result JSON SHA | rows SHA | diagnostics SHA | schema SHA |
|---|---|---|---|---|
| run1（tmp/m2_run1） | `3D7DA102…A0F2A2` | `AA7CBF28…A4772` | `0EA73141…D3E40` | `3CC31B62…68BB4` |
| run2（tmp/m2_run2） | `3D7DA102…A0F2A2` | `AA7CBF28…A4772` | `0EA73141…D3E40` | `3CC31B62…68BB4` |
| canonical | 同 run1/2 | 同 | 同 | 同 |

- **failed_checks=[]；failure_category=null**；三例 positive/negative 均按预期。
- **无 design_invalid**；无 effect/gain 输出。

## 4. 产出

| 文件 | 说明 |
|---|---|
| `run_m2_stage1.py` | Stage1 实现（synthetic/controlled truth only） |
| `m2_stage1.json` | 检查结果（无 telemetry；两跑一致） |
| `m2_stage1_rows.csv` | cohort/group/U/V 行（deterministic） |
| `m2_stage1_diagnostics.json` | 可辨识/closure/randomization 诊断（deterministic） |
| `schema_m2_stage1.json` | 冻结 schema/failure template |
| `timing_m2_stage1.json` | canonical pilot/timing（telemetry，单独） |
| `report_m2_stage1.md` | 报告 |
| `record_m2_stage1.md` | 本记录 |
| `usage_m2_stage1.json` | 命令/输出 SHA/attestation，最后写出 |

## 5. 边界/未做

- **仅机制账**；Stage1 不报效果/增益/regret/方法比较/top-k；不称生物学/机制/迁移/真实决策/新颖性。
- **Stage2/3 不执行**；Stage2 真实数据当前 `data_unavailable`（C203）；不晋升代码；不改旧判定/门槛；不恢复停止实验；不拼 ΔEMAX；技术重复≠独立培养。
- 未读 O'Neil 响应/功能数据；未做湿实验；0 new wells；未改 M2 预注册/N1/A/B/D 产物。
