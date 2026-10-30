# record_t1_mvp —— R201-B T1 模拟器实现+资格门审计记录（未跑主结果）

2026-10-28 · 角色：ON1/ON2/ON2.2/ON3 执行者（非提案者）。任务：R201-B-T1-MVP（仅实现+资格门；不跑主 500/T2/T3/真实响应/湿实验）。**本记录只记录实现/资格门；不称新颖性/机制/迁移/决策收益/独立确认。**

## 1. 时间线

| 时间（本机） | 事件 |
|---|---|
| 00:35–00:37 | 读 task-114、`DECISION_R201_T1_MVP.md`、v0.4 冻结链；建 `t1_mvp/` |
| 00:37–00:41 | 写 `t1_sim.py`（世界/learner/10 arms/成本/EV 近似）；写 `t1_qualification.py`（9 项门+pilot 计时） |
| 00:41–00:43 | 调试 oracle 门：clipped 响应导致 latent top 并列不可辨识；改为 latent 真值 + all-40 noiseless learner 的无限计算极限；learner 加 group fixed effects；通过 |
| 00:43–00:44 | 首次 qualification_pass；发现 `t1_qualify.json` 含 pilot wall 导致两跑不一致 → 将 wall 移入 `timing_pilot.json`，资格 JSON 排除计时 |
| 00:44–00:46 | 两跑 `t1_qualify.json` 逐字节一致（`A50A1E96…`）；pilot wall 6.97s，外推 primary≈5.81min；写 schema/report/record/usage |

## 2. 输入（只读；SHA256）

| 文件 | SHA256 |
|---|---|
| `dual_budget/DECISION_R201_T1_MVP.md` | `1AAAA3E370A0BE099059147BCDB670F98CEE520C5E00EDCD44A30991D7E49CCE` |
| `PROBLEM_B_v0_4.md` | `D6B37E704DE141FE481A73D4BDDC0FFA6CBB0BA7FA6A686004D568415E6C5C99` |
| `DESIGN_B_v0_4.md` | `9112EDDC3180BA6101DF76CB34282BE84E7E9DF0EBD3EC714C4999388E7D01CD` |
| `design_B_revision_v0_4.py` | `E4968C701DB031BF246767D821A31DC5B8EF9AB50D3A0694462E023F661A3A5E` |
| `design_B_v0_4.json` | `A2D0CC1A01A9EF29FC7B2F0ACDC21658AFCEF6EE9D1F1FDC0829E3CC16601AA1` |
| `report_B_v0_4.md` | `31F17B5EF3CE98685ADA837B369837E081C43BC828C7D50071E1B6C7C9D472B0` |
| `record_B_v0_4.md` | `7A3F3A23E5663E49A738054F48B7A80CDD6F11B2684091E6D833581711C532FD` |
| `usage_B_v0_4.json` | `2AE7097824BABC8AE8013B74C4D318E02E76B807E4A6ABA1EFE57312948FBE0E` |

## 3. 输出（本任务；只写 `dual_budget/t1_mvp/` 与 tmp/）

| 文件 | SHA256 |
|---|---|
| `t1_sim.py` | `A09CAE8923AD98FB8DFDFDFAFBA1C8BB82B6084041CC4E12F6C729DE00372930` |
| `t1_qualification.py` | `A7202348C0AD83D6E3B6D1C6B46F73A32A225A2986C842AE5FA0DCE6FBE54381` |
| `t1_qualify.json` | `A50A1E96797A247618EFFF89B232461E2F5749F368E817DCCCF31418A0BA9203` |
| `timing_pilot.json` | `41EA27D464D9734F2A3260AC316BB7DF5E3CFE8DAA56F434CB3EE1218F08A856` |
| `schema_t1_qualify.json` | 见文件 |
| `report_t1_mvp.md` | 见 usage/复核方 |
| `record_t1_mvp.md` | 本文件（SHA 见 usage/复核方） |
| `usage_t1_mvp.json` | 最后写出（SHA 见复核方） |

## 4. 资格门结果（摘要）

- **verdict = qualification_pass**；failed_gates=[]。
- oracle PASS（20 worlds；latent 无限计算极限；clipped tie 不可辨识已注明）；null FP PASS（100 null reps；H_B 未支持；p=0.5）；EV PASS（5 actions；max |Δ|=1.998e-15，离散参考一致性门，非连续真误差/非 exact）；cost PASS（18 configs、neg filler 0、outside 0、10 arms spend≤1、filler 不进 learner）；无泄漏 PASS；10 arms PASS；menu hash PASS；schema PASS；wall PASS。
- pilot：10 replicate×10 arms=100 arm-runs，wall **6.97s**；外推 primary 5,000 arm-runs≈**5.81min** ≤45min；两跑≤90min。
- **两跑 `t1_qualify.json` 逐字节一致** SHA `A50A1E96…`；wall 只在 `timing_pilot.json`。

## 5. 实现备注（Lead 非阻塞备注落实）

1. **filler 价格**：合成 **1 CU/blank/QC well**；非物理 A5 价（5.3–10.7 CU/well 会超 T）；已在 report/usage 标注；若改 A5 价须重算。
2. **EV 门**：有限离散参考一致性门（approx zero-noise vs 5-point noise reference），**不写 exact**；max diff≈2e-15≤0.02；未做连续真误差/更高分辨率参考。
3. **σ**：primary σ=0.10 五点网格；σ=0.05 敏感性未运行（仅描述，不用于 H_B）。
4. **oracle 门**：clipped 响应可能使真 top 并列不可辨识；门使用 latent 真值 + 全 40 无噪声 learner 的无限计算极限；已注明仅评估，不用于结果。
5. 10 arms 同 learner/update/信息/调参/seed；C7 两臂分别输出；整数 key+filler 账本；无真实响应读取。

## 6. 执行/边界

- 运行 `t1_qualification.py` 两次（两跑资格 JSON 一致）；运行 `t1_sim.py` 仅作为模块被导入；**未运行主 500 replicate 结果**、未运行 T2/T3、未读 O'Neil/Validation 真实响应、无湿实验；未改 v0.1–v0.4 文件/其它目录；未晋升代码。
- T1 仅计算证据；资格门通过不等于执行主 T1/决策收益；T2/T3 不执行；不称新颖性/机制/迁移/决策收益/资源足够/独立确认；冻结≠资源足够/关系成立/Stage 1/效果。
- 若 Lead 另批主 T1，须按冻结 primary/500/10 arms/H_B AND；本次未跑。

## 7. 未做/禁止

- 未跑主 500 replicate、未跑 T2/T3、未读真实响应、未做湿实验；未改冻结旋钮；未称任何收益/新颖性/机制/迁移/独立确认。
