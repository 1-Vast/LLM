# R200-D5.1 修订报告：排除 BRD3379 零剂量 + V2 配对 n + active-dose 门

2026-10-27 ｜ 执行：cellstate-lit（task-96） ｜ 状态：**完成修订；不运行效果、不拟合预测、不读表达/响应矩阵**。
依据：`challenge_D5.md`（endpoint-auditor，`revise`，5 必改；当前 `approve_to_lead_exec=false`）。
交付：`PROTOCOL_D5_v0.2.md`（DRAFT）、`d5_revision.py`、`d5_v0_2.json`、本文、`record_d5_v0_2.md`、`usage_d5_v0_2.json`。
**v0.1 文件冻结不改**（`PROTOCOL_D5.md`/`d5.py`/`d5.json`/`report_d5.md`/`record_d5.md`/`usage_d5.json`）；本报告与 v0.2 取代其 primary/门/表述。

## 0. 结论

- **5 必改全部落实**（见 §1）；v0.1 的 **"4 drugs n≥20 confirmatory" 状态已撤回**；V1 primary 改为 **3 个 active drugs：Bortezomib n=22 / Idasanutlin n=24 / Trametinib n=24**；**BRD3379（0.0 µM）仅作 zero-dose/vehicle-like control，secondary/descriptive，不进入任何 primary 均值**。
- **V2 paired 修正**：target24h E1/E2 配对 **15** 线；target48h E1/E2 **16**、E2/E3 **15**；v0.1 `paired_n=2` 是字段 bug（`len(dict)`），已在 JSON 记录旧值/正确值。
- **G0 加 active-dose/identity 门**：G0a 覆盖 + G0b active-dose（metadata-level: dose>0 + ChEMBL）；3 active drugs = conditional pass（执行前需再核化合物/剂量/vehicle）；**BRD3379/control fail，BRD3379 排除出 primary**。
- **MDE（active only）**：Bortezomib 0.865（n=22）、Idasanutlin 0.826（n=24）、Trametinib 0.826（n=24）；达到 δ_min=0.10 所需跨模型误差相关 0.987/0.985/0.985 → **G3 仍很可能失败判 `evaluation_cannot_distinguish`**（不写阴性）。
- **整体 D5 仍 `qualified_with_conditions`（仅 3 active drugs 的分子代理开发层）**；功能 `not_qualified`；时间轴 `unverified`；**`approve_to_lead_exec=false`，建议再挑战**；本轮不运行。

## 1. 五必改落实（challenge_D5 §2）

| # | 挑战要求 | v0.2 落实 | 状态 |
|---|---|---|---|
| 1 | BRD3379=0.0 µM 不能算 V1 第四药；改 3 active drugs；BRD3379 只作 zero-dose/vehicle-like control/secondary，明确标签 | V1 primary = Bortezomib/Idasanutlin/Trametinib 等权平均（n=22/24/24）；BRD3379 输出强制标注 `zero-dose/vehicle-like control (not active)`；不进入 primary mean/CI/状态；撤回 4 药 confirmatory | **已改** |
| 2 | V2 paired_n 字段错误；改配对细胞系数（24h E1/E2=15；48h E1/E2=16、E2/E3=15），以 nested_paired_line_sets 为准 | `d5_v0_2.json:v2_corrected` 给 n_E1/n_E2/n_E3 + paired_n + paired line sets；记录 v0.1 bug [2,2,2]→[15,16,15]；H-D5-2 写明仅用 paired sets | **已改** |
| 3 | G0 加 active dose/处理身份门；BRD3379 未核前不 pass；更新 overall conditions/report §2/§3 | G0a 覆盖门（3 药 ≥20 线 pass）+ G0b active-dose/identity（dose>0 + unit + ChEMBL；3 药 conditional pass；BRD3379/control fail）；BRD3379 排除出 primary；overall conditions 写明 3 active drugs/BRD3379 secondary | **已改** |
| 4 | 更新 d5.json/report/protocol/record/usage 的 4 药表述/MDE/primary；重算 SHA；不得保留 4 drugs confirmatory | v0.2 新文件全部按 3 药重写；MDE 表只列 0.865/0.826/0.826；v0.1 文件不改并登记 SHA；v0.2 SHA 记录在 record/usage | **已改** |
| 5 | 执行协议前细节清单 | `PROTOCOL_D5_v0_2.md` §11 E1–E12（加载/QC/pseudobulk/200 gene panel/fold loader/paired sets/零模型+未来哨兵/B1–B8 调参/两跑 schema/measured MDE 预认证/失败模板/G5 断言）；本轮不运行 | **已补** |

## 2. 关键数字（v0.2，`d5_v0_2.json`）

### 2.1 Active-dose / treatment-identity 分类（metadata-level）

| arm | dose (µM) | ChEMBL | G0b | 角色 |
|---|---|---|---|---|
| Bortezomib | 2.5 | CHEMBL325041 | conditional pass | **active primary（n=22）** |
| Idasanutlin | 2.5 | CHEMBL2402737 | conditional pass | **active primary（n=24）** |
| Trametinib | 0.1 | CHEMBL2103875 | conditional pass | **active primary（n=24）** |
| BRD3379 | **0.0** | — | **fail** | **zero-dose/vehicle-like control；secondary only；排除** |
| control | 0.0 | — | fail（reference） | 时间匹配参照 |

**认证等级**：metadata-level = `dose>0 + dose_unit + ChEMBL annotation`；**不是**独立剂量/化合物/vehicle identity 测定。执行协议必须重新核验后才能运行。

### 2.2 V1 primary（3 active drugs）

- Active = Bortezomib n=22 / Idasanutlin n=24 / Trametinib n=24；各自合法线集合不同（**不是跨药配对**）。
- 主统计量 = 3 个 active drug 的 Δρ 等权平均；报告 per-drug CI 与 drug-level range。
- **MDE 上界（active only）**：0.865 / 0.826 / 0.826；所需 r_err 0.987/0.985/0.985。
- **BRD3379**：95 合法线数字保留但仅作 secondary/zero-dose control 描述；**无 primary 权重**。

### 2.3 V2 paired（修正）

| target | n_E1 | n_E2 | n_E3 | **paired（E1∩E2 / E2∩E3）** |
|---|---|---|---|---|
| 24h | 18 | 15 | — | **15** |
| 48h | 19 | 16 | 15 | **16 / 15** |

v0.1 `paired_n=2` 是 `len(dict)` bug；v0.2 以交集线数定义，并给出精确配对线名单（`v2_corrected.paired_line_sets`）。V2 仍 **exploratory only**（n<20）。

## 3. 资格与门（v0.2）

| 项 | v0.2 |
|---|---|
| V1 早期 RNA → 晚期 RNA（3 active drugs） | **qualified_with_conditions**（confirmatory-development，仅 3 active） |
| V2 两早时点增量 | **qualified_with_conditions（exploratory only）** |
| 晚期功能 | **not_qualified（data_unavailable）**；RNA 代理≠功能 |
| 同板同批/暴露/独立培养 | **time_axis_unverified** |
| BRD3379 | zero-dose/vehicle-like control；secondary/descriptive only |
| **整体 D5** | **qualified_with_conditions（3 active drugs 分子代理开发层；approve_to_lead_exec=false）** |

**G0**：G0a 覆盖（3 药 ≥20 线）+ G0b active-dose/identity（3 药 conditional pass；BRD3379/control fail）。
**G1–G5 / δ_min=0.10**：同 v0.1 结构；预运行 MDE 上界（active only）0.865/0.826/0.826；V2 0.93–1.06；**G3 高失败风险→`evaluation_cannot_distinguish`（不写阴性）**。
**失败类别**：新增 `active_dose_identity_unverified`；其余不变。

## 4. 未变/仍缺（不回避）

1. **无匹配晚期功能读数** → 功能/决策分支停止；需同细胞×同药×同剂量×6/24/48h viability+凋亡/再生长、时间匹配 vehicle、≥3 复孔 × ≥2 独立培养。
2. **无同细胞早–晚配对**（破坏性快照；obs index 全唯一）→ 不做个体轨迹；需 lineage/活细胞成像。
3. **无 batch/plate/run/exposure/独立培养/重复** → `time_axis_unverified`；不能作绝对时间/同板同批主张。
4. **V2 n=15–19<20** → 仅 exploratory；两早时点增量不能出确认性判定。
5. **active-dose 仅 metadata-level**（dose>0 + ChEMBL）→ 执行前必须再核化合物 identity/实际剂量/vehicle。
6. **预运行 MDE 上界高** → V1 3 药与 V2 很可能 G3 失败；不得用换指标制造可分辨。
7. **不声称新颖性/机制/迁移/决策收益/真实轨迹**；A3v2 仅背景、不复用未认证部分。

## 5. v0.1 文件与冻结

- **v0.1 六文件未改**（PROTOCOL_D5.md / d5.py / d5.json / report_d5.md / record_d5.md / usage_d5.json）；SHA 作为输入登记在 `d5_v0_2.json:inputs_sha256`。
- **v0.1 的 4 药 primary / "4 drugs n≥20 confirmatory" 已撤回**；v0.1 文本保留历史但不作运行依据；BRD3379 的 95 线只作 secondary control 数字。
- v0.2 新文件：`PROTOCOL_D5_v0_2.md`、`d5_revision.py`、`d5_v0_2.json`、`report_d5_v0_2.md`、`record_d5_v0_2.md`、`usage_d5_v0_2.json`。

## 6. 确定性 / SHA

- `d5_revision.py` **6a89039c7073782c71083d9095cc72172718ec374b84890e213788233057d199**（31,093 B）。
- `d5_v0_2.json` **d41ed20fc6a4545e2e8cada3b14702edd9c044093bfa4e1a018988358d207830**（32,951 B）；**两次运行逐字节一致**。
- V1 active primary fold manifest SHA **0056d69e4b6fbe515915008fd2f1a40213ea6a8837c7c673546bf76f901a52d2**。
- 输入 h5ad SHA `94a72400…`；metadata-only：未读表达值/响应、未拟合、未联网；v0.1 文件未改。

## 7. 建议

- **建议再提交独立挑战（是）**：挑战方复核 3 药 primary、BRD3379 secondary 标签、V2 paired 15/16/15、G0b/G3、执行清单；**通过前 `approve_to_lead_exec` 保持 false，不运行效果**。
- 若再挑战通过：另立执行协议/任务（E1–E12 冻结后），仍只做分子层；功能/决策/轨迹等新测量；不重开 R196v2/R197v2；不换名重启。
