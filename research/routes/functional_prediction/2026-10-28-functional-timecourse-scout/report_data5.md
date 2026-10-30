# R204-DATA5 报告：公开药物功能时间进程数据定向检索与 D1/D6 核验

2026-10-28 ｜ 执行：cellstate-lit（task-174） ｜ 工作目录 `D:\MAESTRO`。
协议：[PROTOCOL_DATA5.md](PROTOCOL_DATA5.md)（先冻结）｜ 机器可读：[scout_data5.json](scout_data5.json)｜ 脚本：[scout_data5.py](scout_data5.py)｜ 回执：[receipts/](receipts/)
**纪律**：有界检索 + 公开小文件下载（≤500MB/文件）+ 结构核验；**不运行效果/不拟合/不读响应做效应**；不绕过登录/许可；技术重复≠独立培养；不写"不存在/作者未做/只能新湿实验"；不称新颖性/迁移/决策收益/机制；不晋升代码。

## 0. 结论（先行）

**总体：`not_qualified`（D1/D6 缺口未补上；M2 Stage2 仍不可执行）。**
- **D1（多时间功能）**：找到多个多时间 **RNA** 数据集（GSE149428 0–24h；GSE129012 4/8h；GSE154932 0/7/10 weeks；GSE248450 4/12/20 days），但**没有**公开的**多时间功能 numeric**；功能只出现在论文/协议/图或非公开数据中。
- **D6（正交功能）**：GSE154932（Incucyte 监测）、GSE248450（FUCCI 实时细胞周期）、AZ/GDSC（viability + caspase/PARP 报告）、ctos（viability + qPCR）有**功能描述/部分读数**，但**缺公开 per-well/per-time numeric**；不能作为 D6 合格证据。
- 高内涵 imaging（BBBC021/022）是**单处理时点**（24h/单次 profiling）；`Image_Metadata_Time` 是**采集时间**，不是处理时间；无 RNA/计数配对。
- **AZ/GDSC** 功能分支仍 **`data_unavailable`**（mapping/功能 numeric/配对 RNA 未公开；DATA1/DATA3）。
- 有界检索**未发现**"多时间功能 numeric + 配对 RNA/计数 + π + 独立培养"的公开数据集；这是**本任务范围未发现，不是不存在**。
- 不运行 Stage2；不合成/RNA/预测替代独立功能决策；不写"只能新湿实验"。

## 1. 候选表与 D1–D7

| # | 候选 | 来源/许可 | D1 | D2 | D3 | D4 | D5 | D6 | D7 | 总体 |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | **GSE149428** 药物组合匹配时间进程 RNA-seq（MCF7/LNCaP） | NCBI GEO 公开 | pass (0/3/6/9/12/24h) | unclear | partial | **fail** | partial | **fail** | pass | **not_qualified** |
| 2 | **GSE129012** AZD4573 CDK9 抑制剂 RNA-seq 时间进程（MCF7） | NCBI GEO 公开 | pass (4/8h) | unclear | partial | **fail** | partial | **fail** | pass | **not_qualified** |
| 3 | **GSE154932** MDA-MB-231 阿霉素 + Incucyte 监测 | NCBI GEO 公开 | partial (0/7/10 weeks; Incucyte numeric 未公开) | unclear | partial | **fail** | partial | **partial**（numeric 缺） | pass | **not_qualified** |
| 4 | **GSE248450** HCC4006 FUCCI 细胞周期 + RNA（osimertinib±tipifarnib） | NCBI GEO 公开 | partial (4/12/20 days; FUCCI numeric 未公开) | unclear | partial | **fail** | partial | **partial**（numeric 缺） | pass | **not_qualified** |
| 5 | **BBBC021** MCF7 化合物高内涵 imaging | BBBC 公开 | **fail** (24h 单时点) | partial | partial | **fail** | partial | **fail** | **fail** | **not_qualified** |
| 6 | **BBBC022** U2OS Cell Painting | BBBC 公开 | **fail** (单时点；Time=采集时间) | partial | partial | **fail** | partial | **fail** | **fail** | **not_qualified** |
| 7 | **ctos-drug-response-networks**（Zenodo 20043756）结直肠癌类器官 derived data | CC-BY-4.0 | fail (viability 单端点；qPCR 8/48h) | partial | partial | **fail** | partial | **partial**（viability+qPCR） | partial | **not_qualified** |
| 8 | **AZ/GDSC 2024** viability + caspase/PARP（DATA1–3） | Figshare/GDSC 公开 | partial (72h; 6 occasions) | unclear | partial | **fail** | partial | **partial**（numeric 缺） | **fail** | **data_unavailable** |

**共同硬缺口**：**D4 无记录 π/随机化**；**D6 无公开正交功能 numeric**；**D2/D5 独立培养/批次不可认证**；**D1 功能时间序列缺失**（RNA 时间序列不等于功能时间序列）。

## 2. 关键结构核验（只字段/行数/时间点/功能列）

- **GSE149428**：6 个时间点 0/3/6/9/12/24 h；282 samples；设计为 3 drugs + 3 combinations 在 MCF7/LNCaP；**无功能列**（RNA only）。
- **GSE129012**：4 h/8 h；9 samples；AZD4573 vs DMSO；**无功能列**（apoptosis 只在论文题目/摘要）。
- **GSE154932**：3 samples，time point `pre-treatment/7 weeks/10 weeks`；protocol 描述 Incucyte 24h pulse + monitoring；**series matrix 无 function numeric**。
- **GSE248450**：6 samples，处理 4/12/20 days；FUCCI G1/SG2 FACS + RNA；**series matrix 无 function numeric**。
- **BBBC021**：13,200 image fields；113 compounds/8 concentrations；DNA/Tubulin/Actin 三通道；**无 treatment-time 列**；page 明确 24h 固定成像。
- **BBBC022**：单次 Cell Painting；`Image_Metadata_Time` 是采集时间戳（ms），不是处理时间；无 treatment-time 列。
- **ctos**：derived drug sensitivity 表 50 行 × 4 列（viability_ratio/response_label）；qPCR 432 行，timepoint 8h/48h；**无多时间 viability 序列；raw RNA 受控未发布**。
- **AZ/GDSC**：DATA1/DATA3 已核；raw well intensity/72h CTG + caspase/PARP 图；无 mapping/功能 numeric/配对 RNA。

## 3. 下载/可获取性

**已下载（26 个公开文件；`receipts/`；≤500MB/文件）**
- GEO series matrix：GSE149428 16,049 B；GSE129012 3,301 B；GSE154932 3,065 B；GSE248450 3,163 B（NCBI GEO public；no explicit license）。
- BBBC metadata：BBBC021 compound 8,179 B；BBBC021 image 3,965,784 B；BBBC022 image 37,119,471 B（BBBC public；no explicit license）。
- Zenodo：ctos zip 105,618 B（CC-BY-4.0）；4 个 record API JSON；5 个检索 JSON。
- GEO eutils 6 个 XML、BioStudies 1 个 JSON、BBBC 页面 HTML 2 个。
- 逐文件 SHA/大小/URL/许可见 `scout_data5.json:downloads`。

**超限未下载（只记录）**
- BBBC021 55 个 image ZIP ~750 MB each；BBBC022 image ZIPs；GEO 大 supplementary archives；TRACI IncuCyte test data 211,843,215 B（不是药物多时间功能，未下）。
- **未绕过登录/许可**；BBBC/GEO/Zenodo 公开；ctos raw RNA 为受控访问，未尝试绕过。

## 4. 有界检索记录

- GEO eutils：`drug treatment time course apoptosis/viability`、`caspase activity time course drug`、`high content imaging drug time course`、`organoid drug response time course`、`live cell imaging drug response time lapse`、`CellTiter-Glo time course`、`IncuCyte drug treatment`、`RealTime-Glo viability`、`caspase 3/7 time course drug`、`PARP cleavage time course drug`、`TRAIL time course RNA-seq`、`apoptosis RNA-seq time course drug`、`FACS apoptosis RNA-seq drug`。
- BioStudies/ArrayExpress API：`drug time course apoptosis`（broad hits; no qualifying functional multi-time）。
- Zenodo API：`organoid time lapse drug response`、`spheroid drug response time lapse`、`IncuCyte drug response`、`RealTime-Glo viability time course`、`caspase time course drug`；top hits：ctos derived data、TRACI IncuCyte migration、organoid microscopy/paper、DIPG viability PDF；**无多时间功能 numeric + 配对 RNA**。
- BBBC：BBBC021/022 页面 + metadata；单时点 imaging。
- **未做全库/所有 GEO/所有 Dryad/Figshare 页面**；`not_found_in_bounded_search` 仅本任务范围；不写"不存在"。

## 5. 缺失项与下一步

**D1/D6 仍未解决**：
1. 公开数据多为 RNA-only 时间序列（GSE149428/GSE129012）或功能描述在论文/图（GSE154932/GSE248450/AZ）；**没有可分析的多时间功能 numeric**。
2. 高内涵 imaging（BBBC）是单时点形态学，不是 apoptosis/viability 多时间功能；无 RNA 配对。
3. ctos 类器官 derived data 只有单端点 viability + qPCR；raw RNA 受控；无独立培养/π。
4. 全部候选 **D4 fail**；D5/D2 无独立培养/批次可认证。

**下一步**
- **不运行 Stage2**；data readiness 保持 open。
- AZ/GDSC：保留 DATA1 request spec P0/P1（mapping、Fig4/5/6 功能 numeric、per-barcode 18-replicate map）；不写"只能新湿实验"。
- 若未来公开数据补齐 multi-time function numeric + paired RNA/counts + π + independent culture：另立资格协议做清洗/映射/重评；不把描述性下载当合格。
- request spec 需求：同培养物/批次可交换的 **per-well/per-time viability/apoptosis/caspase + 配对 RNA counts + recorded π + independent culture**；不伪造联系人/不发起请求。
- 不称新颖性/迁移/决策收益/机制；不晋升代码；不改旧判定。

## 6. 产物 SHA

| 文件 | 字节 | SHA256 |
|---|---:|---|
| `PROTOCOL_DATA5.md` | 4,140 | `1b89509fb4b9d45fd692a51377812322eba762e0d366740ba1c7c86f4f3c7362` |
| `scout_data5.py` | 30,867 | `8c38c8710f8f7eb49f24a107e9cc2c7e33a53f2f137aabc910d2f849b81e0519` |
| `scout_data5.json` | 44,167 | `1aaf0ebabe366fbef1ba46270fdaa1c242ddea67e7a4ac81525e963b52c88ad9` |
| `report_data5.md`（本文） | — | 见 usage |
| `record_data5.md` / `usage_data5.json` | — | 见 usage |
| `receipts/` | 26 文件 | 逐文件 SHA 见 JSON |

**边界**：无效果/响应统计；无模型拟合；无湿实验；无代码晋升；不改 M2/Stage2/DATA1–4；不称药理/真实决策/迁移/机制/新颖性。
