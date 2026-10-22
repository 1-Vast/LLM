# 独立机制支持方：先锁定可被推翻的时间修复操作

2026-10-22，Asia/Shanghai。角色 `mechanism_advocate`。本文件初始立场在读取本轮反方文件之前落盘；后续交叉意见仅追加。本代理读取既有公开历史及 OASIS/TG-GATEs 元数据，没有打开 DNA/LDH/CEL 响应值、未选药、未训练、未调用 DeepSeek。

**初始判断：没有已建立新颖性的核心机制，不批准搭建新架构。** 但并非从“直接模型可以表示任何函数”推导无研究机会。我保留一个具体、可证伪且很小的归纳偏置候选，先查它是否有可识别的数据机会及直接先例。它不是第二个泛化框架，也不把一轮普通重训练命名为 RSI。

## 唯一候选：由时间切面残差推断可迁移的暴露时钟修正

具体用途：在已由前期存活率筛选的持续暴露剂量菜单内，为新药族选择有限的早期分子/功能测量，使 24 h 肝细胞功能复核排序更可靠。它不发现任意剂量、不推断临床 DILI，也不设计 TG-GATEs 没有记录的 washout、rescue 或序贯换剂量。

最小世界模型写成 `z(t)=T_theta(z0,a,d,t); y(t)=h_phi(z(t))`。在 paid support 表明某药/任务存在系统时间残差时，只新增一个可检验更新算子：`T'(t)=T(g_eta(t))`，其中最简单 `g_eta(t)=exp(eta)*t`，然后由同一修正后的状态重新计算全部相关 readout。`eta` 必须仅从当前已购买的支持观测拟合，不能利用未查询 24 h 目标。其操作区别是**修改有效暴露时间并共同传播到未测时间/剂量与功能输出**；既不是逐端点 offset，也不是把观察到的功能值重复计作新命中。

核心假设不是“存在真实通用生物时钟”，而是窄的统计输运命题：某些可诊断的预测错误具有近似共享的速度/延迟结构，相比独立幅度/功能头修正，单自由度时间修正能更有效迁移到同任务未测时间和剂量，并在后续药族复现。若不同剂量/输出需要互相冲突的 eta，或者时间模型没有非线性可分辨曲率，此假设即失败。初始模型偏差、batch、培养来源、细胞组成及测量漂移都可能伪装为时钟修正；只凭持续暴露观测不能把 eta 解释为药代、通路速率或损伤因果机制。

**Agent 的最小具体动作**是同一冻结 `T,h` 下在真实允许的 `(dose,time,assay)` 菜单内，购买能使 clock / amplitude / head-only 三种更新之后产生不同最终 24 h 复核排序的支持观测；随后根据该观测选择受限算子。若三者对实际候选的排序完全相同，停止诊断，不花预算。比较对象不是被禁止调整的弱静态模型：固定时间/剂量 SOP、直接测功能、uncertainty sampling、普通 knowledge-gradient/model-discrimination 和同一候选族等预算程序搜索都获同样菜单与先验。这使假设可以输；“会询问不同实验”本身没有技术贡献。

**继承内容**只能是确有增益的诊断/更新规则，例如何种已测时间残差使 clock correction 值得测试、选择哪个可用切面、何时退回普通重拟合。继承一个更好的 eta 或模型权重只算参数迁移。诊断规则必须是可执行程序并在新药族共同模型起点重放。**RSI** 另需共同 `p0,theta0,history` 下的旧/新 meta 对未来同 k 次修订提案进行比较；所有源任务拟合、失败查询及形成 meta 的成本另计。只更新 eta/selector、或复用固定 rule，不是递归改进证据。

## 为何保留，但目前不晋级

支持理由是该操作小、易被时间残差证伪，能把“模型有误”落实到一个改变未来预测的参数化动作，而非增加自由潜模块。它可能减少低样本更新的方差，并给 agent 一个真实的 acquisition 区别。如果它比强直接模型有用，必须表现为相同监督/查询/计算下的未来功能决策效用；不要求从逻辑上排除直接预测表达它。

反对理由同样直接：时间重参数化、kinetic alignment、参数化系统辨识、multi-output fitting 和 learned optimizers 都是成熟做法。“残差诊断+选更新算子+继承规则”也有既有自改/元学习先例。目前**没有独有操作优于这些方法的证据**。本候选只是将一个特定可检验的共享误差结构落实为极小更新算子；这个应用归纳偏置是否足以构成新贡献，尚未成立。

TG-GATEs 的 156 个同 compound-dose-unit 2/8/24 h 条件（52 药）只保证身份重叠。跨时间是破坏性样本，不能组成真实单细胞转移或同一培养轨迹；sample-to-lot 未认证。只有三个时间点时，clock、amplitude 与 head drift 很容易不可区分。若最高剂量正是用 24 h 相同功能预筛而来，所有模型先验已含选择反馈，适用范围必须条件于该菜单。尚未认证的 DNA/LDH 完整性也不能由身份推断。

因此，以下两种情形都足以在分子下载前关闭：①需要真实切面支持但 functional/expression 身份无法对应；②保持所有先验一致时，仅靠时间/剂量标签和普通更新已经覆盖实际决策差异，clock 与替代更新在可获得菜单上不可区分。反之，元数据通过只允许预注册 dev 数值信息资格，不能直接批准架构或 novelty claim。

## 必须同信息比较的实验

| 归因 | 最小强比较与否证 |
|---|---|
| 时间状态/世界模型 | 同化学、剂量、时间、早期 paid state 的直接功能 predictor；相同全部辅助分子标签的直接多任务/conditional predictor；状态转移无 clock 与 clock；容量/正则预算匹配；简单 kernel/multitask+blend。预测状态与功能效用分别报告。 |
| 更新 | 固定同支持集的 ordinary refit、continual regularization、offset、amplitude、head-only、joint-fit 和标准 time-warp/kinetic system identification。若后者匹配，则不属新 update mechanism。 |
| Agent | 同一模型/更新族/初始历史，fixed SOP、直接功能测量、AL、KG/Bayesian model discrimination、random/BO/program search；同 query、候选程序、评估/计算/API budget。候选不能独占跨时间监督或损失。 |
| 继承 | 新药族共同起点，weights off/on × procedure off/on；同历史 restart、case retrieval、fixed distillation、常规 meta-learning。只要 fixed rule 匹配，就停止程序特异收益主张。 |
| 联合 | world/direct × adaptive/conventional；联合系统必须赢过最强常规完整系统，交互为正而绝对效用低不晋级。 |
| RSI | 冻结 m0/m1，从相同 p0/theta0/history 提议和评估 k 次修改，再在未用于选择的更后任务裁决；进一步 m1/m2 比较。若只提高起点、候选数/预算或查询增多，不能归为 RSI。 |

结果前须另锁定具体 endpoint、合法复核动作、化学分组、功能损失/效用、预算与实际有用差 `delta_use`。本代理未见数值，不擅定一个易过的 margin。若可达效用差上界低于 delta_use，停止；区间过宽为未决；不能改主指标续命。G0 信息失败时只关闭该配置，不扩大为所有世界模型无价值。

## 本轮证据和访问边界

先前独立审查已精读/核验的 Hyperagents、AIDE²、SpecRSI、VCLMU、Deep Adaptive Design 及 Deep Adaptive Model-Based Design 均是新颖性直接障碍；本轮不把同起点 meta 比较或 editable program 再据为贡献。引用层级沿用 [旧独立审查](../../20261021/autonomous_rsi_round1/NOVELTY_ADVOCATE.md)，本轮并未重读它们全文。

本轮新增 primary-source 检索、原始返回、URL/hash/status/bytes 与 TG 方法段保存在 `advocate_sources/`。第一次欧洲 PMC 搜索返回 HTTP 503；简化请求后成功。首次失败 body 在重跑时被同名结果覆盖，故不能声称原始失败 body/hash/bytes 完整留存；工具控制台保留 HTTP 503 与 URL，`INITIAL_FETCH_FAILURE.json` 记录此缺口。成功请求的原始body与URL/hash/status/bytes以实际文件为准；本代理脚本未保存响应headers。这不是科学阴性或配额拒绝。

## 交叉辩论（待独立反方初稿后追加）

反方在本稿前只发来问题：持续暴露而无 washout/rescue 的菜单如何识别修复对象、实际决策如何超过预筛 dose 先验？我已回复本稿的唯一候选仅为统计结构假设，不声称修复对象被因果识别，且当前 NOT_NOVELTY_ESTABLISHED / 不批准架构。未读取其独立立场，不把问答预告算完整辩论。

## 一手证据追加及最终新颖性裁决

以下新增检索使用 Europe PMC 返回的作者论文摘要/元数据；fullTextXML 条目标明实际精读范围。数据库摘要不是独立性能复现，也未声称穷尽文献。

| 来源与访问层级 | 核验内容 | 对本候选的实质约束 |
|---|---|---|
| Aach & Church, 2001, [Aligning gene expression time series with time warping algorithms](https://doi.org/10.1093/bioinformatics/17.6.495)，原始摘要/元数据 `time_warp_primary.json` | 明确不同实验/个体共同生物过程速度不同，RNA/protein 曲线 time warping，测量噪声/样本量和 concentration warping。 | 暴露时间放缩/可迁移曲线对齐本身已有非常直接先例；不能靠 Agent 调用同一操作获取新颖性。 |
| Zhang et al., 2013 online/2014卷期, [TG-GATEs early-response network](https://doi.org/10.1038/tpj.2013.39)，本代理摘要；随后读取反方取得的 `skeptic_sources/EARLY_TG_FULL.xml.txt` 方法/结果段 | 同药持续暴露，2/8/24 h gene expression/PicoGreen DNA；按 progressive profiles 找 2 h signature，并建四基因 Boolean-network 动态。in-vivo SVM 则是另一项预测设计。 | 早期状态预测后续 cytotoxicity、跨时间应激网络及动态叙事均非新意。原文按表达集群/全样本定义 progressive profiles，不能直接移作化学组外无泄漏基线。原文性能未经复现。 |
| scNODE, 2024, [10.1093/bioinformatics/btae393](https://doi.org/10.1093/bioinformatics/btae393)，全文XML；重点读模型、dynamic regularization 和实验设计 | 不同时点不对齐的细胞群；VAE/ODE 联训与 Wasserstein 动态正则，插值/外推；原研究数据>10时点。 | 未对齐 snapshot 学 latent dynamics、由时间误差同时修 representation/dynamics 已有；不能套其高时间分辨率的可识别性到TG三个切面。 |
| Lorch et al., 2026-10-08, [LCD-CLIPR](https://doi.org/10.1073/pnas.2602630123)，全文XML；重点读模型、stationarity、CLIPR linear-drift段和结果解释 | 观测噪声下的 latent stationary diffusion；以扰动初始/终态响应线性化 drift。作者定理的线性漂移、稳定性等假设明确。 | state/measurement分解与动态扰动传播已有具体算法；其stationary/干预假设并不由TG持续暴露菜单满足，不能借用“因果”标签。 |
| [A world model of the virtual cell](https://doi.org/10.1016/j.cell.2026.08.042)，2026-09-01，作者摘要/元数据 | 持久 cellular state、动作条件转移、跨分子/形态结果、planning 架构愿景。 | 这是框架/评估愿景，不能当已验证本候选性能；宽的 world-model 架构叙事不是本项目新意。 |
| [ProteinTalks](https://doi.org/10.1038/s41586-026-11001-9)，2026-09-09，作者摘要/元数据 | 大规模时间蛋白组，transferable latent dynamics 及 drug efficacy/synergy/organoid applications。 | 项目已有对应停止的PTV复现，不能从摘要重新晋级；时间潜态迁移本身不新。 |
| [AnnFlux](https://doi.org/10.64898/2026.09.01.748703)，2026-09-03 preprint，作者摘要/元数据 | perturbation-conditioned SDE、held-out timepoint/perturbation/combination。 | 用conditioned drift区别静态预测已有；仅据摘要，不推断其功能/Agent/RSI效果。 |

本轮成功请求10次（7次检索+1次精准检索+2次全文）记录 body **1,010,421 bytes**；初始503 body bytes未知，不包括反方独立取得的文件与代理通信开销。没有数据集payload、DNA/LDH/CEL响应、GPU或DeepSeek请求。脚本仅在 `research/tggates_mechanism_review_20261022/`。

## 实际交叉辩论与关闭（后于独立初稿）

反方 `scientific_skeptic` 在其 `SKEPTIC.md` 初稿保存后阅读本稿，正式提出四项问题：①除标准 time-warp/system-ID 以外继承了什么操作；②三个不等间隔切面如何在不读24h目标时区别 clock/amplitude/head；③按真实assay bundle与返回时延计价后如何优于24h功能确认；④完整菜单48药化学分组后是否足以多阶段meta检验。

我的逐项答复：①目前没有额外独有操作或强 fixed rule 无法解释的继承预期，关闭新颖核心主张。②`f(t)-b=c*t^p` 时 clock 与 amplitude 解析等价，`f=b+c*log(t)` 时与 offset 等价；只能在预冻模型有非共线曲率且支持噪声足够低时区别。三切面不确定中间导数，因此无参数族限制时不能识别。③不把2h采样等同2h返回RNA，不假设RNA便宜；既有早期资产的条件任务合法，但主动采购必须计全成本并比较直接功能。④不能用dose/time/两个individual伪造任务数，当前没有48药多阶段meta效能依据。

我向反方反问并得到明确接受的两个边界：`f(t)=1-exp(-kt)` 等非线性曲线中 time-warp 与单一 amplitude 可分，所以三时间与旧先例**不推出所有时间归纳偏置的效用为零**；已持有早期RNA的条件任务不需声称采购更便宜，但各臂必须从相同初始资产出发。反方回复同意，关闭的是当前新颖核心而非所有时间模型。

反方随后执行了根代理授权的[开值前代数审计](clock_observability/RESULT.json)。我读取其协议与结果：单/双输出的不同 amplitude 限制给出不同秩关系，不能声称普遍等价；两个全区间单调曲线可匹配2/8/24及warp=0.5的paid 8h support对应4h，却在未测24h forecast对应12h相差0.02。该构造不是生物数据，但足以反驳无参数族限制的唯一clock识别。没有重复运行已通过的审计。

根代理要求最便宜functional-only数值反证时，我给出一个**明确有限族**而非泛化机制的备选：source化学组仅拟合endpoint×dose-level的2/8/24h pooled模板，heldout组仅买整个8h功能bundle，拟合一个eta∈[-log4,0]后预测未查询24h；与ordinary offset/amplitude、8→24 ridge/kernel、普通curve refit和完全相同的标准time-warp比较。范围只覆盖减速且避免两端越界；不能改称双向时钟。成功最多表明该预冻有限族有条件预测效用，失败也不能排除任意分子世界模型。

**最终资源决定：不运行这个pilot。** 当前即使它成功，标准time-warp完全相同操作仍解释结果，并不能提供将被晋级的新算法；如失败又只能关闭人为模板族。因此它不会改变本候选的新颖性资源决定，不值得为它消费dev数值或下载CEL。候选以 **NO-GO_AS_CORE_INNOVATION / NO_NUMERIC_OPENING_FOR_THIS_CANDIDATE** 关闭；不要求更多数据来挽救这个操作。只有将来出现与已有time-warp实质不同、可在真实行动菜单中反证的新操作，才构成新的研究提案，不能据本稿重开。

仍有价值的未决问题是“真实早期状态相对预筛/剂量先验是否有功能信息、何种测量/预算值得采购”，它可作为来源资格独立研究，但不是此候选成功、Agent或RSI证据。根代理已接受关闭，并把后续限定为寻找具有真实替代暴露schedule/washout/rescue/第二干预分支的公开身份资产；这不构成新架构批准。
