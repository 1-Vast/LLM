# R198-A3v2 记录（record_v2）

2026-10-27 ｜ 执行：cellstate-lit（task-47，A3v2 修订） ｜ 工作目录：`D:\MAESTRO`。
对象：按 `challenge_A3.md`（drugcomb-auditor，`revise`，≤5 必改，不 stop）修订 R198-A3 为可复审的**"另问" L1 群体时间预测开发资产**。**不进入候选冻结、不进入 L2 决策层。**

## 0. 纪律与范围

- 只写 `research/2026-10-27-innovation-scouting/dynamic_route/` 下**新增**文件（`spec.md`、`protocol_draft_v2.md`、`REVISION_A3.md`、`record_v2.md`、`usage_v2.json`）与 `tmp/`；**不改 v1 文件**、其它目录、INDEX/SYNTHESIS/git。
- **禁止项执行**：未训练模型；未运行时间预测/任何 effect 统计；**未读 h5ad 表达矩阵 `X` 数值/obsm/layers**；未读任何表达派生量或响应/存活数值；未联网（本轮 0 次网络请求）；未声称新颖性/动态世界模型/真实轨迹/决策收益。
- v2 唯一执行的代码：`tmp/a3v2_eligibility.py`（metadata-only：h5ad obs 设计列 + `cell_quality` 计数；另算 v1 文件 SHA）；输出 `tmp/a3v2_eligibility.json`。**不写 dynamic_route v1 产物。**

## 1. 读过什么（本轮）

| 输入 | 用途 | 证据状态 |
|---|---|---|
| `challenge_A3.md`（18,890 B；SHA `04ff07f9…`） | 5 必改依据 | 已读 |
| v1 文件 7 个（`qualification.md`、`protocol_draft.md`、`cadence_evidence.md`、`a3_meta.json`、`a3_inspect.py`、`record.md`、`usage.json`） | 冻结/不改；SHA 复核 | 已读/哈希 |
| `data/external/mixseq_scperturb/mcfarland_2020.h5ad` **obs 元数据** | v2 新算 L1 合格单元（≥20 normal cells；时间匹配 control） | metadata-only |
| `research/2026-10-27-innovation-round-r198/record.md`（只读，line 82/134–141） | 确认 `spec.md` 链接路径与挑战结论 | 已读 |
| `research/EVIDENCE_REGISTER.md` C174/C176/C177 条目（行 212/214/215） | 谱系边界引用 | 已读（已核实条目） |
| `research/2026-10-27-cross-domain-directions/{report.md,evidence_notes.md,directions_v2.md}` | 285 键/动态路线背景、CADENCE/CellFlow/先例 | 已读（v1 已用） |
| `reference/papers/arxiv-2604.27646/paper.html` + `tmp/arxiv_2604.27646.txt` | 有界先例（虚拟细胞 in-the-wild 基准；含 McFarland2020；线性基线） | P（本地 HTML；行锚 :186/:269） |
| `reference/papers.tsv`（行 4/20 等） | State A 级 / benchmark P 级 reading scope | 已读 |
| `research/2026-10-27-handoff-method-audit/report.md:25` | XPert P 级先例 | 已读 |

**未读**：PRISM 响应矩阵（本轮完全未碰；v1 只读过元数据）；h5ad 表达值；任何其它研究目录的 effect 结果。

## 2. 做了什么

### 2.1 `tmp/a3v2_eligibility.py`（metadata-only）

- 从 h5ad obs 计算：V1 每药"药物键 + 时间匹配 control 键均 ≥20 QC-normal cells"的合格细胞系数；V2 hashed 臂 clean single-tag × normal 的逐 (line,treat,time) 计数，及目标 12h/48h 严格合格线；并计算 v1 7 文件 SHA 与 v1 record 表比对。
- 结果（`tmp/a3v2_eligibility.json`）：
  - V1 合格线：**BRD3379 95 / Bortezomib 22 / Idasanutlin 24 / Trametinib 24**（均 ≥20 → V1 confirmatory-development）。
  - V2 严格合格线：**目标 12h = 15 系、目标 48h = 15 系**（<20 → exploratory only）；条件级 231/264 ≥20 normal。
  - `v1_hashes_match_record = true`（5/5 与 v1 record 表一致）。
- 未读表达/响应；未写 v1 产物。

### 2.2 新写文件与决定

1. **补交 `spec.md`**（挑战必改-1 选"补文件"，不选"并入"）：独立可审计的 SPEC（资格摘要、定义、L1 判定门、C3 防泄漏、Q 表修正摘要、先例/边界、失败类别/停止、数据规格、不得声称清单、变更记录、v1 SHA）。R198 record line 82 的链接现在可解析；**未修改 R198 record**（写入范围限制）。
2. **`protocol_draft_v2.md`**（DRAFT）：冻结 L1 δ_min=0.10、G1 split-half 门（rho_sb ≥ δ_min+MDE80）、G2 room 门（room ≥ max(δ_min,MDE80)）、G3 MDE80 门（≤0.10；预运行解析上界 0.41/0.86/0.83/0.83 与 1.06；所需误差相关 0.940/0.987/0.985/0.991）、G4 主效应门、G5 泄漏审计；C3 仅 V2（输入严格早于目标），V1 模型集 {C0,C1,C2,C5,C6} 且禁 24h 派生输入；V2 exploratory（n=15）不判定、不作跨药推断；Q2/Q5/Q7 修正 + "静态/两快照已足够"清单；有界先例 + C174/C176/C177 + 不重开 R196v2/R197v2。
3. **`REVISION_A3.md`**：逐条落实挑战 5 必改（要求→落实→验收）、Q 表 before/after diff、关键数字、v1 7 文件 SHA 冻结登记、v2 新文件 SHA、剩余缺口、结论。
4. **`record_v2.md`**（本文件）与 **`usage_v2.json`**：记录读取边界、执行内容、SHA 与纪律。

### 2.3 统一 `kinetic_horizon` 读取描述（挑战必改-1/5）

- **权威表述（v2）**：仅识别文件名/字节数；仅为判断是否为响应缓存而观察 npz 的 **keys/shapes/dtypes（元数据）**；**未读取任何数组值**；provenance/split/用途**未审计**，不能作为认证终点或 SPEC 输入。
- v1 两处不一致（`qualification.md` §0.4 "只列目录、不读内容" vs `record.md` §1.2/§2.7 "观察 keys/shapes/dtypes"）**不改历史文件**；以 v2 权威表述为准（`spec.md` §2；`REVISION_A3.md` §1 必改-1）。

## 3. 验证

```text
v1 7 文件 SHA 计算：5/5 与 v1 record 表一致（tmp/a3v2_eligibility.json: v1_hashes_match_record=true）
spec.md / protocol_draft_v2.md / REVISION_A3.md 存在且非空（见 §4 表与 REVISION_A3 §5）
tmp/a3v2_eligibility.json 可解析（json.load OK）
本轮未训练/未跑时间预测/未读表达或响应/未联网
```

**无**任何 effect/预测计算；§4 的哈希是文件完整性，不是科学验证。

## 4. 产物与 SHA256

| 文件 | 字节 | SHA256 |
|---|---:|---|
| `spec.md`（新） | 19,330 | `1fc255b4485d369da3ca0dbe57e907c9890fb741883987d0d667c3d50a805121` |
| `protocol_draft_v2.md`（新） | 17,875 | `c58e522b6b450f0f9286053c9a131ccf2c2d2168c00cfda7cbcf6f344daeb89b` |
| `REVISION_A3.md`（新） | 16,796 | `d8a5ecd1e1272a8bc052e25f641f5605332afabaeb3bcd118d38fd3f6b45557d` |
| `record_v2.md`（本文件） | 见 usage_v2 | 不自我内嵌 |
| `usage_v2.json`（新） | 见文件 | 见文件 |
| `tmp/a3v2_eligibility.py` | 7,748 | `f9e09b196de678a987f03c0cd9577e4d665d248f5ea52748f5edc340d21de7be` |
| `tmp/a3v2_eligibility.json` | 6,082 | `0e9178338fdadb8934555e3079e46e39d297c48f5c045294572b853ed23a172c` |
| `tmp/arxiv_2604.27646.txt` | 85,942 | `1c4a0fff5dd88a4eb25163e8d88773c6c02599dc65fbc0478bc9988297d34840` |

**v1 冻结 SHA（不改）**：见 `REVISION_A3.md` §4（7 文件；v1 record 表 5/5 + `record.md`/`usage.json` 补齐）。

## 5. 决定与理由

1. **选"补 spec.md"而非"并入"**：挑战要求二选一；R198 record 与 task-41 均把 `spec.md` 当必读，补文件能最小改动地恢复可审计性；且不修改 R198 record（写入范围）。
2. **L1 判定门选"冻结数值门"而非 exploratory**：挑战要求二选一；给 δ_min/MDE80/room/split-half 门能让"比均值好一点"不被叙述为增量；预运行上界明确写出"很可能 `evaluation_cannot_distinguish`"，这是预期而非失败。
3. **C3 只留 V2**：V1 目标是 24h，C3 若用 24h 作输入即目标泄漏；V2 的 third-time 设定才允许"两快照拼接"。
4. **V2 exploratory**：严格合格线仅 15 系（<20）→ 不作判定/跨药推断，避免把单药 15 系当 24 系/多药证据。
5. **有界先例不新增联网**：全部从项目既有 registry/报告读取（2604.27646 本地 HTML、CellFlow/State/XPert/BATCHIE 已有证据级），符合"不下载/不扩大检索"的纪律；`未发现≠不存在`。

## 6. 限制 / 未完成

- 未运行 L1（本任务禁止）；门是"冻结后运行的规则"，MDE/可靠性未实测。
- V2 只有 15 系合规；即使运行也只能 exploratory。
- L2 仍阻塞（无功能结局/批次/剂量/独立培养）；需 `spec.md` §9 的新测量。
- 先例为有界阅读（非系统检索）；State 全文受限（A 级）、XPert P 级。
- R198 record 未改（写入范围）；`spec.md` 已存在使链接可解析，登记由 Lead 决定。
- v1 的措辞不一致只在 v2 权威描述中统一；v1 历史文件不改（避免伪造）。

## 7. 下一执行者从哪里开始

1. 读 `spec.md`（§5 判定门、§5.3 C3 防泄漏）与 `protocol_draft_v2.md`（§3 Q 表、§5 门实现、§6 泄漏审计）。
2. 若 Lead 要运行 L1：先按 `spec.md` §5 冻结运行代码（代码级断言 V1 模型集、G5 审计、种子/折写死），由未参与修订者复审后**另立任务**运行；**不得**改 δ_min/阈值/切分。
3. **L2 不启动**：等 `spec.md` §9 的功能测量与批次/剂量数据；不换名重启。
4. 若 Lead 只保留一个"另问"资产：A3v2 仅为 L1 开发资产，不进入候选；主线仍按 R198 record 的 Lead 处置。
