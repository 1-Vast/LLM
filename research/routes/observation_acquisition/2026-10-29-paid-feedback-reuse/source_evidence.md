# C5–C6来源与可获得性：普通功能数据为主

2026-10-29。主线只依赖常见公开cell×drug药敏功能表及记录的浓度窗。组学、遗传救援、靶点真值不是普通功能预测的准入条件；机制、因果、选择性和独立实际功能收益需要各自匹配证据，不由拟合表升级。公开可下载不等于跨实验室普适，窗字段、时间、重复/QC和上游拟合仍需核实。

## 数据成本与继承边界

本轮不新增功能数据下载，复用已核20,355,833 B的GDSC2 CSV，SHA256 `0883b3ef6e440603094c43c74044e1d333fce61e92e3efa374ea3a54f0b50302`。作者Figshare DOI10.6084/m9.figshare.22362739.v1/file39806563可公开获得，CC BY 4.0。原文件25Feb20，不能冒称最新27Oct23发布。566训练/243已暴露开发、64条件菜单与rank1/8训练参数原封复用，身份/hash见input_freeze.json；不安装、不用GPU、不测序、不新做湿实验。

历史PRISM19Q4约42.49MB亦为普通公开药筛；C2负结果不抹去。24Q2/CTRP确认功能数值继续不开。GDSC原始拟合LN_IC50与窗内≤1µM事件只是复测候选代理，不能替代实际杀伤、重复培养、跨资源或临床收益。导出窗精确语义、上游共享NLME及供体依赖的缺口继承C4 fit_semantics_evidence.md；RMSE不是IC50置信度。

## 直接先例DRP2026：实际取得什么

原文DOI10.1093/bioinformatics/btag293、PMID42103986、PMC13242297。此前实际核读Methods、3.1和3.3，未称全篇/SI复现。论文原链接确认官方仓库：
https://github.com/abbiAR/-Strategic-Cell-Line-and-Compound-Selection-Using-Drug-Response-Profiles

本轮固定commit `d642b2b490f6e98dc2831d1bca830a6e5139bad7`，提交时间2025-12-03T11:24:45Z。repo/commit/完整recursive tree原响应均保留；树未截断，API license=null，树无LICENSE，故许可unknown。仅取得README和全部三个Python源文件，合计21,252B，每件Git blob SHA1与SHA256均核过。数据CSV、表达ZIP和作者环境未取，无作者代码执行。源码subset已通过reference_library.py的--existing登记为existing_user_copy，并按实际manifest补固定commit/partial-scope注记；不是完整仓库数据快照。

root上一步已全文读过四文件，本步再核关键行。实际内容：

- README第10行把整合GDSC响应写为`-log10(IC50)`，未说明浓度单位；不能移植为原CSV的LN_IC50或擅补µM。第12行同时说明MCF10A实测参考面板、其他细胞预测参考面板；不能都叫实测。
- predictive-peroformance脚本（文件名原拼写如此）第85行只loop `test_drugs[:5]`；第107/109行训练和validation分别用各自均值补缺失；第117行GBR100树/depth2。它是对应脚本参数，不能推断整篇执行范围。validation自身协变量均值填补不能自动等同目标标签泄漏。
- differential脚本第18行注释区分MCF7预测/MCF10A实测参考；第29–30行全X均值填补发生在测试细胞移除前；第42行GBR100/depth4。此处理边界要记录，但本核读不独自裁定整篇结论。
- explainability脚本用训练响应相关top500基因及RF200作解释分析，不能因此说普通功能反馈方案必须组学。原文其他实验50树与这里不同实验参数不是自动矛盾。

四文件是静态训练/预测示例，所读源码未见逐批测量再选循环；不能据此宣称整篇或整个领域没有闭环。BATCHIE2025、普通完整历史贝叶斯设计已覆盖反馈更新骨架。C6不认领新算法，只有被独立实用验证支持的能力才可继续。结构初探对COPEx2026、GoBOED及模型误设原文的实际局部范围见principle_scout_sources.md；不是穷尽近两年查新。

## 本轮获取与Harness封账

8/8公开获取动作：repo API、commit API、一次archive、recursive tree、四件固定raw源文件。archive在读到10,000,001B前缀时触发10,000,000B cap，前缀丢弃，无archive文件；保留失败receipt、不重试。成功保存原始来源payload共38,117B，限30MB；另有本地收据/manifest/库内副本，不混作网络新下载。底层重定向HTTP次数unknown。0/4主题query，本轮8动作额度耗尽后无进一步联网。

DS015是一次已完成工具禁用的headless字段整理，真实session-c54cb7f9-23ec-44e0-88f9-cadf1dc1a6fd。4.297s、1834 input/569 output/cache-read256tokens，声明USD0.025、180s/2048输出tokens/12KB stdin；实际4928B stdin。effective backend/实付及底层请求数unknown。原JSON/事件/usage保留。root逐源核后有限采纳，原返回给实测面板添的`10:`行号不正确，实测/预测两句实际均在README第12行；此前root审核也误写了第12行，已在main_review.md更正。该错误不改变单位null或其余四组有源码支持的限定事实。Harness未选择假设、指标或机制。历史6调用加DS015累计7/7，无自动重试、后端替换或后台轮询。

只据这份证据支持便宜公开数据的开发筛查，不支持“普适性/新机制已成立”。独立确认路径必须另有固定覆盖、剂量/时间、重复与费用信息，否则阳性也停放。
