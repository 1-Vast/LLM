# REVISION_A4：按 challenge_A4.md 的修订账（独立候选 → A1 的 (iii) 状态模块）

2026-10-27 ｜ 执行：drugcomb-auditor（task-44）｜ 对象：v1 `{spec.md, prior_art.md, protocol_draft.md, record.md, usage.json}`（**不改**）。v2 新增：`spec_v2.md`、`protocol_draft_v2.md`、本文件、`record_v2.md`、`usage_v2.json`。
依据：`challenge_A4.md`（endpoint-auditor，task-39）；其总判决 **"独立候选 stop；作为 A1 的 (iii) 状态模块 revise（≤5 必改）"**。本文件逐条登记"挑战项 → v2 落点 → 是否已修 / 残余"。
纪律：本轮未运行效果/未训练/未拟合/未估 Q/未读响应做统计；未改 v1 与其它目录；数字均为 metadata/设计算术。

## 0. 总处置

- **接受挑战总判决**：A4v1 作为独立候选 **stop**；A4v2 **不独立候选**，收为 **A1 的 (iii) 状态模块**；**不独立下发 F1/F2/F3 判定**；A1 冻结后启用（当前 `blocked_by_A1`）。
- **二选一输入已写死**：采用 **A1 冲突证书**（`{J, C_conf, X_flip, Δ_pred(U), setup 诊断}`）；**删除 v1 的 Q-flip 主对象与 SCC 独立机制陈述**；不另立 Q-flip 改名路径（若 Lead 要独立候选，须改名另立协议，本 v2 不做）。
- **v1 保留物**：三类失败的 operational 定义（作为引用，不据以判类）、F3 的强制措辞、状态变量清单框架、先例覆盖与"不声称新颖性"、Phase 0"零新增测量先诊断"的思路（降级为描述/筛选）、Phase 1 对照清单方向、失败类别与"阴性不写成不存在"的纪律。

## 1. 三条最致命项的逐条落点

### 致命 1：F1 vs F3 在 Phase 0 结构性不可分 → 已修（降级 + 分离入口）

- **挑战要点**：`flip=1[sign(Q_O)≠sign(Q_V)]` 是跨唯一 O/V 两组的差异；F1 对照 `M4=K+g` 的 `g` 在单位级不存在；cell 级静态 S 只能测 state-associated instability（必要非充分）；Phase 1 被写成 Phase 0 显著之后 → 程序性死锁。
- **v2 落点**：
  - `spec_v2 §2.2`：明确 Phase 0 上限 = `state-associated instability`（描述/筛选），**不判 F3**；F1/F3 真正分离只能靠 ≥3 独立 context 或 Phase 1 within-cell 操纵。
  - `spec_v2 §2.3` + `protocol_v2 §3.2`：**删除 `M4=K+g`**，改为可执行的 `M4 = K + barcode/plate + screen 元数据`；补 **cell one-hot/identity、plate/barcode、leverage/投影核**基线（挑战 ①(d)/(e)）。
  - `spec_v2 §5.3` + `protocol_v2 §3.6/§4.1`：**Phase 1 进入条件不再依赖 Phase 0 显著**；改为 `A1 冻结 && 证书可算 && Phase 0 描述性候选选择规则 && Phase 1 design check`。明确"Phase 0 inconclusive ≠ F3 不存在 ≠ 表征无信息"。
  - `protocol_v2 §3.3`：flip 阈值由噪声模型预注册（`|Q|>z·σ_tech`，z∈{1,2,3} 敏感性，主 z=2），**禁止结果驱动选阈值**；"cross-screen flip > 同 screen 技术噪声"只作描述性检查、不作 F3 判据。
  - `protocol_v2 §3.5`/§4.5：失败类别补 `inconclusive_design`、`leakage`、`indistinguishable_F1_F3`。
- **残余**：F1/F3 的真正分离仍只能由 Phase 1（新测量）或 ≥3 context 提供；A4 自身**不判**，由 A1 归类；A1 未冻结 → 当前不可执行。

### 致命 2：可用性/功效高估 → 已改正数字（并实测复核）

- **挑战要点**：matched 96 中表达 84、突变 95、culture_type 54、medium 55、联合 54（v1 只报 111/125）；`DAY1/GR/DT` 是同屏对照读数（每细胞中位 4 个 level），不能当 S；A0 MDE=0.240 → **0.112（C168）**；1,312 是 **A2 q2.json** 的 barcode 分半标定（1.43% 覆盖），不是 A0；δ_min=0.10 无 operational 依据。
- **本挑战独立复核（metadata-only，`tmp/a4v2_numbers.py` → `tmp/a4v2_numbers.json`）**：
  - matched 96（A0 `matched_conditions.csv`，norm 名后 96/96 可映射 DepMap）；
  - 表达 **84**、突变 **95**、culture_type **54**、culture_medium **55**、表达+突变+culture_type 联合 **54**、再+medium 仍 **54**（与挑战数字一致）；
  - `q2.json → design_check.noise.n_calibration_quadruples = 1312`，`coverage_frac_of_observations = 0.014255`（1.43%）；**a0.json 不含 1312**；
  - C168/SYNTHESIS:11：五折主端点 **MDE=0.112**，0.240 为各折均值、"资源不可用"表述已撤回。
- **v2 落点**：
  - `spec_v2 §4.1`：表格化披露 84/95/54/55/54；明确 Phase 0 分析集 = **54（完整 S_pre）/84（表达子集）**；92,039 条 unit 不是独立 n。
  - `spec_v2 §3`（S_pre/S_measure 表）：**`DAY1/GR/DT` 改归 `S_measure`**，只作 F1/F2/batch 控制，不得支持 F3；`S_pre` 只含表达/突变/culture 注释。
  - `spec_v2 §4.1` + `protocol_v2 §1`：A0 MDE 改 **0.112**（C168），0.240 不再引用；并继续标"仍>0.05，54/84 细胞下很可能 inconclusive_power"。
  - `spec_v2 §4.2` + `protocol_v2 §3.3`：1,312 改引 **A2 q2.json**，明确同 screen/1.43% 覆盖/barcode-rich，只作技术噪声；不当作跨 screen null。
  - `spec_v2 §5.2-5.4` + `protocol_v2 §3.4`：δ_min 改为 **operational**：决策层 δ_min 由"状态测量请求净成本 ≤0"定义（成本用 A5 anchored key **34–68 wells/key** 或 state-readout 板 **1,536 wells/细胞**；A1/A5 未冻结前 Phase 0 不判定）；可执行替代 = `δ_min_AUC = max(0.05, 2×SE_null)`，敏感性 {0.05,0.10,0.15}；v1 的 0.10 仅作敏感性档。
  - `protocol_v2 §3.4`：MDE 模拟写死模型/维数上限（54→≤5、84→≤8，EPV≈10）/λ 网格/seed=20261027/聚类 bootstrap ≥2,000/零模型/配对口径。
- **残余**：Phase 0 实际分析集仅 54/84 细胞，MDE 很可能 >δ_min → 预期 `inconclusive_power`；这不是 F3 阴性。

### 致命 3：Phase 1 设计与算账不成立 → 已重写（well 账/功效/桥接/对照）

- **挑战要点**：`2×2×6×2×2=96` 非 192；`4×6×2×2×2=192` 非 384；两版都不含单药参照/对照（ΔEMAX 必需；A5 anchored key 34–68 wells/key）；12 pair-cell 单元无 state×sign 功效；操纵（培养基/氧）与 Phase 0 S 无桥接且属 g → F3 被误测为 F1 的风险。
- **v2 落点**：
  - `protocol_v2 §4.2`：**修正计数**（96/192，非 192/384）；给出 **完整 well 账**：anchored key = 14 combo + 5 anchor-alone + 4 library-alone + 8–16 controls/QC = **34–68 wells/key**（A5 锚点）；加 **day1 无药对照板 1,536 wells/细胞**、**密度优化 1,344 wells/细胞**（A5 锚点）。
    - Pilot（2 细胞×6 条件×2 状态×2 批；48 keys）：7,392–9,024 wells ≈ 4.8–5.9 板；Main（4×6）：14,784–18,048 wells ≈ 9.6–11.8 板；（6×8）：23,808–30,336 wells ≈ 15.5–19.8 板；技术重复×2 另计；失败 1.5% 另计。
  - `protocol_v2 §4.3`：**功效写死**：独立单位 = pair-cell；24 配对在 discordant 25%、OR≈4 时功效约 50–60%（不足）；48 配对约 80%+；**24 配对只作 pilot/可行性与操纵检查，不产出 F3 证据**；主 F3 证据需 ≥36–48 pair-cell 或更多批/重复；否则 Phase 1 输出 `inconclusive_design` + `measurement_request`。
  - `spec_v2 §6.1` + `protocol_v2 §4.1`：**桥接**——操纵的是**与 Phase 0 同类可测的状态 `S_measure`**（接种密度/时间 → day1 生长/活力），不是培养基/氧（后者明确标为 g，归 (ii)/(iv)）；预注册桥接规则（按 Phase 0 state_association 分层选细胞；2 状态水平；同批测 S_measure；预测方向）。
  - `protocol_v2 §4.1`：补 **vehicle/阳性对照/edge/位置随机化/盲法/独立培养认证**（barcode 不相交 ≠ 独立培养，R2 教训）；补 `inconclusive_design`/`leakage`/`indistinguishable_F1_F3`/`cost_sensitive` 失败类别。
- **残余**：Phase 1 需真实新测量/预算/采购；well 账已给但成本系数未由报价替换（A5 同状态）；操纵与 Phase 0 的桥接仍是设计假设（需 pilot 的操纵检查验证）。

## 2. 六项判决的逐项落点

| 挑战项 | v1 判决 | v2 落点 / 状态 |
|---|---|---|
| ① F1/F2/F3 可区分性 | FAIL | 已修：删 M4=g；补 cell one-hot/plate/barcode/leverage；Phase 0 降级为 state-associated instability；Phase 1 独立入口；阈值/噪声预注册；`inconclusive_design` 补入（spec_v2 §2–§3；protocol_v2 §3） |
| ② 可用变量与功效 | WEAK（含 2 FAIL） | 已修：84/95/54/55/54；S_pre/S_measure 拆分；0.112；1,312→A2；EPV/δ_min/MDE 写死（spec_v2 §3–§4；protocol_v2 §3.4） |
| ③ 先例与差异 | WEAK | 已修：明确**本轮无新检索**、复用既往登记（不再称"有限检索"）；不声称新颖性；补缺口建议（spec_v2 §9；record_v2 §2） |
| ④ 最小实验 | FAIL | 已重写：完整 well 账、功效、桥接、对照、失败类别；96/192 计数更正（spec_v2 §6；protocol_v2 §4） |
| ⑤ 接口/去重/措辞 | WEAK | 已修：所有权表、启用门、输入二选一、逐条去重（A1 v1 P6/P7 与 v2 重编号、A2 III、A3/C175、C174/C176/C177、A5）、Phase 2 复用 A5（spec_v2 §0/§8；protocol_v2 §7） |
| ⑥ 总判决 | stop（独立）/ revise（模块） | **v2 = 模块 DRAFT**；不冻结；A1 冻结后才启用；A1 未冻结 → `blocked_by_A1` |

## 3. 5 条必改的落实对照（挑战 §7）

| # | 必改（挑战原文摘要） | v2 落点 |
|---|---|---|
| 1 | 对象与所有权：A1 owns (i)/(ii)/三类总判定；A4 只做 (iii) 状态变量/状态条件化/测量动作；启用门 = A1 冻结；输入二选一（A1 证书或 Q-flip 改名），删 SCC | 已写死：`spec_v2 §0` 所有权表 + 启用门 + 输入选择（A1 证书；删 SCC/Q-flip 主对象）；`protocol_v2 §0` |
| 2 | F1/F3 判据/对照重写：Phase 0 上限=state-associated instability（必要非充分），不判 F3；M4 改 K+barcode/plate+screen；补 cell one-hot/plate/barcode/leverage；flip 阈值/噪声模型预注册；inconclusive_design；Phase 1 不以 Phase 0 显著为条件 | 已写死：`spec_v2 §2.2–2.3/§5.3`；`protocol_v2 §3.2–3.6` |
| 3 | 数字改正：84/95/54/55/54；S_pre/S_measure；A0 0.112；1,312→A2；δ_min operational；MDE 模拟写死 EPV/seed/聚类 | 已写死：`spec_v2 §3–§4`；`protocol_v2 §1/§3.4`；本文件 §1 附实测复核 |
| 4 | Phase 1 重写：完整 well 账（combo+ref+ctrl+QC，A5 anchored 34–68 wells）；12 单元功效或扩 4–8 细胞系；桥接；vehicle/positive/edge/blinding/独立培养；失败类别补 3 类；修正 192/384 | 已写死：`spec_v2 §6`；`protocol_v2 §4` |
| 5 | 先例/去重/措辞：补检索回执或明确无新检索、降级"未发现"；逐条标注 A1 P6/P7、A2 III、R197/C177、A5；引 C174/C175/C176/C177；Phase 2 复用 A5；删未定义 192；保留/加强措辞模板 | 已写死：`spec_v2 §8–§10`；`protocol_v2 §7`；record_v2 §2（无新检索） |

## 4. 保留项（挑战 §8 = 值得留下的）

- 三类失败 operational 定义（引用，不据以判类）——`spec_v2 §2`。
- F3 强制措辞——`spec_v2 §10`（"F3 只表示在该设定/该状态变量集上……"，并补"不得把 inconclusive 写成 F3 阴性/阳性、不得把 A4 当 A1 通过"）。
- 状态变量可用性清单——`spec_v2 §3–§4`（已按挑战修数字/粒度）。
- 先例覆盖框架 + 不声称新颖性——`spec_v2 §9`；`prior_art.md` v1 保留不改。
- Phase 0"零新增测量先诊断"——已降级为描述/筛选（`protocol_v2 §3`），不作判定/不作 Phase 1 门。
- Phase 1 对照清单方向——保留并补齐（`protocol_v2 §4.1`）。
- 失败类别与阴性纪律——扩充并写死（`protocol_v2 §3.5/§4.5`）。

## 5. 残余缺口（v2 仍不解决；写实）

1. **A1 未冻结**：A4v2 = `blocked_by_A1`；A1 证书 schema/字段未冻结，Phase 0 不能执行。
2. **State 面板覆盖只有 54（完整）/84（表达）**：Phase 0 M2 的 EPV 紧；预期 `inconclusive_power`；不能因此判 F3 不存在/表征无信息。
3. **Phase 1 需新测量/预算/采购**：well 账已给，但报价系数未替换（A5 同状态）；操纵↔S_measure 桥接是设计假设，需 pilot 的操纵检查。
4. **先例无新检索**：明确"本轮无新检索、复用既往登记"；latent confounding/batch effect 等补查未做（spec §9 列为建议）。
5. **A2 III 认证、A5 等成本、A1 三类判定**均不在 A4 权限内；A4 只提供状态证据/测量请求。
6. **不声称**：A4v2 不声称三类已区分/不声称状态已证实/不声称新颖性/不声称决策收益。

## 6. 复核方式（本文件数字与来源）

- 覆盖检查：`tmp/a4v2_numbers.py` → `tmp/a4v2_numbers.json`（只读 A0 `matched_conditions.csv` + DepMap 元数据 + `identity_map.csv`；未读表达/响应值）。
- 边界数字：`SYNTHESIS.md:11`（C168 MDE 0.112）；`q2.json → design_check.noise.n_calibration_quadruples=1312`、`coverage_frac_of_observations=0.014255`；`a0.json controlled_anchor=92039`（A1 主边界，非 Phase 0 独立 n）。
- 本文件不改 v1；v1 的 SHA 在 challenge_A4 §9 已登记，未变。
