# R198-A2 记录（record.md）

日期：2026-10-27 · 角色：定向核验员（lit-verifier）· task-25
范围：**只做设计与先例，不运行效果/训练/湿实验，不读响应做效果**。只写本目录（`research/2026-10-27-innovation-scouting/logic_constraints/`）；未改其它目录/INDEX/SYNTHESIS/git。

## 1. 本轮做了什么

1. **读必读项**：`research/2026-10-27-cross-domain-directions/{report.md,directions_v2.md,cv_nlp_scout.md,evidence_notes.md,BRIEF.md,challenge.md}`；`research/SYNTHESIS.md` §2d（C130/C155/C160/C167 及冻结结论与边界）；`research/EVIDENCE_REGISTER.md` C174/C175；`research/2026-10-27-drugcomb-annotation/{report_pa2.md,pa.py}`；`research/2026-10-27-drugcomb-endpoint/report.md`（MDE/结构预跑锚点）；`research/2026-10-26-agent-cell-evidence-r2/report.md`（KG 阴性先例）；`research/HANDOFF_20261027.md`、`research/2026-10-27-innovation-round-r197/BRIEF.md`（新主线来源）。
2. **LOGICZSL 原文机制核读**：`research/2026-10-27-cross-domain-directions/challenge_sources/LOGICZSL_CVPR2025.txt`（§3.2–3.4、式 2–16 范围内；PDF SHA 见 challenge.md）；提取"概念树→一阶逻辑→模糊逻辑算子→可微损失→总损失"链条与**规则固定、不可被数据修订**的关键差异。
3. **本地关系资源清点（只读身份/注释/元数据）**：
   - GDSC Jaaks fitted（Original）：296,707 行 / 125 细胞 / 2,025 药对 / 65 药 / 3 组织；`*_PATHWAY` 17/21、`*_TARGET` 40/58 水平；单药拟合列与数值浓度列存在（**未读响应值**，仅列名与计数）。
   - DrugComb S1：规模引用 P-B 报告结构预跑（1,175,220 行 / 380,418 cell×pair / 62,826 药对 / 4,088 药 / 112 细胞；无 study/浓度数值列）；本轮未读响应。
   - P-A2 映射 v2：1,800/4,088 映射，125 通路水平（101 个 ≥2；PA 切分可分析 79；中位 5、max 223）。
   - DrugComb 标识表：8,396 药；target_name 非空 4,442；与映射药可连接 1,774 行；归一 target 组 1,262 个，≥2 药者 128（max 12）。
   - MSigDB KEGG/Hallmark gmt 存在；已知药对先验/独立培养/靶点占据等**不可用**（见 spec §3 C8–C10）。
4. **先例题录检索（1 个合并 pass，4 条查询；见 `qa_summary.json` 与 `qa_epmc_*.json`/`qa_openalex_*.json`）**：
   - Q1 EPMC logic/KG × drug combination：27 命中（KG 预测器为主：KGLGANSynergy 2025、DualKG-DC 2026、HyperSynergyX 2026、SynergyGraph 2025、KGANSynergy 2023…）。
   - Q2 EPMC constraint/prior × active learning × drug：7 命中（仅 AL-guided mechanistic modeling 近似）。
   - Q3 OpenAlex KG × drug combination（≥2022）：40 命中（同向）。
   - Q4 OpenAlex rule violation × perturbation：24 命中全为物理/场论，**无相关**。
5. **产出**：`spec.md`（约束来源/形式、C1–C10 可检验性判定、M1/M2 机制候选、三类失败判别式、最小实验）、`prior_art.md`（LOGICZSL 机制 + 药理学近邻 + 覆盖判定）、`protocol_draft.md`（待冻结）、本记录、`usage.json`。

## 2. 关键设计决定（可被挑战）

- 关系一律写成 `(前件 A, 适用条件 Π, 可测关系 B, 统计量 T, 零分布 N, 修订 R, 失败类别 F)`；**同靶点/同义词=同功能被写成待否定假设 C1**，不进入硬约束。
- 三类失败的可操作判别式（spec §5）是 A2 的核心交付；与 A1 的更新器解耦。
- 主检验只放 C2/C3/C5；C1 为门控；C4/C6 降为分析性；C7–C10 明确不可检验或需新测量。
- 与 C130 关系：C130 只提供候选关系，A2 把其适用条件（身份缺失、水平已观测、覆盖非零）写进 Π，并允许被推翻；不重推 C130 数字，不把注释 argmax 当逻辑约束。
- 端点沿用档案口径（`SYNERGY_OBS_EMAX − SYNERGY_EXP_EMAX` 草案），**待 Lead 确认列义**；不换端点制造收益。

## 3. 本轮未做（防止误读）

- 未运行任何效果/回放/训练/拟合；未读响应值做任何统计（GDSC 仅列名+元数据计数；S1 未读）。
- 未下载新数据；未改 reference 清单；未复现 LOGICZSL 或任何方法。
- 未写 `challenge_I003.md`/其它目录；未声称新颖性。
- 未检验 C1–C6 本身（本轮只给"可检验"判定与统计量设计）。

## 4. 缺口与限制

1. 药理学"逻辑规则/知识约束"文献只到题录级（Q1 27 条未读全文），不能声称"未发现"=不存在；LOGICZSL 也只读 §§3.2–3.4 与式 2–16。
2. DrugComb 112 细胞**无组织列**，C4 只能部分检验；GDSC 仅 3 组织且组织×通路稀疏。
3. R1 的 pathway/target 是**每臂单标签**（anchor/library 角色），与 P-A2 的药物级 argmax 标签是两套口径，不能混用；混用需先映射协议。
4. DrugComb S1 无浓度数值列（P-B 已登记），C7 在 R2 上不可检验。
5. target_name 字符串归一有短别名噪声（report_pa2 §7：hnorm≤3 的 52 个 token 影响 55–111 药标签）；C1 结果需报该敏感性。
6. 独立培养、靶点占据不可得（C9/C10 不可检验）；已测药对先验与评估同源（C8 不可用）。
7. 组织/细胞重叠：GDSC 与 DrugComb 的细胞身份映射本轮未建（C4/外部确认的前置）。

## 5. 预算与记账

- 检索：**1 个合并 pass（4 条查询）**；本地文件阅读不计 pass。另：上一轮（R198-A1/R197）语境只读引用，不消耗本任务检索 pass。
- 计算：仅 pandas/openpyxl 只读元数据计数（秒级）；无模型拟合/训练。
- 时间：2026-10-27 18:03–19:0x（净工作约 45 分钟量级；以文件时间戳为准）。
- 模型/effort 运行时不可确认 → `usage.json` 记 unknown；tokens/cost 记 null。

## 6. 下一轮入口（建议）

1. 独立挑战者审 `spec.md` §3/§5 与 `protocol_draft.md` §3/§5/§8/§10；Lead 确认主端点列义与 R1/R3 两套注释不混用。
2. 先写 **constructive 设计体检**（人造 I/II/III 注入 + 置换零 + 探针分歧），不读真实响应；过体检再谈回放。
3. 若进入回放：严格按 `protocol_draft.md` §6/§7 冻结后再执行；A2 只输出归因与探针候选，不评更新器。
