# R190-A0 资格审计记录（record）

角色：数据/设计资格审计员（独立于提案者；不参与效果实验设计，不拟合预测模型）。
工作目录 `D:\MAESTRO`；只写 `research/2026-10-27-cellstate-qualification/` 与 `tmp/`；未改 `PROTOCOL_A0.md`、`research/INDEX.md`、`research/SYNTHESIS.md`、git、其它研究目录。

## 1. 范围与约束

- 任务：执行冻结协议 [PROTOCOL_A0.md](PROTOCOL_A0.md)（含 `AMENDMENT-A0-001`）的 R190-A0 资格审计 —— 判定"用药物靶点基因的细胞表达，能否在留出细胞上把同一药对内细胞按 `ΔEMAX` 排出可检出次序"在本机是否**可检验**。**不评估效果、不报告特征收益。**
- 允许读取（只读，全部本地）：Jaaks Original/Validation fitted 表、raw zip、Glossary、DepMap 19Q4 sample_info / CCLE_expression / CCLE_mutations。
- 响应值 `SYNERGY_DELTA_EMAX` 只允许用于协议 §4 预写死的资格统计（方差成分/上限/room/可靠性/MDE/辅助跨筛可靠性），且代码显式标注 `purpose=qualification`。
- 门槛全部按协议冻结值实现，**未改任何门槛**；任何门槛不可计算 → 记 null 并说明（本次 σ_e(raw)=null）。
- 硬约束：不拟合预测模型；不按响应选特征/细胞/药对；不联网；单条命令 ≤15 分钟。

## 2. 时间线（本机时间，Asia/Shanghai）

| 时间 | 事件 |
|---|---|
| 13:11:33 | 首次读 `PROTOCOL_A0.md`（当时 81 行 / 10,332 B，**尚无修订段**）；仅做只读准备，未生成任何交付物 |
| 13:12:33 | `PROTOCOL_A0.md` mtime 变为 12,154 B —— Lead 追加 `AMENDMENT-A0-001` |
| 13:12–13:13 | 收到 Lead 消息；重读协议（89 行，含修订）。**此后才开始任何数据计算与门槛实现** |
| 13:15:21 | `tmp/_a0_recon1.py`：拟表结构/键/重复行/靶点清单探针（只读） |
| 13:16:07 / 13:16:44 | `tmp/_a0_recon2.py` / `_a0_recon3.py`：身份映射、表达矩阵形状/基因列、靶点映射与药对覆盖（只读，未用响应值做筛选） |
| 13:18:52 | `tmp/_a0_recon4.py`：G3 统计与 MDE 候选口径探针（`purpose=qualification`） |
| 13:20–13:38 | 实现并修订 `a0.py`（1,242 行；仅改实现/修正 bug，未改门槛） |
| 13:39–13:40 | 第 1/2 次正式运行（~75 s / ~73 s）；快照到 `tmp/_a0_runA_*` |
| 13:41:39 | 第 3 次正式运行完成；三份确定性产物与上一次逐字节一致 |
| 13:42 | 清理 `__pycache__`、写 `report.md` / `record.md`、核对产物 SHA256 |

> 修订在本审计的任何脚本产物与门槛判定之前读到；修订只放宽/重述 G1（≥119 映射且其中 ≥105 有表达行）并把 G3(e)/G4 折改到 111 表达细胞，**其余门槛未动**。修订前状态仅"读过 81 行协议文本"，无任何交付文件或判定。协议自身记录了修订时刻为 13:2x。

## 3. 实际命令与耗时

| 命令（均在 `D:\MAESTRO`） | 实测耗时 |
|---|---|
| `D:\anaconda\envs\maestro\python.exe -X utf8 research\2026-10-27-cellstate-qualification\a0.py` | **72.7 s / 75.2 s / 73.4 s**（3 次） |
| `python -m py_compile research\...\a0.py` | <1 s |
| `tmp\_a0_recon1.py` / `_recon2.py` / `_recon3.py` / `_recon4.py` | ~2 s / ~13 s / ~10 s / ~332 s（recon4 为探索性 MDE 循环，仅用于选口径；正式实现已向量化） |
| 校验：`Get-FileHash`、`json.load` 抽查 | <5 s |

资源：CPU-only（无 GPU/无网络）；输入总字节 862,359,332（7 个文件，SHA256 见 `a0.json → P1_inputs`）；单次运行 wall ≈73 s；未做大规模调参或模型训练。

## 4. 观测（结构事实与与先验不一致处）

1. **拟合表行数 296,707 ≠ 键数**：同一 (cell, 有序药对) 有多行（不同锚药浓度 / 重复板），平均 2.741 行/有序键。协议 §4 定义 `y = mean(SYNERGY_DELTA_EMAX over rows of key)`，按此实现。
2. **键口径**：任务背景的 "2,025 药对 / 108,259 键" 是**有序** `(ANCHOR_NAME, LIBRARY_NAME)` 口径（与实测一致）；协议 §4 冻结的是**无序药对**，因此 G3 使用 **1,294 药对 / 70,360 键**（37,899 个 cell-pair 的两种朝向被合并）。两套数字都已报告；G2 的 90% 药对覆盖按协议明写的 2,025 有序药对计算。同名药对 0。
3. **表达矩阵只有 1,249 行**（`sample_info` 1,756 行），Jaaks 125 细胞中 **111** 有表达行、14 缺失（Breast 5 / Colon 6 / Pancreas 3）——与 `AMENDMENT-A0-001` 一致，已逐一列出。
4. **身份连接**：COSMIC 主口径 122/125，剩余 3 个（COLO-824、CaR-1、MFM-223）归一名唯一匹配补齐 → 125/125 唯一 DepMap_ID；无一对多/冲突。
5. **靶点映射**：86 token = 50 精确 + 22 冻结别名 + 14 未映射（机制类）。**但药物级覆盖仅 1161/2025 = 57.3%（两侧各 ≥1 映射基因）**——12 个药（5-FU、Bortezomib、Cisplatin、Docetaxel、Gemcitabine、Oxaliplatin、Paclitaxel、Pictilisib、Taselisib、Temozolomide、Vinorelbine、Vorinostat）没有任何基因级靶点，导致 G2 门槛（≥90%）字面失败。若按"两侧合计 ≥1"读法为 95.0%（通过）——已作为敏感性并报，未改口径。
6. **raw zip 可解析但不含组合端点**：8,164,070 数据行、20 列单药强孔字段（`DRUG_ID/DRUG_NAME/CONC/INTENSITY`），无 `SYNERGY_*`/ΔEMAX 列 → **σ_e(raw) 记 null**，按协议兜底借用 R4 的 σ_e=0.0408，并用 fitted 表重复板结构作敏感性（行级 0.05267、键级 0.02565；ρ_ceiling 0.70–0.90 均过 0.10）。
7. **G3(a) 实测**：cell 0.0500 / pair 0.3257 / interaction 0.6295（和 1.0051）。与 SYNTHESIS 转述的 R26"主效应 0.696、交互 0.275"量级不同——按本资源/协议口径如实报告，不改门槛。
8. **G3(e) MDE 依赖零预测建模**：所有"细胞聚类"零模型（双向聚类 bootstrap 折均值 0.240、固定细胞置换 0.174、5 折端点 0.112/0.080）均 >0.05；只有"逐药对独立"的解析口径 0.0295 ≤0.05。原因：1,294 个药对嵌套在每折 ~22 个留出细胞上，细胞状态型预测排序跨药对共享。
9. Glossary（46 条定义）与拟合表 46 列完全一致（P2 不判死，无缺失/多余）。
10. 分折组织覆盖：fold-2 仅 1 个 Pancreas 细胞（设计限制，记入报告 §5.6）。

## 5. 决定（实现口径与理由）

1. **键/药对口径**：G3 严格按协议 §4 的无序药对（1,294 / 70,360）；G2 严格按协议 §3 明写的 2,025 有序药对。所有地方同时报告两套计数以量化口径差异。
2. **G2 判定**：按冻结文本字面"两侧靶点**均** ≥1 个映射基因"= 每侧各自 ≥1 → 57.3% < 90% → fail（`data_unavailable`）。95.0% 的"合计"读法只作敏感性列示，**不用于判定**（避免事后改口径/改门槛）。
3. **σ_e**：raw 可解析但不含所需量 → `sigma_e_raw=null` 并说明；主口径按协议兜底借用 R4 的 0.0408（`borrowed`），fitted 重复板估计作敏感性。
4. **MDE 主口径**：按协议"bootstrap 按药对与细胞双向聚类"实现为——按细胞（簇）与药对（簇）重采样，零预测为"细胞状态只给出的跨药对共享细胞打分"（细胞级特征前提下的保守/字面读法）；`MDE80=(z0.975+z0.80)·SE`，1,000 次，seed 20261027。同时报"固定细胞置换""5 折端点""逐药对独立解析/iid"四种敏感性，**门槛判定只用协议字面主口径**，并明确该口径分歧需在效果协议冻结时消解。
5. **5 折集合**：按修订在 111 个有表达细胞上做，NFKC→casefold→去非字母数字归一名排序后 `i % 5`（23/22/22/22/22）；125 细胞参考折（每折 25）也一并报告（仅参考）。
6. **不拟合模型**：MDE 只用零预测的解析 SE 与 bootstrap 模拟；没有预测值、没有效果量、没有特征筛选。
7. **判定输出**：`unqualified`；失败门槛 G2（`data_unavailable`）+ G3(e)（`evaluation_cannot_distinguish`）；两处字面歧义的宽读法数字全部并报，交由 Lead 裁定，未在结果后改门槛。
8. **产物边界**：只写本目录与 `tmp/`；`a0.json` 无时间戳、键排序、输入/脚本 SHA256 入库；`usage.json` 记运行遥测、未知记 null。

## 6. 确定性与验证

- 固定种子 `20261027`；JSON `sort_keys=True`；输出无时间戳；`a0.py` 自身 SHA256 在运行时计算并写入 `a0.json`。
- **连续 3 次运行**：`a0.json`、`identity_map.csv`、`target_map.csv` **逐字节一致**
  - `a0.json` = `6497A9882F99AB07165A319961FE4BF70CD5CFFE486C350A12CC372BBA235AB8`
  - `identity_map.csv` = `7BBF0CD3A3E6CB561D175E03D94DA4C8E5DBD4A3B1AE56185FF36858D87044B4`
  - `target_map.csv` = `650AEA40EC51C442FF805A53347616C863245196B91EDD8952B55446F22F9F8A`
- 协议 SHA256 = `8A43325D5E70EC19EEB4E38205FA419101E48FA8C6FB7FE8F1C3C00EE4369BD9`；脚本 SHA256（入库值）= `8069D94630770A590AD631213084D29FE91E61E057DFD88D9652D8CAEF8A280D`。
- `usage.json` 单次 wall ≈73.4 s；因含运行时长，不纳入逐字节比较（已在此记录）。

## 7. 产物清单

| 文件 | 说明 |
|---|---|
| [a0.py](a0.py) | 确定性审计脚本（purpose=qualification；固定 seed 20261027；JSON 键排序；输入/脚本 SHA256 写入 JSON） |
| [a0.json](a0.json) | G1–G5 实测数字与 pass/fail、方差成分、room、σ_e 来源、ρ_ceiling、MDE80（含各敏感性口径）、5 折细胞清单与哈希、`verdict` |
| [identity_map.csv](identity_map.csv) | 125 行冻结映射（CELL_LINE_NAME, COSMIC_ID, DepMap_ID, join_method, note） |
| [target_map.csv](target_map.csv) | 86 个靶点 token 的映射方法/基因/用药计数/未映射原因 |
| [report.md](report.md) | 方法、实测结构、G1–G5 逐项判定与数字、失败类别、解冻条件、局限 |
| [record.md](record.md) | 本文件：范围/预算/命令/耗时/观测/决定 |
| [usage.json](usage.json) | 运行遥测；未知数值 null |

`tmp/` 内为本审计的只读探针与一次运行快照（`_a0_recon1..4.py`、`_a0_runA_*`），不属交付物。

## 8. 未做 / 明确不做

- 未拟合任何预测模型、未报告任何特征收益/效果量、未做特征选择或按响应挑选子集。
- 未联网；未下载数据；未修改任何输入、协议、其它研究目录、INDEX、SYNTHESIS、git。
- 未运行效果实验；未冻结效果协议（若判定为 `qualified` 才应由 Lead 另建 `PROTOCOL_D`）。
- 未触碰同目录下另一任务（`cellstate-lit`）的 `prior_art.md` / `sources_lit/`。
