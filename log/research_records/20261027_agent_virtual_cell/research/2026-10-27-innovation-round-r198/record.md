# R198 轮次记录：机制探索批次（多子智能体并行，Lead 总调度）

2026-10-27。背景：R196/R197 的协议挑战分别判 `revise`（R196 初判撤回 C176；R197 v1 协议作废 C177）；外部重审后主线改为"**少量功能反馈区分三类失败（数值需调整 / 共享关系适用条件失效 / 表征遗漏关键状态），并用于未测药物选择**"。本轮并行开 5 条机制探索 + 2 个回顾性协议挑战；**全部只做设计/先例/资格，不运行效果、不训练、不读响应做效果**。

## 0. 共享纪律

- 每条 scout 交付：机制规格（可证伪预测、被什么证据推翻）、先例覆盖（已覆盖/部分覆盖/未发现；零命中≠不存在）、最小实验设计/`protocol_draft.md`（冻结要点）、记录/usage。
- 只写各自 `research/2026-10-27-innovation-scouting/<line>/` 与 tmp/；不改其它目录/INDEX/SYNTHESIS/git；不声称新颖性；不运行效果。
- 候选冻结前必须经独立挑战；Lead 只冻结**一个**进入下一轮效果。

## 1. R198-A2（logic_constraints，lit-verifier，task-25）——已完成

产物：[spec.md](../2026-10-27-innovation-scouting/logic_constraints/spec.md)、[prior_art.md](../2026-10-27-innovation-scouting/logic_constraints/prior_art.md)、[protocol_draft.md](../2026-10-27-innovation-scouting/logic_constraints/protocol_draft.md)、[record.md](../2026-10-27-innovation-scouting/logic_constraints/record.md)、usage.json + 4 条 prior-art 查询 JSON。

- **约束清单 10 条**：当前数据可检验 5（C1 同靶点功能等价否定性门控、C2 通路对交互方向跨语境共享、C3 通路替代性先验适用条件、C5 单药读数解释 pair 效应、C6 注释谱系一致性）；需新测量 2（C4 组织适用性、C7 剂量/暴露）；不可检验 3（C8 已知药对先验=同源泄漏、C9 独立培养重复、C10 靶点占据/通路激活）。每条含检验统计量/零分布/违反→I/II/III 归因规则。
- **机制候选**：M1 CVT（约束违反后按预注册判别式归入 I/II/III；探测选择=三竞争修订模型分歧最大的 cell×pair）；M2 低容量"适用条件表"对照。可证伪预测 H-A2.1–A2.5（含"全部违反归 I → 停约束迁移主张"、打乱注释零数据优势消失、同靶点硬约束会产生可检出归因错误）。
- **先例覆盖（部分覆盖；不得声称新颖性）**：LOGICZSL 的"关系→模糊逻辑→可微损失"原则已覆盖（本地全文逐字锚点），但其规则固定、数据只用于满足规则；药理学 KG/逻辑约束用于组合预测为题录级已覆盖且拥挤（EPMC Q1=27 条 KG 预测器；OpenAlex Q3=40）；constraint×AL×drug Q2=7 无组合约束式 AL；"rule violation"×perturbation Q4=24 全无关；KG 采集有本地阴性先例（R2：KG−随机=+0.001884 [−0.081,0.063]）。**"约束可被少量功能反馈推翻并按 I/II/III 归因"在已核范围内未发现（题录级，非穷尽）**。
- **最小实验草案**（未冻结）：GDSC Original（SHA 冻结）+ P-A2 映射；按药对留出 20%（按药物聚类）；端点=观测−期望 EMAX 差（**Lead 确认：对应 `SYNERGY_DELTA_EMAX`，主端点已由 P-B/P-B2 冻结；A2 草案应显式引用该列名**）；replay k∈{6,12,24} cell×pair；臂 CVT/M2/random/方差-EIG/无更新；≥20 种子配对；主终点=三类归因正确率，副=未测药 top-k 后悔；δ_min=0.03、MDE80 two-way r=0.20=0.1149/r=0.40=0.0614（归因正确率 MDE 需预注册模拟）；constructive 设计体检（注入 I/III 判别≥0.60、type-I≤0.10、探针分歧、开发池违反数≥5）。
- **缺口**：药理学逻辑约束只到题录级；LOGICZSL 只读 §§3.2–3.4；DrugComb 无组织/浓度列（C4/C7 部分不可检）；GDSC 通路/靶点是每臂单标签、与 P-A2 药物级 argmax 不可混用；target_name 短别名噪声；独立培养/靶点占据不可得。

**入口**：先由独立挑战（task-35）审 spec §3/§5 与 protocol_draft §3/§5/§8/§10，再写 constructive 体检脚本（不读真实响应）；挑战通过前不冻结、不运行。

## 1b. R198-A1（conflict_signal，combocat-auditor，task-24）——已完成

产物：[spec.md](../2026-10-27-innovation-scouting/conflict_signal/spec.md)（24 KB）、prior_art.md、protocol_draft.md、record.md、usage.json。

- **三类失败 operational 签名**：(i) 数值调整 = 约束拟合可行（χ² 在噪声内）+ 更新落在 nuisance 子空间（Λ_null δ 占比≤ε）+ 审计关系保持；签名 r_num/d_rel（现有数据可算）。(ii) 关系冲突 = **关系空间不可行**（最小释放集 J_min 非空）且被违反关系在 **≥2 个独立上下文符号/排序翻转（X_flip）**；判据三件套 C_conf（nuisance-正交关系空间违约，Q 型对比构造）+ X_flip + J_min，并必须同时报 R_abs（原始残差）/L_lev（leverage）作对照；**Jaaks Original/Validation 的 R193-A0 匹配四元组（6,223,367；controlled_anchor 92,039；96 细胞/98 有向药对）上可算（下一轮）**。(iii) 表征遗漏 = 全释放后残差仍结构化且可复现 + φ 空间外推 O_rep 高 + 可测状态 z 使 φ→(φ,z) 在留出上下文优于同维随机块（ΔR²_state）；**当前组合数据不可认证**（无配套可测状态），只能诊断代理；spec §8 给所需最小新测量。
- **关键证明（构建性）**：残差大但 Q=0（i）；残差小但 Q=1 符号翻转（ii）；leverage 与 Q 独立 → **关系冲突不是残差/距离/leverage 改名**；单批反馈一般不可分类，spec §2.1 写死最小可辨识设计，否则输出 `not_identifiable`。
- **机制候选**：**M1 PRU-CC**（AlphaEdit 启发：受保护关系约束更新 + 不可行时最小释放集与冲突证书 + 拒绝/回退；线性情形=投影核回归 → **投影核等价控制必做**）；**M2 DPG**（Poke&Strike 启发：决策精度门控，多解释对未查询动作预测不同才购买；无合法区分测量时拒绝购买/拒绝宣称）。P1–P7 每条给"被什么证据推翻"。
- **先例覆盖（有界检索 15 query；web_fetch 不可用=non-public IP；新条目仅索引级）**：AlphaEdit 机制已覆盖（NLP）但用于药理组合反馈未发现；AlphaEdit+（ACL 2026 Findings）部分覆盖（题名/索引）；LOGICZSL/Poke&Strike 部分覆盖；PDTSyn/BATCHIE 已覆盖预测架构/条件模型+整板选择，未覆盖冲突诊断；**"三类失败区分用于药理组合反馈"本轮未发现先例（不写"不存在"）**；约束回归/不可行诊断/最小释放集=数学常规，**不得主张算法新颖性**。
- **最小实验要点**：Stage 1 固定响应盲抽样反馈 S，只比较更新器（M1/≤3 预注册变体 vs 全量重训、普通适配、层级、GP、投影核等价、冲突抽签、尺寸匹配随机释放）；Stage 2 仅在 Stage 1 出现可归因增量后比较 DPG vs 随机/贪心/不确定性；主指标=未查询菜单配对决策损失；δ_min 从任务成本/最小有用差异定义（本轮不编造）；MDE/功效按细胞/药对聚类预检 80%@δ_min；U 读数代码级隔离；φ/关系集/S 规则/δ_min/预算冻结前写 SHA；失败类别含 `not_identifiable`/`insufficient_precision`/`explained_by_baseline`。
- **缺口**：关系集尚未构造（protocol §2 规则未执行；需下一轮独立"关系资格"步骤并冻结表 SHA）；(iii) 需新测量；(i)/(ii) 真实可区分性未检验；δ_min 无成本/效用无法数值冻结；先例新条目仅索引级。

## 2. 其它线状态（截至本记录）

- **R198-A1（conflict_signal，combocat-auditor，task-24）**：产物已落盘（spec.md 24 KB、protocol_draft.md、prior_art.md、record.md、usage.json），任务尚未标 completed（疑似收尾/汇报中）；待完成后写摘要并派独立挑战。
- **R198-A3（dynamic_route，cellstate-lit，task-26）**：metadata 核查进行中（a3_inspect.py、a3_meta.json 已落盘）。
- **R198-A4（missing_state，drugcomb-auditor，task-27）**：进行中。
- **R198-A5（acquisition_stage3，endpoint-auditor，task-28）**：进行中。
- **R196v2（task-31，annotation-mapper）**：按 AMENDMENT-001 重跑（drug 主单位、≥10 划分）；未出 v2 结果。
- **R197v2（task-33，cellstate-auditor）**：按 AMENDMENT-002（方案 P/Q 二选一）重跑；未出 v2 结果。
- **挑战队列**：T32（R196v2）、T34（R197v2）待各自 runner 完成后派 i003-challenger；T35（A2 spec）已建，下一步派给 i003-challenger（若与 T32/T34 不冲突）。

## 2b. R198-A2 挑战结论（i003-challenger，task-35）——revise；降级为 A1 模块

- **总判决 revise（≤5 必改，冻结前完成）；当前形态不值得直接进入候选冻结。**
- 最致命 3 条：① **主主张无真实 ground truth**——I/II/III 是失败类别标签，真实 GDSC 无标签；只能用人造注入评判别式（constructive 合理），但协议把"归因正确率"当主终点并安排 replay → 真实 replay 无正确率可算；必须收窄为"constructive 判别体检为主 + 真实 replay 仅次级下游选择/归因分布描述"。② **切分/端点/注释三处不一致 + 与既有轮次重复**：按药对留出 20%+按药物聚类+两药未见三者不能同时成立（R196 已示 drug 分折≈held 13 药/每折 2.5–5.8k cell×pair）；主端点 protocol 仍写"待 Lead 确认"而 record 已确认 `SYNERGY_DELTA_EMAX`；注释源 spec 用 GDSC 38 通路模板、protocol 写 P-A2 映射（两套不可混用）；C3 本质=C130 检验（R196/C176 状态）、C5 与 R194/Q2（C172/C174）重叠 → 应交 R196v2/R197v2，不重做。③ **I/II/III 与 A1 同一分类两套操作化 + k 预算无功效**：A1 已有 χ²/Λ_null、X_flip/J_min、ΔR²_state；A2 又给一套（重估降≥50%、条件内外差≥0.20、状态相关）却未预注册主判定/一致性/仲裁；k∈{6,12,24} 与 II（内外各≥10）、III（每状态≥k=6）、§8 每组≥10 冲突且无 MDE/预算表；M1"三个竞争修订模型"未定义；III↔A4、probe↔A5 重叠。
- ≤5 必改：① 主主张/主实验对齐（constructive 为主、replay 次级；C3→R196v2、C5→校准线；无真实代理标签不得报归因正确率）；② 切分/端点/注释统一写死（drug-level 折、四者不相交、`SYNERGY_DELTA_EMAX`、注释二选一）；③ I/II/III operational 化+预算-功效预注册（标量/CV/阈值理由；条件内外≥10 单元；状态清单+每状态 k=6 可行表；MDE 模拟+不过即 inconclusive）；④ A1/A4/A5 接口与去重（两套签名主判定/一致性/仲裁；A2 只出约束/违反/候选状态/固定探针；III 归 A4；acquisition 归 A5；引用 C176/C177 作废状态）；⑤ 先例/新颖性/措辞/冻结清单（补 general-ML 检索或写"未检索不声称空白"；定义三修订模型或 A1 接口契约；冻结 seeds/schema/失败类别/预算；C1 正显著也不得写成"同靶点=同功能"；不是新算子/不重开 R2 KG）。
- **Lead 处置**：A2 **不单独冻结**；降级为 A1 的"约束库/constructive 判别体检"模块（下一轮按必改 1–4 修订后作为 A1 支撑交付），若只冻一个候选则 A1 优先。

## 2c. R198-A5（acquisition_stage3，endpoint-auditor，task-28）——已完成；挑战 T37

- 产物：[spec.md](../2026-10-27-innovation-scouting/acquisition_stage3/spec.md)、[cost_model.md](../2026-10-27-innovation-scouting/acquisition_stage3/cost_model.md)、[prior_art.md](../2026-10-27-innovation-scouting/acquisition_stage3/prior_art.md)、[protocol_draft.md](../2026-10-27-innovation-scouting/acquisition_stage3/protocol_draft.md)、record/usage；成本算术 `tmp/a5_cost_arithmetic.py/json`（确定，`1C27DA82…`）。
- 菜单 A1–A8 与不可购买项（设计外剂量点、历史独立培养、靶点占据/机制读数、未见药化学实体、QC 免费信息、隐藏算力）；成本为 **planning CU 非货币**：central 1,600 keys anchored **569,568 CU**（setup 计入）/172,825（sunk）；cell setup 2,880 wells/cell 支配固定成本（charged vs sunk 差 2.5–5.2×）；等成本 100k CU 下整板 46 动作/5 细胞 vs anchored 277 键/22 细胞 vs 单剂量 20,985 键/30 细胞（形状差 ~450×）；核查算法=total CU 差≤最小动作+三场景排序一致+报物理量/有效独立单元（禁止等行数/keys/wells）。
- 固定更新器 U1（A1 M1）/U2 层级 EB/U3 GP；S0–S7 比较器；主指标=每成本单位未查询决策净收益；成本与检定力分离（MDE 由 n_eff/聚类、δ_min 由决策有用差异、MDE≤δ_min≤headroom）。
- 先例：decision-focused BOED/BATCHIE/GP-KG/EVSI/ENBS 已覆盖；"MDE 作 acquisition 闸"未发现直接先例（零命中仅记录）；三合一等成本比较未发现但属评估/工程组合，**不声称新颖性**。
- 项目内关键：R2 菜单 headroom **0.004343** ≪ CI 宽 ~0.145 → **该菜单不可检验 acquisition**（不推广到所有菜单）；P0 第 2 步未成立不执行；P2 headroom<MDE 直接停（`menu_near_oracle`）；停止类别成本/饱和/无增量/泄漏等写死。
- **Lead 处置**：A5 仅作为第 2 步（可迁移修订）成立后的执行设计；当前不冻结、不执行。挑战 T37（combocat-auditor）进行中。

## 2c2. R198-A1 挑战结论（lit-verifier，task-36）——revise（不 stop，但不得候选冻结）

- **总判决 revise（≤5 必改）**；构建性反例与"投影核等价控制必做"经复算成立；机制对象可证伪、边界披露诚实 → 可保留，但不构成新颖性。
- 最致命 3 条：① **X_flip 最小可辨识设计算术上不可能**：要求"≥2 独立上下文符号一致翻转 + 二项检验显著"，但 n=2 单侧最小 p=0.25（n=3 0.125、n=4 0.0625、n≥5 才≤0.05）→ 按现文永远判不出 (ii)，冲突必落 `not_identifiable`；须 n_min≥5 或功效推导+配对差/聚类置换+MDE/多重比较写死。② **分类不可证伪**：taxonomy 缺"噪声/模型错设/区间错估"第四解释（失败类别也无 `model_misspecified`）；M1 顺序规则（不可行→先试释放，廉价释放几乎总存在）**系统性偏向 (ii)**；`not_identifiable`/`ambiguous_conflict` 无预注册上限、无"人造 i/ii 注入恢复"体检；χ² 用 iid |S| 自由度（忽略 dyadic 依赖，C174 反例 ~10.33×）。③ **关系集不可执行/泄漏**：R_max 无数字、无 R_min/覆盖/稳定性/带宽验收；关系单位与 Cond_r 未定义 → 普通细胞异质性会被读成"关系失效"；S 与参考构造未显式 disjoint（同取 Original 即泄漏）；Jaaks screen/批次与"独立组"完全混淆 → C_conf/X_flip 无法区分关系失效与 screen 偏移；未声明与 R193-A1 的 estimand 差异（C174/C175 禁止"同一 96 细胞换聚合"）。
- ≤5 必改：① 判据可成立（n_min/聚类零/退出上限/注入体检）；② 分类可证伪（第四解释+多解释比较+χ² 依赖感知+σ 传播+ d_rel 降级）；③ 关系集可执行（R_min/max、池化单位/Cond、split-half 防 winner's curse、S 与参考 disjoint、screen 进 nuisance、非重聚合 lineage）；④ 机制对照补齐（M1 必比等式保护投影核+同区间无释放 constrained ridge+soft-penalty；"无释放=投影核"只对等式/无激活约束成立，区间版不等价；P1 改样本外防循环，P2 为主；M2 必比 VOI/decision-focused design 2602.05340/GoBOED/EVSI + Poke&Strike 差异；最小释放集近似/规模写死）；⑤ 协议可执行性（δ_min 成本/效用先于冻结否则 blocked、U 菜单/成本、预算时间、失败类别补 setup_error/ambiguous_conflict/design_invalid/proxy_only、标题 R198-A2→A1、Stage 1 只判 (i)/(ii)、(iii) 仅 proxy、与 A4 协调、措辞模板）。
- **Lead 处置**：A1 **暂不冻结**；先按必改 1–5 修订（task-40）+ 关系集 `relations_check` 验收 + constructive 设计体检 + MDE 预检 80% 后才重审候选冻结。A1 仍是当前最可行候选（相对 A2 有更新器接口与可执行签名），但"关系集资格"是硬前置。

## 2d. R198-A4（missing_state，drugcomb-auditor，task-27）——已完成；挑战 T39

产物：[spec.md](../2026-10-27-innovation-scouting/missing_state/spec.md)、[prior_art.md](../2026-10-27-innovation-scouting/missing_state/prior_art.md)、[protocol_draft.md](../2026-10-27-innovation-scouting/missing_state/protocol_draft.md)（DRAFT，未冻结/未运行）、record/usage（含 SHA；effect_run=false/training=false/novelty_claimed=false）。

- **三类失败定义**：F1 关系失效/适用条件失效（同一关系随已测背景 g 变，组内可重复，归因于 g，补状态无用）；F2 数值调整（残差零均值/尺度/标定问题，重标定后消失）；F3 表征遗漏关键状态（存在未被 φ 表示的、可测量状态 s，固定 x 内有决策相关变异，且不是已测 g 的函数/粗代理）。
- **三条签名**：Sig-A 条件偏移符号翻转可解释性（同细胞同条件对 O/V flip；嵌套 M0 噪声/M1 已知协变量/M2 K+S/M3 容量随机/M4 分组重拟合；F3 要求 flip>噪声地板、M2−M1 样本外 ΔAUC≥δ_min、置换 S 消失、分组重拟合/重标定不吸收）；Sig-B 表征外推距离–残差单调性；Sig-C 状态增广后未测动作改善（本轮不测）。判决表+措辞（F3 只到"该设定/该状态变量集上可复现、决策相关、不被已知协变量解释"；`inconclusive_design`；禁止只换模型名）。
- **可用变量（metadata-only 实测）**：Jaaks 125 细胞→DepMap 125/125、表达 **111/125**、突变 124/125、组织 3 水平、barcode 3,106（无日期/培养来源）、同 screen 培养代理 DAY1/GR/DT 97.7% 行；DepMap 表达 1,249×19,144、突变 1,666 细胞、sample_info 1,756（culture_type 749/medium 768/site 1,755/metastasis 1,103）；DrugComb v1.5 组织 2,313 细胞/34 水平（与 Jaaks 仅 49 共享细胞）；BeatAML 942 临床/707 表达（单药）；Mix-seq 285 键/115 细胞（单药、5 药物含对照、剂量/批次未认证）；PRISM 588 细胞/24 组织（单药端点）；BATCHIE 原始 19 细胞/372 板/20 iterations（本地数据目录空）；LINCS 473,647 sigs/76 细胞/12 时间点；Tahoe 50 h5ad block。
- **可立即检验**（只做预注册诊断/描述）：Jaaks O/V flip 率+噪声地板+已知协变量对照（96 细胞、92,039 controlled_anchor 观测、1,312 重复齐全回路）；状态距离–残差描述；同批状态代理关联；Mix-seq 时间描述；BeatAML 单药状态关联。**需新增测量**：同 (细胞,条件) 独立批次/日期/培养重复；per-measurement 培养；同一 (细胞,组合) 功能时间序列（≥3 点）；同批配对状态读数；跨 screen 规模复验（A3 修正后规格）。**不可检验**：体内/微环境/免疫/PK；靶点占据/通路因果；克隆/谱系/细胞周期状态；F3 因果结论。
- **功效边界**：A0 MDE80=0.240>δ=0.05；A1 MDE80_obs 0.2042>δ_min_obs 0.0893（n_eff≈189）；A3 仅冻结大规模门 not_qualified（41/4,179；ERRATA_A3 已限）→ 可立即检验若执行很可能 `inconclusive_power`，不得写 F3 不存在/表征无信息。
- **先例**：One-Hot News（identity shortcut/LCO/LDO）已覆盖；BATCHIE（cell embedding×drug、plate/QC、后验更新+PDBAL）部分覆盖（cell 状态=学出的 embedding，非可测状态；无遗漏状态检测）；PDTSyn 部分覆盖；DeepSynergy/Baptista/SynVerse/DIPx/Regulon/Tahoe LOCO/SynProtX/within-drug cell ranking 等近邻已覆盖；**"遗漏状态→诊断路由+补测动作"未发现直接先例（检索结果，非空白证明）**；相邻压力：普通残差/后验方差/leverage/距离、batch effect、无混杂敏感性、OOD 基准。剩余差异仅在程序对象（冲突残差三分+补测状态动作+决策相关验收）；若最强替代同信息复现则撤候选。
- **机制候选**：状态条件化冲突信号（SCC）——把 A1 冲突+A2 约束之外残差按已知协变量/状态/噪声三分，输出 F1/F2/F3 标签与"补测哪个状态/条件"动作；不替代更新器。P1–P5 可证伪预测；Phase 0 零新增测量诊断（预注册 δ_min=0.10/α=0.05/按细胞分组 CV/细胞聚类 CI；MDE>δ_min→inconclusive_power 停）；Phase 1 最小新增测量 **2 细胞系×2 状态操纵×6 条件对×2 独立批次×2 重复=192 孔**（可扩 384），对照=同批技术重复/state-matched/K-only/重标定/分组重拟合/容量置换/逻辑约束；Phase 2 仅在支持后做决策实验。失败类别 `numeric_only`/`relation_invariant`(F1)/`missing_state_supported`(F3)/`state_irrelevant`/`inconclusive_power`/`manipulation_failed`/`confounded` 已写死。
- **缺口**：直接先例需系统补查（DECANT/State 全文）；执行需 Lead 冻结 PROTOCOL_A4+独立挑战（预计 Phase 0 可能 inconclusive）；Phase 1 需真实预算；A4 依赖 A1/A2 先有可冻结定义（否则只能诊断/描述）。

## 2e. R198-A3（dynamic_route，cellstate-lit，task-26）——完成；资格 `design_data_partial`；挑战 T41

产物：[qualification.md](../2026-10-27-innovation-scouting/dynamic_route/qualification.md)、[spec.md](../2026-10-27-innovation-scouting/dynamic_route/spec.md)、[protocol_draft.md](../2026-10-27-innovation-scouting/dynamic_route/protocol_draft.md)、[cadence_evidence.md](../2026-10-27-innovation-scouting/dynamic_route/cadence_evidence.md)、a3_meta.json/a3_inspect.py/record/usage。

- **285 键复核通过（双源一致）**：h5ad obs 与旧 census 在 `(perturbation,cell_line)×time∈{6,24}` 完全一致；BRD3379 98 / Bortezomib 24 / Idasanutlin 24 / Trametinib 24 / control 115；115 细胞系；QC-normal ≥10 细胞/键=282/285（3 键需剔除/设门槛）。
- **资格判定 `design_data_partial`**：可做**群体层时间预测开发（L1）**；**决策层不可执行（L2）**——无独立功能结局（obs/var 无 viability/apoptosis/GR/IC50；obsm/layers/uns 空）、无 batch/plate/run 列、剂量单值（Tram 0.1/BRD3379 0.0 与处理矛盾/Bortezomib 2.5/Idasanutlin 2.5 µM）、6h channel 全缺失/24h 部分缺失→时间与 plate/channel 混淆未排除；**不得声称动态世界模型/真实轨迹已支持**。
- **新发现（旧轮未拆）**：hashed 子实验可恢复 per-cell 处理/时间——`time="3,6,12,24,48"` 的 20,028 Trametinib 细胞中 17,553 single-tag（Tram/DMSO 各 5 时间点 + Untreated_48hr；2,339 combo、136 unresolved）；**24 细胞系在全部 5 时间点对 Tram 和 DMSO 均有细胞**（focal24；中位 55 细胞/条件，normal-QC 中位 42）→ 本地不只有 6h/24h 两快照，还有**单药 5 时间点 + 时间匹配 DMSO** 的 hashed 子实验；但 `perturbation` 字段把 DMSO 也写成 Trametinib、dose 全 0.1、hash_tag vs hash_assignment 2,475 细胞不一致。
- **动态量→决策映射（Q1–Q10）**：Q1 早期→晚期持续性（6h 能否替代 24h→D-C 继续/换药）；Q2 早期 vs 晚期细胞系排序（→D-B/D-C responder 名单）；Q3 药物排序时间依赖（仅 4 药，功效低）；Q4 处理×时间交互（→动态特征跨药迁移）；Q5 时间匹配对照漂移；Q6 细胞系×时间交互；Q7 状态组成/细胞周期转移（需表达+注释）；**Q8 可逆性/洗脱、Q9 剂量×时间、Q10 真实路径：本资产不支持**。
- **设计**：L1 可做（V1 6/24h 4 药+对照 115 系/285 键、留细胞系/留药两快照；V2 hashed Tram 24 系×5 时间×DMSO、留时间点；C0 均值/C1 静态/C2 6h-only/C3 两快照拼接/C4 线性-低秩-ODE/C5 oracle；按细胞系分组切分；先报可靠性上限与 room）；L2 决策层需新测量（同细胞系×同药×同剂量×6/24/48h 独立功能读数、时间匹配 vehicle、≥3 复孔×≥2 独立培养，决策/效用/δ_min/MDE 预注册）。
- **功效要点**：独立单位=细胞系（24/115），不是键/细胞；本资产无 replicate → 不能细胞分半估生物学 SD；先算 split-half 可靠性上限与 MDE（cluster bootstrap 按细胞系），room<MDE 或 MDE>δ_min → `evaluation_cannot_distinguish`；禁止把 key/细胞当独立 n。
- **CADENCE**：可识别性依赖 DFA/COA/MRA+PR/FOA；FOA 要求入组时间跨区间、单点塌缩即失败；本资产仅 2 精确点（或单药 5 固定点）、无 linkage、无 batch → **不能当真实路径**；流匹配/插值 t 不是物理时间。
- **失败类别**：`data_unavailable`/`design_invalid`/`identifiability_unsupported`/`evaluation_cannot_distinguish`/`no_increment`/`decision_irrelevant`/`batch_confounded`；资格门不过不跑；L1 无增量停动态取证；预测改善但决策无改善停预测层；不换名重启。
- **Lead 处置**：A3 作为"另问"的 L1 开发资产保留（群体时间预测），不进入决策层；挑战 T41（drugcomb-auditor）进行中。

## 2e2. R198-A2v2（约束库/constructive 体检模块，lit-verifier，task-38）——完成，待挑战

- 产物（新增，v1 未改）：[spec_v2.md](../2026-10-27-innovation-scouting/logic_constraints/spec_v2.md)、[protocol_draft_v2.md](../2026-10-27-innovation-scouting/logic_constraints/protocol_draft_v2.md)、[REVISION_A2.md](../2026-10-27-innovation-scouting/logic_constraints/REVISION_A2.md)、record_v2.md、usage_v2.json、qa2_summary.json + 3 条 general-ML 查询。
- **5 必改落实**：① 主实验=**constructive 判别体检**（人造 I/II/III/null 注入；4 预注册终点 E1 I vs {II,III} 平衡正确率≥0.80、E2 II vs III≥0.70、E3 null 假类≤0.10、E4 unresolvable≤0.25；MDE 模拟不过→design_uninformative）；真实 replay 仅次级且**不报归因正确率**；C3→R196v2、C5→R197v2。② 三统一：drug-level 5 折×13 药（seed 20261027，folds 待生成；每折 both-unseen 药对 45/66/72/82/108、单元 1,898–6,232）、Ref/S/E/U 四集合不相交；端点固定 `SYNERGY_DELTA_EMAX`；注释只用 GDSC 每臂单标签（ANCHOR_PATHWAY 17/LIBRARY_PATHWAY 21；TARGET 40/58），P-A2 不用。③ 预算-功效表：k=6 仅 I vs null、k=12 II 不达、k=24 I+II、k=36 I+II+III constructive；replay 固定 k=24。④ 接口去重：replay 主判定=A1；A2 只交 constraint_id/group/stat/CI/null_p/bh_q/sign_flip_contexts/in-out 单元/候选状态/固定探针（JSON schema 冻结）；K_A2 vs A1 一致性 Cohen's κ≥0.60 记 interface_consistent，冲突→interface_disagreement、不取单一归因、A2 让位 A1；III→A4、acquisition→A5；引 C176/C177 作废状态。⑤ 补 1 有界 general-ML 检索（260/6/30 命中，未发现直接匹配→"有界检索未发现、不声称空白"）；A2 不再自定三修订模型（由 A1 接口契约定义）；C1′ 降为 QA（仅 13 个 size-2 组，功效不足）；不重开 R2 KG；constructive 先于 replay。
- 剩余缺口：constructive 模拟器/MDE 代码、folds.json/constraints_check.json 未生成（冻结清单项）；A1 schema 未联调；A4 状态资源未知；真实 replay 无标签只能描述；折不均衡（45–108 对/折）。A2 **不单独冻结**，等 v2 独立挑战后并入 A1。
- **Lead 处置**：挑战 T42（i003-challenger）派发中；通过后并入 A1 整体冻结。

## 2e3. R198-A2v2 挑战结论（i003-challenger，task-42）——revise；完成必改 1–4 后可并入

- 总判决 **revise（≤5 必改）**；A2v2 的五条 v1 必改落点真实（主实验=constructive、replay 次级不报正确率、C3→R196v2、C5→R197v2、端点/注释统一、C1′降 QA、general-ML 有界检索、引 C176/C177）；独立复算命中 drug-level 5 折每折 13 药、both-unseen **有向**药对 45/66/72/82/108、单元 1,898/3,693/3,588/4,613/6,232、331 pathway-pair 组/≥4 药对 165 组/1,698 对/90,589 单元、65 药/125 细胞/2,025 有向对/108,259 单元。
- 最致命 3 条：① **III/E2 构造上不可达**——III 注入随机 z（2 水平）与元数据无关、K_A2 判别器看不到它；E2（II vs III≥0.70）要么 chance 要么靠未定义"残差结构"硬判；须把 z 注入为**可观测但未进模型的元数据变量**，或预注册可观测残差结构统计量（潜类/双峰/方差比），否则删 E2/降 constructive_partial。② **预算表算术冲突**——spec_v2 §4.5"全三类单批 ≥38（6+20+12）"与同表 k=36 可做 I+II+III（12/12/12）矛盾；k=24 的 I+II（12/12）装不下 6+20=26；须给每 k 显式单元分配/复用规则。③ **MDE 与 δ_min 单位混用 + abstention 记账未定义**——MDE 是可分辨正确率差，不能与目标水平 0.80/0.70/0.10/0.25 直接比；E1/E2 的 balanced accuracy 分母未定义（含/不含 unresolvable；按 resolved 25% abstention 可刷高；null 上 abstention 无约束）；须预注册 abstention 计错/计分母与 null 上限。另 2 处：④ U/S"按药对不相交"与定义矛盾（S⊂U），U 必须排除 S 涉及药对并给每折 U 大小；⑤ "药对"有向/无序未写死（45–108 为有向，无序 33/49/48/49/58；2,025 有向 vs 1,294 无序），须统一并双口径报告；接口 κ≥0.60 只作兼容性检查（A2 借用 A1 的 X_flip≥5/δ_scope=0.20，不独立、不能互相当验证）。
- ≤5 必改：① 修 III/E2（可观测 z 或残差结构统计量）+ E1/E2/E4 abstention 记账；② 重写 k=6/12/24/36 预算-功效分配表（消除 38 vs 36、26 vs 24 冲突）+ constructive 模拟器规模/≥500 批/单命令≤30 min 核算 + II 的"≥5 独立语境"生成定义；③ MDE 与 δ_min 同单位化 + 模拟器/MDE 代码落盘；④ 统一药对单位并修 U/S 不相交定义（U 排除 S 药对，给每折 U 大小）；⑤ 接口 schema 版本化、κ 仅兼容性检查、补 folds.json/constraints_check.json/生成器代码、保持 C1′ QA 与 replay 不报正确率/收益。
- **Lead 处置**：A2v2 仍**不单独冻结**；task-43（A2v3 修订，lit-verifier）在完成必改 1–4 后并入 A1 整体冻结；当前不并入。

## 2d2. R198-A4 挑战结论（endpoint-auditor，task-39）——独立候选 stop；A1 的 (iii) 模块 revise

- **总判决**：作为独立候选 = **stop**（当前形态不得进入候选冻结）；作为 **A1 的 (iii) 状态模块** = **revise（≤5 必改）**，修完重审后可模块冻结，但**不得独立下发 F1/F2/F3 判定**。
- 最致命 3 条：① **F1/F3 在 Phase 0 结构性不可分**——`flip=1[sign(Q_O)≠sign(Q_V)]` 本身是跨唯一两组 O/V 的差异；F1 对照 `M4=K+g` 的 g 在单位级不存在（每单位同时含 O、V），按 g 分层/组内重拟合对 flip 无定义；cell 级静态 S 只能检验"state-associated instability（必要非充分）"，不能判 F3；要分离需 ≥3 独立 context 或 within-cell 状态操纵（Phase 1），而 Phase 1 又被写成 Phase 0 显著之后 → 预期 `inconclusive_power` 变程序性死锁。② **可用性被高估**：A4 报"111/125 有表达"，但 Phase 0 实际 matched 96 细胞中**表达 84、突变 95、culture_type 54、culture_medium 55，联合仅 54**；`DAY1/GR/DT` 每细胞中位 **4 个不同值**（随 barcode/板变化）=同 screen 对照读数，按 A4 自己的 F3 定义不能当 S；**A0 MDE=0.240 已被 C168 更正为五折主端点 0.112**（0.240 是各折均值），**1,312 是 A2 q2.json 的 barcode 分半标定数（同 screen、1.43% 覆盖）而非 A0**；δ_min=0.10（ΔAUC）无 operational 依据（C177 教训）。③ **Phase 1 算账/功效/桥接不成立**：`2×2×6×2×2=96` 不是 192（192 只有把"每条件对=2 孔"写死才成立，A4 未写）；`4×6×2×2×2=192` 不是 384；两版都不含单药参照/对照，而 A4 用 ΔEMAX 端点（按 A5 成本模型 anchored key 34–68 wells/key，真实孔数至少 combo 的 2–4 倍）；2 细胞×6 条件对=12 个 pair-cell 单元，state×sign 交互无功效预计算；操纵的密度/培养基/氧与 Phase 0 的 S（表达/突变/培养注释）无桥接，且培养基/氧本质是测量背景 g → 有把 F3 测成 F1 风险。
- 六项：① F1/F2/F3 可区分性 **FAIL**（M4 不可执行、flip 噪声地板是同 screen 技术噪声、"flip>噪声"不能作 F3 判据、缺 cell one-hot/plate 基线、`inconclusive_design` 分类缺失）；② 可用变量与功效 **WEAK（含 2 FAIL 子项：覆盖/粒度、A0/1312 归属）**；③ 先例/差异 WEAK（One-Hot/BATCHIE/PDTSyn 判定成立、不声称新颖性=PASS；但 usage 写 browsing=false，本轮无检索回执而 prior_art 称"有限检索"→ 需补 query log 或降级；缺 identity/one-hot 与 latent-confounding/batch 文献补查）；④ 最小实验 **FAIL**（Phase 0/Phase 1/Phase 2）；⑤ 接口/去重 WEAK（与 A1 P6/P7、A2 III 同一套三类失败两种操作化；protocol 用 Q flip 而 spec 说 SCC 用 A1 冲突证书，对象不一致；A1 挑战 revise 未冻结、A4 无启用门；缺 C174/C176/C177/A5 引用）；⑥ 总判决如上。
- ≤5 必改：① 写 ownership table：A4 收为 A1 的 (iii) 模块（A1 冻结后启用），二选一写死输入（A1 证书/改名后的 Q-flip），删 SCC 歧义；② 重写 F1/F3 判据：Phase 0 只作 state-associated instability 描述/筛选，M4 改 K+barcode/plate+screen，补 cell one-hot/identity、plate/barcode、leverage 基线，flip 阈值由噪声模型预注册、噪声地板分层披露，"Phase 0 inconclusive ≠ F3 不存在/表征无信息"，Phase 1 不以 Phase 0 显著为条件；③ 改数字：matched 96 的 per-variable 覆盖（84/95/54/55、联合 54）、S 拆 S_pre/S_measure、A0 MDE 0.112（C168）、1,312 改引 A2 及 1.43% 限制、δ_min operational 化、MDE 模拟写死维数上限（EPV）/seed/聚类；④ 重写 Phase 1：完整 well 账（combo+单药参照+对照+QC，与 A5 cost_model 对齐）、12 单元功效或扩到 4–6 细胞系、操纵↔state readouts 桥接、补 vehicle/positive/edge/blinding/独立培养认证、失败类别补 `inconclusive_design`/`leakage`/`indistinguishable_F1_F3`；⑤ 先例/去重/措辞：补检索 query log 或明确"本轮无新检索"、逐条标注与 A1 P6/P7、A2 III、R197/C177、A5 重叠、引用 C174/C175/C176/C177、Phase 2 复用 A5 等成本设计、修正"192 孔"表述与措辞模板。
- 保留项：三类失败 operational 定义（spec §1）、spec 强制措辞、状态变量清单框架、先例诚实性、Phase 0 零新增测量思路、Phase 1 对照清单方向、"阴性不写不存在"纪律、不是 A1 通过/不重估 A1/不启动 B/C 边界。
- **Lead 处置**：A4 **收为 A1 的 (iii) 状态模块**（不独立候选）；task-44（A4v2 修订）派 drugcomb-auditor（完成 T41 后）；修订后由**未参与**挑战者复审（endpoint-auditor 已挑战过，需另派）。同时 A4 文档中的 A0 MDE 0.240→0.112、1,312 归属等事实错误须在 v2 修正。

## 2f. R198-A5 挑战结论（combocat-auditor，task-37）——revise（不 stop，不冻结）

- 总判决 **revise（≤5 必改）**；A5 保留为第 3 步执行设计候选稿，**当前不冻结、不执行**（P0 第 2 步前置目前不存在，只能"冻结不执行"）。
- 六项：① 菜单/成本 **WEAK（含事实错误）**；② 比较器/更新器/指标 WEAK；③ 先例/headroom WEAK；④ 可执行性/停止 WEAK；⑤ 谱系/纪律 PASS（小改）；⑥ revise。
- 最致命 3 条：① **成本物理锚点两处事实错误**——(a) A2/A3 的"12–38 单药参照+8–16 对照 wells"恰等于 Jaaks 每板锚点数，却被按**每 key** 计费、同时按 eta=0.6 打包多 key/板；按 A5 自己系数粗算 anchored campaign central CU 569,568→≈446,000（−21.7%，示性）；(b) R2 实测动作=2 板/766 wells（99.7% 利用率），但 price_plan 仍乘 eta=0.6 → 4 板/动作，等成本表 46 动作=168 板 vs 物理 92 板；文档数字也不符：setup charged/sunk 实际 2.77/3.30/52.28/6.78/11.42×（非"2.5–5.2×"）、C136 距离 5.70–6.21×（非 5.8–6.3×）、"450×"混了 sunk/charged 口径（同口径 charged 8.4×、sunk 381×）。② **等成本比较不可执行**：cell breadth 未冻结（100k CU 表隐含 plate 5 cells / anchored 22 / single-dose 30 cells → 不同细胞集合不可比，违反"同一菜单/信息"）；残余预算 filler 未写死；三场景是否按各场景预算重跑策略未写死；S1 的 13×125 C136 固定设计在 100k CU central charged 下需 5.7× 预算，买不起。③ **headroom/MDE 推论过度 + oracle 可算性未声明**：把 R2 KG−random 的 CI 宽 0.1447 当 MDE（正态近似 MDE80≈0.715×CI 宽，高估 1.4×），并写"任何 acquisition 比较的 MDE 都大于 headroom"（全称未证）；R2 菜单结论方向仍稳健（headroom 0.004343 与 0.145 差 24–33×），但须改为可复算粗代理陈述并显式算 MDE；oracle/headroom 需全部菜单结果已知 → 只适用回溯 replay（未声明）；headroom 是 outcome 相关量，若允许"先算 headroom 再挑菜单"= 结果选择偏差，必须预注册纯元数据菜单构造。
- ≤5 必改：① 按真实板布局重推 A2/A3 参照/对照摊销（per-plate vs per-key 写死；实测动作不乘 eta），重算并修正三个文档数字；② 等成本可执行化（冻结 cell set/setup 会计/filler/容差/under-spend，三场景重跑；主指标改配对 ΔNB@equal CU，NB/CU 仅描述）；③ headroom/MDE 修正（CI≠MDE 并量化；删全称句；MDE_decision 按 P5 预计算；声明回溯 replay；菜单构造纯元数据、不得按 headroom 挑）；④ 预算/停止/失败类别（45 min 与 7 策略×2 seed×3 场景对不上，需时限表；补 oracle_unknown/cost_uncalibrated/protocol_deviation/not_identifiable，拆 inconclusive；δ_min 无 operational 定义则 `blocked_by_utility_definition`；P9 真实报价不可得时给"无量纲 CU 预算"可冻结形态或保持 blocked）；⑤ 谱系/措辞（显式不重开 R187 方差采样、R2 菜单结论只作约束；补引 C176/C177；统一"未发现≠不存在"与 planning-only 模板）。
- 先例/新颖性：decision-focused BOED/BATCHIE/GP-KG/EVSI/ENBS 覆盖判定基本成立；"三合一等成本比较未发现直接先例"被正确标为评估/工程组合、不声称新颖性——PASS；只需把"未发现"写成有界检索结果。
- 附注：A5 usage 记的 SYNTHESIS hash（5FD693D1…）与当前（4499C5EB…，含 C176/C177）不同，冻结前应更新边界引用。

## 2g. R198-A1v2 修订完成（combocat-auditor，task-40）——待复审

- 产物（新增，原 A1 五件未改）：[spec_v2.md](../2026-10-27-innovation-scouting/conflict_signal/spec_v2.md)、[protocol_draft_v2.md](../2026-10-27-innovation-scouting/conflict_signal/protocol_draft_v2.md)（DRAFT）、[REVISION_A1.md](../2026-10-27-innovation-scouting/conflict_signal/REVISION_A1.md)、[relations_check_design.md](../2026-10-27-innovation-scouting/conflict_signal/relations_check_design.md)、record_v2.md、usage_v2.json。
- **5 必改落实**：① 判据：n_ctx_min=12 独立上下文、每关系单侧 α=0.01、primary 关系族≤10、BH q≤0.10；MDE 写死（n=12 时 k≥11 精确 p=0.00317；p1=0.95→功效 0.882、0.90→0.659；预注册 MDE=真实一致翻转率≥0.95 时 80% 功效；更低 p1 须增大 n 不得放宽 α）；两独立评分流程裁决规则。② 分类：新增第四解释 `setup_error`/`model_misspecified`（区间覆盖诊断/σ 带翻转/异方差/批次吸收）；取消 M1 顺序规则→多解释惩罚拟合比较；χ² 依赖感知（细胞×药对双层块置换或 κ 方差膨胀，C174 警示）；σ 在带内须分类一致；d_rel 降描述量。③ 关系集：R_old∈[20,200]；每关系 n_ctx≥12；A/B 构造-校准半分离+半交换复核（方向一致率≥0.90）；区间只在校准半估、宽度≤min(2σ_r,0.10×决策效用范围)、|μ_r|≥0.5σ_r；覆盖候选单元≥50%、每 tissue≥3；Cond_r 纯元数据；S/参考/U 细胞三元不交（参考 84=A42/B42、S 24、U≈17）；screen/batch 进 nuisance、跨 screen 只作敏感性；补非重聚合 lineage（C174/C175）+MDE 预检；`relations_check_design.md` 给 Stage 0 可执行协议（分配/枚举/A-B 半切/bootstrap/区间/验收/SHA 冻结/失败=`data_unavailable`）+≤30 min。④ 机制对照：M1 必比 (a) 等式投影核、(b) 区间无释放 constrained ridge、(c) soft-penalty、(d) 尺寸匹配随机释放；写明"无释放=投影核"只在等式且无激活约束成立、区间激活为 QP 不等价；P1 改样本外诊断增量（防循环），P2 为主；最小释放集写死规模（|R|≤30 精确分支定界/LP 60 s，否则贪心+LP 下界报 gap；J_max=min(5,⌈0.10|R|⌉)，60 s 无认证→ambiguous）；M2 补 VOI/decision-focused/Poke&Strike 差异、Stage 2 必比 VOI/decision-focused、无合法区分测量必须拒绝购买。⑤ 协议：标题 R198-A1；P0a–P0d 前置全过才 Stage 1；**δ_min 未由成本/效用定义 → 冻结状态=`blocked_by_utility_definition`**（不冻结不编造）；U 菜单/成本（A5 修订前只 planning CU，C141 只排组合）；预算/墙钟写死（Stage 0 ≤30/20/15 min；Stage 1 每臂≤45 min 总≤2 h；bootstrap/置换≥2,000）；失败类别补 setup_error/model_misspecified/ambiguous_conflict/design_invalid/proxy_only/not_identifiable(+上限)/completed_null/pass_to_stage2；Stage 1 只判 (i)/(ii)/(setup)，(iii) 只 proxy_only（与 A4 协调）；措辞模板。
- 注入体检数字：每类 (i)/(ii)/(setup) ≥30 单元、效应≥MDE；recall≥0.80、precision≥0.80；置换零下假判 (ii)≤0.10；退出率 not_identifiable≤15%、ambiguous_conflict≤10%，超限→design_invalid 停。
- **δ_min=blocked**（成本/效用未冻结）；剩余缺口：relations_check/注入体检/MDE 预检未运行（下一轮 Stage 0 产出）；R_min=20/n_ctx=12 在 Jaaks 125 细胞可达性未知；MDE 需按实际聚类模拟确认；(iii) proxy 依赖 A4；A5 成本接口待修订；先例补充仅 additive。
- **Lead 处置**：A1v2 待复审（T46，同一挑战者 lit-verifier 在 T43 后复审）；通过后仍需 relations_check/constructive/MDE 三项结果才可候选冻结；δ_min 保持 blocked。

## 2h. R198-A3 挑战结论（drugcomb-auditor，task-41）——revise（不 stop；保留为"另问"L1 开发资产）

- 总判决 **revise（≤5 必改）**；核心数字全部独立可复现（285 键、per-drug 98/24/24/24/115、115 细胞系、双源逐元素一致、每键细胞数、normal≥10=282/285、channel 缺失、hashed 20,028=17,553 single+2,339 combo+136 unresolved、264 line-条件、字段冲突 2,475/9,945、24h-only 9 臂、PRISM 207/209、CADENCE 锚点全命中）；**未发现数据造假/数字错误**。
- 六项：① Mix-seq 资格 **PASS**；② 动态↔决策映射 WEAK；③ 设计草案 WEAK→需修；④ 先例 WEAK（CADENCE 正确，群体时间预测/虚拟细胞基准未覆盖）；⑤ 谱系/纪律 WEAK→需修；⑥ revise。
- 最致命 3 条：① **声明的 `spec.md` 不存在**（R198 record/task-41 都列为必读；A3 record/usage 未列）→ 资格可审、设计 spec 不可审，不能冻结；② **L1 设计无判定门且 C3 有泄漏风险**（L1 无 δ_min/MDE/room/split-half 可靠性门，仅 L2 有；C3"两快照拼接"若 V1 用 24h 作输入=目标泄漏）；③ **动态量→决策 3 处过宽 + 先例/边界不全**（Q2 responder 实为表达 proxy；Q5 误述"6/24 臂只有 24h channel 信息"——实际 control 6h/24h 均有测量，只是 channel/批次不匹配；Q7 需细胞状态注释却标 M；缺群体时间预测/虚拟细胞基准有界先例；缺 C174/C176/C177 边界引用）。
- ≤5 必改：1) 补 spec.md 或正式声明并入 qualification/protocol 并同步 record/usage；统一 kinetic_horizon 读取描述；2) 冻结 L1 δ_min/MDE/room/可靠性门（不过即 `evaluation_cannot_distinguish`），C3 仅 V2 第三时间点、V1 禁止目标时间入输入；3) 修 Q2（表达 proxy 不称 responder）、Q5（control 时间匹配存在但通道/批次不匹配）、Q7（M*/需新增注释），补"静态/两快照已足够"清单；4) 补有界先例（2604.27646 virtual-cell benchmark、CellFlow、State 等；未发现≠不存在、不声称新颖性）+ C174/C176/C177 边界 + 不重开 R196v2/R197v2；5) 统一记录/措辞一致性（保留"不得声称动态世界模型/真实轨迹/决策收益"；阴性不写不存在）。
- 保留：285 键 4 药+对照×115 系 6h/24h 与 hashed Trametinib 5 时间点+时间匹配 DMSO（24 系）可做预注册开发比较；**修完+未参与复审前不冻结、不运行**。
- **Lead 处置**：A3 保留为"另问"L1 开发资产（不进入候选、不进入 L2 决策层）；task-47（A3v2 修订）派 cellstate-lit。

## 2i. R196v2/R197v2 结果前预审（i003-challenger，T45）

- **R196**：① drug 主单位已预注册（§4 主 CI=drug-cluster 65 药双侧角色重抽、主 MDE80=2.802×SD、§5 硬条件 MDE80_drug≤δ_min；cell/pair/twoway/partition 降敏感性）；② ≥10 独立划分已预注册（10 划分×5 折、partition t-CI、50 折 non-independent sensitivity）**但 partition 级只进 sensitivity、不进 verdict** → 仍需补；③ 内层 λ 已统一（3 折 Spearman 算术平均、L_EXT/L_C130 双网格、H196b 配对 drug bootstrap）；④ δ_min/稳定带已 operational（δ_min=0.05 Kendall τ≈0.0318、与 drug MDE 硬联动、稳定带上界取消）；⑤ 措辞/披露部分（peek 披露不准确）。
  - **结果解释前必须补 AMENDMENT-002**：1) partition 级进判定（二选一：(a) partition 95% CI 下界>0 加入合取；(b) partition CI 含 0/符号不一致→最多 weakened；+写死 50 折非独立/两阶段或嵌套 bootstrap）；2) **E9 预算**：E9 冻结"单命令≤15 min"，当前 CPU/墙钟已超；按冻结规则 **wall>15 min → E9 不通过 → verdict `inconclusive`**（不得事后改 deviation 放行），需在 verdict 落盘前写 AMENDMENT-002 声明后果并记录 wall/CPU/缓存路径；peek 披露须更正：v1 已跑出 r196.json 并撤回，**v2 是已知 v1 结果的审计重分析，不是盲验/独立复现**。小项：E7 与 §5 判定门关系；identity 常数 50 折论证；rowlevel_c130_grid 折内 scaler 与 v1 折前 scaler 差异（桥接诊断限定）；Kendall 换算近似。
- **R197**：① 方案 Q/主设计已预注册（H197c 随机条目主设计+B2 主模型；H197a/b 降次；verdict 改 low_rank/no_stable；范围不冷迁移/不反馈/不选药）；② 特征-端点构造重叠/块消融已预注册（B0→BM→BMono→B3；B2 无特征；beyond_prepurchased_features Δ(B2−BMono) CI>0 + B2≥max(...) 点比较）；③ δ_min operational 已预注册（0.10×sqrt(rel_entry)、rel_entry=1−share_noise、A0 先于 B、禁 0.868/旧 CI、不可计算→inconclusive）；④ A0 依赖降级+键级 V5 4,686 键已预注册；⑤ 措辞/谱系/预算/SHA 部分，**type-I 精确性不足**。
  - **结果解释前必须补 AMENDMENT-003**：1) **type-I CP 上界规则**：点≤0.05 不能认证（1/20 触发不了追加；CP 95% 上界≈0.216，0/20≈0.139）→ 设计体检项 = **CP 95% 上界≤0.10**，不满足→按预注册上限追加模拟，仍不满足→`inconclusive`（或预注册最小 sims 40 全 0/47 ≤1）；2) **Δ_primary 配对 bootstrap**（同一次 resample 同时算 B2/B0 的 Spearman 再取 Δ；两模型同测试条目/同 OOF 折）。小项：H197c OOF 拼接尺度 → 每折 Spearman 均值/折内标准化敏感性；record 记 wall/CPU。
- **Lead 处置**：已向两 runner 发结果前补 AMENDMENT 指令；R196 若 wall>15 min 将按冻结规则直接 `inconclusive`（即使 drug CI 正），这是纪律而非结果偏好；R197 补 type-I/配对 bootstrap 后再判。两者结果出来后 i003 立即 T32/T34 结果审。

## 3. Lead 调度规则

1. 先到先挑战：A2 spec 挑战与 R196v2/R197v2 挑战按优先级排队（R196v2/R197v2 是核心证据，优先）。
2. A1/A3/A4/A5 完成后各给一段摘要 + 挑战任务；所有 scout 在挑战通过前不得进入"候选冻结"。
3. 候选冻结只允许一个：依据可证伪性、现有数据可检验性、与三类失败的对应度、先例剩余差异。
4. 不启动 acquisition 效果、不写机制/迁移/决策收益、不晋升代码。
