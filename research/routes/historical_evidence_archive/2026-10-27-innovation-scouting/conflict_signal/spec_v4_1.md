# spec_v4_1 — R199-A1v4.1 补丁规格（gate 修复 + 106 上界 + 审计对齐）

2026-10-27。本文件是 [spec_v4.md](spec_v4.md) 的**补丁**（v4 文件保留不改），落实 R199-A1v4 复审 [challenge_A1_v4.md](challenge_A1_v4.md) 的 5 条必改。范围：**修 Stage 0 gate 功能性阻塞、覆盖上界表述、config/代码 gate 对齐、Pancreas reference 披露、审计链更新**；不改方案 A 的分配/覆盖/MDE 实质逻辑。**本轮不运行效果/真实 P0a-metadata/relations_check，不读响应，不声称新颖性。**

## 1. Run gate 修复（功能性阻塞）

### 1.1 旧实现的问题
v4 的 `check_run_gate(cfg, confirm_run)` 在看 `real_run_enabled` 之后**无条件**检查 utility：
`utility_range is None or delta_min_state == blocked_by_utility_definition` → 返回 `STATUS_BLOCKED`（exit 4）。
它**忽略** `utility.utility_gate_required_for_run=false`，因此 Lead 批准 + two-key 后，`--p0a-metadata` 仍在 metadata 分支之前被 blocked——与"P0d blocked 不阻塞 P0a"直接矛盾。

### 1.2 v4.1 语义（写死；`mode` 感知）
`check_run_gate(cfg, confirm_run, mode)`：

| 条件 | mode=`p0a_metadata` | mode=`relations_check` |
|---|---|---|
| 无 `--confirm-run` | refused（exit 3） | refused（exit 3） |
| `real_run_enabled != true` | refused（exit 3） | refused（exit 3） |
| `utility_gate_required_for_run=false`（当前） | 允许 | 允许（不检查 utility） |
| `utility_gate_required_for_run=true` 且 utility/δ_min blocked | **允许**（metadata 只读元数据） | blocked_by_utility_definition（exit 4） |
| utility 已冻结 | 允许 | 允许 |

- `main()` 按 `--p0a-metadata` 选择 mode；默认/仅 confirm → exit 3 保持不变。
- **三前置**（缺一不可）：**Lead 批准记录 + two-key（`--confirm-run` 且 `real_run_enabled=true`）+ A1v4.1 复审通过**。
- **P0a-metadata PASS ≠ relations_check PASS ≠ Stage 1/效果证据**；P0a-metadata 输出 SHA 冻结后才允许 relations_check。
- P0a-metadata 只读 **6 个元数据列**（cell/tissue/anchor/AC/LC/library，**无 endpoint**），`real_data_read=false`。

## 2. 覆盖上界：106 取代 112（写死）

- **v3 的 114/112 不再作为 v4 上界或可达性证明**：其 S 组成是"从 41 leftover 任取 24（可跨 tissue）"，与 v4 固定 **S=Breast12/Colon12** 不同；且"上界 ≥ 目标"本身不证明可达。
- **v4 独立复算**（challenge_A1_v4，与代码一致的确定性字母序分配；A/B-gated）：候选网格 **171**、A/B≥12 supply **135**、S=12/12 下 **最大覆盖 = 106**（≥86，**余量 20**）。
- **门槛 = P0a-metadata 实际输出的 `counts.s_milp_optimum`**（metadata-only 覆盖最大化 MILP/greedy 的实际值），不是 106 这个复算值、更不是 112；106 仅作独立复核/记录。
- 若实际 `s_milp_optimum < 86` → **跑前 `data_unavailable`（stop）**，不降分母、不加回 Pancreas、不改 S 大小、不放宽 n_ctx/α。
- P0a 输出必须含：`s_milp_optimum`、`expected_passing_count`、`s_solver`、`coverage_denominator`、`coverage_target`、`s_splits_sha256`；并把 v3 114/112 标为 provenance 参考（不参与 gate）。

## 3. config gate 清单与代码输出对齐（写死）

`p0a_metadata.gates`（config）与 `run_p0a_metadata` 输出的 `gates` 键**一一对应**：

| gate（全部为布尔，须 true） | 含义 |
|---|---|
| `reference_matched_subset` | reference 84 ⊆ matched 96 |
| `reference_size_ok` | A=42/B=42 |
| `three_way_disjoint` | A/B/S/U 两两不交 |
| `main_tissues_breast_colon` | 主族 = Breast/Colon |
| `pancreas_excluded` | 无 Pancreas 主族候选 |
| `tissue_span_non_vacuity` | 每条主族关系 tissue span=1 且网格非空 |
| `s_side_cond_cov_ge_12` | S 侧 Cond_r 覆盖 ≥12 的关系存在 |
| `precheck_eligible_ge_target` | post-precheck eligible ≥ 86 |
| `s_milp_optimum_ge_target` | 实际 `s_milp_optimum` ≥ 86 |
| `s_selection_solver` | 信息性（`milp`/`greedy`），非 pass/fail |

未实现的旧名（`reference_84_subset_matched96`/`precheck_eligible_ge_86`/`s_milp_expected_passing_count_recorded`）已删除或改为实际字段；P0a 输出不再写 `reference_milp_upper_bound` 作为"已证上界"，改为 `v3_reference_values_not_applicable`（provenance 说明）。

## 4. 披露（写死）

1. **reference 84 含 18 个 Pancreas 参考细胞**：A=17/16/9、B=16/17/9 → Pancreas A9+B9=18。因主族 per-tissue Breast/Colon、主模型无 tissue nuisance，这 18 个细胞**不参与**主族关系/区间/检验，**仅为保持 84/24/17 冻结组成而保留**；报告/输出必须如实披露（`counts.reference_cells_note`）。本版**不改分配**；未来若要增加 S context，需另立 pre-registration。
2. **n–p1 表的可用性**：`n_ctx_min=12` 是硬下限 → **n=11/k=10 与 n=7/k=7 行不可用（仅参考）**；S=12/tissue → n=14/19 行也不可达。**主计划只有 n=12 行可用**；若预期 p1<0.9307 → `insufficient_precision`（不降 n、不放宽 α、不把 n=11 当捷径）。
3. **κ_B 污染方向披露**（v4 复审 minor）：κ_B 在 calibration half B 上估计，而 B 同时用于区间估计；关系违反可能抬高 κ_B → 报告须写污染方向与 κ 带 `[0.5κ,2κ]` 敏感性；主法仍为 κ_B，κ_N/κ_perm 为诊断/敏感性。

## 5. 审计链与冻结（写死）

- 重跑 synthetic selfcheck（**16/16**，新增 `p0a_metadata_gate_mode_allows_when_utility_blocked`：enabled+confirm+`--p0a-metadata`（utility blocked）→ stub 进入 metadata 分支并 PASS；full 模式仍 blocked）。
- 更新 `SELFCHECK.json`、`record_v4_1.md`、`usage_v4_1.json` 的 SHA；SELFCHECK 内脚本/config 哈希与磁盘一致、逐字节可重复。
- **真实 P0a-metadata 输出 SHA 冻结后才允许 relations_check**；在 Lead 正式批准前 `real_data_read=false`。
- 门禁命令（批准后）：`--confirm-run --p0a-metadata`（metadata-only；≤10 min）；PASS 后再 `--confirm-run`（relations_check；≤30 min）。

## 6. 不变项（保留 v4）

方案 A 的 per-tissue Breast/Colon 主族、Pancreas 排除、84/24/17 分配、覆盖 171/86、S MILP/tie-break、non-vacuity、MDE/n–p1/CP、S=12/tissue→insufficient_precision、退出上限 0.15/0.10、k_E/δ_fit/J/κ、P0a 只用 2.0σ、utility 移 P0d、失败类别/短路、措辞模板、A4/A5 接口、不声称新颖性。

## 7. 剩余缺口

1. 真实 P0a-metadata 未运行（106 为独立复算；实际 `s_milp_optimum` 以运行输出为准；<86 → stop）。
2. P0a relations_check / P0b / P0c / P0d 未运行；P0d blocked 只阻止 Stage 1。
3. 18 个 Pancreas reference 细胞不参与主族（披露；不改分配）。
4. n=11/n=7/n=14/n=19 行均不可用（只 n=12 行）；p1<0.9307 → insufficient_precision。
5. 收缩均值仍等权、sign test 无 cluster 校正；P0b/P0c 未实现。
6. 本轮无新先例检索（不联网）。
