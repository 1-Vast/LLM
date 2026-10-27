# R191 BRIEF（2026-10-27，Lead 起草；下一轮执行）

总体目标不变。R190 已把**第二资源资格**推进到 `eligible_with_conditions`（DrugComb）；本轮的唯一任务是把"**能否复现冻结结论（C130/C155–C156）**"变成一份可执行、可证伪、且在读任何响应值之前冻结的协议。**资格通过 ≠ 复现成立**；R191 不预设复现成功。

## 0. 入口状态（R190 之后）

- 冻结结论（未变、未解冻）：两药都未见时，药物粗化注释替代缺失身份，`ΔEMAX` 排序增益 `通路−identity ≈ +0.1183 [+0.0947,+0.1409]`；一药见过时增益恰 0。解冻条件＝出现满足 C155/C156 规格的第二资源并完成复现。
- R190-E1（[DrugComb 资格审计](../2026-10-27-drugcomb-qualification/report.md)）：`eligible_with_conditions`。v1.4 summary 全量核验：**466,033 组合块 / 4,088 药 / 112 细胞 / 62,826 无序药对 / 380,418 cell×pair**；确定性留药 r=0.2/0.3/0.4 的 both-unseen 单元 **16,078 / 33,148 / 52,368**（≫800）。Jaaks 重合：细胞 18、药 40、cell×pair 键 241。注释：本地并集覆盖 v1.4 组合药的 **51.28%**（项目 38 通路模板仅 0.98%）。**条件**：注释映射协议、端点映射/饱和性、unseen-entity 切分、v1.5 全表未全量核验、v1.4 无 study 列、碰撞剔除。
- 线 D（细胞状态特征）已在 R190 停止（C160）；不得重开/换名。

## 1. R191 的两个前置协议（阶段 1，**不读响应数值**）

**P-A｜注释映射协议（必须可审计、先于任何响应读取冻结）**
- 目标：把 DrugComb v1.4 分析宇宙（4,076 组合药物，碰撞剔除后）映射到 **≥12 个可分析粗略水平**，语义尽可能接近项目通路（GDSC `ANCHOR_PATHWAY`/`LIBRARY_PATHWAY` 的 38 双侧 one-hot / 21 文本水平）。
- 候选来源（按优先级，必须逐条记录覆盖率、水平数、可审计性、是否响应派生）：① Jaaks 通路模板（86 靶点→21 通路）经 DrugComb 药名/靶点联结；② Drug Repurposing Hub（`moa` 1,436 / `target` 2,216 水平）→ 用**冻结的粗化规则**映射到 ≥12 个"通路样"水平；③ PRISM primary/secondary 的 moa/target；④ 如需外部基因集（如 KEGG/Reactome/MSigDB-H 的基因→通路），只允许下载公开、可冻结、可哈希的资源，并在协议中写明版本与映射规则；⑤ 禁止用响应值筛选/验证映射。
- 硬门槛：分析宇宙中**两药均被映射**的药对 ≥ 预注册比例（建议 ≥50%，先写死再算）；可分析水平 ≥12；每水平≥2 药且在训练/留出药物集合均出现（Q1/Q3 口径同 R189-A1）；映射表 SHA256 冻结；报告无法映射比例与 12 个机制类药（5-FU/Bortezomib/Cisplatin/Docetaxel/Gemcitabine/Oxaliplatin/Paclitaxel/Pictilisib/Taselisib/Temozolomide/Vinorelbine/Vorinostat）的处理。
- 若映射无法达到 ≥12 水平/覆盖门槛 → **`not_eligible`（升级）**，记录解冻条件，不进入阶段 2。

**P-B｜端点映射与饱和性协议（不读效应、可读分布统计）**
- 目标：从 DrugComb summary 的响应列（`synergy_bliss`/`synergy_loewe`/`synergy_hsa`/`synergy_zip`/`S_mean`/`css`）中选定与项目 `ΔEMAX` 最可比的**主端点**，或明确改用 raw dose-level 重拟合 ΔEMAX（2 GB 级，需预算评估）。
- 必做：① 端点语义与已发表定义核对（一手文献）；② **饱和/天花板**检查（分布、上下界截断、与随机期望的关系）；③ 指标冗余（同 R189 的 C98 教训：四个连续指标不要当独立终点）；④ 聚合单位（cell×pair 的 mean/median；剂量层 vs summary 层）；⑤ MDE 前置估计（在 both-unseen 16,078 单元、4,088 药下的排序指标 MDE）。
- 硬门槛：主端点非饱和（预注册饱和判据，如 >90% 值贴边/截断或方差塌缩即 fail）；端点与 `ΔEMAX` 的构造可比性有书面论证；MDE ≤ 预注册最小效应（建议 0.02–0.05 量级，先写死再算）。
- 若端点不可用/饱和 → 记录 `endpoint_not_usable`，不进入阶段 2（或明确改用 raw 重拟合的新协议）。

## 2. 阶段 2（仅在 P-A、P-B 都通过后冻结）：复现协议草案

- 任务：在 DrugComb 内复现 **both-unseen regime 的条件结构**——身份归零时，粗注释是否恢复排序信息。
- 宇宙：DrugComb v1.4 summary 组合块；排除碰撞键；敏感性分析排除与 Jaaks 重合的实体（细胞 18/药 40/键 241）或按 unseen-entity 切分。
- 切分：确定性留药 r=0.20（k=818，both-unseen 16,078 单元；主）＋敏感性 r=0.30/0.40；训练=两药均不在留出集合的药对；测试=两药均在留出集合。**按药物分组内层 λ**（R163 教训）；三路互斥（训练/采购/最终评估）在本协议中显式定义。
- 特征臂（同信息、同预算）：① `identity`（药 one-hot；留出药恒为 0）；② `annotation`（P-A 映射的粗水平 one-hot；双侧）；③ `size_matched_random`（同组大小随机块，5 次平均）；④ `shuffled_mapping`（打乱药↔注释映射）；⑤ `pair_mean`/常数基线（边际在 both-unseen 处不可定义，需明确当常数处理并披露）。
- 模型：ridge（标准化、内层 CV 选 λ、按药物分组）；主指标：Spearman(pred, y)（与 C130 同口径）；副指标：top-quartile AUC / top-k 命中（按 DrugComb 端点定义预注册）。
- 统计：bootstrap 按药对（并报按药/细胞聚类敏感性）；MDE 必报；预注册最小效应 δ_min；失败类别：`not_replicated` / `construct_mismatch` / `inconclusive`（inconclusive=失败，不救）。
- 防泄漏：注释映射不用响应；切分按药；内层 λ 按药分组；shuffle/size-matched 必做；主端点与 MDE 先冻结。
- 停止条件：P-A/P-B 失败 → 升级资格结论、停；主对比不成立 → 记录"在 DrugComb 上未复现"，不换指标/换切分重试；不得把复现写成新机制。

## 3. 代理与预算

- 阶段 1：2 名独立代理（P-A 映射审计；P-B 端点/饱和审计）＋Lead 综合；检索 1–2 pass（EPMC/OpenAlex/arXiv，优先本地）。
- 阶段 2：**独立挑战者**先审协议（必做），通过后由独立 runner 执行；Lead 只做核验与综合。
- 计算：CPU；P-A/P-B ≤30 分钟；阶段 2 单次 ≤45 分钟；下载 ≤2 GB（若需 raw dose-level，先单独评估并写回执）。

## 4. 明确不做

不重开线 D（细胞状态特征）；不重开 I003/可检出性线；不用预测方差/分歧采样；不把"DrugComb eligible"写成"冻结结论已解冻"；不做机制/靶点/临床主张；不晋升代码；不在协议冻结前读响应值做效应估计。
