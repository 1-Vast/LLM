# R199-A1v4.1 Stage 0 — relations_check（方案 A：per-tissue Breast/Colon；gate 修复版）

**状态：v4.1 工程实现已同步 A1v4.1 补丁；未在真实数据上运行，未产出任何真实关系表。** 本目录实现 A1v4 的 Stage 0 P0a-metadata → P0a relations_check（[../spec_v4_1.md](../spec_v4_1.md) / [../spec_v4.md](../spec_v4.md) / [../protocol_draft_v4.md](../protocol_draft_v4.md)），供 Lead 批准 P0a-metadata 后运行。

> **v4.1 补丁（相对 v4）**：① **run gate 模式感知**——`--p0a-metadata` 只需 two-key（`--confirm-run` + `real_run_enabled=true`），**utility/P0d blocked 不再阻塞 metadata**；full relations_check 仅在 `utility_gate_required_for_run=true` 时要求 utility；默认/仅 confirm → exit 3。② 覆盖上界改用 **v4 独立复算 max=106（≥86，余量 20）**，v3 的 114/112 仅标 provenance、不作门槛；P0a 以实际 `s_milp_optimum` 为门槛。③ config gate 清单与代码输出对齐，P0a 输出 `s_milp_optimum/solver/denominator/target/S splits SHA`。④ 披露 reference 84 含 **18 个 Pancreas 细胞（A9+B9）未被主族使用**；**n=11、n=7 行在 n_ctx_min=12 下不可用（仅参考）**。⑤ selfcheck 新增 gate-mode 用例（16/16），SELFCHECK/usage/record SHA 更新；**P0a-metadata PASS ≠ relations_check PASS ≠ Stage 1/效果**。

> **v4 关键变化（相对 v3 骨架）**：主族 = **per-tissue Breast/Colon**（Pancreas 明确排除，外部有效性披露）；覆盖分母 = post-precheck 主族网格 **171 → ≥86**；**P0a-metadata 先跑**（分配/网格/S 覆盖最大化/non-vacuity/eligible≥86；失败则跑前 stop）；P0a 只用 2.0σ_r、utility 移 P0d；**删除 64/16 与 min_relations_per_tissue=3**；`require_matched_conditions_subset=true`；two-key gate 保留。**本轮未运行真实数据。**

## 1. 文件（SHA 见 record_v4_1 §5）

| 文件 | 作用 |
|---|---|
| `relations_check.py` | Stage 0 实现：**模式感知 two-key gate**；**P0a-metadata**（显式 84/24/17、reference⊆matched96、per-tissue Breast/Colon 171 网格、S 覆盖最大化 MILP/贪心、non-vacuity、s_milp_optimum≥86）；P0a relations_check（A/B 半分离+交换、α/BH、2.0σ_r、覆盖 86/171）；`--p0a-metadata` CLI；确定性输出+SHA |
| `relations_check_config.json` | v4.1 全键：per_tissue Breast/Colon、排除 Pancreas、显式 tissue counts（A 17/16/9、B 16/17/9、S 12/12/0、U 6/0/11）、coverage 171/86、interval/utility off、require_matched_conditions_subset=true、MDE/n–p1/CP 规则、gate 清单与代码对齐、v4 复算 106 provenance |
| `synthetic_selfcheck.py` | 纯合成自检（不读 Jaaks、不联网），**16 项**测试（含 v4.1 gate-mode 用例）；生成 `SELFCHECK.json` |
| `SELFCHECK.json` | **16/16** synthetic 检查；**synthetic，不构成任何生物学证据**；synthetic 覆盖目标缩放（56→28，非真实 171→86） |
| `README.md` | 本文件 |

## 2. 运行门禁（写死）

默认（安全；不打开任何真实文件）：
```powershell
& D:\anaconda\envs\maestro\python.exe research\2026-10-27-innovation-scouting\conflict_signal\stage0\relations_check.py
# -> {"status":"refused","reason":"...--confirm-run flag is required...","real_data_read":false}，exit 3
```
真实 Stage 0 需要**三前置**（缺一不可）：**Lead 批准记录 + two-key（`--confirm-run` 且 `real_run_enabled=true`）+ A1v4.1 复审通过**。当前 `real_run_enabled=false`，默认/仅 `--confirm-run` 均 exit 3。
- **`--p0a-metadata`**：只需 two-key；utility/P0d blocked **不阻塞**（只读元数据，`real_data_read=false`）。
- **full relations_check**：two-key + utility 仅在 `utility_gate_required_for_run=true` 时要求；当前 false，P0d 前允许跑；若改为 true 且 utility blocked → exit 4（blocked_by_utility_definition）。
- **P0a-metadata PASS 不等于 relations_check PASS，也不等于 Stage 1/效果证据**；P0a 输出 SHA 冻结后才允许跑 relations_check。

命令（**待批准后才可用**）：
```powershell
# 1) metadata-only P0a precheck（不读响应列；输出 p0a_metadata.json）
& D:\anaconda\envs\maestro\python.exe research\2026-10-27-innovation-scouting\conflict_signal\stage0\relations_check.py --confirm-run --p0a-metadata
# 2) P0a relations_check（仅 P0a-metadata PASS 后）
& D:\anaconda\envs\maestro\python.exe research\2026-10-27-innovation-scouting\conflict_signal\stage0\relations_check.py --confirm-run
```
输出到 `stage0/real_run/`；预算 P0a-metadata ≤10 min、relations_check ≤30 min（超时 → design_invalid）。真实 loader 只读元数据/参考 A/B 响应列；S/U 响应不解析、不进内存；`require_matched_conditions_subset=true`。

## 3. v4.1 config 同步（相对 v3，已完成）

| 键 | v3（stale） | v4.1（现在） |
|---|---|---|
| `candidate_enumeration.context_mode` | per_tissue | **per_tissue**（主族 Breast/Colon；不再宣称 pooled） |
| `main_family_tissues` / `excluded_tissues` | — | `[Breast, Colon]` / `[Pancreas]` |
| `statistics.interval_utility_check_enabled` | true | **false**（P0a 只用 2.0σ_r） |
| `utility.utility_gate_required_for_run` | true | **false**（P0a 不被 δ_min 卡；P0d 单独 blocked） |
| `global_acceptance.coverage_denominator` / `coverage_min_abs` | null | **171 / 86** |
| `global_acceptance.min_relations_per_tissue` | 3 | **删除（null）** |
| `data.require_matched_conditions_subset` | false | **true**（reference 84 ⊆ matched 96） |
| `cell_allocation.explicit_tissue_counts` | 无（比例） | **显式 A/B/S/U tissue counts**（84/24/17；删 64/16） |
| `p0a_metadata` | 无 | **新增节**（budget/gates/output/failure categories） |
| `run_gate.mode_aware` | false（utility 无条件阻断） | **true**（`--p0a-metadata` 只需 two-key；full 仅 flag=true 时要求 utility） |
| `coverage.v3 114/112` | 写成"已证上界" | **删除/标 provenance；v4 独立复算 max=106（余量 20），实际门槛=s_milp_optimum** |
| `p0a_metadata.gates` | 5 个名称与代码不一致 | **与代码输出 10 个 key 对齐（含 s_milp_optimum_ge_target）** |
| `--p0a-metadata` CLI / S 预检 / matched 限制 / span 检查 | 无 | **已实现（v4.1 修复 gate 后可批准运行）** |

## 4. 合成自检（`SELFCHECK.json`；synthetic，不可作为证据）

运行：
```powershell
& D:\anaconda\envs\maestro\python.exe research\2026-10-27-innovation-scouting\conflict_signal\stage0\synthetic_selfcheck.py
# -> SELFCHECK.json；all_passed=true（16/16）；约 3–5 s；重跑逐字节相同
```
只使用合成元数据（模仿 Original 125 / matched 96 的 tissue 计数）与合成 y 值；不打开 Jaaks、不读真实响应、不联网；真实 loader 未调用（`isolation_no_real_data` 断言）。**synthetic 覆盖目标为 56→28（缩放），非真实 171→86，已在 SELFCHECK 警告中披露。**

| 测试 | 说明 |
|---|---|
| `p0a_metadata_pass` | P0a：reference⊆matched、三向不交、非空池/span、S 覆盖、eligible≥target |
| `p0a_no_pancreas_s_cells` | S 不含 Pancreas，S=24 = 12 Breast + 12 Colon |
| `run_gate_refusal` | 默认拒绝；`--confirm-run` 单独不足；main() exit 3 |
| **`p0a_metadata_gate_mode_allows_when_utility_blocked`** | **v4.1 新用例**：enabled+confirm+`--p0a-metadata`（utility blocked）→ 进入 metadata 分支（stub loader，不读真实数据）；full 模式仍 blocked |
| `blocked_utility_branch` | 显式 utility gate 打开且 δ_min blocked → full relations_check blocked |
| `pass_pipeline_synthetic` / `determinism_and_sha` | per-tissue 管线 pass；两次运行逐字节相同 + SHA 一致 |
| `p0a_fail_coverage_unreachable` | 目标 > eligible → 跑前 data_unavailable |
| `p0a_fail_non_vacuity` | 空候选网格 → design_invalid（non-vacuity gate） |
| `fail_insufficient_nctx` / `fail_interval_too_wide` / `fail_bh_none_significant` / `fail_R_below_min` / `fail_R_above_max` / `fail_budget_exceeded` | 失败分支各触发一次 |
| `isolation_no_real_data` | 未调用真实 loader；pandas 未导入 |

## 5. SHA256（v4.1 冻结；本轮验证）

见 `record_v4_1.md` §5 与 `usage_v4_1.json`；SELFCHECK.json 内 `script_sha256` 记录脚本/config 哈希并与磁盘一致。**v4.1 文件清单以 record_v4_1 §5 为准；v4 文档保留不改，由 v4.1 补丁覆盖。**

## 6. 已知缺口

1. **真实 P0a-metadata 未运行**：171 网格、真实 S MILP 覆盖（v4 独立复算 max=106）、non-vacuity/s_milp_optimum≥86 需真实 metadata 实测；若实际 <86 → 跑前 `data_unavailable`（stop，不降标准）。
2. **P0a relations_check/P0b/P0c/P0d 未运行**；P0d（δ_min/效用）仍 `blocked_by_utility_definition`，不阻塞 P0a 但阻止 Stage 1。
3. **S=24 按 tissue 12/12** → 每条主族关系最多 12 S context；**n=14/19 行不可用；n=11、n=7 行也因 n_ctx_min=12 不可用（仅参考）**；若预期 p1<0.9307 → `insufficient_precision`（不扩 S、不放宽 α、不降 n）。
4. **Pancreas 排除**：外部有效性不覆盖 Pancreas/其他 tissue；**reference 84 中 18 个 Pancreas 细胞（A9+B9）不被主族使用，仅为保持 84/24/17 组成而保留**，报告必须如实披露。
5. **P0b/P0c 未实现**（独立生成器/MDE 预检，属协议层下一轮）。
6. 收缩组均值当前为 cell 级等权均值（未额外 shrink）；sign test 无 cluster 校正（cluster 敏感性/P0b/P0c 处理）。
7. 本轮没有任何生物/关系/效果结论；不得引用本目录声称关系存在/约束有效；**P0a-metadata PASS ≠ relations_check PASS ≠ Stage 1/效果**。
