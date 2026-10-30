# record_N1_design.md —— R203-N1 预注册执行记录（设计/算术/合成 pilot 计时；不运行效果）

角色：独立设计/审计员（未参与 R197/R200/203 模型开发）· 任务 task-130（R203-N1，机制账）· 日期 2026-10-28
只写 `research/2026-10-28-n1-synthetic-prereg/` 与 `tmp/`；**未改 A/B/D 线与 R203-P1 产物**；未运行效果/方法比较；未读 O'Neil 响应；0 wells/compute-only；non-blind 不适用（纯合成，无实测数据）。

## 0. 要求与完成对照

| 要求 | 状态 |
|---|---|
| ① 与静态 S-add 实质区别；state/sequence 非静态过程；static 退化；if-rename 判据 + `design_invalid: rename_static_Sadd` | ✅ PROBLEM_N1 §1（S=3 状态转移/state-specific β_s,γ_s 历史动作依赖/共享动态核/plan-pair conflict/h；static 为 S=1,β=γ=0,h=0 退化）；V1–V4 + 失败类别 |
| ② 生成器冻结（状态/序列/计划/剂量/噪声/违例/隐藏参数/可辨识/gauge；GT-static + GT-nonstatic 两套 ground-truth） | ✅ PROBLEM_N1 §2/§3；generator_n1.json `generator_spec`；两套 ground-truth |
| ③ 主终点 held-out decision regret（δ=.05 normalized；U/regret/归一化/决策集/菜单；headroom+MDE preflight；近满分另立达标预算） | ✅ PROBLEM_N1 §4；DESIGN_N1 §5；MDE80=.0438@n=360/deff=2.2；n_req 278；headroom 设计目标 .10≥.05 |
| ④ 等 compute/query 基线（full retrain、static S-add 同信息同预算、hierarchical/EB、GP、random、AL；统一 update/信息/调参/秒/查询数/先验/初始数据） | ✅ PROBLEM_N1 §5 / DESIGN_N1 §3（B1–B6 + M；统一 prior/初始/feedback/query/调参/特征/cap） |
| ⑤ 校准/资格门先于效果（FPR≤α、power、可辨识/参数恢复、无泄漏、两跑/schema/预算；失败只 design_invalid 不报结果） | ✅ DESIGN_N1 §5 G1–G7 + V4；generator_n1.json 校准算术（FPR .0502、power≈1.00）；失败类别 |
| ⑥ 失败类别/停止（rename_static_Sadd/generator_misspecified/calibration_failed/nonidentifiable/leakage/compute_budget_exceeded/no_increment/inconclusive；强基线等效→撤主张） | ✅ PROBLEM_N1 §7 / DESIGN_N1 §6；B2 static S-add 显式强基线 |
| ⑦ 预算：合成 pilot 10 replicate 计时 + 主预算（replicate 数/wall/CPU/内存 cap）；不用 A/B 资源；不运行效果 | ✅ `timing_n1_pilot.json`（10 replicate stub 0.0005 s/rep、投影 0.95 s，仅下界）；主预算 n=360/R=50/methods=7；wall≤1800 s/CPU≤2 h/8 GB |
| ⑧ 边界（机制账 only；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；不恢复已停止实验；不改旧门槛） | ✅ 各文件 §边界 |
| 标 completed + send_message | ✅ |

## 1. 时间线（Asia/Shanghai，2026-10-28）

| 时间 | 事件 |
|---|---|
| ~10:23 | 读 task-130 并 claim；读 DECISION_R203_P1_SCOPE、R203-P1 PROBLEM/DESIGN/power_scope |
| ~10:25 | 写 `PROBLEM_N1.md`（非静态生成过程/退化/V1–V4 判据/生成器/终点/基线/门/预算/边界） |
| ~10:26 | 写 `generator_n1.py`（冻结 spec、可辨识 Jacobian、校准 power/FPR、headroom/MDE、pilot 计时） |
| ~10:27 | 修 bug：history transition 最初用**状态共同**的 β/γ——softmax 对共同平移不变 ⇒ 无历史依赖信号；改为 **state-specific β_s/γ_s** 并计算 KL（=0.617）→ V2 设计算术通过；修 chisquare 占位符；加 additive-gauge 投影 rank（90/107，nullity 17） |
| ~10:28 | `generator_n1.json` 两跑逐字节一致（`21BA30AA…`；wall 0.2 s）；写 DESIGN_N1/report |
| ~10:32 | record/usage 完成；标 completed + send_message |

## 2. 实现与披露

1. **只做设计算术**：generator spec 冻结；Jacobian rank（代表设计：params 107/obs 288/rank 90/nullity 17）用于 gauge/可辨识说明；校准 power/FPR 由预注册振幅的非中心 χ² 设计算术（power≈1.00；FPR .0502）；headroom/MDE 用 R203-P1 公式（MDE80=.0438@n=360/deff=2.2；n_req 278）；**无方法比较、无效果、无预测**。
2. **pilot 计时为 stub 下界**：10 replicate 生成器/更新 stub 0.0005 s/rep、投影 main≈0.95 s；**不**代表真实实现；N1 执行前须以真实实现重跑 pilot 并冻结预算。计时文件为 telemetry（多次运行可变，不进结果 JSON）。
3. **历史依赖 bug 披露**：最初 β/γ 为状态共同参数，softmax 共同平移不变 ⇒ 无信号；已改为 state-specific β_s/γ_s（V2 设计 KL=0.617）。属设计算术修正，未运行效果。
4. **无 O'Neil 响应/无 A/B 资源**：本任务不读任何响应；纯合成；0 wells；compute-only；未晋升代码；未恢复已停止实验。
5. **确定性**：`generator_n1.json` 两跑逐字节一致；JSON 键排序/无时间戳/allow_nan=False；PROBLEM/DESIGN SHA 写入 JSON。

## 3. 关键结果（与 report 一致）

- 与静态 S-add 区别：S=3 状态转移 + state-specific 历史/动作依赖（KL=0.617）+ 共享动态核 + plan-pair conflict（E_h=.20）+ held-out decision regret 终点；static 为 S=1,β=γ=0,h=0 退化。
- 可辨识：代表设计 rank 90/107、nullity 17；gauge（状态标签/加性常数/interaction 加性方向）已列；参数恢复门写入。
- 校准：GT-static FPR .0502；GT-nonstatic state/interaction/history power≈1.000（n_rep=200，设计振幅满足≥.80）。
- Headroom/MDE：δ=.05；GT-nonstatic 设计 headroom .10≥.05；n=360、deff=2.2 → MDE80 .0438≤.05；n_req(SD=.20)=278≤360。
- 基线 B1–B6 + M；统一预算/信息/调参/特征；B2 static S-add 为关键强基线，等效→撤主张。
- 预算：pilot stub 0.0005 s/rep（下界）；主预算 n=360/R=50/7 方法；wall≤1800 s/CPU≤2 h/8 GB；0 wells。

## 4. 产物与哈希

| 文件 | SHA256 |
|---|---|
| `PROBLEM_N1.md` | `23F4668A71F8B0201C38B9134E23D9AB4034CFDBA8FF81EE3093D68B1D55545B` |
| `DESIGN_N1.md` | `8FAAC49189BC8870488F3944E2131E4664FCD3B18D1162C62E95FB8BCBA039CE` |
| `generator_n1.py` | `F509708EE4922D65B04178CA7CD824963537A73D5119E182063DCF90BA9F2E44` |
| `generator_n1.json` | `21BA30AAFCC3D0E047BDFAAD8A2DEA778E616C32EEF11BAC44239E34D8378559` |
| `timing_n1_pilot.json` | 计时文件（telemetry；末次 `7BA4E299…`） |
| report/record/usage | 见 `usage_N1_design.json` |

## 5. 缺口与下一步

- **未运行 N1 效果**（设计/算术/pilot 计时 only）；N1/N2 执行须另立预注册 + 独立挑战 + Lead 批准。
- pilot 计时为 stub 下界，真实实现预算待 N1 执行前 pilot。
- 机制账 only：不称药理/真实决策/迁移/机制/新颖性；不晋升代码；不恢复已停止实验；不改旧判定/门槛。
