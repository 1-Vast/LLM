## 对另一方与 root 裁决的明确回应

### 一、我支持的判断

1. **root 对 3567 的裁决正确**：3567 不是“第二种估计器口径”，而是错误计数。另一方首轮把 4143 与 3567 说成“两种口径、不能互相替代”，这是错的；root 明确纠正为“old 3567 count is an error”，我同意。我首轮也指出 3567 内部自洽但口径未冻结，root 的裁决比我更彻底：不是“两种口径并存”，而是 3567 作废、4336 为唯一保守上限。这一点我接受并修正我首轮的措辞。

2. **root 对 weighted refit 的修正正确，且比我首轮更精确**：root 冻结了 `sum_i w_i||Y_i-predict_i||² + n_rows*alpha||A||²`，明确“w 作为 multiplicity、分母是行数而非权重和”。我首轮只要求“source 权重=1、Middle 权重=w、截距按 WLS 估计”，未冻结分母口径；root 的分母口径是必要的，否则 w 会同时改变有效样本量和正则强度，alpha 网格不可比。我支持。

3. **root 对 b_new 重算范围的冻结正确**：root 写“recompute b_new for ALL source and query rows, and recompute ALL h targets y-b_new and b-derived features”。这比我首轮的“重算 h 的 source 残差目标”更完整——我首轮只说 source 残差，root 明确 ALL（source + query）。我支持，并承认我首轮表述不够全。

4. **root 对 nuisance ownership 的冻结正确**：outer i、inner j 的 nuisance 同时排除 i 和 j；targets for j 只在该预测之后访问；final error rows 用 leave-one-source-out、final nuisance 用 all-source。这解决了我首轮“必须修正 3”的全部要点，且比我更严格（我首轮只写“排除 inner 目标 block”，root 写“同时排除 i,j”）。我支持。

5. **root 对 no-observed-RNA 的冻结正确**：genuine no-observedRNA family 移除所有 actualRNA-derived features。我首轮说“direct 与 no-observed-RNA 的差异正是 actual x_M/u_M/g(actual x_M)/v_M 的有无”，root 的“移除所有 actualRNA-derived features”与之一致且更可执行。我支持。

6. **root 对 SVD 的冻结正确**：float64 NumPy、固定版本 receipt、稳定排序奇异值、numerical-rank tolerance `max(shape)*eps*smax`、Q sign cancels in QQ'、rho0 保留两 block 归一化和零化 cross-block weights。我首轮要求“SVD 确定性设置与 factor 存储格式冻结”，root 给出了具体容差和 sign 处理，我支持；root 说“Q sign changes predictions”被拒绝，这是对的——Q 的符号在 QQ' 中抵消，预测不变，我首轮说“符号翻转会导致 A_r 符号翻转但预测不变”与 root 一致。

7. **root 拒绝“duplicating ridge inputs never changes predictions”正确**：我首轮说“冗余列在 ridge 中不改变预测（若 scaling 一致）”，这个说法过强。root 冻结“Ridge duplicate columns can change effective regularization; report the frozen feature set instead of claiming duplication invariance”，这是对的：重复列改变 X'X 的谱，从而改变有效正则化，预测会变。我修正我首轮的措辞：冗余列不构成泄漏，但**会**改变 ridge 解，不能声称预测不变。

8. **root 对四基因 baseline 的冻结正确**：mapping 已独立冻结，所以在 RNA conversion 前加入；8 配置为 shared b-alpha .1/1 × direct penalty .01/.1/1/10；预测 y_H-b_H，输入 [designM/H, y_M/SD, four mean-log difference gene values, b_M/b_H]，用 shared fold-local base b，无 actual all-probe x_M，加 b_H。这与我首轮“四基因 193 是新增 estimator fits 而非 pipeline evaluations”一致，且 root 明确了输入块。我支持。另一方首轮说“若四基因映射未冻结，4336 中的 193 是条件性预算”，root 已裁决 mapping 已冻结，所以 193 是确定预算，不是 conditional。另一方这一点被 root 覆盖。

9. **root 对门槛的冻结正确**：strictly >.02 absolute AND >=10% relative，对最强非同构普通 comparator，含所有原九族和新普通族；rho0 exact copy merged；mixture fixed 50/50 不调；route 和 noRNA 比较要求 strictly lower MAE；derangement descriptive only；no bootstrap confirmatory；development 已暴露；no single-N sample-efficiency claim。我首轮说“不改变原成功门槛 >0.02 绝对且 ≥10% 相对”，root 的“strictly”和“含新普通族”是更严格的冻结，我支持。

10. **root 对 API audit 的裁决正确**：前两次 direct reviews 是 thinking with 9000 completion tokens 返回 EMPTY、finish_reason=length 的失败产物，不是实质 review；第二次 no-thinking 的非空文本才是实质 review。我首轮文本是实质 review，不是失败产物；root 的 audit 与我无关，但我支持 root 不把失败产物当证据。

### 二、我反对的判断

1. **反对另一方首轮“4143 是含 pipeline 的 fit 计数，3567 是不含 pipeline 的 estimator-fit 计数，二者口径不同、不能互相替代”**。root 已裁决 3567 是 error，不是有效口径。另一方把错误计数包装成“第二种口径”，这在记账上是危险的：它允许在 manifest 中同时报两个数并让读者以为二者都合法。正确做法是：3567 作废，4336 是唯一保守上限，manifest 只报 4336 及其逐项展开，不报 3567 作为“替代口径”。我首轮说“3567 内部自洽但需补全口径”，这个措辞也不够；应改为“3567 是错误计数，4336 是唯一上限”。

2. **反对另一方首轮“derange null 仅描述性，不能当 p 值，也不能救失败主门槛——草案这点正确，保留但降级其证据地位”中的“降级”措辞**。root 冻结“derangement is descriptive only, cannot rescue primary failure or establish significance”。这不是“降级证据地位”，而是“它不是证据，只是诊断”。我首轮说“diagnostic-null 是配对反馈 bundle 关联诊断，不是 RNA 特异性置换检验，不提供 p 值，不能挽救失败主门”，与 root 一致；另一方的“降级”暗示它原本有证据地位，这是错的。

3. **反对另一方首轮“低秩 ridge 必要但仅作为容量控制，不是机制主张”中的“仅”**。root 冻结了低秩 ridge 的具体公式、rank cap、rho0 两 block 归一化、SVD 容差；这些是实现契约，不是“仅容量控制”可以概括的。低秩 ridge 的 rank cap 公平性（full joint 总秩 ≥ 受限方法）是比较公平性的必要条件，不是可选容量控制。我首轮说“r 独立按输出块 cap，且 full joint 不获更少总秩——这一点必须保留，否则比较不公平”，与 root 一致；另一方的“仅”弱化了这一点。

4. **反对另一方首轮“不需要额外 4 路以上 mask”的表述**。root 冻结的是“fixed route masks, fixed rules, mixtures, and rank projections have zero additional estimator fits”，即 route mask 零额外 fit，但不是“不需要额外 mask”。我首轮说“route 2×2 必要；no-observed-RNA 必要；derange null 仅描述性”，与 root 一致。另一方的“不需要额外 4 路以上 mask”容易被读成“mask 设计已足够、不需再审”，但 root 的冻结是“same fit/config maps for all 2x2 route masks; no retuning masks”，即 mask 必须用同一 fit、不得 retune。这是实现约束，不是“不需要”。

### 三、未决分歧

1. **ordinary-refit 的 597 中“21 final”的单位**。root 冻结“Weighted refit:8x24x3 +7development x3=597”，即 8 配置 × 24 outer × 3 estimator（b/f/h）= 576，加 7 development × 3 = 21，共 597。这解决了单位问题：3 是 b/f/h 三个 estimator，不是 b/f/g 三个 pipeline。我首轮说“若 21 指 7×3（b/f/g 分别 refit），则与‘refit b, f and g’一致，但需明确计数单位”，root 的冻结是 b/f/h（h 是 g 的加性成分），不是 b/f/g。这是一个措辞差异：root 用 h，我首轮用 g。**未决**：manifest 中应写“b/f/h 三个 estimator”，还是“b/f/g 三个 estimator”？我倾向 root 的 b/f/h，因为 g=b+h 是组合，refit 的是 h 不是 g；但草案原文写“refit b, f and g”，需在 manifest 中统一为“refit b, f, and h（g 由 b+h 重算）”。这是措辞未决，不是数值未决。

2. **四基因 193 的 8 配置中“shared b-alpha .1/1”与“direct penalty .01/.1/1/10”的组合**。root 冻结“Its eight configurations: shared b-alpha .1/1, direct penalty .01/.1/1/10”。这是 2×4=8，正确。但“shared b-alpha”是指 b 的 alpha 用 .1/1，还是指 shared base pack 的 alpha 用 .1/1？如果是后者，则 b/f/h 三个 estimator 都用同一 alpha，与 base pack 一致；如果是前者，则只有 b 用 .1/1，f/h 用什么？**未决**：manifest 需明确四基因 baseline 的 shared b-alpha 是否等于 base pack 的 shared alpha，以及 f/h 的 alpha 是否同源。我倾向“shared b-alpha = base pack 的 shared alpha，b/f/h 同 alpha”，但 root 的措辞只写“shared b-alpha”，需冻结。

3. **rho0 的“zeroed cross-block weights”与“two-block normalization”的具体实现**。root 冻结“rho0 retains two-block normalization and zeroed cross-block weights”。我首轮说“rho=0 时零列必须显式保留（或等价地固定两 block 的列索引），否则 rho=0 与 rho>0 的 B_state 不是同一参数化”。root 的“zeroed cross-block weights”是等价的，但“zeroed”是指 sqrt(0)*v_M=0 的列保留，还是指 cross-block 权重矩阵置零？**未决**：manifest 需明确 rho0 的 B_state 输入维度是否与 rho>0 相同（即是否保留零列）。我倾向“保留零列、固定列索引”，与 root 的“retains two-block normalization”一致，但需 manifest 逐行写死。

4. **weighted refit 的“original h transform”与“recomputed b_new for ALL rows”的交互**。root 冻结“Original source-fitted input block transforms retained (including original h transform), but weighted centering/intercepts recomputed”。这意味着 h 的输入 block scaling 用 source fit，但 h 的 centering/intercept 用 weighted 重算。我首轮说“block scaling 固定为 source fit，weighted refit 只更新系数”，root 的“weighted centering/intercepts recomputed”比我更细：不仅系数，centering/intercept 也重算。**未决**：h 的输入 block scaling 是 source fit 的 RMS，还是 weighted 重算的 RMS？root 说“transforms retained”但“centering/intercepts recomputed”，我理解为 scaling 保留、centering 重算；但“transform”通常含 scaling+centering，需 manifest 明确 scaling 是否也重算。我倾向 scaling 保留（否则构成用 query 信息调特征尺度），centering/intercept 重算。这是未决的实现细节，需 root 在 code freeze 前写死。

5. **“mixture is fixed 50/50 and not tuned”的 comparator 身份**。root 冻结 50/50 mixture 是 fixed、不调。但 mixture 的 50/50 是预测值平均还是 MAE 平均？如果是预测值平均，则 mixture 是一个新 predictor，需在 manifest 中计为 0 fit（因为它是两个已选配置的凸组合，无系数求解）；如果是 MAE 平均，则它不是 predictor，不能作为 comparator。**未决**：manifest 需明确 50/50 是 prediction-space average，且不计 fit。我倾向 prediction-space average，0 fit，与 root 的“mixtures have zero additional estimator fits”一致。

### 四、最小后续验证

以下是最小、可执行、不扩展研究范围的验证，按优先级：

1. **manifest 计数对账（冻结前，0 fit）**：生成 4336 的逐项公式，写死：shared-base 1806；correction 3×8×24×2+3×2=1152+6=1158；direct/KRR/noRNA 3×8×24+3=579；weighted refit 8×24×3+7×3=576+21=597；four-gene 8×24+1=193；null 2+1=3。合计 1806+1158+579+597+193+3=4336。同时写死“3567 作废，不作为替代口径”。验证方式：独立脚本从 manifest 重算，与 4336 逐项相等；不等则 stop。

2. **weighted refit 的两步等价性测试（冻结前，synthetic，0 real fit）**：构造 synthetic source+query，验证 (a) b_new 重算 ALL rows 后 h 目标 y-b_new 与 b-derived features 一致；(b) WLS 分母为 n_rows 而非 sum weights；(c) source 权重=1、query 权重=w；(d) h 的 scaling 用 source fit、centering/intercept 用 weighted 重算。验证方式：与显式逐行 WLS 的闭式解逐元素比较，容差写死。不等则 stop。

3. **nuisance ownership 的哨兵测试（冻结前，synthetic，0 real fit）**：对 outer i、inner j，注入 sentinel 到 i 和 j 的 High RNA/function，断言任何 nuisance fit 的输入哈希不含 sentinel；断言 j 的 target 只在 j 的 nuisance 预测生成后访问。验证方式：训练集哈希 + sentinel 断言。失败则 stop。

4. **rho0 两 block 参数化测试（冻结前，synthetic，0 real fit）**：验证 rho0 的 B_state 输入维度与 rho>0 相同（零列保留或固定列索引），且 rho0 的 collapsed affine predictor 与 sequential evaluation 逐元素 float64 相等（容差写死）。验证方式：exact-copy 测试。失败则 stop。

5. **SVD 确定性测试（冻结前，synthetic，0 real fit）**：固定 NumPy 版本 receipt，验证 sorted singular values、numerical-rank tolerance `max(shape)*eps*smax`、Q sign 在 QQ' 中抵消（即 A_r 预测对 Q 符号不变）。验证方式：两次不同 sign 约定的 SVD，预测逐元素相等。失败则 stop。

6. **四基因 baseline 的 alpha 同源测试（冻结前，synthetic，0 real fit）**：验证 shared b-alpha 与 base pack 的 shared alpha 同源，且 f/h 的 alpha 与 b 同源（或 manifest 写死的替代规则）。验证方式：配置序列化逐项比对。失败则 stop。

7. **MAS5 QC accessor 修复的科学合理性（技术，非统计）**：root 的修复是把 `se.exprs(calls)` 改为 `assayDataElement(calls,"se.exprs")`，核实 affy 源码后仅改 accessor，原代码/失败保留，未处理其余阵列，CDF 用原始 manufacturer data 环境 native affy lookup，所有数值方法不变。**我无科学合理性异议**：这是 accessor 名称错误，不是数值方法变更；MAS5 的 normalize=TRUE、sc=500、hgu133plus2cdf、log2(pmax(·,1)) 均未变；失败保留、未处理其余阵列，符合“technical failure 记录、不静默替换”的协议。唯一要求：manifest 记录 affy 版本、CDF 版本、accessor 修复的 diff、第一源 CEL 的输入/输出 SHA，以及“QC accessor 错误不构成 biological negative result”。这与我首轮“单芯片 MAS5 的 scale-500 是相对状态”的可记录局限一致，不改变可证伪性。

8. **50/50 mixture 的 prediction-space 定义（冻结前，0 fit）**：验证 mixture 是两个已选配置的 prediction-space 平均，0 fit，不作为独立 predictor 参与 selection。验证方式：manifest 写死 + 代码断言。失败则 stop。

以上 1–8 均为冻结前或 synthetic 验证，0 real fit，不扩展网格、不加数据、不改门槛。任一失败则 stop，记录为本 phase 的技术失败，不是 biological negative result。

### 五、对“最小技术修复”的直接回答

**无科学合理性异议。** 理由：accessor 名称错误（`se.exprs` vs `assayDataElement(...,"se.exprs")`）是 R/Bioconductor API 层面的修复，不改变 MAS5 的数值算法、不改变 CDF、不改变 normalize=TRUE/sc=500、不改变 log2(pmax(·,1))、不改变 54675 坐标。原代码/失败保留、未处理其余阵列、native affy lookup 用原始 manufacturer data 环境，符合“technical failure 记录、不静默替换、不自动 substitute”的协议。要求：manifest 记录 affy 版本、CDF 版本、修复 diff、第一源 CEL 输入/输出 SHA，并标注“QC accessor 错误是技术失败，不是 biological negative result”。这不构成对数值方法的变更，也不构成对冻结协议的偏离。