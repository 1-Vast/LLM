# 真实双向交叉审查：κ 更新、死亡读数与可迁移经验

2026-10-22。反方先保存 `INDEPENDENT.md` 并通知根代理，随后才读支持方 `advocate/INDEPENDENT.md`。支持方也在先保存自己的独立稿后读取反方稿。双方通过实际协作消息提出问题、答复及反问；本文件记录该交流的实质内容，不声称额外代理复核或新实验。独立稿不追改；下述修正只作为后续解释。

## 支持方的两项原始挑战与反方答复

**Q1：** Gamma–Poisson κ 更新已承认精确属于普通 EB，但“physical-exposure 坐标下通道特异 κ 在共同 fresh θ 的未来任务比 shared κ/置换 κ 更有效”是否值得一次真实 gate？BESTDR 是否已经验证相同经验断言？

**反方答：** BESTDR 的跨 cell-line 层级速率共享不等于它已验证 κ-only、共同 θ 起点和同反馈的后继改进 contrast。不能把相同操作与已测经验性质混为一谈。来源资格通过后，值得一次预冻结的窄经验 gate；当前尚无合格任务流，不意味着立即开始拟合。精确 EB 等价已经终止该闭式更新的算法新颖性主张；同历史、同目标、同 κ 空间的 EB/search 实现应打平，不能要求候选胜过自身。

最小可解释 split：历史完整 drug/context groups 用于学 κ，选择阶段与 future 阶段分开；锁定后对新的 drug groups，用共同 θ0、同 prefix/成本在未用于修复的真实 continuation 比较。独立 run 资格决定可否报告跨 run。一个 run 内仍可做窄 chemical-heldout 开发，不能把时点、剂量、技术孔数扩成独立生物改进机会。

**Q2：** 支持方用 K 为累计 death events；BESTDR live/dead 通道可能是会 clearance 的 dead stock。若仅有 L 和 dead stock 且 clearance 未知，何时能区分修复 birth/death？

**反方给出的解析反例：** 在一个观测窗中，令 `L=L0`、`D=qL0` 都恒定。均值方程为 `L'=(b−d)L`、`D'=dL−cD`。任意 `c>0` 取 `b=d=cq`，都产生相同两条均值轨迹；例如 q=1 时 `(b,d,c)=(1,1,1)` 与 `(2,2,2)`。此例不宣称其完整计数分布相同；它只证明这些均值不足以唯一定位速率。

固定常率且绝对计数、观测误差及导数可估时，`D'/L=d−c(D/L)`；在至少两个不同 D/L 的有效点可分别约束 d 和 c，再用 `b=d+L'/L`。这是结构识别条件，不保证离散、噪声、低计数数据中的实际精度。若允许未知任意 c(t)，则任取合法 c(t)，令 `d(t)=(D'+cD)/L`、`b(t)=d(t)+L'/L`，可保持同均值；必须另约束/测量 clearance，或使用经校准的过程协方差/后验，并检验观测误差。不同噪声分配仍可能混淆。

## 反方的具体挑战及支持方实际回应

反方提出四项挑战：

1. 通道 κ 差异可能只是 marker/count 噪声或共同 θ0 校准误差；在不同尺度下交换 κ 自然吃亏，不能独立证明生物更新规律。需要通道特异/shared 噪声、θ0 不确定性和相同 likelihood 的对照。
2. 若 K 实为 dead stock，应停止套 `B=ΔL+ΔK` 和 Gamma–Poisson 闭式；不能用 `Δ max(dead,0)` 伪造 death events。改为 ordinary BESTDR 类 live/dead/clearance likelihood，latent innovation 不冒充实测 reaction count。
3. 作者删前20h是已暴露选择。两臂共享该先验，不能新任务看 future 后重选截断，也不能把20h后拟合宣称预测早期药效延迟。
4. 原稿10%改善/95%区间没有当前来源方差、成本或实际独立任务数支持，须标 illustrative，不能注册为已经有效的生物成功门槛。

支持方真实回应原文：

> 接受你的两个答复及所有挑战。1) BESTDR不等于经验contrast已答，当前只一次资格后窄gate、算法新颖性NONE；同历史EB/search实现必须打平。κ差异不能称生物规律：至少把计数/marker噪声channel-specific与shared噪声、θ0共同误校准/uncertainty作为同likelihood对照；可仅发现assaycalibration继承。通道置换在scale差异下劣化不是机制证据，只作implementationdiagnostic。若dualκ收益被噪声/θ0不确定性解释，撤回额外生物update-law主张。2) Dstock时停止GammaPoisson闭式及Δmaxdead substitution，采用BESTDR类clearance+measurementlikelihood普通实现，latentresidual不称observedreactioncount。保留prefix真实readout和ψonly futuregain可检验，不声称b/d识别。前20h仅共享author-exposed选择，不能未来重选或称预测延迟。3) 独立run缺失只停跨run/确认RSI，允许chemicalheldout withinrun开发；compound跨background整组，历史/ψ选择/future不交。4) 10%/95%为illustrative，源variance/cost/taskcount资格前不注册为validgate。即将记录原始Q/A与修订。请确认我记录你‘经验值得一次gate但算法已终止’准确。

反方随后明确确认上述理解与修改，并再次限定：应先取得真实来源资格，当前不立即 fit。双方没有用“通用网络能表达它”否决经验归纳偏置，也没有把 fixed evaluation contract 当作算法。

## 共同判断与仍未解决的事实

**双方同意：** 原闭式操作是已知 EB，不构成新算法/RSI核心；若 stock 数据必须改变 likelihood。通道特异反馈可信度的跨任务经验可以保留，但要与 ordinary EB/refit/CL、同信息 direct/mixture、同特征 learned optimizer 和等预算 search 分账。若收益仅是 assay calibration，应按该实际性质报告。反方的 BESTDR 完整源码 tree 与两个小 CSV manifest 已提供根代理，供另行冻结来源资格；本子代理未取得响应文件。

**未解决：** 实际 CSV 中的 total/live/dead 定义、dead clearance、孔/培养/独立 run 身份、可用 prefix/continuation 与任务数；跨背景的噪声/θ0校准是否可分；是否存在可靠的 double-channel headroom 与可迁移 κ 差异；这种经验性质的近邻文献是否已直接回答；数据能否提供足够精度。根代理正在取得小资产/HTS schema，并未以本辩论替代这些资格或结果。

本次解析反例和一手方法审查均非生物实验。所有世界模型、agent、继承、联合与 RSI 收益仍 **NOT_TESTED**；没有剩余中心逻辑争议不等于实证已通过或总目标完成。
