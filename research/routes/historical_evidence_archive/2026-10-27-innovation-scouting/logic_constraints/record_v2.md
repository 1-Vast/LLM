# R198-A2v2 记录（record_v2.md）

日期：2026-10-27 · 角色：定向核验员（lit-verifier）· task-38
状态：**v2 修订交付完成（仍为 DRAFT，不单独冻结）；本轮不运行效果/训练/回放/拟合，不读响应做效果。**
工作范围：只写 `research/2026-10-27-innovation-scouting/logic_constraints/` 下**新增**文件（spec_v2/protocol_draft_v2/REVISION_A2/record_v2/usage_v2 + qa2_* JSON）与 `tmp/` 下只读脚本；**未改 v1 文件**（SHA 见 §4）、未改 A1 产物/其它目录/INDEX/SYNTHESIS/git。

## 1. 本轮做了什么（按顺序）

1. 读挑战 [challenge_A2.md](challenge_A2.md)（revise，≤5 必改）与 Lead 的降级处置；读 R198 record（A2 降级为 A1 支撑模块、端点确认 `SYNERGY_DELTA_EMAX`）、`EVIDENCE_REGISTER` C176/C177、SYNTHESIS 相关边界；回读 v1 spec/protocol/prior_art。
2. 读 A1 conflict_signal 的 spec/prior_art/protocol/record（只读，供 §6 接口与 A1 挑战口径对齐；**未改 A1 产物**）。
3. **元数据计数（响应盲）**：用 GDSC Original fitted 表的**身份/注释/设计列**（无响应列）计算 v2 所需写死数字（脚本 `tmp/a2v2_metadata_counts.py`、`tmp/a2v2_pass_and_counts.py`）：
   - 296,707 行 / 2,025 药对 / 125 细胞 / 3 组织 / 65 药（46 anchor + 65 library）；median cells/pair = 47。
   - pathway-pair 组：331 组；**≥2 药对 275 组（1,969 对）**；**≥4 药对 165 组（1,698 对 / 90,589 cell×pair 单元）**。
   - target 组：ANCHOR 40 标签 = 34 单 + 6 双；LIBRARY 58 标签 = 51 单 + 7 双（**无 ≥3 组**）。
   - drug-level 5 折（种子 20261027）：每折 13 药；both-unseen 药对 45/66/72/82/108；cell×pair 单元 1,898/3,693/3,588/4,613/6,232。
4. **general-ML 有界元数据检索（补必改 5）**：OpenAlex 3 条查询（未读全文）：`"belief revision" AND "experiment"` 260 命中；`"constraint learning" AND "active learning"` 6 命中；`"abductive" AND "active learning"` 30 命中。**未发现直接匹配**；写"有界检索未发现、不声称空白"（原始 JSON：`qa2_summary.json`、`qa2_openalex_G*.json`）。
5. 写 v2：`spec_v2.md`（降级定位/三统一/约束库 v2/constructive 主实验/预算-功效/A1-A4-A5 接口/措辞与冻结清单）、`protocol_draft_v2.md`（冻结用详情：SHA/折/四集合/统计量/模拟器/终点/MDE/失败类别/预算）、`REVISION_A2.md`（逐条回应必改 1–5 + v1→v2 变更表）、本记录、`usage_v2.json`。

## 2. 落地的 5 条必改（一句话版）

1. **主主张/主实验对齐**：constructive 判别体检为主；真实 replay 次级且**不报归因正确率**；C3→R196v2、C5→R197v2（spec_v2 §4/§5、§3 末）。
2. **切分/端点/注释三统一**：drug-level 5 折×13 药 + 四集合 disjoint；端点固定 `SYNERGY_DELTA_EMAX`；只用 GDSC 表内每臂单标签，P-A2 不用（spec_v2 §2、protocol_v2 §0–§1）。
3. **I/II/III operational + 预算-功效**：K_A2 规则化判别器（r_I/δ_scope=0.20/≥5 语境/状态分层）；4 个预注册终点（0.80/0.70/0.10/0.25）；k=6/12/24/36 预算表；MDE 模拟不过即 `design_uninformative`（spec_v2 §4.4/4.5、protocol_v2 §3）。
4. **A1/A4/A5 接口去重**：replay 主判定=A1、A2 只给约束/违反/候选状态/固定探针；一致性 κ、`interface_disagreement` 仲裁；III→A4、acquisition→A5；引 C176/C177 作废状态（spec_v2 §6、protocol_v2 §5）。
5. **先例/新颖性/措辞/冻结**：补 general-ML 有界检索；取消 A2 自定"三修订模型"（更新侧归 A1）；seeds/schema/失败类别/usage/预算/时间写死；C1 正显著也不得写"同靶点=同功能"；constructive 先于 replay（spec_v2 §7/§8、protocol_v2 §0/§6/§7）。

## 3. 关键口径与证据锚点（可核对）

- 端点：`SYNERGY_DELTA_EMAX`（R198 record §1 Lead 确认；P-B/P-B2 冻结）——v2 引用而非重推。
- C176（R196 作废：`replicated_under_audit` 撤回、C130 审计级可靠性未建立）；C177（R197 v1 协议作废、低秩结构未检验）——v2 §0 引用，不当证据。
- C172/C174：1.43% 仅加性条件主效应份额、Q2 加权矩/依赖单位需重核——v2 用它限制 C5/方差份额，不重做。
- R2 KG 先例：`KG − 随机 = +0.001884 [−0.081112,+0.063593]`——v2 仅作 acquisition 边界引用（probe/采样收益归 A5）。
- LOGICZSL：v2 不重提其机制；v1 prior_art 的部分覆盖判定沿用（规则固定、数据只用于满足规则），v2 不再主张"约束修订"是原则差异，只交 constructive 体检。
- A1 挑战口径对齐：`X_flip` ≥5 个独立语境、条件内/外 ≥10 单元、δ_scope=0.20——v2 采用（见我提交的 `conflict_signal/challenge_A1.md` §7），便于 A1 冻结时接口一致。

## 4. v1 文件未改（SHA256，写 v2 前快照）

| 文件 | SHA256 |
|---|---|
| `spec.md` | `139282B4E36677ED6019856C86AB68E46679CE92C90B6FBD550D63C1A521848B` |
| `protocol_draft.md` | `587E2675DD51E9E431CE0025691E14102A7ED7C8F3DF62E5FBC043CFEC1D227C` |
| `prior_art.md` | `8C484393B223B4CDB70109EFB5DFA3869D629BD0B3465DCD4DC39FE02ADFA66C` |
| `record.md` | `49136AD5F7220F40A7E20B83A8C32D794177804ABFB561DD9A36F44302F7379E` |
| `usage.json` | `ADD8C70276CAAF8F1CCB0BEC222D0AC85D25C7DFEC92C949B8C82993E7EBD13E` |
| `challenge_A2.md`（挑战者文件，只读） | `363CEF71098AADE5E6BAA0AB75530D4EB396856B5C4BBB7A1B361974FA4531D6` |

## 5. 本轮未做 / 缺口

- 未写 constructive 模拟器/MDE 代码（下一轮设计体检前置项）；未生成 `folds.json`/`constraints_check.json`（冻结清单项）；未联调 A1 更新器接口（A1 侧尚未提供 schema，v2 只给出 A2→A1 字段）。
- A4（missing_state）状态资源未知 → III 的可认证性依赖 A4；A2 只做 constructive 与候选状态清单。
- general-ML 只到元数据级（3 条查询、未读全文）；不声称空白。
- 真实 replay 无 ground truth → 只作描述；任何"三类已在真实数据区分/收益"的表述禁止。
- 折不均衡（45–108 对/折；1,898–6,232 单元/折）→ 分析按折 block 配对并报最小折；若最小折功效不足，构造性体检不受影响，replay 只作描述。

## 6. 下一轮入口

1. 独立挑战者复审 v2（重点：constructive 终点/阈值/MDE、折与四集合、A1 接口仲裁、C2′ 组门槛、C1′ QA 定位）。
2. 若通过：按 `protocol_draft_v2.md` §3 先写 constructive 模拟器与 ≥500 批 MDE 模拟（不读真实响应），过体检后再谈 replay（且 replay 只描述）。
3. 与 A1 冻结对齐：A1 提供更新器与 replay 主判定；A2 提供约束库/违反统计量/固定探针；A4/A5 按 §6 接口消费。
