# R198-A1v3 复审（challenge_A1_v3.md）——同一挑战者对 v2 复审 5 必改与 Lead 已决事项的只读复审

2026-10-27 · 挑战者：endpoint-auditor（task-36/42 同一挑战者；未参与 A1 设计）· 对象：`research/2026-10-27-innovation-scouting/conflict_signal/{spec_v3.md, protocol_draft_v3.md, REVISION_A1_v3.md, record_v3.md, usage_v3.json}` + Stage 0 实现（`stage0/{relations_check_config.json, relations_check.py, SELFCHECK.json}`）。
方式：**只读审查 + 纯算术/元数据复核**（`tmp/challenge_a1v3_checks{,2,3,4,5,6}.py` → `tmp/challenge_a1v3_checks*.json`）；**不运行效果/relations_check/体检/MDE 预检，不读任何 S/U 或参考响应，不改 A1 v1/v2/v3 产物**。
完整性：v3 的 spec/protocol/REVISION 三件 SHA 与 `usage_v3.json` 的 `deliverables_sha256` 登记一致（spec `DE92C65E…BF30E`、protocol `3FC57D72…503D`、REVISION `79789420…A8A4A0`）；`record_v3.md` 与 `usage_v3.json` 为自引用文件（未在 usage_v3 内自登记），本挑战记录的复算 SHA 为 record `889E89E8…620D7`、usage `85887F53…DF707`；v1/v2 文件 SHA 未变（spec_v2 `52959E29…`、protocol_v2 `15C7DA58…`、REVISION_A1 `5CF8661F…`、relations_check `00D087AD…`、record_v2 `C7C8C2FD…`、usage_v2 `9AE2C942…`）；Stage 0 现有 `relations_check_config.json` `F08587AB…300AB`、`relations_check.py` `74F36C9E…37E5B`、`SELFCHECK.json` `D86CE2F6…E2ECE9`（未同步 v3，见 ⑤）。

## 0. 总判决

**revise（≤5 必改）；当前版本不得进入 Stage 0 冻结；Stage 0（P0a-metadata）按 v3 自己的验收规则会返回 `data_unavailable`（不是资源不足，而是冻结的 115/229 与 S 侧预检+S=24 算术不相容）。**
- **不是 stop**：v3 把 v2 复审的多数问题实质修好了（MDE 标注、n–p1 表、P0a 只用 2.0σ、覆盖分母赋值、P0b 独立生成器、M_setup 正式模型、惩罚拟合/δ_fit、J 族、κ 三法、退出分母、64/16 废弃、P0a–P0d 清单/短路）。这些应保留。
- **但 Lead 已决的"跨 tissue 池化"没有解决 v2 指出的算术不可行**：在 v3 选定的 A0 matched 96 关系宇宙上，**229/229 个候选关系都是单 tissue**（见 §2.1），池化是**空操作**；Pancreas 的 29 细胞仍不足以支撑 24 reference + 12 S；且 P0a-metadata 的 S 侧预检与"覆盖 ≥115/229"在 S=24 下最多只能到 **114**（Breast/Colon 仅 112）。
- **若 Lead 不接受修改 115/S 或关系宇宙**：诚实结局是**在跑 Stage 0 之前判 `data_unavailable`/stop**，不要用一轮 Stage 0 去"确认"一个算术上已知不可达的目标。

**最致命 3 条**

1. **池化在所选关系宇宙上是空操作（决定性）**：A0 matched 96 上的候选关系 **229 条全部单 tissue**（span：Breast 134 / Colon 37 / Pancreas 58；**0 条多 tissue**）；matched 宇宙 31 个 anchor 中 20 个只在 1 tissue 有候选键。因此"tissue 进 nuisance / 跨 tissue 平均"在**任何一条关系内部都不可估计**（tissue 在关系内是常数，被 μ_r 吸收），"pooled context 解决 Pancreas 算术"是**未发生**的：Pancreas 关系仍要 24 reference（A/B 各≥12）+ 12 S（同 Cond_r），而 Pancreas 总共只有 **29** 个 Original 细胞（matched 28；reference 24 后剩 5）→ **58 条 Pancreas 候选永远过不了 S 侧 ≥12**。v3 的"外部有效性=跨 tissue 平均"没有数据基础，必须改词或改关系宇宙。
2. **覆盖 115/229 与强制 S 侧预检在 S=24 下算术不相容**：S=24 从剩余 41 细胞抽；对 A/B≥12 的 149 条候选（我的示例切分；v3 估 ≈154）做"至少 12 个 S 细胞满足 Cond_r"的预检：
   - 随机 S 抽取 200 次：通过数 min 13 / median **69** / max 94；
   - 贪心启发式：93；
   - **MILP 精确上界：全候选 114，Breast/Colon-only 112**（≤115）。
   即：**即使 S 按最有利方式选，也达不到 115**；29 条 Pancreas 候选在 A/B 池内恒 0。v3 的 P0a-metadata 规则（预检后候选 <115 → `data_unavailable`）会把设计判死；Lead 的 115 与 S=24/precheck 需要重新一起定（见必改 2）。
3. **Stage 0 实现未同步 v3，且代码结构上无法发现"池化空操作"**：config 仍是 `context_mode="per_tissue"`、`interval_utility_check_enabled=true`、`utility_gate_required_for_run=true`、`coverage_denominator=null`、`min_relations_per_tissue=3`、`min_reference_per_tissue=28`（与 v3 "按 tissue 比例分层"不一致：比例应为 ≈29/31/24）、`require_matched_conditions_subset=false`（与 v3 "reference 84 ⊆ matched 96"矛盾）；`relations_check.py` **没有 S 侧预检、没有 matched 限制、没有 tissue-span/非空池检查**；`pooled_across_tissue` 只是把分组标签换成 ALL——在单 tissue 候选上结果与 per_tissue **相同 229**。所以"把 context_mode 改成 pooled"不能修好任何东西。two-key run gate（`--confirm-run` + real_run_enabled=false）能防误跑（PASS 部分），但同步清单必须加入 **non-vacuity gate**（若宣称 pooled，主族候选必须跨 ≥2 tissue；否则 `data_unavailable`/改口径），否则跑出来的 PASS/FAIL 都无意义。

## 1. 六项判决摘要

| # | 复审项 | 判定 | 一句话依据 |
|---|---|---|---|
| ① | tissue 算术/context（pooled、n_ctx/α、S=24 与 S 预检、84⊆matched96、S24/U17、覆盖 115/229、per-tissue 敏感性） | **FAIL** | 229/229 候选单 tissue（0 多 tissue）→ 池化空操作；Pancreas 24+12>29 仍不可行；S 预检下覆盖最多 114<115；84/24/17 与 S24/U17 算术本身正确；"per-tissue 仅敏感性"与"所有候选都是单 tissue"矛盾 |
| ② | P0a 验收/顺序（2.0σ、效用移 P0d、分母 229、清单+短路） | **WEAK** | 2.0σ/效用移 P0d/分母冻结/短路清单都已写（PASS）；但分母 229 与 S 预检不相容、P0a-metadata 未实现、config 未同步 |
| ③ | MDE/统计（p1≈0.9307、n–p1 表、sign test+cluster、P0b 生成器、P0c CP/n_eff） | **PASS（minor WEAK）** | 我逐项复算：MDE(80%,n=12)=p1≈0.93074（power 0.7998）；n–p1 表的 α/power 全对；p1≥0.95 保守目标 0.8816；sign test+cluster/置换敏感性；P0b iid/依赖独立生成器；P0c CP 阈值需写精确（0/29→0.098、0/40→0.072、1/46→0.099、1/47→0.097） |
| ④ | M_setup/惩罚拟合/J/κ/退出上限 | **WEAK** | M_setup 正式模型+共享似然+惩罚公式/δ_fit/5-fold 已写（PASS）；但 τ_t 在单 tissue 关系上不可识别（池化空操作的直接后果）；k_E 未定义；退出上限 `max(0.15,P95)`+"P95 超硬天花板即 invalid"使 caps 恒为 0.15/0.10（P95 派生规则退化）；κ 三法可执行 |
| ⑤ | 统一/接口/Stage 0 代码同步 | **WEAK** | 64/16 废弃、84/24/17 统一、A4/A5/Stage1 三类/(iii) proxy/措辞模板都已写（PASS）；但 config 六处仍 stale、无 S 预检/matched 限制/非空池检查、pooled 模式空操作；two-key gate 可防误跑 |
| ⑥ | 总判决 / 是否可进 Stage 0 | **revise（≤5 必改）；当前不可进 Stage 0** | 见 §0/§2；修完必改 1–5 并获 Lead 对覆盖/S 的重新决定后才可进 Stage 0 |

## 2. 逐项取证

### 2.1 ① tissue 算术 / context（**FAIL**）

**v3 已落实的（PASS 部分）**：§2.1 写了 Original 51/45/29、matched 33/35/28 的可行性表，并正确写出 tissue-specific 需 24+12=36>29 的不可行结论；`n_ctx_min=12`、`α=0.01` 保持；S=24（24≥12）；P0a 增加 S 侧 Cond_r 覆盖预检；84/24/17 统一；reference 84（A42/B42）⊆ matched 96；S 24/U 17 从剩余 41；覆盖分母 229→≥115 写死；per-tissue/Breast-Colon 仅敏感性披露。**这些文字都在，且大多正确。**

**我的复核（关键反驳）**：
1. **候选关系在 A0 matched 宇宙上全是单 tissue**。从 `matched_conditions.csv`（9,154 个 matched cell×condition 键）枚举候选 `(anchor, anchor_conc, library_conc, unordered library pair)`，229 条候选的细胞 tissue span：**Breast 134、Colon 37、Pancreas 58、多 tissue 0**；对应的 anchor 在 matched 宇宙中 31 个（20 个 1 tissue、6 个 2、5 个 3），但同一 `(anchor, 两浓度, library pair)` 的 matched 键只落在单一 tissue 内。→ **"pooled across tissue" 与 "per_tissue" 在这 229 条上产生同一集合**（我复核 pooled_total=229、per_tissue_total=229），tissue 随机效应在每条关系内是常数，τ_t 不可识别；所谓"跨 tissue 平均"没有任何跨 tissue 的对比可平均。
2. **因此 Pancreas 不可行性没有被解决**：Pancreas 关系仍需要 reference A/B 各 ≥12（24 个 Pancreas 细胞）+ S 侧 ≥12 个满足 Cond_r 的细胞；Pancreas 总共 29 个 Original 细胞 → 剩余 5 <12。**58 条 Pancreas 候选在 S 侧恒失败**；这与是否"pooled"无关，因为其他 tissue 的细胞没有该 Pancreas anchor/library pair 的测量条件。
3. **S 侧预检 + 覆盖 115 不相容（见 §2.2）**：S=24 下 MILP 上界 114（全候选）/112（Breast/Colon），永远 <115。
4. **"per-tissue 仅敏感性"的措辞与实际相反**：既然所有候选都是单 tissue，per-tissue 结构就是唯一真实结构；把 per-tissue 叫"敏感性"、把"pooled"叫主族，是把同一个估计换标签，没有增加任何跨 tissue 信息（且外部有效性声明"跨 tissue 平均"不成立）。
5. **算术本身的正误**：84⊆matched96 ✓（84≤96）；A42/B42 ✓；S24/U17 ✓（84+24+17=125；matched 剩余 12 + unmatched 29 = 41 ✓）；Pancreas 36>29 ✓；S=24 按 tissue 分层 ~8 <12 ✓。这些 PASS，问题在 pool 的定义与后果。

### 2.2 ② P0a 验收/顺序（**WEAK**）

**PASS**：P0a 只用 `w_r≤2.0σ_r`；效用宽度移到 P0d（`blocked_by_utility_definition` 不再阻塞 P0a）；覆盖分母 229 冻结；P0a-metadata → relations_check → P0b → P0c → P0d 按序+短路清单；失败类别；预算/墙钟；two-key run gate。

**WEAK/FAIL 子项**：
1. **覆盖 115/229 与 S 侧预检在 S=24 下不相容（决定性）**。用 A42/B42 示例切分（A=(Breast14,Colon16,Pancreas12)，B 同）：
   - A/B 均≥12 的候选 149 条（v3 估 ≈154；同量级）；
   - S=24 从剩余 41 抽，候选通过条件 = 其 S 中满足两侧 library/两浓度元数据的细胞数 ≥12；
   - 随机 200 次：min 13 / median **69** / max 94；
   - 贪心：93；**MILP 精确上界：全候选 114，Breast/Colon-only 112**（`tmp/challenge_a1v3_checks6.py`）。
   - 由于 Pancreas 候选 29 条在 A/B 池内（58 条在网格内）结构性不能通过，网格层面最多 = 114（或 Breast/Colon 112），**<115**。v3 的规则"预检后候选 <115 → data_unavailable"必然触发；`P0a-metadata` 的 PASS 条件（≥115）在 S=24 下**不可达**（不是"需实测才知道"，是上界已 114）。
2. **P0a-metadata 尚未实现**：config 没有 S 侧预检键、没有 matched 限制、没有 tissue-span 检查；code 无对应逻辑；预算 ≤10 min 可行但需要写代码。v3 §7 的同步清单是"下一轮"——可以，但必须把本项列为**Stage 0 前置**（否则跑的是 stale 实现）。
3. **分母 229 的语义**：若主族实际只能是 Breast/Colon（Pancreas 被结构排除），分母应写成 171（或"post-precheck pool"），否则 115 是对一个不可达集合的要求；若保留 229，必须把 Pancreas 关系明确标为"结构不可测"并相应调整覆盖定义（见必改 2）。
4. **S 选择规则未写**：S=24 从剩余 41 抽，但"随机"还是"覆盖最大化（metadata-only）"没写；两者对预检通过数影响巨大（随机 median 69 vs MILP 114）。必须先冻结规则并算期望通过数；若选覆盖最大化，S 的组成就是设计的一部分（仍不读 y，合法），但必须写死。

### 2.3 ③ MDE / 统计（**PASS，minor WEAK**）

**我逐项复算（`tmp/challenge_a1v3_checks.py`/`checks2.py`）：**
- n=12、α=0.01：拒绝域 k≥11，P(X≥11|p=0.5)=**0.00317383**；k=12=**0.00024414**；✓
- **MDE**：80% 功效在 p1=**0.930743**（精确；power=0.7998），v3 写 p1≈0.9307 ✓；p1=0.95 → power=**0.88164**（保守目标）✓；p1=0.90 → 0.65900 ✓；n=12 时 p1=0.93 → 0.79668 ✓。
- **n–p1 表**：n=11/k=10（α=0.005859, power(0.95)=0.8981）✓；n=14/k=12（α=0.006470, power(0.90)=0.8416）✓；n=19/k=15（α=0.009605, power(0.85)=0.8556）✓；n=7/k=7（α=0.0078125, power(0.98)=0.8681）✓——**全对**。
- sign test 主统计量 + cluster（细胞/药对/批）bootstrap/置换敏感性 + 不一致 → `ambiguous_conflict` ✓。
- P0b 独立生成器：iid（ρ=0,τ=0）与依赖（ρ∈{0.2,0.4,0.6}、κ∈{1,3,10}）；只用参考方差/相关参数+合成长标签；不得注入参考违反结构；每类 ≥30、recall/precision≥0.80、type-I≤0.10；P0b/P0c 依赖模型校准 ✓。
- P0c：ρ×κ=4×3 格、每格 ≥1,000 批；`n_eff=n_ctx/(1+(n_ctx−1)ρ̂)`；80%±0.05；type-I 点≤0.05 且 CP95 上界≤0.10。
- **CP 规则需写精确（minor WEAK）**：我复算 Clopper–Pearson 95% 上界：`0/20=0.139`、`0/29=0.098`、`0/40=0.072`、`0/47=0.062`；`1/40=0.113`、`1/46=0.099`、`1/47=0.097`、`1/51=0.090`。所以"追加到 ≥40"只对 0 事件充分（0.072），对 1 事件需 ≥46；v3 的"≥40 或 47 全 0/≤1"方向对但表述含混（"0/20 类不足"是什么？），必须写成公式："若观测 0 事件，n≥29 已足够（0/29=0.098），预注册取 n≥40；若观测 ≤1 事件，取 n≥47；否则按 CP 公式报告上界"。
- **n–p1 表与 context 可得性**：n=14/19 行要求每条关系有 14/19 个 S 上下文；S=24 总量允许，但**每条关系**的 S 侧预检只保证 ≥12（v3 §2.2）；若某关系只有 12–13 个 S 细胞，则"p1<0.9307 时增大 n"不可执行 → 应落 `insufficient_precision` 并记录；v3 未写这条联动，必须补。

### 2.4 ④ M_setup / 惩罚拟合 / J / κ / 退出上限（**WEAK**）

**PASS**：M_setup 正式概率模型（`y=φ^Tθ+u_tissue+v_batch+ε`，`u~N(0,τ_t²)`、`v~N(0,τ_b²)`、`ε~N(0,σ_i²γ²)`；M_i 固定 γ=1,τ_b=0；共享预测似然；5 折 by cells）；惩罚准则 `score=−2·loglik_heldout+λ_k·k_E·log(n_eff)`、λ_k∈{0.5,1,2} 主 1、`n_eff=n_ctx/(1+(n_ctx−1)ρ̂)`、`δ_fit=2.0`；J 候选族（单例/贪心前向≤5步/结构族，≤200，J_max=min(5,ceil(0.1|R|))，60 s）；κ 三法（nuisance-only 残差/留出半 B/置换零）与污染诊断；σ 带一致性；退出上限 operational 分母（eligible S 单元）+ P95 派生 + 硬天花板。

**WEAK/FAIL 子项**：
1. **τ_t 不可识别（池化空操作的直接后果）**：229 条候选全部单 tissue，S 单元在同一关系内 tissue 常数 → `u_tissue` 与 μ_r 共线，τ_t 无法估计；M_setup 的 `τ_t` 在单 tissue 关系上是边界参数。必须：要么从 M_setup 删掉 u_tissue（τ_t 仅用于跨关系/多 tissue 情形），要么承认 M_setup 只能在多 tissue 关系上使用（当前没有）。否则 M_setup 的模型比较不可执行。
2. **k_E 未定义**：M_i/M_setup/M_ii(J) 的"自由参数个数"没有写出（M_i 的 θ 维数、M_setup 的 γ/τ_t/τ_b 计几个、M_ii(J) 释放 |J| 个关系时计 |J| 还是别的）。`δ_fit=2.0` 与 BIC 型惩罚（每参数 log n_eff≈4–7）的尺度没有对齐说明（2.0 在 AIC 尺度常见，但 score 是 BIC 型）。必须写死 k_E 计数表与 δ_fit 的尺度依据。
3. **退出上限公式退化**：v3 写 `冻结上限 = max(0.15, P95_notid)`、`max(0.10, P95_ambig)`，又写"若 P95 超过硬天花板（notid>0.15 或 ambig>0.10）→ design_invalid"。两者合起来：P95≤0.15 时 cap=0.15；P95>0.15 时 invalid → **cap 恒为 0.15/0.10，P95 派生规则没有任何效果**。必须改成可执行的二选一：(a) cap=固定 0.15/0.10，P95 只作为"设计是否可判"的诊断；(b) cap=max(ceiling,P95) 且不因 P95>ceiling 直接 invalid（但那会允许放松，与"不能降低"纪律冲突）。当前写法自相矛盾。
4. **J 的代价/多解**：v3 保留"最小代价可行 J"，但"代价"定义（释放关系数？区间宽度？Δ_pred(U)？）未写；多解并列 → ambiguous ✓；60 s ✓。需写死代价函数。
5. **κ 三法**：三法可执行、有污染诊断 ✓；但"以 (b)/(c) 为主"的判定阈值（什么算污染）未写；κ band 的宽度/来源未写死。WEAK。

### 2.5 ⑤ 统一 / 接口 / Stage 0 代码同步（**WEAK**）

**PASS**：64/16 废弃、统一 84/24/17（spec_v3 §0 第 9 条、REVISION §2）；A4/A5 接口保留（A4 决定 (iii)；A5 成本接口在修订通过前 Stage 2 不启动）；Stage 1 只判 (i)/(ii)/(setup)、(iii) proxy、措辞模板、P0a–P0d 清单/短路、预算/墙钟、失败类别、two-key run gate（`--confirm-run` + `real_run_enabled=false`）。

**WEAK/FAIL 子项（Stage 0 代码同步缺口）**：config 仍为 A1v2 设计——
- `candidate_enumeration.context_mode="per_tissue"` → 应为 `pooled_across_tissue`（但见 §2.1：在这个关系宇宙上切换无效，须加 non-vacuity gate）；
- `statistics.interval_utility_check_enabled=true` → 应 false；`utility.utility_gate_required_for_run=true` → 应 false（P0a 不依赖 utility）；
- `global_acceptance.coverage_denominator=null`、`coverage_min_abs=null` → 应 229/115（或按必改 2 修正后的值）；`min_relations_per_tissue=3` → pooled 主族下应删除/改语义；
- `cell_allocation.min_reference_per_tissue=28` → 与 v3"按 tissue 比例分层"不一致（比例约 29/31/24；28/28/28 也可解释为显式设计，但必须写明并以 SHA 冻结）；`require_matched_conditions_subset=false` → 应为 true（reference 84 ⊆ matched 96）；
- `design_sync_pending_v3` 仍写 "if unified to 64/16, update…" → 与"64/16 废弃"矛盾，应删除；
- code 无 S 侧预检、无 matched 限制、无 tissue-span/非空池检查；`pooled_across_tissue` 仅分组标签 ALL，候选结果与 per_tissue 相同（229）。
- 缺失 `P0a-metadata` 输出 schema（分配/网格/预检数/SHA）与 P0b/P0c 独立脚本接口。
- **结论**：v3 在文档层面统一了，但**实现层仍是 A1v2**；v3 §7 的"下一轮同步"是合理的，但必须把本次复审发现的**非空池检查**加入同步清单，否则实现者按 v3 §7 改完 config 仍不会发现池化空操作。

### 2.6 ⑥ 总判决 / 是否可进 Stage 0

**revise（≤5 必改）**；
- **当前不可进 Stage 0**：按 v3 自己的 P0a-metadata 规则，S 侧预检后候选 ≤114（Breast/Colon ≤112）<115 → `data_unavailable`。这不是"资源待实测"，是**上界已定**（MILP 114）。跑 Stage 0 只会产出一个由冻结阈值导致的 `data_unavailable`，且无法区分"资源不足"与"阈值/分配不相容"。
- **修完必改 1–5（含 Lead 对覆盖/S 的重新决定与 Stage 0 代码同步）后**：可进入 Stage 0：P0a-metadata（含 S 侧预检与非空池检查）→ P0a relations_check → P0b → P0c → P0d；P0d 允许 blocked（只阻止 Stage 1）。
- **若 Lead 坚持 115/229 + S=24 + matched96 不变**：应在 Stage 0 之前判 `data_unavailable`（或 stop），不要跑。

## 3. 五条必改（≤5）

1. **解决池化空操作与 Pancreas 结构性排除（①）**：写死 "229/229 候选单 tissue、0 多 tissue" 的事实（含 span 分布），然后二选一：
   - **(A) 保留 matched96，改命题**：主族 = per-tissue 的 Breast/Colon 关系（结构排除全部 Pancreas：24 reference+12 S=36>29），删掉"跨 tissue 池化/平均"措辞与"tissue 进 nuisance 可估"的声明；外部有效性明确限制；或
   - **(B) 改关系宇宙**：用 Original 125 全 screen 构造关系，主族限定为**真正的多 tissue 候选**（我复核 Original 上 33,132 条候选中 multi-tissue 1,336 条），reference 不再要求 ⊆ matched96（84 从 125 抽），重算 S/U/网格/覆盖与 84⊆matched 关系；需新 lineage 段与重审。
   - 若两者都不接受 → `data_unavailable`/stop（不跑 Stage 0）。
   - 无论 A/B，P0a-metadata 必须加 **non-vacuity gate**：宣称 pooled 时主族候选每条的 tissue span ≥2；否则 data_unavailable 或改标签。
2. **重定覆盖与 S 预检（①/② 的算术）**：Lead 需在以下之间重新决定并写死（附我给的数字）：
   - 若保留 S=24/匹配 96：覆盖分母改为 **post-precheck pool**（示例：Breast/Colon 171 网格 → 50%=86；或 AB 池 120 → 50%=60），验收 = post-precheck 的 ≥50% 且 R_min=20；不得再用 115/229；
   - 或增大 S（如 S=36；需同时改 reference/U 且 Pancreas 仍需 ≥24+12≤29 的算术检查，实际仍不可行）——不推荐；
   - 或明确"115/229 在 S=24 下不可达"→ 在 Stage 0 前 `data_unavailable`。
   - 同时写死 S 的选择规则（随机 vs metadata-only 覆盖最大化）与期望通过数；预注册"预检后候选 <R_min 才 data_unavailable"。
3. **同步 Stage 0 实现并加前置门（⑤）**：一次性改完 config 全键（见 §2.5）、实现 P0a-metadata（matched 限制、S 侧 Cond_r 预检、tissue-span/非空池检查、输出 schema/SHA），重跑 synthetic selfcheck（确定性、失败分支覆盖），冻结 config/script/SELFCHECK SHA，保留 two-key gate；在 P0a-metadata PASS 之前不得跑 relations_check。删除 64/16 残留说明与 `min_relations_per_tissue=3`（pooled 主族不需要）；`min_reference_per_tissue` 写清比例或显式 28/28/28 并说明与 matched 33/35/28 的关系。
4. **修 M_setup/惩罚/退出上限（④）**：由于单 tissue 关系 τ_t 不可识别，从 M_setup 删掉 u_tissue（或只在多 tissue 关系上启用并声明）；写 k_E 计数表（M_i/M_setup/M_ii(J)）与 δ_fit=2.0 的尺度依据（AIC vs BIC）；写 J 的代价函数；修退出上限逻辑（固定 0.15/0.10，P95 只作诊断，或 max(ceiling,P95) 且去掉"超天花板即 invalid"的矛盾）；κ 三法的主/敏感性选择与污染判定阈值写死。
5. **补 MDE/CP/n–p1 与 context 可得性的联动（③）**：写精确 CP 规则（0/29=0.098 已够、预注册 n≥40；≤1 事件预注册 n≥47；公式给出）；写 P0c 80%±0.05 的定义/每格 1,000 批/追加规则；把 n–p1 表与"每关系 S 侧可用上下文数"联动：若某关系只有 12–13 个 S 上下文，则 p1<0.9307 时无法增大 n → `insufficient_precision`（写死）；保留 sign test 主+cluster 敏感性；P0b 生成器明确"合成关系标签/方向从何而来"（不得注入参考违反结构，但需说明是否用参考关系定义）。

## 4. 保留项（v3 的实质进步，务必保留）

- §2.1 的 tissue 可行性表与"tissue-specific 24+12=36>29 不可行"的算术（正确）。
- n_ctx=12 / α=0.01 不放宽；S=24/P0a S 侧预检思路；84/24/17 统一；64/16 废弃。
- **MDE 修正**：p1≈0.9307（80%）；p1≥0.95 保守目标 0.8816；n–p1 表全部数值正确（我复算）。
- sign test 主 + cluster bootstrap/置换敏感性；P0b iid/依赖独立生成器；P0c n_eff/CP 方向。
- P0a 只用 2.0σ_r、效用移 P0d；P0a–P0d 清单/短路；预算/墙钟；失败类别；two-key run gate。
- M_setup 正式模型 + 共享似然；惩罚拟合公式/λ_k/δ_fit/5-fold；J 候选族；κ 三法；退出分母 operational 化。
- A4/A5 接口、Stage 1 三类、(iii) proxy_only、措辞模板、lineage（C174/C175）、不声称新颖性。
- REVISION §3 对"仍存缺口"的诚实披露（未运行/未验证/blocked/代码未同步）——应保留并把本次新发现（池化空操作、覆盖-预检不相容）加入。

## 5. 复核证据与本轮边界

- **脚本与输出**：`tmp/challenge_a1v3_checks.py`→`checks.json`（Original/matched tissue、候选网格；CP95：0/29=0.098、0/40=0.072、1/46=0.099、1/47=0.097）；`checks2.py`→`checks2.json`（matched 宇宙：per_tissue=pooled=229；A/B supply 149；S 侧随机 30 次通过数 min14/median62.5/max94；leftover eligible ≥12 有 118 条）；`checks3.py`→`checks3.json`（候选 tissue span：Breast134/Colon37/Pancreas58，**多 tissue 0**；anchor 20/31 单 tissue）；`checks4.py`→`checks4.json`（若用 Original 125 全 screen：33,132 候选、multi-tissue 1,336；reference 84 从 125 抽的示例）；`checks5.py`→`checks5.json`（S=24 随机/贪心：median 69/93）；`checks6.py`→`checks6.json`（**MILP 精确上界：全候选 114、Breast/Colon 112** <115）。
- **关键数字**：n=12 k≥11 p=0.00317383；80% 功效 p1=0.930743；power(0.95)=0.88164；n–p1 表 α/power 全对；CP 阈值如上；Original 125 细胞 Breast51/Colon45/Pancreas29；matched 96 Breast33/Colon35/Pancreas28；Pancreas 24+12=36>29；S=24 分层 ~6–10/tissue；候选 229 全单 tissue；A/B supply 149；S 预检上界 114（Breast/Colon 112）。
- **完整性**：v1/v2/v3 文件 SHA 与 usage_v3/record_v3 登记一致；`stage0` 三件 SHA 记录于页首（未同步 v3）；**未改任何 A1 产物、其它目录、INDEX/SYNTHESIS/git**；只新增本文件与 `tmp/`。
- **边界**：本轮**不运行效果/relations_check/constructive 体检/MDE 预检、不训练、不读响应值（只读 identity/condition/tissue 元数据做算术）**；所有数字是元数据/纯算术/协议审查，不是生物学或效果证据；挑战结论不构成对 A1 作者身份或既往记录的改写。

## 6. 给 Lead 的建议

- **裁决点**：必须先决定下面两个 Lead-level 问题，否则 Stage 0 无意义：
  1. **关系宇宙**：保留 matched96（则必须是 per-tissue Breast/Colon 主族 + 明确排除 Pancreas，删"跨 tissue 池化"声明），还是改用 Original 125 全 screen 的 multi-tissue 候选（则重算 reference/S/U/网格/覆盖并重审 lineage）；
  2. **覆盖阈值/S 分配**：115/229 与 S=24 不可并存（MILP 上界 114）；要么改覆盖分母/阈值（post-precheck 50%、≥R_min=20），要么先判 data_unavailable。
- 之后按必改 1–5 修订；修完由**同一挑战者**再做一次只读复审（符合原 challenge_A1 重审条件），通过后才进入 Stage 0（P0a-metadata 先跑）。**不要**在未解决 1/2 前跑 Stage 0——那只会产生一个由阈值造成的 `data_unavailable`，不能归因。
