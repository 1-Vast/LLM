# record_A.md —— R201-A（机制 A 形式化 + O'Neil 资格 + 最小设计）执行记录

角色：独立审计/设计员（未参与 R197/R200 模型开发）· 任务 task-102（R201-A）· 日期 2026-10-28
只写 `research/2026-10-27-agent-cell-colearning/mechanism_A/` 与 `tmp/`；未改其它目录/INDEX/SYNTHESIS/git；未下载；**未训练/未拟合预测/未做效应或迁移统计**；**未读 O'Neil 响应数值**（只读身份/剂量列 + viability 空值掩码）；未读单药工作簿数值；未拼 ΔEMAX。

## 0. 要求与完成对照

| 要求（task-102） | 状态 |
|---|---|
| 1 形式化：计划/共享算子 S/联合矛盾度量/可辨识性/反事实查询/决策选择；2-3 个具体矛盾例子 | ✅ `PROBLEM_A.md` §0–§5（3 个构造例子） |
| 2 本地资格（metadata-only）：O'Neil complete-case 4×4 是否支持跨计划一致性检验；单元/上下文/剂量/缺失/批次限制；ONeil 仅开发性；Jaaks/其它是否独立目标；qualified/qwc/not_qualified | ✅ `qualify_A.py` → `qualify_A.json`；O'Neil=`qualified_with_conditions`；Jaaks=`not_qualified`；决策终点=`evaluation_cannot_distinguish` |
| 3 最小可证伪设计（预注册草案，不执行）：主假设；比较器 C0–C9；等信息等预算；主终点 top-k/选择/后悔；MDE/δ_min 或 evaluation_cannot_distinguish；零模型；失败类别；停止条件 | ✅ `DESIGN_A.md`（P0/P1/P2/S1/S2；δ_min=0.05；MDE 数字；零模型；停止条件） |
| 4 边界：开发性；不称新颖性/机制/迁移/决策收益；不重复 D1 stop/D3 design_invalid/A1 data_unavailable；不拼 ΔEMAX；不运行效果 | ✅ `PROBLEM_A.md §0/§8`、`DESIGN_A.md §0/§10`、报告 §5 |
| 完成后标 completed + send_message（形式化/例子/资格/设计/缺口/挑战建议） | ✅ |

## 1. 时间线（Asia/Shanghai，2026-10-28）

| 时间 | 事件 |
|---|---|
| ~00:13 | 读 task-102 并 claim；读 R201 BRIEF、agent-cell-colearning/report.md、candidates_v3、ON1/ON2/ON3 限制、PEEK_DISCLOSURE_ON3、D3 停止结论、SYNTHESIS C186–C190 |
| ~00:20 | **`PROBLEM_A.md` 冻结**（形式化/例子/边界；`qualify_A.py` 尚不存在） |
| ~00:22–00:26 | `qualify_A.py` 首版→修正（见 §2）；成功运行 wall **137.5 s**，`qualify_A.json` SHA `D1DD2706…8457C2D4` |
| ~00:27 | 启动同脚本第二次运行（确定性校验，后台 `tmp/qualify_A_run2_stdout.txt`）→ 两次 `qualify_A.json` 逐字节一致（两次运行 `qualify_A.json` 逐字节一致（`d1dd270629ef6449f08bc381d080155dfffc5cc562290929bdc5458f8457c2d4`；run1 wall 137.5 s、run2 wall 136.4 s；差异仅来自机器负载，产物无差异）） |
| ~00:30 | `DESIGN_A.md` / `report_A.md` / `record_A.md` / `usage_A.json` 完成；标 completed + send_message |

## 2. 实现、bug 与偏离（全部披露）

1. **文件格式/读取偏离（已修）**：O'Neil combination workbook 实为 OOXML（PK zip）但扩展名 `.xls`；`openpyxl.load_workbook(path)` 按扩展名拒绝。改为`open(PATH,'rb')` 文件对象 + `pd.read_excel(fh, sheet_name='combination response', engine='openpyxl')`（44.2 s，368,832×13）。
2. **bug（修复，无产物）**：openpyxl read_only 行迭代在**空单元格**处会省略/移位列 → 首版把缺失 viability 误判为全部非空（pair-cell 全部 16 行、batch3 也"完整"）。pandas 读取后空值→NaN，标定复算与 ON2 完全一致：complete-case 363,090（98.44%）、6 个披露门全部 `true`、pair-cell 桶 22,035/702/315。
3. **bug（修复，无产物）**：`n_required` 字典用 `str(0.10)='0.1'` 作键导致 `KeyError '0.10'`；改为显式 `'0.05'/'0.10'`。
4. **口径修正（非 bug）**：完整 4×4 网格 pair-cells 需分全批与 batch1：全批 **22,035**、batch1 **21,726**（batch1 有 684 个 15 行 pair-cell；ON2 的 22,035 是全批口径）。JSON 两数都记录，报告注明。
5. **数据读取边界**：只读 `BatchID/cell_line/drugA_name/drugA Conc/drugB_name/drugB Conc/combination_name` 与 viability1–4 的**空值掩码**；未计算任何响应均值/方差/相关；`mu/muMax`、`X/X0` 未用于统计。单药工作簿仅登记元数据（1.68 MB、16,752 行/39 细胞/38 药，来自 ON1 记录；不读数值）。
6. **无统计偏离**：所有资格数字为结构/计数/设计矩阵秩；算子一致性审计只做 0/1 设计矩阵 rank，不拟合任何预测。
7. **peek/non-blind**：ON3 QUICK invalid artifact 已见（`PEEK_DISCLOSURE_ON3`），本方向所有设计/执行均 non-blind/peeked；报告不称盲验/独立确认。

## 3. 运行事实

| 运行 | 目的 | wall | 结果 SHA256 |
|---|---|---|---|
| 1 | 首次成功（pandas 读取 + 结构/秩审计） | **137.5 s** | `D1DD270629EF6449F08BC381D080155DFFFC5CC562290929BDC5458F8457C2D4` |
| 2 | 确定性复核（同脚本同输入） | 136.4 s | `D1DD270629EF6449F08BC381D080155DFFFC5CC562290929BDC5458F8457C2D4`（与 run1 相同） |

单命令 ≤15 min 预算 ✓；JSON 键排序/无时间戳/allow_nan=False；输入 SHA 全部写入 JSON。

## 4. 关键结果（与报告一致）

- **O'Neil 结构**：368,832 行/39 细胞/38 药/583 无序药对；batch1 358,560、batch2 5,232、batch3 5,040；complete-case **363,090（98.44%）**（缺失 0/78/198/5,742）；pair-cell 桶 **16 行=22,035 / 15 行=702 / 0 行=315**（与 ON2 逐项一致）。
- **跨计划支持**：完整 4×4 网格 pair-cells 全批 22,035（batch1 21,726）；39/39 细胞有完整网格；每细胞 pair-cells 中位 565；drug-role 上下文 2,879（≥2 上下文 2,791，剂量集对齐 2,791）；共享剂量水平 11,164；**计划对（同成员/角色+≥2 共同剂量）441,867**（每细胞中位 11,623）。
- **可辨识性（加性算子）**：每细胞设计 rank 中位 295、**过识别度中位 8,745**；39/39 细胞 ≥1、≥16；target30 30/30。
- **Jaaks**：296,707 行/125 细胞/1,294 对/70,360 键；每键剂量对最多 **4**（无完整 4×4 网格）；端点 ΔEMAX → `not_qualified`（`no_operational_target`+`data_insufficient`），不拼接。
- **判定**：O'Neil `qualified_with_conditions`（8 条条件，含开发性/技术重复/batch3/702 行/无双药参照/non-blind/决策不可认证）；决策收益 `evaluation_cannot_distinguish`：rank MDE80=**0.7625**、top-k 0.33–0.36、regret 0.10–0.26 >δ_min=0.05；决策认证需 **≈6,283 独立细胞（δ=0.05）/≈1,573（δ=0.10）**。
- **设计**：H_A（联合矛盾存在 + 界收紧）+ H_A2（等预算下 active 计划差选择）；比较器 C0–C9；P0/P1/P2/S1/S2；等信息/预算 cap（≤256 wells/arm/折、≤2 CPU-h/arm、≤20 配置、5 折×6 细胞）；零模型 5 类；失败类别/停止条件写死；S1 仅描述性。

## 5. 产物与哈希

| 文件 | SHA256 |
|---|---|
| `PROBLEM_A.md` | `dfb2dce81d59e2826ed5d5fb2beee6b8b7f0bdca54444f488fec80fbe0c84570` |
| `qualify_A.py` | `fbb9d3cf83b8a2167bcdc6eb40e9eb16872f9af37057cc820b42783c53cd113b` |
| `qualify_A.json` | `D1DD270629EF6449F08BC381D080155DFFFC5CC562290929BDC5458F8457C2D4` |
| `DESIGN_A.md` / `report_A.md` / `record_A.md` | 见 `usage_A.json` |
| 只读引用（未改） | O'Neil workbook（SHA 见 JSON inputs）、`on1.json`、`PEEK_DISCLOSURE_ON3.md`、`on3_exec.json`、Jaaks fitted（SHA 见 JSON） |

## 6. 缺口（本轮明确未做）

- 未读响应值：J/ΔW 的实际计算属**执行阶段**，本轮只给形式定义、δ_J=τ 预注册规则与结构可行性（过识别/计划对支持）。
- 未做决策功效认证：30 细胞 MDE 已算 → `evaluation_cannot_distinguish`；需外部独立细胞（≈6,283/≈1,573）。
- P-program（顺序/时点）本地无资源；单药参照未资格化；迁移/机制资源不存在。
- 未执行任何效果/算法比较；设计须经独立挑战 + Lead 批准后才可执行。
