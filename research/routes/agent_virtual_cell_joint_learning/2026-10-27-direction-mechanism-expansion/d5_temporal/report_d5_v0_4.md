# R200-D5.4 修订报告：SHA/size 修正 + E7 3,600 fits + 预算预检（5 必改）

2026-10-27 ｜ 执行：cellstate-lit（task-100） ｜ 状态：**descriptive_only（按 challenge_D5_v0_3.md 的 revise/5 必改修订；不运行效果）**。
依据：`challenge_D5_v0_3.md`（endpoint-auditor：**revise**；修完 1–3 后可建议 `approve_to_lead_exec_descriptive`；不 approve confirmatory；不 stop）。
交付：`PROTOCOL_D5_v0_4.md`（DRAFT/descriptive_only）、`d5_revision_v0_4.py`、`d5_v0_4.json`、本文、`record_d5_v0_4.md`、`usage_d5_v0_4.json`。
**v0.1/v0.2/v0.3 全部冻结不改**；v0.4 是唯一描述性执行依据候选。

## 0. 结论

- **5 必改全部落实**；D5 保持**纯描述性开发层分析**（无 confirmatory）；**不建议再挑战**（挑战者已明确"修完 1–3 后可 approve_to_lead_exec_descriptive"）。
- **修正**：① v0.3 protocol/report 旧 SHA/size 不再出现在 v0.4；v0.4 引用 v0.3 **实际** code `D66FBDBE…`（27,070 B）/JSON `97250A0B…`（28,629 B）；② E7 总拟合数改为 **3,600**（6 tuned models × 600）；③ 补 **CPU/wall 预算预检**（两跑 + 零模型估算 **34–67 min**，期望 ~45 min；cap 120 min；预执行 synthetic timing test；超 → `protocol_deviation` stop，不放宽）。
- **推荐**：`approve_to_lead_exec_descriptive = true`（Lead 决定；仅描述性）；**不自行批准执行**。
- **若 Lead 要 confirmatory**：**stop + 测量规格**（每药约 1,571 独立细胞系或认证 r_err≥0.987/0.985；配对/功能/batch 新测量）。

## 1. 五必改落实

| # | 必改 | v0.4 落实 | 状态 |
|---|---|---|---|
| 1 | 旧 SHA/size 残留（v0.3 protocol §12/report） | v0.4 引用 v0.3 实际 **code `D66FBDBE…`（27,070 B）/JSON `97250A0B…`（28,629 B）**；v0.4 全部产物不含旧 SHA 前缀（已检索）；v0.3 旧值仅存冻结历史 | **已改** |
| 2 | E7 总拟合数：6×600 = **3,600** | `total_tuned_fits=3,600`、`max_fits_total=3,600`；同步 protocol/JSON/report/usage/checklist；不预注册第 7 模型；tuning-grid SHA **`4d3b6d02…`** | **已改** |
| 3 | CPU/wall 预算预检 | `budget_precheck`：两跑 + 零模型估算 **34–67 min**（期望 ~45 min）；cap **120 min**；预执行 synthetic timing test；超 → `protocol_deviation` STOP；不放宽 cap | **已补** |
| 4 | 描述性执行冻结（E1–E12/EX-G0b/两跑/schema） | §7 E1–E12 v0.4、§6 EX-G0b 先核（失败→`active_dose_identity_unverified` STOP）、两跑逐字节、§3.1 描述性 schema；禁止 confirmatory/G3/G4/`evaluation_cannot_distinguish` 推断/biology/功能/迁移/决策/机制/新颖性/真实轨迹；BRD3379 永不回 primary | **已冻结** |
| 5 | Lead 文本：仅 approve descriptive_only；confirmatory→stop+规格 | §9 `lead_approval_suggested_text`；confirmatory → stop + 测量规格（1,571 独立细胞系/药或 r_err≥0.987/0.985；配对/功能/batch 新测量） | **已写** |

## 2. 关键数字 / 预算

- **active drugs**：Bortezomib 22 / Idasanutlin 24 / Trametinib 24；V1 6h→24h RNA 分子代理；V2 paired **15/16/15**（exploratory）；BRD3379 secondary（zero-dose/vehicle-like control）。
- **E7**：6 tuned models（B1/B3/B4/B5/B7/B8）× **600 fits/model** = **3,600 fits/run**；8 candidates × 5 inner folds；15 outer units；未 tuned B0/B2/B6 不占网格。
- **E6**：N1/N2/N3/N4/N6 各 **1,000** 次；seed 20261027。
- **预算预检**：数据加载/pseudobulk 16–32 min + tuned fits 8–15 min + untuned 1–2 min + 零模型 4–8 min + 报告/IO 5–10 min = **34–67 min**（期望 ~45 min），两跑合计；cap **120 min**；预执行 synthetic timing test（不读表达/响应）；超 → `protocol_deviation` STOP；**不得放宽 cap**。
- **描述性精度**：MDE 上界（描述性参考）0.865/0.826/0.826；只作 precision descriptor，不是检验判定。

## 3. v0.3 实际 SHA（v0.4 引用，冻结历史）

| 文件 | 字节 | SHA256 |
|---|---:|---|
| `d5_revision_v0_3.py` | 27,070 | `d66fbdbe7641b16ffa145eaf70faed4d166fa7dcc5e569752c045ac5dd695122` |
| `d5_v0_3.json` | 28,629 | `97250a0b85a53824aceb0b99efe1493074e6f8aefbfba4387403f77b4cc05798` |
| `PROTOCOL_D5_v0_3.md` | 14,171 | `e848a0ba41fc8535de747184b19f9e0c3527b81a008c1b5d518a331693293614` |
| `report_d5_v0_3.md` | 7,547 | `2c35780dda6d075f55e53c9c6423dd7f96c5d65c0f0ac42ddd9fce8d319c4898` |
| `record_d5_v0_3.md` | 8,115 | `018f57e4cb4373fd62e5510d5361e0939594791e69e98f4e9f58b473e8c5a885` |
| `usage_d5_v0_3.json` | 8,565 | `1fb7c4a2bc563a468730a0d3153b98bf107580f1304995736267ae03308e87a4` |

v0.3 的 protocol/report 旧 SHA 值在 v0.3 冻结历史中；**v0.4 不再引用旧值**（已检索确认 v0.4 产物无旧前缀）。

## 4. v0.4 新 SHA

| 文件 | 字节 | SHA256 |
|---|---:|---|
| `PROTOCOL_D5_v0_4.md` | 见 record/usage | 见 record/usage |
| `report_d5_v0_4.md` | 见 record/usage | 见 record/usage |
| `d5_revision_v0_4.py` | 24,172 | `d4d627a14a3a517f83adc8f4daa84d0f94833261609a5353aad56864dce75090` |
| `d5_v0_4.json` | 36,343 | `3d6fbf8279cd4faa45788239c028aa0a341d474f517c1e2f1895e5620dbe3681` |
| `record_d5_v0_4.md` | 见 usage | 见 `usage_d5_v0_4.json` |
| `usage_d5_v0_4.json` | 见文件 | 见文件 |

E7 tuning-grid SHA **`4d3b6d02474505b6fe67e31bce837784dbb85ce91b03ec3d1c9f540d2bbc66b5`**；`d5_revision_v0_4.py` 两次运行 `d5_v0_4.json` 逐字节一致。

## 5. 描述性执行冻结清单（摘要）

- **EX-G0a**：3 active drugs ≥20 合法线（22/24/24 pass）。
- **EX-G0b**：执行前实测/记录 compound identity / actual dose / vehicle identity / source；失败 → `active_dose_identity_unverified` STOP；BRD3379 永不回 primary。
- **E1–E12**：数据加载/QC/pseudobulk/200 panel/fold loader/V1 无跨药配对/V2 paired 15/16/15/零模型 1,000/调参 3,600 fits/两跑逐字节/schema/描述性测量/报告模板/G5 断言/本轮不运行。
- **报告字段**：per-drug Δρ/CI/MDE/room/reliability/per-fold + summary + BRD3379 secondary + V2 exploratory；禁止 confirmatory/biology/function/migration/decision/mechanism/novelty/真实轨迹。
- **停止**：EX-G0 失败、泄漏、超预算（`protocol_deviation`，不放宽 cap）、功能/时间轴边界、confirmatory 需求 → stop。

## 6. 未变/仍缺

1. 功能 `not_qualified`（无匹配晚期功能；RNA 代理≠功能）；需同细胞×同药×同剂量×6/24/48h viability+凋亡/再生长、时间匹配 vehicle、≥3 复孔 × ≥2 独立培养。
2. 无同细胞早–晚配对（破坏性快照）；需 lineage/活细胞成像。
3. 无 batch/plate/run/exposure/独立培养/重复 → `time_axis_unverified`。
4. active-dose 仅 metadata-level；执行前 EX-G0b 再核。
5. V2 15–19 线 <20 → exploratory only。
6. **confirmatory 不可行**：MDE 上界 0.865/0.826/0.826 >> δ=0.10；需约 1,571 独立细胞系/药或认证 r_err≥0.987/0.985；配对/功能/batch 新测量；若 Lead 要求 confirmatory → **stop**。
7. 不声称 confirmatory/biology/功能/迁移/决策/机制/新颖性/真实轨迹；RNA 不是功能。

## 7. 建议

- **不建议再挑战**（挑战者已说明修完 1–3 后可 `approve_to_lead_exec_descriptive`）；建议 Lead 直接决定 **descriptive_only 批准/不批准**。
- 若批准：另立**描述性执行**任务；执行前 EX-G0b 先核 + synthetic timing test；两跑逐字节；只报描述性字段；不确认/不机制/不功能。
- 若 Lead 要 confirmatory：**stop + 测量规格**；不得用描述性运行替代。
- v0.1/v0.2/v0.3 未改；BRD3379 永不回 primary；不重开 R196v2/R197v2。
