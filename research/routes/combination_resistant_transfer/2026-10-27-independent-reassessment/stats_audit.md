# 独立统计审查：失败判断、功效门槛与可引用范围

2026-10-27。只读审查 A0、P-B/P-B2、阶段 2 v1–v3，并按协调者追加范围核查 R189、R5、R187 与严格调参审计。本审查不发展后续候选，不运行历史效果、模型训练或原审计脚本，不读取封存结果，不联网。所有新的计算只来自已发布 JSON 的算术，或明确标记的纯模拟反例。

**结论：多项按冻结协议停止的决定成立，但不能据此合并成“研究路线已被否证”或“整个资源原则上不可检验”。** A0 的 0.240 不是冻结五折平均主端点的 MDE；P-B 的标称 MDE80 未通过自己的功效校验；阶段 2 没有可审查的 preflight/效果结果。另一方面，A0 的全药对靶点覆盖不足、ComboCat 的实体身份不可得、R187 未观察到该采样规则的优势，都有各自成立的证据范围。

本报告的标签：**错误**＝可定位的单位、公式、估计对象或逻辑错误；**过强**＝观察不足以推出其解释；**未决**＝现有产物未识别所需量；**成立**＝在明确限定的范围内得到支持。这些标签不按数量投票。

| 对象 | 可保留判断 | 需要降级或撤回的判断 |
|---|---|---|
| A0 | 按原覆盖门槛、原随机预测 gate 为 `unqualified` | 0.240 是主端点 MDE；任意细胞状态预测都共享排序；现资源对所有 δ=0.05 实验不可检验 |
| A0 的 room | 存在加法拟合后的残差及 within-pair 变异 | 残差 0.6295 已证明可学习生物交互；ρ_ceiling=0.7879 是有效可靠性上界 |
| P-B/P-B2 | 冻结算法在指定网格未过 gate；端点饱和并非失败原因 | 标称 MDE80 已被校准；null 方差已决定具体模型/对照检验的功效；外推数字是数学最小样本量 |
| 阶段 2 | 协议经过修订；正式执行仍未完成 | 已发生外部复现失败；已证明完整规则具有 80% 功效 |
| R189 | 现冻结输入无法建立实体和注释连接；class=5 不足 12 | cell×pair 单元必定 ≤C(k,2)=351；小随机期望等于硬不可达 |
| R5 | 暴露数据中的跨 screen 反序比同细胞文件比较多，探索性 | 双文件 τ 是任何方法上限；4% 比较反序意味着 4% 可预测药对/细胞 |
| R187/R163 | 单资源、固定算法及切分下的描述结果 | 非显著就证明无优势；饱和原因已识别；切分区间就是未来任务总体区间 |

## A0：功效对象与资格判断

### A1｜0.240 与冻结主端点不一致【错误；不自动改变 gate 结果】

`PROTOCOL_A0.md:55` 的主端点是“within-pair Spearman 的**折均值**”，即先求每折统计量 T_f，再报告 T=(T_1+…+T_5)/5。`a0.py:882–884` 却以各折 `2.801585×SE(T_f)` 的平均作 gate。一般而言，`mean(SE(T_f))` 不等于 `SE(mean(T_f))`，后者还需要折间协方差。

原产物已计算另一组对应五折平均端点的数字：

- `a0.json → G3_signal_room_power.e_power_mde80.fold_mde80_bootstrap_shared_cell_mean = 0.240164`；
- 同对象 `fivefold_endpoint_mde80_bootstrap_shared_cell = 0.111932`；
- 固定细胞的五折平均随机化口径为 `0.079813`，逐药对独立随机排序口径为 `0.014061`。

实现来源为 `a0.py:870–883`；报告同时列出了两组数字（`report.md:166–169`），所以不是结果被隐藏。**实际后果**：0.240 不应被称为该主端点的最小可检效应；也不能据它估算需要增加多少细胞。即使改用脚本已有的 0.111932，该特定共享随机预测算法仍未过 0.05，因此本项错误本身不使原 gate 通过。五折模拟还未包含五个训练过程共享训练数据导致的预测依赖，0.111932 也不是实际学习器已经校准的功效保证。

### A2｜“细胞状态特征必然给所有药对同一排序”不成立【过强；实际功效未决】

`a0.py:278–305` 的 shared null 对每个重复生成一条细胞分数 `z_c`，给所有药对广播相同排序；`report.md:28,169,220` 将其解释为细胞状态特征的直接/典型结构。该 null 适用于一个纯细胞主效应分数，但不由“使用细胞表达”这一条件推出。

若预测为 `f(pair, expression_cell)`，不同药对可使用不同靶点基因、不同系数或不同交互，排序可不同。它们仍共享细胞、基因和训练资料，因而也不能直接当作逐药对独立。共享一个排序与逐药对完全独立不是穷尽两种情况；不存在已证明的方差单调关系，能把前者自动当作任意模型的保守上界。脚本自己的 `a0.json → verdict.sensitivity_notes.G3e_null_model_dependence` 也承认未来预测结构尚未确定。

此外，代码并非字面“零预测”：常数预测的 Spearman 未定义，代码实际使用的是**无信息随机预测器的分布**。随机化零分布、固定已训练预测器的抽样分布、重新训练导致的变动是不同实验。预先定义无信息随机预测作为资格规则可以执行，但不能把它称为无需学习器假设的资源功效。

**实际后果**：按冻结 null 停止成立；“本机现有资源不能支持任一可检出 δ=0.05 的排细胞实验”（`report.md:25`）过强。相反，本审查也未证明某个现实设计能达到 80% 功效。

### A3｜对 0 的检验不能门控所有 paired 增量效用【过强】

`PROTOCOL_A0.md:55–56` 同时列出 tissue-only、可加细胞主效应、随机基因等对照，但 G3(e) 只审计随机预测器单臂相关对 0。若后续问题是两个方法在同一测试单位上的增量，目标是 `D=T_new−T_base`，有

`Var(D)=Var(T_new)+Var(T_base)−2Cov(T_new,T_base)`。

共同的细胞难度或 screen 扰动可在差中消去，也可能不消去；单臂 null SE 不能识别这个协方差。纯算术反例：两个统计量各 SE=0.1、相关=0.99，则差的 SE=0.014142，MDE80≈0.03962；单臂 MDE80≈0.28016。此反例不代表本资源存在这样的模型，只反驳“单臂 MDE 大，所以任何 0.05 增量都不可检验”的推理。

**实际后果**：必须先确定要检验的是绝对排序信息、相对简单基线的增量，还是筛选行动效用。三个量不能由同一个随机预测 null 代替。对于 PB 所特定的 constant identity 基线，把未定义的 Spearman **显式扩展记分为 0**，则可以把相对该基线的记分写成单臂记分；此约定仍不能处理非恒定随机对照和 tissue-only 对照的 paired 方差。

### A4｜interaction、room 和可靠性上界未识别真实交互信号【过强；可靠性未决】

`a0.py:178–217,718–748` 实现的是 `y≈μ+a_cell+b_pair` 的最小二乘加法拟合。`var_share_interaction=0.629473` 是残差方差/总方差（`a0.json → G3_signal_room_power.a_variance_components.all_125_cells`），包括真实交互、测量误差、未建模的剂量/朝向/板/批次差异等。它不是已分离的生物交互方差。

`y_int=y−pair_mean`（`a0.py:743–748`）还保留细胞主效应，不能单独叫作交互路径。观测 SD 中位数为 0.052196 只说明观测有变异；“与自身量级比较可防止变异全是噪声”的门槛（`PROTOCOL_A0.md:42`；`report.md:146`）没有实现噪声分离。

可靠性计算还有具体公式问题：代码将**观测** within-pair 方差 `median_pair_sd²` 命名为 `var_signal`，再算 `sqrt(V_obs/(V_obs+σ_e²))`（`a0.py:744–748,787–790`）。经典独立加性误差模型若 `V_obs=V_signal+σ_e²`，相应 latent-to-observed Pearson ceiling 应是 `sqrt(max(0,V_obs−σ_e²)/V_obs)`，而不是再次把噪声加在分母。若全部观测方差都是噪声，原公式仍输出 0.707，足以通过 0.10 gate。

代入已报数字，两种公式约为 0.7879 与 0.6237；**后者仅是公式说明，不能作为本审查更正后的真实 ceiling**：借用的 R4 well-level 噪声与 Jaaks 键级 ΔEMAX 不同；`sigma_key=sigma_row/sqrt(mean_rows_per_key)`（`a0.py:779–786`）又需要独立、同质重复假设。无序键混合朝向与锚药浓度的限制已在 `report.md:236` 披露。

可保留的正面证据是已报跨筛重叠 98 个药对的 within-pair 排序相关均值 0.592679（`a0.json → G3_signal_room_power.d_reliability.cross_screen_reliability_aux`）。它提示该选择性重叠子集有重复排序结构，但不是所有 1294 药对的信号比例或独立机制证明。

**实际后果**：G3(a,c,d) 的数值计算和阈值判定可记录；应撤回“0.63 已证明真实交互”“非纯噪声已证明”和“0.788 是有效可靠性上界”。此处不支持以无信号否决细胞状态，也不支持以有交互论证必有可学习收益。

### A5｜G2 的全宇宙覆盖失败成立；union 不是同一条件【成立】

`PROTOCOL_A0.md:34–35` 明写两侧靶点均至少一个映射基因。`a0.json → verdict.gates.G2=false`，两侧各有映射为 1161/2025=57.3%，未达 90%；合计任一侧有映射的 95.0% 是另一条件。将“每侧”改成“合计”会改变可用特征构造，不能仅因结果可过而称等价措辞澄清。

**实际后果**：原全药对、双侧靶点表达方案的资料条件确实未满足。已覆盖药对子集可作为另行冻结的研究对象，但须重新报告选择范围、覆盖与功效，不能继承全宇宙资格或本审查的任何功效保证。

## P-B/P-B2：MDE 与经验 power 不属于同一抽样实验

### B1｜零模型方差包含两层随机性，power 只含一层【错误的校准对应；gate 执行事实成立】

`pb.py:659–670`、`pb2.py:285–294` 每次既重抽 pair/cell multiplicity，又重新抽 `z_pair`；`pb.py:737–740`、`pb2.py:319–322` 的功效校验则固定 y 与单位，只重抽预测噪声。这是不同的随机实验。一般有

`Var_{z,bootstrap}(T)=E_z[Var_bootstrap(T|z)]+Var_z[E_bootstrap(T|z)]`。

额外的项并非错误计数本身——若研究目标明确包含随机重生成预测器与样本的联合变动，可以定义这样的量——但不能将其直接当作固定预测器检验的 SE，再以固定单位实验验证它。

原数据产物已暴露不一致：`PROTOCOL_PB.md:167` 要求 δ=MDE80_B 的经验 power≈0.80，允许 ±0.05；`pb.json → mde['0.20'].power_check.targets['0.114850510067447'].reject_rate=0.708`。这低于 0.75。`report.md:205` 报出了该数，却未按协议把它标为校准未通过。

`pb.json → mde['0.20'].diagnostic_decomposition` 另给固定 y 置换 SE=0.027829、固定 z 的 pair bootstrap SE=0.0288，而 gate 的 pair SE=0.037882、pair×cell SE=0.040995。差异不全来自生物资源的有效样本量。纯模拟 600 独立点的对应 SD 为：只重抽 z 0.04057；固定 z 重抽单位 0.04131；两者同时重抽 0.05777，倍率 1.424，接近线性得分可解析的 `sqrt(2−1/n)`。

**实际后果**：标称“80% MDE”未经自身校验，P-B/P-B2 的精确 power/MDE、后续 F3 的继承和所需样本量应视作该算法下的条件性规划量。冻结 gate 不过可以继续作为停止记录，但不是“真实检验功效不足”已经被独立校准的证明。

### B2｜c=δ/ρ_pm 不把模拟真值校准为 Spearman δ【错误；真实功效未决】

`pb.py:723–742`、`pb2.py:305–326` 先把真实 y 的 pair mean 标准化，再生成 `z=c·base+sqrt(1−c²)·noise`，设 `c=δ/ρ_pm`。这是线性混合系数，不是 Spearman 的逆映射。即使 base 正态、每对只有一个观测，Gaussian Pearson 相关 c 对应的总体 Spearman 为 `(6/π)asin(c/2)`，不恰为 c；偏态、并列、单位权重不等时差异可更大。

纯模拟中目标参数 0.1183 在正态 signal 上得到约 0.11231，而独立构造的极偏 lognormal signal 得到约 0.00031。这里的 lognormal 反例只证明公式缺少一般校准，**不表示 DrugComb 具有此分布或其真实 power 是该值**。

`power_check` 未保存各 δ 下实现的相关均值/分布、alternative 方差或 empirical type-I error，因而无法由现有 JSON 将“0.783/0.938 拒绝率”解释为“真 Spearman=0.1183 时的功效”。未满足80%可能混合了真值偏离、两种抽样实验不同和设计方差。

**实际后果**：可以保留“特定响应驱动构造下的模拟拒绝率”，不能将其视作实际注释模型、相同真 Spearman 值或任意学习器的 power。校准需与最终检验同抽样实验、同估计对象，并验证实现的目标量；本轮未执行这种新实验。

### B3｜null variance 不能模型无关地门控具体效果与对照【过强】

pair 共享预测结构较 A0 的全药对共享细胞排序更贴合 PB 的“只排药对”任务（`PROTOCOL_PB.md:157–165`），且处理单位内重复是必要的。仍然，iid `z_pair` 没有模拟：同一粗注释水平导致的跨 pair 并列、共享药物导致的 pair 间依赖、ridge 调参/训练变动、主臂与随机映射臂的协方差。

`pb.json → judgment.verdict='endpoint_not_usable'` 同时明确 `primary_metric_usable_* = true`、`comparability_argument_holds=true`，失败是 δ_min=0.03 下的 gate。该命名不能在综合时缩写成“Bliss 端点不可用/饱和”。从 0.1149 的单 null SE 不能排除某种更有效检验，也不能保证某种实际注释模型达到该功效。

### B4｜样本量外推是带假设的规划，不是数学最小值【过强】

`pb2.py:548–598` 固定 `SE≈c/sqrt(n)`，从六个设计点取 `median(SE·sqrt(n))`，再取 unit 与 pair 两种外推的较大者。其自身在 `PROTOCOL_PB2.md:81–84` 与 JSON 中披露了固定细胞数、pair 大小分布不等比、仅六点等限制。不同 r 还改变训练池、测试组成与可预期效应，不是仅增加独立样本数。

`pb2.json → decision.design_recommendation.minimum_required_annotated_both_unseen_units` 的 14386.6/22450.6 应标为“沿该 null 算法和缩放假设的规划值”，不能写成资源的理论最小规模。更不能因为一个预注册 r 网格没有通过，就断言整个注释宇宙不存在任何可检验设计；原 JSON 自己也列出额外 r 的条件性可行方案，未宣称观察到复现效果。

## 阶段 2：v3 修订尚未得到完整功效验证

### S1｜旧 CI 下界可被选为目标数，但不构成可信下限保证【过强】

v1 `PROTOCOL_STAGE2.md:68` 与 `AMENDMENT-001.md:24` 用 R163 的 0.0947 作为“保守可信下界”。原 R163 的区间来自 40 次重叠切分均值的 bootstrap（`e163_tuned_headline.py:134–145`），内层是行级而非 both-unseen 调参，且标准化先于内层分折（同文件 `57–75`）。这些问题已被 `handoff-method-audit/report.md:7–13` 定位。

可预先把 0.0947 作为一个明确的工程/科学目标，这不因来源有缺陷就自动禁止。**但它不再享有原任务总体 95% 下界或“保守可信”的含义**，也不跨 r、端点、注释体系自动保持。`AMENDMENT-001.md:48–51` 对三种构造变化的披露是必要且成立的。

v1 的 `annotation-only` 与 R163 的 `Xboth=identity+annotation` 在训练时不等价；测试 identity 列常数不使训练拟合等价。`AMENDMENT-001.md:17–20` 已修复主臂定义。此修订可保留，但不是已有外部复现证据。

### S2｜点估计门槛与80%功效要分开；联合功效近似仍有未证假设【成立的提醒；现有校准未决】

v3 完整成功规则为 R1 点估计≥0.0947、R2 CI>0、R3 优于10次随机映射的均值（`AMENDMENT-001.md:28–35`，主 CI 后被 `AMENDMENT-002.md:16–24` 修订）。仅对零显著有80%功效不代表完整规则有80%通过率；这一修改方向成立。

不过，v3 的 F3 用 `ρ_hat=ρ_true+N(0,s)`、独立 `m_null=N(0,u)`，差 SE=`sqrt(s²+u²)`，并称忽略两者正相关是“保守”（`AMENDMENT-002.md:20–24`）。实际 Cov 的符号、10个随机臂的共同变动、平均控制的 u、null 均值，以及 s 能否迁移到非零真值，均未由 pair 随机分数 null 识别。正相关若成立，该方差会偏大；负相关或未模拟的共同训练因素存在时，就无此保守保证。忽略相关后重新生成独立估计量，也不等于仅给真实 paired 差使用一个更宽 CI。

还需避免把较早挑战表的粗算当作正式结果：`challenge_STAGE2.md:200–210` 通过乘边际通过率得到≈0.63，忽略几条规则共享同一主臂估计量。在它所写的独立正态对照假设、MDE=.075、真值=.1183 下，纯模拟完整两对照规则约为 **0.729**，而边际概率相乘约为 **0.625**；若改为10个独立对照均值则约 **0.8105**。这些都不是现资源的真实功效，只说明较早≈0.63不能当作不可执行的证明。

另外，在对称无偏近似下，真值恰为 R1 门槛0.0947时，`P(ρ_hat≥0.0947)=0.5`，完整成功率至多0.5。这一构造事实与样本量无关。因此 R1 的δ不能被读成“在这个δ处已有80%复现功效”。v3 选择在更高真值0.1183检查80%是另一明确目标，但并未证明它等于跨资源真实效应。

**实际后果**：完整规则的校准需求成立；现有解析近似不足以宣布已保证80%，亦不足以宣布一定不能通过。2000次模拟在p=.8附近的 Monte Carlo SE约.009，若将点通过率80%作为硬 gate，也应披露这一模拟误差。

### S3｜pair×cell 聚类不自动覆盖未见药物推断【未决；不能单凭 pair ICC 选定】

v3 主 CI改为 pair×cell（`AMENDMENT-002.md:16`），并以 pair ICC=.765作为原因。该 ICC说明同pair多cell有关联，不能证明**不同pair只要共享药物就独立**。如果目标是新药物总体，(A,B)和(A,C)仍共享药物A、注释与训练结构；93个粗注释水平还可造成更多依赖。若只描述固定留出药池，则又是更窄的估计对象，不能用该CI宣称未来新药总体外推。

`s2lib.py:599–614` 确实按冻结 pair×cell multiplicity重抽固定预测，主臂和其他臂使用同一重采样索引，这是 paired CI 的合理实现方向；它没有包含重训练不确定性，需要在目标中明说。留药敏感性 `617–631` 为两个角色分别独立抽ca/cb；对无序药对，同一药在不同配对中跨角色出现时，这并非一个对该药统一重抽的 dyadic 处理。角色聚类可作为特定敏感性，不能仅凭“留出药聚类”名称视作已解决节点共享依赖。

**实际后果**：不是要求把聚类维度无限增加，而是必须先冻结推断总体、共享药物/注释依赖的允许假设，并说明CI覆盖的是哪种变动；两种CI都报也不能自动证明任何一种正确。

### S4｜阶段 2 当前是未执行，不能称复现失败【成立】

本次目录检查：`research/2026-10-27-drugcomb-replication/` 有 `PROTOCOL_STAGE2.md`、两份AMENDMENT、`challenge_STAGE2.md`、`s2lib.py`；没有协议所需 `preflight.json`、`stage2.json` 或效果报告（交付要求见 `PROTOCOL_STAGE2.md:85–90`）。本审查不运行这些实验。

**实际后果**：此状态应写“预检/正式复现未完成”或“设计尚未获得可审查执行证据”。不能写“DrugComb复现了/未复现”，也不能以没有结果排除真实效应。

## R189：cell×pair 上界的单位错误

### C1｜C(k,2) 约束不同药对，不约束 cell×pair 单元【错误；当前资源不合格仍有独立理由】

`combocat-resource-audit/report.md:38,49,114` 将806定义为 cell×无序pair总单元；`119–123` 却写 cell×pair数≤C(k,2)，从k=27推出351<800。`audit.py:625–626`明确实现同一上界。一个pair可在多个cell出现，因此只用“36cells、806单元”的信息，正确通用上界至多是 `min(806,36*C(k,2))`，在k=27时仍为806。原351证明不成立。

随机固定k个药留出、每个pair含两个不同药时，任何已观测pair被全部留出的精确概率为 `k(k−1)/(136*135)`，不需要药对均匀分布；相应期望单元为30.82/72.00/125.64（k=27/41/54）。原f²近似为31.8/73.3/127.1。**小期望不能变成每个确定性切分都不可能达到门槛**；若要用概率控制，须明确随机设计和尾概率。

若还可核实“清单里的136个药全部实际参与这806个单元”，则存在另一条件性证明：非留出的136−k个药各至少参加一个非both-unseen单元，而一单元最多覆盖两个非留出药，所以 `U_H≤806−ceil((136−k)/2)`，为751/758/765，仍<800。**这是需覆盖前提的不同证明**；原代码仅凭summary ID构造N，无法从匿名root联回并核验该前提，不能静默替换原351证据。

另有直接算术错误：`report.md:151` 以 `800/f²` 写“总单元≈2,000–5,000”；r=.20–.40应约 **20,000–5,000**，即5千至2万。这仍只是相应随机设计下的期望规模规划。

**实际后果**：撤回Q2的351硬上界及据此断言“身份解决后也已证不可达”。保留实体不可得、root无法与drug/cell/class连接（`report.md:16–19,44–49`），以及冻结class定义下最多5<12（`80–83,126,132`）——它们独立足以支持本次输入的 `unqualified`，本审查没有救活这个资源。

## R5、R187 与严格调参审计的解释范围

### R5-1｜同细胞双文件τ不是“任何方法的上限”【过强；可保留经验对照】

`r5/report.md:7,14` 把τ_half=.891称为无需分布假设的任何方法上限。两次带噪测量的秩一致性，只是该条件下的重复性。知道潜在真值的预测、平均更多测量或有效去噪，均可能高于两单文件一致性。

严格反例：独立加性Gaussian误差下，若两个带噪测量的总体Kendall τ=.891，则潜在真值与一个测量的τ约=.92283。该解析反例已经否定普适上界；不需要对BATCHIE重新估计任何效果。

跨cell与同cell比较可作为探索性screen transport对照；但同cell重复同日、不同cell跨日期/批次（原报告 `54,60` 自己已披露），因此不能由差异排除纯batch/异方差解释，或将其归因于cell生物学。

### R5-2｜4%是筛选后 action 比较的反序率，不是可预测亚群比例【过强；预测性未决】

`e006e_reversal_rate.py:45–55` 在同一layout的两个响应向量中，枚举两个action单元i,j，要求两向量中gap都≥.10，比较符号；再跨file/cellpair累加（`110–122,143–152`）。因此 `report.md:38` 的362117/9043806约4%，其分母是**重复计数的合格action比较**，不是不同药对、细胞、患者或异常动作数。

其余96%只表示同一筛选后比较集合的方向未反转，不证明存在覆盖96%实体的全局共同序；也不识别那4%是否可以事前预测。`report.md:43` 的“4%的可预测少数”与 `65` 明确“没有训练预测器”不一致。

**实际后果**：保留“在已暴露screen中、两边gap≥.10的合格比较里，跨screen反序率4.00%、同cell文件比较0.29%”的探索性现象。撤回普适上限、96%共享实体结构与4%可预测亚群；cell/batch仍不可分。

### R187｜特定方差采样未显优势成立，‘无优势因为饱和’未被识别【错误的二分判定；原因解释过强】

`e187_pair_active.py:165–170` 令H438=(CI下界>0)，再令H439_no_advantage=`not H438`。未拒绝无正优势不等于证明无优势；若要排除某个有意义优势，需要相应非劣/等效边界与有效区间，不能把逻辑否定显著性当作另一假设成立。

原观察可保留：`E187_RESULTS.json → results` 两臂差−.0039736，朴素切分bootstrap CI[−.0126774,.0054419]，MDE=.014167。`report.md:23` 用MDE声称能排除>.014不恰当：MDE是设计拒绝率概念，排除效应靠有效CI；即使原CI有效，其正上界也应是.00544而非MDE。

50pair补入后分数几乎不变（`report.md:29–31`）可由学习曲线平缓、强正则、模型不适配、当前选择规则、所买数据不相关等解释，不能独自识别“饱和”原因。两臂各50pair也不保证相同测量成本：脚本 `139–145` 只保存uncertainty臂行数；原方法审计 `handoff-method-audit/report.md:17–19` 已指出此限制。

**实际后果**：保留“该资源、该λ/模型、该方差采样规则和50pair预算下未观察到优于随机的描述性优势”。不得关闭所有Agent取证、决策实验设计或主动学习原则；也不由此授权重复用户已排除的方差采样路线。

### R163/严格调参｜旧效应未被验证为总体增益，也未被证明为零【成立的限定】

原R163外层药物隔离在 `e163_tuned_headline.py:105–111` 可见；问题是内层任务、折前标准化及推断范围，并非已证明外层测试标签泄漏。40次重叠切分可以在**数据固定、随机split seeds独立**的窄目标下描述切分生成器平均分的Monte Carlo变动；训练/测试共享母体不使这种条件性随机化推断自动毫无意义。但它不能充当新药/新cell/新数据集总体95%CI或未来任务power。

严格调参审计 `drug-group-nested-audit/report.md:5–14,18–24` 报行级/药分组均值.09401/.09375，范围含负值，明确不把重复切分当独立任务、身份相关未定义，且调参优化MSE而排序仅描述。它没有证明原.1183全部由某一个缺陷造成，也没有证明真实注释收益为零。宜保留为**单资源条件排序现象**，而非已确认的稳定效应或一项已被彻底推翻的发现。

## 本审查允许的统计处置

1. 保留旧协议与产物；在综合中分别标记“按规则停止”“具体前提不满足”“未执行”“现有证据未能区分”，不把这些都写成生物学失败。
2. 任何后续效果协议先写清估计对象、总体与计费单位：绝对相关、paired增量、行动价值不能混用；随机预测null、抽样SE、重新训练变动不能混用。
3. 功效校准必须覆盖最终规则及真实依赖假设，并检查实现的真值、type-I error、Monte Carlo误差；不要把任意null SD乘2.801585直接称为资源的模型无关MDE80。
4. 残差/重复性只按已识别的量报告。未分离measurement/design/batch时，不以“interaction”“ceiling”“可预测少数”等名称替代证据。

这些是对现有证据的修订条件，不是一个已获支持的新候选，也不证明下一实验必定值得运行。

## 可复核产物、来源与读取记录

- [纯模拟及解析反例代码](D:/MAESTRO/research/2026-10-27-independent-reassessment/stats_toy_checks.py)：只生成合成数值，`data_read=[]`，无模型训练。
- [反例结果](D:/MAESTRO/research/2026-10-27-independent-reassessment/stats_toy_checks.json)：固定seed20261027；600点/3000重复的双重随机性示例、paired方差算例、Spearman参数反例、50万次联合规则模拟、Gaussianτ反例与组合计数。
- 对原始生物学效果的计算次数：**0**。对他人冻结文件的写入次数：**0**。联网检索次数：**0**。

本轮读取按任务目录定向进行：先读BRIEF；读取A0协议、代码、JSON及报告；读取PB/PB2协议、功效函数、JSON及报告；读取stage2 v1、两次修订、挑战与s2lib的CI函数；定向读取R189单位与边界代码、R5两个统计函数及报告、R187判定函数/JSON/报告、R163调参与区间函数、两份严格方法审计。两次大输出被截断后按行号恢复所需部分；不依据截断缺失段作结论。没有读取输入CSV的响应、凭据或sealed材料。

主要来源路径（上文行号均对应本轮读取文件）：

| 简称 | 原文件 |
|---|---|
| A0 | [PROTOCOL_A0.md](D:/MAESTRO/research/2026-10-27-cellstate-qualification/PROTOCOL_A0.md:37)、[a0.py](D:/MAESTRO/research/2026-10-27-cellstate-qualification/a0.py:278)、[a0.json](D:/MAESTRO/research/2026-10-27-cellstate-qualification/a0.json)、[report.md](D:/MAESTRO/research/2026-10-27-cellstate-qualification/report.md:155) |
| P-B | [PROTOCOL_PB.md](D:/MAESTRO/research/2026-10-27-drugcomb-endpoint/PROTOCOL_PB.md:155)、[pb.py](D:/MAESTRO/research/2026-10-27-drugcomb-endpoint/pb.py:652)、[pb.json](D:/MAESTRO/research/2026-10-27-drugcomb-endpoint/pb.json)、[report.md](D:/MAESTRO/research/2026-10-27-drugcomb-endpoint/report.md:187) |
| P-B2 | [PROTOCOL_PB2.md](D:/MAESTRO/research/2026-10-27-drugcomb-endpoint/PROTOCOL_PB2.md:45)、[pb2.py](D:/MAESTRO/research/2026-10-27-drugcomb-endpoint/pb2.py:279)、[pb2.json](D:/MAESTRO/research/2026-10-27-drugcomb-endpoint/pb2.json) |
| 阶段2 | [PROTOCOL_STAGE2.md](D:/MAESTRO/research/2026-10-27-drugcomb-replication/PROTOCOL_STAGE2.md:34)、[AMENDMENT-001.md](D:/MAESTRO/research/2026-10-27-drugcomb-replication/AMENDMENT-001.md:22)、[AMENDMENT-002.md](D:/MAESTRO/research/2026-10-27-drugcomb-replication/AMENDMENT-002.md:14)、[challenge_STAGE2.md](D:/MAESTRO/research/2026-10-27-drugcomb-replication/challenge_STAGE2.md:198)、[s2lib.py](D:/MAESTRO/research/2026-10-27-drugcomb-replication/s2lib.py:599) |
| R189 | [report.md](D:/MAESTRO/research/2026-10-27-combocat-resource-audit/report.md:112)、[audit.py](D:/MAESTRO/research/2026-10-27-combocat-resource-audit/audit.py:610) |
| R5 | [report.md](D:/MAESTRO/research/2026-10-27-agent-cell-identifiability-r5/report.md:7)、[e006b_split_half.py](D:/MAESTRO/research/2026-10-27-agent-cell-identifiability-r5/e006b_split_half.py:168)、[e006e_reversal_rate.py](D:/MAESTRO/research/2026-10-27-agent-cell-identifiability-r5/e006e_reversal_rate.py:45) |
| R187 | [report.md](D:/MAESTRO/research/2026-10-27-agent-cell-identifiability-r187/report.md:17)、[e187_pair_active.py](D:/MAESTRO/research/2026-10-27-agent-cell-identifiability-r187/e187_pair_active.py:139)、[E187_RESULTS.json](D:/MAESTRO/research/2026-10-27-agent-cell-identifiability-r187/E187_RESULTS.json) |
| R163 | [e163_tuned_headline.py](D:/MAESTRO/research/2026-10-27-agent-cell-identifiability-r163/e163_tuned_headline.py:57) |
| 现有方法审计 | [handoff-method-audit/report.md](D:/MAESTRO/research/2026-10-27-handoff-method-audit/report.md:5)、[drug-group-nested-audit/report.md](D:/MAESTRO/research/2026-10-27-drug-group-nested-audit/report.md:5)、[replication_correction.md](D:/MAESTRO/research/2026-10-27-drug-group-nested-audit/replication_correction.md) |

