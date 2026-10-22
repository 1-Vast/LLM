# 独立怀疑方审查：心肌安全药理

2026-10-22；当前处置 **NO_CORE_INNOVATION_PROMOTED**。可以建立有价值的功能预测/校准实验，但现有证据不支持把普通离子通道动力学、群体校准、主动学习或程序选择改称新机制或 RSI。本审查不否定心肌应用；它区分数据适配性与技术新颖性。

## 实际读取和历史重复检查

正确以 XML 解析并记录 SHA256 的三篇全文见 `SOURCE_REVIEW_EXTRACTION.json`：

- *Integral approach to organelle profiling ...*，DOI `10.3389/ftox.2025.1644119`。
- *A Deep-Learning-Based Scoring Framework ...*，DOI `10.34133/csbj.0217`。
- Blinova et al.2018，DOI `10.1016/j.celrep.2018.08.079`。

历史 `*DECISION*.md/*PROTOCOL*.md/*REPORT*.md/*FINDINGS*.md/*REVIEW*.md` 的 cardiac/CiPA/TdP 关键词检索只出现零散引用，没有定位到已执行的 CiPA 研究阶段。这是有限检索，不是整个历史未研究该方向的证明。已读既往双核心协议对“普通程序修改并不预先构成算法创新”的明确区分；本次遵守该界限。初次过宽全文搜索输出严重截断，随后改为限定文档名检索；一次尝试读取不存在的 `research/next_asset_20261022/extract_next.py` 失败，未修改该路径。无数值结局据此分析。

## 已有工作构成的实质反驳

2025 organelle 工作已做三名 donor、17 种小分子、205 形态参数、MEA、FDA 临床类别和 sPLS-DA；形态/功能融合不是新的贡献。作者报告的76%是作者结果，不是本项目复现。GSE289264 是已认证 RNA repository 指针，不能据此声称所有影像/MEA 原始数据均已公开下载。RNA 使用每药“最大功能效应且不显著损失存活”的选择浓度，也不能直接拼成完整多剂量多组学轨迹。

multi-donor AI 全文明确 baseline-only autoencoder、reconstruction-error、五 donor、1,029 compounds、剂量与 donor vote、heldout donor；完整高通量 screening dataset 必须 request。代码链接不是完整原始数据可得的证明。重命名 autoencoder latent、donor adaptation 或 uncertainty score 不构成新机制。

Blinova2018 的真实公开表由并行数据审查员获取，本审查没有重复下载。作者已将 arrhythmia、repolarization、临床 Cmax 浓度关系用于回归，已讨论 sodium/calcium/potassium 正控校准、site2 serum-free 与 site4 dofetilide sensitivity、balanced multichannel block、未测 free concentration、波形下降导致 FPD 难测。作者还报告 quiescence 不能进一步改进其选定模型。因而“正控适配世界模型”“以 simulation/hiPSC 差异寻找机制”“把静止和心律失常区分开”均已有非常接近的任务内先例，须比较而非宣称首创。

更强的机制/改进程序先例：

1. Li et al.2017，`10.1161/CIRCEP.116.004628`：primary-index/abstract 已实际取得，整合 dynamic drug-hERG binding、multichannel pharmacology 和 ORd。故加药物结合动力学不是新机制。本次未取得其全文，不声称已核查所有实现细节。
2. Passini et al.2017，`10.3389/fphys.2017.00668`，全文 `passini2017_fulltext.body`：1,213 calibrated ventricular AP model population、62 reference compounds、concentration-response、多 phenotype 与 repolarization/depolarization abnormalities；不同 ionic profiles 的 vulnerability 及 repolarization reserve 已属作者机制。
3. *Bayesian Calibration ... Using Restitution Curve Emulators*，`10.3389/fphys.2021.693015`：索引/摘要明确 PCA+GP emulator、posterior calibration、identifiability、未探测条件下不同 parameter settings 的预测分歧。潜在参数后验和模型分歧本身不新。
4. *Model-driven optimal experimental design for calibrating cardiac electrophysiology models*，`10.1016/j.cmpb.2023.107690`：摘要明确自动设计 voltage/current-clamp 以识别各主要电流的 cell-specific conductance，并检验后续预测。参数识别驱动测量选择已有直接先例。
5. 最新 cAPM，`10.1016/j.compbiomed.2026.111882`，首发2026-07-30：primary-index/abstract 明确 task-agnostic pacing→ECG surrogate、active learning、continual retention/replay、跨 physiology/geometries sequential tasks；评估是 in-silico pace-mapping，并非相同 cardiotoxicity 场景，也未由摘要建立“改进策略本身的改进”。但 world+AL+继承这个组合本身已经不能作为新颖性主张。

以上新增主源的实际响应、HTTP200 receipts 和哈希均在本目录。一次查询命中31、仅取15，不是穷尽性综述；后四个中除 Passini 外本次依据索引/摘要，不能升级为全文方法认证。

## 唯一允许保留的候选：显式观察状态的校准

**候选地位：基线/探针，非已通过的新机制。** 结构上先预测观察状态，再对有效测量预测功能：

`p(m, z | drug, concentration, context, paid feedback)` 与
`p(ddFPDc | m=measurable, drug, concentration, context, paid feedback)`。

`m` 是可测性，`z` 是作者定义的 EAD/Q 等观察类别。两者不是同一个变量：未测 ddFPDc 不得自动设为 Q、EAD、零或最坏风险。若作者规则不能认证 null 的含义，就只保留“是否存在合法有限测量”这个观察事实，停止病理性缺失主张。普通 two-head/hurdle model 可以实现这条规则；结构本身并无已识别的独到之处。解释性 mechanistic simulator 若可用，应额外预测同一状态，但不能用成人 ventricular APD 与 hiPSC ddFPDc 强行同标度。

唯一先验明确的可检验收益是：**同等已付 assay query 数下，在未查 site–drug–dose 组合上，预测观察状态和条件 ddFPDc 的泛化更好**。这比直接复述公开的28药临床 risk 更能检验实验反馈；risk 已随 shared strings 暴露，不是新发现终点。15 site/line/platform contexts 来自10 sites、2商业细胞，不是15 donors；同site两个细胞context不得当独立 task。

必要最小比较：同药 source-context 剂量均值/曲线；site-calibrated/混合效应曲线；same-information direct two-head predictor with missingness mask；普通重拟合；fixed/selective query with equal query bundles。若有 simulator，再加 calibrated simulator 和简单 simulator/direct mixture。缺失状态监督和同样可用的 paid feedback 必须全部公平提供。不能把 outcome-associated EAD strings 放进预测未查询状态的输入。

评价按 heldout **site** 分组，并按 drug 处理重复测量相关性；跨药泛化需要另报整药持出，不能拿同药在其他site的插值称新药预测。查询一次 `(site, cell, platform, drug, concentration)` 的全部对应记录，不能把8859行、技术重复或剂量点各算一个独立任务。well/run/replicate 映射尚未认证，停止任何单井预算或独立样本量声明。

观察状态用 proper scoring rule，条件连续值用 dev-frozen standardized MAE，且同时报告 coverage，避免只在容易可测条件获利。数值成功边界必须在 dev-only 噪声/用途分析后冻结；目前没有合理依据编造提升阈值。本审查**未打开/拟合 assay scalar，未注册数值检验已成功**。若增益被 direct two-head+mask、同药曲线、普通refit或简单混合消除，则停止“world observation mechanism”主张；即使获益也仅说明该观察处理有用，仍须审查一般 missing-data/hurdle/joint model 文献后决定是否有技术贡献。

## 对智能体、继承、RSI的边界

先运行 fixed-method 单项探针即可回答数据是否支持功能预测，不需要先发明复杂智能体。后续若只有 program menu selection 或 query-policy search，按其本名报告；这不能由有限15contexts自动升级为RSI。

C4 必须在同一初始化世界模型、相同输入/预算/搜索空间上比较同一 improver 的早/晚 checkpoint，衡量后续改进曲线或 budget-to-target；并对比 equal-budget ordinary search/AL/CL。旧 checkpoint=direct、新 checkpoint=mechanistic world 的比较不能识别策略改进。站点内重复与同药重叠要纳入训练/评估依赖，不能靠多随机seed制造task population。当前尚无C4证据。

**最终建议：**允许上述窄校准探针作为证据生成；不将其提升为核心创新。暂无足以申请“深入创新机制验证”的心肌机制候选。若想继续创新方向，应在真实数据支持的失败类型中寻找无法由这些已有程序解释的效应，再交由不同立场独立评审，而非增加模块修饰已有工作。
