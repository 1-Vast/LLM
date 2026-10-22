# 实际交叉裁决：经验更新规则值得什么 gate

2026-10-22。独立稿先存，后读 scientific_skeptic 的 `../skeptic/INDEPENDENT.md` 与 functional_auditor 的 `../functional_auditor/DRAFT.md`。我分别主动发出两问；收到方法反方答复及新挑战、数据反方四问后逐项回应；方法反方确认修订，数据反方也给出对我两问的原答。**真实消息原文全部另存 CROSS_RAW_MESSAGES.md。** 独立稿保留原样，以下修订覆盖其适用范围及停止规则。

## 1. 已停止与仍可检验的部分

**停止算法新颖性：** event-count 的两个 κ 闭式更新就是 Gamma–Poisson empirical Bayes。相同 EB、相同 κ 空间同信息搜索应当给相同结果。这不是因为通用预测器能表示而否决，而是具体所有步骤已被普通方法逐项复制。

**条件保留窄经验 gate：** BESTDR 已共享 birth/death rate priors，但其已审操作不等于已经验证“只继承 ψ、共同 fresh θ0／同反馈／未来 continuation gain、shared κ／通道归因”的这个经验 contrast。因此可在真实资产资格后作一次预冻结试验，未资格不立刻拟合。该试验首先只能问是否有可复现的 updater-transfer gain；不是新算法认证。

**生物主张更窄：** κ 通道差异可能完全来自 measurement noise、marker persistence、量纲、起点 θ0 校准或其不确定性。需给候选和基线相同 observation model，比较 shared/channel-specific noise 与 θ0 uncertainty，不能把 swapped κ 失败单独当生物机制。若被这些解释，报告 assay/prior calibration 的普通继承，不称新的 biological update law。

## 2. Dstock 不能替代累计 K

STACK 的 Sytox Green 是 dead-object stock，live mKate2 可暂留在 dead cells，旧尸体信号可消失。trailing max 定义 LF readout，不重建死亡事件。因此不采用 Δdead 或 Δmax(dead) 构造 event D/B，不 clip 负或非整数计数差来凑 Poisson。

最小普通替代是 latent live/dead stock model：

`Ldot=(b-d)L`, `Ddot=dL-cD`，另有 marker overlap/lag 与计数噪声的 observation model。

它可预测真实读数，不保证每个 b,d,c 都被识别。方法反方给同均值反例：L=L0、D=qL0 恒定时，任意 c>0 取 b=d=cq 产生完全相同均值；例如 q=1 时 b=d=c=1 与2。若 c(t) 任意，`d=(Ddot+cD)/L`、`b=d+Ldot/L` 可配出相同轨迹。不能 numerical derivative 一算就当机制真值。

在常率、绝对计数、校准 observation noise 下，若 D/L 在观测中具有足够变化，`Ddot/L=d-c(D/L)` 可提供 d,c 识别条件，随后 b=d+Ldot/L；实际离散数据还需估计精度／posterior uncertainty。若 BESTDR likelihood 是实际实现，必须与其含 clearance／measurement／hierarchical variants 同信息比较，而非只用最弱版本。

**修订结果：** stock source 对精确 event updater 是 source incompatible，不是 biological transfer negative；保留 conventional state-space／readout forecasting。没有 K 时，“观测 reaction residual 的 dual κ 迁移”精确主张仍未测试；latent 参数 posterior 不冒充测得标签。

## 3. 一 screen 不再作为所有实验的停止条件

接受数据反方纠正：缺 independent runs 只停止 cross-run／确认性继承和 RSI 主张，不停止有边界的实际 within-screen forecasting。

可行探索：所有 wells/arms/backgrounds 的同一 compound 整组；train compounds 学共同 background-conditioned θ0 constructor 与历史 ψ；disjoint validation compounds 调 EB/search；全数锁定后 test compounds 给相同 fresh θ0、相同 prefix。比较 gain(ψ1)-gain(ψ0) 于未用 continuation，不能给 ψ1 偷看 test drug future。

compound-cluster uncertainty 仅条件于这些 screens，不代表重做实验的 biological variability。两个 background／额外 TMZ screen 不能制造足够独立 history/validation/future bioreps；反向背景测试最多两个具名方向探索。更不能把 technical wells、时间点或读数数当未来研究任务。

原独立稿 section8 的“只有一个 independent run 则停止”修订为：停止 cross-run/RSI confirmation，允许明确 conditional within-screen 的开发 gate。

## 4. 最小真实 gate 和额外 agent 的否证

source：先认证 exact count semantics、time/action/background/compound keys、单位、缺失及 acquisition unit。Root 新取得 BESTDR CSV／HTS schema 的状态独立记录；本 cross 没读任何响应。

comparison：第一阶段固定相同反馈，比较 shared/dual κ、尺度审查后的 swapped κ 诊断、普通 EB、same-space equal-budget search、strong direct prefix、kinetic/readout、simple mixture。只有数据里真实存在的 trajectory／predeclared window bundles 才能揭示，不能查询任意药物／剂量／新动作。现有 raw channel 不支持 event update 时，程序类型相应改为普通 state-space update，不假装沿用闭式。

若同信息 ordinary EB／refit／search／mixture 复现全部 gain，额外 agent/new-updater gain=NONE；若无 fixed-start future update gain，也停止 ψ 继承经验主张。source 与 conventional prefix forecast 可以保留；方法失败不要求丢弃真实功能资产。

原稿 10%／95% 仅 illustrative，尚未由实际 source variance／独立任务数／cost 校准，**不是本轮已冻结有效性能阈值**。Root 应在单独响应开启前依据真实单位冻结一个主 gate，本 cross 不越权替它定响应分析或运行实验。不能在看到 future 后挑截断／窗口；BESTDR 作者20h截断属于所有方法共享的文献暴露先验，不是我们在早期预测到了药效延迟。

## 5. 支持、反对、未决与当前决定

支持：BESTDR 等新一手资产使真实 live/dead stock 的最小功能预测更具体；同一反馈与共同 θ0 可以区分 updater inheritance 和权重携带；已知 EB 同操作不等于对应经验 contrast 已测。

反对：闭式操作普通 EB 已完整实现；实际 marker channel 不是累计 event，原物理定位在这些 source 上不成立；通道 κ 差异或许纯观测／起点误差，已知搜索可解释全部未来 gain。

未决：exact source schema 与可用 unit；真实性能与噪声模型；κ-transfer 是否有超出普通校准的经验现象；有限公开屏幕是否足以设合理开发 split。无一被记录成已执行阴性。

**共同决定：一次 source-qualified、预冻结、窄 within-screen real-data gate 可值得做；当前无新算法核心、无 agent/RSI 性能。** 若发现 ordinary EB 完整解释且没有新的经验性质，不再扩大程序空间。保留有用功能预测与更新归因结论，继续总目标但不宣布完成。
