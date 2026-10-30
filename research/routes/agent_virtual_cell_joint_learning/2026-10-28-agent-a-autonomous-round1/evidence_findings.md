# 生物需要、直接近邻与证据停止

2026-10-28。本角色先存 `initial_evidence.md`，后核来源；未读本轮候选。effective model/effort=unknown。2条主题query已用尽；不扩源。未跑实验/训练、未下载数据集/权重、未改src、未干预M1。原始请求/响应、原文、失败收据与scope均在 `sources/evidence/`。HTTP原始收据含公开会话Set-Cookie，仅本地保留，不再打印或外发。

**最能改变选择的发现：DrugReflector已完成真实外部表型→任务签名更新→重新选药→新药物验证。** 不能以闭环、Agent或功能反馈改变任务表示本身为新增贡献。另一个边界是：归一化RNA快照、测序回收数、培养物活体总量/真实功能不是同一观测。

## 最有价值的两个科学问题

**Q1：哪些当前RNA边缘分布不可区分的药物处理后群体，在后续合法药物/洗脱动作下具有不同功能结局？哪一项成本可接受的真实测量能区分它们？** 科学输出应是当前信息能区分的后续动作，不能以平滑轨迹替代。谱系标记比例、活细胞数、再生长、分泌等须分别定义。药物动作施于培养物/孔；细胞是采样单位，重复与不确定性须在孔、培养批次或供者层面定义。

**Q2：真实功能反馈改变的可复用学习对象，超出签名校准、功能头或完整监督重拟合了吗？** 同样的新标签若让简单方法得到同样后续药物排序，成立的是新信息/监督价值。更强的问题是反馈识别的区分能否用于未更新过的动作或独立背景，且不依赖不可观测的同细胞纵向耦合。迁移须有额外不变性与支持域条件。

## 最近邻的具体运算与覆盖

**E-P1：Active learning framework leveraging transcriptomics identifies modulators of disease phenotypes.** Benjamin DeMeo et al. Science，2025-10-23；[DOI 10.1126/science.adi8577](https://doi.org/10.1126/science.adi8577)。作者原PDF已保存，2,388,235 bytes，`%PDF-`有效，SHA256 `36d184d295092a02bc5ab1e2f98c248c9b8a44d018cfa6e810735b6d34cad0f7`。

运算为：CMap签名→药物分类器；目标签名→排名→选药；条件级RNA与Day7流式表型→pseudobulk基因表型关联→学习签名→与原签名插值→重新排名。文字可写作 `s_new=s0+eta*(s_learned-s0)`，但这是运算复述，未核补充代码等式。20药物（12hit/8non-hit），RNA Day1/2/5/7；在cell type/time/eta网格中采用Day1 HSPC、eta=.7。后续96未筛药，85过QC、22hit。直接覆盖真实表型更新任务表示与下一批选药；未据此确认核心动力学更新、序贯药物策略或动态迁移。流式Mk/Ery谱系丰度不能冒充血小板释放/凝血等生理功能。阅读PDF pp1–7选段、pp11–12、Fig3/4 captions；supp方法403，未复现。

**E-P2：ARTEMIS integrates autoencoders and Schrödinger Bridges to predict continuous dynamics of gene expression, cell population, and perturbation from time-series single-cell data.** Bioinformatics 2025；[DOI 10.1093/bioinformatics/btaf218](https://doi.org/10.1093/bioinformatics/btaf218)。原JATS `artemis_PMC12261462.xml`已保存。VAE与unbalanced Schrödinger bridge交替/联合优化，latent对齐和重构使表示随过程拟合改变；另拟合kill-rate网络。2.3明确假设：无额外群体信息时，以收集细胞数代表相对群体量，并忽略测序回收变异。不能默认套用于固定回收/池化测序。已覆盖快照表示与过程共同拟合；所读范围未建立外部真实功能闭环。阅读2.1/2.3/2.4/2.5/4完整选节，未核补充算法/结果。

**E-P3：Learning Individual Dynamics from Sparse Cross-Sectional Snapshots（CADENCE）.** [arXiv:2605.23470v1](https://arxiv.org/html/2605.23470v1)，2026-05-22。复用已有原HTML，保存选段。静态context→专家混合参数→latent ODE。可辨识性依赖context可确定动力学组、有限参数族、FOA等；A.3的FOA直接要求不同参数产生不同时间边缘分布族，不能由拟合自动获得。RNA等价而功能相异过程不满足其现有观测区分条件。阅读S2–S5、S9、A.3选节；未独立审计证明或复现。

**E-P4：Conditional Monge Gap enables generalizable single-cell perturbation modelling.** Nature Machine Intelligence，2026-06-01；[DOI 10.1038/s42256-026-01242-8](https://www.nature.com/articles/s42256-026-01242-8)。原HTML已保存。已读运算为以条件c和source cell s预测位移 `s+T_phi(c,s)`，一个条件transport跨药物/剂量/组合共享信息；不能默认transport等于真实细胞路径。讨论保留未见类型、稀疏MoA/高剂量、支持域外与batch局限。阅读Discussion完整、Architecture首段、Data/Code availability；未通读loss与实验。

## DrugReflector公开表与信息合同

| 条目 | 核实范围与边界 |
|---|---|
| [GSE305979](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE305979)官方SOFT metadata | 单donor CD34+ HSPC；60,000细胞/初始孔；固定1uM；Day0/2/5给药；RNA Day0/1/2/5/7；每药biological duplicate跨libraries；12 CMO samples/library。有药物×时间，无背景×剂量/策略交叉。GSM是library，不能按GSM数计独立药物重复 |
| GEO文件清单 | 4个h5ad：Day0 raw、Day1–7 raw、demuxed、normalized+celltype；声明well/treatment映射。未下载核实际完整交叉，清单未列独立流式表；不能据此断言全研究未公开表型 |
| [Zenodo16921906](https://zenodo.org/records/16921906) | 3个state-transition v-score h5ad文件名已核，不是20药物配对表型表；未下载 |
| 原文TableS1/S2/S4及TablesS1–S7 | S1/S2初筛排名、S4更新排名的存在声明已核；Science supplement403，表格payload/schema未取到，不能认证可直接join的最小公开源表齐备 |
| 原始Mk screen与额外供者 | p4：107排名药物，100nM/1uM/10uM，取最大非细胞毒诱导剂量；87随机；17hit向2额外donor验证，15过QC/13两donor通过。不是20条件时序的跨donor全交叉 |
| 剂量与配对 | RNA时序固定1uM，主screen标签可能为三剂量最大值，不能直接拼接；20条件Day7配对flow是否严格同1uM仍待supp核。RNA/flow是条件级配对，不是同细胞纵向身份 |
| 留出 | 签名eta/type/time使用反馈选择；96新药是前瞻留出，不自动证明跨donor/给药策略迁移或全部候选宇宙的序贯regret |

**真实数据开发性验证：NOT_READY。** 最小缺口为条件级源表：药物、donor、dose/exposure、RNA与flow孔映射、Day7原始表型/活性/QC、独立孔/批次重复、原始/更新排名和screen轮次。当前原文足以定义合同和最近邻，不能启动真实数据效果验证；未取得不等于不存在。

## 最小可判别实验（仅设计，未执行）

先冻结同一背景与已知暴露下两类处理历史，要求它们当前RNA边缘分布在预设测量精度内不可区分，但对一个后续合法动作（维持或洗脱后再挑战）的真实功能排序可能相反。是否有这种可重复生物实例必须实测，不能由合成设定当发现。独立培养重复分给RNA、真实功能取证、后续动作结局；不以测序数代活体量。

先给所有方法**相同已付费证据**，比较：A 冻结RNA模型+更新任务签名（DrugReflector式），B 冻结表示+重拟合功能头，C 足够强的完整重拟合，D 所提共同学习对象。各方法获得相同动作历史和标签。随后另测相同合法查询菜单/成本下的取证选择，把“选了更多有用信息”和“更新运算更好”区分开。

主终点是未用于更新的后续动作真实功能效用/排序损失，按独立培养重复估计不确定性；若声称迁移，完整留出背景。没有可重复功能分歧→Q1不成立；有分歧但当前证据不能区分→信息不足；强同信息基线同样有效→信息价值成立而算法贡献未立；仅同背景有效→不声称迁移。

本轮可用有限合成反例检验上述信息合同，但仅能检验计算与可辨识边界，不能证明生物机制或算法优越。若日后取得DrugReflector源表，可做20条件Day1 RNA→Day7流式的整药留出校准，**那只能检验表型对齐，不能冒充上述序贯动作实验。**

统一登记交协调者：E-P1/E-P2/E-P4可增量登记；E-P3已有库；保持partial scope、来源角色和hash。另注意CellFlow同名：库中arXiv2502.09775为形态图像方法（作者项目现名CellFlux），另有transcriptomic CellFlow 2025.04.11.648220；本角色未通读后者，不互换名称。
