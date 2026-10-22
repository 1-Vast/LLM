# TG-GATEs固定中剂量支持的source/development功能空间检查草案

2026-10-22。**DRAFT / NOT_AUTHORIZATION_TO_OPEN / NOT_RUN**。应由root完成化学身份、分区、实际代码及输入freeze后另存正式protocol；本稿不给脚本任何raw开值权限。全部未来test/later目标保持封存，不改旧phase。

## 目的与决定

目标是决定是否值得为“两实测innovation分离迁移”下载/处理CEL，以及是否有必要再做query-agent；不是检验RNA/world性能或宣布没有毒性信号。预设应用是已预筛持续暴露目录中新药中剂量M反馈后，预测最高有效剂量H的24h DNA relative survival。

主要loss为每化学实体等权的 `abs(pred_H_DNA−mean_H_DNA)/100`，报告单位为relative-survival-unit；DNA是唯一主终点。LDH同单位误差完整次要。官方发布的百分比直接/100，不作新control重归一化、不剪到[0,1]、不logit、不把LDH当泄漏率。主候选未来应同时达到 **绝对0.02且相对10% MAE下降**；本检查只问该门在source/dev是否留有误差空间。它是研究工程效用门，不声称为临床安全阈值或重复误差已校准。root若需改，必须在本检查开值前改并冻结。

## 开值前必须完成的manifest

1. 用既有47-label三正剂量双assay身份菜单确定候选；接受root已明确授权的**released-catalog探索范围：47name+PubChem proxy-parent/scaffold保守blocking**。名字解析的primary候选不是源物料CAS真值，alias/盐形不确定及非小分子资格逐项披露，不因尚无完美CAS映射自动禁止整个pilot。去重group数按真实proxy结果，不能保证47独立化学实体或donor。
2. 冻结互斥source/development/later角色和全部sample keys；同proxy-parent/scaffold group不跨角色。无环结构不因空Murcko被并成一组；不确定/多候选的保守阻断和缺失fingerprint处理由root先冻结，不能把unknown hash当新化学实体。暴露过的公共论文/旧目录身份另记，不称原始盲样或真实compound-disjoint生物材料验证。
3. 每condition以 `EXP_ID,compound,canonical dose,original unit,dose level,time`定组，raw sample键以EXP_ID/GROUP_ID/INDIVIDUAL_ID认证；manifest列全原始replicate keys及匹配metadata。不把不同EXP/lot猜成同培养，化学别名合并也不擅自平均不同实验。
4. 将来earlyRNA2h仅表示逻辑成本，此阶段不读CEL。source/dev需要的24h L/M/H DNA/LDH原始记录可读取；later全部剂量/时间outcome禁止数值化、禁止计算min/max/null新统计。既有metadata-only旗标可读取。worker逐raw行先按identity角色过滤，再仅对source/dev匹配行numeric cast。

## 数值与聚合合同

- CSV cp932、单个既定成员，header必须完全匹配旧schema；read raw ZIP会接触包含later字节，明确记录这一字节接触，隔离worker不导出later raw字符串或数值。
- 缺失token沿用旧固定集合；非missing但无法Decimal/float解析、NaN/Inf记invalid，不填0、不删异常后继续原门。所有**有限**发布百分比保留；<0与>100分别作显式质量flag并报告，均不自动clip或删去。当前MAE对有限值有定义，目标是发布assay读数而非强制[0,1]概率；若有超界值，结论不能将该读数逐项当真实生存概率。此规则开值前冻结，不在看到超界后临时救数据。
- 一个condition/time/assay的均值是manifest中**全部原始预列重复**的算术均值；记录n、SD、range（只source/dev）。不能因结果大小挑某个individual。DNA/LDH各自按同keys聚合；未知assay采样依赖不靠均值消除。
- 若任一预列source/dev主DNA数值invalid，第一run以NUMERICAL_QUALIFICATION_ABORT结束，保存键/原因和已接触数量，不自动缩小目录、改终点或重跑。若只有LDH invalid，也不能悄然保留“双assay完整”主张；先结束本合同并决定是否另立明确单assay设计。raw字符串不写异常stacktrace。
- 均值/SD是目录发布重复的描述，不能直接称独立donor噪声下限。重复误差可完整报告，不用两重复推普适assay噪声。

## 三类必要baseline，固定菜单与选择

仅source训练/组内调参，development只作预列模型的headroom评分/方向选择；所有H_dev结果是开发暴露，绝不当confirmatory评估。模型选择及每项failed fit都记账，later从不读取。

1. **prescreen-aware constants**：0.85常数；source H-DNA均值和中位数；主要constant由source grouped-CV MAE选。0.85是利用公开预筛先验的基线，绝不把真实H标签设为0.85。
2. **dose/chemistry direct**：H浓度和H/M比的log、合法单位/设计特征，外加冻结的PubChem-proxy fingerprint；不输入免费L/H功能、H RNA、未来missing统计或compound名字作ID。使用proxy并披露局限，不要求等待真实CAS完美映射；不能以label hash当化学结构。
3. **完整M-functional direct**：M的两assay均值、SD/重复数、H/M剂量及同样化学特征。为尽快执行本路由检查，建议仅预列下述紧凑baseline，不先上树/大网格：M_DNA copy；`M_DNA+source median(H_DNA−M_DNA)`；按proxy Tanimoto最近source化合物迁移其H−M差值；完整特征ridge（正则{0.1,1,10,100}）与RBF kernel ridge（同4正则、核尺度为source训练pairwise squared-distance中位数的{0.5,2}倍）。源fold内拟合标准化、特征/距离尺度；最近邻tie按冻结字符串排序。zero-distance/空结构后备规则开值前写明，不能按功能选邻居。

source CV以proxy-block为单位；若group数少到预列fold不可执行，run在开值前的设计检查即停止而不临时把dose拆fold。没有要求某任意固定N证明功效。正式protocol须按实际group数固定fold；建议source leave-one-block-out，以source OOF MAE分别选择ridge/kernel配置，development不反复调网格。所有baseline同M feedback；CEL成本此阶段为0。这一紧凑菜单是有用的headroom screen，绝不称已经覆盖未来world试验所需全部最强direct/CL/AL比较。

## 预定headroom结论

计算source组外及development的best baseline H-DNA MAE、每药loss和chemical-group不确定性描述。development baseline如果 `MAE≤0.02`，则即使完美predictor，在这个dev样本也无法留下严格>0.02绝对改善：**STOP_THIS_H_CONFIRMATION_CONFIGURATION_FOR_THIS_UTILITY**，不下载CEL来救这个合同。source同样很低则加强路由；不把这个有限样本结论说成所有未来药物无headroom。

若最强M-functional direct仍有 `MAE>0.02`，只说明存在数值改善空间，不证明RNA有信息、两innovation必要或能达到10%/0.02门；GO仅到单独冻结的RNA反馈结构pilot。若CI很宽或source/dev方向冲突，结论是弱证据/未决，下一步应按原门的精度与成本决定，不把点估计正当PASS。不能通过换H目标/改阈值/事后subgroup救低headroom。

## query-agent的额外必要门（可分开冻结）

此阶段M支持固定，不需要agent。若日后比较L/M query，先在source/dev对一个**同一预定updater**生成两动作的H预测，选择在不看H时完成。随后evaluator计算 `best-fixed loss−mean(min(loss_L,loss_M))`，给出两query菜单内的oracle choice headroom。若这个上界小于预设选择收益门，停止该updater下的query选择agent；不停止固定M反馈/world。此oracle只在source/dev开发，不训练时泄漏later H，也不称真实可实现策略。换updater须另列对照和预算，不能把选择与更新同时变而归因agent。

## 成本、记录和停止后续

记录source/dev每compound24h L/M/H功能条件、每assay/重复payload、逻辑bundle总数及实际重复使用；本检查并未新做湿实验。API、HTTP、CPU、fits（含CV和失败）按真实次数；读已缓存ZIP无新download。后续RNAbundle还要付2h CEL全部重复/controls、download/归一化费用，不能由本headroom成本替代。跨arm共享source测量只在预列成本规则下共享一次，失败读数/fit不退费。

所有代码/tests在research，protocol/freeze/raw-exposure/forecast/开发数值/决定在当前log。原47菜单身份及旧STOP只读。无任何world/agent/继承/joint/C4成功可由此headroom检查推出。
