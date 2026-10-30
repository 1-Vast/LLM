# record_A_v0_2.md —— R201-A.1（P0/P1 预注册冻结）执行记录

角色：独立审计/设计修订员（未参与 R197/R200 模型开发）· 任务 task-112（R201-A.1）· 日期 2026-10-28
只写 `research/2026-10-27-agent-cell-colearning/mechanism_A/` 与 `tmp/`；**未改 v0.1 文件**（PROBLEM_A/DESIGN_A/qualify_A.py/qualify_A.json/report_A/record_A/usage_A 均未动）；未改其它目录/INDEX/SYNTHESIS/git；未下载；未训练/未拟合预测/未做效应或迁移统计；**未读 O'Neil 响应数值**（只读身份/剂量列 + viability 空值掩码）；未读单药工作簿数值；未拼 ΔEMAX。

## 0. 要求与完成对照（challenge_A 5 必改）

| 要求 | 状态 |
|---|---|
| 1 例 3 显式化或标仅供示意并替换/剔除 | ✅ `PROBLEM_A_v0_2.md §3`：原秩 1 叙述作废（仅示意）；新增显式 E3（role-agnostic 示例，含观测/约束/J_SSE=1.0/RMS=0.5）；形式证据 = E1+E2 |
| 2 P2/ΔW 空集规则 | ✅ `PROBLEM_A_v0_2.md §4`：`V_pq=∅`、`W(∅)=+∞`/sentinel、ΔW 仅非空对、P1/P2 适用关系；P2 不执行 |
| 3 P1 精确统计/FPR/多重性 | ✅ `PROBLEM_A_v0_2.md §5` + `DESIGN_A_v0_2.md §3`：|U|=340,088、F_pair、F_crit=2.60、per-cell max、N_perm=500/seed 20261029、BH q=0.05、三条件阳性、半拆/算子打乱门、pair 计数仅描述性 |
| 4 H_A2/S2 数值目标 | ✅ `PROBLEM_A_v0_2.md §6`：W*=0.05、R*=0.05、δ_noninf=0.01、wells 差 ≥max(8 wells,25%)、同预算 cap；执行延后 |
| 5 P0/P1 执行细节 | ✅ `DESIGN_A_v0_2.md`：y 聚合、τ/σ_pair、over-id/plan-pair 口径、折清单 5×6、两跑/schema/失败模板、G5 断言、data-only 预算（0 新 wells；wall 900 s/CPU 2 h/8 GB；F 计算量 3.40×10⁸） |
| 边界不变 | ✅ 开发性/non-blind/不称新颖性/不拼 ΔEMAX/技术重复≠独立培养；P1 阴性→`no_joint_contradiction`，不写"矛盾不存在" |
| 完成后标 completed + send_message | ✅ |

## 1. 时间线（Asia/Shanghai，2026-10-28）

| 时间 | 事件 |
|---|---|
| ~00:35 | 读 task-112 并 claim；读 challenge_A.md（5 必改）、PROBLEM_A/DESIGN_A v0.1、qualify_A.json、ON/D1/D3 记录 |
| ~00:37 | **`PROBLEM_A_v0_2.md` / `DESIGN_A_v0_2.md` 冻结**（`qualify_A_v0_2.py` 尚不存在） |
| ~00:38 | 写 `qualify_A_v0_2.py`（metadata/结构/P1 宇宙/折/P0 门/G5 断言；无响应统计） |
| ~00:39–00:45 | 首跑成功：**wall 371.3 s**，`qualify_A_v0_2.json` SHA `D6AE3506…B532B01E62`；|U|=340,088、target30 完整网格 16,722、over-id median 8,745、G1/G2/G4/G5 data-side PASS |
| ~00:46 | 启动同脚本第二次运行（确定性校验，后台 `tmp/qualify_v02_run2_stdout.txt`）→ 两次 `qualify_A_v0_2.json` 逐字节一致（两次运行 `qualify_A_v0_2.json` 逐字节一致（`d6ae35066ee20670f3f4f12d5c72f117943b48954f0551854e7516b532b01e62`；run1 wall 371.3 s、run2 wall 351.1 s；差异仅来自机器负载，产物无差异）） |
| ~00:52 | report/record/usage 完成；标 completed + send_message |

## 2. 实现、数据边界与偏离（全部披露）

- **v0.2 脚本首跑即成功**（无统计偏离）；运行只做：读 identity/dose 列 + viability 空值掩码（ON2 v2.1 口径）→ target30 完整 4×4 网格结构 → **P1 宇宙 |U| 逐对精确计数**（只数结构，不读响应）→ per-cell 加性设计 rank/over-id（0/1 设计矩阵 rank，不拟合）→ 折清单 → P0 G1–G5 data-side 断言 → 预算参数 → 写 JSON。
- **未读响应值**：无任何响应均值/方差/相关/效应；`viability1–4` 仅用于 `isna()` 空值掩码；`X/X0`、`mu/muMax` 未使用；单药工作簿未打开（v0.1 已记录元数据，本 v0.2 未读）。
- **v0.1 保留**：`PROBLEM_A.md DFB2DCE8…`、`DESIGN_A.md D1D02A4B…`、`qualify_A.py FBB9D3CF…`、`qualify_A.json D1DD2706…`、report/record/usage_A 均未改；v0.2 文件仅为 5 必改增量。
- **|U| 交叉核对**：target30 |U| = **340,088**，恰好等于 ON3 target30 单元数（每个 plan pair = 一次成员替换）；这是结构一致性检查，不是效果结果。
- **口径说明**：v0.1 的 441,867 计划对是 39 细胞全量；v0.2 **P1 限定 target30** → |U|=340,088（39/30 细胞比例合理）；G1 阈值 |U|≥100,000 为预注册下限，实测 340,088 PASS。
- **无效果/无拟合**：per-plan 加性"合法性"、F_pair、置换、BH、半拆 FPR 等均在**执行协议**中冻结，本轮不运行；qualify 只做结构/设计秩/计数。
- 补充：P1 执行实现须向量化（每 plan-cell 预计算 (drug,role) 的 4 剂量行均值；上下文组内成对 F 广播；行置换为 16 值重排后 4×4 行均值），预算 JSON 记录 F 计算量 3.40×10⁸；若实现超 wall/CPU cap → `design_invalid: compute_budget_exceeded`（不增删 N_perm）。

## 3. 运行事实

| 运行 | 目的 | wall | 结果 SHA256 |
|---|---|---|---|
| 1 | v0.2 资格/冻结输入（首跑） | **371.3 s** | `D6AE35066EE20670F3F4F12D5C72F117943B48954F0551854E7516B532B01E62` |
| 2 | 确定性复核（同脚本同输入） | 351.1 s | `D6AE35066EE20670F3F4F12D5C72F117943B48954F0551854E7516B532B01E62`（与 run1 相同） |

单命令 ≤15 min 预算 ✓（v0.1 为 137 s；v0.2 增加 target30 全 U 计数与逐对结构审计）；JSON 键排序/无时间戳/allow_nan=False；输入 SHA + protocol/design SHA 写入 JSON。

## 4. 关键结果（与报告一致）

- **例 3**：原秩 1 叙述作废（仅示意）；显式 E3 role-agnostic 示例：`SSE_joint(c)=2(c−2)²+2(c−1)²`、`min SSE=1.0`、`J_SSE=1.0`、RMS=0.5；在预注册 role-stratified S-add 下无矛盾 → **不作 H_A 证据**。
- **空集规则**：`M_pq=∅ ⇒ V_pq=∅`；`W(∅)=+∞`/sentinel `undefined_joint_infeasible`；ΔW 仅非空对；P1 全对、P2 非空对且非空≥20%；A.1 不执行 P2。
- **P1 冻结**：|U|=**340,088**；`F_pair=[||P⊥(f_p−f_q)||²/(K−1)]/σ_pair²`；`F_crit=2.60`；per-cell `T_c=max`；N_perm=**500**、seed=**20261029**；BH q=0.05（30 细胞）；P1 阳性 = ≥5 细胞 + pooled 超零分布 Q95 + G1–G5；半拆 FPR≤0.10、算子打乱≤0.10；pair 计数仅描述性。
- **H_A2/S2**：W*=0.05、R*=0.05、δ_noninf=0.01、wells 差 ≥max(8 wells,25%)、同预算；**延后不执行**。
- **P0/G5 数字**：target30 完整网格 pair-cells **16,722**；每细胞 median 565；over-id median **8,745**（30/30≥16）；target30∩Jaaks=∅；无 ΔEMAX/SYNERGY 列；702/315 pair-cell 排除；无新 wells；peek 披露存在 → G1/G2/G4/G5 data-side PASS，G3 执行期计算。
- **折清单**：5 折 × 6 细胞（seed 20261028；JSON 记录逐折细胞名）；仅描述性，不参与 P1 推断。

## 5. 产物与哈希

| 文件 | SHA256 |
|---|---|
| `PROBLEM_A_v0_2.md` | `61ec2fc982b807256f4795dce4f242d148b4e4403a7f0886592c99f1b88ab18a` |
| `DESIGN_A_v0_2.md` | `486272b2675b510efd32fdf33ac80fc2d2822111d9d6082ef4505ed235459b3c` |
| `qualify_A_v0_2.py` | `44b8d8d418edf4b8a7fc70ac365a0de0aa633863acdc59b365526aa2ebf34555` |
| `qualify_A_v0_2.json` | `D6AE35066EE20670F3F4F12D5C72F117943B48954F0551854E7516B532B01E62` |
| report/record/usage | 见 `usage_A_v0_2.json` |
| v0.1（未改） | PROBLEM_A `DFB2DCE8…`、DESIGN_A `D1D02A4B…`、qualify_A.py `FBB9D3CF…`、qualify_A.json `D1DD2706…`；输入 SHA 见 JSON |

## 6. 缺口（本轮明确未做）

- 未执行 P0/P1（等 Lead 批准；P1 统计量已冻结但无响应读取）。
- 未执行 P2/S1/S2/H_A2（未批准）；P2 空集规则与 H_A2/S2 数值目标仅冻结。
- 未做决策/迁移认证（30 细胞 MDE 0.7625 > δ_min → `evaluation_cannot_distinguish`；需 ≈6,283/≈1,573 独立细胞）。
- 无新测量；若 P1 后需升级，须另立协议 + 独立挑战 + Lead 批准。
