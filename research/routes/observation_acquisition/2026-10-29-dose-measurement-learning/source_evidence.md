# 原件、导出观测与数学边界

2026-10-29。此处为root核验与来源综合，不是独立科学审阅；独立初判/复判见independent_challenge.md。普通公开cell/drug/物理dose/固定功能终点可作为主线，不把缺组学、源well或独立培养一律当普通同筛预测的否决条件。更强机制、跨培养或真实实验节省主张另需对应证据。

## 普通导出响应：DQ1实际结果与适用范围

既有公开AZ/GDSC ZIP为241088863B，SHA256 e8cb50f6ce860fa17586a555130cb3b019f6011ed1976c0f0d3e00fb072d3259。本轮没有重新下载。DQ1事前固定member combo_well_stats_GDSC_007_05May22.csv前20000行；首次数值解析两侧导出y，共40000出现。Decimal零容差、不平均/舍入/clip，以(project,cell,reference,numeric concentration)去重。CSV流短暂分词整行，不保留或数值解析拟合yhat/IC50/AUC及组合inhibition。

root结果5924唯一导出键，5923键重复；重复键原字符串/有限数值冲突均0，缺失/非有限/负或零dose、y越[0,1]及ref身份映射冲突均0。每键可作为同筛导出层级的一项确定观测，用于另冻的开发预测；相同键副本不得跨查询/评分。该前缀全部开发暴露，不能以新拆分重命名独立确认。

先前fresh作者独立重写dq1_independent_check.py，但句柄消失且未留结果。后续新代理先审脚本，再实际执行一次、先落盘后比较root实现：复现5924/5923及零冲突；CPU0.515625s、脚本wall0.5723977s、实际exit0。监控工作集峰值37679104B仅为采样，不是硬RAM限额证明。原独立作者曾先看header/两行再核hash，顺序偏差保留。本次执行不能抹去它。16个packet按键值全一致，但root浓度Decimal数序与独立文本字典序不同，10与3.16255534位置互换；本次16键集合相同。独立实现额外范围过滤和潜在另16冲突例本次无实际影响，不将其当一般情况下协议等价。见dq1_independent_review.md及原结果。

root另做无响应数值解析的支持交叉核查（support_qualification.json）：19cell、11drug、204cell×drug组、876ref曲线；772曲线7浓度、104曲线5浓度；146cell×drug组多ref。19cell的171对中153对共有11drug、18对共有6drug；全部171对至少有3drug各自跨cell共享至少3个精确物理浓度。仅证真实菜单交叉够开展后续局部关系检验；不证局部响应关系可复用，不跨ref平均，不把ref当培养。该补充由root运行，未另获完整独立重写。

## 旧公开源码解释处理与join，不能认证实际生成版本

从既有官方缓存定向核读并保存7个原源码/DESCRIPTION/LICENSE文件，共144966B，见source_code/provenance.json。未运行R，短缓存标识00c04b4/34d8422未认证为实际导出生成版本或完整commit。

- gdscmatrixanalyser R/classes.R313–350的get_monotherapies用treatment=S/Ltag和POSITION取单药，调用calc_viability(trim=TRUE)，再以MASTER_CELL_ID及BARCODE+lib_drug进入prepNlmeData；402–410定义viability=(intensity−mean_B)/(mean_NC1−mean_B)，并截断至[0,1]。
- gdscIC50 R/nlme_fit_prep.R779–824把normalized_intensity转y，再y=1−y；以BARCODE与lib_drug形成ref。这支持“归一化/截断后的inhibition-like单药导出响应”，不叫未经处理仪器原数。响应方向解释仍受实际生成版本缺口限制。
- analyser R/matrix_well_stats.R48–66把按浓度降序排列的单药统计赋予dose标签，再按libN_dose标签join组合行，先删除单药conc/POSITION/CL；组合行POSITION不能还原单药源well。classes.R272–284的输出字段链也已核。

此前字典对INTENSITY写fluorescence、S15/S17一般72h CTG2/luminescence的来源冲突保留，未以本轮代码读取消解；stock expansion/同键重复不等独立培养。同终点导出预测可成立，独立噪声/培养/仪器解释需更多来源。

## P4：2026CV多任务选测，条件性原理与可证错误分别保留

Deconstructing Multi-Task Active Learning: The Paradox of Gradient Conflict and Orthogonal Decomposition，arXiv2610.23623v1；本轮原Atom确认首发/该版2026-10-16，formal venue未核，NeurIPS checklist不等录用。原HTML746403B。root实读§3.1–3.2、§4.1–4.2、§5.1–5.3、AppendixA.1及B.3；公式原文局部核对，不称全图/实验/作者代码已审。p4_blocks.json只是导航投影。

实际运算：获取阶段按hardness与MC-dropout任务熵序列绝对相关的均值之补量CTMI筛top(k×m)，再k-center覆盖；优化阶段另用PCGrad。CTMI做pool内min-max，不是实算互信息或其界。独立heads条件下total covariance由shared latent项给出，是条件性分解，不能识别共同生物原因。视觉一次标注多任务，药筛每个功能键单独收费，信息制度不同。

S3.SS1.p2.1及A.1把g1≈−k g2(k>0)推出未加权g1+g2消失/SGD停滞，并把投影与表征正交扩展连接。root手推g1=(2,0),g2=(−1,0)：精确反平行，α=1/3凸组合为0，但sum=(1,0)非0。标准双向PCGrad将两者分别投影到0，并不必然生成新方向。只有等模k=1才使未加权sum0；近似反平行一般不严格秩亏。文中自己的local/empirical限制保留；该数学缺口否定上述普遍推论，不代替对其经验结果的复现裁决。借用“获取与优化分别论证”，不移植CTMI/PCGrad为药理机制。

原文abstract及AppendixI自称代码在https://github.com/Juho-Jung/multitask_active_learning_official。本轮未取得此repo/commit/license，记not_verified，不能把链接当实现验证。

## P5：多输出剂量响应的直接强先例

Multi-output prediction of dose–response curves enables drug repositioning and biomarker discovery，npj Precision Oncology，DOI10.1038/s41698-024-00691-x。原主JATS电子2024-09-20，早期公开日期未知；是最近相关旧先例，非2026新论文。523653B。root实读Sec10/13/18/22/23，Sec13/18截断后独立小输出恢复。

以每一相对dose index作输出，ICM潜在GP共享；输入含基因组和drug特征，Sec18对mutation/met/CN/chemical特征组使用相乘EQ核，LBFGS/边际似然估参数。GDSC1/2剂量/协议筛选与归一明确，不是任意跨drug物理dose等价。原始测量导出经gdscIC50预处理作标签，Sec23在预测稀疏点间PCHIP插值算摘要；插值点不是密集新实验，拟合Sig4派生终点不作本轮免费真值。多输出、相关参数学习及曲线重建已有；去掉组学并不是算法贡献。

Code availability原文明确https://github.com/juanjogg1987/MOGPs_for_Dose_Response_Predictions；本轮repo/commit/license未取得，not_verified。无作者代码运行/效果复现。

## P6：学习结构、选点、反馈更新的宽泛闭环已实际提出

Data-driven learning of structure augments quantitative prediction of biological responses，PLOS Computational Biology，DOI10.1371/journal.pcbi.1012185。原主JATS电子2024-06-03，早期公开未知，publication-update metadata2024-07-09；不是2026新作。256339B。root完整核sec013/015、sec006关键尾部已恢复截断；独立challenger另读sec003/006/013/015。

SVC从定量输出阈值化类别学边界，decision-function距离加入SVR等定量回归。主动步骤以25初始点作30次20/5split，用SAR相对SVR预测收益挑边界，再各取10个正/负近边界点，另比远/混合，增加实测反馈并更新边界和回归；文中展示一轮，三药细菌群落、4³=64组合的功能问题。宽泛“反馈学结构→改善预测/下一测量→再学结构”已有，但它不自动覆盖M.v0局部协方差/隐式近似前瞻链。

先在嵌入早期peer review见repo当时为空的批评，随后实际核主文front Data Availability同一官方URL：https://github.com/YChH/StructureLearning。本轮GitHub commit/HEAD原响应确认full commit6b0d4e653b6f3f0ac49a6ea3b038442417223018，日期2024-05-24；以该sha下载3521669B原ZIP。不能用旧reviewer空repo说法描述现状，也不认证该commit就是论文完整生成运行版本。

Archive有12成员：4原notebook17508532B及8CSV/XLSX数据成员468164B。仅提取/登记4notebook；8数据成员未打开/提取/用作响应，压缩原档案仍包含这些字节，所以不称本次code获取完全data-free。只解析notebook的source字符串数组，不读取outputs作证据、不执行。AL02-Final.ipynb source-array12 lines11–14调用decision_function；array52 lines1–44筛训练20点的复杂/简单Results差，branch要求>0.3，55–88按正负边界距离排序去旧点，每侧取前20候选并集后随机抽n=20，91–119生成新train/test并重跑回归。source-array60/77另见近边界分支。未全文核全部代码、各实验分支或运行输出；这处0.3门槛不能泛化为全论文统一规则，也不据此断言作者结果错误。

原archive无LICENSE/依赖清单，许可unknown，AL分支调用round3.xlsx但archive不含该文件，复现缺口明示。p6_code_receipt.json与reference/repositories.tsv分别保留原档/排除/commit和partial-snapshot关系；技术导入状态existing_user_copy表示本地导入已取得的字节，并非作者运行已复现。

## M.v0数学核验与研究裁决

root独立核对challenger固定eta基准：m_T(z)=m_T+c(z−m_u)/S，C'_TT=C_TT−ccᵀ/S，平方Bayes风险下降tr(Wccᵀ)/S。后验均值位移期望平方等于同一风险下降，不能再加一次。eta随机时还需E_eta Cov(f_T|eta,D)+Cov_eta E(f_T|eta,D)；当前点估计/一步Hessian/Jacobian尚未指定怎样一致组合。缺件是算法自身未闭合，不是数据稀缺造成。

亦核B=diag(s)+wwᵀ在w=0时∂B/∂w_j=0，故仅经B光滑依赖的似然g_w及J_w为0；可分离平滑ridge下w–s混合H块也为0，可逆时一步delta_w=0。任意人为混合H不能被这结论覆盖，非零初始化可避开；完整重拟合若也永远零起点同样可停滞。此为未冻结实现的条件性反例，不证明所有近似方法失败。初步r=0梯度口头反例被challenger自行更正：已付q_A时条件均值随r变，不能使用错误版本。初判/更正均保留。

同剂量激活多个帽函数的系数似然交叉项phi_i phi_j/sigma²非0；它不能直接等同eta的H，但足以否定“先验节点独立即自动给出块对角曲率”。三节点高斯求积本身不处理任意双峰关系后验，也不是精确积分oracle。N1应有同一求积与完整重拟合，公平核算训练/缓存/选点全部成本。

本轮采用：普通导出预测有可用且不稀有的数据入口；保留“局部跨cell关系能否跨未查询drug复用”的科学问题。M.v0停在不完整候选，0实质修订、0经验H、0科学性能run；不启pass3，不靠补模块救回。P4/P5/P6不足以裁定其具体近似已经先做，也不足以建立其新颖；影响函数主动设计/超参数不确定性/多分辨率局部核最近先例未闭合。后续先检验真实普通支持内的关系复用与具体筛选决策，才值得为前瞻加速继续开发。
