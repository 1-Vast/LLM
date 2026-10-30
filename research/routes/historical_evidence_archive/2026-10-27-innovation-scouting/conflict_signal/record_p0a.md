# record_p0a — R199-A1v4.1 批准后 P0a-metadata 运行记录（metadata-only）

2026-10-27。依据 Lead 批准文件 [APPROVAL_P0A.md](APPROVAL_P0A.md)（三前置满足：A1v4 复审 5 条已修 + two-key + Lead 批准）。**只运行 `relations_check.py --confirm-run --p0a-metadata`（metadata-only；不跑 full relations_check、不读任何 endpoint/S/U 响应）。** 判定：**`p0a_metadata_pass`**。

## 1. 批准窗口与 gate 状态

| 项 | 值 |
|---|---|
| 基线 config SHA（运行前，`real_run_enabled=false`） | `BB1FE3230B70EB53B5A39EF7D7D37DF256F296E866133939881E0E3E909CF9B4` |
| 批准窗口 config SHA（仅 `real_run_enabled=true`，其它键未改） | `B60CC8D0E8B567322F831DA3E8D83A11B1042A617B4AC36D95A68A890803D946` |
| 运行后 config SHA（回写 `real_run_enabled=false`） | `BB1FE3230B70EB53B5A39EF7D7D37DF256F296E866133939881E0E3E909CF9B4`（=基线，逐字节还原） |
| 默认（无 flag） | exit 3 `refused`（运行前、回写后各验证一次） |
| 仅 `--confirm-run`（full 模式） | exit 3 `refused`（运行前、回写后各验证一次；full 从未运行） |
| `--confirm-run --p0a-metadata` | 批准窗口内进入 metadata 分支并 PASS；运行后回写 gate 关闭 |

## 2. 执行窗口内发现并修复的 3 个 loader/enumeration 缺陷（须由 Lead 复核）

批准后首次运行暴露实现与真实数据 schema 不一致（均为 metadata/工程问题，**未读 endpoint**）；修复后有效运行才得到与 v4 设计一致的数字。

1. **matched_conditions.csv 列名小写 schema**：A0 交付文件列为 `cell,tissue,anchor_id,library_id,anchor_conc,library_conc,...`，而 loader 用 fitted 表列名（`CELL_LINE_NAME` 等）去取 → `metadata_load_error:matched_conditions_missing_columns`。修复：matched CSV 显式使用小写别名（元数据字段）。
2. **pandas `usecols` 返回文件列序**：`pd.read_csv(usecols=[CELL_LINE_NAME,Tissue,...])` 实际按文件顺序返回（Tissue 在前），位置解包导致 `cell_tissue` 只有 3 个"细胞"（tissue 名）→ 参考分配 0。修复：读入后显式按目标列序重排再位置解包。
3. **候选网格枚举口径**：v4 代码从"全部 Original 条件的 union"枚举 library pair → 首次有效运行网格 30,488（错误放大）；challenge/A0 口径是 **matched_conditions.csv 的逐 cell 键 union**（229 全网格；主族 171）。修复：候选 key 用 `matched_conds`（A0 matched 键、浓度 canonical `.10g`），候选 cells 用全部 Original 元数据（供 S 覆盖），并加浓度 canonical。修复后网格 **171（Breast134+Colon37）**、A/B≥12 supply **135**、`s_milp_optimum=106`、solver **milp** —— 与 challenge_A1_v4 独立复算 106 一致。

> 无效中间尝试的输出（已被覆盖，不冻结、不引用）：`85F1F2BF…`（grid 0）、`5B1B64F6…`（grid 30488）。**最终冻结输出为 `338A234E…`**。上述修复改变了 `relations_check.py` SHA（见 §5）；**判定逻辑/阈值/分配未改**，自检重跑仍 16/16。

## 3. 有效运行结果（冻结）

| 指标 | 值 |
|---|---|
| 命令 | `relations_check.py --confirm-run --p0a-metadata` |
| wall time | **3.0 s**（最终有效运行；预算 600 s，未超时） |
| elapsed_s（脚本内） | 2.8 |
| CPU | 单进程约等于 wall（pandas 读元数据为主；无并行） |
| status | **pass** |
| `s_milp_optimum` | **106** |
| `expected_passing_count` | **106** |
| 候选网格（总/主族） | 171 = Breast 134 + Colon 37（Pancreas 58 已排除） |
| `ab_supply_candidates` | 135 |
| `precheck_eligible` | 106（Breast 79 / Colon 27） |
| `coverage_denominator` / `coverage_target` | **171 / 86** |
| coverage（通过/分母） | 106/171 = 62.0%（≥86 ✓） |
| `s_solver` | **milp**（scipy HiGHS；非贪心） |
| `s_splits_sha256` | `34C4B9D7198CC451822AC8C4A3A553825D917CE0B56D16D9851AAD96BA9783D1` |
| S 组成 | 24 = Breast 12 / Colon 12 / Pancreas 0 |
| reference | A 42（B17/C16/P9）、B 42（B16/C17/P9）；matched 子集 ✓；三向不交 ✓ |
| U | 17 = B6/C0/P11 |
| 18 Pancreas reference 披露 | `counts.reference_cells_note` 已写入："reference 84 includes A9+B9=18 Pancreas cells that are NOT used by the per-tissue Breast/Colon main family..." |
| v3 114/112 | `v3_reference_values_not_applicable`（仅 provenance，不作 gate） |

**10 个 gate 逐项**（最终输出 `p0a_metadata.json`）：
`reference_matched_subset=true`、`reference_size_ok=true`、`three_way_disjoint=true`、`main_tissues_breast_colon=true`、`pancreas_excluded=true`、`tissue_span_non_vacuity=true`、`s_side_cond_cov_ge_12=true`、`precheck_eligible_ge_target=true`、`s_milp_optimum_ge_target=true`、`s_selection_solver="milp"`（信息性）。**9 个布尔 gate 全 PASS + `s_milp_optimum=106≥86` → `p0a_metadata_pass`。**

## 4. 冻结输出

- 文件：`stage0/real_run/p0a_metadata.json`
- SHA256：**`338A234E931E11C27105952839BC69F9681D4D8516419B4B78D2F81C36F58247`**
- sidecar：`stage0/real_run/p0a_metadata.json.sha256`（与文件哈希一致，已核）
- 内容：schema `r198-a1-stage0-p0a-metadata-v4`、status `pass`、gates 10 项、counts（含 `s_milp_optimum/expected_passing_count/s_solver/s_splits_sha256/coverage_denominator/target/reference_cells_note/v3_reference_values_not_applicable`）、allocation splits（A/B/S/U 计数与 SHA，无细胞名）、notes（P0a PASS ≠ relations_check PASS ≠ Stage1/效果；metadata-only；18 Pancreas 披露）。
- **未生成** `relations.csv`/`relations_check.json`（full 未运行）。

## 5. 冻结后的文件 SHA（最终状态）

| 文件 | SHA256 |
|---|---|
| `stage0/relations_check.py`（含 3 个执行期 loader/枚举修复） | `88ACAFD2E5A75865E8A9771006D7DFF58F38F1638BDB9677A93A0D83F76E06C0` |
| `stage0/relations_check_config.json`（回写后） | `BB1FE3230B70EB53B5A39EF7D7D37DF256F296E866133939881E0E3E909CF9B4` |
| `stage0/synthetic_selfcheck.py`（API 适配后） | `0A0455EDA438B51A9A0A0AD0AEAA74BE55D0BE28B7149E5FE0A14757E11242F8` |
| `stage0/SELFCHECK.json`（16/16，回写后重跑） | `8836AD8A088819A00FBA6F1DB1FAB902F85F7363A8AE1FD0271259E77023AFFE` |
| `stage0/README.md` | `A6954E43DAA44A6F59094932F6D258D71B4CED5466D0E97F613BEBC840E2E97E` |
| `stage0/real_run/p0a_metadata.json` | `338A234E931E11C27105952839BC69F9681D4D8516419B4B78D2F81C36F58247` |
| `record_p0a.md` / `usage_p0a.json` | 自引用（外部复算） |

## 6. 判定与解释边界

- **判定 = `p0a_metadata_pass`**：`s_milp_optimum=106 ≥ 86` 且 9 个布尔 gate 全 PASS。`s_selection_solver=milp` 为信息字段，不是 pass/fail gate。
- **该 PASS 只说明 metadata-only 前置（分配/网格/S 侧覆盖/non-vacuity/eligible≥86）达标**；**不是**关系成立、不是 relations_check PASS、不是 Stage 1、不是效果/迁移/决策证据。
- S=24 按 tissue 12/12 → 主族关系最多 12 个 S context；n=14/19 行不可用；若预期 p1<0.9307 → insufficient_precision（不降 n/不放宽 α）。
- 18 个 Pancreas reference 细胞不参与主族（披露，不改分配）；Pancreas 不声称、不外推。
- P0d（δ_min/效用）仍 `blocked_by_utility_definition`，只阻止 Stage 1。

## 7. 下一步（等 Lead 复核）

1. Lead 复核本记录 + 冻结输出 SHA + 执行期 3 个 loader/枚举修复（建议确认修复不改变设计逻辑；自检 16/16）。
2. 若同意，再批准 **P0a relations_check**（参考响应可读、≤30 min）；其前不得运行 full。
3. 不降分母/不加回 Pancreas/不改 S 大小/不放宽 α；P0a-metadata 输出 SHA 已冻结。

## 8. 局限

- 有效运行只**一次**（修复后）；运行前失败尝试已记录（§2），未用于任何判定。
- CPU 未单独采样（单进程、wall≈CPU；pandas 元数据读取为主）。
- 未运行 relations_check/P0b/P0c/P0d；未读 endpoint；无新先例检索；不声称新颖性。
