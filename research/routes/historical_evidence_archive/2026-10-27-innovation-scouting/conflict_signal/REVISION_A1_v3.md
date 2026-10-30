# REVISION_A1_v3 — 对 challenge_A1_v2.md 的逐条回应

2026-10-27。对象：R198-A1v2 复审 [challenge_A1_v2.md](challenge_A1_v2.md)（revise，≤5 必改）。本文件逐条说明修订落在 [spec_v3.md](spec_v3.md) / [protocol_draft_v3.md](protocol_draft_v3.md) 的哪些节，以及 **Lead 已决（写死）** 事项的落实。v1/v2 原文件均**未改动**。本轮不运行效果/relations_check/体检/MDE 预检；不声称新颖性。

## 0. 总览

| 复审 5 必改 / 致命项 | v3 处置 | 状态 |
|---|---|---|
| ① Stage 1 的 X_flip 在 tissue-specific Cond_r 下算术不可行（Pancreas 29 / matched 28 vs 24+12=36）；S=24 分层 ~8/tissue<12 | **Lead 已决：Context = 跨 tissue 池化（tissue 进 nuisance）**；主族 pooled，Breast/Colon 仅敏感性，per-tissue exploratory。可行性表写死：Original 51/45/29、matched 33/35/28；pooled 后 reference 84⊆matched96（A42/B42）、S 24 从剩余 41 抽、U 17；S 侧 Cond_r 覆盖≥12 metadata-only 预检。若池化仍不可行 → data_unavailable，不降 n_ctx。（spec_v3 §2.1；protocol_v3 P0a-metadata） | 已修（算术写死；未实测真实资源） |
| ② P0a 验收自相矛盾：宽度含 0.10×决策效用范围但 P0d blocked；覆盖分母未定义（229→≥115） | **P0a 只用 2.0σ_r**；效用/δ_min 移到 **P0d**；**覆盖分母冻结 229 → 通过≥115**；`R_old∈[20,200]` 保留。（spec_v3 §2.2；protocol_v3 P0a relations_check） | 已修 |
| ③ MDE 标注错误（80% 在 p1≈0.9307 非 0.95）；sign test 独立性；spec_v2 与 relations_check 的 context 定义冲突（差 2 倍） | MDE 写死 **p1≈0.9307**；p1≥0.95 为**保守设计目标（power 0.8816）**；补 **n–p1 表**（0.98→n7/k7 0.868；0.95→n11/k10 0.898；0.93→n11/k10 0.823；0.90→n14/k12 0.842；0.85→n19/k15 0.856）；**context 冻结 = 一个 S 细胞（pooled）**，删除 v2 的 cell-pair 组定义；sign test 主统计量 + cluster（细胞/药对/批）bootstrap/置换敏感性；P0b/P0c 依赖模型校准 type-I/功效并报 ρ/κ。（spec_v3 §1/§3.1/§4；protocol_v3 P0c） | 已修 |
| ④ 第四解释：M_setup 无正式概率模型；惩罚拟合/δ_fit/CV；J 候选族；κ 估计；退出上限无 operational 分母 | M_setup 正式概率模型（γ/τ_t/τ_b + 共享预测似然）；惩罚拟合公式 `score=−2·loglik_heldout+λ_k k_E log(n_eff)`、λ_k∈{0.5,1,2}（主 1）、**δ_fit=2.0**、5-fold by cells；**J 候选族生成**（单例/贪心前向≤5步/结构族，≤200，J_max=min(5,ceil(0.10|R|))，60 s）；**κ 三法**（nuisance-only 残差/留出半 B/置换零）与 σ 带一致性；退出上限 operational 分母 = eligible S 单元数（P0a 输出冻结），上限来自 P0b 依赖零 P95 且只能抬高（硬天花板 notid 0.15/ambig 0.10）。（spec_v3 §3.2/§3.3；protocol_v3 P2/P0b） | 已修 |
| ⑤ 统一 64/16 与 84/24/17；P0b 独立生成器（iid+依赖，不注入参考违反结构）；P0c ±0.05/模拟次数/n_eff 写死；P0a–P0d 清单化；A4/A5/Stage1 三类/(iii) proxy/措辞 | **统一 84/24/17，64/16 废弃**；P0b **独立生成器 M0(iid)/M1(依赖 ρ/κ)**，只用参考方差参数+合成长标签，不注入参考违反结构；每类 ≥30 单元、recall/precision≥0.80、type-I≤0.10；P0c 每格 ≥1,000 批、power 80%±0.05、CP 95% 上界≤0.10、n_eff 写死；**P0a–P0d 清单+短路**（protocol_v3 P0 清单）；A4/A5 接口、Stage 1 三类、(iii) proxy、措辞模板保留（spec_v3 §7/§8） | 已修 |

## 1. 六项复审判决的逐项回应

### ① 判据可成立（WEAK：算术 PASS；MDE 标注/依赖/context 定义 FAIL 子项）
- 算术 PASS 保留（p=0.0031738 / 0.0002441；power 0.8816/0.6590 复核一致）。
- **MDE 修正**：写死 MDE(80%,n=12)=p1≈0.9307（精确 0.93074，power 0.7998）；p1≥0.95 是保守设计目标（0.8816），不是 MDE；补 n–p1 表（§3.1）。**若预期 p1<0.9307 必须按表增大 n，不得放宽 α**。
- **context 定义统一**：v3 冻结 context=一个 S 细胞（pooled Cond_r）；删除 v2 "细胞组对/一个 cell-pair 组"的表述；S 侧覆盖≥12 由 P0a metadata 预检保证；若 S 侧可用 context <n 表要求 → `insufficient_precision`，不换定义。
- **依赖**：exact sign test 为主统计量；同时报 cluster bootstrap/置换（细胞/药对/批次）p/MDE，二者不一致 → `ambiguous_conflict`；P0b/P0c 用依赖生成模型校准；ρ/κ 敏感性写死报告。
- 两独立评分流程裁决、primary 家族/BH（≤10, q≤0.10）保留（spec_v3 §2.2）。

### ② 分类可证伪（WEAK）
- M_setup 正式概率模型 + 共享预测似然 + γ 校准已写（§3.2）；
- 多解释惩罚拟合公式/λ_k/δ_fit/CV 写死（§3.2）；无顺序默认、释放廉价不构成 (ii) 证据；
- χ² 依赖（细胞×药对双层块置换/κ 膨胀）保留；**κ 三法估计**与污染诊断（§3.2）；σ 带一致性；
- 退出上限 operational 分母与 P0b 派生规则（§3.3）；
- d_rel 仅描述（v2 保留）。

### ③ 关系集可执行（FAIL → 已修，算术写死）
- 可行性表（Original 51/45/29；matched 33/35/28）与 tissue-specific 不可行结论写死；**pooled context** 解决；reference 84 ⊆ matched 96（A42/B42，tissue 比例分层），S 24 从剩余 41 抽，U 17；
- 候选网格 229，A/B≥12 供给 ≈154（Breast86/Colon37/Pancreas31）；覆盖要求 115/229 写死；若预检/供给/覆盖不足 → `data_unavailable`；
- S 侧 Cond_r 覆盖≥12 metadata-only 预检（新，P0a-metadata）；
- 半分离/交换、区间宽度 2.0σ_r、|μ|≥0.5σ、R∈[20,200]、primary 族/BH 写死；
- 非重聚合 lineage 保留（C174/C175）；screen/batch nuisance、跨 screen 仅敏感性。

### ④ 机制对照（WEAK：多数 PASS，未写死项补齐）
- M1 (a)–(d) + 基线、QP 不等价、P1 样本外/P2 主、释放集规模/近似/60 s 保留；
- **J 候选族生成**写死（§3.2）；
- **P2 不再依赖 blocked 的 δ_min**：P2 的决策损失比较所需 δ_min 由 P0d 定义，若 blocked 则 P2 只能做描述性报告（不判成功）；P0a/P0b 不依赖 utility；
- M2 VOI/decision-focused 对照、Stage 2 门控保留。

### ⑤ 协议/门控/措辞（WEAK：多数 PASS）
- P0a–P0d 清单化 + 短路（P0a-metadata → P0a relations_check → P0b → P0c → P0d）；
- δ_min blocked 状态保留（P0d）；64/16 废弃、统一 84/24/17；预算/墙钟（P6）；
- 失败类别补齐（P4）；Stage 1 只判 (i)/(ii)/(setup)，(iii) proxy；A4/A5 接口；
- 措辞模板（spec_v3 §8）：pooled 主族/跨 tissue 平均/不写每 tissue 成立；不写新颖性/机制/迁移/决策收益。

## 2. Lead 已决事项落实位置

| Lead 决策 | 落实位置 |
|---|---|
| Context=跨 tissue 池化；Breast/Colon 敏感性；per-tissue exploratory | spec_v3 §0/§1/§1.2；protocol_v3 P-1/P0a |
| n_ctx=12、α=0.01 不放宽 | spec_v3 §3.1；protocol_v3 P0a/P0c |
| S=24 可行；P0a 增 S 侧 Cond_r 覆盖≥12 metadata-only 预检 | spec_v3 §2.1；protocol_v3 P0a-metadata 3 |
| P0a 只用 2.0σ_r；效用移 P0d | spec_v3 §2.2；protocol_v3 P0a/P0d |
| 覆盖分母 229→≥115 | spec_v3 §2.2；protocol_v3 P0a |
| MDE p1≈0.9307；p1≥0.95 保守目标；n–p1 表 | spec_v3 §3.1（表）；protocol_v3 P0c |
| P0b/P0c 依赖生成模型（ρ/κ 敏感性） | spec_v3 §4；protocol_v3 P0b/P0c |
| M_setup 正式模型+共享似然；惩罚拟合/δ_fit/CV；J 族；κ 估计；退出分母 | spec_v3 §3.2/§3.3 |
| 统一 64/16 与 84/24/17 | spec_v3 §7；protocol_v3 P0a-metadata |
| P0b 独立生成器（iid+依赖，不注入参考违反结构） | spec_v3 §4.1；protocol_v3 P0b |
| P0c ±0.05/模拟次数/n_eff 写死 | spec_v3 §4.2；protocol_v3 P0c |
| P0a–P0d 清单化；A4/A5/Stage1/(iii) proxy/措辞 | spec_v3 §5/§7/§8；protocol_v3 P0 清单/P4/P8 |
| 关系集算术表/不可行→池化 或 data_unavailable | spec_v3 §2.1；protocol_v3 P-1/P0a |

## 3. 仍存缺口（下一轮 Stage 0 前必须处理）

1. **Stage 0 实现未同步 v3**：`stage0/relations_check_config.json` 仍是 A1v2 设计（per_tissue；P0a 含 utility 分支；84/24/17 与 64/16 未统一；无 S 侧预检/matched 限制）。同步清单见 spec_v3 §7；须先改实现再跑真实 Stage 0。**本轮不修改 Stage 0 代码**（避免半同步状态）。
2. **P0a-metadata 尚未实现/运行**：S 侧 Cond_r 覆盖≥12 预检、matched-96 限制、candidate grid 229/供给 154 的实测均需下一轮脚本；本轮只写协议。
3. **真实资源可达性未验证**：pooled 后 reference 84⊆matched96、S 24 从剩余 41 抽、U 17 的分配可行性（含 A/B tissue 比例分层）需在真实 Jaaks 元数据上算；若不足 → data_unavailable，不降标准。
4. **P0b/P0c 未实现/未跑**：独立生成器（iid/依赖）、κ/ρ 敏感性、退出上限派生、CP 规则均待下一轮。
5. **δ_min/效用仍 blocked**：P0d 未定义前 Stage 1 不能冻结；P0a/P0b/P0c 可先做。
6. **主族 pooled 的科学收窄**：pooled 后命题变为"跨组织池化的关系冲突"；per-tissue/ Breast-Colon 只作敏感性；外部有效性必须披露（Pancreas 仅 28 matched 细胞）。不得两边都写。
7. **A4/A5 接口**：A4 决定 (iii) 能否升级；A5 成本/菜单接口在 A5 修订通过前 Stage 2 不启动。
8. 先例补充仍只在 v2 spec §9（原 prior_art 不改）；v3 未新增先例检索（本轮不联网）。

## 4. 重审条件

v3 修订后由同一挑战者（endpoint-auditor）只读复审；通过后才进入 Stage 0（P0a-metadata → P0a relations_check → P0b → P0c → P0d）。任一 P0 阶段失败按失败类别停（`data_unavailable`/`design_invalid`/`insufficient_precision`/`blocked_by_utility_definition`），**不降 n_ctx、不放宽 α、不改 context 定义、不换聚合**。
