# record_B_v0_4 —— R201-B.3 审计记录（T1 冻结候选；未运行）

2026-10-28 · 角色：ON1/ON2/ON2.2/ON3 执行者（非提案者）。任务：R201-B.3（按 `challenge_B_v0_3.md` revise 5 必改修 filler 单位/arm-run/x1x2+EV/spend 校验/边界；仅 T1 实现+资格门）。**未运行 T1/T2/T3、未拟合、未读响应、无湿实验；不称新颖性/机制/迁移/决策收益。**

## 1. 时间线

| 时间（本机） | 事件 |
|---|---|
| 00:31–00:32 | 读 `challenge_B_v0_3.md`（SHA `9B6F4438…`）、v0.3 文件、A5/ON2-EX/ON3/PEEK/C187/C190；确认 5 必改 |
| 00:32–00:34 | 写 `design_B_revision_v0_4.py`（仅算术：修正 filler 公式/18 格校验/10 arms wall/x 表/EV 网格/T3 r）；运行一次生成 `design_B_v0_4.json` |
| 00:34–00:36 | 写 `PROBLEM_B_v0_4.md`、`DESIGN_B_v0_4.md`、`report_B_v0_4.md`、本 record、`usage_B_v0_4.json`；核对 SHA；未改 v0.1–v0.3 文件 |

## 2. 输入（只读；SHA256）

| 文件 | SHA256 |
|---|---|
| `challenge_B_v0_3.md`（R201-B.3-C1） | `9B6F4438C47B771AEDFC8B2043F09E3C5438EBE2B4A228FE93806CCCF2D457F9` |
| `PROBLEM_B_v0_3.md` | `753B9CF8BEA1CC8B2963F7F67D5622C710CE1F85D0631F035C777B6403C5F900` |
| `DESIGN_B_v0_3.md` | `183BE5DEA3FBCCE2B95C551C1D99B80FF25A75ADA29A28B9EC102B3A06AFF22C` |
| `design_B_v0_3.json` | `50E6EE30959CACD9894F799276BE907388189BCFF9B225DC7E6C68611E8A27D9` |
| `report_B_v0_3.md` | `012026ADDC2B09A6AE6CBB374563CDA1B5260B01427F2E2D829ED8F93621B29A` |
| `record_B_v0_3.md` | `77AB57BEF5870F3D5AA65FFA6DEDA103AB39D8E6E0E7AD96A2BAE09AE51BD021` |
| `dual_budget/challenge_B_v0_2.md`（前轮） | `4D3A3AB565E184975DB87CF971E6839E5795C761FD956155386324F5B9A07712` |
| R201 `BRIEF.md` | `3F859B1FA234331194C7C4A61A5F9AF516860AF25232834DFB22E5526B9006DE` |
| `agent-cell-colearning/report.md` | `91FC9E7BCB40826E124AC19995C27878DEB40EFF277C42176A07E99248CA8020` |
| D3 `report_d3_v0_2.md` | `F36E2BBC343873910CBB5AD7D7234161321763ECF12CF869B0FD487EA517D39E` |
| D1 `DECISION_D1_STOP.md` | `86D802E9C19CD878758155FBECD1EE3DCE3CA3BF05CE17C33E2C81AE64E18A25` |
| A5 `cost_model.md` | `46824DBE8D967CEC090D5D1F6982C972350D8560402C875515646CE9E35CB6F0` |
| ON2-EX `report_calib.md` | `80A7563E3FBDDEA460C53198059CD3E2801A9112CFA4631FDD3A6D3BA3295871` |
| ON3 v1.2 `report_on3_exec.md` | `1F4CD991583545585D12CD23468F0B170C62A5D6E417FF856886CD6E758B4B8F` |
| `PEEK_DISCLOSURE_ON3.md` | `B4CAD9555341A46C47F26981AE84F82ABC28124AADECE37DFE30B05D7FF75260` |
| C187 `report.md` | `7282155E06C051F407D06E54F4EEA3D2A3B9B2B4148F57726C4A6C82281543CC` |
| C190 `record.md` | `7A6286529B166083D3C8234F02A9BEA3672778E2588B9C0DCB61D35841B8BFD3` |

## 3. 输出（本任务；只写 `dual_budget/` 与 tmp/）

| 文件 | SHA256 |
|---|---|
| `PROBLEM_B_v0_4.md` | `D6B37E704DE141FE481A73D4BDDC0FFA6CBB0BA7FA6A686004D568415E6C5C99` |
| `DESIGN_B_v0_4.md` | `9112EDDC3180BA6101DF76CB34282BE84E7E9DF0EBD3EC714C4999388E7D01CD` |
| `design_B_revision_v0_4.py` | `E4968C701DB031BF246767D821A31DC5B8EF9AB50D3A0694462E023F661A3A5E` |
| `design_B_v0_4.json` | `A2D0CC1A01A9EF29FC7B2F0ACDC21658AFCEF6EE9D1F1FDC0829E3CC16601AA1` |
| `report_B_v0_4.md` | 见 usage/复核方 |
| `record_B_v0_4.md` | 本文件（SHA 见 usage/复核方） |
| `usage_B_v0_4.json` | 最后写出（SHA 见复核方） |

## 4. 冻结要点（详见 DESIGN/report）

- filler 公式修正：`(B_E_CU+B_C/κ)−n0×363.6`；18 格 negative=0、全部 `|spend−T_CU|≤1`；primary residual 109.2/filler 110 wells/diff 0.8；κ=0.1 例 residual 91.2。
- T1 **10 arms**：π_dual+C0–C6+C7 两臂；primary 5,000、sensitivity 8,500、total 13,500 arm-runs；pilot 100；单次≤45min、两跑≤90min；fallback 写死。
- x1/x2 40-plan 表/公式冻结；θ 固定；EV 125 gamma worlds+噪声近似，误差门≤0.02，超过 design_invalid；不再称精确枚举。
- primary/500/MDE 0.088594 不变；H_B AND 规则；best-single inner validation；敏感性仅描述。
- T2 描述+PEEK `B4CAD955…`；T3 `data_unavailable/cost_uncalibrated`，r primary=5（714,474.0 CU）；T2/T3 不执行；T1 批准仅实现+资格门、资格门先于结果、失败只 design_invalid、不报结果。

## 5. 执行/边界

- 仅运行 `design_B_revision_v0_4.py` 一次（算术；无数据文件读取/拟合/响应值）；未运行 T1/T2/T3；未改 v0.1–v0.3 文件/其它目录；未晋升代码。
- T1 仅计算证据；不称新颖性/机制/迁移/决策收益/资源足够/独立确认；D1/D3/A1/C187 不重复；技术重复≠独立培养；冻结≠资源足够/关系成立/Stage 1/效果。

## 6. 未做/禁止

- 未读原始响应值做统计；未拟合预测；未运行模拟/效果/湿实验；未改既有报告；不称任何收益/新颖性/机制/迁移/独立确认。
