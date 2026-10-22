# Open TG-GATEs 身份与跨 lot 任务资格

2026-10-22，Asia/Shanghai。本协议在任何本区块新网络获取前登记。动机是 OASIS 固定双 endpoint 技术排名资格失败后，寻找具备实际跨背景反馈单元的新来源，不修改 OASIS 失败或停止条件。

允许来源：官方 Open TG-GATEs archive README、原始论文 PMC4384023 的方法/metadata，以及经说明确认为身份资料的细胞/sample/CEL attributes/补充表。新响应 body 总量 **<=2,000,000 bytes**，一个顺序网络写入者；每次请求先流式限额，不自动下载目录全部资产。<=20 分钟初始元数据区块。代码仅 `research/tggates_source_qualification_20261022/`，所有新来源/收据/结论/失败仅本目录。不得下载或读取 CEL、DNA/LDH 数值表、单样本表达、任意模型参数；无需 GPU、拟合或模型 API。

开始先检查旧仓库是否已使用该来源，已有文献/下载/数值曝光不能因新目录而重置。新检查必须具体回答：

1. 人原代肝细胞身份是否存在 compound-dose-time × source/culture/lot 的可追溯重复配对，而非三个重复或不同药被分在六 lot；标识是否稳定，关联能否从官方 metadata 建立。
2. 每个 lot 的人源来源/培养过程/重复含义；不能把 six lots 自动当 six donors，也不能把时间点当不同生物背景。
3. 2/8/24h、剂量与 DNA/LDH 是否同条件/同样本或独立参考；不读 endpoint 数字。高剂量是否由先前 viability 选择，是否存在按效应大小/不完整覆盖的筛选。
4. 可用反馈究竟是同条件原始观测、多模态同时读出，还是可作为后续时间预测/跨 lot 校正的真实后继观测。仅有不同 assay 名称或公开大样本不通过。

本区块通过仅表示有继续建立任务合同的来源资格，不表示世界模型/智能体/继承/RSI成立。若没有相同 compound-dose-time 的跨真实背景配对或必要键无法认证，记录 NOT_QUALIFIED/IDENTITY_BLOCKED及具体缺口，不重定义RSI，也不因查看元数据而擅自开放数值或放宽资源上限。公开论文 aggregate 方法可读，不作个体结局优化。
