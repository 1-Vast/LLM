# 从真正有价观测的CV方法继续研究普通药筛共学

2026-10-29。**找到两个比“全图压缩”更贴近实验获取的来源原则，但尚未形成可推荐的新Agent×虚拟细胞机制。** CVPR2025 SIB-ACS先付小批探针，再按反馈改变采样；ISO同时选择对象与标签精度。本轮核到了它们的实际方法，也补齐一篇关键化学规则原文。关键科学判断是：反馈造成的预测变化、真实误差改善和最终选药收益必须分别检验，不能由前一项代替后一项。

本轮是探索/方法核读，0新功能值、0原输入/化学支持重算、0效果实验。历史H_L阴性、E.v1结构覆盖不足和成员匹配工程缺陷导致的独立复算未完成均保持原状。没有通过拟合跑分或增加模态来回避它们，总目标ACTIVE / NOT_ACHIEVED。

## 两个可用源原则及具体限制

筛选团队的实际问题仍是用有限cell×drug×physical-dose功能读数，决定下批测什么、哪种范围可借用，以及何时直接测目标。比较对象必须允许完整历史、重新拟合、直接目标测量和相同孔/批次成本。RNA、显微、谱系、新合成不作为通用输入条件。

| 已核原文 | 实际操作 | 打开的药筛问题 | 当前边界 |
|---|---|---|---|
| [SIB-ACS，CVPR2025](https://openaccess.thecvf.com/content/CVPR2025/html/Tian_Sampling_Innovation-Based_Adaptive_Compressive_Sensing_CVPR_2025_paper.html)，PDF页3–5、§3.1–3.3、Eq1–18 | 先uniform initial sampling；每stage另付uniform innovation sampling；两轻量重建的平方变化alpha，按alpha²分配剩余block样本；最终学习型重建，训练l1+SSIM | 能否从少量已付功能探针估计下一批在哪些关系上仍有可学收益？它确实不要求部署前先见全真图 | 学习型模型的预测变化不自动是风险下降；任意dense sensing、像素局部性、image loss不自动对应合法药筛动作或选药效用。单孔坐标查询是合法已知selector，不能一概说药筛没有已知测量算子 |
| [ISO，CVPR2025](https://openaccess.thecvf.com/content/CVPR2025/html/Matsuo_Instance-wise_Supervision-level_Optimization_in_Active_Learning_CVPR_2025_paper.html)，PDF页1、3–6、Algorithm1、§4.2–4.3/5.3 | 学习global label-level improvement；VCR=M_level×instance uncertainty/cost；结合diversity选batch。Cf/Cw预给，实验Cf=1，Cw=1/2并比较1/4、1/8 | 一个对象该得到多少信息，是否应由可学习收益和真实费用共同决定？ | 其weak是superclass人工标签，费用是相对annotation单位；单孔读数事后分箱不省孔。单点→曲线需真实嵌套/剩余孔/开批合同，已读Algorithm1未给weak→full升级。验证集为一轮B量级，总图预算是否扣含仍unknown |

二者官方PDF分别11页、9页；仅上列方法/成本段及必要设置已读，不称全文复现或作者结果验证。[冻结迁移判断](transfer_assessment_frozen.md)保留原始推导，后续条件更正在[澄清](assessment_clarifications.md)。两份PDF原字节与哈希在来源目录及共享library；官方代码链接已登记但未取commit/源码/许可，未执行作者代码。更广泛多尺度/多模态最新覆盖没有因这两篇完成。

另从正式CVPR2025全目录定位Foveated Instance Segmentation，仅核其完整官方摘要：它按user gaze节省segmentation计算，不提供本轮付费药筛观测原则，因此不再取全文；保留A等级，不能把摘要筛选当方法核读。

## 预测变化什么时候才有科学含义

令历史预测m0、反馈后m1、真响应x，d=m1−m0，e=x−m0，则平方误差下降为

`R0−R1=2eᵀd−||d||²`。

它通常不等于innovation `||d||²`。x=0、m0=0、m1=1时，innovation=1而误差下降=−1；这是解析反例，未运行模拟或使用生物数据。若新残差与d正交，或在平方可积、嵌套历史、正确联合后验条件均值下对下一反馈及未知真值取条件期望，可以得到相应等式。后者是期望结论，不是每次读数改善，更不是任意网络refit成立。没有据此否认SIB已报告的图像实验性能。

一个明确自然适配是把更新投到预定药物功能对比L。明确采用以下充分条件：给定当前历史，F为Gaussian、条件协方差C；合法单孔Y_q=F_q+epsilon，epsilon~N(0,s²)且在该历史下与F独立；L预定或由当前历史确定，v=C[q,q]+s²>0。此时，

`E||L(m_new−m)||² = ||LC[:,q]||²/v`，

恰好是`tr(LCLᵀ)−tr(LC_newLᵀ)`。因此这个一步目标评分就是已有目标线性Gaussian/A-optimal设计的运算；去掉共同平移、加“决策尺度”名字并不新增运算。**这只对应该一步适配，不覆盖SIB已付probe、逐实现alpha²分配和完整多阶段算法。** 也不以Gaussian特例否定所有nonlinear/non-Gaussian研究可能；真正的新计算近似、识别能力或同资源效用仍可另检验。

独立挑战先保存初判，再重读两份原PDF。[初判/原件/最终判断](independent_challenge.md)指出原冻结稿少写观测噪声条件，要求明确有限矩、条件期望对象与正分母，并防止把一步对应扩成全SIB；root按原文和推导采纳，原稿不改写。内容与代数核查不产生药物效用证据。

## 化学最近先例从摘要推进到了方法

[2023 Chemical rules原文](https://doi.org/10.1186/s13321-023-00707-x)经PubMed精确DOI→PMID/PMCID→EuropePMC正式OA JATS取得；CC BY4.0。source worker读取方法、结果/讨论；root独立读取Par29、30、31、33、37、38、39、40、43、46、53、54、60。补充/作者代码未取，2020 Transform方法仍未核。[详细原件和读取范围](chemical_methods.md)。

原文明确定义attachment radius0–5环境匹配；模型适用域另以top-K Tanimoto阈值处理，二者不同。规则`Svalidity=Nneg/Ntotal`的Nneg是**模型预测**转阴的生成分子，只统计模型ID对象，不能当作新分子实测成功率。主文用test set定适用域，重复化合物重新赋标签不证明生物重复，approved-drug负类包含无致突变证据者。其85.08%规则只出现一次属于该Ames数据，不是GDSC支持统计。

该论文具体覆盖了“结构环境限制编辑规则”与离线模型评估；已读主文没有给出主动付费query、观测反馈触发的规则拆分/修订等细节，仍记not described/unknown，不据此宣称本文不存在任何未来闭环。它是binary Ames集合，不能充当两细胞同dose/time连续ΔS证据。这补齐一个近邻，不证明E.v1完整已做或首次；E.v1还受上一轮1/11映射及独立复算未完的资格门约束。

## 从全档案选线，而非只接最新候选

requested Astra/MAX中性scout先存结构brief与初稿，再局部核5件已有2025–2026原文，最后对照旧档案；有限memory暴露已明示，不能称对历史完全盲。[初稿](neutral_initial.md)、[原文/条件](neutral_sources.md)、[具体碰撞与未读清单](neutral_archive_comparison.md)保留。

“平均响应相似但探针信息价值不同”与旧B1/G1及同一技能迁移反例重合；“反例修复共享分组”与OPINE/core旧线重合。其二元例子虽显示联合关系不同，但同价直接测Y1即可揭示所需量，故不证明省孔。root核了B1冻结构造和旧目标方向归约，采纳这些具体对应，没有仅因能写成Bayes就否定所有新方法。

保留的旧问题是：普通共同观测在何种可读取结构条件下足以学习可迁移的条件关系，并服务多个未查询目标？较弱、不同承重的比较是单药剂量阈值/形状约束，它不依赖跨药联合关系，但同样已有标准顺序设计。两条尚未因本轮得到新增算法或效用证据，不换名重开已停设定。

## 当前决定、下一证据与实际成本

新增可复用成果是三件新原件的局部方法证据、真正付费获取与仅省计算的区别、预测更新的风险条件及两个明确最近操作先例。**暂不冻结新算法优势H，不启动效果实验，不晋升src/tools。** 首先还需一个具体不同运算/可计算性或科学能力，以及能验证该差异的合法观测/真实费用合同。若只是SIB试探采样、ISO进度×uncertainty/cost或一步A-optimal改名，则停止对应新颖性主张；若数据/测量条件不够则park，不判效应阴性。后续任何验证轮须另冻一个H、同信息强对手、数据/预算/指标/停止门；已开发暴露的GDSC前缀不伪装独立确认。

保留历史31pass，新增两个工作单元耗用，累计33/33；并非把每次PDF读取/代理/代数检查都算独立科学验证。公开逻辑动作10/12，显式主题query1次（arXiv429后停该源），另一次CVPR目录获取与离线过滤；成功body12,609,779B，全部body12,609,793B，余2动作未为凑数使用。一次同host落地页间隔约0.818s，低于≥1s节流规则；随后脚本加显式间隔，未重发该请求。无重试/认证绕过/新功能数据/真实metadata重算/安装/GPU/作者代码执行/效果实验/核心更改/提交/发布。实际请求、限额、失败与本地预处理更正见[预算](budget_usage.json)。

DS026新隔离headless一次完成7条指定来源/单位/资格抄录，56字段和7个quote_literal经root核对；分类由root事前给定，不是辅助模型科学判断。[验收/usage](../deepseek/tasks/DS026/main_review.md)：3.766s、2085input/504output/256cache-read，6832B stdin；累计18/18，effective型号/底层请求数/实付未知，USD0.025不是已验证硬美元cap。0工具/重试/换后端，进程已退出；旧DS007/008/DS024记录不动，默认台账断点已续记，不虚称后台。

内部source请求Sol/medium、中性scout请求Astra/MAX、fresh挑战请求Sol/high，effective/usage/费用未知。Terra无原生选项；用户在收尾新增6luna备选后，实际请求gpt-6-luna/high按organize-files整理阶段证据与接续条件，见[整理内容审阅](organization_review.md)，不冒称Terra。root维护共享入口并作最终科学判断，保留独立挑战、冻结稿、更正和来源。物理移动/删除0。

共享library新增4条来源、3件文件；[最终verify](library_verify.json)为127唯一来源、111论文文件，74HTML/17PDF/25pending/8restricted/3abstract_only（按唯一来源状态），10代码快照关联9篇，errors/warnings为空。本轮新增代码快照0，四条官方repo仅登记not_verified。2023主JATS借generic supplement技术槽保存，非科学SI，主PDF/HTML仍pending。已将化学root读取范围更正为上列13个段号，清空未核的首次公开日期，保留正式日期；按落地页六作者更正Foveated题录；三件文件source_url更正为真实公开获取地址，不能把工具local intake默认字样当用户上传。这些完整性与来源更正均不认证科学成立。

后续[内容审阅](content_review.md)与[组织验收](organization_verification.json)分别记录综合表述范围和实际文件账本；后续审阅已暴露root报告，不倒称原始独立初判或独立功能确认。

总目标继续保持ACTIVE / NOT_ACHIEVED。
