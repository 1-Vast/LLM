# R198-A5-C1 独立挑战：取证策略设计（acquisition_stage3）

2026-10-27。挑战角色：独立挑战者（不参与 A5 设计、不运行 acquisition/训练/收益模拟）。本文件只读审阅 A5 的 [spec.md](spec.md) / [cost_model.md](cost_model.md) / [prior_art.md](prior_art.md) / [protocol_draft.md](protocol_draft.md) / [record.md](record.md) / `tmp/a5_cost_arithmetic.py|json`，并独立复算其算术（只读脚本见 `tmp/a5_challenge_checks.py`，不改任何 A5 产物）。

## 0. 审阅快照与边界

- 只读快照 SHA256（前 4 位）：spec.md `7962C9C1…`、cost_model.md `46824DBE…`、prior_art.md `F891C3C2…`、protocol_draft.md `E2578E8F…`、record.md `96A6B889…`、usage.json `941239A2…`、`tmp/a5_cost_arithmetic.py` `1A7C821C…`、`tmp/a5_cost_arithmetic.json` `1C27DA82…`（与 usage 记录一致）。
- **未运行**任何 acquisition、训练、回放或收益模拟；未改 A5 任何文件；本挑战只复算 `tmp/a5_cost_arithmetic.json` 的内部一致性与文档数字是否匹配。
- 上下文版本提示：A5 usage 记录的 `SYNTHESIS` hash 为 `5FD693D1…`，当前 SYNTHESIS 为 `4499C5EB…`（之后新增 C176/C177 等 R196/R197 撤回登记）。这与 A5 结论无直接冲突（A5 主要引用 C136/C144/C154/C156/C171），但 A5 冻结前应补引 **C176/C177**（R196/R197 已作废、第 2 步尚无结果）以免误读前置状态。

## 总判决

**`revise`**（≤5 必改；**不 stop**）。A5 的骨架——"等合法预算、固定更新器、未查询决策净收益、菜单 headroom 预检、先例不声称新颖性、第 2 步未成立不执行"——可保留且有价值；但存在 **4 类必须修的问题**：成本物理锚点的两处事实性错误、等成本算法的可执行缺口、headroom/MDE 的推论过度、运行预算与停止类别不一致。**当前形态不得进入候选冻结、不得执行**；且 P0 前置（第 2 步可迁移修订）目前不存在，即使修完也必须等前置。

| 要求项 | 判定 | 一句话 |
|---|---|---|
| ① 菜单与成本模型 | **WEAK（含必须修的事实错误）** | 骨架可审计；但"per-key 参照/对照 wells"与"per-plate 锚点"混淆、R2 实测 2 板却被 eta 算成 4 板、"setup ratio 2.5–5.2×/距离 5.8–6.3×"与 JSON 不符 |
| ② 比较器/更新器/指标 | **WEAK** | 固定更新器、S0–S7、主/次指标写得好；但 S1/S5/S6 未 operational、MDE 借用 C136 相关尺度、δ_min 无单位、等成本下 cell breadth 未冻结 |
| ③ 先例与 headroom | **WEAK** | 先例覆盖判定基本成立且不声称新颖性；但把 R2 的 CI 宽度当 MDE、"任何 acquisition 比较的 MDE 都大于 headroom" 属过度陈述 |
| ④ 可执行性与停止条件 | **WEAK** | P0/P2 写死；但 headroom/oracle 只在回溯 replay 可算、菜单按 headroom 选会构成结果选择、45 min 预算算不过来、P9 的"真实报价"无货币记录时永久阻塞 |
| ⑤ 谱系/纪律 | **PASS（小改）** | planning/effect 标签一致、不声称新颖性、不复活 A1/A2；缺"不重开 R187 方差采样/R2 菜单结论只作约束"的显式句 |
| ⑥ 总判决 | **revise** | 5 必改见 §2；修完 + 第 2 步前置 + 关系/更新器接口就位后才可重审冻结；**本轮不运行 acquisition** |

## 1. 逐项证据与修改

### ① 菜单与成本模型：WEAK（两处事实性错误 + 一处结构性混淆）

**成立的部分（PASS 子项）**

- A1–A8 动作与 7 项不可购买项有物理锚点与来源（Jaaks 1,536-well/2×7/对照/播种优化/day-1；BATCHIE 384-well/2 板 766 wells；R2 动作；BeatAML 7×1；DrugComb 布局族）；**不可购买项写死**（[spec.md](spec.md) §2）。
- CU 明确"非货币、planning"：[cost_model.md](cost_model.md) §0/§3/§9 与 [record.md](record.md) §1 多处重复，**未把 CU 写成美元/货币**；成本系数为区间且要求冻结前报价替换（§8、protocol P9）——这一点是 PASS。
- 等成本核查的原则写死：total CU 差 ≤ 最小动作、三场景排序一致、必须报 wells/plates/keys/cells/batches 与有效独立单元、禁止等行数/keys/wells（[cost_model.md](cost_model.md) §5、[spec.md](spec.md) §8.4）。
- 我复算了 [cost_model.md](cost_model.md) §7 敏感性：`c_well ±50%` 恰为 ±50%（所有 CU 项线性于 c_well）、`replicates 2→1/3` = −14.5%/+14.5%、`eta 0.6→0.3/0.9` = +6.7%/−2.2% —— **与文档一致**（见 `tmp/a5_challenge_checks.py`）。

**必须修的事实错误**

1. **per-key 参照/对照 wells 与 per-plate 物理锚点混淆（结构性）**：[cost_model.md](cost_model.md) §2 给 A2 anchored key 记 "12–38 单药参照 + 8–16 对照 wells/**key**"；但 §1 的物理锚点原文是**每板**："five replicates of the anchor alone (high and low)" + "four replicates of the library alone (full dose response)"，即 anchor-alone 5–10 wells/板、library-alone 7–28 wells/板、controls 8–16/板（≈20–54 wells/板）。若每板装多 key（A5 的打包公式按 1,536×eta=0.6 装，1600 keys 只算 89–480 板），参照/对照必须按板摊销（约 3–6 wells/key；可对照 R193-A0 审计的 Jaaks 板结构：每 barcode 约 95–100 个 fitted 行、24–26 anchors、1–2 libraries），不能同时"每 key 记全板参照"又"多 key 共享板"。**两种自洽读法**：(a) 参照/对照按板共享 → 每 key wells 大幅下降（我按 A5 自己的系数粗算 anchored 1,600-key campaign central CU 由 **569,568 → ≈446,000**，−21.7%；该数是**下界示意**，不是替换数字）；(b) 每 key 独占自己的参照/对照 → 一块 1,536 板只能放 1 个 34–68 wells 的 key，`eta=0.6` 与 18 keys/板不成立。**必须用真实 Jaaks 板布局/DRUGSET 重新推导，并把两种读法都写入敏感性；否则 C136 规模 CU、等成本表、形状比较都不可靠。**
2. **R2 实测整板动作被 eta 重复打折**：[cost_model.md](cost_model.md) §1 记录 R2 合法动作 = **2 张物理板 / 766 wells**（766/768≈99.7% 利用率，实测），但 `tmp/a5_cost_arithmetic.py` 的 `price_plan` 对 A1 也套 `eta=0.6`，把 758 averaged wells/动作算成 `ceil(758/(384×0.6))=4` 板/动作；等成本表中 46 个整板动作对应 **168 板**，而物理实测应为 **92 板**（46×2）——plate/batch 成本与板数被高估。**已实测的物理动作不应再乘 eta**；eta 只用于把"未打包的 wells"折算成板。
3. **两处文档数字与 JSON 不符**：
   - [cost_model.md](cost_model.md) §4/record 称 "setup 计入 vs sunk 使同一设计的 central CU 相差 **2.5–5.2 倍**"；按 JSON 实际为：anchored 3.30×、6×6 grid 2.77×、single-dose（复用单药）**52.28×**、single-dose（新参照）6.78×、mono 11.42×。若只指组合路径应为 **2.8–3.3×**；若指全部路径应写 **2.8–52×** 并解释 single-dose 的极端差异。当前范围**两边都不对**。
   - [cost_model.md](cost_model.md) §6 称 "距离 1,600 keys 的 C136 门槛差 **5.8–6.3 倍**"；按 JSON（100k CU central charged）实际为 anchored **5.70×**、6×6 grid **6.21×** → 应写 **5.7–6.2×**。
   - "同一预算可买 46 个整板动作 vs 20,985 个单剂量 key（形状差 **~450 倍**）"：20,985 是 **setup sunk** 口径、46 是 **charged** 口径，混了口径；同口径 charged 为 384/46 ≈ **8.4×**，同口径 sunk 为 20,985/55 ≈ **381×**。作为"形状示意"可用，但必须标口径，否则会被当成公平比较。
4. **缺失成本项/摊派规则（次要）**：cell line 采购/扩增、培养/传代记录、化合物库存维护未计价（A5 只计 wells+setup+plate+batch）；若菜单允许新细胞，需说明这些是否已含在 A7 固定块内，否则 `cost_calibration` 不完整。

### ② 比较器/更新器/指标：WEAK

**成立（PASS 子项）**：U1/U2/U3 固定、所有策略共用同一更新器、禁止策略自带更新器/调参、基线可正常更新（[spec.md](spec.md) §4、[protocol_draft.md](protocol_draft.md) P3）；S0–S7 定义清楚；主指标=未查询决策净收益、次指标预注册；按细胞/药对/批次聚类、禁止 wells/keys 当独立单元、禁止相关指标替代决策指标（§6）；成本与检定力分离表（[cost_model.md](cost_model.md) §6）写死；`MDE_decision ≤ δ_min ≤ headroom` 冻结门槛写死。

**必须修**
1. **MDE 不能借用 C136 的相关/效应尺度**（C136 是 ΔEMAX 排序增益的 1,600 keys→80% 功效锚点，不是"决策净收益"指标的 MDE）；P5 虽写"由决策指标计算"，但 §3/§6 的实际规划锚仍以 C136 计；冻结前必须给出 decision-metric 的配对、聚类 MDE 计算脚本与空/备择模拟（含策略间共享随机项），并说明 C136 只作**购买量级**锚点。
2. **δ_min 无单位/无 operational 定义**：当前只写"top-k 净收益的最小业务意义"；任务若无可认证成本/效用，**必须把冻结状态标为 `blocked_by_utility_definition`**（而不是继续可冻结）。A1 挑战也已指出该类问题；A5 应在 P5 加"δ_min 未定义 → 不冻结"。
3. **S1/S5/S6 未 operational**：S1 "13 对×125 细胞（C136 规模）固定设计"在 100k CU central charged 下买不起（C136 1,600 keys 需 5.7 倍预算），必须改为"预算缩放后的预注册固定设计"；S5 的 VOI/决策 AL 需固定估计器（plug-in 还是后验期望、是否用 DPG 接口）与随机化规则；S6 的 PDBAL 距离/参数/批次需写死，否则不同执行者会实现出不同策略。
4. **等成本下的 cell breadth 未冻结（与 ① 联动）**：100k CU 等成本表隐含 plate 路径 5 cells、anchored 22 cells、single-dose 30 cells——**不同策略在不同细胞集合上评分，NB/决策损失不可比**，违反 A5 自己的"同一菜单/同一信息"公平性。必须写死：固定 cell 集合（若 setup charged 则预算必须覆盖 setup；或声明 sunk 并说明细胞已可得），或在同一预算下把 cell breadth 作为显式设计因子并只做同 cell 集合内比较；否则等成本表只能当形状示意，不能当比较设计。
5. **主指标表述**：等预算下"每成本单位净收益"与"ΔNB"只是常数缩放；建议主指标明确为 `ΔNB（配对，等 total CU）`，`NB per CU` 仅作描述（避免不同预算/不同 CU 的比率比较）；λ 成本的效用换算需预注册并报敏感性。

### ③ 先例与 headroom：WEAK

**成立**：decision-focused BOED / BATCHIE 整板 / GP-KG / EVSI/ENBS 的"已覆盖/部分覆盖"判定与锚点基本成立（prior_art 逐条给了 F01–F16 等本地已核锚点；多保真度 BO/SHIFT-DRP 等明确标"题录/摘要级、未核方法"）；"完整成本账 + menu-oracle 门槛 + 未查询决策损失"的组合**明确标为评估/工程组合、不构成新算法**（prior_art §1/§4）——**符合"不得声称新颖性"**，PASS 子项；"未发现"措辞有"有界检索、非穷尽"限制（§3）。

**必须修**
1. **`headroom ≪ MDE → 该菜单不可检验` 的 MDE 代理不成立**：[spec.md](spec.md) §3 用 "KG−random 的 95% 区间宽 ~0.145" 当 acquisition MDE，并写"**任何** acquisition 比较的 MDE 都大于菜单头空间"。两点问题：(a) CI 宽度不是 MDE；正态近似下 `MDE80 ≈ (1.96+0.8416)/(2×1.96) ≈ 0.715 × CI 宽度`（即 CI 宽度高估 MDE 约 1.4 倍）；(b) "任何"是未证明的全称量词（MDE 随设计/重复数/指标/聚类变化）。**R2 那个菜单的结论仍很可能是对的**（headroom 0.004343 与 0.145 差 ~33×，即使按 0.715 折算也差 ~24×；且 R2 的 5-cell 小菜单/单动作预算使其不可能撑起 acquisition 比较），但文本必须改为："用 R2 观测的 CI 宽度作**粗代理上界**，与 headroom 相差 ~24–33×；MDE 必须按 P5 的定义在 R2 设计上显式计算；该结论只适用于该菜单/该预算"。
2. **菜单选择偏差（headroom 是结果相关量）**：[spec.md](spec.md) §1 把 headroom 当"菜单属性，与策略/成本无关"——统计上正确，但 headroom 依赖 outcomes（oracle）。若执行者可以在多个候选菜单间**先算 headroom 再挑菜单**，等于用结果选择任务（`menu_near_oracle` 闸反而奖励挑到 headroom 大的菜单）。必须预注册**菜单构造规则（纯元数据）**：固定资源、固定 cell×pair 宇宙、固定端点/效用，一次性枚举；不得按 headroom 选菜单；若必须多菜单比较，需预注册选择/多重校正规则。
3. 先例要点补一句：R189-F14 的"统计功效×acquisition 零命中"是**有界检索**结果（prior_art 已写），冻结文本不得把它写成"不存在先例"。

### ④ 可执行性与停止条件：WEAK

**成立**：P0 写死"第 2 步不成立不执行"（[protocol_draft.md](protocol_draft.md) P0、[spec.md](spec.md) §0/§9）；P2 预检"headroom<MDE/δ 直接停（`menu_near_oracle`）先于购买"写死（P2 预检、S2）；失败类别 8 个已列（P6）；泄漏/独立评分者/QC 时点/菜单哈希写死（P7）；本轮不运行（P11）。**P0 当前实际未满足**（第 2 步尚无结果，C176/C177 显示 R196/R197 协议均已作废）——A5 目前只能保持"冻结但不执行"，这一点 A5 写对了。

**必须修**
1. **headroom/oracle 的可算性前提未写**：`oracle = max over 可买全菜单 U(a)` 需要**全部菜单结果已知**。这只在**回溯 replay**（历史已测、策略不可见）中成立；对"真前瞻购买"，oracle 未知，headroom 无法在购买前计算，P2 预检不可执行。A5 必须显式声明"本设计仅适用于已测归档的回溯 replay 菜单（R2 式）"；若允许前瞻菜单，需另写 oracle 的 pilot 估计与不确定性规则（不得假装已知）。
2. **运行时间预算自相矛盾**：P0 写"单策略单预算 ≤45 min；总运行 ≤2×45 min（两轮独立 seed 集）"，但策略集有 S0–S7（≥7 个），若再乘 optimistic/central/conservative 三场景（等成本排序一致要求）与多轮购买，**总时长不可能 ≤90 min**。必须给每策略/每轮/每场景的时限表与总预算（或缩策略集/缩预算），否则 P8 不可执行。
3. **等成本的可执行细节未写死**：残余预算补足规则只有"例如各策略都补固定配对 filler"（[cost_model.md](cost_model.md) §5 步骤 2），不是冻结规则；必须写死 filler（同一设计、同一信息、计入 NB）、允许 under-spend 方向与容差（≤一个最小动作）、以及**三场景下策略需按该场景预算重跑**（而不是只重算同一个 plan 的 CU）——后者会让 plan 在某些场景超预算/欠预算，使"三场景排序一致"失去意义。
4. **失败类别不完整**：缺 `oracle_unknown`（前瞻菜单）、`cost_uncalibrated`（P9 未补齐时）、`protocol_deviation`（执行偏离）、`not_identifiable`（策略/动作不可区分）；且 `inconclusive` 混装"MDE>δ""买不到目标 keys""设计检查不过"，冻结时应拆开。`no_stable_increment` 要求"两轮独立 seed 集"——需定义什么叫独立（seed 集/数据轮次/批）并给单轮 null 的处置。
5. **P9 "用真实报价/LOI 替换系数"在本项目不可得**：R2 已声明无认证的货币成本记录；若坚持 P9-1，冻结将永久阻塞。建议二选一：① Lead 接受"**无量纲 CU 预算** + 明确不写货币结论"作为可冻结形态（并把 `cost_uncalibrated` 标为限制而非失败）；② 保持阻塞并记录所需报价来源。否则 A5 的设计无法通过自己的 P9 门。
6. **δ_min/MDE/headroom 三者无法在当前冻结**（δ_min 无单位、MDE 无决策指标脚本、headroom 依赖菜单；见 ②③）：P9-5 应写"未定 → 不冻结"。

### ⑤ 谱系/纪律：PASS（小改）

**成立**：全文 planning 与 effect 分离（"所有数字是规划算术、不是效果证据"多处）；不运行 acquisition/训练/回放；不复活 A1/A2（只引用其更新器/DPG 接口）；B/C/RSI 未启动；引用 C136/C144/C154/C156/C171 的边界；不声称新颖性；未改其它目录；headroom 结论有"不推广到所有菜单"的限定（record/R198 摘要）。

**小改**
1. 补显式谱系句：**不重跑 R187 的预测方差采样**（S4/S6 是新的 stage-3 比较器，不是 R187 的复活）；**R2 的 5-cell 菜单阴性保留为菜单属性/教训，不外推为 acquisition 一般阴性**；A5 是"第 2 步成立后"的 stage-3 新对象，需在 P0 与 prior_art §4 明写。
2. R198 当前状态引用：补 **C176/C177**（R196/R197 已作废），说明"第 2 步尚无结果、A5 只能冻结不执行"；避免读者把 R197 的协议作废误读为 step-2 已完成。
3. 措辞模板：把"未发现直接先例"统一为"本轮有界检索未发现（非穷尽；不证明不存在）"；"规划数"处避免"差 5.8–6.3 倍"这类未标注来源的数字（见 ① 修正）。

## 2. 五条必改（冻结前完成；不改则不得进入候选冻结）

1. **物理成本重算**：按真实板布局重推 A2/A3 的参照/对照摊销（per-plate vs per-key 二选一并写死）；已实测动作（R2 766 wells/2 板）不乘 eta；重算 campaign/等成本/敏感性，并修正 "2.5–5.2×"、"5.8–6.3×"、"~450×" 三个数字（用 JSON 可复算值；明确口径）。
2. **等成本可执行化**：冻结 cell 集合与 setup 会计（charged/sunk 全局一致；charged 时预算须覆盖 setup）；写死 filler/残余容差/under-spend 方向；三场景下按各自预算**重跑策略**；主指标改为配对 `ΔNB`（等 total CU），`NB per CU` 仅描述。
3. **headroom/MDE 修正**：CI 宽度 ≠ MDE（量化 0.715 关系）；删除"任何 acquisition 比较的 MDE 都大于 headroom"的全称句，改为可复算的粗代理陈述；`MDE_decision` 必须按 P5 在决策指标上预计算；**声明 headroom/oracle 仅适用于回溯 replay**；菜单构造纯元数据、不得按 headroom 挑菜单。
4. **预算/停止/失败类别**：给 45 min 与 7 策略×2 seed 集×3 场景的一致时限表；补 `oracle_unknown`/`cost_uncalibrated`/`protocol_deviation`/`not_identifiable` 并把 `inconclusive` 拆分；δ_min 无 operational 定义时标 `blocked_by_utility_definition`；P9 增加"无量纲 CU 预算"可冻结形态或明确保持 blocked。
5. **谱系/措辞**：显式"不重开 R187 方差采样；R2 菜单结论仅作约束/教训；A5 是第 2 步成立后的 stage-3 对象"；补引 C176/C177；统一"未发现≠不存在"与 planning-only 模板。

## 3. 最致命 3 条（判断顺序）

1. **成本物理锚点两处事实错误（①-1/①-2）**：per-key 参照/对照与 per-plate 锚点混淆 + R2 实测 2 板被 eta 算成 4 板 → 所有 CU/campaign/等成本数字的可信度受损；这是"等预算比较"的地基。
2. **等成本比较的可执行性缺口（①/④-2/④-3/②-4）**：cell breadth 未冻结、filler/三场景重跑未写死、S1 买不起 → 即使数字修好，比较仍不可执行/不公平。
3. **headroom/MDE 推论过度 + oracle 可算性未声明（③-1/③-2/④-1）**：CI 宽度当 MDE、"任何"全称句、菜单可按 headroom 选、oracle 只在 replay 可算——这些直接影响"是否该运行"的判定。

## 4. 是否值得进入候选冻结？

**否（本轮）**。A5 应作为**第 3 步执行设计的候选稿保留**；冻结前需要：(a) 完成上述 ≤5 必改并再次独立挑战；(b) 第 2 步（固定反馈修订迁移）出现可迁移证据（目前不存在，见 C176/C177 与 R198 记录）；(c) 关系集/更新器接口（A1v2）就位并冻结。修完后 A5 的价值是"可审计的成本/等成本/headroom 闸设计"，而不是新算法或效果主张。

## 5. 本挑战的限制

- 只审阅设计与算术，不运行 acquisition/训练/回放；未核 A5 引用的外部论文原文（沿用 A5 的 F01–F16 本地记录）；未复现 R2 原始结果（只核对报告数字）。
- 挑战中的"修正后数字"（如 446,000 CU、−21.7%、0.715×CI）只是**示性复算**，用于证明文档数字可被独立检验；冻结时应由 A5 用真实板布局重算，而非采用本文件的示例值。
- 复算脚本：`tmp/a5_challenge_checks.py`（只读 A5 的 JSON，不写 A5 目录）。
