# R15 记录：证据登记建立；一次受限的文献核对把两条主张收窄

2026-10-27，Asia/Shanghai。继承 R1–R14，不改总目标。本轮做两件事：把 14 轮的结果压成一张状态表；按目标要求做一次 2025–2026 一手文献核对（**受限**，见 §2）。总目标保持 **ACTIVE / NOT_ACHIEVED**。

## 1．证据登记（新交付）

[research/EVIDENCE_REGISTER.md](../EVIDENCE_REGISTER.md)：7 条资源事实（F1–F7）、13 条主张（C1–C13）、5 条已停线与重开条件、5 条不可声称事项。状态严格分五档：已核实 / 探索性 / 已否证 / 已停止 / 不可检验。所有数值已逐条对本轮之前的 JSON 复核（18/18 通过）。

用途：后续轮次直接引用它判定"这条线能不能再开"，避免重开已停的线；也防止把探索性数值写成已确认能力。

## 2．文献核对：**受限**，只能做到片段级

**访问限制**：本环境的 `web_fetch` 对所有域名都返回"解析到非公网 IP"，包括 `icml.cc`、`www.ebi.ac.uk`（Europe PMC REST）。因此本轮**无法打开任何一手正文**，只用 `web_search` 拿到标题/片段。按技能规则，这只能算**片段级**，**不能**据此断言"无人做过"。

四个定向查询（2026-10-27，DSH web_search）：药物组合协同是否跨细胞系保守 / 药物反应的 conformal 预测 / GP 与简单基线用于剂量-反应面 / EI 在常方差下是否退化为利用。

片段层面确认存在（**均未读正文**）：

| 主题 | 片段证据 | 对我们的含义 |
|---|---|---|
| 药物反应的 **conformal** 预测 | [ConfPert: Distribution-Free Conformal Coverage for Single-Cell Perturbation Predictors](https://icml.cc/virtual/2026/72123)（ICML 2026）；[Conformal prediction of molecule-induced cancer cell growth inhibition challenged by strong distribution shifts](https://www.sciencedirect.com/science/article/pii/S0031320325011641)（Pattern Recognition） | **R12 必须收窄**（见 §3） |
| 跨细胞系协同可预测性 | [npj 2024 图 2：跨细胞系 Pearson 相关（NCI-ALMANAC 60 系 / O'Neil 39 系）](https://www.nature.com/articles/s44386-024-00004-z/figures/2) | 我们的 C12（交互 ρ=0.353）**很可能是在重新推导已知结构**，不能当新发现 |
| 组合贝叶斯优化的**结构化核** | [Savitar: Pharmacology-Aware CP-Tensor Kernel Beats Domain-Specific Baselines in Drug-Combination Bayesian Optimization](https://icml.cc/virtual/2026/71701)（ICML 2026）；另见其[curve-aware 版本](https://ICML.cc/virtual/2026/74340) | 我们的 C9（通用 RBF-GP 输给均值）**不能**说成"GP 不行"，只能说"未加结构的 GP 不行"——与领域方向一致 |
| GP 用于协同面 | 一个组会报告 *Modelling Cancer Drug Synergy Surfaces with Gaussian Processes*（片段级，非论文） | 同上 |
| EI ≡ 利用（常方差） | 只找到教科书式讨论（如 MIT 学位论文中的采集函数章节），**没有** 2025–26 专门文献 | 这是**标准事实**，不应写成我们的发现 |

## 3．由此产生的两条收窄（本轮的实质产出）

**收窄 1（R12）**：R12 的原表述是"无法事先判断单次预测是否可信"。正确表述应为：**"我们手搭的 6 特征 logistic 可信度模型失败（AUC 0.477）"**。conformal / 分布无关覆盖在 2025–26 已是活跃方向（片段已确认存在），我们**没有测**。所以"可信度不可预判"是**过度概括**，须撤回到"该模型失败"。

**收窄 2（C9）**：R11 的"GP 不如跨细胞均值"只能限定为**通用 RBF 核、固定两维 log 剂量坐标**这一配置。2026 年已有工作用**药理感知的结构化核**在组合 BO 上宣称击败领域基线（片段级）。我们不能据此说"GP 方法不行"，只能说"我们那一种 GP 不行"。

另外两条**降级为已知/标准**、不再作为本研究的新发现陈述：
- EI 在常方差下与利用同序（R9 的 `ei_gap_by_k = 0`）——标准 BO 事实。
- 交互跨细胞部分保守（C12）——活跃领域里已有的结构，需要一手核对才能判断我们是否只做了复现；在核对前按"探索性、可能为复现"对待。

## 4．这一轮没有做的

- 没有新实验、没有新数据、没有下载。
- 没有完成"一手"核对——这是硬限制，不是选择。下一次若环境允许访问一手正文，应优先核对：C12 是否只是复现、conformal 在我们任务上的覆盖-风险曲线、Savitar 类核在我们数据上的表现。

## 5．下一门（未冻结、未运行，按收窄后的表述）

**用 conformal 替代手搭可信度模型**：在我们的留一细胞任务上给出覆盖-风险曲线，检验"给定置信水平下的实际命中率"是否达到名义水平。这是 R12 的直接修正版，且是 2025–26 的标准做法。若 conformal 也失败，才可以恢复"该任务上可信度不可预判"的表述。

## 6．预算、边界

- 0 次付费 LLM 调用；0 次下载；无新湿实验。两个文献子代理在本轮启动后失败（无输出），故改由协调者用 `web_search` 直接做片段级核对——这一限制已写在 §2，不冒充一手核对。
- 未改 `src/`、`tools/`、旧报告、sealed；未晋升代码；除 `EVIDENCE_REGISTER.md` 与 `research/INDEX.md` 外未改其他文件。
