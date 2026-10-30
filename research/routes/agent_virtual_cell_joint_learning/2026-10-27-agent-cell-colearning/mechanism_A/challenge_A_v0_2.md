# R201-A.1-C1 轻量确认（challenge_A_v0_2.md）

2026-10-28 · 挑战者：endpoint-auditor（与 ON1/ON2/ON3/D1/D3/D5/A 同一独立挑战者；未参与 A.1）· 对象：`research/2026-10-27-agent-cell-colearning/mechanism_A/{PROBLEM_A_v0_2.md, DESIGN_A_v0_2.md, qualify_A_v0_2.py, qualify_A_v0_2.json, report_A_v0_2.md, record_A_v0_2.md, usage_A_v0_2.json}`。
方式：**只读轻量复核**（E3 演算/P2 空集/P1 FPR/预算/SHA；**不运行效果、不拟合、不读 O'Neil 响应值做统计**）；只写本文件与 `tmp/`。
完整性：`PROBLEM_A_v0_2.md` **`61EC2FC9…`**；`DESIGN_A_v0_2.md` **`486272B2…`**；`qualify_A_v0_2.py` `44B8D8D4…`；`qualify_A_v0_2.json` **`D6AE3506…`**；`report_A_v0_2.md` **`75984409…`**；`record_A_v0_2.md` **`75EC244F…`**；`usage_A_v0_2.json` `1B628E95…`——均与磁盘实算一致。

## 0. 总判决

**approve_p0p1_to_lead（仅 P0/P1 最小实验；data-only、0 新 wells；不执行 P2/S1/S2/H_A2）。**
A.1 已把上一轮 5 条必改落到位：例 3 处理（原秩 1 叙述标“仅示意、不作形式证据”并剔除；新增显式 E3 的 SSE/J/RMS 演算；role-stratified S-add 下无矛盾，E3 不计入 H_A 形式证据；形式证据=E1+E2）；P2/ΔW 空集规则冻结且 A.1 不执行 P2；P1 统计/FPR/BH/阳性三条件冻结；H_A2 数值目标冻结但延后；P0/P1 执行细节（y、半拆噪声、U、F、N_perm、seed、BH、两跑/schema、G5、0 wells、budget）具体可执行。**无 fatal must-fix；可提交 Lead 批准 P0/P1。**

**最致命 3 条（均为登记/执行边界，不是驳回项）**
1. **P1 零模型依赖“plan-cell 内 16 行可交换”**：row permutation 合法零要求行/剂量位/板结构不引入不可交换性；batch1 无 plate 记录、同 pair-cell 16 行共享 wells，故 P1 的 FPR 必须由 **G3 半拆分 + 算子打乱 + N_perm 行置换**共同背书；若执行时发现行/板结构破坏可交换性 → `design_invalid: null_calibration`，不得改 N_perm/阈值。
2. **pair 级 `F_pair≥F_crit` 计数在 H0 下期望 ~1.7 万假阳性**：只能作描述性；P1 推断必须用 **per-cell max + BH(q=.05) + pooled Q95 + G1–G5**；任何 pair 级计数/挑细胞不得单独作为存在性证据。
3. **P1 预算 3.40×10⁸ F 计算**（340,088 U × (观测+500 行置换+500 算子打乱)）与 **wall≤900 s / CPU≤2 h / 8 GB** 需在 P0 后先做 **预算预检**；超限 → `design_invalid: compute_budget_exceeded`；不得减 N_perm/换便宜分析。

## 1. 逐条确认

### ① 例 3 / E3 —— **PASS**

- **原秩 1 叙述**：PROBLEM v0.2 §3.1 明确标 **“仅示意、不作形式证据，已从形式证据集合中剔除”**；不再引用为矛盾例子。**PASS**。
- **E3（role-agnostic 错族示例）显式**：
  - p1 `(1,2;3,4)` role A X 差 =2；p2 `(1,2;4,5)` role B X 差 =1；
  - role-agnostic 共同 `c=f_X(d2)−f_X(d1)`：`SSE_joint(c)=2(c−2)²+2(c−1)²`，min 在 c=1.5 = **1.0**；`J_SSE=1.0`、RMS=0.5；
  - **role-stratified S-add** 下 p1/p2 各自精确拟合、**无矛盾**；E3 **不计入 H_A 形式证据**；形式证据=**E1+E2**。**PASS（数学正确）**。
- **秩 1 可识别性核算**：S-r1 每计划自由 `(g_b,v_b,λ)`、共享 `(f_a,u_a)`；两计划未知数 `2K+2(2M+1)`、观测 `2KM`；K=M=4 → 32>26，K=M=2 → 8<14；说明 2×2 示意无约束力；**PASS**。

### ② P2/ΔW 空集 —— **PASS**

- `M_pq(τ)={θ:r_p≤τ∧r_q≤τ}` 可能为空；`V_pq={m_H(θ):θ∈M_pq}`；**M_pq=∅⇒V_pq=∅**。
- `W_p(∅)=+∞` sentinel `undefined_joint_infeasible`；`ΔW` 仅在 `V_pq≠∅` 定义；P1 用全部合格对、P2 只用非空对（未来 ≥20% 门槛）；**A.1 不执行 P2**；**PASS**。

### ③ P1 统计/FPR/多重性 —— **PASS**

- `|U|=340,088`（target30；每细胞 **9,047–11,623**；共享 **1 个 (drug,role) 上下文×4 共同剂量**）；单计划合法=`additive residual RMS≤1.96σ_obs/2`。
- `F_pair=[||P⊥(f_p−f_q)||²/(K−1)]/σ_pair²`（K=4）；**F_crit=2.60**；per-cell `T_c=max F`；**16 行 plan-cell 内置换 N_perm=500、seed=20261029**；per-cell p+BH q=.05（30 细胞）。
- **阳性三条件**：`BH拒绝≥5` ∧ `pooled F_pair≥F_crit 比例≥置换Q95` ∧ `G1–G5`；**P1 阴性只写 `no_joint_contradiction`**；pair 级仅描述性（H0 期望 ~1.7 万假阳性不得单独作证据）。
- **FPR/零模型门**：技术半拆 FPR≤0.10；算子打乱检测≤0.10；族错设<5%→`design_invalid: family_misspecification`；**PASS**。
- **`U`/`F` 预算**：340,428,088 F 计算估计；wall≤900s、CPU≤2h、8GB；超限→`design_invalid: compute_budget_exceeded`；**PASS（需预检）**。

### ④ H_A2/S2 —— **PASS（延后，不执行）**

- `W*=0.05`、`R*=0.05`、`δ_noninf=0.01`（单侧95% CI）、`n_C−n_M*≥max(8 wells,25% n_C)`、同计算预算；**A.1 不执行**；P1 后另立预注册 + 独立挑战；**PASS**。

### ⑤ P0/P1 执行细节 —— **PASS**

- `y=mean(viability1..4)` primary；`X/X0` sensitivity only；`σ_obs` 半拆 `{1,2}/{3,4}`，`σ_pair²=σ_obs²/2`；over-id/plan-pair/target30 计数；5 折×6 细胞 seed **20261028**（仅描述性一致性）；两跑逐字节 + 11 字段 schema + 失败模板；G5 六条（target30∩Jaaks=∅、viability-only、batch1-only、702/315 排除、无新 wells、peek 打印）；**0 新 wells**、wall≤900s/CPU≤2h/内存≤8GB；**PASS**。
- **P0 门 G1–G5**：G1 覆盖（30/30，完整 pair-cells 16,722，U=340,088≥100,000）；G2 over-id median 8,745≥16；G3 噪声半拆；G4 泄漏/隔离；G5 边界/lineage；**PASS**。
- **P1 正/负解释**：只写“本资源/本族/本设计下存在联合矛盾”的开发性存在性；阴性只写 `no_joint_contradiction`，不写“矛盾不存在”；**PASS**。

### ⑥ 边界/先例 —— **PASS**

- 仅开发性；不称新颖性/机制/迁移/决策收益；CoMap/LAWM/MDA/COPEx 仅背景；不重复 D1/D3/A1；不拼 ΔEMAX；non-blind/peeked 继承；P-program 本地不存在；功能/决策需新测量；**PASS**。

## 2. Lead 批准 P0/P1 文本（建议直接采用）

> **批准 R201-A 仅进入 P0/P1 最小实验（开发性形式/存在性；data-only；不进入 P2/S1/S2/H_A2）。**
> 冻结：`PROBLEM_A_v0_2.md` `61EC2FC9…`、`DESIGN_A_v0_2.md` `486272B2…`、`qualify_A_v0_2.json` `D6AE3506…`、`report_A_v0_2.md` `75984409…`、`record_A_v0_2.md` `75EC244F…`；y=mean(viability1–4)、半拆 σ_obs、σ_pair²=σ_obs²/2、F_crit=2.60、U=340,088、N_perm=500、seed=20261029、BH q=.05、G1–G5、失败模板、预算（0 新 wells；wall≤900s/CPU≤2h/内存≤8GB）。
> **P1 解释边界**：只写“本资源/本族/本设计下存在联合矛盾”的开发性存在性；P1 阴性只写 `no_joint_contradiction`，不写“矛盾不存在/结构不存在”；pair 级计数仅描述性；不称生物学/机制/迁移/决策收益/新颖性；non-blind/peeked。
> **不执行**：P2/ΔW、S1 决策终点、S2/H_A2；H_A2 数值目标已冻结但延后另立预注册；任何算法/决策/迁移主张需 P1 后独立挑战 + Lead 批准。
> 若执行需任何新测量/新 wells → 停 P0/P1，另立协议；超 budget → `design_invalid: compute_budget_exceeded`。

## 3. 复核证据与本轮边界

- 实际 SHA 见页首；E3/SSE/J/RMS 演算核对；P2 空集/frozen；P1 F/Fcrit/N_perm/BH/FPR；P0/P1 细节；**无 fatal must-fix**；只列 3 条登记/执行边界（零模型可交换性、pair 级假阳性、预算预检）。
- **本轮未运行效果/未拟合/未读 O'Neil 响应值做统计**；只读文档/JSON/SHA；只写本文件与 `tmp/`。
- **approve_p0p1_to_lead**；P0/P1 data-only、0 新 wells；P2/S1/S2/H_A2 不执行；不称新颖性/机制/迁移/决策/生物学；阴性≠不存在；冻结≠资源足够/关系成立/Stage1/效果。
