# PROTOCOL_ON3 —— O'Neil 开发性**描述性预测**协议（DRAFT v0.1，**设计阶段，未运行**；需独立挑战 + Lead 批准后才可执行）

2026-10-27 · 角色：ON1/ON2/ON2.2 执行者（非提案者；不参与效果设计/挑战）。工作目录 `D:\MAESTRO`；只写 `research/2026-10-27-core-module-design/oneil_dev/` 新增与 `tmp/`；不改 ON1/ON2/ON2-EX 产物。
**本文件是 DRAFT：未运行任何效果/训练/更新器比较；不含任何响应值统计；执行前必须经独立挑战（建议 endpoint-auditor）+ Lead 批准，并冻结为 execution protocol。**

## 0. 依据与问题（写死）

**依据（只读）**：
- ON2 v2.2 冻结资格：`PROTOCOL_ON2.md` SHA `7B34DB79…0B2BA7`；`ERRATA_ON2_1.md` `3C6138DF…E7870B`；`report_on2_1.md` `C6CF6467…D569EE`；`record_on2_1.md` `789A0114…484694`；`on2.json`（v2.0 历史数据产物，门级数字有效）`AD7E6D13…81F7C8`。
- ON2-EX 资格执行（唯一允许的资格执行）：`exec_calibration/calib.json` `DC2D29C1…8A6A`，**`calibration_passed`**：σ̂_e=**0.1422665081**、SE_unit=**0.0251494031**、MDE80=**0.0287644381**（n_eff=6，δ_min=0.10，28.76% of δ_min）；all-available 敏感性 σ̂_e=0.1434390629/MDE=0.0290015134 也 PASS；确定性单插补敏感性已报告。
- R199 BRIEF；challenge_ON2_2_confirm（**approve_freeze**，冻结文本生效）。

**问题（仅开发性）**：在 O'Neil **complete-case 内部细胞 5 折留出**下，
> `Δ(c;a,a';b)` 的留出值是否能被**条件结构**（cell 上下文 × partner × member 对 的交互/低秩/层级）**预测**，且是否**优于强静态基线**？

**明确不是**：不是迁移/外推（不跨资源、不跨 screen）；不是决策收益/试验设计/样本选择；不是机制；不是独立确认；不是更新器比较（任何固定反馈/更新器比较须**另立** pre-registration + 独立挑战）；不声称新颖性/新算法/资源足够。

## 1. 数据与切分（继承 ON2，冻结候选）

- **主 cohort**：complete-case 行（viability1–4 全非空）= **363,090 / 368,832 = 98.44%**；**主分析仅 BatchID=1**（357,876 行）；batch2（5,214 行）**不进主分析**（仅披露/敏感性可选，不得进入训练或指标）；batch3 全失（0/5,040，披露）。
- **目标细胞**：ON2 冻结的 **30 个非 Jaaks 重叠细胞**；9 个重叠细胞排除（列表见 ON2 产物）；source/target 不相交（Jaaks 仅 lineage 审计）。
- **5 折**：**继承 ON2 冻结的细胞分折**（`on2.json → fold_design.folds`，6/6/6/6/6；fold 0–4 细胞列表见附录 A）；**held-out 与训练细胞不相交**；**不重新分折、不换种子**。
- **单元 Δ**：complete-case 成员上下文 = `(batch,cell,partner,role,member)` 的 16 行（4 partner doses × 4 member doses）完整网格；单元 Δ = 两成员完整网格均值之差（符号按归一名升序，前者减后者）；角色分层（partner_role ∈ {A,B}）；**k=1 行沿用 ON2 排除规则**；不插值/不外推剂量；**不与 Jaaks ΔEMAX 拼接/换算**。
- **缺失/不完整处理（继承 ON2）**：complete-case 后 **702 个 pair-cell 只剩 15 行**、member context 不完整 → 不进入主分析（计数披露）；**主分析不做插补**；**确定性行均值单插补仅作敏感性（不是 MI，无 m/seed/Rubin）**，不进入主指标；缺失机制未知（**不假设 MCAR/MAR**）。
- **观察值掩码（ON3 新增，冻结）**：5 折 × 6 held-out 细胞中，对每个 held-out 细胞的单元 Δ 做**确定性 20% 掩码**：
  - key 字符串 = `ON3|batch|cell|partner|partner_role|member_a|member_a'|seed_mask`，`seed_mask = "ON3-mask-20261130"`；`h = SHA256(key)` 的十六进制值；
  - 每个 fold 内按 `h` 升序，取前 `ceil(0.20 × N_fold)` 个单元为**评价掩码单元**（其余 80% 为该细胞的**非掩码上下文**）；
  - **掩码只由 key 与固定 seed 生成，与响应值无关**；**冻结后不因结果改 mask/seed/fraction**；
  - 审计要求：每 fold 掩码单元 ≥5,000（预期 5 折单元 66,556–69,738 → 掩码 13,311–13,948）；每个 held-out 细胞掩码单元 ≥500；每个 fold 掩码上下文（cell,partner,role）≥50。
- **训练/预测边界**：训练 = 该 fold 的 24 个训练细胞（batch1、complete-case）；**held-out 细胞的非掩码 80% 单元可作为 transductive context**；**掩码单元值绝不进入任何模型拟合/超参/特征/选择**；全局参数只用训练细胞；超参只在训练细胞内部 CV 选。

## 2. 目标量与指标（冻结）

- **Y** = 评价掩码单元的 Δ 值；预测为点预测；评价仅在掩码单元上。
- **主指标**：**Spearman ρ(pred, Y_obs)**（pooled over fold 的掩码单元）；报告每 fold ρ_f、5 折 mean/SD、per-cell median。
- **次指标**：**MAE** = mean|pred − Y_obs|（掩码单元，per fold mean/SD；与 B0 配对）。
- **描述性 top-k**（开发性描述，**无决策收益含义**）：对每个 fold 的掩码上下文 `(cell,partner,role)` 中掩码单元数 ≥k 的上下文，取预测 top-k 与观测 top-k 的 overlap（precision@k）；k ∈ {1,3,5}；报告 pooled 与 per-fold；同时报告 base rate 与上下文数。
- **增量定义（pre-registered）**：比较器 X 相对强静态基线 B2 "有描述性增量" 需同时满足：
  (i) mean Δρ(X−B2) ≥ **0.10**；
  (ii) ≥ **4/5** folds 的 Δρ>0；
  (iii) 按细胞聚类的 paired bootstrap 95% CI（重采样 held-out 细胞，B=5,000，seed=20261130）**排除 0**；
  (iv) 观测 Δρ > **B6 打乱零模型** Δρ 的 95th percentile。
  未满足 → `no_increment`（描述性停止，不换指标/不换基线/不追结果）。
- **无法区分**：若观测 ρ 落在 B6 零分布 95% 范围内，或任何 fold 指标不可估计（mask 覆盖不足），→ `evaluation_cannot_distinguish`（停止）。MDE80=0.0287644381≤δ_min=0.10 为设计门前置（不是效果证据）。

## 3. 比较器（全部 pre-registered；实现同一掩码/同一折；不预设胜出）

| 代号 | 名称 | 定义（只用训练细胞 + held-out 非掩码 context） |
|---|---|---|
| B0 | 全局均值 | 训练细胞全部单元 Δ 的均值（cell-blind 常数） |
| B1 | 静态可加 | `μ + r_role + p_partner + m_memberpair` 主效应（cell-blind；未见 member-pair/partner 按预注册 backoff：→ role×partner 均值 → 全局均值） |
| B2 | 静态强基线 | `partner × member-pair` 交互 mean（cell-blind lookup；backoff 同 B1）；**强静态基线** |
| B3 | 细胞上下文偏移 | B2 + held-out 细胞**非掩码**单元均值 − 训练均值（transductive context；无 cell 身份特征） |
| B4 | 条件结构（层级/低秩） | `Y ≈ μ + r_role + p_partner + m_pair + c_cell + U_cell·V_pair`；rank r∈{1,2,3,5}、λ∈{0.01,0.1,1,10}、ALS 25 iter 固定；`c_cell,U_cell` 由 held-out **非掩码** context 估计；超参只用训练细胞内部 CV 选 |
| B5 | 强预测器（容量对照） | HistGBM（`max_depth∈{2,3}`, `min_samples_leaf∈{50,200}`, `learning_rate=0.05`, `max_iter=200`），特征=member-pair target-encoding（仅训练 fold 计算）、partner、role、cell offset（非掩码 context）、context size；**不含 cell id** |
| B5-shuf | 容量对照/标签打乱 | B5 同容量，训练细胞 cell 标签打乱（negative control） |
| B6 | 打乱零模型 | B4 同结构，但 held-out 细胞的 context 单元跨细胞打乱（保持 (partner,role) 分层）；用于各指标零分布与 95th 校准 |

**禁止**：更新器对比、跨资源数据、Jaaks、DrugComb、单药工作簿数值（未单独资格，primary 不用）、cell metadata/组织来源、任何 test-set 调参、未列出的模型/特征。

## 4. 功效/MDE（用 ON2-EX 实测）

- **用实测 σ̂_e = 0.1422665081**（well-level，complete-case all batches；ON2-EX `calib.json`），**不沿用借用先验**。
- `SE_unit = σ̂_e/√32 = 0.0251494031`；`MDE80 = 2.801585·SE_unit/√n_eff = 0.0287644381`（**n_eff=6** = 每折 held-out 细胞数，保守；技术重复≠独立 n）；`δ_min = 0.10` **写死**（开发性用途；不是决策效用阈值）。
- 认证：MDE80 (0.02876) ≤ δ_min (0.10) → `calibration_passed`（ON2-EX）；若执行前复核发现 MDE80>δ_min → **`design_invalid: precision_insufficient` 停**。
- 说明：MDE80 是**均值 Δ 尺度**的精度先验；排名类指标用 B6 打乱零模型校准（不做参数检定力宣称）；MAE 的 MDE 不作精确映射，仅报告配对差与零分布。

## 5. 门控、泄漏审计、失败类别、停止（冻结）

### 5.1 数据门（任一 FAIL → `data_unavailable`，停）

- ON2 数据门已 PASS（complete-case 363,090/98.44%；DG1 340,088/2,149/30/11,623；DG2 96.91%；DG4/DG5；见 ON2 报告）——ON3 不重开；
- ON3 追加：batch1 主分析 357,876 行；30 目标细胞；5 折各 6 细胞；每 fold 掩码单元 **≥5,000**、held-out 每细胞掩码 **≥500**、每 fold 掩码上下文 **≥50**；所有评价单元 Δ 可计算（complete-case 网格完整）；702 个 15 行 pair-cell 计数披露；无 endpoint 缺失。

### 5.2 设计门（任一 FAIL → `design_invalid`，停）

- MDE80 (实测 σ̂_e) ≤ δ_min=0.10；
- 掩码确定性（hash+固定 seed；不依赖响应值）；
- 超参/模型选择只用训练细胞内部 CV；比较器/网格/backoff 全部 pre-registered；
- **泄漏审计（9 项，逐项记录；任一 FAIL → design_invalid）**：
  1. **掩码扰动测试**：将掩码单元值全部 +1e6 后，所有模型预测**不变**（代码路径不含掩码值）；
  2. held-out cell 身份不得作为特征（只能用其非掩码 context 聚合）；
  3. 主分析只用 batch1；batch2/batch3 不进入训练/指标；
  4. 无 Jaaks / ΔEMAX / 其它资源；
  5. 无剂量外推/插值（只用完整 4×4 网格）；
  6. 无 test-set 调参（超参 inner CV 仅在 24 训练细胞内）；
  7. 掩码只由 key+seed 生成（不含响应值）；
  8. 单药工作簿数值**不进 primary**（若未来单独资格通过，只能作为**预先注册的敏感性**，不得进 primary）；
  9. 折分配继承 ON2，不重分折/不换 seed。
- **零模型校准**：B6 打乱零模型 mean |ρ| ≤ 0.10，且 B4 的 B6 零分布 95th 区间覆盖 0；否则 `design_invalid`（实现/泄漏问题，不进入结果解释）。

### 5.3 失败类别与停止条件

- 失败类别（冻结）：`data_unavailable` / `design_invalid` / `evaluation_cannot_distinguish` / `no_increment`。
- 停止：任一数据/设计门 FAIL → 停并记录；增量定义不满足 → `no_increment` 停；观测落在零分布内 → `evaluation_cannot_distinguish` 停；**不得换指标/切分/端点/掩码/比较器凑结果；不得重跑换 seed 追结果**。
- 执行前必须：独立挑战通过 + Lead 批准 + 冻结为 execution protocol（本 DRAFT 不是执行依据）。

## 6. 结果报告边界（执行时也适用）

- 只报 O'Neil complete-case、batch1、30 目标细胞、内部 5 折的**开发性描述**：留出 Spearman/MAE/top-k 描述、与静态/条件/容量/零模型的对比。
- **不得**：称迁移/外推、决策收益、机制、独立确认、更新器优势、新算法、资源足够；不得把 B2 强静态基线当"结构成立"证据；不得把阴性当"结构不存在"证明（只记录本资源/本设计下未观察到描述性增量）。
- 技术重复≠独立培养；缺失机制未知；无暴露时间/assay 方法列；单药参照未用；batch3 全失、702 个 15 行 pair-cell 为限制。
- **本 DRAFT 未运行任何效果/训练/更新器；不读响应值做统计；只写本目录新增文件与 tmp/。**

## 7. 交付/确定性

- 本任务交付（DRAFT）：`PROTOCOL_ON3.md`（本文件）、`on3_design.md`（设计理由/替代方案/风险）、`record_on3_design.md`（起草审计记录）、`usage_on3_design.json`（输入 SHA/wall/attestation）。
- 输入 SHA（只读二进制哈希，不解析响应值）：工作簿 `A0E2E002…C14818`；PROTOCOL_ON2 `7B34DB79…0B2BA7`；ERRATA `3C6138DF…E7870B`；report_on2_1 `C6CF6467…D569EE`；record_on2_1 `789A0114…484694`；on2.json `AD7E6D13…81F7C8`；calib.json `DC2D29C1…8A6A`；report_calib `80A7563E…295871`；challenge_ON2_2_confirm `4C2A0A14…1D51B6C`。
- 执行阶段：确定性（JSON 键排序、无时间戳、输入/脚本 SHA、两跑逐字节一致）；单命令 ≤45 min；所有超参/模型/掩码/阈值在 execution protocol 冻结后不得改。

## 附录 A：ON2 冻结分折（继承；不得改）

- fold 0：a2058, colo320dm, kpl1, ncih23, pa1, uacc62
- fold 1：a2780, dld1, lncap, ncih460, rpmi7951, uwb1289
- fold 2：a375, efm192b, msto, ncih520, skmel30, uwb1289brca1
- fold 3：a427, es2, ncih1650, ov90, skmes1, vcap
- fold 4：caov3, ht144, ncih2122, ovcar3, skov3, zr751
- 每折单元 Δ 数：66,556–69,738（on2.json fold_stats）；预期掩码 5,000+。

## 附录 B：版本/状态

- v0.1 DRAFT，2026-10-27；**未运行**；等待独立挑战（建议 endpoint-auditor，与 ON1/ON2 同一挑战者）与 Lead 批准后冻结。
