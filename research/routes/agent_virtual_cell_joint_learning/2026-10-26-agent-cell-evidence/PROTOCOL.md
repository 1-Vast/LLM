# E001：可观测性与动作资格

冻结先于执行；2026-10-26。元数据普查，不是预测器竞赛。

H001：当前原始药理数据和核验来源足以组成“同剂量药物×背景交叉＋正交靶点/遗传参照＋与查询分离的功能终点＋独立重复身份”的取证任务。若四项不能同时核验，拒绝进入机制性共同学习实验。缺一项不是生物学反证。

输入白名单：PRISM 19Q4 raw 的 primary/secondary treatment、cell-line、secondary pooling metadata、两份原始 readme；前轮合法下载的 BATCHIE PAIR_SCREEN。禁止 sealed、holdout、vault、reserve、confirmation。不加载数值响应列；BATCHIE 仅读药物、细胞、剂量、QC、iteration、file、Plate、Well，不能按活性挑案例。PRISM 仅读设计元数据，不把笛卡尔积当实际观测。保留历史暴露状态。

检查：PRISM 固定 screen、dose，统计候选药物/细胞/检测板层级；redos按readme记technical，不声称生物重复。BATCHIE规范无向药物/剂量，统计实际药物对×细胞与file/plate/well层级、整板动作大小；不合并MG63/MG-63等未核实身份。追踪正交参照/终点的连接键；这些表缺字段不等于外部资源不存在。独立性必须有培养/批次映射支持，不机械要求3文件。

主要结果是资格状态和计数。确定性普查不做收益置信区间。本实验无查询/拟合，模型/采样比较及收益CI为NOT_RUN，不能记零差或成功。资格过关后另冻结同信息强预测器、重训练、层级模型及等反馈随机、GP、决策主动学习比较、任务级封存与主要效用。

停止：独立终点、正交参照或重复映射不可核验，则停止机制性实证，不以更多模块/模拟阳性补足。保留功能问题；元学习/RSI不准入。

命令：`D:/anaconda/envs/maestro/python.exe -B research/2026-10-26-agent-cell-evidence/audit.py`。

验证：记录每输入/协议/脚本SHA256，schema检查，technical-redo事实保留，无响应列进入数据框，重算一致。软件检查不代表科学资格通过。
