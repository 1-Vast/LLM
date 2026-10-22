# 支持方 post-result 操作与失败记录

2026-10-22。本阶段授权为已解封结果的只读审查，之后明确追加 `FIT_RUNS.jsonl` 的 phase/arm/config/timing 字段。未读取 ZIP、reserve 数值、模型或新增 raw test targets；未拟合、改变方法或选择。

1. 读取 `MEASURED_PROTOCOL.md` 的预定门/停止条件，以及已授权结果与化学 `QUALIFICATION.md`。
2. 首次临时 Python schema 摘要错误假定 `TEST_METRICS.json` 为 endpoint→policy 嵌套；实际为 `policy__endpoint` 扁平映射，发生 `AttributeError: 'float' object has no attribute 'get'`，命令 exit1。它只读已授权结果，未写或改变实验数据；之后按真实 schema 摘要。没有将该读取脚本异常当成实验失败/重跑理由。
3. 一次临时摘要直接打印了完整 plateau dict，输出被工具截断。随后改用聚合摘要读取549 episodes/37367 correlated point-pairs。此为输出过量，不是缺失数据或模型失败，未据截断挑选结果。
4. 新增 `research/az_paid_reference_gate_20261022/post_result_evidence.py`：只读结果、独立算两主差值与注册门逻辑，保留全部22策略核心分数、六局部比较、coverage、支持域、plateau聚合、计时和输入SHA。执行 exit0，见当前 phase 的 `ADVOCATE_POST_RESULT_EVIDENCE_RUN.txt`；`POST_RESULT_EVIDENCE.json`确认所有输入前后hash相同。没有复算原始test labels；完整数值auditor由另一代理独立完成，来源身份区分于本审查。
5. 与 skeptic/data 真实双向交叉，明确保留局部正向、mono两CI跨零、质量/速度不可换门、精准STOP、非普遍不可能性及化学未解非leak。实际问答保存在 `POST_RESULT_REVIEW.md`，不把设想问题当已发生对话。
6. 根汇总指出 effect MAE config6、effect_offset MAE config7/eta=.25，所以 .000857 改善是整个 offset family 选择比较，非固定 base 的纯校准贡献；已据此明确修订 post 解释，没有改动任何实验结果。

当前决定：主门双失败，精确 STOP；本阶段无新实验。所有代码和当前阶段新增日志均在指定 research/log 目录，没有更改先前冻结文件或文献独立稿。
