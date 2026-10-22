# 建设性反方独立稿：把两种已测创新量分开，检验修复能否跨剂量与化学组继承

2026-10-22。总体目标 **ACTIVE / NOT_ACHIEVED**。本稿封存前未读任何本轮其他代理稿。已知root任务、历史共享摘要与先前renewal交叉材料，故不称历史全盲。此次直接运行维护中的DeepSeek client，session66990已exit0：1logical/provider call、16,775tokens（prompt1,624/completion15,151）、model `deepseek-flash`、response SHA `c4b53be8dd4ba637f494c915be4915fd0ffd03182cdf8ff4a4855a643f999876`。未执行生成代码；新HTTP=0、新生物数值=0、新fit=0。

## 一、推荐一个正向经验贡献，不宣称已有新算子

**候选主张：在TG-GATEs已预筛的持续暴露菜单中，已购中剂量的早期RNA预测误差，与在实际RNA条件下仍存在的24h功能预测误差，包含不同的、可跨剂量并跨化学组迁移的修复信息。先修状态、再仅传播剩余功能误差，比把两项误差当同一标签信号、统一offset或只在功能头重训练更有效。**

这是“什么错误可以继承”的具体科学未知。早RNA→毒性、普通kernel、低秩回归、顺序条件化或Gaussian innovation都已有，不是本稿发现。最邻近的普通实现是联合状态/功能协方差模型的顺序条件化；若训练、信息和约束完全相同，必须合并同一方法。贡献候选是可被强普通模型推翻的**反馈结构与有限样本预测规律**，尚不是论文级新核心。只有跨化学验证、必要性消融及实际确认效用幸存后，才值得考虑更广资产上的继承/智能体。

这一选择改进本人旧“响应kernel迁移”草案：直接问哪项反馈修复哪部分预测误差，避免把所有反馈一股脑乘分子相似度；也比provider新加的残差锥/F-S-R模块简单。它不识别真实致伤机制，不要求个体同细胞配对，也不把条件均值的预测分解称因果中介。

应用固定为体外安全性确认辅助：在一个已筛选新药上，买一次中剂量condition bundle后，预测同药最高有效剂量24h DNA relative survival；LDH relative survival完整次要报告。低剂量是后续可选查询动作，第一关先固定中剂量，避免状态结构与主动选择混杂。并不直接省掉所有最高剂量湿实验；能否减少确认预算是后续决策实验要测的效用。

## 二、最小操作：10行

1. 元数据先冻结有效正L/M/H、chemical-parent/scaffold角色及曝光；H的RNA/function在later-task中均不可见。
2. 仅source训练 `f(drug,dose)→early RNA state` 与 `g(state,drug,dose)→24h function`；source按chemical-group交叉拟合所有误差。
3. 从source的组外预测构造分子创新 `u_d=x_d−f(drug,d)` 与条件功能创新 `v_d=y_d−g(x_d,drug,d)`。
4. source学习低秩强收缩的跨剂量映射 `B_x:u_M→u_H`，以及 `B_y:(v_M,state/dose context)→v_H`。
5. development仅选择预列rank/shrinkage、是否使用RNA context；冻结后不碰later H。
6. later所有方法取得同一M剂量bundle：实际2h RNA重复和24h DNA/LDH读数；H不购、不提供。
7. 状态修复 `s*_H=f(drug,H)+B_x[x_M−f(drug,M)]`。
8. 功能修复 `y*_H=g(s*_H,drug,H)+B_y[y_M−g(x_M,drug,M)]`。
9. 所有特征/标准化/误差模型由source内构建；later只应用已冻结程序，先保存H预测再揭示H。
10. 与同信息joint predictor、ordinary conditional covariance及全history direct比较；精确复制品合并，不制造world/direct双标签。

允许 `B_x=0` 或 `B_y=0` 作为真实消融；若最简单一个为零模型最好，就删除无必要模块，不为满足框架图保留。`g`可为线性低秩/非线性共享头，但比较必须匹配源辅助RNA标签、完整已付history及程序预算。高维表达不适合47label随意搜，先冻结小维source-only表示与普通四基因签名。

## 三、数据、分区与第一项能改变行动的check

已认证metadata是47个标签、每药三个严格正且不同浓度、2h CEL及24h两功能完整。它们不是47独立parent、donor或前瞻任务。功能raw ZIP已在旧phase sealed_source，身份布尔投影可复用；本候选未开真实值或CEL。DNA/LDH都是官方relative-survival百分比，不剪到[0,100]、不未经检查logit，不把LDH视为原始泄漏。高剂量按survival预筛/溶解度限选；本应用条件于该菜单。

先做两个廉价门，才付CEL/复杂程序费用：

- **身份门**：对47标签认证parent/结构（无Murcko环的药不共享空scaffold）、固定source/development/later角色；报告去重后group数及有效分区。不能把hash标签等同于化学隔离。
- **source/development-only功能headroom门**：预先冻结目标、归一化单位、聚合、不完整/非有限处理和实用效用；仅解封source/dev的L/M/H功能，later全部封存。比较prescreen-aware constant、dose-only与M-dose功能直接模型。若最强baseline误差连预设绝对改善空间都不剩，停止该最高剂量确认配置；不靠下载RNA或改阈值救。

建议把0.02relative-survival-unit并且10% MAE改善作为研究筛选门，**这只是待root/双方在开值前冻结的工程门，不是噪声已证或临床阈值**。公开Zhang原文已有group平均DNA差异等结果，不能当新raw值或据此选择test子集。两个重复只能做粗略重复差异；不得把同一原代培养来源/归一化的重复差叫普适assay噪声下限。

身份与headroom过关后，source/dev组外拟合最小10行程序，H的DNA MAE为唯一主终点，LDH及联合误差完整次要。先检验 `u_M`对`u_H`、`v_M`对`v_H`是否在chemical+dose、普通四基因、M-function与完整同信息direct之外提供稳定可用的增量；随后才一次性评later。这个真实数值check会决定是否值得深入，而非再做一个只证普通代数可复现的toy。

分区比例需以认证group数和预期区间精度决定，不能先冒称足够。47label最多支持小样本目录pilot；可以冻结source/dev/later角色并对source做grouped-CV，不能把折数或剂量数当独立N。若无足够独立later groups，做明确的探索性估计并另找外源确认，不把原test改成dev来增加成功机会。

## 四、最强反证与各模块必要性

必须给普通full-history direct同样的sourceRNA监督、实际M RNA/function、chemical+dose、mask；也给强ordinary factorized/joint covariance/conditional kernel同样的数据和拟合机会。仅打chemical+dose弱模型不证明world。联合Gaussian条件化若精确得到相同两步修复，是同一方法而非竞品。

必要对照是：无反馈；只有功能反馈；只有RNA反馈；统一offset/dose曲线；只修状态；只修功能；两误差直接相加；同信息联合低秩条件预测；全量普通重训/正则few-shot/continual；source固定与继承更新；简单混合及同候选数程序搜索。真实的状态贡献须通过RNA监督/响应残差的具体结构消融成立，不靠名称。

source-only表示与置乱合同要预先固定。把M RNA跨compound置乱时保持dose、batch/可得设计分层与尺度；将conditional功能创新跨组置乱；用四基因stress替代完整状态；以保持范数/rank但破坏对应关系的source配对置乱检验。**不能把全空间可逆旋转、同时重拟合可旋转模型当有效阴性对照**，因为这可能只换坐标。若普通joint模型完全解释两阶段收益，不宣传新更新算子；若RNA置乱不影响收益，状态反馈解释失败；若仅一个assay/后选子组有利，主主张失败。

停止：identity不支持任务；source/dev无实用headroom；跨组预测无增量；强同信息模型饱和；只在已见近邻/批次有利；RNA置乱/四基因/offset足够；表达成本吃掉净效用。停止此配置，不推成世界模型或RNA反馈普遍无效。

## 五、agent、继承及C4：明确可检验，但不能本轮冒报

首个固定M实验只测反馈结构。随后agent才在固定L/M menu买一bundle，和固定L、固定M、随机、ordinary AL/uncertainty/基于预期高剂量MAE下降的query策略比较。H目标始终固定，完整bundle/CEL/functional/预处理/拟合/provider成本都记账。若买M几乎总好，固定策略就是结果，不需LLM。

模型继承是在相同source初始化、相同新任务起点与已购历史下，允许保留 `f/g/B`，比较普通全量重训与CL；程序继承只保留rank/shrinkage/哪些误差分支/查询优先级，模型参数重置；joint保留两者。必要factor对照分别报告W、A、模型/程序继承及joint净收益，不要求超加和；world与direct同构部分合并。

**正确C4应比较同一种improver的早/晚checkpoint，不能拿“更新T/G”与“更新π”两个不同功能当old/new证据。** 可执行有限合同是：

- solver `P0`固定为上述source predictor及更新程序字典；所有later测试都从同一 `P0`、同一已购M history与相同源校准episode bank开始；H目标从不作候选选择。
- `J_old`为初始proposal scheduler；`J_new`是从早期任务已揭示H反馈得到的**同一scheduler**后期checkpoint，改变对“state/head/both、rank/shrinkage、查询规则”的proposal优先级及评估后修订规则。
- 两者取得同一可得历史、相同代码/字典/校准反馈、K次候选程序评估、同API/CPU上限；候选只在共同source校准episodes和已付support上验证。先封later H预测，再由隔离evaluator评分。
- 主指标是common-start从 `P0`获得的later H损失下降与候选评估数的面积/同K最终改善；J_new要让**改进过程**更有效。单纯起始predictor更强不算。
- ordinary fixed scheduler、meta-learned selector/retrieval、random/grid/枚举搜索都能保留并使用同一历史、同候选字典和预算，不能通过禁止其继承而造优势。若K足以完整枚举，就不应预期优先级有最终优势。
- 可比较结果将属于有界离线改进效率，尚非无限加速或前瞻药物发现。47label若不足以隔开source、策略学习、独立later检验及精度，就C4 NOT_TESTED，不任设“12task/3round”当充分功效证明。

这是后续合同草案，当前没有实际common-start运行；不把source/dev模型选参叫RSI，不把旧数据上的代码变化当能力改进。

## 六、provider响应的吸收与否决

响应建议DNA/LDH共同轴/分离轴、残差锥门控F/S/R，主动拒绝迁移，有可解释性优点。但至少六项必须修：它给出未经数值认证的logit；操作有时同时用L/M两bundle但成本写成一个；随机旋转可能不改变模型；F/S分支可能输出同构；给出任意12task/3round不能证明功效；C4把两个不同功能improver及被禁止继承的ordinary search比较，未固定同一later起点。故**不按provider稿直接建框架**。

本稿只保留其提醒：功能错误不是一项无结构标量，拒绝传递可减少负迁移；但在首个小样本check中先用最简单收缩和分支消融，不上残差锥/三个策略/可编辑程序。尚无新核心清关；推荐身份+source/dev headroom之后的一项真实两反馈结构检验，而非继续纯source列表或纯算法命名审查。
