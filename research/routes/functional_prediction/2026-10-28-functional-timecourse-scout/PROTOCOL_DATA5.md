# R204-DATA5 协议：公开药物功能时间进程数据定向检索与 D1/D6 核验

2026-10-28 ｜ 执行：cellstate-lit（task-174） ｜ 工作目录 `D:\MAESTRO`。
状态：**检索/下载/结构核验协议（先冻结；不运行效果/不拟合/不读响应做效应）**；用户已授权"允许下载公开数据"。
对象：R204-M2 Stage2 D1/D6 缺口（DATA4/C212 判 `not_qualified`；共同硬缺口 D4/D6/D2/D5）。本任务定向检索**药物诱导功能时间进程**（apoptosis/caspase/PARP、viability/CTG/IncuCyte/RealTime-Glo 多时间、regrowth/colony、高内涵成像时间序列、类器官/球体时间进程），评估能否补 D1（多时间功能）与 D6（正交功能）。
输出目录：`research/2026-10-28-functional-timecourse-scout/`（本协议、`scout_data5.py`、`scout_data5.json`、`report_data5.md`、`record_data5.md`、`usage_data5.json`、`receipts/`）与 `tmp/`；不改 M2/Stage2/DATA1–4 产物。

## 1. 目标与边界

- **目标**：找公开、可下载、≥2 时间点的**功能读数**（apoptosis/caspase/PARP、viability/CTG/IncuCyte/RealTime-Glo、regrowth/colony、高内涵 imaging），优先与 RNA/计数同处理同时间；按 D1–D7 核验。
- **不运行效果/不拟合/不读响应做效应**；下载后只核验字段/行数/时间点/功能列；不拼 ΔEMAX；技术重复≠独立培养；不把描述性下载当合格。
- **不绕过**登录/许可/DUA；单文件 **≤500MB**，超限只记录；不伪造联系人/不发起请求；不写"不存在/作者未做/只能新湿实验"；不称新颖性/迁移/决策收益/机制；不晋升代码。

## 2. D1–D7（M2 Stage2；写死）

| 门 | 要求 |
|---|---|
| D1 | 多时间功能/群体快照（≥2 时间点；功能优先，RNA 快照次之） |
| D2 | 同培养物/背景/批次可交换 |
| D3 | 剂量/时间/function readout（viability/apoptosis/caspase/regrowth 等） |
| D4 | 记录 π/动作标签/随机化分配 |
| D5 | 独立培养/板重复（非技术孔） |
| D6 | 正交功能（≥2 独立功能模态，如 viability + apoptosis/caspase；或 function + 正交读出） |
| D7 | 计数+RNA（同一实验单元/时间点） |

逐项 `pass/partial/fail/unclear`；总体 `qualified/qualified_with_conditions/not_qualified/data_unavailable`。**若只有描述/无公开 numeric → data_unavailable**；不得把"下载了 metadata"当 qualified。

## 3. 候选范围（不预设）

1. **GEO/ArrayExpress 药物时间进程功能**：apoptosis/caspase、PARP cleavage、viability/CTG/IncuCyte/RealTime-Glo 多时间、regrowth/colony；
2. **高内涵成像时间序列**：BBBC 等（Cell Painting/荧光）；
3. **类器官/球体药物响应时间进程**：Figshare/Zenodo/Dryad（注意受限）；
4. **公开药企/学术时间进程筛选**（2020–2026）；
5. **配对 RNA/计数**：同一处理/时间是否有 transcriptome 伴随。

**有界工具/来源**：NCBI GEO eutils + FTP、ArrayExpress/BioStudies API、BBBC 页面/metadata、Zenodo API、HuggingFace API（如适用）、web_search。检索查询/回执存 `receipts/`；不声称穷尽。

## 4. 下载与核验

- 记录 landing URL、license、登录要求、文件 URL/HTTP/大小/SHA；≤500MB 下载到 `receipts/`；超限只记录。
- 结构核验：GEO series matrix/字段、sample metadata 的 timepoint/dose/treatment；表格字段/行数/时间点/功能列；imaging metadata 的 treatment time vs acquisition time；**不读响应做效应**。
- 已有 DATA1–4/DATA3 结论可引用；不重复下载大文件。

## 5. 输出判定

- 候选表 + D1–D7 + 总体判定；缺失项；qwc/qualified→清洗/映射/资格重评下一步（不运行）；不合格→缺口与 request spec 需求。
- 确定性 JSON（排序键、无时间戳）；两跑逐字节；报告/记录/usage。

## 6. 不做/不称

- 不运行效果/预测/拟合/响应统计/湿实验/代码晋升；不改 M2/Stage2/DATA1–4。
- 不称药理学/机制/迁移/真实决策/新颖性；不写"不存在/作者未做/只能新湿实验"；不把技术重复当独立培养。
