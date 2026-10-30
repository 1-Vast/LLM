# R189 轮次记录：ComboCat 第二资源资格审计（线 A）+ I003 先例核验与独立挑战（线 B）

2026-10-27。角色：Lead（协调、冻结、核验、综合）＋ 3 名独立代理：数据资格审计员（combocat-auditor，task-1）、定向文献核验员（lit-verifier，task-2）、独立挑战者（i003-challenger，task-3）。提案者（Lead）不自评候选。

本轮范围由 [BRIEF.md](BRIEF.md) 冻结：线 A＝ComboCat 稠密组合补充表能否作为冻结结论外部复现的"第二资源"（A1 资格审计；A2 仅在 A1 达标后冻结并运行）；线 B＝新候选 I003 的最近先例定向核验、候选冻结与独立挑战（不运行效果实验）。**两条线最终都不启动效果实验**；本轮无新正面结果、无机制/临床主张、无代码晋升。

## 0. 一句话结果

- **线 A：`unqualified`（两口径一致）**——ComboCat 稠密补充表在发布形态下**结构性**不满足 A2 门槛：804/806 个 root 为 32 位十六进制匿名 id（药物名全表为占位符，无 cell line 列，3,383,955 次 md5 模板反解 0 命中）→ 药对图/身份/注释不可构造；已发布 drug class 只有 **5** 个水平（门槛 12）；**总 cell×pair 单元只有 806**，即使身份公开，20% 留药下 both-unseen 上界 **351 < 800**，均匀期望仅 **31.8**。**第二资源仍未出现。**
- **线 B：`STOP`**——本轮冻结的 `I003.v1`（决策聚焦证据选择）**复用了 R5 已停止的 I003.v1 编号与同一对象（主张 B：可检出性约束）**，违反 R5"不换名重提"与 BRIEF §1"不做重命名/重跑失败路线"；独立挑战另判其主分数在 r 固定时与纯决策价值秩等价、MDE 的 σ/r 在本归档不可操作化、主对比预期零效应；先例核验判 **部分覆盖**（decision-focused acquisition 已有 GoBOED/决策聚焦序贯设计，乘积门控已有 R-IDeA）。**候选撤回，不进入效果实验。**
- 本轮把两条"资源侧/谱系侧"约束写实：①外部验证资源的**设计级门槛**（both-unseen 单元 ≈ f²·总单元 ⇒ 需总 cell×pair ≈ 2,000–5,000，而不是"测量行数多"）；②"不得改名重提"规则第二次生效（第一次为 R5 主张 B 自身）。

## 1. 线 A：ComboCat 稠密补充表资格审计（R189-A1）

### 1.1 任务、输入与协议

- 输入：`research/2026-10-27-oneil-transfer-qualification/combocat_dense_supp_data1.zip`（73,327,836 B，SHA256 `5639020dbe…59e9e`，与 download_receipt 一致）；内含 `Supplementary_Table_1_REVISED.xlsx`（74,857,017 B，SHA256 `c2f28b75…571c`）。
- 协议：[../2026-10-27-combocat-resource-audit/PROTOCOL.md](../2026-10-27-combocat-resource-audit/PROTOCOL.md)（读取任何数据行之前冻结，SHA256 `3918548e…640e`；本轮未修改）。AMENDMENT-001（允许用同出版物 MOESM8 元数据做身份/注释联结，未读任何响应值）于 12:32 写在读任何响应值之前。
- 结论产物：[report.md](../2026-10-27-combocat-resource-audit/report.md)、[audit.json](../2026-10-27-combocat-resource-audit/audit.json)、[counts.json](../2026-10-27-combocat-resource-audit/counts.json)、[overlap.json](../2026-10-27-combocat-resource-audit/overlap.json)、[record.md](../2026-10-27-combocat-resource-audit/record.md)、[audit.py](../2026-10-27-combocat-resource-audit/audit.py)、[usage.json](../2026-10-27-combocat-resource-audit/usage.json)。
- 纪律：**18 个响应/派生列只做 `cell is None` 存在性计数，未读数值**；4 个 `flagged_*` 只计空/非空；8 个未分类列（`zprime`/`robust_zprime`/`moran_i`/`abs_res`/`nearest_pred`/`nearest_dose`/`Amount`/`...9`）完全不读；不联网、不跑响应建模、不改其它目录。

### 1.2 实测结构与先验假设（关键更正）

| 项 | 先验（BRIEF/简报） | 实测 | 结论 |
|---|---|---|---|
| 行数 | 292,459 | 292,458 数据行（+1 表头） | 一致 |
| 列/细胞/药物 | 45 列、36 细胞、136 药物 | 45 列、36 个整数 cell ID、136 个整数 drug ID | 一致（**都只有 ID，无名字**） |
| 组合数 | 806 组合 | **806 个 root** ＝ 806 个 (combination:cell_line) 单元 ＝ 论文 806 块稠密板 | 一致，但**语义是总单元数，不是 both-unseen 子集** |
| 重复 | 3 技术重复 | 每 root 恰 3 replicate（各 97,486 行）；词表原文 "all reps are in the same plate" | 一致，**同板技术重复** |
| 剂量 | 10×10 | 每 root 11×11 设计孔（10 剂量+0）=121（766 root）或 120（40 个有 barcode 的 in-house root） | 一致；完整网格应 292,578 行，实际缺 120 行（40 板×(0,0) 孔×3 重复） |
| root 身份 | "真实实体在 root_id"（任务简报假设） | **仅 2/806 描述性**（`CHP134_AZD1390_CX-5461…`、`LUM_SMX_TMP…`）；**804/806（99.752%）为不透明 32-hex**；`drug1_name/drug2_name` 全表占位符 `drug1`/`drug2` | **先验不成立** |
| 注释表 | 药物 class 可联结 | zip `drugs_summary` 仅整数 ID+class；`cell_lines_summary` 仅整数 ID+organism+lineage；**无 名↔ID 表**；MOESM8 实为**稀疏模式 135 化合物清单**（无 root 键） | 身份/注释不可联结 |

- 身份反解：按冻结协议做**有界离线** md5 模板尝试（5 种 id 模板 ×36×136×136、3 种名称模板 ×135²、40 个 barcode）共 **3,383,955 个候选，0 命中** → "在本轮冻结输入＋AMENDMENT-001 已发布元数据下不可解析"；不证明作者映射方式，也不推断 804 个匿名 root 的来源。
- 外部重合（只报告）：重算与 prior `counts.json` 逐项一致（Jaaks 121 细胞/65 药物/1,294 药对/67,812 cell×pair；O'Neil 35/38/583/20,405）；ComboCat 可恢复实体严格重合 **0/0/0**；清单层面 MOESM8 与 Jaaks/O'Neil 文本重合 28/13（非稠密映射，不能作泄漏依据）；804 个匿名 root 的外部性**不可验证**。

### 1.3 Q1–Q5 判定（冻结门槛，无事后调整）

| 门槛 | 实测/上界 | 门槛 | 判定 |
|---|---|---|---|
| Q1 注释水平 | 已发布 class 分类最多 **5 水平**（zip class：investigational 73/chemotherapeutic 26/antibiotic 18/antifungal 15/natural_product 4；MOESM8 Action_Class 亦 5） | ≥12 | **FAIL（结构性）** |
| Q2 both-unseen 单元 | 总单元 806；k=27/41/54；主估计、随机敏感性、贪心上界均 **null（不可计算）**；解析上界 min(806,C(k,2))=**351/806/806**；均匀期望 31.8/73.3/127.1 | ≥800 | **FAIL**：r=0.2 硬上界 351<800；r=0.3/0.4 需 ≥99.25% 单元集中才可能，实际不可达 |
| Q3 训练未见的 class | 不可计算（无逐 root 药物/class 归属） | =0 | **不可判定→不满足** |
| Q4 外部性 | 可恢复实体 0/0/0；清单层面 28/13；804 root 不可验证 | 只报告 | 报告级；"未见实体"表述必须加限定 |
| Q5 端点/重复 | 端点为 luminescence 活力派生 %Cell Death（raw_val→归一化→Bliss 派生）；重复为同板技术重复 | 限制性 | **始终成立**：只能检验"粗注释替代身份"的可重复性，不能升级为独立功能终点/独立培养/机制/临床结论 |

**总判定：`unqualified`（zip-only 与含已发布元数据两口径一致）。** 失败类别：`assumption_contradicts`（匿名化 root、MOESM8 非稠密名表、806 为总单元）、`data_unavailable`（无 cell line 列/药名占位符/无稠密名↔class 表）、`data_insufficient`（Q1 5<12；Q2 上界 351<800）、`evaluation_cannot_distinguish`（Q3）。

### 1.4 为什么这是结构性的，不是"数据质量差"

1. **匿名化**（804/806 root 无身份）使药对图、留药切分、逐 root 注释全部不可构造——这是发布形态问题，改门槛不可绕过。
2. **粒度**：即使拿到身份，已发布 class 只有 5 个水平；Reported_Target 有 99 水平但按冻结口径不是 class，且 MOESM8 是稀疏模式清单、无 root 键。
3. **规模**：806 是**总** cell×pair 单元，不是 both-unseen 子集。对 r∈{0.2,0.3,0.4}，both-unseen 单元 ≤ min(806, C(k,2)) = 351/806/806，且均匀期望只有 31.8/73.3/127.1——**总单元数本身远低于"≥800 both-unseen"所需的量级**。要在 20–40% 留药下达到 800，粗估需要总 cell×pair ≥ 800/f² ≈ **2,000–5,000**。
4. 技术重复与 viability 派生端点再各降一档：即使 A2 能跑，也只能检验"粗注释替代身份"的可重复性。

### 1.5 解冻条件（资源层面，写入 report §9）

1. 发布**非匿名化 root_id →（细胞系名, drug1 名, drug2 名）**映射（或去匿名稠密表）；
2. 发布**稠密 136 药物的 name + class**，且 class 可分析水平 ≥12（训练/留出均出现）；
3. 总 cell×pair 单元达到约 **2,000–5,000**（当前 806），以支持 20–40% 留药下 both-unseen ≥800；若维持 806 单元则必须重新冻结门槛（本轮不允许事后调整）；
4. 若要升级为独立功能终点/独立培养证据：需非 viability 端点与独立培养重复——当前资源结构性没有。

## 2. 线 B：I003 先例核验 + 独立挑战 → STOP

### 2.1 先例核验（[evidence.md](../2026-10-27-detectability-acquisition/evidence.md)，F01–F30；35 条引文经脚本逐字回查、0 miss）

- **部分覆盖**：decision-focused acquisition/BOED 已由 **GoBOED**（arXiv 2605.26093，"fully decision-focused"）与**决策聚焦序贯设计**（arXiv 2602.05340，directional uncertainty 更早停止）直接实现；"acquisition 分数 × sigmoid 门控"乘积结构见 **R-IDeA**（arXiv 2506.07805，但门控变量是**模型错设残差** `|f̂−g|`，不是测量可分辨性/MDE）；噪声/识别 SNR 与预算 regime 见 **2605.04895**（强先验压平 acquisition 差异、GDSC2 上 greedy 常胜、注入噪声重新拉开差异）；"决策价值 vs 样本量/成本"属成熟 **EVSI/ENBS** 临床设计框架（仅题录级）。"决策相关≠学习必需"已有 2026 研究。
- **唯一未发现先例的物件**："以每动作实际重复数计算 MDE 作为 acquisition 准入闸"（PASS2：EPMC power×acquisition hitCount=0；OpenAlex "decision-focused"∧"acquisition function"=0、"statistical power"∧"BOED"=0）。**零命中只作检索结果记录，不作"不存在"证据**；仍属**构成/评估修正**材料，不足以支撑新算法主张。
- **对候选的自纠**：候选 §4 的 "BATCHIE SNR 惩罚 DBAL" 未被正文支持——BATCHIE 正文是 PDBAL（最小化后验样本间期望距离）；"undetectable"仅出现在 phase-I 孔失败的数据质量语境（补充材料未下载，记缺口 G3）。
- 检索缺口：G1 arXiv API 本轮不可达（2 次 timeout+1 次 429，PASS2 未覆盖 arXiv 侧）；G2 EVSI 仅题录；G3 BATCHIE 补充材料未下载；G4 ComboCat 身份只查了已下载发布物。

### 2.2 独立挑战（[challenge_I003.md](../2026-10-27-detectability-acquisition/challenge_I003.md)，10 项判决：FAIL 1/2/3/6/7/8/9、WEAK 4/5、总判决 stop）

- **数学独特性消失**：主分数 S=VOI×D；r 固定（本资源唯一可行）时 D 在决策带内近似常数 → S 与纯决策价值**秩等价**；σ≈0 时 D≡1 ⇒ H2 恰是"本候选≡纯决策臂"的等价性证明。一阶下 VOI≈决策敏感度²·σ²·EIG，乘积不产生新估计量；乘积门控先例 R-IDeA 已存在。
- **MDE 不可操作化**：r 在本归档固定为每条件 2 个同日文件、非独立；"同条件重复"含归一化锚点会把噪声低估 2.4 倍；可用 σ_e≈0.04 是另一板型的借用估计；行级动作与 C141（模型对同对细胞内预测完全相同）冲突。
- **谱系/准入闸违约（决定性，见 2.3）**。
- **结构性无效风险**：C154/C129/C144（估计饱和、29 倍数据持平、分配近中性）说明换 acquisition 分数救不了压平曲线；候选靠自注入合成高斯噪声"制造"可救曲线，H2 还把 R187 阴性错误归因于"σ≈0 回放"。
- **实验不可区分**：I003 vs 纯决策主对比预期≈0；H3 由 σ 定义自动成立、不可证伪；方差臂与 EIG 臂在独立高斯回放下秩相同（与候选自己的 |ρ|<0.9 体检互相矛盾）；20 种子为重叠切分伪重复、无 MDE 推导。

### 2.3 谱系冲突（本次核验直接引用档案行号确认）

- R5 冻结的 **I003.v1** 主张 B："只聚合/只选'可检出'的单元对，比用全部秩对更有效"——E006 后**判不成立、停止、"不换名重提"**；主张 C（决策收益）仍锁定；R5 记录"已用完一次实质修订，再次改前提即超限"（[R5 CANDIDATE_I003.md:21-22,47-49](../2026-10-27-agent-cell-identifiability-r5/CANDIDATE_I003.md)）。
- R4 写死主张 B 的准入闸："只有在主张 A 成立、且存在独立决策收益后才准入；否则按 R2 与 T307 的阴性直接停止"，并要求 T307 三条件（真/打乱/无反馈，同预算配对）与 T309 区分测试（[R4 record:96-97,112,114](../2026-10-27-agent-cell-identifiability-r4/record.md)）。
- 本轮候选**沿用同一编号 I003.v1**、把对象改写成"决策聚焦 acquisition"，未处理上述准入闸/T307/T309 → 按 BRIEF §1 属"重命名/重跑已有失败路线"。**独立挑战的 stop 判决与本条谱系冲突一致；Lead 采纳。**

### 2.4 Lead 裁定与保留物

- **候选撤回**：`CANDIDATE_I003_v1.md` 已加"STOP"状态节（原文保留）；本轮不运行任何效果实验，不晋升代码。
- **保留但不准入**：唯一可能为真的残余是"把无法分辨的对比**整类**判为不可作为证据、从而改变可选动作集与停止条件"——它需要**新编号、重新登记、先解决 r/σ 与 R4 T307/T309 准入闸**，且只能作为**评估修正**提出，不得声称算法收益。
- **对"决策聚焦 acquisition"问题域不停线**：停的是本候选形态；未来若重启，必须先写清与 GoBOED/2602.05340/R-IDeA 的差异，并在强先验 regime 下预期 acquisition 空间被压平（2605.04895）。

## 3. 本轮新增可引用事实（登记编号见 EVIDENCE_REGISTER / CLAIM_STATUS_AUDIT）

- **C155** ComboCat 稠密补充表作为"第二资源"**unqualified**（两口径一致）：身份匿名化（804/806）、class 仅 5 水平、总单元 806（Q2 上界 351<800）；附解冻条件。证据：audit.json/report.md。
- **C156** 外部验证资源的**设计级门槛**：both-unseen 单元 ≤ min(N_total, C(k,2))，均匀配对期望 ≈ f²·N_total；要支持"20–40% 留药下 both-unseen ≥800"，需总 cell×pair ≈ **2,000–5,000**。**"测量行数多"不等于"可留药单元多"**（ComboCat 292,458 行 → 806 单元）。证据：report §7、本记录 §1.4。
- **C157** I003.v1（R189 版）**STOP**：与 R5 已停 I003.v1 同编号同对象（主张 B），违反"不换名重提"；独立挑战判数学独特性消失/MDE 不可操作化/主对比预期零效应。**保留物**＝"整类判不可作为证据→改动作集/停止条件"，须新登记。证据：challenge_I003.md、R5/R4 引用。
- **C158** 先例定位（一手全文级）：decision-focused acquisition、决策聚焦序贯+停止、乘积门控结构、噪声/预算 regime 均已有 2026 先例；**"每动作 MDE 作准入闸"零命中但属评估修正**；BATCHIE 正文无 SNR 惩罚项（更正候选表述）。证据：evidence.md F01–F30；零命中不等于不存在（缺口 G1–G4）。

## 4. 停止与不重复清单（本轮新增）

1. **I003 谱系**：不得再以"可检出性约束/可分辨性门控"为名重提 I003；任何重启须新编号 + 新登记 + 解决 T307/T309。
2. **R187 预测方差采样**（用户已排除）与**本轮 I003.v1 形态**都不得换名重跑。
3. **ComboCat dense**：在解冻条件满足前，不得作为"A2 外部复现"运行；不得用稀疏模式补全值当实测标签。
4. 不得把 292,458 行当作独立测量单元；不得把 806 块板当作可留药总体。
5. 本轮未产生任何正面的决策收益/迁移/机制结论。

## 5. 下一步（R190 候选，待 Lead 冻结 BRIEF）

- **候选 D（Lead 建议优先做资格审计）**：**细胞状态特征能否让模型排细胞**——用本机 `data/external/depmap_19q4/CCLE_expression.csv`（19,144 基因 × 1,756 细胞系；**125/125 Jaaks 细胞按归一名字可匹配**）的药物靶点基因表达/突变构造细胞特征，直接检验 C141 的结构边界（"两臂都没有细胞特征所以不能排细胞"）是否可由知识增强打破。需要先做资源资格审计（表达行/基因列、86 个靶点的基因映射 50/86 精确 + 别名表、缺失值口径、泄漏与切分、MDE），再冻结可证伪假设；**不预设成立**。
- **候选 E**：外部复现资源再资格化（如 DrugComb）——但按 C156，先核对"总 cell×pair 单元 ≥2,000–5,000、药物名+≥12 水平注释、与 Jaaks 训练集无实体重叠"三项，再决定是否花预算。
- **候选 F（仅评估修正）**：把"MDE 准入闸"作为**已有 decision-focused 方法的评估修正**（非新算法），若做须新登记、且先解决 r/σ 与真实计费单位。

## 6. Lead 独立核验记录（本轮）

- **A1 确定性复跑**：`python research/2026-10-27-combocat-resource-audit/audit.py` 由 Lead 独立重跑一次（约 120 s），三份 JSON 的 SHA256 与审计员产物**逐字节一致**（audit.json `B2066265…00DD`、counts.json `FEEE650F…282D`、overlap.json `4E706C29…4710`）；audit.json 内 script/protocol SHA256 与磁盘一致。
- **响应值保护**：grep `audit.py` 确认 18 个 DENY 列只出现在 `row[i] is None` 计数分支；产物只有计数/名称/派生比率，无响应数值；audit.json 记录 `response_values_read: false`。
- **数字抽查**：Lead 独立复核——292,458 行 = 40×360 + 766×363；C(27,2)=351<800；(k/136)²×806=31.8/73.3/127.1；class 5 水平与 MOESM8 Action_Class 5 水平（Lead 直读 moonshot 表核实）。
- **B1 引文抽查**：Lead 逐字复核 combocat_sentences L46/L50/L65/L161/L231、2605.26093_sentences L26/L27、2605.04895 L191、2506.07805 L172、batchie_sentences L98，均与 evidence.md 一致；引用核对脚本自报 35 found / 0 miss。
- **C1 档案抽查**：Lead 直读 R5 CANDIDATE_I003.md:21-22,47-49、R5 report:29,52、R4 record:96-97,112,114、R187 report:29，确认挑战者引用的谱系/准入闸事实成立。

## 7. 产物、预算与边界

- 本轮新目录/产物：[../2026-10-27-combocat-resource-audit/](../2026-10-27-combocat-resource-audit/)（7 件）、[../2026-10-27-detectability-acquisition/](../2026-10-27-detectability-acquisition/)（evidence.md、pass_log.md、challenge_I003.md、sources/ 新增；含 ComboCat 补充材料与 arXiv 全文）、本目录 BRIEF/CANDIDATE/record。
- 代理：3 名（数据资格审计、文献核验、独立挑战）＋Lead；无付费 LLM API 调用（usage.json：token/费用记 null，不记 0）。
- 计算：审计脚本 2 次全跑（含确定性复跑，各约 85–120 s）；无 GPU、无湿实验、无响应建模。
- 边界：本轮结论是**资源资格**与**候选停止**，不是对 ComboCat 科学价值的评价，也不是对"决策聚焦 acquisition"问题域的否证；无机制/靶点/临床主张；**未晋升任何代码**；总体目标未达成。
