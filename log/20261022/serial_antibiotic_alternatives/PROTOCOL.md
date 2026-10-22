# 独立替代来源scout：固定一次PubMed查询

2026-10-22，Asia/Shanghai。初始上限3个HTTP请求、HTTP body总量≤1MB、15min；先登记再执行。只查真实细菌抗生素temporal exposure/evolution/perturbation，关注morbidostat/eVOLVER/collateral sensitivity与实际state/genome/phenotype、growth/function及可执行菜单。结果最多报告2个精确primary leads。日期截止2026-10-22。

不重复根代理Jeong/Tay3D来源，不重开PTV/PRISM/O'Neil。EuropePMCsearch已有503，不复用其搜索。固定PubMed query见脚本：antibiotic+bacteria AND morbidostat/eVOLVER/collateral-sensitivity AND temporal/sequential/cycling/time-resolved/drug-switching。第1请求esearch取得最多12 PubMed IDs，第2请求efetch原始metadata/abstract。若有第3请求，只对其中1项原始公开方法/身份入口作直取，不能换查询扫查。

只允许文献方法和public accession/schema/identity metadata，不下载数值growth/MIC/expression/sequence矩阵，不作模型或架构。摘要中reported performance仅算先验，不作独立验证。真正可晋级须认证drug/action/dose/time、环境/strain/run/lineage身份、决策前state、功能终点和共享prefix/选择菜单；全量菜单不可得保持NOT_AUTHENTICATED。

脚本在research/serial_antibiotic_alternatives_20261022，raw来源、错误body、request URL/status/bytes/hash及报告在本目录。文件拒绝覆盖，错误也计入请求和字节预算；没有取得errorbody则标unknown，不填0。
