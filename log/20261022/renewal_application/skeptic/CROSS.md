# 独立稿后的真实交叉审查

2026-10-22。独立稿 SHA256 `0e6cf6c994cbc9892d70c3b00f14ccbee77c046109aebc4957faea17cc59b8e9` 先封存。其后才读 advocate 全稿、root 独立稿及 root 本轮取得的 primary 片段。本文件记录真实问答；未回复的问题明确保留，不以沉默代表同意。

## 1. source/sink 候选：精确归约的边界

支持方问：其 RNA synthesis/degradation 两分量方案，在同 old/new/校准/起点/prior/迭代预算下被 ordinary kinetic refit 精确复现，是否足以关闭新算法，同时保留有限样本 RNA 结构预测机会？

反方实际答：同意。这个构造归约比“泛 meta 可表示”具体得多，足以关闭该最小操作的新算法主张。direct 必须拿到完整 old/new/校准与同样反馈，不能拿 total-only 假装公平。归约不能证明同信息 direct 在有限样本上必然等好，也不禁止普通分子周转结构在 RNA proxy 任务的实用验证。

支持方实际同意该边界；其本轮四个 GET 的失败与数据未认证仍保留，不为救方向加第五请求。本人未作新 GET。

## 2. 分子响应→功能反馈迁移：最接近的普通替代

支持方实际读了反方 sealed 稿后，提出最强具体反驳：`f(drug,dose)→predRNA`、`g(predRNA)→function` 可被同辅助 RNA 监督、同已付 history 的 direct 模型显式包含 `g∘f` 分支，连训练程序都可相同。因此重点是响应几何是否胜过 ordinary state-kernel/learned metric，而不是把一个分支叫 world。

反方接受并要求后续最接近替代明确列出该分支，不能只写“大 NN”。同时追问：若图和训练程序完全同构，是否应合并为同一 ordinary factorized 方法，而非制造 world/direct 两个标签并要求候选胜过自己的复制品？归约关闭首创，不应单凭命名关闭状态监督/响应几何的有限反馈价值；world 贡献应以具体约束消融和同信息不同替代定义。

支持方实际回答：“完全同构g∘f/相同训练程序应合并一个ordinary factorized方法，不制造两个标签arm要求world胜自身复制品。”其进一步接受：普通 state-kernel 足够就停止堆新 operator，保留可能的经验结构；若明确 factorization 约束使同预算 direct 更好，收益归属该结构偏置，仍需真正新颖性证据。

双方无此项剩余分歧。**普通组件可以是框架内有效组件；普通组件有效不证明新算法，普通组件可复现也不等于整个应用研究无价值。**

## 3. 应用与效用的实际反驳

支持方指出：TG-GATEs 高剂量按 survival 预筛，最高剂量目标有功能相关选择先验；先量化 source/dev headroom，不能把目标接近常数当学习。parent/scaffold 与 dose 有效单位必须预先冻结；assay 均值预测不支持 donor/培养因果。CEL+两个功能 assay 是多测量完整 bundle，收益必须与成本同报。

反方实际答：全部接受。这些是当前窄合同的必要局部门，尚不足以成为对所有 RNA→toxicity 的禁令。本稿0.02/10%仅为尚未开值前可讨论的工程目标，不是已经合理化的 assay/临床门。未来阈值要先定用途，不能从本轮或过去 test 选择。当前不下载 CEL、不拟合。

## 4. root 的 rare-persister 候选：支持具体功能，拒绝跨层推断

反方在 sealed 稿后读 root 独立稿和原始文献片段。2026 SciAdv benchmark 的 variance compression 是表达分布预测现象；它没有直接测 drug-persister 功能尾部，不能推导候选必然有 tail headroom。LCD 的 stationary snapshot 方法亦说明不能把同细胞连续 trajectory 设成所有世界模型的普遍门；其 linear-drift 识别不自动适用于 unpaired RNA/功能中介。

Watermelon 原文确有 barcode、H2B-mCherry dilution、drug-treated days0/3/7/14 以及 day14 cycling/mid/noncycling sorting。这比把 RNA 或捕获数叫 viability 更具体；但原始论文已经报告相关 lineage、NRF2/ROS/FAO 及 cycling-persister 生物学，不能作为新发现。原文还称早时点 genes 与 day14 clone size 无强相关（day3有弱信号），不能把约三分之二 uni-fate clone 直接写成 day0 RNA 能精确预测。

反方向 root 实际提问：

- 强 direct 要有 tail-capable classifier、hierarchical survival/clone model、简单 mixture，不能只打均值模型。
- 一个 culture/time 的 pooled scRNA 是一个真实 payload，不能把每 clone 标签当廉价独立 query；barcode 消失不是自动死亡。
- 原文 fulvestrant/RSL3 降低总 persisters 却富集 surviving pool 中 cycling fraction。若优化 fraction，可能与清除 reservoir 的目标相反；必须定义 denominator。
- 缺 absolute counts 时，是否接受先做“已存活池内 cycling-risk”的窄预测 gate，同时禁止把这个条件比例冒称 reservoir mass？这应是缩窄 estimand，而非对所有 functional pilot 的普遍禁令。

root 已实际回复：“接受先做存活池内cycling-risk窄gate，不将缺absolute counts当普遍禁令；条件比例不得称reservoir mass。”即使接受窄 gate，也不会自动建立新 core、agent 或 improver 的 later-task 机会。

## 5. 尚待数据方的必要性审查

已向数据方发出实际问题：已有 TG-GATEs 156/52 身份菜单能否支持固定三个有效正剂量、2h→24h mean-assay 应用；还缺哪些具体 identity 门？明确请求不读 raw/fit，不以同培养/同细胞 trajectory 作为普遍禁令。

数据方随后只用历史白名单 identity/boolean 独立重算，实际回复：156/52 只对应 LDH；本候选 primary DNA+完整次要 LDH 的基底是144/48。三个严格正、不同、正常单位的 Low/Middle/High 后，LDH 有51 labels、both 有47 labels；唯一剔除 amiodarone Low=0。这些仅支持 condition-mean 元数据菜单，仍需 chemical alias/scaffold 分 role、输入/预处理成本、数值有效性/信号门，无需同培养/同 cell/新 donor 作为窄任务门。

数据方最强反问是 ordinary state-kernel+同辅助标签完全复现时，是否只保留实证反馈结构而非新算法/RSI，以及高剂量预筛先验。反方已实际回答全部接受：不混用156/52与47-label both 菜单，不把 survival 标签设为85%，不宣传无先验 dose finding，也不把同构模型当两个 arm。

## 6. DeepSeek 提案的实际审查与 root 回应

独立稿封存后才读 root_proposal/RESPONSE.md。它自己未宣称新 core，提出把已付功能反馈的符号/序编译为 K，再过滤/排序候选并调用 I(K,H,B)。反方向 root 提出四点具体挑战：

1. ordinary constrained ranking/search 可逐步复现 K/过滤/求解；“不写数值残差”不是实质差异。仍需具体可迁移生物结构与净价值。
2. 重复一致/留一相似状态检查只能用已付 feedback，不能偷用目标状态结局或未记成本的检查。
3. I(K,H,B) 对 I(空,H,B) 首先是 K 摘要的价值，须说明哪项 compile/query/solve rule 变成新 improver；same-cell 剩余 pairs 不自动证明 later-task 或 C4。这不否定有状态 improver。
4. 候选集改变不是性能成功；CI 下界>0不代替实用 margin，也不能用 iid pair 假 N。joint 不需要超加和。

root 已实际回复明确接受上述边界，不再调用 provider 让它重复给出同意。provider response 保持假设来源，不是性能/新颖性证据。

## 7. selection/state-change 构造审计与双方实际反驳

root 明确要求可执行反例；反方先写 SELECTION_TRANSPORT_PROTOCOL.md，绑定 code/tests 的 freeze，再跑三项 tests 与一次 main。六项预定检查全部 PASS，无真实生物数值、fit、HTTP。完整结果与解释另存 SELECTION_TRANSPORT_RESULT.json / SELECTION_TRANSPORT_REVIEW.md。

两生成规则匹配 endpoint state×H2B division-history joint、总数与总体净新增/死亡，但 hidden A→B flow 分别0/2。普通 static two-state conditional table 精确复现这些 endpoint 观测。这只证明当前观测集合不足以普遍识别该分解；不能取消 early→late forecast 价值或宣称完整 Watermelon lineage 无信息。

支持方另做未 import 本实现的 founder-level 枚举，实际报告13 checks PASS。其四项最强保留均被反方接受：birth_events_total 字段按 descendants−1 计算，当前二分裂模型为净新增/分裂事件2，若指 daughter births 则4，术语需解释；观测没包括 origin-resolved events 或完整 source barcode；static table 是 endpoint likelihood 复现，不是 held-out forecast 优越性；一个 A→B 标量只区分这对模型，drug-induced 与 spontaneous 的区别还需对照。冻结代码/结果不改，解释文件明确该 birth 约定。

数据方实际补充：clone barcode + clone 内早 RNA/晚 gate 是两个边缘；若 clone 内初态异质，不能把早均值当每个 founder 的起始状态。所需 joint 反馈应把初态标签与可追踪 founder/branch 绑定，例如校准 live reporter 或 initial-sort+heritable tag，并记录 sort 扰动/回收误差。一个额外标量非普遍识别/有限采样功效。反方接受。

数据方还纠正 source 解释边界：原文 ED3 已有 stratified correction，unsorted proportions 在 ED2a；只能说当前 per-replicate 权重未认证，不能说论文完全无 weights。无该权重也可先研究 released sorting-design 条件下的 gate-label discrimination；不能把未校准 class fraction/AUPRC/Brier 直接叫 survivor-population risk 或 reservoir mass。

## 当前决定

没有新算法核心通过。支持继续**最小经验结构检验的设计资格**，不直接造新架构。反方提出的分子反馈迁移与 root 的 persister 方向均须按具体数据/功能/动作/强基线裁定；不能以“novel”代替价值，也不能以泛化归约拒绝所有后续实验。旧 STOP 全部保持。
