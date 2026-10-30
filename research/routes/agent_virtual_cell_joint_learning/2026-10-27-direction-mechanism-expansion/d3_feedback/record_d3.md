# record_d3 —— R200-D3 资格/设计记录（record_d3.md）

2026-10-27 · 角色：ON1/ON2/ON2.2/ON3 执行者（非提案者）· 任务：R200-D3（task-87）。
**状态：design/qualification only；未执行 ON3/D3 效果，未运行预测/更新器/acquisition，未读原始响应值做统计。**

## 1. 时间线

| 时间（本机） | 事件 |
|---|---|
| 22:31 | 读 task-87、R200 BRIEF、direction-mechanism-expansion/report.md + mechanisms_v3.md、cross-domain directions_v1、A0/Q2、ON2 v2.2/freeze、ON2-EX calib、ON3 v1.1/PEEK |
| 22:31–22:34 | 建立 `d3_feedback/`；写 `d3.py`（metadata-only：只读 ON2 frozen `on2.json`/calib，不读 workbook/响应值；单 anchor 层/资格/反馈预算算术） |
| 22:34 | 运行 `d3.py` → `d3.json`：verdict `qualified_with_conditions`；units 340,088/contexts 2,149/cells 30；feedback 120 units/11.0 plate-equiv；MDE prior 0.0287644381 ≤ δ_min 0.10 |
| 22:34–22:36 | 写 `PROTOCOL_D3.md`/`report_d3.md`/本记录/`usage_d3.json`；核对 SHA；确认未改其它目录/未执行效果 |

## 2. 输入（只读）

| 文件 | SHA256 |
|---|---|
| `oneil_dev/on2.json`（ON2 v2.2 frozen metadata） | `AD7E6D1359ED69670548B8EF237EA5B3415F934F5FF305B352EA3C79AC81F7C8` |
| `oneil_dev/exec_calibration/calib.json`（ON2-EX） | `DC2D29C1B92059F431761BB39C27F9C54CFD3909AB705E8D1FA3AE21C4A48A6A` |
| `2026-10-27-conditional-shift/a0.json` | `72BBAF6D…1ECA22` |
| `2026-10-27-conditional-shift/q2.json` | `94C5CD9B…73DE2` |
| `direction-mechanism-expansion/report.md` | `B6B6C3F2…FFCBC` |
| `direction-mechanism-expansion/mechanisms_v3.md` | `577CC6B0…20CFE` |
| `innovation-round-r200/BRIEF.md` | `B75BD21A…A8CB6` |
| `cross-domain-directions/directions_v1.md` | `752CC80A…FE9C` |

> d3.py 只读 on2.json/calib.json；A0/Q2/report/BRIEF/cross-domain 只作文字依据/哈希记录；未解析原始响应值。

## 3. 资格结论

- **verdict：`qualified_with_conditions`**。
- 单 anchor 层：**340,088 units / 2,149 contexts / 30 target cells / 5 folds（6 cells each）**；每折 units 68,152/66,743/66,556/69,738/68,899；contexts 432/427/427/432/431。
- 每 unit：4 technical reps/member（Δ 的 replicate-level differences=4）、8 wells、2 member measurements；**independent cultures=1**；technical reps 只做 precision，n_eff=held-out cells（6）。
- 覆盖/缺失：complete-case rows 363,090/368,832=98.44%；batch3 **0/5,040**；702 个 15-row pair-cell；missing 78/198/5,742；batch2 disclosure-only；无双药参照。
- 条件/限制：O'Neil 仅开发性；单 anchor 派生不是独立 single-dose screen；技术重复≠独立培养；batch3 全失/702 pair-cell/缺失机制未知；不称 independent confirmation/migration/decision benefit/mechanism。
- **Jaaks 备选：not_qualified_for_D3_endpoint**：A0/Q2 matching 为 `SYNERGY_DELTA_EMAX`；D3 禁止 ΔEMAX 拼接；若未来用，需独立 viability 端点+A0 匹配/端点可比；本设计不用。

## 4. 设计摘要

- **切分**：5 折继承 ON2；每折 24 support cells + 6 held-out cells；不重分；目标为 held-out 全部单剂量 units（未查询成员×伙伴），不回测。
- **固定反馈**：24 units/fold，总 120；1 轮；deterministic hash/stratified seed 20261130；response-independent；所有 updater/control 同包同成本；no acquisition。
- **成本**：8 wells/unit；每折 192 wells=2×96-well plates；10% failure → 2.2 plate-equiv/fold；总 **11.0 plate-equiv**；query measurements 0。
- **Updaters**：U_conflict（primary）、U_residual、U_posterior、U_leverage。
- **Controls**：C0 global mean；C1 static additive；**C2 full-history retrain（primary）**；C3 ordinary adaptation；C4 hierarchical/EB；C5 GP；C6 projected kernel/ridge equivalent。同信息/同预算；不给 U_conflict 额外数据。
- **Primary H_D3**：U_conflict − C2 的 held-out Spearman Δρ ≥ δ_min=0.10；唯一 primary；其余 secondary/描述性。
- **MDE**：δ_min=0.10；ON2-EX prior σ_e=0.1422665081、SE_unit=0.0251494031、n_eff=6 → MDE80=**0.0287644381**≤δ_min（design prior pass）；执行前测 MDE，>δ_min→design_invalid；rank 用 null/bootstrap，CI 不能排除 0→evaluation_cannot_distinguish。
- **Null**：feedback label permutation 1,000（primary）；random pack 1,000；no-feedback static/global。
- **Failure**：data_unavailable/design_invalid/evaluation_cannot_distinguish/no_increment。
- **Stop**：只纠已测点→停 feedback-generalization；普通方法等效/更好→撤 unique-operator；MDE>δ_min→design_invalid；泄漏/端点混用→design_invalid；不比较 acquisition。

## 5. 产出

| 文件 | 说明 |
|---|---|
| `d3.py` | metadata-only 资格/设计算术（不拟合/不读响应） |
| `d3.json` | 资格数字、split、feedback budget、updaters/controls、MDE、null、failure/stop、边界、输入 SHA |
| `PROTOCOL_D3.md` | 预注册设计草案（draft；未执行） |
| `report_d3.md` | 资格/设计报告（设计 only） |
| `record_d3.md` | 本记录 |
| `usage_d3.json` | 运行/输出 SHA/attestation，最后写出 |

## 6. 未做/边界

- **未执行效果/未拟合预测/未比较 acquisition/未训练更新器**；未读 O'Neil workbook 或原始响应值做统计。
- 不称独立确认/迁移/决策收益/机制/新颖性；技术重复≠独立培养；不与 ΔEMAX 拼接。
- 结果只可写方向内开发性描述；本文件是设计，不是结果；须独立挑战 + Lead 批准后才可另立执行协议。
- 未改其它目录/冻结产物/核心代码；只写 `d3_feedback/` 与 `tmp/`。
