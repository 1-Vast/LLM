# 独立怀疑审查：STACK 2017 的原始轨迹资格

2026-10-22，scientific_skeptic。先读本阶段 ROOT_PROTOCOL 与既存 `functional_dynamics_gate/functional_auditor/PRIMARY_EVIDENCE.json`，另离线投影同目录已保留的原始 PMC XML；**本稿落盘前未读本阶段其他 peer 稿、manifest 新结果、数值工作簿或 QC 值**。无 GET、fit、API、数值 workbook/array 访问。离线代码在 `research/stack_raw_qualification_20261022/skeptic_primary_projection.py`，原文投影保留 `skeptic/PRIMARY_PROJECTION.json`。源为 Forcina et al. STACK 2017，PMC5509363；下载可用性与精确对象身份由 root 另行认证。

**独立结论：有条件值得资格化为多化合物、少数 cell/background screen 的 early marker forecast / retrospective follow-up triage 数据；现无新算法或 RSI 证据。** 同 screen 预测开发是合理起点，不必先有多中心独立湿实验才可运行；但多 compound/well/frame 不能被写成同等数量的独立科研改进任务。目标 qualification 未过之前不注册精确性能实验，更不从论文声称 raw 当前可取得。

## 一手叙述支持什么，不支持什么

原文明确 Nuc::mKate2 标记核对象、Sytox Green (SG) 标记膜通透后的对象，单位为 objects/mm²；检测/segmentation 对 cell line 分别优化。mKate2 丢失机制可能随细胞和 perturbation 不同；persistent mKate2+/SG+ double positives 可使 LF 低估死亡。长死细胞 SG 信号可消失，作者计算某时点 LF 时用从起始至该时点的最大 SG counts 作修正。因此 raw SG stock/其差分不是真累计死亡事件，raw red 标记也不保证每一个是真实可增殖细胞，两个 marker 不自然组成互斥守恒 compartment。

允许诚实问题：“相同已测 early red trajectory、dose/time/合法 plate/background 信息，加入 early SG history 能否更好预测 later red-object readout？”或“能否用完整合法 early markers 预测未来 source-defined marker LF/优先级？”后者在应用上可有价值，但未来 LF 本身含 SG，early D 对含 D 的 endpoint 优势不能代替对 later viable/red 功能的增量。LF 不是独立 orthogonal assay，既有最大值修正也不是新世界模型。绝不能把未来全程 maxD 带入 prefix LF；截至当前时点的 running max 与全程 MAX 是不同操作。

主要 screen 方法为：1,833-member library、5µM；T98GN ±400µM TMZ，4h/96h；U-2 OSN，2h/118h。五个 plate/experiment、起始 seed 与不同 acquisition cadence 可影响预测。三份 raw 结果若可取得，首先代表两个 cell lines、三个 cell/background conditions，不是三个随机抽取的独立领域，更不是 1,833 次科学程序改进。T98G ±TMZ 是有价值的配对背景干预，但共享 cell line/library/layout/测量流程，其外推不是第二独立生物系统。全库 screen 的每条件 run/replicate 必须从实际 workbook map 认证；论文总体“除注明外三 biological replicates”与其他小实验的三重复不能自动分配给大 screen。

## QC、选择与标签泄漏

原文存在至少四层不同选择，不能合并成一个无害 QC：

- 图像计数相对上一点变化 >10-fold 被 censor；这是响应依赖的时序处理，后来缺失可能不是随机。
- 高起始 SG/视觉判定荧光背景的 compounds 被剔除；有的判断使用 0 或4h和视觉证据，必须认证现有表实际包含哪些 flags/原始值，不推断所有 flag 仅用合法 prefix。
- 起始 mKate2 <50 或>400 objects/mm² 的 well 被去掉。可作为明确记录的基线 eligibility，但不能在不同臂采用不同 mask。
- LFmax 的 plate-specific DMSO阈值、LFmax>0.5、LED fit 可辨识性、ROL/SOL 分位等均使用未来 response，是已选致死子集/结局定义，不能给“全库 prospective early triage”偷偷定 cohort，也不能用 full-curve LED 参数作 early feature。

论文称“eight”背景 compounds 的括号列表实际可数为九个；1,833 library members 与 1,819 passing-QC 也不等于同一 unique compound 计数。现阶段不手修作者列表、不据叙述推精确 mask，须以获得的身份与 QA provenance 报告差异。盐型、重复条目、同 compound across screens/plates 与控制孔都需 identity map，不能为更大 n 当独立药物。

如果 raw workbook 已作者处理、不能恢复 censor 前值，**并不因此不可分析**：可做“作者处理后/筛选后 cohort 内的 retrospective prediction”，全臂同 mask，清楚报告无法运输到未筛全库。若 goal 为 prospective triage，则 eligibility 必须在 query 时可知，未来 QC 的使用、失败/弃权及成本需计入。当前 phase 只看 headers/identities，不打开 QC decisions 来挑最利 cohort。

## 最小可证伪的三层检验

第一层为**条件 D 信息**，不是 world-model claim。实际 raw schema 合格后，选择一个预定 physical prefix/target、主未来 readout、统一 missingness/QC 及实用阈值；所有模型共享完整 red prefix、time、dose、已知 plate/background 与合法 initial-state。四臂 L-only、D0-only、end-prefix D snapshot、full-D history 用同 supervised labels、相同候选 direct 家族/调参次数/训练预算与分组。主要报告未来 red（若这是问题）而非以后 D/joint loss；动态历史主张必须胜过两 snapshot，不能只胜少信息 L-only。若主 endpoint 选 source-defined LF，则明确这是 marker-LF forecast，不能将其阳性当独立 viability 证明。

同 screen compound-group train/validation/test 是最低可行开发：同 compound 的 duplicate/salt-aware合并（仅在身份确证时）、技术孔、所有 frames 一起分组。未认证结构/作用靶标时可按 compound ID hash 分组，不强造 scaffold/general-target claim；有合法结构时才考虑 scaffold/class holdout。drug identity不可让heldout化合物以其他 screen 的标签静默进入训练：若跨screen同 compound 的历史被允许，须另明示这是背景转移，不是 unseen-drug prediction。plate 分布/normalization须固定并逐plate报告；plate与compound布局如耦合，同screen阳性不自动是新plate鲁棒性。future DMSO/control trajectories如用于归一化，属于额外 assay-time信息，需明确可用性与成本、全臂共享，不能伪称只需早期测量。

第二层为**同信息 world contribution**：固定 L+D/history/control信息，比较强 direct temporal/prefix predictor、普通 multivariate state-space/kinetic/clearance/refit、作者 LED 的合法 early-prefix拟合（不能用 fullcurve估参）、简单固定/validation选混合及同预算模型/程序搜索。先要求未来多时点/主功能 readout上超过这些模型的预定实用幅度，保留 runtime、每类失拟与所有fold；latent injury/birth/death名称不是机制识别。若 ordinary direct/kinetic 已解释全部增益，保留通道价值，不晋升新world core。single5µM screen 不支持未测 dose-response、药代动力学或任意组合预测；±TMZ仅提供实际测过的一种 background对比。

第三层为**triage/agent contribution**，需要实际合法 query menu：每次可付费揭示哪一个 compound 的哪段未来读数、初始共同可见信息、总 budget 与反馈时间。固定世界模型/固定策略、普通 retraining/CL/AL、随机/uncertainty/简单混合、等预算程序搜索都要同反馈/成本。先在同screen未见compound cohorts做明确的retrospective simulator是可行的，但只能宣称这些marker目标上的离线选择价值，不是减少真实湿实验已被证实。top-k未来收益定义须先锁定，不能从作者future LFmax已筛名单中挑正例，再声称发现新hit。

## 继承与 RSI 的边界不靠强行增加模块解决

三 screen 可允许诚实同screen开发、少量背景转移和窄的disjoint compound-cohort/common-start序列实验。共享 library/plate/measurement 使任务相关，应明确顺序与禁止未来feedback/策略选择；多个 episodes/重排/bootstraps不增加生物背景数。可以问“在这固定来源任务分布里，已冻结并继承的procedure是否帮助后来学习”，不能从中声称跨科研问题/实验室泛化。

继承收益须拆开权重、数据记忆/缓存、固定程序、改进策略本身。RSI 的进一步可证伪主张是：**更新后的改进策略，在相同后续初始模型/程序、相同后来feedback与compute下，比原始/冻结改进策略让下一次改进更有效**；还要与等预算普通 search、一次选定固定策略、普通重训/CL/AL区分。仅 later任务MAE下降、变多训练数据或选出更好超参，不是 improvement-of-improver。三screen本身不能提供这种结论；若需要多轮独立阶段才能作强主张而实际没有，应如实停在开发级诊断，不把三个screen硬拆成大量独立研究任务。

## 资格通过/停止条件

本阶段通过仅指：v1-bound确切 raw/library对象当前可得、大小/hash/版本可追溯；header/identity/time可与response和QC分开；raw marker及派生LF/QA定义、compound/well/plate/screen/replicate复用关系有显式map。字段名与时间合法不等于数值合法；合法性检验与处理规则必须在之后数值前预注册，不能开值后选对数/裁剪/换 endpoint。

manifest取不到、对象/hash不符、身份/response无法限域分开，则 bounded source qualification 停止在partial/failure，不写D信息或生物阴性。已处理/QC后版本仍可支持诚实限定开发；缺跨run生物重复只限制generalization，不禁止所有拟合。任何新 core 候选仍须按用户要求再次不同立场评审与真实实测，数据可用性不等于新颖性。

本阶段资源：0网络/0fit/0API/0workbook-response访问，复用一手原文与既存证据；所有新代码/记录均在规定 research/ 与 log/。历史 HTS001 STOP、HCT116 observation abort 均保持，不借 STACK 重命名为已复现。
