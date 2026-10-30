# R201-A-C1 独立挑战（challenge_A.md）

2026-10-28 · 挑战者：endpoint-auditor（与 ON1/ON2/ON3/D1/D3/D5 同一独立挑战者；未参与 R201-A）· 对象：`research/2026-10-27-agent-cell-colearning/mechanism_A/{PROBLEM_A.md, qualify_A.py, qualify_A.json, DESIGN_A.md, report_A.md, record_A.md, usage_A.json}`。
方式：**只读复核**（形式化/资格数字/设计/预算/边界；**不运行效果、不拟合、不读 O'Neil 响应值做统计**）；只写本文件与 `tmp/`。
完整性：`PROBLEM_A.md` `DFB2DCE8…`；`qualify_A.py` `FBB9D3CF…`；`qualify_A.json` `D1DD2706…`；`DESIGN_A.md` `D1D02A4B…`；`report_A.md` `D5B652AD…`；`record_A.md` `94BC53A2…`；`usage_A.json` `488F7AC3…`——均与磁盘实算一致。

## 0. 总判决

**approve_to_lead_mvp（仅 P0/P1 最小实验；不 approve P2/S2/H_A2）。**
R201-A 的**形式化骨架、资格数字/过识别解释、qwc 条件、决策不可认证与所需独立细胞数、C0–C9 与等信息/等预算、P0/P1 主终点、零模型/停止条件、边界**基本成立；**P0/P1 可在 Lead 批准前补下列 5 条细节后进入**，但 **P2/S2/H_A2 暂不批准**（需 P1 后另立预注册）。
**不是 stop**：P0/P1 的形式/存在性问题是可验证的，资源结构支持；**不是无保留 approve**：仍有 3 个形式/统计细节必须先冻结。

**最致命 3 条（均为 P0/P1 前置条件）**

1. **例 3（秩 1 交互矛盾）不是可复核的具体例子**：PROBLEM_A §5 只写“构造使 p1 需要 u(d2)/u(d1)=1、p2 需要=2”，没有给出 p1/p2 的观测/设计/参数化与 J>0 的显式演算；例 1/2 有显式数字（例 2 的 1+5=2+4、f_a 差 2 vs 3），例 3 目前是**纸面叙述**。任务 ① 要求 3 个例子数学正确/可示范；需补显式观测或明确标记“仅示意、不计入形式证据”。
2. **P2/ΔW 在 `V_pq` 为空时未定义**：`V_{pq}=V_p∩V_q` 可能为空（正是 P1 的“联合不可行”）；此时 `W(V_{pq})` 无定义，`ΔW` 无法计算。P1 与 P2 的适用关系、P2 是仅取 **V_pq 非空** 的计划对，还是对空集赋 ∞/单独规则，必须写死；否则 H_A 的 (iii)/P2 不可执行。
3. **P1 的存在性阈值未含多重性/FPR 的精确统计**：`≥5 cells 各≥1 个 J≥δ_J` + `pooled 比例≥1%` 在 441,867 个计划对/39 细胞上仍可能被 **计划对选择/技术噪声**放大；零模型有 5 类，但没有写死 **P1 的精确统计量、FPR/族错误控制、随机计划对/半拆分阈值对应关系**。P1 是 primary，需在 P0 后、P1 前冻结一个可复算的 **per-cell/pooled 零分布门**（不得看结果改阈值）。

## 1. 逐条确认

### ① 形式化 —— **PASS 主体；例 3 WEAK**

- 计划 p（P-dose/P-replace/P-program）、S（`f_{a,role}`+伙伴函数+交互核 h+角色分层+噪声）、`J=ε_pq−max(ε_p,ε_q)`、证书 θ*、可辨识条件（重叠/角色/gauge/over-id≥1/非矩形/τ）、`V(p*)`、`R(p)=max_q h_V(c_q−c_p)`、一次反馈统一修订、双预算——**定义自洽，PASS**。
- **例 1**：µ=(1/2,1/2)，A(p)=[[1−p,p],[p,1−p]]，B 制备第一状态；BA=p、BAA=2p(1−p)；取 BA=0（p=0）与 BAA=1/2（p=1/2）分别合法，联合同 p 不可能。**正确**。
- **例 2**：p1 `(1,2;3,4)` 加性一致 1+4=2+3=5，f_a 差 2；p2 `(1,2;4,5)` 一致 1+5=2+4=6，f_a 差 3；单独精确、联合不允许同一 f_a；**正确**。
- **例 3 WEAK**：秩 1 交互的“同一 f_a/u”约束方向对，但无显式 p1/p2 观测/参数值/J 演算；需补成可复核例子（或明确仅示意）。**WEAK/必须补**。

### ② 资格 —— **PASS**

- O'Neil 数字与 ON2 一致：**368,832 行 / 363,090 complete-case（98.44%）**；batch1 357,876、batch2 5,214、batch3 0；**pair-cell 16 行=22,035（全批）/21,726（batch1）；15 行=702；0 行=315**；39 cells/38 drugs；**drug-role 上下文 2,879（≥2 =2,791，剂量集对齐 2,791）**；**shared dose 11,164**；**plan pairs 441,867**；**每细胞 rank 中位 295、over-id 中位 8,745**；**39/39、target30 30/30**。**PASS**。
- **过识别解释**正确：`over=#obs−rank`（9,040−295=8,745）；**是结构可检验性，不是效果**；**PASS**。
- **qwc 8 条件**：complete-case/batch2 disclosure/batch3 lost/702 excluded/no dual reference/non-blind/over-id≥1/decision cannot distinguish；**充分/保守**；**PASS**。
- **Jaaks**：ΔEMAX 端点、每键剂量对最多 4、无可比 4×4 网格 → **not_qualified，不拼接**；**PASS**。
- **决策终点**：30 cells → rank MDE **0.7625**、top-k **0.33–0.36**、regret **0.10–0.26** 均 >δ_min=.05 → `evaluation_cannot_distinguish`；**≈6,282（δ=.05）/≈1,573（δ=.10）独立细胞**；**正确/诚实**；**PASS**。

### ③ 设计 —— **PASS 主体；P1/P2/H_A2 需冻结**

- **H_A**（J≥δ_J=τ + ΔW≥δ_W=.05）**可证伪**；**H_A2**（等 wells+计算预算更少 wells 达同等界/决策目标）**方向可证伪**，但**“同等界/决策目标”与“更少 wells”的等价界/差值阈值未写死**；**P2 与空 V_pq** 见致命 2；**P1 阈值**见致命 3。
- **C0–C9**：mean / 同信息全局求解 / 共享参数后验 / 约束生成 / 全历史重训 / 层级 / GP / 决策 AL / 随机计划对 / 静态最佳预测+优化；**防选择性**（C8 随机、C1 全局、C7 最强竞争），**PASS**。
- **等信息/等预算**：≤256 wells/arm/fold、≤2 CPU-h/arm、≤20 配置、5 折×6 细胞、同 mask、求解/证书/重认证计费；**PASS（可核查）**。
- **P0→P1→P2**：P0 覆盖/可识别/噪声；P1 存在性；P2 界收紧；S1 仅描述性；S2 算法/预算；**PASS 主体**；P2 需空集规则。
- **零模型**：计划内置换、算子打乱、随机选择、技术半拆 FPR、无约束对照；**PASS（但 P1 精确 FPR 见致命 3）**。
- **失败/停止**：`data_unavailable`/`design_invalid`/`evaluation_cannot_distinguish`/`no_joint_contradiction`/`no_increment`/`no_decision_benefit`；**P1 不达→no_joint**；强基线等效→撤算法；只改已测→停反馈迁移；决策不变→停决策；**PASS**。

### ④ 边界/先例 —— **PASS**

- 开发性；不称新颖性/机制/迁移/决策收益；CoMap/LAWM/MDA/COPEx 仅背景；不重复 D1/D3/A1；不拼 ΔEMAX；non-blind/peeked 继承；P-program 本地不存在；单药参照需另立资格；功能/决策需新测量；**PASS**。

## 2. 必改（≤5；P0/P1 前）

1. **例 3 显式化**：给出 p1/p2 的具体观测/设计矩阵、同一 f_a/u 参数化、J 的显式值；或明确标记“仅示意、不作为形式证据”。任务 ① 要求 3 个数学正确/可示范例子；当前 1/2 可核，3 仅是叙述。
2. **定义 P2/ΔW 的空集规则**：`V_pq=∅` 时 `ΔW` 无定义；需写死 P2 仅取 `V_pq≠∅` 的计划对（空集归 P1），或给 `W(∅)` 的约定；并明确 P1/P2 是同一计划对过滤器的两个条件，还是两个独立子集。
3. **冻结 P1 精确统计/FPR**：P1 primary 的 `≥5 cells/≥1%` 需配一个可复算的 per-cell/pooled null 门（计划内置换 + 算子打乱 + 技术半拆 FPR）；写死统计量、α/族错误、seed、是否对 441,867 对做选择校正；不得看结果改阈值。
4. **H_A2/S2 目标写死**：定义“同等界/决策目标”的数值阈值、wells 差值的最小有意义差、允许的等价界（non-inferiority margin）；否则 H_A2 的“更少 wells”不可证伪；S2 仅描述性。
5. **P0/P1 执行细节**：y 聚合（mean viability；执行期二选一冻结）、τ/σ_pair 噪声标定、over-id/plan-pair 计数口径、整 pair-cell/剂量行留出、折清单、两跑/schema、失败模板、G5 断言、P0/P1 budget（P0/P1 只用已有数据；无新 wells 时说明）。P0/P1 执行前另立协议；本轮不执行。

## 3. Lead 批准 P0/P1 的条款（建议）

> **批准 R201-A 仅进入 P0/P1 最小实验（开发性形式/存在性；不进入 P2/S2/H_A2）。**
> 冻结：PROBLEM_A `DFB2DCE8…`（补例 3 后重算 SHA）、qualify_A `D1DD2706…`、DESIGN_A `D1D02A4B…`（P1/P2 修正后重算）、C0–C9、P0/P1 门、等信息/预算、零模型、失败/停止。
> **P0**：覆盖/过识别/噪声；**P1**：单独合法 + `J≥δ_J=τ` 的计划对存在性；**P2/S1/S2 不执行**（P2/S2 另立预注册；S1 仅描述性，若未来跑也 `evaluation_cannot_distinguish`）。
> **P0/P1 不做**：决策/迁移/机制/新颖性；不拼 ΔEMAX；不读单药工作簿数值；技术重复≠独立培养；non-blind/peeked。
> **P1 结果解释**：只写“本资源/本族下存在联合矛盾”的开发性存在性；不写结构成立/生物机制/迁移/决策；P1 不达 → `no_joint_contradiction`，不写“矛盾不存在”。
> **预算**：P0/P1 用已有 O'Neil 数据/结构，不新增 wells；若执行需要任何新测量，另立协议；计算 cap/两跑/schema 先冻结。

## 4. 复核证据与本轮边界

- 实际 SHA 见页首；资格数字与 report/record/JSON 一致；例 1/2 数学正确；例 3 无显式演算；P2/ΔW 空集未定义；P1 阈值/ FPR 未精确冻结。
- **本轮未运行效果/未拟合/未读 O'Neil 响应值做统计**；只读文档/JSON/SHA/结构；只写本文件与 `tmp/`。
- **approve_to_lead_mvp（仅 P0/P1）**；P2/S2/H_A2 未批准；不称新颖性/机制/迁移/决策/生物学；阴性≠不存在；冻结≠资源足够/关系成立/Stage1/效果。
