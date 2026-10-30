# R201-A.1 报告：P0/P1 预注册冻结（5 必改落实；仅 P0/P1 提交批准）

2026-10-28。角色：独立审计/设计修订员（未参与 R197/R200 模型开发）。任务 task-112（R201-A.1）。
**只做设计/预注册：不运行效果、不拟合预测、不读 O'Neil 响应值做统计；不称新颖性/机制/迁移/决策收益。**
- 形式化修订：[PROBLEM_A_v0_2.md](PROBLEM_A_v0_2.md)（`61ec2fc982b807256f4795dce4f242d148b4e4403a7f0886592c99f1b88ab18a`）
- P0/P1 执行协议：[DESIGN_A_v0_2.md](DESIGN_A_v0_2.md)（`486272b2675b510efd32fdf33ac80fc2d2822111d9d6082ef4505ed235459b3c`）
- 资格/冻结输入：[qualify_A_v0_2.py](qualify_A_v0_2.py)（`44b8d8d418edf4b8a7fc70ac365a0de0aa633863acdc59b365526aa2ebf34555`）→ [qualify_A_v0_2.json](qualify_A_v0_2.json)（`d6ae35066ee20670f3f4f12d5c72f117943b48954f0551854e7516b532b01e62`）
- 记录/用量：[record_A_v0_2.md](record_A_v0_2.md)、[usage_A_v0_2.json](usage_A_v0_2.json)
- v0.1 文件未改动（PROBLEM_A `DFB2DCE8…`、DESIGN_A `D1D02A4B…`、qualify_A.json `D1DD2706…`）
- 依据：challenge_A（**approve_to_lead_mvp：仅 P0/P1**；5 必改）、R201 BRIEF、ON1–ON3/PEEK、D1/D3/A1 停止结论。
- **状态：待 Lead 批准 P0/P1（建议批准前轻量 confirm）；P2/S1/S2/H_A2 不执行。**

## 0. 5 必改落实（与裁定）

| # | 必改 | v0.2 落实 |
|---|---|---|
| 1 | 例 3 秩 1 交互无显式演算 | **原秩 1 叙述明确标"仅示意、不作形式证据"并剔除**；新增**显式 E3（role-agnostic 错族示例）**：完整观测/约束/J 数值演算（J_SSE=1.0、RMS=0.5）；形式证据例子 = **E1 + E2**（E3 仅族设定警示，不计入 H_A 证据） |
| 2 | P2/ΔW 空集未定义 | 冻结 `M_pq(τ)`/`V_pq=∅` 定义、`W(∅)=+∞`/sentinel `undefined_joint_infeasible`、`ΔW` 仅非空对、P1/P2 适用关系（P1 全对、P2 仅非空且非空对≥20%）；**A.1 不执行 P2** |
| 3 | P1 缺精确统计/FPR/多重性 | 冻结：`U` 宇宙（target30 精确 **340,088** 对）、`F_pair` 公式、`F_crit=2.60`、per-cell max 置换零分布（N_perm=500、seed 20261029）、30 细胞 BH q=0.05、P1 阳性三条件（≥5 细胞 + pooled 超零分布 Q95 + G1–G5）、技术半拆/算子打乱 FPR 门；pair 级计数只描述性（44 万对 FPR 论证） |
| 4 | H_A2/S2 数值目标未写死 | 冻结：`W*=0.05`、`R*=0.05`、`δ_noninf=0.01`、wells 差 `≥max(8 wells, 25%)`、同预算 cap；**A.1 不执行**（延后另立预注册） |
| 5 | P0/P1 执行细节 | DESIGN v0.2：y=mean(viability1–4)（冻结）、`σ_pair²=σ_obs²/2`、`F_crit`、over-id/plan-pair 计数口径、折清单（5×6，seed 20261028）、两跑/schema/失败模板、**G5 边界断言**（target30∩Jaaks=∅、无 ΔEMAX、batch1-only、702/315 排除、无新 wells、peek 披露）、预算（data-only，0 新 wells；wall ≤900 s、CPU ≤2 h、内存 ≤8 GB） |

**裁定**：P0/P1 已达到"可提交 Lead 批准"的预注册完备度；**P2/S2/H_A2 不批准**（P1 后另立）。若 P1 不达 → 只写 `no_joint_contradiction`（本资源/本族/本设计下未检出），**不写"矛盾不存在"**。

## 1. 例 3 处理（必改 1）

- **v0.1 例 3（rank-1 叙述）→ 作废**：仅一句"构造使 p1 需要 `u(d2)/u(d1)=1`、p2 需要 =2"，无观测/设计矩阵/J 演算；已标"仅示意、不作形式证据"并剔除。
- **秩 1 可识别性核算（写入 PROBLEM_A_v0_2 §3.2）**：S-r1 两计划合计未知数 `2K+2(2M+1)`、观测 `2KM`，需 `2KM > 2K+4M+2` 才可能有过识别约束（K=M=4 时 32>26 ✓；K=2 时 8<14 ✗）→ 秩 1 矛盾必须在大网格上显式列出设计矩阵，不能靠 2×2 示意。
- **新增显式 E3（role-agnostic 错族示例；完整可复核）**：药物 X 在 p1 为 role A、在 p2 为 **role B**（同一剂量 d1,d2）：
  - p1：`y(d1,e1)=1, y(d1,e2)=2, y(d2,e1)=3, y(d2,e2)=4`（role-stratified 加性精确拟合，`f_X^A(d2)−f_X^A(d1)=2`）。
  - p2：`y(e1,d1)=1, y(e1,d2)=2, y(e2,d1)=4, y(e2,d2)=5`（精确拟合，`g_X^B(d2)−g_X^B(d1)=1`）。
  - role-agnostic 族强制同一 `f_X`：共同参数 `c=f_X(d2)−f_X(d1)`；`SSE_joint(c)=2(c−2)²+2(c−1)²`，`min SSE=1.0`（c=1.5）；单独 SSE=0 → **J_SSE=1.0、RMS=0.5**。
  - **正确读法**：这是**族错设警示**（role 分层必须写死），在预注册 role-stratified S-add 下无矛盾 → **不作 H_A 形式证据**；P1 主族必须角色分层。

## 2. P2/ΔW 空集规则（必改 2；冻结，P2 不执行）

- `M_pq(τ)={θ: r_p≤τ ∧ r_q≤τ}`；若空 → **`V_pq=∅`**（空集，非单点/非∞点）。
- `W_p(V)=sup_{θ∈V}R_p(θ)−inf_{θ∈V}R_p(θ)`；**`W_p(∅)=+∞`**；实现用 sentinel **`undefined_joint_infeasible`**，不参与数值聚合。
- `ΔW(p,q)=mean_{s∈{p,q}}[W_s(V_s^sep)−W_s(V_pq)]`，**仅 `V_pq≠∅` 有定义**。
- **P1 用全部合格对**（只算 J，不涉及 ΔW）；**P2 只用非空 `V_pq` 对**；空集对归 P1 证据；P2 可估需"非空对 ≥ 合格对 ×20%"（未来预注册）；**A.1 不执行 P2**。

## 3. P1 精确统计/FPR/多重性（必改 3；冻结）

- **检验宇宙 U**：同一 target30 细胞；两 pair-cell 均 batch1 complete-case 完整 4×4 网格；共享 ≥1 `(drug,role)` 上下文且共同剂量 ≥2。**v0.2 实测：|U|=340,088**（恰好与 ON3 target30 单元数一致——每个 plan pair = 一次成员替换；交叉核对）；每细胞 9,047–11,623 对；全部对共享 1 个上下文、4 个共同剂量（hist 冻结于 JSON）。
- **统计量**：单计划合法 = 加性残差 RMS ≤ `1.96·σ_obs/2`；`F_pair=[||P⊥(f_p−f_q)||²/(K−1)]/σ_pair²`（K=4）；`F_crit=2.60`（F_{0.95,3,∞}）；per-cell `T_c=max F_pair`。
- **零分布**：plan-cell 内 16 行行置换，N_perm=**500**、seed=**20261029**；per-cell p=(1+#{T^(b)≥T})/(1+N_perm)；**BH q=0.05**（30 细胞）。
- **P1 阳性（三条件同时）**：① BH 拒绝细胞 ≥5；② pooled `F_pair≥F_crit` 比例 ≥ 置换零分布 pooled 比例 Q95；③ G1–G5 PASS。**阴性** → `no_joint_contradiction`（不写"矛盾不存在"）。
- **FPR 论证（340,088 对）**：pair 级计数**只作描述性**（H0 下逐对 5% 误报 → 期望 ~1.7 万假阳性，故 pair 计数永不单独作证据）；推断用 per-cell max（吸收 cell 内 ~10^4 对多重性）+ BH（跨 30 细胞 FDR）。**随机计划对**只属 H_A2（未批）；P1 无选择。
- **零模型门（P0 后 P1 前）**：技术半拆 FPR ≤0.10；算子打乱（(drug,role) 标签细胞内置换）检测率 ≤0.10；行置换零分布本身 PASS。任一失败 → `design_invalid: null_calibration`。
- **族错设门**：合格对中"两计划都合法"比例 <5% → `design_invalid: family_misspecification`（S-add 不适合；不得改族重跑，需另立 S-r1 协议）。

## 4. H_A2/S2 数值目标（必改 4；冻结但延后）

- "同等界"目标 `W* = 0.05`（归一化效用）；"同等决策目标" `R* = 0.05`（S1 仍只描述性，MDE 0.7625 > δ_min）。
- 非劣 margin `δ_noninf = 0.01`（单侧 95% CI）；"更少 wells" 最小有意义差 `n_C − n_M* ≥ max(8 wells, 25%·n_C)`；计算成本全计（≤2 CPU-h/arm、≤20 配置）。
- **A.1 不执行 H_A2/S2**（Lead 未批；P1 通过后另立预注册 + 独立挑战）。

## 5. P0/P1 执行细节（必改 5；DESIGN_A_v0_2）

- **数据/人群**：O'Neil batch1 complete-case；target30（9 个 Jaaks 重叠细胞排除）；702 个 15 行/315 个 0 行 pair-cell 排除；不插值；无新 wells（data-only）。
- **y 聚合（主）**：`y_row = mean(viability1..4)`（冻结）；`X/X0` 仅敏感性；`mu/muMax` 不用；k=1 行不参与标定。
- **噪声**：固定列索引分半 `{1,2}/{3,4}`（禁按值排序）；`σ_obs=sqrt(mean((half1−half2)²)/2)`；`σ_pair²=σ_obs²/2`；`F_crit=2.60`；半拆 FPR 门 ≤0.10。
- **P0 门 G1–G5**：G1 覆盖（30/30 细胞、每细胞完整网格 pair-cells ≥200；|U| ≥100,000；实测 16,722 pair-cells、median 565、|U|=340,088 → PASS）；G2 可识别（over-id ≥16；实测 median 8,745，30/30 → PASS）；G3 噪声（执行期计算）；G4 泄漏/隔离（batch1 only、target30∩Jaaks=∅、无 ΔEMAX → PASS）；**G5 边界断言**（六条代码级断言：target30∩Jaaks=∅、端点只 viability、batch1 only、702/315 排除、无新 wells、peek 披露已打印）。
- **折清单**：30 target 细胞按归一名排序、seed 20261028 置换、`fold=index%5` → **5×6**（JSON 含逐折细胞清单）；仅描述性一致性，不参与 P1 推断。
- **两跑/schema/失败模板**：同脚本两跑 `outputs_A_v0_2.json` 逐字节一致；字段含 gates/p0/p1/null/failure_category/notes；失败模板 `failure_category ∈ {data_unavailable, design_invalid:coverage|identifiability|noise_calibration|leakage|boundary|null_calibration|compute_budget_exceeded|family_misspecification, no_joint_contradiction}`。
- **预算**：0 新 wells/plate/轮次；wall ≤900 s、CPU ≤2 h、内存 ≤8 GB；置换 N_perm=500 ×2 类；**F 计算量 ≈3.40×10⁸**（340,088×(1+500+500)）；执行须用**向量化实现**（每 plan-cell 预计算各 (drug,role) 的 4 剂量行均值向量；每个上下文组内成对 F 用数组广播一次算完；行置换用重排 16 值后重塑 4×4 求行均值），per-perm 仅 ~34 万对 × 4 维运算 → 预估 wall 数分钟内；超 cap → `design_invalid: compute_budget_exceeded`（不增删 N_perm）。
- **若执行需要新测量**：停 P0/P1，另立协议（记录所需测量）。

## 6. 资格数字（v0.2 复核，与 v0.1/ON2 一致）

| 项 | 值 |
|---|---|
| O'Neil 行/细胞/药/对 | 368,832 / 39 / 38 / 583；complete-case 363,090（98.44%） |
| target30 完整 4×4 网格 pair-cells | **16,722**（30/30 细胞；每细胞 median 565） |
| **P1 宇宙 |U|** | **340,088**（每细胞 9,047–11,623；全部共 1 上下文×4 共同剂量） |
| 加性设计过识别度 | per-cell median **8,745**；30/30 ≥16（P0 G2 PASS） |
| 4 个技术重复/行 | 是；k=1 行不参与标定；702/315 pair-cell 排除 |
| Jaaks 重叠细胞 | target30 ∩ Jaaks = **∅**（G4/G5 PASS） |
| 端点 | 仅 viability1–4；无 ΔEMAX/SYNERGY 列（G5 PASS） |
| 汇总 | G1/G2/G4/G5 data-side **PASS**；G3 在执行期计算 |

## 7. 剩余缺口/所需测量（不变）

- 决策认证需 **≈6,283 独立细胞（δ=0.05）/≈1,573（δ=0.10）**；本设计 P1 不做决策/迁移。
- P2/S2/H_A2 需 P1 后另立预注册；P-program（顺序/时点）本地不存在；单药参照需另立资格。
- 若 P1 阳性且想升级：必须先 P2 预注册（空集规则已冻结）+ 独立挑战 + Lead 批准；不得直接写"矛盾存在/机制/迁移"。

## 8. 建议

- **建议 Lead 批准 P0/P1**（数据-only、0 新 wells；开发性形式/存在性）；批准文本建议引用 DESIGN_A_v0_2 §8。
- 建议批准前请 endpoint-auditor 做一次**轻量 confirm**（5 必改落实 + 例 3 显式化 + P1 FPR/BH + 执行细节/SHA），预计只需只读复核，不需再跑数据。
- 挑战通过/批准后：先执行 P0（G1–G5、噪声标定、族合法性比例），P0 PASS 再执行 P1；P1 阴性只写 `no_joint_contradiction`；不执行 P2/S2/H_A2。

## 9. 产物与确定性

| 文件 | SHA256 |
|---|---|
| `PROBLEM_A_v0_2.md` | `61ec2fc982b807256f4795dce4f242d148b4e4403a7f0886592c99f1b88ab18a` |
| `DESIGN_A_v0_2.md` | `486272b2675b510efd32fdf33ac80fc2d2822111d9d6082ef4505ed235459b3c` |
| `qualify_A_v0_2.py` | `44b8d8d418edf4b8a7fc70ac365a0de0aa633863acdc59b365526aa2ebf34555` |
| `qualify_A_v0_2.json` | `d6ae35066ee20670f3f4f12d5c72f117943b48954f0551854e7516b532b01e62` |
| report/record/usage | 见 `usage_A_v0_2.json` |

**确定性**：同脚本两次运行 `qualify_A_v0_2.json` 逐字节一致（两次运行 `qualify_A_v0_2.json` 逐字节一致（`d6ae35066ee20670f3f4f12d5c72f117943b48954f0551854e7516b532b01e62`；run1 wall 371.3 s、run2 wall 351.1 s；差异仅来自机器负载，产物无差异））；JSON 键排序/无时间戳/allow_nan=False；输入 SHA + protocol/design SHA 全部写入 JSON；单命令 wall ≈371 s（v0.1 为 137 s；v0.2 增加 target30 全 U 计数与逐对结构审计）。
