# 双核心状态增益：输入恢复、真实状态敏感性与限定回顾性预测

2026-10-01；本轮从 `1d8c9440070b77f43094c9f5da81d3f88a3964f4` 的实际工作区继续。起始工作区已有未提交修改，未覆盖。原始状态、假设和 A/B/C/D 验证计划见 [start.json](start.json)、[plan.json](plan.json)。本目录是新增交付；上一轮冻结材料保留。

本轮解除了“只能认证相同基线、无法实际比较状态”和“没有可执行的回顾性 RNA 任务”两个执行阻塞，并找到特征轴完整的另一官方 STATE checkpoint。**原 Tahoe 的外部新 RNA 接入尚未认证；替代路线真实前向成功，但预先规定的输出等价容差未通过。** 没有把这些结果升级为前瞻动作或部署效用证据。

| 层次 | 实际执行及状态 | 可以得出的结论 |
| --- | --- | --- |
| 原 Tahoe 新 RNA | 31 个坐标仍无权威身份；数值匹配有多解 | 未完成；禁止猜测、补零或删除后声称合法 |
| 替代官方 STATE 输入 | 6,546 个有序特征；32 条真实原始 UMI 记录重建；2 请求、6 次真实前向 | 输入重建技术成功；输出等价检查失败；外部新 RNA 认证未完成 |
| 原 STATE 状态敏感性 | 3 个真实控制池 × 3 种子，9 请求、36 次真实前向 | 输出响应基线变化；幅度仅为种子变化的约 1.14 倍；不证明预测改善 |
| ReSisTrace 回顾性状态预测 | RidgeRNA；425 个匹配测试单元；可见/盲参考/置乱/无变化 | 可见 MSE 0.4669，盲参考 0.2617；限定预测负结果，非 STATE 结果 |
| 知识辅助预测诊断 | PublicTargetGOKernel；嵌套开发验证，共 94 次拟合 | 原负结果主要伴随弱响应一致性及幅度失配；收缩后接近无变化，未证明知识贡献 |
| 前瞻动作、终局效用 | 未运行 | 尚无满足其独立证据门槛的任务；不是测得零增益 |
| 部署净价值 | 不可识别 | 决策前可读取、完整尝试与成本等缺口尚在 |

## A. 新 RNA：恢复了什么，仍缺什么

### 原 Tahoe 路线

重新核验 STATE 官方仓库版本 `9bbfe78a434a55205e4de834e1ea99f85f7a3add`，发现正确模型库为 [ST-HVG-Tahoe](https://huggingface.co/arcinstitute/ST-HVG-Tahoe)，固定 revision `ca6b751972493f8448e3256d1340ae70ad43e1e7`。此前旧名称 `ST-Tahoe` 的 401 不等于正确公开模型不可取得。此为对旧获取结论的追加更正，未改写旧收据。

取得其实际 `zeroshot/generalization.toml`，SHA256 `83ee774e7e3709d3fa123e279685905dd055c4b900df8155c4c4b1047ef6f37c`，原件 [actual_tahoe_split_v2.raw](material/actual_tahoe_split_v2.raw)。该文件列出 C32、HOP62、HepG2/C3A、Hs 766T、PANC-1 的 test 标记，并未将 NCI-H596 列为 cell-type holdout；它与配置引用的 `generalization_zeroshot.toml` 文件名仍不同。文件内容不能证明该权重实际采用了哪份训练数据。**训练细胞、药物、样本与结局的实际暴露仍 unknown；c39 是本地开发资料。**

官方 notebook 继续消费已加工的 `obsm`。公开 issues [279](https://github.com/arcinstitute/state/issues/279)、[268](https://github.com/arcinstitute/state/issues/268) 也提出 2,000 维轴缺失；issue 150 的“使用原来的轴”没有给出该轴。PR [246](https://github.com/arcinstitute/state/pull/246) 在所取版本为 open/unmerged，不能倒推旧权重特征。相关固定原件见 `evidence/` 和 `followup/`。当前通用预处理重新筛 HVG 的代码不是旧权重导出配方。

对剩余 31 个坐标进行了全部 c39 行的唯一性检查：25 个坐标全零，每个有 **26,097** 个全零基因匹配；其余 6 个各仅有 1 个非零细胞，每个仍有 **2–5** 个精确数值候选。因此统计匹配也不能消除身份歧义。见 [统计](unresolved_coordinate_statistics.json)、[候选及多解记录](tahoe_numeric_candidates.json)。没有将候选升级为认证。ST-HVG-Parse 的 `var_dims` 有 18,308 个名称但模型输入为 2,000，也没有闭合有序子轴。

### 单独命名的官方替代路线

使用 [arcinstitute/st-x-replogle-full](https://huggingface.co/arcinstitute/st-x-replogle-full) 的 `k562_0.99`，revision `48ad5f70215ab4c58caa5a68e77d837601d29d35`。权重 664,158,271 bytes，SHA256 `e616f13fc127d0c46ebfebfe21b2b1f12e7e1e63d65ed09230b41c5f96f6e15b`。这是另一个 STATE 模型，不是原 Tahoe 模型修复后改名。其基因干预也不能与原 Trametinib 药物菜单混用。

`var_dims`、权重超参数和官方已处理数据共同支持 **6,546 个完整有序坐标**，输入/输出均为 6,546，扰动编码 2,024 项，batch 编码 56 项，上下文映射包含 hepg2/jurkat/k562/rpe1。映射存在只说明技术编码可用，不证明某上下文是训练留出。配置和模型文件 SHA、逐坐标 Ensembl 映射见 [contract.json](raw_reconstruction_v3/contract.json)。

从以下固定原始大文件做有预算上限的 HTTP Range 读取，保存每块起止、大小、SHA、时间和失败，不下载约 30 GB 的整个合并矩阵：

- `State-Replogle-Filtered@d790193bb2c93726541a75ca3fa873a92ed44da5/replogle_concat.h5ad`。
- `Replogle-Nadig-Preprint@833d2be9f604dd656ebaddf875d9ad3fbf5dda0d/GSE264667_hepg2_raw_singlecell_01.h5ad`，145,473 × 9,624 原始 UMI。

确认 hepg2 背景后，仅移除合并导出条码的精确 `-hepg2` 后缀，关联前 32 条 processed 记录与原始 native barcode；不按表达相似性关联。原始行号/ID 在 [raw_processed_join.json](replogle_extraction_verified/raw_processed_join.json)。第二次独立获取的计数、加工矩阵和三个轴全部一致，见 [extraction_reproduction.json](extraction_reproduction.json)。

研究转换器先对**全部 9,624 个存储基因**做 CP10,000，再 natural log1p，按完整映射取 6,546 坐标，输出 float32。两个不同 Ensembl ID 共用 HSPA14 符号时保留为不同坐标；明确映射匹配官方的 `HSPA14`/`HSPA14-1` 命名，不按符号求和。Ensembl 版本后缀不擅自删改，参考注释 release 仍 unknown。非法/缺失/重复/重排 ID、非整数、负数、非有限数和空文库显式失败。没有匹配模型背景、batch 或动作时拒绝，不 fallback。

32 条同记录重建的最大绝对输入误差为 **4.76837158203125e-7**，通过预定 `atol=rtol=1e-6`。但这只是特定存储基因全集下的经验重建；原始测序过滤、全基因分母及训练导出的精确历史配方尚不全。`convert_counts` 默认拒绝外部新 RNA，只有显式 `research_reconstruction=True` 才运行研究重建。不能直接将它当成通用新样本接入器。

### 实际加载失败、最小兼容修复和未通过项

新权重最初被当前 transformers 5.17.0 的 architecture validator 拒绝：hidden size 328 不能被 12 heads 整除。然而权重显式指定 head_dim 64，8 层 q/k/v 为 768×328、o 为 328×768；旧 transformers v4.55.0 的公开配置支持此结构。没有升级/降级环境或改写权重。

v1 原始失败、v2 仅替换方法而缓存验证器仍拒绝、v3 针对**完全匹配该几何结构**的进程内兼容修复均保留。适配器检查实际张量，替换方法及缓存 validator，仍 strict load，进程结束即撤销。证据见 `compatibility/`、[适配源码快照](raw_reconstruction_v3_compat_source.py.txt) 和各版 stderr/receipt。

v3 用一条真实 hepg2/gem49/non-targeting baseline，固定 TFAM、MAP2K7，各 16 请求行，seed 42，对“原始重建”和“官方加工”各运行一次。**2 请求成功、6 次实际 forward；物理实验为 0。** 两输出最大差 **2.2649765014648438e-6**，预定 `atol=rtol=1e-6` 的配对输出检查**失败**。后续 float32/Scanpy/运算顺序诊断仍残留输入差；未放宽容差，也未挑选通过的记录。

v3 历史 summary 的 `technical_reconstruction: passed` 过宽；同文件的 `paired_output_tolerance_pass: false` 原本正确。保留原文件，在 [勘误](raw_reconstruction_status_erratum.json) 明确总状态为“输入重建与真实前向通过，输出等价未通过”；现代码修正该状态。**替代模型的完整前瞻认证仍未完成。**

## B. 原 STATE 对不同真实状态的敏感性

[冻结](sensitivity_v1/freeze.json) 先按元数据选 NCI-H596 的 plate1、plate10、plate11，各取前 30 个真实 DMSO 控制细胞；固定原权重 SHA256 `2c9b2e74f59c2fdde73e77c3eec8a8ed26a00e5237d2b5bb3b02122475f623a3`。这些控制来自实验终点，不是已认证决策前基线。不同 plate 是本技术试验有意替换的池，不宣称它们是前瞻匹配控制或独立培养。

菜单为 Trametinib 0.05/0.5/5 µM，每动作 16 请求；种子 17/42/103 配对。终点预先固定为预测 EGR1 坐标 546 的均值，越小越优；前两名差 ≤1e-6 拒答。该 RNA surrogate 不代表存活或疗效。查询行与真实观察、物理尝试隔离。

9 个请求全部成功，36 次 forward。先对每动作 16 个查询求均值，再在三个动作和全部坐标上计算 RMS。相同种子更换池的平均预测 RMS 为 **0.1172259**；同池更换种子的平均 RMS 为 **0.1026226**；比值 **1.1423**。这是描述性敏感性，不是信噪比显著性检验。动作间预测差值和排序见 [summary.json](sensitivity_v1/summary.json)。

9 个池间配对里 7 个选择器输出变化：**只有 1 个是两个具体动作间的切换，另 6 个涉及拒答**。同池跨种子的 9 个配对也有 4 个变化，均涉及拒答。对种子求均值后，三个池都选 5 µM。单种子没有处处占优的动作，但目前也没有稳定的状态特异排名优势。见 [解释及计数](sensitivity_interpretation.json)。同背景整池循环替换使用相同实际预测，不引入跨细胞背景置乱。

因此“输出是否响应状态”有技术正结果；“状态是否提高预测准确性”在这个 STATE 试验中**未运行**；动作正确/错误/终局效用均没有合法观测参照。不能将预测变化称为状态增益。

## C. ReSisTrace：可完成的限定回顾性状态预测

本轮新取 GSE223003 的 8 份原始计数和 8 份元数据：carboplatin rep1 GSM6938163/64、rep2 65/66；growth control rep1 GSM6938175/76、rep2 77/78。固定分析代码 revision `26203470e69a311c25ab666310353391f3cc46bc`。article DOI [10.1038/s41467-024-45478-7](https://doi.org/10.1038/s41467-024-45478-7)；论文 CC BY 4.0、代码 MIT 的证据沿用已保存原件，数据使用许可仍 unknown。没有把论文许可自动套给全部资产。

代码 `Preprocess_Carbo_2.Rmd` 668–684 行说明 `sisters` 是仅在 before-treatment 样本中按完全相同 lineage-label combination 分组；752–802 行的 `prer_r_group` 则使用 pre/post 匹配，只用于之后关联响应。Control2 的对应部分为 760 行附近和 849–897 行。论文 protocol 支持破坏性 pre aliquot 与 sister 后代关系，不能写成同一细胞纵向 RNA。

为所有已沉积基线组建查询，输入只使用 pre RNA、pre-only sisters 或 singleton native cell ID。不用 `drugSens`、后代是否检出或后代 RNA 选择特征、构造输入或决定谁得到预测。先固定 256 基因、查询列表、上下文内置乱，再读 post 表达。后验 exact-match ID 仅关联真实后代 RNA用于训练/评分；缺失响应不填零、不当死亡。分母是全部**已沉积、经作者 QC 的基线组**，不是全部原始入组/尝试。

模型是单独命名的 **RidgeRNA**，不是 STATE 或 TxPert：Kuramochi 与原 STATE 药物契约不兼容。rep1 训练、rep2 保留为本次探索性测试；rep1 内 hash 五分之一作开发验证，α=10 固定不调参。基因只按 rep1 的 pre RNA 方差选择；CP10,000 使用全存储基因的实际 UMI 总数，逐样本与 `nCount_RNA` 一致。所有 ID/变换写入 [freeze.json](resistrace_v1/freeze.json)。

盲参考为 rep1 对应 action context 的全部基线组均值；可见/盲组用相同 Ridge 模型族、α 和拟合预算。盲组常量输入产生训练后代的上下文平均预测，和单独的简单上下文均值基线相同。置乱只在同动作、同 replicate 的全部基线组内进行。该开发盲参考适用于这个辅助研究，**不等于为原 STATE 认证了独立培养的盲参考池**。

| 测试背景 | 已沉积基线组 | 有 exact-match 后代 RNA | 覆盖率 | 可见 MSE | 盲参考/上下文均值 MSE | 置乱 MSE | 无变化 MSE |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Carboplatin rep2 | 4,432 | 214 | 4.83% | 0.534303 | 0.277508 | 0.714392 | 0.510379 |
| Growth control rep2 | 1,870 | 211 | 11.28% | 0.399456 | 0.245937 | 0.560998 | 0.531601 |
| 两背景等权 | — | 425 | — | **0.466879** | **0.261722** | **0.637695** | **0.520990** |

rep1 对应覆盖为 186/4,569 和 296/2,565。实际后代、预测及评分索引分别保存在同一 npz 的明确命名数组里；从未把预测当作观测补齐。问题及关联表见 [baseline_questions.json](resistrace_v1/baseline_questions.json)、[response_joins.json](resistrace_v1/response_joins.json)，原始行和哈希的补充定位见 [response_source_index.json](response_source_index.json)。

可见 MSE 比盲参考高约 **78.39%**。可见优于置乱、且总体优于无变化，说明某些对应关系有预测信息，但不足以支持对最强简单基线的状态增益。Carboplatin 可见甚至劣于无变化。pooled calibration slope 可见为 0.7581/0.8347，盲参考为 0.9920/0.9941；完整 MAE、截距和开发验证见 [summary.json](resistrace_v1/summary.json)。这些是混合基因的 pooled 校准量，不能代替逐基因或培养层级校准。

资格限于“**已沉积且可精确关联的后代条件下的 RNA 预测**”。未检出可能受生物学、采样、扩增、标记及 QC 影响，选择机制未知；不能外推到全部细胞存活、死亡或平均药物因果效应。replicate 是实际文件分组，不认证为独立启动培养；可能共享 transduced pool、vial 或亲本。因此无物理层级 CI，也不声称真正未见生物学个体的泛化。作者元数据及研究方向此前已查看；本研究明示探索性，不伪装成确认研究。

状态采样在处理前、但处理完成/可读取时刻未知，不阻止上述限定预测研究；仍阻止“当时可据此作 RNA 决策”的结论。两个背景分别建模，不视为同一亲本的多个已随机分配动作，更不比较其存活效用。

## D. 知识预测负结果：诊断后只做一个最小改进

旧 [knowledge_run_v2](../20261001_state_prospective/knowledge_run_v2/summary.json) 的 GO 模型较剂量基线 MSE 高约 4.67%，且不如无变化。该结果不改写，所有旧结局本轮一律视作开发资料。

检索并保存强基线文献：Nature Methods [10.1038/s41592-025-02772-6](https://doi.org/10.1038/s41592-025-02772-6)，及 Science Advances [10.1126/sciadv.aed3414](https://doi.org/10.1126/sciadv.aed3414)。文献支持把简单预测和匹配控制纳入比较，并不证明本数据的失败原因。TxPert 的公开实现、非公开图限制和 batch-matched control 要求沿用上一轮固定源审查；本轮未运行 TxPert，也未扩张图谱。

开发数据中的实际诊断：

- 历史 1,296 个 condition/plate 组仅 536 个进入评估，另外 760 个完整保留：743 个缺少图内精确靶点、8 个低于细胞数规则、6 个没有精确药物元数据、3 个发生空化学字段转换错误。379 条药物注释中 264 条有 provider 靶点，只有 163 条能匹配图基因。Afatinib 的 EGFR/ERBB2 有注释却不在此图的可匹配轴中，不能称为该药“没有已知靶点”。本轮保持旧资格集合以避免事后改变比较，详见 [coverage](knowledge_coverage.json)。
- 同药物/同剂量跨 plate 的 170 个响应对，cosine 中位数 **0.02195**。这说明当前控制中心化响应的复现性很弱；不是独立培养的可靠性估计。
- 同 plate/剂量不同化学身份的 10,186 个对，GO 相似与 RNA 响应相似的 Spearman **0.02787**。共享 pair 依赖下不附未经校正的显著性声明。
- 536 个外折记录中 35 个无同剂量的正 GO 邻居；其余“有邻居”也不保证作用方向/效力可转移。
- GO 预测平方均值 **0.00174091**，预测与响应内积均值 **0.00009482**。按 `MSE=E[y²]+E[p²]−2E[py]`，预测幅度代价远高于有用对齐；该诊断按记录均值，不能与按化学身份宏平均 MSE 混淆。
- 现注释只有静态靶点/GO；无每个剂量的效力、占有率、激动/抑制方向或逐问题状态。缺少这些语义不能靠增加图节点自动补齐。

唯一改进是把预测向零效应收缩，收缩系数限制 [0,1]、只用内层留出预测拟合。保留原五个 whole-plate 外折，内外均 purge 同化学身份。v1 三个内折在 purge 后出现空训练集，保留失败冻结；只查元数据支持后改为 outer-train 内 leave-one-plate-out，两个模型相同预算，共 94 次拟合。没有查看外折结局来选系数。即便如此，因为旧结果已参与诊断，v2 仍是**嵌套开发验证**。

| 模型 | 化学身份宏平均 MSE | 宏平均 MAE |
| --- | ---: | ---: |
| 剂量核 + 内层收缩 | 0.00848447879 | 0.0478748261 |
| PublicTargetGOKernel + 内层收缩 | 0.00848443997 | 0.0478749714 |
| 无变化 | 0.00848988964 | **0.0476253802** |

GO 收缩系数约 0.023–0.080；相对无变化的 MSE 改善仅约 0.0642%，GO 对剂量的绝对差仅 3.88e-8，MAE 仍输无变化。结论是幅度校准消除了大部分伤害，**没有令人信服的新增知识贡献**。无统计检验、无新确认测试、无状态输入，不归为 STATE 结果。详见 [diagnosis.json](knowledge_diagnosis_v2/diagnosis.json)、[summary.json](knowledge_diagnosis_v2/summary.json)。

## 搜索范围、资格与剩余最小缺口

本轮覆盖官方模型/数据目录、源代码、issues/PR、notebook、GEO 原始 RNA/metadata、ReSisTrace 原始分析代码、Europe PMC 文献和两组新的 sister/pretreatment lineage 检索。查询文本、页大小和所获原文完整保存在各 `plan.json`/`receipts.json`；不是系统综述，也不声称穷尽公开数据。

此前 Live-seq、Rewind、ClonMapper、ReSisTrace AML、Cycloop/DeepCellControl 等具体排除依据继续引用 [历史审查](../20261001_state_prospective/candidate_review.json) 及仓库 STATE_IDENTIFIABILITY，不重新包装成新候选。ReSisTrace 因新增原始 UMI、metadata 和代码证据，**仅重新开放限定回顾性 RNA 预测**。新检索中的 Unify（10.1038/s41467-026-76230-y）等只作为未审查线索，不能声称排除。TRADE 原文请求 500、替代 BioC HTTP 200 返回错误体；这属于获取失败，不是论文或设计不成立。

三种前瞻入口分别仍缺证据：sister panel 缺可读取时点、动作分配/完整账本及共同效用；完整策略比较缺随机入组/统一资源和真实终点；随机动作日志缺经认证 conditional propensity/支持及后续轨迹处理。没有要求同一细胞同时观察两潜在结局，也没有用估计器填补零支持或未知历史事实。成本未知不再阻挡预测任务，但使净部署价值不可识别；没有任意设效用区间。

最少新增工作详见 [采集补充](collection_addendum.md)：完整原始 RNA 导出契约（或为另一模型独立认证）；真实独立开发盲参考培养；基线采集→处理完成→可读取→决策→随机分配→执行→结局的证据链；所有入组、取消、失败、QC、等待漂移和实际成本。独立培养级效应方差、组内相关、动作改变/拒答/失败率、延迟及成本分布是功效设计输入，当前不能给有依据的确认样本量。

## 环境、收据、测试与复现

实际解释器 `D:\anaconda\envs\maestro\python.exe`，Python 3.11.16；torch 2.7.0+cu126、transformers 5.17.0、numpy 2.4.6、anndata 0.12.19。完整依赖见 [environment.json](environment.json)。**本轮未安装、升级或降级依赖，生产 src 无改动。** CPU 实际前向也由 trace 记录；CUDA 可用并不等于本次在 GPU 运行。

公共来源共 **195 个逻辑请求**（含 Range 块），3 个获取失败，另有 1 个 HTTP200 错误体；保存约 929 MB payload。STATE 本地共 15 个请求，11 成功、4 加载失败，42 次实际 forward。服务、失败/重试、时间、字节和输入输出摘要见 [api_summary.json](api_summary.json)、[source_index.json](source_index.json)。未调用外部生成模型推理 API，STATE 全为本地真实权重。费用统一为 **unknown**，没有声称免费；自动 HTTP 重定向的底层往返数未计入逻辑请求数。未联系作者，未购买服务。临时签名地址/凭证不写入交付。大矩阵及第三方原件留本地、由本目录 ignore 防止默认提交。

相关统一测试 **176 passed，0 failed，0 errors，0 skipped**，约 56 秒；[实际命令、源哈希和环境](verification.json)、[XML](verification.xml)、[stdout](pytest_stdout.txt)。其中本轮契约测试 14 项；测试包括全库归一化后取轴、非法计数/轴拒绝、未来关联不改变基线分组、未匹配不当死亡、盲模型不读取逐问题状态、库总数/身份、拒答与 Range 响应偏移检查。旧前瞻认证的测试继续通过，不等于本轮重跑全部旧真实 checkpoint 不变性试验。已运行的失败均保留在 [execution_failures.json](execution_failures.json)。

从仓库根目录用 PowerShell 运行。输出目录必须新建，以下 `reproduce_*` 为复现目录名，不是历史执行名称；实际子进程命令在 receipt，冻结的执行源码在每个 run 目录。取数计划可按 `state_search_acquire --plan ... --out <新目录>` 重放，保持相对来源布局。

```powershell
$rnaPy = 'D:\anaconda\envs\maestro\python.exe'
$rnaRun = 'tools/datasets/audit_results/20261001_state_response'
& $rnaPy -m tools.datasets.state_sensitivity --root D:\MAESTRO --out "$rnaRun/reproduce_sensitivity"
& $rnaPy -m tools.datasets.resistrace_retrospective --sources $rnaRun --out "$rnaRun/reproduce_resistrace"
& $rnaPy -m tools.datasets.state_knowledge_diagnose --previous tools/datasets/audit_results/20261001_state_prospective/knowledge_run_v2 --out "$rnaRun/reproduce_knowledge"
& $rnaPy -m tools.datasets.state_replogle_extract --out "$rnaRun/reproduce_extraction"
& $rnaPy -m tools.datasets.state_raw_reconstruction --sources $rnaRun --inputs "$rnaRun/reproduce_extraction" --out "$rnaRun/reproduce_raw"
& $rnaPy -m pytest -o addopts= -q tests/test_state_response_research.py tests/test_state_prospective_input.py tests/test_state_knowledge_retrospective.py tests/test_state_evidence_followup.py tests/test_state_search_build.py tests/test_state_identifiability.py tests/test_state_public_review.py tests/test_state_adapter.py tests/test_state_runner_paths.py tests/test_condition_response_modes.py tests/test_input_basis_identity.py tests/test_repository_shape.py
```

原始运行后只修正 raw 重建的摘要状态文字并增加 `--inputs` 复现入口；差异和源哈希见 [source_evolution.json](source_evolution.json)，不改原结果。最终原件、冻结、模型输出及历史前缀完整性见 [final_integrity.json](final_integrity.json)，交付清单见 [delivery_manifest.json](delivery_manifest.json)。没有提交或推送。

本轮有真实观测支持的是同记录 UMI 重建、真实控制池敏感性、ReSisTrace 条件后代 RNA 误差及 c39 知识模型诊断。STATE 的生物学预测增益仍未测；辅助 RidgeRNA 的所定义比较为负结果；技术选择变化已观测，但实际动作改善效用未运行；部署净价值仍不可识别。
