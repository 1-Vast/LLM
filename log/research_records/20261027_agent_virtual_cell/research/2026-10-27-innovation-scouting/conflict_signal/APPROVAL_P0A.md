# P0a-metadata 运行批准（Lead，2026-10-27）

依据：A1v4.1 补丁完成（task-56；selfcheck 16/16、逐字节可重复、SHA 冻结）；A1v4 复审（challenge_A1_v4）5 条必改已落实，复审意见为"修完无需第三次全量复审，Lead 确认即可批准"。**Lead 批准运行 P0a-metadata**（仅元数据、不读响应）。

## 三前置（全部满足）
1. 独立复审通过：challenge_A1_v4 判 revise，5 条必改已修（gate 模式、106 上界、config/代码 gate 对齐、18 Pancreas 参考披露、审计链/三前置）。
2. two-key gate：`--confirm-run` + config `real_run_enabled=true`；默认/仅 confirm 仍必须 exit 3。
3. Lead 批准：本文件；批准后只跑 `--p0a-metadata`，**不跑 full relations_check**。

## 运行范围与冻结要求
- 命令：`relations_check.py --confirm-run --p0a-metadata`（metadata-only；loader 只读 6 个元数据列、无 endpoint；`real_data_read` 只允许在 P0a 元数据路径为 true）。
- 输出：`stage0/real_run/p0a_metadata.json`（+record）；必须含 `s_milp_optimum`、`expected_passing_count`、`s_solver`、`s_splits_sha256`、`coverage_denominator`/`coverage_target`、10 个 gate、`reference_cells_note`（18 Pancreas 参考披露）、`v3_reference_values_not_applicable`。
- **判定**：`s_milp_optimum ≥ 86` 且其余 9 gate 全 PASS → `p0a_metadata_pass`；否则 `data_unavailable`（stop，不降分母/不加回 Pancreas/不改 S 大小/不放宽 α）。
- 输出 SHA 冻结后才允许（经 Lead 复核）进入 relations_check（参考响应可读、≤30 min）。
- **P0a-metadata PASS ≠ 关系成立 ≠ relations_check PASS ≠ Stage 1 ≠ 效果/迁移/决策证据**。
- 运行时预算 ≤10 min；若超时 → design_invalid（记录）。
