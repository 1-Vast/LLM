# FSI 与 CCIP：最强善意版本及 root audit 的作用域

2026-10-22。先保存 INDEPENDENT.md，后读 mechanism/RESPONSE、improver/RESPONSE、两份 root algebra protocol、代码和有限结果摘要；未读本阶段 peer 新稿。未重跑 audit、未 fit、未新增生物 response 或改 freeze。provider 输出是提案，root toy 是代数/执行证据，二者均非药效实验。

## FSI：值得保留的是校准决策问题，不是当前秩冲突解释

最强善意版本是一个真实的预算问题：新板的读出偏移不确定时，先测一个对照，可能比再测一个药物孔更能改善**绝对 hit 阈值或跨板候选比较**；已知对照和药物标签应约束不同模块，避免少量异常对照破坏药物效应形状。这个经验问题有潜在实际意义，不能因参数更新等于普通方法就宣布所有主动校准无用。

但原文说“板尺度解释状态/功能的板内秩冲突”，模型又是 `yhat=s_b+f_i`。对板内任意 i,j，`yhat_i-yhat_j=f_i-f_j`，因此校准 s 不改变板内次序或 κ_b；正的共同乘法同样保持次序。root 对这项确切理由的反例/不变量成立。原文按 κ_b 选锚并不能靠更新 s 让 κ_b 下降；若 V_b 会因测量而下降，那还需定义，不可默认秩冲突已被解决。

**root 不应越界的地方：** 不同板的偏移不同，比较 `s_b+f_i` 与 `s_c+f_j` 时次序可以改变；绝对 hit 阈值也会改变。因此板内秩不变，不推出跨板 ranking 或 threshold acquisition 没有价值。κ_b 也可能作为偏移风险的统计代理，即便不是其数学成因；这需要独立证据验证其相关性和查询价值，不能由不变量单独排除。然而这些都不是原提案已经认证的新性质，若保留须明确改为新的前瞻校准假设，不能说原尺度致秩冲突解释被证明了。

更新审查：字面 `s←s+eta(y-f)` 不减当前 s，重复稳定对照会累计漂移，root 的演示有效。改为 `s←s+eta(y-s-f)` 后，控制标签更新截距、药物标签更新形状，正是带标签类型掩码的块梯度。在线性例子 root 40 steps 最大差约2.78e−17；对可微非线性 f，也能直接写为相同 loss 的固定块掩码，不需要援引通用 NN 表达性。这与我独立提出的模块mask候选有同一个具体归约。

“只有对照识别 s”还须 f_control 已知/被锚定；冻结 theta 只是算法条件，并不证明生物板偏移与模型控制偏差可分。只有药物标签且固定 s，theta 的识别仍需设计 rank/支持。root rank-1 的设计反例反驳原文无条件可识别性，不能推出所有满秩实验都不可识别。标签来源分流是一种可选择的归纳偏置，不是识别定理。

**FSI 当前决定：STOP_EXACT_RANK_RATIONALE_AND_NEW_OPERATOR_CLAIM。** 最强普通比较必须包含带已知对照设计矩阵/掩码的层次模型、同动作菜单的主动校准、部分 pooling、普通全 refit/在线更新，而非只给普通 AL 药物点。若要保留普通功能 pilot，必须先取得真实 board/control/state/function/重复身份；本提案明确未认证这些，故现在没有可执行真实新板实验。最低 pilot 可检验预先固定的绝对阈值/跨板决策是否在同总成本下受益，且对照是活性/死亡/读出校准的哪种定义要分清。先前 STACK 的 opaque contexts、#N/A 与 library plate 不能充任对照，已停 test 不重开。

provider 的“>=2板/>=1细胞系方向一致”不能支撑泛化到新板/细胞系的核心或 RSI；需与真实独立单位和功效相称。校准效果也不单独证明世界模型必要：同 z/d/b 的强 direct 可用同一校准层。改良 τ 的 inherited acquisition rule 若确实提高后续改进，应作为普通策略学习与程序搜索的对照结果，不因命名 FSI 自动新颖。

## CCIP：可能有价值的是可迁移区域构造；证书表本身不是新操作

最强善意版本不是“失败多就禁用”：它试图从**高置信且可重复的模型失配**学到一个可在新任务、购标签之前识别的条件 R，并证明某类更新算子在该条件下经常低收益；从而优先尝试别的算子，把有限程序/测量预算转到更有效的改进。若 R 能概括真实干预状态上的稳定失效结构，并显著减少新任务实验成本，这是值得测试的实证现象，不能只因用了 Beta 就排除。

字面版本有严重错误：它选择验证误差最小的 o*，无论成功与否却记为失败。root 明确给出成功的最优算子被禁用的反例，足以反驳该无条件规则。最善意修正应按**实际执行且有明确定义的成功/失败反馈**给每个算子记账，而不是把相对最优当成失败证据。还要收费：为确定 o* 运行全部候选的训练/验证不可免费。

修正后同 R、门控、gain/cost 和事件序列下，Beta计数、>.5禁用、预算排序完全由普通 region×operator Bernoulli统计实现；root 的8 events 是这项表示级归约的实例。禁止 o 后无其他探索/例外便不可能看到 o 自己纠错，root 的 reachability 反例正确。跨任务同名 R 不保证算子收益同分布，任务反转反例反驳无条件可靠运输，**并不反驳另行认证的稳定条件失效区域可能有用**。

**真正尚未被这份 toy 覆盖的只有区域构造和行动耦合。** root 只给普通控制器同一个 R，因此没有证明任意学习 R 的算法都等价。但原提案也尚未给出那个算法的关键可执行细节：

- `R=TopK遮挡特征集，使遮挡后e下降最大` 定义的是被遮挡特征的集合，不等于输入空间区域的成员谓词。还缺 K、遮挡值/分布、候选搜索、tie、成本、跨模型版本的稳定性和新 x 的 membership 规则。
- e 依赖已经付费的 y。若把同一“使误差下降”优化用于未查询 x 的区域判定，就需要未购 y，形成实际查询泄漏。可以从旧反例训练一个只用合法 x 的规则，但这个**规则学习器必须明确写出并验证**；不能把它藏在“区域”二字中。
- 遮挡令已见误差偶然变小不是 causal responsibility，也不证明算子效应由同一特征控制。可迁移 operator×R 异质性应直接在独立任务测量，不能只看原模型误差集中度。
- σ 要定义和校准。普通预测器的 SD 不是自动的高置信错误证明，任意缩放 σ 会改变进入证书的事件；没有测量噪声/模型不确定性资格时，“证伪证书”过强。
- hard ban 需要可达的恢复路径、探索/到期或有效运输边界，且所有重试要收费。修正为这些机制会落入标准有探索/遗忘的 contextual bandit 控制；可能有益，但其数学标签不是创新。

如果补为一个固定有限规则树：训练树的输入仅合法历史/x，叶子就是 R；在叶子内对 operator 做相同 Beta统计，则普通 **同规则树+contextual bandit+同查询选择器** 逐步执行相同操作。这样是具体普通基线，不是通用预测器表达性论证。若候选实际产生了这套基线无法得到的共享区域/识别约束，就需给出是哪一个不变量或哪一步；目前没有。

**CCIP 当前决定：STOP_LITERAL_RULE_AND_CERTIFICATE_NOVELTY；region-learning/query-coupling 未定且未指定，不可当成已存在的创新。** 最便宜下一门应先提交 label-blind 的区域成员函数、算子success定义、完整计费与恢复机制，在没有新生物数值的构造例上检查不会泄漏/误禁/锁死。仅当有真正结构增量与合格新功能任务，才考虑真实 pilot；不在已停 STACK 的暴露 train/validation 上切20小任务来证明 drug world/RSI。该做法不会制造独立任务或新功能依据。

## 比 root 更积极但仍可证伪的保留

两项 root audits 都没有测得药效、主动实验节省、程序继承或 RSI；不能从 toy failure/归约宣布生物新发现不可能。FSI 留下可验证的**真实跨板绝对校准决策**，CCIP 留下可验证的**label-blind、可运输的算子失效条件学习**。这两个具体经验问题是否值得花真实数据预算，取决于认证应用和是否强于普通同信息方法。当前各自缺必要数据/操作，故不建议直接大规模实现，不把缺口补成复杂架构。

两者都未提供新 intervention-conditioned transition/rollout 的贡献，也未完成 world/agent/inheritance/joint/psi1>psi0 的独立证据。已有普通组件仍可能带来非平凡生物功能实证；当前没有该实证，不能用这个可能性授予新核心资格。下一步真实交叉应专门挑战上述 scope，而非仅互相复述 STOP。

## Constructive：AZ2024 最多一项普通结构机会

此段在独立两候选 review 后，应 root 要求，读取数据方 INDEPENDENT.md 后追加；未开 AZ response。**不为 FSI/CCIP 开值；可以先做 AZ design-only census。** 数据方认证的 source 是 Cancer Discovery2024 DOI10.1158/2159-8290.CD-23-0388，109 pairs/37 drugs、72h CTG normalized inhibitory response，7×7或AZD1775的5×5，静态功能面，无匹配早期干预状态。这里不借“world”命名添加动态解释。

唯一结构假设：**药对的组合效应中，跨细胞背景差异有相当部分由单药效力/剂量坐标解释；在单药效应坐标中，剩余 pair-specific interaction surface 可作近似共享先验。** 设 u=已付费的A单药抑制效应，v=已付费的B单药效应，组合抑制为

`Y_AB,c(dA,dB) = u + v - u*v + h_AB(u,v) + delta_AB,c(u,v)`。

待测限制是“共享 h 的模型是否足够好，新增细胞特异 delta 在当前反馈预算下是否有可靠、可预测的决策增益”；不是断言 delta 恒零，也不是称 Bliss 具有机制真值。u/v 不应因标准化噪声或负抑制被事后裁剪。假设可能失败，尤其原文已经报告背景特异性；应在预定完整合格菜单评估，不能开值后挑支持共享的癌种/药对。

最简普通实现为 Bliss baseline 加 pair-specific tensor-spline/kernel residual。强对照须获得相同单药曲线、同 dose/pair/background 元数据与全部付费 bundle 反馈：同 effect-coordinate 的普通分层残差/全 refit、强 direct response-surface predictor、以及仅 Bliss/HSA 与简单混合；不可以不给 direct 单药效应坐标。这个结构模型本身就是可实现该假设的普通方法，不主张新算子。

**区分来自什么的最便宜 component test：** 固定相同已购 bundle 历史，在未购、且两种药单药曲线已合法覆盖的 pair-dose 上，比较 (i)只据当前 monotherapy更新坐标而冻结共享h，(ii)同历史同时允许普通交互残差refit，(iii)同信息强direct。测实际normalized inhibition预测和预先限定剂量范围内的推荐regret；不能用max-over49 noisy synergy当唯一utility。若加delta的改善不可靠或无净决策headroom，停止开发“需更复杂cell-specific repair”的方向；若有稳定异质性，才为以后的普通更新策略机会检验提供根据。该 component masking仅用于归因，所有采集成本仍按实际完整bundle支付；真正policy比较另用相同合法菜单/预算。

**不能免费获得mono：** 8个pair bundles至多覆盖16个不同药的单药曲线，且重复参考可能来自不同板/剂量。目标未购pair必须落在已覆盖drug graph与匹配dose support内，或另明确付费获取mono。不能一边按8次query收费、一边给全37drug的monotherapies。元数据清点应先验证有足够这样的未购target pairs，否则本机会实验不可执行。

source尚缺（先只census，不开响应）：实际SIDM×pair的有效菜单/QC与缺失；monotherapy/control references是否逐bundle匹配及跨pair重复来源；准确dose/单位/5×5裁减映射；可支付的mono覆盖图；matrix/occasion/plate/technical-replicate标识；与已暴露Jaaks的重叠及合法新任务角色。现有wellstats已归一化，若没有原始luminescence/blank/DMSO及其不确定性，不能把单药/组合残差诊断为仪器尺度错误；这里只识别统计运输/预测结构，不鉴定normalization的生物因果来源。

数据不足就停止这一个pilot，不另开多个候选。数据足够也须独立前响应协议、预算/功效与成功停止阈值，再只开development。此题的价值在于找到可测功能结构及普通方法是否已有足够能力；即便成立，也不自动证明world、agent、继承或RSI，不是 FSI/CCIP 的救援。

### 实际数据交叉后的 metadata 更新

数据方随后报告 root 独立协议取得的 glossary/header：C wells 附 matched mono_y/yhat，含 MASTER_CELL_ID、CELL_ID(stock expansion)、BARCODE、DRUGSET_ID、cmatrix、实际drugIDs与µM dose；无原始controls/SIDM。本方没有自行打开CSV。上文的“SIDM×pair清点”因此应具体落实为认证 MASTER_CELL_ID/model 与 CELL_ID/stock、plate/layout 层级，不能猜 SIDM 或把 stock/plate 另算新任务。

运输机会必须来自已付费其他矩阵：如购 A–C 与 B–C 后，才可用合法匹配的 A/B 单药参考预测未购 A–B；不能从未购 A–B 行偷取附带的 mono_yhat。跨 BARCODE 的参考是否可运输仍未核验。不存在闭合 pair graph 或匹配 dose 就停止本 pilot。

另须区分 dose support 与 effect-space support：单药平坦或非单射曲线可把不同实际剂量折叠到同 u,v，但组合功能不同；这会直接挑战效应坐标充分性。metadata 不提供数值支持/噪声资格，后续 development 协议需前瞻界定共同支持、插值和 measurement-error 的处理，不许开值后挑合适区域。这里识别的是给定参考下的函数压缩/预测运输，不是原始归一化错误的因果归因。
