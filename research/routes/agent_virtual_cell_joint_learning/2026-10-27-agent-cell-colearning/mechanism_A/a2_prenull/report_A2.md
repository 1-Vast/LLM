# R201-A.2 报告：零模型/σ 尺度修正预注册（C192 后；本轮不执行 P1）

2026-10-28。角色：独立审计/设计修订员（未参与 R197/R200 模型开发）。任务 task-118（A.2）。
**只做设计/算术/合成校准：未运行 P1、未读 O'Neil 响应做效应、未拟合预测；non-blind/peeked 继承 ON3；不称生物学/机制/迁移/决策收益/新颖性。**
- 问题界定：[PROBLEM_A2.md](PROBLEM_A2.md)（`93c7613b…8237f1`）
- 合成校准/算术：[null_design_A2.py](null_design_A2.py)（`bd281f12…e8f021`）→ [null_design_A2.json](null_design_A2.json)（`7bcba58d…E0D948`）
- A.2 执行设计：[DESIGN_A2.md](DESIGN_A2.md)（`6bb3460e…4ea717d89`）
- 记录/用量：[record_A2.md](record_A2.md)、[usage_A2.json](usage_A2.json)
- 依据：C192（A-P0P1 执行期发现）、`p0p1/a_p0p1.json`、`report_a_p0p1.md`、`DESIGN_A_v0_2.md`、`DECISION_R201_A_P0P1.md`；**未改 A.1 产物**。

## 0. C192 复述与不可解释性

A.1 P0/P1 执行（Lead 批准、data-only、0 新 wells）在冻结规则下判 `p0p1_negative`（BH 拒绝 0/30；pooled observed 0.1537 < null Q95 0.7491；G1–G5 PASS），但执行期发现两类校准问题：

| # | 发现 | 数字 |
|---|---|---|
| ① | 冻结行置换零分布**严重偏高**，不对应 shared-f H0 | null pooled 中位 **0.7457** ≫ observed **0.1537**；null median T **146.31** ≫ observed **73.43** |
| ② | σ 尺度不一致 | 冻结 `σ_obs=0.065704`（公式 `/2`）；`σ_obs_alt=0.092919`；冻结 `σ_pair²=0.00215849`；`F_self` 中位 **0.4579**（H0 期望≈1） |

**结论**：A.1 的 negative 只能写"本资源/本族/本设计（冻结零模型）下未检出"，**不能写"矛盾不存在"**，**不构成机制 A 阴性证据**。**A.2 只修 null 与 σ 归一化；不改 P1 统计量/阈值/族/数据**；必须作为新预注册整体重跑 P1，不得在 A.1 结果上事后换 null/阈值。

## 1. σ 尺度修正（算术已核）

- 归一化推导（R=M=4）：`Var(y_row)=σ_w²/4`；`Var(f)=σ_w²/16`；配对差 `Var(d)=σ_w²/8` ⇒ **σ_pair²=σ_w²/8**。
- `σ_w_hat=sqrt(mean((h1−h2)²))=0.092919`（技术半拆 {1,2}/{3,4}；A.1 的 `σ_obs_alt`）。
- **S1（独立性派生，敏感性）**：`σ_pair²_S1=σ_w_hat²/8=0.00107924`。
- **S2（primary；半拆层直接校准）**：`σ_pair²_A2 = mean_{plan,context}[ ||P⊥(f_h1−f_h2)||²/(K−1) ]`（H0 下 E[F_self]=1；A.2 执行期计算）。
- **A.1 诊断**：冻结 `σ_pair²=0.00215849` = **2.000×S1** → A.1 的 F 尺度为归一化尺度的一半；`F_self` 中位 0.4579 证实尺度不一致。**不缩放 A.1、不改 F_crit**；A.2 整体重跑。
- **F_crit=2.60 保留条件**：S2 归一化后 `F_self` 均值/中位 ∈[0.5,2]、`FPR@F_crit≤0.10`；否则 `design_invalid: scale_mismatch`。

## 2. 候选零模型（预注册比较；合成校准，不依赖 A.1/A.2 observed 结果）

合成设置（预注册，不读 O'Neil 响应）：5 cells × 6 groups × 6 plans、K=M=4、σ_w=0.10；违例 = 一条计划 profile 形状偏移 2·σ_pair；seed 20261030；n_pairs=450。

| id | H0 | 可交换性/假设 | 实现 | FPR@2.60 | power | primary-eligible |
|---|---|---|---|---|---|---|
| **N0** χ² 校准 | shared f + iid 噪声 | iid；σ 正确 | 解析/模拟 χ²₃/3；pooled 尾概率 | **0.048** | **0.296** | ✅ |
| **N1** 参数化 bootstrap | shared f + 每计划 g | 参数化；f,g 可识别 | 拟合 shared f（组内均值 profile）+ 每计划 g，重模拟噪声后重算 F | **0.054** | **0.289** | ✅ |
| **N2** 残差置换 | 加性拟合后残差可交换 | 残差 iid；保持孔位 | 每 plan-cell 加性拟合，置残差后重算 F | 0.165 | 0.193 | ❌（FPR>0.10） |
| **N3** dose-split 交叉拟合 | 剂量可交换仅用于噪声估计 | 2+2 剂量交叉拟合 | 半剂量 profile 差估尺度，χ² null 缩放 | **0.042** | **0.296** | ✅ |
| **N4** dose-label 置换 | **不成立**（A.1 行置换极端版） | 剂量标签；与 shared-f H0 相悖 | 置换每计划 4 个剂量位置 | 0.947 | 0.000 | ❌（invalid，仅对照） |
| **N5** 技术半拆层 | 半拆分独立；shared f | 独立半拆 | 由 F_self 校准尺度，归一化 χ² null | **0.049** | **0.296** | ✅ |

**选择规则（预注册；只看合成校准）**：FPR∈[0.02,0.10] 且非 N4，取 power 最高；并列优先级 **N0 > N3 > N2 > N1 > N5**。
**结果：primary null = N0（χ² 校准）**；eligible = N0/N1/N3/N5；N2 不 eligible；N4 无效对照。
**实现细化（预注册写入 A.2）**：per-cell `T_c` 需保留共享 profile 的相关结构 → **pooled 用 N0 的 pair 级 χ²；per-cell T_c null 用 N1 参数化 bootstrap**（两者均通过合成校准：N0 .048/.296、N1 .054/.289）。此细化在预注册中写死，不是结果驱动选择。

## 3. A.2 执行设计要点（DESIGN_A2.md）

- **不变**：数据/人群、|U|=340,088、单独合法规则（用 A.2 σ 重算阈值）、S-add 族、`F_pair` 公式、per-cell T_c、`F_crit=2.60`（条件性）、N_perm=500、BH q=0.05、阳性三条件。
- **仅改**：① σ_pair² 用 S2（S1 敏感性）；② 零模型用 N0（pooled）+ N1（per-cell T_c）；③ 新增诊断门。
- **诊断门（先于 P1 判定；任一失败不进入 P1）**：D1 σ 非退化；D2 `F_self` 均值/中位∈[0.5,2]；D3 `F_self` FPR≤0.10；D4 primary null pooled 中位∈[0.02,0.15]；D5 `median(T_null)/median(T_obs)`∈[0.2,3]；D6 预算；D7 G1–G5。失败类别：`design_invalid: scale_mismatch|noise_calibration|null_calibration|compute_budget_exceeded`（+A.1 既有类别）。
- **预算**：data-only、**0 新 wells**；wall≤900 s、CPU≤2 h、内存≤8 GB；primary null 500 + pooled 500 + 候选 N2/N3/N5 各 500（≈2,500 模拟；预检 per-run ≤~10 min）；两跑逐字节一致；结果 JSON 不含 telemetry。
- **解释边界**：阳性仅"本资源/本族/本设计下存在联合矛盾（开发性）"；阴性仅 `no_joint_contradiction`（不写"矛盾不存在"）；pair 级仅描述性；non-blind/peeked；**A.2 通过前不进入 P2/S2/H_A2**；不称生物学/机制/迁移/决策收益/新颖性。

## 4. 边界与不主张

- A.2 是**新预注册**；A.1 的 `p0p1_negative` 原样保留、不重判；不得用 A.1 结果换 null/σ/阈值。
- 未运行 P1、未读 O'Neil 响应做效应；合成校准只用于选择零模型（机制已知、无 O'Neil 响应），不改 P1 统计量。
- 未执行 P2/ΔW、S1、S2/H_A2；无新测量/新 wells。
- 不称新颖性/生物学/机制/迁移/决策收益；技术重复≠独立培养；不拼 ΔEMAX；non-blind/peeked。

## 5. 产物与确定性

| 文件 | SHA256 |
|---|---|
| `PROBLEM_A2.md` | `93C7613BDF7E218171C83A6FA3F371283E252C0F9249562E8830DD027C8237F1` |
| `DESIGN_A2.md` | `6BB3460E9FD2F44F35FEDF4B7815662728CA372BB1D67DADA8229AE4EA717D89` |
| `null_design_A2.py` | `BD281F122D407AB76D6DD40435A6B86CBB97A2233541A7016A738A0AE5E8F021` |
| `null_design_A2.json` | `7BCBA58DD26849345EB3143607BA95EF2329313417DD14F6E2C1D77295E0D948` |
| report/record/usage | 见 `usage_A2.json` |

**确定性**：同脚本两次运行 `null_design_A2.json` 逐字节一致（SHA 相同；wall 均 0.2 s）；JSON 键排序/无时间戳/allow_nan=False；输入 SHA 写入 JSON。

## 6. 建议

1. **将 A.2 预注册（PROBLEM_A2 + DESIGN_A2 + null_design_A2）提交独立挑战**（endpoint-auditor/i003）；挑战通过后再请 Lead 批准 A.2 执行。
2. 挑战重点：σ S2 公式与归一化门、候选 null 合成校准与选择规则（不依赖 observed）、N0/N1 实现细化、诊断门 D1–D7、预算/failure categories、解释边界。
3. **A.2 通过并执行完前**：不进入 P2/S2/H_A2；不解释 A.1 negative；不写"矛盾不存在/机制/迁移/决策收益"。
