# R198-A2v3 独立复审（task-49）：约束库 / constructive 判别体检模块

2026-10-27。角色：独立挑战者（非提案者、未参与 A2、不运行模拟器/效果）。对象：[spec_v3.md](spec_v3.md)、[protocol_draft_v3.md](protocol_draft_v3.md)、[REVISION_A2_v3.md](REVISION_A2_v3.md)、[record_v3.md](record_v3.md)、设计版 [folds.json](folds.json)/[constraints_check.json](constraints_check.json)/[constructive_sim.py](constructive_sim.py)；参照 [challenge_A2_v2.md](challenge_A2_v2.md)、[challenge_A2.md](challenge_A2.md)、R198 record。**本轮不运行模拟器/效果/训练/回放、不读响应做效果、不改 A2 产物；只写本文件与 `tmp/`。**

> 说明：Lead 先给的 task-48 不存在（task-48 是 A1 Stage0 的工程任务；我没写它的任何文件），本文件按更正后的 **task-49** 完成。

## 0. 结论先行

**总判决：revise（≤5 必改；均为"并入 A1 整体冻结前"的短补丁，无需重跑——A2 尚未运行）。完成必改 1–3 后即可并入 A1 整体冻结；当前形态不建议直接并入。**

v3 对 v2 三个致命问题做了**实质性修复**，且设计版产物经我独立核验基本可信：
① **III/E2 可达性**：z 从"随机不可观测"改为 **BARCODE 派生、可观测、未进入模型/关系**的候选状态；K_A2 改为两步（残差结构统计量 + ≤6 候选 max-statistic 置换识别；未识别→`unresolvable`；仍失败→`constructive_partial`）；E2 不再构造上不可达 ✓。
② **abstention 记账**：E1/E2 分母=全部非 null 世界、abstention 计错；E4 收紧至 ≤0.10 + 每类 resolved≥0.85；且给出"E4≤0.10 ⇒ resolved≥0.90；E1 all-world 0.80 ⇒ resolved_acc≥0.889；E2 ⇒0.778"的算术自洽 ✓。
③ **预算表**：改成"20 单元结构化批次（10 in/10 out；每层 z 5/5）同时满足 I(20)/II(10 vs10)/III(z 各10)"，k=6/12/20/24/36 显式分配；不再有 6+20+12=38 的算术冲突 ✓。
④ **δ_min 同单位**：δ_min=目标−机会（E1 0.30/E2 0.20/E3 0.05/E4 0.10），MDE 定义为同单位正确率/率差，MDE≤δ_min 才推进 ✓。
⑤ **单位/U-S/接口**：C2′ 有向主、U/top-k 无序主、双口径；U=both-unseen−S 涉药对；S=24 directed/24 unordered；删除 v2 错误断言；`a2_to_a1/v3` schema；κ 仅兼容性 ✓。

**但仍有 3 个会在 A1 冻结后立刻反咬的缺口（详见 §2）：**
1. **`constructive_sim.py` 不是可执行模拟器，是 DESIGN STUB**：`make_world()` 只返回参数字典、不生成世界；`classify()` 直接返回 `DESIGN_STUB_NOT_IMPLEMENTED`；`endpoints()` `raise NotImplementedError`；`--confirm-run` 也 `raise SystemExit`（[constructive_sim.py:42-51,69-91,110-121](constructive_sim.py#L42)）。因此 E1–E4 可达性、MDE≤δ_min、≤5 min 预算目前都只是**计划**，冻结清单里"constructive_sim.py 已落盘"是按"骨架落盘"写的，不是可执行设计。**并入 A1 冻结前必须把模拟器实现完整（不运行）并重记 SHA**，否则 A2 模块冻结的是一个无法执行的占位。
2. **z 的分析单元定义/冻结产物缺失**：spec 说 z=BARCODE 派生 2 水平、"数字后缀奇偶/分组"，但 (a) BARCODE 是**行级**（同一 cell×condition 键可有多个 barcode），而分析单元是 cell×pair Q 条目（由 4 个键构成）；(b) `folds.json`/`constraints_check.json` 里**没有 z 的逐单元取值**，`constructive_sim.py` 只加载 `folds.json`，`make_world` 也没有 z 数据；(c) 判别器候选里又要用 z 做残差分层。**必须新增一个元数据-only 的 `state_z.json`（键/单元→2 水平；规则与聚合写死、SHA 冻结）**，并把"z 的单元级取值 + 判别器可见、生成器注入同一份"写死，否则 E2 仍依赖实现者自由解释。
3. **E3 的 null abstention 规则方向写反/可被刷过**：spec/protocol 写"abstention 在 null 上计为无假类（正确），null resolved rate 只作描述且 **≤0.50** 为卫生上限（不作为判定；防'全 abstain 过 E3'由 E1/E2/E4b 挡住）"（[spec_v3.md:79-84](spec_v3.md#L79)、[protocol_draft_v3.md:66-67](protocol_draft_v3.md#L66)）。但：全 abstain 时 null resolved=0 ≤0.50，**正好通过**这个"上限"；E1/E2 只覆盖非 null 世界、E4b 的"每类"若指 I/II/III 也不含 null → **没有任何判据挡住 null 全 abstain**，E3（false-class=0）可被刷过。必须改为"null **unresolvable** 率 ≤0.50（即 resolved≥0.50）"作为判定条件（或把 null abstention 计为假类），并写死 E1 balanced accuracy 的类权重（I vs {II,III} 的平衡口径）。

**是否可并入 A1 整体冻结：完成必改 1–3（+4/5 的文本小修）后可并入；当前形态不建议。**

## 1. v2 挑战 5 条必改的落实状态

| v2 必改 | v3 落点 | 状态 |
|---|---|---|
| 1. III/E2 可达性 + abstention 记账 | z=BARCODE 派生可观测未建模状态；K_A2 两步（残差结构 dip/潜类 BIC/方差比 + ≤6 候选 max-stat 识别；未识别→unresolvable/partial）；E1/E2 全非 null 世界、abstention 计错；E4≤0.10+E4b resolved≥0.85；E3 null 记账与卫生上限 | **已落实（但 E3 方向 bug、z 单元定义缺失，见 §2）** |
| 2. 预算-功效表重写 | 20 单元结构化批次同时满足 I/II/III；k=6/12/20/24/36 显式分配与复用；II 的 5/8 细胞组；96 世界×90,589 单元/MDE 4×4 k×1,000 批≈≤5 min | **已落实（算术自洽；但模拟器为 stub，时间未验证）** |
| 3. MDE/δ_min 同单位 | δ_min=目标−机会（0.30/0.20/0.05/0.10）；MDE=同单位正确率/率差；MDE≤δ_min；≥1,000 批 | **已落实** |
| 4. 药对单位 + U/S 不相交 | 有向主口径（2,025/331/275/165/90,589）与无序敏感性（1,294/305/215/117）；U=both-unseen−S 涉药对；S 24 directed ∧ 24 unordered；删 v2 错误断言 | **已落实（我独立核验 S/U 不变量全部成立；无序组定义仍缺，见 §2-4）** |
| 5. 接口/冻结清单补齐 | `a2_to_a1/v3` schema；κ 仅兼容性；folds.json/constraints_check.json/constructive_sim.py 落盘记 SHA；C176/C177/A4/A5；C1′ QA only；replay 不报正确率/收益 | **已落实（但 simulator 是 stub；无序组定义缺失）** |

## 2. 仍缺项（≤5 必改，A1 冻结前完成）

### 必改 1｜把 `constructive_sim.py` 从 STUB 变成可执行设计（不运行）
- 证据：`make_world()` 仅返回 `{class,sigma,delta,seed,groups,injection}`，没有生成 y；`classify()` 返回 `{"decision": None, "reason": "DESIGN_STUB_NOT_IMPLEMENTED"}`；`endpoints()` 直接 `raise NotImplementedError`；`main()` 在 `--confirm-run` 时也 `raise SystemExit("--confirm-run is not implemented in the design version; implement at freeze.")`（[constructive_sim.py:42-51,69-91,110-121](constructive_sim.py#L42)）。
- 要求：在并入 A1 冻结前实现完整管线（世界生成器：按 folds.json 维度 + z 状态产物 + b_cell/b_pair/b_dose/g/h_state/ε；II 的 5/8 细胞组翻转；K_A2 规则 1–5 含候选 max-stat；E1–E4 与 MDE 模拟），**仍不运行**；重记 SHA 并更新冻结清单。`mde_plan()` 里的 "estimated_runtime_min: <=5" 必须标注"未验证的规划值"（现在只是计划）。若 Lead 选择"冻结后实现"，则冻结清单不得把模拟器写作"已落盘可执行"，报告只能写"设计已冻结、实现待补"。

### 必改 2｜z 的逐单元定义与冻结产物（E2 可达性的另一半）
- 证据：spec 只说"BARCODE 数字后缀奇偶/分组构造 2 水平"（[spec_v3.md:57](spec_v3.md#L57)），但 BARCODE 是行级、Q 单元由 4 个 cell×condition 键构成，`folds.json`/`constraints_check.json` **没有 z 的单元取值**；`constructive_sim.py` 的 `load_design()` 只读 `folds.json`，`make_world()` 无 z 数据。
- 要求：新增元数据-only `state_z.json`（或写入 folds.json）：对每个分析单元/键给出 2 水平 z 的确定性算法（例如 BARCODE 数字后缀奇偶；同一 cell×condition 键多 barcode 时取规则如"多数/最小 barcode/均值阈值"）；SHA 冻结；写明生成器注入的 z 与判别器候选使用的 z **是同一份**；写死 z 与其他候选（尤其 cell_groups_8、Tissue、drug_type、dose_layout）的构造独立性检查（避免 z 与 cell 组高度共线导致 identified_state 不是 z）。

### 必改 3｜E3 null abstention 规则 + E1 平衡准确率口径
- 证据：spec/protocol "null resolved rate ≤0.50 为卫生上限（不作为判定；防全 abstain 过 E3 由 E1/E2/E4b 挡住）"（[spec_v3.md:83](spec_v3.md#L83)、[protocol_draft_v3.md:66-67](protocol_draft_v3.md#L66)）；但全 abstain 时 null resolved=0≤0.50，E1/E2 不含 null、E4b 若为 I/II/III 类也不含 null → 没有判据挡住。
- 要求（二选一写死）：(a) 把"null **unresolvable** 率 ≤0.50"（即 null resolved≥0.50）加入设计体检判定条件；或 (b) null 上的 abstention 计为假类（则 E3 = false-class rate 含 abstention；不再需要 0.50 上限）。同时写死 E1 的 balanced accuracy 类权重：I vs {II,III} 是**类平衡**（各 24 世界等权，合并类权重 0.5/0.5）还是世界平衡（I=24 vs 非I=48，需按世界数加权）——现在只写"balanced accuracy"未定义；E2 的 II/III 各 24 等权可直接类平衡。E4b "每类"要明确是否含 null（建议明确"I/II/III 三类"）。

### 必改 4｜无序敏感性组定义 + k=6 z 分配 + partial/fail 判定补齐
- **无序敏感性 305/215/117**（[constraints_check.json](constraints_check.json)）没有定义：有向对的两个方向在无序化后，pathway-pair 组用哪一臂的（anchor 通路, library 通路）？建议写死"按有向对 (anchor_id, library_id) 字典序取规范方向"或"两个方向各算一次再合并"；否则 305/215/117 不可复现。
- **k=6 的 z 分配**：spec_v3 §4.5 表写"6 单元：3 in/3 out（z 各 3）"（总 z 各 3），但 `constructive_sim.py` 的 `k_allocation` 写 `6: {"in":3,"out":3,"state_per_stratum":3}`（每层 3/3 需要 6 单元/层，矛盾）；必须统一"每层 z 计数 vs 总计"的定义（k=12 的 `state_per_stratum:3` 也有同样读法歧义）。
- **`constructive_partial`/`constructive_fail` 的完整判定**：spec §4.3 只写"E1 过而 E2 不过→partial；E1 不过→fail"，没有写 E3/E4/E4b 失败时归 partial 还是 fail；必须写死（建议任一 E3/E4/E4b 失败 → `constructive_fail`，E1 过仅 E2 不过 → partial）。
- 顺带：E1 "I vs {II,III} balanced accuracy" 在 24 世界/类下，若按类平衡，I 权重 0.5、II+III 合计 0.5（各 0.25）；这些权重必须写进判别/体检脚本，否则 E1 的 0.80 与 δ_min 0.30 的对应不唯一。

### 必改 5｜冻结清单/预算/披露的文本修正
- 冻结清单把 `constructive_sim.py` 勾成 `[x] 已落盘`（[spec_v3.md:114](spec_v3.md#L114)）；在必改 1 完成前应写 `[ ] 骨架已落盘、实现待补`，并新增 `state_z.json` 条目。
- `mde_plan` 的 "estimated_runtime_min: <=5" 与 spec"估计 ≤5 min，硬上限 30 min"均未验证（未运行）；报告/冻结文本一律写"未验证的规划值"。
- 记录里"设计版产物 **不是**任何世界生成或效果结果"✓；但 `constructive_sim.py` 名为 DESIGN VERSION 却含 `--confirm-run` 门禁——门禁本身 OK（防止误跑），但"实现待补"需明示，避免 A1 冻结时误以为可直接执行。

## 3. 只读核验附录（我独立复算/检查，均通过）

- **SHA256** 与 record_v3 一致：folds.json `3546E34EBA1CAF41C206F3C5742905F908C27083CDCF354265E055EE193C9DD7`；constraints_check.json `B35018F70C97BF2A67FC473B708654501A8BE6B6E454D40F8D58B28271E93039`；constructive_sim.py `2D9E0D61C753EAE6EE85352864E904F2A5758B7B624292ED84C5DCEC5C621AE6`；spec_v3 `E638955C…`；protocol_v3 `1EE0A4F5…`。
- **folds.json 不变量（逐折）**：5 折各 13 held 药；both-unseen directed 45/66/72/82/108、unordered 33/49/48/49/58、cell×directed-pair 单元 1,898/3,693/3,588/4,613/6,232；**S24 每折恰 24 个单元、24 个不同 directed 对、24 个不同 unordered 对**，S 的 directed/unordered 对与 U 交集均为 **0**（U 定义已排除）；S 的 tissue 计数每折均 ≥2/组织（fold0 16/3/5、fold1 20/2/2、fold2 18/3/3、fold3 12/6/6、fold4 14/8/2）；U 大小 **directed 21/42/48/58/84、unordered 9/25/24/25/34**，与 claims 一致；`top-k` 规则 fold0=5/其余=10 ✓；`cell_groups_8` 大小 16/16/16/16/16/15/15/15 ✓。
- **constraints_check.json**：331 组；≥2=275（1,969 对）；≥4=165（1,698 对/**90,589 单元**）；target ANCHOR 40=34+6、LIBRARY 58=51+7（无 ≥3）；逐折 Ref 组覆盖与 test 组覆盖已落盘；零分布计划写明未运行；无序敏感性 305/215/117 已给（但组定义缺失，见必改 4）。
- **预算表算术**：k=20 的 10 in/10 out、每层 z 5/5 ⇒ II 10/10、III z 各 10、I 20；k=12 的 6/6、每层 z 3/3 ⇒ III z 各 6、II 6/6<10 不判；k=6 见必改 4 的分配歧义；k=24=20+4 备用、III 只 proxy；k=36=20+16 确认批次（8/8；z 4/4，II 不达只作稳定性描述）——除 k=6 读法外**算术自洽**，v2 的 38/26 冲突已消除 ✓。
- **E3/E4 算术**：E4≤0.10⇒resolved≥0.90；E1 all-world 0.80⇒resolved_acc≥0.889；E2⇒≥0.778 ✓（与文档一致）；E4b 每类≥0.85 与 E4 总体≤0.10 可共存（需非均匀）；E3 见必改 3。
- **`constructive_sim.py` 只读检查**：无响应列读取；`--plan`/无 `--confirm-run` 时只打印计划；`--confirm-run` 抛 SystemExit（stub）；`DESIGN_STUB_NOT_IMPLEMENTED`/`NotImplementedError` 确认未实现。

## 4. 结论与并入条件

- **是否可并入 A1 整体冻结**：完成必改 1–3（模拟器实现/z 单元产物/E3 规则）与 4–5（文本/定义补齐）后**可以**；当前**不建议**。
- **验证性质**：A2v3 仍为 DRAFT，"设计上可检验"不等于已检验；constructive 体检/MDE 必须冻结后运行，且其结果只能支持"在注入世界里的判别器可分性/Gate"；replay 不报归因正确率/收益、不写机制/迁移/新算法。
- **本轮不运行模拟器/效果**：本复审未运行 A2 模拟器、未读响应、未改 A2 产物（v1/v2/v3）、未写其它目录；只写本文件与 `tmp/`。

**一句话：v3 把 v2 的三个致命问题（III/E2 不可达、预算 38 vs 36、MDE/δ 单位混用+abstention 记账）实质修好了；三统一数字、S/U 不变量、20 单元结构化批次的算术经我独立核验成立；但 `constructive_sim.py` 仍是返回 `DESIGN_STUB_NOT_IMPLEMENTED` 的骨架（E1–E4/MDE/≤5 min 都未验证）、z 的逐单元定义与冻结产物缺失、E3 null abstention 规则写反可被"全 abstain"刷过——完成必改 1–5（短补丁、无需重跑）后可并入 A1 整体冻结，当前形态不建议。**
