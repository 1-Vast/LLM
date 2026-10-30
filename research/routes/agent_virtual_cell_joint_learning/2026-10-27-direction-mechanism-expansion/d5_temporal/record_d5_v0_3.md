# R200-D5.3 记录（record_d5_v0_3）

2026-10-27 ｜ 执行：cellstate-lit（task-98） ｜ 工作目录：`D:\MAESTRO`。
对象：按 `challenge_D5_v0_2.md`（endpoint-auditor，**reduce_to_descriptive**，5 必改）把 D5 从 v0.2 降级为**纯描述性** v0.3。**不运行效果、不拟合预测、不读表达/响应矩阵。**
只写 `research/2026-10-27-direction-mechanism-expansion/d5_temporal/` 下 **v0.3 新文件** 与 `tmp/`；**v0.1/v0.2 六文件均冻结不改**。

## 0. 纪律与范围

- 未训练/未拟合/未运行效果或预测统计；未读 h5ad 表达矩阵 `X` 数值、`obsm`/`layers`、任何响应/功能矩阵；未联网。
- v0.3 唯一执行代码：`d5_revision_v0_3.py`（metadata-only：读 v0.1/v0.2 JSON/SHA + challenge 文件 + h5ad 元数据 + 已装库版本元数据；**无拟合**；输出 `d5_v0_3.json`）。
- 所有数字来自 v0.2 已登记资格（本任务不重算 h5ad 计数；v0.2 资格已由 challenge 复核）与库版本元数据；**没有效果/预测数值**。

## 1. 读过什么

| 输入 | 用途 | 证据状态 |
|---|---|---|
| `challenge_D5_v0_2.md`（11,036 B） | reduce_to_descriptive 的 5 必改依据 | 已读 |
| v0.1 六文件 + v0.2 六文件 | 冻结历史；SHA 登记；typo 定位；数字交叉核对 | 已读/哈希 |
| `challenge_D5.md`（11,300 B） | v0.1 挑战历史 | 已读 |
| `d5_v0_2.json` | active drugs/n、MDE、V2 paired、v0.2 typo 所在 protocol 文本 | 已读/引用 |
| h5ad **obs/var 元数据** | 仅作为输入 SHA 登记（本任务未重算计数；v0.2 已复核） | metadata-only |
| 已装库版本（importlib.metadata） | E7 library 版本（scikit-learn 1.9.0 等） | 元数据 |
| 背景（R200 BRIEF、direction report/mechanisms_v3、R199 BRIEF、ERRATA_A3、A3v2） | 边界/纪律（前轮已读） | 已读（前轮） |

**未读**：h5ad `X` 值；任何响应/功能矩阵；其它研究目录 effect 结果。

## 2. 实际执行

### 2.1 `d5_revision_v0_3.py`（metadata-only；确定性）

命令：
```text
D:\anaconda\envs\maestro\python.exe research\2026-10-27-direction-mechanism-expansion\d5_temporal\d5_revision_v0_3.py
```
行为：
1. 登记 v0.1/v0.2/challenge/h5ad 的 SHA（不读 X 值）；读取 v0.2 JSON 的 active drugs（Bortezomib 22 / Idasanutlin 24 / Trametinib 24）、MDE（0.865/0.826/0.826）、V2 paired（15/16/15）。
2. **typo 审计**：在 v0.2 protocol 文本中定位 paired-set typo（第三组 16），记录行号 **96**；v0.2 正确 token（15/16/15）行 105。v0.3 产物不含该 typo 字面量（已检索）。
3. **E6 零模型冻结**：N1/N2/N3/N4/N6 均 **1,000** 次，seed 20261027；写清合法零/聚类/配对单位；N5 future-leak sentinel。
4. **E7 具体调参计划**：库版本（scikit-learn 1.9.0 等）、内层 5 折按细胞系、每 tuned model 8 candidates × 5 inner = 40 fits/unit、15 outer units、600 fits/tuned model、总上限 4,200、CPU 120 min、具体 grids（B1/B3/B7/B8 ridge alpha；B4 HistGBM 8 组合；B5 GP 8 组合）；**tuning-grid SHA `d2835e79…`**。
5. **降级描述性**：生成 `descriptive_analysis`（H-D5-1 descriptive；无 G3/G4 通过/失败；无 `evaluation_cannot_distinguish` 推断；报告字段 §4；精度描述子规则）。
6. **执行前门**：EX-G0a 覆盖（22/24/24）；EX-G0b 要求执行前再核 compound identity/dose/vehicle；失败 → `active_dose_identity_unverified` STOP；BRD3379 永不回 primary。
7. 输出 `d5_v0_3.json`（含 revision_changes、descriptive_analysis、execution_gates、null_models_E6、tuning_E7、E1–E12 v0.3、failure/stop、verdicts、cross_check、inputs SHA、script SHA）。
8. 本任务不写 v0.1/v0.2 文件；不运行效果。

**未执行**：`X` 读取、模型拟合/预测/效应统计、网络请求。

### 2.2 轮次

`d5_revision_v0_3.py` 共运行 4 次：run1 初版成功；run2（mask typo 字面量后）成功；run3（limits 措辞 patch 后）成功；run4 为 run3 的立即重跑，`d5_v0_3.json` 与 run3 **逐字节一致**（最终 SHA `97250a0b…`）。

## 3. 验证

```text
v0.1/v0.2/challenge SHA 与 challenge_D5_v0_2 §4 报告值一致（登记于 d5_v0_3.json:inputs_sha256）
v0.2 protocol typo 定位：line 96（第三组 16）；v0.3 artifacts 中该字面量 0 次，15/16/15 在 protocol/report/JSON/code 一致
d5_v0_3.json:
  两次连续运行逐字节一致：SHA256 97250a0b85a53824aceb0b99efe1493074e6f8aefbfba4387403f77b4cc05798 (28,629 B)
  json.load OK
  active drugs = Bortezomib/Idasanutlin/Trametinib (22/24/24); paired = 15/16/15; n_permutations = 1000; verdict = descriptive_only; approve_to_lead_exec = false
未读表达/响应；未拟合；未联网；v0.1/v0.2 未改
```

**无**任何效果/预测计算；以上仅为文件哈希、typo 审计、结构计数与确定性检查。

## 4. 产物与 SHA256

| 文件 | 字节 | SHA256 |
|---|---:|---|
| `PROTOCOL_D5_v0_3.md`（新，descriptive_only） | 14,171 | `e848a0ba41fc8535de747184b19f9e0c3527b81a008c1b5d518a331693293614` |
| `report_d5_v0_3.md`（新） | 7,547 | `2c35780dda6d075f55e53c9c6423dd7f96c5d65c0f0ac42ddd9fce8d319c4898` |
| `d5_revision_v0_3.py`（新） | 27,070 | `d66fbdbe7641b16ffa145eaf70faed4d166fa7dcc5e569752c045ac5dd695122` |
| `d5_v0_3.json`（新） | 28,629 | `97250a0b85a53824aceb0b99efe1493074e6f8aefbfba4387403f77b4cc05798` |
| `record_d5_v0_3.md`（本文件） | — | 见 `usage_d5_v0_3.json` |
| `usage_d5_v0_3.json`（新） | — | 见文件 |
| v0.1/v0.2 输入（不改） | — | 见 `d5_v0_3.json:inputs_sha256` |

**v0.1/v0.2 未改**；v0.2 的 paired-set typo 保留在 `PROTOCOL_D5_v0_2.md:96` 冻结历史；v0.3 修正为 **15/16/15**。
E7 tuning-grid SHA `d2835e79b3a75c3eed91622954339f235be5d7368add28d01840fe45a353e751`。

## 5. 决定与理由

1. **reduce_to_descriptive**：challenge 明确建议；G3 预运行上界 0.865/0.826/0.826 ≫ δ=0.10，confirmatory H-D5-1 在 22/24/24 线几乎不可执行；**不能 approve confirmatory**。降级后保留开发资产但**不伪装 confirmatory**。
2. **移除 confirmatory/G3/G4/`evaluation_cannot_distinguish` 推断**：避免把"精度不足"当"时间预测不存在"；只报告描述性 Δρ/CI/MDE/room/reliability/per-fold。
3. **E6 1,000**：challenge 指出 v0.1 冻结口径 1,000，v0.2 的 ≥200 是反向降级；v0.3 固定 1,000，并写清合法零/聚类/配对。
4. **E7 具体化**：不给执行者留下自由选择空间；冻结 library/网格/候选数/内层折/trials/compute cap 与 grid SHA。
5. **G0b 执行前再核**：metadata 注释不等于 identity/dose/vehicle 认证；失败即 `active_dose_identity_unverified` STOP；BRD3379 永不回 primary。
6. **不运行效果**：任务要求；执行需另立描述性任务 + 独立挑战。

## 6. 限制 / 未完成

- 本轮只做文档/资格/设计修订；**不运行效果/不拟合/不读表达**；描述性执行尚未发生。
- active-dose 仍为 metadata-level（执行前须再核）；功能/时间轴/配对/batch 缺口不变。
- V2 15–19<20 仅 exploratory；BRD3379 只作 zero-dose/vehicle-like control。
- 若 Lead 要 confirmatory H-D5-1：**stop**（所需独立细胞系约 1,571/药或认证 r_err≥0.987/0.985；配对/功能/batch 新测量）；不得用描述性运行替代。
- v0.1/v0.2 保留历史；v0.3 是唯一描述性执行依据候选。

## 7. 下一执行者从哪里开始

1. 读 `PROTOCOL_D5_v0_3.md`（§3 描述性、§4 报告字段、§5 执行前门、§6 零模型 1,000、§7 调参计划、§8 E1–E12）与 `report_d5_v0_3.md`。
2. **再提交独立挑战（reduce 路径：是）**：审 typo 修复、E6 1,000、E7 冻结清单/预算、描述性 schema/inference 规则、EX-G0b；挑战通过前 `approve_to_lead_exec=false`。
3. 挑战通过后另立**描述性执行**任务（仍只分子层；不确认/不机制/不功能）；先跑 E1–E9 并报告描述性字段，再决定是否值得继续。
4. **若 Lead 要 confirmatory：stop + 测量规格**；不得用描述性执行替代；不重开 R196v2/R197v2。
