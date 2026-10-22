# 独立建设性反方：一个真正能执行的 state/function feedback 贡献

你是第三方科研合作者。请从下列已认证证据独立提出一个最强、简洁、有机会产生正结果的具体机制或经验贡献。允许使用普通组件，但必须有新的、可证伪的细胞状态/功能反馈结构；不要只否决，也不要靠换名称宣称新算法。此调用是实验性提案，不是文献/数据验证。不要编造引用、尚未观察数值或新数据源，不输出可直接执行的大型代码。

## 用户目标及本轮权限

构建以虚拟细胞干预世界模型为基础的药物发现科研智能体；可从实验反馈改变模型更新、研究程序及改进策略，能力继承至后续研究。分别检验world、agent、inheritance、joint及RSI策略本身的common-start后续改进效率。允许直接DeepSeek API及多代理；所有记录log、代码research。整体仍NOT_ACHIEVED。

## 已认证的最具体可执行资产

TG-GATEs人原代肝细胞持续暴露；condition-mean早RNA与后功能按药/剂量/时间对齐，非同细胞/同一物理培养个体配对。已冻结元数据/缺失身份审计，尚未为本候选读取真实RNA或功能数值。

- 2h→24h、两份CEL与DNA(%)和LDH(%)两个功能完整，Low/Middle/High均严格正、三个不同有效浓度的菜单是47个compound labels（不是52）。47是否对应独立parent/scaffold尚未认证。144/48是未去掉amiodarone Low=0前的相关菜单；不能混用。
- DNA(%)、LDH(%)都被官方定义为relative survival；不要把后者当原始泄漏率或推断birth/death。高剂量是80–90%relative-survival预筛或溶解度限制后选择，不能无视这个先验，也不能把标签直接设85%。没有sample→lot mapping，不能证明donor transfer。
- 每个药的最高有效剂量可作为固定target，低/中剂量为可选支持条件。需要的早RNA重复+24h功能是condition bundle，不能把它称一条廉价标量；目标剂量RNA若未买，world必须预测该状态，不能当免费输入。若给所有方法目标RNA，则是另一个合理应用，但不隔离状态预测价值。
- 在未见chemical parent/scaffold groups中预测24h高剂量DNA及LDH，仅是已预筛体外毒性确认/剂量外推辅助，不是临床疗效；47labels只支持有界small-N pilot，不能把剂量/技术重复算成新task。

## 已知阴性与邻近普通解释

- O'Neil/PRISM程序编辑没有击败固定规则/等预算搜索；PTV-1 ppODE世界不及强direct；HTS001普通增长/收缩更新被50/50混合和等预算搜索精确复现；STACK完整历史的小增益未过实用门；AZ paid-reference effect坐标不及强full direct；PRISM固定2池全板计划缺失率不合格。不能重开旧STOP或AZ413reserve。
- 最近一轮signed update价值/score chooser cross-noise增益−.361111/+ .222222 hits/64，两向门失败；这只是否定该历史score菜单，不能宣称分子反馈普遍无价值。
- TG-GATEs单eta time warp已经作为ordinary system identification且诊断不可识别被STOP；不要换名重提。
- 早RNA→后毒性已有直接先例：Zhang等DOI10.1038/tpj.2013.39，EGR1/ATF3/GDF15/FGF21四基因；动态网络或stress signature本身非新。
- LCD-CLIPR PNAS2026-10-08 DOI10.1073/pnas.2602630123已有stationary perturbation diffusion/噪声拆分/组合预测。SciAdv2026-09-09 DOI10.1126/sciadv.aed3414的13方法25数据集benchmark发现保守表达预测/方差压缩，但不自动证明毒性尾部headroom。
- Watermelon有barcode/H2B-mCherry真实proliferation-history，2cultures，但未经采样校准的sorted capture仅能做released gate条件下预测；selection/transition可构造观测等价，不能当已识别机制，2cultures不能供广泛C4。

普通模型必须足够强：chemical+dose direct；拿同样辅助RNA标签的direct；拿完整已付RNA/function/mask/history的direct；ordinary factorized f(drug,dose)→state→function；source response-kernel/learned metric/shrinkage；offset/dose-curve refit、全量重训练、continual learning、AL、简单混合、等预算程序搜索。如果f/g/训练完全同构，合并同一方法，不要求某方法击败自己的复制品。精确constructive reproduction否定该operator首创；泛NN/meta表达能力不能代替同信息/同预算实证。普通组件有效仍可能支持可重复的经验结构贡献。

## 我的先验草案（你可以替换或改进，但仅推荐一个）

核心未知不是早RNA预测毒性，而是“哪个功能反馈能帮助哪个未测高剂量”：早期干预响应几何是否决定**功能预测残差的跨条件可迁移性**，超出化学相似性、剂量、整体offset及四基因stress。用source任务学习state-dependent的两功能残差协方差/低秩修正；在later药已买一低/中dose bundle后，决定只修正function head、仅修正state branch，还是拒绝迁移。反馈可改变下一任务的更新策略，但不能用名称当RSI。

最邻近解释就是ordinary conditional kernel/多任务回归/贝叶斯更新；可能完全复现操作。因此一个有希望的贡献应精确说明：哪个未曾验证的**生物统计结构**、哪种保留/置乱/同信息控制会让它成功或失败、如何让这一发现改变实际确认决策。不要强行声称每个模块独创。我的独立稿封存前不读其他新代理稿；本prompt只含历史共享证据与本人草案。

## 必须回答

1. 只推荐一个最强candidate，明确与草案的关系，给一句非平凡可证伪主张及实际用途。若找不到新算法，明说并给最强可执行经验贡献。
2. ≤12行的精确操作；把哪些项必须学、哪些冻结、target不可见哪些写清。
3. exact source/development/later task分工和反馈单位；47label power限制，数据化学/数值/headroom门；首先做哪个cheap decisivecheck，成功/停止条件。不能读test后调门，不能把toy check当生物验证。
4. 最接近ordinary explanation和真正能否定候选的同信息对照/置乱；新颖性边界与哪些结论不能下。
5. world/agent/model inheritance/program inheritance/joint如何分别识别；如果world/direct同构需合并，给具体结构消融而非标签比较。
6. 写出RSI C4的可执行common-start合同：两个明确improvers、同later predictor/program/history/permissions/budget、改变的状态、improvement效率指标、等预算普通搜索。有限化47task不够时不得假报RSI成功。

以中文写，保持简洁、具体、可直接转为冻结实验合同。不要输出安全免责声明或虚构已经完成的结果。
