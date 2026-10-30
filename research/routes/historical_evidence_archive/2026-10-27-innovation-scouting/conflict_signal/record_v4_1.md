# record_v4_1 — R199-A1v4.1 补丁过程记录（gate 修复 + 106 + 审计对齐）

2026-10-27。角色：R198-A1 提案者，按 R199-A1v4 复审 [challenge_A1_v4.md](challenge_A1_v4.md)（revise，≤5 必改）修 **run gate 功能性阻塞**、覆盖上界表述、config/代码 gate 对齐、Pancreas reference 披露与审计链。**本轮不运行效果/真实 P0a-metadata/relations_check；不读 S/U 或参考响应；不改 v1–v4 文件；不声称新颖性。**

## 1. 范围与输入

- 输入（只读）：[challenge_A1_v4.md](challenge_A1_v4.md)、[spec_v4.md](spec_v4.md)、[protocol_draft_v4.md](protocol_draft_v4.md)、[REVISION_A1_v4.md](REVISION_A1_v4.md)、`stage0/` v4 实现、R198 record、SYNTHESIS C 边界。
- 只写：`conflict_signal/` 下新增 v4.1 文件（`spec_v4_1.md`、`REVISION_A1_v4_1.md`、`record_v4_1.md`、`usage_v4_1.json`）+ **更新 `stage0/` 4 件**（`relations_check.py`、`relations_check_config.json`、`synthetic_selfcheck.py`、`SELFCHECK.json`、`README.md`）；`tmp/stage0_selfcheck_runs` 为合成测试输出。未改 v1–v4、其它目录、INDEX/SYNTHESIS/git；未联网。
- 不做：运行效果/训练/真实 P0a-metadata/真实 relations_check/体检/MDE 预检；不读响应值；不编造 δ_min。

## 2. 5 条必改落实

1. **run gate（功能性阻塞）**：`check_run_gate(cfg, confirm_run, mode)` 改为模式感知——`--p0a-metadata` 只需 two-key（`--confirm-run` + `real_run_enabled=true`），utility/P0d blocked **不阻塞**；full relations_check 仅在 `utility_gate_required_for_run=true` 时要求 utility；默认/仅 confirm → exit 3。`main()` 按 `--p0a-metadata` 传 mode；新增 selfcheck 用例（enabled+confirm+`--p0a-metadata`，utility blocked，stub loader）验证**进入 metadata 分支并 PASS**、full 模式仍 blocked。
2. **覆盖上界**：删除/标 provenance v3 的 114/112（不同 S 组成、非 v4 上界/可达性证明）；config 改 `v4_recompute_max_covered_not_a_gate={106,...}`；**门槛=P0a-metadata 实际 `counts.s_milp_optimum`**；<86 → 跑前 `data_unavailable`。v4 独立复算 max=106（≥86，余量 20）。
3. **config/代码 gate 对齐**：config `p0a_metadata.gates` 改为代码实际 10 个 key（含 `s_milp_optimum_ge_target`）；P0a 输出新增 `s_milp_optimum/expected_passing_count/s_solver/s_splits_sha256/coverage_denominator/coverage_target/reference_cells_note/v3_reference_values_not_applicable`；删除未实现旧名与 `reference_milp_upper_bound`。
4. **披露**：reference 84 含 A9+B9=18 Pancreas 参考细胞，因主族 per-tissue Breast/Colon（无 tissue nuisance）**不参与主族关系/区间/检验**，仅为保持 84/24/17 组成；不改分配。n–p1 表 n=11/n=7（n<n_ctx_min=12）与 n=14/19（S=12/tissue）均标 `usable:false`，主计划只 n=12 行可用。
5. **审计链**：selfcheck 16/16（新增 gate-mode 用例），逐字节可重复；SELFCHECK 内脚本/config 哈希与磁盘一致；冻结 stage0 4 件与 v4.1 文档 SHA；record 写清三前置 + P0a 输出 SHA 冻结后才跑 relations_check + P0a PASS≠relations_check PASS≠Stage1/效果 + loader 只读 6 元数据列（无 endpoint）、`real_data_read=false`。

## 3. 决定与理由

1. **gate 用 mode 参数而不是改 config 语义**：P0d 的 blocked 只应阻止 Stage 1/效果轮与 full 检查（当 flag=true），不应阻止 metadata-only 预检；mode 最小改动且保持 two-key 强度。
2. **106 只作独立复核、不作 gate**：v4 复审的 106 与代码一致的确定性分配吻合，但实际 S 覆盖取决于真实 metadata；门槛必须是运行输出的 `s_milp_optimum`，避免再次误读上界。
3. **gate 清单以代码输出为准**：config 只声明审计期望；P0a 输出直接带 10 个 key + 数值，审计可逐项复核。
4. **18 个 Pancreas reference 细胞不改分配**：Lead 方案 A 已冻结 84/24/17；改配会触发新协议/重审，本轮只如实披露。
5. **不声称新颖性**：v4.1 仅修工程门控/审计链。

## 4. Stage 0 更新（文件级）

- `relations_check.py`：`check_run_gate` 模式感知；`select_s_cells`/`run_p0a_metadata` 输出 `s_milp_optimum` 等；`s_milp_optimum_ge_target` gate；`_json_safe` 保证输出确定性 JSON；`write_p0a_outputs` 增加 notes（P0a≠relations_check≠Stage1、106/112 非 gate、18 Pancreas 披露、metadata-only）。
- `relations_check_config.json`：schema v4.1、design_documents 加 spec_v4_1/challenge_A1_v4、run_gate.mode_aware、known_metadata_facts 106 provenance/reference_note、coverage v3→v4 provenance、MDE n–p1 `usable` 标注、p0a_metadata.gates 10 键 + execution_preconditions/post_conditions。
- `synthetic_selfcheck.py`：新增 gate-mode 用例；schema/warning/notes 更新为 v4.1；共 16 项测试。
- `SELFCHECK.json`：16/16 pass、deterministic；synthetic（覆盖目标缩放 56→28 已披露）；`real_data_read=false`、`network=false`。
- `README.md`：v4.1 说明（gate 模式/106/18 Pancreas/16 测试/三前置/P0a≠Stage1）。

## 5. 产物与冻结 SHA256

| 文件 | SHA256 |
|---|---|
| `spec_v4_1.md` | `2ABDE0F06EDCDF58A4B78106802EE50CE3F423145ACC78320BDFF2902B6C3DBC` |
| `REVISION_A1_v4_1.md` | `CC83F914745EC135D044D5308E77B4FD9F0299D0FF69AB865C2025E593BEF272` |
| `stage0/relations_check.py` | `90CC80BB5DAD84EB62C283B55FAFEAD40FA2FEB6E6EF545DCF4B7704D44DF447` |
| `stage0/relations_check_config.json` | `BB1FE3230B70EB53B5A39EF7D7D37DF256F296E866133939881E0E3E909CF9B4` |
| `stage0/synthetic_selfcheck.py` | `5DC94B3AC733D7006F6F149AE2704D5AF7B6B94C7386F095F74A2E5BABAFC64F` |
| `stage0/SELFCHECK.json` | `1A8EF75B01EADA1AA9C0C8EE4D1BB28774CE0F97DF46EAA122BA3B7D48E6EEB0` |
| `stage0/README.md` | `A6954E43DAA44A6F59094932F6D258D71B4CED5466D0E97F613BEBC840E2E97E` |
| `record_v4_1.md` / `usage_v4_1.json` | 自引用（外部复算） |

v4 文件未改（复核：spec_v4 `633E1D68…16AB`、protocol_v4 `F0B2830A…3F57`、REVISION_v4 `B8B727A8…E866`）；v1–v3 未改（spec_v3 `DE92C65E…`、protocol_v3 `3FC57D72…`、REVISION_v3 `79789420…`、record_v3 `889E89E8…`、usage_v3 `85887F53…`）。

## 6. 批准前置与语义（写死）

- **三前置（缺一不可）**：① Lead 批准记录；② two-key（`--confirm-run` 且 `real_run_enabled=true`）；③ A1v4.1 复审通过（本文件对应 challenge_A1_v4 修复；Lead 确认后无需第三次全量复审）。
- 批准后：先跑 `--confirm-run --p0a-metadata`（metadata-only，≤10 min，不读 endpoint，`real_data_read=false`）；**P0a-metadata 输出 SHA 冻结后才允许 relations_check**（参考响应可读，≤30 min）。
- **P0a-metadata PASS ≠ relations_check PASS ≠ Stage 1 / 效果证据**；P0d（δ_min/效用）仍 `blocked_by_utility_definition`，只阻止 Stage 1。
- 若 P0a-metadata 实际 `s_milp_optimum < 86` → 跑前 `data_unavailable`（stop）；不降分母、不加回 Pancreas、不改 S 大小、不放宽 n_ctx/α。

## 7. 局限与剩余缺口

- **真实 P0a-metadata 未运行**：171 网格/真实 S 覆盖/actual `s_milp_optimum`（v4 复算 106）/non-vacuity 均待实测。
- P0a relations_check/P0b/P0c/P0d 未运行；P0d blocked。
- 18 个 Pancreas reference 细胞不参与主族（披露；不改分配）。
- 主计划只 n=12 行可用；p1<0.9307 → insufficient_precision。
- 收缩均值仍等权、sign test 无 cluster 校正；P0b/P0c 未实现；真实 loader 未在真实数据演练；MILP 依赖 scipy（兜底贪心）。
- 本轮无任何生物/关系/效果结论；无新先例检索。
