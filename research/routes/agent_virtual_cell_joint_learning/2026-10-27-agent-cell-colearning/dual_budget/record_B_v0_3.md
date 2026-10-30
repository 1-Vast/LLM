# record_B_v0_3 —— R201-B.2 审计记录（T1 冻结候选；未运行）

2026-10-28 · 角色：ON1/ON2/ON2.2/ON3 执行者（非提案者）。任务：R201-B.2（按 `challenge_B_v0_2.md` revise 5 必改冻结 T1 预注册；仅 T1 实现+资格门，不执行结果/T2/T3）。**未运行效果/未拟合/未读响应/无湿实验；不称新颖性/机制/迁移/决策收益。**

## 1. 时间线

| 时间（本机） | 事件 |
|---|---|
| 00:26–00:27 | 读 `challenge_B_v0_2.md`（SHA `4D3A3AB5…`）、v0.2 文件、R201/A5/ON2-EX/ON3/PEEK/C187/C190；确认 5 必改 |
| 00:27–00:29 | 写 `design_B_revision_v0_3.py`（仅算术：primary 配置/500、整数 key+filler、敏感性表、H_B 规则、冻结旋钮、wall、T3 r）；运行一次生成 `design_B_v0_3.json` |
| 00:29–00:31 | 写 `PROBLEM_B_v0_3.md`、`DESIGN_B_v0_3.md`、`report_B_v0_3.md`、本 record、`usage_B_v0_3.json`；核对 SHA；未改 v0.1/v0.2 文件 |

## 2. 输入（只读；SHA256）

| 文件 | SHA256 |
|---|---|
| `challenge_B_v0_2.md`（R201-B.2-C1） | `4D3A3AB565E184975DB87CF971E6839E5795C761FD956155386324F5B9A07712` |
| `PROBLEM_B_v0_2.md` | `618C6EDA5897524EA9A763F8EFFD15CFD55476A8B081907A74B866E35CC01158` |
| `DESIGN_B_v0_2.md` | `6E30C98D770BBFE6F8A0F93C1CAB9E0E3B7C619463B054243A71C5197CD68911` |
| `design_B_v0_2.json` | `128E129D953FEAF1852A5EBC971A976B9576B4A66A131AF9AE56773FA65128BC` |
| `report_B_v0_2.md` | `9F6AD80DF75E28482E7B8E0FA8180D7044985A040EF625D14AFBC8B1530143D4` |
| `record_B_v0_2.md` | `D974E59A06AB85578E568A853093B98F2B48B7871FE49F12CF698C1736E1116E` |
| `dual_budget/challenge_B.md`（前轮） | `45E18D67158BC7FE32FFF70B17953F58F29448AF52902DD56316B3DE27539B09` |
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
| `PROBLEM_B_v0_3.md` | `753B9CF8BEA1CC8B2963F7F67D5622C710CE1F85D0631F035C777B6403C5F900` |
| `DESIGN_B_v0_3.md` | `183BE5DEA3FBCCE2B95C551C1D99B80FF25A75ADA29A28B9EC102B3A06AFF22C` |
| `design_B_revision_v0_3.py` | `AA49E4C8E3565FC59D7F8B732D59DFEBADACF4C618E4BC70C807172824A66D1C` |
| `design_B_v0_3.json` | `50E6EE30959CACD9894F799276BE907388189BCFF9B225DC7E6C68611E8A27D9` |
| `report_B_v0_3.md` | 见 usage/复核方 |
| `record_B_v0_3.md` | 本文件（SHA 见 usage/复核方） |
| `usage_B_v0_3.json` | 最后写出（SHA 见复核方） |

## 4. 冻结要点（详见 DESIGN/report）

- primary `(B_C=1200s,B_E=16 keys),κ=1,σ=0.10`；**500 独立 replicate=500 decision units**；MDE=0.088594≤0.10；主 H_B 只用 primary。
- 敏感性 17 格×50=850 replicate（seed 规则写死）；只描述/`cost_sensitive`。
- 固定预算对 (300,4)/(1200,16)/(3600,64)；κ{0.1,1,10}；σ{0.05,0.10}；网格唯一。
- 整数 keys+filler：experiment-only n0=19 keys + blank/QC filler 109.2 CU（primary 例）；filler 不进学习器；无泄漏单测断言。
- H_B AND：两 Holm 主对比均正且显著且点估计≥δ=0.10；否则 partial/no/below_delta；主检验仅 primary。
- 模拟器旋钮全部冻结（O/M/σ/γ/τ/f/θ/证书阶梯/动作库/EV/R_max/seed/schema/两跑）。
- wall：primary 4,000 + sensitivity 6,800 arm-runs；pilot 10 replicate；单次≤45min/两跑≤90min；fallback 写死；资格门先于结果。
- T2 描述+PEEK `B4CAD955…`；T3 `data_unavailable/cost_uncalibrated`，r primary=5（714,474.0 CU）；T2/T3 不执行。

## 5. 执行/边界

- 仅运行 `design_B_revision_v0_3.py` 一次（算术；无数据文件读取/拟合/响应值）；未运行 T1/T2/T3；未改 v0.1/v0.2 文件/其它目录；未晋升代码。
- 请求批准 **仅 T1 模拟器实现+资格门**；不批准结果/T2/T3 执行；T1 仅计算证据，不外推真实决策收益。
- 冻结≠资源足够/关系成立/Stage 1/效果；不称新颖性/机制/迁移/决策收益/独立确认；D1/D3/A1/C187 不重复；技术重复≠独立培养。

## 6. 未做/禁止

- 未读原始响应值做统计；未拟合预测；未运行模拟/效果/湿实验；未改既有报告；不称任何收益/新颖性/机制/迁移/独立确认。
