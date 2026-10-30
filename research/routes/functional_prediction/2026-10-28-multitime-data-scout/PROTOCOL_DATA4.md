# R204-DATA4 协议：公开多时间功能/群体快照数据检索与 D1–D7 资格核验

2026-10-28 ｜ 执行：cellstate-lit（task-172） ｜ 工作目录 `D:\MAESTRO`。
状态：**检索/下载核验协议（先冻结；metadata-only + 小文件结构核验；不运行效果/不拟合/不读响应做效应）**。
用户已明确"允许下载公开数据"；本协议只下载**公开、无需绕过登录/许可**、单文件 **≤500 MB** 的数据/元数据；超限仅记录不下载。
对象：R204-M2 Stage2 数据门 D1–D7（定义见 §2）；M2 v0.2 / Stage2 v0.2 / DECISION_R204_M2_STAGE2_ACCEPT / DATA1 / DATA2 / R204 BRIEF / ERRATA C197/C199/C201/C203/C205/C210。
输出目录：`research/2026-10-28-multitime-data-scout/`（`PROTOCOL_DATA4.md`、`scout_data4.py`、`scout_data4.json`、`report_data4.md`、`record_data4.md`、`usage_data4.json`、`receipts/`）与 `tmp/`；不改 M2/Stage2/DATA1–3 产物。

> **核心声明**：本任务只做**有界检索 + 公开文件结构核验 + 资格判定**；**不运行任何效果/预测/拟合/响应统计**；下载到本地后**只读字段/行数/时间点/功能列**，不读响应做效应，不拼 ΔEMAX；不写"不存在"，只写"有界检索未发现"；不称新颖性/迁移/决策收益/机制；不晋升代码。

## 1. 目标与边界

- 目标：检索可公开获取的**多时间功能/群体快照**资源，逐项核验能否满足 M2 Stage2 数据门 D1–D7；给候选表、逐项判定、总体判定、缺失项与下一步（合格→清洗/映射/另立协议；不合格→缺口/request spec）。
- **不预设结论**：候选逐一核；可以有 `not_found_in_bounded_search`（不是"不存在"）。
- **不执行**：Stage2/3、真实响应分析、模型比较、效应统计、代码晋升、湿实验；不读任何 response/function 数值做效应。
- **不绕过**：登录/付费/点击协议/DUA/受控访问；遇到此类候选标 `restricted_login_or_terms`，不下载、不伪造访问。
- **单文件上限 500 MB**：超限记录 URL/size/原因，不下载；本地已存在且 >500MB 的资产只登记元数据（不复制）。
- **技术重复≠独立培养**；字段 glossary/设计声明≠映射；论文已做≠当前公开可取得。

## 2. D1–D7 数据门（M2 Stage2；写死）

| 门 | 要求 | 判定要点 |
|---|---|---|
| **D1** | 多时间功能/群体快照 | 至少 2 个时间点的**功能读数**或**群体快照**；优先多时间功能；只有单时点= fail/partial |
| **D2** | 同培养物/背景/批次可交换 | 同一培养物/背景/批次可追溯；跨时间点是同单位配对/可交换；无 culture/batch 标签= unclear/partial |
| **D3** | 剂量/时间/function readout | 显式 dose、time、功能读数（viability/apoptosis/caspase/regrowth 等）；RNA-only=partial |
| **D4** | 记录 π/动作标签 | 处理分配概率/策略/动作标签（π）或可重建的随机化记录；单纯 treatment 标签=fail |
| **D5** | 独立培养/板重复 | 独立培养或独立板重复（非技术孔重复）；只有 technical replicate=partial/fail |
| **D6** | 正交功能 | 两个独立功能模态（如 viability + apoptosis/caspase；或 function + 正交读出）；无= fail |
| **D7** | 计数+RNA | 原始计数与 RNA 并存（同一实验单元/时间点）；仅 RNA 或仅功能=fail/partial |

判定等级：`pass / partial / fail / unclear`。总体：`qualified / qualified_with_conditions / not_qualified / data_unavailable`；**若只是公开描述/下载不足、不能结构核验，则 `data_unavailable`**；不得把描述性下载当合格。

## 3. 候选检索范围（不预设）

1. **scPerturb/perturb-seq 多时间集合**：Mix-seq（本地 scPerturb 资产）、Norman/Replogle 时间版本（若有）、Perturb-seq time course。
2. **单细胞药物时间序列**：sci-Plex（GSE139944）、DRUG-Seq（GSE214965）、其它 2024–2026 药物时间序列。
3. **类器官/患者来源顺序给药**：Dryad/Figshare/Zenodo（注意 C200/C210 受限情况）。
4. **功能读数数据集**：apoptosis/caspase/靶点参与/再生长，配 RNA/计数。
5. **2025–2026 新公开组合/时间数据**：Tahoe-100M、X-Atlas/Orion、Europe PMC/Figshare/Zenodo/GEO。

**有界检索工具/来源**：NCBI GEO（eutils esearch/esummary + FTP 文件）、HuggingFace dataset API/README/metadata、Zenodo API、Europe PMC/R204 DATA1/DATA2 已核记录。检索查询/结果写入 `receipts/search_log.json` 与报告；不声称穷尽。

## 4. 下载与回执

- 对每个候选：
  - 记录 landing URL、许可（license）、是否需登录/点击协议、文件 URL、HTTP 状态、Content-Length、本地路径、SHA256、下载日期。
  - 单文件 ≤500MB：下载到 `receipts/`；>500MB：只记录 URL/大小/原因（`not_downloaded_over_500MB`）。
- **只做结构核验**：
  - 文本/表格：字段名、行数、时间点唯一值、功能列存在性、重复/培养/批次标签存在性；
  - parquet/h5ad：列名、行数、唯一时间/dose/药物/细胞系数；
  - **不读 response/function 数值做效应**；不拟合、不统计、不比较候选效果。
- 已有公开报告（DATA1/DATA2、M2 v0.2）可作为候选证据；不重复下载大文件。

## 5. 输出与判定

- `scout_data4.json`：候选表（URL/license/size/SHA/access）、D1–D7 评级、总体判定、结构核验、搜索日志、缺失项、下一步；确定性（排序键、无时间戳）。
- `report_data4.md`：候选表 + 逐项 D1–D7 + 总体判定 + 可下载/受限 + 缺口 + 下一步。
- `record_data4.md`：读/搜/下载/核验过程、命令、SHA、错误、限制。
- `usage_data4.json`：输入/输出 SHA、下载/未下载清单、网络请求、无效果声明。
- 总体判定规则：任一候选满足 D1–D7=qualified；满足但带条件=qwc；有数据但关键门失败=not_qualified；只有描述/不可核验=data_unavailable。

## 6. 不做 / 不称

- 不运行效果/预测/拟合/响应统计；不读响应做效应；不拼 ΔEMAX；不把技术重复当独立培养；不把 glossary/design 声明当 mapping。
- 不称新颖性/迁移/决策收益/机制/药理；不晋升代码；不改旧判定/门槛；不恢复停止实验。
- 不写"不存在/作者未做/只能新湿实验"；只写有界检索结果与缺口；request spec 需求不伪造联系人、不发起请求。
