# R200-D5.4 记录（record_d5_v0_4）

2026-10-27 ｜ 执行：cellstate-lit（task-100） ｜ 工作目录：`D:\MAESTRO`。
对象：按 `challenge_D5_v0_3.md`（endpoint-auditor，**revise**，5 必改）修 v0.3 → v0.4：SHA/size 自洽、E7 总拟合数 **3,600**、CPU/wall **预算预检**、描述性执行冻结、Lead 文本。**不运行效果、不拟合预测、不读表达/响应矩阵。**
只写 `research/2026-10-27-direction-mechanism-expansion/d5_temporal/` 下 **v0.4 新文件** 与 `tmp/`；**v0.1/v0.2/v0.3 全部冻结不改**。

## 0. 纪律与范围

- 未训练/未拟合/未运行效果或预测统计；未读 h5ad 表达矩阵 `X` 数值、`obsm`/`layers`、任何响应/功能矩阵；未联网。
- v0.4 唯一执行代码：`d5_revision_v0_4.py`（metadata-only：读 v0.1–v0.3 产物 SHA、v0.3 JSON、challenge；读已装库版本元数据；**无拟合**；输出 `d5_v0_4.json`）。
- 没有效果/预测数值；本任务只做文档/预算/SHA 自洽与描述性执行冻结。

## 1. 读过什么

| 输入 | 用途 | 证据状态 |
|---|---|---|
| `challenge_D5_v0_3.md`（9,727 B） | 5 必改依据 | 已读 |
| v0.1/v0.2/v0.3 六文件×3 | 冻结历史；SHA 登记；旧 SHA 位置审计；数字交叉核对 | 已读/哈希 |
| `challenge_D5.md`、`challenge_D5_v0_2.md` | 历史挑战 | 已读（前轮/本任务登记） |
| `d5_v0_3.json` | active drugs/n、V2 paired、描述性 schema、EX-G0b、E6/E7 内容 | 已读/引用 |
| h5ad **obs/var 元数据**（SHA） | 输入登记；**未读 X 值** | metadata-only |
| 已装库版本（importlib.metadata） | E7 library 版本 | 元数据 |
| 背景（R200 BRIEF、direction report/mechanisms_v3、R199 BRIEF、ERRATA_A3、A3v2） | 边界/纪律（前轮已读） | 已读（前轮） |

**未读**：h5ad `X` 值；任何响应/功能矩阵；其它研究目录 effect 结果。

## 2. 实际执行

### 2.1 `d5_revision_v0_4.py`（metadata-only；确定性）

命令：
```text
D:\anaconda\envs\maestro\python.exe research/2026-10-27-direction-mechanism-expansion/d5_temporal/d5_revision_v0_4.py
```
行为：
1. 登记 v0.1/v0.2/v0.3 六文件×3、三个 challenge、h5ad 的 SHA（不读 X 值）。
2. **SHA/size 审计**：核对 v0.3 实际值（code 27,070 B / JSON 28,629 B / protocol / report / record / usage），与 challenge 记录一致；定位 v0.3 protocol §12/report 中旧 SHA 值的行号（协议 171、report 69/70），**v0.4 不再引用旧值**；v0.4 产物按设计不含旧前缀。
3. 读取 v0.3 JSON 的 active drugs（Bortezomib 22 / Idasanutlin 24 / Trametinib 24）、V2 paired 15/16/15、描述性 schema/EX-G0b/E6；复制为 v0.4（语义不变）。
4. **E7 修正**：6 tuned models（B1/B3/B4/B5/B7/B8）× 600 = **3,600 fits/run**；`max_fits_total=3,600`；不预注册第 7 模型；重新计算 tuning-grid SHA **`4d3b6d02…`**。
5. **预算预检**：两跑 + 零模型估算 **34–67 min**（期望 ~45 min），cap **120 min**；预执行 synthetic timing test；超 → `protocol_deviation` STOP，不放宽 cap；给出各组件估算/依据/零模型 ops。
6. 输出 `d5_v0_4.json`（revision_changes、sha_consistency_audit、descriptive_analysis、execution_gates、null_models_E6、tuning_E7+budget_precheck、E1–E12 v0.4、failure/stop、lead_approval_suggested_text、verdicts、inputs SHA、script SHA）。
7. 本任务不写 v0.1–v0.3 文件；不运行效果。

**未执行**：`X` 读取、模型拟合/预测/效应统计、网络请求。

### 2.2 轮次

`d5_revision_v0_4.py` 共运行 **2 次**（run1 成功；run2 为立即重跑），`d5_v0_4.json` 两次**逐字节一致**（最终 SHA `3d6fbf82…`）。

## 3. 验证

```text
v0.3 实际 SHA 与 challenge_D5_v0_3 §4 一致（code 27,070 B / JSON 28,629 B / protocol 14,171 B / report 7,547 B / record 8,115 B / usage 8,565 B）
v0.3 protocol/report 旧 SHA 前缀仅存在于冻结 v0.3（协议 line 171、report line 69/70）；v0.4 产物中旧前缀 0 次
v0.4 产物中旧总数/typo 均为 0 次；15/16/15 全文一致
d5_v0_4.json:
  两次连续运行逐字节一致：SHA256 3d6fbf8279cd4faa45788239c028aa0a341d474f517c1e2f1895e5620dbe3681 (36,343 B)
  json.load OK；total_tuned_fits=3600；n_permutations=1000；budget total range [34,67] min；cap 120
  verdict=descriptive_only；recommend_approve_to_lead_exec_descriptive=true；approve_to_lead_exec=lead_decision_required
未读表达/响应；未拟合；未联网；v0.1/v0.2/v0.3 未改
```

**无**任何效果/预测计算；以上仅为文件哈希、旧值审计、预算估算与确定性检查。

## 4. 产物与 SHA256

| 文件 | 字节 | SHA256 |
|---|---:|---|
| `PROTOCOL_D5_v0_4.md`（新，descriptive_only） | 14,945 | `8a31766447c627d0e90aae874def5c51dc94be5de20f281c3ef80655612d10f2` |
| `report_d5_v0_4.md`（新） | 7,680 | `67e02b0aed97eda408015b5962edfdb80d8223b63c07b9e098b6dc817e05ed6e` |
| `d5_revision_v0_4.py`（新） | 24,172 | `d4d627a14a3a517f83adc8f4daa84d0f94833261609a5353aad56864dce75090` |
| `d5_v0_4.json`（新） | 36,343 | `3d6fbf8279cd4faa45788239c028aa0a341d474f517c1e2f1895e5620dbe3681` |
| `record_d5_v0_4.md`（本文件） | — | 见 `usage_d5_v0_4.json` |
| `usage_d5_v0_4.json`（新） | — | 见文件 |

**v0.3 实际 SHA（引用，不改）**：code `d66fbdbe…`（27,070 B）、JSON `97250a0b…`（28,629 B）、protocol `e848a0ba…`、report `2c35780d…`、record `018f57e4…`、usage `1fb7c4a2…`。
**v0.1/v0.2/v0.3 未改**；v0.4 不含旧 SHA 前缀、不含旧总数、不含 typo。
E7 tuning-grid SHA `4d3b6d02474505b6fe67e31bce837784dbb85ce91b03ec3d1c9f540d2bbc66b5`。

## 5. 决定与理由

1. **SHA 修正放 v0.4**：v0.3 冻结不改；v0.4 引用实际值并全产物清除旧前缀，冻结链自洽（v0.3 旧值只留历史）。
2. **E7 总拟合数 3,600**：6 tuned models × 600；旧总数只有在 7 个 tuned model 时才成立，当前无第 7 模型；不改网格语义、不预注册第 7 模型。
3. **预算预检给估算 + 预执行 timing test**：两跑 + 零模型估算 34–67 min（期望 ~45）< 120 cap；执行前 synthetic timing test；超 → `protocol_deviation` STOP，不放宽 cap（不把 cap 当结果后调整的余地）。
4. **描述性执行冻结**：E1–E12/EX-G0b/两跑/schema 写死；禁止 confirmatory/G3/G4/`evaluation_cannot_distinguish` 推断/biology/功能/迁移/决策/机制/新颖性/真实轨迹；BRD3379 永不回 primary。
5. **Lead 文本**：仅 approve descriptive_only；confirmatory → stop + 测量规格；不自行批准（`approve_to_lead_exec=lead_decision_required`）。
6. **不运行效果**：任务要求；执行需另立描述性任务 + Lead 批准。

## 6. 限制 / 未完成

- 本轮只做文档/预算/SHA 自洽与描述性冻结；**不运行效果/不拟合/不读表达**；描述性执行尚未发生。
- 预算预检是估算，不是实测；执行前 synthetic timing test 可能触发 `protocol_deviation`。
- active-dose 仍 metadata-level；执行前 EX-G0b 必须再核；功能/时间轴/配对/batch 缺口不变。
- V2 15–19<20 仅 exploratory；BRD3379 只作 zero-dose/vehicle-like control。
- 若 Lead 要 confirmatory：**stop**（约 1,571 独立细胞系/药或认证 r_err≥0.987/0.985；配对/功能/batch 新测量）。
- v0.1/v0.2/v0.3 保留历史；v0.4 是唯一描述性执行依据候选。

## 7. 下一执行者从哪里开始

1. 读 `PROTOCOL_D5_v0_4.md`（§0 五必改、§5 E7 3,600 + 预算预检、§6 EX-G0b、§7 E1–E12、§9 Lead 文本）与 `report_d5_v0_4.md`。
2. **无需再挑战**（挑战者已说明修完 1–3 后可 `approve_to_lead_exec_descriptive`）；等 Lead 决定：
   - **批准 descriptive_only** → 另立描述性执行任务：EX-G0b 先核 → synthetic timing test → 两跑 → 只报描述性字段；不得确认/机制/功能。
   - **要求 confirmatory** → **stop + 测量规格**；不得用描述性运行替代。
3. **不重开 R196v2/R197v2**；BRD3379 永不回 primary；v0.1/v0.2/v0.3 不改。
