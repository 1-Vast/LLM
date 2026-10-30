# PROTOCOL_DRAFT_v2 — R198-A1（关系冲突信号与三类失败区分）草案

**状态：DRAFT，未冻结、未执行。** 本文件是 [protocol_draft.md](protocol_draft.md) 的修订版（原文件保留），按 [challenge_A1.md](challenge_A1.md) 的 5 条必改修订；机制/统计定义见 [spec_v2.md](spec_v2.md)，关系集资格见 [relations_check_design.md](relations_check_design.md)。**本轮不运行、不训练、不读响应做效果。**

## P0 冻结前置（四项全过才允许进入 Stage 1；任一不过 → 记录失败类别，停）

- **P0a 关系集资格**：执行 `relations_check_design.md` 的协议，产出 `relations.csv`/`relations_check.json`（SHA 冻结）。**通过条件**（写死）：`R_old` 条数 ∈ [20, 200]；每条关系独立上下文 ≥12；构造半/校准半方向一致率 ≥0.90 且半交换后仍通过；区间宽度 `≤min(2.0σ_r, 0.10×决策效用范围)`；关系覆盖候选单元空间 ≥50%；两半细胞组不重叠。失败 → `data_unavailable`。
- **P0b 设计体检（constructive，注入类恢复）**：用与真实数据同结构的人造反例（不读真实响应；用参考统计量生成）注入判类流程：每类 (i)/(ii)/(setup) 各 ≥30 个单元、效应量 ≥ 预注册 MDE；**通过条件**：每类 recall ≥0.80 且 precision ≥0.80；置换零下假判 (ii) ≤0.10（type-I 校准）；`not_identifiable`+`ambiguous` 退出率 ≤ 预注册上限。失败 → `design_invalid`（不得改判据继续）。
- **P0c MDE/功效预检**：按 Stage 1 主指标（未查询决策损失）与预注册聚类（细胞/药对）模拟完整流程；**要求 80% 功效（±0.05）于 δ_min，type-I ≤0.10**；同时报告独立单元数（不把匹配四元组名义数当独立 n；C171 教训）。失败 → `insufficient_precision`，停，不救。
- **P0d δ_min 与成本/效用**：δ_min 必须由**决策有用差异**定义（单位=未查询菜单 U 上的效用/损失；由 A5 成本接口与任务价值推导），在接触 S/U 响应前写死；**若成本/效用不可得 → 冻结状态=`blocked_by_utility_definition`，不得进入效果轮、不得编造数值**。
- 依赖：P0a 的两半切分与 §P2 的参考/S/U 细胞组不交叠规则一致；A4（missing_state）若给出可测状态，才允许将 (iii) 从 `proxy_only` 升级；A5（acquisition）冻结前 Stage 2 不启动。

## P1 任务对象（冻结字段）

- 端点 y：`SYNERGY_DELTA_EMAX`（或经 P-B/P-B2 同意的等价物；换端点=换轮）；附可比性/饱和性/可靠性记录。
- 单位 `u=(c,p,d)`；c 的细胞组标签 g(c) 由元数据（组织+预注册细胞分组）定义；p 有向（anchor→library，方向写死）；d = 已发布设计列（`ANCHOR_CONC`/`LIBRARY_CONC`；完整剂量点集不可得时只用设计列）。
- 表征 φ：购板前可得（细胞基线特征[DepMap 19Q4 表达/拷贝数/突变，须先冻结算子]、药物/药对粗注释、组织、设计元数据）；**不得含反馈/不得用 S 或 U 选特征**；φ 算子/特征清单/缺失处理的 SHA 在 P0 前冻结。
- 反馈批 S：响应盲抽取（固定 seed，元数据分层）；规模由 P0c 决定；S 的键集合 SHA 在接触 y 前冻结。
- 未查询菜单 U：固定动作集合（**只排组合、不排细胞**，C141）+ 成本表 + 效用函数；U 的动作数/成本/效用候选值见 P2；U 读数代码级隔离（独立 runner）。
- 预算/成本：Stage 1 使用 A5 成本接口（planning CU；A5 正按 challenge_A5 修订）；本协议允许的替代口径 = "固定反馈批 + 固定计算预算"（不用货币），并写明**不写货币结论**。

## P2 参考/S/U 切分与关系冻结（写死）

1. **细胞组切分**：参考 R 细胞组、S 细胞组、U 细胞组两两不相交（主设计）；同一 screen 内切分，screen/batch 作为 nuisance（batch/barcode 随机效应或协变量）进入更新器与 f_old。跨 screen（Original→Validation）只作敏感性并披露"screen=独立组"完全混淆。
2. **关系集**：按 [relations_check_design.md](relations_check_design.md) 生成：`R_old` ∈[20,200] 条；每条 `(a_r, l_r, u_r, Cond_r)`；n_ctx ≥12；两半方向一致率 ≥0.90；区间宽度验收；关系表 SHA 冻结在接触 S/U 响应前；**不得用 S 增删关系**。
3. **关系单位**：`a_r` = nuisance-正交 dyadic 对比（Q 型）；`Cond_r` = 元数据可判定字段（细胞组标签/方向/`ANCHOR_CONC`/`LIBRARY_CONC`/端点）；S 单位是否 ∈Cond_r 的判定规则写死；out_of_cond 单位不计入也不判失败。
4. **构造/校准半分离**：关系方向只在构造半选、区间只在校准半估；半交换重跑，两次都过才进入 `R_old`；种子冻结（防 winner's curse）。
5. **S 抽取**：响应盲、元数据分层、固定 seed；代码与 S 键 SHA 在 P0d 后、接触 y 前冻结；抽取规则不得使用 R_abs/C_conf/U。
6. **U 隔离**：U 的 y 由独立 runner 持有；实现层断言：Stage 1 判定前任何读取 U y 的代码路径直接报错并判 `leakage`。

## P3 更新器与机制对照（同一 S、φ、预算）

- **更新器（固定）**：M1 PRU-CC（[spec_v2.md](spec_v2.md) §8）：`θ_new=argmin ||W_S(Φ_Sθ−y_S)||²+λ||θ−θ_old||² s.t. l≤Aθ≤u`；λ 由参考集内层药物分组 CV 选（网格写死）；τ_r 噪声容差；关系区间来自 P2。
- **必比对照（同信息/同调参预算/同算力）**：
  1. 等式保护投影核（AlphaEdit 精确对应）；
  2. 同区间无释放 constrained ridge（隔离"释放"与"约束"）；
  3. soft-penalty/层级先验（关系作为惩罚）；
  4. 尺寸匹配随机释放（随机释放 |J_min| 条同代价关系）；
  5. 全量重训、普通适配/微调、层级经验贝叶斯、多输出 GP。
- **等价性声明**：M1 无释放只在"等式约束且无激活约束"时等价于投影核/普通 ridge；区间约束有激活时为 QP，**不得要求数值等同**，只做 KKT/实现自校验并报告差异。
- **释放求解**：|R_old|≤200；精确最小释放（|R|≤30，分支定界/LP，60 s/单元）或贪心+LP 下界；`J_max=min(5,ceil(0.10|R_old|))`；60 s 无认证 → `ambiguous_conflict`；解/gap/时间入账。
- **禁止**：策略/更新器自带额外特征或调参；用 S/U 结果选 λ/阈值/关系；基线被冻结以制造优势。

## P4 判定流程（Stage 1 只判 (i)/(ii)/(setup)/(ambiguous)；(iii) 只 proxy）

1. 四解释候选模型族 M_i/M_ii(J)/M_setup（M_iii 仅 proxy），同一数据/预算下按预注册惩罚拟合准则比较（样本外拟合 + 复杂度/代价 + Δ_pred(U)）。
2. 判类规则：M_i 领先 → (i)；M_ii(J) 领先且通过 **X_flip（n_min=12、α=0.01、BH q≤0.10）+ C_conf + J_min 稳定性** → (ii)；M_setup 领先 → `model_misspecified`（setup_error）；差距小于 δ_fit 或对 U 预测不同 → `ambiguous_conflict`；无法估 → `not_identifiable`。
3. **禁止顺序默认**：不得"不可行→先选最便宜释放→判 (ii)"；释放廉价不是 (ii) 的证据；必须多解释比较 + 尺寸匹配随机释放 + soft-penalty 对照。
4. **依赖感知 χ²/σ**：χ² 阈值用细胞×药对双层块置换/聚类零分布或 κ 膨胀方差（κ 从参考估，C174 警告 dyadic vs iid 可达 ~10.33×）；σ 在 `[σ_lo,σ_hi]` 带内必须分类一致，否则 `ambiguous_conflict`。
5. **两独立评分流程**（签名统计 vs M1 拟合证书）不一致的裁决：预注册规则 = (a) 若一方为 `setup_error` 且区间覆盖/σ 敏感性支持 → setup；(b) 若签名统计支持 (ii) 但 M_ii 未领先 → `ambiguous_conflict`；(c) 其余不一致 → `ambiguous_conflict`。没有第三方事后仲裁。
6. **X_flip 的 n_min/MDE/多重比较**：n_min=12 独立上下文；每关系精确单侧符号检验 α=0.01；预注册 primary 关系族 ≤10 条（BH q≤0.10），其余 exploratory；MDE=真实一致翻转率 0.95 时 80% 功效（n=12 时 P(X≥11)=0.882）；若预期更低 → P0c 模拟增大 n，不得事后放宽。

## P5 主指标、δ_min、MDE（冻结模板）

- 主指标（Stage 1）：**未查询菜单 U 上的配对决策损失** `Δℓ = ℓ(对照) − ℓ(M1)`（正=改善），按细胞/药对聚类 bootstrap（≥2,000 次，固定 seed）；报告 CI、n_eff、ICC。
- 次指标（不参与判定）：regret、hit@k、分类稳定性、释放集规模、`C_conf`/`X_flip` 描述、成本/耗时。
- δ_min：**必须由成本/效用定义**（决策有用差异；单位=U 的效用/损失），P0d 前写死；`MDE_decision ≤ δ_min`；δ_min ±50% 敏感性；禁止旧 CI 反推。**未定义 → `blocked_by_utility_definition`（不冻结）**。
- MDE_decision：由 P0c 的 80% 功效模拟给出（决策指标、聚类、预算）；C136 的 1,600 keys→80% 只是"数据量级锚"，**不得当决策指标 MDE**。

## P6 失败类别与停止规则（v2 写死）

| 类别 | 触发 | 动作 |
|---|---|---|
| `data_unavailable` | P0a 关系集不达标 / φ / S/U/成本无法冻结 | 停；列缺项与所需测量/资源 |
| `insufficient_precision` | P0c MDE>δ_min 或功效<80% | 停；不判阴性；报所需独立单元 |
| `design_invalid` | P0b 注入体检失败（recall/precision<0.80 或 type-I>0.10 或退出率超上限） | 停；不得改判据继续 |
| `model_misspecified`（setup_error） | 区间覆盖不足/σ 带翻转/异方差/批次吸收 | 先重估；重估后仍违例才可进 (ii) |
| `not_identifiable` | 单上下文/独立测量组<2/状态不可测/无合法区分测量 | **上限：≤15% 单元**；超限 → `design_invalid`；必须附追加测量/预算 |
| `ambiguous_conflict` | 多解释对 U 预测不同 / J_min 不唯一 / 两流程不一致 | **上限：≤10% 单元**；超限 → `design_invalid`；必须附可区分测量清单 |
| `explained_by_baseline` | 诊断/释放增量被 R_abs/L_lev/后验方差/投影核/尺寸匹配解释 | 撤诊断/机制主张，保留描述 |
| `conflict_only_in_development` | 只在开发臂成立、跨 screen/细胞组不复验 | 不写"可迁移" |
| `proxy_only` | (iii) 只有代理 signature；无可测状态 | 报告代理，禁止"三类已区分" |
| `leakage` | 任何路径使用未购/U/QC/terminal 信息或 S 的 y 进了关系构造 | 整轮失败，不救 |
| `pass_to_stage2` | Stage 1 配对 Δℓ CI 下界>0 且 ≥δ_min、优于全部对照、P0b/P0c 通过 | 才允许 Stage 2（M2 对照含 VOI/decision-focused） |
| `completed_null` | 正确执行的 Stage 1 未达 pass（CI 含 0 或 <δ_min） | 记无增量（负结果）；不写"关系不存在" |

## P7 泄漏/公平/新鲜度（写死）

1. 参考/S/U 细胞组两两不交；S 响应盲抽取；S 键 SHA、U 键 SHA、φ/关系表/δ_min/预算 SHA 全部在接触 y 前冻结。
2. 关系构造只用参考集 half A/B（与 S/U 无关）；禁止用 S 增删/加权关系。
3. 所有对照同信息同预算；λ/超参网格共用；算力（CPU/wall）入账。
4. 必做负对照：置换冲突标签（打乱 relation↔unit 映射）、尺寸匹配随机释放、常数/无更新、随机特征块。
5. U 读数隔离实现 + 失败即 `leakage`；独立 runner 评分。
6. 报告 planned/observed 分离；不换端点/分层/δ/关系；不按结果调判据。

## P8 预算、时间与计算

- Stage 0：relations_check ≤30 min；constructive 体检 ≤20 min；MDE 预检 ≤15 min（均 CPU 单机）。
- Stage 1：每个更新/对照臂 ≤45 min；总 ≤2 h（含 bootstrap/置换：≥2,000 次；重采样固定 seed）；最小释放求解 60 s/单元。
- Stage 2（若进入）：按 A5 修订后成本/墙钟；单命令 ≤45 min。
- 超预算 → 缩任务/停，不扩时间；所有运行写 JSON/CSV/usage。

## P9 冻结清单（缺一不可；未齐 = 不得冻结）

1. P0a 关系集 SHA + relations_check.json 验收结果（R_min/R_max/n_ctx/稳定性/区间/覆盖/半交换）。
2. P0b constructive 体检结果（每类 recall/precision、type-I、退出率）。
3. P0c MDE 预检结果（80%@δ_min、聚类、独立单元数）。
4. P0d δ_min 的成本/效用定义与数值（否则 blocked）。
5. φ 算子/特征 SHA；端点可比性/饱和性证据；S/U 键与抽取算法 SHA。
6. 更新器选择（M1 变体/λ 网格）与对照臂清单（含等式投影核、同区间无释放 constrained ridge、soft-penalty、尺寸匹配随机释放）。
7. 统计：聚类结构、bootstrap/置换次数与 seed、多重比较（primary ≤10 关系，BH q≤0.10）、分类裁决规则。
8. 预算/成本/墙钟表；失败类别与退出上限；独立 runner/隔离实现。
9. 独立挑战意见（本文件修订后须由同一挑战者复审）。

## P10 给挑战者的问题（必须能推翻）

1. n_min=12/α=0.01/BH q≤0.10 的 MDE 推导是否成立（p1=0.95→80% 功效；更低 p1 是否应增大 n）？上下文独立性规则是否可执行？
2. 多解释比较是否真的消除了 M1 顺序偏置？注入体检的阈值/构造是否可信？
3. 依赖感知 χ²/κ 估计与 σ 带内一致性是否可操作（κ 的估计本身会不会被关系违反污染）？
4. 关系集 R_min/R_max/n_ctx/区间宽度/覆盖 50% 是否可达成（Jaaks 资源）？Cond_r 定义是否把细胞异质性误归 (ii)？
5. S/参考 disjoint 与同 screen nuisance 的主设计是否足够；跨 screen 只作敏感性是否会关掉可检验问题？
6. M1 对照（等式投影核/同区间无释放/soft-penalty/尺寸匹配）是否公平、是否覆盖"硬约束 vs 软先验"已知差异？
7. P1（样本外诊断增量）是否仍有循环？P2 是否被主指标/δ_min 绑定？
8. 协议可执行性：P0a–P0d 的顺序、δ_min blocked 状态、预算/墙钟、失败类别/退出上限是否写死？
9. 谱系：是否仍属"同一 96 细胞换聚合"（C174/C175 禁止）？MDE 预检能否证明不是？
10. 是否把 operational 归因写成机制/迁移/决策收益/新颖性？

## P11 边界（写死）

- 只在 P0a–P0d 全过 + 独立挑战复审通过后才冻结执行；本轮不运行、不训练、不读响应做效果。
- 只写"在该参考/反馈/菜单/预算下的 operational 归因与更新比较结果"；不写机制/临床/迁移/决策收益；不晋升代码；不声称新颖性。
- `not_identifiable`/`insufficient_precision`/`proxy_only`/`completed_null` 均不得写成"关系不存在/机制无效/阴性"。
- 条件偏移 ≠ 机制；分类正确 ≠ 生成原因；成本可行性 ≠ 科学收益。
