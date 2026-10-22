# 独立支持方：最小 PRISM 同化合物 profile 更新机会审查

2026-10-22。依据根代理给定的拟议合同，先独立保存本稿，未读取本阶段其他评审新稿。本阶段正式协议尚在编写；第一次目录核查时两个新phase目录尚不存在，`rg`报路径不存在，未因此访问替代数据或旧数值。本稿没有新GET、生物数字读取、拟合、provider调用或旧阶段改动。此前元数据结论只按根已给事实使用，不将其冒称本代理本轮重新核实。

## 判断

**有实际价值、足够简洁，适合在严格资格门后做普通更新价值机会诊断；不是新核心、世界模型或RSI验证。** 两个固定X1 whole-pool反馈，预测其余18个pool的X2/X3，构成明确的有限观测profile completion。它能先检验：同样已付反馈下，更新是否比冻结预测更好；一个全局普通方法是否已足够；不同化合物是否稳定地需要不同更新。只有这三问有实用正证据，才有理由研究source训练的可迁移selector。负结果也有清楚用途，不必依靠LLM、多代理运行时、动态world或代码重写。

当前只支持**conditional released/transductive catalog**中的更新机会，而非independently normalized biological repeat、前瞻新pool实验、held-out cell-context泛化或药效发现。later轴是新compound/chemical groups，同一固定481-context面板；source/target共享context不是错误，但必须如实描述。旧anchor与AZ停止记录保持不变，新metadata合同不能自动repair旧STOP或宣传fresh confirmation。

## 拟议合同中已经清楚且应该保留的部分

- 限定HTS002、exact2.5µM，481固定context slots/20pools；元数据/header/STR/identity资格与finite资格分开。1279等既有上限不是本阶段已合格任务数。
- 35compound plates按`SHA256('prism-profile-20261022-v1|'+plate)`固定排序，前7test、接7dev、余21source。dev移除与test parent或exactMurcko相交，**包括empty scaffold**；source按dev/test**原始全部heldout**chemical groups purge，不能先删不利heldout后把它们重作source。
- 两个paid pools全局按同seed的`|pool|`哈希固定，不随化合物或响应改变；每method收到同样完整已付X1 pool输出。audit为其余18pools的X2与X3，分别评价、不先collapse。
- 不使用primary标签或外部checkpoint；共同起始模型和source covariance/检索库只从source chemical响应构建。metadata存在于primary不代表某模型已训练过，但本合同明确排除相关标签，最容易审计。
- 两个paid pool是两个physical pool-profile acquisition blocks，不能按单cell scalar免费购买。catalog计费与真实wet-lab成本分开，控制/失败费用未重建不填假数。
- 第一coverage门属于feasibility：paid每pool X1≥80%finite，audit X2/X3各≥80%，test候选总体保留≥70%，且6/7testplate各≥10合格compound。没有iid CI或功效承诺；完整panel失败只STOP该完整配置，可以保留partial-catalog用途，不能事后换pool/plate/compound救门。

## 正式协议需要先消除的几个歧义

这些是最小合同的明确化，不是建议添加架构或新的探索分支。

1. **audit 80%的分母。** `X2/X3各≥80%`若指每个rep在全部18audit pools的context总分母，应写明；它不保证每个pool都有80%，甚至可能有整个pool缺失。若要每pool门，则必须事前明确那是不同且更严格的门，不能看finite结果后切换。至少记录每rep/per-pool计数、预定context与完整denominator，禁止把不存在/缺失context静默缩掉。
2. **通过6/7后第7plate的角色。** 建议所有预定testplate及其所有合格compound仍进入既定报告，不因为低于10而被排除；若某plate零合格，七plate宏如何定义必须先写，不能悄悄变成六plate或仅好plate的estimand。资格分母保留全部nominal候选，并逐plate报告留存和排除理由。
3. **source/development的replica权限。** 只source chemicals还不等于明确source X1、X2、X3哪些可训练。最小清晰选择是source X1构建起点和更新统计，dev X1给同paid反馈，dev X2/X3合法选少量固定超参/最佳固定方法；若source也用X2/X3，必须同供所有对照并计费，不能隐含当额外免费训练标签。根最终合同应只选一种。
4. **missingness先于预测的访问合同。** prefit资格允许读取test audit的finite布尔掩码时，目标不是完全未接触：这是一个按预定missingness合格的conditional panel。应隔离finite-only资格代码，不输出响应强度/损失，合格名单与方法预算随后冻结，再训练/封存预测；最终值才评分。不能说未使用任何test信息，也不能按效果/QC强弱选panel。所有被筛掉候选的已尝试paid/audit信息仍记成本。
5. **化学与plate依赖。** parent/scaffold purge是任务阻断，不建立盐型/处理等价。此前metadata图把parent/scaffold/plate同时OR后成单连通，只能解释依赖，不能将一个连通图硬称独立N=1279或N=35。七testplates是很小的内部panel，no-iid-CI立场合理；若要将来确认性精度，需另有合适独立单位，不在本pilot伪造。

这些问题已通过直接消息询问根，当前稿在未收到具体最终文本时保留为待决，不替根默默选分母。

## 最小普通方法足以形成真正问题

共同起点为仅source训练的固定chemical/context direct predictor `f0(c,l)`；未来task `c` 的已付context集合`P`是两个whole pools的全部允许观测，audit集合`A`是其余18pool固定context。所有方法从同`f0`与同`H_P`出发；不足finite的规则统一，不让个别方法独享更有利panel。

1. **冻结chemical direct/no update**：`f0_A`。这是起点和信息增加价值锚，不能冒充最强同反馈基线。
2. **constant residual offset**：`f0_A + alpha * mean_P(y_P-f0_P)`。`alpha`只用source/dev预定；为避免pool大小决定权重，可固定先每pool平均再pool平均。它是合法且极廉价的MSE/MAE校准动作，但不改变同task内部排序，不能用来制造top-k决策机会。
3. **source residual covariance conditioning**：`f0_A + K_AP (K_PP + lambda I)^(-1) (y_P-f0_P)`，K只从source响应/允许残差构建，regularization固定。化学起点在source过拟合后直接计算残差会影响K估计，应事前定义是source交叉拟合残差、普通profile协方差还是其他一种，费用透明；不能根据test挑定义。这里只是经典条件线性预测/正则更新，不是新world算子。
4. **source kNN profile transfer**：按同paid残差或预定source空间找邻居，平均其audit residual。距离、k、mask规则只source/dev确定；source库与全成本共享，不把test其他未付pool放进距离。
5. **同反馈强直接 predictor**：训练输入必须含同两paid whole-pool观测、缺失mask与chemical/context特征；可用source pseudoepisodes模拟该固定paid/audit模式，直接预测剩余18pools。只给direct化学特征、却给cov/kNN paid响应是不公平的弱对照。若它以普通回归同预算解释全部收益，停止world必要性/新operator主张，保留普通completion结果。

这些是固定小菜单，不需要LLM或controller。源chemical数量与计算预算决定是否可运行，不能只匹配最终一次fit，却漏计K、检索库、源pseudoepisodes、调参/失败。source covariance在固定context面板上可能已经是一个有效静态world组件；这个名称合法但不增加信息，也没有自动新颖性。

若日后增加普通full retraining/CL/AL，须确有相应数据序列/query合同并同预算；当前单次两pool feedback不该硬塞多轮AL或把重fit叫新实验。当前也没有procedure inheritance或更强later improver的测试。

## 哪些指标能合法回答机会问题？

### 基本终点：先固定一个预测损失

建议正式协议选一个主损失，如released log2 fold-change的MSE；自然单位是`(log2 fold-change)^2`，不是药效、死亡率或hits/64。MAE可作为完整报告的次要稳健性诊断，但不能主项失败后改宣MAE成功。R²/相关可描述，不能在低方差profile中当可靠实际收益。

对每个compound c、audit replica r、pool p，先在该固定pool有限共同context上算损失，再对18pool等权（前提每pool可评分合同明确）；再按compound与预定plate宏汇总。pool等权避免不同pool cell counts隐含决定终点；若选择context等权也可，但它是另一明确estimand，不能事后换。所有方法用相同qualified mask，不按其预测/模型删行。

`V_cr(k)=L_cr(f0)-L_cr(U_k(f0,H_P))` 为普通更新价值。X2/X3均用同一次冻结prediction，分别列`V`和差值；两rep共享ComBat/control/可能stock，不能视为两次独立生物重复。主损失及是否plate等权须在值打开前定，不从test变异选择。

### 机会O1：是否值得在task间选择？

先报告每个固定更新相对冻结起点、相对**dev选定最佳固定方法**及同反馈强direct的收益；如果一个普通方法普遍足够好，selector就不必要。不能只跟最弱no-update比较。

`mean_c max_k V_ck - max_k mean_c V_ck`的同表hindsight gap会乐观。可把X2上逐task选择的动作放到X3评分，反向也报，tie顺序固定；主比较仍用dev选定fixed，另列test hindsight best fixed作描述。这里的X2 chooser读了隐藏结果，是**不可部署的诊断**，不是合法features策略，也不是潜在真实oracle或所有可行selector的上界；失败只停止依赖该chooser的扩展论据，不能证明所有selector不可能。

同时报告同task各动作差的方向/排名稳定性、ties、反转、两方向净loss收益与每plate结果。rank correlation本身不够，必须实际净损失收益达到源用途预定的实用尺度；本稿不搬用AZ .02、旧 .1875 hits或其他assay阈值。只有七plates又有化学依赖，当前无需伪CI/power；描述稳定并不自动满足确认性显著性。

### 下一步边界

资格门通过可以证明这个固定catalog具备可评分panel；普通方法有收益可以证明有限反馈更新有用；跨rep chooser有收益也最多提示当前conditional任务的选择机会。三者都**不**证明合法history可预测更新价值。需要之后source/dev训练的小selector、在untouched future compound groups只用paid fields选择动作，才检验可部署预测性。

后期psi相对早期psi在相同起始模型/程序/数据/初始history/权限/预算上更有效才是C4；当前机会诊断不是C4成功，也不是C4失败。world、agent、solver/policy inheritance与总joint需分别消融，joint不要求superadditive，静态functional world不强制时间动力学。

## 覆盖门的精确意义与STOP

预定80%/70%/6-of-7×10是一个可审计的完整panel可行性门，**不是充分功效或生物学有用性证明**。根的设定可以作为一次bounded资格检查；本代理没有数值证据建议调整它，亦不建议失败后加pool/换plate。

若未通过，STOP该完整panel配置、不fit；保留逐pool/compound/plate缺失和已付费用，partial catalog另有描述用途但不能自动复活本性能实验。若资格通过，再按新冻结的最小方法与预算做机会诊断，不因上限大而跳过commonmask/强direct。若同反馈强direct或固定普通更新已经解释全部，停止world/selector新颖性路线；若普通更新无实用收益或跨rep选择不稳定，停止该菜单chooser投入论据。区间/样本不足则称未决或资格不足，不宣布所有更新无效。

**当前支持结论：** 这是一项具体、合法scope内有价值的普通研究机会，比抽象world+RSI框架更可证伪；在上述分母/rep权限/起点/强对照明确后，可支持先执行coverage-only资格门。没有新核心通过；没有授权本稿启动响应读取或fit，等待正式协议与实际交叉。
