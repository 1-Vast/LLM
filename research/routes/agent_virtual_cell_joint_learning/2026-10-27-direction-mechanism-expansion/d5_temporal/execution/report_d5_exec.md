# R200-D5-EXEC 报告：一次纯描述性执行（非 confirmatory）

2026-10-28 ｜ 执行：cellstate-lit（task-101） ｜ 状态：**completed_descriptive_only（单次描述性执行；非 confirmatory）**。
依据：`DECISION_D5_DESCRIPTIVE_EXEC.md`（Lead 批准 descriptive_only；确认对象 v0.4 SHA `8a317664…`、`3d6fbf82…`、`d4d627a1…`、`67e02b0a…`、`d6c3fcd9…`；v0.1–v0.3 冻结）。
执行：`run_d5_exec.py`（单线程 BLAS，seed 20261027）；机器可读结果：`d5_exec.json`；预算预检：`timing_test.json`。
**声明：本分析不检验时间预测是否成立；只描述 3 active drugs 的 per-drug Δρ/CI/MDE/room/reliability/per-fold 与 V2 exploratory。MDE/room 仅为 precision descriptor；不推断 biology/时间预测/迁移/决策收益；BRD3379 永不进 primary；RNA 代理≠功能。**

## 0. 执行结论（仅描述性）

- **EX-G0a pass**：3 active drugs 合法线 22/24/24（Bortezomib/Idasanutlin/Trametinib）。
- **EX-G0b pass（metadata-level，带限制）**：compound identity + actual dose µM + vehicle + source/assay 已记录；**无独立化合物 identity/剂量/vehicle 实测**（未做湿实验）。未触发 `active_dose_identity_unverified`。
- **timing test pass**：synthetic-only 保守投影 **24.74 min**（cap 120 min）；实际两跑 + 零模型总 wall **135.83 s（2.26 min）**，远低于 cap。
- **两跑一致**：v1+v2 结果 JSON SHA 两次均为 **`295f5206…e18a21e`**；`equal=true`。
- **描述性数值**（不得解释为支持/否定时间预测）：
  - V1 Δρ：Bortezomib **0.1954**、Idasanutlin **0.1757**、Trametinib **0.1209**；3 药等权平均 **0.1640**。
  - 所有 per-drug Δρ CI 均跨 0；MDE80 **0.686/0.667/0.706**（均 > δ_min=0.10，仅精度描述）。
  - V2 paired Δρ：target24h E1/E2 **0.0679**；target48h E1/E2 **0.0235**、E2/E3 **0.0714**；均为 exploratory，CI 跨 0。
- **边界**：功能 `not_qualified`、`time_axis_unverified`、BRD3379 secondary only；无 confirmatory/G3/G4/`evaluation_cannot_distinguish` 推断；不称 biology/功能/迁移/决策/机制/新颖性/真实轨迹。

## 1. EX-G0 先核（执行前）

| 门 | 结果 |
|---|---|
| EX-G0a 覆盖 | **pass**：Bortezomib 22 / Idasanutlin 24 / Trametinib 24 合法线 |
| EX-G0b active-dose/identity | **pass_metadata_level_with_limitation**：dose 2.5/2.5/0.1 µM；ChEMBL CHEMBL325041/CHEMBL2402737/CHEMBL2103875；vehicle=time-matched control（V1）/DMSO hash（V2）；source=h5ad；assay=scRNA-seq perturbation screen；**无独立 identity/dose/vehicle 实测** |
| 失败处理 | 未失败；若失败应 STOP `active_dose_identity_unverified` 并不得执行 |

## 2. 预算预检与实测 wall

| 项 | 值 |
|---|---|
| synthetic timing test | **pass**；投影 **24.74 min**（cap **120 min**）；`timing_test.json` SHA `6cb48586…` |
| 实际总 wall（最终执行） | **135.83 s（≈2.26 min）**（含 pseudobulk、CCLE、两跑、V1/V2 零模型） |
| 组件 | prep ≈4.3 s；CCLE ≈3.0 s；analysis two runs ≈125.4 s（见 `d5_exec.json:timing`） |
| fits | V1 tuned 5 模型 ×600 = 3,000；V2 B8 tuned 600；合计 **3,600/run**；零模型 N1/N2/N3/N4/N6 各 1,000 次 |
| 结论 | 未触发 `protocol_deviation`；cap 未放宽 |

## 3. V1 描述性结果（3 active drugs；leave-cell-line-out 5 折；6h→24h RNA 代理）

| drug | n | ρ_early6h | ρ_static | **Δρ** | Δρ 95% CI | MDE80 | room | reliability |
|---|---:|---:|---:|---:|---|---:|---:|---:|
| Bortezomib | 22 | -0.0672 | -0.2626 | **0.1954** | [-0.2728, 0.6835] | 0.6859 | 1.2355 | 0.9203 |
| Idasanutlin | 24 | 0.2113 | 0.0357 | **0.1757** | [-0.2916, 0.6470] | 0.6672 | 0.9617 | 0.9437 |
| Trametinib | 24 | 0.0400 | -0.0809 | **0.1209** | [-0.3757, 0.6040] | 0.7058 | 1.0791 | 0.9789 |

- **Summary**：等权平均 Δρ **0.1640**；per-drug 范围 **[0.1209, 0.1954]**；MDE80 均 > δ_min=0.10 → **descriptive precision insufficient for confirmatory inference**（精度描述，不是检验阴性/不存在）。
- per-fold Δρ 见 `d5_exec.json:v1.<drug>.per_fold_delta_rho`（方向不一致，例如 Bortezomib fold0 +0.8、fold1 −0.3）；fold manifest SHA `0056d69e…`。
- 选中超参数（每折 alpha/GP/GBM）见 `selected_hyperparameters`；B3/B7 在 V1 为同一 early-ridge 设定（协议允许；B7 单快照重复实现）。

## 4. V1 零模型（1000×；仅描述性分布）

| 零模型 | 分布 mean | median | p95 | observed | fraction null ≥ observed |
|---|---:|---:|---:|---:|---:|
| N1 cell-shuffle | 0.0351 | 0.0377 | 0.1743 | 0.1640 | 0.064 |
| N2 drug-shuffle | 0.1610 | 0.1640 | 0.2337 | 0.1640 | 0.654 |
| N6 static-capacity | 0.0254 | 0.0220 | 0.2342 | 0.1640 | 0.142 |
| N5 future-leak sentinel | ρ_oracle mean **0.9895**（管道/指标正常） | — | — | — | — |

**注**：以上仅描述性对照；**不是 confirmatory p 值/判定**；不得写成支持/否定时间预测。

## 5. V2 exploratory（Trametinib 5 时点；paired 15/16/15）

| contrast | n_E1 | n_E2 | n_E3 | paired_n | Δρ | Δρ 95% CI | MDE80 | capacity control mean/p95/fraction | time-shuffle mean/p95/fraction |
|---|---:|---:|---:|---:|---:|---|---:|---|---|
| target24h E1→E2 | 18 | 15 | — | 15 | **0.0679** | [-0.4910, 0.5622] | 0.7412 | 0.3439 / 0.7143 / 0.516 | 0.1943 / 0.5537 / 0.267 |
| target48h E1→E2 | 19 | 16 | 15 | 16 | **0.0235** | [-0.3540, 0.4084] | 0.5208 | 0.1433 / 0.4529 / 0.971 | 0.0476 / 0.3649 / 0.917 |
| target48h E2→E3 | 19 | 16 | 15 | 15 | **0.0714** | [-0.3236, 0.4557] | 0.5189 | -0.0288 / 0.2750 / 0.933 | 0.0568 / 0.4180 / 0.946 |

- V2 全部 **exploratory_only**；n<20；CI 均跨 0；**不得升级 confirmatory**。
- capacity/time-shuffle 的 `observed_delta` 基于 panel-target y（与表格 Δρ 的全基因 target mean 口径略有差异）；仅描述性。
- V2 B8 采用 8×5 调参（600 fits），其余 E1/E2/E3 为固定 alpha=1.0 的描述性 ridge（未额外网格）；见 §7 偏差。

## 6. 数据/设计执行事实

| 项 | 值 |
|---|---|
| h5ad | `mcfarland_2020.h5ad` SHA `94a72400…`；182,875×32,738 |
| pseudobulk groups | 428（QC-normal；min/max cells 8/389） |
| half groups（reliability） | 140 |
| CCLE 静态特征 | 18,099 genes；209 细胞系匹配（DepMap_ID）；train-fold-only PCA(20)+ridge |
| V1 folds | 冻结 v0.2 manifest（22/24/24；`index%5`；fold SHA `0056d69e…`） |
| V2 paired | target24h 15；target48h 16/15（frozen v0.2） |
| 两跑 | `equal=true`；SHA `295f5206…` |
| 输出 SHA | `d5_exec.json` **`13c4d3ae…142588`**；`timing_test.json` **`6cb48586…1800bf`**；`run_d5_exec.py` **`2a4ba0ae…0e21b9`** |

## 7. 偏差/限制（必须随结果一起读）

1. **非 confirmatory**：未做 H-D5-1 推断；未使用 G3/G4 通过/失败；未把 `evaluation_cannot_distinguish` 当推断。
2. **V2 为 exploratory 简化实现**：E1/E2/E3 固定 alpha=1.0 ridge（无网格）；B8 调参 600 fits；capacity/time-shuffle 各 1,000 次；n<20，不能升级。
3. **V1 B3 与 B7 重复**（均为 single-early ridge）；按协议预算各计 600 fits，结果相同属预期；不作为两个独立证据。
4. **EX-G0b 仅 metadata-level**：未做独立化合物 identity/dose/vehicle 实测；仅记录 h5ad 注释/source/assay。
5. **静态特征仅 CCLE/DepMap 匹配线**（209/line 交集）；未匹配线在 B1 中被排除，V1 使用共同线计算 ρ（n_used≤n_eligible）。
6. 无同细胞早–晚配对、无 batch/plate/exposure/独立培养/重复；`time_axis_unverified`；RNA 代理≠功能；BRD3379 secondary only。
7. 所有 MDE/room/CI 为描述性精度量；**不得**写成"时间预测成立/不存在"或 biology/功能/迁移/决策/机制/新颖性结论。

## 8. 文件

- `execution/run_d5_exec.py`：**2a4ba0ae…**（48,259 B）
- `execution/d5_exec.json`：**13c4d3ae…**（27,200 B；含 EX-G0、timing、V1/V2、零模型、两跑、边界）
- `execution/timing_test.json`：**6cb48586…**（512 B）
- `execution/report_d5_exec.md`（本文）
- `execution/record_d5_exec.md`、`execution/usage_d5_exec.json`（见文件）
- v0.1–v0.4 协议文件未改。

**最终边界**：本次执行**只**产出描述性字段；不声称 confirmatory、biology/功能、迁移、决策收益、机制、新颖性、真实轨迹；BRD3379 永不回 primary；功能 `not_qualified`、时间轴 `unverified`。
