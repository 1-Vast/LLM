# R200-D5.3 纯描述性协议：早期状态→晚期响应（PROTOCOL_D5_v0_3，DRAFT / descriptive_only）

2026-10-27 ｜ 执行：cellstate-lit（task-98） ｜ 状态：**descriptive_only（按 challenge_D5_v0_2.md 的 reduce_to_descriptive + 5 必改修订；不运行效果）**。
上游：`challenge_D5_v0_2.md`（endpoint-auditor：**reduce_to_descriptive**，5 必改；`approve_to_lead_exec=false`；若 Lead 要求 confirmatory → stop）。
历史：v0.1（`PROTOCOL_D5.md`/`d5.py`/`d5.json`/…）与 v0.2（`PROTOCOL_D5_v0_2.md`/`d5_revision.py`/`d5_v0_2.json`/…）**冻结不改**；v0.3 是唯一运行依据候选，且**仅描述性**。
本轮只做文档/资格/设计修订：**不运行效果、不拟合预测、不读表达或响应矩阵、不联网**；不称新颖性/机制/迁移/决策收益/biology/功能。

> **核心声明**：**本分析不检验时间预测是否成立；只描述可达到的精度与方向。** 所有数值（Δρ/CI/MDE/room/reliability）均为描述性/精度描述子，**不用于 confirmatory 推断**；不写"支持/证明时间预测"。

---

## 0. 相对 v0.2 的 5 必改（challenge_D5_v0_2 §2）

| # | 必改 | v0.3 落实 |
|---|---|---|
| 1 | **H-D5-2 paired-set typo（第三组 16→15）** | v0.3 全文用 **15/16/15**；v0.2 的 typo 在 `PROTOCOL_D5_v0_2.md:96` 已登记为冻结历史；v0.3 无该 typo（第三组统一为 15） |
| 2 | **E6 零模型冻结为 1,000** | N1/N2/N3/N4/N6 均 **1,000 次**（不降级）；写清合法零分布/聚类配对单位/seed |
| 3 | **E7 具体化** | 冻结 library/版本、grid、候选数、内层折、trials、compute cap；tuning-grid SHA `d2835e79…` |
| 4 | **降级为纯描述性** | H-D5-1 改 descriptive；**移除 G3/G4 通过/失败**；`evaluation_cannot_distinguish` **不再作推断**；只报 per-drug Δρ/CI/MDE/room/reliability/per-fold + BRD3379 secondary + V2 exploratory；明确"不检验时间预测是否成立" |
| 5 | **G0b 执行前再核** | G0b 改为**执行前实测/记录 compound identity、dose、vehicle**；失败 → `active_dose_identity_unverified` STOP；BRD3379 永不回 primary |

---

## 1. 范围（纯描述性开发层）

- **保留**：3 active drugs（Bortezomib n=22 / Idasanutlin n=24 / Trametinib n=24）；V1 6h→24h **分子（RNA）代理**；V2 Trametinib 5 时点 **exploratory**（paired 15/16/15，n<20）；BRD3379 **zero-dose/vehicle-like control（secondary/descriptive only）**。
- **不做**：confirmatory H-D5-1 检验；G3/G4 通过/失败；把 `evaluation_cannot_distinguish` 当推断；biology/功能/迁移/决策/机制/新颖性/真实轨迹；L2 决策层；重开 R196v2/R197v2。
- **功能路由**：`not_qualified`（本地无匹配晚期功能；RNA 代理≠功能）。
- **时间轴**：`time_axis_unverified`（无 batch/plate/run/exposure/独立培养；破坏性快照）。
- **若 Lead 要 confirmatory**：**stop**，记录所需测量规格（每 active drug 约 1,571 条独立细胞系或认证 r_err≥0.987/0.985；配对/功能/batch 新测量）；不要用描述性运行替代。

---

## 2. 数据与设计（与 v0.2 一致，仅语义降级）

| 项 | v0.3 |
|---|---|
| 单元 | 细胞系（不是 key/细胞/时间点） |
| V1 端点 | 6h early RNA → 24h late RNA 分子代理：QC-normal pseudobulk logFC（相对时间匹配 control）；train-only top-K=200 基因 logFC 均值；向量版副端点 |
| V1 active drugs | Bortezomib 22 / Idasanutlin 24 / Trametinib 24（各自合法线；**不做跨药配对**） |
| V1 切分 | leave-cell-line-out 5 折（排序后 `index%5`）；内层 5 折按细胞系分组；标准化/PCA/基因集/λ 只训练折 |
| BRD3379 | zero-dose/vehicle-like control（0.0 µM、无 ChEMBL）；**secondary/descriptive only**；历史 95 线仅描述；**永不进 primary** |
| V2 | Trametinib 5 时点 + DMSO；目标 24h/48h；输入严格更早；**paired n=15/16/15**；n<20 → exploratory only |
| 功能 | 本地无匹配晚期功能 → not_qualified |
| 时间轴 | 无 batch/plate/run/exposure/独立培养/重复 → time_axis_unverified |

---

## 3. 纯描述性分析（无 confirmatory）

### 3.1 报告内容（只描述，不检验）

- **V1**：每 active drug 报告 `ρ(early6h)`、`ρ(static)`、`Δρ=ρ_early−ρ_static`、Δρ 的 cluster-bootstrap CI（按细胞系）、`MDE80`（cluster bootstrap 估计）、`room=ρ_oracle−ρ_static`、split-half 可靠性（Spearman–Brown）、per-fold Δρ、折清单 SHA、选中超参数。
- **摘要**：3 active drugs 的等权平均 Δρ、per-drug 范围、**精度描述**（MDE/room/reliability 与 Δρ 的关系）。
- **BRD3379**：仅 secondary/描述；强制标注 zero-dose/vehicle-like control；不进入任何 primary 摘要/均值/CI。
- **V2**：每个对比报告 E1/E2/E3 的 n、**paired n（15/16/15）**、paired Δρ、CI、per-fold、capacity control 结果；**exploratory only**，不跨药推断。
- **功能/时间轴**：只报告 not_qualified / unverified 的资格状态，不尝试推断。

### 3.2 明确禁止的推断

- 不做 H-D5-1 confirmatory 检验；不报告 confirmatory p-value/显著/支持/证明。
- 不设 G3/G4 通过/失败；`evaluation_cannot_distinguish` **不再作为推断结论**；只用 **precision descriptor** 描述（如 "MDE80 > δ_min → 描述性精度不足以支持 confirmatory inference"，不是检验判定）。
- 不写 biology/功能/迁移/决策收益/机制/新颖性/真实轨迹；不把 RNA 当功能。

### 3.3 描述性精度标签（不是推断）

| 观察 | 允许写法 |
|---|---|
| Δρ 的 CI 宽 / MDE 大 | "descriptive precision insufficient for confirmatory inference"（描述性精度不足；不是检验阴性） |
| Δρ 方向为正/负 | "direction of the observed association in this development asset"（方向描述；不推断成立） |
| room 小 | "limited headroom between static and oracle in this asset"（描述） |
| V2 n<20 | "exploratory only; no confirmatory statement" |

---

## 4. 报告字段清单（执行时冻结 schema）

**V1 per drug**：`drug, n_eligible_lines, rho_early6h, rho_static, delta_rho, delta_ci_low, delta_ci_high, mde80, room, reliability_split_half, per_fold_delta_rho, fold_manifest_sha256, selected_hyperparameters`。
**Summary**：`active_drug_equal_weight_mean_delta_rho, min/max_per_drug_delta_rho, descriptive_precision_note`。
**BRD3379**：`role, n_eligible_lines, secondary_descriptive_only`（永不 primary）。
**V2**：`target_h, E1/E2/E3, n_E1, n_E2, n_E3, paired_n, delta_rho, delta_ci, per_fold, capacity_control_result, exploratory_only`。
**禁止字段**：confirmatory p-value/推断判定、biology/function/migration/decision/mechanism/novelty 陈述。

---

## 5. 执行前置门（eligibility/identity，不是推断门）

- **EX-G0a 覆盖**：每 active drug ≥20 合法线（22/24/24 → pass）。
- **EX-G0b active-dose/identity 执行前再核**：必须**实测/记录**每 active drug 的
  ① compound identity；② 实际 dose（µM）；③ vehicle identity；④ identity 的来源/assay。
  **metadata-level 注释不够**（v0.2 的 conditional pass 只是前置资格）。
  - 失败 → **`active_dose_identity_unverified` STOP**；不执行；不得用"metadata 通过"代替。
  - **BRD3379 永不回 primary**（zero-dose/vehicle-like control only）。
- （执行前还需）功能路由 not_qualified 与 time_axis_unverified 的现状在报告中如实标注；不得把它们当"可推断"。

---

## 6. E6 零模型（冻结 1,000 次）

| 零模型 | 设计 | 次数 |
|---|---|---|
| N0 mean | 训练线均值；无置换 | 0 |
| **N1 cell-shuffle** | 同 drug/time/fold 内置换细胞系标签（细胞不配对） | **1,000** |
| **N2 drug-shuffle**（V1） | 在 3 active drugs 间置换早期特征药物标签 | **1,000** |
| **N3 time-shuffle**（V2） | 同 (line,treatment) 内允许的更早时间标签间置换 | **1,000** |
| **N4 capacity control**（V2） | 同维随机特征加 E1 / 第二时点特征置换 | **1,000** |
| N5 future-leak sentinel | 用目标时点特征替代早期特征（应接近 oracle；否则管道失效 fail closed） | 1/折/arm（哨兵，非零分布） |
| **N6 static-capacity** | 同维随机基因块 | **1,000** |

**合法零分布规则**：只在同折/同药/同时间层内置换；不混合折；保留边缘分布；真实与零模型同调参预算；记录 seed `20261027` 与次数；**不得低于 1,000**（除非预注册功效依据）。

---

## 7. E7 具体调参计划（冻结；无拟合）

- **环境**：scikit-learn 1.9.0、numpy 2.4.6、pandas 2.3.3、scipy 1.17.1；CPU；max wall 120 min；单 fit 超时 120 s；超过 → `protocol_deviation`，不报结果。
- **共同预算**：内层 CV = 按细胞系分组 5 折；每 tuned model **8 candidates × 5 inner folds = 40 fits/outer unit**；outer units = 5 折 × 3 active drugs = 15 → **600 fits/tuned model**；总上限 **4,200 fits**。
- **B1 static ridge**：`sklearn.linear_model.Ridge`，alpha grid = [0.01, 0.1, 1, 10, 100, 1e3, 1e4, 1e5]（8）。
- **B3 linear ridge early**：同 B1 网格（8）。
- **B4 tree/GBM**：`sklearn.ensemble.HistGradientBoostingRegressor`；8 个预注册组合（max_depth {2,3}；learning_rate {0.03,0.1}；max_leaf_nodes {7,15}；l2_regularization {0,1} 的具体 8 行，见 JSON `tuning_E7`）。
- **B5 GP**：`sklearn.gaussian_process.GaussianProcessRegressor`（RBF+WhiteKernel）；length_scale {0.1,1,10,100} × alpha_white {1e-3,1e-2} = 8。
- **B7 single early ridge / B8 two early ridge**：同 B1 网格（8）。
- **未调参**：B0 mean、B2 cell identity、B6 simple linear-time（V2 closed-form）。
- **同预算规则**：tuned 模型恰 8 候选 × 5 内折；未 tuned 0；报告候选数/选中超参；**不得用测试折调参**；**tuning-grid SHA `d2835e79b3a75c3eed91622954339f235be5d7368add28d01840fe45a353e751`** 执行前冻结，结果后不得改。

---

## 8. 执行清单 E1–E12（v0.3；本轮只列不执行）

| id | 内容 |
|---|---|
| E1 数据加载 | h5ad obs+表达（执行时）；QC=`cell_quality=="normal"`；pseudobulk mean per (drug,line,time)；对照=时间匹配 control（V1）或 DMSO hash（V2）；logFC=log2((pseudo+1)/(ctrl+1))；记录细胞数；不做表达选择 |
| E2 200 gene panel | 每 drug/target/fold 用训练线 mean |logFC| top-200；冻结 gene list SHA；测试线不进 |
| E3 fold loader/assert | 加载 v0.3 折清单；断言划分/无跨折线/`index%5`/seed/SHA |
| E4 V1 无跨药配对 | 每 active drug 用自己合法线（22/24/24）；不跨药配对；报告 per-drug |
| E5 V2 paired | 只用 paired sets：24h E1/E2=15；48h E1/E2=16、E2/E3=15；输入严格更早 |
| **E6 零模型** | **N1/N2/N3/N4/N6 = 1,000 次**；seed 20261027；合法零/聚类/配对规则；N5 future-leak sentinel；fail closed |
| **E7 调参** | 冻结 §7：8 candidates × 5 inner folds；40 fits/unit；15 units；600 fits/tuned model；≤4,200 fits；CPU 120 min cap；grid SHA `d2835e79…`；no test tuning |
| E8 两跑/schema | 同 seed 跑两次、输出逐字节一致；固定 schema（§4 字段）+ config/fold SHA + pseudobulk SHA |
| E9 描述性测量 | 计算 split-half reliability/room/MDE 作为**精度描述子**；无 pass/fail；不得写 `evaluation_cannot_distinguish` 推断；记录实测值 |
| E10 描述性报告模板 | §4 字段 + 精度标签；禁止 confirmatory/biology/function/migration/decision/mechanism 语言 |
| E11 G5 断言 | 目标/未来时间不在输入；V1 无两快照臂；折按细胞系；预处理仅训练折；无表达派生测试信息；future sentinel；fail closed |
| E12 本轮不运行 | 本轮无效果/预测/表达读取；执行需另立任务 + 独立挑战 |

---

## 9. 失败类别 / 停止条件（v0.3）

- 执行/资格类：`data_unavailable`、`active_dose_identity_unverified`、`design_invalid`、`time_axis_unverified`、`functional_route_not_qualified`、`identifiability_unsupported`、`protocol_deviation`。
- **描述性精度标签**：`descriptive_precision_insufficient`（**精度描述，不是检验推断**；不得写成阴性/不存在）。
- **停止**：EX-G0a/G0b 失败 → 停；泄漏审计失败 → 停并修；无功能 → 停功能主张；无 batch/exposure → 停绝对时间/轨迹主张；MDE 大 → 只写精度描述；不换端点/阈值/切分；BRD3379 不回 primary。

---

## 10. 若升级功能/绝对时间（不变）

同 v0.2：匹配晚期功能（viability+凋亡/再生长；时间匹配 vehicle；≥3 复孔 × ≥2 独立培养）；暴露/时间轴/批次；重复；若轨迹需同细胞/谱系链接。**confirmatory H-D5-1 所需独立细胞系约 1,571/药（或认证 r_err≥0.987/0.985）**——当前 22/24/24 远不足；**Lead 若要求 confirmatory → stop**。

---

## 11. 边界 / 不称

- A3v2 `L1/L2` 仅背景；不重用未认证部分；C176/C177/C179/C181/C186 仅背景；不重开 R196v2/R197v2；R195 ERRATA_A3 范围限制保留。
- **不得声称**：confirmatory、支持/证明时间预测、biology、功能/viability、迁移、决策收益、机制、新颖性、真实轨迹、动态世界模型；BRD3379 不是 active drug；RNA 不是功能。
- 功能/决策/轨迹需新测量。

---

## 12. SHA / 确定性 / 再挑战

- v0.3 新产物：`d5_revision_v0_3.py` **ff4c03ebbc1d497bb393c1cbfbdde5b9f6b96715cf24cd8192ae1648a80f3ad7**（26,947 B）；`d5_v0_3.json` **3508dadaa9af416fb05717bf19a77d901d28543f52d11881873e7443610d7a26**（28,575 B）；两次运行逐字节一致。
- v0.1/v0.2 六文件 + challenge 的 SHA 作为输入登记在 `d5_v0_3.json:inputs_sha256`；**v0.1/v0.2 未改**；v0.2 的 typo 仅在冻结历史中（v0.3 已修正为 15/16/15）。
- **`approve_to_lead_exec=false`**；建议**再提交独立挑战（reduce 路径）**：审 typo 修复、E6 1,000、E7 冻结清单、描述性 schema、G0b 再核；通过前不执行。
- 若 Lead 要 confirmatory：**stop** + 测量规格；不得用描述性执行替代。
