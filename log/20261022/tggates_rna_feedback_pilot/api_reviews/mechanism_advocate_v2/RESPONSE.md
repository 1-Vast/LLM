# 独立方法审查：把候选主张压到可被一次冻结 pilot 推翻

## 1. 最强合理技术主张（压缩后）

**可冻结、可推翻的主张：**

> 在固定 MAS5 单芯片、54675 探针坐标、固定四基因签名映射、固定 24 source / 7 development、later 14 不开的前提下，对已冻结的 rho=0 约束联合修正（state map + function map），其 development 7 的 DNA MAE 相对**最强非同构普通基线**（含 direct ridge、RBF KRR、no-observed-RNA ridge、weighted refit、原九族 comparator、50/50 mixture）至少绝对降低 0.02 且相对降低 ≥10%；且该增益在 route ablation（state-off / function-off）与 no-observed-RNA ablation 下不出现同等或更大增益；且该增益不能被"把 observed-Middle 特征 bundle 整体 derange"的诊断 null 复现。

一次冻结 pilot 的推翻条件：上述四条中任一条不成立，即主张被推翻，停止该配置扩展，不得改端点、删化合物、加数据、放宽阈值。

## 2. 是不是普通线性联合预测/正则化？

**是。** 逐条对照：

- 基座 b/f/g 是带非惩罚截距的多输出线性 ridge；g 对 x 是仿射（h 线性 + b 不依赖 x）。
- 修正 B_state / B_function 是**在 ridge 度量下的秩约束线性映射**（SVD 截断 + ridge 因子），rho 只改输入块加权，不改线性性。
- rho=0 的"受限联合"与"顺序求值"是同一仿射预测器的两种描述（草案自己要求 synthetic exact-copy 验证）。因此它不是新算法核心，只是**带结构先验的普通正则化联合线性模型**。
- 唯一非平凡处是"用 inner-OOF 残差 u/v 作为修正输入"和"route ablation"——这是**特征工程 + 消融设计**，不是新学习范式。
- direct ridge / KRR / weighted refit / no-observed-RNA 全是普通基线族。

结论：该候选**不是**独特算法、不是智能体、不是 RSI；即使全部门槛通过，也只支持"在该小样本、该反馈预算下，observed Middle state/function 对 High 功能预测有可测的预测增益"，**不支持**结构独特性、跨任务继承、主动查询智能体或 C4/RSI。

## 3. 低秩 ridge、样本外残差、强基线、4 路 mask 的必要性

- **低秩 ridge（r∈{1,2}, λ∈{0.1,1}）**：必要但仅作为**容量控制**，防止 54675 维 x 在 n=24 下过拟合；不是机制主张。r 独立按输出块 cap，且 full joint 不获更少总秩——这一点必须保留，否则比较不公平。
- **样本外残差（inner-OOF u/v）**：必要，否则修正输入含目标泄漏；但必须确认 inner-OOF 的 nuisance 拟合**不含 outer High RNA/function**（草案已写，需测试验证）。
- **强普通基线**：必要，否则"增益"可能只是"用了 observed Middle RNA"这一测量信息。no-observed-RNA ridge 是**关键对照**，必须与候选共享除 observed-RNA 外的一切信息。
- **4 路 mask（route ablation 2×2 + no-observed-RNA + derange null）**：route 2×2 必要（区分 state 与 function 贡献）；no-observed-RNA 必要（测量信息 vs 结构）；derange null **仅描述性**，不能当 p 值，也不能救失败主门槛——草案这点正确，保留但降级其证据地位。**不需要**额外 4 路以上 mask。

## 4. 最小实现方案

1. 预处理：按 PREPROCESS 文档，affy::mas5 单芯片、sc=500、hgu133plus2cdf、log2(pmax(·,1))、54675 坐标固定排序；四基因映射独立冻结后平均探针，不选最优探针。
2. 状态向量：处理组两重复均值 − 同实验 2h 匹配对照两重复均值；共享对照身份与成本保留。
3. 基座：b/f/g 三 ridge，α∈{0.1,1}，dual 形式 K+nλI，float64，不裁剪。
4. inner-OOF：source 24 留一 block，再在 23 内留一 block 生成 u/v 与 direct 特征；outer High 只进 evaluator。
5. 修正：rho∈{0,0.5,1}，r∈{1,2}，λ∈{0.1,1}，两 α → 每 rho 族 8 配置；route mask 零额外 fit。
6. 基线族：direct ridge 8、RBF KRR 8、no-observed-RNA 8、weighted refit 8、原九族 comparator 不重跑、50/50 mixture 零搜索。
7. 选择：每族按 source OOF DNA MAE 选一配置，字典序破平；development 不参与任何选择。
8. 评分：development 7 DNA MAE 主分，LDH、逐化合物、route 对比、no-observed-RNA、source High-state 误差、全基线并报；group bootstrap 仅描述。
9. 门槛：原 >0.02 绝对且 ≥10% 相对，对最强非同构普通基线，不可改。

## 5. 必须执行的等价性与防泄漏测试

- **exact-copy 等价性**：rho=0 的 B 顺序求值 vs 合并仿射预测器，逐元素 float64 相等（容差写明）。
- **防泄漏 1**：outer block 的 High RNA/function 不出现在任何 nuisance 拟合、缩放、残差、带宽、特征构造中；用哨兵值/哈希断言。
- **防泄漏 2**：inner-OOF 行生成时，对应 nuisance 拟合不得见该行 High 目标；用逐行训练集哈希断言。
- **防泄漏 3**：development 不参与 α/r/λ/rho/族/基因/权重选择；选择日志与 development 评分进程隔离（seal 后评分）。
- **防泄漏 4**：derange null 只置换 observed-Middle 派生特征块，不置换原始阵列、不跨 fold 所有权，不产生隐藏 High-array 接触。
- **防泄漏 5**：预处理 array-local，跨 array 学习表示不得缓存复用；MAS5 单芯片断言。
- **坐标一致性**：所有 fold 同一 54675 有序坐标；四基因映射独立冻结哈希。
- **秩 cap 公平性**：full joint 总秩 ≥ 受限方法；逐输出块 cap 记录。
- **计数对账**：manifest 精确生成，分类计数（fit / SVD / cache / pipeline / 预处理 / 墙钟 / 峰值内存）分离；失败尝试入账。

## 6. 预算修正与实质错误检查

- 原 576 双 map pipeline 误当 576 fit → 修正 4143 fit；四基因 baseline 额外 193 → 4336。**算术自洽**：4143 + 193 = 4336。
- 但草案正文的 pre-implementation ceiling 写 3,567（1,806 base + 582 correction + 579 direct/KRR/no-obs + 597 refit + 3 null）。**两者不一致**：3,567 与 4,143 差 576，恰是"576 双 map pipeline 被误计/漏计"的量级。需明确：4,143 是含 pipeline 的 fit 计数，3,567 是不含 pipeline 的 estimator-fit 计数，二者口径不同，**不能互相替代**；manifest 必须同时报两种口径并显式标注。这是**实质的记账口径风险**，不是纯笔误。
- 另一实质问题：草案说"do not add the four-gene stress baseline until mapping frozen"，但预算已把 193 fit 计入 4336。若四基因映射未冻结，4336 中的 193 是**条件性预算**，manifest 必须标注 conditional，否则冻结时口径漂移。
- 其余检查：24 source / 7 development / later 14 未开、MAS5 单芯片、54675 坐标、四基因映射独立冻结、门槛不可改——均自洽，无其他实质错误。

## 7. 即便通过也仅支持什么

- 仅支持：**在该 N=24、单 Middle bundle、固定反馈预算下，observed Middle state/function 相对最强普通基线有可测预测增益**（若 no-observed-RNA 与 route ablation 均支持）。
- **不支持**：独特算法核心、结构优势、跨任务继承、主动查询智能体、样本效率曲线、joint world+agent 增益、C4、RSI。
- 选择 rank/shrinkage 于 source 是**普通调参**，不是 C4/RSI。
- derange null 是描述性关联诊断，**不是** RNA 特异性置换检验，**不是** p 值，**不能**救失败主门槛。
- development 已暴露，seal 只防运行时目标使用，**不恢复盲法**；不得声称无偏性能估计。

## 8. 不要求的

不要求额外数据探索、不要求新大架构、不要求第三层嵌套、不要求扩网格、不要求 Low/development-High/later RNA、不要求放宽或改端点。