# R198-A2v4 规格补丁（spec_v4.md）

日期：2026-10-27 · 角色：定向核验员（lit-verifier）· task-51
补丁对象：A2v3（[spec_v3.md](spec_v3.md)/[protocol_draft_v3.md](protocol_draft_v3.md)）；本文件 = **并入 A1 整体冻结前的 5 条短补丁**（依据 [challenge_A2_v3.md](challenge_A2_v3.md)，revise）。未变内容以 v3 为准；本文件只写差异。
**本轮不运行效果/模拟器/训练/回放/拟合；不读响应做效果；不声称新颖性。**

## P1｜模拟器实现（挑战必改 1）

- 新增 [constructive_sim_v4.py](constructive_sim_v4.py)：**完整实现、只落盘不运行**（本轮已做 `compile()` 语法检查，未执行；无副作用）。
  - `load_units()`：从 folds.json + state_z.json + GDSC **身份/注释/设计列**构造单元宇宙（无响应列）。
  - `make_world()`：**真正生成 y**（b_cell+b_pair+b_dose+g_group+h_state·z+ε；注入 I/II/III/null；II 用 3 个 out-of-condition 细胞组符号翻转）。
  - `sample_batch()`：k=6/12/20/24/36 的显式分配与复用（20 结构化批次：10 in/10 out、z 各 5；24 加 4 备用；36 加 16 独立确认批次）。
  - `classify()`：规则 1–5（r_I nuisance 重估；condition gap≥0.20 + ≥5 细胞组翻转；残差结构 + ≤6 候选 max-stat 识别；null_ok/unresolvable）。
  - `endpoints()`/`verdict()`：E1–E4/E4b + null gate（§P3），partial/fail 归属（§P4）。
  - `--confirm-run` 门禁：无该 flag 只打印计划；**本轮未执行任何模式**（连 `--plan` 都未运行；只做语法编译）。
- 冻结文本修正：`mde_plan()["estimated_runtime_min"]` 明写 **"UNVERIFIED PLANNING VALUE"**；冻结清单不得写"可执行已落盘"，只写"实现已落盘、未验证/未运行"。
- SHA256：`3f5d4c3747d32320cae8498e06146a31b1e3df96ef6750cbe6bb20984c202464`（record_v4 §3）。

## P2｜z 的逐单元定义与冻结产物（挑战必改 2）

- 新增 [state_z.json](state_z.json)（metadata-only，4.4 MB；SHA256 `8a475bb6442cacce811423953e777675cb125b4915b3c187cd27134ffa603872`）：
  - **分析单元**：cell × directed pair（108,259 单元）；单元键 `(CELL_LINE_NAME, ANCHOR_NAME, LIBRARY_NAME)`。
  - **行级规则**：`BARCODE` 数字串取整 → mod 2 得行级 z（覆盖率 **296,707/296,707 = 100%**，0/1 平衡 148,613/148,094）。
  - **单元级聚合**：单元内所有行级 z 取**多数**；多数并列时取**该单元最小数值 BARCODE 的奇偶**（确定性）；无 barcode 的回退规则登记为"不需要"（0 单元）。
  - 结果：108,259/108,259 单元有 z；0/1 平衡 **54,251/54,008**；并列 tie 单元 **5,967**。
  - **Q 单元（4 个 cell×condition 键）聚合规则**（休眠，A2v4 不用 R193-A0 四元组）：4 键 z 多数；并列取字典序最小 (cell,condition) 键的 z。
  - **共线/可识别性检查**（Cramér's V）：z vs `cell_groups_8` = **0.0214**；vs `Tissue` = **0.0138**；vs `drug_type 同/异` = **0.0107** → 非共线（冻结要求 V≤0.30）。
  - **同一份**：生成器注入 III 的 z 与 K_A2 候选状态判别**必须读取同一 `state_z.json`**；禁止另行推导。
- 候选状态清单（≤6）：Tissue、drug_type 同/异、cell_groups_8、**state_z.json 的 z**、A4 提供状态（若可用；版本另记）；`dose_layout` 因设计列是管道分隔的浓度序列、非标量，**v4 不作为候选**（明示，避免不可复现的分箱）。

## P3｜E3 null abstention 规则 + E1/E4b 口径（挑战必改 3）

- **选择 (a)**：**null unresolvable 率 ≤0.50（即 null resolved ≥0.50）作为设计体检 gate**（与 E3 并列，写入 verdict）。
  - E3：null 上 false-class 率（decision ∈ {I,II,III}）≤0.10；null 上 abstention 计为"无假类"。
  - null gate：`null_unresolvable ≤ 0.50`（若失败 → constructive_fail；不再保留 v3 的"resolved≤0.50 卫生上限"反向写法）。
- **E1 类权重（写死）**：class-balanced——I 权重 0.5，{II,III} 合并权重 0.5（II/III 在池内等权，各 0.25）；**分母=全部非 null 世界，abstention=错**。
- **E2**：II 与 III 各 0.5 类平衡；abstention=错。
- **E4b "每类"明确 = I/II/III 三类（不含 null）**，每类 resolved ≥0.85；null 由独立 null gate 管。
- 算术自洽不变：E4≤0.10 ⇒ resolved≥0.90；E1 all-world 0.80 ⇒ resolved accuracy ≥0.889；E2 ⇒ ≥0.778。

## P4｜无序敏感性组定义、k=6 z 读法、partial/fail 归属（挑战必改 4）

- **无序敏感性组（规范方向）**：对 unordered 药对 {A,B}，定义**规范方向 = 药名字典序较小者为 p1 臂、较大者为 p2 臂**；组标签 =（p1 的 pathway, p2 的 pathway）。按此规则重算：**320 组，≥2 药对 209，≥4 药对 119（覆盖 971 个无序对）**——**替代 v3 的 305/215/117**（v3 用 `.first()` 非规范方向，不可复现，撤回其作为敏感性口径）。有向主口径（331/275/165/1,698 对/90,589 单元）不变。
- **k=6 的 z 分配读法统一**：`z_total` 是**跨 6 单元的总数**（z=0 共 3、z=1 共 3），**不是每层 3/3**；k=6 不判 III。k=12/20 的 `z_total` 同为总数（6/6、10/10），且每层内部按 z 平衡分配（12：每层 3/3；20：每层 5/5）。`k_allocation` 已按此实现。
- **constructive_partial/fail 归属（写死）**：E1 失败 → `constructive_fail`；E1 过而 E2 失败 → `constructive_partial`；E1/E2 均过但 **E3 或 E4 或 E4b 或 null gate 任一失败 → `constructive_fail`**（不归 partial）。判定顺序与函数见 `constructive_sim_v4.verdict()`。
- II 的 ≥5 独立语境：**8 个细胞组中 5 个 in-condition 组**（预注册条件谓词 G0–G4 = in，G5–G7 = out）；判别按细胞组计翻转数。

## P5｜冻结清单/预算/披露文本修正（挑战必改 5）

- 冻结清单修正：`constructive_sim_v4.py` 标 **"[x] 实现已落盘、未运行"**、`constructive_sim.py`（v3 骨架）标 **"[x] 骨架（历史，不再作为可执行件）"**；新增 `state_z.json` 条目。
- 预算 `/mde_plan` 的 ≤5 min 一律写 **"未验证的规划值（UNVERIFIED PLANNING VALUE）"**；实际耗时须在冻结后首次运行记录。
- 报告/冻结文本不得写"可执行已落盘/已通过"；constructive 与 MDE 仍是**冻结后执行项**。
- 其余（不声称新颖性、C1′ QA only、replay 不报归因正确率/收益、C176/C177、A4/A5 接口、κ 仅兼容性）沿用 v3。

## 补丁落点索引

| 挑战必改 | 落点 |
|---|---|
| 1 模拟器实现 | `constructive_sim_v4.py`（SHA 见 P1）+ protocol_v4 §3 + 冻结清单 P5 |
| 2 z 产物 | `state_z.json`（SHA 见 P2）+ protocol_v4 §3.1 |
| 3 E3/null/E1/E4b | 本文件 P3 + protocol_v4 §3.3 |
| 4 无序组/k=6/partial | 本文件 P4 + protocol_v4 §1/§3.4 |
| 5 冻结清单文本 | 本文件 P5 + protocol_v4 §6 |
