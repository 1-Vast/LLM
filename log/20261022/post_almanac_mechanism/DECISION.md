# 新近邻与两个具体操作的研究决定

2026-10-22。完整目标 ACTIVE / NOT_ACHIEVED。本轮 **PROGRESS**：新增已认证2026直接近邻、官方实现合同、一个真实API候选、两项先写协议的精确检查，以及实际独立/交叉质疑。没有新的生物性能或可晋升的核心机制。

## 当前证据与不变边界

上一轮ALMANAC普通直接RBF的功能反馈MSE收益保留；同study排除后排序恶化也保留。该轮anchortransport novelty/RSI扩张STOP未重启，没有添加纠偏菜单或打开后20cell。decryptE蛋白增量/CDK组成/旧守恒、梯度重组、bracket和continuation等限定STOP保留。本轮不以相关的普通适应成功推定世界模型、agent或RSI必要性。

## 新一手证据改变了最近对照

- **AssayLoop，arXiv2609.11877v1**：作者已经跨历史CRISPRscreens训练反馈条件的实验选择策略，AssayFormer监督训练后用GRPO，AssayLoop与LLM早期先验组合，AssayLLM另有直接后训练。因此“继承会看实验反馈的策略”不是当前新机制。1349训练/20验证/20测试及作者性能只是原文报告，未在本项目复现。公开README另有更大默认split；作者论文20+20子集按响应统计和LLM表现筛选，不能称元数据盲的随机前瞻人群。原文、版本、读取边界与官方README在frontier/。
- **AR-BED，2610.20832v1**与**DABS，2607.16927v1**分别已有外部生成模型的信息奖励摊销设计、spike-and-slab解析边缘化加自适应筛选。改成药物目标或放松强heredity先验，不自动构成不同操作。未复现作者实验。
- **State正式发表信息**已由EuropePMC核查为2026 Cell DOI10.1016/j.cell.2026.07.052；官方README的downsample_cells可按干预组封顶。因此至少启用时输入组数量不等于实验绝对存活量。仅条件状态分布缺少mass仍是真实观测缺口，但加counthead/联合似然已有忠实普通实现，本轮无新算子或新反馈合同，不换名重启质量锚点路线。
- DGM已有固定modifying-metaagent对照，SICA已有archive最佳agent作editor及时间/成本utility。普通metaoptimizer可以有真实Level3能力；是否超过第三方强普通方法是额外方法贡献比较，不是Level3定义本身。新common-start对照需允许双方利用相同源traces，不能削弱普通优化器。

## API矩形约束候选：实际精确检验后STOP

一次deepseek-flash请求提出CCI：将四格交互b=y11−y10−y01+y00变成容差约束，对低维rule做最小位移投影，以coveragebandit选择下一条约束并继承通过模式。原request/response/usage完整保留。biology与skeptic先分别封存API_REVIEW，再实际双向挑战；frontier后审范围另记，不当作第三份完全独立初稿。

ROOT_MATH_PROTOCOL先于执行。root用Fraction独立实现候选normal-equation投影与完整普通KKT求解，2×2、2×3、3×3的 **21个精确案例一致**，另 **63个单slab案例**通过可行性/法向最优条件。不是任意非线性rulegrammars等价定理。最强faithful对手须相同rulefamily/r0/contrast/epsilon的**硬约束QP/投影**及相同覆盖策略；有限惩罚softloss不必等价，不能用它充当唯一对手。

精确nullspace反例显示additive主效应可改变MSE/单药排序而不改交互证书。它只否定“零证书自动保证完整功能”，不否定交互约束有用。正面条件也核验：三corner已知且contrast确定时第四corner可识别。四格独立等方差噪声对contrast方差乘4，共同offset抵消；真实共享控制协方差和成本需单独认证。缺一格、只一条边差分并不能无条件认证交互；vehicle不是凭空0，归一化1不是新独立测量。

覆盖表使下一轮更快也可能只是已覆盖内容/更好初始rule；须重置下游起点比较改进策略。善意解释C_t为全部observed约束，预设合法epsilon调整可以接受，STOP不依赖挑最差歧义。**STOP_LITERAL_CCI_CORE_PROMOTION**：当前无超出上述同操作普通对手的具体差异，不启动生物拟合、不把ALMANAC已停路线换名打开。

## AssayFormer奖励：新增可验证问题，常规修复也已在作者实现中

原文Methods4.5称每步reward为actualhits减context-free参考在同remainingpool的hits，并以剩余回报作优势。frontier先执行4候选/3步deterministic反例：labels(0,1,0,0)，actual A=(0,2,1)找1hit却reward−1，B=(2,3,0)找0hit却reward0。原因只有actual候选被删，参考可重复比较同项。

skeptic挑战参考随机性，root另先写ASSAY_REWARD_PROTOCOL，再用严格正权重PL参考(10000,100,1,1)做精确期望：A预期reward−25507499/26017701，B为−153045301/5153035251，仍严格反向。24条轨迹验证terminal-zero potential的望远镜恒等式。frontier另有finite-logit例。它们只检查显示的目标结构，不是作者训练权重、GRPO有限组优化、湿实验或性能复现。作者AppendixB明确terminal-EF ablation反而较差，必须保留：目标一致性并不保证有限训练效果更好。

root随后只获取官方GitHubtree与一个89KB训练源文件，2HTTP200，保存tree及精确gitblob校验。固定版本rl.py的context_delta分支实际上使用**deterministic topk参考**（459–463），与actual共享obs_mask、只删除actualchoices（469–470）；剩余回报递推在499–506。初始deterministic反例对应这个branch，但未执行作者代码，也未认证发表checkpoint具体采用哪配置。代码同时早已含 **telescope默认模式和nvr_terminal模式**（334–350、474–480、494–497）；因此“改为标准望远镜奖励”不仅是常规操作，还是作者自己的现成实现，不能申报我们的算法贡献。需区分当前pinned源实现与论文实验版本。

frontier与skeptic又分别静态复核官方代码并实际互答（OFFICIAL_CODE_REVIEW/CROSS）：望远镜在gamma=1时，无warm为finalNVR，有共享warm为finalNVR减共同initialwarmNVR；gamma≠1不能泛称相同无折扣目标。group标准化、clipping、KL/entropy和辅助项使路径reward顺序更不能自动推出梯度/最终性能。两个源码评审都未运行作者代码。

**VERIFIED scoped mathematical objective mismatch；NO_NOVEL_REPAIR_PROMOTION。** 这是更准确的强对照和后续研究约束，不能据此宣称复现推翻作者效果，也不授权立即下载CRISPR标签/启动又一生物pilot。若未来提出真正不同的价值估计操作，需同这些已存在模式/普通Bayesian设计/强direct取得有限总成本优势；本轮未提出。

## 下一行动与完整目标

本轮NO_CANDIDATE：一个矩形投影候选被具体同操作普通对手解释；一个奖励问题被发现，但最直接修复已有。停止这两个字面创新扩张，不扩大玩具、调整epsilon/矩形库或接上新editor追求表面新颖性。反证不等于所有元学习/硬约束/世界模型无创新空间。

下一步必须是一个具体不同的可执行学习/估值操作及真实功能合同。AssayLoop已经提供反馈规则迁移近邻，故若沿此科学任务，应优先研究在偏差/稀疏反馈下估计“模型修订对后来实验的真实增益”的技术缺口；尚无估计器，不把缺口命名为方案、不直接做数据资格长流程。候选若需要额外counterfactual标签，普通对手也应获得并计价。

Level3能力测试应冻结前后improver，从相同新下游模型、初始archive和外部历史起点，在独立later任务比较有限预算下后代程序utility曲线。普通learnedoptimizer可满足该能力；新颖性/有用增量还须强ordinary与等预算search对照。源期和部署成本都计，匹配utility的摊销条件为NΔc>ΔCtrain（不是永远把普通对手源成本当0）。当前没有此真实结果，也没有WM独立、agent、继承或联合收益。完整目标仍未达成。

## 过程与资源范围

三native立场（frontier使用请求可用的gpt-6-astra；另外两者为复用nativeagent，不虚报其具体权重身份）。frontier封存前收到skeptic一条一般性结论消息，故不是完全隔离；skeptic完整外部目标是在初稿seal后补读并以新addendum披露。独立原稿与追加澄清均保留，实际交叉问答不按多数投票决定科学结论。

API实际1逻辑调用/3930reported tokens（550prompt、3380completion）/23.563秒；transportattempt数由client不提供，美元计费不可得。root2公共HTTP，frontier7，biology4，skeptic3；各角色receipt为准，不把重下载旧primary算新发现。无生物响应解码、无数据/权重下载、无预测模型训练、无湿实验。数学代码由root/agent针对明确检查手写，不是执行API生成代码或作者代码。

失误包括root提前读取不存在旧recursive_operator DECISION路径、Windows glob传rg失败、单行primary文本导致过量输出；均未据此读取数据或修改旧证据。各角色提取失败另留原记录。所有新代码research/，来源、API、推导、质疑和失败log/；src/tools未改，旧导航dirty不清理，历史三provenance漂移未修复，本地绑定不宣称全局完整性。所有protected reserves保持关闭。
