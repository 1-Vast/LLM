# 药物 lesson 合同、ReTTT 迁移及 API 构造的实际交叉

2026-10-22。biology/INDEPENDENT.md 独立封存后实际读 frontier/INDEPENDENT.md、skeptic/INDEPENDENT.md、api/RESPONSE.md，以及本阶段已存 ReTTT rettt.txt 的模型/记忆状态、Sec2.3维护、Eq13/14训练、Sec3.4、A.1成本、A.2重置和A.3证据检查片段。未新请求来源、打开数组/保护值或执行toy；论文数字均为作者报告，本角色未复现。

## ReTTT 是实际局部正面，但反馈认证不能换域

原文 ReTTT 在当前轨迹上产生(type,content,evidence)程序lesson，以schema、有效轨迹引用、字符串规则及任务结果一致性筛选，再维护memory并用token CE更新共享action/reflection的LoRA。Frozen Reflection保留action更新但reflection用初始策略；ALFWorld/Qwen3.5-9B作者报告56.43%→63.57%，即7.14个百分点。应承认适应lesson生成策略的episode内组件收益，不因标准fine-tuning存在而抹去该实际控制。

但环境反馈能确认“操作已成功/前置条件未满足”，与一个噪声viability终点的含义不同。药物未降低growth可能来自暴露不足、剂量/时长、缺少脆弱性、测量控制、细胞混合/适应，不能由字符串一致性认证“靶点无关/路径造成耐药”。可核验lesson至多先记为限定细胞/批次/剂量/时长/单位的测量事实与明确不确定性；跨药物、机制或反事实lesson需要额外证据，不可把生成文本当新分子标签。

并行培养的静态终点不是同一培养的连续状态轨迹；模型checkpoint可复制不等于生物culture可reset。真正连续给药可能改变细胞群体、暴露及可测状态，更新后所预测对象和action条件都须重定，不能把ALFWorld式episode接口直接移植为细胞动态证据。

A.2明确adapter、optimizer state、procedural memory每episode后重置；原文将跨episode consolidation留作future work。因此7.14点不是后续独立研究任务的继承收益或改进策略继承效率证据。论文也明确reflection成本使总worker time不低于aTTT；不能仅以梯度步更少称低总成本。

## 显式 lesson 修改不等于参数去除

删除或替换memory里的旧lesson并训练新lesson，不会自动撤销旧lesson先前写入LoRA和optimizer的影响。状态依赖梯度、其他intervening updates和Adam state使简单减旧gradient不等于corrected-history replay。此处不是指控ReTTT声称exact unlearning，也不据此否定其成功率；这是迁移为可靠科研记忆时新增的明确义务。

独立认证、带时间戳的测量更正可能使此问题有科研价值；但“新测量不同”不等于旧测量错误，可能真实背景/动态已变。没有认证revision stream不能免费删除负证据。本阶段没有这类新生物合同，也没有比checkpoint+optimizer回放或普通线性充分统计downdate更独特的新方法，不应因此加editor。

## 与 frontier、skeptic 的实际双向问答

本角色向frontier发出最强生物质询：string grounding不能认证target/exposure因果lesson，episode reset不支持跨任务RSI，旧显式memory替换不保证参数erase；缺生物verifier新构造则不晋升。Frontier实际答复接受，明确只能支持测量事实及范围明确预测、不能制造分子label，保留ReTTT来源域内局部反思适应贡献。

Frontier反问本角色：真实药理机制不可辨，是否就意味着未测功能决策永远不能改善？本角色明确答复不是；可被支持反馈区分的统计结构仍可能让普通mixture产生实用utility。本角色最小反例只限同分布support但query最佳相反的那一合同，不是全称少量feedback无用；NO新核心不否定普通能力实验价值。共同保留这个问题，但当前不授权旧STOP实验重启。

Skeptic实际质询本角色两结构Bayes稿：T/E若只是statistical labels，功能终点不能认证target/exposure机制；NO_CANDIDATE是否否定研究价值？本角色明确接受：只停止新操作晋升，不否认统计结构选择的实用价值；同式两权重对手证明具体有限操作无差异，不冒充已检索某个完整发表先例。

本角色反问skeptic的SPO推导：baseline相对utility在固定start/history/actionset/weights下只是普通decision loss减常数，但baseline随phi变化、finite估计、episode权重或方差控制不同可能改变具体算法。Skeptic实际接受目标身份不推完整finite训练成本身份，不按family label否定整个updater。

## API PM-SSRP：NOT_RUN，不是性能阴性

API明确输出NO_CANDIDATE后仍给pairmean锚+support-span residual传播，并建议至少5新cell实验。该文字不能直接执行：

- 本项目pairmean是其余八个未测query的平均真值，属于事后评价量；每pair只揭高高角的旧合同并不提供这个均值。若另买完整support-pair曲面，可能合法，但任务、预算、支持集抽样及外推目标都须重立，不能假定免费。预测pairmean也不是实测pairmean。
- m_c从多个support pair聚合改变旧目标pair之间禁pool的明确合同。它不是本阶段授权的旧实验延伸，API声称“不触碰STOP”不成立；本阶段不重开后20cell或其他保护值。
- centered-pairmean error贡献55%/69%是固定预测误差平方的记账，不能推出一个已观测、可独立传播的低维生物锚；投影不是移除/新增训练项的干预。
- swap count只是集合距离。以>7/cell合并regret恶化作为证伪阈值，是从旧描述数目提取任意标准；<=7也可严重恶化、>7也可显著改善。新cell数“至少5”亦未给独立性/效能依据，不是现成许可。
- 固定kernel的span定义与outside-span判定尚未给可执行精度合同；普通RBF插值是否等同所写操作也不能只凭名称。即便补足仍未出现值得打破STOP的新差异。

本角色将swap阈值问题实际发给skeptic；其明确答复接受上述count不等utility，并同意PM-SSRP是信息/操作合同不合格，非已执行性能FAILED。API没有新实验结果，不能写成已证性能不行。决定不运行、不补参数、不下载新数据。

当前NO_CANDIDATE / NO_PROMOTION。保留ReTTT作者域内局部正面和普通功能反馈的已知实用证据，但没有新生物lesson认证器、结构修订算子或可验证独特有限成本性质。完整world/agent/inheritance/joint/improved-improver目标仍ACTIVE / NOT_ACHIEVED。
