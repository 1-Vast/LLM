# 清理清单（2026-10-16）

本次只删除可再生内容；研究冻结材料、结果、外部数据和有引用的缓存均保留。

| 类别 | 范围 | 删除前估计 | 理由 |
|---|---|---:|---|
| Python 字节码 | 全仓库 `__pycache__/` | 218 files / 4,130,544 bytes | 解释器自动再生，无实验内容 |
| pytest 缓存 | 全仓库 `.pytest_cache/` | 已包含在上项扫描 | 测试后自动再生，无科学结论 |
| dry-run 缓存 | `research/knowledge_transfer_20261012/cache/dryrun_*` 与 `dryrun_phase1.log` | 约 2.23 MB | 无全文引用、仅模拟运行 |

未删除：`data/external/`、冻结研究文件、`knowledge_transfer/cache` 中被 FREEZE/input_audit/回放引用的数组和模型、`outputs` 中被 `EVIDENCE.md` 引用的历史结果，以及重复但仍可独立回放的测试快照。
