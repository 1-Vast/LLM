# R200-D5.3 修订报告：纯描述性降级 + typo/零模型/E7/G0b（5 必改）

2026-10-27 ｜ 执行：cellstate-lit（task-98） ｜ 状态：**descriptive_only（按 challenge_D5_v0_2.md 的 reduce_to_descriptive 修订；不运行效果）**。
依据：`challenge_D5_v0_2.md`（endpoint-auditor：**reduce_to_descriptive**，5 必改；`approve_to_lead_exec=false`；若 Lead 要求 confirmatory → **stop**）。
交付：`PROTOCOL_D5_v0_3.md`（DRAFT/descriptive_only）、`d5_revision_v0_3.py`、`d5_v0_3.json`、本文、`record_d5_v0_3.md`、`usage_d5_v0_3.json`。
**v0.1/v0.2 文件冻结不改**；v0.3 是唯一描述性执行依据候选。

## 0. 结论

- **5 必改全部落实**；D5 从 v0.2 的 "confirmatory-development（3 active drugs）" **降级为纯描述性开发层分析**：**不做 confirmatory H-D5-1 检验、不设 G3/G4 通过/失败、不把 `evaluation_cannot_distinguish` 当推断**；只报告 per-drug Δρ/CI/MDE/room/reliability/per-fold + BRD3379 secondary + V2 exploratory。
- **核心声明**：**本分析不检验时间预测是否成立；只描述可达到的精度与方向。** 不写 biology/功能/迁移/决策/机制/新颖性。
- **保留**：3 active drugs（Bortezomib 22 / Idasanutlin 24 / Trametinib 24）、V1 6h→24h 分子代理、V2 exploratory（paired 15/16/15）、BRD3379 zero-dose/vehicle-like control（secondary/descriptive only）、功能 `not_qualified`、`time_axis_unverified`。
- **`approve_to_lead_exec=false`**；建议**再挑战（reduce 路径）**；若 Lead 要 confirmatory → **stop + 测量规格**（每药约 1,571 独立细胞系或认证 r_err≥0.987/0.985；配对/功能/batch 新测量）。

## 1. 五必改落实（challenge_D5_v0_2 §2）

| # | 必改 | v0.3 落实 | 状态 |
|---|---|---|---|
| 1 | H-D5-2 paired-set typo（第三组 16→15） | v0.3 全文 **15/16/15**；v0.2 typo 定位在 `PROTOCOL_D5_v0_2.md:96`（冻结历史）；v0.3 无该 typo（已检索） | **已改** |
| 2 | E6 零模型冻结 1,000（不得 200 降级） | N1/N2/N3/N4/N6 均 **1,000 次**；写清合法零/聚类配对单位/seed 20261027；不得低于 1,000 除非预注册功效依据 | **已改** |
| 3 | E7 具体化 B1–B8 library/网格/候选数/内层折/trials/compute cap | 冻结 sklearn 1.9.0 等版本；内层 5 折按细胞系；每 tuned model **8 candidates × 5 inner = 40 fits/unit**；15 outer units → **600 fits/model**；总上限 4,200；CPU 120 min；grid SHA **d2835e79…** | **已改** |
| 4 | 降级纯描述性：H-D5-1 descriptive；移除 G3/G4 通过/失败与 `evaluation_cannot_distinguish` 推断 | v0.3 `descriptive_only`；报告字段（§4）只含描述性 Δρ/CI/MDE/room/reliability/per-fold；精度描述子标签（不是检验判定）；明确"不检验时间预测是否成立" | **已改** |
| 5 | G0b 执行前再核 compound identity/dose/vehicle；失败 → `active_dose_identity_unverified` 停；BRD3379 不回 primary | v0.3 EX-G0b 要求实测/记录 4 项（identity/dose/vehicle/source）；失败 STOP；BRD3379 永久排除 primary | **已改** |

## 2. 关键数字（描述性口径；`d5_v0_3.json`）

| active drug | n 合法线 | MDE80 上界（描述性） | 所需 r_err（描述性参考） |
|---|---:|---:|---:|
| Bortezomib | 22 | 0.865 | 0.987 |
| Idasanutlin | 24 | 0.826 | 0.985 |
| Trametinib | 24 | 0.826 | 0.985 |

- **V2 paired**：target24h E1/E2 = **15**；target48h E1/E2 = **16**、E2/E3 = **15**（v0.3 全文一致；v0.2 typo 已修）。
- **BRD3379**：zero-dose/vehicle-like control（0.0 µM、无 ChEMBL）；secondary/descriptive only；**永不进 primary**（历史 95 线仅描述）。
- **描述性摘要**（执行时报告）：3 active drugs 等权平均 Δρ、per-drug 范围、CI、MDE、room、split-half reliability、per-fold。
- **精度描述子**：MDE80 大 → 写 "descriptive precision insufficient for confirmatory inference"（不是检验阴性/不存在）。

## 3. 描述性报告字段清单（执行时冻结）

- **V1 per drug**：`drug, n_eligible_lines, rho_early6h, rho_static, delta_rho, delta_ci_low, delta_ci_high, mde80, room, reliability_split_half, per_fold_delta_rho, fold_manifest_sha256, selected_hyperparameters`。
- **Summary**：`active_drug_equal_weight_mean_delta_rho, min/max_per_drug_delta_rho, descriptive_precision_note`。
- **BRD3379**：`role, n_eligible_lines, secondary_descriptive_only`。
- **V2**：`target_h, E1/E2/E3, n_E1, n_E2, n_E3, paired_n, delta_rho, delta_ci, per_fold, capacity_control_result, exploratory_only`。
- **禁止**：confirmatory p-value/推断判定、biology/function/migration/decision/mechanism/novelty/真实轨迹陈述。

## 4. 执行前门（不是推断门）

- **EX-G0a**：每 active drug ≥20 合法线（22/24/24 → pass）。
- **EX-G0b**：执行前**实测/记录** compound identity、actual dose（µM）、vehicle identity、identity 来源/assay；metadata-level 不够；**失败 → `active_dose_identity_unverified` STOP**；**BRD3379 永不回 primary**。

## 5. 未变/仍缺（不回避）

1. 无匹配晚期功能读数 → `functional_route=not_qualified`；RNA 代理≠功能；需同细胞×同药×同剂量×6/24/48h viability+凋亡/再生长、时间匹配 vehicle、≥3 复孔 × ≥2 独立培养。
2. 无同细胞早–晚配对（破坏性快照；obs 全唯一）→ 不做个体轨迹；需 lineage/活细胞成像。
3. 无 batch/plate/run/exposure/独立培养/重复 → `time_axis_unverified`；不能作绝对时间/同板同批主张。
4. V2 15–19 线 <20 → exploratory only；不能升级 confirmatory。
5. active-dose 仅在执行前再核后生效；v0.2 的 metadata-level conditional pass 只是前置资格。
6. **confirmatory H-D5-1 当前不可执行**：MDE 上界 0.865/0.826/0.826 >> δ_min=0.10；若 Lead 要求 confirmatory → **stop**（非 approve），不得用一次描述性/不可分辨运行替代。
7. 不声称 confirmatory/biology/功能/迁移/决策/机制/新颖性/真实轨迹。

## 6. v0.1/v0.2 冻结与 SHA

- **v0.1 六文件、v0.2 六文件均未改**；SHA 作为输入登记在 `d5_v0_3.json:inputs_sha256`（含 challenge_D5 / challenge_D5_v0_2）。
- v0.2 的 paired-set typo（第三组 16→15）只在 `PROTOCOL_D5_v0_2.md:96` 冻结历史中；v0.3 修正为 **15/16/15**（`PROTOCOL_D5_v0_3.md` 无 typo）。
- v0.3 新文件：`PROTOCOL_D5_v0_3.md`、`d5_revision_v0_3.py`、`d5_v0_3.json`、`report_d5_v0_3.md`、`record_d5_v0_3.md`、`usage_d5_v0_3.json`。

## 7. 确定性 / SHA

- `d5_revision_v0_3.py` **ff4c03ebbc1d497bb393c1cbfbdde5b9f6b96715cf24cd8192ae1648a80f3ad7**（26,947 B）。
- `d5_v0_3.json` **3508dadaa9af416fb05717bf19a77d901d28543f52d11881873e7443610d7a26**（28,575 B）；**两次运行逐字节一致**。
- E7 tuning-grid SHA **d2835e79b3a75c3eed91622954339f235be5d7368add28d01840fe45a353e751**。
- metadata-only：未读表达/响应、未拟合、未联网；v0.1/v0.2 未改。

## 8. 建议

- **建议再提交独立挑战（reduce 路径：是）**：审 typo 修复、E6 1,000、E7 冻结清单/预算、描述性 schema/inference 规则、EX-G0b。
- 挑战通过前 `approve_to_lead_exec` 保持 false、不执行；通过后另立**描述性执行**任务（仍只分子层；不确认/不机制/不功能）。
- **若 Lead 要 confirmatory H-D5-1：stop**（记录测量规格：每药约 1,571 独立细胞系或认证 r_err≥0.987/0.985；配对/功能/batch 新测量）；不得用描述性运行替代。
