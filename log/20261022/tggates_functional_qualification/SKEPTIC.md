# TG-GATEs 独立反方：时间预测、反馈更新与 RSI 的可识别边界

2026-10-22，Asia/Shanghai。角色：`scientific_skeptic`。本初始立场在阅读支持方正式提案前写定；已收到其候选的一句话概述，因此不声称对候选名称完全盲法，但下述数据/归因审查独立形成。未读取任何未开放 DNA、LDH、CEL 数值，不训练模型、不调用 DeepSeek，不改动 OASIS FAIL/STOP。下方全文/最新来源核验及交叉辩论以追加区分，不倒改初始立场。

## 初始判断

**可以资格审查一个条件于已预筛剂量菜单的、持续同药暴露下早期分子状态→24h功能预测任务；目前没有证据批准新世界模型/Agent/RSI 架构。** 不是因为直接模型的通用表达能力在逻辑上排除世界模型价值，而是尚未指出有限数据/有限计算下应该产生可验证优势的独有操作。合理的动力学归纳偏置可以有用，但必须击败使用同样时间、状态、剂量、功能辅助监督的直接与常规动力学模型。

历史 OASIS 关闭的是登记的全菜单双端点重复排序配置。MT 重尾和低 Spearman 不能外推到所有早晚预测/形态功能任务；也不能换指标救它。本次 TG-GATEs 是新数据资格，不是重置阴性结果。

## 当前来源允许与不允许的结论

数据资格报告与原始论文 DOI [10.1093/nar/gku955](https://doi.org/10.1093/nar/gku955)，Methods 的 Data framework、Dose setting、Hepatocyte treatment、GeneChip analysis 已直接读取。原文限定：人/鼠原代肝细胞最多四剂量、三时间，duplicate microarray；最高 in-vitro 浓度按 80–90% relative survival，难溶药按最大溶解度，原则上低中高 1:5:25；项目共用六人源 lot，但确切 sample→lot 未获得。原文还说 GeneChip QC 曾替换损坏样本且 QC 信息未公开。方法原文摘录在 `skeptic_sources/TG_METHOD_EXCERPTS.json`。

身份目录有 52 药/156 非control compound-dose-unit 条件覆盖2/8/24h，但尚未认证对应 DNA/LDH 的覆盖与测量单位。不同时间的破坏性采样不是同一个细胞的纵向状态。individual 1/2 不是已认证 donor。不得把探针、时间、孔或同药多剂量当独立未来任务。

菜单没有认证 washout、rescue、换药、换剂量或测量过程干预。由此可检验的是持续相同处理的条件预测/反馈泛化，不能检验随时间施加不同动作的反事实转移；2→8→24 的拟合也不自动识别真实细胞机制。仅有三时间且间隔6/16h，无法凭 latent time-composition 漂亮图证明 semigroup、真实速率或 Markov 充分性。

最高剂量的预筛设计本身提供功能先验。所有臂都须有 dose-level、实际剂量/单位、溶解度例外信息（能获得的部分）和同样预筛历史/成本口径。删除 High 标签仍保留了按先前 survival 选出的实际剂量。该任务若继续，应明确条件于这个 released menu；不能声称零先验新药安全剂量发现。预筛 assay/time/lot 细节待根代理审计，未得到不等于没有预筛或已证明独立。

## 先确定一个真实决策

研究者须在以下两类中明确选定主任务，而不能在结果后切换：

1. **购买早期分子测量是否改善固定24h功能复核菜单的分配。** 所有臂计入早期取样、阵列处理和晚期复核成本；真实早期状态给所有条件模型。2h采样不等于2h返回表达结果，不能凭时间标签声称提速。DNA/LDH 很可能比微阵列便宜，因此省费用/时延须有真实成本依据；否则只能以一个预算比率敏感性分析作体外筛选研究。
2. **已拥有早期状态时，少量晚期功能反馈能否传播到未测药/剂量，降低后续确认损失。** 这是合法的固定资产条件任务；所有直接/多任务模型获得完全相同早期状态。已查询动作的标签不得重新计为未查询命中。评价在未查询且化学组独立目标上，必须优于相同初始预测器+普通重训练/核条件更新。

选择“优先确认最强已知高剂量损伤”可能只是预筛先验再发现。需要说明业务效用是漏掉迟发损伤的代价、保留候选的代价还是对不确定药补测；标签/阈值须由可认证功能测量制定，不能把表达应激自定为临床DILI。未有真实干预改变剂量/疗程时，不称药物治疗规划。

## 原始先例与检索边界（初始）

直接先例 [Zhang et al., DOI 10.1038/tpj.2013.39](https://doi.org/10.1038/tpj.2013.39)，[PMC4034126](https://pmc.ncbi.nlm.nih.gov/articles/PMC4034126/)：本次由 Europe PMC 原始文献元数据/摘要核验，论文发表于2013 online/2014卷期。摘要明确使用 TG-GATEs gene expression、cell-based assays 和 histopathology，指出2h EGR1、ATF3、GDF15、FGF21 诱导预示后来 cytotoxic death，并对该网络进行 modelling/simulation 与 intrinsic dynamics 分析。因此早期状态预测迟发毒性、应激网络及动力学叙事不是新意。全文正在获取，未从摘要推出其具体 split 或性能已与本项目相同。

2026-10-22 精确日期范围检索已取原始摘要；最新 primary 来源包括 ProteinTalks DOI [10.1038/s41586-026-11001-9](https://doi.org/10.1038/s41586-026-11001-9)（2026-09-09）和 CellForge DOI [10.21203/rs.3.rs-10954762/v1](https://doi.org/10.21203/rs.3.rs-10954762/v1)（2026-09-17预印本）。前者原始摘要主张时间蛋白组预训练的可迁移动力学 latent 能支持药效/联合/类器官排序；后者主张多代理自己提出架构、写代码并验证六个单细胞扰动数据集。本文尚未精读二者全文，**不把摘要当公平比较证明，不作性能复现或穷尽新颖性断言**；但“动态表征可迁移用于药物发现”“多代理研究虚拟细胞模型”的宽叙事已有直接先例。

RSI 边界采用已独立核验的 `log/20261021/autonomous_rsi_round1/` 一手来源：Hyperagents 可编辑 task/meta program，AIDE² 自改科研代码，SpecRSI 学改进器且含共同artifact fork/同状态后继控制。共同起点实验是必须的归因设计，不能单独作为新算法。不能仅以这些宽先例排除某个未提出的细胞更新操作。

初次 early-human 检索返回1243项，相关性低，含病毒/肿瘤等无关结果；不把它当 TG-GATEs 专项综述。已启动精确 `TITLE_ABS:"TG-GATEs"` 日期过滤及主论文全文获取；结果与失败保留于 `skeptic_sources/`，不删掉低相关检索。原始检索3请求300,271 HTTP body bytes，仅文献，无实验数据下载。

## 最少且能推翻候选的实验阶梯

**G0 数据/用途：** 先完成精确键、时间/终点配对、重复单位、功能缺失、剂量先验资格；根据实际决策选择误差/净效用，而非照搬 OASIS 全菜单 Spearman 门。开dev前固定化学去重、source freeze、分区、主要损失、可用最小效用差δ与功效/停止规则；reserve 不参与特征、normalization、阈值或程序选择。无匹配功能或没有合法动作/实际效用，就停止相应配置。

**G1 同信息世界模型：** 用固定相同支持集和查询序列，比较 (a) chemistry+dose+时间/预筛先验，(b) 加已付费早期状态的强直接模型，(c) 具有相同晚期表达/功能辅助监督与容量预算的直接多任务模型，(d) 显式转移+功能头，(e) 最简单常规动力学/状态空间模型+同反馈重拟合，(f) kernel/GP残差条件更新及简单混合。所有候选可用同样监督、调参和搜索预算。先证明早期状态增量，再问显式转移约束增量；预测晚期状态更准但功能/真实决策不改善，不支持应用贡献。不能把“去掉全部辅助表达损失”当唯一世界模型消融。

**G2 Agent：** 固定同一个获胜模型，再比较固定dose/time覆盖、预筛dose优先、exploit-first、uncertainty/信息增益、标准主动学习/贝叶斯设计及同候选程序族等预算随机/BO/程序搜索。每次query必须来自真实可获得菜单且按整组实际输出计价；早期+晚期同一物理测定不能拆作多次免费反馈。只有真实采集因策略不同而带来未查询目标增益，才是采集策略贡献。

**G3 继承与联合：** 化学组/未来任务流预冻，权重和可执行程序分别开关；对照同历史from-scratch、固定检索、普通元学习/蒸馏。world/direct × agent/conventional 2×2，同预算看最强完整系统净效用；交互为正但总性能输不支持晋级。继承较强初始模型不能代替程序增益。

**G4 RSI：** 保存真正不同的改进策略m0/m1，再从完全相同的模型、任务程序和可见历史p0/w0/H分别给予k次修改/评价；更后从未用于策略选择的任务评估improvement@k/净增益曲线。强检索/普通搜索得相同失败历史和评价预算。若再形成m2，从另一共同起点比较m2/m1。计入形成策略的源任务、API与搜索成本；更多编辑次数、成功故事、同一任务CV提高或人工修代码不算RSI。

可证伪条件包括：早期表达没有超过预筛/剂量先验的实用增量；同信息直接/多任务模型匹配；常规动力学校准/普通残差更新匹配；固定/普通AL匹配；移植程序无净增益；共同起点meta策略不提高后续改进。若预冻主要效用差区间上界<δ，判无实用增益；区间宽则INCONCLUSIVE，不算支持，也不事后换主指标。数据只覆盖52药的完整早时间菜单时，有效独立化学组可能不足多阶段meta检验，不能靠时间/剂量复制出样本量。

## 对根代理的当前建议

完成 outcome-blind 功能配对和剂量血缘是合理下一步。随后先明确预筛后复核决策与成本、固定同信息强基线，再决定是否值得取得分子数据。**不因有三时间标签自动批准下载12GB CEL或构建Agent。** 这不是否定时间模型；是把其有限数据实用增量从免费额外观测、先验和普通更新中隔离。总目标未完成，当前不发布新颖性或RSI成功主张。

## 全文与最新来源追加

初稿后取得 Zhang et al. `EARLY_TG_FULL.xml`（134,963 bytes）并直接读取 Methods/Results。该文Pico-Green总DNA确为每个in-vitro实验的功能读出，在相同时间control下计算变化；不是本次新取得DNA表每行单位的官方认证。作者把全人源表达不分药/剂量/时间聚类，关联DNA后选择2→8→24 progressive profiles得到早期基因；随后在鼠重复同流程。in-vivo SVM使用80/20 random records split与10fold tuning。由此**不能把该文作者准确率当新药化学holdout验证**，也不能按其posthoc progressive选择方式制定本项目dev/reserve。文中四基因Boolean网络依赖文献结构，模拟与观察符合；没有证明真实干预下因果速率或研究程序继承。

最新原始 benchmark全文也已获取并读相关方法/结果：[A systematic comparison of single-cell perturbation response prediction models, Science Advances 2026-09-09, DOI 10.1126/sciadv.aed3414](https://doi.org/10.1126/sciadv.aed3414)，本地`BENCHMARK_FULL.xml`。13模型/25数据/24指标的作者结果显示绝对expression相关可随小效应更高、delta/DE表现则与大效应相关；方法明确含context/perturbation mean、linear、MLP基线。不能仅以它评估单细胞分子而外推人肝细胞功能，不能挑其某指标排名替代本项目预冻功能决策。

精确TG-GATEs检索还取得原始摘要：

- [A pharmacokinetics-informed ODE extrapolates long-term fenofibrate transcriptomic responses, 2026-08-25预印本, DOI 10.64898/2026.08.25.746919](https://doi.org/10.64898/2026.08.25.746919)：PK profile+Hill effect+coexpression module turnover，拟合rat-liver三剂量至day8、预测heldout day29，并比较统计/linear/MLP transition。只有单药，摘要明确跨药/器官/剂量方案待测。是标准低维kinetic强基线的近期直接先例，不是人源功能/agent/RSI的完成证明；仅核摘要。
- [Ontology-Driven Annotation of Key Events Enables Transcriptomics-Based Assessment of Adverse Outcome Pathway Networks, 2026-10-13预印本, DOI 10.64898/2026.10.06.756965](https://doi.org/10.64898/2026.10.06.756965)：人PHH TG四化合物AOP注释/ssGSEA；原始摘要自限为molecular perturbation，非KE激活或AOP因果进程直接证明。强调不以gene set叙事替代功能真值；仅核摘要。

全部7请求共900,159 HTTP body bytes，URL/status/hash在`skeptic_sources/NETWORK.json`及`PRIMARY_NETWORK.json`。没有数据集数值下载，没有重试根代理负责的S2/viability supplement路径。检索不是穷尽综述。

## 实际交叉辩论与裁决

支持方`mechanism_advocate`先保存`ADVOCATE.md`，我保存本文初稿后才互读。其唯一候选是`T'(t)=T(exp(eta)t)`，从paid support拟合单eta，跨未测时间/剂量/输出传播；Agent选择能区分clock/amplitude/head且使最终24h排序不同的菜单观测。独立初稿均未批准新架构。

我的正式四问（协作消息）是：单eta之外拟继承的独有操作是什么；三切面和一个支持如何排除幅度/头修正、线性轨迹完全等价怎么办；RNA/功能query如何按真实成本及返回时延计费、如何胜过直接24h确认；48药完整功能+CEL菜单化学组/meta分割后如何避免剂量时间伪样本量。

支持方实际回答承认：**没有超出标准time-warp/system ID的新增操作，也尚无强fixed rule无法解释的继承预期**，因此当前核心新颖性NO-GO；幂律clock=amplitude、log轨迹clock=offset，只有冻结曲线非共线敏感度下才可区分；不假设RNA便宜；没有48药元阶段power依据，不用dose/time补数。它建议如果做功能-only pooled-template pilot，只算有限族kinetic utility资格，不能作为创新或RSI。

支持方对我的反问也成立：饱和曲线`1-exp(-kt)`的timewarp与单common amplitude并不普遍等价；既有早期RNA条件任务无需证明这项沉没资产比功能便宜，只要所有臂初始成本一致。我的回应接受这两个边界，本文初稿已分别将有限数据bias和既有RNA条件任务列为可测机会。

根代理随后要求先做代数审计，已完成[clock audit](clock_observability/REPORT.md)：预注册、5数学不变量测试全过、构造两条全区间单调曲线匹配2/8/24及相同paid support但withheld预测不同。其结果否定一般可识别性，不否定固定参数族预测价值。没有真实功能值，不能将0.02构造差当实用效应。

**裁决：关闭当前单eta clock作为待深入的新颖核心；不关闭时间建模/早期状态信息的所有实用性。** 这不是代理投票，依据是操作与成熟timewarp相同，且没有新的继承/改进策略操作。功能-only数值pilot若不可能改变后续资源决策，只会重做常规校准，不值得为了有实验而消耗dev；若根代理确有固定候选族/实际24h复核预算的用途，可单独预注册一次普通kinetic utility资格，不能据通过自动升级世界模型/Agent/RSI。

仍未决的是：预筛条件下是否有功能反馈能跨未测剂量/药族传播、早期分子监督是否带来足够增量、以及是否存在真正超出普通更新/搜索的操作。目前均无正证据。没有因来源菜单完整便批准CEL下载，没有把未运行实验说成失败。
