# R199-ON3v0.2 同一挑战者复核（challenge_ON3_v0_2.md）

2026-10-27 · 挑战者：endpoint-auditor（与 ON3 v0.1 挑战同一人；未参与 ON3v0.2 修订）· 对象：`research/2026-10-27-core-module-design/oneil_dev/{PROTOCOL_ON3_v0_2.md, on3_design_v0_2.md, record_on3_design_v0_2.md, usage_on3_design_v0_2.json}` + `tmp/{_on3_v02_mask_design.py, on3_v02_mask_design.json}` + ON2/ON2-EX 只读参照。
方式：**只读复核**（文档/SHA/设计性 precompute JSON；**不运行效果/训练/更新器、不读响应值做统计、不运行 ON3 执行代码**）；只写本文件与 `tmp/`。
完整性：`PROTOCOL_ON3_v0_2.md` SHA `97FE124A…F5F4FB9`；`on3_design_v0_2.md` `4AB51CE5…C58BBA`；`record_on3_design_v0_2.md` `3B9786C4…4E9513`；`usage_on3_design_v0_2.json` `2F41A8A3…DD14DC`；mask precompute 脚本 `39557B04…A92638`、输出 `F49B6F92…7B782026`；与 usage/record 一致。v0.1 文件 SHA 未变。

## 0. 总判决

**approve_to_lead（附执行前必办条件；不是 freeze，不是 revise/stop）。**

ON3-C1 的 5 条必改**实质已落实**：整成员块掩码修复了单元级/整上下文级泄漏（symbolic reconstruction 0，覆盖门 PASS）；B4 vs B2 已锁为唯一 primary、B5-shuf 删除；MDE/rank 已分离（MDE80 只 mean Δ/MAE，rank 用 `Δρ_min_rank=max(0.10,Q95_null)+bootstrap`）；B6/B5/B4/bootstrap 的 schema 已列出；batch2 仅披露、top-k 移附录、流程/冻结后不改项明确。
**可以提交 Lead 批准**，但 **冻结 execution protocol 前必须完成 §5 的"执行前必办"**，其中最硬的是 **B6 1,000×5×B4 的预算测试尚未做**（以及参考实现/10 项单测/两跑确定性）；若预算超 45 min，必须在**冻结前**改 B6 置换数或 null 实现并披露，**不得执行时缩减**。另有 3 处协议语义必须在冻结前修清（context-ablation 不是二元泄漏门、MAE 与 MDE 尺度、B5 "masked member-pair TE" 措辞/纯冷细胞 schema）。这些不改变 primary 设计，故不要求再走一轮 DRAFT 修订；可作为 Lead 批准前的执行协议条件。

**最致命 3 条（均为执行前 blocker，不是设计级泄漏）**

1. **B6 预算未测 + "每次重拟合 B4"语义未定**：v0.2 要求 B6 **1,000 置换 × 5 折 × 重拟合 B4（ALS 25 iter）**，但**没有做预算测试**；record/design 也自认需冻结前测。若每次全量重拟合，耗时可能远超 45 min；若只重估 held-out cell 的 `c_cell/U_cell`（训练结构固定），则成本低但需在协议中明确"refit B4"的语义。**冻结前必须实测**：超 45 min 则在冻结前调整置换数（如 500）或改 null 构造并披露；**不得执行时缩减**。
2. **context-ablation 被错误地归入"10 项泄漏审计全 PASS"（语义矛盾）**：§2.4 item 3 把 context-ablation（B4 vs B4-ablated 的 Δρ_context）列为泄漏审计；但 §2.4/design §4 又说 Δρ_context≤0 只写"未观察到 context 描述性增益"，不是失败。§6.2 却写"泄漏审计 10 项全 PASS（含 reconstruction=0）"——若 Δρ_context≤0，会错误地判 `design_invalid`（或反之漏掉真正的二元泄漏检查）。必须把 **context-ablation 移出二元泄漏门**，作为独立描述性诊断；真正泄漏审计应为 9 项二元项（或另设明确 pass 条件）。
3. **MAE 与 MDE 尺度仍混用 + B5 "masked member-pair TE" 措辞 + 纯冷细胞 schema 缺失**：§4 line91/103 将 `|ΔMAE| < MDE80=0.0287644381` 作为 `evaluation_cannot_distinguish` 的 mean 尺度门槛；但 **MDE80 是 mean Δ 尺度**，不是 MAE 尺度（MAE 差的 MDE 未推导）。同时 §3 B5 特征写"**masked** member-pair target-encoding"（若指被掩码单元的目标值，属泄漏；若只是 member-pair，需改词）；纯冷细胞只在设计/§2.1 提到，protocol 没有定义/schema/单测。三者必须在冻结前写清。

## 1. 逐条判决（对照 task-71 ①–⑥）

| # | 复核项 | 判定 | 依据 |
|---|---|---|---|
| ① | 整成员块掩码是否阻断重建；reconstruction 0/157,768；context-ablation；纯冷细胞；覆盖门 | **PASS（mask 主体）/ WEAK（3 个小项）** | M=8/38 药物，规则 partner/member∈M 全掩码；`tmp/on3_v02_mask_design.json`：target30 掩码 **157,768/340,088=46.39%**；每 fold 掩码 **30,824–32,400**、掩码上下文 **368–372**、每 cell 掩码 min **4,237**、非掩码 context min **4,749**；覆盖门全 PASS；`symbolic_reconstructable_masked_units=0`。**mask 主体 PASS**；但 reconstruction 脚本实际对 **all batch1 U（205,044 masked units）** 统计，protocol 写 0/**157,768 target**；执行须按 target/fold 复算并记录分母。context-ablation 分类问题见致命 2；纯冷细胞未写进 protocol/schema（仅 design/§2.1 提及）。 |
| ② | 唯一 primary B4 vs B2；B3/B5 secondary；B0/B1 参照；B5-shuf 删除；禁止选最佳 | **PASS** | protocol §0/§3：B4 vs B2 唯一增量判定；B3/B5 只描述；B0/B1 层级参照；B5-shuf 删除并说明原因；§3 line85/§6 完整表、不选最佳；与 challenge_ON3 必改 2 一致。 |
| ③ | MDE/rank 分离；MDE80 仅 mean Δ/MAE；rank `Δρ_min_rank=max(0.10,Q95_null)+bootstrap`；0.10 非 rank MDE；单侧；null 内→cannot distinguish | **WEAK（rank 主体 PASS；MAE 尺度须修）** | §4：rank 主指标、MDE80 只 mean Δ/MAE、`Δρ_min_rank=max(0.10,Q95_null(Δρ))`、配对 bootstrap（5,000/seed/2.5–97.5+单侧）、B6 单侧 p≤0.05、4/5 folds；0.10 明确描述阈值。**但 `|ΔMAE|<MDE80` 的 mean 尺度门槛仍混用 MAE**（见致命 3）；`Q95_null(Δρ)` 的 null Δρ 定义需写清（B4_null−B2）；MAE 应只作描述/另立精度，或明确 MDE80 只对 mean Δ（不是 MAE）。 |
| ④ | 代码级 schema：B6 1,000/seed/refit/单侧；B5 random_state/5 折 TE/容量；B4 ALS/LOO；bootstrap；mask key/排序/tie；两跑/≤45 min/10 单测；预算测试 | **WEAK（schema 主体 PASS；预算/实现/单测未做）** | protocol §5/§10：B6 1,000/20261130/每次重拟合/单侧；B5 random_state=20261130、5 折交叉拟合 TE、容量网格；B4 ALS init/seed/tol/max_iter/rank/λ、LOO-CV、c/U 仅非掩码 context；bootstrap 5,000/seed/percentile；mask key/tie/scope；两跑逐字节、≤45 min、10 项单测；**明确记录 B6 预算测试未做、参考实现/单测/两跑未做**（record §6）——必须列为冻结前必办。 |
| ⑤ | batch2 仅披露；top-k 附录；覆盖/模板/失败类别；流程/冻结后不改 | **PASS** | §1 line16/§6.3 batch2 disclosure-only（5,214 行/1,129 单元/136 上下文；不进训练/指标/增量/敏感性）；§8 top-k 附录（tie 归一名）；§7 阴性/阳性模板；§6.4 失败类别/停止；§6.5 流程；冻结后不改 mask/seed/fraction/超参/rank/λ/指标/差值规则。 |
| ⑥ | 总判决 / 是否可提交 Lead | **approve_to_lead（附执行前必办）** | 5 条设计必改实质落实；mask 泄漏主体修复；唯一 primary/MDE rank 分离/边界/flow 通过；剩余为执行协议级预算/实现/小语义修补，见 §5。 |

## 2. 掩码与重建：PASS 主体，3 个须补

- **整成员块 mask 证据**：M=`dinaciclib, erlotinib, methotrexate, mitomycine, sn38, sorafenib, topotecan, vinorelbine`（8/38；SHA key + seed 20261130）；held-out cell 内 `masked iff partner∈M or a∈M or a'∈M`。**所有含 M 的 g(c,{x,y}) 节点只出现在被掩码单元**；非掩码单元只含非 M g 节点，因此被掩码单元不在非掩码特征张成空间内——比整上下文掩码更强，跨上下文恒等式（`Δ(a,a';b)=Δ(b,b';a)+Δ(a,a';b')−Δ(b,b';a')`）也不能用非掩码项重建。**mask 主体设计 PASS。**
- **reconstruction 0**：`tmp/on3_v02_mask_design.json` `symbolic_reconstructable_masked_units=0`；但脚本对 **all batch1 masked units 205,044** 统计，protocol/design 写 **0/157,768 target30**；JSON 未存分母。执行时须按 **target30/per fold** 复算并输出 `reconstructed/denominator`，单测断言 0；不能只引用 0 而无分母。
- **覆盖**：target30 340,088；masked 157,768（46.39%）；fold masked 30,824–32,400；fold masked contexts 368–372；cell masked min 4,237；cell unmasked context min 4,749；全部超过 5,000/50/500/500 门。**PASS。**
- **context-ablation**：设计合理（B4 vs B4-ablated，c=U=0），但**不是二元泄漏审计**；见致命 2/§5。
- **纯冷细胞**：design §2.3/§8 说"确认性 sensitivity"，但 **protocol v0.2 没有定义**（无 schema/指标/单测/是否进报告）；要么写进 protocol，要么删掉，不能只在 design 里悬空。
- **mask 20% 的定义**：20% 是**药物比例**（8/38=21.05%，ceil），不是单元比例；实际掩码 46.39% 已在 §2.2/表披露；PASS（但报告须持续标注"20% drugs, 46.4% units"）。

## 3. 唯一 primary / 比较器 / MDE/rank

- **B4 vs B2**：唯一 primary；B3/B5 secondary；B0/B1 参照；B5-shuf 删除；完整表；不选最佳。**PASS。**
- **MDE/rank 分离**：MDE80=0.0287644381 只 mean Δ/MAE；rank 用 `Δρ_min_rank=max(0.10,Q95_null(Δρ))` + 配对 bootstrap；δ_min=0.10 只 mean 尺度；0.10 描述阈值非 rank MDE；单侧 95th；null 内→`evaluation_cannot_distinguish`；**基本 PASS**。
- **仍须修**：
  - `|ΔMAE| < MDE80` 的 MAE 门槛：**MDE80 是 mean Δ 尺度，不是 MAE 尺度**；应删除该门，或为 MAE 定义独立的 null/CI，不要把 mean-Δ MDE 套到 MAE。
  - `Q95_null(Δρ)` 的 **null Δρ 定义**：应明确为 `ρ(B4_null)−ρ(B2)`（同一掩码单元、同一 B2）；B6 null p 也需同一定义。
  - bootstrap：按 held-out 细胞分层、预测固定、B=5,000、seed=20261130；已写，但需在 schema 中明确是**配对**（同一 resample 同时算 B4/B2）与 percentile 类型。
- **B2**：cell-blind partner×member-pair lookup + backoff；不使 held-out context；合理强静态基线；PASS。
- **B5**：5 折交叉拟合 target encoding、random_state、容量网格已写；但 §3 "**masked** member-pair target-encoding" 措辞危险：若"masked"指被掩码单元的目标值 → 泄漏；若是 member-pair TE 的训练折计算 → 应删"masked"或明确"训练 cell 的 member-pair TE，5 折交叉拟合，不使用任何掩码单元响应"。**冻结前必须澄清。**

## 4. B6/B4/B5/单测 schema

- **B6**：1,000 置换、seed 20261130、每次"重拟合 B4"、单侧上 95th、双边 2.5–97.5 报告、null 校准门（2.5–97.5 覆盖 0 且 mean|ρ_null|≤0.05）；**schema 方向正确**。但：
  - **预算测试未做**（record §6 明说）；1,000×5×B4 若全量重拟合可能远超 45 min；冻结前必须实测；超预算则在冻结前改置换数/null 实现并披露，不得执行时缩减。
  - "refit B4"语义未定：若每次全量 ALS 重拟合 vs 训练结构固定、仅重估 held-out c/U，成本差异大；须写死并在预算测试中采用最终语义。
  - `Δρ_p`/`Q95_null`/p 值需明确用 B4_null−B2 配对；B6 null 校准门应加入 10 单测（当前 10 项单测未列 B6 null gate）。
- **B4**：ALS init normal(seed=20261130,0.01)、tol=1e-6、max_iter=25、rank/λ 网格、c/U 仅非掩码 context、LOO-CV；方向正确；需参考实现与单测确认确定性/无 held-out masked 值进入。
- **B5**：random_state/5 折 TE/容量网格已写；须修 "masked member-pair TE" 措辞与 TE 的折定义（仅训练细胞；eval member-pair 的处理/backoff）。
- **mask**：M/SHA/seed/rule/scope/tie 已写；PASS。
- **bootstrap**：B=5,000/seed/percentile 已写；PASS（需配对 schema）。
- **确定性/预算**：两跑逐字节、JSON 排序、无时间戳、≤45 min 已写；**参考实现/两跑/预算测试未做**（record §6 自认）→ 冻结前必办。

## 5. Lead 批准前必须完成的执行前事项（不是再改 DRAFT；建议 Lead 以条件批准）

1. **B6 预算测试（最高优先）**：用最终语义实现 cold-start 版 B6（1,000×5×B4 或按需预计算训练结构）；实测单命令 wall ≤45 min。超预算则**在冻结前**调整置换数（如 500）或 null 构造并披露；**禁止执行时缩减**。同时把 B6 置换数/seed/refit 语义写入 execution protocol。
2. **参考实现 + 10 项单测 + 两跑确定性 + 输出 schema 校验**：mask 确定性/掩码规则/reconstruction=0（target30/per fold 分母）/mask 扰动/context-ablation 跑通/schema/两跑/fold 继承/无 Jaaks 路径/无 test 调参；另加 **B6 null 校准门**单测。全部通过后才冻结。
3. **修 context-ablation 分类**：从二元"10 项泄漏审计全 PASS"中移出，作为独立描述性诊断（≤0 只改措辞，不 design_invalid）；真正泄漏审计改为 9 个二元项（mask perturbation、no cell id、batch1 only、no Jaaks/ΔEMAX、no dose interpolation、no test tuning、mask key、single-agent excluded、fold inheritance）；reconstruction 单列为 model-free audit（必须=0）。
4. **修 MAE/MDE 与 B5 措辞/纯冷细胞**：删除或改写 `|ΔMAE|<MDE80` 门（MDE80 只 mean Δ；MAE 另立 null/CI 或仅描述）；把 B5 "masked member-pair target-encoding" 改为"member-pair target-encoding，训练 cell 内 5 折交叉拟合，不使用任何掩码单元响应"；若保留纯冷细胞 sensitivity，则在 protocol 定义其指标/schema/单测，否则删除 design 的悬空表述。
5. **冻结执行协议**：Lead 批准后写 execution protocol（含最终预算/B6 置换数/所有 schema/单测/两跑/≤45 min），冻结后不改 mask/seed/fraction/超参/rank/λ/指标/差值规则；执行仍只写开发性描述，不称迁移/决策/机制/独立确认/更新器/资源足够/新颖性。

## 6. 对 task-71 各重点的直接回答

- **① 整成员块掩码：PASS**；系数论证+重建 0+覆盖门成立；**但 reconstruction 分母须按 target30 复算**；context-ablation 不是二元泄漏门；纯冷细胞未进 protocol。
- **② B4 vs B2 唯一 primary、B5-shuf 删除：PASS。**
- **③ MDE/rank 分离：PASS 主体；MAE 与 MDE 尺度仍混用、B6 null Δρ 定义需写清（执行前修）。**
- **④ schema：PASS 主体；预算测试/参考实现/10 单测/两跑均未做，必须列冻结前必办；B6 "refit"语义需定。**
- **⑤ batch2 仅披露、top-k 附录、流程/冻结后不改：PASS。**
- **⑥ 总判决：approve_to_lead（附条件）；不是 revise/stop；当前不可直接 freeze。**

## 7. 复核证据与本轮边界

- 文件 SHA 见页首；mask precompute JSON/脚本 SHA 与 usage/record 一致；v0.1/ON2/ON2-EX 冻结产物未改。
- 设计性 precompute 是 metadata/nullness-only；本轮未运行效果/训练/更新器，未读响应值，未运行 ON3 执行代码；只写 `challenge_ON3_v0_2.md` 与 `tmp/`。
- 结论只审"是否可提交 Lead 批准/是否满足冻结前置"；draft 仍不是执行依据；冻结≠资源足够/关系成立/效果。
