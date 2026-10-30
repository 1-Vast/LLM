# R198-A2v2 修订报告（REVISION_A2.md）— 逐条回应挑战必改

日期：2026-10-27 · 角色：A2 提案者（lit-verifier）· task-38
对象：R198-A2 scout 被独立挑战 [challenge_A2.md](challenge_A2.md) 判 **revise（≤5 必改）**。本文件逐条说明 v2 如何落实；**原 v1 文件（spec.md/protocol_draft.md/prior_art.md/record.md/usage.json）保留不改**，v2 为新增：[spec_v2.md](spec_v2.md)、[protocol_draft_v2.md](protocol_draft_v2.md)、本文件、[record_v2.md](record_v2.md)、[usage_v2.json](usage_v2.json)。
**本轮不运行效果/训练/回放/拟合；不读响应做效果；不改 A1 产物。**

## 0. 必改 1：主主张/主实验对齐（constructive 为主，replay 降级）

| 挑战要求 | v2 落实 |
|---|---|
| I/II/III 在真实数据无 ground truth，不能把 replay 的"归因正确率"当主终点 | **主实验改为 constructive 判别体检**：spec_v2 §4（合成世界 + 注入 I/II/III/null）；protocol_v2 §3（判别器 K_A2、4 个预注册终点、MDE、预算-功效表） |
| 真实 replay 只作次级描述（归因分布/下游选择描述，不得报"归因正确率"） | spec_v2 §5 / protocol_v2 §4：replay 仅在 constructive_pass（或 Lead 允许 partial）后；只报违反统计量分布、归因分布（描述）、U 上 top-k 预测排序与描述性后悔；**明令禁止"归因正确率"与收益结论** |
| 若坚持真实归因正确率须有可审计代理标签；当前没有 → 不得 | spec_v2 §5：真实 replay **无标签、不评分**；只有注入世界有标签（由生成器给出，construct 定义） |
| C3（C130 检验）交 R196v2；C5（单药解释）交 R197v2/校准线，不重做 | spec_v2 §3 末：C3→R196v2（引 C176：审计未通过、不得当已认证）、C5→R197v2/校准线（引 C172/C174）；A2 不重推 |

**v1 撤回的主张**："主终点=三类归因正确率（在真实 replay 上）"、"20 种子 replay 作效果实验"——v2 不再成立。

## 1. 必改 2：切分/端点/注释三统一（写死）

| 挑战问题 | v2 落实 |
|---|---|
| "按药对留出 20% + 按药物聚类成折"自相矛盾 | **只保留 drug-level 切分**：5 折 × 13 药，种子 20261027（`folds.json` 冻结）；四集合 Ref/S/E/U 互不相交规则写死（spec_v2 §2.3、protocol_v2 §1）。实测：每折 both-unseen 药对 45/66/72/82/108、cell×pair 单元 1,898/3,693/3,588/4,613/6,232（median 47 cells/pair） |
| 端点"待确认"与 record 已确认冲突 | 固定 **`SYNERGY_DELTA_EMAX`**（引用 R198 record §1 的 Lead 确认；P-B/P-B2 冻结口径）；删除"待确认"表述（spec_v2 §2.2、protocol_v2 §0） |
| 注释源 GDSC 38 通路 vs P-A2 映射混用 | **v2 只用 GDSC 表内每臂单标签**（ANCHOR_PATHWAY 17 / LIBRARY_PATHWAY 21；ANCHOR_TARGET 40 / LIBRARY_TARGET 58）；**P-A2 映射在 v2 不使用**；若未来使用须先写独立映射协议（spec_v2 §2.1） |
| C1 target/单药谱、C2 pathway-pair 组计数与组内≥2 药对门槛要写死 | C1′：仅 library 臂 58 标签（51 单药+7 双药，**无 ≥3 组**）→ **降级 QA only**，不门控、不删约束；C2′：331 组，**≥2 药对 275 组（1,969 对）/≥4 药对 165 组（1,698 对、90,589 单元）**，主检验只用 ≥4 组；组内 ≥2 为敏感性（spec_v2 §3） |
| C2 的 Π 与统计量错配（identity 缺失不影响观测符号） | **删除 C2 的"两药身份缺失"条件**（那是 C130 regime，属 C3→R196v2）；C2′ 的 Π 改为"两臂表内单标签 + 两组通路已出现 + 已发布剂量布局"（spec_v2 §3 C2′） |
| C1 正显著仍可能被读成"同靶点≈同功能"许可 | 写死：**即使 C1′ 显著也只支持单药功能谱相似，禁止升级为组合功能等价/硬约束**（spec_v2 §3 C1′、§7 措辞模板） |

## 2. 必改 3：I/II/III operational 化 + 预算-功效预注册

| 挑战要求 | v2 落实 |
|---|---|
| I 的标量/CV/≥50% 阈值理由 | v2 改为 `r_I`（nuisance 标量重估后 χ² 比）+ 零分布分位阈值（q_0.10），删除无理由的"≥50%"；CV 折按药对分组（spec_v2 §4.4 规则 1、protocol_v2 §3.2） |
| II 条件内外≥10 单元、δ_scope=0.20 理由 | δ_scope=0.20 的 operational 理由写死（"两比例 0.7 vs 0.5，低于它不改变 A1 发布/释放决策"）；内/外各 ≥10 单元；**≥5 个独立语境符号翻转**（与 A1 挑战修正对齐）（spec_v2 §4.4/4.5、protocol_v2 §3.2/3.4） |
| III 状态变量清单 + 每状态 k=6 | 候选状态只来自元数据：tissue / drug_type / dose_layout + A4 新增变量；每状态 ≥6 单元；**真实 replay 不认证 III（只 `III_proxy_flag`，交 A4）**（spec_v2 §4.4、protocol_v2 §3.2 规则 4） |
| k∈{6,12,24} 与判别式样本量冲突 | **预算-功效表**：k=6 仅 I vs null；k=12 II 不达门槛；k=24 I+II 达标；k=36 I+II+III constructive；真实 replay 固定 **k=24**；v1 的"k∈{6,12,24} 同时判三类"**删除**（spec_v2 §4.5、protocol_v2 §3.4） |
| MDE/判别正确率模拟（不过即 inconclusive） | 4 个预注册终点 + 每格 ≥20 世界 + ≥500 模拟批 MDE（80% power）；任一 MDE > δ_min → `design_uninformative`，不得进入 replay（spec_v2 §4.4、protocol_v2 §3.3） |
| unresolvable ≤0.25 在预算内定义 | 定义为"非 null 注入上判别器输出 unidentifiable/mixed 的比例"；预算表与 k 网格证明该上限可达成；超过 → `constructive_fail`（spec_v2 §4.4 E4、protocol_v2 §3.3） |

## 3. 必改 4：A1/A4/A5 接口与去重

| 挑战要求 | v2 落实 |
|---|---|
| I/II/III 与 A1 同一分类两套操作的"主判定/一致性/仲裁"要预注册 | spec_v2 §6 / protocol_v2 §5：**真实 replay 主判定=A1**；A2 判别式只在 constructive 是主检验、replay 只作数据侧证据；一致性用同一 constructive 世界上的 Cohen's κ（≥0.60 `interface_consistent`，描述性）；冲突 → `interface_disagreement`，不取单一归因、A2 让位 A1、冲突样本全保留 |
| A2 只输出约束/违反/候选状态/固定探针 | `A2→A1` JSON schema 冻结（constraint_id/group/stat/CI/null_p/bh_q/sign_flip_contexts/in/out_condition_units/candidate_state_text/fixed_probe_list）（protocol_v2 §5） |
| III 归 A4；acquisition 归 A5 | III 的状态表征/认证归 A4（A2 只给候选状态+每状态 k=6 探针）；probe 收益/采样比较归 A5（A2 的 probe 为固定评估协议）；v1 的"CVT vs random/方差/EIG"**移出 A2**，如保留须并入 A5 目录（spec_v2 §1/§6） |
| C3 归 R196v2、C5 归 R194/R197 校准 | 同必改 1；A2 不重做 |
| 引用 C176/C177 作废状态 | spec_v2 §0 写明：C176（R196 `replicated_under_audit` 作废、C130 审计未建立）、C177（R197 v1 协议作废、低秩结构未检验）；不引 C130 数字/R197 结论当证据 |

## 4. 必改 5：先例/新颖性/措辞/冻结清单

| 挑战要求 | v2 落实 |
|---|---|
| 补 general-ML 检索或写"未检索不声称空白" | 本轮补 **1 个有界元数据 pass（3 条 OpenAlex 查询，未读全文）**：belief revision+experiment 260 命中、constraint learning+active learning 6 命中、abductive+active learning 30 命中；**未发现直接匹配，写"有界检索未发现，不声称空白"**（`qa2_summary.json`、`qa2_openalex_*.json`；spec_v2 §8） |
| M1 的"三个竞争修订模型"没定义 | v2 **取消 A2 定义三修订模型**：A2 用规则化判别器 K_A2（约束统计量，protocol_v2 §3.2）；更新侧的三模型/修订模型由 **A1 在其接口契约中定义**（spec_v2 §6）；A2 不依赖其内部形式 |
| 冻结 seeds/schema/失败类别/usage/预算 | protocol_v2 §0/§6/§7 冻结表：seeds（20261027）、JSON schema、失败类别（data_unavailable/insufficient_units/design_uninformative/constructive_fail/constructive_partial/interface_divergent/interface_disagreement/not_identifiable）、usage、单命令 ≤30 min 预算、冻结清单 |
| C1 正显著不得写成"同靶点=同功能" | 写死（spec_v2 §3 C1′/§7 措辞模板） |
| 不是新算子、不重开 R2 KG | spec_v2 §0/§6：A2 不主张新算法；R2 KG−随机=+0.001884 [−0.081112,+0.063593] 仅作 acquisition 边界引用；probe 选择收益归 A5 |
| constructive 体检先于 replay | spec_v2 §4→§5 / protocol_v2 §3→§4：`constructive_pass` 之前不得 replay |

## 5. 与 Lead 处置（A2 降级为 A1 支撑模块）的一致性

- A2 **不单独冻结**：v2 明确为 A1 的"约束库 / constructive 判别体检"模块（spec_v2 §0/§1）；并入 A1 整体候选冻结时生效。
- **主实验 = constructive 判别体检**（不是效果实验）：真实 replay 只给 A1/A5 提供约束违反与探针数据。
- 与 A1 挑战的**互相一致**：A2v2 采用 A1 挑战修正后的 `X_flip n_min≥5` 与 `δ_scope=0.20` 口径（见我的 A1 挑战 challenge_A1.md §7 必改 1/2），便于 A1 冻结时接口一致。
- 5 条必改全部有落点（§0–§4）；**剩余缺口**：constructive 模拟器/MDE 代码未写、`folds.json`/`constraints_check.json` 未生成、A1 更新器接口未联调、A4 状态资源未知、general-ML 仅元数据级——这些在冻结清单中，不阻塞本轮"设计修订"交付。

## 6. v1 → v2 变更清单（便于审计）

| 项 | v1 | v2 |
|---|---|---|
| 定位 | 独立候选 M1/M2 | A1 支撑模块（不单独冻结） |
| 主实验 | GDSC replay 主终点=归因正确率 | **constructive 判别体检**为主；replay 次级描述 |
| 切分 | "20% 药对 + 按药物聚类"（矛盾） | drug-level 5 折×13 药；四集合 disjoint；实测计数 |
| 端点 | "待确认" | 固定 `SYNERGY_DELTA_EMAX` |
| 注释 | GDSC + P-A2 混用 | GDSC 表内每臂单标签；P-A2 不用 |
| C1 | 门控（显著则保留/否则删） | QA only；纪律规则不变；13 个 size-2 组说明功效不足 |
| C2 | Π 混入 C130 identity regime | 删除该条件；331/275/165 组计数与门槛写死 |
| C3/C5 | A2 重做 | 交 R196v2/R197v2，只引状态 |
| C4/C6 | 部分检验 | C4 exploratory、C6 QA |
| I/II/III | 真实 replay 归因正确率 | constructive 4 终点（E1–E4）+ MDE；replay 不报正确率 |
| k | k∈{6,12,24} 三类 | 预算表：k=6/12/24/36 各能判什么；replay k=24 只 I/II |
| M1 三修订模型 | 未定义 | A2 不用；更新侧由 A1 接口定义 |
| 探针/采集 | CVT vs random（A2） | 移出 A2 → A5；A2 只给固定探针 |
| 先例 | 药理学+LOGICZSL 有界检索 | 加 general-ML 3 条有界元数据查询；仍不声称空白 |
| 冻结 | 无 | 冻结清单 + seeds/schema/失败类别/预算/时间 |
