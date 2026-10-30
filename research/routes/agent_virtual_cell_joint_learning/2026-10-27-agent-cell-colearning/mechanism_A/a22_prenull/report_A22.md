# R201-A.2.2 报告：异方差稳健 σ/零模型/诊断预注册（C194 后；本轮不运行 P1）

2026-10-28。角色：独立审计/设计修订员（未参与 R197/R200 模型开发）。任务 task-123（A.2.2）。
**只做设计/算术/合成校准：未运行 P1、未读 O'Neil 响应做效应、未拟合预测；A.2/A.1 不重判；A.2.2 通过前不进 P2/S2/H_A2；non-blind/peeked；0 新 wells。**
- 问题定义：[PROBLEM_A22.md](PROBLEM_A22.md)（`69605BBC…49D7E334`）
- 执行设计：[DESIGN_A22.md](DESIGN_A22.md)（`EAC8EA10…84531E76`）
- 合成校准/算术：[sigma_robust_A22.py](sigma_robust_A22.py)（`EEDFEF77…A9996858`）→ [sigma_robust_A22.json](sigma_robust_A22.json)（`12DC9855…53D6A2`）
- 记录/用量：[record_A22.md](record_A22.md)、[usage_A22.json](usage_A22.json)
- 依据：C194（A.2-EXEC：D2 FAIL、P1 未执行）、`a2_exec/` 产物、A.2 v0.2 链、challenge_A2；**未改 A.1/A.2/A2-EXEC/P0P1 产物**。

## 0. C194 复述与不可解释性

A.2-EXEC 在预注册 D2 门失败：**`design_invalid: scale_mismatch`，P1 未执行（P1=None）**，无 positive/negative；A.1 `p0p1_negative` 仍不可解释（仅"冻结 null 下未检出"）。

| C194 | 数字 |
|---|---|
| D2 | F_self_check **mean 0.9700 ✅ / median 0.4153 ❌**；分位 p5 .04 / p25 .17 / p50 .42 / p75 1.00 / p95 3.61 / max 67.18 |
| σ（A.2） | σ_w_hat=0.092919；S1=0.00107924；σ_pair²_A2=0.00110139（/S1=1.0205） |
| 机制 | `d_avg=(r1−r4)/2`；同 wells 半拆差在 context 间强异方差（p25 .17 vs p95 3.61）；单一全局 σ 只能校准均值 |
| 其它 | D1/D3/D6/D7 PASS；n_legal_A2=176,934；P1 未执行 |

## 1. 候选稳健 σ（合成校准；不读 O'Neil 响应、不依赖 A.2 observed）

合成设置（预注册）：6 cells × 8 contexts × **12 plans**、K=M=4；true σ²(c)~lognormal(sd=.7)（p25 .781/p50 1.079/p95 3.898）；H0=shared f+context 异方差噪声；违例=一条 plan profile 形状偏移 2σ(c)；seed=20261031。

| scheme | H0/假设 | 实现 | coverage | FPR@2.60 | worst-context FPR | power | eligible |
|---|---|---|---|---|---|---|---|
| **R0** 全局均值（A.2 基线） | shared f+iid（同方差） | 单一全局 σ | 0.500 | 0.0723 | **0.682** | 0.129 | ❌ |
| **R1** per-context（half-split） | context 内 iid；异方差允许 | σ²(c)=0.5×mean_plans ||P⊥d_A||²/(K−1)；F_pair 用共享 context σ²(c) | **0.917** | 0.0739 | **0.424** | 0.171 | ❌（worst>0.25） |
| **R2med** 稳健全局中位 | 稳健位置 | median_c σ²(c) | 0.604 | 0.1222 | 0.803 | 0.129 | ❌ |
| **R2trim** 稳健全局截尾 | 稳健位置 | 20% trimmed mean | 0.604 | 0.1206 | 0.803 | 0.129 | ❌ |
| **R4** fuller-profile resampling（**primary**） | shared f；同 context plan-pair 可交换（H0 下 pair 差=纯噪声） | σ²(c)=mean_{plan pairs in c}||P⊥(f_a−f_b)||²/(K−1)；F_pair 用共享 context σ²(c) | **0.875** | **0.0439** | **0.121**（p95 .076） | **0.183** | ✅ |

**选择规则（预注册，只用于合成校准）**：eligible ⇔ coverage≥**0.85**（48 contexts 二项容差）∧ overall FPR∈[0.02,0.10] ∧ worst-context FPR≤0.25 ∧ context-FPR p95≤0.20；eligible 中取 power 最高；并列 R1>R2med>R2trim>R4>R0；无 eligible→`design_invalid: null_calibration`。
**结果：primary = R4_full_profile（唯一 eligible）**；R0（A.2 基线）coverage .500 复现异方差失效；R1 coverage 高但 worst-context FPR .424 超门；R2 稳健全局 coverage .604（稳健位置≠逐 context 校准）。

## 2. D2/D3 重设计（替代 A.2 全局中位门；不用 observed 后验）

- **D2（scale_mismatch）**：① per-context F_self_check 中位 coverage∈[0.5,2] **≥0.85**；② 全局 F_self_check 中位∈[0.5,1.5]；③ overall F_self_check FPR@F_crit≤0.10；④ σ²_R4(c) 的 p95/p05 ratio 仅诊断报告。
- **D3（noise_calibration）**：① overall FPR@F_crit≤0.10；② **worst-context FPR≤0.25**；③ **context-FPR p95≤0.20**。
- **F_crit 条件**：D2+D3 全 PASS 才保留 **F_crit=2.60**（R4 标准化后 F~χ²₃/3）；否则 `design_invalid: scale_mismatch`；不缩放 observed F、不改阈值。
- **F_pair 归一化**：`F_pair=[||P⊥(f_p−f_q)||²/(K−1)]/σ²_R4(shared context)`；pooled/per-cell 同用；不再用全局单一 σ。

## 3. A.2.2 执行设计（要点；完整见 DESIGN_A22.md）

- **不变**：数据/target30/完整 4×4、**|U|=340,088**、**A.2 legal 规则不变**（全局 σ_obs_A2、阈值≈0.0910607；n_legal_A2≥17,004.4）、S-add 族、F_pair/T_c/pooled 结构、**N_perm=500**、BH q=0.05、阳性三条件。
- **仅改**：σ² 用 **R4 per-context**；F_pair 用共享 context σ²_R4(c) 归一化；null 分层/参数化 bootstrap（context 异方差）；**D2/D3 重设计**。
- **流程**：D1 → D2/D3 → D7/G1–G5 → D6 pilot → observed F/T → N0-strat(pooled χ², 500) → N1-R4(per-cell bootstrap, 500, seed 20261029) → D4/D5 → 阳性三条件；任一失败→对应 `design_invalid`，不进入 P1 判定。
- **预算**：data-only、0 新 wells；wall≤900 s、CPU≤2 h、内存≤8 GB；≈2,500 模拟（N1 500 + N0 500 + 诊断 1,500）；超限→`design_invalid: compute_budget_exceeded`（不减 N_perm）；两跑逐字节、JSON 无 telemetry。
- **失败类别统一**：`scale_mismatch`（D1/D2/F_crit）、`noise_calibration`（D3）、`null_calibration`（D4/D5）、`compute_budget_exceeded`（D6）、A.1/A.2 既有类别（coverage/identifiability/leakage/family）。
- **解释边界**：阳性仅"本资源/本族/本设计下存在联合矛盾（开发性）"；阴性仅 `no_joint_contradiction`（不写"矛盾不存在"）；pair 级仅描述性；不称生物学/机制/迁移/决策收益/新颖性；non-blind/peeked；A.2.2 通过前不进 P2/S2/H_A2；A.1/A.2 不重判。

## 4. 边界与不主张

- A.2.2 是新预注册；A.2 `design_invalid: scale_mismatch` 与 A.1 `p0p1_negative` 均保持原样；不得用 A.2/A.1 observed 结果后验选 scheme/阈值/门。
- 未运行 P1、未读 O'Neil 响应做效应；合成校准只用于选 scheme/校准 D2/D3（机制已知、无 O'Neil 响应）。
- 未执行 P2/S1/S2/H_A2；0 新 wells；不称新颖性/生物学/机制/迁移/决策收益；技术重复≠独立培养；不拼 ΔEMAX。

## 5. 产物与确定性

| 文件 | SHA256 |
|---|---|
| `PROBLEM_A22.md` | `69605BBCEA37ECFA2783F08BCC2EF194C89971F637435A853D25C46849D7E334` |
| `DESIGN_A22.md` | `EAC8EA10FEDC6DA5F3D0293C2C43BBCD82C9ECB6A43EF2CB4714492284531E76` |
| `sigma_robust_A22.py` | `EEDFEF77D71A4BA00B31BED88F7783237E0C9B903D9FCBD79D5706C8A9996858` |
| `sigma_robust_A22.json` | `12DC9855A567D7ECF333F6718BB996E3EDE9BFCBDA095E09263CD79BF053D6A2` |
| report/record/usage | 见 `usage_A22.json` |

**确定性**：同脚本两跑 `sigma_robust_A22.json` 逐字节一致（SHA `12DC9855…53D6A2`；wall 各 0.5–0.6 s）；JSON 键排序/无时间戳/allow_nan=False；文档 SHA 写入 JSON。

## 6. 建议

1. **提交 A.2.2 预注册（PROBLEM_A22 + DESIGN_A22 + sigma_robust_A22）做独立挑战**；挑战通过后请 Lead **批准 A.2.2 data-only P1 重跑**（0 新 wells；不进 P2/S2/H_A2；A.1/A.2 不重判）。
2. 挑战重点：R4 σ 公式/前置排除比例门/F_pair 归一化；D2/D3 新门（coverage≥0.85、worst-context FPR≤0.25、context-FPR p95≤0.20）；null 分层/bootstrap 实现与 seed/N_perm；预算/失败类别/两跑/schema；解释边界。
3. A.2.2 执行前不解释 A.1/A.2 negative；不写"矛盾不存在/机制/迁移/决策收益"。
