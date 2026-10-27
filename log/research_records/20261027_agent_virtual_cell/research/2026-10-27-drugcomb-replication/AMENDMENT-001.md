# AMENDMENT-001（PROTOCOL_STAGE2 v1 → v2，2026-10-27 **运行效果之前**冻结）

依据：独立挑战 [challenge_STAGE2.md](challenge_STAGE2.md)（总判决 revise；5 条必改）与 Lead 裁定。**本 AMENDMENT 在任何 identity/annotation 模型或效应运行之前写定**；v1 原文保留，冲突处以本文件为准。v2 = v1 + 本文件。

## 0. 必改项对照（挑战 §3 → 本文件）

| 挑战必改 | 本 AMENDMENT 的处理 |
|---|---|
| ① 主臂应为 identity+annotation（同 R163 Xboth） | §1：主臂改 `Xboth`（identity one-hot + annotation one-hot）；`annotation-only` 降为次臂；`identity-only` 按定义常数 ρ=0 |
| ② δ_min 与 BRIEF 冲突、三句披露 | §2：Lead 裁定 δ_min=**0.0947**（原结论 CI 下界，Tier A）并写明与 BRIEF 的冲突与理由；§5 补披露（跨 r/端点/注释系统、训练规模、可检验范围） |
| ③ CI/gate 口径、联合检定力、随机对照、r=0.55 切分 | §3：F3 改为模拟**完整判定规则的联合检定力**；CI 统一按留出药聚类；随机对照改为单一 10 次零模型均值；补容量对照；§4 改用**种子置换**切分（修正 r=0.55 前缀退化）；写明 F3@r50 失败即停、不得替补 |
| ④ 标准化泄漏、F4 不变量 | §6：标准化与内层 λ 均**每内层折内拟合**；F4 扩展为不变量断言；stage2.py 运行时断言 preflight gates |
| ⑤ study/剂量/细胞混杂、选择偏差、措辞边界 | §7：study-proxy 分层/偏相关/去均值敏感性（次要）；选择偏差披露；§8 措辞边界 |

## 1. 特征臂（v2；冻结）

- **主臂 `Xboth`**：`identity one-hot（训练药，两侧）+ annotation one-hot（训练水平，两侧）`——与 R163 冻结结论的 `Xboth` 同构（e163 脚本 Xboth = Xid ∪ Xpath）。
- 次臂：`annotation_only`（仅注解）、`identity_only`（仅身份；both-unseen 预测为常数，ρ 按 0 记）。
- 对照臂：`Xboth_random`（把药↔注解随机重指派，**10 个固定种子**：5 个保持水平大小多重集 size-matched、5 个均匀随机；合并为**单一零模型族**，取 10 次的均值）、`Xboth_capacity`（在 Xboth 上追加 2×L 个固定种子高斯随机连续特征，测试"容量伪影"）、`constant`。
- 主判定只用 `Xboth` vs `Xboth_random` 均值；其余为支持性报告。

## 2. δ_min 与复现目标的 Lead 裁定（解决 BRIEF 冲突）

- BRIEF 初稿写 δ_min=0.1183（=原头条效应）；**本 AMENDMENT 改为 δ_min=0.0947**（=原冻结结论 95% CI **下界**，P-B2 的 Tier A 保守目标）。理由：第二资源复现检验的是**条件结构的方向与量级是否达到原结论的最保守可信下界**，而不是要求点估计超过原头条（后者在真值为 0.1183 时约 50% 误判）；δ_min=0.0947 仍远高于"零/噪声"量级，且 F3 用联合检定力在真值 0.1183 下校准。**该改动是 Lead 决定的协议修订（并非依据任何已观察效应）**，写入 AMENDMENT 并在记录中披露 BRIEF 冲突。

## 3. 判定规则（v2 冻结；F3 必须覆盖它）

- R1：`Xboth` 的测试池 Spearman ρ 点估计 **≥ 0.0947**；
- R2：ρ 的 95% CI（**按留出药聚类** bootstrap，1,000 次，种子 20261027）下界 **>0**；
- R3：`Xboth ρ − Xboth_random_mean(10)` 的 95% CI（同聚类口径）下界 **>0**；
- **`replicated` = R1∧R2∧R3**；`partial` = R2 成立但（¬R1 或 ¬R3）；`not_replicated` = R2 不成立，或随机对照臂本身 ρ 与主臂不可区分（无结构特异性）；`inconclusive` = F3 未过。
- **F3（pre-flight，先于效果）**：用 P-B2 冻结方法在实际 v2 池上计算：
  (a) `MDE80_two_way ≤ 0.0947`；
  (b) 在真值 0.1183（及 0.0947）下模拟**完整判定规则**（R1∧R2∧R3）的联合检定力，要求 **P(replicated | ρ=0.1183) ≥0.80**；
  (c) **预先声明的设计阶梯（power-only，不看任何效应）**：F3 先算 r=0.50；若联合检定力 <0.80，则在**同一冻结方法**下再算 r=0.55（种子置换切分，非前缀）；取**最小的、满足 MDE80≤0.0947 且联合检定力≥0.80 的 r** 作为实际主设计；若 {0.50,0.55} 都不满足 → **停止**（`inconclusive`），不得再改 r/δ_min/规则或换端点。
  (d) 阶梯的选择只依据零模型/检定力（F3 输出），在运行任何 identity/annotation 模型之前完成并写入 `preflight.json`；事后不得替换。
- 敏感性（预先声明、不参与主判定）：r 取主设计之外的另一个已算腿、E1 切分、v1 映射、Jaaks 重合实体排除、`annotation_only` 臂、`Xboth_capacity` 臂。

## 4. 切分规则（v2；修正 r=0.55 退化）

- 主切分：**种子置换**——`rng = numpy.random.default_rng(20261027)`；`names = sorted(mapped_drug_names)`；`perm = rng.permutation(len(names))`；留出集 H = `names[perm][:k]`，`k=round(r*N)`，r=0.50（主）。训练药 = 其余。
- 该规则对 r=0.50/0.55 均不退化；替换 v1 的 `names[0::step]` 前缀规则（后者在 N=1,800、r=0.55 时 step=1 退化为字典序前缀，挑战已证明）。**测试池/训练池计数须在 pre-flight 重算**（预期与 scoping 的 32,299/5,342/108/27,230 同量级，具体以实测为准）。
- E1 切分敏感性：同一置换规则作用在全体 4,088 药上。
- r=0.55 仅作敏感性；**F3 失败不得以它替补**。

## 5. 必须随结果披露的三条构造差异（挑战②）

1. **跨 r**：原效应在 r=0.20 测得；本设计 r=0.50，训练药集从 1,800 药→900 药，训练有注释单元 **83,684（v2 r=0.20 严格口径）→ 27,230（r=0.50）**（−67.5%）。**不假定跨 r 效应相等**；结论限定为"在 r=0.50 的 both-unseen regime 上复现该条件结构"。
2. **跨端点**：原 `ΔEMAX`（剂量-反应拟合 observed−expected EMax）vs DrugComb `synergy_bliss`（剂量矩阵 Bliss 残差均值）——P-B 已论证同零模型/同方向/尺度可比，但**不是同一统计量**。
3. **跨注释系统**：原项目通路模板（GDSC 38 双侧 one-hot / 21 文本水平）vs 本设计 KEGG 186→93 可分析水平的 argmax 单标签（"靶点基因集共属"粗代理，并列/单基因偏差已知）。
- 因此"replicated"只表示：**在该切片/端点/注释体系下，注解在 both-unseen 上恢复了可检出排序信息且优于零模型**；**不得**写成"原效应量复现"或"Jaaks 结论独立确认"。

## 6. 泄漏与不变量（v2）

- **标准化与内层 λ 都只在每个内层折的训练部分拟合**（修正 v1 的"先在训练池整体标准化再切内层折"——R163 审计原缺陷）。外层测试药绝不进入任何拟合；测试标签只在最终打分使用一次。
- 内层验证必须是 **both-unseen**：内层 3 折按训练药分组，验证集 = 两药都在内层留出药的单元（与外部切分同构）。
- **F4 不变量（stage2.py 运行时断言）**：① 外层训练/测试药集互斥；② 内层折药集互斥；③ 随机指派精确保持大小多重集（size-matched 那 5 个）；④ 全程不读测试 y（除最终打分）；⑤ identity-only 预测在测试池为常数；⑥ annotation/Xboth 预测非常数；⑦ 各输入/映射 SHA 与 preflight 一致；⑧ preflight gates 全过（未过则 abort）。

## 7. 混杂与选择偏差（次要分析，不改主判定）

- **study/剂量代理**：按 P-B 的 block_id 20 等分位窗口构造 study proxy；报告 (a) 测试池/proxy 构成、注释水平×proxy 关联；(b) 主臂 ρ 在 proxy 分层内与"对 proxy 去均值（partial Spearman）"后的值；(c) `Xboth` 加入 proxy one-hot（仅作诊断臂，不为判定）。
- **选择偏差披露**：有注释测试池仅占全宇宙 both-unseen（r=0.50）的 **36.5%**（32,299/87,989）；注释子集多 block 暴露 12.5% vs 全宇宙 6.1%；108 个测试细胞全部也出现在训练池（细胞层面非 cold-start）；药物覆盖 44.03%。这些限制写入报告，不得省略。
- Jaaks 重合实体（18 细胞/40 药/241 键）排除作敏感性；不作主分析。

## 8. 措辞边界（v2）

- `not_replicated`：只能写"在 DrugComb/r=0.50/synergy_bliss/KEGG-argmax 注释这一设定下未检出原条件结构的方向性一致"；不得写"原结论被推翻"或"DrugComb 不能复现"（construct mismatch/端点差异仍是候选解释）。
- `replicated`：只能写"在该设定下复现了条件结构的方向/量级下限"；不得写机制、临床、独立确认、Jaaks 泛化。
- `partial`：写"方向一致但未达保守量级/未通过对照特异性"，不得当成功亦不当失败。

## 9. 版本状态

**PROTOCOL_STAGE2 v2 = v1 + AMENDMENT-001，FROZEN（2026-10-27，任何效果代码之前）。** 若执行中发现偏离，写 AMENDMENT-00X 并披露；不得静默改判据。
