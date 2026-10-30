# R198-A4v2 协议草案（DRAFT，不运行）：A1 的 (iii) 状态模块——状态关联诊断与状态操纵设计

2026-10-27 ｜ 执行：drugcomb-auditor（task-44）｜ 状态：**DRAFT / NOT FROZEN / NOT RUN** ｜ 配套：[spec_v2.md](spec_v2.md)、[REVISION_A4.md](REVISION_A4.md)、[record_v2.md](record_v2.md)、[usage_v2.json](usage_v2.json)。
**本协议不独立下发 F1/F2/F3 判定**；A1 拥有三类总判定，A4 只输出 `state_association` 诊断与 `measurement_request`。本文件不训练/不拟合/不估 Q/不读响应做统计；不得声称机制/决策收益/新颖性；阴性不写成"不存在"。

## 0. 身份、启用门与输入（写死）

- **模块定位**：A1 的 (iii) 支撑模块（见 spec_v2 §0 所有权表）；A4 的输出供 A1 v2 的 (iii) `proxy_only` 更新与 P6/P7（v1 编号）状态证据使用；A4 不判类。
- **启用门**：**A1 冻结（A1 v2 当前 revise 未冻结 → A4 = `blocked_by_A1`）**；A1 冻结并把证书 schema 固定后，本协议才可进入 P0a；A1 未冻结时任何 Phase 0/1 都不执行。
- **输入（二选一写死）**：**A1 冲突证书**（`{J, C_conf, X_flip, Δ_pred(U), setup 诊断}`；`conflict_signal/spec_v2.md` §8、`protocol_draft_v2.md`）。**不使用 Q-flip 改名路径**；A4 不另立 Q 跨 screen 符号判定，也不复用 v1 的 SCC 机制陈述。
- **端点**：`SYNERGY_DELTA_EMAX` 类功能端点（与参考同尺度；换端点=新轮）；Phase 0 只用 A1 证书/关系标识，不重估 A1 主 Q。
- **本轮纪律**：只写本目录新增文件；不运行任何效果/模拟器/时间预测；不读响应值做统计；不下载；不改 v1、A1/A2/A3/A5 产物、其它目录/INDEX/git。

## 1. 数据与固定输入（执行前冻结 SHA）

| 输入 | 用途 | 来源/边界 |
|---|---|---|
| A1 冻结证书（`C_conf`/`X_flip`/`J_min`/`Δ_pred(U)`/setup） | Phase 0 的冲突单元 | A1 冻结后产出；A4 不重算 A1 主判定 |
| Jaaks Original/Validation fitted（匹配 96 细胞；A0/A1 冻结口径） | 冲突/关系背景 | 只读；不重拟合/不重估 A1 主 Q |
| A0 `matched_conditions.csv`（96 细胞）+ `identity_map.csv`（125/125→DepMap） | 细胞级连接 | 只读；SHA 冻结 |
| DepMap `CCLE_expression.csv`（1,249×19,144）、`CCLE_mutations.csv`（1,666 细胞）、`sample_info.csv`（1,756；culture_type/medium 等） | `S_pre` 面板 + cell one-hot | 只读；无响应派生列 |
| 覆盖数字（本挑战实测，冻结报告用） | Phase 0 分析集 | matched 96：表达 **84**、突变 **95**、culture_type **54**、medium **55**、联合 **54**（spec_v2 §4.1） |
| A0 MDE 边界 | 设计参考 | **0.112**（C168；0.240 是各折均值、旧"资源不可用"表述已撤回） |
| A2 `q2.json` barcode 分半标定（1,312 四元组；1.43% 覆盖；barcode-rich、同 screen） | 噪声模型/阈值的唯一技术噪声来源 | **不是 A0**；不得当跨 screen null |
| A5 `cost_model.md`（anchored key 34–68 wells；day1 板 1,536/细胞；密度优化 1,344/细胞；等成本框架） | Phase 1 well 账 / Phase 2 等成本 | 只读；A5 当前 revise 未冻结 → Phase 2 不启动 |
| A2 III（logic_constraints v3） | 排除域/候选状态清单接口 | 只读；A4 不评价 A2 约束 |
| A3/C175、C160/C167/C171/C172/C174/C176/C177 | 边界引用 | 见 §7 |

## 2. 预注册设计检查（P0a–P0e；先于任何统计；不过即停，不救）

| 检查 | 内容 | 不过的处理 |
|---|---|---|
| **P0a 输入资格** | A1 已冻结且证书 schema/字段齐全；证书单元数、细胞覆盖、`Cond_r` 可判定；A1 声明 (iii) 请求状态证据 | `blocked_by_A1`/`data_unavailable`，停 |
| **P0b 覆盖/EPV** | matched 96 的 `S_pre` 覆盖（54/84）；模型维数 ≤5（54 细胞）/≤8（84）；缺失指示规则；54/84 两版敏感性预注册 | `design_invalid`，停（不放宽 EPV） |
| **P0c MDE 模拟** | 按 §4.3 的写死方案（模型/维数/λ 网格/seed/聚类/bootstrap/零模型）模拟 power；要求 `MDE80 ≤ δ_min`（δ_min 见 §4.2） | `inconclusive_power`，停；不进入效应比较 |
| **P0d 泄漏/公平** | 状态变量无响应派生；细胞分组 CV；A1 证书与 A4 分析集不共享测试标签；S 面板 SHA 预先冻结；置换/随机对照实现 | `leakage`/`design_invalid`，停 |
| **P0e 失败类别/停止写死** | 所有失败类别与触发条件见 §6；不得事后增加"通过"分支 | 未写死 → 不冻结 |

## 3. Phase 0：A1 冲突证书的"状态可解释性"诊断（描述性，不判 F3）

### 3.1 目标与输出

- 目标：在 A1 证书单元上，检验**用药前细胞状态 `S_pre`**（表达/突变/culture 注释）是否能在 `K`（已知协变量）之外解释 A1 冲突（`C_conf` 或冲突标签）；输出 **state-associated instability** 诊断 + 不确定性 + 敏感性 + `measurement_request` 候选。
- 输出：`state_association.csv`（每证书/关系：分数、CI、y 是否使用、覆盖、缺失）、`phase0_report`、`measurement_request.md`。**Phase 0 不产出 F1/F2/F3 判定**。

### 3.2 变量与模型（写死；EPV 限维）

- `K`：tissue/lineage + 剂量设计（A1 `Cond_r` 内的设计字段）+ screen/plate/barcode 元数据 + **cell one-hot（identity 基线）**。
- `S_pre`：表达（≤3 PCs for 54；≤5 PCs for 84）+ 预注册突变二值特征（≤2）+ culture_type（≤2 个二值化水平；54 细胞版）；总数 ≤5（54 细胞）/≤8（84 细胞）。
- `S_measure`（仅作 F1/F2/batch 控制，不进 F3 证据）：`DAY1_NORM_MEAN/SD`、`GROWTH_RATE`、`DOUBLING_TIME`、`BARCODE`（同屏读数，随板变化）。
- 模型（同一 CV/同一调参预算）：
  - M0：噪声/常数；
  - M1：`K`（含 cell one-hot）；
  - M2：`K + S_pre`（主状态增量）；
  - M3：`K + 容量匹配随机 S`（同维随机特征/置换 S）；
  - M4：`K + barcode/plate + screen`（**F1/batch 对照**；替代 v1 的 M4=K+g）；
  - M5：A1 证书基线（A1 自带分数/不确定性）；
  - M6：`K + S_measure`（仅描述性对照，**不得**用于 F3 证据）。
- 主统计量：细胞分组 CV 下，预测 A1 冲突标签/连续冲突量的 **ΔAUC(M2−M1)**；同时报告 M2−M0、M2−M4、M2−M6、以及 M2 对 cell one-hot/plate/leverage 的增量；54/84 两版敏感性。
- **不主判** M2−M1 单独即 F3；所有输出都是 `state_association` 描述。

### 3.3 噪声模型与 flip 阈值（预注册，禁止结果驱动）

- 技术噪声：A2 `q2.json` 的 1,312 barcode 分半四元组（1.43% 覆盖）→ `σ_tech`、`P(flip|noise)`；按 barcode 数分层报告；披露 barcode-rich 选择偏差。
- flip 阈值：`|Q| > z·σ_tech`，z ∈ {1,2,3} 全报告；主阈值 z=2 预注册（仅作**描述性**不稳定检查）；**禁止**按结果反选 z。
- 跨 screen flip 与同 screen 技术噪声之差：**只作描述性不稳定检查，不作 F3 判据**（跨 screen 含批次/周期；A1 的 (ii) 负责关系冲突，不归 A4）。

### 3.4 δ_min（operational；修正 v1 的 0.10 无依据）与 MDE 方案

- **决策层 δ_min（唯一"有用差异"定义）**：`δ_min =` 使 A1 的"状态测量请求"决策**净成本 ≤0** 的最小状态增量。测量成本按 A5 anchored key **34–68 wells/key** 或 1 张 state-readout 板（**1,536 wells/细胞**）计；收益侧 = 避免一次错误关系修订/错误释放的 CU 成本。**在 A1/A5 冻结该成本前，Phase 0 不产出判定**（`blocked_by_utility_definition`）。
- **Phase 0 可执行替代（决策效用未冻结时）**：`δ_min_AUC = max(0.05, 2×SE_null(ΔAUC))`；`SE_null` 用预注册按细胞 cluster bootstrap（≥2,000 次，seed=20261027）在 null 下给出；敏感性档 **{0.05, 0.10, 0.15}** 全报告。**v1 的 δ_min=0.10 只保留为敏感性档，不再作主判据。**
- **MDE 模拟（写死，不运行）**：模型/特征集/λ 网格（内层按细胞分组 CV）、维数上限（54→≤5、84→≤8）、AUC 配对 cluster bootstrap（≥2,000 次、seed=20261027）、零模型（置换状态标签/打乱 plate）、power@δ_min；MDE80≤δ_min 才进入效应比较。

### 3.5 Phase 0 失败类别（写死）

`blocked_by_A1`（A1 未冻结/证书不可得）、`data_unavailable`（覆盖/证书不足）、`design_invalid`（EPV/泄漏/阈值未冻结）、`leakage`、`inconclusive_power`（MDE>δ_min）、`inconclusive_design`（设计/操纵/覆盖检查不过）、`state_associated_instability` 三档（present/absent/inconclusive_design，**仅描述**）。
**Phase 0 inconclusive ≠ F3 不存在/表征无信息**；不得把 `absent` 写成"表征无信息"。

### 3.6 Phase 1 进入条件（**不依赖 Phase 0 显著**；修正死锁）

`A1 冻结 && A1 证书可算 && Phase 0 描述性候选选择规则通过（预注册：按 state_association 分层平衡选细胞/条件；S_pre 覆盖≥50% 或明确缺失处理；Phase 1 可测状态读数可得）&& Phase 1 design check（§5.2）通过`。
- 若 Phase 0 得 `inconclusive_*`，**仍可按上述规则进入 Phase 1**（Phase 1 是 F3 证据入口，不是 Phase 0 的奖励）；Phase 1 若也失败，A4 输出 `measurement_request` 与 `indistinguishable_F1_F3`，不写 F3 不存在。

## 4. Phase 1：状态操纵的最小设计（F3 证据；完整 well 账）

### 4.1 设计（桥接 Phase 0 的 S_pre 与操纵后 S_measure）

| 层 | 选择 |
|---|---|
| 细胞 | 4–8 个 Jaaks/DepMap 可映射细胞系；按 Phase 0 state_association 分层（高/低不稳定）各半；含 2 个以上组织/lineage |
| 药对/条件 | 6–8 个（细胞,药对）条件对，来自 A1 冲突证书候选；按 Phase 0 平衡 flip/non-flip 选择 |
| 状态操纵 | **2 个状态水平**：低/高接种密度（或短/长接种后时间）——同培养基、同板型、同批次框架；**操纵后 S_measure = day1 生长率/活力/汇合度**（与 Jaaks DAY1/GR/DT 同类） |
| 批次 | 2 个独立批次（不同日/不同 passage/不同培养瓶；**barcode 不相交 ≠ 独立培养**） |
| 重复 | 2 个技术重复孔/状态/批（另计 QC/失败） |
| 端点 | `SYNERGY_DELTA_EMAX` 类功能端点；每 (细胞,药对) anchored 设计（2×7 dose = 14 combo wells + 5 anchor-alone + 4 library-alone + 8–16 controls/QC = **34–68 wells/key**） |
| 状态读数 | day1 无药对照板（**1,536 wells/细胞**）；新状态密度优化（**1,344 wells/细胞**）；处理后 viability 读数在 combo 板内 |
| 对照 | vehicle（DMSO，每状态每板）、阳性对照（已知协同对/plate positive）、blank/edge wells、位置随机化、盲法读数；培养基/氧仅作**次级 g 对照**，不进 F3 主证据 |

### 4.2 Well 账（明确算术；修正 v1 的 192/384）

**v1 更正**：`2×2×6×2×2 = 96`（v1 误写 192）；`4×6×2×2×2 = 192`（v1 误写 384）；且 v1 未含单药参照/对照/QC。

**Pilot（2 细胞 × 6 条件 × 2 状态 × 2 批；pair-cell=12）**：
- anchored keys = 2×6×2×2 = **48** → combo+ref+ctrl = 48×(34–68) = **1,632–3,264 wells**
- day1 对照 = 2×1,536 = **3,072 wells**
- 密度优化 = 2×1,344 = **2,688 wells**
- **合计 7,392–9,024 wells ≈ 4.8–5.9 张 1,536 板**（未含 1.5% 失败率；2 重复时翻倍）

**Main（4–8 细胞 × 6–8 条件 × 2 状态 × 2 批）**：

| 组件 | 4×6 设计 | 6×8 设计 |
|---|---:|---:|
| pair-cell 单元 | 24 | 48 |
| anchored keys | 96 | 192 |
| combo+ref+ctrl（34–68/键） | 3,264–6,528 | 6,528–13,056 |
| day1 对照（1,536/细胞） | 6,144 | 9,216 |
| 密度优化（1,344/细胞） | 5,376 | 8,064 |
| **合计 wells** | **14,784–18,048** | **23,808–30,336** |
| **≈1,536 板** | **9.6–11.8** | **15.5–19.8** |

- 若 2 个技术重复孔：wells 再乘 2（除 density/day1 已按板计）；QC 失败 1.5% 另加；板/批固定成本按 A5 计 CU，不在此处用 CU。
- **"每条件对 2 孔"不是许可的隐含假设**：v1 的 192/384 只有在把"每条件对=2 孔"写死时才成立；v2 显式写死技术重复=2（计入上表倍数），不再混用。

### 4.3 功效（写死算法；本轮不运行）

- 独立单位 = pair-cell（24 pilot / 48 main）；主检验 = **配对 exact McNemar**（状态×符号），α=0.05 双侧（或预注册单侧）；预期 discordant 比例由 Phase 0/pilot 预注册（不得事后挑）。
- 粗算（写死为设计输入）：24 配对、discordant 25%、OR≈4 时功效约 **50–60%**（不足 80%）；48 配对同假设约 **80%+**。结论：**24 配对设计只作 pilot/可行性/操纵检查，不产出 F3 证据**；主 F3 证据需 ≥36–48 pair-cell（6–8 细胞 × 6–8 条件），否则 Phase 1 输出 `inconclusive_design` + `measurement_request`。
- MDE 用精确/模拟（≥2,000 次、seed=20261027、按细胞聚类）；`MDE>δ_min` → `inconclusive_power`；不得用"pilot 后再算"替代预注册方案。
- 操纵检查：2 状态×2 批的 `S_measure` 差异必须预注册显著（否则 `manipulation_failed`）；状态读数与操纵强度相关（预注册符号）。

### 4.4 分析（预注册）

1. 主：状态对 (细胞,条件) 的 `sign` 与幅度的影响（配对 McNemar / 混合模型，按细胞/批聚类）；效应方向与 Phase 0 的 state_association 预测方向一致性（预注册符号）。
2. 桥接：`S_measure` 作为显式中介/协变量加入"无状态"模型后，flip/误差是否减少；与只重标定、只加 cell one-hot、只加 plate/barcode 对照比较。
3. 判别 F1/F3 的尝试（**只输出证据，不判类**）：若操纵改变的是测量背景 g（培养基/氧）→ 不能作 F3 证据；若 state-matched 对照（同 g、同批、不同 S_measure）仍出现符号变化且与 S_measure 共变 → 支持"状态驱动"；若所有允许操纵下 F1 重拟合同样解释 → `indistinguishable_F1_F3`。
4. 决策相关（仅作次级描述）：状态条件化后未测选择的排序/预测变化；不报决策净收益（Phase 2 才做，且复用 A5）。

### 4.5 Phase 1 失败类别与停止（写死）

| 类别 | 触发 | 动作 |
|---|---|---|
| `manipulation_failed` | 操纵检查不过/读数缺失 | 停；修操纵或降级为观察 |
| `leakage` | 状态读数/标签/测试信息泄漏 | 立即停；报实现与修复 |
| `indistinguishable_F1_F3` | 状态匹配对照同样变化；或 F1 重拟合完全解释 | 输出诊断；不写 F3 不存在/存在 |
| `inconclusive_design` | pilot 功效/覆盖/操纵检查不过 | 停；给 `measurement_request` 与所需规模 |
| `inconclusive_power` | 主设计 MDE>δ_min | 停；报所需 pair-cell/批 |
| `state_irrelevant` | 状态关联但不改善未测排序 | 保留状态描述；不升级 |
| `cost_sensitive` | 若接 Phase 2，A5 三价格场景排序不一致 | 不报赢家；退回 A5 |

## 5. Phase 2（仅当 A1 请求 + Phase 1 支持 + A5 冻结）

- **直接复用 A5**（`acquisition_stage3/spec.md`、`cost_model.md`、`protocol_draft.md`）：同一菜单/动作类型、total CU 等成本、三价格场景（optimistic/central/conservative）+ filler/容差、`MDE_decision ≤ δ_min ≤ headroom`、`cost_sensitive` 处理；A4 只把"状态测量动作"作为菜单中的一类动作，不另造成本/指标/停止规则。**A5 当前 revise 未冻结 → Phase 2 不启动。**

## 6. 泄漏/公平/新鲜度（写死）

1. A1 证书、S 面板（SHA）、模型/特征集、δ_min/敏感性档、seed、失败类别全部在接触任何测试标签前冻结。
2. 细胞分组 CV（同细胞不跨折）；A1 证书测试单元与 A4 分析集不共享测试标签；A4 不使用 A1 未冻结的判定。
3. 所有对照同信息/同调参预算；随机/置换对照实现入库；`S_pre` 缺失处理预注册（缺失指示，不插补响应）。
4. Phase 1 独立培养/批次/盲法/位置随机化写死；培养基/氧只作 g 对照；不把 barcode 不相交当独立培养。
5. 输出分离：Phase 0 只写 `state_association`；Phase 1 只写状态证据；F1/F2/F3 由 A1 写。

## 7. 谱系/边界引用（写死）

- **A1**：v1 的 P6=(iii) 状态 z 改善残差、P7=三类签名互不替代（`conflict_signal/spec.md` §7）；A1 v2 已重编号（P6 `setup_error`、P7 注入体检/泄漏）且 (iii) 仅 `proxy_only`（`spec_v2.md` §2/§7）→ A4 v2 以 A1 **v2 接口**为准；A1 未冻结 → `blocked_by_A1`。
- **A2**：v3 §0/§1 已把 III 认证→A4；A4 只用 A2 排除域/候选状态，不评 A2 约束。
- **A3/C175**：`not_qualified` 只对冻结大规模门槛；A4 不引用 41/4,179 作证据。
- **C160/C167/C171/C172/C174/C176/C177**：细胞状态分支停于检定力非无信息；R192 未复现≠否证；R193-A1 inconclusive 非阴性；1.43% 仅加性份额；R196/R197 已作废（不复活）。
- **A5**：Phase 1 well 账/Phase 2 等成本全部引用 A5；A5 冻结前不启动 Phase 2。
- **本轮无新检索**：不声称新颖性/差异；"未发现直接先例"只作既往登记结果。

## 8. 冻结清单（若 Lead 要冻结本协议）

1. A1 冻结并给出证书 schema（字段/单位/缺失规则）。
2. A4 状态面板冻结（`S_pre` 列表/维数/54/84 版本、缺失处理、SHA）。
3. Phase 0 模型/λ 网格/EPV/δ_min（决策效用或 reliability-adjusted 门）/MDE 模拟方案/seed/失败类别全部写死。
4. Phase 1 设计（细胞/条件/状态/批次/重复/板型/well 账/操纵检查/桥接/盲法/独立培养）与功效模拟写死；采购报价替换 A5 系数后才可执行。
5. Phase 2 等 A5 冻结后另行接入。
6. 独立挑战者复审（未参与 A4 v2 修订）。

## 9. 本轮状态

**本轮不运行任何 Phase；不训练/不拟合/不估 Q/不读响应；不声称新颖性/机制/决策收益；A4 = `blocked_by_A1` 的 DRAFT 模块。**
