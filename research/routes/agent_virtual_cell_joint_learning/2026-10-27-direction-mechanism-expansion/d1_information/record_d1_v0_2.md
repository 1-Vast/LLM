# record_d1_v0_2.md —— R200-D1.1 修订执行记录（v0.2）

角色：独立审计/设计修订员（未参与 R197 模型开发）· 任务 task-94（R200-D1.1）· 日期 2026-10-27
只写 `research/2026-10-27-direction-mechanism-expansion/d1_information/` 的 v0.2 文件与 `tmp/`；**未改 v0.1 文件、其它目录、INDEX/SYNTHESIS/git**；未下载；未训练/拟合任何模型；未读 O'Neil/Validation 响应值。

## 0. 要求与完成对照

| 要求（task-94 / challenge_D1 5 必改） | 状态 |
|---|---|
| 1 修正目标资格（O'Neil 不是空目录、T4 表述、nyman 归类、汇总/所需规格） | ✅ §2、`d1_v0_2.json → facts_v0_2 / E_eligibility_v0_2` |
| 2 锁定目标层级与功效（T3 design_invalid、T2 预注册 MDE、T1 前驱、T4 无目标；不得事后换） | ✅ §3、`F_power`；选择规则写死 |
| 3 操作化主对比/基线/闭包门 | ✅ §4、`G_closure_gate / H_operational_definitions` |
| 4 MDE/δ/cluster/bootstrap/预算写死 | ✅ §3/§5、`F_power.bootstrap`、§4 cap |
| 5 边界/措辞/三处一致 | ✅ §5、`K_wording`；Report/PROTOCOL/JSON 一致 |
| 明确裁定（可执行最小实验 vs stop） | ✅ **默认 stop**（T2 保守规划 MDE80=0.0941>0.05 → `design_invalid: precision_insufficient`；T3 0.2018；T4 无目标）；条件分支见 §1 |

## 1. 裁定与分支（与报告 §0 一致）

- **默认裁定：stop**——无可认证的最小实验。T2（唯一候选 primary）保守规划 MDE80=**0.0941 > δ_min=0.05** → `design_invalid: precision_insufficient`；T3 MDE80=**0.2018** → exploratory only/design_invalid；T1 MDE80=0.0896（内部前驱）；T4 无合格目标。
- **分支 A（需 Lead 明确批准 AMENDMENT）**：预注册**乐观独立规划**（ICC=0、ρ_AB=0）→ T2 MDE80=**0.0414≤0.05**，可提交**仅"跨 screen 同键复现"**的窄化设计（T1 前驱、T3 exploratory），**不得**称独立测量/培养/lineage 或"闭包外/新键迁移"。
- **分支 B（Lead 坚持新键/闭包外独立检验）**：本地无合格目标/功效 → **stop**，所需测量规格见报告 §6/`J_required_measurements`。

## 2. 时间线（Asia/Shanghai，2026-10-27）

| 时间 | 事件 |
|---|---|
| ~23:29 | 读 task-94 并 claim；读 `challenge_D1.md`（revise，5 必改） |
| ~23:32 | 核验 O'Neil/nyman 事实：`data/raw/oneil2026_qualification/` 7 文件/40,543,740 B；`on1.json` DG5 "9/39 cells overlap Jaaks and are EXCLUDED from target set (30 non-overlap cells)"；`jaaks_overlap_frac=0.23076923`；O'Neil 端点 X/X0、368,832 行、39 细胞/583 药对；`nyman2020` 0 文件 |
| **~23:36** | **`PROTOCOL_D1_v0_2.md` 冻结**（5 必改落点、MDE 公式/选择规则、操作化定义；`d1_revision.py` 尚不存在） |
| ~23:38 | 写 `d1_revision.py`（metadata/资格/功效审计；无模型拟合） |
| ~23:40 | 首跑 bug：`on1.json` 的 overlap 字段在 `cells` 子对象下（`on1.get(...)` 返回 None）→ 修正为 `on1['cells']['jaaks_overlap']`；随后成功 |
| ~23:42 | 追加裁定分支字段（T2 过门阈值 ρ≥0.7177；decision_branches）→ **两次完整运行 `d1_v0_2.json` 逐字节一致**（`aeb22543881a8a90dfb94f659c72d445d305a576fec1dd7b713649cf3547ae82`；两次 wall 均 0.2 s） |
| ~23:44 | 报告/记录/usage 完成；标 completed；send_message 给 lead |

## 3. 实现与偏离（全部披露）

- **无统计定义变更**：MDE 公式/ICC 先验/门/选择规则均在 `PROTOCOL_D1_v0_2.md` 冻结后实现；`d1_revision.py` 只做计数与公式计算，不训练/不拟合、不做效应或迁移统计。
- **bug（修复，无产物）**：`on1.json` 的 `jaaks_overlap`/`jaaks_overlap_frac` 嵌在 `cells` 下；首版顶层读取返回 None（`%d` TypeError）。修正后 O'Neil 事实 = 9/39 细胞（23.08%）、30 非重叠目标细胞。
- **数据读取边界**：O'Neil 只读目录清单/既有资格记录（`on1.json`、`PROTOCOL_ON1.md`、`counts.json`、`report.md`），**未读 O'Neil 响应值**；Validation 只读身份/设计列（Barcode/cell/anchor/library/concentration），**未读端点值**；A0 份额为 v0.1 已冻结的只读引用（`share_cellpair=0.03943517`、`share_cond_raw=0.01428744`），作为**规划 ICC 先验**并披露为近似（Q 方差份额 ≠ 秩相关 ICC）。
- **近似披露**：`Var(Δρ)≈2(1−ρ_AB)/(n_eff−3)` 为 Fisher-z 近似；`DE=1+(m̄−1)ICC` 为两路加性设计效应；T2 的过门阈值（ICC≤0.003663 或 ρ_AB≥0.7177）是同一公式的代数反解。
- **运行**：`d1_revision.py` 两次运行（wall 各 0.2 s，≤15 min 预算）；确定性通过（JSON 逐字节一致）；产物 SHA 见 §5。
- **未做**：未运行任何效果/迁移实验；未构造 target 预测；未改 v0.1 文件与其它目录；未下载。

## 4. 关键结果（与报告一致）

- **资格修正**：9 候选 → `qualified=0`、`qualified_with_conditions=1`（Validation，仅跨 screen 同键复测层）、`not_qualified=8`。O'Neil = `not_qualified`（`data_insufficient`+`no_operational_target`；7 文件/40,543,740 B；9/39 共享细胞<10；保守 5 细胞/27 cell×pair 键；X/X0 ≠ ΔEMAX；历史已用非封存）；Nyman2020 = 目录存在/0 文件 → `data_unavailable`；T4 = "无满足 A0 复用门槛的不同测量/培养目标"。
- **功效锁定（保守主规划 ICC priors×1、ρ_AB=0）**：T1 18,782 键 → DE 9.584、n_eff 1,959.8、**MDE80 0.0896**；**T2 9,154 键 → DE 5.156、n_eff 1,775.4、MDE80 0.0941（>0.05 → design_invalid）**；T3 495 键 → DE 1.274、n_eff 388.7、MDE80 0.2018；T2 pair-level 98 → MDE80 0.4067。
- **过门条件**：保守 ICC 先验下 T2 需 ICC≤0.003663（先验的 9.3%）或 ρ_AB≥0.7177；乐观独立情景 MDE80=0.0414（需 Lead 明确批准 AMENDMENT）。
- **操作化**：主模型源特征块 B1–B4 + 闭包排除①（训练集=最大线性无关基 3,005）/③（仅非闭包评估单元）、②投影敏感性；精确闭包基线逐目标定义（T1/T3 键级贡献 0；T2 键级基线=源值直传；派生次级用 target training）；闭包门 ≤5%（S-random 预期失败、S-structural 可用、不得按结果换）；等信息/预算 cap（30 配置、5 折、600 s/1,200 s/8 GB）；Δ=Spearman 差、cluster=cell、配对 bootstrap B=2,000/seed=20261120/percentile；零模型/失败类别/停止条件写死。

## 5. 产物与哈希

| 文件 | SHA256 |
|---|---|
| `PROTOCOL_D1_v0_2.md` | `f77d1c05bb4cf3ffb68529ea75fd6c1cb153b360a2dd376433ad3379f461a302` |
| `d1_revision.py` | `7b67dfd452df9608b9f46ae5046a007f879a86c3c912669fec34fe774e3bc7a4` |
| `d1_v0_2.json` | `aeb22543881a8a90dfb94f659c72d445d305a576fec1dd7b713649cf3547ae82` |
| `report_d1_v0_2.md` / `record_d1_v0_2.md` | 见 `usage_d1_v0_2.json` |
| 只读引用（未改） | v0.1 `d1.json` `F0DC308F…`、`PROTOCOL_D1.md` `E693496F…`、`d1.py` `E9737BF5…`；`on1.json`、`PROTOCOL_ON1.md`、`oneil counts.json`、A0 `a0.json`、`matched_conditions.csv`、Validation fitted（SHA 见 `d1_v0_2.json → inputs`） |

**确定性**：同脚本两次运行 `d1_v0_2.json` 逐字节一致（`aeb22543881a8a90dfb94f659c72d445d305a576fec1dd7b713649cf3547ae82`）；JSON 键排序、无时间戳、`allow_nan=False`；输入/脚本/协议 SHA 写入 JSON。

## 6. 缺口（本轮明确未做）

- 未读 O'Neil/Validation 端点响应；未做任何效果/迁移/相关统计；未构造预测。
- 未为 T2 做实际功效认证（需要目标侧 ICC/ρ_AB 的实测，属执行期预注册步骤；本轮只给保守规划值与过门阈值）。
- 未补独立测量资源；所需规格见报告 §6。
- 三处一致性检查：report §2/§3/§5 与 `PROTOCOL_D1_v0_2.md` §2/§3/§5 与 `d1_v0_2.json → E_eligibility_v0_2/F_power/K_wording` 使用同一判定与数字（已核对）。
