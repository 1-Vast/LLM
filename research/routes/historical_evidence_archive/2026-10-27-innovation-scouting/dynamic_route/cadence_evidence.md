# CADENCE 可识别性条件与本地 Mix-seq 的对照（证据摘录）

用途：给 [`protocol_draft.md`](protocol_draft.md) §2 提供逐字依据，防止把"多时间快照/流匹配"当成真实路径。
来源：**CADENCE**，*Learning Individual Dynamics from Sparse Cross-Sectional Snapshots*，arXiv:2605.23470v1，<https://arxiv.org/html/2605.23470v1>。
本地副本与 hash（本轮复核）：
- `tmp/cadence_2605.23470v1.html`（519,952 B，SHA256 `8b7b07163c4588dfe7fe1b9e941b8133146501fa42b851917fcbd7ae63366a3c`）
- `tmp/cadence_2605.23470v1.txt`（88,732 B，SHA256 `fe5a576294422c85e91b6275ba565445d04fe78c6bb269a6bced906e0a5db87e`；由 HTML 去标签得到，行号稳定）
证据状态：用户报告（`research/2026-10-27-cross-domain-directions/evidence_notes.md:20`）为 P 级阅读；本轮补充 HTML 复核（P，未核证明细节与实验）。引文中的 `…` 表示省略，数学符号按抽取文本原样保留。

## A. 问题设定：无结构时不可识别

**A1｜从稀疏/横截面数据推个体轨迹本身是病态问题。** `tmp/cadence_2605.23470v1.txt:71`
> "inferring individualized, continuous-time trajectories is fundamentally ill-posed"
> "recovers continuous individual trajectories from isolated snapshots by anchoring latent dynamics to static, individual-level contexts"
（摘要，:71；同段说明只在"extremely sparse or entirely cross-sectional data"下提出。）

**A2｜没有结构假设时，能完美重建数据的模型配置是不可数无穷多（Proposition 1）。** `:123`（命题头 `:122`）
> "the set of model configurations consistent with perfect reconstruction is uncountably infinite"
（证明思路是任意光滑微分同胚可吸收空间映射、重建不变；见 :124。）

## B. 可识别性所需的结构假设（Thm 1–2 的前提）

| 编号 | 假设 | 逐字引文（行锚） | 对本地数据的含义 |
|---|---|---|---|
| DFA | Dynamical Foliation：同 context 叶的个体共享动力学参数 | "converting sparse snapshots into an effective longitudinal signal"（`:135`）；"share the same dynamical parameter"（`:134`） | 需假设同一静态 context（细胞系/状态特征）的 units 共享动力学；Mix-seq 每个条件是不同细胞群体，无法验证同参数 |
| COA | Context Observability：静态 context 足以识别每个 realization 的动力学 regime | "static context must carry enough information to identify each realization’s dynamical regime"（`:138`） | 需静态 cell-line 特征足够；Mix-seq 有 DepMap_ID 但无预注册的静态 context 面板/无验证 |
| MRA | Manifold Regularity：动力学参数空间有限维且几何正则 | "the space of dynamical parameters is finite-dimensional and geometrically regular"（`:132`） | 不能由 6h/24h 两快照验证 |
| PR | Parametric Restriction：参数属于有限维族且不同参数产生不同流 | "distinct parameters produce distinct flows"（`:573`） | 需预注册模型族；仅 2 个时间点时大量参数族都拟合边缘分布 |
| FOA | Flow Observability：不同参数产生可观测不同的时间索引推前边缘分布族 | "distinct parameters produce observationally distinct families of time-indexed pushforward marginals"（`:575`） | **本资产最弱项**：只有 2 个精确时间点（或单药 5 个固定点），"入组时间"不构成区间；见 C |

## C. FOA 的时间丰富性要求与失败模式

**C1｜时间丰富性要求入组时间跨一个区间。** `:581`
> "Enrollment times span an interval"
（前提见 :580 "Temporal richness"。）

**C2｜入组时间塌缩到单点时 FOA 失败。** `:588`
> "Enrollment times collapse to a single point, entirely eliminating temporal variation."

**C3｜即使多个时间点预测准确，也未必辨识真实路径。**（用户报告结论，`evidence_notes.md:20`；本轮未逐条重读其实验）
> 用户报告：CADENCE "结论依赖已知入组时间/静态背景、参数族及参数到时间边缘分布的注入条件。多时间快照本身不认证这些条件。"

**C4｜作者自己列出的最根本漏洞是未观测混杂（COA 被违反）。** `:396`
> "if critical information dictating the dynamical archetype is missing from the static context, COA is violated"

## D. 流匹配/插值的边界（跨文献，来自用户报告）

- **CellFlow（形态）**：用未配对终点图像做流匹配；**插值 `t` 不是物理时间**。用户报告 `evidence_notes.md:19` 引 <https://arxiv.org/html/2502.09775v1>（P 级；本轮未重读）。含义：流匹配可以生成"中间形态"，但不证明真实路径/药效恢复。
- **target-identifiability 预印本**（SSRN 7368638）：用户报告 `report.md:157` 提到其摘要涉及破坏性单细胞快照、路径目标、sharp bounds 与目标相关采样时间（A 级，全文 403 未读）。本文件只登记为"近期先例压力"，不引用其定理。

## E. 把条件映射到本地 Mix-seq（结论）

| 条件 | Mix-seq 现状 | 判定 |
|---|---|---|
| 已知/多样入组时间 | 精确时间点只有 6h 与 24h（4 药+对照）；hashed 臂有 3/6/12/24/48h（单药 Trametinib） | **部分**（单药 5 点，固定网格，不是区间采样；且 hash 赋值未重建） |
| 静态 context 可观测（COA） | 有 209 个 DepMap_ID；无预注册静态特征面板 | **需补充**（basal 表达可作候选，但须冻结） |
| 同 context 叶共享动力学（DFA） | 每个时间点都是**不同细胞群体**；无谱系/轨迹链接 | **不满足/不可验证** |
| 有限参数族（PR） | 未定义 | 设计问题，可预注册 |
| 时间丰富性/FOA | 2 个精确点；hashed 臂 5 个固定点；无连续入组时间 | **不满足**（按 C1/C2） |
| 批次/run 可观测 | 无 batch/plate/run 列；时间与 channel 混淆未排除 | **不满足** |
| 路径的独立验证 | **无功能结局** | **不满足** |

**结论**：本地数据最多支持**群体边缘分布层面的时间预测开发**；**不能**支持"恢复真实路径"或"动态信息改变具体药物决策"的因果/机制主张。若要用 CADENCE 类方法，必须先补：个体/谱系链接（或可辩护的 DFA/COA 静态面板）、更丰富的入组时间、批次/run 记录、以及独立功能结局用于验证路径（见 `protocol_draft.md` §6）。
