# LIST固定源码I/O资格：单独后续阶段

2026-10-22，Asia/Shanghai。原4请求code discovery报告已完成，保持原记录。本阶段在请求前登记，最多2次GitHub固定blob SHA请求、combined完整body≤100,000bytes、无重试/无同SHA再次GET；单writer、请求前拒绝覆盖、失败原始body与receipt立即持久。

只取：

1. `4. Colony Tracking, Combination Index/Colony analysis.m`，14,280bytes，Git blobSHA`f4a48f96172fa803d1506c505dd46dcb2b1499a8`。
2. `4. Colony Tracking, Combination Index/Syngergy Calculation/Calculation.m`，9,694bytes，Git blobSHA`4472a4bf24c001e66980755fb2b07cf9cb5d828f`。

使用GitHub官方固定blob API，校验base64解码后的Git blobSHA与字节数。只阅读，不执行第三方代码，不下载CSV/XLSX/TIF或模型。源码若含嵌入响应数字，明确算作source exposure，不能冒称未见响应，也不将它当新实验、校准阈值或heldout终点。

输出逐项给源码行号：growth/state定义与单位；segmentation/tracking是否用未来帧或整轨迹信息；时间维度及正/反/同步顺序；dose、condition/run/chamber/colony键；I/O文件和列契约；硬编码示例/真实数据与完整矩阵的区别。无法从代码确认就保留未知，不猜schema或读CSV验证。

本阶段只能决定是否有下一项有意义的identity/schema资格，不批准架构。代码脚本只 `research/antibiotic_schedule_qualification_20261022/advocate_code_io*`，来源、解码副本、报告仅本日志目录。
