# 对 Root 冻结裁决与新技术证据的独立回应

**先直接回答技术修复的科学合理性异议问题：无异议，且该修复在方法上比原路径更保守。**

理由限定在给定材料内：

1. 错误发生在 QC accessor 层（`se.exprs(calls)` → `assayDataElement(calls,"se.exprs")`），不触及 MAS5 数值、CDF 定义、坐标排序或 log2 floor。它属于读取层修复，不构成"看到数据后改方法"。
2. 失败代码/失败产物保留、未处理其余阵列、未用修复后的输出做任何选择——这满足"技术失败入账、不静默替换"的冻结要求。
3. 用原始 manufacturer data environment 走 native affy lookup，替代失败的 namespace lazy-load，是同一 CDF 定义的实现路径切换，不是 CDF 变更。只要 manifest 记录两次路径的 CDF 哈希一致，就不构成坐标漂移。
4. 唯一需要补的记账：这次 MAS5 计算是否计入"transform fits / preprocessing"计数器（Root 第2条已把 preprocessing 与 estimator fit 分离）。建议在 manifest 中把它标为 **preprocessing technical retry**，不计 estimator fit，但计入失败/重试账本。这不改变 4336 上限。

**残余风险（须记录，不构成反对）**：第一源阵列的 MAS5 已算出但未落盘，重跑时若 R/Bioconductor/affy 版本 receipt 与首次不完全一致，需比对输出 SHA；若不一致，属版本漂移而非方法变更，应作为技术事件记录，不得据此改预处理。

---

## 一、对另一方（首轮评审）判断的逐项处置

**支持（我接受为我方立场的一部分）：**

- **weighted refit 必须两步**：b 先更新，再以 b_new 重算所有 source 与 query 行的 h 目标 y−b_new 和 b 派生特征，然后更新 f、h。这一条我首轮只写了"recompute b-derived g features"，未把 h 的 source 残差目标随 b_new 重算写死，是实质缺口。Root 第3条已把它冻结为"recompute ALL h targets y−b_new and b-derived features"，我接受。
- **WLS 权重作用域与正则约定**：source 行权重=1、恰好一条 compound-mean Middle 行权重 w、目标函数 `sum w_i||·||² + n_rows*alpha||A||²`（w 作 multiplicity，分母用行数而非权重和）。这一条比我首轮"true weighted least squares"更精确，接受。
- **inner-OOF nuisance 严格排除 inner 目标 block，且 direct 与 B 共享同一套 inner-OOF nuisance 预测**：我首轮已提"inner nuisance fit 训练集严格排除 inner 目标 block"，但未把"direct 家族不得单独重拟合 nuisance"写成硬约束。Root 第4条"one shared nuisance bank for corrections and all direct families"冻结了它，接受。
- **rho=0 显式保留两 block 零列/固定列索引**：我首轮已提，Root 第5条"rho0 retains two-block normalization and zeroed cross-block weights"确认，接受。
- **low-rank ridge 公式的数学正确性**：对方对我方 A_r 公式的审查结论（ridge 度量下秩约束解，Eckart–Young 加权变体，s=0 安全）与我方一致，无分歧。
- **direct 确定性冗余/共线性不构成泄漏、但会使 alpha 网格退化**：接受为可记录局限；Root 第5条进一步裁决"report the frozen feature set instead of claiming duplication invariance"，即不得声称重复列对预测无影响，接受。
- **fit 计数单位必须统一并逐项展开**：接受。Root 第2条已给出权威口径（一次系数求解=1 fit；两 correction map=2；b/f/h pack=3；4336 为保守上限；3567 是错误而非合法第二口径）。

**反对（我不接受对方或需明确不采纳的）：**

- **"3567 可作为另一 estimator accounting convention"**：反对。我首轮已判 3567 与 4143 是口径混用而非两个合法口径；Root 第8条明确"rejects reviewers' suggestions that the erroneous 3567 count is valid under a second estimator convention"。我与此一致，不接受把 3567 保留为可选记账。
- **"duplicating ridge inputs never changes predictions"**：反对。我首轮说"冗余列在 ridge 中不改变预测（若 scaling 一致）"——这句话过强，须撤回。重复列会改变有效正则化与数值条件，预测可变化。Root 第8条明确拒绝该说法。更正为：重复列不构成泄漏，但会改变有效惩罚；manifest 报告冻结特征集，不声称重复不变性。
- **"Q 符号翻转会改变预测"**：反对（即反对此说法）。Q 符号在 QQ' 中抵消，预测不变；但须固定 SVD 求解器版本/排序/数值秩容差，使可复现性不依赖符号约定。Root 第5、8条与此一致。
- **对方"ordinary-refit 21 final 可能是 7 而非 21，则总数应为 4322"的备选**：不接受为并列选项。Root 第2条已冻结 weighted refit = 8×24×3 + 7 development×3 = 597，即 21 final 按"7 development drugs × 3 estimators"计。对方提出的 4322 是错误口径下的算术，不是待决分歧。
- **对方"inner-OOF 行目标 u_H/v_H 使用 inner High"的措辞**：接受其内容（nuisance 预测排除 inner block，目标在预测后接入），但反对把"leave each complete block out again"留作可解释措辞——Root 第4条已冻结为"inner j nuisance excludes BOTH i,j"，即双重排除，比对方措辞更严。我接受 Root 版本，不接受较松的"排除 inner 目标 block"单独表述。

**未决分歧（真实存在、需在代码冻结前定死）：**

1. **四基因 baseline 的加入时点**：我方首轮与对方均按"映射未独立冻结则不加入、193 为条件性预算"处理；Root 第1条裁决"mapping is already independently frozen, so add the ordinary four-gene baseline now, before RNA conversion"，并把 8 配置定义为 shared b-alpha .1/1 × direct penalty .01/.1/1/10，输入为 [designM/H, y_M/SD, four mean-log difference gene values, b_M/b_H]，**不含 actual all-probe x_M**，加 b_H。这改变了四基因族的输入定义（不是我方首轮设想的"四基因签名映射后平均探针"作为独立 comparator 的简单版）。**未决点**：该族是否与 direct ridge 共享同一 inner-OOF nuisance bank 与同一 fold 结构？Root 第4条说"all direct families"共享 nuisance bank，四基因族是否属"direct family"需在 manifest 显式归类，否则 193 的折结构与 576 outer 的可比性无法审计。这是记账/可比性未决，不是科学分歧。
2. **development 7 的 weighted refit final（21 fit）是否使用 development Middle 行**：Root 第3条说"exactly one added compound-mean Middle row weight w"，第2条把 7 development×3 计入 597。这意味着 weighted refit 的 final 会以 development 的 Middle 行做一次普通重拟合（无 High）。**未决点**：这次重拟合发生在 seal 之前还是之后？若在 seal 前，它接触 development Middle（允许）但不接触 development High（必须断言）；若在 seal 后，则它属于 scoring 流程的一部分，须与 prediction 文件一同封存。建议 manifest 明确：development Middle 行进入 weighted refit final 是**部署时可得信息**，不构成目标泄漏，但须与 development High 的读取进程隔离。
3. **derangement null 的"2 maps + 1 direct = 3 fit"是否复用已选 rho=0 与 direct 的 base pack**：Root 第2条计 3 fit，第6条说 derangement 仅描述性。**未决点**：这 3 fit 是否使用与主分析相同的 base pack 缓存（即不额外拟合 b/f/g），还是独立重拟合 base？若复用缓存，则"3 fit"只是 B/direct 的 refit；若独立，则计数应含 base。须在 manifest 写死，否则 4336 的"conservative ceiling"含义漂移。

---

## 二、对 Root 冻结裁决的明确支持/反对

**支持（全部接受为约束）：**

- 第1条：预处理走 PREPROCESS_PROTOCOL.md、原始 manufacturer CDF、native affy lookup、54675 固定坐标、四基因映射已冻结故现在加入、8 配置定义、加 b_H、同八配置 source selection。
- 第2条：fit 定义（一次系数求解=1；两 map=2；b/f/h pack=3）、4336 保守上限、3567 是错误、pipeline/transform/SVD/retry/cache 分离计数、若代码因式分解导致实际 solve 更少则披露复用而非假装花掉预算。
- 第3条：weighted refit 精确两步、source 权重=1、恰一条 compound-mean Middle 行权重 w、正则分母用行数、b 先更新再重算所有 h 目标与 b 派生特征、f 用 source M/H + query Middle、h 用实际状态与重算残差、每次更新=1 fit、refit 预测用更新后 g(updated f_H,H)、无 query High。
- 第4条：one shared nuisance bank、inner j 排除 i 与 j、j 的目标在预测后接入、outer i High 不进任何 train feature/transform、final error rows 用 leave-one-source-out、final nuisance 用 all-source、固定探针坐标、2×2 route mask 共享同一 fit/config 不重调、v-only 仍用 observedRNA、genuine no-observedRNA 移除所有 actualRNA 派生特征。
- 第5条：float64 NumPy SVD、固定软件/版本 receipt、排序奇异值、数值秩容差 max(shape)*eps*smax、Q 符号在 QQ' 抵消故无符号依赖主张、rho0 保留两 block 归一化与零化跨 block 权重、存 low-rank factors、centered RBF 用 trained intercept、所有 block scale 为 training-only energy RMS、重复列可改变有效正则故报告冻结特征集而非声称重复不变。
- 第6条：>0.02 绝对且 ≥10% 相对、对最强非同构普通 comparator、九族与新普通族全报、rho0 exact copy 合并、mixture 固定 50/50 不调、route 与 noRNA 比较须严格更低才支持各自增量、derangement 仅描述性不能救主门槛、无 confirmatory bootstrap、development 已历史暴露、无单 N 样本效率主张。
- 第7条：建模前通过 primal/dual、weighted WLS、full-rank reduced-ridge identity、collapsed-sequential identity、train-only scaling、fold-owner/heldoutHigh-sentinel 测试；seal 数值代码/数据/输出/预测文件后再由隔离 scoring 读 developmentHigh function；不恢复历史盲法；数值执行需单独 code freeze。
- 第8条：API 审计事实（前两次 direct review 为 9000 completion tokens、EMPTY content、finish_reason=length 的失败产物，非实质评审）；reject 3567 合法第二口径、reject 重复列不变性、reject Q 符号改变预测；accept source-residual recomputation、literal WLS weights、strict nuisance ownership、separate measurement ablation；对立回复与精确成本与经验证据分离。

**反对/须更正（Root 裁决中我认为需收紧或纠正的）：**

- **无实质反对。** 我首轮有一处过强表述（"冗余列在 ridge 中不改变预测"）已被 Root 第8条与第5条纠正，我撤回该表述，接受"报告冻结特征集、不声称重复不变性"。
- 唯一要求补充的**不是反对而是记账闭合**：Root 第2条把 4336 拆为 1806+1158+579+597+193+3。逐项核算：1806+1158=2964；+579=3543；+597=4140；+193=4333；+3=4336。算术自洽。但第1条新增四基因族的输入定义（含 b_H、不含 actual x_M）与第4条"all direct families"共享 nuisance bank 的归类，须在 manifest 显式写明，否则 193 的折结构与 576 outer 的可比性无法审计。这是**记账闭合要求**，非反对。

---

## 三、最小后续验证（冻结前必须完成、不扩网格、不加数据）

按 Root 第7条与第8条，最小验证集为：

1. **primal/dual 一致性**：同一 ridge 问题，primal 正规方程解与 dual K+nλI 解在 float64 下逐元素一致（容差写明，建议 ≤1e-10 相对）。
2. **weighted WLS 一致性**：对固定 w 向量，`sum w_i||Y_i−X_iA||² + n_rows*alpha||A||²` 的解析解与代码解一致；验证 w 作 multiplicity、分母为行数。
3. **full-rank reduced-ridge identity**：r ≥ 数值秩时 A_r 等于 A_ridge（逐元素，容差写明）。
4. **collapsed-sequential identity**：rho=0 的 B 顺序求值（x*=f_H+B_state(u_M,v_M)，y*=g(x*,H)+B_function(u_M,v_M)）与合并仿射预测器逐元素一致。
5. **train-only scaling**：断言所有 block scale/center 仅由当前 fit 训练行计算；outer block 不进入任何 scale。
6. **fold-owner/heldoutHigh-sentinel**：用哨兵值/哈希断言 outer i High 不出现在任何 nuisance 拟合、缩放、残差、带宽、特征构造；inner j 目标在预测后才接入。
7. **rho=0 零列保留**：断言 rho=0 与 rho>0 的 B_state 参数化维度相同、列索引固定，route ablation 使用同一 fitted B maps。
8. **四基因族归类**：manifest 写明四基因族是否属"direct family"共享 nuisance bank，以及 193 的折结构与 576 outer 的对应关系。
9. **derangement null 的 base 复用**：manifest 写明 3 fit 是否复用已选 base pack 缓存；若复用，计数含义为 B/direct refit；若不复用，4336 须相应调整或明确"conservative ceiling"含冗余。
10. **第一源阵列技术重跑的 receipt 比对**：比对首次与重跑的 R/Bioconductor/affy/CDF 版本 receipt 与输出 SHA；不一致则记为版本漂移技术事件，不改预处理。

以上 10 项均为**冻结前 code freeze 的通过条件**，不产生新 estimator fit，不扩网格，不加数据，不改门槛。

---

## 四、即便全部通过，本轮支持/不支持（与首轮一致，不扩）

- **支持**：在该 N=24、单 Middle bundle、固定反馈预算下，observed Middle state/function 相对最强非同构普通基线有可测预测增益（若 no-observed-RNA 与 route ablation 均严格支持）。
- **不支持**：独特算法核心、结构优势、跨任务继承、主动查询智能体、样本效率曲线、joint world+agent 增益、C4、RSI；derangement null 不提供 p 值；development 已暴露，seal 不恢复盲法；source 上调 rank/shrinkage 是普通调参。

**结论**：对第一源 CEL 的 MAS5 QC accessor 最小修复，无科学合理性异议，前提是 manifest 记为 preprocessing technical retry、比对版本/输出 SHA、不据此改预处理。对另一方与 Root 的判断：支持其 weighted refit 两步、WLS 权重/正则约定、strict nuisance ownership、rho0 零列保留、fit 计数统一与 4336 权威性、Q 符号抵消、重复列不声称不变；反对 3567 作为合法第二口径、反对重复列不变性、反对 Q 符号改变预测；未决分歧仅为四基因族归类、development Middle 进入 weighted refit final 的 seal 时点、derangement null 的 base 复用三项记账闭合，须在 code freeze 前写死。