# 序贯抗生素3D菌落资产：独立初始资格问题

2026-10-22，Asia/Shanghai。角色`scientific_skeptic`。**只据根代理已取得的原始PubMed摘要形成初始立场；当前未读新原文/manifest，没有认证公开数据或完整菜单，不作新颖性/架构晋级。** 后续原文检查只追加，不将后见事实回填为本稿事先知道。

原始记录：PMID41278959，PMC12636614，DOI[10.1101/2025.10.30.684665](https://doi.org/10.1101/2025.10.30.684665)，题名`Massively multiplexed microfluidics maps combinatorial and sequential antibiotic responses in 3D`，来源是`log/20261022/intervention_schedule_qualification/root_sources/PRIMARY_SUMMARY.json`中对应记录。摘要声称512独立可编程hydrogel chambers、追踪10,000 colonies、约半百万图像、同时/序贯给药共2,700 drug-dose combinations，以及stiffness/nutrient timing实验。**这些是平台/作者规模描述，不能等同512独立任务、10,000独立干预分配或2,700完整序贯菜单。** 无新增HTTP请求；未获取raw图像、表达或功能矩阵。

## 应用与可支持的潜在问题

若原始资产可取得，最自然应用是**3D水凝胶中细菌菌落群体的抗生素顺序/剂量实验分配或约束菜单内调度**，目标是未来生长抑制/恢复，而非人PHH、临床DILI或患者治疗。是否包含真正细胞分子状态目前未知；摘要只认证live-image morphology/growth。形态可作为观测状态，但不能把它改称已测转录组/机制分子状态，也不能以菌落尺度动态替代单细胞世界模型验证。

它比只有单次持续药物的三个破坏性时间点更接近实际序贯干预；但必须先确定真实可执行研究动作和信息时序。可以有两个不同任务，不应混用：

1. **跨实验闭环。** 研究智能体在完整有限schedule菜单中逐个选择下一次菌落实验，收到实测轨迹后更新预测器并选择后续实验；完整的静态schedule结果表可以支持这种offline replay，不需要每个菌落可自适应改变第二药。它仍需击败普通active learning/重训练，不能因逐轮选实验自动声称RSI。
2. **同菌落内反馈控制。** 先处理A，观察状态后按状态选B/时间/剂量。这需要共同prefix下实际第二动作分支、决策前状态、动作随机化/分配规则与足够positivity。只有事先固定的AB/BA列表或平台“可编程”能力不足支持该任务。不能用模拟器补齐未测动作后又拿模拟回报自证生物控制。

## 必须先认证的身份与时间菜单

- 论文/public repository的准确版本、license、稳定链接或accession，data-availability声明是否等于可下载的身份+响应；如果只“available upon request”，本轮尚无可执行公共replay。
- strain/species/genotype、是否有多个真实遗传/培养背景；chip/device/run/day、hydrogel batch/stiffness、medium、nutrient timing及独立培养关系。
- 每个schedule的drug1、dose1、start/stop、washout/残留处理、drug2、dose2、start/stop、观察时间；“sequence”是否只是延迟加入第二药而第一药持续存在。
- 同步AB、A→B、B→A、单药、vehicle/营养对照是否存在；每组是否完整dose grid、实际子菜单各有多少唯一条件；2,700中多少是序贯、多少是不同基质/浓度而非独立药对。
- colony ID是否在时间上真实追踪；parent chamber、field、image、time、segmentation object能否关联；分裂/合并/脱落是否导致换ID或幸存者偏差。
- 每个记录的随机化单位、重复run数、技术/生物重复数，以及丢帧、分割失败、菌落消失、未增长的保留规则。没有长出可见菌落不能直接当缺失删除。

若不能取得上述必要键或共同prefix/可选择实验菜单不闭合，只关闭相应replay任务；不泛称数据无用。

## 图像状态与生长终点：合法预测信息和泄漏的分界

同一显微图像可同时提供size/morphology和growth。这并不使**决策前**形态预测**未来**生长自动无效；大小、增长速度是合法廉价强状态。但以下会制造无意义增益：

- 特征含第二次干预后/最终评价窗口帧；分割、追踪、embedding或QC使用完整轨迹回填早期对象；按未来是否可追踪来选样本；目标时间进入normalization。
- growth目标本来由同帧面积/体积计算，模型拿到同帧面积或其等价变换；若预测相对增长，baseline denominator和特征共同噪声带来回归均值伪效应。
- 将抑菌、细胞死亡、耐药/持留的解释混在一起。图像面积停滞不认证细菌被杀；“resistance”需要作者的实际验证/功能定义，不能从regrowth自造遗传耐药真值。

必要强对照是同decision-cut可见的最后大小/体积、最近一段增长斜率、lag、既往drug-dose-time、基质/营养/位置/run信息；简单growth curves/Gompertz/logistic/state-space、强条件direct predictor及同未来轨迹辅助监督的multitask模型。先测完整形态是否超过size+slope，再问显式状态转移是否提供净功能/调度增益。所有模型获得相同paid前缀、辅助标签与未来不可见限制；不同变量名称不构成世界模型消融。

3D群体状态还可能主要反映扩散、局部耗竭、几何屏蔽、初始菌落大小及水凝胶环境。它们可以是有用的环境状态，但不证明模型识别细胞内机制。应让直接基线显式获得这些已知条件，不让世界模型独占metadata。

## 独立单位、heldout与继承/meta任务量

处理一般分配在chamber，多个colony/帧共享处理、流体、基质、运行；10,000 colonies不是10,000独立随机干预。应先按真实分配单位聚合/cluster uncertainty；所有同colony图像和同chamber随访进入同partition。schedule chemical family/药对holdout和run/device holdout回答不同问题，均不能由随机image split替代。若某drug pair只在某run出现，药效与run不可分，不能用模型“去批次”宣布已认证跨条件。

新任务可按真正heldout strain、环境或药物机制/药对定义；每类须说明共享动作/可转移关系、源/后续任务先后和独立单位。只有一个strain/一批设备的许多剂量和时间不自动提供多阶段meta实验所需任务数。若多个hydrogel/nutrient环境只是同一批次设计，可做条件泛化，但不能改称跨生物背景验证。

程序/权重继承必须分开，与同历史普通refit、continual、case retrieval、蒸馏、固定policy和等预算程序搜索比较。RSI另需从共同model/program/history起点对冻结m0/m1给同k次提案/评价，在更后未优化任务比较改进效率，并计形成m1的历史成本；新菌落更多或更好初始预测器不等于更会改进。当前摘要无法认证任务量与公共数据支持这些设计。

## 初始裁决与最便宜的后续资格

**保持SOURCE_IDENTITY_REQUIRED；不据规模描述自动批准架构。** 支持方正在取得原始方法与manifest，我不重复fetch。下一步先只审查其schema/文件清单与时间/处理身份，分别数真实strain/run/chamber/colony/schedule、共同prefix分支和功能缺失。若公开文件足以形成合法跨实验查询菜单，再预冻身份分区和一个具体生长抑制/确认决策；若只有图片/摘要而无处理→轨迹键，暂不开放响应。

这项资产有实质性的序贯干预线索；初始怀疑针对信息边界和归因，不是预判world model或菌落动态一定无价值。新的核心操作仍需独立提出、与已有调度/系统辨识/active learning实质比较，不能因换成细菌而重置历史阴性教训。

## 实际来源检查追加

支持方结束其3个登记请求后通知未取得全文/manifest。我独立检查了`advocate_sources/NETWORK.json`、`PAPER_TEXT.txt`及`PAPER_NCBI.xml`内容，确认：

- Europe PMC `fullTextXML`返回HTTP500，151 bytes；本地`PAPER.xml`不是论文全文。
- NCBI EFetch返回HTTP200、7,020 bytes，但XML只有front/abstract，无body。它明确写有`The publisher of this article does not allow downloading of the full text in XML form.`，所以HTTP200不是全文资格；`PAPER_TEXT.txt`也只是同一摘要。
- bioRxiv原站全文返回HTTP429、12,010 bytes，不是已取得方法。未再重试/更换方式绕过。

本次支持方3请求共19,181 HTTP body bytes，receipt URL/status/hash齐全；本反方没有新增HTTP。NCBI front确认作者Jeong等、preprint v1和实际epub日期2025-10-31，不能只凭DOI中的2025.10.30声称发表日。此日期仍在2026-10-22文献截止之前。

**修订资格状态：ABSTRACT_ONLY / METHODS_AND_MANIFEST_NOT_AUTHENTICATED。** 仍无法认证strain、drug/dose/lag、washout还是追加、共同prefix第二动作分支、功能frame定义、处理→轨迹键、独立run或可用于heldout/meta的任务数量。未看到manifest不是证明作者不公开数据，也不是证明方法没有这些内容；是本轮尚无可执行公共asset证据。没有响应值、图像或模型实验。

因此目前只保留前述应用/风险清单，不能从摘要中2,700组合推导完整科学agent replay或cell-feedback-policy。若后续根代理经正常公开来源获得方法与data入口，须首先完成身份菜单与终点定义审计再决定数值开值；本轮不把访问失败当科学失败，也不因来源失败重跑之前停止的clock/OASIS配置。
