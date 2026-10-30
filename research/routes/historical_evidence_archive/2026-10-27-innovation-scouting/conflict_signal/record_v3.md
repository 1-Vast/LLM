# record_v3 — R198-A1v3 修订过程记录（设计修订；无效果运行）

2026-10-27。角色：R198-A1 提案者，按 R198-A1v2 复审 [challenge_A1_v2.md](challenge_A1_v2.md)（revise，≤5 必改）与 **Lead 已决事项**做 v3 修订。**本轮只写设计与协议，不运行效果/relations_check/体检/MDE 预检，不读 S/U 响应，不改 A1 v1/v2 文件，不声称新颖性。**

## 1. 范围与输入

- 输入（只读）：[challenge_A1_v2.md](challenge_A1_v2.md)（endpoint-auditor 复审）、[challenge_A1.md](challenge_A1.md)、A1 v1/v2 六件（spec.md/spec_v2.md、protocol_draft.md/protocol_draft_v2.md、prior_art.md、REVISION_A1.md、relations_check_design.md、record*.md/usage*.json）、R198 record、SYNTHESIS 相关 C 边界（C141/C154/C160/C167/C171/C172/C174/C175/C176/C177）。
- 只写 `research/2026-10-27-innovation-scouting/conflict_signal/` 下**新增 v3 文件**：`spec_v3.md`、`protocol_draft_v3.md`、`REVISION_A1_v3.md`、`record_v3.md`、`usage_v3.json`；不改 v1/v2、其它目录、INDEX/SYNTHESIS/git；未联网。
- 不做：运行效果/训练/真实 relations_check/constructive 体检/MDE 预检；不编造 δ_min/效用；不声称"三类已区分"或"关系成立"。

## 2. 关键修订（对应复审 5 必改 + Lead 已决）

1. **tissue 算术不可行 → 跨 tissue 池化（写死）**：可行性表 Original 51/45/29、matched 33/35/28；tissue-specific 下 reference A/B 各≥12 + S≥12 = 36 > Pancreas 29（matched 28）→ 结构性不可行；S=24 分层 ~8/tissue <12。Lead 已决 **context=pooled（tissue 进 nuisance）**；主族 pooled，Breast/Colon 仅敏感性，per-tissue exploratory；reference 84⊆matched96（A42/B42，tissue 比例分层）、S24（剩余 41 抽）、U17；S 侧 Cond_r 覆盖≥12 metadata-only 预检。
2. **P0a 验收矛盾修复**：P0a 只用区间宽度 **2.0σ_r**；效用/δ_min 移到 **P0d**；覆盖分母冻结 **229→通过关系≥115**；`R_old∈[20,200]`、n_ctx=12、α=0.01 保留。
3. **MDE/context 定义修正**：MDE(80%,n=12)=**p1≈0.9307**（精确 0.93074，power≈0.80）；p1≥0.95 为**保守设计目标**（power 0.8816）；补 n–p1 表（0.98→n7/k7 0.8681；0.95→n11/k10 0.8981；0.93→n11/k10 0.8228；0.90→n14/k12 0.8416；0.85→n19/k15 0.8556）；context 冻结=一个 S 细胞（pooled），删除 v2 cell-pair 组定义；exact sign test 主统计量 + cluster bootstrap/置换敏感性；P0b/P0c 依赖生成模型报 ρ/κ。
4. **M_setup/拟合/释放/κ/退出上限**：M_setup 正式概率模型（γ/τ_t/τ_b + 共享预测似然）；惩罚拟合 `score=−2·loglik_heldout+λ_k k_E log(n_eff)`（λ_k=1 主，δ_fit=2.0，5-fold by cells）；J 候选族生成（单例/贪心前向≤5/结构族，≤200，J_max=min(5,ceil(0.10|R|))，60 s）；κ 三法（nuisance-only/留出半/置换）；退出上限 operational 分母=eligible S 单元、由 P0b 依赖零 P95 派生（只能抬高；硬天花板 notid .15/ambig .10）。
5. **统一与流程**：64/16 废弃，统一 84/24/17；P0b 独立生成器（iid+依赖两版，不注入参考违反结构）；P0c 每格 ≥1,000 批、power 80%±0.05、CP 95% 上界≤0.10、n_eff 写死；P0a–P0d 清单+短路；A4/A5 接口、Stage 1 三类、(iii) proxy、措辞模板保留。

## 3. 决定与理由

1. **接受 Lead 的 pooled context 作为唯一主口径**：因为 tissue-specific 在 Jaaks Pancreas 上算术不可行（36>29/28）；pooled 后主关系是"跨组织平均"，必须在报告中披露外部有效性限制；per-tissue 仅 exploratory，避免事后择优。
2. **P0a 与 P0d 解耦**：先做不依赖 utility 的关系资格（2.0σ_r），δ_min/效用只在 P0d（Stage 1 前）检查；这样 P0a 不再被 blocked 卡死，但 Stage 1 仍须 δ_min 冻结。
3. **MDE 用精确二项写死**：80% 功效对应 p1≈0.9307；p1≥0.95 只作保守目标；n–p1 表给"若预期更低必须增大 n"的可执行规则，避免用 0.95 误标 MDE。
4. **依赖/context**：sign test 在共享药对/板/批下不是独立 Bernoulli；v3 以 cluster bootstrap/置换为敏感性、P0b/P0c 依赖模型校准；若两者不一致判 ambiguous，不硬判。
5. **退出上限从不许降低**：P0b 派生上限只能抬高；若硬天花板被超 → design_invalid（说明设计不可判），不放宽。
6. **Stage 0 实现本轮不半同步**：v3 冻结前不改 stage0 代码；在 spec_v3 §7 给出精确同步清单（config 键与新增代码项），下一轮一次做完再跑真实数据。
7. **不声称新颖性**：机制成分均有先例；v3 只是提高可判定性/可执行性。

## 4. 本轮产物与 SHA（写后）

| 文件 | 说明 |
|---|---|
| `spec_v3.md` | A1 v3 机制规格（pooled context、可行性表、MDE/n–p1 表、M_setup/惩罚拟合/J/κ/退出上限、P0a–P0d） |
| `protocol_draft_v3.md` | 若冻结的执行清单（P0a-metadata→P0a→P0b→P0c→P0d→Stage 1；失败类别/预算/泄漏/措辞） |
| `REVISION_A1_v3.md` | 逐条回应 challenge_A1_v2（5 必改 + Lead 已决 + 六项判决） |
| `record_v3.md` | 本文件 |
| `usage_v3.json` | 运行时账（token/费用 null；命令与耗时） |

写后 SHA 见 `usage_v3.json` 的 `deliverables_sha256`（自引用文件外部复算）。

## 5. 局限与剩余缺口

- **未验证**：pooled 后真实 Jaaks 可达性（reference 84⊆matched96、S 24 从剩余 41 抽、U17、S 侧覆盖、候选供给/覆盖 115）需下一轮 P0a-metadata 实测；本轮只写算术/协议。
- **Stage 0 实现未同步 v3**（config 仍 per_tissue、含 utility 分支、无 matched 限制/S 侧预检）；同步清单在 spec_v3 §7，下一轮一次改完并重跑 synthetic selfcheck。
- **P0b/P0c 未实现/未跑**：独立生成器、ρ/κ 敏感性、CP 规则、退出上限派生仍需脚本与运行。
- **δ_min/效用 blocked**：P0d 未定义前 Stage 1 不能冻结；P0a/P0b/P0c 可先行。
- **先例无新增检索**（本轮不联网）；M2 先例仍以 v2 §9 为 additive。
- **(iii) 仍 proxy_only**（依赖 A4）；A5 成本接口待其修订通过。
- 本轮没有任何生物/关系/效果结论；所有数字是元数据算术/统计推导/协议参数。
