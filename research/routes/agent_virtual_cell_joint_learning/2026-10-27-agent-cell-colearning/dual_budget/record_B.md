# record_B —— R201-B 设计任务审计记录（design-only；未运行）

2026-10-27/28 · 角色：ON1/ON2/ON2.2/ON3 执行者（非提案者）。任务：R201-B（与真实实验双预算决策形式化+设计）。**本任务只做设计/资格算术；未运行效果、未拟合预测模型、未读响应值、未做湿实验；不称新颖性/机制/迁移/决策收益/资源足够/独立确认。**

## 1. 时间线

| 时间（本机） | 事件 |
|---|---|
| 00:13–00:14 | 读 R201 `BRIEF.md`、`agent-cell-colearning/report.md`（方向1/2 与机制边界）、`d3_feedback/report_d3_v0_2.md`、`DECISION_D1_STOP.md`、`acquisition_stage3/cost_model.md`+`challenge_A5.md`、ON2-EX `report_calib.md`、ON3 v1.2 `report_on3_exec.md`/`PEEK_DISCLOSURE_ON3.md`、C187 `report.md`、C190 `record.md`/`BRIEF.md` |
| 00:14–00:15 | 建 `dual_budget/`；写 `design_B.py`（仅预算/检定力算术，硬编码已公开设计常量；无数据读取/拟合）；运行一次生成 `design_B.json` |
| 00:15–00:17 | 写 `PROBLEM_B.md`（形式化/判据/策略/边界）、`DESIGN_B.md`（预注册草案：假设/比较器/预算/终点/MDE/零/失败/停止/Tiers/可执行性） |
| 00:17–00:18 | 写 `report_B.md`、本 record、`usage_B.json`；核对 SHA；确认只写 `dual_budget/` 与 tmp |

## 2. 输入（只读；SHA256）

| 文件 | SHA256 |
|---|---|
| `research/2026-10-27-innovation-round-r201/BRIEF.md` | `3F859B1FA234331194C7C4A61A5F9AF516860AF25232834DFB22E5526B9006DE` |
| `research/2026-10-27-agent-cell-colearning/report.md` | `91FC9E7BCB40826E124AC19995C27878DEB40EFF277C42176A07E99248CA8020` |
| `d3_feedback/report_d3_v0_2.md` | `F36E2BBC343873910CBB5AD7D7234161321763ECF12CF869B0FD487EA517D39E` |
| `d1_information/DECISION_D1_STOP.md` | `86D802E9C19CD878758155FBECD1EE3DCE3CA3BF05CE17C33E2C81AE64E18A25` |
| `acquisition_stage3/cost_model.md` | `46824DBE8D967CEC090D5D1F6982C972350D8560402C875515646CE9E35CB6F0` |
| `acquisition_stage3/challenge_A5.md` | `18DE99B4F22DE720088B9E895C04BE804E212D0BB4ADFD29CB2E20A787709ED5` |
| `core-module-design/oneil_dev/exec_calibration/report_calib.md` | `80A7563E3FBDDEA460C53198059CD3E2801A9112CFA4631FDD3A6D3BA3295871` |
| `core-module-design/oneil_dev/report_on3_exec.md`（v1.2） | `1F4CD991583545585D12CD23468F0B170C62A5D6E417FF856886CD6E758B4B8F` |
| `core-module-design/oneil_dev/PEEK_DISCLOSURE_ON3.md` | `B4CAD9555341A46C47F26981AE84F82ABC28124AADECE37DFE30B05D7FF75260` |
| `2026-10-27-agent-cell-identifiability-r187/report.md` | `7282155E06C051F407D06E54F4EEA3D2A3B9B2B4148F57726C4A6C82281543CC` |
| `2026-10-27-innovation-round-r190/record.md` | `7A6286529B166083D3C8234F02A9BEA3672778E2588B9C0DCB61D35841B8BFD3` |
| `2026-10-27-innovation-round-r190/BRIEF.md` | `7EB7B4CCA8D61CC2BE16EB23E9B59CEE22EB33947BCABD8A80EA04775CBEEB2F` |

## 3. 输出（本任务；只写 `dual_budget/` 与 tmp/）

| 文件 | SHA256 | 说明 |
|---|---|---|
| `PROBLEM_B.md` | `3CB742415010A6ACE8E87CCC11FE004EC61668645F74F375AF03E19B2EFE7659` | 形式化/判据/策略/边界 |
| `DESIGN_B.md` | `69FF9B101CA36127E122CD76839599D0828A0B28DB7C7CD1E5827C4D6BD71C63` | 预注册设计草案 |
| `design_B.py` | `151BB6136D9174D8BEB398C39904C2E403A91CBF33C1E6AC5A12A6E9CC115330` | 仅设计/预算算术；无数据读取/拟合 |
| `design_B.json` | `38A1FBD0A8FB1A0FF1C3EFF2B262538DCD44D9917B0DC38D1122C6A12FE97808` | 确定性设计算术输出 |
| `report_B.md` | `0EB0E49A14CE8CEA1AE329A4B93C380EDFD103253C810950C27D015CBE3EC9C6` | 设计报告 |
| `record_B.md` | 本文件（SHA 见 usage/复核方） | 审计记录 |
| `usage_B.json` | 最后写出（SHA 见复核方） | 用量/attestation |

## 4. 关键设计结果（详见 report/DESIGN）

- **形式化**：决策状态 (P, M_t, B_C, B_E, A, π)；判据 = 计算认证缺口 `g_C=(h_out−h_in)/Δ_decision`（>1 → compute-limited，先算不买） + 计算收敛后相容集决策翻转 + `MDE_decision≤δ_min≤headroom`/power（→ evidence-limited）；`g_C≤1` 且决策唯一 → compute_sufficient；预算内无法分辨 → `evaluation_cannot_distinguish`。
- **主假设**：同总成本下 `π_dual` 的未测计划 top-k 决策收益 > 最佳单一预算（compute-only/experiment-only），且非预测提分替代；比较器 C0–C7（随机实验/更多计算/全重训/普通决策 AL/GP-BOED/通用求解器/随机预算/单预算）+ oracle 描述上界；同信息/同预算/同 cell 集合/同 setup 会计/计入对照重复失败板轮次；三价格场景重排。
- **MDE 算术**：δ_min=0.10 暂定；本地 O'Neil n=6 decision MDE 0.8087、rank MDE 2.2875；n=30 pooled 0.3617/0.7625 → **precision_insufficient/evaluation_cannot_distinguish**；合成器 500 replicate decision MDE 0.0886 → **仅计算证据**；湿实验需约 393 独立决策单元（≈142,894.8 CU central），A5 100k 示例只买 275 keys，C136 1,600-key 门槛约 581,760 CU → **data_unavailable/cost_uncalibrated**。
- **预算**：B_C 300–3600s（ON3 v1.2 实测 wall 1272.06/1130.61s；B6 5,000 perms、bootstrap 5,000；raw 306.722s/5,000 perms 锚）；B_E 按 A5 wells/CU（非货币，报价/LOI 前仅 planning）；所有计算/认证/实验选择/对照/失败重买计费。
- **停止/失败**：普通方法等效 → 撤新意；只有预测改善 → `no_decision_benefit`；MDE>δ/效用未定义 → 未决/blocked；资源不可得 → data_unavailable；D1 stop/D3 design_invalid/A1 data_unavailable/C187 pair-AL 饱和不重复。
- **非盲/peek**：设计写于 ON3 v1.2/QUICK 后；未用其响应/结果选择方向/阈值/预算；若用 O'Neil 必须带 PEEK 披露；不得称盲验/独立确认/预注册确认。

## 5. 执行/边界

- 仅运行 `design_B.py` 一次（算术；无数据文件读取/拟合/响应值）；未运行 acquisition/效果/训练/湿实验；未修改其它目录、未晋升代码。
- 本设计是 **未冻结草案**；需独立挑战（形式化/判据/等预算/终点 MDE/停止条件/边界）后再由 Lead 决定是否允许 T1 模拟器预注册。当前**不建议 T2/T3 执行**。
- 冻结 ≠ 资源足够/关系成立/Stage 1/效果；不称新颖性/机制/迁移/决策收益/独立确认；技术重复≠独立培养；O'Neil 限制不变。

## 6. 未做/禁止

- 未读原始响应值做统计；未拟合预测模型；未 sim/效果实验；未买湿实验；未改 D1/D3/A1/C187/C190 产物；未声称任何决策收益/新颖性/机制/迁移。
