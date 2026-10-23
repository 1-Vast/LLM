# ESG 实际交叉审查与 root 精确核查范围

2026-10-22。本角色 API_REVIEW.md 已独立封存后才读 skeptic/API_REVIEW.md、root 的 ROOT_ESG_PROTOCOL.md、EXACT_ESG.json 与 research/update_rule_renewal_20261022/exact_esg.py。此处为新增交叉记录，不改独立意见。未重新执行或独立枚举 root 代码；数值归属 root。零新数据、API、模型拟合或保护响应读取。

## 精确证据究竟证伪什么

Root 构造六个同状态、不同药物顶点，固定非零差分敏感度，响应为独立连续噪声；720 个响应次序等概率。alpha=.05、delta=.1、一个方向时，无序 15 边门接受 49/720=.0680556，有序 30 边为 169/720=.2347222。每条边边际一致概率仍为 .5。这不只指控反向重复，也直接展示去重后共享端点依赖足以破坏所述 binomial 门校准。不是对所有 block/permutation 方法无效的证明。

Root 的四状态同药物例采用真实药物效应 0、状态主效应 y=s、冻结 baseline=0、g=phi*s。门仍接受正向 g 更新；无序门 p=1/64，有序 p=1/4096。该例允许模型 baseline 失准，推翻并集边普遍消去状态 nuisance 及对 g 的生物模块解释。它不证明总预测或功能决策必然变坏：把 baseline 误差写进 g 可能改善总预测。同状态边确实消去纯加性状态误差；baseline 完美校准时该特定反例不触发。

对 L(phi)=sum_edges |(y_i-y_j)-(f_i-f_j)|，非零残差处 -D_v L=sum sign(rho)*a=S。Root 数值导数核对仅执行在其标量 nuisance 见证，普遍等式来自此链式法则，不宣称数值测试覆盖一般非线性模型或零残差。合理零点 subgradient 可另行规定。

## 实际相互质疑与答复

本角色向 skeptic 提问：不能将并集边缺陷扩大为任何边差都无用；合法同状态边及 dependency-aware 检验可能保留经验价值，停止应限当前规则。Skeptic 实际答复同意，并反向要求本角色修正两处范围：有限 eta/组合步缺稳定保证不等于经验 rank 学习无效；误写 g 不等于总预测恶化。本角色明确接受两点，并记录为上述范围。

本角色又质疑 skeptic 的 7 条 a=1 一致、1 条 a=100 不一致见证：k=7/8、binomial p=9/256，但 S=-93，确实说明检验的方向与执行的方向可相反；然而执行 -v 仍是相应 pairwise L1 下降方向，不能直接声称 loss/utility 变差。Skeptic 实际回信明确同意这一范围。其四顶点共同 latent Z 例是另一个、较宽 null 下的精确反例；不混称 root 的 iid 六顶点结果由 skeptic 或本角色复跑。

## 最强善意解释与停止边界

保留的具体想法是：真实功能反馈形成合法 contrasts，低维方向白名单可作为普通 procedure inheritance，门即使缺所称统计保证仍可能是有用启发式。缺乏普适 Kendall 改善定理本身不构成否定经验价值的理由。

公平直接对手必须具有同一 g、方向集、合法反馈、门、步长与缓存的节点导数，并对上述 pairwise residual L1 做坐标符号下降。这个对手与所写 S 更新逐项相同；不能只比较 sample SGD 或任意 logistic ranking。基于现有方程，这个表示法没有额外操作或有限成本优势。相等操作不等于文献首创权证明，更不等于整个 learned optimizer 家族都没有创新。

若修为同状态边、合法独立物理块检验和更合理方向门，必须重新给出实际差异与新合同。不能自动把修正后的普通 pairwise 学习称新核心，也不能自动否认任何未来结构化改进。当前没有需要用生物 pilot 再确认的差异主张。

决定维持 STOP_LITERAL_ESG_CORE / NO_CANDIDATE_AS_WRITTEN。它针对当前统计保证、nuisance 解释及额外机制主张，不断言全部边学习或功能反馈更新无效。无新 toy/data 跟进；完整世界模型、智能体、继承、联合收益及 improved-improver 目标仍 ACTIVE / NOT_ACHIEVED。
