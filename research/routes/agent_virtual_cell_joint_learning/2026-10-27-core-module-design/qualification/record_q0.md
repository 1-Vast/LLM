# record_q0 —— R199-Q0 数据资格审计执行记录（metadata-only）

2026-10-27 ｜ 执行：drugcomb-auditor（task-53）｜ 工作目录 `D:\MAESTRO`
**范围**：只写 `research/2026-10-27-core-module-design/qualification/`（`PROTOCOL_Q0.md`、`q0.py`、`q0.json`、`report_q0.md`、`record_q0.md`、`usage_q0.json`）与 `tmp/` 侦察/补丁文件；**不改**其它目录、INDEX、SYNTHESIS、git、A0/A1/A2/A3 产物、`src/`。
**纪律**：不训练/不拟合/不估效果；响应列只做存在性/空值检查，**未读响应数值做效应**；不重开 R196/R197 旧判定；不写机制/迁移/决策收益/新颖性；阴性完整记录。

## 0. 任务与判定

- 任务：R199 唯一任务——数据资格审计，检查本地/可下载数据是否支持 `Δ(c;a,a';b)=E[y(c,a,b)]−E[y(c,a',b)]` 的成员×伙伴×细胞三向交叉、合法暴露、独立功能终点、重复/批次，并使"固定反馈比较更新器"可公平执行。
- **总体判定：`not_qualified`**；候选 `O'Neil = qualified_with_conditions`，其余 `not_qualified`（Jaaks Original/Validation 可作 source，但非独立 target；DrugComb v1.4/v1.5 G2 fail；BeatAML/Mix-seq 无组合）。
- 一句话：**交叉规模与 MDE 不是阻塞项；阻塞在"同族独立功能端点 + 合法暴露 + 独立培养/批次 + 非重聚合 lineage"没有任何 source→target 对同时满足。**

## 1. 预冻结侦察声明

冻结前只做：阅读 R199 BRIEF、`core-module-design/report.md`、`ERRATA_A3.md`/`a3.json`、`REVOCATION_R196.md`、R196v2/R197v2 记录、DrugComb 资格报告；以及候选文件的**列名/行数/实体数/重复结构**核对。**未计算门槛判定、未用响应值、未调阈值**。`PROTOCOL_Q0.md` 在 q0.py 首次运行前写成并补入"总体 source→target 判定"规则后冻结（SHA `D87C004E…A26877`）；此后**未再修改协议**。`q0.py` 从原始文件重算全部数字。

## 2. 输入（只读）

- `research/2026-10-27-innovation-round-r199/BRIEF.md`（对象/门槛/停止条件；C176/C177 状态）。
- `research/2026-10-27-core-module-design/report.md`（Δ 定义、三模块、E0 资格；不声称机制）。
- `research/2026-10-27-conditional-shift/{ERRATA_A3.md,a3.json}`（A3 边界；41/4,179 仅背景）。
- `research/2026-10-27-c130-audit/REVOCATION_R196.md`、`record_r196_v2.md`（C176：R196v2 `inconclusive`）。
- `research/2026-10-27-q-structure/record_r197_v2.md`（C177：R197 v1 作废；v2 `inconclusive`）。
- 数据文件（metadata-only）：Jaaks Original/Validation fitted（`CELL_LINE_NAME/ANCHOR_ID/LIBRARY_ID/ANCHOR_CONC/LIBRARY_CONC/BARCODE` 列）、DrugComb v1.4 summary（`block_id/drug_row/drug_col/cell_line_name/conc_*_unit`）、DrugComb v1.5 full（`tmp/a3_v15_summary.csv`；只读 `study_name/cell_line_name/drug_row/drug_col/block_id` 与端点头存在性）、O'Neil workbook（`BatchID/cell_line/drugA_name/drugA Conc/drugB_name/drugB Conc`）、BeatAML 文件列表/probit 列名、Mix-seq h5ad obs 元数据（`n_obs/perturbation/obs 列`）。响应列**未读值**。

## 3. 实现与运行

### 3.1 命令

```powershell
cd D:\MAESTRO\research\2026-10-27-core-module-design\qualification
& D:\anaconda\envs\maestro\python.exe q0.py    # 首跑 ~177 s；修复后 ~80 s
```

- 最终产物：`q0.json`（SHA `F952CCF3…1DA786B`）；同脚本同输入连续两跑逐字节相同（run1=run2=该 SHA）。
- 运行时间：最终 ~80 s（DrugComb v1.5 1.43M 行 streaming + O'Neil Excel 读取 + Jaaks pair 覆盖枚举）；<15 min 预算。
- 确定性：JSON 键排序、无时间戳；输入/脚本 SHA 写在 `q0.json`。

### 3.2 实现迭代（工程/定义修正，全部披露；未改冻结阈值）

| # | 问题 | 修正 | 影响 |
|---|---|---|---|
| 1 | 首版对 Jaaks/O'Neil 的 pair×cell 表用 `set` 枚举，内存风险；首跑被中止 | 改为"计数字典 + key cap"（G1 只关心 ≥3 细胞；不再存 cell 集合） | 无统计口径变化；大候选（DrugComb）在 cap 处标 `not_enumerated`，G1 未认证 |
| 2 | DrugComb v1.5 的 units 在 cross 枚举提前停止时被少计 | 拆为两次独立 pass：先全量算 units/contexts，再受 cap 限制枚举 cross | 修正 v15 units 76,415,680（此前 9,346,196 为 bug 值） |
| 3 | Jaaks G2 用"anchor 浓度集合完全相同"过严（部分键只测到 1 个 anchor 浓度） | 改为"同 `(cell,anchor)` 下所有成员至少 1 个共同 anchor 浓度"，并同时报 ≥2 共同浓度比例 | Jaaks G2 由 fail → conditional（匹配 99.34%；≥2 浓度 85.46%） |
| 4 | O'Neil 的 partner 剂量匹配用"每 (cell,partner) 只有一个剂量值"错误判据 | 改为 batch-aware：同 `BatchID×cell×partner` 下各成员使用同一伙伴剂量集（4×4 网格） | O'Neil partner matching 由 0.0 → 1.0；G2 conditional；O'Neil 成为 `qualified_with_conditions` |
| 5 | O'Neil 的替换单元跨批次混算 | 改为 `(BatchID, cell, partner)` 为单元（同一实验内合法暴露） | 单元 699,746；上下文 1,792；更符合"合法暴露" |

- 以上均为**实现/定义正确性修正**，在最终判定前完成；**未改协议中的门槛数字**；最终 q0.json 为修正后结果。

## 4. 关键结果（详见 report_q0.md / q0.json）

1. **三向交叉**：Jaaks Original 2,014,581 单元/3,199 上下文/125 细胞/42,959 个 ≥3 细胞成员对；Validation 12,622/991/97/388；O'Neil 699,746/1,792/39/27,391；DrugComb v1.5 理论 76,415,680/20,226/288（cross 未认证）；v1.4 52,873,936/11,148/112（未认证）；BeatAML/Mix-seq 0。
2. **五门槛**：Jaaks Original/Validation = G1 pass；G2/G3/G4 conditional；G5 fail（自身/96 共享细胞）。O'Neil = G1 pass；G2–G5 全 conditional（partner 匹配 100%；4 技术重复；9/39 与 Jaaks 重叠）。DrugComb v1.5/v1.4 = G2 fail（无数字剂量），G1 未认证（v1.5）/未认证（v1.4），G3/G4/G5 conditional；BeatAML/Mix-seq = G1/G3/G4 fail。
3. **Δ 可估/MDE**：Jaaks anchor 级重复仅 14.58% 单元 ≥2 行（技术/barcode）；O'Neil 每 dose-cell 4 技术重复；MDE80 在 n_eff 24–192、σ_e 0.041/0.058/0.109 下为 0.008–0.062；达 MDE≤0.10 仅需 n_eff 1.3–9.3 → **精度不是阻塞项**。
4. **总体**：source Jaaks 可估；target O'Neil gates ok 但**端点族不兼容**（ΔEMAX vs raw viability；O'Neil 无单药参照）；DrugComb target G2 fail；无公平 source→target 对 → `not_qualified`。
5. **同 96 细胞**：Jaaks Original/Validation 共享 **96 细胞/4,760 pair 键**，明确未当独立数据。

## 5. 未执行 / 限制

- **未读响应值做统计**；未训练/拟合/估 Q；未下载新数据（DrugComb v1.5 full 为既有 `tmp/` 文件；未下载 DrugComb raw 2.0 GB）。
- **未改**其它目录/INDEX/SYNTHESIS/git；未改 A0/A1/A2/A3 产物。
- 阈值（G1 规模、δ_min=0.10）为冻结的 provisional/设计下限；第 2 步前须由 A5 决策成本替换 δ_min。
- DrugComb v1.4/v1.5 的 pair×cell 覆盖在 5,000,000 键 cap 处停止（G1 未认证）；这是内存保护，不是"交叉不存在"。
- O'Neil 的 BatchID 被当作同一实验 exposure 单元；若实际只是同 lab 技术批，G4 仍 conditional（已标）。
- 本审计不是系统资源综述；"未列"≠"不存在"。

## 6. 下一执行者从哪里开始

1. 先读 `report_q0.md` §0/§5/§7：总体 `not_qualified`；唯一条件候选是 O'Neil（开发性、内部细胞留出、viability 端点、无独立培养/独立功能读数）。
2. **不要进入第 2 步**（公平更新器比较）除非补 §7 的测量规格：独立 target 资源 + 同族端点 + 数字剂量/暴露 + 独立培养/批次 + 非重聚合 lineage + 正交功能读数；先冻结新协议，不得用换指标/切分/剂量档凑资格。
3. 若 Lead 只批准"O'Neil 内部细胞留出"的窄开发任务：按 report §4.2 条件执行；不得称独立确认/迁移/决策收益；仍不得称机制。
4. 不得把同一 96 细胞换聚合当新数据；不得把 DrugComb 大单元数当资格。

## 7. 产物 SHA256

| 文件 | 字节 | SHA256 |
|---|---:|---|
| `PROTOCOL_Q0.md` | 10,636 | `D87C004E3FDBCC7093C76B913D6D79C98C0DA02C9A3C9B4B6108A03381A26877` |
| `q0.py` | 40,237 | `01FDDDE5F25E2AB71278EBEE96D23DA49A878B26A7FA1BA2BFF65F18FE27C54D` |
| `q0.json` | 33,889 | `F952CCF3418CDD994D58412DE56E8EA3C3AF23C0E48A9C45147E7EDC91DA786B` |
| `report_q0.md` | 见 usage_q0.json | 见 usage_q0.json |
