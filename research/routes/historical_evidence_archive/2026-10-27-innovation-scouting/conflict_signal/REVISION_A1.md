# REVISION_A1 — 对 challenge_A1.md 的逐条回应（R198-A1v2）

2026-10-27。对象：独立挑战 [challenge_A1.md](challenge_A1.md)（task-36，判决 `revise`，≤5 必改）。本文件逐条说明修订落在 [spec_v2.md](spec_v2.md) / [protocol_draft_v2.md](protocol_draft_v2.md) / [relations_check_design.md](relations_check_design.md) 的哪些节；**原 spec.md/protocol_draft.md/prior_art.md/record.md 不改**（保留审计痕迹）。**本轮不运行效果/训练、不读响应做效果、不声称新颖性。**

## 0. 总览

| 挑战项 | 挑战判定 | v2 处置 | 状态 |
|---|---|---|---|
| ① X_flip 最小设计算术不可能 | FAIL | n_min=12、α=0.01、BH q≤0.10、MDE 推导写死（spec_v2 §3.1；protocol P4.6） | 已修；待 P0c 模拟复核 |
| ② 分类不可证伪（第四解释/顺序偏置/χ² iid/退出无上限） | FAIL→WEAK | 加 `setup_error` 第四解释与多解释比较（spec_v2 §2(iv)/§3.3；protocol P4）；依赖感知 χ²/κ、σ 带、d_rel 降级；退出上限 15%/10%（protocol P6） | 已修 |
| ③ 关系集不可执行/泄漏/混淆 | FAIL | 关系单位/Cond_r/池化、R_min=20/R_max=200、n_ctx=12、区间宽度、覆盖 50%、构造/校准半分离、S/参考 disjoint、screen nuisance、非重聚合 lineage（spec_v2 §4；relations_check_design 全篇） | 已修（协议可执行；尚未运行） |
| ④ 最小实验（体检/δ_min 顺序/失败类别/预算/U 成本） | WEAK | P0a–P0d 前置 + 注入体检阈值 + δ_min blocked + 失败类别 + 预算墙钟 + U 菜单/成本（protocol_draft_v2 P0/P5/P6/P8） | 已修 |
| ⑤ 谱系/纪律（标题混号/Stage1 两类/A4 协调/措辞） | PASS+minor | 标题改回 R198-A1；Stage 1 只判 (i)/(ii)/(setup)；A4/A5 接口段；措辞模板（spec_v2 §10；protocol P11） | 已修 |
| 机制对照（等式投影核/区间 constrained ridge/soft-penalty；P1 循环；M2 VOI 对照；最小释放集规模） | WEAK | spec_v2 §5.1/§5.2/§5.3、§8；protocol P3 | 已修 |
| 两评分流程裁决/先例补充 | 缺 | protocol P4.5；spec_v2 §9 | 已修 |

## 1. 判据可成立（挑战必改 1）

**挑战**：X_flip 要求"≥2 上下文符号一致 + 二项显著"；n=2 单侧 p=0.25，n=5 才 0.031 → 按 v1 永远判不出 (ii)。

**修订**（[spec_v2.md](spec_v2.md) §3.1，[protocol_draft_v2.md](protocol_draft_v2.md) P4.6）：
- 写死 **n_ctx_min=12 个独立上下文**（上下文定义、独立性规则、Cond_r 判定；out_of_cond 不计）。
- 主判据：每关系精确单侧符号检验 **α=0.01**；预注册 primary 关系族 **≤10 条**，**BH FDR q≤0.10**（exploratory 只报告不判类）。
- **MDE 写死**：n=12 时 k≥11/12 精确 p=0.00317、k=12 p=0.000244；功效：真实一致翻转率 p1=0.95 → 0.882；p1=0.90 → 0.659。**预注册 MDE = p1≥0.95 时 80% 功效**；若预期 p1<0.95，必须按 P0c 模拟增大 n，不得事后放宽 α。
- 另给敏感性统计：上下文级配对差 + 细胞/药对聚类 bootstrap（≥2,000）+ 置换零；与符号检验不一致 → `ambiguous_conflict`。
- `not_identifiable`/`ambiguous_conflict` **预注册上限**：分别为反馈单元的 **≤15% / ≤10%**；超限 → `design_invalid` 停（protocol P6），并必须附"追加测量清单/预算"。
- **注入体检**（P0b）：人造 (i)/(ii)/(setup) 各 ≥30 单元、效应量≥MDE；要求每类 recall≥0.80、precision≥0.80、置换零下假判 (ii)≤0.10；失败 → `design_invalid`。

**残余**：n_min=12 的 MDE 推导（p1=0.95）需在 P0c 用实际聚类结构模拟确认；若实际有效上下文更少 → `insufficient_precision` 停（不在本轮假装通过）。

## 2. 分类可证伪（挑战必改 2）

**挑战**：缺第四解释；M1"先试释放"系统性偏向 (ii)；χ² 用 iid |S| 自由度；σ 未传播；d_rel 误杀。

**修订**：
1. **第四解释 `setup_error`**（spec_v2 §2(iv)）：噪声/模型错设、σ 错估、区间 winner's curse/错估、批次未吸收；签名 = 区间覆盖诊断、σ 带内翻转、异方差/聚集、批次吸收后 C_conf 消失。失败类别加 **`model_misspecified`**（含 `noise_model_invalid`/`interval_miscalibrated` 子标签，protocol P6）。
2. **取消顺序默认**（spec_v2 §3.3，protocol P4.1–P4.3）：四解释候选模型（i / ii(J) / setup / iii-proxy）同一数据/预算下按**预注册惩罚拟合**（样本外拟合 + 复杂度/代价 + Δ_pred(U)）比较；**释放廉价不是 (ii) 的证据**；与同尺寸随机释放/soft-penalty/无释放 constrained ridge 对照；若惩罚拟合差 < δ_fit 或对 U 预测不同 → `ambiguous_conflict`。
3. **依赖感知 χ²/σ**（spec_v2 §3.2）：零分布用细胞×药对双层块置换/聚类 bootstrap（≥2,000）或 κ 方差膨胀（κ 从参考估；C174 的 dyadic vs iid 差可达 ~10.33×，不得取 κ=1）；σ 在 `[σ_lo,σ_hi]` 带内分类须一致，否则 `ambiguous_conflict`。
4. **d_rel 降级**：仅描述量，不作判类必要条件（区间约束下合法更新可沿关系行空间 slack 移动）。
5. **两评分流程裁决规则**（protocol P4.5）：签名统计 vs M1 拟合证书不一致时：setup 证据优先 → setup；签名支持 (ii) 但 M_ii 未领先 → ambiguous；其余 → ambiguous；无第三方事后仲裁。

## 3. 关系集可执行（挑战必改 3；原挑战判 FAIL）

**修订**（spec_v2 §4 + [relations_check_design.md](relations_check_design.md)）：
1. **关系单位/池化/Cond_r**：关系定义在 `(细胞组 G, anchor a, ANCHOR_CONC, LIBRARY_CONC, 无序 library 对 l1,l2, 端点)` 的元数据类上；统计量 = 细胞级受控对比 `d_c=y(c,p)−y(c,q)` 的**收缩组均值**与区间；`Cond_r` 只由元数据判定；S 单位仅在 `u∈Cond_r` 时计入。避免把普通细胞异质性读成关系失效。
2. **定量验收（写死数字）**：`R_min=20`、`R_max=200`；每关系独立上下文 ≥**12**；构造半/校准半方向一致率 ≥**0.90** 且半交换后仍通过；区间宽度 `≤min(2.0σ_r, 0.10×决策效用范围)`；`|μ_r|≥0.5σ_r`（近零关系不得进主族）；覆盖候选单元空间 ≥**50%**；每 tissue ≥3 条、主族 ≤10 条。
3. **防 winner's curse**：方向只在构造半 A 选、区间只在校准半 B 估；A↔B 交换复核；同一半禁止既选又估；种子/规则冻结。
4. **S/参考显式 disjoint**：参考 84 细胞（A42/B42）、S 24 细胞、U 其余（≈17）；三元不交、按 tissue 分层、元数据盲抽取；S 键 SHA 在接触 y 前冻结；跨 screen（Original/Validation）只作**敏感性**并披露 screen/批次与"独立组"完全混淆（R193-A0）。
5. **screen/batch 进 nuisance**：主设计同 screen 内切细胞；每批/barcode 作为 nuisance/随机效应进入 f_old 与更新器；跨 screen 只作交换敏感性。
6. **非重聚合 lineage**（spec_v2 §0/§8 P8；protocol P0c/P11）：声明 estimand 不是 Q 估计、不是同一 96 细胞换聚合；P0c MDE 预检必须按独立单元计算；MDE>δ_min → `insufficient_precision` 停，不换判据。
7. **响应盲细节**：S 抽取代码/seed/键 SHA、U 键 SHA、φ/关系表/δ_min/预算 SHA 全部在接触 y 前冻结（protocol P0d/P7）；U 隔离实现 + 失败即 `leakage`。

**残余**：relations_check 尚未运行（本轮不读参考响应）；R_min=20 与 n_ctx=12 在 Jaaks 125 细胞资源上的可达性需 Stage 0 实测（若不可达 → `data_unavailable`，不降标准）。

## 4. 机制对照补齐（挑战必改 4）

**修订**（spec_v2 §5.1/§5.2/§5.3、§8；protocol P3）：
- M1 必比：**(1) 等式保护投影核**（AlphaEdit 精确对应）、**(2) 同区间无释放 constrained ridge**（隔离"释放"与"约束"）、**(3) soft-penalty/层级先验**、**(4) 尺寸匹配随机释放**，再加全量重训/普通适配/层级/GP。
- **数学条件写明**：M1 无释放只在"等式约束且无激活约束"时等价于投影核/普通 ridge；**区间约束有激活绑定时为 QP，不等价**——因此不得要求"数值等同"，只做 KKT/实现自校验并报差异。
- **P1 去循环**：改写为**样本外**诊断增量（预注册嵌套模型、置换零、尺寸匹配随机；评估期诊断量预测基线退化）；**P2 为主机制检验**（J_min 释放 vs 同尺寸随机释放 vs 无释放 constrained ridge vs soft-penalty 的未查询决策损失比较）。
- **最小释放集规模/近似写死**：|R_old|≤200；精确解 |R|≤30（分支定界/LP，60 s/单元）；否则贪心+LP 下界并报 gap；`J_max=min(5,ceil(0.10|R_old|))`；60 s 无认证 → `ambiguous_conflict`。
- **M2 先例与对照**：补 decision-focused sequential design（2602.05340）、GoBOED（2605.26093）、EVSI/ENBS、Poke&Strike；M2 = VOI/决策聚焦设计 + 解释集辨识 + 拒绝购买规则变体；Stage 2 必比 VOI/decision-focused baseline（不只 random/贪心/不确定性）；无合法区分测量 → `no_discriminating_measurement`（拒绝购买/宣称）。

## 5. 协议可执行性（挑战必改 5）

- **标题/术语**：protocol_draft_v2 标题改回 **R198-A1**（v1 误写 A2，provenance 修正）。
- **δ_min**：必须由成本/效用定义并先于冻结写死；未定义 → **`blocked_by_utility_definition`**（不冻结、不编造数值）；`MDE_decision≤δ_min`；禁止旧 CI 反推。
- **U 菜单/成本/效用**：prot_v2 P1/P5 列出候选（组合菜单；成本用 A5 接口，A5 修订通过前只 planning CU；C141：只排组合不排细胞）；数值未定 → blocking 而非编造。
- **预算/墙钟**：Stage 0 relations_check ≤30 min、体检 ≤20 min、MDE 预检 ≤15 min；Stage 1 每臂 ≤45 min、总 ≤2 h；释放求解 60 s/单元；bootstrap/置换 ≥2,000；超预算缩任务/停。
- **失败类别**（protocol P6）：补 `setup_error`/`model_misspecified`、`ambiguous_conflict`、`design_invalid`、`proxy_only`、`not_identifiable`（上限）、`leakage`、`completed_null`、`pass_to_stage2` 等；退出超限 → `design_invalid`。
- **Stage 1 只判 (i)/(ii)/(setup)**；(iii) 只输出 `proxy_only`（与 A4 协调：A4 资源结论决定 (iii) 能否升级）；报告模板禁止"三类已区分"措辞。
- **措辞模板**（spec_v2 §10）：operational 归因；不写新颖性/机制/迁移/决策收益；`not_identifiable`/`insufficient_precision`/`proxy_only` 不得写成阴性/不存在。

## 6. 其它 minor（挑战 §6/§5.7）

- 两独立评分流程裁决规则 → protocol P4.5（已补）。
- 预算/时间 → protocol P8（已补）。
- 与 A4/A5 协调 → spec_v2 §10、protocol P0/P11（已补）。
- "注入类恢复"体检 → protocol P0b（已补）。
- U 只许排组合（C141）→ spec_v2 §1/§9、protocol P1.P5（已补）。

## 7. 仍存的缺口（必须在重审前补齐，不是本轮可声称完成）

1. **relations_check 未运行**：关系表、R_old 条数、稳定性/区间/覆盖均未知；P0a 只能由下一轮 Stage 0 产生。
2. **constructive 体检未运行**：P0b 的 recall/precision/type-I 需下一轮脚本与结果。
3. **MDE 预检未运行**：n_min=12 的 MDE 推导需按实际聚类/资源模拟确认；δ_min 未定义 → 当前冻结状态 = `blocked_by_utility_definition`。
4. **关系集可达性未知**：R_min=20 与 n_ctx=12 在 Jaaks 125 细胞上的可行性需 Stage 0 实测；不可达 → `data_unavailable`，不得放阈值。
5. **(iii) 仍不可认证**：依赖 A4 的可测状态结论；本轮只 proxy。
6. **A5 成本接口**：A5 正按 challenge_A5 修订；A1 Stage 2 不得在 A5 修订通过前启动。
7. 先例补充（VOI/decision-focused/EVSI）只在 spec_v2 §9 增补；原 prior_art.md 按"不改原文件"保留，重审时以 spec_v2 §9 为准并说明 additive。

## 8. 重审条件（与挑战 §7 一致）

5 条必改落实后由同一挑战者只读复审，并附：(a) `relations_check.json` 验收结果（P0a）；(b) constructive 体检结果（P0b）；(c) MDE 预检 80% 结果（P0c）；(d) δ_min/成本状态（P0d）。任一失败 → 按失败类别停（`data_unavailable`/`insufficient_precision`/`design_invalid`），不得换判据/换聚合。
