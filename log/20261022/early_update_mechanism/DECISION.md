# 更新机制续研：实际反证后的决定

2026-10-22。完整目标ACTIVE / NOT_ACHIEVED。本轮PROGRESS：新增一手算法边界、三个独立具体对象与API候选、实际交叉往返和先冻结数学检查，改变下一步研究动作。没有合格新核心、真实细胞性能或RSI成功。

## 输入及独立过程

上一轮晚期门STOP保持，不能再扩大24h输入救结果。早期E相对化学的pool信号及其不稳定fold方向完整保留；不是蛋白值单独贡献或世界模型证据。旧CDK、TG、CiPA、AZ等限定STOP不重启。

frontier/PROPOSAL.md、recursive/PROPOSAL.md和biology/INDEPENDENT.md分别在读peer前封存。三方随后实际读对方原稿、发问与答复，分别保留CROSS_REVIEW及seal；不同立场不等于不同模型权重，也不以票数证明机制失败。另有一个独立DeepSeek请求，rawrequest/response/receipt完整保留，没有执行模型生成代码。数学脚本均为明确检查的人工实现，不是新生物训练。

## 一手新边界

- TTT-Discover：2601.16175，首发2026-01-22，审阅v2。原文entropic objective、自适应KL温度及PUCT重用已是具体学习搜索机制；Pancreas上训练算法、PBMC/Tabula上测试，不能泛称没有迁移。但迁移去噪算法不自动证明改进器更会改进。作者结果不作本项目复现。
- Population Evolution：2610.05950v1，2026-10-05。原文明确weak/unsuccessful transfers入ledger并影响后来proposal context，代码继承而权重逐次重新训练。因此“继承阴性经验来改后续提案”不是本项目独立创新。
- 2610.09604v1梯度历史learned optimizer、SEAL和2610.16491v1 SpecRSI的原始全文在recursive/PRIMARY_EVIDENCE.json逐段核查，复用既有实际HTTP与哈希，没有重复下载。下游loss训练更新器、同artifact换改进器等已有直接先例。
- Titans首发2024-12-31，不能因2501编号称2025新作；DGM后修不是新首发。Frontier此次重新下载这些近邻属于实际检索成本，并非新发现。

frontier引用方法段与版本/原句，不宣称全文每页已审读；两次早期探索GET未存原始响应，仅作线索，缺口在FAILURES.md披露。primary全文、实际body/hash和日期文件足以支持列明的窄结论，不是穷尽新颖性证明。

## 候选与真正检验

### 分子梯度传送与功能梯度预条件

frontier提出分子梯度g_m通过源训练的正定P=diag(softplus(v))+BB'进入8维adapter，P按更新后的功能query loss训练/继承。recursive独立提出proper functional支持梯度的低秩正定P作为强普通对象。两者反馈不同，不能混成同一信息合同。frontier原稿将旧源误写PTPC，实际交叉已改认旧PTDS18stock/17lineage breast资产，功能字段/时点共同合同尚未认证；原稿保留不改。

明确的普通同结构双层metaoptimizer能逐步复现frontier当前操作。其先冻结5个8维/秩2合成例，candidate矩阵步与ordinary分解步最大误差2.22e-16；解析外梯度与普通双层目标中心差分最大差5.20e-8，在预设1e-6内。不是所有元学习都无创新，而是本具体结构没有额外性质。

实际交叉给出严格边界：若g_q=−alpha*g_m、alpha>0，则正步长更新a−eta*P*g_m的功能一阶导数为alpha*g_m'P*g_m>0。frontier与recursive分别冻结后实际核查，分子下降而功能上升。非共线时raw dot<0仍可能由SPD改善，例g_m=(1,0)、g_q=(−1,1)、P=[[1,2],[2,5]]使weighted dot从−1变+1；保留这个反例，不普遍否定处理冲突的能力。

放宽为任意传送T可翻转符号，但普通多输出ridge已做到；与独立least-squares解误差4.44e-16。改成非正定本身不是新的核心。

recursive预冻结的同信息二维支持二次例：同起点loss50.5，共享曲率时继承P一步到0，scalar SGD到.49005；交换曲率后同P到490050.49005，scalar仍.49005，同支持Newton到0。所有方法都得到X/y，Newton没有免费未来Hessian；这不是真实预算/功能泛化试验。保留共享几何下的真实数学收益，也保留迁移风险。不能从这个特例宣称一般P等价EB；一般EB等价并未完整证明。

决定：两类P保留为强常规基线，STOP_CURRENT_DISTINCT_CORE；不据此训练新的生物模型或启动RSI层。

### 跨模态效价位移与第二剂量反驳

biology提出从分子dose tangent剔除nuisance后估计共享剂量轴位移，再购买最能辨别shift/amplitude预测的第二剂量，先存功能预测、再揭反馈，允许拒绝耦合。

root先写ROOT_MATH_PROTOCOL，再独立比较5固定seed×2lambda：profiledelta与X=[−j,A]的ordinary jointWLS/MAP完全一致，10case最大误差2.22e-16；5个j落nuisance空间的情形信息为0（浮点容差内）。精确反例还表明lambda=1、I=1时无噪trueδ=1被缩到1/2；两候选功能预测0/.1、噪声界.1时观察.05与双方兼容，不能保证第二点拒绝错误模型。

biology实际接受这些结果：原P1的无噪精确恢复须限定lambda=0且可识别；P2需预设可分间隔和噪声条件，无法辨别不能当耦合成立。q2预存预测及检验是科学上合理的行为，但ordinary model-discrimination/OED同样可做，尚无独特额外机制或实测预算优势。

其新应用线索decryptE有真实OA方法正文：144药、Jurkat、5剂量、18h与并行fitness设计；首次2024-05-07，不是2025首发算法。原文同时称fitness only marginally affected。只认证设计，尚未认证完整逐drug-dose×function矩阵下载join、逐孔重复或可用动态范围；未下载生物补表或cast新值。State2026仅读原始摘要，decryptM2023仅元数据背景，不能写成两篇全文性能/数据合同已复核。

决定：当前共享shift+MAP+OED组合不晋升独特核心，不启动其生物拟合。保留真实药理问题与公开资产线索，不宣称该资产或所有剂量结构都无价值。其建议10%/3倍控制噪声等门仅原稿建议，尚非生物预测前正式冻结协议。

### API秩势规则

API也自称暂无合格核心，提出同化学组pairwise秩势校准。root先冻结后只读已曝光的600条件metadata/保存score：596组中592单例、4双例，组内相反标签pair数0。因此指定pair loss没有数据项，正L2唯一选a=b=0，无需拟合；11个有理数例核查score精确等于普通[s,z,z³]线性特征。原答把G定义为基础预测器微调而不是editor，预测后续DeltaAP符号也不证明改进策略产生更好后代。

决定：STOP_API_RANK_RULE_BEFORE_FITTING，不采纳API现场建议的新.015/.01门。native审查读了root结果，并未假称独立重新计数。

## 交叉中的必要修订

无目标蛋白的新药预测和全队列6h实测给定不是一个合同。固定P好于I不等于改进策略自身变好；继续meta-training好于冻结不学习也不够，仍需同历史/同预算FTL、EB或learnedoptimizer。8标签达16标签risk仅未验证的资源效率主张；稀有阳性时应保留全N支持频率、proper risk的class分解、prior/EB和排序结果，不能补采阳性或把截距校准当药物发现。

两反馈剂量的主risk必须覆盖全部预定任务，不能只在选中shift的子群报好分；普通Hill/GP必须得到相同源prior。源期成本需在真实有限后续任务数上摊销，CPU/API/标签没有统一价格时分别报告，不能借无限未来任务隐藏成本。这些是实际问答修订，原独立稿未回写。

## 总决定与下一步

NO_PROMOTION_THIS_ROUND。已有局部可验证算子，当前均有具体普通实现/明确适用限制，尚无充分新颖性或实际应用收益。不是“所有函数可表达所以创新不可能”，也不是缺钱/工具阻塞；无需用户确认才能继续。

世界模型、智能体、继承、联合收益及improved-improver：本轮均没有真实生物证据。共享曲率合成收益不能升级成继承成功；公开论文作者的跨任务结果不能挪作我们的结果。完整目标未达成。

下一步应寻找一个具备可测额外结构/有限预算优势的规则；剂量应用若继续，先在任何生物值访问前认证功能矩阵的真实join和源域动态范围合同，再冻结同反馈direct/Hill/MAP/GP/OED/有限程序搜索，不能把普通组合换名为新算子。若只有小普通收益，应独立报告并保持核心机制未建立。不得以本轮结论打开A375/后三背景或重启PTPC晚期STOP。

预算：本轮1次直接DeepSeek逻辑调用，实际模型deepseek-flash，reported9720tokens（765prompt/8955completion），54.922秒；transport底层尝试数未由maintainedclient暴露。Native代理tokens/美元不可得，不虚报。Frontier记录14公共HTTP，biology4，recursive0新增/复用旧认证全文；前述未存body线索缺口保留。所有新增脚本research/、原始来源/失败/决策log/，src/tools不改。

保护TG later14/AZ413/CiPA8–9/MSElater与PTPC四保留背景；本轮无新生物数值/湿实验/生物拟合。历史三response provenance漂移未恢复，本轮局部绑定不等于全历史完整性。
