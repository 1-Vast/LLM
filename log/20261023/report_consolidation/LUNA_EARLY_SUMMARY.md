# MAESTRO研究报告整合（注册表39项）
`research/STUDIES.json`中的39项研究各保留一行独立结论、关键指标/限制及可点击归档证据；注册外的2026-10-20/21最终决定另列。所有结论按后续修订优先级整理。
## 跨研究共同边界

这些研究反复检验的是有限任务/数据上的规划、反馈、程序修改或继承；不能由文件、运行次数、agent 调用数、可执行原型或合成环境推出科学支持。**agent/世界模型/RSI 的跨任务增益尚未建立**：相关研究多为暴露开发/公开回放，若组件未被接受或实际行使，则对应效应是未测试而非零效应；若普通模型/简单 refit 匹配，则不应归功于 agent。真实独立确认、前瞻测量的效用和普遍化主张仍缺证据。

# 注册研究全量索引（39/39）

以下逐项对应 `research/STUDIES.json` 的 39 个 `path`。一句话结论采用登记闭合结论并结合最终报告/修订；指标保留能区分结果的最小数字，未测试与无效应严格区分。Markdown 链接直接指向注册的 evidence 文件；括号中补充后续审计/修订。

| 研究 | 最终结论、关键数字与边界 | 原始证据 |
|---|---|---|
| `knowledge_transfer_20261012` | **部分支持**RKT 预测迁移：A1 pooled−generic +0.218、pooled−context +0.033；决策层 MAESTRO 在 11 个批次未胜 sparse_hub（utility .579 vs .623）。公开数据、7线；不能声称规划/LLM优势或前瞻确认。 | [README](../../research_records/knowledge_transfer_20261012/README.md) |
| `context_discrimination_20261013` | **没有agent协同**。84复合物pilot中强固定对照16个相反活性案例，RKT 15、LLM+RKT 12、集成agent 10；效用还受活性条件化和已暴露数据限制。 | [README](../../research_records/context_discrimination_20261013/README.md) |
| `evidence_transfer_20261013` | **协同未确认**：测试方向组学响应的20/20测试化合物中确定性模型14命中，集成/常规agent各12、agent-only 10；公开回顾性数据，不是新培养或通用虚拟细胞。 | [README](../../research_records/evidence_transfer_20261013/README.md) |
| `collaboration_limits_20261013` | **仅支持端点决策校准**：GCP新线命中77/141 vs 55/141（+15.6个百分点），校准 q≥.5 的命中率 .815 vs .379；agent donor残差无增益、memory无学习通路。不是agent优势或新转移模型。 | [README](../../research_records/collaboration_limits_20261013/README.md) |
| `selective_hit_triage_20261013` | **不支持agent**；确认性主张须以纠正后的双重终点结果为准，运行结果曾漏掉一半注册终点，as-run 文件明确排除。提升的是决策审查/claim audit/triage三个工程契约；LLM arms未运行。 | [README](../../research_records/selective_hit_triage_20261013/README.md) |
| `knowledge_reality_20261013` | **只到机制类别**：加知识使选择性profile r .0786→.0842（+0.0056），但保持共享靶/MoA的基因重标即可重现（+0.0057）；独有target身份/上下文及功能价值未建立，G2失败，24Q2未开封。 | [README](../../research_records/knowledge_reality_20261013/README.md) |
| `evaluator_audit_20261013` | **评估契约审计**：发现测试批次归一化泄漏、outcome-derived eligibility/missingness、未冻结身份输入等缺陷；确认阶段未运行且未读24Q2响应。该审计不改写原科学结果。 | [README](../../research_records/evaluator_audit_20261013/README.md) |
| `orbit_contrast_20261013` | **身份价值存在但没有方法增益**：392个冷启动留出化合物中知识含机制类别身份信息；OCEA门控不优于无条件残差/准确率门控，功能遗传知识超出机制类无增益；target triage无决策效用。全数据此前暴露。 | [README](../../research_records/orbit_contrast_20261013/README.md) |
| `mechanism_falsification_20261014` | **机制真值资产受阻**：本地无匹配的实测正/负机制参照，故A1/算法阶段未运行；conformal triage在该样本不可用（约需50万校准单位）。软件契约修复/21任务基准只证明规范符合，不证明机制能力。 | [README](../../research_records/mechanism_falsification_20261014/README.md) |
| `indication_triage_20261016` | **暴露开发结果；传播未测试**：草案的PRISM19Q4开发分析没有冻结/确认阶段，按自身计划 LLM 与L1000阶段未建；后续核查发现早期“hits”主要是对已探测细胞重读（394/395、293/293），不能算未测对传播。 | [README](../../research_records/indication_triage_20261016/README.md)（[后续纠错](../../research_records/feedback_propagation_20261018/REPORT.md)） |
| `presage_transfer_20261016` | **P0 NO-GO**：真实路径+通路模型 top-3 命中率14.01%，训练线均值14.49%、化学邻居15.77%、化学+target/MoA邻居16.36%；其增量对化学+机制仅+0.0028 [-.0020,.0083]。PRISM暴露开发，P1-P3/LLM未运行。 | [REPORT](../../research_records/presage_transfer_20261016/REPORT.md) |
| `anchor_purchase_20261016` | **独立端点受阻**：1,200核心仅794满足三列身份规则；终端配对44.5%未知，独立培养/物理成本不能认证。已知命中数不能定总效用；政策模型未拟合，故非锚点无效证据。 | [REPORT](../../research_records/anchor_purchase_20261016/REPORT.md) |
| `context_transfer_20261017` | 注册框架名为CONFIRMED，但修订后只支持Beat AML内功能反馈：maestro−vc0 +.073 [.025,.127]，低于有用增益门槛.05；与exploit-first完全相同。不能声称agent适应、超过固定流程、RNA先验或成本优势。 | [REPORT](../../research_records/context_transfer_20261017/REPORT.md) |
| `feedback_attribution_20261017` | **反馈归因；无RNA先验/selector优势**：主要D−B +.065 [.030,.105]，虽为正但下界未超过每轮成本阈值.05；RNA先验没有超过强静态ridge，普通ridge+反馈可匹配探针收益。暴露Beat AML开发。 | [REPORT](../../research_records/feedback_attribution_20261017/REPORT.md) |
| `program_revision_20261017` | **revision NO-GO，早期seed增益被推翻**：原I2 +.211经合同修复为+.117 [-.026,.248]，I1 +.283 [-.065,.699]、policy +.356 [-.088,.856]均未确认；seed是预设程序库而非agent发现。 | [REPORT](../../research_records/program_revision_20261017/REPORT.md)（[seed归因修订](../../research_records/seed_attribution_20261017/REPORT.md)） |
| `seed_attribution_20261017` | **修正后的seed收益未确认**：合同修复后I2 +.117 [-.026,.248]、I1 +.283 [-.065,.699]、策略+.356 [-.088,.856]；可用性加权只是敏感性分析，数据暴露且21谱系组，不是独立确认。 | [REPORT](../../research_records/seed_attribution_20261017/REPORT.md)（[2026-10-18区间勘误](../../research_records/seed_attribution_20261017/ERRATUM_20261018.md)） |
| `beataml_g1_20261017` | **G1失败，停止低秩分支**：候选对ridge +.098 [.045,.153]，扣除额外轮次后下界−.005；ridge加同样反馈已基本匹配。暴露开发数据，不证明反馈普遍无效。 | [REPORT](../../research_records/beataml_g1_20261017/REPORT.md) |
| `feedback_propagation_20261018` | **停止repair程序搜索**：注册R1仅2.78 vs ridge+feedback 2.64、kNN 2.69未过有用门槛；更关键的是早期命中大量重读已探测对。模拟噪声两次结果差异大，无独立池/真实成本。 | [REPORT](../../research_records/feedback_propagation_20261018/REPORT.md) |
| `acquisition_program_20261018` | **留出组无采集搜索增益**：fixed A-optimal 1.822事件/64 compounds，lookahead 1.717（−.106 [-.262,.022]），agent程序1.725；实际反馈优于无反馈，但策略均为暴露开发/假设池成本。 | [REPORT](../../research_records/acquisition_program_20261018/REPORT.md) |
| `observable_state_20261018` | **撤回agent及typed-edit主张（本arena）**：agent确认率.081，enumerator .059、random .051；agent−enumerator +.022 [-.022,.074]，未达到实用阈值.10。target-gene rule .088只是未校正探索线索；决策效用未测试。 | [REPORT_OBS](../../research_records/observable_state_20261018/REPORT_OBS.md) |
| `eg_rpt_20261019` | **草案未运行，无transfer model**：首个H0头间可重复性/效用空间尚未过门，不应把“131 vs 100”回顾性最好情形当证据；没有模型拟合、封存数据、API或独立验证。 | [PROTOCOL](../../research_records/eg_rpt_20261019/PROTOCOL.md) |
| `maestro_far_20261019` | **该arena不支持FAR**：test中FAR−exploit-first +.006 [-.003,.018]，未过冻结下界+.010；失败签名AUROC约.5。assay+repair本身有收益但非FAR特异；agent/2×2/transfer未运行。 | [REPORT](../../research_records/maestro_far_20261019/REPORT.md) |
| `replicate_decisions_20261019` | **仅D1支持，D2不支持**：复制噪声后验改善同药背景选择 +.118 [.084,.157]；跨药progression −.008 [-.037,.025]。暴露PRISM开发数据，留存用于窄决策场景。 | [REPORT](../../research_records/replicate_decisions_20261019/REPORT.md) |
| `heavy_tail_rsd_20261019` | **重尾噪声未修复D2**：heavy-tail−raw D2 +.015 [-.014,.046]，低于阈值；选中药80%区间覆盖仅.690。D1方向保留但不达阈值，第二次实测读数仍是强比较。 | [REPORT](../../research_records/heavy_tail_rsd_20261019/REPORT.md) |
| `decoupled_calibration_rsd_20261019` | **解耦校准保持、仅开发；决策相同**：对已暴露HTS002做开发读数，校准变化未改变任何冻结决策；确认阶段因无授权未开。数字详见 [DEV_RESULT](../../../data/processed/research_results/research_records/decoupled_calibration_rsd_20261019/DEV_RESULT.json)。 | [DEV_RESULT](../../../data/processed/research_results/research_records/decoupled_calibration_rsd_20261019/DEV_RESULT.json) |
| `action_substitution_20261019` | **窄结论；停止同家族替代主线**：交互端点的partner条件可重复部分可改善预测误差17%，但预测变好没有转成净决策收益；功能相似优于注释同靶参考。仅暴露Jaaks开发数据，agent/协同未测试。 | [REPORT](../../research_records/action_substitution_20261019/REPORT.md) |
| `kinobeads_substitution_20261019` | **不支持binding作为替代性信息**：binding kernel比功能核B5更差（MSE差−.000059 [-.000115,-.000010]）；AUROC .635 [.476,.738]未过机会水平。暴露数据，关Jaaks binding支线。 | [REPORT](../../research_records/kinobeads_substitution_20261019/REPORT.md) |
| `biological_residual_gate_20261019` | **样本量不足且Gate3失败；停止此action space**：目标注释至多约+2.8%，生物不匹配预测错误AUROC .48；可选动作的机会仅.012，低于最小有用.02，即使完美selector也不足。 | [REPORT](../../research_records/biological_residual_gate_20261019/REPORT.md) |
| `implementation_identifiability_v1` | **工程逻辑成立、biology被资产阻断**：AURORA-A已知案例可测逻辑，但没有同条件终点对照、数值终点和谱系；G2-G5未运行，不能说已区分抑制与降解。 | [REPORT](../../research_records/implementation_identifiability_v1/REPORT.md) |
| `implementation_identifiability_v1_audit1` | **audit1不改变asset block**：10/10 mutation checks、v1 byte-identical replay；Level3/4观测为0，G2-G5仍未跑。资料缺口不能被逻辑验证补成生物机制证据。 | [AMENDMENT](../../research_records/implementation_identifiability_v1_audit1/AMENDMENT.md) |
| `functional_rule_revision_20261020` | **不支持规则修订**：候选−refit −.0005（报告区间[-.0008,+.0005]），部署均退回refit；但后续SVC指出去重pair bootstrap不是标准bootstrap，区间仅描述，不能声称排除有用增益。 | [REPORT](../../research_records/functional_rule_revision_20261020/REPORT.md)（[SVC审阅](../../research_records/self_improving_virtual_cell_20261020/REPORT.md)） |
| `self_improving_virtual_cell_20261020` | **prototype可执行，效用无支持**：主要T/B16 evo_full−refit −.0009，delta_use .00645；E路线超过直接确认无决策空间。所有数据暴露。 | [REPORT](../../research_records/self_improving_virtual_cell_20261020/REPORT.md) |
| `innovation_validation_20261020` | **H1/H2/H3/H5无支持，H4未测**：diagnostic acquisition相对latent+A-optimal仅+.0017，低于margin .01；继承差−.0000；H4实际药理效用未测。后续修复纠正KG/继承实现缺陷，但仍未建立独有收益。 | [REPORT](../../research_records/innovation_validation_20261020/REPORT.md)（[repair1](../../research_records/innovation_validation_repair1_20261020/REPORT.md)） |
| `innovation_validation_repair1_20261020` | **工程修复/开发诊断，不建立innovation**：修复KG估计值由错误−.0010恢复至解析值约.1606；严格旧检查点仍失败，等资源H2/真实药效未测试，原评估未被重写。 | [REPORT](../../research_records/innovation_validation_repair1_20261020/REPORT.md) |
| `procedure_inheritance_20261020` | **关闭：无fresh one-step之上的实用收益**：B=3 plan +.00755、低于冻结margin .01；同B对lookahead +.000955、对distillation +.000153。八个合成流，实测药效未测试。 | [REPORT](../../research_records/procedure_inheritance_20261020/REPORT.md)（[audit1](../../research_records/procedure_inheritance_20261020_audit1/REPORT.md)） |
| `procedure_inheritance_20261020_audit1` | **只读审计，原关闭不变**：重放3,840行为行并修正成本/primary gate；移植内容未执行，新regime修复循环及药效都未测。有限合成两seed结果不是开放式进化证明。 | [REPORT](../../research_records/procedure_inheritance_20261020_audit1/REPORT.md) |
| `self_repair_qualification_20261020` | **无单元满足超越refitting的self-repair**：Beat AML后续shift可由普通逐药offset修复（top-5效用+.370 [.257,.497] vs静态covariate）；其结构成因无法识别，暴露开发。 | [QUALIFICATION](../../research_records/self_repair_qualification_20261020/QUALIFICATION.md) |
| `dual_core_innovation_validation_20261021` | **停止此PTV任务配置**：7 final lineages上ppODE−B1 precision@5 −.229 [-.286,-.200]；无LLM edit被接受，组合未测试。公开数据回放，不推论所有世界模型或agent。 | [REPORT](../../research_records/dual_core_innovation_validation_20261021/REPORT.md) |
| `dual_core_innovation_validation_20261021_repair1` | **工程修复完成，innovation未建立，原STOP保留**：更新PPODE对冻结仅+.143 hits [0,.429]，仍低于强blend/kernel比较；最终数值已暴露，整目录快照漂移触发exit 2。 | [REPORT](../../research_records/dual_core_innovation_validation_20261021_repair1/REPORT.md) |

## 指定日期日志中注册表外的最终决定

- `log/20261021/rsi_next_qualification/DECISION.md`：未晋升新核心；PTV同配置不扩模，RSI候选仍只是未过资格的普通条件预测假说；DMG功能目标路径/剂量信息路径未认证。公开暴露的7-lineage PTV内，简单0.5 PPODE+0.5 B1的正向开发信号不能与14药池、dev+selection训练下的消融拼接归因。并不证明RSI一般不可能。
- `log/20261021/oasis_source_qualification/REPORT.md`：只确认OASIS功能动作菜单的基础覆盖并允许继续身份/QC协议准备；1,085药标签×8剂量可形成8,680动作，但不是严格双重复（72动作记录数>2），160重复键待解释；67/68个plate目录有CellPainting来源对象，尚未认证well级配对。一个五供体PHH混池，不支持新供体/背景或RSI确认；没有读功能值、拟合或筛选候选药。
- `log/20261020`中额外最终摘要仅`SELF_REPAIR_QUALIFICATION.md`，对应上述注册研究；其他文件为次步prompt、准备/清理记录或注册研究日记，不是额外独立最终科学决定。

## 覆盖与阅读说明

覆盖表的机器清单逐字采用 `research/STUDIES.json` 每条study的 `path` 与 `evidence`，并纳入登记的 `superseding_audit`；39项均存在并已逐项打开最终evidence，审阅时未读取原始大数组/payload。`COVERAGE_EARLY.json` 另列两份注册外最终决定日志。`research/REPORT.md`、`research/EVIDENCE.md` 与各修订用来交叉核对优先顺序。覆盖是导航记录，不是科学质量计分，也不以研究数量证明结论。



