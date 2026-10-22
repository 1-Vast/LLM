下面按“必须修正（会改变计数/正确性或构成泄漏风险）”与“可记录的局限（不改变本轮可证伪性）”分开。仅依据两份草案推理，不引入新数据、不扩展研究范围。

## 一、计数审查：3567→4336 的修正是正确的，但需补全口径

原草案 3,567 的错误确认成立：

- 1,806 shared-base fits：301 个训练集 × 2 alpha × 3 个估计器（b、f、g）= 1,806。正确。
- 582 两输出块校正拟合：576 outer + 6 final。正确。
- 579 direct/KRR/no-observed-RNA：576 outer + 3 final。正确。
- 597 ordinary-refit：576 outer + 21 final（7 development drugs × 3？）。这里需核对：草案写“21 final across seven development drugs”，而 weighted refit 网格是 w∈{1,4,16,64}×alpha∈{0.1,1}=8 配置。若 final 是对 7 个 development drug 各拟合一次选定配置，则 7 次，不是 21 次；若 21 指 7×3（b/f/g 分别 refit），则与“refit b, f and g”一致，但草案前文又说“576 outer plus 21 final”，576 已按每配置每 outer 折计。**必须明确 ordinary-refit 的 fit 计数单位**：是一个 pipeline（b+f+g 合并计 1）还是三个估计器分别计 3。否则 597 不可复算。
- 3 个 diagnostic-null fits。正确。

修正后 1,806+582+579+597+3=3,567 本身是自洽的，但用户指出“576 个校正 pipeline 每个拟合两个 map，所以应 1152 而非 576”。这取决于“fit”定义：若一个校正 pipeline 同时拟合 state map 和 function map，且二者共享 SVD/ridge 分解，则按“估计器拟合”计 2；若按“pipeline 评估”计 1。草案第 582 行写“582 two-output-block correction fits（share ridge factorization across ranks；576 outer plus six final）”，即已按 2 map/pipeline 计为 576 outer？需要逐项核对：576 outer 若已是 2×288 pipeline，则与“576 个校正 pipeline”矛盾。**必须统一 fit 计数单位并在 manifest 中逐行展开**，否则 4,143 与 4,336 的差异无法审计。

用户给出的修正链：576 pipeline × 2 map = 1,152；原 3,567 中校正项 582 应改为 1,152+6=1,158？则总数变为 1,806+1,158+579+597+3=4,143。再加四基因 8 配置×24 折+1 final=193，得 4,336。**这个算术在“每 pipeline 两 map 分别计 fit”的口径下正确**，但必须同时说明：四基因 8 配置×24 折是 192 outer + 1 final=193，且这 193 是否与已有 576 outer 的折结构一致、是否共享 base pack 缓存，需在 manifest 中标注“新增估计器拟合”而非“新增 pipeline 评估”。

**必须修正 1**：把“estimator fit”定义为单一可复算单位（建议：一次系数求解，含多输出但共享分解的算 1 次求解、2 个输出块各记 1 个 fit），并在 manifest 中对 4,336 逐项给出公式：shared-base 1,806；correction 1,152+6；direct/KRR/no-RNA 576+3；ordinary-refit 576+21（或按实际单位重算）；四基因 192+1；diagnostic-null 3。若 ordinary-refit 的 21 实际是 7 而非 21，则总数应为 4,322，必须冻结前定死。

## 二、weighted update：必须修正的统计正确性问题

草案写：“Ordinary weighted refit: refit b, f and g on source plus the queried drug's observed Middle rows, with Middle observation weight w∈{1,4,16,64} and alpha∈{0.1,1}: 8. Retain the source-fitted input transformations and use true weighted least squares for coefficients/intercepts; update b with y_M, f with x_M, and g with the actual paired x_M/y_M. Recompute b-derived g features under the updated b.”

问题：

1. **g 的更新目标与 b 的更新不一致**。g(x,c,d)=b(c,d)+h(x,design,b)，h 拟合 y−b。若 b 被 y_M 更新，则 h 的训练目标 y−b 在 source 行上也应随新 b 重算，否则 h 仍在拟合旧 b 的残差，而 g 的加性结构被破坏。草案只说“Recompute b-derived g features under the updated b”，未说重算 h 的 source 残差目标。**必须修正**：weighted refit 中，若 b 更新，则 h 的 source 行目标 y−b_new 必须重算后再拟合 h；否则 g 不是 b_new+h 的合法加性模型，weighted refit 与 direct comparator 不可比。
2. **加权 WLS 的权重作用域**。Middle 观测权重 w 只应作用于新增的 queried drug Middle 行；source 行权重应为 1（或明确 source 行也乘 w，但那会改变 source 有效样本量并影响所有 alpha 比较）。草案未写明。**必须修正**：明确 source 行权重=1，Middle 行权重=w；截距不加权惩罚但参与加权最小二乘；若使用“unpenalized intercept”，加权截距需在 WLS 中按权重估计，不能先中心化再忽略权重。
3. **f 的更新用 x_M 但 f 的输入是 design**。f(c,d) 预测 RNA x from design，Middle 行有 design 和 x_M，可加入；但 source M/H 行与 Middle 行的 design 块缩放必须沿用 source-fitted transform（草案已说 retain source-fitted input transformations），这点正确。需确保 weighted refit 不重新估计 block scaling，否则构成用 queried drug 信息调特征尺度，虽非 High 泄漏，但会改变 comparator 的“ordinary”性质。**可记录但建议冻结**：block scaling 固定为 source fit，weighted refit 只更新系数。
4. **g 的更新用 actual paired x_M/y_M**，但 g 的输入含 b(c,d)。若 b 更新，g 的输入 b 值在 Middle 行也应使用 b_new，而非 source b。草案说“Recompute b-derived g features under the updated b”，方向正确，但需明确 Middle 行的 g 特征也用 b_new，且 h 的 Middle 行目标 y_M−b_new 参与加权拟合。**必须修正**：给出 weighted refit 的精确两步——先 WLS 更新 b（source+Middle，权重 1/w），再以 b_new 重算所有行 b 特征和 h 目标，WLS 更新 f（source M/H+Middle，权重 1/w），再 WLS 更新 h（source M/H+Middle，权重 1/w，目标 y−b_new）。否则 597 计数下的“refit b, f and g”不是同一个可复算模型。

## 三、两阶段嵌套 crossfit：泄漏风险与必须修正

草案：“For every fixed configuration, leave one source proxy block out. Within the remaining 23 source singleton blocks, leave each complete block out again to generate training error/direct-feature rows. Then fit B/direct on those rows, fit the shared base on all 23, and forecast the outer compound from its Middle history. No outer High RNA/function enters any fitting, scaling, residual, bandwidth, or feature stage.”

统计上这是正确的 nested crossfit 骨架：outer 留一 block，inner 在 23 内留一生成 OOF 误差行，B/direct 在 inner-OOF 行上拟合，base 在全部 23 上拟合。泄漏风险点：

1. **inner-OOF 行的目标 u_H/v_H 使用 inner High RNA/function**。草案说“The inner High RNA/function supplies inner-row targets after nuisance predictions are generated, never the corresponding nuisance fit.”这是正确的：nuisance（f/g）对 inner 折的预测必须来自不含该 inner block 的 fit，然后才用该 block 的 High 目标构造 u/v。**必须确认**：inner 折的 f/g 预测不得来自包含该 inner block 的 base pack；否则 u/v 含目标折信息，B 的训练目标泄漏。草案的“leave each complete block out again”应明确为：对 inner block j，用 23−{j} 拟合 f/g 得预测，再用 j 的 High 构造 u_H/v_H。若实现为“用全部 23 拟合 f/g 再算 23 个 inner 残差”，则泄漏。**必须修正措辞**：inner nuisance fit 的训练集严格排除 inner 目标 block。
2. **block scaling 与 rho 归一化**。草案说“Normalize u_M and v_M as separate input blocks using only these training errors.”正确，但需明确：inner-OOF 误差行的 scaling 不得使用 outer block 的任何信息；outer 预测时 u_M/v_M 用同一 training-error scaling。**可记录**：outer block 的 u_M/v_M 值在预测时可能超出 training scaling 范围，这是正常外推，不是泄漏。
3. **direct 模型的 inner-OOF 辅助特征**。草案说 direct 从 inner-OOF auxiliary features 构建，“so their training features have the same deployment-like nuisance predictions as correction models.”正确。但需确认：direct 的 f_M/f_H/u_M/v_M 等特征在 inner 行上也来自排除该 inner block 的 nuisance fit；outer 预测时这些特征来自排除 outer block 的 fit（即 23 个 block 的 base）。**必须修正**：明确 direct 的 inner 特征与 B 的 inner 误差行使用同一套 inner-OOF nuisance 预测，不得为 direct 单独重拟合 nuisance 或使用不同折结构，否则 576 outer 计数与可比性失效。
4. **final 训练**：“Final training uses all source and source leave-one-block-out nuisance rows.”正确，但 final 的 B/direct 训练行是 24 个 leave-one-block-out 行（每个 block 的 nuisance 预测来自排除该 block 的 fit），目标用该 block 的 High。这 24 行与 outer 的 23 行结构不同，需在 manifest 中标注 final fit 的训练集是 24 行，不是 23 行。**可记录**：final 的 B 拟合使用 24 个 OOF 行，outer 评估的 B 使用 23 个 inner-OOF 行，二者样本量不同，属预期。
5. **development 的 Middle 历史**：“forecast the outer compound from its Middle history”与“forecast authentic development histories”。development 只有 Middle+controls，无 High。需确认 development 的 Middle 状态 x_M 用同一单芯片 MAS5 变换，且不参与任何 source 训练。**可记录**：development Middle 的预处理是 array-local，可缓存，不构成跨数组泄漏；但 development 的 y_M 在 no-observed-RNA 与 direct 中的使用必须与 source 训练行一致，不得在 scoring 前用 development High 调参。

## 四、低秩 ridge 公式：数学正确性审查

草案公式：对 centered/scaled X、centered Y，SVD X=U diag(s) V'，Z=diag(s/√(s²+nλ)) U'Y，保留 Z 的前 r 个右奇异向量 Q，A_r=V diag(s/(s²+nλ)) U'Y Q Q'。

审查：

- 标准 ridge 解为 A_ridge=V diag(s/(s²+nλ)) U'Y。这是正确的（对 min (1/n)||Y−XA||²+λ||A||²，正规方程 (X'X+nλI)A=X'Y，SVD 代入得此式）。
- 秩约束在 ridge 度量下的解：若要求 A 的列空间限制在 X'X+nλI 度量的前 r 个方向，则 A_r=V diag(s/(s²+nλ)) U'Y Q Q'，其中 Q 是 Z 的前 r 个右奇异向量。这等价于对 Z 做截断 SVD 再映射回系数空间。**数学上正确**，前提是 Q 来自 Z 的 SVD 且 Z 的定义与 A_ridge 的因子一致。
- 但需注意：Z=diag(s/√(s²+nλ))U'Y 的右奇异向量 Q 是 Y 在 ridge 白化后的主方向；A_r 的秩不超过 r，且是 ridge 目标下秩 r 的最优解（Eckart–Young 在加权范数下的变体）。**可记录**：该解不是普通最小二乘秩约束解，而是 ridge 度量下的秩约束解；草案已声明“solves ridge under a rank constraint in the ridge metric”，正确。
- **必须修正的边界**：r 的 cap 写“independently capped at min(r, target dimension, available numerical rank) for each output block. Thus full joint does not receive less total rank than the restricted method.”这里“full joint does not receive less total rank”需要精确化：若 state map 和 function map 各自 cap 到 r，则 full joint（rho=1）两个 map 各 r，restricted（rho=0）state map 用 [u_M] 可能数值秩为 1，function map 用 [v_M] 可能秩为 1；full joint 用 [u_M,v_M] 数值秩可达 2。因此 full joint 的总秩不小于 restricted，正确。但若 r=1，full joint 两个 map 各 1，restricted 也各 1，总秩相同；草案说“does not receive less”是弱保证，正确。**可记录**：r=1 时 full joint 与 restricted 总秩相同，比较的是方向而非秩预算。
- **必须修正**：Z 的 SVD 应在数值上稳定计算；当 s²+nλ 极小或 s=0 时，diag(s/√(s²+nλ)) 对 s=0 为 0，安全；但若 nλ 极小且 s 非零，比值趋近 1，无发散。**可记录**：float64 下 SVD 截断需固定符号/排序规则，否则 Q 的符号翻转会导致 A_r 符号翻转但预测不变；manifest 应记录 SVD 求解器的确定性设置。
- **必须修正**：A_r 的存储为 factors，但预测 x*=f_H+B_state(u_M,v_M) 时 B_state 的输入块 scaling 必须与训练时一致；草案说“Center/scale the two blocks before applying sqrt(rho); keep the same two-block normalization at every rho, including zero.”正确，但 rho=0 时 sqrt(0)*v_M=0，若实现为删除该列，则 B_state 的输入维度随 rho 变化，SVD 的 V 维度也变化；草案说“keep the same two-block normalization at every rho”，意味着 rho=0 仍保留零列或保留两 block 结构。**必须修正措辞**：rho=0 时零列必须显式保留（或等价地固定两 block 的列索引），否则 rho=0 与 rho>0 的 B_state 不是同一参数化，route ablation 的“same fitted base and B maps”不成立。

## 五、direct comparator 是否遗漏信息

草案 direct 输入块：design for M/H、actual x_M、actual y_M+SDs、f_M、f_H、u_M、v_M、b_M/b_H、g(x_M,M)、g(f_H,H)。预测 y_H−g(f_H,H) 再加回。

审查遗漏：

1. **g(x_M,M) 与 g(f_H,H) 都在，但 g(f_M,M) 只在 no-observed-RNA 中出现**。direct 有 actual x_M，所以 g(x_M,M) 覆盖了 Middle 状态经 g 的预测；g(f_M,M) 是“用预测 RNA 代替实际 RNA”的对照，direct 不需要，因为 direct 有 actual x_M。**可记录**：direct 与 no-observed-RNA 的差异正是 actual x_M/u_M/g(actual x_M)/v_M 的有无，这是设计意图，不是遗漏。
2. **b_M/b_H 与 g(x_M,M)/g(f_H,H) 有函数依赖**：g=b+h，b_M 是 g 的加性成分，g(x_M,M)=b_M+h(x_M,...)。同时放入 b_M 和 g(x_M,M) 不构成泄漏，但是确定性冗余；草案说“Deterministic duplicate columns are permitted”，正确。**可记录**：冗余列在 ridge 中不改变预测（若 scaling 一致），但会改变系数和数值条件；建议 manifest 记录条件数，不要求删除。
3. **actual y_M+SDs 与 v_M=y_M−g(x_M,M) 同时放入**：v_M 是 y_M 与 g 的差，g 又由 b+h 决定，存在线性依赖；同样不构成泄漏，但 ridge 的 alpha 网格可能因共线性使不同 alpha 预测接近。**可记录**：direct 的 8 配置网格在共线下可能退化，选择仍按 OOF MAE，不额外调参。
4. **是否遗漏 Middle 的 replicate SD 在 v_M 上的传播**？草案 direct 有 y_M/SDs，v_M 只用了 y_M 点值；若 Middle 功能有两个 replicate，其 SD 已作为独立块，但 v_M 的构造未用 SD 加权。**可记录**：这是 direct 的普通特征选择，不是必须修正；若要用 SD 加权 v_M，需在冻结前声明，否则构成事后选择。
5. **是否遗漏 source High RNA 的直接监督**？direct 通过 f/g 获得 source High RNA 监督，且预测残差 y_H−g(f_H,H) 的目标含 High 功能；source High RNA 本身不作为 direct 输入（因为部署时无 High RNA）。**正确**，不遗漏。
6. **direct 的 f_H 与 g(f_H,H) 同时放入**：f_H 是预测 RNA，g(f_H,H) 是预测功能；二者有函数依赖但信息不同（RNA 坐标 vs 功能预测）。**可记录**：这是有意的 composed-world prior，不是泄漏。
7. **no-observed-RNA 的输入含 f_M/f_H 和 g(f_M,M)/g(f_H,H)**，但 f_M/f_H 来自 design 的 RNA 预测，不含 actual x_M；正确。需确认 no-observed-RNA 的 f_M/f_H 与 direct 的 f_M/f_H 来自同一 nuisance fit（排除 outer block），否则比较不公平。**必须修正**：明确所有 direct 家族（含 no-observed-RNA）的 f/g 特征来自同一套 inner-OOF/outer nuisance 预测，不得为某家族单独重拟合。

## 六、必须修正 vs 可记录局限

**必须修正（冻结前）**：

1. 统一 fit 计数单位，逐项展开 4,336（或按 ordinary-refit 实际单位重算后的数），并在 manifest 中给出公式；确认四基因 193 是新增 estimator fits 而非 pipeline evaluations。
2. weighted refit 的精确两步：b 更新后重算 h 的 source 残差目标；source 行权重=1、Middle 行权重=w；b_new 用于所有 g 特征；block scaling 固定为 source fit。
3. inner-OOF nuisance fit 严格排除 inner 目标 block；direct 与 B 共享同一套 inner-OOF nuisance 预测；outer 预测的 nuisance 来自 23-block fit。
4. rho=0 时显式保留两 block 零列/固定列索引，确保 route ablation 的“same fitted B maps”成立。
5. direct 家族（含 no-observed-RNA）的 f/g 特征来自同一 nuisance 预测，不得单独重拟合。
6. 低秩 ridge 的 SVD 确定性设置（符号/排序）与 A_r 的 factor 存储格式在 manifest 中冻结。

**可记录局限（不改变本轮可证伪性）**：

1. 7 个 development proxy 的 group bootstrap 仅描述性，不识别 donor 泛化；selection-exposed OOF 分数不声称无偏。
2. 单芯片 MAS5 的 scale-500 是相对状态，非绝对 RNA/cell；细胞毒性全局位移不可消除。
3. 四基因 comparator 若映射未独立冻结则不加入；其缺失不构成扩展理由。
4. direct 输入的确定性冗余/共线性可能使 alpha 网格退化，选择仍按 OOF MAE，不额外调参。
5. diagnostic-null 是配对反馈 bundle 关联诊断，不是 RNA 特异性置换检验，不提供 p 值，不能挽救失败主门。
6. development 功能暴露已存在，seal 只防运行时目标使用，不恢复盲法。
7. final B 用 24 个 OOF 行、outer B 用 23 个 inner-OOF 行，样本量差异属预期。
8. r=1 时 full joint 与 restricted 总秩相同，比较的是方向而非秩预算。

**不提出的内容**：不要求第三层嵌套、不要求保留集、不要求新增数据、不要求扩展研究范围；上述修正均为计数/实现口径与泄漏边界的冻结，不改变原成功门槛 >0.02 绝对且 ≥10% 相对。