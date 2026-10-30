# R204-DATA5 记录（record_data5）

2026-10-28 ｜ 执行：cellstate-lit（task-174） ｜ 工作目录 `D:\MAESTRO`。
对象：公开药物功能时间进程定向检索 + D1/D6 核验；用户已授权"允许下载公开数据"。
**不运行效果/不拟合/不读响应做效应**；只写 `research/2026-10-28-functional-timecourse-scout/` 与 `tmp/`；**不改 M2/Stage2/DATA1–4 产物**。

## 0. 纪律与范围

- **有界检索 + 公开文件下载（≤500MB/文件）+ 结构核验**；不读响应做效应、不拟合、不统计、不拼 ΔEMAX。
- 未绕过登录/许可/DUA；BBBC/GEO/Zenodo 公开；ctos raw RNA 受控访问，未尝试绕过。
- 技术重复≠独立培养；功能描述/论文图≠公开 numeric；不写"不存在/作者未做/只能新湿实验"。
- 不称新颖性/迁移/决策收益/机制/药理；不晋升代码；不改旧判定。

## 1. 读取/输入

| 输入 | 用途 |
|---|---|
| `2026-10-28-multitime-data-scout/{report_data4.md,scout_data4.json}` | DATA4/C212：6 候选 not_qualified；D4/D6/D2/D5 缺口 |
| `2026-10-28-m2-stage2-prep/{PROBLEM,DESIGN}_M2_STAGE2_v0_2.md` | D1–D7 定义、Stage2 门 |
| `2026-10-28-az-download-verify/report_data3.md` | AZ/GDSC 公开数据/字段/功能 numeric 缺失（C211） |
| `2026-10-28-deep-coupling-redesign/{BRIEF_R204.md,report.md}` | R204/M2 背景与边界 |
| `EVIDENCE_REGISTER.md`（C211/C212） | 数据 readiness/旧判定（只读） |

## 2. 检索与下载

**检索**：
- web_search 4 组：sci-Plex 时间点、多时间 apoptosis/功能、perturb-seq time course、organoid sequential。
- GEO eutils（XML 回执 `receipts/eutils_gds_*.xml`）：drug treatment time course apoptosis/viability；caspase activity time course drug；high content imaging drug time course；organoid drug response time course；live cell imaging drug response time lapse；CellTiter-Glo time course；IncuCyte drug treatment；RealTime-Glo viability；caspase 3/7 time course drug；PARP cleavage time course drug；TRAIL time course RNA-seq；apoptosis RNA-seq time course drug；FACS apoptosis RNA-seq drug。
- BIOStudies/ArrayExpress API：drug time course apoptosis（广泛命中，无合格多时间功能数据集）。
- Zenodo API 5 组：organoid time lapse drug response；spheroid drug response time lapse；IncuCyte drug response；RealTime-Glo viability time course；caspase time course drug。
- BBBC：BBBC021/BBBC022 页面 + metadata CSV。

**下载（26 个公开文件；41,545,223 B；`receipts/`）**：
- GEO series matrix：GSE149428 16,049 B；GSE129012 3,301 B；GSE154932 3,065 B；GSE248450 3,163 B。
- BBBC：BBBC021 compound 8,179 B；BBBC021 image 3,965,784 B；BBBC022 image 37,119,471 B；HTML 页面 2 个。
- Zenodo：ctos zip 105,618 B（CC-BY-4.0）；record/search JSON。
- GEO eutils 6 XML；BioStudies 1 JSON。
- 逐文件 URL/bytes/SHA/license/login 见 `scout_data5.json:downloads`。

**超限未下载**：BBBC021/022 image ZIPs（~750MB each 等）；GEO 大 archives；TRACI IncuCyte 211,843,215 B（非药物多时间功能）。**未绕过任何受限访问**。

## 3. 结构核验（只字段/行数/时间点/功能列）

- GSE149428：0/3/6/9/12/24 h；282 samples；RNA only；无功能列。
- GSE129012：4/8 h；9 samples；RNA only；无功能列（apoptosis 只在论文）。
- GSE154932：pre-treatment/7 weeks/10 weeks；3 samples；Incucyte 监测描述但 series matrix 无 function numeric。
- GSE248450：4/12/20 days；6 samples；FUCCI G1/SG2 + RNA；无 function numeric。
- BBBC021：13,200 image fields；113 compounds/8 concentrations；DNA/Tubulin/Actin；无 treatment-time 列（页面 24h 固定）。
- BBBC022：单次 Cell Painting；`Image_Metadata_Time` = 采集时间戳；单时点。
- ctos：drug_sensitivity 50×4（viability_ratio/response_label）；qPCR 432×6（timepoint 8h/48h）；raw RNA 受控未发布。
- AZ/GDSC：DATA1/DATA3 已核；raw well/72h CTG + caspase/PARP 图；mapping/功能 numeric/配对 RNA 缺。

## 4. 排错/注意

- BBBC022 image CSV 有行字段数不一致（Expected 22, saw 24），用 `on_bad_lines="skip"` 读取（结构计数；不读响应）。
- GEO timepoint 解析初期被 cell line 名（MCF7/4006）干扰，改为从 `Series_overall_design` 的明确短语抽取（GSE149428 `at ... hours`；GSE248450 `for ... days`）。
- BBBC 页面 HTML 噪声大；只取 metadata CSV 字段（compound/concentration/Replicate/channels/time column）。
- 未遇到需要登录/许可绕过的下载；ctos raw RNA 为受控访问，未尝试。

## 5. 验证与产物

```text
scout_data5.py 运行两次，scout_data5.json 逐字节一致：
  SHA256 1aaf0ebabe366fbef1ba46270fdaa1c242ddea67e7a4ac81525e963b52c88ad9 (44,167 B)
PROTOCOL_DATA5.md SHA256 1b89509fb4b9d45fd692a51377812322eba762e0d366740ba1c7c86f4f3c7362 (4,140 B)
scout_data5.py SHA256 8c38c8710f8f7eb49f24a107e9cc2c7e33a53f2f137aabc910d2f849b81e0519 (30,867 B)
report_data5.md SHA256 d3b6d8d16169ec3ad9ce94d609069b8305c5dd4a3200b09d6fd948d4e80e5799 (9,264 B)
receipts/ 26 文件，合计 41,545,223 B；逐文件 SHA 见 scout_data5.json:downloads
```

**总体判定**：`not_qualified`（D1 多时间功能 numeric 未找到；D6 只有部分描述/numeric 缺失；D4/D5/D2 仍不合格）；AZ/GDSC 功能分支 `data_unavailable`。
**有界检索未发现**"多时间功能 numeric + 配对 RNA/计数 + π + 独立培养"数据集；**不是不存在**。
**未运行**：效果/预测/拟合/响应统计/湿实验/代码晋升。

## 6. 产物与 SHA256

| 文件 | 字节 | SHA256 |
|---|---:|---|
| `PROTOCOL_DATA5.md` | 4,140 | `1b89509fb4b9d45fd692a51377812322eba762e0d366740ba1c7c86f4f3c7362` |
| `scout_data5.py` | 30,867 | `8c38c8710f8f7eb49f24a107e9cc2c7e33a53f2f137aabc910d2f849b81e0519` |
| `scout_data5.json` | 44,167 | `1aaf0ebabe366fbef1ba46270fdaa1c242ddea67e7a4ac81525e963b52c88ad9` |
| `report_data5.md` | 9,264 | `d3b6d8d16169ec3ad9ce94d609069b8305c5dd4a3200b09d6fd948d4e80e5799` |
| `record_data5.md`（本文件） | — | 见 usage |
| `usage_data5.json` | — | 见文件 |
| `receipts/` | 26 文件 | 逐文件见 JSON |

## 7. 限制/下一步

- 有界检索；未做全库/所有 Dryad/Figshare 页面；`not_found` 仅本任务范围。
- >500MB/文件未下载；BBBC/GEO 大图/大矩阵未做全数据字段审计。
- 没有候选达到 D1–D7；不运行 Stage2；AZ 保留 DATA1 request spec；若未来公开数据补齐多时间功能 numeric + paired RNA/counts + π + independent culture，再另立资格协议；不写"只能新湿实验"。
- 不称新颖性/迁移/决策收益/机制；不晋升代码；不改旧判定。
