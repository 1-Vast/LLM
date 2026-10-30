# record_B_v0_2 —— R201-B.1 修订审计记录（design-only；未运行）

2026-10-28 · 角色：ON1/ON2/ON2.2/ON3 执行者（非提案者）。任务：R201-B.1（按 `challenge_B.md` revise 5 必改修订 v0.2；仅 T1 模拟器预注册，不执行 T1/T2/T3）。**未运行效果/未拟合预测/未读响应值/无湿实验；不称新颖性/机制/迁移/决策收益。**

## 1. 时间线

| 时间（本机） | 事件 |
|---|---|
| 00:20–00:21 | 读 `challenge_B.md`（SHA `45E18D67…`）、v0.1 产物、BRIEF/报告/成本/MDE 材料；确认 5 必改 |
| 00:21–00:23 | 写 `design_B_revision.py`（仅算术：等成本换算、primary MDE、decision unit/key→CU、T1 预算/T3 成本）；运行一次生成 `design_B_v0_2.json` |
| 00:23–00:26 | 写 `PROBLEM_B_v0_2.md`、`DESIGN_B_v0_2.md`（形式化/判定树/等成本/primary统一/T1 预注册/T2/T3 边界） |
| 00:26–00:27 | 写 `report_B_v0_2.md`、本 record、`usage_B_v0_2.json`；核对 SHA；未改 v0.1 文件 |

## 2. 输入（只读；SHA256）

| 文件 | SHA256 |
|---|---|
| `dual_budget/challenge_B.md`（R201-B-C1） | `45E18D67158BC7FE32FFF70B17953F58F29448AF52902DD56316B3DE27539B09` |
| `dual_budget/PROBLEM_B.md`（v0.1） | `3CB742415010A6ACE8E87CCC11FE004EC61668645F74F375AF03E19B2EFE7659` |
| `dual_budget/DESIGN_B.md`（v0.1） | `69FF9B101CA36127E122CD76839599D0828A0B28DB7C7CD1E5827C4D6BD71C63` |
| `dual_budget/design_B.py`（v0.1） | `151BB6136D9174D8BEB398C39904C2E403A91CBF33C1E6AC5A12A6E9CC115330` |
| `dual_budget/design_B.json`（v0.1） | `38A1FBD0A8FB1A0FF1C3EFF2B262538DCD44D9917B0DC38D1122C6A12FE97808` |
| `dual_budget/report_B.md`（v0.1） | `0EB0E49A14CE8CEA1AE329A4B93C380EDFD103253C810950C27D015CBE3EC9C6` |
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
| `PROBLEM_B_v0_2.md` | `618C6EDA5897524EA9A763F8EFFD15CFD55476A8B081907A74B866E35CC01158` |
| `DESIGN_B_v0_2.md` | `6E30C98D770BBFE6F8A0F93C1CAB9E0E3B7C619463B054243A71C5197CD68911` |
| `design_B_revision.py` | `57749DA797DBD0907CE5AE13739ADF69969DD6BA4049B37B518D87576DDB3423` |
| `design_B_v0_2.json` | `128E129D953FEAF1852A5EBC971A976B9576B4A66A131AF9AE56773FA65128BC` |
| `report_B_v0_2.md` | 见 usage/复核方 |
| `record_B_v0_2.md` | 本文件（SHA 见 usage/复核方） |
| `usage_B_v0_2.json` | 最后写出（SHA 见复核方） |

## 4. 关键修订结果（详见 report/DESIGN）

- **等总成本**：T1 合成 `κ` s/CU ∈{0.1,1,10}；`T=B_C+κ·B_E_CU`；compute-only `B_C_eff=B_C+κ·B_E`、experiment-only `B_E_eff=B_E+B_C/κ`；残余 filler；账本可审计；best-single 只在 inner validation 选；测试集两主对比 Holms、max 仅描述（同时 CI）。
- **判据**：T1 合成证书 `[h_in,h_out]`、`Δ_utility=0.10`、headroom/EV 可算；唯一判定树；B_C 耗尽 g_C>1 → `compute_budget_exceeded`（不买实验/不静默停）；无证书模型 → `certificate_unavailable`；headroom 未知 → `oracle_unknown`；T2/T3 未冻结前不下结论。
- **Primary 统一**：top-1 selection accuracy（[0,1]）；MDE paired-binary：n=6/30/393/500 → 0.808748/0.361683/0.099929/0.088594；δ=0.10 为操作阈值；top-k/regret 降为 secondary（T1 校准）；decision unit=独立 cell/fold 菜单；T3 r keys/unit∈{1,5,10} → 142,894.8/714,474.0/1,428,948.0 CU；393 keys≠393 units。
- **T1 预注册**：500 独立 replicate/seed；共享算子+隐藏 γ+噪声；oracle/top-k/null 校准；无泄漏单测；C0–C7 等价；等成本；两跑；schema；pilot wall 门（≤45min/两跑≤90min）；资格门先于结果。
- **T2/T3**：T2 仅描述+PEEK `B4CAD955…`；T3 `data_unavailable/cost_uncalibrated`；不做主检验；不称新颖性/决策收益/迁移/机制。

## 5. 执行/边界

- 仅运行 `design_B_revision.py` 一次（算术；无数据文件读取/拟合/响应值）；未运行 T1/T2/T3；未改 v0.1 文件/其它目录；未晋升代码。
- 本 v0.2 为未冻结草案；建议独立挑战者只读复核后，由 Lead 决定是否批准 **T1 预注册（仅 T1）**；T2/T3 不批执行。
- 冻结≠资源足够/关系成立/Stage 1/效果；T1 仅计算证据，不外推生物/真实决策收益；技术重复≠独立培养；D1/D3/A1/C187 不重复。

## 6. 未做/禁止

- 未读原始响应值做统计；未拟合预测；未运行模拟/效果/湿实验；未改 ON3/PEEK/A5/既有报告；不称任何收益/新颖性/机制/迁移/独立确认。
