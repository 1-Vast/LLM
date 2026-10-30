# R200-D5.4 纯描述性协议（PROTOCOL_D5_v0_4，DRAFT / descriptive_only）

2026-10-27 ｜ 执行：cellstate-lit（task-100） ｜ 状态：**descriptive_only（按 challenge_D5_v0_3.md 的 revise/5 必改修订；不运行效果）**。
上游：`challenge_D5_v0_3.md`（endpoint-auditor：**revise**；修完 1–3 后建议 `approve_to_lead_exec_descriptive`；不 approve confirmatory；不 stop）。
历史：v0.1/v0.2/v0.3 全部冻结不改；**v0.4 是唯一描述性执行依据候选**。
本轮只做文档/预算/SHA 自洽修订：**不运行效果、不拟合预测、不读表达或响应矩阵、不联网**；不称新颖性/机制/迁移/决策收益/biology/功能/真实轨迹。

> **核心声明（不变）**：**本分析不检验时间预测是否成立；只描述可达到的精度与方向。** 所有 Δρ/CI/MDE/room/reliability 均为描述性/精度描述子，**不用于 confirmatory 推断**；**不设 H-D5-1 检验、不设 G3/G4 通过/失败、不把 `evaluation_cannot_distinguish` 当推断**。

---

## 0. 相对 v0.3 的 5 必改（challenge_D5_v0_3 §2）

| # | 必改 | v0.4 落实 |
|---|---|---|
| 1 | **旧 SHA/size 残留**：v0.3 protocol §12/report 引用与实际不符的旧值；须改为实际 `d5_revision_v0_3.py`/`d5_v0_3.json` 值；全文清除旧前缀 | **已改**：v0.4 引用实际 **code `D66FBDBE…`（27,070 B）**、**JSON `97250A0B…`（28,629 B）**；v0.4 全部产物**不含旧 SHA 前缀**（已检索）；v0.3 冻结历史保留旧值，v0.4 为运行依据 |
| 2 | **E7 总拟合数算术**：6 tuned models × 600 = **3,600**（不是旧总数） | **已改**：`total_tuned_fits = 3,600`、`max_fits_total = 3,600`；同步 protocol/JSON/report/usage/checklist；**不预注册第 7 个模型**；tuning-grid SHA **`4d3b6d02…`** |
| 3 | **CPU/wall 预算预检**（3,600 fits + 零模型，120 min cap；超→`protocol_deviation` stop） | **已补**：`budget_precheck`（两跑合计估算 **34–67 min**，期望 **~45 min**；cap **120 min**；预执行 synthetic timing test；超 → `protocol_deviation` STOP；**不得放宽 cap**） |
| 4 | **描述性执行冻结**：E1–E12 执行版、EX-G0b 先核、两跑/schema；禁止 confirmatory/biology 等 | **已冻结**：§5 E1–E12 v0.4、§6 EX-G0b、§7 两跑/schema/描述性字段；禁止项写死 |
| 5 | **Lead 文本**：仅 approve descriptive_only；confirmatory→stop+规格 | **已写**：§9 `lead_approval_suggested_text`；confirmatory → **stop + 测量规格**（每药约 1,571 独立细胞系或 r_err≥0.987/0.985；配对/功能/batch 新测量） |

---

## 1. 范围（纯描述性）

- **保留**：3 active drugs（Bortezomib n=22 / Idasanutlin n=24 / Trametinib n=24）；V1 6h→24h **RNA 分子代理**；V2 Trametinib 5 时点 **exploratory**（paired **15/16/15**，n<20）；BRD3379 **zero-dose/vehicle-like control（secondary/descriptive only）**。
- **不做**：confirmatory H-D5-1；G3/G4 通过/失败；`evaluation_cannot_distinguish` 推断；biology/功能/迁移/决策/机制/新颖性/真实轨迹；L2 决策层；重开 R196v2/R197v2。
- **资格边界（写死）**：功能路由 `not_qualified`（RNA 代理≠功能）；`time_axis_unverified`（无 batch/plate/run/exposure/独立培养/重复；破坏性快照）。
- **Lead 若要求 confirmatory**：**stop + 测量规格**；不得用描述性运行替代。

---

## 2. 数据与设计（与 v0.3 一致，仅修 SHA/预算）

| 项 | v0.4 |
|---|---|
| 单元 | 细胞系（非 key/细胞/时间点） |
| V1 端点 | 6h early RNA → 24h late RNA 分子代理：QC-normal pseudobulk logFC（相对时间匹配 control）；train-only top-200 基因 logFC 均值 |
| V1 active drugs | Bortezomib 22 / Idasanutlin 24 / Trametinib 24（各自合法线；**不做跨药配对**） |
| V1 切分 | leave-cell-line-out 5 折（排序后 `index%5`）；内层 5 折按细胞系分组；标准化/PCA/基因集/λ 只训练折 |
| BRD3379 | zero-dose/vehicle-like control（0.0 µM、无 ChEMBL）；secondary/descriptive only；**永不进 primary** |
| V2 | Trametinib 5 时点 + DMSO；目标 24h/48h；输入严格更早；**paired 15/16/15**；n<20 → exploratory only |
| 功能/时间轴 | not_qualified / unverified（边界不变） |

---

## 3. 纯描述性分析（无 confirmatory）

- **V1 per drug**：报告 `ρ(early6h)`、`ρ(static)`、`Δρ=ρ_early−ρ_static`、Δρ 的 cluster-bootstrap CI（按细胞系）、`MDE80`、`room=ρ_oracle−ρ_static`、split-half 可靠性（Spearman–Brown）、per-fold Δρ、折清单 SHA、选中超参数。
- **摘要**：3 active drugs 等权平均 Δρ、per-drug 范围、**精度描述**（MDE/room/reliability 与 Δρ 的关系）。
- **BRD3379**：仅 secondary/描述；强制标注 zero-dose/vehicle-like control；不进入任何 primary 摘要/均值/CI。
- **V2**：每个对比报告 n_E1/E2/E3、**paired n（15/16/15）**、paired Δρ、CI、per-fold、capacity control 结果；**exploratory only**。
- **禁止推断**：不做 H-D5-1 confirmatory 检验；不报告 confirmatory p 值/显著/支持/证明；不设 G3/G4 通过失败；`evaluation_cannot_distinguish` 不再作推断；不写 biology/功能/迁移/决策/机制/新颖性/真实轨迹；不把 RNA 当功能。
- **精度描述子**：`descriptive precision insufficient for confirmatory inference`（描述，不是检验判定/阴性/不存在）。

### 3.1 描述性报告字段（执行时冻结 schema）

**V1 per drug**：`drug, n_eligible_lines, rho_early6h, rho_static, delta_rho, delta_ci_low, delta_ci_high, mde80, room, reliability_split_half, per_fold_delta_rho, fold_manifest_sha256, gene_panel_sha256, pseudobulk_sha256, selected_hyperparameters`。
**Summary**：`active_drug_equal_weight_mean_delta_rho, min/max_per_drug_delta_rho, descriptive_precision_note`。
**BRD3379**：`role, n_eligible_lines_secondary_only`。
**V2**：`target_h, E1/E2/E3, n_E1, n_E2, n_E3, paired_n, delta_rho, delta_ci, per_fold, capacity_control_result, exploratory_only`。
**禁止字段**：confirmatory p-value/判定、biology/function/migration/decision/mechanism/novelty/真实轨迹。

---

## 4. E6 零模型（冻结 1,000）

- **N1 cell-shuffle**：同 drug/time/fold 内置换细胞系标签（细胞不配对），**1,000 次**。
- **N2 drug-shuffle**（V1）：3 active drugs 间置换早期特征药物标签，**1,000 次**。
- **N3 time-shuffle**（V2）：同 (line,treatment) 内允许更早时间标签置换，**1,000 次**。
- **N4 capacity control**（V2）：同维随机特征加 E1 / 第二时点特征置换，**1,000 次**。
- **N5 future-leak sentinel**：目标时点特征替代早期特征（应接近 oracle；否则 fail closed），1/折/arm。
- **N6 static-capacity**：同维随机基因块，**1,000 次**。
- 合法规则：只在同折/同药/同时间层置换；不混合折；保留边缘；真实与零模型同调参预算；seed `20261027`；**不得低于 1,000**（除非预注册功效依据）。

---

## 5. E7 调参 + 预算预检（冻结；无拟合）

### 5.1 调参计划

- **环境**：scikit-learn 1.9.0、numpy 2.4.6、pandas 2.3.3、scipy 1.17.1；CPU。
- **共同预算**：内层 5 折按细胞系；每 tuned model **8 candidates × 5 folds = 40 fits/outer unit**；outer units = 5 折 × 3 active drugs = 15 → **600 fits/tuned model**；**6 tuned models（B1/B3/B4/B5/B7/B8）→ 3,600 fits total per run**；**不预注册第 7 个模型**。
- **网格**：B1/B3/B7/B8 ridge alpha = [0.01, 0.1, 1, 10, 100, 1e3, 1e4, 1e5]；B4 HistGradientBoosting 8 个预注册组合（max_depth {2,3}、learning_rate {0.03,0.1}、max_leaf_nodes {7,15}、l2_regularization {0,1}）；B5 GP length_scale {0.1,1,10,100} × alpha_white {1e-3,1e-2} = 8。
- **未 tuned**：B0 mean、B2 cell identity、B6 simple linear-time（V2 closed-form）。
- **冻结**：tuning-grid SHA **`4d3b6d02474505b6fe67e31bce837784dbb85ce91b03ec3d1c9f540d2bbc66b5`**；运行前冻结，结果后不得改；同预算可核查；禁止用测试折调参。

### 5.2 CPU/wall 预算预检（新；不运行效果）

| 组件 | 估算（两跑 + 零模型） |
|---|---|
| 数据加载/QC/pseudobulk（×2） | 16–32 min |
| 3,600 tuned fits/run（×2） | 8–15 min |
| untuned B0/B2/B6（×2） | 1–2 min |
| 零模型：N1/N2/N3/N6 标签置换（冻结预测；4×1,000×15 units，无 refit）+ N4 1,000 随机特征 × 15 units ridge + N5 sentinel | 4–8 min |
| 报告/IO/overhead（×2） | 5–10 min |
| **合计** | **34–67 min（期望 ~45 min）** |

- **cap = 120 min（两跑合计）**；**不得放宽**。
- **预执行**：先用同维 synthetic arrays 做 timing test（不读表达/响应、不产生生物学结果），测 wall 并投影；若投影/实测 > 120 min → **`protocol_deviation` STOP**，不得放宽 cap。
- 执行时必须报告：实测 precheck wall、各组件 wall、实际 fits 数、两跑一致性。

---

## 6. 执行前置门 EX-G0（不是推断门）

- **EX-G0a 覆盖**：每 active drug ≥20 合法线（22/24/24 → pass）。
- **EX-G0b active-dose/identity 先核**：执行前必须**实测/记录**：
  ① compound identity；② actual dose（µM）；③ vehicle identity；④ identity 来源/assay。
  metadata-level 注释不够。**失败 → `active_dose_identity_unverified` STOP**；**BRD3379 永不回 primary**。
- 执行前还须确认：功能 not_qualified、time_axis_unverified 在报告中如实标注；不得当"可推断"。

---

## 7. E1–E12（v0.4 执行版，冻结；本轮不执行）

| id | 内容 |
|---|---|
| E1 数据加载 | h5ad obs+表达（执行时）；QC=`cell_quality=="normal"`；pseudobulk mean per (drug,line,time)；对照=时间匹配 control（V1）或 DMSO hash（V2）；logFC=log2((pseudo+1)/(ctrl+1))；记录细胞数；不做表达选择；输出 pseudobulk SHA |
| E2 200 gene panel | 每 drug/target/fold 用训练线 mean |logFC| top-200；冻结 gene list SHA；测试线不进 |
| E3 fold loader/assert | 加载 v0.4 折清单；断言划分/无跨折线/`index%5`/seed/SHA |
| E4 V1 无跨药配对 | 每 active drug 用自己合法线（22/24/24）；不跨药配对；报告 per-drug |
| E5 V2 paired | 只用 paired sets：24h E1/E2=15；48h E1/E2=16、E2/E3=15；输入严格更早 |
| E6 零模型 | N1/N2/N3/N4/N6 = 1,000 次；seed 20261027；合法零/聚类/配对规则；N5 future-leak sentinel；fail closed |
| E7 调参/预算 | 6 tuned models × 600 = **3,600 fits/run**；8 candidates × 5 inner；CPU cap 120 min 两跑；预算预检；grid SHA `4d3b6d02…`；no test tuning |
| E8 两跑/schema | 同 seed 跑两次、输出逐字节一致；固定 schema（§3.1）+ config/fold/gene-panel/pseudobulk SHA |
| E9 描述性测量 | split-half reliability/room/MDE 作为**精度描述子**；无 pass/fail；不得写 `evaluation_cannot_distinguish` 推断；记录实测值 |
| E10 描述性报告模板 | §3.1 字段 + 精度标签；禁止 confirmatory/biology/function/migration/decision/mechanism 语言 |
| E11 G5 断言 | 目标/未来时间不在输入；V1 无两快照臂；折按细胞系；预处理仅训练折；future sentinel；fail closed |
| E12 本轮不运行 | 本轮无效果/预测/表达读取；执行需另立任务 + Lead 批准 |

---

## 8. 失败类别 / 停止条件（v0.4）

- 执行/资格类：`data_unavailable`、`active_dose_identity_unverified`、`design_invalid`、`time_axis_unverified`、`functional_route_not_qualified`、`identifiability_unsupported`、`protocol_deviation`。
- 描述性精度标签：`descriptive_precision_insufficient`（**精度描述，不是检验推断**）。
- **停止**：EX-G0a/G0b 失败 → 停；泄漏 → 停；**预算超 120 min → `protocol_deviation` 停，不放宽 cap**；无功能 → 停功能主张；无 batch/exposure → 停绝对时间/轨迹主张；不换端点/阈值/切分；BRD3379 不回 primary；confirmatory 需求 → stop + 测量规格。

---

## 9. Lead 批准文本（建议；仅 descriptive_only）

> **批准 D5 v0.4 进入一次纯描述性执行（descriptive_only；非 confirmatory）。**
> 冻结：protocol_v0_4 SHA、code `d4d627a1…`（24,172 B）、JSON `3d6fbf82…`（36,343 B）、report/record/usage SHA（见 `record_d5_v0_4.md`）；v0.3 实际 code `D66FBDBE…`（27,070 B）/JSON `97250A0B…`（28,629 B）为历史输入。
> 预算：E7 **3,600 tuned fits/run（6×600）**；零模型 N1/N2/N3/N4/N6 各 1,000；两跑 + overhead 估算 **34–67 min**、期望 ~45 min；**CPU cap 120 min**；预执行 synthetic timing test，超 → `protocol_deviation` stop，不放宽 cap。
> 范围：3 active drugs（22/24/24）、V1 6h→24h RNA 分子代理、V2 exploratory（15/16/15）、BRD3379 secondary only；**不检验 H-D5-1、不设 G3/G4 通过失败、不写 evaluation_cannot_distinguish 推断**；只报 per-drug Δρ/CI/MDE/room/reliability/per-fold；不称 biology/功能/迁移/决策/机制/新颖性/真实轨迹；RNA 代理≠功能。
> 停止：EX-G0a/G0b 失败→stop；泄漏→design_invalid；超预算→protocol_deviation；功能/时间轴边界不变；**若要求 confirmatory → stop + 测量规格**（每药约 1,571 独立细胞系或 r_err≥0.987/0.985；配对/功能/batch 新测量）。
> 其他：v0.1/v0.2/v0.3 未改；BRD3379 永不回 primary。

---

## 10. 边界 / 不称

- A3v2 `L1/L2` 仅背景；不重用未认证部分；C176/C177/C179/C181/C186 仅背景；不重开 R196v2/R197v2；R195 ERRATA_A3 范围限制保留。
- **不得声称**：confirmatory、支持/证明时间预测、biology、功能/viability、迁移、决策收益、机制、新颖性、真实轨迹、动态世界模型；BRD3379 不是 active drug；RNA 不是功能。
- 功能/决策/轨迹需新测量。

---

## 11. SHA / 确定性 / 批准路径

- **v0.3 实际值（v0.4 引用，冻结历史）**：`d5_revision_v0_3.py` **D66FBDBE…（27,070 B）**；`d5_v0_3.json` **97250A0B…（28,629 B）**；v0.3 protocol/report 中的旧 SHA 值**已不再被 v0.4 引用**；v0.4 全部产物不含旧前缀（已检索）。
- **v0.4 新产物**：`d5_revision_v0_4.py` **d4d627a1…（24,172 B）**；`d5_v0_4.json` **3d6fbf82…（36,343 B）**；两次运行逐字节一致；`PROTOCOL_D5_v0_4.md`/`report_d5_v0_4.md`/`record_d5_v0_4.md`/`usage_d5_v0_4.json` 的 SHA 见 record/usage；tuning-grid SHA **4d3b6d02…**。
- **批准路径**：修完 1–3 后**建议 `approve_to_lead_exec_descriptive`**（仅描述性、非 confirmatory；成本可控）；当前 `approve_to_lead_exec = lead_decision_required`，**不自行批准**。
- **confirmatory 不可行**：MDE 上界 0.865/0.826/0.826 >> δ=0.10；需约 1,571 独立细胞系/药或认证 r_err≥0.987/0.985；配对/功能/batch 新测量；若 Lead 要求 confirmatory → **stop**。
