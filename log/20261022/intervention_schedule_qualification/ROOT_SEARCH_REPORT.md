# PubMed替代源搜索：取得一个真实序贯干预候选资产

2026-10-22。欧洲PMC服务503后，先登记 `PROTOCOL_ROOT_PUBMED.md`，再用已工作的官方PubMed Entrez作一次固定查询及该查询返回的20条primary article记录获取。两个请求均200，共 **442,043 body bytes**；原始SEARCH/ARTICLES XML、投影及hash/URL/status在`root_sources/`，执行输出在`ROOT_PUBMED_EXECUTION.txt`。没有重试，也未打开实验矩阵。

查询共46项，只取按发表时间排序的前20项；含膜相序、材料堆叠等不相关结果，因此不能声称完成全面的序贯药理综述。返回的作者摘要是文献先验，里面的定性效应及公开数字不是本项目复现或独立结局。

最具体的跟进源是 [Massively multiplexed microfluidics maps combinatorial and sequential antibiotic responses in 3D](https://doi.org/10.1101/2025.10.30.684665)，PMID41278959、PMC12636614，2025预印本。原始摘要主张512个可独立编程3D培养腔、约10,000菌落实时显微成像、约2,700个抗生素dose-combination条件，并实际比较同步与顺序给药、营养时序和水凝胶硬度。它比仅有固定暴露时间标签更接近可执行干预菜单，但摘要尚不认证公开数据、状态/功能配对、完整政策replay或有效独立任务数。

因此已启动**该单一source的primary方法/数据manifest资格**，记录于`log/20261022/antibiotic_schedule_qualification/`，同时由不同立场代理核查必要条件。应用若成立，是3D细菌微菌落内的抗菌给药顺序选择；不是人肝细胞毒性/临床疗效，也不能把菌落图像预测自动称完整虚拟单细胞。核心问题仍是干预下状态转移怎样支持功能决策与可继承的研究程序，不能把任务缩成普通菌落生长forecast后宣称原目标完成。

必须重点审查：形态与growth是否从相同图像计算而产生目标泄漏；早期可用state及后期functional读出时间；独立腔、菌落、处理/批次/strain的嵌套；真正实测的替代顺序与给药间隔；是否只有静态schedule对照还是有足够state-conditional行动支持；source/未来任务能否独立划分；公开文件及精确identity键。任何缺失不能用模拟补成实测评价，也不因大量菌落数而制造meta任务。

其他相关但暂不优先的作者摘要线索（未获取全文/资产）：

- [MEK+mTOR glioblastoma, 2025](https://doi.org/10.1158/1535-7163.MCT-23-0864)，PMID40746158，含phosphoproteomics与serial/simultaneous处理，但本次没有认证公共配对数据或独立背景数量。
- [Sequential palbociclib/cisplatin proteomics, 2024](https://doi.org/10.1097/CAD.0000000000001633)，PMID39011652，HeLa有限药序机制研究；不能自动提供足够继承任务。
- [Tamoxifen-resistant breast-cancer drug selection, 2024](https://doi.org/10.1016/j.jprot.2024.105319)，PMID39299547，其“sequential screening”主要指筛选流程层级，不宜误认成完整多次给药schedule资产。

本次没有找到可宣布成功的新机制，没有模型、Agent或RSI实验。没有将Lee/GSE30516身份资格或服务访问失败改写为整个目标不可行。下一步以单源真实manifest证据决定，而非先追加架构。
