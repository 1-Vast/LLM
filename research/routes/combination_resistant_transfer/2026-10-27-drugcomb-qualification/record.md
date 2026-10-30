# record —— R190-E1 DrugComb 资格审计（时间线 / 预算 / 决定 / 局限）

2026-10-27，数据资源资格审计员。工作目录 `D:\MAESTRO`；解释器 `D:\anaconda\envs\maestro\python.exe`（Python 3.11.16 / pandas 2.3.3 / numpy 2.4.6 / pypdf 6.18.0 / requests 2.34.2）。本文件记录**过程**；判定与数字见 [report.md](report.md)、[e1.json](e1.json)。

## 1. 范围与纪律

- 只写 `research/2026-10-27-drugcomb-qualification/` 与 `tmp/`；未修改 PROTOCOL/其它研究目录/INDEX/SYNTHESIS/git/源数据。
- 只读身份/注释/单位字符串列；响应列在 `e1.py` 中只以表头字符串出现（见 §7 复核）。
- 未读响应数值做任何统计、未训练模型、未跑效应估计、未联网提交数据。

## 2. 协议前勘察（disclosure）

按任务要求"先冻结 PROTOCOL_E1.md 再跑审计"。协议冻结（13:45 前后）之前做过的**只读**勘察仅有：
1. 网络与文件定位：`drugcomb.org`/`drugcomb.fimm.fi` 探测（失败，见 §3）；Zenodo API 三个 DrugComb 记录的文件清单/大小/MD5；Europe PMC 两篇 DrugComb 论文全文与 NAR 2021 补充材料；Figshare API 的 DrugComb 搜索（未找到官方数据仓库）。
2. 文件头/表头/行数：v1.4 summary 表头与行数（1,175,220）；v1.5 summary 表头（Range 请求）；v1.5 两个标识表 sheet/列名。
3. 结构预检：v1.4 组合/单药行数、实体数、cell×pair、碰撞；v1.5 标识表实体数；Jaaks 身份列；注释来源覆盖预检。

这些只用于**确定文件可用性/列名/分母形态**；`PROTOCOL_E1.md` 中冻结的门槛（①–⑤）、名归一、分母（D1/D2）、来源清单、采样方案、判定规则均未因预检结果调整。`e1.py` 从原始文件重新计算全部数字。**协议冻结后未修改协议**（SHA256 `48f3100…cca890`）。

## 3. 网络尝试（记录失败，不把"没找到"写成"不存在"）

| 目标 | 结果 |
|---|---|
| `https://drugcomb.org/`、`https://drugcomb.fimm.fi/`、`/downloads/` | `SSL: UNEXPECTED_EOF_WHILE_READING`（与任务已知网络事实一致） |
| `http://api.drugcomb.org`、`http://drugcomb.org` | 连接失败（"An error occurred while sending the request"） |
| `https://api.figshare.com/v2/articles/search`（search_for=DrugComb） | 可用，但未找到 DrugComb 官方数据仓库（返回的是无关数据集） |
| `https://zenodo.org/api/records/{11102665,15235991,18449193,18756096}` | **可用**；定位到 v1.4 summary、v1.5 summary、v1.5 标识表 |
| `https://www.ebi.ac.uk/europepmc/webservices/rest/...`（PMC8218202 / PMC6602441） | **可用**；取得 NAR 2021 与 2019 全文与 NAR 2021 补充材料（含 S1 37-study 表） |
| Zenodo 文件下载（含 60 字节区间块） | 可用；过程中偶发 1 次 `SSL: UNEXPECTED_EOF`，`fetch_data.py` 内置 3 次重试后成功，60/60 块完整 |

## 4. 实际命令与耗时

| 步骤 | 命令 | 耗时/结果 |
|---|---|---|
| 定位/探测 | `Invoke-WebRequest` 探测门户 + Zenodo/EuropePMC REST | 若干秒；见 §3 |
| 全量下载 v1.4 + 标识表 | `Invoke-WebRequest` 下载到 `downloads/` | v1.4 98.4 s；drug id 11.2 s；cell id 2 s |
| 统一取数（分块样本 + 回执） | `python fetch_data.py` | 201.6 s；EPMC supp 33.2 s；60×1 MB 分块其余；总下载 260,015,829 B |
| 审计 | `python e1.py` | **22.5–27.2 s**（两次/三次运行） |
| 确定性复核 | 连续两次运行 `e1.py`，比较 `e1.json` SHA256 | **相同** `2FD636D8…19DDB` |

`fetch_data.py` 幂等（已存在且字节数匹配则复用）；分块起点公式固定，逐块 SHA256 写入 `download_receipt.json`。

## 5. 预算

- 正式输入下载：**260,015,829 B = 260.0 MB**（v1.4 193.2 MB + v1.5 药标识 5.86 MB + 细胞标识 0.16 MB + EPMC 补充 0.81 MB + v1.5 分块样本 60.0 MB）。
- 另：两篇论文 fullTextXML 共 **208,064 B**（tmp/，用于已发布事实）；合计 **≈260.2 MB ≤ 300 MB**。
- v1.5 summary 全文件 1,421,694,989 B 超预算 → 只取 4.22% 固定分块样本；全文件 SHA256 记 `null`（不猜），官方 MD5 记录。

## 6. 观测（关键事实；数字以 e1.json 为准）

1. **v1.4 summary 全量**：1,175,220 块（distinct block_id 同数；单药式 709,187、组合 466,033）；组合药物 4,150 原始名 / 4,088 归一名（12 碰撞键）；细胞 112；无序药对 62,826；**cell×pair 单元 380,418**；浓度单位全 `uM`；**无 study 列**。
2. **v1.5 summary**：paper 报 751,498 组合块 + 717,684 单药块 = 1,469,182（S1 字母表解析复算吻合）；本机以 60 块 4.22% 字节样本核验（61,872 行 / 组合 32,721 / 19 个 study 出现；**剔除 GDSC/Jaaks 组合 study 后 cell×pair 下界 29,028**）。
3. **GDSC/Jaaks**：S1 中唯一匹配 GDSC 模式的 study 是 `GDSC1`（PharmacoDB 单药，矩阵 5x1/9x1，225,480 块）；v1.5 样本内 GDSC1 11,575 行全为单药、组合 0；无 Jaaks；v1.5 发布（2021-03）早于 Jaaks 2022。→ 组合单元排除 = 0。
4. **S1 复算**：字母表 5 数字段解析 + 单药/组合分类规则（PharmacoDB ∪ {BEATAML,TOURET,GORDON,ELLINGER}）**精确复现论文 751,498/717,684**；唯一矩阵启发式分歧为 FALLAHI-SICHANI（111 块，10x1/20x1，按论文总数记 combo），已记录在 `e1.json`。
5. **身份**：v1.5 标识表 8,396 药（论文 8,397，差 −1 未解释）/2,320 细胞；归一名 8,251/2,315；碰撞键 128/5；DepMap 1,475、COSMIC 1,002、Cellosaurus 1,659、tissue 34 水平；样本内名↔标识表匹配 100%。
6. **外部重合（Jaaks 身份列）**：Jaaks Original 125 细胞/65 药/108,259 有序键/70,360 无序单元；与 v1.4 组合集交集：细胞 18、药物 40、单元键 241；v1.5 标识表交集：细胞 124、药物 54。
7. **注释**：本地 7 来源并集对 D1（4,076）覆盖 **51.28%**（2,090 药，仅超线 +1.28 pp），对 D2（8,251）49.12%；Jaaks 项目现用通路模板（ANCHOR/LIBRARY_PATHWAY）只覆盖 0.98%（40 药），但提供 21 文本水平/38 双侧 one-hot 水平（与 SYNTHESIS "38 通路"一致）；DRH/PRISM 等 MoA/target 水平数远超 12，但语义 ≠ 项目通路，映射协议本地缺失。块加权（补充诊断）：两药均被本地并集注释的 v1.4 组合块 = 45.23%，至少一药 = 88.83%。
8. **端点**：v1.4 12 个响应/派生列、v1.5 14 个；无显式 QC flag 列；v1.5 有 study/tissue/clinical phase/target name 注释列。饱和性未测（协议禁止读响应值）。

## 7. 响应值保护复核

- `e1.py` 用 `csv.reader` 按**列位置**只取 READ 列；响应列名只在与表头列表比较时出现（`V14_DENY`/`V15_DENY` 常量用于"列存在性"），从未按响应列下标取行值、从未转 float、未写入任何统计。
- 产物人工复核：`e1.json`/`report.md`/`record.md` 中出现的响应相关文本仅有**列名**（如 `css`, `synergy_bliss`, `S_sum`）与"存在性"判断；未出现任何响应数值。
- Jaaks 拟合表只读 `CELL_LINE_NAME/ANCHOR_NAME/LIBRARY_NAME/ANCHOR_PATHWAY/LIBRARY_PATHWAY`（不读 `SYNERGY_*`/`LIBRARY_*` 响应列）。

## 8. 决定与理由

1. **判定 `eligible_with_conditions`**：五门槛全过（见 report §0/§9）；条件 1–7 逐条可核。不硬凑：④ 的"51.28% 仅超线 1.28 pp、D2 仅 49.12%"与"通路映射缺失"全部写入条件，并给出"若 ④ 收紧为项目同款通路标签则 not_eligible（0.98%）"的口径敏感性。
2. **主口径选择**（协议 §7 冻结）：D1 = 可下载全量核验的 v1.4 组合药物全集（4,076）为主；D2 = v1.5 药全集（8,251）为次。理由：复现分析实际进入药对分析的是"组合药物"，v1.5 全表未能在预算内全量核验；D2 的 49.12% 作为条件报告而非判定值。
3. **v1.5 只报样本下界**：不把 60 块样本的 29,028 当作全量 cell×pair；全量精确值记 `null`；"v1.5 全表可用"作为条件 1。
4. **GDSC/Jaaks 排除**：按 study 名 + 发布时序 + S1 分类判定组合单元排除 0；v1.4 无 study 列的不可逐 study 复核性作为条件 6。

## 9. 产物

| 文件 | 说明 |
|---|---|
| `PROTOCOL_E1.md` | 运行前冻结；SHA256 `48f310028de08f3d11b634d9998ea20055d8a3de41dcf45afb6d347a61cca890` |
| `fetch_data.py` | 确定性取数；SHA256 `3C39D6669B8AEF31925447929497F4873F83892F914CB4FFC5E6459215E45122` |
| `download_receipt.json` | 逐文件 URL/字节/MD5/SHA256 + 60 分块回执；SHA256 `8A9A52BA55890000DE1304A9E3C88D0E27D18C294B709493FDA6E6641AC69CF2` |
| `e1.py` | 离线审计；SHA256 `7684556DD766F0A0ADB0FEC030BCFE69177B99D30195863EF9F5C7FED5D2D916` |
| `e1.json` | 全部审计数字 + 判定；SHA256 `2FD636D84E8BEC816BCC429B691D962ED90D4B07FFF88608DB99C2BB49219DDB`（两次运行一致） |
| `report.md` | 审计报告（判定、门槛、规格对照、条件、缺口、附录 S1/样本 study 表） |
| `record.md` | 本文件 |
| `usage.json` | 运行时账（token/费用不可得记 null） |
| `downloads/` | 冻结输入（v1.4 summary、v1.5 标识表、EPMC 补充 zip、v1.5 分块样本 `v15_chunks/`） |

## 10. 局限（详见 report §10）

- 门户/API 不可达 → 无法取得 per-study 下载页与 study 级 QC；v1.5 分块样本覆盖 19/37 study（未覆盖的是小 study，属抽样缺口而非不存在）。
- v1.5 全文件未全量下载（预算）→ 全量 SHA256/全量精确 cell×pair 记 null。
- v1.4 无 study 列 → 排除只能依赖版本先验 + v1.5/S1 证据。
- 注释只用严格归一名（禁止同义词推断）→ 覆盖率可能低估；`data/knowledge/` 为空；MoA/target → 项目通路语义映射缺失。
- Jaaks 口径：本轮实测 Original 108,259 有序键 = BRIEF 的 108,259；无序归一单元 70,360，与 C155 报告的 67,812/121 细胞（先前口径）不同，未追查差异。
- 端点饱和性、ΔEMAX 可派生性、测量体制可比性未核验（协议明确不回答；下一轮前置条件）。
