# record_M1_v0_2 —— R204-M1.1 三项必补执行记录

2026-10-28 · 角色：ON1/ON2/ON3/D1/D3/D5/A/B 线同一独立审计/设计者。
**任务：R204-M1.1（修 G 编号/等预算基线规格/Stage1 生成器与容差；设计，不运行效果）。** 只写 `research/2026-10-28-m1-executable-gen-prereg/` v0.2 文件与 tmp/；未改 v0.1 产物/M2/N1/A-B-D/旧门槛/旧判定/代码；未运行效果/训练/真实数据/湿实验；0 wells。

## 0. 时间线

| 时间（Asia/Shanghai） | 事件 |
|---|---|
| 当前轮 | 读 task-155、M1-C1 三项必补、v0.1 PROBLEM/DESIGN/formalism/challenge |
| — | 新建 v0.2 工作副本；先写 `stage1_m1_schema_v0_2.json`（G1–G6/生成器/基线/失败模板） |
| — | 改 `formalism_M1_v0_2.py`：输出 v0.2；加载 schema；结构化 G1–G6；baseline specs/stage1 generator；保留形式化/反例/投影/Doob |
| — | 运行两次独立进程；`formalism_M1_v0_2.json` 逐字节一致 `B7298653…988A7AE`；timing 单独 |
| — | 重写 `PROBLEM_M1_v0_2.md`/`DESIGN_M1_v0_2.md`：G1–G6、B1–B5 规格、Stage1 生成器/容差/S1-a–e；写 report/record/usage |

## 1. 三项必补

1. **G 编号统一 G1–G6**：G1 条件药效；G2 支持/程序；G3 投影/近似；G4 无泄漏；G5 两跑；G6 schema/预算。文档/JSON/schema/失败类别同步。
2. **等预算基线规格冻结**：B1 random MPC/B2 max-ent/B3 conditional MC/B4 constrained SB/B5 same-info DF；目标函数/信息集/调参≤20/计算 cap/停止/等价审计全部写入 DESIGN/schema；Stage1 检查性比较可复现；不得只比错误目标条件化。
3. **Stage1 生成器/容差冻结**：X=4/A=3/Y=4；Pθ softmax seed 20261112；eval 20261113；r(y)=y；τ=1.0；π0 full/constrained；样本量/容差/S1-a–e 判据写死；允许数值差异但阈值预注册。

## 2. 算术复核/两跑

- 反例：target A=.99665795、B=.00334205；E_A=1<E_B=2；π*_B=.73105858；仅证风险。
- 投影：KL star=.24038053 < uniform=.45067680；可执行条件核差 1.11e-16；target within-action tilt=.43647 不可执行 proposal。
- 支持/Doob：无支持 π*=0；Doob 核非药物。
- 两独立进程 `formalism_M1_v0_2.json` SHA 均 **`B72986535F3839E2BE058250DEA9D61F560DF0243AFF86329845DD361988A7AE`**；timing 单独。
- pilot：5e-6 s/rep；projected .0053 s；caps 1800s/2h/8GB；0 wells；未输出增益/效果。

## 3. 产出

| 文件 | 说明 |
|---|---|
| `PROBLEM_M1_v0_2.md` | v0.2 形式化 + B1–B5 + Stage1 生成器/容差 + G1–G6 |
| `DESIGN_M1_v0_2.md` | v0.2 执行设计（不运行） |
| `formalism_M1_v0_2.py` | 形式化/投影/反例/检查性算术；不跑效果 |
| `formalism_M1_v0_2.json` | 两跑一致结果 |
| `stage1_m1_schema_v0_2.json` | schema/G1–G6/基线/生成器/失败模板 |
| `report_M1_v0_2.md` | 报告 |
| `record_M1_v0_2.md` | 本记录 |
| `timing_M1_pilot_v0_2.json` | canonical timing |
| `usage_M1_v0_2.json` | 命令/SHA/attestation，最后写出 |

## 4. 未做/边界

- 未运行效果比较/训练/真实数据/湿实验/Stage2/3；未输出 regret/决策效用/增益/方法优劣。
- 未改 v0.1/M2/N1/A-B-D/旧门槛/旧判定/代码；不恢复停止实验；不拼 ΔEMAX；技术重复≠独立培养。
- 不称药理/真实决策/迁移/机制/新颖性；一步投影=最大熵控制、SB 近邻，公式不称创新。
- **M1 Stage1 执行仍须另立预注册+独立挑战+Lead 批准**；Stage2/3 需合格数据（当前 data_unavailable，C203）。
