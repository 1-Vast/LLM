# REVISION_A1_v4_1 — 对 challenge_A1_v4.md 的逐条回应（gate 修复补丁）

2026-10-27。对象：R199-A1v4 复审 [challenge_A1_v4.md](challenge_A1_v4.md)（revise，≤5 必改）。本文件逐条说明 v4.1 补丁落在何处（[spec_v4_1.md](spec_v4_1.md) + `stage0/`）；v1–v4 文件保留不改。**本轮不运行效果/真实 P0a-metadata/relations_check，不读响应，不声称新颖性。**

## 0. 5 条必改处置

| # | must-fix | v4.1 处置 | 状态 |
|---|---|---|---|
| 1 | **run gate 功能性阻塞**：`check_run_gate` 忽略 `utility_gate_required_for_run=false`，`--p0a-metadata` 在 metadata 分支前被 blocked（exit 4） | **模式感知 gate**：`check_run_gate(cfg, confirm_run, mode)`；`--p0a-metadata` 只需 two-key（confirm + real_run_enabled），utility/P0d blocked 不阻塞；full relations_check 仅在 `utility_gate_required_for_run=true` 时要求 utility；默认/仅 confirm → exit 3。新增 selfcheck 用例 `p0a_metadata_gate_mode_allows_when_utility_blocked`（stub loader，进入 metadata 分支并 PASS；full 仍 blocked） | 已修 |
| 2 | **112 上界误读**：v3 的 114/112 不是 v4 上界/可达性证明 | 删除/标 provenance：v3 114/112 不再作门槛；**v4 独立复算 max=106（≥86，余量 20）** 仅作复核记录；**门槛 = P0a-metadata 实际 `counts.s_milp_optimum`**；<86 → 跑前 `data_unavailable` | 已修 |
| 3 | **config gate 清单与代码输出不一致** | config `p0a_metadata.gates` 改为代码实际 10 个 key（含 `s_milp_optimum_ge_target`）；P0a 输出新增 `s_milp_optimum`/`expected_passing_count`/`s_solver`/`s_splits_sha256`/`coverage_denominator`/`coverage_target`；删除未实现旧名；`reference_milp_upper_bound` 改为 provenance 说明 | 已修 |
| 4 | **18 个 Pancreas reference 细胞未被主族使用未披露**；n=11 行不可用 | spec_v4_1 §4、config `known_metadata_facts.reference_note`、P0a `counts.reference_cells_note` 披露：reference 84 含 A9+B9=18 Pancreas 细胞，主族 per-tissue Breast/Colon 无 tissue nuisance → 不参与关系/区间/检验，仅为保持 84/24/17 组成；**不改分配**。n–p1 表标 `usable:false`：n=11/n=7（n<12）+ n=14/19（S=12/tissue 不可达），只 n=12 行可用 | 已修 |
| 5 | **审计链/批准前置/SHA 更新** | 重跑 selfcheck **16/16**（含新 gate-mode 用例）；冻结并登记 stage0 脚本/config/SELFCHECK/README SHA 与 v4.1 文档 SHA；在 record_v4_1 写清三前置（Lead 批准 + two-key + A1v4.1 复审通过）、P0a-metadata 输出 SHA 冻结后才跑 relations_check、P0a-metadata PASS ≠ relations_check PASS ≠ Stage 1/效果、loader 只读 6 元数据列（无 endpoint）且 `real_data_read=false` | 已修 |

## 1. 逐项证据

### ① gate（功能性阻塞，最高优先）
- 代码：`stage0/relations_check.py::check_run_gate(cfg, confirm_run, mode="relations_check")`：
  - 两模式都要求 `--confirm-run` 且 `real_run_enabled=true`；
  - `mode="p0a_metadata"`：跳过 utility 检查（P0d blocked 不阻塞 metadata-only）；
  - `mode="relations_check"`：仅 `utility.utility_gate_required_for_run=true` 时检查 utility；当前 config=false，因此 P0d 前允许跑。
  - `main()` 按 `--p0a-metadata` 传 mode。
- 行为表（spec_v4_1 §1.2）：默认/仅 confirm → exit 3；enabled+confirm+`--p0a-metadata`（utility blocked）→ 进入 metadata 分支；enabled+confirm+full relations_check（flag=true 且 utility blocked）→ exit 4；flag=false → 允许。
- selfcheck 新用例：临时 config（`real_run_enabled=true`、`utility_range=None`、`delta_min_state=blocked_by_utility_definition`、`utility_gate_required_for_run=true`）+ `unittest.mock.patch` 替换真实 loader（**不读真实数据**）→ `main(["--confirm-run","--p0a-metadata",...])` 返回 0、输出 `p0a_metadata.json`、status=pass、`s_milp_optimum=56`（synthetic 缩放）；同时断言 full mode 返回 `blocked_by_utility_definition`。

### ② 覆盖上界 106
- v3 的 114/112 来自不同 S 组成（41 leftover 任取 24、可跨 tissue），且上界不证明可达 → 不再引用为"已证上界"；config 中删除 `reference_milp_upper_bound_after_S_precheck`，改 `v4_recompute_max_covered_not_a_gate`（value=106 + provenance + v3 values not applicable）。
- v4 独立复算（challenge_A1_v4）：网格 171、A/B≥12 supply 135、S=12/12 下 max=106（Breast 91 + Colon 25 近似组合；精确 MILP 106）→ ≥86，余量 20。
- **门槛**：P0a-metadata 实际 `s_milp_optimum`（metadata-only MILP/greedy 输出）；若 <86 → `data_unavailable`（stop）。106 仅记录，不作 gate。

### ③ config/代码 gate 对齐
- config `p0a_metadata.gates`（10 个）：`reference_matched_subset`、`reference_size_ok`、`three_way_disjoint`、`main_tissues_breast_colon`、`pancreas_excluded`、`tissue_span_non_vacuity`、`s_side_cond_cov_ge_12`、`precheck_eligible_ge_target`、`s_milp_optimum_ge_target`、`s_selection_solver`（最后一项信息性）。
- P0a 输出新增：`counts.s_milp_optimum`、`counts.expected_passing_count`、`counts.s_solver`、`counts.s_splits_sha256`、`counts.coverage_denominator`、`counts.coverage_target`、`counts.reference_cells_note`、`counts.v3_reference_values_not_applicable`；`write_p0a_outputs` 增加 notes（P0a PASS ≠ relations_check PASS ≠ Stage 1；106/112 不是 gate；18 Pancreas 披露；metadata-only）。
- 删除未实现旧 gate 名；`run_p0a_metadata` 增加 `s_milp_optimum_ge_target` 布尔门。

### ④ 披露
- reference 组成：A(Breast17/Colon16/Pancreas9)、B(Breast16/Colon17/Pancreas9) → 18 个 Pancreas 参考细胞；主族 per-tissue Breast/Colon + 无 tissue nuisance → 不参与主族。spec_v4_1 §4、config `reference_note`、P0a `reference_cells_note` 三处披露；**不改分配**。
- n–p1 表：n=11/k=10 与 n=7/k=7 行 `usable:false`（n<n_ctx_min=12）；n=14/19 `usable:false`（S=12/tissue 不可达）；只 n=12 行可用；p1<0.9307 → `insufficient_precision`（不降 n、不放宽 α、不用 n=11 捷径）。

### ⑤ 审计链/前置/SHA
- selfcheck 16/16（新增 gate-mode 用例）；SELFCHECK 逐字节可重复；`SELFCHECK.json` 内记录脚本/config SHA 与磁盘一致。
- record_v4_1 §5 冻结 SHA；三前置 + P0a 输出 SHA 冻结后跑 relations_check + `real_data_read=false` 写清。
- `load_metadata_inputs` 只读 6 个元数据列（无 endpoint）——复审 PASS 项保留。

## 2. 保留项（v4 实质进步，未动）

方案 A 分配/排除/覆盖算术（84/24/17、reference⊆matched96、171/86、S12/12、U17、171 网格、R_min=20）；τ_t 删除；per-tissue 主族与 Pancreas 排除/披露；MDE p1≈0.930743/power 0.7998、n–p1 表、CP 精确规则、S=12/tissue→insufficient_precision、退出上限固定 0.15/0.10、k_E、δ_fit=2.5、J 代价、κ 主法（κ_B，加污染方向披露）、P0a 只用 2.0σ、utility 移 P0d、P0a–P0d 清单/短路、失败类别、措辞模板、A4/A5 接口、不声称新颖性。

## 3. 仍存缺口

1. 真实 P0a-metadata 未运行：106 为独立复算，实际 `s_milp_optimum` 以运行输出为准（<86 → stop）。
2. P0a relations_check / P0b / P0c / P0d 未运行；P0d blocked 只阻止 Stage 1。
3. 18 个 Pancreas reference 细胞不参与主族（披露；不改分配）。
4. 主计划只 n=12 行可用；p1<0.9307 → insufficient_precision。
5. 收缩均值仍等权、sign test 无 cluster 校正；P0b/P0c 未实现。
6. 本轮无新先例检索（不联网）。

## 4. 批准建议（给 Lead）

修完 5 条后：可批准 **P0a-metadata**（metadata-only；不读响应）。批准记录需写：**Lead 批准 + two-key（`--confirm-run` 且 `real_run_enabled=true`）+ A1v4.1 复审通过**。批准后建议先只跑合成 selfcheck 复核（不读真实数据），再跑真实 `--p0a-metadata`；其输出 SHA 冻结后才允许 relations_check。**P0a-metadata PASS 不等于关系成立、不等于 Stage 1、不是效果证据。**
