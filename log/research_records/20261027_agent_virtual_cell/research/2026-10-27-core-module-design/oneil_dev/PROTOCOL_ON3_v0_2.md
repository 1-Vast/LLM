# PROTOCOL_ON3 v0.2 —— O'Neil 开发性**描述性预测**协议（DRAFT v0.2，**设计阶段，未运行**；按 challenge_ON3 5 条必改修订）

2026-10-27 · 角色：ON1/ON2/ON2.2/ON3 执行者（非提案者；未参与挑战）。工作目录 `D:\MAESTRO`；只写 `research/2026-10-27-core-module-design/oneil_dev/` 新增与 `tmp/`；**不改** ON1/ON2/ON2-EX 产物与 ON3 v0.1 原文件。
**本文件是 DRAFT v0.2：未运行任何效果/训练/更新器；不含响应值统计；执行前须经同一挑战者（endpoint-auditor）复核 + Lead 批准，冻结为 execution protocol。v0.1 已被本版取代（保留为历史）。**

## 0. 依据与问题（写死）

**依据**：ON2 v2.2 冻结资格（`PROTOCOL_ON2.md` `7B34DB79…`、`ERRATA_ON2_1.md` `3C6138DF…`、`report_on2_1.md` `C6CF6467…`、`record_on2_1.md` `789A0114…`、`on2.json` `AD7E6D13…`）；ON2-EX 认证 `exec_calibration/calib.json` `DC2D29C1…`：**σ̂_e=0.1422665081、SE_unit=0.0251494031、MDE80=0.0287644381、n_eff=6、δ_min=0.10、`calibration_passed`**；`challenge_ON2_2_confirm.md`（approve_freeze）；`challenge_ON3.md`（ON3-C1：**revise，5 条必改**）；R199 BRIEF。

**问题（仅开发性）**：在 O'Neil **complete-case、batch1、30 目标细胞、5 折细胞留出**下，**被掩码成员单位的 `Δ(c;a,a';b)` 能否被条件结构预测，且是否优于强静态基线 B2？**
- **唯一 primary comparator：B4（条件结构）vs B2（静态强基线）**。B3/B5 只作 secondary，B0/B1 只作层级参照；**不允许"选最佳 X"**。
- 不是迁移/外推、决策收益、机制、独立确认、更新器比较（更新器须另立协议+挑战）、新算法/新颖性/资源足够。

## 1. 数据与切分（继承 ON2；冻结）

- **主 cohort**：complete-case（viability1–4 全非空）**363,090/368,832=98.44%**；**主分析 BatchID=1（357,876 行）**；batch2 **只作披露**（5,214 行 / 1,129 单元 / 136 上下文；**不进训练、不进指标、不进增量判定、不做敏感性**；见 §6.3）；batch3 全失（0/5,040，披露）。
- **目标细胞**：30 个非 Jaaks 重叠细胞（9 个排除）；5 折继承 ON2（6/6/6/6/6；附录 B），**不重分折/不换 seed**；held-out 与训练细胞不相交。
- **单元 Δ**：complete-case 成员上下文 = `(batch,cell,partner,role,member)` 16 行完整网格；单元 Δ = 两成员网格均值之差（符号按归一名升序）；角色分层；k=1 行沿用 ON2 排除；不插值/不外推剂量；**不与 Jaaks ΔEMAX 拼接**。
- **不完整处理**：ON2 的 702 个 15 行 pair-cell → member context 不完整 → 排除并计数；主分析不插补；确定性行均值单插补仅敏感性（不是 MI，无 m/seed/Rubin）；缺失机制未知（不假设 MCAR/MAR）。

## 2. 评价掩码（v0.2 修复核心：整成员块掩码）

### 2.1 为什么不能"整上下文掩码"（v0.1 泄漏的完整修复）

v0.1 的单元级 20% 掩码可被同上下文非掩码单元**精确重建**：对上下文内三成员 `a,a',c`，
`Δ(a,a') = Δ(a,c) + Δ(c,a')`（同伴侣 telescoping）。**即使改成"整上下文掩码"，仍有跨上下文精确恒等式**：
设 `g(x,y)` 为药对 `{x,y}` 的网格均值（角色定向对称），则对任意 `b'`：
`Δ(a,a';b) = Δ(b,b';a) + Δ(a,a';b') − Δ(b,b';a')`
（分别来自上下文 `(partner=a,role A)`、`(partner=b',role B)`、`(partner=a',role A)`）。整上下文掩码后其他上下文大多未掩码，因此该恒等式仍可精确重建被掩码上下文。**结论：必须用整成员块掩码（本协议选择，challenge 选项 B）或纯冷细胞（选项 C，仅确认性敏感性）。**

### 2.2 整成员块掩码（冻结）

- **掩码成员选择**：38 个药中按 `SHA256("ON3v0.2|M|20261130|"+归一名)` 升序取前 **8 个（=ceil(20%×38)）**；tie 按归一名。**冻结列表**：`dinaciclib, erlotinib, methotrexate, mitomycine, sn38, sorafenib, topotecan, vinorelbine`（`tmp/on3_v02_mask_design.json` 可复算）。
- **掩码规则**：held-out 细胞中，单元 `Δ(c;a,a';b)` 被掩码 **iff `b∈M` 或 `a∈M` 或 `a'∈M`**（伙伴或任一成员属于 M）。被掩码 cell 内这些单元**不提供任何同上下文/跨上下文可重建信息**；评价只在掩码单元上。
- **transductive context**：held-out 细胞的**非掩码单元**（全部涉及药物 ∉ M）可作 cell context；但 **M 相关单元绝不进入任何模型路径/特征/超参**。
- **披露**：20% 是**掩码药物比例**，不是单元比例；实际掩码单元比例约 **46.4%**（下方覆盖表）。这是设计选择，不是"随机 20% 单元掩码"。
- **冻结后不得改**：M 列表/seed/掩码规则/比例/作用范围。

### 2.3 覆盖计数（设计性预计算；metadata/空值掩码 only，未读响应值）

来源：`tmp/_on3_v02_mask_design.py`（SHA `39557B04…`）→ `tmp/on3_v02_mask_design.json`（SHA `F49B6F92…`）；batch1、target 30 细胞：

| 项 | 值 |
|---|---|
| batch1 全部单元 | 441,867 |
| target30 单元 | 340,088 |
| target30 掩码单元 | **157,768（46.39%）** |
| target30 非掩码（context）单元 | 182,320 |
| 每 fold 掩码单元 | **30,824–32,400** |
| 每 fold 掩码上下文 | **368–372** |
| 每 fold 非掩码单元 | 35,680–37,338 |
| 每 held-out 细胞掩码单元（min/median） | **4,237 / 5,400** |
| 每 held-out 细胞非掩码 context 单元（min/median） | **4,749 / 6,223** |
| batch2 披露（不进分析） | 1,129 单元 / 136 上下文 |

**覆盖门（冻结）**：每 fold 掩码单元 **≥5,000**；每 held-out 细胞掩码单元 **≥500**；每 fold 掩码上下文 **≥50**；每 held-out 细胞非掩码 context 单元 **≥500**。任一 FAIL → `design_invalid`（覆盖不足）。

### 2.4 泄漏审计（v0.2 新增第 10 项；设计门，执行时逐项断言）

1. **model-free 重建审计（新增，最高优先）**：以网格均值变量 `g(c,{x,y})` 为节点、非掩码单元为边（边连接同一 partner 的两个 pair 节点），建并查集；**被掩码单元的两个端点节点若在非掩码图中同连通 → 可精确重建**。**要求可重建数 = 0**；设计性预计算已为 **0 / 157,768**（`tmp/on3_v02_mask_design.json`）。执行时须逐 fold 复算并断言 =0。
   - 形式理由：任何含 M 药物的 `g` 节点只出现在被掩码单元中，非掩码特征中其系数恒 0，故被掩码单元不在非掩码特征张成空间内（系数论证）。
2. 掩码扰动测试：把所有掩码单元 Δ 值 +1e6 后，所有模型预测逐字节不变。
3. **context-ablation 审计**：B4 含 cell context vs B4 去除 held-out cell 特定因子（c_cell=0、U_cell=0）；报告 `Δρ_context = ρ(B4) − ρ(B4-ablated)`；≤0 时只能写"该设计下未观察到 context 描述性增益"。
4. 无 cell id/身份特征（只允许非掩码 context 聚合）。
5. 主分析仅 batch1；batch2/batch3 不进任何训练/指标。
6. 无 Jaaks/ΔEMAX/其它资源。
7. 无剂量插值/外推（只用完整 4×4 网格）。
8. 无 test-set 调参（超参只在 24 训练细胞内 CV）。
9. 掩码选择只依赖药名+SHA seed（不含响应/剂量/细胞身份）。
10. 折分配继承 ON2（不重分折/不换 seed）。

## 3. 比较器（冻结；B4 vs B2 为唯一 primary）

| 代号 | 角色 | 定义（只用训练细胞 + held-out 非掩码 context） |
|---|---|---|
| B0 | 层级参照 | 训练单元全局均值 |
| B1 | 层级参照 | `μ + role + partner + member-pair` 主效应（cell-blind；backoff：pair/partner 未见 → role×partner → 全局） |
| **B2** | **唯一 primary 基线** | **静态强基线**：`partner × member-pair` 交互均值（cell-blind lookup；backoff 同 B1；**绝不使用 held-out 非掩码单元**） |
| B3 | secondary（描述） | B2 + held-out 非掩码 context 的 cell offset（transductive） |
| **B4** | **唯一 primary 条件结构** | 层级 + 低秩：`μ + role + partner + member-pair + c_cell + U_cell·V_pair`；rank r∈{1,2,3,5}、λ∈{0.01,0.1,1,10}、ALS 细节见 §5.3；`c_cell,U_cell` **只由 held-out 非掩码 context 估计**；超参只用训练细胞 CV |
| B5 | secondary（容量对照） | HistGBM（容量网格见 §5.3）；特征=masked member-pair target-encoding（训练 fold 内交叉拟合）、partner、role、cell offset（非掩码 context）、context size；**无 cell id** |
| — | **删除** | v0.1 的 **B5-shuf 删除**（"训练 cell 标签打乱"对不含 cell id 的 B5 无效；负对照改由 B6 null 承担，B5 只作 capacity 描述） |
| B6 | 零模型 | B4 同结构，但 held-out cell 的**非掩码 context** 跨细胞打乱（保持 partner/role 分层）；用于 null 分布（§5.2） |

- **唯一增量判定**：`B4 vs B2`；B3/B5 只报告描述性数字，**不得**参与 `incremental`/`no_increment` 判定；所有比较输出完整表（不允许选最佳）。
- 禁止：更新器比较、跨资源、单药数值进 primary（若未来用须先单独资格）、cell 组织/表达等未列特征、test 调参。

## 4. 指标（冻结）

- **主指标（rank）**：Spearman ρ(pred, Y_obs)，掩码单元 pooled per fold；报告 5 折 mean/SD、总 pooled、per-cell median。主比较 **Δρ = ρ(B4) − ρ(B2)**（唯一 primary）。
- **次指标（mean 尺度）**：MAE = mean|pred − Y_obs|（掩码单元，per fold mean/SD）；报告 ΔMAE(B4−B2) 与 **MDE80=0.0287644381**（ON2-EX 实测 σ̂_e 推导，mean Δ 尺度）比较。
- **描述性 top-k（移到附录 A）**：k∈{1,3,5}；仅掩码上下文且掩码单元数 ≥k；tie 按归一名 member-pair 升序；报告 overlap/precision、base rate、上下文数；**无决策收益含义**。
- **rank 精度（不声称 MDE）**：
  - **B6 null-calibrated 最小 Δρ**：`Δρ_min_rank = max(0.10, Q_{0.95}(Δρ_null))`（单侧上 95th；**0.10 是预注册描述阈值，不是 MDE**）；
  - **配对 bootstrap**：按 held-out 细胞分层重采样（每 fold 6 细胞，B=5,000，seed=20261130），给出 Δρ 的 2.5/97.5 与单侧 95th 区间（预测固定，不重拟合）；
  - 两套都报告；**不得**把 MDE80 当 rank 精度。
- **增量判定（仅 B4 vs B2）**：同时满足 → "描述性增量"：
  (i) 观测 Δρ ≥ `Δρ_min_rank`；
  (ii) bootstrap 单侧 95% 下界 > 0；
  (iii) B6 单侧 p ≤ 0.05（观测 Δρ > null 95th）；
  (iv) ≥4/5 folds 的 Δρ>0（描述性稳健性）。
  否则 → `no_increment`（描述性停止；不换指标/基线/掩码/seed）。
- **mean/MAE 判定**：若 |ΔMAE| < MDE80=0.0287644381 → `evaluation_cannot_distinguish`（mean Δ 尺度不足）；若 rank 观测落 B6 95% 内 → `evaluation_cannot_distinguish`（rank 不可区分）。δ_min=0.10 **只对 mean 尺度**（描述阈值，不是 rank MDE）。

## 5. 代码级冻结 schema（执行前不得改）

### 5.1 掩码/B6/B5/B4/bootstrap

- **mask**：M 选择 key/排序/tie 见 §2.2；作用域 batch1 target30；掩码规则固定；**不重选 M**。
- **B6**：**置换 1,000 次**（fixed），seed **20261130**；每次置换 held-out cell 的非掩码 context 跨细胞（保持 partner/role 分层），**每次重拟合 B4**（同一 24 训练细胞、同一超参）；**单侧上 95th** 用于 p/阈值；同时报告双侧 2.5–97.5；null 校准门：B4 null Spearman 的 2.5–97.5 覆盖 0 **且** mean|ρ_null| ≤ **0.05**，否则 `design_invalid`。
- **B5**：`HistGradientBoostingRegressor`，`random_state=20261130`；`max_depth∈{2,3}`、`min_samples_leaf∈{50,200}`、`learning_rate=0.05`、`max_iter=200`；member-pair target-encoding 用 **5 折交叉拟合（fold 按训练细胞，seed=20261130）**；特征固定列表（TE pair、TE partner、role、cell offset、context size）；无 cell id；超参由训练细胞 inner CV。
- **B4**：ALS 交替；`U,V` 初始化 `np.random.default_rng(20261130).normal(0, 0.01, shape)`；`tol=1e-6`、`max_iter=25`；rank grid `{1,2,3,5}`、λ grid `{0.01,0.1,1,10}`；`c_cell/U_cell` 只由 held-out 非掩码单元估计；超参由 24 训练细胞 leave-one-cell-out CV 选；**不 refit on held-out masked 或 test**。
- **bootstrap**：按 held-out 细胞分层配对重采样（5 folds×6 cells；B=5,000；seed=20261130；percentile 2.5/97.5 与单侧 95th；预测固定不重拟合）。
- **确定性**：两跑 `on3_exec.json` **逐字节一致**；JSON 键排序、无时间戳、`allow_nan=False`；输入/脚本 SHA 写入；单命令 **≤45 min**。

### 5.2 输出 schema（JSON 键，冻结）

`task, protocol, inputs, mask{M,seed,rule,counts}, coverage{fold,cell}, results{folds×comparators×metrics}, primary{delta_rho,delta_mae,ci,min_rank,null_p}, null{B6_distribution_summary}, context_ablation, bootstrap, gates{data,design,leakage}, verdict, failure_categories, attestation, determinism`。禁止额外模型/指标键。

### 5.3 单元测试（执行前冻结；全部须过）

1. mask 确定性（同 M 列表/SHA）；2. 掩码规则（无 unmasked 单元涉及 M 药物）；3. **symbolic reconstruction audit =0**；4. 掩码扰动测试（+1e6 预测不变）；5. context-ablation 跑通；6. output schema 校验；7. 两跑逐字节一致；8. fold 分配=ON2 冻结；9. 无 Jaaks/ΔEMAX 数据路径；10. 无 test 调参（超参来源检查）。

## 6. 门控/失败/停止/流程

### 6.1 数据门（FAIL → `data_unavailable`）

ON2 数据门已 PASS（不重开）；ON3v0.2 追加：batch1 357,876 行；30 目标细胞；5 折 6/6/6/6/6；**覆盖门**见 §2.3（fold 掩码 ≥5,000；cell 掩码 ≥500；fold 掩码上下文 ≥50；cell 非掩码 context ≥500）；702 个 15 行 pair-cell 计数披露；无 endpoint 缺失。

### 6.2 设计门（FAIL → `design_invalid`）

MDE80（实测 σ̂_e）≤ δ_min=0.10；掩码/seed 确定；超参仅训练 CV；**泄漏审计 10 项全 PASS（含 reconstruction=0）**；B6 null 校准门通过；两跑一致；单测 10/10。

### 6.3 batch2 / 披露（冻结）

batch2 **只作描述性披露**（5,214 行 / 1,129 单元 / 136 上下文；不进训练/指标/增量/敏感性）；batch3 全失（0/5,040）披露；702 个 15 行 pair-cell 排除计数；以上只写"数据边界"，不作任何 effect 解释。

### 6.4 失败类别/停止

`data_unavailable` / `design_invalid` / `evaluation_cannot_distinguish` / `no_increment`（冻结）。停止：任一 gate FAIL 停并记录；增量不满足 → `no_increment`；rank/MAE 不可区分 → `evaluation_cannot_distinguish`；**不换指标/切分/端点/掩码/比较器/seed/超参；不因结果重跑**。

### 6.5 流程

DRAFT v0.2 → **同一挑战者（endpoint-auditor）复核** → Lead 批准 → 冻结 execution protocol → 执行一次；执行仍只写 O'Neil 内部开发性描述，**不得**称迁移/决策收益/机制/独立确认/更新器优势/资源足够/新颖性。**冻结后不得改 mask/seed/fraction/超参/rank/λ/指标/差值规则。**

## 7. 报告模板与阴性措辞（冻结）

- 报告必须含：数据边界（complete-case/batch1/30 cells/5 folds/702/batch2 披露）；覆盖表（mask 数/context 数/每 cell）；B4 vs B2 主结果（Δρ、bootstrap CI、null p、Δρ_min_rank、MAE/ΔMAE/MDE80）；B3/B5/B0/B1 完整描述表（不参与增量）；context-ablation；10 项泄漏审计与单测；确定性/SHA；失败类别（如有）。
- **阴性模板**："在本资源（O'Neil complete-case、batch1、30 目标细胞）与本设计（整成员块掩码、5 折细胞留出）下，未观察到 B4 相对 B2 的预注册描述性增量；这不等于结构不存在、不可迁移或没有决策价值。"
- **阳性模板**："在本资源/本设计下观察到 B4 相对 B2 的预注册描述性增量（Δρ=…，CI…，null p=…）；仅描述性，不构成迁移/决策收益/机制/独立确认证据。"

## 8. 附录 A：top-k（描述性，无决策含义）

- k∈{1,3,5}；仅掩码上下文且掩码单元数 ≥k；预测 top-k 与观测 top-k 的 overlap/precision；tie 按归一名 member-pair 升序；报告 base rate/上下文数；**仅附录**，不进 primary/increment。

## 9. 附录 B：ON2 冻结分折（继承）

- fold 0：a2058, colo320dm, kpl1, ncih23, pa1, uacc62
- fold 1：a2780, dld1, lncap, ncih460, rpmi7951, uwb1289
- fold 2：a375, efm192b, msto, ncih520, skmel30, uwb1289brca1
- fold 3：a427, es2, ncih1650, ov90, skmes1, vcap
- fold 4：caov3, ht144, ncih2122, ovcar3, skov3, zr751

## 10. 附录 C：B6/B5/B4 的伪代码级定义

```
M = first 8 of sorted(drugs, key=SHA256("ON3v0.2|M|20261130|"+norm(drug)))
masked(cell,partner,role,a,a') = (partner in M) or (a in M) or (a' in M)   # held-out cells only
unmasked_context(cell) = all units of cell with not masked(...)            # never uses M
B2: mean_Y over training cells grouped by (partner, member-pair) with backoff (role×partner -> global)
B4: fit μ + role + partner + pair effects on training cells; per held-out cell:
    c_cell = mean(unmasked_context) - training_mean
    U_cell: ALS projection of unmasked_context onto V (rank grid, λ grid), 25 iters, tol 1e-6
    predict masked units: μ+... + c_cell + U_cell·V_pair (pair factor from training)
B6: for p in 1..1000: permute held-out context units across cells (stratified partner/role);
    refit B4 (same hyperparams); collect ρ_p, Δρ_p; one-sided 95th.
B5: HistGBM(random_state=20261130, grid) with 5-fold cross-fitted target encodings on training cells only.
bootstrap: resample held-out cells within fold (B=5000, seed=20261130), fixed predictions.
```

## 11. 交付与 SHA

- 本任务交付（DRAFT v0.2）：`PROTOCOL_ON3_v0_2.md`（本文件）、`on3_design_v0_2.md`、`record_on3_design_v0_2.md`、`usage_on3_design_v0_2.json`；保留 v0.1 四个文件为历史。
- 设计性预计算（metadata/空值掩码 only；未读响应值）：`tmp/_on3_v02_mask_design.py` SHA `39557B04…A92638`、`tmp/on3_v02_mask_design.json` SHA `F49B6F92…7B782026`；wall 39.24 s。
- 输入 SHA 见 `usage_on3_design_v0_2.json`（工作簿 `A0E2E002…`、ON2/ON2-EX 冻结文件、challenge_ON3 `23283 B` 等）。
- v0.1 产物保持：`PROTOCOL_ON3.md` `B78197F1…`、`on3_design.md` `34000CA1…`、`record_on3_design.md` `747AEC63…`、`usage_on3_design.json` `05A1A8AF…`。
