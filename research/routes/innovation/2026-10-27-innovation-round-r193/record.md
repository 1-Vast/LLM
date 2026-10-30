# R193 轮次记录：条件偏移可复验性——A0 匹配资格审计（`matching_qualified`）＋ A1 协议草稿

2026-10-27。角色：Lead（冻结/核验/综合）＋ A0 匹配审计员（combocat-auditor，task-13）＋ 独立挑战者（i003-challenger，task-14，进行中）。**本轮未估计任何 Q/效应、未拟合模型、未做新药理主张。** 本轮是 R192 之后的方向切换：先查"信息对象"（条件偏移是否可复验），再谈反馈/Agent。

## 0. 一句话结果

- **A0 `matching_qualified`**：Original（296,707 行）与 Validation（23,505 行）两 screen 的 barcode 集合交集为 0；两独立组**共同匹配四元组（2×2 最小闭环）R4 = 6,223,367**（门槛 ≥500）；覆盖 **96 细胞 / 98 有向药对 / 291 条件 / 31 anchor / 38 library / 3,418 细胞对**；R3 半匹配 802,445；barcode 分半次级 R4 43,208,857。**匹配全程响应盲**（端点仅空串存在性检查；四 Δ 端点空值 0）。
- **边界**：剂量等价只到**已发布设计列**（拟合表无完整 library 浓度点集、无 Validation raw 布局）；**独立组与 screen/批次完全混淆** → 只能主张"跨 screen 条件稳定性"；单药参照在 A0 为 DENY、A1 需显式解禁；500 只是 MDE floor，6.22M 是高度嵌套计数、**不是独立样本量**；**匹配合格 ≠ Q 稳定/可迁移**。
- **A1 协议草稿**已写（[PROTOCOL_Q_DRAFT.md](../2026-10-27-conditional-shift/PROTOCOL_Q_DRAFT.md)）：主分析拟用**细胞对级聚合 Q**（n≈3,418）＋条件对级/四元组级支持，含零分布、MDE、δ_min、停止分支；**待独立挑战通过后冻结**。
- **独立挑战进行中**（task-14）：审查匹配定义是否响应盲、剂量/方向可比性、回路可估性、批次混淆、δ/MDE/零分布是否先冻结、是否只是旧有限交互筛选/R5 改名。**未通过不运行 A1。**

## 1. 背景与方向切换（来自 R192 与独立重审）

- R192 阶段 2 首次执行 DrugComb 外部复现：预注册 `not_replicated`，但功效口径未校准（P-B 自校验 0.708；实际拟合臂 realized SE→MDE≈0.150）、proxy 调整后弱信号消失（partial ρ=0.010）、对切分/口径敏感 → construct/power/true-negative 未分离（C167）。
- 独立重审指出：现有最强正结果来自"两侧身份/注释 one-hot 的加性线性模型"，无细胞特征、无药对×细胞项，可能只学到"哪些药物平均更容易产生较高组合读数"；应先问**条件偏移是否可复验、反馈传递什么信息**，再谈 acquisition/Agent（C168）。
- 因此 R193 主问题：**匹配条件下 `Q=(y[c,p]−y[c,q])−(y[c',p]−y[c',q])` 能否在独立测量中复验**（[R193 BRIEF](../2026-10-27-innovation-round-r193/BRIEF.md)）。Q 消去加性细胞/药对主效应，不要求排序反转。

## 2. A0 匹配资格审计（`matching_qualified`）

产物：[PROTOCOL_A0.md](../2026-10-27-conditional-shift/PROTOCOL_A0.md)（运行前冻结，SHA `D77316ED…AA93`）、[a0.py](../2026-10-27-conditional-shift/a0.py)（`444E939C…C3525`）、[a0.json](../2026-10-27-conditional-shift/a0.json)（`72BBAF6D…ECA22`）、[matched_conditions.csv](../2026-10-27-conditional-shift/matched_conditions.csv)（9,154 双组可用键）、[matched_quadruples.csv](../2026-10-27-conditional-shift/matched_quadruples.csv)（20 万行审计子集，全量计数在 a0.json）、[report.md](../2026-10-27-conditional-shift/report.md)、[record.md](../2026-10-27-conditional-shift/record.md)、[usage.json](../2026-10-27-conditional-shift/usage.json)。

| 门槛（冻结） | 要求 | 实测 | 判定 |
|---|---|---|---|
| 主：两独立组共同匹配四元组 R4 | ≥500 | **6,223,367** | PASS |
| 独立测量组 ≥2 | 两组板不重叠、各自 ≥500 四元组 | Original vs Validation：barcode 交集 **0**；G1-only 4,415,971,041 / G2-only 7,301,337 | PASS |
| 覆盖下限 | ≥10 细胞、≥10 有向药对 | **96 细胞 / 98 有向药对**（291 条件、31 anchor、38 library、3,418 细胞对） | PASS |
| 端点可用 | 四键 `SYNERGY_DELTA_EMAX` 均存在 | 四 Δ 端点空值 0/全部行（存在性检查） | PASS |

- **条件定义（冻结）**：有向药对 `ANCHOR_ID→LIBRARY_ID`（方向固定）+ `ANCHOR_CONC`（uM）+ `LIBRARY_CONC`（library 最高浓度，uM）；四元组要求四键使用同一条件元组。
- **计数结构**：R0 4,034,637,772 / R1 177,515,510 / R2 214,664,684 / R3 802,445 / R4 6,223,367；匹配复制子图 387 节点（96 细胞+291 条件）/9,154 边/每个四元组恰是一个 4-回路；**树不能识别非可加性，2×2 是最小闭环**。
- **分层**：controlled_anchor 92,039；same_anchor_any_conc 568,029；same_library 309,351；disjoint_pairs 5,345,987（**ERRATA：更正为 4,612,633**——a0.py 漏减跨朝向共享；见 [ERRATA_A0.md](../2026-10-27-conditional-shift/ERRATA_A0.md)）；same_tissue 6,217,553 / cross_tissue 5,814（跨组织匹配稀少 → A1 主张范围主要同组织）。
- **剂量可比性**：anchor 浓度水平 26 vs 20（共同 20）；`LIBRARY_CONC` 12 vs 11（共同 10）；127 个共同药对有多设计元组；无完整 library 浓度点集、无 Validation raw 布局 → **孔级不可验证**。
- **独立性**：Original 重复板（键的 barcode 数 1→180,485、2→10,940、…、10→1,357）；barcode 分半次级 R4 43,208,857（板级独立性弱于跨 screen）。
- **局限（随判定引用）**：screen 与批次完全混淆；单药参照 A0 DENY；6.22M 是嵌套计数非独立样本；**匹配合格 ≠ Q 稳定/可迁移**。
- **Lead 核验**：独立重跑 `a0.py`（27.4 s）→ a0.json/两 CSV SHA 逐字节一致；四 Δ 端点空值 0；响应列只读空串存在性（无效应计算）。

## 3. 独立挑战 verdict、A0 勘误与 A1 协议 v1 冻结

- **独立挑战（task-14，i003-challenger）完成，总判决 `revise`**（[challenge_A0.md](../2026-10-27-conditional-shift/challenge_A0.md)）：A0 头部门槛被独立实现**逐项复现**（结构计数、9,154 共同键、barcode 交集 0、R0–R4、覆盖、五份 SHA 一致、响应盲代码审计成立）；但 A1 DRAFT 未冻结（6+ 开放选择，无完整规则功效）、Q 保留 cell×单药/剂量项（H193b 被写成可选）、A0 有 4 处计数/口径错误、Validation 选择偏差未披露。判决 1/2/3/5 为 WEAK、4 为 **FAIL**、6 为 revise（**不是 stop**）。
- **A0 勘误（ERRATA_A0.md；不改 `matching_qualified`）**：`disjoint_pairs` **4,612,633**（非 5,345,987，漏跨朝向共享 733,354）；G1-only/G2-only M3 无序口径 **4,412,540,421 / 7,234,325**；条件级有向药对数 **129**（非 130）；barcode-split R4 仅覆盖 **46 细胞/583 细胞对**；补 **Validation 选择偏差**（R31：4.4% 键、可能是挑过的子集；F9 组织构成偏移）与剂量分层披露。
- **PROTOCOL_Q v1 FROZEN**（[PROTOCOL_Q.md](../2026-10-27-conditional-shift/PROTOCOL_Q.md)，2026-10-27，任何 Q 读取之前；取代 DRAFT）：
  - 唯一主设计：**细胞对级 median Q**（每个 cp 主分层四元组 ≥5；`Spearman(Q_A^cp,Q_B^cp)`；按细胞聚类 bootstrap）＋**主分层 controlled_anchor**（同 anchor/同 anchor_conc/同 library_conc，仅 library 不同；A0 92,039 个）；条件对级/四元组级/其它分层全部预注册为次级。
  - **δ_min_latent=0.10** 的 operational 理由（解释方差 <1% 不足以支持后续反馈实验；不得用旧 CI 倒推）；`δ_min_obs=0.10×sqrt(rel_A·rel_B)`（衰减，rel 由 barcode 分半 Spearman-Brown 估）。
  - **零分布**：screen 内细胞标签置换（1,000 次，固定种子）；**design_check 先于任何 Q 复验**：cp 数≥500、可靠性、MDE80_obs≤δ_min_obs、完整规则 joint power（latent 0.30≥0.80；0.10 报告）、type-I≤0.10；任一不过→`inconclusive` 停；`q1.py` 运行时断言。
  - **H193b 升级为必做主解释项**：单药列（两表 7 列、空值 0）构造 `F=ΔSA(c,p,q)−ΔSA(c',p,q)`（主特征 LIBRARY_EMAX 差），交叉拟合 β（β_A 用于 B、β_B 用于 A），报告 `Spearman(Q_adj^A,Q_adj^B)`；调整后 CI 含 0 或点 <δ_min_obs → `single_agent_explained_unresolved`，不得声称条件结构超出单药/剂量稳定性。
  - 选择偏差诊断：matched/unmatched 元数据比较、Original 内按 Validation 构成匹配的随机子集对照、回归到均值；衰减校正仅次级解释。
  - 判定/措辞：`reproducible` 只能写"该匹配子集跨 screen 条件结构可复验"；`not_reproducible` 不得写"无条件结构"（construct/剂量/power/选择/批次未分离）；`inconclusive`=停；**谱系写死**：不是旧有限交互筛选、不是 R5 反序重启、不用 Q 反推交互族、B/C/acquisition 不启动。
- **A1 已排独立执行**（task-15，endpoint-auditor，按 PROTOCOL_Q v1；先 design_check，未过即停）。
- **A1 执行完成（task-15，endpoint-auditor）→ `inconclusive`（design_check 未过，按协议 §7 停在主 Q 之前）**：
  - 结构：controlled_anchor 四元组 **92,039**、细胞对 **1,501**（≥5/cp；96 细胞、291 条件、9,154 键、129 条件级有向药对；R4 全量复算 6,223,367 命中 A0/ERRATA）→ PASS。
  - 可靠性（within-screen barcode 分半，Spearman-Brown）：rel_A(Original)=**0.864**（r=0.760，仅 61 cp/1,593 键，CI 宽）；rel_B(Validation)=**0.741**（r=0.588，1,501 cp/8,974 键）→ 覆盖率规则 PASS。
  - δ_min_obs（保守 rel 界）=**0.0893**（点估计口径 0.0800）；**MDE80_obs（cell-cluster 结构）=0.2042 > δ_min_obs ⇒ FAIL**（唯一失败 gate，11 项中 10 项过）。敏感性：去偏经验 0.1523（FAIL）、iid 解析 0.0723（唯一「通过」但忽略已证实的细胞聚类、协议不允许）、零模型 cell-share≥0.25 → 0.264–0.294（FAIL）→ 判定稳健。
  - 完整规则 joint power：latent 0.30 → **0.896**（PASS）；latent 0.10 → **0.174**；type-I（置换零数据）→ **0.018**（PASS）。**0.10–0.30 区间的 latent 效应不能被本设计可靠分类**（写死）。
  - 失败在**有效样本量**（1,501 cp 只来自 96 细胞；bootstrap SE 是 iid 的 2.8 倍，n_eff≈**189**），不是 Q 噪声（rel 0.74–0.86）也不是四元组少（92,039）。**这不是「条件偏移不存在」的证据**。
  - 按协议**未计算/未落盘**：主统计量+CI+置换零分布（q1.py 写盘前硬断言，`main_q_computed=false`）、H193b 交叉拟合调整（单药 7 列已核验可用，非「做不到」）、选择偏差诊断、次级统计量。
  - 解冻条件（runner 列出）：更多独立细胞/独立测量组；或有不靠旧 CI 反推的、operational 的更小 δ_min_latent；或有效独立样本更大的分析单元（**不能只是同一 96 细胞换聚合**）。B/C 不启动。
  - 产物：[q1.py](../2026-10-27-conditional-shift/q1.py)、[q1.json](../2026-10-27-conditional-shift/q1.json)（`064AD3C3…03534`，两次逐字节相同）、[q1_rows.csv](../2026-10-27-conditional-shift/q1_rows.csv)、[report_q1.md](../2026-10-27-conditional-shift/report_q1.md)、[record_q1.md](../2026-10-27-conditional-shift/record_q1.md)、[usage_q1.json](../2026-10-27-conditional-shift/usage_q1.json)；A0/ERRATA/challenge/PROTOCOL_Q 哈希未变。

## 4. 下一步与边界

- **A1 执行中/待执行**（task-15）：design_check → 主统计量（cp 级 median Q × 两个 screen）→ H193b 单药调整 → 选择偏差诊断 → 次级统计量。若 design_check 不过 → `inconclusive`，不进入主 Q（正常出口）。
- **分支（协议冻结）**：not_reproducible → 不做可迁移条件结构主张，接受普通加性/静态先验解释，B/C 不启动；reproducible 且 H193b 调整后仍成立 → 才允许下一轮设计 B（反馈传递：固定可购买板套餐，比较无/真/打乱反馈对未查询动作损失）；reproducible 但 H193b 解释 → 给普通单药/剂量稳定性记功。
- **A1 结果 → 进入 A2 新问题（R194）**：A1 `inconclusive`（power 边界，非阴性）说明「跨 screen 复验」在本资源上不可检验。R194 改为先问**Q 的条件级结构是否可估**（见 [R194 BRIEF](../2026-10-27-innovation-round-r194/BRIEF.md)）：用 within-screen 方差分解 + barcode 重复噪声，估计 condition-pair / cell-pair 分量与条件级可靠性；若条件级分量不可分辨 → 记边界并停止条件结构主张；若可分辨 → 再谈跨 screen/反馈。**明确不是把「96 细胞换聚合」当解冻路径**。
- 旧路线不变：I003 停（谱系+操作化）、细胞状态 D 停（A0 更正后仍不达 δ=.05 门）、R187 采样不重启、R192 DrugComb 阶段 2 `not_replicated`（功效未校准，未解冻）。
- 边界：A1 只检验"匹配子集上的跨 screen 条件稳定性"；不是机制/迁移/新算法/Agent 收益；不晋升代码。

## 5. 产物、预算与边界

- 本目录：[BRIEF.md](BRIEF.md)、本记录；条件偏移目录见 §2/§3；无新效果代码运行（A0 只做匹配）。
- 预算：A0 单次 26–35 s CPU；无 GPU、无网络新下载、无湿实验、无付费 API；未改 `src/`；**未晋升代码**；总体目标未达成。
- 边界：A0 是**资格结论**，不是 Q 稳定性/可迁移/机制/临床证据；6.22M 不可当独立 n；matches 不等于生物学同一实体。
