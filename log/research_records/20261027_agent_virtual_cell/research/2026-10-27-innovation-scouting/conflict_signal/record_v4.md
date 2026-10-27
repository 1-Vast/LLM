# record_v4 — R199-A1v4 修订过程记录（per-tissue Breast/Colon；方案 A）

2026-10-27。角色：R198-A1 提案者，按 R198-A1v3 复审 [challenge_A1_v3.md](challenge_A1_v3.md)（revise，≤5 必改）与 **Lead 已决方案 A** 做 v4 修订，并**一次性同步 Stage 0 代码/config、重跑合成自检**。**本轮不运行效果/真实 relations_check；不读 S/U 响应；不改 v1–v3；不声称新颖性。**

## 1. 范围与输入

- 输入（只读）：[challenge_A1_v3.md](challenge_A1_v3.md)、A1 v1–v3、[relations_check_design.md](relations_check_design.md)、R198 record、SYNTHESIS 相关 C 边界。
- 只写：`conflict_signal/` 下新增 **v4 文件**（`spec_v4.md`、`protocol_draft_v4.md`、`REVISION_A1_v4.md`、`record_v4.md`、`usage_v4.json`）与 **`stage0/` 内 v4 同步**（`relations_check.py`、`relations_check_config.json`、`synthetic_selfcheck.py`、`SELFCHECK.json`、`README.md`）；`tmp/stage0_selfcheck_runs` 为合成测试输出。未改 v1–v3、其它目录、INDEX/SYNTHESIS/git；未联网。
- 不做：运行效果/训练/真实 P0a-metadata/真实 relations_check/constructive/MDE 预检；不读 S/U 或参考响应值；不编造 δ_min。

## 2. 关键修订（方案 A）

1. **主族改 per-tissue Breast/Colon**：确认复审事实——matched 96 候选 229 条全单 tissue（B134/C37/P58；多 tissue 0），v3"跨 tissue 池化"是空操作；Pancreas 24 reference+12 S=36>29/28 不可行。**Pancreas 明确排除**并披露外部有效性损失；删除"跨 tissue 平均"；**τ_t 从主模型删除**（仅多 tissue 关系启用）。
2. **覆盖口径**：post-precheck 主族网格 **171（B134+C37）→ 通过 ≥86**（ceil(0.5×171)）；R_min=20 保留；**S 选择写死**（remaining 41 池，S=24=B12/C12，metadata-only 覆盖最大化 MILP/HiGHS，确定性贪心兜底，tie-break 冻结 cell 顺序；预注册期望通过数=s_milp_optimum）；**P0a-metadata non-vacuity gate**；eligible<86 → 跑前 `data_unavailable`/stop。
3. **数字写死**：matched 96 B33/C35/P28；排除后 matched 68；候选 229（B134/C37/P58）；主族 171；覆盖 ≥86/171；reference 84：A(B17/C16/P9)+B(B16/C17/P9)；S 24：B12/C12/P0；U 17：B6/C0/P11；challenge MILP 上界 114（全）/112（B/C，≥86）。
4. **Stage 0 一次性同步并冻结**：config v4 全键（per_tissue Breast/Colon、excluded Pancreas、interval/utility off、coverage 171/86、require_matched_conditions_subset=true、显式 tissue counts、删 min_relations_per_tissue/64-16、p0a_metadata 节）；代码新增 `allocate_reference_v4`/`enumerate_candidate_universe`/`select_s_cells`（MILP/non-vacuity）/`run_p0a_metadata`/`load_metadata_inputs`/`--p0a-metadata` CLI（two-key gate 保留）；合成自检 v4 **15/15 pass**、逐字节可重复；冻结 script/config/SELFCHECK SHA。
5. **保留并修正**：MDE(80%,n=12)=p1≈0.930743/power 0.7998；p1≥0.95 保守目标 0.88164；n–p1 表；**S=24 12/12 → 主族关系最多 12 S context，n=14/19 行不可用；预期 p1<0.9307 → insufficient_precision**；CP 精确规则（0/29=0.098、0/40=0.072、1/47=0.097、1/46=0.099；预注册 0→n≥40、≤1→n≥47）；**退出上限固定 0.15/0.10**（P95 仅诊断）；k_E（M_i=q+2、M_setup=q+4、M_ii=q+2+|J|）；**δ_fit=2.5**（敏感性 2.0/2.5/5.0，n_eff=12 一参数 log12≈2.485）；J 代价（|J| 主，tie-break Σw/σ；敏感性 |J|+0.1Σw/σ；J_max=min(5,ceil(0.10|R|))；60 s）；κ 主法=留出校准半 B 残差；P0a 只用 2.0σ_r、utility 移 P0d；84/24/17 统一；P0b 独立生成器（iid+依赖）；P0c CP 规则；P0a–P0d 清单+短路。
6. **措辞**：主族 per-tissue Breast/Colon 分别报告；Pancreas 排除披露；不写"跨 tissue 平均/每个 tissue 成立"；不写新颖性/机制/迁移/决策收益。

## 3. 决定与理由

1. **接受方案 A 而非 Original-125 多 tissue 宇宙**：保留 A0 matched 96 谱系（C174/C175 非重聚合、matched 条件可比），只把主族收窄到结构可行的 Breast/Colon；Pancreas 不声称（诚实排除优于用不可测关系凑数）。
2. **覆盖分母改 post-precheck 171**：115/229 与 S=24 的 MILP 上界 114 不可并存；171/86 在已证上界 112 内，且 86≥R_min=20，保留"覆盖过半主族候选"的原意；S 选择写死以消除随机 S 的不确定性。
3. **n=14/19 联动写死**：S=24 按 tissue 12/12 时每条关系最多 12 context，n=14/19 的表行在主计划不可用；与其事后增大 S，不如先判 insufficient_precision（不降标准）。
4. **退出上限固定**：v3 的 max(0.15,P95) 退化；固定 cap 更可审计，P95 只作诊断。
5. **Stage 0 同步本轮一次做完并冻结 SHA**：避免"实现 stale、跑出来的 PASS/FAIL 无意义"；合成 15/15 是工程证据不是生物证据。
6. **不声称新颖性**：机制成分均有先例；v4 只提高可判定性/可执行性。

## 4. Stage 0 config 同步清单（已落地）

| 项 | v4 值/状态 |
|---|---|
| context_mode | per_tissue（主族 Breast/Colon；不宣称 pooled） |
| main_family_tissues / excluded_tissues | `["Breast","Colon"]` / `["Pancreas"]` |
| interval_utility_check_enabled / utility_gate_required_for_run | false / false |
| coverage_denominator / coverage_min_abs | 171 / 86 |
| require_matched_conditions_subset | true |
| explicit_tissue_counts | A 17/16/9；B 16/17/9；S 12/12/0；U 6/0/11 |
| min_relations_per_tissue / 64-16 残留 | 删除 / 删除 |
| p0a_metadata 节 | budget 600 s、gates、output、失败类别 |
| 代码 | `allocate_reference_v4`、`enumerate_candidate_universe`（per-tissue、候选 cells 含 unmatched 以做 S 覆盖）、`select_s_cells`（MILP/贪心）、`run_p0a_metadata`、`load_metadata_inputs`（无端点列）、`--p0a-metadata` CLI |
| two-key gate | 保留（`--confirm-run` + `run_gate.real_run_enabled=true`；当前 false） |
| synthetic selfcheck | v4 15/15 pass；P0a pass/no-Pancreas-S/coverage-fail/non-vacuity-fail + 管线 + 失败分支 + gate + isolation；SELFCHECK 标明 synthetic、覆盖目标缩放 56→28 |

## 5. 产物与 SHA256（写后冻结）

| 文件 | SHA256 |
|---|---|
| `spec_v4.md` | `633E1D687C40712BC4843F618A657F888D46487304F39E9AC599E4827FFF16AB` |
| `protocol_draft_v4.md` | `F0B2830A50D696B7C2A7115F7B3952B1BE378F96C5A6C05AB37DA08600463F57` |
| `REVISION_A1_v4.md` | `B8B727A8CAAD206C29C9D600478261FE5E5F675869DD08F6B0F8FC85BC42E866` |
| `stage0/relations_check.py` | `D7DE7B40838002E2D2CB80DE83D74B4C5F68C6164607EF3E482A8999C40D33BC` |
| `stage0/relations_check_config.json` | `3AEDDAB545B338362470DFDB79A477A251B24B862339D98CDA7DDE4FD8874771` |
| `stage0/synthetic_selfcheck.py` | `91E576CF1863EF710D660B2F57B0CBD64CC587132605C3EA6E6A95AE1039DA7F` |
| `stage0/SELFCHECK.json` | `458FB9951A0674CE99480FE79FE87F6DA73A859415381F5F7EF675DF30786B87` |
| `stage0/README.md` | `6C9A9E68188AF4D3939EF5A8D2F27BB5116087C522ADB33F6872DD1EC9A96707` |
| `record_v4.md` / `usage_v4.json` | 自引用（外部复算） |

v1–v3 未改（复核：spec_v3 `DE92C65E…`、protocol_v3 `3FC57D72…`、REVISION_A1_v3 `79789420…`、record_v3 `889E89E8…`、usage_v3 `85887F53…`；与 challenge_A1_v3 记录一致）。

## 6. 局限与剩余缺口

- **真实 P0a-metadata 未运行**：171 网格、真实 S MILP 覆盖、non-vacuity/eligible≥86 需真实 metadata 实测；若 MILP 最优 <86 → 跑前 `data_unavailable`（stop，不降标准）。
- **后续阶段未运行**：P0a relations_check/P0b/P0c/P0d；P0d δ_min/效用仍 `blocked_by_utility_definition`（不阻塞 P0a，阻止 Stage 1）。
- **S=12 context/tissue 的上限**：主族关系最多 12 S context；n=14/19 行不可用；预期 p1<0.9307 → insufficient_precision。
- **Pancreas 排除**：外部有效性损失必须披露；不得外推。
- **Stage 0 实现细节**：收缩组均值仍是 cell 级等权均值（未额外 shrink）；sign test 无 cluster 校正（cluster 敏感性/P0b/P0c 处理）；真实 loader 未在真实数据演练；MILP 求解器依赖 scipy（已确认 1.17.1；不可用时贪心兜底并在输出记录 solver 名）。
- **先例**：本轮不联网、无新增检索；M2 先例以 v2 §9 为 additive。
- 本轮无任何生物/关系/效果结论；所有数字为元数据算术/工程测试/协议参数。
