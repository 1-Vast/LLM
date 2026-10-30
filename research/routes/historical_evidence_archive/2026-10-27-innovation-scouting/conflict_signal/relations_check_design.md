# relations_check_design — 关系集资格审计（Stage 0）可执行协议

2026-10-27。配套 [spec_v2.md](spec_v2.md) §4/§5 与 [protocol_draft_v2.md](protocol_draft_v2.md) P0a/P2。**本文件只是下一轮 Stage 0 的协议设计；本轮不运行**（不读参考响应之外的任何响应；不构造/冻结关系表；不接触 S/U）。目的：把挑战指出的"关系集不可执行/无验收/泄漏/winner's curse/Cond_r 未定义"落成可判定 pass/fail 的审计。

## 0. 范围与数据使用

- 输入（只读，SHA 冻结）：
  - R193-A0 产物：`research/2026-10-27-conditional-shift/matched_conditions.csv`（9,154 行，双组可用 cell×condition 键）与 `a0.py`/`a0.json`（必要时用 a0.py 重生成全量匹配四元组，禁止手改）；`PROTOCOL_A0.md` 的匹配口径。
  - Jaaks Original/Validation fitted 表（响应列只读参考细胞；本审计不读 S/U 的任何响应）。
- **数据使用边界（写死）**：本 Stage 0 只能读**参考细胞**的响应/端点；S/U 的键集合与响应在关系表 SHA 冻结前不可见（由独立 runner 保管）；关系构造/验收不得使用 S/U 的任何信息；不得用验证集结果挑关系。
- 输出：`relations.csv`（关系表）、`relations_check.json`（验收）、`relation_splits.json`（半切分与 SHA）、`usage_stage0.json`；全部键排序、无时间戳、确定性。

## 1. 细胞分配（先于一切；元数据盲）

- 用 Jaaks Original 的 125 个细胞（按 tissue 分层：Breast/Colon/Pancreas）做**三元不交**分配（固定 seed 20261027；分层按元数据，不看响应）：
  - **参考 84 细胞**：再分构造半 A（42）与校准半 B（42），A/B 按 tissue 分层、互不重叠；
  - **反馈 S 24 细胞**（Stage 1 用；本 Stage 0 不看其响应）；
  - **未查询 U 其余细胞（≈17）**（Stage 1 用；本 Stage 0 不看其响应）。
- 若任一 tissue 层内 B 细胞数 < `n_ctx_min = 12`（见 §4.4），按 pre-registered 规则把参考层扩到 84 内可调，或把该 tissue 的关系降级为 exploratory；**不得改用 S/U 细胞**。
- 分配表 SHA 冻结；S/U 细胞集合由独立 runner 确认"未出现在关系表构造中"。

## 2. 关系单位（写死）

- **作用单位**：参考细胞 c 上的**同 anchor 受控对比**：`p=(a,l1)`, `q=(a,l2)`，同方向（anchor→library）、同 `ANCHOR_CONC`、同 `LIBRARY_CONC`、同端点；来自 R193-A0 匹配四元组宇宙中满足"同 anchor 且同两浓度设计"的 cell×condition 键（A0 的 `controlled_anchor` 类；60 条件→按 (anchor, anc_conc, lib_conc, l1,l2) 归并）。
- **细胞级统计量**：`d_c(p,q) = y(c,p) − y(c,q)`（cell×pair 聚合读数；聚合规则由 A1 Stage 0 前冻结算子；与 C130 ΔEMAX 一致优先）。
- **关系 r**：`(G, anchor a, ANCHOR_CONC, LIBRARY_CONC, l1, l2, endpoint)`，`Cond_r` = 上述元数据字段（细胞组 G∈{Breast,Colon,Pancreas} 或预注册子组、方向、两浓度、端点）。**`Cond_r` 只由元数据判定，不得用响应定义**。
- **关系陈述**：在参考细胞组内，`d_c(p,q)` 的组级中心 `μ_r` 与其误差带 `[l_r,u_r]`；符号关系 = `sign(μ_r)`（"在该组/方向/剂量布局下 l1 相对 l2 的系统方向"）。
- 池化：`μ_r` = 细胞级 d_c 的**收缩组均值**（细胞随机效应；用 A/B 两半各自估计，见 §4）；不得把单个细胞/单个四元组直接当关系。
- S 单位进入检验的条件：S 的该 cell×condition 键满足 `u∈Cond_r`（同一 tissue 组、同 anchor/两浓度/方向/端点）才计入；否则 `out_of_cond`（不计、不判失败）。

## 3. 关系候选与选择（构造半 A）

1. 从 `controlled_anchor` cell×condition 键枚举候选：`G × (anchor, ANC_CONC, LIB_CONC) × 无序 library 对 (l1,l2)`；要求每候选在 A 中有 ≥`n_min_A = 12` 个细胞可计算 `d_c`（A 层内 42 细胞/tissue 分配足够）。
2. 在 A 上计算 `μ_r^A` 与细胞级 bootstrap/半样本稳定性（≥500 次；固定 seed）：要求 `sign(μ_r^A)` 在 bootstrap 中一致率 ≥0.90；否则丢弃。
3. 在 B（与 A 细胞不交）上独立验证方向：`sign(μ_r^B) == sign(μ_r^A)` 且 B 侧细胞级符号一致率 ≥0.90；**A↔B 交换重跑**，只有两次都通过的关系进入候选（防 winner's curse）。
4. 区间 `[l_r,u_r]` **只在 B（校准半）估计**（bootstrap 95% 区间；细胞级重采样 ≥1,000）；不得用 A 的残差估区间。
5. 关系族规模与多重检验：按稳定性排序取前 `R_max=200`；预注册 **primary 关系 ≤10**（Holm/BH 族），其余 exploratory（BH q≤0.10，只报告不进判类）；选择规则（排序键、并列处理）写死在脚本。
6. 单关系验收（全部满足）：
   - 独立上下文数 ≥ `n_ctx_min=12`（B 内可计算细胞数；上下文=细胞，互不共享）；
   - A/B 方向一致率 ≥0.90（含交换复核）；
   - 区间宽度 `w_r=(u_r−l_r) ≤ min(2.0·σ_r, 0.10·决策效用范围)`（`σ_r` 由 B 细胞级 d_c 的 SD 估计；效用范围在 δ_min 冻结时给出）；
   - 区间不含 0 或按预注册边界（近零关系不得进主族：`|μ_r| ≥ 0.5σ_r`，避免"零关系"被拿来当硬约束）；
   - 每关系在 A、B 中有 ≥12 细胞且每细胞 ≥1 个完整受控对比。
7. 全局验收（P0a）：
   - `R_old` 条数 ∈ **[20, 200]**；
   - 主族（≤10）与 exploratory 分开报告；覆盖候选单元空间 ≥**50%**（按 G×anchor×设计×library 对计数）；
   - 每个 tissue 组至少 3 条关系、且主族不得全来自单一 tissue；
   - 关系表 `relations.csv` SHA 冻结在接触 S/U 之前；冻结后**不得增删/改区间**（只可加 exploratory 且不影响主判定）。

## 4. 稳定性与依赖的统计口径（写死）

- 上下文独立性：同一关系内，上下文=不同细胞（不共享 barcode/培养批次；同 barcode 只取一次）；
- 跨关系依赖：关系共用部分细胞 → 家族多重检验用 BH（对 PRDS 稳健）并报依赖敏感性（cluster bootstrap）；主族 ≤10 且 Holm 备选；
- 区间：细胞级 bootstrap（≥1,000）；同时报 cluster-robust（按 tissue×batch 两层）与 iid 对照；若两者结论不同 → 该关系降为 exploratory；
- 半交换：A/B 交换后仍须通过，否则丢弃；记录两次结果（`relation_splits.json`）。

## 5. 关系表字段（`relations.csv`；SHA 冻结）

`relation_id, cell_group, anchor_id, anchor_name, anchor_conc, library_conc, library1_id, library1_name, library2_id, library2_name, endpoint, mu_A, mu_B, sign, l_B, u_B, w_B, sigma_r, n_ctx_A, n_ctx_B, stability_A, stability_B, swap_pass, family(primary/exploratory), cond_fields`。

## 6. 可执行流水线（下一轮；本轮不运行）

```
0) 冻结细胞分配(A/B/S/U)+seed+SHA；独立 runner 保管 S/U 键与响应
1) 载入 R193-A0 匹配四元组/controlled_anchor 键（只读；SHA 校验）
2) 清洗：端点存在；方向/浓度/端点字段齐全；cell 名归一（沿用 §2 口径）
3) 枚举候选关系；A 半估计 μ_r^A、bootstrap 稳定性；A→B 方向验证；B 估区间；B→A 交换复核
4) 单关系验收 → 全局验收 → 冻结 relations.csv/relations_check.json（SHA）
5) 输出：R_old 条数、主族/exploratory 数、各 tissue 覆盖、区间宽度分布、稳定性分布、被丢弃原因计数
```
- 计算预算：≤30 min（CPU 单机）；bootstrap ≥500（选择）/≥1,000（区间）；脚本确定性（固定 seed/键排序/无时间戳）；失败即 `data_unavailable`（不换端点/不换聚合）。

## 7. Pass/Fail 判据（写死，对应 protocol_v2 P0a）

- **PASS**：R_old∈[20,200]；每关系 n_ctx≥12；A/B 方向一致率≥0.90 且交换通过；区间宽度验收；覆盖≥50%；每 tissue ≥3 条；主族 ≤10；`relations_check.json` SHA 记录。
- **FAIL** → `data_unavailable`：任一项不满足；**不得**通过降低 n_min/放宽容差/换 tissue 定义/用 S 信息"补救"；下一轮只能改资源/改问题。
- 报告必须同时给"被丢弃原因分布"（方向不稳/区间过宽/近零/覆盖不足/依赖不稳），避免只报通过者。

## 8. 与 A1 主线/其它线的接口

- 关系表是 Stage 1 的**唯一**关系来源；冻结后不得用 S 增删/调权；M1 保护对象、C_conf、X_flip、J_min 均建在其上。
- 与 R193-A1 estimand 的差异（C174/C175）：本表是**关系资格**（参考数据内的稳定方向+区间），不是 Q 估计，不是同一 96 细胞换聚合；若 P0c MDE 预检显示 n_eff 仅来自同一批细胞/不合格 → `insufficient_precision` 停。
- 与 R198-A4：若 A4 找到可测状态 z，关系表需加一列 `state_scope` 并在新状态层重做验收；在此之前 (iii) 只 proxy。
- 与 R198-A5：A5 的成本/菜单接口在 A5 修订通过后才可用于 Stage 2。
