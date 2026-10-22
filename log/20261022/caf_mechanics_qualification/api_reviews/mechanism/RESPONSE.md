独立首评（未使用其他角色观点）。本包未授权拟合或开新 assay；以下只作可证伪的预注册候选，不声称已有性能。

## 一、探索与筛选

我先排除三类：CAF2026 的 cubic hysteresis/空间 transport 无全文与 raw traces，且上轮已被修正；TG-GATEs 的 source-state 失败说明“继承特征”不能直接归因；普通 latent-state/neuralODE/low-rank/EVSI 不满足“具体结构规则”。可用的最干净资产仍是 Joy et al. 2023（PNAS doi:10.1073/pnas.2311995120；PMC10756289；Zenodo record 8385319）。它明确同时触及机械/结构状态与功能恢复：作者报告 washout 后 firing 在 24–48 h 恢复，而 vesicle clustering 未完全恢复，且 3D force 与 2D MEA 并非同一样本。现有 workbooks 只有表头/ZIP schema 合格，数值未 cast，不能拟合；但这足以提出一个“状态恢复≠功能恢复”的最小机制。

## 二、唯一候选：活动门控的功能储备再充填（AGFR）

令 \(M(t)\in[0,1]\) 为可测的结构/机械容许度（force 或 vesicle clustering 的代理，不是功能真值），\(u(t)\ge0\) 为药物暴露，\(y(t)\) 为功能输出（firing/burst 或收缩功能），\(R(t)\) 为功能储备：

\[
y=y_{\max}\,R\,\sigma\!\left(\frac{M-M_c}{s}\right)
\]

\[
\dot M=k_M\big(M_{\rm eq}(u)-M\big)
\]

\[
\dot R=(r_0+r_1 y)(1-R)-q\,u\,R,\qquad R\in[0,1].
\]

操作上，按观测到的干预区间分段积分；每次干预后只更新 \((M_c,s,k_M,r_0,r_1,q)\)，并与 \(r_1=0\) 的普通储备模型作嵌套比较。关键结构不是“多一个 latent”，而是两条可证伪约束：**功能储备的再充填率是当前已实现功能的函数，而不是 washout 时间或结构状态的函数；功能输出又被结构容许阈值乘性门控。** 因此可出现两种分离：\(M\) 恢复但 \(R\) 仍低→功能不恢复；\(M\) 仅过许可阈值、但 \(R\) 被活动重新充填→功能恢复而结构未完全恢复。

最接近的普通机制是 readily releasable pool 的耗竭/固定速率再充填、homeostatic plasticity，以及平滑恢复的 latent state-space。作者自己的 local reserve 解释属于普通生物学假说，不是本候选的新颖性；本候选只把“活动依赖的再充填 + 结构许可阈值”作为可单独否证的更新规则。若 \(r_1=0\)，它就退回普通储备模型，候选失败。

药物发现应用应限定为**功能恢复型洗脱/给药日程筛选**：预测哪些 washout/adjuvant 日程能在结构未完全正常化时恢复功能，并用早期残余活动作为再充填生物标志；不声称 CAF 疗效或临床反应。

## 三、普通解释与决定性证伪

普通解释包括：RRP 耗竭与固定再充填、活动依赖稳态可塑性、药物组织结合导致的缓慢 washout、2D 功能与 3D 力不是同一样本、仅存活样本被测量、 assay 灵敏度差异。它们都能产生“结构未恢复但功能恢复”的表观现象。

决定性证伪不是再看相关性，而是干预活动窗口：在 washout 恢复期对活动作可逆分级钳制/扰动，若 24–48 h 功能恢复不随活动改变，且 \(r_1\approx0\)，停止。第二个证伪是交叉顺序：先恢复结构再给药物、与先 washout 再恢复结构，若功能只由当前 \(M\) 和 time-since-washout 决定，AGFR 无增益。负控制必须是真正打断“活动→R 再充填”的信号：在保持基线 firing、处理组和边缘分布的前提下，将 washout 期活动标签跨 well 置换，或用时间错位 \(y\) 反馈；不能只用 ID 重命名或保持 nuisance 的普通 permutation。

## 四、数据缺口与最廉价判别

现有 Joy 数据不能识别该机制：Fig3d 只有一个 force history，Fig3b 是发育时间点；Fig5a/b 虽为同一 MEA 图的 before/1 h/24 h/48 h 列，但仅 4 个 sample、共同处理序列；Fig6h 行匿名，culture/synapse 分组未认证；无 raw firing trajectories，也无恢复期活动操纵；3D force 与 2D MEA 不能按“Sample1”配对。CAF2026 无全文/traces；GSE229742 表达也未与机械/FRAP 配对。故当前不能做历史 vs 混杂的判别。

最廉价第一步**不开新 assay**：核验 Zenodo 8385319 中 Fig5a/b、Fig6h 的 row/sample/run 映射与处理区间，确认 before/after 列是否同 well 配对、匿名行能否与 force/处理关联。若可配对，做 within-sample 检验：1 h 残余活动是否在控制基线后预测 24/48 h 恢复；并拟合 AGFR 对 \(r_1=0\)、结构-only、time-since-washout、additive latent。若映射不可认证，结论只能是“源数据不足”，不得拟合或宣称机制。真正决定性的活动钳制实验需另授权；本包不开启。

## 五、成功/停止条件

成功需同时满足：① row/sample/run 映射与处理区间可认证；② 在 leave-one-schedule-out 或至少两个 washout 日程上，AGFR 对功能恢复的预测和日程排序优于同信息结构-only、time-since-washout、additive latent 与 \(r_1=0\)；③ 活动置换负控制下增益消失，而原始活动下保留；④ 等数据/等预算比较，不能只靠额外参数或 source features。有用增益阈值应以“节省一次额外 washout arm 的实验成本”定义；成本未定时不写数字，不用 p 值代替。

停止条件：无认证配对/区间；\(r_1\) 不优于 0；活动扰动不改变恢复；当前结构状态或 time-since-washout 已等效；增益仅来自继承特征/额外参数；日程排序不优于固定日程；无法构造同信息普通基线。候选允许失败。

## 六、归因边界

- **world**：只归因于 \(M,R,y\) 方程本身。必须在 held-out 干预日程上击败同信息 world-free/结构-only，并做 source-feature ablation；不能拿 CAF/RNA 的未配对相关当证据。
- **agent**：冻结 world 后，只比较“选择活动窗口/交叉顺序实验”的策略与随机、网格、普通 EVSI 的每 assay 决策 regret。无真实决策端点则不归因。
- **继承**：旧/新从共同起点、同预算；继承参数或源特征须胜过无继承与打乱源特征，并通过 same-data refit。既往 TG source-state 变差提示默认不归因。
- **联合**：做 world on/off × agent on/off 的 2×2；只有交互项改善真实功能恢复/每 assay，才叫 joint。不是 counts+location，也不是两个主效应相加。
- **C4**：旧/新 improver 共同起点、同算力/数据、真实闭环反馈；只有 AGFR 使 improver 的下一轮提议优于同预算普通循环才算。当前静态数据不能支持 C4，故不声称。