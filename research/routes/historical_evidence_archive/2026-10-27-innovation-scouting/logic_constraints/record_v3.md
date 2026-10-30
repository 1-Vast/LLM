# R198-A2v3 记录（record_v3.md）

日期：2026-10-27 · 角色：定向核验员（lit-verifier）· task-43
状态：**v3 修订交付完成（DRAFT，待并入 A1 整体冻结）；本轮不运行效果/模拟器/训练/回放/拟合，不读响应做效果，不声称新颖性。**
写入范围：只新增 `research/2026-10-27-innovation-scouting/logic_constraints/` 下文件（spec_v3/protocol_draft_v3/REVISION_A2_v3/record_v3/usage_v3 + 设计版 folds.json/constraints_check.json + constructive_sim.py）；另用 `tmp/a2v3_build_design_artifacts.py` 生成设计版产物（只读元数据/注释/设计列）。**未改 v1/v2 文件**（SHA §4）、未改 A1 产物/其它目录/INDEX/SYNTHESIS/git。

## 1. 本轮做了什么

1. 读 v2 挑战 [challenge_A2_v2.md](challenge_A2_v2.md)（revise，≤5 必改；致命 3 条：III/E2 不可达、预算表算术冲突、MDE/δ_min 单位混用 + abstention 记账），并回读 v2 产物与 v1 挑战。
2. 落实必改 1–5（逐条见 [REVISION_A2_v3.md](REVISION_A2_v3.md)）：III 的 z 改为可观测未建模元数据状态（BARCODE 派生 2 水平）+ 残差结构统计量 + ≤6 候选 max-stat 识别；E1/E2/E4 abstention 记账写死（E4 收紧到 0.10 + 每类 resolved ≥0.85，算术自洽）；预算表改为 20 单元结构化批次同时满足 I/II/III（k=6/12/20/24/36 显式分配与复用）；MDE/δ_min 同单位（δ_min=0.30/0.20/0.05/0.10，MDE=可分辨正确率/率差）；药对单位有向/无序双口径写死并与 U/S 修正；`a2_to_a1/v3` schema 版本化、κ 仅兼容性。
3. **设计版产物生成（metadata-only，非模拟器、非效果）**：
   - 脚本：`tmp/a2v3_build_design_artifacts.py`（只读 `COMBI_ID/BARCODE/Tissue/CELL_LINE_NAME/ANCHOR_NAME/LIBRARY_NAME/*_TARGET/*_PATHWAY/*_DRUG_TYPE` 等身份/注释/设计列；**未读响应列**）。
   - `folds.json`：5 折×13 药（seed 20261027）；每折 both-unseen directed 对 45/66/72/82/108、unordered 33/49/48/49/58、cell×directed-pair 单元 1,898/3,693/3,588/4,613/6,232；S24（24 个不同 directed 对 ∧ 不同 unordered 对，响应盲）；U = both-unseen − S 涉及对（unordered 9/25/24/25/34；directed 21/42/48/58/84）；top-k（fold0=5，其余=10）；`cell_groups_8`（按 (Tissue, CELL_LINE_NAME) 排序 round-robin）。
   - `constraints_check.json`：C2′ 有向组 331（≥2=275/1,969 对；≥4=165/1,698 对/90,589 单元）；无序敏感性 305/215/117；target 组（ANCHOR 40=34+6；LIBRARY 58=51+7，无 ≥3）；每折 Ref 组覆盖与 test 组覆盖；零分布计划（未被运行）。
   - `constructive_sim.py`（DESIGN VERSION）：世界生成器/判别器/端点/预算骨架 + `--confirm-run` 门禁；**未运行**。
4. 写 spec_v3 / protocol_draft_v3 / REVISION_A2_v3 / 本记录 / usage_v3。

## 2. 5 条必改的落实位置（一句话）

1. **III/E2 可达性 + abstention**：spec_v3 §4.3（z=BARCODE 派生可观测未建模状态；残差结构统计量+候选 max-stat；未识别→unresolvable/partial）；§4.4 + protocol_v3 §3.3（E1/E2 分母=全部非 null 世界、abstention 计错；E4≤0.10 + 每类 resolved≥0.85；E3 null 记账与卫生上限；算术自洽 0.90×0.889=0.80）。
2. **预算-功效**：spec_v3 §4.5 + protocol_v3 §3.4（20 单元结构化批次=10 in/10 out × z 5/5，同时满足 I(≥6)/II(10 vs 10)/III(z 各≥6)；k=6/12/20/24/36 显式分配与复用；II 的 ≥5 语境=8 细胞组中 5 组；模拟器 96 世界/16,000 次轻量分类，估计 ≤5 min、硬上限 30 min）。
3. **MDE/δ_min 同单位**：spec_v3 §4.4 + protocol_v3 §3.3（δ_min = 目标−机会：0.30/0.20/0.05/0.10；MDE=可分辨正确率/率差；≥1,000 批；MDE>δ_min ⇒ design_uninformative）；`constructive_sim.py` 落盘未运行。
4. **药对单位 + U/S**：spec_v3 §2.4 + protocol_v3 §1（C2′ 有向主：2,025 有向对/331/275/165/90,589 单元；U/top-k 无序主：1,294 无序对/每折 33/49/48/49/58；S=24 不同 directed ∧ 不同 unordered；U=both-unseen−S 涉及对，逐折大小写死；删除 v2 错误断言）。
5. **接口/冻结清单**：spec_v3 §6 + protocol_v3 §5–§6（`a2_to_a1/v3` 版本化 schema；κ≥0.60 仅兼容性、A1/A2 同类判别不互作验证；folds.json/constraints_check.json/constructive_sim.py 已落盘并记 SHA；C1′ QA only；replay 不报归因正确率/收益；引 C176/C177）。

## 3. 设计版产物 SHA256（冻结清单用）

| 文件 | SHA256 |
|---|---|
| `folds.json` | `3546E34EBA1CAF41C206F3C5742905F908C27083CDCF354265E055EE193C9DD7` |
| `constraints_check.json` | `B35018F70C97BF2A67FC473B708654501A8BE6B6E454D40F8D58B28271E93039` |
| `constructive_sim.py`（未运行） | `2D9E0D61C753EAE6EE85352864E904F2A5758B7B624292ED84C5DCEC5C621AE6` |
| `spec_v3.md` | `E638955CA0CF8DE2A53B1CC50011A0FAEADA21A04B47CB1787577D60B3406D10` |
| `protocol_draft_v3.md` | `1EE0A4F5A96D1269DFE1C1B0E64D13EB512A055B3EDF396444052AB7BEF45011` |

## 4. v1/v2 文件未改（SHA256 快照）

| 文件 | SHA256 |
|---|---|
| `spec.md`（v1） | `139282B4E36677ED6019856C86AB68E46679CE92C90B6FBD550D63C1A521848B` |
| `protocol_draft.md`（v1） | `587E2675DD51E9E431CE0025691E14102A7ED7C8F3DF62E5FBC043CFEC1D227C` |
| `prior_art.md` | `8C484393B223B4CDB70109EFB5DFA3869D629BD0B3465DCD4DC39FE02ADFA66C` |
| `record.md`（v1） | `49136AD5F7220F40A7E20B83A8C32D794177804ABFB561DD9A36F44302F7379E` |
| `usage.json`（v1） | `ADD8C70276CAAF8F1CCB0BEC222D0AC85D25C7DFEC92C949B8C82993E7EBD13E` |
| `spec_v2.md` | `0467FA0F85423189…`（仅前 16 hex 记录；v2 保持） |
| `protocol_draft_v2.md` | `DEFDD8EB7BDF7E9E…`（同上） |
| `REVISION_A2.md` | `CA2B3CDF8B552715…`（同上） |
| `record_v2.md` / `usage_v2.json` | `FC3B866819038790…` / `33D05E3A682C413B…`（同上） |

## 5. 本轮未做 / 限制

- **未运行 constructive 模拟器/MDE 模拟**（本任务明确禁止）；E1–E4 是否可达、MDE 是否 ≤δ_min **尚未验证**——冻结后执行项，不是本轮结论。
- 未运行 replay；未读响应值做效果；未改 A1 产物。
- `SYNERGY_DELTA_EMAX` 列义按 R198 record 引用，未独立核列。
- A1 更新器/schema 未提供；`a2_to_a1/v3` 是 A2 侧契约，联调待 A1。
- A4 状态资源未知；III 的真实数据认证仍归 A4。
- general-ML 先例仍只到元数据级（不声称空白）。
- 设计版产物只含元数据计数/S 抽样设计/U 大小/组覆盖；**不是**任何世界生成或效果结果。

## 6. 下一轮入口

1. 独立挑战者复审 v3（重点：20 单元结构化批次的复用合法性、III 状态识别公平性、abstention 记账与 E1–E4 自洽、U/S 定义、schema 版本）。
2. 若通过：并入 A1 整体冻结；冻结后先跑 `constructive_sim.py` 的 constructive 体检 + MDE（≥1,000 批），`constructive_pass/partial/fail` 落盘；再按 A1 接口做 replay（只描述）。
3. 任何 constructive/MDE 失败按 `constructive_fail`/`design_uninformative` 记录，不换阈值/不删终点重试。
