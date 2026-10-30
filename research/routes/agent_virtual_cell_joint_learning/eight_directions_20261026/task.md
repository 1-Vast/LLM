# 继续入口

本轮八方向最小尝试已结束，最终为v2。读report.md，再看independent_review_20261026/review.md；根目录数值为最终探索性读数，asrun_v0和asrun_v1均作废且保留。

复跑：在D:/MAESTRO，`.venv/Scripts/python.exe -B research/eight_directions_20261026/run.py`；检查用同目录verify.py；方向4/5用evidence_audit/run_audit.py。

绝不把历史derived primary当原始2.5μM响应：v1原始对齐失败。最终run.py只从raw指定column_name读取Y，npz仅用于开放身份白名单。不读取任何旧sealed/confirmation响应，不覆盖既有研究，不修改最终评价器以制造进步。

方向1需要正交机制参照和同复杂度规则/层级模型对照；方向5需要核实plate/file/well的独立重复身份、曝光时间与容差，当前没有TOST结果或可运行TOST实现。方向7仅内部经验风险排序，需活性匹配与独立screen确认。方向6/8不能以本次策略选择冒充完整元学习或RSI。

不必继续搜索架构；优先获取能真正改变上述证据门槛的新信息。环境只需现有CPU numpy/pandas/scipy/sklearn/h5py，无外部模型桥。
