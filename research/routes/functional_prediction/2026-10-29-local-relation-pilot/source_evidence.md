# 本轮原文、源码与证据边界

2026-10-29。本轮是 H_L 必要前提的定向核查，非完整领域综述。两个主题查询和四次实际获取均保存在 [retrieval.jsonl](retrieval.jsonl)，原始搜索响应在 [search_results.json](search_results.json)。6/6 逻辑获取动作、2/2 查询、0 自动重试；四件成功响应共 3,982,688 B。未继续翻页或追查全部施引，不能据此主张普遍新颖性。正文阅读级别均为 P，而非全文复现。

## P1：GVALID 的目标依赖获取已有明确先例

*Active Policy Optimization for Individualized Dosing via Gradient Variance Minimization*，Yi Wan、Xin Wang、Huanhuan Chen。官方 [PMLR 页面](https://proceedings.mlr.press/v306/wan26l.html) 的 citation metadata 给出 ICML2026、PMLR306:124676–124705、2026-09-29；首次公开日期未另核。实际 [PDF 原件](sources/p1_gvalid.pdf) 为 2,067,391 B，SHA256 `d34740a8f2a0e511bd93e1e5176d20d30e7b64708682d80c815f4982438f5637`。本轮 root 与运行前挑战者核读 PDF 页3–6 的问题、假设和获取方法；30页证明与实验未复现。[提取投影](p1_pdf_text.json)只是导航，引用依据仍是原件。

- 页3的对象为连续剂量、个体上下文、单次干预；目标是最终策略价值，非最小达阈值的有限剂量菜单。
- 页4的梯度风险联系依赖平滑、强凹/内部最优点等条件；不自动适用于本轮原始有限点的阈值推荐。
- 页5–6、Eq10–19，以当前最优剂量附近的有限差分梯度方差为代理目标，通过协方差平方/观测方差打分和 Schur 更新构建批次。一般“模型指导获取—反馈更新策略”已存在；不能把它当新机制，也不能把本文定理移植给 H_L。

官方 Software 链接确认 [作者仓库](https://github.com/ry-wan/GVALID)。取得一次 HEAD ZIP：1,736,917 B，SHA256 `f489c425f6a8c39c29ead1342109692fc7a829481e884731ccd0fce0170a3de3`；完整 commit 未知。45成员中提取14个源代码/配置/README/LICENSE 文件，共161,088 B，位于 [源码快照](../../reference/code/ry-wan-gvalid/archive-f489c425f6a8/Readme.md)；MIT 许可已读。31成员未提取，包括两个 NPY 共51,832,368 B 解压体积、输出、图和字节码。归档含偶带数据，未开或提取，不能称 data-free。[原件/排除清单](p1_code_receipt.json)。

实际只读 Readme 前55行与 `src/samplers.py` 852–1147：`GVALIDSampler` 在当前预测最优点构建有限差分对，以 `sum(K_g_q**2)/var_q` 贪心选择并更新协方差。所读实现用均匀 `linspace` 候选剂量，而原文 Eq14 写粗格内随机取点；不是完整逐行复现。README 提及 main.py，实际快照入口为 run_experiment.py。未安装、运行作者代码或据其 outputs 采信效果。

## P2：低成本初筛可指导追加剂量，但终点和选择边界不同

*Predicting Quantifiability from Primary Screens to Prioritize Dose-Response Profiling*，Sean Lim。[arXiv2608.26538v1 原HTML](sources/p2_quantifiability.html)的版本横幅为 2026-08-27；正式期刊/会议身份未核。162,632 B，SHA256 `bb561dbb5a676cf97ffea4de7c9ceb60e44deada5168910bdf78c05b24619b5f`。root 与运行前挑战者核读 Methods2.1–2.6；root 补核 Data Availability。[段落投影](p2_blocks.json)。

Methods2.1 使用32,971个历史上已从三点初筛晋升到11点曲线的 compound–assay 对；主目标为可报告的定量效力/曲线，不是本轮原始导出 inhibition≥0.5。结论条件化于原晋升政策，未晋升对象的反事实追加收益不可据此直接得到。2.2–2.5给出初筛幅度/形状/变异特征、Morgan指纹、RF及按时间重算历史统计的滚动评估；不能把随机分割中的全矩阵统计误称完全时间安全。2.6的 ToxCast 外部检验针对信号幅度关联，不等于外部验证 EvE 训练模型或药筛节省。

Data Availability 作者称 EvE Bio releases1–11 和 invitroDB4.3 为公开数据，前者 CC BY-NC-SA4.0；本轮没有下载或核准为 cell×drug 功能数据。原HTML未识别到本任务代码仓库/Code Availability，小范围未找到不等于没有源码。

## P3 与已有 CV/NLP 原理

复用 [DrEval2026 原文](../../reference/papers/doi-10.1038-s41467-026-72903-w/paper.html)，DOI10.1038/s41467-026-72903-w，本轮实际重读 Par24/44 的身份/均值效应，未重下或重新复现；它支持保留强简单对照，不能直接给 H_L 的数值结果。

早前已核读 H-Net2025、DC-DiT2026 和 SimMLM2025，原件、方法定位与限制见 [多尺度/多模态研究](../2026-10-29-multiscale-common-function/source_evidence.md)。本轮没有重新扩成另一套 CV/NLP 文库。可借的是按任务改变处理粒度、计入部署预算、用信息子集检验条件贡献；完整视觉/文本输入上的计算压缩不自动减少实验孔，随机模态 dropout 不代表药筛的选择性缺测。H_L 特别检验物理剂量位置上的局部关系；失败不反驳所有多尺度或多模态原理。

## 登记、失败与尚未覆盖

两篇新原件与 GVALID 部分源码已通过 reference_library.py 本地入库，未再次网络获取。[登记记录](registration_log.json)保存实际命令。库校验 [library_verify.json](library_verify.json)：123唯一来源、108论文文件、10代码快照关联9篇；errors/warnings为空仅证明清单完整性。

工程失败分别保留：PDF初次UTF-8投影遇 pypdf surrogate，改为 JSON ensure_ascii=True 保存投影，原PDF未变；收口时一次辅助HTML解析报 `ModuleNotFoundError: No module named 'bs4'`，未安装依赖，改用标准库 HTMLParser 静态检查。两者不是科学阴性。更近的剂量注册、局部迁移和主动曲线先例未穷尽；原始单药 source-well、培养重复、准确 assay 时间/技术的导出对应仍未核准，沿用父轮限制。
