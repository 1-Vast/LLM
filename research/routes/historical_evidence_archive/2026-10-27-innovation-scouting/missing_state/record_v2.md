# record_v2 —— R198-A4v2 修订执行记录（按 challenge_A4.md；不运行效果）

2026-10-27 ｜ 执行：drugcomb-auditor（task-44）｜ 工作目录 `D:\MAESTRO` ｜ 范围：**只新增** `missing_state/{spec_v2.md, protocol_draft_v2.md, REVISION_A4.md, record_v2.md, usage_v2.json}` 与 `tmp/` 只读复核脚本；**不改 v1 文件、A1/A2/A3/A5 产物、其它目录/INDEX/SYNTHESIS/git**。

## 0. 本轮性质

- 输入：`challenge_A4.md`（endpoint-auditor，task-39）判 **独立候选 stop / 作为 A1 的 (iii) 状态模块 revise（≤5 必改）**；Lead task-44 要求把 5 条必改全部落实。
- 输出：v2 设计/协议 **DRAFT**；**不运行效果、不训练/不拟合、不估 Q、不读响应做统计**；不声称新颖性/机制/决策收益。
- 状态：`blocked_by_A1`（A1 v2 当前 revise 未冻结；A4 启用门 = A1 冻结）。

## 1. 实际执行

### 1.1 读取（只读）

| 类别 | 内容 |
|---|---|
| A4 v1 | `missing_state/{spec.md, protocol_draft.md, prior_art.md, record.md, usage.json}` + `challenge_A4.md` |
| A1 v1 | `conflict_signal/spec.md`（§7 P6=(iii) state z 改进残差、P7=三类签名互不替代；§8 最小新测量请求） |
| A1 v2 | `conflict_signal/spec_v2.md`（§2(iii) 仅 `proxy_only`；§8 证书 `{J,C_conf,X_flip,Δ_pred(U),setup诊断}`；P6/P7 重编号）、`protocol_draft_v2.md`（P6 失败类别/P7 泄漏）、`REVISION_A1.md`；`challenge_A1.md` 状态（revise、未冻结） |
| A2 v3 | `logic_constraints/spec_v3.md`（A2 = A1 支撑模块；III 认证→A4；不评 A1 三类） |
| A5 | `acquisition_stage3/{spec.md, cost_model.md}`（anchored key 34–68 wells；day1 板 1,536/细胞；密度优化 1,344/细胞；等成本 total CU/三价格场景/filler/容差；A5 当前 revise 未冻结） |
| 边界 | `SYNTHESIS.md:11`（C160/C167/C171/C172/C174/C176/C177 相关段）；`ERRATA_Q2.md`/`ERRATA_A3.md`（C174/C175）；`research/2026-10-27-innovation-round-r198/record.md`（A1/A2/A3/A4/A5 并行状态） |
| 数据（只读元数据） | A0 `matched_conditions.csv`（9,154 行、96 细胞）；`identity_map.csv`（125/125→DepMap）；DepMap `CCLE_expression.csv`（表头/行名）、`CCLE_mutations.csv`（DepMap_ID 列）、`sample_info.csv`（culture_type/medium 等列）；`a0.json`（controlled_anchor=92,039）；`q2.json`（`design_check.noise.n_calibration_quadruples=1312`、`coverage_frac_of_observations=0.014255`） |

### 1.2 复核计算（metadata-only；脚本 `tmp/a4v2_numbers.py` → `tmp/a4v2_numbers.json`）

- **96 匹配细胞**（A0 `matched_conditions.csv`，按 spec 的归一化名字规则映射 DepMap）→ 96/96 可映射。
- 覆盖（96 匹配中）：**表达 84、突变 95、culture_type 54、culture_medium 55、表达+突变+culture_type 联合 54、再+medium 仍 54**（与 challenge_A4 §3.1 一致；修正 v1 的 111/125）。
- **1,312 归属**：`q2.json → design_check.noise.n_calibration_quadruples = 1312`，`coverage_frac_of_observations = 0.014255`（1.43%）；`a0.json` 不含 1312 → 纠正 v1。
- **A0 MDE**：`SYNTHESIS.md:11`（C168）五折主端点 **MDE=0.112**；0.240 为各折均值、"资源不可用"已撤回 → 纠正 v1。
- 以上结果只用于设计/覆盖披露；**未读表达值/响应值**（`CCLE_expression` 只读行名/表头；`q2.json`/`a0.json` 为已执行的统计量登记，不重算效果）。

### 1.3 决策（写死到 v2）

1. **所有权**：A4 = A1 的 (iii) 状态支撑模块；A1 owns (i)/(ii)/三类总判定；A4 只出 `state_association` 诊断 + `measurement_request`；**不独立下发 F1/F2/F3**；启用门 = A1 冻结（当前 `blocked_by_A1`）。
2. **输入二选一**：选 **A1 冲突证书**（`{J,C_conf,X_flip,Δ_pred(U),setup诊断}`）；删除 v1 的 Q-flip 主对象与 SCC 独立机制陈述；不另立改名 Q-flip 路径。
3. **Phase 0 降级**：只作 `state-associated instability` 描述/筛选（必要非充分）；删 `M4=K+g`，改 `K+barcode/plate+screen`；补 cell one-hot/plate/leverage 基线；flip 阈值/噪声地板预注册；Phase 0 inconclusive ≠ F3 不存在；**Phase 1 不以 Phase 0 显著为条件**。
4. **数字改正**：84/95/54/55/54；`S_pre`/`S_measure` 拆分（DAY1/GR/DT 归 S_measure，不得支持 F3）；A0 MDE=0.112；1,312→A2；δ_min operational（决策成本或 reliability-adjusted + 敏感性）；MDE 模拟写死 EPV/seed/聚类。
5. **Phase 1 重写**：well 账（anchored 34–68 wells/key + day1 1,536/细胞 + 密度优化 1,344/细胞；pilot 7,392–9,024 wells、4×6 main 14,784–18,048、6×8 main 23,808–30,336）；24 配对仅 pilot（功效约 50–60%）、主 F3 证据需 ≥36–48 pair-cell；桥接（操纵 S_measure 而非培养基/氧 g）；补 vehicle/阳性/edge/盲法/独立培养；失败类别补 `inconclusive_design`/`leakage`/`indistinguishable_F1_F3`/`cost_sensitive`；修正 v1 的 192/384。
6. **先例/去重/措辞**：明确**本轮无新检索**（v1"有限检索"降级）；逐条标注 A1 v1 P6/P7 与 v2 重编号；A2 III、A3/C175、C174/C176/C177、A5；Phase 2 复用 A5 等成本；保留/加强措辞模板。

## 2. 本轮未做 / 限制

- **未运行任何效果/模拟器/时间预测/训练/拟合/估 Q**；未读响应数值做统计。
- **无新文献检索**：本轮只复用既往登记（`prior_art.md` v1 不改）；不声称新颖性/差异；"未发现"只作既往检索结果。
- **不改 v1**：v1 五个文件的 SHA 与 challenge_A4 §9 一致（未动）；v2 文件独立。
- 未改 A1/A2/A3/A5 产物、其它目录、INDEX、SYNTHESIS、git。
- **残余**：A1 未冻结（`blocked_by_A1`）；State 面板覆盖 54/84 很紧、Phase 0 预期 inconclusive_power；Phase 1 需真实新测量/预算/采购；操纵↔S_measure 桥接需 pilot 验证；A2 III 认证/A5 等成本/A1 三类判定均不在 A4 权限内。

## 3. 下一执行者从哪里开始

1. 先读 `spec_v2.md` §0（所有权/启用门/输入）+ `protocol_draft_v2.md` §2（P0a–P0e）与 §3（Phase 0）、§4（Phase 1）。
2. **不要在本轮启动任何 Phase**：A1 未冻结 → A4 保持 `blocked_by_A1`；即使 A1 冻结，Phase 0 也需先冻结 S 面板/模型/δ_min/MDE 方案并过独立挑战。
3. 若 Lead 只保留 A4 为 A1 模块：等 A1 冻结后把 A4 的 `state_association` + `measurement_request` 作为 A1 v2 (iii) 的输入；不重开独立候选。
4. 若 Lead 要独立候选：必须按 challenge_A4 §0 改命题/改名（不得沿用"冲突/三类失败"判定口径），并按 v2 的 Phase 0/1 设计另立协议。

## 4. 产物 SHA256

见 `usage_v2.json`（写盘后计算）；v1 文件哈希与 challenge_A4 §9 一致（未改）。
