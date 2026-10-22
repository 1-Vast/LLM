# Chemical genetics / evolution 身份资格：方法与公开登记

2026-10-22，Asia/Shanghai。请求前登记。唯一原始研究为 *Systematic mapping of antibiotic cross-resistance and collateral sensitivity with chemical genetics*，DOI10.1038/s41564-024-01857-w，PMC11726442，PMID39623067。根代理既有PubMed摘要线索见 `../serial_antibiotic_alternatives/REPORT.md`。

最多2次GET、combined response body≤2,000,000bytes。第1请求固定Europe PMC `https://www.ebi.ac.uk/europepmc/webservices/rest/PMC11726442/fullTextXML`；若失败立即保留body/hash/status，不换source或重试。只从保存XML投影methods/材料实验身份、Data/Code Availability与明确dataset accession/URL；不读取results量化claim或响应值。若方法内容包括实测响应表/数值，投影排除表格/图/结果及abstract，不导出。第2请求只有在第1XML明确给出公开data registry/代码manifest关联时，才访问该正式registry metadata，不能取响应矩阵/样本表/图像。顺序singlewriter、请求前拒绝覆盖，失败立即持久。

目标是认证：起始genetic状态/删除株与40drug功能screen的实际keys；70真实演化pair的drug、founder、lineage、选择/重试、状态测量及功能身份；公开data/code的真实位置与可配对菜单。跨实验query/update/transfer replay不强求同colony控制分支，但需合法动作/真实结局、独立任务和feedback成本。不能把40drug静态矩阵冒称时间转移，也不能将进化验证成功率当本项目性能。

无exactjoin/公开metadata则保留NOT_QUALIFIED；来源可用性不是架构或新颖性批准。源码/实验脚本只 `research/chemical_genetics_qualification_20261022/`，全部协议/来源/失败/报告只本日志目录。
