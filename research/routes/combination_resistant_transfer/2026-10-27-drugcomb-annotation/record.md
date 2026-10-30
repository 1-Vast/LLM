# record.md —— P-A（R191 阶段 1 注释映射与覆盖审计）执行记录

角色：注释映射与覆盖审计员（独立于提案者）· 任务：task-7（revision 1 → claim 后 revision 2）· 日期：2026-10-27
唯一写目录：`research/2026-10-27-drugcomb-annotation/`（+ `tmp/`）。未修改源数据、其它研究目录、`research/INDEX.md`、`SYNTHESIS.md`、`reference/`、`log/`、git。

## 0. 要求（Lead 指令）与完成对照

| # | 任务/Lead 要求 | 状态 |
|---|---|---|
| 1 | 读 task-7 全文并用最新 revision claim；完成 complete | ✅ claim rev1→2；完成时 complete |
| 2 | **先写 `PROTOCOL_PA.md` 冻结策略与门槛，再跑** | ✅ 协议 v1 14:06:31；v2 14:07:51（均在 `pa.py` 存在前） |
| 3 | 主规则 argmax `|T_j∩P|`（S1 KEGG / S2 Hallmark / S3 并集） | ✅ 全部实现并报告 |
| 4 | **Lead 补充**：预注册规则 A（argmax）+ 规则 B（超几何 z≥1.64）+ 确定性开关（A 出现"单水平>40%"或"可分析水平<12"→改用 B） | ✅ 写入协议 v2 §6；三库均未触发（S1 13.12%/62、S2 9.39%/42、S3 9.73%/74）→ chosen=A；A/B 全部数字已报告 |
| 5 | **Lead 补充**：token 切分 `| ; , /` 与空白、括号说明、不做别名推断、未匹配如实计 unmapped | ✅ 协议 v2 §5（T1）；T0 变体作敏感性；93 个新增映射药全部来自内嵌基因符号抽取 |
| 6 | 只读 v1.4 身份列，不读响应列 | ✅ `csv.reader` 按列位置取 3 列；DENY 12 列仅表头存在性；产物 grep 0 命中 |
| 7 | ≥12 可分析水平 / both-unseen ≥800 / 训练 ≥5,000 / 覆盖 ≥25% | ✅ 62 / 2,682 / 85,436 / 34.69% |
| 8 | 敏感性 r=0.30/0.40、每水平留出覆盖、S2/S3、并列比例 | ✅ 全部在 `pa.json` + `report.md` §7 |
| 9 | 12 个机制类药处理、Jaaks 对照 | ✅ `report.md` §8/§9 |
| 10 | 交付：PROTOCOL_PA.md / pa.py / pa.json / mapping_table.csv（SHA256）/ report.md / record.md / usage.json | ✅ 全部落盘（+ `resources/` 两个 GMT、`mapping_table_rules_AB.csv` 辅助表） |
| 11 | 判定 `mapping_qualified` / `mapping_not_qualified`（列失败门槛与解冻条件） | ✅ `mapping_qualified`；无失败门槛/无解冻条件；冲突与条件见 report §9/§11 |
| 12 | 完成后 send_message 给 lead（判定/覆盖率/水平数/单元数/S1-S3/SHA256/失败门槛） | ✅ 完成时发送 |
| 13 | 不得用响应值；不得改其它目录/INDEX/SYNTHESIS/git | ✅ 遵守（见 §5 审计） |

## 1. 时间线（本机时间，Asia/Shanghai）

| 时间 | 事件 |
|---|---|
| 14:00 起 | 读 task-7（rev1）→ claim（rev2）；读 BRIEF、R190-E1 的 `PROTOCOL_E1.md`/`report.md`/`e1.json`/`e1.py` 口径 |
| 14:01 | 下载 MSigDB GMT（2 文件，148,696 B）；核对 Python/包版本；计算 7 个输入 SHA256 |
| 14:02–14:06 | 只读勘察：I1 表头/身份列、I2/I3 列与行数、GMT 结构；`tmp/` 原型复算（**协议 §2 已披露**） |
| **14:06:31** | **`PROTOCOL_PA.md` v1 写定**（`pa.py` 尚不存在） |
| **14:07:24** | **收到 Lead 补充指令**（规则 A/B + 超几何 z + 确定性开关；token 切分细化） |
| **14:07:51** | **协议 v2 写定**（运行前；门槛数值未改）→ 之后不再修改 |
| 14:08–14:10 | 实现 `pa.py`（独立实现，不复用原型脚本）；首次运行在 `[4/9]` 因实现 bug 中止（**无产物写出**） |
| 14:10:34 前后 | 修复后**首次成功运行**（20.98 s）；产出 `pa.json`/两张映射表 |
| 14:11–14:14 | 非响应 grep 审计；token 切分差异诊断（tmp/，只读）；确定性复查（连续两次运行哈希一致） |
| 14:14:30 | 为 `brief_pa_diagnostic` 增加"逐库"数字（判定无关诊断）→ `pa.py` 最终版 |
| 14:15:26 | 连续两次运行，产物哈希一致；采集全部数字 |
| 14:22–14:28 | 写 `report.md`、`record.md`、`usage.json` |

## 2. 实际命令与耗时

```powershell
# 资源下载（14:01）
Invoke-WebRequest 'https://data.broadinstitute.org/gsea-msigdb/msigdb/release/2023.1.Hs/c2.cp.kegg.v2023.1.Hs.symbols.gmt'
Invoke-WebRequest 'https://data.broadinstitute.org/gsea-msigdb/msigdb/release/2023.1.Hs/h.all.v2023.1.Hs.symbols.gmt'
# 分析（离线、确定性）
cd D:\MAESTRO\research\2026-10-27-drugcomb-annotation
& 'D:\anaconda\envs\maestro\python.exe' pa.py
```

- `pa.py` 墙钟：首次成功 20.98 s；复跑 20–44 s（冷/热缓存）；CPU 单机；**不联网**。预算 ≤30 min。
- 下载：148,696 B（预算 ≤50 MB，任务给的上限）＋零额外数据下载。

## 3. 实现 bug 与处置（均不涉及规则/门槛）

1. 规则 B 的 `sd` 是**逐基因集数组**（依赖 `K_P`），首版写成标量判断 `if sd == 0.0:` → `ValueError`。修复：`sd` 为数组，`pos = mask & (sd > 0)`，逐元素计算；`sd==0` 的通路 z=0。
2. 修复时误删 `zmax = float(np.nanmax(z))` 一行 → 立即补回。
3. 两处 bug 均发生在首次成功运行之前，**未写出任何产物**；修复后规则、门槛、切分、并列仲裁与协议 v2 完全一致。
4. `pa.py` 之后三次修改（**均判定无关**，每次修改后重跑两次确认确定性）：(a) 在 `brief_pa_diagnostic` 中增加逐库"两药均映射"药对/单元比例；(b) 在 `token_sensitivity` 中增加 T0↔T1 丢失数（实测三库均为 **0**）与 T1 新增基因符号 token 数（1,459）；(c) 增加 `mapping_source_attribution`（映射药的命中基因来源归属：仅 I2 / 仅 I3 / 两者）与 I2/I3 精确符号 token 数，并据此修正 report 中"来源归属"的表述（此前基于 T0 原型的"仅 2 个"在 T1 口径下应为 95）。

## 4. 观测与决定

1. **来源归属**：I2 `target_name` 是**蛋白全名**而非基因符号（如 `Thymidylate synthase`），T1 切分只能抽到蛋白名内嵌的大写符号词。实测（`pa.json` → `mapping_source_attribution`）：S1-A 的 1,418 个映射药中 **1,175（82.9%）的命中基因只来自 DRH**、148 个两来源都有、**95（6.7%）只来自 I2**（I2 贡献 100 个精确符号 token，DRH 贡献 974 个）。注意：T0 口径下 I2 独有贡献仅 2 个药，T1 下升到 95——两者都是同一条冻结规则的直接结果；I2 抽出的符号可能混有词内伪符号（已见例：Taselisib 的 `C2` 来自 "…C2 domain-containing…"）。属协议 §5 已声明的事实，**未改规则**。
2. **token 切分（Lead 要求 T1）**：相对 T0（仅切 `| ; ,`）新增 93 个映射药（S1；S2 +85、S3 +100），全部来自"复合/连写靶点名中的内嵌基因符号"（`FLT3/JAK3/RET/BTK/SRC/...`，与激酶抑制剂注释一致）；**三库 × 两规则的 T0→T1 丢失数均为 0**（`pa.json` → `token_sensitivity.*.drugs_mapped_T0_not_T1_*`）。T1 为协议冻结主规则，T0 作敏感性。
3. **Lead 预探对账**：预探 KEGG 1,341（32.8%）/ Hallmark 1,224（29.9%）落在本次 T0（1,325/1,204）与 T1（1,418/1,289）之间 → 可由 token 切分严格度差异解释；预探脚本未留存，无法逐条对账；±0.4–2.1 pp，不影响门槛。
4. **开关决定**：规则 A 在三库均未退化（最大水平占比 9.39–13.12% ≪40%；可分析水平 42–74 ≥12）→ `chosen = A`，主策略 = **S1 + A**（预注册层级第一项）。规则 B 数字全部报告（其 z 阈值实际不筛药，最小 z=4.24；`z≥1.64` vs `p<0.05` 在 55 药上不一致 → 已在 report §6/§11 标注"B 只应作水平多样性敏感性"）。
5. **单元口径**：按 task-7 用 **PA 切分**（N=已映射药）为主口径 → both-unseen 有注释单元 2,682；同时报告 **E1 切分**（N=4,088，与 R190 的 16,078 兼容）→ 3,739（占 16,078 的 23.3%）。**这是阶段 2 必须二选一写死的条件**（report §11 条件 1）。
6. **task-7 文本与 E1 规则的细微不一致**：task-7 写 `names[0::5][:k]`，E1 规则是 `step=N//k`；主策略 N=1,418 → k=284、step=4（非 5）。按"与 E1 同一确定性规则"取 `step=N//k` 为主口径，字面 step=5 变体作敏感性（2,682 vs 4,203，均 ≥800）。
7. **BRIEF 旧门槛冲突**：BRIEF §P-A 建议"两药均映射药对 ≥50%"，实测 S1 29.06% / S2 27.23% / S3 36.94%，任何策略都不满足。task-7 已以 G1–G4 取代；本报告按 task-7 判定并在 report §9 显式披露，交 Lead 裁决。
8. **Jaaks 模板**：21 水平、仅覆盖 D1 40 药（0.98%）→ 单独不可行；作为先验理由记录，不作主策略（预注册）。

## 5. 审计自查

- **响应值**：v1.4 仅 `csv.reader` 按列位置读 `drug_row/drug_col/cell_line_name`；12 个 DENY 列只记录表头存在性；产物 grep `synergy|bliss|loewe|ic50|css|ri_row|ri_col|S_mean|S_sum|S_max` = **0 命中**；`pa.json` 中响应列名仅作文档性字符串（3 处列表），`dict_key_hits=0`。
- **确定性**：`pa.py` 无随机/无时间戳/JSON `sort_keys=True`；同一版本连续 2–3 次运行，`pa.json`、`mapping_table.csv`、`mapping_table_rules_AB.csv` SHA256 完全一致。
- **E1 交叉校验**：466,033 / 4,088 / 4,076 / 112 / 62,826 / 380,418 / 16,078 全部相等（不符则脚本 `SystemExit`）。
- **输入哈希**：I1–I7 的字节数与 SHA256 与协议 §1 冻结值 7/7 相等（不符则 `SystemExit`）。
- **写范围**：只写 `research/2026-10-27-drugcomb-annotation/` 与 `tmp/`；未触碰 INDEX/SYNTHESIS/git/其它目录（只读 E1 目录）。

## 6. 缺口与未做的事

- **未读响应值**（按协议）：端点可用性/饱和性属 P-B，不在本轮。
- 未测试 Enrichr/Reactome/GO 等替代基因集库（task-7 只要求 KEGG/Hallmark；资源预算已用 148,696 B）。
- 未使用同义词/别名表（协议禁止别名推断）：5-FU 等失配是**设计选择**，不是检索缺口。
- 未对规则 A 的标签做"生物学正确性"人工标注（不可审计、易引入主观）；改用可审计诊断（并列率、score=1 占比、家族偏置示例）替代。
- 未计算 MDE / 效应量（阶段 2，且本轮不读响应）。
- 预探脚本（Lead 侧）未留存 → 1,341/1,224 只能解释性对账，无法逐条复现。

## 7. 预算

| 项 | 用量 |
|---|---|
| 下载 | 148,696 B（≤50 MB 预算） |
| 计算 | `pa.py` 单次 21–44 s；总计算 <5 min（≤30 min 预算） |
| 写入磁盘 | 方案目录 ~3.0 MB（产物 2.7 MB + GMT 148 KB） |
| token/费用 | 运行时不可得 → `usage.json` 记 `null`（不记 0） |

## 8. 产物哈希（最终）

| 文件 | SHA256 |
|---|---|
| `PROTOCOL_PA.md` | `16c40f9f61765637185bd061b1aeb4e62886bdfa027b8baf509830775bae607d` |
| `pa.py` | `25e64208a95b0c92b126823020e361ad208e517eef95c4f093f6be835ff470f3` |
| `pa.json` | `f5559d26a86679bd7be77ffd00fc5c4195be50eb611e8677a87434fb842c9fa3` |
| `mapping_table.csv` | `45ede63521dc44fefec52d717765b4d2ba7d08ec3fde4372811c4d516de038d4` |
| `mapping_table_rules_AB.csv` | `96f1f51be78f970c28bb6409d240db99e4a568dea7a9b1a2144414c5329db87c` |
| `resources/c2.cp.kegg.v2023.1.Hs.symbols.gmt` | `48de51190366ee388dffe34fa2931e590de43ee5e2a4c27c50c0fc33b9d194fc` |
| `resources/h.all.v2023.1.Hs.symbols.gmt` | `27e48f776cda235ad5b63acaecc3136853ee79c6447d883ce2b070a4d2d47b75` |

## 9. 最终判定

**`mapping_qualified`**；主策略 **S1 (KEGG) + 规则 A**；覆盖 1,418/4,088 = **34.69%**；可分析水平 **62**；both-unseen 有注释单元 **2,682**（E1 切分 3,739）；训练单元 **85,436**；无失败门槛、无解冻条件；6 条随判定条件见 `report.md` §11。
