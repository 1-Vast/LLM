# record_m1_s2c_prereg_v0_2.md —— R204-M1-S2C.1 修订预注册记录（headroom 阈值 .10；不运行候选）

角色：独立执行设计/审计员（未参与 R197/R200/203 模型开发）· 任务 task-196（R204-M1-S2C.1）· 日期 2026-10-28
只写 `research/2026-10-28-m1-s2c-planning-prereg/` 下 v0.2 文件与 `tmp/`；**未改 v0.1 产物/H1b/C216/C217/M1 设计链/M2/M3/N1/A-B-D**；**未训练 C-MDN/未运行候选规划/未报效果/未读真实数据**；机制账 only；compute-only、0 wells。

## 0. 必改落实

| # | 要求 | 状态 |
|---|---|---|
| ① 统一 headroom 阈值 | ✅ stop_conditions[0] 改为 **headroom<2δ=.10 → 未见候选前重设并冻结环境，或 `design_invalid: unreachable_gate` 停止；不执行**；与 requirement/redesign_rule 一致；不降 .10 为 .05 |
| ② schema/JSON 可判字段 | ✅ 新增 `headroom_required=0.10`、`headroom_decision_rule`、`headroom_stop_category="design_invalid: unreachable_gate"`；schema/JSON/stop_conditions 同步；执行器按 2δ 判 |
| ③ headroom 语义 | ✅ 明确设计期实测（候选未见前）；本轮未重设环境；若未来重设须在候选结果前记录并冻结；不得用候选结果反选 |
| ④ 保持 | ✅ 旧/新分离；冻结环境/Pθ；六比较/Holm/δ=.05/raw-paired/CI R≥20/等价审计/seeds 20261901–54/两跑/caps 1800 s/2 h/8 GB/0 wells/schema/11 失败/边界；headroom 值保留（full .22625306 CI [.22094996,.23155615]；constrained .15141651 CI [.15007466,.15275836]） |

## 1. 时间线（Asia/Shanghai，2026-10-28）

| 时间 | 事件 |
|---|---|
| ~16:40 | 读 task-196 并 claim；读 M1-S2C-C1 挑战、v0.1 产物、H1b/C216/C217 链 |
| ~16:43 | 复制 v0.1→v0.2 脚本；Python patch：路径/task、headroom_required/decision_rule/stop_category、schema 字段、stop_conditions[0] 改 .10、输出字段 |
| ~16:45 | 运行成功：headroom 值不变（full .22625、constrained .15142）、stop_conditions[0]=2δ=.10、schema 字段齐全；两跑 plan/schema 逐字节一致 |
| ~16:49 | 写 PROBLEM/DESIGN/report/record/usage v0.2；标 completed + send_message |

## 2. 实现与披露

1. **仅预注册修订**：不训练/不运行候选；headroom 值保留；只改阈值/字段/文档。
2. **阈值统一**：stop_conditions[0] 由 “<δ=.05” 改为 **“<2δ=.10 → 未见候选前重设并冻结环境，或 design_invalid: unreachable_gate 停止；不执行”**；requirement/redesign_rule/decision_rule 全部按 .10。
3. **schema 字段**：headroom_required=0.10、headroom_decision_rule、headroom_stop_category；headroom_measured_design_time_before_candidate=true、no_candidate_results_used_for_headroom=true。
4. **headroom 值**：full .22625306 CI [.22094996,.23155615]；constrained .15141651 CI [.15007466,.15275836]；均≥.10 → executable；未重设环境。
5. **保持**：六比较/Holm family 6/δ=.05/raw-paired/CI R≥20/等价审计/seeds 20261901–54（overlap=[]）/两跑/caps/schema/11 失败/边界不变。
6. **确定性**：`headroom_design_m1_s2c_v0_2.json`（`89C3586B…`）两跑逐字节一致；JSON 无 telemetry；wall≈3.4–3.6 s 仅 usage/报告。
7. **边界**：机制账 only；未训练 C-MDN/未运行候选/未读真实数据；不改旧判定；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；M1 不与 M2/M3 混同；N1 不作证据；data readiness open（C203/C205/C210/C214）。

## 3. 关键结果

- headroom threshold：**headroom_required=0.10**；stop category=design_invalid: unreachable_gate；stop_conditions[0]=headroom<2δ=.10 → 重设/冻结或 stop，不执行。
- headroom values（未变）：full .22625306 CI [.22094996,.23155615]；constrained .15141651 CI [.15007466,.15275836]；均≥.10 → executable；未重设环境。
- 六比较族/Holm 6/δ=.05/raw-paired/CI replicate≥20/等价审计；seeds 20261901–54；caps 1800/7200/8GB/0 wells；两跑/schema/失败/停止。
- 无 C-MDN/无候选规划/无效果；本轮仅预注册修订。

## 4. 产物与哈希

| 文件 | SHA256 |
|---|---|
| `PROBLEM_M1_S2C_v0_2.md` | `2692C4FB5D625972E33C3952C430B4F24D2BAC76CB4B53D3D22B59A0909A868E` |
| `DESIGN_M1_S2C_v0_2.md` | `FFC3A13CDEA522B54190F43D564F3E4DC3D85AAA357060BECD319AF6C74C0FD0` |
| `headroom_design_m1_s2c_v0_2.py` | `40F44DD4EBDFB187E5E388E639B7552094BEB464A10CD8C540A3FEE92070D5B1` |
| `headroom_design_m1_s2c_v0_2.json` | `89C3586B596013A23651C768913BB84A41EA33B2DA00718BA590B21375013741` |
| `schema_m1_s2c_v0_2.json` | `4DCFE96B516AFEB6222145F081B90453079C9208EF4DEC23ED8192BB8A9668EF` |
| report/record/usage | 见 `usage_m1_s2c_prereg_v0_2.json` |
| v0.1 只读（未改） | PROBLEM `5F4E690C…`、DESIGN `E1030AB4…`、script `E45B1231…`、JSON `1C8B64A4…`、schema `FD5A2774…` |

## 5. 缺口与下一步

- **S2c 尚未执行**；本文件仅预注册修订（阈值统一 .10）。
- 执行前：轻量复核 + Lead 批准 + 重核 headroom/环境/六比较/seeds/两跑/schema/失败模板 + 最终实现 pilot 冻结；不改旧判定。
- 机制账 only；不训练 C-MDN/不运行候选/不报效果；不晋升代码/不改旧判定/不恢复停止实验。
