# R199-A1v4 复审（challenge_A1_v4.md）——A1v4 + Stage0 v4 的只读复审

2026-10-27 · 挑战者：endpoint-auditor（task-36/42/52 同一挑战者；未参与 A1 设计）· 对象：`research/2026-10-27-innovation-scouting/conflict_signal/{spec_v4.md, protocol_draft_v4.md, REVISION_A1_v4.md, record_v4.md, usage_v4.json}` + `stage0/{relations_check.py, relations_check_config.json, synthetic_selfcheck.py, SELFCHECK.json, README.md}`。
方式：**只读审查 + 纯算术/元数据复核**（`tmp/challenge_a1v4_checks{,2,3}.py`、`tmp/challenge_a1v4_meta_check.py` → `tmp/challenge_a1v4_checks*.json`）；**不运行真实数据/P0a-metadata/relations_check/体检/MDE 预检，不读任何响应值，不改 A1 产物**。
完整性：v4 交付物 SHA 与 `usage_v4.json` / `record_v4.md` 登记一致（spec `633E1D68…16AB`、protocol `F0B2830A…3F57`、REVISION `B8B727A8…E866`、stage0 `relations_check.py` `D7DE7B40…D33BC`、config `3AEDDAB5…4771`、synthetic `91E576CF…DA7F`、SELFCHECK `458FB995…6B87`、README `6C9A9E68…6707`）；v1–v3 文件 SHA 未变（v3 spec `DE92C65E…`、protocol `3FC57D72…`、REVISION `79789420…`、record `889E89E8…`、usage `85887F53…`）。

## 0. 总判决

**revise（≤5 必改）；当前不可批准运行 P0a-metadata。** 方案 A 的设计与算术基本自洽、Stage0 代码/config 大部分已同步、合成自检 15/15 与 SHA 登记也一致；**但存在 1 个功能性阻塞**：
- `check_run_gate` **忽略** config 的 `utility.utility_gate_required_for_run=false`，在 utility/δ_min 仍 `blocked_by_utility_definition` 时把**所有真实运行**（包括 `--p0a-metadata`）在进入 metadata 分支之前判为 `blocked_by_utility_definition`（exit 4）。也就是说：**Lead 即使批准并把 `real_run_enabled` 置 true，`--p0a-metadata` 也不会运行**，与 v4 的"P0d blocked 不阻塞 P0a"直接矛盾；selfcheck 的 gate 测试也没有覆盖这个真实路径。
- 另外 3 个审计/文档问题（覆盖上界 112 的误读、config 与代码的 gate 名称不一致、18 个 Pancreas reference 细胞未使用未披露）会误导审计或让 P0a 输出对不上冻结 gate 清单；都属于可快速修复项。
- 修完 5 条后可**批准 P0a-metadata**（届时由 Lead 记录批准 + two-key + 本次复审通过；P0a 只读元数据）。修之前不要跑——命令会返回 blocked 而非 metadata 结果。

**最致命 3 条**

1. **`--p0a-metadata` 被 utility 闸阻塞（功能性阻塞）**：`stage0/relations_check.py:991` 在 `main()` 中先调用 `check_run_gate(cfg, args.confirm_run)`；`check_run_gate`（`:79-92`）在 `utility_range is None or delta_min_state == "blocked_by_utility_definition"` 时返回 `STATUS_BLOCKED`，**完全无视** `utility.utility_gate_required_for_run=false`（config 已设 false）。因此 Lead 批准 + `--confirm-run` + `real_run_enabled=true` 后，`--p0a-metadata` 仍返回 exit 4、`blocked_by_utility_definition`，metadata 分支（`:996`）永远不可达；full relations_check 同样被阻塞。这与 spec_v4 §5（P0a-metadata 先跑）、usage_v4 open_gaps（"P0d blocked 不阻塞 P0a"）矛盾。selfcheck 只测试 `gate_default/confirm_only` 与 `run_relations_check` 的 blocked 分支，**没有测试"enabled + confirm + --p0a-metadata + utility blocked"应进入 metadata 分支**。
2. **覆盖上界 112 的表述是误读（audit 误导，不阻塞实际执行但必须改）**：v4 把 `challenge MILP` 的 **112** 写成"S 选择后可达到的上界；112≥86，目标在已证上界内"（spec_v4 §1.1/§2、REVISION §2、config `coverage/reference_milp_upper_bound_after_S_precheck`）。**112 是 v3 在"从 41 个 leftover 中任选 24 个（可跨 tissue）"假设下的上界，且是上界而非可达性证明**；v4 的 S 组成是固定的 **Breast12/Colon12**（Breast 从 18 个 leftover 中选 12，Colon 取全部 12 个 leftover），约束不同。我用**与代码一致的确定性字母序分配**重算：候选网格 171、A/B≥12 supply=135、S=12/12 下 **MILP 最大覆盖 = 106**（Breast 91 + Colon 25 的近似组合，精确 MILP 为 106）→ **≥86 可达、余量 20**；但 **112 既不是 v4 的上界、也不是可达性证明**，不能写成"已证上界内"。要求：用 P0a-metadata 实际输出的 `s_milp_optimum`（本次预计 106，取决于冻结分配/实现）作为门槛，删除/改写 112 字段或标注"v3 参考值，不同 S 组成，不适用于 v4"。
3. **config 的 p0a gate 清单与代码输出不一致（审计不可复核）**：config `p0a_metadata.gates` = `['reference_84_subset_matched96','three_way_disjoint','main_tissues_breast_colon','pancreas_excluded','tissue_span_non_vacuity','s_side_cond_cov_ge_12','precheck_eligible_ge_86','s_milp_expected_passing_count_recorded']`；代码实际写出的 gates 是 `reference_matched_subset`、`reference_size_ok`、`three_way_disjoint`、`main_tissues_breast_colon`、`pancreas_excluded`、`tissue_span_non_vacuity`、`s_side_cond_cov_ge_12`、`precheck_eligible_ge_target`、`s_selection_solver`——**两个名称不同、`s_milp_expected_passing_count_recorded` 没有实现**；同时 `result["counts"]["reference_milp_upper_bound"]` 仍把 config 的 v3 114/112 写进 P0a 输出。审计者无法把 P0a 输出对回冻结 gate 清单。必须在跑之前对齐。

## 1. 六项判决摘要

| # | 复审项 | 判定 | 一句话依据 |
|---|---|---|---|
| ① | 方案 A 落实（per-tissue Breast/Colon、Pancreas 排除+披露、删跨 tissue 平均、τ_t 删除、排除后数字自洽） | **PASS（含 2 minor）** | matched 68=B33+C35、主族 171=134+37、reference 84（A17/16/9、B16/17/9）、S 24=B12/C12、U 17=B6/C0/P11、剩余池 41 全部自洽（84+24+17=125；33+33+18=84；B18/C12/P11=41）；τ_t 已删；无 "pooled/跨 tissue 平均" 主族措辞；minor：18 个 Pancreas reference 细胞实际未被主族使用（见必改 4）；n=11 行在 n_ctx_min=12 下也不可用（表格注释放错了对象） |
| ② | 覆盖（171→≥86、R_min=20、S 选择 MILP/贪心/tie-break、预注册期望、non-vacuity、eligible<86→data_unavailable、112≥86 上界与可达性） | **WEAK** | 覆盖口径/门槛/MILP/贪心/non-vacuity/预检门**已实现且逻辑正确**；但 **112 的"已证上界"是误读**（v3 不同 S 组成的上界，不是 v4 可达性证明）；我用代码一致的确定性分配重算 **v4 max=106≥86**（可达，余量 20）；要求以 P0a 实际 `s_milp_optimum` 为准并改掉 112 字段 |
| ③ | MDE/统计/规则（MDE p1≈0.930743、power、n–p1 表、S=12/tissue + insufficient_precision、CP 精确规则、退出上限 0.15/0.10、k_E、δ_fit=2.5、J 代价、κ 主法留出校准半、P0a 只用 2.0σ、utility 移 P0d） | **PASS（minor）** | 全部写死且算术正确：MDE(80%,n=12)=0.930743（power 0.7998）、p1=0.95→0.88164；n–p1 表 k/α/power 与我的精确二项一致；CP：0/29=0.098、0/40=0.072、1/46=0.099、1/47=0.097；k_E=q+2/q+4/q+2+\|J\|；δ_fit=2.5（log 12≈2.485）；J cost=\|J\|、tie-break Σw/σ、J_max、60 s；κ 主=留出 B；P0a 只用 2.0σ、utility 移 P0d。minor：n=11 行在 n_ctx_min=12 下不可用（不应只标注 n=14/19）；κ_B 仍在 B 上（B 同时用于区间）需披露污染方向（非阻塞） |
| ④ | Stage0 同步（config 全键、代码函数、two-key、自检 15/15/逐字节/SHA） | **FAIL（含 1 个功能性阻塞）** | config 键、函数、selfcheck、SHA 登记基本都对（见页首）；**但 `check_run_gate` 忽略 `utility_gate_required_for_run=false`，把 `--p0a-metadata` 在 metadata 分支前判 blocked（exit4）**；selfcheck 没覆盖该路径；config gate 名与代码输出不一致（见致命 3）；其余（`load_metadata_inputs` 只读 6 个元数据列、不含 endpoint；`run_p0a_metadata` 的 A/B→S→coverage 逻辑正确；`select_s_cells` MILP 目标与 12/12 约束正确）为 PASS |
| ⑤ | 门控/措辞（Lead 批准 + two-key + 复审 + eligible≥86 前置；失败类别/短路；措辞模板；P0a 通过≠Stage 1） | **WEAK** | 前置条件/失败类别/短路/措辞模板都写了；但代码门控与"P0d blocked 不阻塞 P0a"矛盾（同致命 1）；需在修好门控后把"Lead 批准记录 + two-key + 复审通过"写进 record，并明确 P0a-metadata PASS 只产关系资格/覆盖，不是 Stage 1 或效果证据 |
| ⑥ | 总判决 / 是否可批准 P0a-metadata | **revise（≤5 必改）；当前不可批准** | 设计实质可批准；但代码门控 bug 使 P0a-metadata 无法运行；112 误读与 gate 清单不一致会污染审计；修完 5 条后可批准 |

## 2. 逐项取证

### 2.1 ① 方案 A 落实（PASS；2 minor）

**自洽性复核（全部通过）**：
- matched 96 = B33/C35/P28；排除后 matched **68**（B33+C35）✓；候选 229（B134/C37/P58）✓；主族 **171** ✓。
- reference 84 = A(B17/C16/P9)+B(B16/C17/P9)：A 42 + B 42 = 84 ✓；Breast 33=matched33 ✓；Colon 33≤35 ✓；Pancreas 18≤28 ✓；reference ⊆ matched96 ✓。
- S 24 = B12/C12/P0；U 17 = B6/C0/P11；84+24+17=125 ✓；三元不交 ✓；tissue 合计：B 33+12+6=51 ✓、C 33+12+0=45 ✓、P 18+0+11=29 ✓（= Original 125 细胞 tissue 计数）。
- 剩余池 41 = matched 余 12（C2+P10）+ unmatched 29（B18/C10/P1）→ B18/C12/P11 ✓。
- 覆盖 86 = ceil(0.5×171)=86 ✓；R_min=20 保留 ✓。
- **τ_t**：主模型 `d_c ~ μ_r + u_batch + ε`（无 τ_t）✓；spec 明确"仅多 tissue 关系时启用"✓。
- **措辞**：主族 per-tissue Breast/Colon，Pancreas 明确排除并披露外部有效性 ✓；不再写"跨 tissue 平均/池化"✓。

**Minor（需在文档里补/改，非阻塞）**：
1. reference 84 中有 **A9+B9=18 个 Pancreas 参考细胞**，但主模型是 per-tissue、且主族无 Pancreas 关系——这 18 个细胞在 Breast/Colon 关系构造/区间/检验中**完全不会被使用**。spec 把它们写成 "Pancreas 参考细胞仅作 nuisance/稳健性" 不成立（per-tissue 模型没有 tissue nuisance；也没有跨 tissue 稳健性计算）。要么如实写"为保持 84/24/17 组成而保留、实际未使用"，要么（Lead 决定）把这 18 个细胞改配给 S/U 以增大 S context（可缓解 n=14/19 不可用）——本版不预留，按 v4 冻结则必须披露。
2. **n=11/k=10 行**（spec_v4 §3.1 表）在 `n_ctx_min=12` 下同样**不可用**（关系至少 12 个 context；不能把 12 个 context 降成 n=11 检验）。v4 只写"n=14/19 行不可用"，应同时注明 n=11 行只是参考、不进入主计划；否则可能被误用为"p1=0.95 时用 n=11 达到 0.898 power"的捷径（实际要用 n=12/k≥11，power 0.882，已够）。

### 2.2 ② 覆盖（WEAK：112 误读；v4 实际 max=106）

**PASS 的实现**：`run_p0a_metadata` 的 order 正确——`allocate_reference_v4`（reference⊆matched、显式 A/B）→ `enumerate_candidate_universe`（per-tissue Breast/Colon，候选 cells 含 unmatched 以便 S 覆盖；本版主族 171）→ A/B≥12 supply → `select_s_cells`（MILP 主/贪心兜底；per-tissue 12/12；目标=最大化"≥12 S 细胞在 Cond_r"的候选数）→ S 侧预检 → gates（non-vacuity、pancreas_excluded、`precheck_eligible_ge_target`=86、三向不交、reference_matched_subset、reference_size_ok）→ PASS/`data_unavailable`。逻辑与 v4 文字一致，`load_metadata_inputs` 只读 6 个元数据列（不含 endpoint/响应）✓。

**关键复核（我的独立计算，metadata-only）**：
- 我按代码的**确定性字母序分配**（`allocate_reference_v4` 用 sorted pool，A=前 na、B=下一段；无 RNG）复现：A 42/B 42、leftover 41、reference B33/C33/P18；主族网格 B134/C37=171；A/B≥12 的 supply=**135**。
- S 组成固定 B12（从 leftover B18 中选 12）/C12（leftover C12 全取）；候选通过条件=其 12 个 S 细胞全部满足 Cond_r（因每 tissue 恰好 12 个 S context）。
- **最大覆盖 = 106**（Brute force/MILP 等价；≥86，余量 20）。代码 `select_s_cells` 的 MILP 目标/约束与此一致，预计输出 `s_milp_optimum=106` 左右（精确值由 HiGHS 与 tie-break 决定；只要 ≥86 即 PASS）。
- **因此 v4 的 86 目标可达，但 112 不是 v4 的上界/可达性证明**：112 来自 v3 `challenge_A1_v3` 的 MILP（当时 S=24 从 41 leftover 中任取，含跨 tissue 选择），与 v4 的 B12/C12 固定组成不同；而且"上界 ≥ 目标"本身不证明目标可达（需要构造/实测）。要求：把 spec_v4 §1.1/§2、REVISION §2 的 "112≥86 → 目标在已证上界内" 改为："v3 参考值 112（不同 S 组成，不适用）；v4 以 P0a-metadata 实际 `s_milp_optimum` 为准（本次独立复算约 106）"；config `coverage/reference_milp_upper_bound_after_S_precheck` 应删除或标注 provenance，不要写进 P0a 输出当作"已证"。
- **注意**：P0a-metadata 的 PASS 只说明"关系资格阶段的前置（网格/分配/S 覆盖）达标"，不说明 relations_check 通过（A/B 方向稳定性、区间宽度、覆盖 ≥86 还要在 relations_check 用参考响应做）。措辞要写"P0a-metadata PASS ≠ Stage 1/效果"。

### 2.3 ③ MDE/统计/规则（PASS；minor）

**复算全部正确**：
- n=12 k≥11 精确 p=0.00317383；k=12=0.00024414；80% power 的 p1=**0.930743**（精确；power 0.7998）；p1=0.95→0.88164。
- n–p1 表：n=12/k11（α=0.003174）；n=11/k10（0.005859；p1=0.95 power 0.8981；0.93 0.8228）；n=14/k12（0.006470；0.90 power 0.8416）；n=19/k15（0.009605；0.85 0.8556）；n=7/k7（0.0078125；0.98 0.8681）——**全部与我的精确二项一致**。
- CP：0/29=0.0981、0/40=0.0722、1/46=0.0990、1/47=0.0970 → 预注册 0 事件 n≥40、≤1 事件 n≥47 ✓；规则写死 ✓。
- 退出上限固定 0.15/0.10（P95 仅诊断）✓；k_E=q+2/q+4/q+2+|J| ✓；δ_fit=2.5（BIC 尺度 log n_eff≈2.485）✓；J cost=|J|、tie-break Σw/σ、J_max、60 s ✓；κ 主法=留出校准半 B ✓（minor：B 同时用于区间估计，κ_B 可能被关系违反抬高；需在 v4 报告里写污染方向/κ 带敏感性，非阻塞）；P0a 只用 2.0σ_r ✓；utility 移 P0d ✓。
- **minor**：n=11 行在 `n_ctx_min=12` 下不可用（见 2.1 minor 2）；"S=12/tissue → 每条关系最多 12 context" ✓，故 p1<0.9307 时 `insufficient_precision` ✓；但 v4 表格应把 n=11 也标注为"参考/不进入主计划"。

### 2.4 ④ Stage0 同步（FAIL：gate 阻塞 + 审计不一致）

**PASS 的部分（核对过实际文件）**：
- config v4 键基本齐全：`schema=v4`、`context_mode=per_tissue`、`main_family_tissues=[Breast,Colon]`、`excluded_tissues=[Pancreas]`、`interval_utility_check_enabled=false`、`utility_gate_required_for_run=false`、`coverage.denominator=171`、`coverage_min_abs=86`、`require_matched_conditions_subset=true`、显式 tissue counts（A17/16/9、B16/17/9、S12/12/0、U6/0/11）、`min_relations_per_tissue=None`、`p0a_metadata` 节（budget 600s/gates/output/failure）、MDE/n–p1/CP、`run_gate.real_run_enabled=false` ✓。
- 代码：`allocate_reference_v4`（reference⊆matched、显式 A/B）、`enumerate_candidate_universe`（per-tissue、候选 cells 含 unmatched）、`select_s_cells`（MILP/贪心、12/12 约束）、`run_p0a_metadata`（A/B→S→gates）、`load_metadata_inputs`（只读 6 元数据列，**不含 endpoint**）、`--p0a-metadata` CLI、`write_p0a_outputs`（JSON 排序、SHA、无时间戳）✓。
- `SELFCHECK.json`：15/15、`deterministic_outputs=true`、`synthetic_only=true`、`real_data_read=false`、`network=false`；其 `config_sha256`/`script_sha256` 与实际文件 SHA **一致**（`3AEDDAB5…`、`D7DE7B40…`、`91E576CF…`）；`SELFCHECK.json` 本身 SHA `458FB995…` 与 usage/record 登记一致，且为合成数据（覆盖目标缩放 56→28 已披露）✓。

**FAIL（功能性阻塞）**：
- `check_run_gate(cfg, confirm_run)` 在 `utility_range is None` 或 `delta_min_state == blocked_by_utility_definition` 时返回 `STATUS_BLOCKED`（exit 4），**不检查** `utility.utility_gate_required_for_run`（config 已置 false）。`main()` 在 `--p0a-metadata` 分支前就调用它（`:991`），所以：
  - 默认：exit 3（正确）；
  - `--confirm-run` 但 real_run_enabled=false：exit 3（正确）；
  - **Lead 批准后 real_run_enabled=true + --confirm-run + --p0a-metadata：exit 4 `blocked_by_utility_definition`（错误；P0a 应可运行）**；
  - full relations_check 同样被阻塞（v4 允许 P0a relations_check 在 P0d 前跑）。
- `SELFCHECK` 的 `run_gate_refusal` 只测 default/confirm-only；`blocked_utility_branch` 直接调 `run_relations_check(...)` 并显式设 `utility_gate_required_for_run=True`；**没有测"main + enabled + --p0a-metadata + utility blocked 应进入 metadata 分支"**。因此 15/15 不能证明批准后能跑。
- **审计不一致**：config `p0a_metadata.gates` 名称与代码输出不一致（`reference_84_subset_matched96` vs `reference_matched_subset`；`precheck_eligible_ge_86` vs `precheck_eligible_ge_target`；`s_milp_expected_passing_count_recorded` 未实现）；`result["counts"]["reference_milp_upper_bound"]` 仍把 config 的 v3 114/112 写进 P0a 输出。

### 2.5 ⑤ 门控/措辞（WEAK）

- 前置条件（Lead 批准 + two-key + 复审通过 + eligible≥86）在 v4 文档/ record 里有，但**代码门控未按 v4 的分阶段语义实现**（同 ④）；修好后需把"Lead 批准时间/方式 + `--confirm-run` + real_run_enabled=true + 复审通过"写入 record，并把 "P0a-metadata PASS ≠ relations_check/PASS ≠ Stage 1/效果" 写进输出措辞。
- 失败类别/短路（P0a-metadata fail → `data_unavailable`/`design_invalid`，不跑 relations_check；P0d blocked 只阻止 Stage 1）✓；措辞模板（不声称新颖性/机制/迁移/决策收益；per-tissue Breast/Colon；Pancreas 排除披露）✓。
- 建议在 P0a 输出加 `s_milp_optimum`、`solver`、`S splits SHA`、`coverage target`、`gate list`，并在 record 里冻结 P0a 输出 SHA 后才允许 relations_check（v4 P7 已列，需落到代码/记录）。

### 2.6 ⑥ 总判决 / 是否可批准 P0a-metadata

**revise（≤5 必改）；当前不可批准。** 设计实质（方案 A 的分配/排除/覆盖/MDE/CP/统计规则）已达到可运行水平；**唯一硬阻塞是 run gate 的实现**；另 4 项是覆盖上界误读、config/代码 gate 清单不一致、18 个 Pancreas reference 未使用披露、以及修完后自检/SHA/记录更新。修复 1–2（代码）和 3–5（文档/审计）后，由 Lead 批准 + two-key，即可跑 P0a-metadata（metadata-only；不读响应）；**本挑战不再需要第三次全量复审，除非修复改动了分配/覆盖/MDE 逻辑**。

## 3. 五条必改（≤5）

1. **修 run gate（功能性阻塞）**：`check_run_gate` 必须尊重 `utility.utility_gate_required_for_run`（false → 不因 utility blocked 拒绝）；推荐模式感知：`--p0a-metadata` 只需 two-key（`--confirm-run` + `real_run_enabled=true`）；full relations_check 也只在 `utility_gate_required_for_run=true` 时才要求 utility/δ_min（P0d 前允许跑 P0a relations_check）。保留：默认/仅 confirm → exit 3；`real_run_enabled=false` → exit 3；**并新增 selfcheck 测试**：enabled + confirm + `--p0a-metadata`（+ utility blocked）→ 进入 metadata 分支（合成/拒绝读取真实数据的检查），以及 full relations_check 的行为；重跑 selfcheck、更新 SELFCHECK/usage_v4/record_v4 SHA。
2. **修覆盖上界表述**：把 spec_v4 §1.1/§2、REVISION §2 的 "112≥86 → 目标在已证上界内" 改为："v3 MILP 112 是不同 S 组成（41 leftover 任取 24）的上界，不适用于 v4；v4 以 P0a-metadata 实际 `s_milp_optimum` 为准（独立复算约 **106**，≥86 可达，余量 20）"；从 config `coverage/reference_milp_upper_bound_after_S_precheck` 删除或标 provenance；P0a 输出记录 `s_milp_optimum/solver/coverage_target`，不得把 112 当"已证"写入 P0a。
3. **对齐 config gate 清单与代码输出**：将 config `p0a_metadata.gates` 改为代码实际写出的 8–9 个 gate 名（`reference_matched_subset`、`reference_size_ok`、`three_way_disjoint`、`main_tissues_breast_colon`、`pancreas_excluded`、`tissue_span_non_vacuity`、`s_side_cond_cov_ge_12`、`precheck_eligible_ge_target`、`s_selection_solver`），并**实现/输出 `s_milp_optimum`（期望通过数）**；移除未实现的 `s_milp_expected_passing_count_recorded` 或明确改名为已实现字段；P0a 输出加 `coverage_denominator/target`、S splits SHA、solver、expected count。
4. **披露 18 个 Pancreas reference 细胞未被使用**：在 spec/protocol/record 中如实写"reference 84 含 A9+B9 个 Pancreas 细胞；因主族 per-tissue Breast/Colon 且主模型无 tissue nuisance，这些细胞不参与主族关系/区间/检验，仅为保持 84/24/17 组成而保留；若未来要增加 S context，可重分配（本版不预留）"；同时把 n=11/k10 行标注为"n_ctx_min=12 下不可用（仅参考）"，不只标 n=14/19。
5. **修完后更新审计链并写清批准前置**：重跑 synthetic selfcheck（含新 gate 测试），更新 `SELFCHECK.json`/`usage_v4`/`record_v4` 的 SHA；在 record 里写"Lead 批准 + two-key + 复审通过"三前置，明确 P0a-metadata PASS ≠ relations_check PASS ≠ Stage 1/效果；P0a-metadata 输出 SHA 冻结后才允许 relations_check；确认 `load_metadata_inputs` 只读 6 个元数据列（无 endpoint）并保留 `real_data_read=false` 直到批准。

## 4. 保留项（v4 的实质进步，务必保留）

- 方案 A 的分配/排除/覆盖算术（本复审 §2.1 全部自洽）；τ_t 删除；per-tissue 主族与 Pancreas 排除/披露。
- 覆盖口径 171→86、R_min=20、S MILP/贪心/tie-break、non-vacuity、eligible<86→data_unavailable 的设计（**实现逻辑正确**，只需改 112 表述）。
- MDE/n–p1/CP 精确规则、S=12/tissue→insufficient_precision、退出上限固定 0.15/0.10、k_E/δ_fit/J/κ 主法、P0a 只用 2.0σ、utility 移 P0d。
- Stage0 代码函数（allocate/enumerate/select_s/run_p0a_metadata/loader）、config 全键、`--p0a-metadata`、合成 selfcheck 15/15 与 SHA（**只差 gate 修复与测试补充**）。
- 失败类别/短路、措辞模板、A4/A5 接口、lineage、C 边界、不声称新颖性；REVISION/record 的诚实缺口披露。

## 5. 复核证据与本轮边界

- **脚本与输出**：`tmp/challenge_a1v4_checks.py`→`checks.json`（v4 分配/B12/C12 的 coverage：max 116 without A/B gate）；`tmp/challenge_a1v4_checks2.py`→`checks2.json`（A/B-gated max 104 illustrative seed）；`tmp/challenge_a1v4_checks3.py`→`checks3.json`（**与代码一致的确定性字母序分配：A42/B42、leftover41、网格 171、supply 135、S=12/12 下 max covered=106**）；`tmp/challenge_a1v4_meta_check.py`（config/代码 gate 名单、selfcheck ids、64/16 残留检查）。
- **关键数字**：MDE p1≈0.930743（power 0.7998）、p1=0.95→0.88164；n–p1 表全对；CP 0/29=0.098、0/40=0.072、1/46=0.099、1/47=0.097；matched 96 B33/C35/P28；主族 171；reference 84（A17/16/9+B16/17/9）；S24 B12/C12；U17 B6/C0/P11；剩余 41；v4 S 覆盖 max **106**（A/B-gated，≥86）；112 为 v3 不同 S 组成的上界。
- **完整性**：v4 交付物 SHA 与 usage_v4/record_v4 一致；v3/v1–v2 未变；Stage0 三件 SHA 与 SELFCHECK/usage 一致；**未改任何 A1 产物/其它目录/INDEX/SYNTHESIS/git**；只新增本文件与 `tmp/`。
- **边界**：本轮**不运行真实数据/P0a-metadata/relations_check/体检/MDE 预检、不训练、不读任何响应值**（只读 identity/condition/tissue 元数据做算术）；所有数字是元数据/纯算术/协议审查，不是生物学或效果证据；挑战结论不构成对 A1 作者身份或既往记录的改写。

## 6. 给 Lead 的批准建议

- **当前：不可批准 P0a-metadata**（命令会 blocked_by_utility_definition，什么都不跑）。
- **修完必改 1–5（1 个代码门控 + 1 个覆盖表述 + 1 个 gate 对齐 + 1 个披露 + 1 个自检/SHA/记录）后：可批准**。建议 Lead 在批准前让实现者只跑合成 selfcheck（不读真实数据）确认：
  1. default / 仅 `--confirm-run` → exit 3；
  2. `real_run_enabled=true` + `--confirm-run` + `--p0a-metadata`（utility blocked）→ 进入 metadata 分支（但自检环境不得读真实数据；可用 stub/fixture）；
  3. 输出 P0a `s_milp_optimum/solver/gates` 与 config gate 清单一致；
  4. P0a-metadata 输出 SHA 冻结，且 `real_data_read=false` 直到 Lead 正式批准的那一次。
- 真实 P0a-metadata（只读元数据）通过后，才允许 P0a relations_check（参考响应可读、≤30 min）；P0d 仍 blocked 只阻止 Stage 1。**P0a-metadata PASS 不是关系成立、不是 Stage 1、不是效果证据。**
