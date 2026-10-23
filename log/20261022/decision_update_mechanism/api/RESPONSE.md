NO_CANDIDATE

理由压缩为一句话：在你给出的约束下，我找不到一个**真正具体的新操作**能同时满足“由可得功能反馈验证、可继承、有限成本上有实质区别、且不落入已停路线或普通已有算法改名”这四项；任何我能构造出的候选，拆解后都只剩两类之一——(a) 已被STOP覆盖的corrector/gate/paired-DR/固定nuisance约束的变体；(b) 普通已有算法（如带pair-mean特征的RBF残差、query外合成梯度、固定key的tanh teacher）的重新参数化，额外贡献无法在合法端点上被单独证伪。

为不空转，下面给出**唯一一个我评估后仍决定不推荐为“新操作”的具体构造**，并说明它为何不达标、以及若强行要做的最小证伪长什么样。这满足“至多一个真正具体的新操作或NO_CANDIDATE”的形式要求，同时诚实标注它不是合格新操作。

---

**被评估构造（不推荐，仅作否定性记录）**

**操作名**：pair-mean 锚定的 support-span 残差传播（PM-SSRP）

**动机**：现有事实说 centered pairmean 误差在两套配置 10/10 cell 都改善、贡献 55%/69% 净 MSE 收益，且 top89 只交换每 cell 1–7 pair。这说明有益信号集中在“pair 级中心化均值”这一低维统计量上，而非 global offset 或 shape-only。一个自然的可迁移修订是：把 pairmean 作为**唯一可传播的低维锚**，只在 support span 内做残差传播，禁止跨 span 外推。

**形式化**：对 cell c、药对 (i,j)，令
- m_c = 该 cell 内所有已观测 pair 的 centered pairmean 估计（用 support 内 pair 的 y 减去单药可加基线后取均值）；
- 预测 ŷ_ij = additive_ij + m_c + r_ij，其中 r_ij 由 support 内 pair 的残差用固定核 K 做**span 内**插值，span 外 r_ij ≡ 0。

有限伪代码：
```
for cell c:
    base_ij = f_add(i,j)                      # 单药可加基线，冻结
    resid_ij = y_ij - base_ij  (仅 support 内)
    m_c = mean(resid_ij over support pairs)    # centered pairmean 锚
    r_ij = K_interp(resid - m_c, support)      # 仅 support span 内
    pred_ij = base_ij + m_c + r_ij
    if (i,j) outside support span: r_ij = 0
```

**真实信息合同**：只用 ALMANAC 已公开的 cell–drug–drug 响应矩阵、单药响应、以及“同 study 源条目”标记；端点分两个——(E1) 状态预测端点：held-out pair 的 MSE 与 centered pairmean 误差分解；(E2) 药物决策端点：top89 pair 选择的 regret 与每 cell 交换 pair 数。禁止用未测 query 真值做门。

**最强普通对手**：同一 additive 基线上，直接用 support 内 pair 的 RBF 残差插值（无 m_c 锚、无 span 截断），即你现有“普通 RBF 表面预测”的等价物。若 PM-SSRP 不能在该对手之上、在 E1 的 centered pairmean 分量和 E2 的 top89 regret 上同时给出**可分解的额外贡献**，则它只是把已知 pairmean 收益重新包装。

**可能错误**：(1) centered pairmean 的 10/10 改善可能主要由 support 内 pair 的**选择效应**驱动，而非可传播的低维锚；span 截断会把这一收益在 span 外归零，导致 E2 regret 恶化超过 top89 交换 1–7 pair 的轻微恶化幅度。(2) m_c 与 r_ij 的分解在有限 support 下不可识别，55%/69% 的贡献可能无法在 held-out cell 上复现为独立可加项。(3) 该构造与已 STOP 的“固定 nuisance 约束 ridge”“pairwise residual sign gate”在数学上邻近，容易被判为变体重启。

**最小证伪**：在**至少 5 个未参与调参的新 cell**上，固定同一 additive 基线与同一核 K，比较 PM-SSRP 与普通 RBF 对手；若 PM-SSRP 在 E1 的 centered pairmean 分量上相对对手的改善中位数 ≤ 0，**或** E2 的 top89 regret 相对对手恶化且交换 pair 数 > 7/cell，则证伪“pairmean 锚 + span 内传播”是可继承的有益修订。该证伪只需已公开 ALMANAC 数据与现有评估脚本，成本有限，且不触碰任何 STOP 路线。

**为何仍判 NO_CANDIDATE**：上述构造的额外贡献（m_c 锚 + span 截断）在最强普通对手面前，预期只能解释为“把 centered pairmean 收益显式化”，而这一收益你已有事实表明普通 RBF 已部分捕获（MSE 改善 10%，排除同 study 后 6%）。它没有提供**超出普通 RBF 的可证伪新传播机制**；span 截断更像约束而非新操作；且与已 STOP 的 nuisance 约束路线邻近。因此我不把它列为合格新操作，维持 NO_CANDIDATE。

---

**诚实说明**：若必须推进，我建议的不是新算法，而是**先做上述最小证伪的否定性实验**，用其结果决定 pairmean 锚是否值得作为可继承组件；在得到正结果前，不应宣称任何 RSI 或 worldmodel/agent 必要性——你现有事实也不支持后者。引用仅作待核线索：SIB2004.12696 的 query 外合成梯度已非新原则；tanh teacher 的固定 key 限制传播到 support span，与本构造的 span 截断同病，不能仅换参数化称新。