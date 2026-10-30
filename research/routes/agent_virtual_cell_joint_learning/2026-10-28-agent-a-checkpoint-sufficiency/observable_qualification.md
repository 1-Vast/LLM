# 四组校准读出与功能端点：来源资格

2026-10-28。责任B；仅离线来源核读。未读取本轮A输出，未打开 `data.txt` / `pert.txt` 数值，未拟合或统计响应。effective_model / effort：unknown。

**结论：AKTpS473、S6pS240可按原始同名节点作固定面板分析；MAPK和GSK3可建立有原补表支持的来源内部对应，但必须保留其非逐字别名及抗体/亚型限制。原始CV筛选和“三个生物重复”的文字不足以恢复逐条件噪声或设定生物等效界限。`cellviab`最清楚地对应72h resazurin细胞数估计；细胞周期时间和节点变换仍有歧义。**这些限制不否定机制，也不自动阻止明确限定的条件层固定面板描述/预测。

## 1. 四组逐项资格

直接核读原始补充DOCX的Table A/B，以及作者网站的 `node_index.txt` 标签；不用已有自动别名表代替原件。

| 校准组（Table A） | Table A校准读出 | 原Table B蛋白/位点 | 网站82蛋白区的节点 | 对应结论 |
|---|---|---|---|---|
| AKTi 1/2、ZSTK474 | AKTpS473 | AKT / S473 | AKTpS473，index第7行 | **精确同名。**可选作来源中的AKT-S473抗体读出；不扩成AKT全部活性或某一AKT亚型。 |
| Temsirolimus、RO-31-7549 | S6pS240 | S6 / S240 | S6pS240，第44行 | **精确同名。**可选作来源中的S6-S240读出；不与S6总量或S6pS235合并。 |
| PD0325901、PLX4720 | MAPK1pT202 | ERK/MAPK1 / T202 | MAPKpT202，第3行 | **有作者表B蛋白/位点支持的内部对照；非作者明确声明的token别名。**可在预先声明映射规则的来源内描述/预测中对应；保留原token。不能声称已解决外部标准蛋白ID、ERK亚型或双位点抗体语义。 |
| P6、SR | GSK3pS21 | GSK3-αβ / S21 | GSK3abpS21，第14行 | **有作者表B支持的内部对照；非逐字同名或明确token别名。**可在预先声明的来源内映射中使用；只能称作者标注的GSK3-αβ/S21测量，不能改成GSK3β-S21或断言α/β单亚型特异性。 |

这里的Table B标题明确为“Proteins that respond to at least one perturbation and exist in models”。其41个数据行每行左右各一项，共列82个蛋白/位点条目；不提供抗体厂商、catalog、clone、lot或校准Western blot的具体抗体。节点index中相应四项都位于蛋白节点区，功能节点另列第83–87行。

MAPK组不是仅凭常识猜测：Table A的`MAPK1`与Table B的`ERK/MAPK1`共享作者明确写出的`MAPK1`标识，T202相同；JATS Figure 6 caption另明确称“ERK phosphorylation at T202”。但作者没有写“`MAPK1pT202` is an alias of `MAPKpT202`”，也没有给该抗体的catalog或表位证书。本核读不借外部常识把作者的T202、MAPK1和其他ERK亚型编号静默校正。

GSK3组中Table B还分别列`GSK3-αβ / S9`和`GSK3-αβ`总量，表明作者区分了不同测量条目；不能把S21、S9、总量互换。`ab`与`αβ`在这份来源内部有很强命名对应，但单凭这些名称不能确定抗体是否同时识别两个亚型、各自位点贡献及交叉反应。机制解释需保留该不确定性。

**所有四组共同的限制：**Table A的IC40是Western blot校准的“presumed target or downstream effector”读出；RPPA在24h以抗体检测。原件没有证明校准WB与RPPA使用同一catalog/表位/批次，也未证明校准时点与RPPA相同。它们是作者选定的作用校准线索，不等于直接靶标占据，不等于两种药在24h实测相同，也不等于两种药的其余作用相同。

JATS `s4-1-1-4`明确提醒单表位抗体会检测多种磷酸化状态的混合物：例如anti-AKTpS473可能同时结合AKTpS473和AKTpS473_pT308；作者为数据库先验采用strict mapping，不会使实际抗体信号变成单一分子状态。因此`AKTpS473`也只能作为测量算子输出，不能解释成唯一分子实体或完整机制状态。

## 2. CV与重复：作者说了什么

JATS `s4-2-2`的原文是：

> Three biological replicates are spotted for each sample (i.e., drug condition) on RPPA slides.

应保留作者的“biological”表述，不能未经证据把它改成技术重复。该段还说明每张slide用一种抗体，先按Bradford调蛋白浓度、MicroVigene定量、按标准RPPA程序归一化，再相对对应无药对照log归一化。筛除规则为：

> eliminated those readouts with intra- or inter-slide coefficient of variation >0.15 ... and low degree of staining by antibodies

138原始实体经质量筛选剩100，再以“至少对一次处理有响应”筛成82。这个两阶段过程是面板定义，不是本轮可据以调阈值的噪声样本。`s4-2-3`迭代信号检测中的σ是“standard deviation of the overall data”，跨响应点迭代剔除强信号；它不是按条件估计的生物重复标准差。

目前原件没有给出四个读出的逐条件CV、各独立培养/slide/spot的ID、逐重复数值、与无药对照的协方差或全部条件的聚合公式。不能从“没有超过0.15的readout被保留”反推出每一对读出差异的误差条，更不能把0.15当作`±0.15 log2`、SE、95%界或生物等效阈值。等效界限本来还需科学意义上的容差，单独一个精密度筛选阈值也不能给出它。

JATS `fig6s2`专门对c-Myc RPPA图写“Each data point is the average of RPPA readouts from three replicates”。这确证该图是三重复平均；没有授权把这一图注外推为所有89条件所有节点在公开矩阵中的聚合方式。功能验证Figure 6的JQ1组合有三生物重复及SE/SEM图注，但属于后续验证实验；不是全部89训练条件功能端点的可恢复重复轴。

补表E所谓CI/coverage来自1000或4000模型的预测分布及交叉验证覆盖率，不是实验生物重复噪声。网站模板中`Average response`与`Standard deviation`也位于simulation结果区，不能拿来当原始测量均值/SD。

**可支持的统计层级：**目前不能从以上原件单独做生物等效、给新生物CI或依据点差否证机制。若根协调核齐响应语义，可预先冻结四组全部保留、标明别名层级，进行条件层、固定面板的回顾性预测/描述。留出伙伴、重采样条件或随机seed可评价相应预测稳定性，不能充当独立生物重复。这里不因缺噪声估计或缺物理剂量换算，自动否定token级预测可行性。

## 3. 独立功能端点到底是什么

网站node index的五个功能标签为`G2M`、`G1arrest`、`G2arrest`、`Sarrest`、`cellviab`。它们是功能读出节点；不代表五个独立实验任务，也不等于五种分子机制。

| 端点 | 原件可确定的测量合同 | 时间、聚合与解释界限 |
|---|---|---|
| cellviab | JATS `s4-2-4`：resazurin，44µM孵育1h；530nm激发/590nm发射；利用细胞数标准曲线估计各sample的cell number。Figure 2给相对无药`log2(perturbed/unperturbed)`语义。 | **72h after drug treatment明确。**这是经代谢荧光校准的细胞数/viability代理，不是直接活细胞计数、直接死亡、凋亡比例或患者效应。原段未给全部89条件各重复到公开单值的聚合/误差公式。 |
| 细胞周期四标签 | 乙锭染色细胞核DNA含量的流式群体分布；收集悬浮及贴壁部分；记录G1、G2/M、S及sub-G1比例。Figure 2说以处理/未处理的细胞周期状态百分比作响应。 | **时间未闭合：同一Methods开头写flow为24h，后文写72h后收集。**Figure 6及`fig6s3`的后续JQ1验证明确24h，不能据此统一89条件。`G2M`与`G2arrest`如何分别由G2/M、sub-G1或其他门控转化，现有文字未明确；不自行把`G2M`改作sub-G1或凋亡。 |

“All phenotypic measurements are made in perturbation conditions identical to those of proteomic measurements”支持相同名义处理条件的跨测量对照；它不证明同一个细胞的24h信号与72h命运被追踪。RPPA裂解、流式采样和resazurin使用不同测量，当前只能建立**条件层的信号摘要—功能摘要关系**。不能据此拟合并宣称已识别个体细胞的`Law(Y|m)`、同状态的因果中介或细胞轨迹。

因此本轮若选择主功能端点，`cellviab`是来源合同最清楚的候选；这只是资格推荐，不基于任何响应值好坏。细胞周期应单独标注时间/构造歧义；需要时仍可作为原标签预测目标进行限定分析，但不能同时声称已解明其精确生物测量时刻或四输出相互独立。

## 4. 可交给协议冻结的字段

- 精确同名组：AKTpS473、S6pS240。
- 显式保留原token的来源内部映射组：`MAPK1pT202 -> MAPKpT202`、`GSK3pS21 -> GSK3abpS21`。支持是原Table B蛋白/位点，不写成作者明确别名声明；不借结果决定是否启用。
- 解释单位：作者选定的抗体读出/条件摘要；不是完整靶标程序、唯一亚型或直接占据。
- 蛋白时间：24h；最清楚功能端点：72h resazurin cell-number proxy；流式时间与节点变换另留unknown。
- 当前噪声资格：作者声明RPPA三生物重复，但未恢复逐条件误差/公开单值聚合；CV阈值及模型ensemble区间不可代用。
- 当前可做与不可声称：允许预注册的固定来源、固定82面板、条件层回顾性预测/描述；不凭现有信息给生物等效/机制否证/个体Law/独立决策或跨背景迁移结论。

本轮网络请求/主题查询均0，新增核心来源0，未读取data/pert数值，未修改旧B-F1或任何src。小证据清单为同目录`observable_evidence.json`，保存原件URL、当前SHA256和阅读定位。
