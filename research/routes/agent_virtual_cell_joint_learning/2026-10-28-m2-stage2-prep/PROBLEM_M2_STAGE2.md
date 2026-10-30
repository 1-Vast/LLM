# PROBLEM_M2_STAGE2 —— R204-M2 Stage2/3 数据就绪门与设计草案（不运行效果）

2026-10-28。对象：R204-M2（D1/M2 首选主线）Stage2/3。依据：M2 v0.2 预注册链、C206 Stage1 PASS（`research/2026-10-28-m2-stage1/`）、Lead `DECISION_R204_M2_STAGE1.md`、R204 DATA1（C205）、ERRATA C197/C199/C201/C203/C205、R203-P1 链。
**状态：设计准备草案；Stage2/3 未执行；未读真实响应/功能数据；未运行方法比较/未报告效果；当前数据 `data_unavailable`；机制账 only；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定；0 wells。Stage2/3 执行须另立预注册 + 独立挑战 + Lead 批准 + 合格数据。**

## 0. 前置核验（已通过）

`stage2_plan.py` 本地只读核验 15 个冻结链文件 SHA：M2 v0.2（PROBLEM `25BC2663…`、DESIGN `5891858E…`、formalism py `DE3C29A9…`、JSON `A99D31B1…`、schema `3CC31B62…`）、Lead Stage1 决定（`7C01D9C6…`）、Stage1/C206（m2_stage1.json `3D7DA102…`、rows `AA7CBF28…`、diagnostics `0EA73141…`、report `9EC6416A…`、record `8909C1CE…`、usage `B6C24226…`、timing `163C9B78…`）、DATA1 report `117B3C13…`/request spec `D9A36585…`；**mismatches=0、chain_pass=true**；Stage1 `failed_checks=[]`、`no_effect_results=true`、full K 75/75、same-U 3/3 → **Stage1 PASS 已核实**。任一不匹配 → stop `design_invalid: chain_mismatch`（执行时重核）。

## 1. 数据就绪门（Stage2 前；当前未通过）

### 1.1 合格数据合同（全部满足才允许 Stage2 执行）

| # | 合同项 | 要求 |
|---|---|---|
| D1 | 多时间功能/群体快照 | 同一培养物/cohort 的多时点功能读数 + 群体快照（不是单时点 RNA） |
| D2 | 可交换性 | 同培养物/背景/批次（source/handling/batch）可交换；不伪配同细胞轨迹 |
| D3 | 剂量/时间/function readout | 合法动作的剂量/时间/function 读数齐全，且与动作标签对齐 |
| D4 | 记录 π 与动作标签 | 随机化分配 π 先于结果记录；动作标签完整、不聚合 |
| D5 | 独立培养/板重复 | 独立培养/板（技术三重复≠独立培养；不当独立单位） |
| D6 | 正交功能 | 声称的功能需 apoptosis/caspase/靶点参与/regrowth 等正交读数；未取得前不得声称 |
| D7 | 计数 + RNA | 增殖/死亡绝对计数与 RNA 并存；归一化 RNA 不能单独区分数量变化 |

### 1.2 当前状态：**`data_unavailable`**

- 当前 AZ/GDSC 2024 公开 listing **缺**：`BARCODE/cmatrix/CELL_ID → experiment/occasion/technical replicate/treatment date/passage/culture` 映射；7 系×6 实验×3 技术重复官方映射/对账；Fig 4E/F、5C/D、6C–E 的 caspase/PARP/western **numeric 源数据**；72 h/CellTiter-Glo/Caspase-Glo/QVD 协议-键映射；Figshare dataset README/数据字典（C203/C205；DATA1 结论 `partial`，missing ≠ 作者未做）。
- **Stage2 执行不允许**；**不得**用合成数据/RNA 提分/预测/算子误差替代独立功能决策；不得由导出缺失推断"只能新湿实验"。

### 1.3 获取/重导清单（引用 request spec，不伪造联系人）

依据 `research/2026-10-28-az-data-acquisition/requests/data_request_spec.json`（`D9A36585…`）与 `report_data1.md`（`117B3C13…`）：

1. **P0 数据字典/映射**：经出版方对应作者/Figshare 公开联系渠道请求 BARCODE/cmatrix/`CELL_ID → experiment/occasion/technical replicate/treatment date/passage/culture` 映射；不伪造邮箱、不绕过登录/许可。
2. **P1 功能 numeric**：请求 Fig 4E/F、5C/D、6C–E 的 caspase/PARP/western numeric 源表；未取得前不声称正交功能。
3. **P2 协议映射**：请求 72 h/CellTiter-Glo/Caspase-Glo/QVD 的逐批/逐键协议映射。
4. **重导/再生成**：在公开 BARCODE/SCAN_ID/DRUGSET_ID/cmatrix 上重导独立培养/板/批次标签；技术三重复不得当独立培养；与 301 exact-18/161 6×3 单元对账。
5. **门通过后**：登记数据 SHA、交换性/平衡诊断、预先注册响应/功能角色；数据角色冻结后方可 Stage2。**本轮不发起请求、不读数据。**

## 2. Stage2 设计（固定反馈比较学习；不执行）

- **候选**：M2 任务驱动群体功能算子（小 φ 族/state-action 依赖 K_a）。
- **基线**（同信息/同预算/同调参/同预训练）：**full-history retrain、hierarchical GP、KoopCell/DisKO 适配、TD-JEPA/后继特征适配、state-space/PKPD、full retrain from scratch**；每基线输入/信息集/超参预算/训练-更新流程/等预算审计见 DESIGN。
- **协议**：相同固定反馈流（所有方法看到同一 queried actions/feedback；学习比较，不做 acquisition 优势）；先留出**程序**、再留出**背景**；新功能所有方法同标定；只换已观测功能权重=**有限任务重组**，不是零样本迁移。
- **主端点**：独立功能下的实际决策效用/后悔；δ=**0.05 normalized**；headroom=U_max−U0 先检（<δ→`unreachable_gate`；近满分→另立 budget-to-target，不换端点）；配对 MDE=2.801585·SD/√n_eff；cluster CI 按培养物/背景/任务；**6,282 仅 Fisher-z 参考、非通用门**。
- **次端点**：预测校准、算子/K_a 误差、RNA 误差（不得替代主端点）。

## 3. Stage3 设计（固定更新器比较取证；不执行）

- **固定更新器**：所有 selector 共用同一 learner/updater；**实验选择与学习器分开**。
- **selector**：候选 M2 主动干预选择 vs **random、GP acquisition、最优输入设计（受控弱 EDMD/系统辨识）、BATCHIE 适配**。
- **同成本/合法实验包**：相同 cohorts/plates/doses/timepoints/controls/feedback rounds；完整闭环计培养物/板/对照/失败/重复/标定/计算/调参。
- **防选择性**：候选集/轮次预先注册；先留出程序再背景；所有 selector 同菜单/同成本包；不得用目标结果事后调 selector。
- **主/次端点**同 Stage2；Stage3 仅在 Stage2 PASS + 合格数据 + 另立批准后启动。

## 4. 失败类别/停止/预算

- **失败类别**：`design_invalid: identifiability|randomization|closure|leakage|compute_budget_exceeded|rename_edmd`、`data_unavailable`、`unreachable_gate`、`precision_insufficient`、`no_increment`、`inconclusive`。
- **停止**：数据门失败→`data_unavailable`（当前）；等预算标准方法复制/超过→撤主算法（`no_increment`/`rename_edmd`）；闭合/随机化/测量合同失败→stop；仅 RNA/预测/算子误差收益→撤；反馈/实验成本超冻结上限→stop；CI 无法排除无实用收益→`inconclusive`；跨任务失败→限当前任务；不得换端点/降 δ。
- **预算**：Stage2 compute wall≤1800 s/CPU≤2 h/内存≤8 GB（data-only，0 wells）；Stage3 wall≤1800 s/CPU≤2 h/内存≤8 GB（实验成本进闭环账，不执行）；当前仅设计/骨架/单测/计时，compute-only、0 wells。

## 5. 边界

机制账 only；Stage2/3 **不执行**；不读真实响应/功能数据；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定/门槛；不恢复停止实验；**Stage2/3 执行须另立预注册 + 独立挑战 + Lead 批准 + 合格数据**；不批代码晋升/真实数据/湿实验。
