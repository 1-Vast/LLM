# record_n1_effect —— R203-N1 效果执行审计记录（合成机制账；verdict=no_increment）

2026-10-28 · 角色：ON1/ON2/ON2.2/ON3 执行者（非提案者）。任务：R203-N1-EXEC（按 Lead `DECISION_R203_N1_EXEC.md` 执行一次；仅合成机制账、compute-only、0 wells）。**不称药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定/门槛；未跑 T2/T3/真实响应/湿实验。**

## 1. 时间线

| 时间（本机） | 事件 |
|---|---|
| 11:02–11:04 | 读 task-142、`DECISION_R203_N1_EXEC.md`、PROBLEM/DESIGN_N1_EXEC、exec_plan.py/json、v0.4/C204 链；核对 SHAs |
| 11:04–11:07 | 写 `run_n1_effect.py`（只读导入冻结 generator；U/regret/方法/headroom/pilot/两跑/分析） |
| 11:07–11:13 | run1：首次写 summary 时 ndarray 序列化错误；修复 sanitize/summary 后重跑 |
| 11:13–11:29 | run2 同 seeds 独立进程；发现 `n_units_total` 误算（dict 长度 bug）；修正为 15,000 |
| 11:29–11:47 | 修正后重跑 run1/run2；两跑一致 |
| 11:47–11:56 | 发现 summary 缺 `secondary_holm_p`（schema 要求）；补字段后重跑 run1/run2（各约 7–8min） |
| 11:56–12:06 | 最终两跑逐字节一致 SHA `CAAC6718…`；写报告/记录/usage |

## 2. 输入（只读；SHA256）

| 文件 | SHA256 |
|---|---|
| `DECISION_R203_N1_EXEC.md` | `930F1567254095945C228532AB8D1576915AAD01AC8ACC06185D99B573C174AD` |
| `PROBLEM_N1_EXEC.md` | `9993F0BA…`（见 exec_plan.json 链） |
| `DESIGN_N1_EXEC.md` | `29F784E7…` |
| `exec_plan.py` / `exec_plan.json` | `843DEC39…` / `BECEE7F8…` |
| v0.4 链（7 文件） | PROBLEM `5C513D94…`、DESIGN `94BAB805…`、generator py `AA5D454A…`、generator json `35E41136…`、V4_validation `254BEBAB…`、pilot `A4C7E0F6…`、DECISION pre `930F1567…` |
| C204 链（8 文件） | run_n1_gates `D2AA831F…`、n1_gates `529C1D2E…`、rows `78457E1F…`、timing `5A52E42F…`、schema `F2D561D9…`、report `38CFD34C…`、record `DA21E2D9…`、usage `F795C15D…` |
| V4_MODEL_SPEC | `A69B845D9808A93444042CC034F37EA4E9AA74C03835BACC39DF5445A6BF3289` |

## 3. 输出（本任务；只写 `2026-10-28-n1-effect-run/` 与 tmp/）

| 文件 | SHA256 |
|---|---|
| `run_n1_effect.py` | `4698E7452258D6BF51E003385BF37E02A8C1FC8A517735689F0AA9F79BC11B7B` |
| `n1_effect.json`（两跑一致） | `CAAC6718E002EA1C97D1F179B0B284BA0639479E8C3FA2FBFDEF3326E24D7044` |
| `n1_effect_rows.csv` | `60EA6BA7A227C3BEC7CFB75AA341ABD2BC1F36EC9233A2CAAF67E6DFF3D995FE` |
| `n1_effect_summary.json` | `342713DA9E7E6DE75DD43E5AB8CED4A8490BA11769C8B9E2BA7D6310507CA651` |
| `headroom_precheck.json` | `EC42006F3AA3990AA9C2D219A66888DDF4C70B7654FFBEAA38A951263551F7B2` |
| `timing_n1_effect.json` | `5089B4E9DB6320313CAFA5D495FF732713DD94671E18352EE7C22E4C891A55EF` |
| `schema_n1_effect.json` | 见文件 |
| `report_n1_effect.md` | 见 usage/复核方 |
| `record_n1_effect.md` | 本文件（SHA 见 usage/复核方） |
| `usage_n1_effect.json` | 最后写出（SHA 见复核方） |

## 4. 执行结果（预注册）

- 链核验 PASS；pilot/G7：per-rep ~0.69–0.76s、projected main ~313–342s、mem ~0.036GB、caps PASS、B2 audit PASS。
- headroom：U0(B2)=**0.337630279**、headroom **0.662369721≥δ**（PASS，非 ceiling）。
- 主执行：50 reps×300 units×7 methods；**15,000 paired units**；primary `D=R(M)−R(B2)` mean **+0.00605165**、CI95 **[0.00328402,0.00881927]**、Holm p **0.00017858**；成功三项未满足（mean 未≤−δ、CI upper>0）→ **`no_increment`**。
- family6（预注册）：B1/B2 +0.00605165（Holm p .00017858；冻结实现中 `FullRetrain(StaticAdd)` 未覆写 fit，B1/B2 估计相同——冻结代码细节，未改）；B3 +0.00630875、B4 +0.00652235、B5 +0.15819377、B6 +0.16286624；仅预注册报告，不作算法主张。
- 保守 MDE **0.04798268**；actual cluster-robust MDE **0.00385839≤.05**；precision PASS。
- 两跑 `n1_effect.json` 逐字节一致 SHA **`CAAC6718…`**；wall run1/run2 total **454.31/431.51 s**、CPU **433.5/413.6 s**、mem **0.0974/0.0973 GB**；caps PASS。
- 失败类别：`no_increment`（预注册分类）；无 design_invalid/chain/two-run/schema/leakage/budget 失败。

## 5. 实现备注/边界

- effect runner **只读导入**冻结 generator `AA5D454A…`；未改 λ/特征/初始化/方法类；B1/B2 冻结类实现差异缺失已如实记录，未执行时修改。
- U 定义按预注册公式 `U=(ybar_control−ybar_p)/(ybar_control−ybar_floor)`；因冻结 generator 无 no-drug 对照，control/floor 取 universe 内 expected plan response 的 max/min（写入 report/记录）；U∈[0,1]，headroom 用 U_max=1。
- 仅合成机制证据；不称药理/真实决策/迁移/机制/新颖性；`no_increment` 不写"双预算/方法无效"；不晋升代码；不改旧门槛；0 wells；未用 A/B 资源；T2/T3 未执行。
