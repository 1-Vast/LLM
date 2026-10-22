# 支持方独立提案：把state aliasing落实为最小、可反证的更新

2026-10-22，Asia/Shanghai。角色 `mechanism_advocate`。本初稿在读取本轮反方文件之前落盘；已收到反方一句概要和问题，因此不声称对问题完全盲法。只用已取得的身份/源码证据和方法学推理，不新开HTTP、不读取Growth/图像/矩阵、不搭架构或运行新性能实验。

**初始裁决：候选值得作为“当前状态是否足够支持动作选择”的科学问题；尚没有不同于controlled predictive states、counterexample-guided state splitting和主动模型鉴别的独有操作，因此不批准其作为新颖核心架构。** 可执行分解可以防止泛泛的“加记忆”，但命名、模块组合或一个history bit阳性不能满足总研究目标。

## 最小具体操作

具体应用暂限于真实抗生素schedule菜单上的下一实验/下一continuation研究决策。`h`为当前允许的已知给药与观测历史，`x=phi(h)`为当前细胞/微菌落state，`u`为一个真实允许的后续schedule或实验，`Y`为未来实测growth功能，`c`保留strain/run/环境。模型状态不是“真实细胞机制”的默认等价物。

候选只做一次显式编辑：在当前state block内发现**同一后续动作u的future prediction相互冲突的两个历史**后，选择一个可在决策前计算的最小predicate `g(h)`，把状态从`x`改成`(x,g(h))`，只重拟合受影响的transition/readout部分，并将该predicate与失败/适用条件序列化。`g`来自预先允许的有限、简单字典，例如上一药物/剂量类别、持续暴露累计量、距切换时间、已买的early-growth slope或某个形态特征；不包含未来帧、未来Growth、作者终点CI、测试drug identity lookup或事后最优action。

最小行为链：

1. **提出alias witness**：两已测prefix histories在原`phi`和规定context下相同/近似，但在相同continuation u下出现不能由已估计噪声解释的实用结局差。
2. **形成候选split**：枚举最少新predicate，使同一受限模型的该conditional error变小；优先最小description length，而非无约束增加latent dimension。
3. **独立反证**：用尚未参与选predicate的真实允许query，检验split是否改变未查询actions的正确排序；没有新支持时只保留待测候选，不把模型自己的rollout作验证。
4. **保留或撤回**：若同信息普通history-conditioned model、MDL split或等预算搜索匹配，按已有类别报告；不能把“state representation被改变”自动称world-model贡献。

确切改变counterfactual decision的地方是`g`改变同一continuation下的预测，并使原来共享一个state的两个history采用不同action。一个解析示意：原state相同，历史h0下B比C好、h1下C比B好；只看state的policy无法两者都选对，加入history bit能改变第二动作。这只证明原state不充分；一个含同history bit的conditional table/tree同样能做到，因此不证明本操作独有或world必需。

## 最重要的范围：一种collision不等于所有控制主张

反证`phi`的predictive sufficiency，最低需要不同h0/h1、匹配规定context/当前phi、以及相同continuation u的真实结局。原history可不同，不能要求它们prefix也相同；若prefix全同而无随机状态差，恰好没有history bit可分。

若要进一步证明这是**action-specific**隐藏state、会改变最优动作，而不是普通baseline-growth偏移，最干净的是h0/h1 × u0/u1的已测2×2，且对动作的utility排序发生反转或至少有预冻实用增量。只比较A→B与B→A时prefix和continuation都变，不能单独定位state aliasing；仍可以合法比较两种完整schedule的总效果。

跨实验query/update replay可以把每个完整schedule当独立真实实验，不要求同一个colony被分叉。较强的state-feedback第二动作控制才需有匹配prefix、决策前state和真实替代continuation支撑。不同破坏性样本/姐妹培养也可以提供适当对照，但需认证exchangeability/随机化及独立run，不能把同图像或同chamber多个colonies当独立随机实验。不同历史的观察性state matching不能自动消除未测run/培养混淆，因此“修复的是真实因果细胞state”比conditional预测充分性更强，本候选不默认获得它。

## 与已有方法的实质区别：目前没有成立

这个操作的有用之处是把世界模型state的必要性定义成真实continuation上的行为约束，而不是仅重建RNA/形态更好。它可能在小反馈预算下，以一个具有可检验适用条件的history predicate，减少自由度和错误更新的传播。无须从一般conditional NN的表达能力推导它无用；有限数据/计算下的归纳偏置收益仍可能存在。

但目前提出的步骤都被直接已有方法覆盖：

| 候选操作 | 直接已有解释/比较 |
|---|---|
| 按未来action-conditioned结果区分过去history | controlled predictive-state/causal-state思想、history-conditional预测 |
| witness引起最小memory/state split | active automata learning的counterexample refinement、variable-order/MDL状态划分、CEGAR |
| 选择最有辨识力的continuation | active model discrimination、信息价值/knowledge gradient、主动学习 |
| 保存split程序和witness并移植到新task | 普通规则迁移、meta-learning、case retrieval/蒸馏 |
| 根据源任务改写选split/选test的策略 | learned optimizer/科研程序搜索；项目已核的一手Hyperagents/SpecRSI等RSI先例 |

经典操作族包括Angluin式query/counterexample automata learning、PSR、CSSR/controlled extensions；本稿是相关方法定位，**未在本轮新HTTP核验这些经典论文全文**，不能据表假称已穷尽所有具体算法。反方若提供精确等价程序，我不以生物学命名逃避归约。

**目前不存在可诚实声称的实质不等价步骤或新可证保证。** “有真实细胞动作约束”“能继承memory predicate”“程序可编辑”都不足补足这一点。本候选若有价值，目前更像一个面向应用的最小充分state诊断和受约束更新，而不是已找到的新世界模型/Agent/RSI核心机制。

## 可证伪预测与强比较

结果前必须锁定合法任务、source/未来化学或strain/context分区、测量单位、query bundle/cost、容差/噪声估计、端点与实用差delta。不能事后按最漂亮drug pair寻找碰撞或替换终点。

1. **真实机会**：在预冻phi和context匹配下，存在可重复的continuation-dependent residual，且足以改变未来action决策；若只剩共同offset、当前count/area/early slope或已知dose/order解释，停止此split主张。
2. **受限更新效用**：固定同支持集下，最小split改善未查询功能效用并超过direct same-history table/tree/kernel、同辅助监督多任务conditional模型、普通refit/continual learning、MDL controlled-state split和简单混合。若现有方法匹配，即使split有预测收益也停止新增机制主张。
3. **Agent效用**：同模型/候选split family/初始数据，对fixed coverage、直接功能测量、普通AL/KG/model-discrimination与等预算随机/BO/program search；正确“问出一个collision”但终点效用不变，不晋级。
4. **程序继承**：更后任务共同模型/程序起点，split规则迁移优于同历史restart/retrieval/distillation/meta-learning；不能只移植旧drug标签bit或较强权重。权重与程序分别开关。
5. **联合收益**：world/direct × agent/conventional 2×2；联合须超过最强常规完整系统。正交互而绝对效用输，仍失败。
6. **RSI**：从相同task程序、模型、可见history出发，冻结旧/新改进策略m0/m1，各给相同k次proposal/evaluation/真实query，比较更后未优化任务的改进曲线；若再形成m2，同样比较m2/m1。形成策略的历史成本另计。只是固定refinement policy越来越多state、或更强初始partition，不说明“改进策略本身更会改进”。

主要差区间上界低于delta则停止；区间宽为未决，不算支持，不换指标续命。没有可认证的实测continuation对照时，该特定collision机制NOT_TESTABLE，但不否定静态schedule query/update任务的其他价值。

## 各模块是否必要

- **可更新的state/transition**：仅当同信息history-conditional直接模型不能匹配有限预算决策收益时，才有显式world贡献。一个predicate加到直接tree上同样有效时，不把它强塞进world架构。
- **实验选择Agent**：仅当选择哪些真实test/continuation使改进更快/更有用，超出固定覆盖与普通AL，才必要。静态有限字典的穷举更简单且匹配，就使用它。
- **继承程序**：须实际移植可执行且跨task有效的split/诊断规则。保存证据有审计价值，但不自动有能力收益。
- **LLM/多代理**：评审有方法学作用；部署LLM不由上述机制逻辑必需。有限predicate字典无须先加LLM提案层；其独立贡献需要另测。
- **元改进器**：目前仅为用户完整目标要求的待检验部分，不应凭“系统能编辑自己的refiner”添加模块。若普通固定refinement或meta-learning匹配，移除RSI主张。

## 当前数据能否承载

LIST仓库已认证真实source/文件metadata，但`Colony analysis.m`在本次已读源码中处理9个静态TIF/z-stack，并未提供time track；Growth脚本只要求generic A/B、Time/Dose/Growth/Dosing_Type，无strain/run/chamber/colony映射，且对全窗口结果做posthoc均值/CI。因此不能从这两份代码拼出真实collision。Zenodo与实际schedule/trace身份正由其他独立角色核查，本稿不先假定它通过。

如果后续身份证明有真实schedule→早期state→后续growth配对，最便宜的下一步仍是预注册一个**state信息/aliasing资格**，不是构建refinement系统；且只有结果能改变具体技术路线、并且有可能区别一个实质新操作时才值得消费数值。当前由于没有独有操作，即便找出有趣alias也只能支持研究问题，不能因此自动晋级新架构。

## 待交叉审查

反方已发来问题：候选可能等同controlled predictive state/automata/variable-order split；same-history direct与MDL split必须同预算。我的独立初稿同意这一硬比较，且尚未给出不等价步骤。正式读取其独立文件并交叉后只追加意见，不改写上述初始立场。
