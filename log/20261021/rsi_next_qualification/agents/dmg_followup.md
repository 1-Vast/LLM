# DMG 元数据补充审计，2026-10-21

结论：**NO-GO：当前不能启动药效排序、联合收益或 RSI 确认实验。** 这不排除在独立协议下做未见药物/药族的分子预测开发；但不能据此宣称反馈改善功能决策。未扩大数值下载。

脚本：[dmg_metadata.py](../../../../research/rsi_next_qualification_20261021/dmg_metadata.py)。收据：[dmg_metadata_receipt.json](dmg_metadata_receipt.json)。复现：在仓库根目录运行 `python research/rsi_next_qualification_20261021/dmg_metadata.py`。脚本约26.11秒；4线程、12份GEO brief元数据、4份孔位元数据、22次文件HEAD；无训练/GPU/API实验，种子不适用。

## 已查实的文件与样本结构

[GSE264130](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE264130) 的完整GSM清单只有下列四份。每份是整板，不是一条独立细胞背景：

| GSM | 细胞系 / 重复 | 元数据 supplement | gzip bytes |
|---|---|---|---:|
| GSM8212608 | DIPG6 / 1A | GSM8212608_DiPG6PS1A-samples.tsv.gz | 5,629 |
| GSM8212609 | DIPG6 / 1B | GSM8212609_DiPG6PS1B-samples.tsv.gz | 5,639 |
| GSM8212610 | SF8628 / 1A | GSM8212610_SF8628PS1A-samples.tsv.gz | 5,647 |
| GSM8212611 | SF8628 / 1B | GSM8212611_SF8628PS1B-samples.tsv.gz | 5,644 |

元数据总载荷 **22,559 bytes**。文件无表头，三列为barcode、well、`drug_dose_time`条件字符串。四板均384孔：372种相同药物、6 DMSO、6 MOCK；各细胞系A/B条件完全一致；两细胞系有**114种药的剂量字符串不同**，全部时间字符串为24。因此可核对同药，但不能把两系的RNA当作相同剂量实验。字符串剂量单位需由协议/附件显式确认，不能仅由文件名推定。

每个GSM还各有一个相邻 `_counts.tsv.gz`，均仅HEAD，未读取。系列层仅列出22,056,960-byte `GSE264130_RAW.tar`，同样未取内容。原始测序可通过SRA关联追踪，但测序不补充48h功能矩阵。完整URL、SHA256、SRA/BioSample关系及孔位条件已存收据。GSM8212610/11的source/tissue字段拼为SF8626，但cell line字段与标题为SF8628；保留该冲突，未静默改写源记录。

## 发布方附件定位

发布方：[Nature Genetics DOI 10.1038/s41588-026-02550-w](https://www.nature.com/articles/s41588-026-02550-w)。以下均HEAD 200，**未读取XLSX/PDF工作表或数值**。共同前缀是 `https://media.springernature.com/original/springer-static/esm/art%3A10.1038%2Fs41588-026-02550-w/MediaObjects/`，收据保留全URL与ETag。

| 文件尾名 | 发布方说明 | HEAD大小 |
|---|---|---:|
| 41588_2026_2550_MOESM1_ESM.pdf | 补图1–7 | 51,192,919 |
| 41588_2026_2550_MOESM2_ESM.pdf | Reporting Summary | 143,616 |
| 41588_2026_2550_MOESM3_ESM.xlsx | 补表1–5；表4为药物扰动元数据及推断NES | 未给Content-Length |
| 41588_2026_2550_MOESM4_ESM.xlsx | Fig5两周肿瘤体积 | 10,742 |
| 41588_2026_2550_MOESM5_ESM.xlsx | Extended Fig7体积 | 未给Content-Length |
| 41588_2026_2550_MOESM6_ESM.xlsx | Fig4药物组细胞状态数量 | 10,861 |
| 41588_2026_2550_MOESM7_ESM.xlsx | Supplementary Fig4细胞状态数量 | 未给Content-Length |

附件名称/说明没有指向完整372药48h CellTiter-Glo十剂量矩阵，也没有单列Fig6患者功能筛选的Source Data。**未定位不等于已证明附件内部不存在**：本次按授权仅查元数据，未取MOESM3来找工作表。公开方法确实描述了48h十剂量三重复先确定EC20，再选24h RNA剂量，但实验做过并不能证明完整原始功能数据已发布。

## 三患者混淆与其他accession

[GSE264412](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE264412) 的三个GSM8217750/51/52分别为MTB36/37/41；前两者Biopsy，后者Surgery，均明确untreated tumor。只列一个202,644-byte KallistoCounts补充文件。它能提供基线RNA，不能提供三患者药后RNA或功能矩阵。

论文正文确实描述MTB36/37各63药、MTB41 175药功能筛选（与PLATE-seq交集分别52/52/124），因此“完全没有患者药效实验”也不成立；准确缺口是**这些功能结果的可核验发布路径和完整动作菜单尚未找到**。患者RNA与药物转录组来自不同对象。引用69是Rusert et al. 2020 medulloblastoma精密医学方法论文，并非另一个已核验DMG结果accession。

同时核对全部其他数据可用性所列GSE：

- GSE267415：CRISPR转录因子筛选；series仅2个聚合GSM、计数包及两份样本信息XLSX，不是小分子372药功能矩阵。
- GSE262774：3个GSM，DIPG4423/正常脑干基线scRNA；不补三患者药物菜单。
- GSE262775：24个GSM，DIPG17药物/vehicle scRNA；是同一模型多处理，未把其算成24独立背景。系列只列RAW.tar，未取数值。

上述链接没有解决三患者干预转录组或完整372药功能响应的发布缺口。没有请求作者、发送邮件或扩展大规模搜索。

## 具体重启条件

1. 先取得独立的文件/schema清单，确认372药×2系的实际48h剂量、原始well/replicate/plate/control、完整反应矩阵及缺失标记；或明确受限于三患者63/63/175药的共同已测菜单。仅EC20列不足以构成无偏功能目标。
2. 预先说明RNA剂量由EC20选择这一信息路径。若目标是该EC20或同批拟合量，RNA剂量属于结局衍生信息；强直接基线须获得相同剂量元数据。不能把该设置包装成零信息未知药效预测。
3. 若拿到完整功能菜单，允许先做药物/药族留出开发：精确绑定cell、compound、dose、duration，按药族隔离支持药和目标药，不在仅两细胞背景上宣称新背景泛化。
4. 联合收益/继承/RSI需要额外独立任务、锁定评价及预算；两系两重复、单系24鼠样本或三患者基线RNA都不能替代它们。

工作流失败记录：最初探索性打印把第一条孔位记录误当表头，显示383；正式脚本按无表头处理并验证384，无第一药丢失。一次web点击附件链接遭unsupported XLSX/timeout拒绝，未返回数值；之后仅用HEAD，不声称这些web尝试零网络载荷。正式脚本未请求任何计数/功能/XLSX/PDF/TAR body。未改既有冻结报告或数据。
