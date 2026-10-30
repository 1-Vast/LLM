# report_B —— R201-B 双预算决策设计报告（**设计/资格轮，未运行**）

2026-10-27/28 · 角色：ON1/ON2/ON2.2/ON3 执行者（非提案者）。任务：R201-B（方向2 双预算决策形式化 + 预注册设计；本轮不执行）。**本报告只总结设计/算术/可执行性；不运行效果、不拟合预测、不读响应值、无湿实验；不称新颖性/机制/迁移/决策收益/资源足够/独立确认。**

## 0. 交付

| 文件 | 作用 | SHA256 |
|---|---|---|
| `PROBLEM_B.md` | 形式化问题/判据/策略/边界 | `3CB742415010A6ACE8E87CCC11FE004EC61668645F74F375AF03E19B2EFE7659` |
| `DESIGN_B.md` | 预注册设计草案（比较器/预算/终点/MDE/零/失败/停止/Tiers） | `69FF9B101CA36127E122CD76839599D0828A0B28DB7C7CD1E5827C4D6BD71C63` |
| `design_B.py` | 仅设计/预算算术；无数据读取/拟合 | `151BB6136D9174D8BEB398C39904C2E403A91CBF33C1E6AC5A12A6E9CC115330` |
| `design_B.json` | 确定性算术输出（MDE/预算/门） | `38A1FBD0A8FB1A0FF1C3EFF2B262538DCD44D9917B0DC38D1122C6A12FE97808` |
| `record_B.md` / `usage_B.json` | 审计记录/用量 | 见各文件 |

## 1. 形式化结论

**决策状态** = (候选计划集 P、当前共同反事实模型 M_t、计算预算 B_C [实测 CPU-second]、实验预算 B_E [wells/plates/keys/rounds + A5 规划 CU]、动作空间 compute∪experiment、策略 π)。每轮策略选择：继续计算、买实验（买什么）、或停止。

**可操作判据（写死）**：
1. **compute-limited**：固定数据、提高求解精度/迭代/证书后，top-k 决策集改变，或认证缺口 `g_C = (h_out−h_in)/Δ_decision > 1` → 继续计算，**不买实验**。
2. **evidence-limited**：`g_C≤1` 后相容集内仍有改变决策的世界，且 `MDE_decision(B_E)≤δ_min≤headroom`、power≥0.80、期望决策价值>成本 → 买**每 CU 决策歧义下降最大**的实验包。
3. **compute_sufficient**：`g_C≤1` 且相容世界给出同一决策 → 停止，不买实验。
4. **不可识别**：预算内无法达到 `MDE≤δ_min` → `evaluation_cannot_distinguish`（未决，不是结构不存在/策略失败）。

**与 AL/BOED/COPEx 关系**：一般概念（决策价值选实验、非短视、约束生成、计算决策）已被覆盖；CoMap/LAWM/MDA/COPEx 等已有联合/任务摘要/动态约束。本设计**不声称新颖性**；差别仅限定为具体共享对象（跨计划共同反事实/约束算子 + 计算认证状态）与更新运算（计算证书收紧 + 真实反馈统一修订），是否成立由同信息/同预算对照裁决。

## 2. 预注册设计摘要（草案，未冻结）

- **主假设 H_B**：同等总成本下，`π_dual` 在留出未测计划上的 top-k 决策收益高于最佳单一预算策略（compute-only/experiment-only），且不是预测提分替代；预测指标只作辅助/阴性对照。
- **主终点**：未测计划 top-k 决策收益（k=5，`topk_hit` 差，按独立 cell/fold 配对）；次：归一化后悔/选择准确率/预测辅助；迁移另立协议，不做主推断。
- **比较器（同信息/同预算）**：C0 固定计算+随机实验；C1 固定实验+更多计算；C2 全历史重训；C3 普通决策 AL；C4 GP/BOED；C5 通用求解器；C6 随机预算分配；C7 compute-only/experiment-only；oracle 仅描述上界。
- **预算对照**：同一 `(B_C,B_E)` 预算对；计算秒实测（含求解/认证/重拟合/构图）；实验按 A5 wells/CU（含对照/重复/失败板/setup/filler/轮次）；三价格场景重跑，排序不一致 → `cost_sensitive`；禁止等 rows/keys/wells 冒充等成本。
- **零模型**：随机决策/随机预算分配/shuffle 计划效用/compute-only/experiment-only/solver-seed shuffle。
- **失败类别**：`data_unavailable`、`design_invalid`（precision/leakage/cost/utility）、`evaluation_cannot_distinguish`、`no_increment`、`no_decision_benefit`、`cost_sensitive`、`oracle_unknown`、`protocol_deviation`、`compute_budget_exceeded`。
- **停止**：同信息普通方法等效 → 撤新意；决策收益不成立/仅预测改善 → 停决策创新；MDE>δ/效用未定义 → 未决/blocked；资源不可得 → data_unavailable；泄漏/偏差 → design_invalid。

## 3. 检定力/预算算术（design_B.json，确定性）

- **δ_min=0.10 暂定**（top-k hit 绝对差）；业务效用定义未冻结前标 `blocked_by_utility_definition`。
- **MDE（保守）**：decision accuracy `2.801585×sqrt(0.5/n)`；rank Δρ `2.801585×sqrt(2/(n−3))`。
- **本地 O'Neil**：n=6 → decision MDE **0.8087**、rank MDE **2.2875**；n=30 pooled → **0.3617 / 0.7625** → 远大于 0.10 → **`evaluation_cannot_distinguish`（precision_insufficient）**；加 wells/技术重复不增加独立细胞 n（D3 教训）。
- **合成模拟器**：500 独立 replicate → decision MDE **0.0886 ≤0.10**，**仅计算证据**；须先过模拟器资格（oracle/噪声/预算 scaling/泄漏），不能外推生物决策收益。
- **湿实验**：达 decision MDE 0.10 需约 **393 独立决策单元**；A5 anchored central 363.6 CU/key → **142,894.8 CU**（A5 100k 示例只能买约 275 keys）；C136 1,600-key 80% ≈ **581,760 CU**；当前无报价/LOI/湿预算/独立培养 → **`data_unavailable / cost_uncalibrated`**。
- **计算预算**：B_C ∈ {300,600,1200,2400,3600}s；ON3 v1.2 实测 wall **1272.06/1130.61s**（B6 5,000 perms、bootstrap 5,000），raw 306.722s/5,000 perms 作预算锚；所有计算/认证计费。

## 4. 可执行性裁决

| Tier | 状态 | 说明 |
|---|---|---|
| T0 形式化/算术（本轮） | **完成** | 本目录；只读既有报告+算术 |
| T1 合成模拟器 | **可构建（未运行）** | 可做算法证伪；必须资格+独立挑战；仅计算证据 |
| T2 O'Neil 回顾性 dev | **可做但不可判主假设** | 决策/rank MDE 远>0.10；仅操作/描述；需 PEEK 披露与另立协议 |
| T3 前瞻湿实验 | **data_unavailable / cost_uncalibrated** | 无 wet budget/报价/LOI/独立培养；不得假装可执行 |

## 5. 缺口/所需测量

1. 真实报价/LOI 替换 A5 系数（否则 CU 仅 planning，不写货币结论）。
2. 湿实验预算/细胞材料/板位/独立培养/失败率 pilot。
3. 业务效用尺度与 δ_min 操作化（否则 `blocked_by_utility_definition`）；headroom 需回溯菜单 oracle，前瞻菜单记 `oracle_unknown`。
4. 若用 O'Neil：必须带 `PEEK_DISCLOSURE_ON3.md` `B4CAD955…`（non-blind/peeked），仅开发性描述，不作决策收益/迁移/机制主张。
5. 模拟器资格与独立挑战；Lead 批准后才可冻结/执行。
6. D1 stop / D3 design_invalid / A1 data_unavailable / C187 pair-level AL 饱和均为已否定/关闭路线：本设计不退回普通 pair-level AL、不退回预测提分、不把技术重复当独立 n。

## 6. 边界（随本报告引用）

- 仅设计；**未运行**效果/拟合/响应读取/湿实验；不称新颖性/机制/迁移/决策收益/资源足够/独立确认；冻结 ≠ 资源足够/关系成立/Stage 1/效果。
- 本设计写于 ON3 v1.2/QUICK 之后（non-blind/inherited-peek 上下文）；未用其结果选择本设计的方向/阈值/预算/比较器；未来若用 O'Neil 数据须附 PEEK 披露，不得称盲验/独立确认/预注册确认。
- 建议：先交独立挑战者只读复核（形式化/判据/预算对照/终点 MDE/停止条件/边界），再决定是否允许 T1 模拟器预注册；当前不建议任何 T2/T3 执行。
