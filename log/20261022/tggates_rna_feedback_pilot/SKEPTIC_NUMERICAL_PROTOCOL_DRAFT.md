# 最小两error数值合同草案：同信息普通方法先充分，再问哪项结构可迁移

2026-10-22。**DRAFT / NOT_FROZEN / NO_RNA_DOWNLOAD_OR_FIT_AUTHORIZATION**。承接EXPOSURE_AND_SCOPE.md；仅本新phase可写。本文不改旧API/headroom代码、freeze或结果。source24、development7的L/M/H功能已完全开发曝光；later14labels/8proxyblocks的功能与RNA继续封存。不能把本阶段称fresh-blind确认。

## 1. 具体用途、可证伪主张与不变效用

固定新药Middle condition bundle：2h早RNA及24h DNA/LDH发布读数，预测同药未购High的24h发布DNA百分比/100；LDH完整次要。它是已预筛目录的条件均值确认辅助，非同细胞中介、临床安全性、birth/death或新donor外推。High RNA绝不作为development主预测输入。

可证伪的经验结构是：**跨剂量分子预测误差与在实际分子状态条件下仍剩的功能预测误差，存在可在未见proxy化学组使用的低rank、近block-sparse输运结构；在small-N下，其约束可减少过拟合/负迁移，并带来实用High-assay预测改善。**

这不声称u/v产生了新信息：在冻结f/g后，u/v是实际Middle RNA/function的确定性重参数化。最邻近普通方法是联合条件回归/协方差更新。显式同约束、同训练、同计算的ordinary copy必须合并一方法，不能要求方法击败自己。一般NN可表达并不替代实际同信息比较。

效用仍为DNA MAE相对最强**非同构**冻结ordinary alternative严格下降>0.02且相对≥10%；当前既有best开发baseline 0.023357意味着必要MAE<0.003357。若新ordinary baseline更强，要求更严。小幅正差、LDH好看、state预测准确或某个高误差药物改善，都不能替代这个门。开发结果仍是筛查，不自动晋级core。

## 2. 最小可观测数据与费用

固定source24药的2h Middle+High及匹配2hcontrols；development7药只2h Middle+controls。data已认证172个HG-U133_Plus_2 CEL与31ZIP目录，ZIP总量约3.658GB；以其精确manifest为准，不重用早先“172是逻辑估计”当实际下载receipt。Low、developmentHigh及later RNA不转换；不买额外oracle来救主预测。

若下载的31个实验ZIP含其他dose/time数组，完整压缩字节接触须披露；只按准许BARCODE/member列表提取和解析172个CEL，不解码未准许entries。不下载later实验档案。DNA/LDH继续使用已开放CONDITION_MEANS，不重开raw功能；既有source Low功能标签对所有方法均可用，不能暗中给direct隐藏。世界分支若只用有RNA的M/H训练，是其结构选择；普通dose/function prior允许使用全部source L/M/H。

此阶段没有新湿实验。费用分别报：ZIP请求/失败/bytes、准许CEL数/解码数、controls共享、RNA预处理、每fold变换/encoder/f/g/B/direct fit与超参候选、缓存命中、峰值内存/CPU。High-source RNA是所有方法共享的有成本辅助监督，不能只给world。计失败，不退款；不得把前阶段3.8s功能screen当RNA总成本。

## 3. 可部署RNA变换与共同坐标

单数组MAS5是可隔离的简洁候选；其具体软件/注释/信号规则需来源与实现审查后由正式protocol固定。processed全目录joint-RMA不能直接充当strict source-only输入。任何transform不得通过联合归一化developmentHigh/later或被留出的sourceHigh泄漏未购分布。

建议每数组独立处理后，按预先固定注释和probe→gene聚合生成同一gene坐标的log-signal，再以同实验2hcontrols形成condition-mean log-response；两treated重复和controls都按固定全量规则，不按功能挑probe/replicate。正值/零值处理、映射歧义、非有限数值须在转换前固定；不以看过RNA后的feature过滤救结果。

**OOF的PCA坐标不能直接混合堆叠。** 若每fold训练自己的PCA，f的预测必须先重构回固定gene坐标，才定义 `u=x−xhat`。不将foldA的PC1直接当foldB的PC1，也不以需要heldoutHigh的对齐修正。g输出在固定DNA/LDH单位，v可直接跨fold堆叠。state内部encoder可为source-only PCA4，固定q=4减少搜索；f/g输入标准化、PCA和任何训练期gene筛选均在相应训练proxyblock内拟合。

若gene筛选会产生不同fold基因集，预测回固定全gene坐标时须有训练定义的重构/后备，不按heldout值填补；更简单的是先用固定annotation gene集合、不做按response的筛选。u的高维回归使用dual/低rank实现，避免显式gene×gene矩阵。精确copy同样受这个规则约束。

## 4. 最小共享base与两个真实error

每个任务的known design为chemical proxy、原单位、log10浓度、log10(H/M)，不能用compound ID当特征。fixed Middle不涉及query优化。

1. `f(c,d)→xhat_d`：由source M/H RNA监督的正则线性/核状态预测；内部可PCA4，输出重构gene response。
2. `g(x,c,d)→y_d`：线性multi-output readout，输出DNA/LDH；线性相对于gene/state和已列design features，排除Jensen/distribution plug-in解释。既有dose/function prior可作所有方法共有context，不独享L功能。
3. 对一组外预测定义 `u_d=x_d−f(c,d)`，`v_d=y_d−g(x_d,c,d)`。v混含g误设、assay误差、normalization/lot，不称已识别RNA外生物机制。
4. block-restricted校正为 `x*_H=f(c,H)+B_x u_M`，`y*_H=g(x*_H,c,H)+B_y v_M`。

base f/g可用共享ridge α∈{1,10}的小网格；若实际维度/数值稳定性需要另设，必须在RNA转换前替换并冻结，不能后补。g和所有direct有截距/合理source prior，禁止用高正则回归到零的弱baseline。任何RBF/核模型训练目标center于训练均值，预测加回。

## 5. 2×2是路由消融，不是假造测量权限差

四个分支为：state-error route off/on × conditional-function-error route off/on。共同base、共同完整已购Middle history；分别将B_x/B_y置零，其他训练和调参权限匹配。

**v-only仍用实际Middle RNA计算g(x_M)，不能称“只买功能、不用RNA”。** 该2×2测的是修复路径的必要性，不是RNA是否被测的主效应。另需一个真正不使用observedMiddle RNA的ablation：保留相同source辅助RNA监督与M功能，用预测xhat_M构造普通功能残差；主full-history direct始终获得完整x_M/y_M。不得把branchmask带来的信息限制当公平baseline被击败。

## 6. 同信息ordinary对照：合并copy，给一般模型更充分机会

至少固定以下可执行族；共享预处理和相同合法信息，每族报告完整source选择、开发预测及费用：

- 原九个function/chemistry baselines原样保留，全部分数，不只弱0.85。
- **同约束ordinaryjoint**：若实现等价于上述B_x/B_y，合并为候选一项，不另做败者。
- **full joint + cross-block shrink**：支持`v_M→u_H`与`u_M→v_H`，检验block restriction是否真有有限样本价值。可按输出block拟合ridge；输入u/v各自用训练期block scale标准化，避免上万gene坐标淹没两个功能单位。
- **full-history direct auxiliary**：拿实际M gene/state、两功能、全部design、预测M/H状态、u/v及相同f/g辅助源标签，直接预测High功能。允许一个共享f分支显式包含`g∘f`，其中完全相同的子程序合并，不把它削弱为chemical-only。另给普通gene/PCA direct ridge或centered KRR。
- **普通重训练/收缩更新**：用全source合法RNA/function加已购M重新拟合f/g，source prior/正则和样本权重source内定；保留同一可部署encoder，不能给它未来High。它要能真正用RNA和功能，不能只加输出offset。
- fixed offset、已有Middle copy、四基因stress EGR1/ATF3/GDF15/FGF21（注释可认证时）、固定50/50混合完整报告。四基因probe映射按外部注释固定，不按本RNA效果挑probe。

最小输运网格建议：每个输出block rank r∈{1,2}，ridge λ∈{1,10}；共享base α∈{1,10}，每族8配置。ρ∈{0,0.5,1}分别代表cross-block禁止、强收缩、与同block等惩罚。可等价用输入[u,√ρv]预测uH及[√ρu,v]预测vH；ρ=0是候选本身而非新的copy competitor，ρ=1是真正一般joint。所有数值scale只由该fold训练误差估计；rank是每output-block秩而非把fulljoint总rank压得比diag还低。

将ρ三族与2×2路径放入一个预列普通程序字典即可；对每族最多8个源选择配置，direct ridge/KRR也给8个合法配置/相当fit预算。若普通枚举直接选到ρ=0并复现候选，说明是普通有限程序选择，不是新agent/RSI。不能禁ordinary方法携带source历史、分子监督或counterfactual训练标签来造优势。

## 7. nested proxy-OOF必须真正阻断High，并避免过度声称

source24proxyblocks固定；development7只作已曝光功能下的RNA开发筛查。对每个预列配置做source外层leave-one-proxyblock-out：

1. 外层被留出组的全部RNA/功能不得进入reference训练、encoder、f、g、B、scale或超参拟合。它的M是评估时已购history；High只供隔离evaluator在source内评分/误差诊断。
2. 为给外层训练组构造B训练数据，再在外层训练集内部crossfit f/g/encoder；每条训练innovation由未训练过该药High的模型产生，并回到共同gene/assay坐标。
3. 用这些内层innovation拟合B，外层对被留出M应用并预测H；所有ordinary comparison复制相同role/dataflow。
4. 预列配置由source外层OOF DNA MAE选择，再用全部source内部crossfit误差训练最终B；development不选择rank、gene、signature、λ或分支。

这一设计给固定配置的外层预测无被评分药High泄漏；**在同批外层预测上选超参后的selectedCV仍非无偏nested性能估计**。若要额外宣称选择程序本身的无偏source性能，需要再外包选择层并重算，当前小pilot不作该主张。不能借“nested”一词把model-selection偏差抹去，也不必为一个开发筛查无限堆新验证层。

reference/PCA可按精确训练label集合缓存，缓存键包括train keys/代码/注释/参数hash；不同outer/inner训练集不可错误复用含heldoutHigh的变换。完整fit账含base、inner crossfit、correction、direct、重复/失败。精确预计fit数由冻结实现生成，不能仅数最终8个配置。

## 8. 一项真正的配对反证与结果解释

预先固定source-training内的整药M/H RNA对置乱，保留dose-level、向量尺度、训练数组集合；只破坏RNA与chemical/function配对。每fold单独按固定seed映射，不使用developmentH挑置乱。source PCA整体分布可不变，但关联被破坏。各方法得同一置乱数据。再用固定四基因/无observedRNA对照。全空间可逆旋转同时重拟合模型不是有效阴性，不复制旧API的旋转错误。

普通等价合并后仍可测三个非平凡问题：

1. 实际Middle分子反馈是否在完整Middle功能/chemistry/auxiliary-state direct之外提供可用跨proxy组信息？若full-history direct已经同样好，只支持测量信息，不支持独特结构。
2. 有无源内可预测的cross-dose error结构，block constraint比ρ=1或ρ=0.5减少small-N负迁移？ρ=1匹配时block必要性失败；不能强称细胞模块解耦。
3. 这种结构在未用来选参数的development RNA条件下是否保留原始实用门？偏差很小或只一个开发药驱动时完整报告，不事后删除。

## 9. 成功、停止及后续边界

所有预测与配置在应用developmentRNA后、评分脚本读取其既有High功能前封存；尽管研究者已看过功能，仍可防止运行时target误用，不能因此称真正盲测。开发结果全部保留，以DNA每compound等权MAE主评；LDH/state error/每药与proxygroup loss次要完整。描述性group-bootstrap不纠正开发family选择，不能凭7组宣称广泛generalization。

只有在原>0.02/≥10%效用成立、非同构强ordinary未解释全部、对应RNA/路由消融与置乱吻合时，才可考虑下一独立评价，不立即称新core。效用未过、RNA无增量、普通joint/direct匹配、置乱同效或主要来自后选子组，停止本用途核心深入，保留较窄普通预测观察。失败不靠另开Low/devHigh/later、换LDH、改阈值或扩大模型搜索救。

later维持封存；本固定M单反馈试验没有有效agent动作比较、继承/CL across-task收益、joint或old/new-improver C4结果。任何后续程序继承必须在同一later solver/history/预算reset比较，不能把source挑rank/shrinkage叫RSI。当前仅推进真正世界状态反馈贡献的一项可证伪数值研究，不替代原完整目标。
