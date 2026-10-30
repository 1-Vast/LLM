# R204-DATA4 记录（record_data4）

2026-10-28 ｜ 执行：cellstate-lit（task-172） ｜ 工作目录 `D:\MAESTRO`。
对象：公开多时间功能/群体快照数据检索 + D1–D7 资格核验；用户已授权"允许下载公开数据"。
**不运行效果/不拟合/不读响应做效应**；只写 `research/2026-10-28-multitime-data-scout/` 与 `tmp/`；**不改 M2/Stage2/DATA1–3 产物**。

## 0. 纪律与范围

- 只做**有界检索 + 公开文件下载（≤500MB/文件）+ 结构核验**；不做响应统计、不拟合、不比较候选效果、不拼 ΔEMAX。
- 不绕过登录/许可/DUA；遇到 gated 只记录；本轮没遇到需登录的候选下载。
- 技术重复≠独立培养；glossary/设计声明≠mapping；缺失只写"本任务未取得/未发现"。
- 不称新颖性/迁移/决策收益/机制/药理；不晋升代码；不改旧判定/门槛。

## 1. 读取/输入

| 输入 | 用途 |
|---|---|
| `2026-10-28-m2-stage2-prep/{PROBLEM,DESIGN}_M2_STAGE2_v0_2.md` | D1–D7 定义、Stage2 门/边界 |
| `DECISION_R204_M2_STAGE2_ACCEPT.md` | 当前 `data_unavailable`、不执行 Stage2 |
| `2026-10-28-az-data-acquisition/report_data1.md`、`2026-10-28-az-code-hunt/report_data2.md` | AZ/GDSC 公开可获取性、mapping/功能 numeric 缺失（C205/C210） |
| `2026-10-28-deep-coupling-redesign/{BRIEF_R204.md,report.md}` | R204/M2 背景与边界 |
| `ERRATA_R201_R202.md` | C197/C199/C201/C203 等边界 |
| 本地 `data/external/mixseq_scperturb/mcfarland_2020.h5ad` | Mix-seq 结构核验（obs/var metadata only；**未读 X 值**） |

## 2. 实际检索/下载

**检索**：
- web_search 4 组查询（sci-Plex 时间点、多时间功能+apoptosis、perturb-seq time course、organoid sequential）。
- NCBI GEO eutils esearch（5 组；XML 存 `receipts/eutils_gds_*.xml`）：single cell drug time course apoptosis；perturb-seq time course；single cell drug treatment time series；single cell RNA-seq apoptosis FACS drug；organoid drug single cell time course。
- NCBI GEO 页面/FTP：GSE139944、GSE214965。
- Zenodo API 2 组（JSON 存 `receipts/`）：organoid drug single cell time course；sequential drug treatment organoid single cell。
- HuggingFace API：Tahoe-100M、X-Atlas/Orion（API JSON + README/LICENSE）。

**下载（公开；29 个文件；合计 92,488,275 B）**：
- GSE214965：series matrix + sample metadata + raw counts（1.7 MB）。
- GSE139944：3 series matrix、filelist、GSM4150377/78/79 的小 metadata（sciPlex3 pData 84.7 MB）。
- Tahoe：README/LICENSE + sample/drug/cell_line metadata（<66 KB each）。
- X-Atlas：README/LICENSE。
- eutils XML 5、Zenodo JSON 2、HF API JSON 2。
- 命令：`Invoke-WebRequest`（HTTPS/FTP 公开）；每文件记录 URL/bytes/SHA256/许可/是否需登录（见 `scout_data4.json:downloads`）。
- **超限未下载**（只记录）：sci-Plex RAW.tar 9.9 GB；sciPlex3 RDS/UMI 530–2900 MB；Tahoe 337 GB；X-Atlas 126 GB；AZ Overall_ANOVA 1.96 GB。

## 3. 结构核验（只字段/行数/时间点/功能列）

- **GSE214965**：sample metadata 160 行 × 11 列；`timepoint` {6h,22h}；20 drugs；4 replicate labels；raw counts 22,760 genes × 160 samples；functional columns = []；`count_sum/genes_detected` 是 RNA QC，不是功能。
- **GSE139944**：pData（前 200k 行扫描）：`time_point` {24,72}（24h 170,942；72h 19,864；NA 9,194）；190 drugs/6 dose levels/53 culture_plate/rep1-2；functional columns = []；大 UMI/RDS 未下载。
- **Tahoe-100M**：sample metadata 1,344 行 × 8 列；无 time 列；无功能列；drug metadata 379 行；cell line 1,000 行；337 GB 未下载。
- **X-Atlas/Orion**：README/API：8M cells、337 parquet、126 GB；RNA-only；无 time/dose/function；CC-BY-NC-SA-4.0。
- **Mix-seq**：h5ad 182,875 × 32,738（SHA `94a72400…`）；obs 含 time/perturbation/dose/cell_quality/hash 等，**无 functional 列**；6/24h + Tram 5 时点；X 未读。
- **AZ/GDSC**：按 DATA1/DATA2 已核；mapping/功能 numeric `not_in_listing`；本次未重复下载。

## 4. 排错/注意

- pData 为空格分隔、混合 quoted/unquoted 字段；初期用 `re.findall` 只抓 quoted 字段导致列错位；改为 quote-aware tokenizer + 右侧对齐（数据行比 header 多 1 个尾字段）后得到 time_point {24,72}、190 drugs、53 culture_plate。**仅结构核验，不读响应**。
- raw counts header 为 160 sample 列；数据行 161 列（首列 gene）；按行计数得到 22,760 genes，避免把 header 列数误当基因数。
- 未遇到需要登录/许可绕过的下载；GEO/FTP/HF 均公开。

## 5. 验证与产物

```text
scout_data4.py 运行两次，scout_data4.json 逐字节一致：
  SHA256 8aa5ac2ba9306ba0383f1fe60044ea338df3cb8f7412a6839992fb4e244081ce (43,352 B)
PROTOCOL_DATA4.md SHA256 c206217a6ca8c1fe65d7fd7bde4e257e43f303fc8a4b0828170c325a46729912 (6,481 B)
scout_data4.py SHA256 a9723dd9106ad490097f2a9f6f1112ee9e6694163f6587a739120373d3f2f414 (34,287 B)
report_data4.md SHA256 601c2474734e3fe5bfddd45ee87dff5dbe76cd1b797c1e3e4545c8424e804e5b (10,171 B)
receipts/ 29 个文件，合计 92,488,275 B；逐文件 SHA 见 scout_data4.json:downloads
```

**总体判定**：`not_qualified`（无候选满足 D1–D7；D4/D6/D2/D5 硬缺口）；AZ/GDSC 功能分支 `data_unavailable`。
**有界检索未发现**"多时间功能 + 配对 RNA/计数 + π + 独立培养"数据集；**不是不存在**。
**未运行**：效果/预测/拟合/响应统计/湿实验/代码晋升。

## 6. 产物与 SHA256

| 文件 | 字节 | SHA256 |
|---|---:|---|
| `PROTOCOL_DATA4.md` | 6,481 | `c206217a6ca8c1fe65d7fd7bde4e257e43f303fc8a4b0828170c325a46729912` |
| `scout_data4.py` | 34,287 | `a9723dd9106ad490097f2a9f6f1112ee9e6694163f6587a739120373d3f2f414` |
| `scout_data4.json` | 43,352 | `8aa5ac2ba9306ba0383f1fe60044ea338df3cb8f7412a6839992fb4e244081ce` |
| `report_data4.md` | 10,171 | `601c2474734e3fe5bfddd45ee87dff5dbe76cd1b797c1e3e4545c8424e804e5b` |
| `record_data4.md`（本文件） | — | 见 usage |
| `usage_data4.json` | — | 见文件 |
| `receipts/` | 29 文件 | 逐文件见 JSON |

## 7. 限制/下一步

- 有界检索（GEO/Zenodo/HF + 少量 web）；未做全库引文追踪/全部 GEO/所有 Dryad/Figshare 页面；`not_found` 只在本任务范围。
- 大文件（>500MB/文件）未下载，只记录；因此部分候选（Tahoe/X-Atlas/sci-Plex 大矩阵）只做 metadata/README 结构核验，未做全数据字段审计。
- 没有候选达到 D1–D7；下一步按报告 §5：不运行 Stage2；AZ 保留 DATA1 request spec；若未来补数据再另立资格协议/清洗映射；不写"只能新湿实验"。
- 不称新颖性/迁移/决策收益/机制；不晋升代码；不改旧判定。
