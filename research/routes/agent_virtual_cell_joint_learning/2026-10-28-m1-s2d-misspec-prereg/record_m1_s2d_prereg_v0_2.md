# record_m1_s2d_prereg_v0_2.md —— R204-M1-S2D.1 修订预注册记录（每 target R≥20/共 60 cells；不运行候选）

角色：独立执行设计/审计员（未参与 R197/R200/203 模型开发）· 任务 task-201（R204-M1-S2D.1）· 日期 2026-10-28
只写 `research/2026-10-28-m1-s2d-misspec-prereg/` 下 v0.2 文件与 `tmp/`；**未改 v0.1 产物/S2c/H1b/C216/C217/M1 设计链/M2/M3/N1/A-B-D**；**未训练 C-MDN/未运行候选规划/未报效果/未读真实数据**；机制账 only；compute-only、0 wells。

## 0. 必改落实

| # | 要求 | 状态 |
|---|---|---|
| ① 扩执行 cells 每 target≥20/共≥60 | ✅ **T1 20262041–20262060、T2 20262061–20262080、T3 20262081–20262100**；每 target 20、共 60；`execution_cell_seed_blocks` 写死；48 作废；与旧集 disjoint（overlap=[]） |
| ② schema/JSON 可判字段 | ✅ `R_execution_per_target=20`、`n_targets=3`、`n_cells=60`、`cluster="replicate"`、`CI_method="95% t interval across independent replicates (df=R-1); cluster=replicate"`；`multiple_testing.CI` 与实际 cells 一致；T2/T3 每 target Holm 也按 R=20 |
| ③ T2 有效行数 | ✅ 冻结 **T2 valid_eval_rows=4093**（3 极端解析下溢行剔除；nominal 4096）；T1/T3=4096；schema/JSON + note；不按 4096 谎报 |
| ④ 保持 | ✅ 目标/headroom 值（T1 .51107412/T2 .56758207/T3 .39007047，均≥.10）/仅源训练/六比较/δ=.05/Holm/raw-paired/T2T3 不合并/主成功仅 T1/headroom seeds 20262011–30/data 20262031/eval 20262032/两跑/caps/schema/11 失败/停止/边界；不训练/不执行候选 |

## 1. 时间线（Asia/Shanghai，2026-10-28）

| 时间 | 事件 |
|---|---|
| ~18:00 | 读 task-201 并 claim；读 M1-S2D-C1 挑战、v0.1 产物、S2c/H1b/C216/C217 链 |
| ~18:03 | 复制 v0.1→v0.2 脚本；patch：三 target cell blocks 20262041–20262100、R_execution/n_targets/n_cells/cluster/CI_method、multiple_testing.CI、T2 valid rows、schema/output |
| ~18:05 | 运行成功：headroom 值不变；exec cells 60（20/target）；overlap=[]；T2 valid=4093；两跑 JSON/schema 逐字节一致 |
| ~18:10 | 写 PROBLEM/DESIGN/report/record/usage v0.2；标 completed + send_message |

## 2. 实现与披露

1. **仅预注册修订**：不训练/不运行候选；headroom 值保留；只改执行 cells/字段/文档/T2 记录。
2. **cells 扩展**：T1 20262041–20262060（20）、T2 20262061–20262080（20）、T3 20262081–20262100（20），总 60；与 headroom 20262011–30、data 20262031、eval 20262032、旧集 disjoint；`execution_cell_seed_blocks` 写死。
3. **可判字段**：R_execution_per_target=20、n_targets=3、n_cells=60、cluster=replicate、CI_method 95% t(df=19)、每 target Holm；multiple_testing.CI 与实际 cells 一致；T2/T3 不得次级豁免 CI。
4. **T2 有效行数**：冻结 valid_eval_rows=4093（T1/T3=4096；nominal 4096）；schema/JSON 记录原因，不谎报 4096。
5. **headroom 值（未变）**：T1 .51107412 CI[.46843293,.55371531]；T2 .56758207 CI[.56039835,.57476580]；T3 .39007047 CI[.38530525,.39483569]；均≥.10 → executable；未重设环境。
6. **确定性**：`headroom_design_m1_s2d_v0_2.json`（`B2095AEF…`）两跑逐字节一致；JSON 无 telemetry；wall≈5.5–5.8 s 仅 usage/报告。
7. **边界**：机制账 only；未训练 C-MDN/未运行候选/未读真实数据；不改旧判定；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；S2d 不改 S2c；M1 不与 M2/M3 混同；N1 不作证据；data readiness open（C203/C205/C210/C214）。

## 3. 关键结果

- 执行 cells：T1 20262041–60、T2 20262061–80、T3 20262081–100；每 target R=20、共 60；overlap=[]。
- schema/JSON：R_execution_per_target=20、n_targets=3、n_cells=60、cluster=replicate、CI_method 95% t(df=19)；multiple_testing.CI 与实际一致；T2/T3 每 target Holm R=20。
- T2 valid_eval_rows=4093 冻结（T1/T3 4096；nominal 4096）；记录原因，不谎报。
- headroom（未变）：T1 .51107412、T2 .56758207、T3 .39007047，均≥.10；executable；未重设。
- 六比较/Holm/δ=.05/raw-paired/目标分层/等价审计；headroom seeds 20262011–30、data 20262031/eval 20262032；两跑/caps/schema/11 失败/停止。
- 无 C-MDN/无候选规划/无效果；本轮仅预注册修订。

## 4. 产物与哈希

| 文件 | SHA256 |
|---|---|
| `PROBLEM_M1_S2D_v0_2.md` | `25114A56B5745A1A517E4AECF415EDD013A6C9F128CBA523E2238F6BCFE69D98` |
| `DESIGN_M1_S2D_v0_2.md` | `1676FD5E6087A775424EB34B0A8E919F8996D829F2869081C9D0D5722D8A623D` |
| `headroom_design_m1_s2d_v0_2.py` | `CA56B472585A2FFB63BEFAC56D0FEB331FB4A7F9D3CD6BC119B0428E2F10E44F` |
| `headroom_design_m1_s2d_v0_2.json` | `B2095AEFE23CA531B35794316A84A210C6263129D4E75D5644FA942B12C8F091` |
| `schema_m1_s2d_v0_2.json` | `A9D0D197BF406F04CB4F721F84CD5D718C19C8166FDF9D57DB55BA69357E6D43` |
| report/record/usage | 见 `usage_m1_s2d_prereg_v0_2.json` |
| v0.1 只读（未改） | PROBLEM `00394113…`、DESIGN `86F5B08F…`、script `552F746C…`、JSON `12A9B91B…`、schema `20B13ADD…` |

## 5. 缺口与下一步

- **S2d 尚未执行**；本文件仅预注册修订（cells 60、可判字段、T2 4093）。
- 执行前：轻量复核 + Lead 批准 + 重核环境/headroom/每 target R=20/两跑/schema/失败模板 + 最终实现 pilot 冻结；不改旧判定。
- 机制账 only；不训练 C-MDN/不运行候选/不报效果；不晋升代码/不改旧判定/不恢复停止实验。
