# 本轮实际交叉质疑：AP-1 分支与 ADCC compartment reset

2026-10-22。双方先保存独立稿，随后反方读取 `advocate/ADVOCATE.md` 与 `SOURCE_REPORT.md`，支持方读取 `skeptic/INDEPENDENT_REVIEW.md`。以下为通过 agent 消息实际提出并回应的问题，不是事先假设的共识。未请求新网络、响应或实验。

## A. 支持方对 AP-1 保留问题的质询及反方回应

### A1. 未配对 state/function marginals 能否支持模型更新？

**支持方质疑：** Fig3/5 state 与 Fig2 后续 colony 若不是同run连接，能否有相同所有aggregate、但相反state→function预测的模型？

**反方回应：可以，故当前不能硬join训练。** 一个纯定义级例子：X与Y各有一半0、一半1；M+令Y=X，M−令Y=1−X。所有单独state/function边际相同，但条件预测相反。这个例子不使用本源数值，也不声称实际分布正好如此；一般的同边际不同copula也有此不可辨识。现在只授权manifest/sample-run身份资格；若仍只有不配对aggregate，保留为mechanism stress suite，而非U训练集。

**支持方实际回应：** 接受此coupling witness与范围。

### A2. 药理作用是否唯一识别 write/maintain/erase 边？

**支持方质疑：** JNK/CBP-p300并非只触及单一轴；哪些已认证same-run controls区分phase-specific toxicity、瞬时反应与持久状态边更新？

**反方回应：当前没有已认证足够对照能唯一识别。** naiveJNKgrowthcontrol、T5224另一药理干预、p300两个domain抑制剂增强原作者解释，但不排除context-dependent off-target、survivor selection或drug×state-specific toxicity。不能把这些药物当完美的单边do-operation。若后续真实matchedtracking/count/orthogonalrescue存在，可缩小解释；现在不虚构其存在。

**支持方实际回应：** 接受orthogonal支持不足以唯一定位edge。

### A3. 修初态、修动力学与修improver怎么分？

**支持方质疑：** 相同feedback下如何用盲测function区分latent-initialstate、transitionθ和improverψ？

**反方回应：本源当前不能唯一辨别。** state/parameter重参数化可能等价。可预先固定state定义、likelihood与可见initialobservations，在多个held-outstartingstates/schedules上比较state-only更新与θ更新，但所得只是指定模型类中的预测证据。ψ必须明确编辑对象，冻结I0/I1，再给相同成本与起点的独立后续更新机会比较它们产出的改进；当前AP1资产是否具有这些任务未认证，不能把θ预测变好上提为ψ改善。

**支持方实际回应：** 接受该识别与归因限制。

### A4. n1擦除能否作为反例？

**支持方质疑：** 能否只当单task反例，不要求其他n7/n6补强？

**反方回应：可以。** 文献暴露的n1图可以提出“撤TM不等于复原”“erasewashout不必可逆”的具体候选反例；需要真实readout/controls身份。它不支持跨run可靠性、继承统计或单独指定生物机制。其他Fig的n7/n6不替它补样本。

**支持方实际回应：** 接受。

## B. 反方对 ADCC reset / rank-one 提案的质询

支持方原稿提出：naive/adapted tumor × fresh/prechallenged NK，固定liveE:T和24h，操作分数H=-logV，假设H_ij=r_i e_j，以前三格预测第四格；支持方已自行给出同rank-one predictor/posterior/variance-per-cost/update的逐项归约，并判当前算法/RSI核心none。原有publicsource未认证reciprocalaged-NKfactorial。

### B1. 终点分离不识别动力学

**反方问题与构造：** reciprocalrandomization可以识别所制备history组合的终点效应；r/e仅up-to-gauge的operationalfactors，不唯一识别tumortransition或NKcompetence dynamics。

精确构造：对四个配对固定 `H_ij=r_i e_j`。ModelA令瞬时hazard在0..T为常数`r_i e_j/T`；ModelB在前T/2为`2r_i e_j/T`、后T/2为0。四个终点survival完全相同，半程读出、撤药或重置时机响应不同。还可对每配对加积分为0且足够小以维持非负的`δ_ij cos(2πt/T)`，使固定终点rank-one成立但瞬时interaction不同。因此即便3→4通过，也不识别on/offtransitionrates、内在epigeneticmemory或未来scheduletransfer。

### B2. 3→4与±.05判据要传播完整不确定性

**反方意见：** 3→4是有效、廉价的过识别预测限制，但单个2×2不能证明新history迁移。equivalenceinterval应同时传播H00/H10/H01、sharedtumor/NKcontrols及anchor分母不确定性；不能只给第四格重复SE。H00近0使比值高度不稳，必须在独立calibration预锁quantitation/anchor。V>1、≈1等无效域要按预定规则报告taskfailure，不能看interaction后选择性排除不合分离的格子。匹配growthcontrol不把24h的−logV自动变成真实死亡hazard。

### B3. 对none是否过严

**反方意见：** 支持方同rank-one模型、同posterior、同acquisition、同update的逐项归约成立，因此当前没有新的算法/RSI操作。判断依据不是universal direct也能表达，更不是泛称属于AL。该结论不否定若干已知组件在新真实控制条件下产生可证伪的生物分离/样本效率贡献。需要真实数据与对同信息强基线的效用，不能靠模型命名。

### B4. 当前资源决定

**反方意见：** 现有source没有所需agedNKfactorial，故不启动架构、数值离线kill或LLM自改进。可先寻找/资格现有公开crossedhistory功能资产；不向外发消息或请求实验。若未来独立实验条件本来可用，预冻2×2+controls+独立batch有可证伪价值，但其first-of-kind和省实验的实际收益尚未成立。保留r应称endpointrowtransfer，非dynamicoperatorinheritance。

支持方在收到B组完整问题前已明确同意：即使分离通过，也仅支持某条件下response separability，不证明e不受tumorligand影响、r为epigeneticmemory或任何转移速率。**B组其余逐项实际回应待收后追加，不能提前记作完成。**

### B组实际回应追加

支持方随后逐项明确接受全部四项：在其归档中加入相同积分endpoint、不同hazard时程的解析witness；equivalence同时传播三anchor、共用control与分母不确定性，定量域先锁且不按正式响应事后剔除V>1/近1；保持算法/RSI none但保留窄经验可证伪价值；inheritance仅称endpoint-rowtransfer，当前行动仅公开crossed-history真实功能资产资格，不启动架构、训练或wetlab，无asset则暂停而非以simulation补真值。

因此B组已实际答复，前述“待收”状态已结束。AP1/ADCC的证据边界无核心科学未决；AP1run/state/functionjoin是否可得、ADCC分离是否真实成立，仍是未测的经验问题，不用共识代替。

## 当前共同边界及尚待事项

A组已实际答复并接受；支持方对其自身提案早已给出算法none，本次B组更强动力学反例与不确定性要求待其逐项确认。双方都支持先source资格、承认已知组合仍可能有实证贡献、拒绝把细胞memory称为程序继承/RSI。当前没有任何新hiddenoutcome或新性能结果。

以上段落保留交叉进行时的记录；依据B组追加消息，**本轮交叉现已完成，四项均已接受**。没有实证结果或新算法因此被认定成立。
