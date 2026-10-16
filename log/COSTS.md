# 成本与资产边界

- 研究根目录的 protocol、freeze、results、claims、deviations、artifacts、审计日志和验证脚本属于证据，保留。
- `data/external/`（约 61 GB）是原始外部数据/模型，不是临时缓存；保留。
- `research/knowledge_transfer_20261012/cache/` 的大型数组/模型仍被 freeze、input audit 或回放引用，不能整体删除。
- dry-run 缓存和 pytest 临时输出可再生；清理前记录路径、大小、哈希和引用检查。
- 研究记录中明确的 provider calls、下载状态和未运行状态必须保留；没有实际调用不能写成成功实验。
