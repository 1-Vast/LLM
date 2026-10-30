# R192 / R193 最新结果独立审查

2026-10-27；审查者 latest_results_audit。只读协议、实际代码、JSON、报告与已有独立挑战；未联网、未启动训练或旧效果代码、未读 sealed/凭据。仅写本文件。实算限于已有结果算术、matched_conditions.csv 的元数据枚举和纯数学反例。“错误”均指指定推理或实现，不由停止标签倒推方向失败。

## 1. 结论与最新性

**R192 已执行，未通过预注册复合规则，不能称原命题被否证。** Xboth rho=0.094640，主 CI=[-0.007016,0.179018]；相对10次随机映射均值差=.084659，CI=[-.024944,.177368]。区间仍容纳门槛.0947与原头条.1183。当前报告已经明确禁止“原结论被推翻/DrugComb不能复现”。

**R193 已产生 q1.json、report_q1.md 等完整设计检查交付；没有跨screen主Q/H193b结果。** 最新 judgment=inconclusive，唯一失败项为 mde80_obs_le_delta_min_obs；main_q_computed=false。within-screen分半相关是已执行结果，不能替代H193a跨screen相关。按指定gate停止成立；从同屏分半r/SE外推出跨屏nullSE的有效性尚未建立，所以“本资源真正无法检出”仍过强。

R192 留下“身份缺失时，粗注释能否提供超出研究组成的药对先验”的问题；R193 留下“共同设计子集内，同组织条件对比能否在复测中保留”的问题。两者均未识别机制、反馈传递或独立决策收益。

审查期间 R193 从只有q1.py变化为JSON和报告落盘；代码曾在结果后继续追加说明/运行时gate，最早JSON记录的脚本SHA与当时新代码不一致。**09:03:40 UTC检查已匹配，09:07:03 UTC终检三份关键文件SHA未再变化**；进程查询未见命令含q1.py的Python进程。不把暂态差异当数据造假或最终错误：

| 产物 | SHA256 / 当前状态 |
|---|---|
| R192 preflight.json | b6d337704e46df3586d46c45d0e5dee17fe5bf212e4e88a0c0cc3ba5dece22fa |
| R192 stage2.json | 89c34e3c5f602244847d01cae9929ffb9b4cd7e86e6ec8bf98df3fce730c05cf |
| R192 stage2.py / s2lib.py | 1649fd0acc6019942f669f8ef31900239bb2ce603512c20334cf93be17017b3e / b39bea1d7a62fa70cccd8f9ecdeb2aa6c67789e15b7d0670fb07cb9257cbbcaf；与report:177-181一致 |
| R193 PROTOCOL_Q.md | 74fa675a77031e6df1d68831615e8753eadda13f41f27ab23096d836091ed1cf |
| R193 q1.py | f21592c450d9445ff72d2dbf38c1aefb7ab47a188d323634f29c712560a58b04；41,596 B；与最新q1.json.script一致 |
| R193 q1.json | 064ad3c3a7aef6d9bf67c139b144503a3ea2bacbdaf39f240f40113140903534；mtime 08:59:58 UTC |
| R193 q1_rows.csv | edecb0355c6fe8d66b5b3cf37679c3f472a8724bef2cc5562edc234f506524d6 |
| R193 report_q1.md | 03885f2ccb447c452a64a8b003ff0761a08d9814ceab160b0fb90dd9e71634a0 |
| R193 record_q1.md / usage_q1.json | 均已存在，mtime 09:00:32 UTC |

旧 independent-reassessment/stats_audit.md:141-145 的“阶段2尚未执行”已过时；其统计论证可另核，文件存在性不能继续照抄。本审查以新产物为准，保留活跃写入过程。

## 2. R192：主对比、功效与组成

路径简称 R192=research/2026-10-27-drugcomb-replication/。

| 审查项 | 判别 | 定位与允许的解释 |
|---|---|---|
| not_replicated | **可保留；称否证过强** | report.md:13-22,78-102；stage2.json → judgment、main.xboth_ci_pair_cell、main.diff_vs_random_ci_pair_cell。R1距离仅.000060；实质限制是R2/R3宽CI。复合规则未过不是对rho>=.0947的拒绝，更不是原跨资源命题为假的证明。 |
| v3修订 | **可保留** | AMENDMENT-001.md:17-20将Xboth定为主臂、annotation_only降次臂；AMENDMENT-002.md:16-24统一pair×cell主CI并检查联合规则，:38-43允许仅看preflight的一步r=.50→.55。不能再按v1指控“偷换主臂/未声明阶梯”。记录与实现相符不等于本审查独立验证了所有文件先于效果的真实历史。 |
| 副臂能否救主判定 | **不能** | annotation_only rho=.106767、CI=[.005782,.188873]，但相对随机均值的差CI=[-.010829,.188431]；stage2.py:274-275,321-337。副臂不是主臂，也未通过对照特异性。E1、v1映射、留药聚类正CI同样只是敏感性。 |
| .0947门槛 | **冻结数值可保留；“保守可信下界”过强** | AMENDMENT-001.md:22-24公开其来源。旧R163区间是特定切分均值的区间，不能跨r/端点/注释体系自动成为新任务总体下界；旧方法定位见 independent-reassessment/stats_audit.md:113-119。R1是规划门槛，不是非劣效检验。 |
| F3功效 | **gate执行可保留；80%保证未决** | preflight.json → gates.f3：选r=.55，SE=.023926、MDE=.067032、联合率.8335。preflight.py:30-35每轮既重抽pair/cell又重抽z；正式CI固定已拟合pred，仅重抽单位。两者不是同一随机实验。f3_power:42-63另假设独立正态和对照SE；2000次模拟不能验证这些假设。 |
| realized SE / .150 | **诊断可保留；称真实MDE过强** | stage2.json → main.diagnostics_not_judgment：Xboth固定预测的SE=.053568，乘2.801585得.150075；固定随机pred等价量.049211。说明规划null不能代表结构化预测的不确定性；.150仍是事后正态等价值，未经备择/完整规则校准，不能当排除小效应的界限。 |
| CI含义 | **固定设计描述可保留；新药总体推断未决** | s2lib.py:585-605用pair次数×cell次数重抽固定y/pred，不重训、不重选split；不同pair共享drug/注释的依赖未自动覆盖。:646-660将两个排序角色分别独立抽药，同药跨角色时不是统一节点重抽，且索引为全体drug。两种CI都报不保证未来未见药物外推。 |
| study proxy调整 | **统计结果可保留；因果归因过强** | report.md:119-128；stage2.py:154-185；s2lib.py:275-280。proxy为block_id二十分位，不是核对过的study/batch ID。rank在bin内去均值后partial rho=.010246、CI=[-.026928,.046315]；控制cell为.023425、CI=[-.012324,.059115]。支持“汇总关联依赖组成、注释特异性未建立”，不能证明主要由真实study批次驱动，也可能移除组间生物信号。 |
| capacity对照 | **实现可保留；解释收窄** | AMENDMENT-001.md:19；stage2.py:291-298。它在真Xboth上追加2L个按cell×pair单元产生的高斯列，仍保留真注释；rho=.090540只表示这种追加噪声未明显提高分数，不是纯随机特征替代注释仍同样有效，也不能据此证明/排除一般容量解释。 |
| 恒定baseline top100=.52 | **数值由实现产生；机会基线解释错误** | stage2.json → main.top100_hit；s2lib.py:723-728稳定排序后取前100。常数全部并列，.52只是输入行序命中率，不能声称恒定模型会选药或优于Xboth。随机打破并列的期望应为池内阳性比例（约上四分位；y ties可略高）；Xboth大量并列也需一致规则。常数AUC=.5是合理sanity。 |
| JSON与报告小冲突 | **需披露；不改变主判定** | main.rho.identity_only/constant为null，report.md:85“按定义0”是记分约定，真实Spearman未定义。disclosures.cells_not_held_out写所有测试cell均在训练；main.selection_bias_main_design实际100/106，report:140已写对，不能据泛化字段推成cell cold-start。 |

**必须随结果传递的组成条件**（report.md:133-142；stage2.json → main.selection_bias_main_design）：主r=.55，训练17,683 units；测试45,138 units /7,961 pairs /106 cells；映射1800/4088药；测试仅全cell×pair宇宙11.87%。原效应r=.20；原DeltaEMAX与本次整矩阵Bliss均值、原注释与KEGG argmax代理均不同，原40切分均值与本次单切分也不同。可保留的是具体身份缺失任务的弱正排序与组成敏感性；不能缩成“虚拟细胞/agent方向被否证”。

## 3. R193：真实匹配、最新停止与统计对象

路径简称 R193=research/2026-10-27-conditional-shift/。

| 审查项 | 判别 | 定位与允许的解释 |
|---|---|---|
| matching_qualified | **可保留** | a0.json → qualification、quadruples；report.md:14-23,60-79；challenge_A0.md:9。9154共同键、两表barcode不相交、6,223,367共同四回路有具体证据。结构非退化不代表数百万独立重复、可靠效应或充分功效。 |
| ERRATA/有向口径 | **应继承更正** | ERRATA_A0.md:9-14：disjoint=4,612,633；G1-only/G2-only=4,412,540,421 /7,234,325；条件级有向对129。A0 report:20,68称98“有向”不严谨；a0.py:297实将ID排序，98是无序对。药对级共同有向130、条件级129与无序98不能互换。 |
| 匹配剂量 | **设计列可比可保留；完整曲线等价未决** | PROTOCOL_A0.md:32-44,94；report:79,86,114；Q协议:17。相同anchor浓度/library最高浓度不证明整条网格、拟合范围、时间或药效等价；不同library同数值浓度也不等于同占据/抑制强度。 |
| 新Q产物 | **设计停止成立；Q阴性说法错误** | q1.json → judgment.main_q_computed=false、failure_reasons=[mde80_obs_le_delta_min_obs]；report_q1.md:15-27,97-100。92,039 cycles /1501cp；规划MDE=.204241 > obs门槛.089286；近似power@latent.1=.174、@.3=.896、type-I=.018。没有跨筛主rho/adjusted-Q。 |
| runner范围 | **停止分支成立；主分析未实现** | q1.py:653-663：失败不进主分析，通过则SystemExit并明说此build仅实现设计/停止；report_q1:133-135已披露。不能把代码称作H193a/H193b全流程已执行，也不把未执行主分支当漏交主结果。 |
| signed median | **定义可执行；代表一般交互过强** | Q协议:21-24；q1.py:334-355按cell名定c/c'、按library ID定p/q；:434-441在cp内取有符号Q的median。它是ID定向的位置统计量，稳定但正负平衡的交互可被消掉；换ID编码会改变聚合量，见下节。 |
| 6M / n_eff | **计数可保留；独立n未识别** | a0.json → matched_replication_graph：6.22M来自9154边。主层1501cp共享96cell和条件。q1.json → design_check.mde80_obs.primary_empirical_cluster_adjusted.n_eff=189.158213是公式输出，不是数出的独立生物单元，也不是所有估计对象的功效上限。 |
| 可靠性/衰减 | **分半相关可保留；latent精确解释未决** | 最新q1.json → design_check.reliability：Original1593重复键/61cp；Validation8974/1501cp；SB后.863684/.740580。Original是更窄条件子集；median非线性、前后两半不等大、同筛误差可能相关，不能自动套经典等半独立误差/Spearman衰减关系。 |
| 分半协议 | **存在可定位偏离** | PROTOCOL_Q.md:39写“奇偶分半”；A0协议:43及q1.py:415-420用排序前ceil(n/2)/其余。头注释/新报告公开沿A0；应记裁定或偏离，不能说协议逐字一致。 |
| cell bootstrap | **实现不是通常multiplicity重抽** | q1.py:444-456抽96cell后np.unique丢次数，只保留唯一cp。不同抽样重复数得到同cp集；实为随机保留约63%节点的子抽样，未保留n_i*n_j权重，也未给子抽样尺度校正，SE不自动等于已校准cell-cluster SE；偏差方向未由名称识别。 |
| 从同屏r/SE推跨屏nullSE | **gate算法可执行；校准未决** | q1.py:181-187先用n_eff=((1-r²)/SE)²再转nullSE；:518-558以Validation分半为主。Pearson式换算不自动适用于稀疏median的Spearman，更没有证明同屏半测量相关的抽样分布等于跨screen完整测量相关的null/备择分布。report_q1:76承认其“与主统计量无关”，因此不应继而称资源真实功效已被测定。 |
| 完整规则power/type-I | **近似数值可保留；独立全流程校准过强** | q1.py:590-615仅抽正态rho_hat，用1.96SE和1.645SE阈值，后一项冗余；并未重跑协议主cell置换及估计全流程。report_q1:23,87称“置换零数据模拟”不准确。2000次MC的.896/.018是所设正态模型内通过率，不能验证此正态模型、nullSE或真实检验type-I。 |
| 主置换结构 | **未决** | Q协议:30拟全96cell标签置换；实际主cp全部同组织且条件布局随组织变。如何处理不存在条件、是否允许跨组织交换、固定何种可比cp尚无主执行结果。不能将正态q95当实际cell置换分位。 |
| cell-share零模型 | **构造可报告；“悲观界”过强** | q1.py:559-588已披露结构caveat；加性cell主效应在原始y的Q双差中会消去，直接给Q加u_c-u_c'不是同一null。没有保守性证明，share>=.25的.264-.294不能成为资源硬下界。 |
| 单药调整数据 | **字段可用；充分解释未决** | challenge_A0.md:150-157核7列存在、空值/非数值哨兵0；Q协议:43-49固定F与beta。不能说没有单药资料，但当前没有H193b效果。仅LIBRARY_EMAX的一维线性F不覆盖所有单药/剂量解释。 |
| 访问声明 | **需澄清；非效果泄漏证据** | q1.py:190-207把主/敏感性端点和7单药列转数值；:317-328在gate前聚合矩阵。JSON.response_value_use_attestation却仅列主端点。若used仅指进入gate，应与已访问区分；未见辅助数值用于择单位/调参。 |
| 解冻/静态解释 | **一处方向错误、一处过强** | q1.json → judgment.unfreeze_conditions称把latent门槛改为below.10可解冻：对MDE<=delta规则，降低delta反更难。boundary_wording及report_q1:101的静态解释“不受影响”只能指工作基线保留；未做主Q不能为加性模型赢得经验证据。 |

PROTOCOL_Q.md:28与report_q1.md:62的“rho<.10解释方差<1%，故不足支持任何反馈决策”没有效用推导。Spearman平方是秩线性关联的量，不自动等于功能响应解释方差，更不决定top-k/稀有高值/有代价动作的效用；固定.10可作为公开工程偏好，不能升级成普适药物发现价值定律。

### 3.1 主层实际支撑：本次独立元数据枚举

仅使用 matched_conditions.csv 的ID、设计、组织、barcode数量，未读取响应：

| 量 | 复算 |
|---|---:|
| 主cycles / cp / cells | 92,039 /1501 /96，命中新q1结果 |
| 每cp cycles min/median/max | 6 /58 /134 |
| 不同条件对 | 229 |
| 真正进入主层的cell×condition键 | 4,686 |
| Pancreas / Breast / Colon内cp | 378 /528 /595；跨组织cp=0 |
| Original有≥1完整分半cycle的cp / cells | 61 /21 |
| Original有≥5完整分半cycles的cp | 42；其余19个cp的可靠性median依据少于主分析规定的5个对比 |
| Validation有≥1 /≥5完整分半cycles的cp | 1501 /1501 |
| 共同键中Original / Validation ≥2 barcode的键 | 1593 /8974，命中最新JSON/报告 |
| 共同键中有Original重复键的cell | 36；其中只有21个能在主层形成上述61个可靠性cp |

ERRATA的46cells/583cp是Original全重复键回路宇宙；36是有重复共同键的cell；21是能形成controlled_anchor可靠性cp的cell。三者不冲突，但不能用全宇宙覆盖代表主层可靠性。q1.py的cp_median对分半有限Q直接取median，未再要求分半≥5个，所以可靠性与主目标的聚合精度也不同。

可重放方法：CSV逐行建立 cell→(anchor,library,anchor_conc,library_conc)→两screen barcode数；枚举cell组合，取共同条件，按(anchor,anchor_conc,library_conc)分组；组内不同library选二组合；主cp要求≥5。可靠性再要求四键在该screen均有≥2 barcode。这里的229/4686/21/42是本轮新元数据统计，不是原报告结果。

report_q1.md:79称iid校准“膨胀1.36×”；最新JSON的 design_check.mde80_obs.debiased_empirical_sensitivity.calibration_inflation_factor 实为 .874864。:25,77称“bootstrap SE为iid的2.8倍”也应区分：实测分半SE=.047567，除iid null SE=.025820为1.842倍；2.824倍来自换算后的null SE=.072902，而非直接bootstrap SE。这些尺度混用不能支持“已证明非抽样假象”。它们不改变现行公式gate的算术结果，但削弱该gate已经校准的论证。

### 3.2 两个推理反例：限定对象，不是数据效果

**signed median会消去完美稳定的条件结构。** 设同anchor/同设计的四个library在两screen均有y(c,p)=z_c v_p，ID顺序的v=(1,-1,-1,1)。任意cp的六个Q，除共同因子z_c-z_c'外为(2,2,0,0,-2,-2)，median=0。非零cycle可以全部完美复验，但每cp主median恒为0，主相关未定义。仅将同四条件的ID重编码排序成v=(1,1,-1,-1)，六对比变为(0,2,2,2,2,0)，median=2。本轮已做确定性算术。它不声称Jaaks真实存在此模式，只证明P1不是一般可复验交互的必要条件。

**独立挑战中的纯screen×condition项也会消去。** 若y_gcp=mu_g+a_gc+b_gp+h_gcp，固定screen内的Q把a_gc与b_gp均精确消去。challenge_A0.md:48将一般screen×condition列为Q残留项不准确；真正会留下的是随cell变化的screen×condition扰动，或各键不共享的误差/拟合偏差等。screen与batch不可分的总限制仍成立，但不能用一个实际会消去的项证明它。

### 3.3 H193b可以回答什么

Q协议:46-48的跨screen互用beta不是通常按独立样本折训练的nuisance cross-fitting：beta_B由Q_B估计后进入A残差，beta_A反向进入B，会给残差相关引入额外依赖。纯线性null示例：两screen独立、同一固定特征f、P为其投影，残差为R_A=Q_A-PQ_B、R_B=Q_B-PQ_A；在独立同方差Q下，Cov(R_A,R_B)=-2 sigma² P，而非0。因此主张“避免自减”不足以保证无偏；若将来执行，null/CI应包含整个beta估计步骤。这里没有运行H193b效果。

端点本身已经是Bliss expected-minus-observed残差（现有 drugcomb-endpoint/report.md:132,150给出定义与恒等式）。固定anchor A时，expected部分含A_c×E_cB；比较library B/C再比较cell会出现差中乘积，而非仅library EMAX的一维加性F。anchor浓度相同不使anchor viability在不同cell相同。因此字段确实支持一个冻结的线性解释诊断，不能因其仍显著就称“排除了全部单药/剂量解释”；也不能把未经调整Q必然认作普通单药项，严格无交互的Bliss模型本就令DeltaEMAX为0。

## 4. 能保留并继续发展的研究对象

1. **身份缺失的可迁移先验。** R192有正向排序点估计及明确组成敏感性，可研究何种注释在相同信息边界下对未来drug/context任务提供增量。需要区分药物先验、study/cell组成及配对增量；当前未过不能否证所有分子/靶点到功能迁移，当前正点估计也没证明它。
2. **共同设计下的复测条件对比。** R193共同键和同组织回路真实存在，可以研究对单药参考/测量误差稳健的复验结构。对象应有科学方向或对重编码不敏感，并说明推断对固定条件还是未来条件；数学反例要求重审对象，不授权按已看效果挑聚合量。
3. **有限反馈是否能改善未测条件的决策。** 这是独立问题，不由全局Q相关逻辑蕴含，也未被P1设计停止否证。需另冻反馈信息、受体条件、动作、成本与强基线，直接检验配对收益；“存在回路/跨筛可靠”不能替代算法创新与决策价值。
4. **动态/机制对象。** 这里是静态拟合或矩阵端点，没有轨迹、靶点占据或因果中间态。对动态辨识、控制、CV/NLP机制迁移，现有结果提供观测边界与反例，不能当生物动力学已识别或已失败的证据。

准确的证据状态是：R192完成限定构造的复现尝试，未过复合规则、特异性未建立；R193完成匹配资格和设计检查，主Q/H193b未算，停止所依赖的跨估计对象功效换算仍待验证。可以围绕“何种功能信息可复验、可传递、且对组成/参考稳健”提出新研究对象；不能用停止标签代替正向构造、最近先例差异和独立决策验证。
