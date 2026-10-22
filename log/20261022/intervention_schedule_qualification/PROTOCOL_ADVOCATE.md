# 暴露时序/第二干预公开资产：支持方身份资格

2026-10-22，Asia/Shanghai。登记于新请求之前。只查一个优先原始研究：Lee et al., Cell 2012, DOI10.1016/j.cell.2012.03.031, "Sequential application of anticancer drugs enhances cell death by rewiring apoptotic signaling networks"。目的是认证真实 alternative schedules 与 molecular state+functional outcomes 的公开菜单，不读取原始单样本数值、不拟合、不选药。

最多6次新增 primary HTTP 请求，初始10分钟。优先顺序：欧洲PMC精准原始论文元数据→同篇fullTextXML→全文给定的GEO/正式source metadata→补充资料公开文件菜单（如必要）。不将摘要存在等同数据存在；不下载全表达矩阵、phospho/intensity或apoptosis响应表。

输出必须说明：cell context、drug order/lag/continuous/overlap/dose；molecular assay/time/state；功能终点/time；可配对的identity键或其缺失；是否多个context/多个药序有完整替代动作结局；公开accession/原始URL/source hash；预处理/已公开性能的已曝光边界；作为未来task/RSI源是否足够，哪些未认证。数据论文公开图示的定性菜单可以读取，不把作者结果当独立复现。

没有认证的source或配对菜单时明确NOT_QUALIFIED，不构造不存在干预、不重开PTV/PRISM/O'Neil，也不把有限乳腺癌细胞系写成原代人肝细胞。代码只在 `research/intervention_schedule_qualification_20261022/`，原始来源/结果/失败只在本目录。若覆盖被其他代理取得的同篇来源，优先复用已存在文件而非重复下载。
