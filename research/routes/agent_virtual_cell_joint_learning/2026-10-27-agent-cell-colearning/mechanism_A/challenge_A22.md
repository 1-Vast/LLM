# R201-A.2.2 独立挑战（task-124）：异方差稳健 σ/零模型预注册

2026-10-28。角色：同一独立挑战者（非提案者、未参与 A/A.1/A.2、不运行 P1/不拟合/不读 O'Neil 响应做效应）。对象：[PROBLEM_A22.md](PROBLEM_A22.md)（SHA `69605BBC…`）、[DESIGN_A22.md](DESIGN_A22.md)（`EAC8EA10…`）、[sigma_robust_A22.json](sigma_robust_A22.json)（`12DC9855…`）、[report_A22.md](report_A22.md)（`DC5DBD77…`）、[record_A22.md](record_A22.md)（`8217C71A…`）、`a2_exec/a2_exec.json`（`26BF3B7A…`）/diagnostics（`1846BAD2…`）、A.2 链。**只读；只写本文件与 `tmp/`。**

## 0. 结论先行

**总判决：approve_a22_to_lead（仅 A.2.2 data-only P1 重跑；0 新 wells；不进入 P2/S2/H_A2；A.1/A.2 不重判）。**

v0.2 的 S2/F_self/legal 修正已在 A.2-EXEC 被 C194 证实不足（D2 median .4153、F_self 强异方差；P1 未执行），A.2.2 的 **R4 per-context fuller-profile σ** 与 D2/D3 重设计是合理的下一步。核验 PASS：
- **C194 复述**：D2 mean **0.9700** ✅ / median **0.4153** ❌；分位 p5 .04/p25 .17/p50 .42/p75 1.00/p95 **3.61**/max 67.18；`σ_pair²_A2=0.00110139`（/S1=1.0205）；legal n=**176,934**；P1=False、`design_invalid: scale_mismatch`；A.1 仍不可解释——与 `sigma_robust_A22.json → c194_recap`/`a2_exec` 一致。
- **候选 σ 合成校准**：R0 coverage .500/FPR .0723/worst .682/power .129 不 eligible；R1 .917/.0739/.424/.171 不 eligible（worst>.25）；R2 .604/.1222/.803/.129 不 eligible；**R4 .875/.0439/.121/context-p95 .076/power .183 唯一 eligible**；选择规则（coverage∈[.5,2] per-context 中位≥.85 ∧ overall FPR∈[.02,.10] ∧ worst≤.25 ∧ context-FPR p95≤.20；eligible 取 power 最高；并列 R1>R2med>R2trim>R4>R0；无→design_invalid: null_calibration）在合成校准上预注册，primary=**R4**；不依赖 A.2 observed P1（A.2.2 P1 未执行）✓。
- **R4 σ 公式/前置门**：`σ²_R4(c)=mean_{a<b}||P⊥(f_a−f_b)||²/(K−1)`，per context（cell,drug,role）；F_pair 用共享 context 的 σ²_R4(c)；每 context ≥2 plans、σ² 有限/正、排除 pair≤5%（否则 coverage）；n_legal_A2=176,934≥17,004.4 ✓。
- **D2/D3**：D2 per-context F_self 中位 coverage∈[.5,2]≥.85 + 全局中位∈[.5,1.5] + overall F_self FPR≤.10（ratio p95/p05 仅诊断）；D3 overall FPR≤.10 + worst-context≤.25 + context-FPR p95≤.20；R4 合成 .875/.813/.0439/.121/.076；F_crit=2.60 仅在 D2+D3 全 PASS 时保留，不缩放 observed/不改阈值 ✓。
- **零模型/执行**：N0-strat pooled（分层 χ²₃/3）、N1-R4 per-cell bootstrap（context-specific σ²_R4(c)/2 噪声）、N=500 seed=20261029；D1→D2/D3→D7→D6 pilot→observed→N0→N1→D4/D5；≈2,500 模拟；caps wall≤900s/CPU≤2h/8GB；两跑/无 telemetry；失败类别统一 ✓。
- **边界**：A.1/A.2 不重判；A.2.2 前不进 P2/S2/H_A2；阳性仅开发性存在性、阴性仅 `no_joint_contradiction`；不称生物学/机制/迁移/决策收益/新颖性；non-blind/peeked ✓。
- **披露**：合成 n_plans/context 6→12、coverage .90→.85（48 contexts 二项容差）、新增 context-FPR p95≤.20；candidate selection 只用合成 ✓（C194 是问题触发/诊断，不是 P1 effect；见 §2-3 的披露措辞）。

**结论：可提交 Lead 批准 A.2.2 data-only P1 重跑（0 新 wells；不进入 P2/S2/H_A2）。**

## 1. 逐条判决

| # | 项 | 判决 |
|---|---|---|
| ① | C194 复述/A.1 不可解释性 | **PASS**：D2 median .4153、mean .9700、p95 3.61；d_avg=(r1−r4)/2；异方差；单一全局 σ 只校准均值；P1 未执行；A.1 仍不可解释。 |
| ② | 候选 σ 表/选择规则/primary R4 | **PASS**：R0/R1/R2 均不 eligible，R4 唯一 eligible；规则写死、合成校准、不依赖 A.2 observed；primary R4。 |
| ③ | R4 σ 公式/前置排除比例门 | **PASS**：per-context full-profile plan-pair 差；≥2 plans、排除≤5%；F_pair 用 context σ；n_legal 门。 |
| ④ | D2/D3 新门/F_crit 条件 | **PASS**：coverage≥.85 + global median∈[.5,1.5] + FPR≤.10；overall≤.10 + worst≤.25 + p95≤.20；R4 合成值通过；F_crit 条件化。 |
| ⑤ | null 分层/bootstrap/预算/失败类别 | **PASS**：N0-strat/N1-R4、N=500/seed；≈2,500 模拟；caps；两跑/无 telemetry；失败类别统一。 |
| ⑥ | 披露/边界 | **PASS**：合成参数/阈值变化/新增 p95 门披露；边界与 A.1/A.2 不重判；不进入 P2/S2/H_A2。 |
| ⑦ | 总判决 | **approve_a22_to_lead**。 |

## 2. 非阻塞实现备注（写入实现/记录；不改变批准范围）

1. **F_self_check/coverage 的精确公式**：DESIGN D2 只写"per-context F_self_check"，没有给出 R4 归一化后的 F_self_check 等式与 coverage 的聚合/分母；执行实现必须写死：例如 `F_self(p,q)=[||P⊥(f_p−f_q)||²/(K−1)]/σ²_R4(c)`（plan pairs in context）、per-context coverage=该 context 中 F_self∈[0.5,2] 的比例、全局中位、context-FPR p95 的聚合；不得在执行时另选口径。
2. **R4 σ 的自包含（self-inclusion）**：`σ²_R4(c)` 的 mean 包含被检验 pair 自身，因此 F_pair 的期望并非严格 1（context 计划对少时更明显；D2/D3 用合成校准吸收）。实现/记录应明写这是 **resubstitution/finite-sample** 校准，不得声称"独立尺度"；建议同时报 **leave-one-pair-out** 尺度敏感性（不作主判定），并确认在真实 context plan 数下 F_self coverage 仍≥.85。
3. **C194 披露措辞**：A.2.2 的问题与阈值由 C194 **observed A.2 D2 诊断**触发（A.2 P1 未执行）；"只用合成校准、不看 A.2 observed"应准确写为"**candidate selection/校准只用合成；C194 仅用于问题诊断与预设阈值，不用于 A.2 P1 observed 选择**"，避免读成"完全未看 observed"。
4. **预算**：≈2,500 模拟（N1 500 + N0 500 + 诊断 1,500）的 wall/CPU 估计需在实现后 pilot 测试（caps 900s/2h/8GB）；不得超限后减 N_perm/换分析；两跑输出 SHA/JSON 无 telemetry。
5. **R4 前置排除**：若 context<2 plans 或 σ² 非有限/非正导致排除 pair>5%，只写 `design_invalid: coverage`，不进入 F 推断；被排除 pair/context 清单与计数写入 diagnostics；n_legal_A2 用 A.2 legal（176,934 可参照）门≥17,004.4。

## 3. Lead 批准文本（建议）

> **批准范围**：仅批准 R201-A.2.2 的 **data-only P1 重跑**（0 新 wells；不读取新响应做效应；不做生物学/机制/迁移/决策收益/新颖性主张）；不批准 P2/S2/H_A2；A.1 `p0p1_negative` 与 A.2 `design_invalid: scale_mismatch` 不重判。
>
> **冻结**：数据/O'Neil batch1 complete-case/target30/完整 4×4/|U|=340,088；A.2 legal 规则（σ_obs_A2=σ_w_hat/2≈.0910607，n_legal_A2≥17,004.4）；R4 per-context σ²_R4(c) 公式（full-profile plan-pair 差；≥2 plans；排除≤5%）；F_pair 用共享 context σ²_R4(c)；D1–D7 先于 P1；D2（per-context coverage≥.85 + global median∈[.5,1.5] + overall FPR≤.10）、D3（overall≤.10 + worst≤.25 + context-FPR p95≤.20）；F_crit=2.60 仅在 D2+D3 PASS 时保留；N_perm=500（seed=20261029）、BH q=.05、阳性三条件同 A.1；primary null=N0-strat、per-cell=N1-R4；≈2,500 模拟；wall≤900s/CPU≤2h/8GB；两跑逐字节/JSON 无 telemetry；失败类别统一；阳性仅开发性存在性、阴性仅 no_joint_contradiction；non-blind/peeked；禁止用 A.1/A.2 observed 改规则/阈值、减 N_perm、把阴性写"矛盾不存在"、把阳性写生物学/机制/迁移/决策收益。
>
> **执行前**：实现 F_self_check/coverage 精确公式（见 §2-1）、R4 self-inclusion 披露/leave-one-pair-out 敏感性、C194 披露措辞、预算 pilot；全部通过后再执行 P1。

## 4. 声明

- **本轮不运行 P1/不拟合/不读 O'Neil 响应做效应**：只读 A.2.2/A.2-EXEC 产物与 C194 记录；只写本文件与 `tmp/`；未改 A.2.2 产物。
- **总判决：approve_a22_to_lead**（仅 A.2.2 data-only P1 重跑；0 新 wells；不进入 P2/S2/H_A2；A.1/A.2 不重判）。上述 5 条为非阻塞实现备注；执行后资格门仍先于 P1。

**一句话：v0.2 的 S2/F_self/legal 修正已被 C194 证实不足以处理 context 异方差（D2 median .4153、p95 3.61）；A.2.2 的 R4 per-context fuller-profile σ（.875 coverage/.0439 FPR/.121 worst/.076 p95/.183 power，唯一 eligible）、D2/D3 重设计、N0-strat/N1-R4、预算/失败类别/边界均已核验一致——判 approve_a22_to_lead，仅批准 data-only P1 重跑（0 新 wells；不进入 P2/S2/H_A2；A.1/A.2 不重判）。**
