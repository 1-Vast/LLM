# 独立反方：STACK 单次数值结果

2026-10-22。先读root的RESULTS、FINAL_COVERAGE、TERMINAL、SELECTED、RESOURCES_AND_EXPOSURE；**本稿先于任何peer本轮结果稿/讨论**。任务消息已给主数值/停止状态，非对结果盲读。未读raw/XLSX/新增字段或response数组，未fit、重跑或联网。所有旧freeze/review/CROSS不改。

**裁决：接受 PRIMARY_USEFUL_GAIN_FAIL 与注册停止；同时保留真实的小幅正向预测收益，绝不写“D无信息”。** 这是一个资格合格、完成75fits的有限来源marker预测实验，不是HCT116式目标资格失败，也不产生world/agent/RSI结果。

## 结果与注册门槛

合格test为367/367/364三screen rows，总1098；364个完整三context contributing groups，全部role×screen覆盖>=95%。test中两U2OS条目有D额外prefix failure，另一个L72无效；L-only在相同双通道条件panel评分。train/validation和test的这些已排除值不由剩余分数推断，complete-case范围仍需写明。

| arm/对比 | macro log2 MAE或增益 | 可支持内容 |
| --- | --- | --- |
| L-only | 0.227449984 | matched direct主基线 |
| D0 | 0.227438875 | 与L-only几乎相同，非明显基线校准收益 |
| D24 | 0.223087112 | 描述性终点snapshot增益 |
| D0+D24 | 0.222697714 | 描述性联合端点增益 |
| fullD | 0.219489505 | 当前最低MAE的注册臂 |
| fullD相对L-only | +0.007960479 / 3.50% | 三screen均正；未达.05及10% |
| fullD相对联合端点 | +0.003208210 / 1.44% | 小幅interior集合增量；未达同门槛 |

fullD相对L-only各screen增益约0.008441/0.005155/0.010285，全为正，符合方向条件；但绝对与相对主实用条件均失败。与D0、D24、joint endpoints的历史property条件同样全未达原双门槛，因此不换以其中最有利者、单背景或其它目标救结果。

固定fit的367个test role clusters配对bootstrap，primary95%区间[0.002736,0.013613]，对联合端点[0.000205,0.006211]。区间为正支持这个条件panel上小幅收益方向的重采样一致性，**不使0.008达到0.05，不将3.5%变成10%**，也不是独立生物run显著性。不能以“CI正”宣布成功，不能反过来因实用gate失败抹掉正向数值。所有五臂恰选相同ExtraTrees(max_depth=None,min_leaf5)配置，故描述性差值不是test上换获胜family产生；仍只是固定supervised模型/特征增量，非conditional MI、各时间点必要或动态因果识别。

## direct对growth的大优势如何解释

persistence MAE1.080488、constant log-growth1.056366，显著差于L-only direct0.227450。最低诚实解释是：同screen开发、合法live prefix上学得的非线性经验forecast，比固定常率长外推更适合这些marker轨迹。它可能反映密度/饱和、药物响应时变和测量校准等，当前无证据分解原因。

这里按未见recorded entries留出、跨screen同role，确是预测而非重复把本记录72h训练后评分；不能贬为逻辑恒等式。但所有背景在训练出现，无chemical/dose外推、未检验新run，故只支持来源内surrogate prediction，不证明学到可运输细胞world、更不证明新机制。仅因growth弱，不能宣称worldmodel已被direct普遍击败；强ordinary kinetics/world根本未测。

## 停止范围与是否另立任务

注册停止合理限定为：不再把这个fixed-dose0–24→72h、named-entry/completepanel、registered direct信息路线扩展成核心world/agent/RSI框架。门槛为实用筛选而非自然定律，当前既定门槛不能事后降到约.008/3.5%。不宣布所有SG/death通道、其它任务或虚拟细胞无效；不把小阳性讲成足够新颖的核心。

**当前不推荐在这个已暴露test上追加ratio、模型、目标或时间点来追阈值。** 有效对比是已经一次完成的结果，test现在暴露，不能把后续新程序得分称独立确认。STACK可明确作为未来开发资料/历史失败案例，而非继续自称sealed test。

另立任务只有在先有不同的具体科学/应用主张、可获得且measurement/identity合格的数据、明确与现有方法的实质差异时才值得：先做primary novelty/机制必要性审查和最低反证，而非先装饰agent。若提出D-state独特机制，要有更贴近假说的干预/观察校准或独立功能readout及新合法验证；不强求所有探索都有新wetlab。若提出agent/继承/RSI，则需要实际query menu/cost/feedback、分离训练与后续任务、共同fresh start和等预算ordinary retraining/CL/AL/search；RSI还须更新后的improver让后来改进更有效。三个screen/367clusters/75fits不能充当独立科研任务。

资源记录为单次84.46s、75assay fits，五臂各14trials+1refit；本轮无新network/provider/wetlab，selected formula cells=0。此稿未独立重算逐row预测或seal顺序，真实性核对由后续nonfit审计另行完成；不把root产物阅读伪称全量再验证。
