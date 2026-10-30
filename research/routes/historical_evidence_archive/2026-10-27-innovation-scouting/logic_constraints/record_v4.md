# R198-A2v4 记录（record_v4.md）

日期：2026-10-27 · 角色：定向核验员（lit-verifier）· task-51
状态：**v4 补丁交付完成（DRAFT，待并入 A1 整体冻结）；本轮不运行效果/模拟器/训练/回放/拟合，不读响应做效果，不声称新颖性。**
范围：只新增 `research/2026-10-27-innovation-scouting/logic_constraints/` 下 v4 文件；**未改 v1–v3**（SHA §4）、未改 A1 产物/其它目录/INDEX/SYNTHESIS/git。

## 1. 本轮做了什么

1. 读 A2v3 复审 [challenge_A2_v3.md](challenge_A2_v3.md)（revise，5 短补丁；致命：模拟器是 STUB、z 缺逐单元产物、E3 null abstention 可被"null 全 abstain"刷过）。
2. **P1 模拟器实现**：新增 [constructive_sim_v4.py](constructive_sim_v4.py)，完整实现世界生成（make_world 真生成 y）、k 分配与 S 采样、K_A2 规则 1–5、E1–E4/E4b+null gate、partial/fail、MDE 计划与 `--confirm-run` 门禁；**只落盘未运行**，仅做 `compile()` 语法检查（未执行任何模式、无 __pycache__ 副作用）。
3. **P2 z 产物**：用 metadata-only 脚本 `tmp/a2v4_build_state_z.py` 生成 [state_z.json](state_z.json)（只读身份/注释/设计列，**未读响应**）：行级 BARCODE 数字奇偶（100% 覆盖）→ 单元级多数聚合（tie 取最小数值 barcode 奇偶）→ 108,259 单元全有 z（54,251/54,008，tie 5,967）；附 Q 单元聚合规则、共线检查（Cramér's V vs cell_groups_8 0.0214 / Tissue 0.0138 / drug_type 0.0107）、生成器与判别器同源规则。
4. **P3 E3 规则**：选择 (a) null unresolvable≤0.50 进设计体检 gate；E1 class-balanced（I=0.5，{II,III}=0.5）；E4b 明确 I/II/III 三类不含 null。
5. **P4 定义补齐**：无序敏感性组按"药名字典序规范方向"重算 320/209/119（撤回 v3 305/215/117）；k=6 z 读法统一为总数 3/3（非每层）；partial/fail 归属写死（E1 fail→fail；E1 过 E2 败→partial；E3/E4/E4b/null gate 任一败→fail）。
6. **P5 冻结清单文本**：模拟器标"实现已落盘、未运行"；新增 state_z 条目；预算标"未验证规划值"；报告禁止写"可执行已落盘/已通过"。
7. 写 spec_v4 / protocol_draft_v4 / REVISION_A2_v4 / 本记录 / usage_v4。

## 2. 5 条补丁落实位置

| 补丁 | 落点 |
|---|---|
| 1 模拟器实现 + 预算未验证 + 冻结清单 | `constructive_sim_v4.py`、spec_v4 P1、protocol_v4 §3.4/§6 |
| 2 state_z 单元级定义/共线/同源 | `state_z.json`、spec_v4 P2、protocol_v4 §3.1 |
| 3 E3 null abstention + E1 权重 + E4b | spec_v4 P3、protocol_v4 §3.3、sim `endpoints()/verdict()` |
| 4 无序组定义 + k=6 读法 + partial/fail | spec_v4 P4、protocol_v4 §1/§3.4 |
| 5 冻结清单文本/预算披露 | spec_v4 P5、protocol_v4 §6 |

## 3. v4 产物 SHA256

| 文件 | SHA256 |
|---|---|
| `state_z.json` | `8A475BB6442CACCE811423953E777675CB125B4915B3C187CD27134FFA603872` |
| `constructive_sim_v4.py` | `3F5D4C3747D32320CAE8498E06146A31B1E3DF96EF6750CBE6BB20984C202464` |
| `spec_v4.md` | `FC78E8EC1061BA6CCF1086B6A7DD0A77A52EDF2A76DE61517B8F9AED8A10F59F` |
| `protocol_draft_v4.md` | `6DD1EE08C4C8BB9F5E8497920625EA85CFACF7A46D924EF9DEE83996D36EC495` |
| `REVISION_A2_v4.md` | `0444DF5B0063D3D98E2BED2D4186BFAA39EF9F88F6A82DA7E3FD9811D3FD4F6A` |

模拟器状态：**实现已落盘、未运行**；`--confirm-run` 门禁存在；只做过 `compile()` 语法检查。`mde_plan` 的 ≤5 min 为**未验证规划值**。

## 4. v1–v3 文件未改（SHA 快照；与 record_v3/usage_v3 已记录值一致）

| 文件 | SHA256（前 12） |
|---|---|
| `spec.md` / `spec_v2.md` / `spec_v3.md` | `139282B4E366` / `0467FA0F8542` / `E638955CA0CF` |
| `protocol_draft.md` / `_v2` / `_v3` | `587E2675DD51` / `DEFDD8EB7BDF` / `1EE0A4F5A96D` |
| `prior_art.md` / `record.md` | `8C484393B223` / `49136AD5F722` |
| `record_v2.md` / `record_v3.md` | `FC3B86681903` / `E3BA46924121` |
| `usage.json` / `usage_v2` / `usage_v3` | `ADD8C70276CA` / `33D05E3A682C` / `8BE3A04E8F31` |
| `REVISION_A2.md` / `REVISION_A2_v3.md` | `CA2B3CDF8B55` / `326F8A88E45C` |
| `folds.json` / `constraints_check.json` / `constructive_sim.py` | `3546E34EBA1C` / `B35018F70C97` / `2D9E0D61C753` |

## 5. 本轮未做 / 限制

- **未运行 constructive 体检/MDE 模拟**（禁止）；E1–E4 可达性、MDE≤δ_min、"≤5 min" 均**未验证**（冻结后执行项）。
- 模拟器仅语法编译检查；未运行 `--plan`/`--confirm-run`；未生成任何合成世界。
- `SYNERGY_DELTA_EMAX` 列义按 R198 record 引用，未独立核列。
- A1 更新器/归因 schema 未提供；A4 状态资源未知（III 真实认证仍归 A4）。
- general-ML 先例仍只到元数据级（不声称空白）。
- A2 仍不单独冻结；v4 待复审并入 A1。

## 6. 下一轮入口

1. v4 复审（重点：模拟器实现完整性（不含 stub/NotImplemented）、state_z 与生成器/判別器同源、E3/null gate 与记账自洽、无序组规范定义、partial/fail 归属、冻结清单文本）。
2. 通过后并入 A1 整体冻结；冻结后首次运行 constructive+MDE（≥1,000 批），记录实测耗时（替换"未验证规划值"）；按失败类别落盘。
3. replay 仅在 constructive_pass/Lead 允许 partial 后、按 A1 接口做，且只描述、不报归因正确率/收益。
