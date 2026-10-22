# 独立支持方：干预世界表征能否预测普通更新的后续价值？

2026-10-22。本稿在阅读本阶段其他代理的新独立稿之前保存。先读取已冻结 AZ 与最新一手文献 `DECISION.md`，接受其全部 STOP 与观察边界；没有打开旧 reserve、任何新生物响应或模型，没有数值拟合、DeepSeek/其他模型服务调用。4次公开文献 GET 全部 HTTP200，正文完整保存并逐一核 SHA，见 `HTTP_RECEIPTS.jsonl`、`SOURCE_INDEX.json`。以下是机制/机会资格审查，不是数值实验注册。

## 独立裁决：NO_NEW_CORE；0个候选已满足实质前驱差异

**目前没有找到足以提出为新核心的 world→update-value→later-improver 机制。** 可以写出一个小、可检验的收益预测器，但其主要算法部分落在已建立的验证梯度对齐、任务嵌入、上下文元学习/学习优化内。把细胞响应换成一个 latent、加策略记忆或把目标改名为 update-value，不构成实质差异。

仍值得研究的必要问题更窄：**在固定合法反馈与预算下，不同普通更新的相对收益，是否存在可复现且实际有用的任务间变化，而不是一个方法普遍最好、或者噪声决定排名？** 只有先确认这点，才谈能否由有限付费干预响应预测这种变化。本问题及其可靠性评估不是新方法，历史 EG-RPT 已提出 policy-ranking reliability；这里不重新命名为创新，也不把未运行旧稿当证据。

AZ 的 effect 坐标在其固定低容量模型内胜 dose，却败强直接预测，故不能作为“功能坐标就是充分状态”的依据；也不能外推否定所有功能模型。当前研究若继续，应换成独立的新任务合同与明确的更新价值问题，不在旧面板追加响应几何、回放、代理或新配置救该结果。

## 新核对的三个直接前驱，以及最新工作的已知占位

### GLISTER v4：下一次更新的验证收益已是明确目标

[GLISTER: Generalization based Data Subset Selection for Efficient and Robust Learning](https://ar5iv.labs.arxiv.org/html/2012.10630v4)，原2020-12-19，最新版本2021-06-11。新GET正文 `glister_v4.body/.txt`，SHA `a5939888a222bde67c8b6789ec2e438310cf0c864bd767f320bbb716738c74e8`。正文约1108–1190行的 online meta approximation 以当前参数的一步 subset 更新代入 held-out validation likelihood；1545–1615行展开 Taylor 近似，2275–2279行明确最大化 training-subset 与 validation gradient 的内积。其验证标签是合法 development 信息，不能换成未授权 final audit。2475–2500行的主动学习版本还用假设标签处理未标注点。

因此，`预测某次梯度更新是否有利`、`残差/验证梯度对齐`、`用模型预测补足未知标签后决定下一动作` 都不能直接成为新核心。它做的是样本子集选择；把动作改为有限重训/回放菜单在任务上不同，但普通更新选择的算法概念未因此独到。

### GRAD-MATCH v2：梯度几何与廉价更新选择已有直接形式

[GRAD-MATCH: Gradient Matching based Data Subset Selection for Efficient Deep Model Training](https://ar5iv.labs.arxiv.org/html/2103.00123v2)，原2021-02-27，最新2021-06-11。正文 SHA `e450cae0f8ac937aae940894642217a0a6c1cbc70806c33a371f2877690c7e21`。约590–969行给特定条件下的收敛界，969–1148行说明以训练/验证梯度匹配误差为选择目标，含 isValid 切换；随后以正则化 gradient matching、OMP、last-layer/per-class 近似实现。不能把这些定理泛化到任意非凸世界模型。

它把廉价梯度形状用于更新数据选择；若本项目只计算 residual/Jacobian Gram 再路由普通动作，必须视为强普通解释。其约3011–3018行保留 `Full-EarlyStop` 匹配时间/能耗的全量训练基线，提醒不能只匹配更新次数或候选数，省略 source 价值训练、梯度和搜索费用。

### Task2Vec / model2vec：任务几何预测哪个适配路径好已有前例

[Task2Vec: Task Embedding for Meta-Learning](https://ar5iv.labs.arxiv.org/html/1902.03545v1)，2019-02-10，元数据未发现新版本。正文 SHA `8246b57b03106f5ac883aac07933b96d799a2bdc5bdab9f342a701f5810454f0`。约418–421行使用共同 probe、对任务训练分类头，再以 Fisher 对角/按filter平均作固定维度嵌入；911–1186行区分任务相似与非对称 transfer；1177–1305行的 **model2vec** 显式学习 task/model co-embedding，以既有任务上候选模型表现预测新任务该选哪个。

因此，`付费反馈→任务几何→预测候选适配价值→在新任务选择` 这个结构本身并不新。其视觉分类数据、选择 feature extractor 而非细胞更新菜单是应用差异，不足以构成新算法。一个依赖 source-trained metric/value map 的“世界证书”可能正是它的领域变体。

本轮第1GET还核到2026-10-07的 [Lightweight and Versatile Learned Optimization by Recombination of Gradient History](https://arxiv.org/abs/2610.09604v1) 元数据与最新版本，摘要明确小网络重组梯度历史并迁移新任务。其正文预算/混合路由限制已在上一阶段独立审计，本轮没有重新下载或冒称复现。上一阶段已核的 SEAL、SpecRSI、CellScientist、ShinkaEvolve、AlphaEvolve 等继续排除泛化的可学习改进器、诊断修订、策略记忆和同起点测试的首创性；本阶段不重复请求它们。

这不是穷尽所有 learned optimizer、元学习或生物任务表征工作的 novelty certification。四次GET额度已用尽，不以未搜索到更新名字宣称空白。

## 一个可解析的最小机制，但暂按普通机制拒绝新核心

以下不是第1个“已过门创新候选”，而是**1个被明确归约的待验证实现**；未发现第2个足够不同的方案，因此不为了数量再堆模块。

令静态世界组件给出干预 `a`、context `c` 的响应特征 `phi_W(a,c;H)`，其中 `H` 仅含已授权付费反馈。先固定该特征映射，末端用线性头 `f_theta=phi_W^T theta` 预测一个预定响应标量或固定基因向量的平方损失。普通更新菜单产生 `delta_k=U_k(s)-theta`；例如新观测上的固定正则头重训、预定回放权重的头重训、无更新。动作/超参先固定，不能为各任务事后添加算子。

对平方风险 `R_t(theta)=E_t[(y-phi^T theta)^2]`，固定特征时有精确恒等式：

`V_t(k) = R_t(theta)-R_t(theta+delta_k) = 2 delta_k^T b_t - delta_k^T C_t delta_k`

`b_t=E_t[phi (y-f_theta)]`，`C_t=E_t[phi phi^T]`。

若合法候选池的输入全部可见，`C_t` 可以从其允许输入估计；**`b_t` 包含未来响应，不能偷偷从 final targets 计算**。一个 source-trained 小映射 `T_psi(z(H),s)→b_hat_t`（或直接预测动作收益）可从付费响应几何与当前残差估计它，选择 `argmax_k [2 delta_k^T b_hat_t-delta_k^T C_hat_t delta_k-cost_k]`。cost 的单位转换/多目标约束需由实际用途预定，不能任意减一个计算秒数后称为 assay 效用。公式若扩展到完整非线性模型只是一阶/二阶近似，需验证余项，不能保留“精确”名义。

**最强普通等价：** 忽略二阶项就是更新与目标梯度的对齐；二阶项是熟知的局部风险二次式。学 `b_hat` 是上下文元回归/任务嵌入，直接学 `V` 是 contextual bandit。GLISTER/GRAD-MATCH/Task2Vec 已占据其关键环节。若 ordinary direct encoder 也产生同样有效的 `phi`，world 模块没有必要。单独把 unsigned Fisher 换成 signed residual cross-moment 也不够新。

**唯一尚可证伪的领域假设：** 在限定细胞干预任务上，少量实测响应的某个具体、固定的功能表征，能在相同模型起点与信息预算下，比 raw 同信息强策略/普通任务嵌入更稳定预测 `b_t` 或更新价值。它允许表征丢失准确预测响应所需的信息，却仍保留某个小菜单的更新排序；`预测结果充分` 与 `决定哪种更新有利` 不是同一个命题。但这是尚无证据的归纳偏置/transport 假设，不是已知的生物结构或新算法。

目前不能给出该表征的具体生物等变性、可验证的机制不变量或未被前驱涵盖的推导。因此它没有满足“实质前驱差异”；**新核心资格 NO-GO**。若最终一个小 bandit 足够实现真实表征优势，可保留表征贡献，删除不必要 agent/新RSI算法主张。

**必要模块只有：** 共同且合法的功能响应/直接模型特征；少量真实不同的普通更新；一个 source 学得的价值估计器；冻结 audit 与完整成本。LLM、多代理运行时、memory archive、动态 rollout、代码自改、无限递归均不是该机制的必要模块。继承保存的是 `psi`，是否提高后续改进要另测；存盘本身不是收益。

## 值得先实际检验的机会诊断：先有可靠可用的任务×更新交互

以下是需新任务合同另行注册的实验逻辑，**本阶段不执行、不预定数值门槛**。

### O1：动作价值是否稳定且值得选择？

每个诊断任务 `t` 克隆共同起点 `s_t=(theta,D,H,program,permissions,budget)`，对有限菜单每个动作执行真实更新，收集其 dev 风险收益 `V_tk`。这些全部是 source/development任务，不是 final audit。identity、普通全量重训、固定 replay/regularization 都保留，失败动作和计算均计费。若预算不允许 source 中比较所有动作，则采用预先随机分配动作并记录概率；不能事后把缺失收益当已知标签。

先检查一个固定更新是否已普遍最好。最优任务路由对全局固定最优方法的有用空间是 `E_t[max_k V_tk] - max_k E_t[V_tk]`；直接从同一 noisy matrix 取 max 会夸大它，不能作为可用 headroom。

最小反过拟合诊断：source任务中预先定义两个合法、同目标的 dev评价块A/B，在A选 `k_t^A` 与全局 `k_global^A`，在B评估 `O_AB=mean_t[V_t,k_t^A^B - V_t,k_global^A^B]`，再交换A/B。所有动作从相同 `H` 更新，A/B都不进入这次拟合。报告动作差值的区间、排名跨块一致性、跨 optimizer seeds 的变化与实用损益；若用随机不同干预组作A/B，这检验的是对该干预分布的泛化稳定性，不是独立生物重复。

有真实 replicate 的 physical sample/well/plate 才能另估测量重复性；单细胞拆两半或换训练 seed 都不能证明湿实验更新排名可靠。不同任务的比较仍按 donor/独立细胞context等预定单位配对，不能把细胞、剂量或 action 行数当 task 数。

**O1停止：** 全局单一方法在实用容忍度内已足够；交互仅由噪声/种子/样本量解释；跨块收益小于事前实际门槛；或任务级精度不足且当前来源没有足够独立任务。区间很宽是未决/资格不足，不能伪称零效应。单任务 oracle 在同块好、跨块消失，尤其应停止复杂路由。

### O2：已付功能证据是否能预测这种差异？

O1若有用，再对 `V_tk` 做严格 task-held-out 预测：同 raw `H` 的强直接 value regressor/小 bandit、普通 Task2Vec 类 probe、简单最近邻/均匀/固定最优，与候选 `phi_W` 并列。所有 source trace、标签、预算、调参、预训练权限相同；表征压缩可不可逆，不要求逐字还原，但不得创造额外已知标签。特征与 gene/program 选择只在允许 source 上决定。

预测收益不能只报 `R²` 或排名相关。必须实际用预测选动作，在未用于训练/选择的合法 dev任务块得到相对固定方法和普通策略的改进收益与完整成本；最终 audit 仍另封存。同一世界表征搭普通 bandit若已足够，应删多余 agent 模块。若同信息 raw/probe 能解释全部，不称新领域结构。

### O3：之后才有 C4 与分量归因

只有O1/O2合格才考虑后续实验：对同一 later-task 初始模型/数据/程序/可见history/预算，单换 source早期与后期 `psi`，从真实执行的更新后分数计算 C4。再做初始/继承 solver ×早/晚 `psi` 的2×2，报告世界/直接模型分支、固定策略/可学习策略、solver/策略继承和总系统收益。自然交互可分叉后续history，不能强制不同策略每轮观察相同结果；共同起点和权限/预算仍一致。joint gain不要求正交互，只有 synergy主张才需检验它。

普通重训、CL、AL、简单混合、同菜单程序搜索、足额调参小 learned optimizer 都按同允许反馈与实际总预算比较；source生成价值标签、选择/失败、CPU/GPU、查询和审计成本都入账。单纯在固定H上重复fit是计算，不新增实验反馈。旧/new策略必须在同起点胜，不以更强初始solver或最终best-so-far代替。C4成立可有价值，但上述普通前驱意味着它仍不自动有新算法贡献。

## 一个真实但尚不够格的候选数据源

本代理不为找新数据消耗新的大下载；复核上一阶段已保存的**作者一手 loader 与资产清单**：

- [CellFlow作者 `datasets.py`](https://github.com/theislab/CellFlow/blob/main/src/cellflow/datasets.py) 的 `pbmc_cytokines` 明确12 donors ×90 cytokines，处理为单细胞RNA响应。已保存body SHA `faac0b7e21f2df7627a75ce5186fb10a5e94b6c0cb196df1dd6ee7d84c3d120f`，与原HTTPreceipt重新核对一致。
- [theislab/cellflow-datasets](https://huggingface.co/datasets/theislab/cellflow-datasets) 清单核到 `pbmc_parse.h5ad` **13,101,592,422 bytes**，LFS对象 `c72671b36248b82c559211a28fbf009f4f077e3b2097f9ba6a04d27d27edd4c9`；清单body SHA `a05ac3bf9d07a0e56934648790462776b4307aa34ff41f37ac348feed729c58b` 与原receipt一致。没有下载h5ad或读取任何表达数值。

具体、诚实的应用仅是：**新donor的免疫调节刺激RNA响应预测适配**，选择哪种普通更新更有利。它可以作为静态干预世界/后续适配的代理终点方法学，但这里是 cytokine而非small-molecule drug，RNA而非已测疗效/viability，不满足完整药物发现应用。不能把它写成药效发现验证。

任务独立单位最多为12 donors，cell types/cytokines在donor内嵌套；响应/付费揭示应按真实 physical intervention group及其共同测量输出定义，不能按每个cell免费query。当前metadata尚未核 physical sample/plate/replicate、控制组匹配、缺失、可用celltype及任务三分后数量。即使百万cells也不能制造充分later-task功效。

因此该源只是**source-only机会诊断的待资格来源**，不是现成可执行C4/药物发现数据合同。若没有独立 replicate，只能测对干预分组的泛化/优化稳定性，不能声明生物更新排名重复性。若缺乏足够donors支持独立source/selection/later，停止其confirmatory C4资格，而不是把不同文件/细胞type当独立donors。任何预训练world都需排除later donor/目标响应，不能借公开预训练权重绕过隔离。

若另一数据审计代理核得更适合的真正功能来源，应先按其原始group、开发反馈和独立task数量重新写合同；本稿不读取或预先认可其新稿。更换来源也不允许重开AZreserve或给旧暴露结果新名字。

## 必要性与停止的总判决

| 需要证明的事实 | 当前地位 | 在何时停止 |
|---|---|---|
| 不同普通更新有稳定、实用的任务间价值差异 | 未测；优先O1 | 单一更新已足够、噪声主导、任务单位/精度不足 |
| 有限paid功能表征能预测这种差异 | 未测；O1后才O2 | raw/probe/小bandit/简单检索解释全部；额外标签/计算解释收益 |
| world而非同信息直接表征有必要 | 未建立 | 强direct＋相同策略匹敌；不强留world标签 |
| 后期改进器从共同起点更有效 | 未测；O3 | swap不胜，收益只来自更好起始solver或额外反馈 |
| 一项实质新机制/算法 | **NO_NEW_CORE** | 当前关键步骤已普通归约；不堆复杂模块救新颖性 |

**独立建议：** 不提出两个貌似创新但同义的框架；0个新核心通过。可以继续metadata/provenance资格与实际跨立场评审，选择一个明确的source-only普通更新机会诊断作为未来注册候选，但本阶段不数值执行。只有数据合同、任务级精度、强普通对照和实用门槛均预先写定，才有理由运行；目前不授权大数据下载或新模型搜索。

