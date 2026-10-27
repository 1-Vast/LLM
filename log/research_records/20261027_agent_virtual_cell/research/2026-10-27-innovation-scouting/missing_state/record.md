# record —— R198-A4 执行记录（设计+先例+可用性核查；不运行效果）

2026-10-27 · 角色：机制探索（A4）设计者 · 工作目录 `D:\MAESTRO` · 只新增 `research/2026-10-27-innovation-scouting/missing_state/` 与本任务 `tmp/` 侦察文件；未改 A0/A1/A2/Q/A3 产物、其它目录、INDEX、SYNTHESIS、git、源数据。

## 1. 时间线

| 步骤 | 内容 | 结果 |
|---|---|---|
| 读任务 | `team_task_get(task-27)` 读取完整任务；确认交付物与禁项 | 已 claim（revision 2） |
| 读必读材料 | `cross-domain-directions/{report.md,evidence_notes.md,latest_audit.md}`、`cellstate-qualification/{report.md,prior_art.md}`、`SYNTHESIS.md`（C159/C160/C174 相关段）、`ERRATA_Q2.md`、`ERRATA_A3.md`、R196/R197 BRIEF、INDEX/HANDOFF 最新段 | 见 §3 证据清单 |
| 先例核验 | One-Hot News（identity shortcut/LDO/LCO）、BATCHIE（cell embedding×drug-dose/plate/QC/PDBAL）、PDTSyn（共享+条件分解）、细胞状态特征近邻、DECANT/State/虚拟细胞基准 | 写入 [prior_art.md](prior_art.md) |
| 本机可用性核查 | 只读元数据侦察：Jaaks/DepMap/DrugComb v1.5/BeatAML/Mix-seq/PRISM/BATCHIE 原始表/LINCS/Tahoe；脚本 `tmp/inventory_missing_state.py` → `tmp/a4_inventory.json` | 覆盖与"可立即检验/需新增/不可检验"清单写入 [spec.md](spec.md) §3 |
| 设计 | 三类失败 operational 定义、Sig-A/B/C、判决表、SCC 机制候选、最小实验 | [spec.md](spec.md)、[protocol_draft.md](protocol_draft.md) |
| 边界 | 无效果运行；无训练/拟合；无响应值统计；无新颖性声称 | 本记录 §4 |

## 2. 运行与命令（可复现）

```powershell
# 只读元数据侦察（不使用响应列；BATCHIE 的 Viability/Raw count 显式排除）
& D:\anaconda\envs\maestro\python.exe D:\MAESTRO\tmp\inventory_missing_state.py
# 输出：tmp/a4_inventory.json（metadata-only 覆盖计数）
```

- 环境：Windows / `D:\anaconda\envs\maestro\python.exe`（Python 3.11.16，pandas 2.3.3，numpy 2.4.6）。
- 运行时间：侦察脚本 < 2 min（主要是几个大文件表头/元数据读取；未扫描响应）。
- 本轮**未**运行任何模型/效果/训练/估计脚本；`protocol_draft.md` 为 DRAFT，不产生结果。

## 3. 关键发现（设计层）

1. **"状态表示"不是空白**：One-Hot News（identity shortcut、LCO/LDO、细胞特征≈标识符）、BATCHIE（cell line embedding×drug-dose、plate/QC、后验更新、PDBAL）、PDTSyn（共享+细胞条件分解）、Tahoe LOCO（context-specific residual 预测不了）、DIPx/Regulon/SynVerse/Baptista（表达/通路特征冷启动受限）均已覆盖。**本任务不得把"加状态表示/换 embedding/换分解"当新颖性**（prior_art.md §0/§1.4）。
2. **本任务对象 = 诊断路由 + 测量动作**：冲突残差 → 已知协变量/状态/噪声三分；把"补测状态"作为与"修订关系/重标定"并列的动作；用决策相关指标验收。直接先例**未发现**（检索结果，不是空白证明）；相邻压力（不确定性基线、batch effect、无混杂敏感性、OOD 基准）已列出（prior_art.md §1.5）。
3. **本地状态变量覆盖**（实测，spec.md §3）：Jaaks 125 细胞 → DepMap 映射 125/125、表达 111/125、突变 124/125；DepMap 表达 1,249×19,144、突变 1,666 细胞、sample_info 1,756 细胞（culture_type 749、medium 768、site 1,755 等）；Jaaks 培养代理 DAY1/GR/DT 97.7% 行、barcode 3,106（无日期）；DrugComb v1.5 组织 2,313 细胞/34 水平、depmap 表达交集 1,055、与 Jaaks 仅 49 共享细胞（A3）；BeatAML 942 临床行/707 表达/时间字段 942（单药）；Mix-seq 6h/24h 285 键（5 药物含对照、单药；无组合）；PRISM 588 细胞/24 组织但单药端点；BATCHIE 原始表 19 细胞/372 板/20 iterations（metadata；本地 `data/external/batchie_zenodo_13871987` 为空）；LINCS 473,647 sigs/76 细胞/12 时间点；Tahoe 50 个 h5ad block + 元数据。
4. **功效边界必须随设计一起读**：A0 within-pair MDE80=**0.240**>δ=0.05、111 表达细胞、两侧靶点覆盖仅 57.3%；A1 `inconclusive`（MDE80_obs 0.2042>δ_min_obs 0.0893；n_eff≈189）；A3 跨 study 大规模 `not_qualified`（41 共享细胞/4,179 单元；ERRATA_A3 限定"只对冻结的大规模门槛"）。因此"可立即检验"只能做预注册**诊断/描述**，很可能得到 `inconclusive_power`，不得把阴性写成 F3 不存在或表征无信息。
5. **"可立即检验/需新增测量/不可检验"清单已冻结**（spec.md §3.3）：立即=flip 率/噪声地板/已知协变量对照（Jaaks O/V + 96 细胞 + 92,039 四元组）、状态距离—残差描述、训练状态代理关联、Mix-seq 时间描述、BeatAML 单药状态关联；新增=独立批次/日期/培养重复、per-measurement 培养状态、同一 (细胞,组合) 时间序列、同批配对状态读数、跨 screen 规模复验（A3 规格）；不可检验=体内/微环境/免疫/PK、靶点占据/通路因果、克隆/谱系/细胞周期状态、F3 的因果结论。

## 4. 纪律与边界（本轮）

- **不运行效果**：未训练/未拟合模型、未估 Q、未算响应统计、未启动 B/C/acquisition/RSI、未做湿实验。
- **metadata-only**：侦察只读元数据/列名/计数；BATCHIE 原始表的 `Viability`/`Raw count` 列**排除读取**（脚本显式排除）；未使用任何响应值。
- **不改旧产物**：A0/A1/A2/Q/A3 的协议/结果/记录只读；未改 INDEX/SYNTHESIS/HANDOFF/git/其它目录。
- **不声称新颖性**：见 prior_art.md 与 spec.md §0；`未发现` 只作检索结果；候选是否构成差异由 Lead/独立挑战裁定。
- **证据状态**：本记录引用的数字分三类——本任务实测（inventory）、读项目文件（报告事实）、先例（full-text/P/abstract-only 按 prior_art.md 标注）；未把 `P`/摘要级当全文级。

## 5. 本轮产物

| 文件 | 用途 |
|---|---|
| `spec.md` | 三类失败 operational 定义、Sig-A/B/C、判决表、本地可用性清单、SCC 机制候选+最小实验 |
| `prior_art.md` | 先例逐条覆盖（One-Hot News/BATCHIE/PDTSyn/状态特征近邻/DE/State/虚拟细胞基准）、相邻压力、检索缺口、不声称新颖性 |
| `protocol_draft.md` | 若执行的冻结草案：数据/K/S 变量集/统计量/δ_min=0.10/MDE 门/对照/泄漏防护/Phase 1–2/停止条件（DRAFT 未冻结未运行） |
| `record.md` | 本记录 |
| `usage.json` | 运行/环境/读取/预算账（token 与费用 null；未运行效果） |

## 6. 缺口与下一步（写给 Lead）

1. **直接先例的系统检索缺口**：未查 Google Scholar/Scopus/WoS、未做引文回溯；One-Hot 补充表 S7–S12 与 BATCHIE 补充材料未逐页核；"missing state/unmeasured covariate"术语可能漏检 → 若 Lead 要升级为正式方向，应先做一次有界先例补查（含 DECANT/State 全文获取尝试）。
2. **Phase 0 的执行前提**：需冻结 `PROTOCOL_A4.md`、独立挑战者审 δ_min/MDE/变量集/切分、确认 A0/A1 边界口径；预计 Phase 0 很可能 `inconclusive_power`（A0/A1 已示），这本身是可接受结果。
3. **Phase 1 的真实测量**：需另立实验预算/采购/（如涉及）伦理；当前设计仅给最小可买规模（2–4 细胞系 × 2 状态 × 6 条件 × 2 批 × 2 重复）。
4. **与主线顺序**：A4 依赖 A1 冲突信号与 A2 逻辑约束先有可冻结定义；若 A1 仍未 `qualified`，A4 Phase 0 只能做**诊断/描述**，不得升级为决策主张。
