# R201-P 先例/边界核验：机制 A（跨计划一致反事实细胞模型）与方向 2（计算/实验双预算）

2026-10-28。角色：定向核验员（lit-verifier）· task-104。**只读、不运行效果、不声称新颖性。**
检索预算：**2 个 pass（PASS1 6 条 / PASS2 4 条，合并查询；原始 JSON 在 `D:\MAESTRO\tmp\r201p/`）**；本地一手全文阅读不计 pass。零命中只记录为检索结果，不写"不存在"。
本地一手材料：`research/2026-10-27-agent-cell-colearning/sources/challenger/` 下 CoMap(2606.02372)、LAWM(2512.10016v1)、MDA(2608.09696)、COPEx(guo26g, ICML2026)、OPINE-World(2607.01531)、HIJP(2610.23615v1)、CoLA(2510.26433)、VCWorld(2512.00306)、BOR(icaps16-dolatnia) 的提取文本；R189 已核的 GoBOED(2605.26093)/决策聚焦序贯设计(2602.05340) 全文在 `../2026-10-27-detectability-acquisition/sources/extracts/`。引文均逐字回查（脚本 `tmp/r201p_verify_quotes.py`），≤40 词。

## 0. 结论摘要（逐项覆盖判定）

| 待争取的对象 | 判定 | 最近覆盖者（证据见 §1–§3） |
|---|---|---|
| 模型+策略共同更新 | **已覆盖** | CoMap（闭环 policy↔world model + 特权教师自蒸馏）；CoLA/LAWM/HIJP 联合动作-状态-动力学 |
| 动作/状态/动力学/真实动作解码器联合学习 | **已覆盖** | LAWM（latent action + IDM + action decoder）；CoLA（IDM+world model 共演化）；HIJP（inverse+latent predictor 一致性） |
| 任务摘要/模型发现/机制池/VoI | **已覆盖** | MDA（结构-参数后验、M-open 扩张、query-sufficient 摘要、VoI 选实验） |
| 动态约束/预算下的非短视实验设计 | **已覆盖** | COPEx（constraint state 含剩余预算、scenario-tree lookahead）；BOR（资源/生产 POMDP） |
| 反例/预测检查触发模型修订 | **已覆盖** | OPINE-World（CEGIS 反例驱动重写）；MDA（M-open 预测检查→扩张） |
| 多实验共享同一干预算子的“一致性”本身 | **部分覆盖（数学上被普通联合拟合覆盖）** | 多实验系统辨识/共享参数后验/层级模型已保持一致性（control_scout L36；PASS2-Q3 21 条） |
| “计划对联合不可行（各自合法、联合不可能）”作为**主动选择信号**，反馈统一修订 | **未发现（已核范围内）** | 数学形式=IIS/MCS+set-membership（conflict_signal/prior_art L78；set-membership OED 生物先例 2012）；计划对联合不可行的显式学习/决策目标未在已核条目发现 |
| 选实验区分竞争模型（计划对分歧→买实验） | **已覆盖（经典 OED）** | 模型判别实验设计 127 条题录（1978 review、2008 sequential；PASS2-Q1）；与“计划对”语义不同但动作选择部分覆盖 |
| 计算预算 vs 实验预算**联合分配**并评估独立决策收益 | **部分覆盖** | 单侧已有：MDA 以 MI/compute 选观测模型、HIJP 搜索自由规划、compute-efficient BED、多保真 OED；decision-focused BOED/VOI 管实验预算；**同一账本联合分配未在已核范围发现**（PASS2-Q2 字面查询 0 命中，仅记录检索结果） |
| 决策聚焦 acquisition（下游决策价值） | **已覆盖** | GoBOED、决策聚焦序贯设计、EVSI/ENBS（R189 已核） |

**总体意见**：一般概念（共同更新、联合学习、模型发现、约束/预算实验设计、计算效率、决策聚焦）**均已被覆盖**。R201 若保留机制 A/方向 2，新意只能落到**具体共享对象与更新运算**：即“多个计划必须由同一干预算子产生”的**联合可行性证书**、以及“计算误差认证 vs 真实实验购买”的**同一预算账本**；否则应按 BRIEF 纪律**收窄为评估修正或停，不换名重启**。

---

## 1. 四个用户引用工作：设定 / 共享对象 / 更新运算 / 两问覆盖

### 1.1 CoMap（arXiv 2606.02372v1，LLM agents）

- 设定：POMDP 中的文本世界模型 `W_φ(s_{t+1}|s_t,a_t)` + agent policy；跨 embodied planning/web/tool-use benchmark。
- **共享对象**：文本 world model 与 policy（同一 backbone/教师-学生）；**更新运算**：闭环——policy 用未来反馈反思，on-policy 轨迹用特权教师（可见真实下一状态）做自蒸馏更新 world model。
- 引文（≤40 词）："The resulting on-policy trajectories are then used to update the world model via self-distillation"（`sources/challenger/arxiv-2606.02372-extracted.txt` L6；另 "co-evolves textual world models and agent policies through closed-loop interaction" 同文件 L5–6）。
- 计划/反事实一致性：**未发现**（policy-model 闭环 ≠ 多个计划共享同一算子；papers 的 consistency 是 policy 反思与 model 预测的一致性，不是跨计划联合可行性）。双预算：**未发现**——只有推理成本注记："Second, CoMap requires an additional world-model call at inference time before future-aware reflection."（同文件 L303），无计算/实验预算分配。
- 不能支持什么：其特权教师可见真实完整下一状态；细胞破坏性读出没有免费同状态恢复，不能直接迁移（与 `../2026-10-27-agent-cell-colearning/evidence_notes.md` L11 记录一致）。

### 1.2 LAWM（arXiv 2512.10016v1，离线 RL）

- 设定：离线 RL，带少量 action-labeled + 大量 action-free 轨迹；DMC 控制任务。
- **共享对象**：latent action `u` + latent state `s` + 动力学 + 真实动作 decoder；**更新运算**：混合数据联合训练，有标签用后验 `q(u|s,a)`，无标签用 inverse dynamics `q(u|s,o_{t+1})` 推断潜动作。
- 引文："We introduce a family of latent-action world models that jointly use action-conditioned and action-free data"（同目录 `arxiv-2512.10016v1-extracted.txt` L3；另 "inferring latent actions via inverse dynamics when they are not" 同文件 L13）。
- 计划/反事实一致性：**未发现**；双预算：**未发现**（成本只体现于数据需求/采样效率，无计算 vs 实验预算）。
- 不能支持什么：状态/动作/动力学/decoder 联合学习本身已有；不能据此主张"共同学习"新意（与 `report.md` L23 的内部分析一致）。

### 1.3 MDA（arXiv 2608.09696v1，机制发现 + Bayesian 实验设计）

- 设定：从少量干预发现机械世界模型（M-open：真机制可能不在当前模型池）。
- **共享对象**：模型结构+参数后验（SMC 粒子池）+ LLM 提议器 + VoI 设计；**更新运算**：SMC 后验更新、预测检查失败→LLM 扩张结构、VoI 选下一实验；观测侧 query-sufficient 摘要 `s_φ(y)`，并用 **MI/cost** 选择观测模型（PF vs 合成似然）。
- 引文："Experiments are expensive, so the central problem is data efficiency"（同目录 `arxiv-2608.09696-extracted.txt` L7）；"cheap summary and pays for the filter only where its discrimination clearly justifies the compute."（同文件 L815）；"expansion end-to-end we leave to future work."（同文件 L800）。
- 计划一致性：**未发现**；双预算：**部分覆盖**——Eq.11 以 `MI_o/cost(o)` 在观测模型间选择，cost 明确是计算成本（PF 轨迹数 vs 合成似然模拟数；L811–815 区域），但**未与实验预算 B 联合分配、未以独立决策收益评估**；实验预算只是给定的 B 轮交互（同文件 L131："The agent is then given a budget of"，行锚为准）。
- 不能支持什么：任务摘要/机制后验/VoI/模型池扩张均已有；"端到端摘要与机制共训"作者明确留作未来工作（L800）——不能把"共同学习"写成已实现。

### 1.4 COPEx（ICML 2026，Constrained Bayesian Experimental Design via Online Planning）

- 设定：带动态代价/预算/可行性约束的 BED；**共享对象**：constraint state `z_t`（含上一设计、物理状态、**剩余预算**）+ 后验网络 + 摊销设计策略；**更新运算**：scenario-tree 多步 lookahead 规划，约束状态转移 `z_{t+1}=f(z_t,x_t)`，每步实验成本 `c(x,z)` 计入预算。
- 引文："Budget constraints couple decisions across time"（同目录 `guo26g-extracted.txt` L397）；"only a modest additional computational overhead."（同文件 L21）；"or the remaining budget."（同文件 L349，说明 constraint state 含预算）。
- 计划一致性：**未发现**（无“多计划共享算子/联合不可行”对象）；双预算：**部分覆盖**——实验预算/成本已进约束状态与规划；规划计算只是开销（"modest additional computational overhead"），**不是与实验预算联合分配的决策变量**。
- 不能支持什么：动态约束/预算/非短视实验设计已有；且其 related work 已把 **cost-aware BO/AL** 与 **decision-focused objectives** 列为已有线（同文件 L203–221、L182–183），不能把"成本敏感/决策聚焦"当新意。

---

## 2. 计划一致性 / 共同算子 / 约束生成 / 联合矛盾

### 2.1 已有先例覆盖的组成部分

| 组成 | 已核先例/证据 | 覆盖判定 |
|---|---|---|
| 跨实例共享同一规则（shared operator） | OPINE-World："one transition rule shared across all objects of a type"（`sources/challenger/arxiv-2607.01531-extracted.txt` L7） | **已覆盖（规则共享机制）** |
| 反例/矛盾触发模型修订 | OPINE："when the current model has been contradicted, rewrites the object-centric program so that it again reproduces every recorded transition"（同文件 L51）；"A candidate program is admitted only when it reproduces every recorded transition exactly."（L11）；MDA M-open 预测检查→扩张（MDA L7/L800 区域） | **已覆盖（反例→修订环）** |
| 选实验区分竞争模型 | 模型判别实验设计：PASS2-Q1 **127 题录**（1978 review、2008 sequential/optimal；top 例：*Optimal experimental design for model discrimination*, DOI 10.1037/a0016104） | **已覆盖（动作选择部分）** |
| 集合成员/部分识别 + 实验设计 | PASS1-Q6 **9 题录**，题名逐字："Set membership experimental design for biological systems"（DOI 10.1186/1752-0509-6-21；`tmp/r201p/p1_openalex_P1_q6_set_membership_design.json`；摘要反索引重建后要点=为生物系统有限实验资源做实验设计，摘要级不作全文引文）；本地 A2 先例记录：IIS/MCS 是标准运筹/统计工具（`../2026-10-27-innovation-scouting/conflict_signal/prior_art.md` L78） | **已覆盖（数学形式）** |
| 多实验共享参数/系统辨识 | PASS2-Q3 **21 题录**，含 *Hybrid System Identification through Optimization and Active Learning*（DOI 10.1016/j.ifacol.2024.07.430）、*A software package for system identification in the behavioral setting*（DOI 10.1016/j.conengprac.2013.06.010）；本地记录："全历史重训的贝叶斯模型若每条rollout共享同一后验参数，也已经保留上述一致性"（`control_scout.md` L36） | **已覆盖（普通共享参数/多实验联合拟合）** |
| 约束生成/部分识别/目标导向设计/代理学习 | 本地先例记录：`challenge_sources.md` L45 "对固定声明族" 起的覆盖分析（set-membership 相容集、鲁棒/部分识别、约束生成、目标导向设计、代理学习）；`report.md` L55 "普通非矩形控制、矩/SOS、约束生成和计算决策已覆盖一般原则" | **已覆盖（数学/方法论层）** |

### 2.2 “计划对分歧→选实验→统一修订”闭环

- **部分覆盖**：动作选择（选实验区分模型）有经典 OED；修订环有 OPINE/MDA（反例/预测检查）；模型池/使用 VoI 有 MDA；约束/预算多步规划有 COPEx。
- **未发现（已核范围内）**：把“**多个计划必须由同一干预算子产生**、且存在‘各计划单独合法、联合不可行’（joint contradiction）”作为**显式学习/决策对象**，用计划对分歧选出真实实验、再统一修订该算子——并以未测计划的独立决策收益评价。检索侧证据：PASS1-Q1 "plan consistency" 225 条题名/摘要命中以城市规划、调度、报告生成一致性为主；PASS1-Q2 "plan-consistent" 811 条以物流/排产/护理计划为主；PASS2-Q4 counterfactual×planning×consistency 77 条以 NLP/因果解释/临床决策为主——**均未见“共享干预算子联合可行性”语义**（题名/摘要级，非穷尽）。
- 不能据此写"无人做过"：只写"本任务 2 个 pass 的题录/摘要级检索未发现直接匹配；本地一手全文也未覆盖组合"。

### 2.3 与普通共享参数/层级/约束生成/多任务学习的差异

- **普通共享参数/层级/多任务**：若每条轨迹/计划共享同一参数后验，跨计划一致性**已被普通联合贝叶斯拟合保持**（`control_scout.md` L36；多实验系统辨识 PASS2-Q3 21 条）。因此"共享算子"本身不新；差异必须在**算子类的非矩形/部分识别结构**、**联合不可行的显式证书**、**计划差作为主动查询**、以及**计算/实验记账**四项之一/之几，而不是"加一个共享层/loss"。
- **约束生成**：把 oracle 返回的见证/切面加入约束是列/约束生成（`report.md` L55；`challenge_sources.md` L45 区域），数学上已覆盖；新意只能落在“**联合不可行性**的检测/诊断/实验选择”这一用途，且要证明相对普通 set-membership + 联合拟合有增量。
- **多任务/共享表示**：一般共享表示学习是已知；本任务未见"计划对联合可行性"作为任务定义的工作（同上检索限制）。
- **结论**：若机制 A 只做到"共享参数/联合拟合 + 标准约束生成 + 选实验区分模型"，则已被覆盖 → 应按 BRIEF §纪律**收窄为评估修正或停**；只有把"计划对联合不可行"与“共同算子修订”做成可检验的**更新运算与决策收益**，才可能保留科学问题（仍需实验证明）。

---

## 3. 计算预算 vs 实验预算

### 3.1 已覆盖的单侧先例

| 线 | 已核证据 | 覆盖的点 | 未覆盖的点 |
|---|---|---|---|
| 决策聚焦 AL/BOED | GoBOED："enabling gradient-based design optimization that is fully decision-focused"（`../2026-10-27-detectability-acquisition/sources/extracts/arxiv-2605.26093_sentences.txt` L26）；"When experiments are expensive, time-consuming, or carry safety risks, it is critical to extract as much useful information as possible from each experiment."（同文件 L29）；决策聚焦序贯设计："we demonstrate that our directional uncertainty–based design attains an earlier stopping time than decision-blind designs"（`arxiv-2602.05340_sentences.txt` L13）；EVSI/ENBS（R189 PASS2 题录 477 条，含 *Expected value of sample information to guide the design of group sequential clinical trials*，见 `../2026-10-27-detectability-acquisition/sources/queries/pass2_epmc_P2-q1_EVSI_sample_size.json`） | 按下游决策价值分配**实验/样本预算**与停止 | 计算预算不作为可分配项（只作 wall-clock/实现开销） |
| COPEx | 实验成本进 constraint state：预算 `z_t`（`guo26g-extracted.txt` L397、L349）；规划计算只"modest additional computational overhead"（L21） | 动态实验预算 + 非短视规划 | 计算 vs 实验**联合**分配；规划 compute 不进入与实验同一决策账本 |
| 成本敏感 AL/BO | COPEx related work 已列 cost-aware BO/AL（`guo26g-extracted.txt` L203–221 区域：acquisition 修改、cost-cooling、hard budget、Pandora's box 等） | 单次评估/实验成本进 acquisition | 计算成本作为与实验并列的预算项 |
| MDA（计算感知） | `MI_o/cost(o)` 选观测模型，"cheap summary and pays for the filter only where its discrimination clearly justifies the compute."（`arxiv-2608.09696-extracted.txt` L815） | **计算成本 vs 信息**的局部权衡 | 与实验预算联合；独立决策收益 |
| HIJP（计算效率） | "planning with these models typically requires costly test-time optimization over action sequences"（`arxiv-2610.23615v1-extracted.txt` L3）；搜索自由规划 1.9–16.5× 加速（同文件 L3） | 把规划计算移到训练期、降推理成本 | 与实验预算/决策收益的联合权衡 |
| 计算高效的 BED / 多保真 | PASS1-Q4 **26 题录**，含 *Learning Bayesian Experimental Design Policies Efficiently*（DOI 10.1184/r1/33415399）、*A Multifidelity Estimator of the Expected Information Gain for Bayesian Optimal Experimental Design*（DOI 10.1137/25m1731812）、多保真代理自适应设计（DOI 10.1002/nme.6958） | 计算效率/保真度-信息权衡（题录级） | 联合预算与独立决策收益（未读全文，不能断言） |

### 3.2 直接针对"双预算联合分配"的检索结果

- PASS2-Q2：OpenAlex 标题/摘要 `"compute budget"` AND `"experiment budget"` → **hitCount=0**（`tmp/r201p/p2_openalex_P2_q2_compute_experiment_budget_both.json`）。**只记为检索结果**，不写成"不存在"（同义/近义表述如 cost-aware、multi-fidelity、resource-constrained 已有大量工作）。
- 结论：**部分覆盖**。决策聚焦/成本敏感/多保真各自覆盖一侧；若只把 compute 当作 acquisition 的又一项成本，则**已被 cost-aware BO/AL 与 MDA MI/cost 覆盖**，不构成新意。可能未覆盖的是“**计算误差（认证/近似）改变计划差认证→改变是否购买实验**”的同一账本联合决策，必须以独立药物决策收益（非预测提分）证明。

---

## 4. 不可声称创新的清单（写死；凡引用本文件即受此约束）

1. **模型+策略共同更新/共演化**（CoMap；CoLA/LAWM/HIJP 的联合动作-状态-动力学）。
2. **反例或预测检查触发模型修订**（OPINE World CEGIS；MDA M-open 扩张）。
3. **动态约束/预算下的非短视实验设计**（COPEx；BOR 资源/生产 POMDP）。
4. **任务摘要、query-sufficient 摘要、机制模型池、VoI 选实验**（MDA）。
5. **多实验共享参数/普通层级/多任务联合拟合保持一致性**（多实验系统辨识 21 条题录；共享后验即保留一致性）。
6. **集合成员/部分识别 + 约束生成 + 实验设计**（set-membership OED 生物先例 2012；IIS/MCS 常规；本地 A2 先例记录 L78）。
7. **选实验区分竞争模型**（模型判别 OED：1978 review、2008 sequential；127 条题录）。
8. **计算成本感知**（MDA MI/cost；HIJP search-free；compute-efficient BED；多保真 OED）。
9. **决策聚焦 acquisition / 决策价值×实验预算**（GoBOED、决策聚焦序贯设计、EVSI/ENBS）。
10. **"一般概念已被覆盖"的边界**：不得把上述任一单独或简单相加写成新算法；不得以"首次把 X 与 Y 放一起"作为新意（先例覆盖显示组合亦常见）。

## 5. 可能未被覆盖但需证明的条目（≤3）

- **G1（机制 A 核心）**：把“多个药物计划必须由**同一干预算子**生成”作为显式学习/决策对象，并用“**计划对联合不可行**（各计划单独合法、联合不可能）”的证书作为**主动选择实验的信号**，在破坏性群体观测+少量真实反馈下统一修订；需证明相对**普通共享参数联合拟合 + set-membership 识别 + 模型判别 OED** 有**增量**（预测或未测计划决策），否则收窄为评估修正或停。
- **G2（方向 2）**：把“**计算误差认证**（求解/近似/证书开销）”与“**真实实验购买**”放进**同一预算账本**，按**独立药物决策收益**分配；需证明不只是 cost-aware acquisition/MDA MI-cost 的重新表述（区分“继续计算”与“买实验”的可检验决策规则 + 同信息同预算对照）。**PASS2-Q2 字面查询 0 命中仅作检索记录。**
- **G3（更新运算）**：统一修订后的共同算子对**未测计划/药物**的独立决策收益（而非拟合改善），且不能被**全历史重训/共享参数后验/普通约束生成/重认证缓存**等预算等价方法重现；否则撤一般算法新意，保留科学问题描述。

## 6. 检索记录、零命中与限制

- PASS1（6 queries，OpenAlex/EPMC 元数据）：plan consistency 225、plan-consistent 811、shared dynamics×multitask 1、computational budget×experimental design 26、EPMC compute/experiment budget 2（无关）、set-membership×experimental design 9。文件：`tmp/r201p/p1_*`。
- PASS2（4 queries）：model discrimination×experimental design **127**、**compute budget×experiment budget 0（零命中记录）**、multiple experiments×system identification 21、counterfactual×planning×consistency 77。文件：`tmp/r201p/p2_*`。
- 限制：① 新增检索只到 OpenAlex/EPMC **题录/摘要级**，未读全文；② 一手全文阅读范围限于 §1 列出的本地提取文本（CoMap/LAWM/MDA/COPEx/OPINE/HIJP/CoLA/VCWorld/BOR 的段落，非全文逐段）；③ "plan consistency"等词有严重语义撞车（城市规划/调度/报告一致性），不能以命中数代表方法覆盖；④ 未检索中文/专利/非公开工业文献；⑤ 本文件**不构成首创证明**，只是本任务 2 pass 内的覆盖核验。
- 纪律：若 Lead 选择推进，必须按 BRIEF §纪律：一般方法等效→撤算法主张；只纠正已测点→停；预测改善但决策收益不成立→停决策创新；资源/精度不足→未决并记录。**不得把一般概念当新意，不得换名重启。**

---

### 附：关键本地锚点索引

| 主题 | 锚点 |
|---|---|
| CoMap 闭环/自蒸馏 | `sources/challenger/arxiv-2606.02372-extracted.txt` L5–6、L120（特权教师）、L303（推理成本） |
| LAWM 联合学习 | `sources/challenger/arxiv-2512.10016v1-extracted.txt` L3、L13、L28、L44–48 |
| MDA 机制池/VoI/摘要/MI-cost | `sources/challenger/arxiv-2608.09696-extracted.txt` L7、L131、L171–176、L779–800、L802–817 |
| COPEx 约束状态/预算/规划 | `sources/challenger/guo26g-extracted.txt` L21、L130–158、L203–221、L347–407 |
| OPINE 共享规则/反例修订 | `sources/challenger/arxiv-2607.01531-extracted.txt` L7、L11、L39–51 |
| HIJP 搜索自由规划 | `sources/challenger/arxiv-2610.23615v1-extracted.txt` L3 |
| BOR 资源/生产/固定预算 | `sources/challenger/icaps16-dolatnia-extracted.txt` L46–49、L93 |
| CoLA 联合/共演化 | `sources/challenger/arxiv-2510.26433-extracted.txt` L5、L7 |
| VCWorld 生物世界模型（细胞域近邻） | `sources/challenger/arxiv-2512.00306-extracted.txt` L3–5 |
| 决策聚焦 BOED/序贯设计 | `../2026-10-27-detectability-acquisition/sources/extracts/arxiv-2605.26093_sentences.txt` L26/L29；`arxiv-2602.05340_sentences.txt` L13 |
| EVSI/ENBS 题录 | `../2026-10-27-detectability-acquisition/sources/queries/pass2_epmc_P2-q1_EVSI_sample_size.json` |
| 组合覆盖/一致性内部分析 | `report.md` L23/L55；`challenge_sources.md` L45；`control_scout.md` L36；`recheck_v3.md` L48；`candidates_v3.md` L19 |
| 数学常规（IIS/MCS） | `../2026-10-27-innovation-scouting/conflict_signal/prior_art.md` L78 |
