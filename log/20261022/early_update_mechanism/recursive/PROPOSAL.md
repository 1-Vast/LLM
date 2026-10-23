# 独立递归／最强常规立场：先找出可继承更新器的真实优势

2026-10-22。recursive_distinct。未读本phase任何其他新稿／API提案，未读取保留背景或新生物数值，未重跑旧实验。本稿先独立封存，随后才能交叉与最小反证。**没有一个目前可认定独到的RSI核心。** 但这不意味着“能被普通函数表达就不可能创新”：新贡献可以是更少功能反馈达到同等风险、更少算力得到同等更新，或可证明的迁移条件；必须具体指出是哪一种。

## 1. 一个具体对象，不再搜索prompt层级

最值得用来改变当前判断的最小对象是**功能终点监督的可继承预条件更新器**。我把它明确列为强普通元学习对象，而非声称发明它。若一个新候选连这个对象都没有超越，则无需进入多代程序搜索。

固定基础模型theta0和源定义的p维可更新参数（第一试点只用小头或固定秩adapter；p与秩必须在结果前确定）。在一个新背景支持集S获得功能标签，计算proper functional loss的梯度g；支持药物的已测6h蛋白及mask可以作为共同输入，但不能给候选额外的未查询24h状态。采用

`P_phi = diag(exp(d)) + L L'`, `rank(L)=2`；

`theta_(k+1) = theta_k - eta P_phi gradient_theta Loss_function(S,theta_k)`。

phi=(d,L,eta)在源背景的完整药物分离support/query episode上，通过更新后query功能loss训练。每个新背景重置theta=theta0；只继承phi，避免较强起点冒充较强学习法。先固定最多2个更新步，不加router、历史网络或LLM。一个固定P没有条件化；若候选以后提出条件化P，其新增输入与元训练预算也必须给普通learned optimizer。

这一对象很可能就是经验Bayes先验精度／自然梯度／普通元优化的一个参数化。它的作用是把想验证的“学会如何更新”变成可以运行的数学对象，并提供强对照，而不是让新颖性靠名称逃逸。

## 2. 可改变NO_GO的具体、可证伪优势

目标是作者Efficacy注释的**更新后未查询药物proper risk**，不是原训练loss、表达重建或best模型分数。定义R(U,b)为从同一theta0、同一已观察状态与固定支持药物序列，在付出b个功能标签后，对不相交完整化合物query集的平均BCE。支持数量可预先固定b∈{0,4,8,16}，不得按标签是否阳性补采。AP/排序为次指标；BCE需真实概率输出，不能把SVC margin套sigmoid伪校准。

我愿意改变“尚无有用可继承更新机制”的证据是：一个具体U在**8个标签**下达到至少与最强普通方法**16个标签**相同的功能risk，并在相同8标签时优于它，且源期元训练／搜索费用计入总成本后仍在预先承诺的任务数摊销范围内有收益。这是明确的二倍标签效率研究主张，不是临床阈值；若数据与不确定性不足以检验，不能写成已经二倍。新增实测功能反馈必须真实改变U的后来效果，而不是仅保留更好的theta。

需要的强普通对照具体为：

- 同信息直接联合预测和source-trained support-conditioned predictor；同样得到所有可用状态、mask、药物描述和源episode。
- 从theta0普通重训／正则化replay；FTL在累计支持上重新优化同一目标，充分源调正则和步长，按实际总wall/FLOPs比较而非仅“步数相同”。
- empirical Bayes：同源任务估计均值／对角或低秩协方差，支撑集后验／MAP更新；不能把源信息只送给新phi。
- 普通meta-learned optimizer，包括同参数预算的梯度历史重组；源元任务、外层loss、训练次数和失败预算相同。
- 共享theta0和同反馈预算的有限程序搜索／简单混合；候选数有限，源选择与目标反馈全部入账。原始历史不能对它们隐藏。

这个效率结果若成立，首先支持更新器的应用价值，**还不证明paper新颖性**。若新候选能给出实质不同的估计器／约束并解释为何在此信息和成本下更有效，才进入创新主张。相反，若同信息EB或learned optimizer匹配全部收益，记录普通学习结果，停止独特核心主张。不能仅以“它可写成直接函数”否定统计效率，但也不能以“统计效率或许不同”跳过真正相同的EB实现。

## 3. 不是清单：最短实际反证应对准什么

对上面的固定P，最小反证是**源与新背景曲率旋转**。若源任务loss Hessian为diag(100,1)，源学得P接近diag(.01,1)；新任务Hessian变成diag(1,100)，P仍可把高曲率方向放大，较小源loss不能保证后续反馈更有效。一个从新支持估计曲率的普通Newton／EB更新可能更稳。

封存后应先做一个很小、明确冻结的2维二次loss检查：同初始误差、同支持梯度、比较源固定P、source-tuned scalar SGD、允许同信息曲率的普通Newton/MAP。分别报告正常共享曲率与旋转情形的更新后risk、稳定步长区间和实际可用信息。不能给Newton免费真实Hessian后宣称候选失败；如果候选只获得一次梯度，基线也只用这份观测；若支持提供精确二次样本，则都可用其Hessian。关键是验证“继承P会在什么条件下帮助／伤害”，不是演示所有元学习不可能。

更有价值的后续反证是线性／局部二次下的P是否与源协方差EB完全同一；如是，不能将非零继承收益称新操作。若另一个新候选提出了不同运算，再对那个运算做独立最小反证。本稿不在读peer前替它猜想机制，也没有先做合成实验再倒写假说。

## 4. 当前数据能做什么，不能做什么

HCT116所有600条晚期门标签已经用于开发，不能再当全新盲集。6h联合E的正向pool信号说明静态早期信息有机会，但不是世界模型、更新器或继承证据；晚期门失败也不是所有状态信息绝对无效。旧18stock／17lineage可以作为显式源训练候选，但须先认证功能字段、时点／化合物身份及共同特征合同，不能把不同synergy／single-drug终点默认拼成同一种标签。

一个合理的有限设计是源背景按lineage留出训练U；HCT116只开发；A375只作预固定有限选择；三余留背景仍保留。每个源背景多个药物episode是重采样，不是独立背景，不能从17条源谱系或5条新线虚构几十代独立RSI。现有数量至多支撑一个小更新器迁移试点。若没有可合法得到的源功能任务／共同输入，先停数据合同，不运行无意义大搜索。

本对象目前可以完全建立在静态6h表示上，**因此不能称以世界模型为必要根基**。若以后加入action-conditioned transition／Jacobian，其同信息必须提供给强直接更新器。世界模型贡献需要新的可检验优势：其状态／干预结构在相同源数据、参数和预算下，提高更新器的标签效率或计算效率；去掉transition保留所有观测后若无损，关闭相应贡献。一个普通线性化诱导核能够精确匹配时，先承认常规解释。

## 5. RSI还多一层，不能用U变好冒充E变好

记E为把新实验记录用于改进phi的过程。学习一个更好的phi或同起点U改善，是一阶learning-to-learn。若称改进策略本身提高，必须另固定phi0、可用历史、下一批新反馈与改进预算，把E0和E1各运行一次得到phi_a／phi_b，再从共同theta0比较它们在后来任务上的R。这些后来任务不能是E1的选择标签。

普通FTL元训练、在线元学习、经验Bayes的hyperparameter更新也是E对照；同预算程序搜索同样可改phi或代码。E1要优于它们才值得声称更好的改进策略。复制较好的theta1、更多meta-episode、更多候选、重复检查同一选择背景，都不能给这个结论。最近一手已有same-artifact improver probe，因此即使做对这项设计也不是首次发明RSI评估。

## 6. 三篇2025–2026一手原文实际核查

本轮复用项目已实际HTTP200取得并哈希认证的全文HTML；**0个重复下载／新HTTP**。所有原始HTTP时间、URL、status、bytes、SHA和逐段原句保存在本目录PRIMARY_EVIDENCE.json，非用摘要代替全文。提取器首次因maestro无bs4导入失败，随后改用标准库HTMLParser并成功；无数据／模型执行。

1. **Lightweight and Versatile Learned Optimization by Recombination of Gradient History**，2026-10-07，[arXiv 2610.09604v1](https://arxiv.org/html/2610.09604v1)。`S2.SS1.p1.1`：“The learned optimizer recombines averages of gradient histories … predicting a coefficient for each.” `S2.SS5.p1.1`直接以unrolled held-out loss训练更新器；`S3.SS1...Px2.p1.1`共享初始化、数据顺序、随机流和训练预算。故“继承梯度重组／共同起点／元loss”已不是新操作。限制也明确：`A1.SS3...p1.1`基线无domain-specific sweep，`S3.SS4`真实时间可高于Adam达2.336×且占更多状态内存；不能拿作者默认Adam对照当充分调参最强普通方法。
2. **Self-Adapting Language Models (SEAL)**，原始2025-06、审阅v2 2025-09，[arXiv 2506.10943v2](https://arxiv.org/html/2506.10943v2)。`abstract1.1`：“using the downstream performance of the updated model as the reward signal”；`S2...Px5.p1.1`明确“learning an adaptation strategy … via its outer optimization loop”。因此用下游功能反馈训练更新指令／数据／超参的概念已存在。把文本换成细胞反馈不自动是新技术；该工作不证明生物状态或本任务的效率。
3. **Drafting Agents, Not Just Tokens / SpecRSI**，2026-10-12，[arXiv 2610.16491v1](https://arxiv.org/html/2610.16491v1)。`A4.SS1.p1.1`：“both continuations start from the same already released version, but use original or updated improvers.” `S3.SS4.p6.1`明确actor更新改变continuation law，需fresh searches校准scorer；`A6...Px7.p2.3`不保证无限递归加速。故同产物换改进器、学习验证预算都有直接先例；本研究必须提出细胞任务中的额外统计／计算差异，而非重演该抽象架构。

## 独立结论

我不提名上述普通低秩预条件器为可发表新算法；提名它为未来新规则必须击败、且可立即做曲率／EB反证的具体普通对象。目前改变NO_GO最有价值的证据是新的可继承更新规则在共同起点、强普通对照和真实总预算下提供明确标签效率优势，并且世界模型结构提供不能被精确同信息常规实现解释的必要约束／效率贡献。当前没有这样的结果。下一步应实际交叉审查与一个最小反证，不能再只追加证据门文档或多层prompt。
