# R198-A2v4 修订报告（REVISION_A2_v4.md）— 逐条回应 A2v3 复审 5 补丁

日期：2026-10-27 · 角色：A2 提案者（lit-verifier）· task-51
对象：[challenge_A2_v3.md](challenge_A2_v3.md)（revise，5 短补丁）。v1–v3 文件保留不改（SHA 见 record_v4 §4）；v4 新增：[spec_v4.md](spec_v4.md)、[protocol_draft_v4.md](protocol_draft_v4.md)、本文件、[record_v4.md](record_v4.md)、[usage_v4.json](usage_v4.json)、[constructive_sim_v4.py](constructive_sim_v4.py)（实现已落盘、**未运行**）、[state_z.json](state_z.json)。
**本轮不运行效果/模拟器/训练/回放/拟合；不读响应做效果；不改 A1 产物；不声称新颖性。**

## 必改 1：模拟器从 STUB 变成完整实现（只落盘不运行）

| 复审问题 | v4 落实 |
|---|---|
| `make_world` 不生成 y；`classify`/`endpoints` 是 stub/NotImplemented | 新增 `constructive_sim_v4.py`（SHA256 `3f5d4c3747d32320cae8498e06146a31b1e3df96ef6750cbe6bb20984c202464`）：`load_units()` 从 folds.json+state_z.json+GDSC 身份/注释/设计列构造单元；`make_world()` **真实生成 y**（b_cell+b_pair+b_dose+g_group+h_state·z+ε；四种注入）；`sample_batch()` 实现 k=6/12/20/24/36 分配；`classify()` 实现规则 1–5；`endpoints()`/`verdict()` 实现 E1–E4/E4b+null gate 与 partial/fail；`--confirm-run` 门禁保留。**本轮仅 `compile()` 语法检查，未执行任何模式。** |
| 预算"≤5 min"未验证 | `mde_plan()["estimated_runtime_min"]` 改为 **"<=5 (UNVERIFIED PLANNING VALUE; not measured)"**；spec_v4 P1 / protocol_v4 §3.4 同步；冻结后首次运行须记录实测。 |
| 冻结清单不得写"可执行已落盘" | protocol_v4 §6：写 **"[x] 实现已落盘、未运行"**；v3 骨架 `constructive_sim.py` 标"历史，不再作可执行件"。 |

## 必改 2：z 的逐单元定义与冻结产物

- 新增 **`state_z.json`**（SHA256 `8a475bb6442cacce811423953e777675cb125b4915b3c187cd27134ffa603872`，metadata-only，4.4 MB）：
  - 分析单元 = **cell × directed pair**（108,259）；键 `(CELL_LINE_NAME, ANCHOR_NAME, LIBRARY_NAME)`。
  - 行级 z = **BARCODE 数字串 mod 2**（覆盖 296,707/296,707 = 100%；0/1 = 148,613/148,094）。
  - 单元级 z = **单元内多数**；并列取**最小数值 BARCODE 的奇偶**；无回退（0 单元）；108,259/108,259 有 z；平衡 54,251/54,008；tie 5,967。
  - **Q 单元（4 cell×condition 键）聚合规则**：4 键多数，并列取字典序最小 (cell,condition) 键（休眠；A2v4 不用 R193-A0 四元组）。
  - **共线/可识别性**（Cramér's V）：vs cell_groups_8 **0.0214**、vs Tissue **0.0138**、vs drug_type 同异 **0.0107** → 非共线；冻结要求 V≤0.30，否则替换 z。
  - 冻结规则：**生成器注入与判别器候选使用同一 `state_z.json`**，禁止重算。
- 候选状态清单明确 ≤6：Tissue / drug_type 同异 / cell_groups_8 / state_z 的 z / A4 状态；`dose_layout` 因设计列为管道分隔序列、非标量，v4 明示不作为候选（避免不可复现分箱）。

## 必改 3：E3 null abstention 规则 + E1 权重 + E4b 口径

- **选择 (a)**：**null unresolvable 率 ≤0.50（resolved≥0.50）作为设计体检 gate**（写入 verdict；失败→constructive_fail）。E3 保持 false-class≤0.10，null 上 abstention 计为无假类；删除 v3 "null resolved≤0.50 卫生上限"的反向写法。
- **E1 类权重写死**：class-balanced——I 权重 0.5、{II,III} 合并权重 0.5（池内各 0.25）；分母=全部非 null 世界、abstention 计错。
- **E4b 每类明确 = I/II/III（不含 null）**，各自 resolved≥0.85；null 由 null gate 独立管。
- 算术自洽保持：E4≤0.10⇒resolved≥0.90；E1 0.80⇒resolved acc≥0.889；E2⇒≥0.778。

## 必改 4：无序组定义 + k=6 z 读法 + partial/fail

- **无序敏感性组定义**：unordered {A,B} 规范方向 = 药名字典序较小者为 p1、较大者为 p2；组标签=（p1 pathway, p2 pathway）。按此重算：**320 组 / ≥2=209 / ≥4=119（覆盖 971 个无序对）**；**撤回** v3 的 305/215/117（`.first()` 非规范方向，不可复现）。有向主口径不变。
- **k=6 z 读法统一**：`z_total` 为**跨 6 单元总数**（z=0 共 3、z=1 共 3），非每层 3/3；k=6 不判 III。k=12/20：每层内 3/3、5/5（总 6/6、10/10）。`k_allocation` 按此实现。
- **partial/fail 归属写死**：E1 失败→constructive_fail；E1 过而 E2 失败→constructive_partial；E1/E2 过但 E3/E4/E4b/null gate 任一失败→constructive_fail（不归 partial）。实现于 `verdict()`。

## 必改 5：冻结清单/预算/披露文本

- 冻结清单（protocol_v4 §6）：simulator_v4 `[x] 实现已落盘、未运行`；`constructive_sim.py`（v3 骨架）标历史；**新增 `state_z.json` 条目**；无序敏感性以 v4 口径为准、冻结时重生成 `constraints_check_v4.json`。
- 预算一律标 **"未验证规划值（UNVERIFIED PLANNING VALUE）"**；首次运行记录实测耗时。
- 报告/冻结文本禁止写"可执行已落盘/已通过"；constructive 体检与 MDE 仍是**冻结后执行项**。
- 沿用 v3：不声称新颖性、C1′ QA only、replay 不报归因正确率/收益、C176/C177、A4/A5 接口、κ 仅兼容性。

## 结论与剩余缺口

- 5 条短补丁全部落实；A2v4 具备"可并入 A1 整体冻结"的**设计完备性**：模拟器完整实现（未运行）、z 逐单元产物与共线检查、E3/null 记账、无序组与 k 读法、partial/fail 与冻结清单文本。
- **仍未验证**：constructive 体检与 MDE 未运行（禁止本轮）→ E1–E4 可达性、MDE≤δ_min、≤5 min 实际耗时均未测；`SYNERGY_DELTA_EMAX` 列义未独立核；A1 schema/A4 状态未联调；general-ML 只元数据级。
- A2 仍**不单独冻结**；建议 Lead 在冻结 A1 时把 A2v4 作为模块并入，报告只能写"设计已冻结、实现已落盘未运行、体检待执行"。
