# ALMANAC：普通组合反馈有效，尚无新核心机制

2026-10-22。完整目标 ACTIVE / NOT_ACHIEVED。本轮 **PROGRESS**：实际完成新的官方功能数据试验、独立原始坐标/数值和指标复核、两个选定模型的独立重训，以及不同立场的实际交叉质疑。本轮不是完整科研目标达成。

## 已验证的有限任务与结果

FF实验室内、已知药物样本对向新细胞迁移。不是未见药对、跨实验室、动态细胞状态或真实付费实验。纯元数据重建将150525完整3×3网格按canonical NSC+SAMPLE+实际剂量/细胞合并为148681任务；1844重复组各两份，响应前固定保留最小原CSV行号的完整代表。相关12859个physical(lab,study,plate)均仅一cell，消除了本资格范围内跨cell同板条目重用，但并未认证全部培养/控制独立。

60数值cell键固定hash分20fit/10tune/10development/10selection/10later。前40完整共同目录887samplepairs、35480网格，2148其他pair-dose方案因覆盖不全排除，非响应筛选。不模糊合并样本或实际浓度；无nearestdose补齐。后20cell响应关闭；不同资产的历史reserve也未访问。

唯一主数值PERCENTGROWTH/100，不裁负值。B0使用本pair六单药，B1增加最高×最高组合读数，共同预测其余八点。禁止跨目标pair锚点池化；源细胞可用同目录完整曲面。仅解码442191唯一允许行：122871solo+319320combo。不是用作者EXPECTEDGROWTH/SCORE泄漏目标；NCI基线由合法solo重算。

15个固定普通候选/预算，B1多一个整套B0回退（已披露选择机会差异，不宣称等预算程序搜索优势）。包括NCI、源pair均值/半锚点平移、线性ridge、非线性RBF、普通联合Gaussian与固定混合。20fit→10tune选程序，30source重拟合→10development。结果如下；MSE均在共同887×8 query上先cell内再10cell等权。

| 冻结程序 | B0 MSE | B1 MSE |
|---|---:|---:|
| NCI单药期望 | .0145518811 | .0145518811 |
| pair均值 / 半锚点残差平移 | .0102288647 | .0114071985 |
| 同参数RBF带宽2/λ.01 | .0091307609 | .0084953821 |
| 源选整套程序 | .0094443827 | .0084953821 |
| 源选程序，同pair排除同study后重拟合 | .0100466787 | .0094438057 |

选择B0为RBF2/λ.1，B1为RBF2/λ.01。主gain .0009490006，即MSE降低 **10.05%**；10/10cell改善，固定预测cell bootstrap95%gain[.0006250735,.0012859533]，剔任何单cell平均仍正。same-pair study排除后source各20–30cell、gain .0006028730（约6.00%），预定5门均真。区间条件于固定预测和共同目录，不含完整模型选择/训练变异、测量噪声或全局study独立性；是开发分配门，不是临床有效或独立生物学显著性认证。

事后描述（不改选择和门）：495/887pair平均改善，最大pair占净gain9.84%，八query位置均正。13个非平凡固定学习程序均因anchor改善，但它们相关而非13次独立复现。82.45%gain集中在邻近高高角的三个query位置。B0开发oracle为RBF2/λ.01；同参数B1相对它平均MSE约改善6.96%，只作诊断，不替代冻结主比较。Gaussian与固定mix未胜selected B1，因此当前最强正结果来自普通直接预测器。

## 功能排序的关键反证

固定目录每pair八点平均growth，预测选最低10%（89对）相对真实最低89对的mean-growth regret：主分析 .0086369803→.0077671489，仅6/10cell改善。平均降低约0.087个百分点growth，不能只报相对10%隐去绝对幅度。same-study排除后 **.0096032022→.0097194522，平均恶化**，只有4/10cell改善。MSE正门不能替代排序稳健性；尚无稳健药物筛选/临床决策增益。

## 独立校验与实际争论

两位评审先分别封存独立任务、协议和代码审查，再实际双向交叉，发现并修正了plate风险外推、mean/min排序歧义、弱selection合成测试的夸大风险。原始审查、修订意见和封存均保留。开值后的独立解释也先封存，再实际质疑“为什么局部传播不是普通核”“为何排序恶化阻止晋升”“13个程序是否只是参数选择”。不按多数投票宣布新颖性。

assay独立程序不导入root处理/模型模块，重构442191允许PG记录和35480task全部canonical坐标、完整solo join，数值/索引与保存结果一致；独立复算35组预测指标、source-only选择、bootstrap、gates、study源数通过。另独立实现NCI与RBF，重训两个selected模型的全部887pair/30source→10dev，共141920预测最大差0。没有独立重跑所有tune候选或study敏感性模型，不能扩大审计覆盖。skeptic解释/数学审查不是第二次全量原始数值审计。

## 有界误差诊断与决策边界

在主实验后，按DIAGNOSTIC_SCOPE另做一次20fit→10tune描述诊断，不拟合新纠偏器、不使用development query作诊断依据、不打开reserve。固定已选RBF，计算合法anchor innovation与pred−truth残差的逐cell、逐query相关；同pair排除同study源后重新估计。B1相关比B0减弱但仍偏负，说明可能还有统计性欠传播；它并未给出区分生物响应与同板校准的辨识证据。

这种“残差与已知innovation相关”的结构可以由普通残差回归/stacking表达；尚无证据要求独特的新更新算子，也没有新的机制候选通过新颖性审查。相关性不是证明标准方法已经解释所有误差，也不保证一个未测试的校正器有后续收益。隐藏query的error不可事先观察，跨pair相关还未形成可部署的个例失败规则。两位评审另独立审查诊断并实际互答，同意STOP；报告见各自DIAGNOSTIC_REVIEW与assay/DIAGNOSTIC_CROSS。不能把它直接命名为新世界模型或用更多菜单挽回创新主张。

诊断读取NPZ时会物化整个已许可40cell数组后再切前30cell，因此准确范围是“未选择/使用development truth形成诊断”，而不是“从未物理解码development truth”。后20closed cell从不在该数组内。原诊断协议/输出保留，并以DIAGNOSTIC_READER_SCOPE明确纠正这一措辞。

**SUPPORTED：有限公开目录中普通组合反馈改善功能预测。NO_CORE_PROMOTION；STOP_CURRENT_ANCHOR_TRANSPORT_NOVELTY_AND_RSI_EXPANSION。** 保留成功直接模型为强基线；停止以当前锚点传播描述扩大更新菜单、智能体层级或多代编辑器，不打开后20cell寻找新规则。若未来有实质不同且来源独立的机制证据，需另提明确技术差异并先做独立新颖性/简洁性评审；不能将此STOP换名重启。

完整目标的世界模型独立收益、agent收益、能力继承、联合交互与改进策略更会改进均 **未建立**。当前只有常规反馈适应证据，没有新核心机制。

## 资源、故障与诚信范围

maestro Python3.11.16/numpy2.4.6，HEAD47a0e2dea5a7dd42379fa17eb3621caf6bd0114c，seed20261022。主prepare约10.97秒、主拟合与敏感性约9.38秒；元数据、独立审计/重训、诊断另计，不把这些总成本写成9秒。无DeepSeek调用、无新湿实验，原生agent token/金额未提供。已有公开全曲面的历史测量成本未知；每cell本目录B1需887不同pair的anchor，不能称整cell仅一次测量。

第一次freeze绑定自身仍在写入的console，root在prepare前发现，原无效manifest及记录保留；第二次在数值读取前有效。随后skeptic在不知已封存时更新弱测试措辞的review+seal，两文件发生post-extraction漂移。原有效manifest保留AT_VALUE_READ；拟合前逐项核对其余旧绑定不变，只对两个文档作明确post-extraction行政rebind。独立审计验证该两文件差异，不能从当前文件独立重建所有事件时序，故不宣称全程完全盲或全部文件不变。模型/协议/分割没有随响应更改。

所有新增实验/测试代码在research/almanac_feedback_pilot_20261022，数据、协议、失败、结果、争论在log/；src/tools未改。旧tracked导航改动保留，旧全局三项provenance漂移未解决，本地绑定不代表全局完整性。
