# record_N1_design_v0_3.md —— R203-N1.2 修正预注册执行记录（设计/算术/V4 实测；不运行效果比较）

角色：独立设计/审计员（未参与 R197/R200/203 模型开发）· 任务 task-135（R203-N1.2，机制账）· 日期 2026-10-28
只写 `research/2026-10-28-n1-synthetic-prereg/` 下 v0.3 文件与 `tmp/`；**未改 v0.1/v0.2 产物/A-B-D 线/R203-P1 产物**；未运行效果比较；未读 O'Neil 响应；0 wells/compute-only。

## 0. 要求与完成对照（N1.1-C1 5 必改）

| 必改 | 状态 |
|---|---|
| ① 统一 full-h 参数化摘要 | ✅ 全文唯一维数：compact **107/312/rank95/nullity12**；full **143/600/rank140/nullity3（参数 gauge=3）**；函数空间冗余 compact **129**/full **255**；不再有 359/288/gauge129 full 摘要 |
| ② pilot telemetry 一致 | ✅ 统一 canonical snapshot：**per-rep .02603 s、main 11.72 s、memory .037 GB**；逐方法 **B1 .00109/B2 .00133/B3 .001/B4 .01731/B5 .00083/B6 .00139/M .00308 s**；文本/JSON/timing 一致；旧 .0282/12.7/.038 废弃 |
| ③ G1 point 门收紧 | ✅ **point≤.05（实测 .0488 PASS）** 且 Wilson upper≤.075（实测 .05187）；mc_tol=.00308 仅 CI/敏感性说明 |
| ④ V4 实际运行 | ✅ **已实测 PASS**：200 reps、seed=20261061、T_hold=2、static ridge vs nonstatic filter（soft responsibilities/weighted ridge）；**mean ΔELPD=306.1577、SE=65.4612、95% CI=[177.856, 434.459]**；失败路径→rename_static_Sadd |
| ⑤ 其余冻结 | ✅ n_units=300/MDE80=.04798/n_req278、G2 power=1.000、B1–B6、B2 审计 PASS、caps 1800 s/2 h/8 GB/0 wells、边界/两跑/schema/失败类别不变 |
| 标 completed + send_message | ✅ |

## 1. 时间线（Asia/Shanghai，2026-10-28）

| 时间 | 事件 |
|---|---|
| ~10:47 | 读 task-135 并 claim；读 N1.1-C1 复核（challenge_N1_v0_2.md）、v0.2 产物 |
| ~10:49 | 写 v0.3 脚本（复制 v0.2 + 修 G1 门 + 加入 V4 实际运行 + pilot snapshot 冻结 + v0.3 路径/输出） |
| ~10:50 | V4 首版实现运行：mean ΔELPD=−456.6 FAIL（nonstatic filter 把观测等权分配给三状态，无 soft responsibility）；oracle-state 诊断 mean +4147.6 确认生成器状态信号强 |
| ~10:52 | 修 nonstatic filter：soft state responsibilities + weighted ridge（λ=1）；V4 重跑 **mean 306.1577/SE 65.4612/CI[177.86,434.46] PASS** |
| ~10:54 | 写 PROBLEM/DESIGN v0.3（修 5 必改、统一维数/telemetry/G1 门/V4 实测）；运行主脚本两跑 → `generator_n1_v0_3.json` 逐字节一致（`1577DDD1…`；wall 3.9/4.9 s） |
| ~10:58 | report/record/usage 完成；标 completed + send_message |

## 2. 实现与披露

1. **V4 首次 FAIL（实现问题，已披露）**：nonstatic filter 初版把每个观测等权加入三状态回归（无 responsibility），三状态模型几乎相同且 h 特征过拟合 → 预测差、V4 FAIL（mean −456.6）。用 **oracle-state** 诊断（mean +4147.6）确认生成器有强状态信号后，把过滤更新改为 **soft state responsibilities + weighted ridge**；V4 重跑 PASS。**V4 规则/阈值/seed/n_rep/held-out 均未改**；该修复是校准模型实现纠错，不涉及效果比较；已在本记录/report 披露。
2. **pilot telemetry**：v0.3 不重新计时，冻结 canonical v0.2 real-generator+7-method pilot 遥测（实现相同），避免两套数字；执行前须以最终实现重跑 pilot 并冻结预算。
3. **G1**：门从 α+mc_tol 收紧到 point≤α；mc_tol 仅用于 CI/敏感性说明；实测 .0488≤.05。
4. **无效果比较**：V4 是 pre-effect 校准 gate；未比较方法效果、未报告 regret/mis-selection 等效果指标；未读 O'Neil 响应；未用 A/B 资源。
5. **确定性**：结果 JSON 不含 telemetry；两跑逐字节一致；JSON 键排序/无时间戳；文档 SHA 写入 JSON。
6. **边界**：机制账 only；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定；N1 效果执行另立预注册+挑战+Lead 批准。

## 3. 关键结果（与 report 一致）

- full 12-pair：params 143/obs 600/rank 140/nullity 3（参数 gauge 3）；compact 6-pair：107/312/95/12；函数空间冗余 compact 129/full 255。
- G1：k=976/20000、point=.0488、Wilson .05187 → PASS；G2 powers 1.000；V4 PASS（306.1577/65.4612/[177.86,434.46]）。
- n_units=300；MDE80=.04798；n_req278；pilot snapshot .02603 s/rep、11.72 s main、.037 GB；B2 审计 PASS。
- 结果 JSON SHA `1577DDD1…`；timing SHA `94A3646E…`。

## 4. 产物与哈希

| 文件 | SHA256 |
|---|---|
| `PROBLEM_N1_v0_3.md` | `E404C5FE529A2432C166B7072D0B5939D9927F37E74A2E620B4AB061F618534C` |
| `DESIGN_N1_v0_3.md` | `A65158D7D226DC8E62B5BD7F43AC9D581239E7D22AF4E9EA55BA3CDDC4B37611` |
| `generator_n1_v0_3.py` | `B4E93415215174239B974651D53AAF282EFCE703B49B84088B9C0EB4A9E6FCF5` |
| `generator_n1_v0_3.json` | `1577DDD187AB25726B6E15EAEF587CA85631F295CF14E28E76D7D62392586B32` |
| `timing_n1_pilot_v0_3.json` | `94A3646E8BB186A53E4DA8D7C8885666EEE56F4ABCABB1988FAC339E1448C53D` |
| report/record/usage | 见 `usage_N1_design_v0_3.json` |
| v0.1/v0.2 只读 | PROBLEM v0.2 `C66FD8F4…`、DESIGN v0.2 `1B179AB9…`、generator v0.2 `F1EFD8D8…`/`045DEE05…` 等（未改） |

## 5. 缺口与下一步

- **未运行 N1 效果比较**（V4 为 pre-effect 校准；无效果指标）；N1 效果执行须另立执行预注册 + 独立挑战 + Lead 批准。
- 执行前须以最终实现重跑 pilot 并冻结预算（当前为 canonical v0.2 快照）。
- 机制账 only；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定；不恢复停止实验。
