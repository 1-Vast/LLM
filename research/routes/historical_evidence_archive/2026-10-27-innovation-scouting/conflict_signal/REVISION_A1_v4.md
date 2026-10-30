# REVISION_A1_v4 — 对 challenge_A1_v3.md 的逐条回应（Lead 方案 A）

2026-10-27。对象：R198-A1v3 复审 [challenge_A1_v3.md](challenge_A1_v3.md)（revise，≤5 必改）+ **Lead 已决方案 A**。逐条说明修订落在 [spec_v4.md](spec_v4.md) / [protocol_draft_v4.md](protocol_draft_v4.md) 的哪些节；v1–v3 未改。本轮不运行效果/真实 relations_check；不声称新颖性。

## 0. 总览（5 必改 → v4 处置）

| 复审必改 | v4 处置 | 状态 |
|---|---|---|
| ① tissue 算术/池化空操作（229/229 单 tissue；Pancreas 36>29/28；多 tissue 0） | **Lead 方案 A：主族 = per-tissue Breast/Colon，Pancreas 明确排除**；删除"跨 tissue 平均/池化"；**τ_t 从主模型删除**（仅多 tissue 关系启用）。数字写死：matched 96 B33/C35/P28；排除后 matched=68；候选 229（B134/C37/P58）；主族 171；覆盖 ≥86/171。 | 已修（结构性） |
| ② 覆盖 115/229 与 S 预检不相容（MILP 上界 114/112；S 选择未写） | **post-precheck 分母 171 → ≥86**；**S 选择规则写死**（metadata-only 覆盖最大化 MILP/HiGHS，确定性贪心兜底；tie-break 冻结 cell 顺序）；**预注册期望通过数 = s_milp_optimum**；**P0a-metadata non-vacuity gate**；eligible<86 → **跑前 data_unavailable/stop**；R_min=20 保留。 | 已修 |
| ③ Stage 0 实现 stale / pooled 空操作 / 无 S 预检与 matched 限制 | **本轮一次性同步 Stage 0 代码与 config**（per_tissue Breast/Colon、interval/utility off、coverage_denominator=171/≥86、require_matched_conditions_subset=true、显式 reference 分配、删除 min_relations_per_tissue 与 64/16、S 侧 Cond_r 预检、tissue-span/non-vacuity）；重跑 synthetic selfcheck 15/15；冻结 script/config/SELFCHECK SHA；two-key gate 保留。 | 已完成（工程） |
| ④ MDE/n–p1 与 context 可得性脱节；CP 规则含混；退出上限规则退化 | MDE 保持 **p1≈0.930743**（power 0.7998）、p1≥0.95 保守目标 0.88164；**S=24 按 tissue 12/12 → 每条主族关系最多 12 个 S context，n=14/19 行不可用**；若预期 p1<0.9307 → `insufficient_precision`；**CP 精确规则**（0 事件 n≥29 已足/预注册 n≥40；≤1 事件 n≥47；否则报 CP 公式）；**退出上限固定 0.15/0.10**（P95 仅诊断、不设 cap）。 | 已修 |
| ⑤ M_setup τ_t 不可识别 / k_E 未定义 / δ_fit 尺度 / κ 主法 | M_setup 无 τ_t（单 tissue）；**k_E 写死**：M_i=q+2、M_setup=q+4、M_ii(J)=q+2+\|J\|；`score=−2loglik_heldout+k_E log(n_eff)`；**δ_fit=2.5**（BIC 尺度，n_eff=12 一参数≈2.485；敏感性 2.0/2.5/5.0）；**J 代价写死**（cost=\|J\| 主，tie-break Σw/σ；敏感性 \|J\|+0.1Σw/σ；J_max=min(5,ceil(0.10\|R\|))；60 s）；**κ 主法=留出校准半 B 残差 κ_B**（κ_N 污染诊断、κ_perm 敏感性；带 [0.5κ,2κ]）；σ 带一致。 | 已修 |

## 1. 六项复审判决逐项回应

### ① tissue 算术/context（FAIL → 方案 A 结构性修复）
- 确认复审事实：matched 96 上 229 条候选**全部单 tissue**（B134/C37/P58，多 tissue 0）→ 池化是空操作；Pancreas 24 reference + 12 S = 36 > 29（Original）/28（matched），不可行；S=24 分层 <12/tissue。
- v4 选择 **方案 A**：主族 **per-tissue Breast/Colon**（分别在各自 tissue 内构造/判定/报告）；**Pancreas 明确排除**（结构不可测：58 条候选、29/28 细胞），报告披露外部有效性不覆盖 Pancreas；**删除"跨 tissue 平均/池化"**；**τ_t 删除**（主族单 tissue，不可识别；仅未来多 tissue 关系启用）。
- 数字（spec_v4 §1.1）：matched 96（B33/C35/P28）；排除后 matched **68**；候选 **229**（B134/C37/P58）；主族 **171**；覆盖 ≥86/171；S 24 = B12/C12；U17 = B6/C0/P11；reference 84 = A(B17/C16/P9)+B(B16/C17/P9)。
- 不再声称"pooled context 解决 Pancreas 算术"；改为"明确排除 + 披露"。

### ② P0a 验收/覆盖（WEAK → 写死）
- **覆盖分母 = post-precheck 主族网格 171**；通过 **≥86**；`R_min=20` 保留。
- **S 选择写死**：remaining 41 池中选 24（B12/C12），metadata-only 覆盖最大化（MILP/HiGHS；不可用则确定性贪心），tie-break 冻结 cell 顺序；**预注册期望通过数 = s_milp_optimum**；若 MILP 不可用则用贪心数做门槛（不得事后切换）。
- **P0a-metadata non-vacuity gate**：网格非空、每条主族关系 span=1、A/B≥12、S≥12、Pancreas 不入主族、reference⊆matched96、三向不交、**post-precheck eligible≥86**；否则跑前 `data_unavailable`/`design_invalid`（stop，不跑 relations_check）。
- 若真实 MILP 最优覆盖 <86 → `data_unavailable`；不降分母、不加回 Pancreas、不改 S 大小、不放宽 n_ctx/α。

### ③ Stage 0 实现同步（WEAK → 本轮完成）
- `stage0/relations_check_config.json` 已改为 v4（见 spec_v4 §6）：`context_mode=per_tissue`、`main_family_tissues=[Breast,Colon]`、`excluded_tissues=[Pancreas]`、`interval_utility_check_enabled=false`、`utility_gate_required_for_run=false`、`coverage_denominator=171`、`coverage_min_abs=86`、`require_matched_conditions_subset=true`、显式 tissue counts、`min_relations_per_tissue` 删除、64/16 残留删除、`p0a_metadata` 节、MDE/n–p1/CP 规则。
- `stage0/relations_check.py` 新增：`allocate_reference_v4`（显式 84/24/17、reference⊆matched96）、`enumerate_candidate_universe`（per-tissue Breast/Colon 171 网格；候选 cells 含 unmatched 细胞以做 S 覆盖）、`select_s_cells`（metadata-only MILP/贪心覆盖最大化）、`run_p0a_metadata`（non-vacuity/覆盖/span/三向不交门）、`load_metadata_inputs`（只读元数据，无端点列）、`--p0a-metadata` CLI（two-key gate 保留）；关系管线改为接受 P0a 冻结 splits。
- `stage0/synthetic_selfcheck.py` v4 15 项测试（P0a pass/no-Pancreas-S/coverage-fail/non-vacuity-fail + pipeline pass/determinism + 失败分支 + gate + isolation）；SELFCHECK 明确 synthetic 且 synthetic 覆盖目标缩放（56→28，非真实 171→86）。**冻结 SHA 见 record_v4 §5。**

### ④ MDE/统计（PASS 项保留 + context 联动/CP 精确化）
- 保留：MDE(80%,n=12)=p1≈0.930743（power=0.7998）、p1≥0.95 保守目标 0.88164、n–p1 表（n=7/11/12/14/19 各行 α/power）、sign test+cluster 敏感性、P0b 独立生成器、P0c ρ×κ 网格≥1,000/格、n_eff 公式。
- **context 联动写死**：S=24 按 tissue 12/12 → 每条主族关系最多 12 S context；n=14/19 行对主族全部不可用；若预期 p1<0.9307 → `insufficient_precision`；不得把 n=14/19 写进主计划、不得放宽 α。
- **CP 精确规则**：0 事件 n≥29 上界 0.098 已足，预注册取 n≥40（0.072）；≤1 事件 n≥47（1/47=0.097）；否则用 CP 公式；type-I 点≤0.05 且 CP95 上界≤0.10。
- 退出上限：**固定 0.15/0.10**；P0b P95 只作诊断，不用于设 cap（消除 `max(0.15,P95)` 退化）。

### ⑤ M_setup/惩罚拟合/J/κ/退出（WEAK → 写死）
- **M_setup 正式模型（无 τ_t）**：`y=φθ+u_batch+u_cell+ε`，τ_b/τ_c/γ；共享预测似然；M_i 固定 γ=1,τ_b=0；M_setup 估计 γ/τ_b/τ_c；M_ii(J) 同结构释放 J；k_E 写死（M_i=q+2、M_setup=q+4、M_ii=q+2+\|J\|）。
- **惩罚拟合**：`score=−2loglik_heldout+k_E log(n_eff)`；n_eff=n_ctx/(1+(n_ctx−1)ρ̂)；5-fold by cells；**δ_fit=2.5**（BIC 尺度；敏感性 2.0/2.5/5.0）；score 差≤δ_fit 或 Δ_pred(U) 不同 → ambiguous。
- **J 候选族/代价**：单例∪贪心前向≤5步∪结构族，≤200；J_max=min(5,ceil(0.10|R|))；cost=|J| 主（tie-break Σw/σ 再 relation_id）；敏感性 cost=|J|+0.1Σw/σ；60 s；精确 |R|≤30 分支定界/LP，否则贪心+LP 下界报 gap。
- **κ 主法**：主=留出校准半 B 残差 κ_B；κ_N nuisance-only 诊断（与关系对比相关>0.3 判污染）；κ_perm 敏感性；带 [0.5κ,2κ]；带内分类一致否则 ambiguous。
- **退出上限固定 0.15/0.10**（operational 分母=eligible S 单元）。P0b/P0c 依赖模型与 CP 规则保留。

### ⑥ 总判决/进 Stage 0
- v4 修订完成后需同一挑战者只读复审；通过后先跑 **P0a-metadata**（真实资源上），PASS 才跑 relations_check；任一阶段失败按类别停。

## 2. 排除 Pancreas 后的数字（写死）

| 项 | 值 |
|---|---|
| matched 96 | Breast 33 / Colon 35 / Pancreas 28 |
| 排除后 matched 主族细胞 | **68**（B33+C35） |
| 候选网格 | **229**（B134/C37/P58；多 tissue 0） |
| 主族候选 | **171**（B134+C37） |
| 覆盖分母/目标 | **171 / ≥86** |
| S 选择后上界（challenge MILP） | 全 114；Breast/Colon **112**（≥86，目标在已证上界内） |
| reference 84 | A：B17/C16/P9；B：B16/C17/P9 |
| S 24 / U 17 | S：B12/C12/P0；U：B6/C0/P11 |
| Pancreas | 明确排除（29 Original/28 matched；36>29/28；58 候选结构排除）；外部有效性不覆盖 |

## 3. Stage 0 config 同步清单（已落地，文件级）

见 spec_v4 §6 与 record_v4 §4（config 键逐项、代码函数、selfcheck 15 项、SHA）。

## 4. 仍存缺口（下一轮）

1. **真实 P0a-metadata 未运行**：171 网格、S MILP 实际覆盖、non-vacuity/eligible≥86 均需在真实 metadata 上跑；本轮只实现+合成测试。若实际 MILP 覆盖 <86 → data_unavailable（stop）。
2. **P0a relations_check/P0b/P0c/P0d 未运行**（按协议下一轮；P0d 仍 blocked）。
3. **S=24 12/12 的 consequence**：所有主族关系 n_ctx 上限=12；若真实 p1 预期<0.9307 → insufficient_precision（不扩 S、不放宽 α；扩 S 需重审协议）。
4. **Pancreas 排除后的外部有效性损失**必须在报告中显式披露；不得外推到 Pancreas/其他 tissue。
5. **A4/A5 接口**：(iii) 仍 proxy（依赖 A4）；A5 成本接口待其修订通过，Stage 2 不启动。
6. 本轮无新先例检索（不联网）；M2 先例以 v2 §9 为 additive。

## 5. 重审条件

v4 修订 + Stage 0 实现同步完成后，由同一挑战者只读复审；通过后才允许跑 P0a-metadata（真实 metadata；仍受 two-key gate + Lead 批准）。任何阶段失败按 `data_unavailable`/`design_invalid`/`insufficient_precision`/`blocked_by_utility_definition` 停；**不降 n_ctx、不放宽 α、不改覆盖分母、不加回 Pancreas**。
