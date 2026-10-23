# 从 ALMANAC 已开开发结果定位决策尺度误差

2026-10-22。已读 mandatory objective 与 query_teacher_resolution/CONTINUATION.md，并审查旧 ALMANAC DECISION.md、root/RESULTS.json 的已公开指标、ERROR_DIAGNOSIS.json、DESCRIPTIVE_DIAGNOSTICS.json，以及 run.py、diagnostics.py、error_diagnosis.py 的保存/排序语义。未读本阶段 peer 新稿。零下载、零新模型、零调参、零保护集访问；本稿未打开 NPZ 数值或执行新诊断，不把方法审查称独立复算。所有旧 STOP 仍有效。

## 最有证据的重复误差，以及必须纠正的配置混淆

最强已有结构是：已知组合高高角反馈能改善普通直接预测的功能 MSE，但这种改善未稳定转化为药对选择收益。主 selected 比较 B0 RBF2/lambda .1 与 B1 RBF2/lambda .01：MSE .0094443827→.0084953821（10.05%），top89 regret 实际也改善 .0086369803→.0077671489，6/10 cell 改善。不能把这一主结果写成“10% MSE 改善但 regret 恶化”。

反例来自同 pair 排除同 study 的预定敏感性比较：MSE .0100466787→.0094438057（约6%），regret .0096032022→.0097194522，只有4/10 cell 改善。后者是有限的、同预测规则在 source exclusion 改变后决策不稳证据，不是外部独立生物学失败。两个配置必须并列诊断，不能从一个拿 MSE、另一个拿 regret 组成更强故事。

已有逐 dose 描述把82.45%净 MSE gain定位在靠近反馈高高角的三个 query 位置；已有 source20/tune10 诊断发现合法 anchor innovation 与 pred−truth 残差相关，B1减弱但未消尽。这支持剩余可预测统计误差的动机，但既不能区分同板校准与生物交互，也没有形成可部署的个例失败识别器。不能再把同一相关重跑作为新发现，更不能直接扩展旧 anchor 更新路线。

## 唯一最小诊断：冻结预测的决策尺度审计

读取现有 PREDICTIONS.npz 中 B0-selected/B1-selected 与 B0-study-exclusion/B1-study-exclusion，和 VALUES.npz 的 y[30:40,:,:8]。旧 run.py 保存的预测已是10 development cells×887 pairs×8 queries。VALUES 当前只含已开40 cells，但其 y 成员解压会物化40-cell数组，之后才切10 development；应如实披露，不能声称仅物理解码10-cell truth。后20 closed 不在该成员中，不读取其他资产或 reserve。预先绑定输入 hashes；只做以下一个审计，不拟合校准器、不新增候选、不挑子组或阈值。

对每 cell，误差 E_pq=prediction_pq−truth_pq，定义 pair 平均 e_p=mean_q E_pq、cell offset c=mean_p e_p。严格正交分解为

    mean_pq E_pq² = c² + mean_p(e_p−c)²
                        + mean_pq(E_pq−e_p)².

逐 cell、两套冻结比较分别报告三项 B0/B1及差值，复核相加等于原 MSE。第一项是对所有 pair 统一的 offset 误差，对该 cell 内排序完全无作用；第三项是八 dose 围绕 pair 均值的形状误差，也不改变当前定义的“八 query 平均 growth”选择分数。只有 pair 平均预测参与此任务的排序，且共同 offset 本身仍不参与排序。第二项与排序相关，但下降也不保证 top89 收益，因为平方损失权重不等于 cutoff 决策代价。

同一审计再给出 top89 的精确交换账本。保持旧 run.py 的 argsort/tie 规则，用 mean_q prediction 的最低89对构成 S0、S1，E=S1\S0（进入）、X=S0\S1（退出），|E|=|X|。定义真实 pair 分数 t_p=mean_q truth，则

    regret1−regret0 = [sum_{p in E} t_p−sum_{p in X} t_p]/89.

共同入选部分和真实 oracle 项全部消去。逐 cell 报进入/退出数、真值总差和与旧 regret 变化的数值一致性；原有保存的 cell 顺序、pair canonical目录用于可追溯索引。若需留逐 pair 账本，仅报告冻结集合成员、p0/p1、delta score 与 t，不根据结果选更好集合。不要把89个被选择pair当89次独立实验，也不宣称单个坏交换在测量噪声下稳定。

这是一项描述性投影/选择审计，而不是两个新实验：前半解释 MSE 改在哪里，后半精确解释这个固定决策为什么变化。无需再次拟合source模型、计算新anchor相关或扫描 top-k。固定 k=89，不新增 bootstrap、排序损失训练或 subgroup search；10 cell 的异质性直接列出。

## 合法可观测信息与能回答的问题

预测前可见：相同六单药、已测高高角组合值、冻结模型的 score0/score1、score改变量、预测 cutoff 距离及因此产生的进入/退出身份。现有 anchor innovation 仅在对应高高角基线预测也按合法信息计算时可用。不能将 query truth、真实 residual、oracle top89、swap truth advantage 或 cell-specific offset c 当实验前输入。开发真值只能在这次审计中解释误差，不能据其阈值再建停止/选药策略并宣称验证。

该审计可以区分“对当前排序严格无作用的误差改善”与“改变 pair 选择分数/集合的修订”，并定位 exclusion regret 变坏是否来自少量高代价交换或广泛小变化。它不能仅凭这些终点值识别 MSE改善到底是 assay校准、培养差异还是真实药物相互作用；因为 pair-specific校准也能改变排序，monotonic scale校准也不只表现为常数 offset。这里“offset/shape”是数学方向，不是生物机制归因。

## 成功与停止边界

诊断成功条件只是两项精确恒等式复核、冻结集合和指标可追溯，并得到不混合配置的误差账本。若 gain 主要在排序不变项，支持“当前 MSE 门主要奖励了此决策不用的方向”这一有限解释；若 pair-centered项也改善而 regret恶化，提示误差权重/cutoff风险失配，不等于缺少功能信息。若 regret由极少数交换主导，也只是假设集中性，不能据事后挑出它们设计部署门。

无论哪种结果，都不直接晋升新的药物更新算子、不证明 world model/agent/继承/RSI 必要，不把审计包装成性能改进。结果用于指出是否存在值得另行提出可证伪机制的决策误差；未来任何新规则必须有源可学、目标合法可见的预测信息及同信息强基线，不能用本开发集挑规则后称独立收益。维持旧 anchor-transport 新颖性/RSI扩展 STOP，完整目标 ACTIVE / NOT_ACHIEVED。
