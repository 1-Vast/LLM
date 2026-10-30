# R198-A5 协议草案（PROTOCOL_DRAFT，**不执行**）：取证策略的等合法预算比较

2026-10-27。配套 [spec.md](spec.md) / [cost_model.md](cost_model.md) / [prior_art.md](prior_art.md)。**本文件是"若 Lead 下一轮决定冻结执行"的写死清单；本轮不运行 acquisition/训练/回放，不产生效果数字。** 冻结前必须：(a) 第 2 步（固定反馈的修订迁移比较）已显示可迁移修订；(b) 独立挑战者审过本草案；(c) 所有 `<...>` 占位由 Lead/runner 用真实数据与报价填死并哈希。

## P0 前置条件与准入（先于一切）

- **进入条件**：第 2 步报告给出"修订可迁移"的可证伪证据（不是 A1/A2 的通过，也不是本设计的自证）；若第 2 步失败/不可判 → 本协议保持**冻结但不执行**，记录条件未满足（不救）。
- **准入清单（全部满足才允许跑）**：
  1. 任务对象冻结（P1）；2. 菜单与动作定价冻结（P2）；3. 固定更新器冻结并通过等价性检查（P3）；4. 比较器与预算冻结（P4）；5. 指标/δ_min/MDE 冻结（P5）；6. 停止/失败类别冻结（P6）；7. 泄漏防护与独立评分者就位（P7）；8. 预注册哈希写入 `record.md`（P9）。
- **一次运行时间盒**：单策略单预算的 acquisition 回放 ≤45 min（CPU）；总运行 ≤2×45 min（两轮独立 seed 集）。**若需要超过预算 → 缩任务，不扩时间**。

## P1 任务对象（冻结字段）

- **端点** `y`：`SYNERGY_DELTA_EMAX`（或经 P-B/Q2 同意的等价物；**换端点=换轮**），须附端点可比性论证与饱和度/可靠性记录（引用 P-B / Q2 产物）。
- **单位** `u=(c, pair, design)`：c 细胞；pair 有序（anchor→library，方向写死）或无序（写死一种，与端点对齐）；design=剂量布局（如 `ANCHOR_CONC`/`LIBRARY_CONC`；完整剂量点集不可得时只按已发布设计列，见 spec §2 不可购买项）。
- **菜单 U**：从实际资源（Jaaks Original/Validation 匹配四元组宇宙，或 DrugComb v1.4 组合块，或 BeatAML 单药（仅作对照，不能提供组合决策））导出；**必须在第一次购买前枚举并哈希**；排除项（不可购买/不可见）写死。
- **效用** `U(a)`：写死为功能读数的函数（top-k 命中/`−Viability` 均值/ΔEMAX top-k 均值之一；**不用相关系数**）；oracle 与 static 的评分规则写死（同一评分器、同一 QC 时点）。
- **预算** `B_CU`：见 P2（planning cost units，冻结前由真实报价替换系数）。

## P2 菜单、动作、定价（冻结清单）

- **动作集**（spec §2 A1–A8）：整板、组合行、剂量网格、单剂量孔、单药参照包、重复、新细胞 setup、批次；**明确不可购买项**（设计外剂量、历史独立培养、靶点读数、未见药物、QC 免费信息）。
- **打包规则**：动作按 cell→pair→dose 顺序装入其格式板（利用率 `eta` 由实际布局核出）；每批 ≤10 板；新细胞 setup 记账规则（charged 或 sunk）**全局一致并写死**。
- **成本系数**（冻结前必须由报价/LOI 替换）：`c_well`、`plate_equiv`、`batch_equiv`、`eta`、`fail_frac`、`replicates`；附报价来源与日期。**当前 planning 区间**：见 [cost_model.md](cost_model.md) §3（optimistic/central/conservative）。
- **等成本核查**（写死）：每策略 `CU ∈ [B_CU − c_min, B_CU]`；三场景（optimistic/central/conservative）下排序一致才可下结论，否则 `cost_sensitive`；报告 wells/plates/keys/cells/batches 与有效独立单元；**禁止等行数/等 keys**。
- **预检（先于 acquisition）**：用现有数据离线算 **menu headroom**（oracle − static）与 `MDE_decision(B_CU)`；要求 `MDE_decision ≤ δ_min ≤ headroom`（spec §7 S2），否则**不运行**（记录 `menu_near_oracle`）。

## P3 固定更新器（写死，所有策略共用）

- **选择**（三选一，按可用性冻结，不得按结果换）：
  - **U1**：A1 的 M1 PRU-CC（约束回归/投影核；λ 内层药物分组 CV；冲突证书输出）——引用 [../conflict_signal/spec.md](../conflict_signal/spec.md) §5；
  - **U2**：层级经验贝叶斯（细胞/药对分组；超参数网格冻结，方差分量由源数据估计）；
  - **U3**：多输出 GP（RBF/冻结核参数、noise 标定）——用于 GP-KG/PDBAL 类策略。
- **接口**：输入=已购数据+源数据+特征；输出=所有未查询动作的 `(mean, uncertainty, posterior samples 或 decision-relevant quantity)`。所有策略只经此接口交互；不得策略自带更新器。
- **超参数**：由源数据内层 CV（按细胞/药对分组）选；**acquisition 不能用于调参**；所有策略共享同一网格与算力上限（CPU/wall-time 入账）。
- **等价性检查（先于比较）**：U1 vs U2/U3 在不购买数据时预测一致（同一源数据）；报告差异；若 U1 与投影核/层级模型等价（R189 已提示线性情形等价），则按"等价即撤算法贡献"记录（只保留科学问题）。

## P4 比较器与预算

- **策略集**（spec §5 S0–S7）：static/no-buy、固定配对（13×125 式）、随机整板、贪心 exploit、GP-KG（batch，fantasy 数写死）、决策 AL/VOI（可含 DPG 若冻结）、PDBAL/BATCHIE 式、oracle（事后、只作 headroom/regret）。
- **randomness**：可枚举动作时随机用**全动作均匀期望**（R2 做法）；必须抽样时预注册 seed 集合（≥10 seed），所有策略共享共同随机项；报告 seed 间离散。
- **一次购买的预算粒度**：按 P2 打包；每轮购买 ≤ 冻结上限（例如 ≤1 板/批或单动作），轮数 = 预算/动作成本；轮数也须预注册。
- **信息同权**：同一特征、同一源数据、同一单药参照、同一批次元数据、同一支持标签、同一计算预算；不得给某策略额外特征/预训练（若有，强基线同信息）。

## P5 指标、MDE、δ_min（冻结模板）

- **主指标**：`ΔNB = NB(策略) − NB(对照)` 的**每成本单位净收益**（未查询动作）；主对照预注册为 **S2 随机整板**（以及 S0 static 作为第二对照）；配对预算、配对菜单。
- **次指标**（只报告不改判定）：regret/decision loss、hit@k、购买量、headroom 使用比例、成本分解。
- **统计**：按**细胞**与**药对**（及批次）聚类 bootstrap（≥1,000 次，固定 seed）；报告 n_eff、ICC、95% CI；多重比较：主对比 1 个（预注册），其余为次要 family（Holm 校正后报告，不参与判定）。
- **MDE_decision**：由冻结的效应量、聚类结构、预算/keys 计算（C136 锚：1,600 keys→80% power；200 keys→0.46；**不得**用 wells 代替有效 keys/n_eff）；报告 `MDE_decision(B_CU)`。
- **δ_min**：由"决策有用差异"定义（例如 top-k 净收益的业务最小值），**先于数据写死**；要求 `MDE_decision ≤ δ_min`；并做 δ_min ±50% 敏感性。
- **禁止**：旧 CI 反推 δ_min；用全局相关/训练误差/Spearman 替代决策指标；用 wells/keys 冒充独立单元。

## P6 停止规则与失败类别（冻结）

| 类别 | 触发 | 结论 |
|---|---|---|
| `cost_offset` | `ΔNB − S0` 的 95% CI 上界 < δ_min（成本覆盖收益） | 该策略分支停止 |
| `menu_near_oracle` | `headroom < MDE_decision` 或 `headroom < δ_min` | 菜单不可检验；停止，换菜单需独立理由 |
| `no_stable_increment` | 两轮独立 seed 集上 CI 均含 0 或点估计 < δ_min，且无一致排序 | 无稳定增量；停止该分支 |
| `saturated` | 新增测量的 `|Δ预测|/ΔNB` 低于预注册阈值（C154 现象） | 停止"再加数据"路线 |
| `cost_sensitive` | 排序结论在 optimistic/central/conservative 下不一致 | 不下结论（成本不确定性主导） |
| `leakage` | 任何策略使用未购/QC/terminal 信息 | 该策略作废，整轮判失败 |
| `inconclusive` | MDE > δ_min、或预算买不到目标 keys、或设计检查不过 | 记录设计边界，不救 |
| `completed` | 预注册对比完成且 CI 可判定 | 按 §8 的边界写结论 |

## P7 泄漏/公平（冻结检查清单）

1. acquisition 只看源数据、已购数据、设计特征；QC/terminal 仅在支付并揭示后进入更新，QC 只在共同评分端（R2 首版 bug 教训）。
2. U 与动作集在首次购买前枚举并哈希；不得事后增删/按结果挑层。
3. 随机种子/枚举策略预注册；所有策略共享共同随机项。
4. 等成本核查（P2）每策略执行并留痕。
5. LLM/算力/人工成本入账，不隐藏在"策略实现"。
6. 端点/菜单/效用/δ_min/更新器在首次购买前冻结；执行中改 = 新轮。
7. terminal/评分由未参与策略设计的独立 runner 持有，策略实现者不可见。

## P8 运行与交付

- 运行前：`q3.py`（或 Lead 指定名）实现本协议；输入/脚本/协议 SHA256；确定性（固定种子、键排序、无时间戳）；单策略 ≤45 min。
- 交付：`PROTOCOL_Q3.md`（冻结版）、`q3.py`、`q3.json`、`q3_rows.csv`、`report_q3.md`、`record_q3.md`、`usage_q3.json`；成本/预算/等成本核查表在 JSON。
- 本轮（A5）不写这些文件；只给设计与成本模型。

## P9 冻结前必须补齐的数（不补齐不许冻结）

1. 成本系数与报价来源（`c_well/plate_equiv/batch_equiv`，日期、供应商/实验室报价或 LOI）；`eta` 由实际板布局核出；`fail_frac` 由 pilot 估计。
2. 菜单：实际可购动作清单（资源、格式、布局、动作数），并离线算 `headroom` 与 `MDE_decision`。
3. 端点：端点可比性、饱和性/可靠性（引用 P-B/Q2 产物；不得跳）。
4. 更新器：选择 U1/U2/U3，超参数网格，等价性检查结果。
5. 统计：δ_min 的业务定义、MDE 计算脚本、聚类结构、bootstrap 次数/种子。
6. 预算 `B_CU` 与轮数；等成本核查脚本；三套成本场景。
7. 挑战者意见（独立挑战者必须攻击：headroom 估计、MDE 与 n_eff、成本系数、等成本核查、泄漏、与第 2 步的关系）。

## P10 给独立挑战者的问题（必须能推翻本设计）

1. `headroom` 是否真的大于 `MDE_decision`？——若菜单/预算下 headroom < MDE，本设计应直接判 `menu_near_oracle`，不应跑。
2. 成本系数的 planning 区间是否足以让等成本比较在 optimistic/conservative 下翻转结论？——若翻转，`cost_sensitive`，不报赢家。
3. 更新器是否被策略"偷换"（策略自带更新器/调参/特征差异）？——若是，整轮作废。
4. MDE/n_eff 是否用 wells/keys 冒充独立单元？——若是，判 `inconclusive`。
5. acquisition 是否读了未购/QC/terminal？——若是，`leakage`。
6. 是否把"策略胜出"写成新算法/机制/迁移结论？——若是，越界（只允许工程结论）。
7. 是否违反 C141/C154/C160/C167/C171/C172 的边界（尤其：不得把条件级 1.43% 当规律总量、不得把 A1 inconclusive 当阴性、不得用全局相关替代决策）？——若是，停。

## P11 边界（写死）

- 本协议只在第 2 步成立后执行；本轮不运行、不训练、不模拟收益；所有规划数字不作效果证据。
- 策略胜出只支持"该菜单/该预算/该更新器下的工程结论"；不晋升新算法、不做机制/临床主张、不启动 B/C/RSI、不换端点/分层/δ、不按结果挑层。
- 条件偏移 ≠ 机制；成本可行性 ≠ 科学收益；阴性/不可判同样完整记录。
