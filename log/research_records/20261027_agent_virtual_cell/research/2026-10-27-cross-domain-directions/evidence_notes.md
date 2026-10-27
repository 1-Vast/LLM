# 原文证据与本地对象边界

2026-10-27。有界研究，非系统综述。R=题录，A=摘要，P=读过相关方法/限制片段，F=逐段全文核读；本轮不把任何论文记作F，不声称复现作者效果。统计构造与生物效果分开。

## P1：协调者四条精确查询

1. `2025 2026 virtual cell perturbation prediction benchmark simple baselines generalization`
2. `"CellFlow" perturbation flow matching`
3. `2025 2026 single cell dynamics identifiability snapshots trajectories causal`
4. `2025 2026 compositional drug perturbation combinations causal model prediction`

只继续打开发现源/必要版本和已有库原文。P2/P3原样查询见 robotics_scout.md、cv_nlp_scout.md。P4代理报告用完4条，原样文本未在服务故障前落盘；缺口见challenge.md，不补造。P1–P4共享16-query硬上限，无第五pass。文献日期窗口2025-01-01—2026-10-27，必要奠基原理允许更早版本；AlphaEdit首次2024，所读v4/ICLR2025身份分开记录。

## 改变方向选择的一手源

| 来源/版本 | 实读内容与证据级 | 能支持什么，不能支持什么 |
|---|---|---|
| [Benchmarking virtual cell models for in-the-wild perturbation response](https://arxiv.org/html/2604.27646v1)，2026-04-30 | P；结果中的背景/扰动/跨数据集迁移，基线与评价定义 | 常规线性/加性及直接模型需要强对照；池化不必改善域移。作者结果不等于本项目已复现；测试基因mask等实现须独立冻结。 |
| [CellFlow: Simulating Cellular Morphology Changes via Flow Matching](https://arxiv.org/html/2502.09775v1)，2025-02-13 | P；§§2.2、3.1–3.4、AppendixG | 固定终点形态的未配对生成；线性插值中的t不是实测物理时间。可生成中间形态，不证明真实路径、药效恢复或机制。 |
| [Learning Individual Dynamics from Sparse Cross-Sectional Snapshots / CADENCE](https://arxiv.org/html/2605.23470v1)，2026-05-22 | P；§§2–5，A.3的DFA/COA/PR/FOA | 结论依赖已知入组时间/静态背景、参数族及参数到时间边缘分布的注入条件。多时间快照本身不认证这些条件。 |
| [AlphaEdit](https://arxiv.org/html/2410.02355v4)，2025-04-22v4；首发2024-10-03 | P；§§2.2–3.3，式7–12及数值零空间 | 同冻结旧键的精确输出保持；投影核残差回归等价由本轮推导。没有未经测量的药理迁移信息。 |
| [AlphaEdit复核](https://arxiv.org/html/2606.26783v2)，2026-07-07 | P；§5.3、A.3.1–A.3.2 | 原范围可复现与扩展范围退化是作者实证。后归一化的原文解释不能推翻精确相同旧输出经确定函数仍相同的恒等式；不把所有解释当定理。 |
| [Poke and Strike](https://arxiv.org/html/2509.00178v1)，2025-08-29 | P；§§4.1–4.5、5.3、6 | 任务敏感性决定所需辨识精度，依赖仿真特权真值；作者明确动态结构失配未解决。 |
| [SPI-Active](https://arxiv.org/html/2505.14266v1)，2025-05-20 | P；§§3–4、7，Algorithm1，A.5 | 可执行命令激发辨识方向，FIM与参数补偿限制。机器同个体轨迹不可等同破坏性细胞快照。 |
| [PDTSyn](https://doi.org/10.1093/bib/bbag199)，2026 | P；原JATS sec2g/2h/2m/2r、sec3j，部分表；未核补充/源码 | 共享+细胞条件参数分解、分布对齐、未见细胞/药物/药对已有。三类单轴holdout不能自动当双轴同时冷启动；原文的机制措辞不作靶点真值。 |
| [DECANT](https://doi.org/10.1093/bioinformatics/btag662)，2026 | P；原JATS §§2.4–2.5、2.8–2.9、4 | 输入含处理后细胞、对照与背景；药物留出重构≠未处理输入的全新药预测。作者明确机制latent是转录表型、非靶点参与/因果通路。匹配对照允许最近时间/全局回退，并非所有袋都严格匹配。 |
| [BATCHIE](https://doi.org/10.1038/s41467-024-55287-7)，2025-01-02 | P；旧库JATS Sec12/14/20及式24–30 | 已有条件组合项、后验更新、整板设计，一般有界非负对称模型距离可表示动作分歧。普通共同学习外层或动作距离不新。独立培养/完全双冷启动需另核。 |
| [GoBOED](https://arxiv.org/html/2605.26093v1)，2026-05-25 | P；§3.3、PK例 | 决策导向设计已用于药代剂量；该文明确凸下游决策范围，不代表离散药筛/结构全错已解决。 |
| [Decision-Focused Sequential Experimental Design](https://arxiv.org/html/2602.05340v1)，2026-02-05 | P；摘要、§1方向目标 | 全局误差并非唯一目标、方向不确定性和提前停止已有。 |
| [Target Identifiability from Destructive Single-cell Snapshots](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=7368638)，2026-08-29 | 初始A，403，后由P4继续核查；最终范围以challenge.md为准 | 是C2最近先例威胁；不能把摘要sharp LP/目标采样措辞补成未读定理。 |

## 访问受限，未用于负载机制的条目

- [Wei等，Nature Methods](https://www.nature.com/articles/s41592-025-02980-0)：online2025-12-11、卷期2026。R，出版社跳认证/500；未读方法。
- [Rethinking Perturbation Prediction Baselines，ICLR2026](https://openreview.net/forum?id=AIwJo1IemT)：官方题录/索引片段；forum/PDF验证页，未读正文。
- Theislab [CellFlow官方文档](https://cellflow.readthedocs.io/en/latest/) 链接 `10.1101/2025.04.11.648220v1`，bioRxiv全文未恢复。与形态CellFlow不是同文；文档不能替代本文机制验证。
- [PDGrapher](https://doi.org/10.1038/s41551-025-01481-x)：既有库受限，搜索片段非完整方法；未把因果启发图当真实因果图。
- CV的LOGICZSL在P4恢复官方PDF，协调者后核§§3.2–3.4、式2–16，升级P；PDF已入库。coding-rate组合视频仍只有R/A，不从题名补损失。见challenge.md。

## 直接本地证据

最新R192/R193：latest_audit.md逐条列协议、代码行、JSON键与终检SHA。旧复合阴性/等价性范围沿用已复核的 independent-reassessment/report.md；其“R192未执行”状态已经过时，本轮报告覆盖当前状态，不篡改历史。

Mix-seq只枚举旧 census 的 time/perturbation/cell_line 元数据，见 mixseq_metadata_check.json。285是共同实体键，含对照，不是285药物、不表示285独立培养，也未认证剂量/批次/完整时间结构。原文件源hash会纳入本轮快照。

structural_checks.py/json仅为明确假设的算术反例/正向构造：ID聚合、投影核等价与噪声放大、加性干扰消去、边缘分布相同但路径不同、相关性与选药效用不等价。未产生新生物效果或数据集性能。

## 参考库交付限制

用已安装reference_library.py顺序增量登记和收集；已有manifest不手改。P1新增3份HTML及受限题录；P2/P3新增4份HTML、2份原始JATS在本轮目录。主文件导入器不接受XML，因此JATS不伪装HTML/PDF，也不伪装supplement绕过；库中登记确切原文位置和阅读范围。P4增量及最终verify以record.md/usage.json为准。源码仅已有官方模板快照；本轮未运行/核验新论文源码。
