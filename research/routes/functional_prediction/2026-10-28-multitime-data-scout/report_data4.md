# R204-DATA4 报告：公开多时间功能/群体快照数据检索与 D1–D7 资格核验

2026-10-28 ｜ 执行：cellstate-lit（task-172） ｜ 工作目录 `D:\MAESTRO`。
协议：[PROTOCOL_DATA4.md](PROTOCOL_DATA4.md)（先冻结）｜ 机器可读：[scout_data4.json](scout_data4.json)｜ 脚本：[scout_data4.py](scout_data4.py)｜ 回执：[receipts/](receipts/)
**纪律**：有界检索 + 公开小文件下载（≤500 MB/文件）+ 结构核验；**不运行效果/不拟合/不读响应做效应**；不绕过登录/许可；技术重复≠独立培养；不写"不存在/作者未做/只能新湿实验"；不称新颖性/迁移/决策收益/机制；不晋升代码。

## 0. 结论（先行）

**总体：`not_qualified`（M2 Stage2 D1–D7 未通过；data readiness 保持 open）。**
- 有界检索 + 下载核验了 **6 个候选**；**没有候选满足 D1–D7**。
- **共同硬缺口：D4（无记录 π/随机化分配）、D6（无正交功能读出）、D2/D5（独立培养/批次不可认证）**；多时间 RNA 候选（Mix-seq、sci-Plex 24/72h、DRUG-Seq 6/22h）也都没有功能读数。
- **AZ/GDSC 功能分支：`data_unavailable`**（公开 only viability raw/matrix + caspase/PARP 图；无 mapping、无功能 numeric、无配对 RNA）；保留 DATA1 request spec P0/P1。
- 有界检索**未发现**"多时间功能 + 配对 RNA/计数 + 记录 π/动作 + 独立培养"的公开数据集；**这是本任务范围内的未发现，不是不存在**。
- 不运行 Stage2；不得合成/RNA/预测替代独立功能决策；不写"只能新湿实验"。

## 1. 候选表与总体判定

| # | 候选 | 来源/许可 | 可获取性 | D1 | D2 | D3 | D4 | D5 | D6 | D7 | 总体 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | **Mix-seq**（McFarland 2020，本地 scPerturb 资产） | 本地 h5ad；原论文；本地无再分发许可声明 | 本地 1.46 GB（>500MB 但既有，不下载） | pass | unclear | partial | **fail** | **fail** | **fail** | pass | **not_qualified** |
| 2 | **sci-Plex**（GSE139944） | NCBI GEO 公开；无显式许可 | 小 metadata/pData 下载；大 RDS/UMI >500MB 未下 | pass (24/72h) | partial | partial | **fail** | partial | **fail** | pass | **not_qualified** |
| 3 | **DRUG-Seq LN-229**（GSE214965） | NCBI GEO 公开；无显式许可 | metadata + raw counts 下载（1.7 MB） | pass (6/22h) | unclear | partial | **fail** | partial | **fail** | pass | **not_qualified** |
| 4 | **Tahoe-100M**（2025） | CC0-1.0 | metadata 下载；337 GB parquet 未下 | fail (no time) | unclear | partial | **fail** | unclear | **fail** | pass | **not_qualified** |
| 5 | **X-Atlas/Orion**（2025） | CC-BY-NC-SA-4.0 | README/metadata 下载；126 GB parquet 未下 | fail (single time) | partial | fail | **fail** | partial | **fail** | pass | **not_qualified** |
| 6 | **AZ/GDSC 2024**（DATA1/DATA2 已核） | Figshare/GDSC 公开；无显式许可 | raw well 241 MB 公开；mapping/功能 numeric 缺 | partial | unclear | partial | **fail** | partial | partial | **fail** | **data_unavailable** |

- **D4 全员 fail**：没有候选记录 randomization/π/assignment probability；treatment 标签不等于 π。
- **D6 仅 AZ 部分**：viability + caspase/PARP 在论文中报告，但 numeric 不在公开 listing；其余为 RNA-only。
- **D5 仅 partial**：sci-Plex/DRUG-Seq/AZ 有 plate/well/技术重复或 occasion 标签；但独立培养/板未认证。
- **D7**：RNA 候选有 counts/RNA；AZ 无配对 RNA/counts with function。

## 2. 下载/可获取性与许可

**已下载（公开；≤500MB/文件；`receipts/`；共 29 个文件）**
- **GSE214965**（DRUG-Seq）：series matrix 2,089 B；sample metadata 3,936 B；raw counts 1,737,338 B（SHA `82446902…D0E5DB6`）；结构：20 drugs × 6h/22h × 4 replicate labels；raw counts 22,760 genes × 160 samples；无功能列。
- **GSE139944**（sci-Plex）：3 个 series matrix（2.8–3.2 KB）、filelist、GSM4150377/78/79 pData/hash/cell annotations（小文件；sciPlex3 pData 84,673,357 B，SHA `860BA5C2…5024C2`）；结构：pData `time_point` ∈ {24, 72}（24h 170,942 行；72h 19,864 行；NA 9,194 行；前 200k 行扫描），190 drugs/6 dose levels/53 culture_plate 值；**无功能列**。
- **Tahoe-100M**：README + LICENSE + sample/drug/cell_line metadata（每个 <66 KB）；sample metadata 1,344 samples × 8 列，**无 time 列**、无功能列；337 GB parquet 未下。
- **X-Atlas/Orion**：README/LICENSE（6.2/20.8 KB）；126 GB/337 parquet 未下；RNA-only；无 time/function。
- **GEO eutils 5 个查询 XML、Zenodo 2 个查询 JSON、HF API 2 个 JSON**：检索回执。

**超限未下载（只记录）**
- sci-Plex `GSE139944_RAW.tar` 9.9 GB；sciPlex3 大 RDS/UMI 530–2,900 MB。
- Tahoe-100M 337 GB（3,388 shards）；X-Atlas 126 GB（337 files）；AZ Overall_ANOVA 1.96 GB。
- 均因 >500 MB/文件；**未绕过任何登录/许可**；无 HTTPS 访问失败阻塞（GEO FTP 公开）。

**许可/登录**：
- GEO 候选：NCBI public data；**无显式 license**；无登录；按 NCBI data usage policies 使用。
- Tahoe：CC0-1.0；公开；无 gated。X-Atlas：CC-BY-NC-SA-4.0；公开；无 gated。
- Mix-seq：本地 scPerturb 资产；原论文；本地无再分发许可声明（只作本地结构核验，不再分发）。
- AZ/GDSC：DATA1/DATA2 记录公开 Figshare/GDSC；无登录/terms 阻塞；mapping/功能 numeric `not_in_listing`。

## 3. 逐项 D1–D7 证据摘要

1. **Mix-seq**：D1 pass（6/24h + Tram 3/6/12/24/48h 群体快照）；D2 unclear（同 key 但无 culture/batch；6/24h 是不同臂）；D3 partial（dose/time 有，功能无）；D4 fail；D5 fail（无独立培养/重复记录）；D6 fail（RNA only）；D7 pass。→ not_qualified。
2. **sci-Plex**：D1 pass（sciPlex3 pData 24h/72h 两个时间点；多剂量）；D2 partial（culture_plate/well 标签，但独立培养未认证）；D3 partial（dose/time 有，功能无）；D4 fail；D5 partial（rep/plate 标签≠独立培养）；D6 fail；D7 pass。→ not_qualified。
3. **DRUG-Seq GSE214965**：D1 pass（6/22h）；D2 unclear（同 LN-229/两 library，无 culture/batch）；D3 partial（固定 20uM + 两时间；无功能；count_sum/genes_detected 是 RNA QC）；D4 fail；D5 partial（4 biological replicate 标签；无独立培养）；D6 fail；D7 pass。→ not_qualified。
4. **Tahoe-100M**：D1 fail（sample metadata 无 time；单时点 atlas）；D2 unclear；D3 partial（drug/dose 有，时间/功能无）；D4 fail；D5 unclear（plate only）；D6 fail；D7 pass。→ not_qualified。
5. **X-Atlas/Orion**：D1 fail（单时点 FiCS Perturb-seq）；D2 partial（Batch labels）；D3 fail（无 dose/time/function）；D4 fail；D5 partial（batch labels）；D6 fail；D7 pass。→ not_qualified。
6. **AZ/GDSC**：D1 partial（72h viability + caspase/PARP 报告；六 occasions 不是时间序列；无 RNA 群体快照配对）；D2 unclear；D3 partial（dose/time/viability；功能 numeric 未公开）；D4 fail；D5 partial（6×3 technical；独立培养未认证）；D6 partial（viability + caspase/PARP 报告，numeric 缺）；D7 fail（无 RNA/counts）。→ **data_unavailable**（M2 功能分支）。

## 4. 有界检索记录（不是穷尽）

- GEO eutils 查询：`single cell drug time course apoptosis`、`perturb-seq time course`、`single cell drug treatment time series`、`single cell RNA-seq apoptosis FACS drug`、`organoid drug single cell time course`；命中 GSE214965/GSE139944 等；未命中"多时间功能+RNA+π"组合。
- Zenodo API 查询：`organoid drug single cell time course`、`sequential drug treatment organoid single cell`；top hits 为 organoid 综述/影像/omics，无 D1–D7 合格数据集；**有界未发现**。
- HuggingFace API：Tahoe-100M（CC0；95.6M cells；无 time/function 列）、X-Atlas/Orion（CC-BY-NC-SA；8M cells；RNA-only）。
- 未做全库引文追踪/所有 GEO 页面；`not_found_in_bounded_search` 仅指本任务范围。

## 5. 缺失项与下一步

**主要缺口（M2 Stage2）**
1. **D4**：无 recorded π/随机化/assignment probability；公开数据几乎都是固定处理标签。
2. **D6**：无与 RNA 同单位/同时间/同培养的**正交功能**（apoptosis/caspase/viability/regrowth）numeric。
3. **D2/D5**：无独立培养/板/批次可认证；technical/well/occasion 重复不能替代独立培养。
4. **D1/D3**：少数 RNA 多时间候选（Mix-seq、sci-Plex 24/72h、DRUG-Seq）无功能读数。
5. AZ/GDSC：mapping + 功能 numeric + 配对 RNA 缺；DATA1 request spec 优先。

**下一步**
- **不运行 Stage2**（数据门未过）；不合成/RNA/预测替代独立功能决策。
- 若后续公开数据补齐 multi-time function + paired RNA/counts + π + independent culture：按新 DATA4 资格协议做清洗/映射/重评；不把描述性下载当合格。
- AZ/GDSC：继续 DATA1 request spec P0/P1（mapping、功能 numeric、per-barcode 18-replicate map）；不写"只能新湿实验"。
- 如需新数据：request spec 需求为"同培养物/批次可交换的 multi-time 功能 + 配对 RNA/counts + recorded π/动作 + 独立培养/板重复"；不伪造联系人/不发起请求。
- **不写"不存在"**：本轮为有界检索未发现；不称新颖性/迁移/决策收益/机制。

## 6. 产物 SHA

| 文件 | 字节 | SHA256 |
|---|---:|---|
| `PROTOCOL_DATA4.md` | 6,481 | `c206217a6ca8c1fe65d7fd7bde4e257e43f303fc8a4b0828170c325a46729912` |
| `scout_data4.py` | 34,287 | `a9723dd9106ad490097f2a9f6f1112ee9e6694163f6587a739120373d3f2f414` |
| `scout_data4.json` | 43,352 | `8aa5ac2ba9306ba0383f1fe60044ea338df3cb8f7412a6839992fb4e244081ce` |
| `report_data4.md`（本文） | — | 见 usage |
| `record_data4.md` / `usage_data4.json` | — | 见 usage |
| `receipts/` | 29 个公开文件 | 逐文件 SHA 见 `scout_data4.json:downloads` |

**边界**：无效果/响应统计；无模型拟合；无湿实验；无代码晋升；不改 M2/Stage2/DATA1–3 产物；不称药理/真实决策/迁移/机制/新颖性。
