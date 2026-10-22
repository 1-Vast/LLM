# AZ design acquisition/header gate：只读审查

2026-10-22。只读 `AZ_DESIGN_PROTOCOL.md` 与 `az_acquire_headers.py`；未GET、未读ZIP/HEADERS/glossary/目标值、未重跑下载、未改代码。该审查不涉及AZ2024性能，也不把FSI/CCIP的STOP扩张为其它source开发STOP。

**源接触披露和请求边界满足本次静态审查。** 协议明确ZIP含response、下载属于source-response-byte acquisition，不称完全未暴露；代码binding同时记录`source_response_bytes_acquired=True`与`target_numeric_use=False`。下载/哈希触达源字节，之后只投影字段名；这与没有target数值使用是不同命题。

一次invocation由STARTED文件阻止重复；显式GET最多4次（包括逐次记录的redirect），每次socket timeout30s，Requests默认adapter不自动retry，`allow_redirects=False`。成功archive受241088863-byte上限及最终size/MD5约束，错误/redirect body上限8MiB；异常抛出，不在代码中自动重启。两次实际GET若由root报告，只是4次上限内的用量；本审查没有自行认证运行次数/返回内容。响应body/partial文件保留，receipt finally落盘。

ZIP通过大小/MD5后才列表头；不执行成员、不读data rows，tabular member读取最多65537个解压字节并在>65536时停止，JSON只写成员信息/字段名。该阶段没有目标数值转换、缺失target驱动筛选或task split；逐行metadata census被留给下一份列投影协议。代码当前未读取非表格glossary正文；若root有另一个glossary投影，本稿不声称已审该实现。

一个格式检查的小偏差：协议说第一条logical CSV header且遇unexpected format停止，代码实际读第一条physical line，`csv.reader`默认`strict=False`。若header含未闭合引号/跨行字段，它可能接受截断字段名而不是停止；这不等于已发现此pinned源有该问题，也不涉及target数值使用。未来复用时可用strict解析拒绝这类格式，并明确只支持单physical-line header；**不建议为这点重跑已完成下载**。本稿未读表头结果，格式是否触发交数据方按合法字段投影审查。

没有发现需要阻止本次有界获取/表头资格步骤的实质问题。后续具体数据新发现及metadata census按数据审查处理，不由本稿批准新的生物建模或数值response使用。
