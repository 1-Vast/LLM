# record_pa2.md —— R192-PA2 执行记录（HGNC 别名解析 + 冻结 S1-A 重跑）

角色：注释映射与覆盖审计员（独立于提案者）· 任务：task-9（rev1 → claim 后 rev2）· 日期：2026-10-27
**只新增文件**：`PROTOCOL_PA2.md`、`pa2.py`、`pa2.json`、`mapping_table_v2.csv`、`report_pa2.md`、`record_pa2.md`、`usage_pa2.json`、`resources_hgnc/`。未修改 P-A v1 任何产物、其它目录、INDEX、SYNTHESIS、git。

## 0. 要求（Lead 指令）与完成对照

| # | 要求 | 状态 |
|---|---|---|
| 1 | 读 task-9 全文并 claim；完成 complete | ✅ rev1→2 claim |
| 2 | 用公开 HGNC 完整表（symbol/alias/previous symbol/name）解析 DrugComb `target_name` 蛋白全名/别名 | ✅ 首选 URL 成功；16,982,321 B；SHA256/SHA256 已记录 |
| 3 | **先冻结 PROTOCOL_PA2.md 再跑**；别名规则先写死 | ✅ 协议 14:34:03 冻结（pa2.py 14:37:48 才存在） |
| 4 | 一 token 多 symbol 的 ambiguous：不影响 argmax 才解析，否则不猜 | ✅ 枚举判定（≤3 实体且积 ≤16）；206/284 解析、78 不猜、4 药 capped |
| 5 | 重跑**完全相同的 S1-A 规则与门槛**；报告 v1→v2 覆盖率/可分析水平/both-unseen（PA 与 E1 两口径）/训练单元变化 | ✅ 全部数字见 report_pa2 §3–§7 |
| 6 | 报告新增 ambiguous / unmapped 计数 | ✅ ambiguous 5.18% 药；unmapped v1 2,658 → v2 2,276（Δ−382） |
| 7 | 判 `mapping_v2_qualified` / `not_qualified`（同一 G1–G4） | ✅ `mapping_v2_qualified` |
| 8 | 只新增文件、不改 v1 产物 | ✅ 运行前后 v1 四产物 SHA256 全等（审计 A5） |
| 9 | 不得读响应值 | ✅ 只按列位置读身份 3 列；产物 grep 0 命中 |
| 10 | 失败两次即记录 HGNC 缺口并停下 | 未触发（首选 URL 一次成功） |
| 11 | completed + send_message（v1/v2 数字、v2 表 SHA256、ambiguous 比例、HGNC URL/SHA256） | ✅ 完成时发送 |

## 1. 时间线（本机 Asia/Shanghai）

| 时间 | 事件 |
|---|---|
| 14:29 前后 | 读 task-9 → claim（rev2）；复核 P-A 产物与冻结哈希 |
| 14:30:21 | HGNC 首选 URL 下载成功（16,982,321 B）；核对列/行/status/version 日期 |
| 14:31–14:33 | 只读勘察 + `tmp/pa2_explore*.py` 原型（token/segment 可解析性、ambiguous 规模、通用短别名风险）——**已在协议 §2 披露** |
| **14:34:03** | **`PROTOCOL_PA2.md` 冻结**（`pa2.py` 尚不存在） |
| 14:34–14:37 | 写 `pa2.py`（复用 `pa.py` 冻结实现；`sys.dont_write_bytecode=True`） |
| 14:35–14:39 | 3 次实现 bug 修复后成功运行（每次均在 pa2.json 落盘前失败；映射表在一次失败运行中已写出、被后续成功运行覆盖） |
| 14:39:25/26 | 最终 `mapping_table_v2.csv` / `pa2.json`（连续两次运行哈希一致） |
| 14:40–14:45 | 写 `report_pa2.md`、`record_pa2.md`、`usage_pa2.json`；哈希核对 |

## 2. 实际命令与耗时

```powershell
# HGNC（14:30）
Invoke-WebRequest 'https://storage.googleapis.com/public-download-files/hgnc/tsv/tsv/hgnc_complete_set.txt' -OutFile resources_hgnc\hgnc_complete_set.txt
# 分析（离线、确定性）
cd D:\MAESTRO\research\2026-10-27-drugcomb-annotation
& 'D:\anaconda\envs\maestro\python.exe' pa2.py
```

`pa2.py` 墙钟 **23.9 s**（成功运行），远低于预算；不联网（下载除外）；总下载 16,982,321 B（≤50 MB）。

## 3. 实现 bug 与处置（均不涉及规则/门槛；均在 pa2.json 落盘前失败）

1. `pa.read_v14_identity()` 返回的 dict 不含 `e1_split` 键（v1 是在 `pa.main()` 内附加的）→ `KeyError`。修复：在 `pa2.py` 内用 `pa.split_pa` 重算并断言 E1 全体 both-unseen = 16,078。
2. `target_stats` 不含 v1 `pa.main()` 追加的 `tokens_distinct_D1_exact_symbols` / `drugs_D1_with_exact_symbol` → `KeyError`。修复：在 `pa2.py` 内本地计算（口径同 v1：MSigDB S1∪S2 符号集）。
3. `pa.load_jaaks()` 返回的 stats 不含 `overlap_D1`（v1 在 `pa.main()` 内附加）→ `KeyError`。修复：本地计算 `len(set(jaaks_map) & d1)`。
4. 说明：第 1–3 次运行均在 `mapping_table_v2.csv` 已写出之后、`pa2.json` 写出之前失败；最终成功运行的产物覆盖了中间版本。**规则、门槛、切分、ambiguous 处理与协议 v1 完全一致**，未因 bug 修改任何口径。

## 4. 观测与决定

1. **HGNC 索引规模**：45,277 行全 Approved；归一键 symbol 45,258（19 个归一冲突）、alias_symbol 42,151（1,508 多 symbol）、prev_symbol 15,701（100）、name 45,260（14）、alias_name 11,595（116）；版本日期 `max(date_modified)=2026-10-15`。
2. **v2 主结果（V2-A）**：映射药 1,800/4,088 = 44.03%（+382，+9.34 pp）；可分析水平 79（+17；E1 切分 72，+9）；both-unseen PA 3,056（+374）/ E1 4,654（+915）；训练单元 117,106（+31,670）；严格训练 83,684（+24,896）；水平总数 125（+2）。**判定 `mapping_v2_qualified`**。
3. **增益来源**：930 个 D1 药获得新符号（2,935 个新符号）；segment-name（蛋白全名）层 590 药/1,614 符号、独占 322 药；token-alias 层 533/1,058、独占 271 药；token-symbol 层 118/155、独占 37 药；多层 277 药。→ **"蛋白全名"层是本轮覆盖提升的主引擎**。
4. **ambiguous**：284 个实体（281 token-alias + 3 segment-name），206 解析、78 不猜；含 ambiguous 实体的药 211/4,076 = 5.18%；枚举截断 4 药。
5. **churn**：382 unmapped→mapped、247 标签改变、0 mapped→unmapped；最常见转移 `CALCIUM_SIGNALING→NEUROACTIVE`(13)。
6. **非单调性注意**：V2-B（仅蛋白全名层）的 both-unseen PA = 2,078 **低于** v1 的 2,682 —— 切分建在各自映射药集合上，映射集合变化会改变留出集组成，both-unseen 对映射集合非单调。已在 report_pa2 §7 显式说明；阶段 2 比较时只能按各自切分口径读。
7. **通用短别名精度风险**（协议 §8/§10 预注册诊断）：hnorm 长度 ≤3 的 alias/prev 解析 token 52 个（`II`/`of`/`H`/`H1`/`p38`/`tau`/`A1`/`B1` 等）；剔除 ≤2 长度（V2-D）→ 55 药标签改变；剔除 ≤3 → 111 药标签改变（约 6.2% 映射药）。**未从主规则剔除**（任务给定规则），但已给 V2-B/V2-D 变体数字供阶段 2 选精度模式。
8. **12 药**：v2 未改变 5-FU/Oxaliplatin/Temozolomide 的 unmapped 状态（药物名同义词/无靶点，不属靶点别名层）；Paclitaxel/Vinorelbine 仍为 tubulin 家族偏置标签；Taselisib 标签由 AML 变为 INOSITOL_PHOSPHATE_METABOLISM（新增 PIK3C3/SGCG），仍是弱证据。**规则 A 语义局限未被 v2 改变**。
9. **协议 vs 实现的一处口径说明**：V2-D 的 guard 是"hnorm 长度 ≤2"（协议 §8 原文），而"剔除 ≤3"的数字作为诊断变体在内存中计算、不进入 variants 列表（协议 §10 第 5 项要求报告的正是"剔除后标签变化"）。

## 5. 审计自查

- **响应值**：v1.4 仅 `csv.reader` 按列位置读 `drug_row/drug_col/cell_line_name`；12 个 DENY 列只记表头存在性；`mapping_table_v2.csv` grep `synergy|bliss|loewe|ic50|css|ri_row|ri_col|S_mean|S_sum` = **0 命中**。
- **v1 未改动**：运行前后 `mapping_table.csv`/`pa.json`/`pa.py`/`PROTOCOL_PA.md` SHA256 全等于协议 §1 冻结值（审计 A5）。
- **v1 可复现**：`pa2.py` 重算 1,418 / 34.6869% / 62 / 2,682 / 3,739 / 85,436 与 `pa.json` 逐项相等（A3）。
- **E1 口径**：466,033 / 4,088 / 4,076 / 112 / 62,826 / 380,418 / 16,078 全部复现（脚本内断言）。
- **确定性**：同一版本连续两次运行，`pa2.json` = `41edb023…`、`mapping_table_v2.csv` = `705a5e64…` 完全一致；无时间戳、无随机、JSON `sort_keys=True`；`sys.dont_write_bytecode=True` ⇒ 未在目录内产生 `__pycache__`。
- **输入哈希**：I1–I7 + HGNC 逐条复核（不符即 `SystemExit`）。

## 6. 缺口与未做的事

- **未解析药物名同义词**（5-FU 等）——本轮只解析**靶点**别名/蛋白名；这属阶段 2 之前可另立的范围。
- 未使用 Uniprot/RefSeq/Ensembl 名称映射（协议明确不做）；未用 Enrichr/Reactome。
- 未评估 v2 注释的**效应**（不读响应值，属阶段 2）。
- `V2-A` 含少量通用短别名噪声，未做人工逐条标注（不可审计）；用预注册的 V2-B/V2-D 与 churn 诊断替代。
- HGNC 为活文件：本记录冻结 2026-10-15 版本，后续更新需重新冻结。

## 7. 预算

| 项 | 用量 |
|---|---|
| 下载 | 16,982,321 B（≤50 MB） |
| 计算 | `pa2.py` 单次 23.9 s；总计算 <3 min |
| 写入磁盘 | 新增 ≈ 18.5 MB（HGNC 17.0 MB + 产物 1.2 MB + 报告） |
| token/费用 | 运行时不可得 → `usage_pa2.json` 记 `null` |

## 8. 产物哈希（最终，SHA256）

| 文件 | SHA256 |
|---|---|
| `PROTOCOL_PA2.md` | `447ca67e787f7648ee3c274372bc3fd81c8cedb1288049fad1c225395d8ed1a0` |
| `pa2.py` | `65e1113adfa50d4eda8915647e102f3ff4b1623d80ffe022e0faf35954e65f4d` |
| `pa2.json` | `41edb023e8fffc20607a5eff9048fb1bc9560108c50c818715a43a145b697c61` |
| `mapping_table_v2.csv` | `705a5e6476319b587c9b5e852590baef817cec7b8c4d69b0a54ec7cc686ed015` |
| `resources_hgnc/hgnc_complete_set.txt` | `12363916be36f8f6f91879b0faade4eeaac973722de7136ec61329b77f2c2f91` |
| `report_pa2.md` | 见 `usage_pa2.json` |
| `record_pa2.md` | 见 `usage_pa2.json` |

## 9. 最终判定

**`mapping_v2_qualified`**（同一 G1–G4 门槛 + A1–A5 审计全通过）；主变体 **V2-A**；v1→v2：覆盖 34.69%→**44.03%**、可分析水平 62→**79**、both-unseen（PA）2,682→**3,056**、（E1）3,739→**4,654**、训练单元 85,436→**117,106**；ambiguous 药占比 **5.18%**；冻结 v2 表 SHA256 `705a5e64…`。条件见 `report_pa2.md` §11。
