# R198-A2v4 PROTOCOL 补丁（protocol_draft_v4.md）

**状态：DRAFT；并入 A1 整体冻结前补丁，未冻结、未执行。** 本轮**不运行效果/模拟器/训练/回放/拟合**。未列内容以 [protocol_draft_v3.md](protocol_draft_v3.md) 为准；本文件只写 5 条短补丁后的差异（依据 [challenge_A2_v3.md](challenge_A2_v3.md)）。

## §1 切分 / S / U（v3 不变 + 两处修正）

- 折、S24、U 规则与数值沿用 v3（folds.json 不变；SHA `3546E34E…9DD7`）。
- **无序敏感性组定义（新写死）**：unordered {A,B} 规范方向 = 药名字典序较小者为 p1、较大者为 p2；组标签 =（p1 pathway, p2 pathway）。重算口径：**320 组 / ≥2=209 / ≥4=119（覆盖 971 个无序对）**；v3 的 305/215/117（`.first()` 非规范方向）**撤回**。有向主口径不变（331/275/165/1,698 对/90,589 单元）。
- **k=6 z 读法（新写死）**：`z_total` 为跨 6 单元总数（z=0 共 3、z=1 共 3），非每层 3/3；k=6 不判 III。k=12/20 每层内 z 分别 3/3、5/5（总 6/6、10/10）。

## §2 约束库（v3 不变）

C2′ 有向主、C1′ QA、C4′ exploratory、C6′ QA；C3→R196v2、C5→R197v2；候选状态清单改以 `state_z.json` 的 z 为准（≤6：Tissue / drug_type 同异 / cell_groups_8 / state_z z / A4）。

## §3 Constructive 判别体检（补丁）

### §3.1 状态 z（新）
- 唯一来源 **[state_z.json](state_z.json)**（SHA256 `8a475bb6442cacce811423953e777675cb125b4915b3c187cd27134ffa603872`）：
  - 行级 z = BARCODE 数字串 mod 2（覆盖 296,707/296,707=100%）；
  - 单元（cell×directed pair）级 z = 单元内多数，并列取最小数值 BARCODE 奇偶；无回退（0 单元）；108,259 单元全覆盖；平衡 54,251/54,008；tie 5,967；
  - Q 单元（4 键）聚合规则：4 键多数，并列取字典序最小 (cell,condition) 键（休眠）；
  - 共线性：Cramér's V vs cell_groups_8 0.0214 / Tissue 0.0138 / drug_type 0.0107（冻结要求 V≤0.30）。
  - **生成器注入 III 的 z 与 K_A2 候选判别必须读同一文件**，不得重算。
- 世界生成器（[constructive_sim_v4.py](constructive_sim_v4.py)，实现已落盘、**未运行**；SHA256 `3f5d4c3747d32320cae8498e06146a31b1e3df96ef6750cbe6bb20984c202464`）：y=b_cell+b_pair+b_dose+g_group+h_state·z+ε；II = 3 个 out-of-condition 细胞组（G5–G7）符号翻转；III = h_state=δ 乘 state_z 的 z；I = nuisance 加 δ；null = 仅 ε。σ∈{0.5,1,2}×δ∈{1σ,2σ}×4 世界/格=24/类。

### §3.2 K_A2 判别器（v3 规则不变，实现见 sim §classify）
r_I（nuisance 重估）；condition gap≥0.20 且 ≥5 细胞组翻转 → II；残差结构（dip/2 成分 BIC/候选方差比）+ ≤6 候选 max-stat 置换识别 → III（输出 identified_state）；否则 null_ok/unresolvable。

### §3.3 终点与记账（补丁：E3/null gate/E1 权重/E4b）
| 终点 | 定义 | 判定 |
|---|---|---|
| E1 | class-balanced：I=0.5，{II,III}=0.5（池内各 0.25）；分母=全部非 null 世界，abstention=错 | ≥0.80；MDE≤δ_min=0.30 |
| E2 | II vs III 各 0.5；abstention=错 | ≥0.70；MDE≤0.20 |
| E3 | null false-class 率（decision∈{I,II,III}；null abstention 计无假类） | ≤0.10；MDE≤0.05 |
| **null gate（新，选 (a)）** | **null unresolvable 率 ≤0.50（resolved≥0.50）** | 进设计体检；失败→`constructive_fail` |
| E4 | 非 null unresolvable 率 | ≤0.10；MDE≤0.10 |
| E4b | **I/II/III 三类**各自 resolved ≥0.85（**不含 null**；null 由 null gate 管） | 全部满足 |
- 算术自洽：E4≤0.10⇒resolved≥0.90；E1 0.80⇒resolved acc≥0.889；E2⇒≥0.778。
- MDE = 80% 功效可分辨的正确率/率差（同单位、≥1,000 模拟批）；MDE>δ_min ⇒ `design_uninformative`。

### §3.4 预算表（补丁：k=6 读法/partial-fail）
- k 分配实现于 `constructive_sim_v4.k_allocation()`：6（3in/3out，z 总 3/3）；12（6/6，每层 z 3/3）；**20（10/10，每层 z 5/5；I+II+III）**；24（20+4 备用；replay I+II）；36（20+16 确认批次 8/8，z 每层 4/4；仅稳定性，不放宽阈值）。
- **partial/fail 写死**：E1 失败→`constructive_fail`；E1 过而 E2 失败→`constructive_partial`；E1/E2 过但 E3/E4/E4b/null gate 任一失败→`constructive_fail`。
- MDE/模拟器预算：96 世界×~90,589 单元 + 4 终点×4 k×1,000 批轻量分类；**"≤5 min" 是未验证规划值（UNVERIFIED PLANNING VALUE）**，硬上限 30 min；首次运行须记录实测。

## §4 真实 replay（v3 不变）
仅 constructive_pass（或 Lead 允许 partial）后；只报 C2′ 违反分布、归因分布（描述）、U 上 top-k 预测排序/描述性后悔；不报归因正确率/收益/机制。

## §5 接口（v3 schema `a2_to_a1/v3` 不变）
κ≥0.60 仅兼容性；A1/A2 同类判别不互作验证；仲裁 `interface_disagreement`；A4/A5/C3/C5 归属不变；引 C176/C177。

## §6 冻结清单（补丁文本）
- [x] `folds.json`（v3；SHA `3546E34E…9DD7`）
- [x] `constraints_check.json`（v3；有向口径；SHA `B35018F7…3039`）——**注**：无序敏感性口径以 v4 §1 的规范方向为准（320/209/119），冻结时重生成 `constraints_check_v4.json`
- [x] **`state_z.json`（v4 新增；SHA `8a475bb6…3872`）**
- [x] `constructive_sim_v4.py`：**实现已落盘、未运行**（SHA `3f5d4c37…2464`）；`constructive_sim.py`（v3 骨架）标"历史，不再作可执行件"
- [ ] `SYNERGY_DELTA_EMAX` 列义确认（引 R198 record）
- [ ] 候选状态版本（state_z v1 + A4 状态）写死；V≤0.30 共线 gate
- [ ] constructive 体检与 MDE（≥1,000 批）**冻结后执行**；耗时实测记录；不得写"已通过"
- [ ] 预算标注"未验证规划值"；replay 不报正确率/收益；C1′ QA only
