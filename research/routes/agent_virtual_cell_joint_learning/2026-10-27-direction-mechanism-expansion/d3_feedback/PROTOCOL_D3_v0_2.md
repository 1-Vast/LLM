# PROTOCOL_D3_v0_2 —— R200-D3.1 修订/可行性裁定（单 anchor MDE 修正 + rank 功效）

2026-10-27 · 角色：ON1/ON2/ON2.2/ON3 执行者（非提案者）· 任务：task-91（D3.1）。
**状态：DESIGN REVISION / STOP；不是执行协议。**
本文件按 `challenge_D3.md` 的 5 条必改修订；**不运行效果、不拟合预测、不比较 acquisition、不读原始响应值做统计**。结论：**v0.1 D3 判 `design_invalid: precision_insufficient`，当前 H_D3 不可执行；不建议进入执行协议。** 不称独立确认/迁移/决策收益/机制/新颖性。

## 0. 裁定先行

| 项 | 结果 |
|---|---|
| v0.1 单 anchor 4 reps/8 wells、24 units/fold | **不可执行** |
| 正确 mean-Δ MDE80（batch1 target30 σ=0.1384458，n_eff=6） | **0.1119678 > δ_min=0.10**（all-batches 0.1422665 → 0.1150578） |
| rank-level MDE（primary Spearman Δρ；Fisher-z conservative independent） | **2.2875（n=6）/ 0.7625（pooled 30）> 0.10** |
| 所需独立细胞系（rank MDE≤0.10，独立误差） | **≈1,573 条**（O'Neil target30 只有 30） |
| 或所需模型误差相关（n=30 / n=6） | **≥0.9828 / ≥0.9981**（未认证，不能先验假设） |
| 候选 mean-only 修正（6 reps/member） | mean MDE .0914 pass，但 **rank MDE 仍 2.2875/0.7625 fail** |
| 候选 full-grid / partner-average | mean MDE pass，**rank 仍 fail**；成本大幅上升 |
| 唯一裁定 | **`design_invalid: precision_insufficient`；D3 当前停止；不 approve_to_lead_exec** |

**为什么不是“改聚合单元就可行”**：改 full-grid/partner-average 只改善 **mean-Δ** 精度；primary 是 **rank-level Δρ**，受 **30 个 held-out 细胞系**限制，增加 wells/反馈单元不能把 rank MDE 降到 0.10，除非假设两模型误差相关 ≥0.9828（n=30）——这是未经认证的强假设。因此没有“预注册改变聚合单元/增加 wells/反馈量后仍满足原 H_D3”的可行方案；不挑最低成本方案、不换 primary。

## 1. v0.1 MDE 单位错误（可复核算术）

- D3 v0.1 单元：单 anchor 行，`Δ = mean viability(member a, 4 reps) − mean viability(member a', 4 reps)`；**8 wells/unit**（2 members ×4 tech reps）。
- Δ 方差 = `2σ²/4 = σ²/2`；`SE_unit = σ/√2 = 0.09789598`（σ=batch1 target30 **0.1384458171**）。
- `MDE80 = 2.8015852181 × SE_unit / √n_eff`，n_eff=6 → **0.11196778 > δ_min=0.10**；all-batches σ=0.1422665081 → **0.11505775**。
- v0.1 把 ON2-EX **full-grid** 的 `se_unit=σ/√32=0.0251494` 套到 8-well 单 anchor 单元，得到 0.02876；这是**单位错配**。**该 0.02876 不得再作为 prior pass。**
- ON2-EX scope 也应为 **batch1 target30**（σ=0.1384458），不是 all-batches；即便 full-grid，也不应混用 all-batches 的 .02876 作为 D3 资源门。

## 2. rank-level 功效（primary 是 Spearman Δρ）

H_D3 primary：`Δρ = ρ(U_conflict) − ρ(C2) ≥ δ_min=0.10`（held-out cell lines；per-fold + pooled）。

- **先验公式（保守）**：Fisher-z 近似，独立模型误差：
  `MDE_rank80 = 2.801585 × sqrt(2/(n_eff−3))`。
  - 每折 n_eff=6 → **2.2875**（>1，不可分辨）；
  - pooled 30 → **0.7625**；
  - 两者均 **>0.10**。
- **每折 vs pooled 口径写死**：
  - per-fold Δρ：n_eff=6；primary 可报 mean per-fold Δρ；MDE_rank=2.2875 >δ → design_invalid。
  - pooled：先每折 **within-fold z 标准化**（或只用 per-fold Δρ 均值），n_eff=30 保守 pooled；MDE_rank=.7625 >δ → design_invalid。
  - 不得用 pooled 提升外观精度而不登记折间尺度/配对；两种口径都必须报告。
- **null/bootstrap 的局限**：N1/N2 只回答“CI 是否排除 0”，**不能回答“能否分辨 0.10”**；rank MDE 是独立门。
- **若要 rank MDE≤0.10**：
  - 独立相关假设下需要 **n≈1,573 条独立细胞系**（`3+2(2.801585/.10)²`）；O'Neil target30 只有 30，不可由技术 wells/反馈量补足。
  - 或假设模型误差相关 **≥0.9828（n=30）/ ≥0.9981（n=6）**；未认证，不能先验假设。
- **结论**：H_D3 的 rank-level 可证伪性不足；v0.1 应判 `design_invalid: precision_insufficient`，不是“执行后可能 evaluation_cannot_distinguish”就能带过。

## 3. 候选聚合/加 wells 方案（全部不满足原 H_D3）

| id | 单元/wells | n_eff | mean MDE80 | mean pass? | rank MDE | rank pass? | 模拟采购 plate-eq（5 folds，含10% failure） |
|---|---|---|---|---|---|---|---|
| A | 单 anchor 4 reps（8 wells/unit） | 6 | **0.111968** | ❌ | **2.2875** | ❌ | 11.0 |
| B | 单 anchor 4 reps，pooled 30 | 30 | 0.050074 | ✅ | **0.7625** | ❌ | 11.0 |
| C | partner-dose 平均（16 wells/member；32 wells/unit） | 6 | 0.055984 | ✅ | **2.2875** | ❌ | 44.0 |
| D | full 4×4 grid（64 wells/member；128 wells/unit） | 6 | 0.027992 | ✅ | **2.2875** | ❌ | 176.0 |
| E | 单 anchor 6 reps（12 wells/unit） | 6 | 0.091421 | ✅ | **2.2875** | ❌ | 16.5 |
| F | full grid，pooled 30 | 30 | 0.012518 | ✅ | **0.7625** | ❌ | 176.0 |

- **没有候选 overall pass**；C/D/F 改变问题（非单 anchor / full-grid），仍因 rank MDE fail；E 只是 mean pass，rank fail；B 只是 mean pass，rank fail。
- **不挑最低成本方案**：按 Lead 要求列候选并说明全部不满足原 H_D3；不选 E/B 作“最低成本”包装。
- 8 wells/unit、plate-eq 均为**模拟采购预算**，不是湿实验报价；目标 held-out 数据来自已有资源，query=0；若增加 target reps 需要新的目标测量，成本另计。
- **若只改 mean 目标**（放弃 rank primary），E（6 reps/member，12 wells/unit，16.5 plate-eq）可使 mean MDE .0914≤.10；但这是**换 primary/换问题**，不是 D3.1 修订；不采用，且需新测量/新预注册。
- **full-grid/partner-average** 的 target 已有数据可聚合，但改变科学问题；仍不能救 rank；不采用。

## 4. ON3 non-blind / inherited peek 披露

- D3 与 ON3 共用 O'Neil complete-case；ON3 实现方已见 `tmp/on3_exec_quick_debug.invalid.json`（SHA `39868CE4…`），其中 primary/results：`delta_rho_mean=0.0277068`、CI `[0.01828,0.03572]`、`positive_folds=4`、`delta_rho_min_rank=0.10`、per-fold B0–B5、verdict `design_invalid`。
- 规范文本：`PEEK_DISCLOSURE_ON3.md` SHA `B4CAD955…`；ON3 有效执行 **non-blind/peeked**，不得称盲验/独立确认/预注册确认。
- **D3 是 non-blind/inherited-peek**：D3 设计写于 ON3 QUICK artifact 之后；**未用** ON3 QUICK 的 primary/results 选择 D3 方向/阈值/切分/反馈预算/对照/指标；但**不能主张 blind/独立确认**。D3 v0.2 的任何结论（若未来重开）都必须附 peek 披露。
- 若将来使用 ON3 正式 `on3_exec.json`，还需追加“正式结果是否影响 D3”登记；本任务不重开/不解释 ON3 结果。

## 5. 强基线 / primary 固定（v0.2 设计记录）

即使当前停止，v0.2 删除结果依赖的 **“U_conflict − best ordinary control”**；固定 primary = **U_conflict vs C2 full-history retrain**，其余 secondary/描述性、预指定多重性。

- **C0** global mean/no update；**C1** static additive（no feedback）；**C2** full-history retrain（primary control）；**C3** ordinary adaptation（fine-tune/bias）；**C4** hierarchical/EB；**C5** GP；**C6** projected-kernel/ridge equivalent。
- **补 BRIEF 强基线**：**C7** fully-tuned tree/GBM（depth 2/3/5、leaf 20/50/100、lr .05/.1、iter 200/500，nested CV）；**C8** matrix completion/low-rank（rank 1–5，正则网格）；**C9** direct response prediction（预注册 feature contract；不得事后选分支）；**C10** exact closure where applicable（不适用则报告）。
- 所有 arm 同数据/特征/反馈/调参 trials/seed/compute cap；不得给 U_conflict 额外信息；C2 不得额外数据。

## 6. 反馈 pack / 成本 / 计算预算（若未来重开；本任务不执行）

- **k=24 units/fold（总120），1 轮，no acquisition**；每 support cell **1 unit**（24 support cells/fold）；strata=cell line/partner/member-pair/anchor；seed=20261130；hash rank、去重、max/min 配额；无 held-out cell unit；失败/QC 用同 stratum 的 10% reserve 按 hash 替换，**不用响应替换**；所有 arm 同包。
- **8 wells/unit = 模拟采购预算**（2 members×4 reps；非真实湿实验报价）；base 24×8=192 wells=2 plates/fold；10% failure→2.2 plate-eq/fold；**11.0 total**；query=0；目标评估数据来自已有资源。
- **每 arm 计算/调参 cap**：调参 trials≤20、inner CV 5、seeds=3、wall/CPU≤2 h/arm；N1/N2 各 1,000 次×5 folds×arms 的算力预算；超限 → `design_invalid: compute_budget_exceeded`；不得换便宜分析。
- **N1** feedback label permutation 1,000（合法零）；**N2** random pack 1,000；**N3** no-feedback；N1/N2 与 selection 分布差异说明；cluster bootstrap 单位 = held-out cell 配对。

## 7. 唯一失败/停止树（写死，避免双映射）

1. **`design_invalid: precision_insufficient`**：mean MDE80>0.10 **或** rank MDE80>0.10（prior/measured）→ **停止；v0.1 即此条**。
2. **`design_invalid: leakage_or_endpoint`**：目标/未来时点进入输入、mask/fold 违规、ΔEMAX/端点混用、held-out cell 进入反馈 → 停止/重新预注册。
3. **`evaluation_cannot_distinguish`**：门通过但 rank CI 含 0 或无法分辨 δ_min=0.10 → 不写“无效/不存在”。
4. **`no_increment`**：门通过、rank 点估计 <δ_min 且 CI 排除 0/等效 → 停“需要早期反馈动态信息”主张；保留描述。
5. **`development_increment_present`**：门全过、Δρ≥δ_min 且 95% CI 下界>0 → 仅开发性描述；不升级迁移/机制/决策/独立确认。
6. **`no_generalization`**：只改善已测/反馈点，held-out 未查询不改善 → 停 feedback-generalization 主张。
7. **`data_unavailable`**：资源/资格失败（当前不是；数据存在，是精度不足）。
8. **compute_budget_exceeded**：预算超限 → design_invalid；不得换便宜分析。
> 同一条件只映射一个类别；不以“evaluation_cannot_distinguish”掩盖 rank MDE>δ 的 design_invalid。

## 8. 边界

- **不运行效果/不拟合/不比较 acquisition/不读响应值**；本文件只做设计修订与可行性算术。
- **D3 当前停止**；不建议进入执行协议；若 Lead 要改变问题（如 mean-Δ primary/full-grid），必须**新预注册**并重新挑战，不得把本修订包装成原 H_D3。
- 不称独立确认/迁移/决策收益/机制/新颖性；技术重复≠独立培养；O'Neil 仅开发性；batch3 全失/702 pair-cell/无双药参照/单 anchor 派生等限制不变。
- 不修改 v0.1 `PROTOCOL_D3.md`/d3.py/d3.json 等文件；v0.2 是修订记录/停止裁定。

## 9. 附：为什么不能靠“增加反馈量”修 rank

- 反馈包 k=24/fold 影响 **模型估计**，不改变 **held-out cell 数**；primary 的 rank 精度受 30 个独立细胞系限制。增加反馈单元不能把 rank MDE 从 2.29/0.76 降到 0.10，除非模型误差相关极高（≥.9828/.9981）或外部队列 ~1,573 条。
- 技术 wells 只减少 **测量噪声**，不能替代 **独立细胞系 n**；因此 E/C/D/F 的 mean 改善不能救 rank primary。
- 若未来用 **cell-line-level mean** 聚合（30 个 cell lines），rank MDE 仍由 30 条线限制；若用 **all target cells**（30）同样；只有增加独立细胞系或改变问题（mean-Δ/连续效应）才可能。
