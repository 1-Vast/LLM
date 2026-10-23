# S4代码响应前修订复核

2026-10-22；不修改原CODE_REVIEW的REVISE记录。实际重读新版run.py/test_run.py，未开S4或prepared值。

源target现按各condition训练positions分别构建midrank，之后同组截距/残差，已修复原全challenge排序阻断。新合成测试包含常数源标签严格tie、evaluate的JSON序列化及跨condition独立严格单调变换不变；这些恰好覆盖原bug风险。原held-pair标签隔离和End NaN不变测试保持有意义。此处为静态审阅，不冒称独立运行测试。

**PASS当前冻结准备。** 支持root在合成检查完成并绑定最终代码/协议后执行一次限定S4功能探索。truth exact ties预先排除并计数合法，固定lambda1主/.1与10敏感不得选择；source<2时跳过pair仍应报告不可估原因或以合法缺失元数据证明不可达，不将缺失当成功。

所有结论仍为极小样本普通prefix信息探索，不构成组成STOP救回、新算法、世界模型/agent或RSI证据。
