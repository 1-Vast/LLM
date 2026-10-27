# R199-ON1 审计记录（record_on1）

角色：独立设计/资格复核 runner（非提案者；不参与效果设计）。工作目录 `D:\MAESTRO`；只写 `research/2026-10-27-core-module-design/oneil_dev/` 与 `tmp/`；未改 Q0 产物、其它目录、INDEX、SYNTHESIS、git。

## 1. 范围与依据

- 对象：R199-Q0 允许的唯一窄口径——**O'Neil 开发性内部细胞留出协议草案（设计 + 资格复核，不运行）**。
- 依据（只读）：`research/2026-10-27-core-module-design/qualification/{PROTOCOL_Q0.md, q0.json, report_q0.md}`；`research/2026-10-27-innovation-round-r199/BRIEF.md`；`research/2026-10-27-core-module-design/report.md`；`research/SYNTHESIS.md` C178–C181（C181：A1 Stage-0 `data_unavailable`、批准窗口用尽、唯一窄口径=ONeil 开发性）。
- 冻结协议：本目录 `PROTOCOL_ON1.md`（v1，在**任何 ON1 资格计数之前**冻结）。
- 边界：不训练/不拟合/不估效果/不比较更新器；viability 列只做**存在性/非空计数**，未读数值做任何统计；不联网；不写机制/迁移/决策收益/新颖性。

## 2. 时间线（本机，Asia/Shanghai）

| 时间 | 事件 |
|---|---|
| 19:55 | 接手 task-59；claim；读 Q0 协议/q0.json/report_q0、R199 BRIEF、core-module-design report、SYNTHESIS C178–C181 |
| 19:56–19:59 | metadata-only 侦察 2 轮（`tmp/_on1_recon*.py`：实体/批次/剂量网格/角色定向/成员-伙伴结构/跨细胞覆盖/Jaaks 重叠；**未读 viability 数值**） |
| 20:01 | 写 **`PROTOCOL_ON1.md`（v1 FROZEN）**：范围/定义/数据门 DG1–DG5/设计门 DSG1–DSG4/5 折设计/MDE 公式/失败类别/边界 |
| 20:02–20:06 | 写 `on1.py` 并修复 2 个实现错误（行级统计的成员列名、merge 后缀）；metadata-only 运行 |
| 20:06:5x | **v1 资格运行成功**：`data_unavailable`（DG3 字面失败；其余数据门+全部设计门 PASS）；wall ≈40 s |
| 20:07 | 写 **`AMENDMENT_ON1-001.md`**（DG3 修订提案；在 v1 结果之后、任何 v1.1 运行之前；不改 v1 判定） |
| 20:07:52 | **确定性重跑**：`on1.json` 与上一跑**逐字节一致**（SHA256 `2E793902…`）；wall 40.5 s |
| 20:0x | 写 `report_on1.md`、本 record、核对 SHA/双跑一致 |

## 3. 命令、预算与实际耗时

| 命令 | 实测 |
|---|---|
| `D:\anaconda\envs\maestro\python.exe -X utf8 research\2026-10-27-core-module-design\oneil_dev\on1.py`（`PYTHONHASHSEED=0`） | wall **38.1 s / 40.1 s / 40.5 s**（3 次；最后两次为确定性双跑） |
| metadata 侦察 `tmp/_on1_recon*.py` | 每次 ~35 s（读 38 MB OOXML 工作簿） |
| `python -m py_compile on1.py` | <1 s |

- 单命令 ≤15 min（实测 ~40 s）；CPU-only；无 GPU；无网络；输入总字节 239,493,975（见 usage_on1.json）。

## 4. 观测（关键事实）

1. **O'Neil 结构（复核）**：368,832 行；39 细胞；38 药；3 BatchID；每 (cell, 无序药对) 16 行（22,422 个）/32 行（315 个）；每行 4×4 数字剂量网格；每个无序药对只有一种 A/B 角色定向；伙伴-角色剂量集 100% 唯一匹配。
2. **批次**：batch1 = 358,560 行 / 39 细胞 / 22,410 pair-cells；batch2 = 5,232 行 / 9 细胞 / 327；batch3 = 5,040 行 / 15 细胞 / 315；pair-cell 跨 batch 集合 {(1,):22,101, (2,):321, (1,3):309, (2,3):6}。→ 主分析只用 batch1（协议冻结）。
3. **Jaaks 重叠 9/39**：`hct116, ht29, lovo, mdamb436, ocubm, rko, sw620, sw837, t47d` → 排除，目标 **30** 细胞；30/30 均有合法单元；Jaaks 交集 0/30。
4. **Δ 资格（batch1 主口径）**：全部细胞 472,116 单元 Δ / 2,791 上下文（中位 18 成员）；目标 30 细胞 **363,304 单元 Δ / 2,149 上下文**；严格行级 batch1-target **1,453,216**（8,596 上下文）；跨细胞覆盖：12,430 个 `(p,ρ,{a,a'})` 上下文在 batch1 覆盖 33–39 细胞（目标口径 25–30），**全部 ≥3**；每 (cell,partner,role) 可替换对数 min 1 / median 153 / max 666。
5. **技术重复完整性（DG3 触发）**：`viability1` 无缺失；`viability2` 缺 78；`viability3` 缺 198；`viability4` 缺 5,742；行级 4 重复齐全率 **98.44%**（363,090/368,832）；每行可用重复数 `{1:78, 2:120, 3:5,544, 4:363,090}`；完整成员上下文（46,104）中 **99.66%** 满足 ≥95% 网格行有 ≥2 重复（最差 93.75%）。
6. **与既有结构探针的差异**：`data/ONEIL_STRUCTURE.json` 记"4 重复列全部 nonempty（'4': 368832）"；本次 pandas 非空计数显示三列有空白。两者"nonempty"定义不同（探针可能按单元格存在计），**以本次空值计数为准**，并作为 DG3 触发的直接证据记录。
7. **门控结果**：DG1 全 PASS（363,304 / 30 / 2,149 / 12,430）；DG2 PASS（完整率 100%、剂量匹配 100%、数值剂量存在）；**DG3 FAIL（字面）**；DG4 PASS（30/30）；DG5 PASS（0/30）；**DSG1–DSG4 全 PASS**（5 折各 6 细胞；每折单元 71,004–74,580、上下文 427–432；保守 MDE80 0.02204 ≤0.10）。
8. **MDE 先验**：σ_e ∈ {0.041,0.058,0.109} × n_eff ∈ {6,12,24,30}；保守格 0.02204；达到 0.10 所需 n_eff ≤0.291（即 6 个 held-out 细胞足够）。σ_e **借用**，非 O'Neil 实测（见限制）。
9. **单药工作簿**：16,752 行 / 39 细胞 / 38 药 / 118 浓度 / 6 技术重复（header）；**只登记元数据、未读数值**、本任务不用。

## 5. 决定

1. **v1 判定按冻结规则**：DG3 字面门（四列非空计数=行数）FAIL ⇒ `data_unavailable`（failure category `replicates_missing`）；**未事后放宽门槛**、未改口径、未换端点/切分。
2. **不改 v1**：以 `AMENDMENT_ON1-001.md` 形式提出 v1.1 的预注册修订提案（DG3 改为比例阈值 + 执行期缺失值规则）；明确 v1 记录保持，v1.1 未运行，供 Lead 审阅/决定。
3. **批次处理**：主分析 batch1-only；batch2/3 及 batch1∩batch3 重复只作技术一致性敏感性；技术重复≠独立培养如实写死。
4. **细胞/端点边界**：9 重叠细胞排除、目标 30；仅 viability；不与 Jaaks ΔEMAX 拼；不做独立确认/迁移/决策收益/机制/新算法声明。
5. **单药参照**：只登记元数据；若未来用作对照须另立预注册与资格（本任务不读数值、不设计效果）。
6. **报告结论**：资源/设计本身支持开发性细胞留出（单元/覆盖/MDE 均过），唯一阻塞是 v1 字面 DG3 阈值；建议 Lead 决定是否批准 AMENDMENT_ON1-001 后冻结 v1.1；**不运行效果/更新器**。

## 6. 确定性与产物 SHA

- `PYTHONHASHSEED=0`；JSON 键排序、无时间戳、`allow_nan=False`；`on1.py` 从原始文件重算全部数字（未使用侦察结果）。
- 两跑 `on1.json` **逐字节一致**。

| 文件 | SHA256 |
|---|---|
| `PROTOCOL_ON1.md`（v1 FROZEN） | `3C27CB94C68D40D24FCF736F6107AD76FE5C6599A1AFB04DB75D3BBA099E9EEC` |
| `on1.py` | `694AC09ECC2C7474D2094D4CBF56EBE8EE68659E71FA49808C2EA986B8EFF36B` |
| `on1.json` | `2E793902395C1902C80E8C3D936DE0815AF5B023EB42DD94BC8CDB5F776A3412` |
| `AMENDMENT_ON1-001.md` | `E13489B95603B3CA5EE0BD4D08377E3A824195D92DC6BBFB1514F3927A6FD290` |
| `usage_on1.json` | `47800DBE457D37A36413ED165974655AA1F6F801B68345F1A4A05F0CC249823D` |
| `report_on1.md` / `record_on1.md` | 本报告/本记录（SHA 由审计方重算） |

- `on1.json → inputs` 含：组合工作簿 `A0E2E002…C14818`、单药工作簿 `4A0622C0…ED66DEC`、Jaaks Original（仅细胞名列）`1188968C…FFA278`、PROTOCOL_Q0 `D87C004E…A26877`、q0.json `F952CCF3…DA786B`、R199 BRIEF、PROTOCOL_ON1、脚本 SHA。

## 7. 偏离与限制

- **DG3 字面实现**：按冻结文本"非空计数=行数"实现（等式），导致 v1 `data_unavailable`；修订提案见 AMENDMENT_ON1-001（明确标注非门控、不改变 v1 判定）。
- **未运行任何效果/训练/更新器比较**；未读 viability 数值做统计（仅空值计数）；未使用单药工作簿数值。
- **σ_e 借用**（A0/A2 既有估计）未在 O'Neil 实测；well 级跨 plate/batch 独立假设未认证；执行前须重标定。
- **无暴露时间/assay 方法列**；合法暴露只能部分验证（conditional）。
- **技术重复≠独立培养**；3 BatchID 同 lab。
- **端点仅 viability 派生**；无正交功能读数；不得与 Jaaks ΔEMAX 拼端点。
- **不做资源系统综述**；只针对 O'Neil 窄口径。

## 8. 未做 / 明确不做

- 未训练/未拟合/未估效果/未比较更新器/未做 acquisition/Agent/反馈实验；未改 Q0 产物/其它目录/INDEX/SYNTHESIS/git；未联网。
