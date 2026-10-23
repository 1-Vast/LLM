# Query teacher：生物传播边界的实际交叉审查

2026-10-22。INDEPENDENT.md 已独立封存后读 skeptic/INDEPENDENT.md、frontier/INDEPENDENT.md，并实际发出交叉问题。Frontier 初次读取时尚未写出文件，此后实际读到完成稿，未将失败读取冒充审查。不改独立稿；未新增来源请求、数据或数值实验。

## 最强反对意见已接受

Skeptic 指出 rank-one 右因子限制也是普通单样本 SGD 的性质，并非 teacher 专属缺陷。本角色接受：独立稿的作用是定位可达性与收益归因，而非借普通限制否定 teacher。它可以在已有 key 关联的可达空间内选不同隐藏向量，可能绕过 tanh 饱和；这是一项可检验能力假设，但当前未提供药物特异的新操作或独特性能预测。

单反馈、固定 key 下，k_s 与 k_q 正交时 teacher 对 q 的隐藏写入严格为零；由于 b 更新用 pre-update h_s，teacher 与 head-only 的单步 q 输出相同。多步时 P 可改变后续 support hidden，间接改变后续 b，所以不能外推总预测一直不变。多步保留的严格结论只是 A 在 support key span 正交补上的作用不变。若 key 也更新，需重新分析。

Skeptic 又指出实际 autodiff 若将完整 local target 全局 detach，会抹去 P 的 outer 路径。本角色同意采用明确 recurrence 的外层导数定义：对 A_new=A+eta*r*e*k^T 求导，不能说 inner partial derivative 中 target constant 就意味着 outer 也全 detach。独立稿的 P 零梯度结论还要求固定其他 meta 参数/key，针对该正交单步 query；它与一般非正交情况下有效 outer P 梯度不冲突。

## 生物有用性与创新贡献是两件事

共同 latent susceptibility 的 residual 结构能使一个标量反馈对另一药物有用，但前提是源任务已学到合法跨药物 loadings/关联，而非凭化学相似或一个残差识别多个未知因素。应给普通 residual covariance/ridge、head-only、直接预测和 learned optimizer 同样关联信息及训练成本。不能把源功能训练 k 的收益全记在 teacher P 上。

药物应用仍有可检验的普通能力问题：在源学 key 关联可靠、有限更新预算和独立背景下，query-trained hidden direction 是否超出同信息 head-only/普通更新；多 assay 单位与处理顺序是否影响后续决策。这些问题不是本稿新增算法，也未证明世界模型或 agent 必要。没有新的生物结构或独立有限成本性质，不能仅以应用换域晋升。

Skeptic 实际反问 residual covariance/ridge 的 l 是否免费 oracle。本角色明确答复：l、mu、noise 必须来自相同 source episodes/合法 control，并计训练成本；解析已知 l 只是在声明的受控结构中说明 scalar feedback 的信息量。learned k、A0/b0 和 head 更新均应共享。Skeptic 实际答复同意当前暂无提出的药物特异新操作或独特优势，能力假设可测但 NO_PROMOTION。

## SIB 原文证据改变的结论

Frontier 的 sealed 报告给出 SIB 2004.12696v1 的原文位置：Eq7 held-out query likelihood/KL 外目标、Eq10 finite synthetic-gradient 内循环，Sec3 明确不添加 gradient imitation loss，而由 Eq7 驱动 xi。此处本角色读 frontier 的方法摘录和范围报告，未自行再抓来源或复现论文。该具体一手证据足以停止宽泛“query 风险直接训练 teacher、无需 true-gradient imitation 是新原理”的主张。

但 SIB 是 classifier/posterior、query-input transductive 更新，本规则是 labeled-support residual hidden 写入。两者不能直接逐项等同，实际 query 输入访问、source training 和 deployment 计算亦必须匹配。支持只读本次反馈、不依赖部署 query pool 是明确接口区别，尚不是生物特异收益或新理论贡献。Feature-network detach 也不意味着 xi 的 outer 路径全 detach。

本角色实际向 frontier 提问：e=0 强制不写不能免费解释为有益生物约束；一个测点正确可能来自误差抵消，也不能保证其他药物/细胞状态正确。当前没有认证 residual gating 的独特优势，不应从 exact prior 未定反推出新颖。停止 broad objective 新颖性，与保留完整 formula exact prior UNRESOLVED 并不矛盾。

Frontier 实际答复接受残差为零不是生物正确性证书，并反问本角色是否混淆 ridge 表示 l 与实际从有限 source 估计 l。本角色明确接受边界：解析结构只检验可达性，不能证明 ridge 在真实任务必胜；估计 l 的 source 风险和计算成本必须报告，不能给 ridge 免费 oracle。候选若源学 k/A0/b0，控制必须共享这些资源，不能拿人为 one-hot 贫表示来冒充全部可训练候选。

当前决定：NO_PROMOTION；不因局部几何限制否定全部 teacher，不因未查到同式宣布原创，不新增生物 pilot 或重复 toy。具体隐藏方向的共同能力仍可研究，但本轮没有产生药物特异的新机制；完整目标仍 ACTIVE / NOT_ACHIEVED。
