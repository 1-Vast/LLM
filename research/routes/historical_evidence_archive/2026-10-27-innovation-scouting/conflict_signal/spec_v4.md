# R198-A1v4 机制规格：per-tissue Breast/Colon 关系冲突信号（方案 A）

2026-10-27。本文件按 R198-A1v3 复审 [challenge_A1_v3.md](challenge_A1_v3.md)（revise，≤5 必改）与 **Lead 已决方案 A** 修订 [spec_v3.md](spec_v3.md)；v1–v3 文件保留不改。**只做设计；本轮不运行效果/真实 relations_check，不读 S/U 响应，不声称新颖性。**

## 0. Lead 已决（写死，不再开选项）

1. **主族 = per-tissue Breast/Colon**；**明确排除 Pancreas** 并披露外部有效性损失；删除"跨 tissue 平均"措辞；per-tissue 就是真实结构，不再把 per-tissue 叫"敏感性"。**τ_t（tissue 随机效应）仅在多 tissue 关系时启用；主族关系全是单 tissue → 从主模型删除 τ_t**。
2. **覆盖口径 = post-precheck 分母**：Breast/Colon 池 **171** → 通过关系 **≥86**（=ceil(0.50×171)）；`R_min=20` 保留；**S 选择规则写死**（metadata-only 覆盖最大化 + 预注册期望通过数）；**P0a-metadata 增 non-vacuity gate**；仍不足 → 跑前 `data_unavailable`/stop。
3. **Stage 0 代码一次性同步**（本轮已完成）：config 全键（per_tissue Breast/Colon、interval/utility off、coverage_denominator=171/≥86、require_matched_conditions_subset=true、显式 reference 分配、删除 min_relations_per_tissue=3 与 64/16 残留、S 侧 Cond_r 预检、tissue-span/non-vacuity 检查）；重跑 synthetic selfcheck；冻结 config/script/SELFCHECK SHA；保留 two-key gate。
4. **其余保留并修正**：CP 精确规则；n=14/19 行仅对 S 上下文 ≥14/19 的关系可用（否则 `insufficient_precision`）；退出上限固定 **0.15/0.10**（P95 仅诊断、不用于设 cap）；k_E/δ_fit/J 代价/κ 主法阈值写死；P0a 只用 **2.0σ_r**、效用移 P0d；**84/24/17 统一**；P0b 独立生成器（iid+依赖）；P0c CP 规则；P0a→P0b→P0c→P0d 清单+短路。
5. 关系宇宙仍用 **matched 96**（A0 匹配集）；主族排除 Pancreas；给出排除后 matched 细胞数/候选数/覆盖数字（§1.1）。

## 1. 关系宇宙与 context（v4 冻结）

- 关系单位：`d_c(p,q)=y(c,p)−y(c,q)`，p=(anchor a, library l1)、q=(a,l2)，同方向（anchor→library）、同 `ANCHOR_CONC`、同 `LIBRARY_CONC`、同端点；细胞级对比。
- **关系宇宙 = A0 matched 96 细胞上的候选网格**：229 条候选全为单 tissue（Breast 134 / Colon 37 / Pancreas 58；多 tissue 0，challenge_A1_v3 §2.1 复核）。**v4 主族 = 其中 Breast/Colon 的 171 条**，逐 tissue 构造与判定；Pancreas 58 条**结构排除**（不参与主族、不参与覆盖分母、不参与 Stage 1）。
- **context = 一个细胞**（per-tissue：该关系所属 tissue 的 S 细胞；每个细胞在 Cond_r 内对关系贡献一个符号）。`Cond_r = (direction=anchor→library, ANCHOR_CONC, LIBRARY_CONC, endpoint, tissue)`；不含 tissue 的情形不存在（主族全是单 tissue）。
- **主模型**：`d_c ~ μ_r + u_batch(c) + ε_c`（**无 τ_t**；u_batch 为随机/固定效应，从元数据预注册；细胞随机效应计 1 个方差参数）。区间按细胞 cluster bootstrap；tissue 仅作为**分层/外部有效性披露**（Breast/Colon 分别报告），不进入主模型随机效应。
- 若未来引入多 tissue 关系：才启用 `τ_t` 并按 §3.2 的 M_setup 全模型处理；主族当前不启用。

### 1.1 排除 Pancreas 后的数字（写死；复核 challenge_A1_v3）

| 项 | 数字 | 说明 |
|---|---|---|
| matched 96 细胞 | Breast 33 / Colon 35 / Pancreas 28 | A0 匹配集 |
| **排除 Pancreas 后 matched 细胞** | **68**（Breast33+Colon35） | 主族关系只在这些细胞所在 tissue 内构造 |
| 候选网格（matched 96） | **229**：Breast 134 / Colon 37 / Pancreas 58 | 全单 tissue，多 tissue 0 |
| **主族候选（Breast+Colon）** | **171** = 134+37 | 覆盖分母冻结 |
| **覆盖要求** | **≥86 / 171**（50%；ceil(85.5)=86） | `R_min=20` 保留 |
| S 侧预检后可达上界（challenge MILP） | 全候选 114；**Breast/Colon 112** | 112 ≥ 86 → 目标在**已证上界内**；但实际 S 选择需实测 |
| 参考 84（A42/B42） | A：Breast17/Colon16/Pancreas9；B：Breast16/Colon17/Pancreas9 | reference ⊆ matched 96；Pancreas 参考细胞仅作 nuisance/稳健性，不进主族 |
| S 24 | **Breast 12 / Colon 12 / Pancreas 0** | 每 tissue 恰好 12 个 context（n_ctx=12 恰好满足） |
| U 17 | Breast 6 / Colon 0 / Pancreas 11 | 三向不交；84+24+17=125 |
| S 池（remaining 41） | Breast18 / Colon12 / Pancreas11 | = matched 余 12（Colon2+Pancreas10）+ unmatched Original 29（B18/C10/P1） |

**外部有效性披露**：主族只覆盖 Breast/Colon；Pancreas（29 Original/28 matched 细胞）**不声称**；结果外推到 Pancreas/其他 tissue 无依据。Breast 与 Colon 分别报告（不合并成"跨 tissue 平均"）。

### 1.2 覆盖与 S 选择（写死）

- **S 选择规则（metadata-only，不读 y）**：在 remaining 41 池中选 S=24（Breast12/Colon12），目标 = 最大化满足"≥12 个 S 细胞在 Cond_r 内且两侧 library/两浓度元数据键齐全"的候选关系数；实现 = 二进制 MILP（scipy.optimize.milp/HiGHS，确定性；不可用则确定性贪心兜底）；tie-break 按冻结 cell 顺序。**S 的组成是设计的一部分，写死并 SHA 冻结**。
- **预注册期望通过数** = MILP 最优覆盖数（记 `s_milp_optimum`）；若 MILP 不可用则记录贪心覆盖数并**只用贪心数做门槛**（不得事后切换口径）。
- **P0a-metadata non-vacuity gate**：主族候选网格非空；每条主族关系 tissue span = 1；A/B 各 ≥12；每条关系 S 覆盖 ≥12；Pancreas 不在主族；**post-precheck eligible ≥86**；reference 84 ⊆ matched 96 且三向不交。任一不过 → **`data_unavailable` / `design_invalid`（跑前停）**，不跑 relations_check。
- 若真实 MILP 最优覆盖 <86 → **`data_unavailable`（stop）**；不降低分母、不把 Pancreas 加回、不改 S 大小、不放宽 n_ctx/α。

## 2. 关系资格（P0a relations_check，参考响应可读）

- 每 tissue 独立：`n_ctx≥12`（S 或 B 细胞）；A/B 半分离 + 交换（方向一致率 ≥0.90）；`|μ_r|≥0.5σ_r`；区间 **仅 `w_r≤2.0σ_r`**（效用/δ_min 在 P0d）；`R_old∈[20,200]`。
- **覆盖：通过关系 ≥86/171**（冻结）；primary 族 ≤10；每关系精确单侧符号检验 **α=0.01**；primary 族 BH q≤0.10；exploratory BH q≤0.10 仅报告；主族 = per-tissue Breast/Colon 分别报告（不合并）。
- 失败类别：`data_unavailable`（供给/S 覆盖/覆盖不足）、`design_invalid`（协议/实现/budget）。
- 输出：relations.csv（per-tissue 关系、Cond_r、μ/区间/σ/n_ctx/stability/swap、primary/exploratory、SHA）、relations_check.json、relation_splits.json（分配 SHA）；预算 ≤30 min。

## 3. 判据统计（保留 v3 PASS 项 + v4 修正）

### 3.1 X_flip / MDE（写死；保留 v3 复核通过的数字）

- n_ctx_min=12、α=0.01 不放宽；**MDE(80%, n=12)=p1≈0.930743**（k≥11，p=0.00317383，power=0.7998）；**p1≥0.95 为保守设计目标**（power 0.88164），不是 MDE。
- n–p1 表（写死）：n=12/k11（p1 0.9307→0.7998；0.95→0.88164）；n=11/k10（0.95→0.8981；0.93→0.8228）；n=14/k12（0.90→0.8416）；n=19/k15（0.85→0.8556）；n=7/k7（0.98→0.8681）。
- **context 可得性联动（v4 新增）**：S=24 按 tissue 12/12 固定 → **每条主族关系最多 12 个 S context**；n=14/19 行**对主族全部关系不可用**。因此若预期 p1<0.9307（80% 目标在 n=12 达不到）→ **`insufficient_precision`**，不得放宽 α 或把 n=14/19 写进主计划；除非未来改变 S 大小/tissue 分配并重审（本版不预留）。
- sign test 为主统计量 + cluster（细胞/药对/批）bootstrap/置换敏感性；两者不一致 → `ambiguous_conflict`；P0b/P0c 依赖模型校准 type-I/功效并报 ρ/κ。

### 3.2 四解释与 M_setup（v4：无 τ_t、k_E 写死）

- 解释集 `E={M_i, M_ii(J), M_setup}`（(iii) 只 `proxy_only`）。
- **M_setup 概率模型**：`y_i = φ_i^Tθ + u_batch(i) + u_cell(i) + ε_i`，u_batch~N(0,τ_b²)，u_cell~N(0,τ_c²)，ε~N(0,σ_i²γ²)；参数 θ（nuisance）、τ_b、τ_c、γ（区间/噪声校准）。**无 τ_t**（主族单 tissue；若未来多 tissue 关系才加 τ_t，并另立 pre-registration）。
- **共享预测似然**：所有解释共用同一观测模型（同样 τ_b/τ_c/γ 结构），只通过 (a) 是否释放关系约束、(b) 是否估计 γ/τ 区分；M_i 固定 γ=1、τ_b=0（参考值）；M_setup 估计 γ、τ_b、τ_c；M_ii(J) 与 M_i 同结构、释放 J。
- **k_E 写死**：`q` = 固定 nuisance 参数数（剂量/screen/batch 固定效应）；`M_i: k_i=q+2`（τ_c、σ）；`M_setup: k_s=q+4`（γ、τ_b、τ_c、σ）；`M_ii(J): k_ii=q+2+|J|`（每个释放关系 +1 个自由对比度）。
- **惩罚拟合准则**：`score(E) = −2·loglik_heldout(E) + k_E·log(n_eff)`；`n_eff = n_ctx/(1+(n_ctx−1)ρ̂)`；5-fold by cells；**δ_fit=2.5**（BIC 尺度：n_eff=12 时一个参数 ≈log 12≈2.485；敏感性 2.0/2.5/5.0）。score 差 ≤δ_fit 或对 U 的 Δ_pred 不同 → `ambiguous_conflict`。
- **J 候选族**：单例释放 ∪ 按 C_conf 下降的贪心前向释放（≤5 步）∪ 预注册结构族（按剂量布局/药对类）；总候选 ≤200；**J_max=min(5, ceil(0.10|R_old|))**；**代价（写死，主）**：`cost(J)=|J|`，tie-break=`Σ_{r∈J} w_r/σ_r` 再按 relation_id；**敏感性**：`cost=|J| + 0.1·Σ w_r/σ_r`。最小代价可行 J = `J_min`；60 s 无认证或多解 → `ambiguous_conflict`；精确 |R|≤30 用分支定界/LP，否则贪心+LP 下界报 gap。
- **κ 主法（写死）**：**主 = 留出校准半 B 的残差 κ_B**（不被关系违反污染）；诊断 = nuisance-only 残差 κ_N（若与关系对比相关 >0.3 → 判污染、用 κ_B/置换）；敏感性 = 置换零 κ_perm；报告 [κ_lo,κ_hi]=[0.5κ̂,2κ̂]；分类在带内一致，否则 ambiguous；χ² 用 cell×pair 双层块置换或 κ 方差膨胀（C174 警示）。

### 3.3 退出上限（v4 修正：固定，不由 P95 派生）

- 上限**固定**：`not_identifiable ≤0.15`、`ambiguous_conflict ≤0.10`（operational 分母 = eligible S 单元数，P0a-metadata 输出冻结）。
- P0b 依赖零生成报告的 exit-rate **P95 仅作诊断**（记录在报告，不用于设 cap、不改变上限）；若运行时超固定上限 → `design_invalid` 停并报逐单元原因。

## 4. P0b/P0c（保留 v3，CP 规则精确化）

- P0b 独立生成器 M0（iid）/M1（依赖 ρ∈{0.2,0.4,0.6}、κ∈{1,3,10}）；只用参考方差/相关参数 + 合成长标签，**不注入参考违反结构**；每类（(i)、(ii)、(setup)）≥30 单元；recall≥0.80、precision≥0.80、置换零 type-I≤0.10；失败 → `design_invalid`。
- P0c：ρ×κ 4×3 格、每格 ≥1,000 批；`n_eff` 写死；目标 80%±0.05；**type-I CP 精确规则**：
  - 若观测 0 事件：n≥29 时 CP95 上界=0.098≤0.10（可接受）；**预注册取 n≥40**（0/40=0.072）；
  - 若观测 ≤1 事件：**取 n≥47**（1/47=0.097；1/46=0.099）；
  - 否则用 Clopper–Pearson 公式直接报上界；**点估计 type-I≤0.05 且 CP95 上界≤0.10**。
- 任一格 80% 目标不满足或 CP 不达标 → `insufficient_precision`；不换聚合/不放宽 α。
- 依赖 P0c 的 MDE 结论必须标注 p1≈0.9307（n=12）并披露依赖调整后的 n_eff。

## 5. P0a–P0d 流程（写死；短路）

1. **P0a-metadata**（metadata-only，本轮实现已同步）：分配（84/24/17 显式；reference⊆matched96；Breast/Colon 主族；S24=12/12；U17）；候选网格 171 分母；S 覆盖最大化；non-vacuity；post-precheck eligible≥86；输出 p0a_metadata.json+SHA；≤10 min。失败 → `data_unavailable`/`design_invalid`，**stop 不跑 relations_check**。
2. **P0a relations_check**（参考响应可读）：半分离/交换/n_ctx/α/BH/覆盖 86/171/区间 2.0σ_r/R∈[20,200]；输出+SHA；≤30 min。
3. **P0b**：独立生成器（iid+依赖）注入三体检；退出率按固定上限；失败 → `design_invalid`。
4. **P0c**：MDE/功效/CP；失败 → `insufficient_precision`。
5. **P0d**：δ_min/成本/效用（blocked 则 `blocked_by_utility_definition`）；效用宽度检查 `w≤min(2σ,0.10×utility_range)`；P0d 不过 → 不进 Stage 1。
- 所有阶段输出 SHA、无时间戳、确定性；失败类别：`data_unavailable`/`design_invalid`/`insufficient_precision`/`blocked_by_utility_definition`。

## 6. Stage 0 实现同步清单（本轮已完成，冻结 SHA 见 record_v4）

`stage0/relations_check.py` 新增/修改：`allocate_reference_v4`（显式 A/B/ S/U 组成、reference⊆matched）、`enumerate_candidate_universe`（per-tissue Breast/Colon 网格、候选 cells 含 unmatched 细胞以做 S 覆盖）、`select_s_cells`（metadata-only MILP/greedy 覆盖最大化）、`run_p0a_metadata`（non-vacuity/覆盖/三向不交/span 门）、`load_metadata_inputs`（只读元数据，无端点列）、`--p0a-metadata` CLI（仍受 two-key gate）。
`stage0/relations_check_config.json`：`schema=v4`、`context_mode=per_tissue`、`main_family_tissues=[Breast,Colon]`、`excluded_tissues=[Pancreas]`、`interval_utility_check_enabled=false`、`utility_gate_required_for_run=false`、`coverage_denominator=171/coverage_min_abs=86`、`require_matched_conditions_subset=true`、显式 tissue counts（A17/16/9、B16/17/9、S12/12/0、U6/0/11）、删除 `min_relations_per_tissue` 与 64/16 残留、`p0a_metadata` 节、CP/MDE/n–p1 表。
`stage0/synthetic_selfcheck.py`：v4 版 15 项测试（P0a-metadata pass / no-Pancreas-S / coverage-fail / non-vacuity-fail + 关系管线 pass/determinism + 失败分支 + two-key gate + isolation）；SELFCHECK 标记 synthetic、真实覆盖目标未在 synthetic 中缩放混用（synthetic 用 56→28，明确披露）。

## 7. 措辞模板（写死）

- 主族 = **per-tissue Breast/Colon**，分别报告；**明确排除 Pancreas** 并披露："Pancreas（29 Original/28 matched）因 24 reference+12 S=36>29 结构性不可行，不纳入主族；外部有效性不覆盖 Pancreas 及其它 tissue。"
- 不写"跨 tissue 平均/池化"；不写"每个 tissue 成立"（仅 Breast/Colon，且分别报告）。
- 判类："operational 归因：（i)/(ii)/(setup)，per-tissue Breast/Colon"（不是生成原因）。
- `not_identifiable`/`insufficient_precision`/`proxy_only`/`completed_null` 不写成阴性/不存在；不写新颖性/机制/迁移/决策收益；P2 只写"该参考/反馈/菜单/预算/context 下的更新比较"。
- 条件级 1.43% 只是加性主效应份额（C174）；A1v2/C176/C177 作废状态不复活；A4/A5 接口保留。
