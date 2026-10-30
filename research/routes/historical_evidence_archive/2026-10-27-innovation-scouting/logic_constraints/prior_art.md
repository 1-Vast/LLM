# R198-A2 先例核验（prior_art.md）

日期：2026-10-27 · 角色：定向核验员（lit-verifier）· task-25
范围：LOGICZSL 原文机制 + 药理学"知识约束/逻辑规则"用于组合预测/主动学习的近邻。**不声称新颖性**；本轮只做题录/摘要级检索（1 个合并 pass，4 条查询，见 §4），非穷尽。逐字引文均标行锚，Lead 可抽查。

## 1. LOGICZSL（CVPR 2025）原文机制（本地全文，P 级）

- 来源：`research/2026-10-27-cross-domain-directions/challenge_sources/LOGICZSL_CVPR2025.txt`（官方 PDF 提取文本；PDF 收据 SHA256 `d74f41ea6f2c3fbd4f4c68dadc0354d12605ba2b12996220aa5dbb2c05df8fd6`，2,401,464 B，收据见 [challenge.md](../2026-10-27-cross-domain-directions/challenge.md) L17；阅读范围为 §§3.2–3.4、式 2–16，见同文 L25）。
- 断言 1（关系→规则→可微损失）：LLM 构造原语概念树，再写成一阶逻辑规则，经模糊逻辑算子 grounding 成损失项。"relational knowledge and we then devise three logic rules"（L271）；"are approximated and grounded on data in a form of loss"（L391）；"constraints. To simplify, we limit the tree depth to 2:"（L392）。状态：reported。
- 断言 2（三类规则与总损失）：对象归纳/扩展/属性扩展三条逻辑（Loi/Loe/Lae）分别落地；总损失 `L = Lce + β(Loi + Loe + Lae),`（L501）；"logic-induced loss in Eq. 13. Please see §4.4 for details."（L1099，消融见 Table 4）。状态：reported。
- 断言 3（模糊算子/量词）：蕴含与合取被松弛为乘积等算子（§3.3 式 2–3，L338–356 区域）。状态：reported。
- **关键差异（对本任务）**：LOGICZSL 的规则来自 LLM 且**在训练中固定**——数据只用于满足约束/拟合表示，没有"数据否定并修订规则"的机制（本轮所读 §§3.2–3.4、式 2–16 范围内未见；全文其余部分未逐段核）。可迁移的是"把共享关系明确化为可被数据检验的约束"这一**原则**；不可迁移的是"LLM 语义树=生物硬约束"（[report.md](../2026-10-27-cross-domain-directions/report.md) L123："药物属于某靶点类，不蕴含其在任一细胞/剂量具有同一功能"）。
- 先例覆盖判定：**关系落到可训练约束 = 已覆盖**；**约束本身可被新功能反馈推翻并按失败类型归因 = 本轮已核范围未发现**（不等于不存在）。

## 2. 药理学"知识约束/逻辑规则"近邻

### 2.1 本地已核条目（引用库 / 前轮报告）

| 近邻 | 实际原则 | 证据级与锚点 | 对 A2 的覆盖判定 |
|---|---|---|---|
| BATCHIE（Nat Commun 2025） | 层级张量分解单药/组合项 + 后验更新 + 整板设计 | P；[跨域报告](../2026-10-27-cross-domain-directions/report.md) L127、"evidence_notes.md" L27；本 episode `sources/batchie_fulltext.txt` | **部分覆盖**：知识结构进模型 + 反馈更新已有；无约束推翻/归因 |
| PDTSyn（Brief. Bioinform. 2026） | 共享/特异参数分解、未见细胞/药物/药对划分 | P；[report_pa2 邻近条目](../2026-10-27-cross-domain-directions/evidence_notes.md) L25、cv_nlp_scout L84 | **部分覆盖**：共享结构预测；不以功能反馈检验关系 |
| DECANT（Bioinformatics 2026） | 匹配 treated/control、药物/背景分离；机制 latent=转录表型 | P；evidence_notes L26、cv_nlp_scout L85 | **部分覆盖**：共享/特异分离；明确非靶点/机制证据 |
| DeepSynBa（Bioinformatics 2026） | 完整剂量表面分离 potency/efficacy | P；[重审报告](../2026-10-27-independent-reassessment/report.md) L84 | **部分覆盖**：剂量条件已被建模；不检验约束可否定性 |
| Permutation-invariant multi-output GP（arXiv 2407.00175，2024 奠基） | 多输出 GP、置换不变、预测区间 | P；`reference/papers.tsv` arxiv-2407.00175 行 | **部分覆盖**：强基线；无逻辑关系约束 |
| TxPert（Nat Biotechnol 2026） | 多知识图谱预测转录扰动 | R（出版社 cookie，仅题录）；`reference/papers.tsv` doi-10.1038-s41587-026-03113-4 行 | **部分覆盖（题录级）**：知识图注入预测；未核其是否检验/修订约束 |
| AROMA（2026） | 表达分类 + 知识图谱解释；图边是关联 | P；`research/2026-10-26-agent-cell-evidence/report.md` L24、`candidate.md` L32 | **部分覆盖**：KG 解释 ≠ 机制/功能真值 |
| Iterative AI-guided triple-drug combinations（arXiv 2606.06562，2026） | 迭代 AI 指导的选择性三药组合优化 | P；`reference/papers.tsv` 该行（Methods 14–16、限制段） | **部分覆盖**：迭代选择；非"约束被反馈推翻" |
| R2 本地回放（KG 动作设计） | 固定 GP 更新下比较 KG 动作 vs 随机 | 已核实结果；[R2 报告](../2026-10-26-agent-cell-evidence-r2/report.md) L34：`KG − 随机 = +0.001884 [−0.081112,+0.063593]` | **已覆盖（阴性先例）**：本档案内 KG 动作设计无稳定优势；不得换名重启 |

### 2.2 本轮题录级检索（PASS：1，4 条合并查询；原始 JSON 在本目录 `qa_*`）

| ID | 查询（节选） | 命中 | 判读 |
|---|---|---|---|
| Q1 | EPMC：("logic rule"/"first-order logic"/"logical rule"/"knowledge graph") × ("drug combination"/"synergy prediction"/"combination therapy")，2020–2026 | 27 | 命中以 **KG 预测器**为主：KGLGANSynergy(2025)、DualKG-DC(2026)、HyperSynergyX(2026)、SynergyGraph(2025)、KGANSynergy(2023)、"Mechanistically Explainable AI…"(2025)。→ 药理学**知识约束/图约束作为预测特征 = 部分覆盖（题录级，未读全文）**；未见"约束可被小样本反馈推翻"的明确题录 |
| Q2 | EPMC：("constraint"/"prior knowledge") × ("active learning"/"sequential experimental design") × ("drug"/"combination")，2020–2026 | 7 | 仅 AL-guided mechanistic modeling（CXCL9 调控，2026/2025）近似；**组合筛选×约束式 AL = 本轮未发现（题录级）** |
| Q3 | OpenAlex 标题摘要：`"knowledge graph" AND "drug combination"`，≥2022 | 40 | 与 Q1 同向：知识图×组合预测密集；未见约束否定/归因 |
| Q4 | OpenAlex 标题摘要：`"rule violation" AND "perturbation"` | 24 | 全为物理/场论等无关命中 → **无相关**（记录为检索结果） |

### 2.3 覆盖判定汇总

| A2 主张的组成 | 判定 | 依据 |
|---|---|---|
| 把共享关系写成数据可检验的约束 | **已覆盖（原则）** | LOGICZSL §3.3；[report.md](../2026-10-27-cross-domain-directions/report.md) L121/L123 |
| 知识/逻辑约束进入药物组合预测 | **部分覆盖（且拥挤）** | Q1 27 条 KG 预测器（题录级）；PDTSyn/DeepSynBa/TxPert/AROMA |
| 约束被少量功能反馈**推翻**并区分 I/II/III 失败 | **未发现（已核范围）** | §2.1/§2.2；无全文级核验，故只写"未发现" |
| KG/逻辑约束改善**主动选择** | **部分覆盖且有本地阴性** | R2 `KG − 随机` CI 含 0；BATCHIE/决策 AL 先例 |
| "同靶点=同功能"作为硬约束 | **明确拒绝**（不是先例问题） | report.md L123、L92；cv_nlp_scout L76 反例 4 |

## 3. 结论与非声称边界

- **不能声称新颖性**：把关系写成约束、把知识图用于组合预测、反馈更新，均已有先例；"添加逻辑损失/兼容矩阵"属已知知识约束迁移（[report.md](../2026-10-27-cross-domain-directions/report.md) L123 原文："若只是添加逻辑损失或兼容矩阵，属于已知知识约束迁移；本轮不将其列作新算法"）。
- **A2 的可交付空间**：不是新算法，而是**可否定关系的检验设计**（C1–C10，见 spec.md §3）＋"三类失败归因"的预注册判别式（spec.md §5）。其贡献是否成立由下一轮设计/回放检验决定，本轮未验证。
- 检索限制：Q1–Q4 只到题录/摘要级，未读全文；LOGICZSL 只读 §§3.2–3.4 与式 2–16（challenge.md L25 声明范围）；**零命中只作为检索结果记录，不写成"不存在"**。
