# P0a relations_check 运行批准（Lead，2026-10-27）

依据：P0a-metadata `p0a_metadata_pass`（输出 SHA `338A234E931E11C27105952839BC69F9681D4D8516419B4B78D2F81C36F58247`；s_milp_optimum=106≥86；9 布尔门 PASS）；执行期 3 个 loader/枚举缺陷已由 Lead 接受为 implementation correction（逻辑/阈值/分配未改；selfcheck 16/16；relations_check.py SHA `88ACAFD2…`）。

## 三前置
1. P0a-metadata PASS 且输出 SHA 冻结。
2. two-key：`--confirm-run` + config 临时 `real_run_enabled=true`（运行后立即回写 false，SHA 逐字节还原；default/仅 confirm 必须 exit 3）。
3. Lead 批准（本文件）。

## 范围与冻结
- 只运行 `relations_check.py --confirm-run`（P0a relations_check；参考响应可读、≤30 min）；**不运行 P0b/P0c/P0d，不进 Stage 1**。
- 读入：A0 matched_conditions 元数据 + reference A/B 84 细胞端点为区间/方向估计；S/U 响应不进内存（按设计两 pass）。
- 输出：`stage0/real_run/relations_check.json`、`relations.csv`、`relation_splits.json`、record/usage；全部 SHA 冻结并交 Lead 复核。
- 判定：按 A1v4.1 冻结协议（R∈[20,200]、n_ctx≥12、α=0.01、BH q≤0.10、覆盖/is_global 规则、失败类别 `data_unavailable`/`design_invalid`/`blocked_by_utility_definition`）；**不降分母、不加回 Pancreas、不改 S 大小、不放宽 α**。
- **relations_check 通过 ≠ 关系成立 ≠ Stage 1 ≠ 效果/迁移/决策收益**；P0b 需另议、P0d 仍 blocked。
