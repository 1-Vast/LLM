# record_t1_main —— R201-B 主 T1 执行审计记录（仅计算证据）

2026-10-28 · 角色：ON1/ON2/ON2.2/ON3 执行者（非提案者）。任务：R201-B-T1-MAIN（按 `DECISION_R201_T1_MAIN.md` 执行主 T1 一次；仅合成模拟器/计算证据；不跑 T2/T3/真实响应/湿实验）。**不称新颖性/机制/迁移/决策收益/独立确认；不得外推生物/药物决策；冻结≠资源足够/关系成立/Stage 1/效果。**

## 1. 时间线

| 时间（本机） | 事件 |
|---|---|
| 00:52–00:53 | 读 task-115/`DECISION_R201_T1_MAIN.md`；建 `t1_main/`；写 `run_t1_main.py`（调用 t1_mvp 模拟器；冻结 primary/10 arms/H_B/敏感性/两跑） |
| 00:53–01:10 | run1：资格门快检→primary 500×10→敏感性 17×50×10；H_B=`partial_decision_benefit`；wall 974.96s；结果 JSON SHA `58E290A7…` |
| 01:10–01:28 | run2：同命令；结果 JSON 与 run1 **逐字节一致** SHA `58E290A7…`；wall 956.73s |
| 01:28–01:30 | 写 `report_t1_main.md`/本 record/`usage_t1_main.json`；核对 SHA；未改冻结旋钮/其它目录 |

## 2. 输入（只读；SHA256）

| 文件 | SHA256 |
|---|---|
| `DECISION_R201_T1_MAIN.md`（Lead 批准主 T1） | `19719E25774EDA298E354018EA786DDE5FC17F9BFC75E234CDFF5B81D9E1820B` |
| `PROBLEM_B_v0_4.md` | `D6B37E704DE141FE481A73D4BDDC0FFA6CBB0BA7FA6A686004D568415E6C5C99` |
| `DESIGN_B_v0_4.md` | `9112EDDC3180BA6101DF76CB34282BE84E7E9DF0EBD3EC714C4999388E7D01CD` |
| `design_B_revision_v0_4.py` | `E4968C701DB031BF246767D821A31DC5B8EF9AB50D3A0694462E023F661A3A5E` |
| `design_B_v0_4.json` | `A2D0CC1A01A9EF29FC7B2F0ACDC21658AFCEF6EE9D1F1FDC0829E3CC16601AA1` |
| `report_B_v0_4.md` | `31F17B5EF3CE98685ADA837B369837E081C43BC828C7D50071E1B6C7C9D472B0` |
| `record_B_v0_4.md` | `7A3F3A23E5663E49A738054F48B7A80CDD6F11B2684091E6D833581711C532FD` |
| `usage_B_v0_4.json` | `2AE7097824BABC8AE8013B74C4D318E02E76B807E4A6ABA1EFE57312948FBE0E` |
| T1-MVP：`t1_sim.py` | `A09CAE8923AD98FB8DFDFDFAFBA1C8BB82B6084041CC4E12F6C729DE00372930` |
| T1-MVP：`t1_qualification.py` | `A7202348C0AD83D6E3B6D1C6B46F73A32A225A2986C842AE5FA0DCE6FBE54381` |
| T1-MVP：`t1_qualify.json` | `A50A1E96797A247618EFFF89B232461E2F5749F368E817DCCCF31418A0BA9203` |

## 3. 输出（本任务；只写 `t1_main/` 与 tmp/）

| 文件 | SHA256 |
|---|---|
| `run_t1_main.py` | `F805AA3EDD5CE8C07978D437DBB020F757FC2C2D50AE19579E84CC1E75A351F7` |
| `t1_main.json`（两跑一致） | `58E290A7935472F9B34B856CE832BC2B822E24B37431F9E55843E654B95ADB05` |
| `t1_main_rows.csv`（5,000 行） | `2A227AB0EFE97603D4AB9A0DB003DCCF73067C7B82DC6862C5A90A41D267369F` |
| `timing_main.json`（run2） | `A5A816FBB9E2AA25F0CE9566DEC166D7628E3D17BB04FB3C8A347C6958A6232C` |
| `report_t1_main.md` | 见 usage/复核方 |
| `record_t1_main.md` | 本文件（SHA 见 usage/复核方） |
| `usage_t1_main.json` | 最后写出（SHA 见复核方） |

## 4. 执行/结果

- 冻结 primary `(1200s,16 keys,κ=1,σ=0.10)`；500 replicate=500 decision units；10 arms；primary arm-runs 5,000；敏感性 17×50×10=8,500（描述）。
- 资格门快检：与 T1-MVP 一致，全部 PASS，无偏差（frozen_chain 核对通过）。
- **H_B = `partial_decision_benefit`**：`dual vs C7_compute_only` 点估计 +0.022、CI [0.006,0.040]、Holm p=0.01117（显著正但<δ）；`dual vs C7_experiment_only` +0.010、CI [−0.006,0.026]、Holm p=0.11252（不显著）；两对比未同时显著正、均<δ=0.10 → partial（按预注册；不写"双预算无效"）。
- per-arm mean selection accuracy：π_dual 0.912；C0/C1 0.906；C2 0.890；C3/C4/C5 0.878；C6 0.888；C7_compute_only 0.890；C7_experiment_only 0.902（仅描述）。
- 敏感性 17 格描述：dual−C7 两对比每格均值范围约 −0.04…+0.04；不用于 H_B、不选赢家。
- wall：run1 974.96s（quick 70.65+primary 348.46+sensitivity 555.67）；run2 956.73s（68.39+337.90+550.25）；均≤45min；两跑≤90min。
- 两跑 `t1_main.json`/CSV 逐字节一致；timing 文件因 wall 不同属预期。

## 5. 边界/未做

- **仅计算证据（synthetic）**；不称新颖性/机制/迁移/决策收益/独立确认；不得外推 O'Neil/生物/药物决策；H_B 未支持不写"双预算无效"、不写结构成立/不存在。
- 未运行 T2/T3；未读真实响应；无湿实验；未改冻结旋钮/设计文件/其它目录；未晋升代码。
- 冻结 ≠ 资源足够/关系成立/Stage 1/效果；技术重复≠独立培养。
