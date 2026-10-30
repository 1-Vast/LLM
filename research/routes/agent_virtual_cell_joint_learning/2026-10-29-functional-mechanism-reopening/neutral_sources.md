# 中性 scout 的静态来源与预算记录

2026-10-29。读取原文的目的仅为发现能改变问题的条件。0 网络动作；0 下载；0 原 ZIP/response 派生读取；0 科学效果运行、拟合、训练、作者代码执行；0 子代理。使用 PowerShell 的 Get-Content、rg、Import-Csv、Select-Xml 对已有元数据和论文原文作静态读取；局部去标记/去重复 TeX 仅为显示正文，未形成响应数据或科学计算。仅写本 episode 的三个 `neutral_*.md` 文件。

## 实际范围

- 本轮 `record.md` 全文；innovation-research `SKILL.md` 全文与 `references/idea-development.md` 全文。指导用于“观察—限制条件—改变—可行构造—区分预测”，未读取维护测试作为研究证据。
- `reference/papers.tsv`：初次关键词全文行检索输出截断，不能算全读；后将 paper_id/title/local_path/download_status 四列分成前 55、其后 55、110 以后到末尾三段，全部可见。没有把已下载标签当本 scout 全文阅读或重新哈希验证。阅读过的元数据注释提及既有读法与少量历史标签，因此 fresh 仅表示未读旧候选正文/结论，不是完全无历史提示。
- MEMORY.md 仅工作流维护条目，范围 438–480；采用的规则在 470–478：区分改进机制与普通重拟合；被截断的内容需恢复。未读取 D:\MAESTRO 旧研究候选的 memory 条目或 rollout。关联 rollout id：01a175d3-5fd2-7283-b199-96dde529fe77。所有指导已在现行技能核回；不把旧维护实验当当前研究结果。

## 四件原文，未扩展第五件

| ID | 原文与本地路径 | 本轮实际读到的部分 | 支持与限制 |
|---|---|---|---|
| N1 | [Generalised Transportability via Causal Abstractions](https://arxiv.org/abs/2608.15645)，`reference/papers/arxiv-2608.15645/paper.html` | Abstract；Introduction 主要段落（HTML 390–460，初次截断处 411–432 已另取）；Section 7/7.1（1555–1645，全段恢复）；Section 11（3267–3312）。显示时公式省略，未读形式证明、算法细节和实验表。 | 原文把可信 source SCM、已知可变机制与 target ambiguity 作为前提。可借鉴“一个共享映射对多个干预必须兼容”的问题原则；不能把该定理直接应用于无已知 SCM 的药筛，不能许诺实际区间覆盖。Section 11 也明示方向与半径依赖声明的知识；观察拟合未必选择正确半径。 |
| N2 | [Data-driven learning of structure augments quantitative prediction of biological responses](https://doi.org/10.1371/journal.pcbi.1012185)，`reference/papers/doi-10.1371-journal.pcbi.1012185/supp-p6_structure_learning.xml` | Abstract/Author summary；标题为 Learnt structure contains rich information to assist regression、Structure-augmented regression、Application of SAR to active learning 的三个完整 XML sec。未读其他实验结果、附件和代码。 | 先用 SVC 学阈值边界，再把边界函数值加入回归；边界附近/远处选点已是明确先例。阈值边界或所谓“结构学习”本身不证明分子机制。作者模拟与性能值仅为论文报告，未重现。技术文件名含 supp，但文件内容为 main article JATS。 |
| N3 | [Multi-output prediction of dose–response curves enables drug repositioning and biomarker discovery](https://doi.org/10.1038/s41698-024-00691-x)，`reference/papers/doi-10.1038-s41698-024-00691-x/supp-p5_dose_mogp.xml` | Abstract；Methods Dose–response、Multi-output Gaussian process regression model、Prediction on GDSC1 and GDSC2 and vice versa、Measuring observed dose–response curves。模型段初次输出因重复 TeX 截断，已单独去除重复 TeX 并恢复全部正文及 MathML 文本；其余三节初次可见。未读全实验/代码/补充材料。 | 剂量为多输出，ICM 共享潜在 GP；跨筛选比较仅在剂量重叠区域；曲线摘要采用拟合曲线。属于直接多输出预测强替代，不能从“共享更新对象”推出新颖性。文内 assay 命名只按原文记录，没有独立验证其所有试剂措辞。 |
| N4 | [A Simple High-Content Cell Cycle Assay Reveals Frequent Discrepancies between Cell Number and ATP and MTS Proliferation Assays](https://doi.org/10.1371/journal.pone.0063583)，`reference/papers/doi-10.1371-journal.pone.0063583/paper.html` | Abstract；Introduction 1431/1433/1434/1436；Compound Treatment 1439；Comparison of Assay Formats 1885–1896 全段，及 1884 的 tivantinib 段。初次搜索输出截断，所依赖 assay 比较段已单独恢复。未读全部方法、图像、其他结果或补充文件。 | 药物条件可改变每细胞 ATP/MTS 量；细胞计数与代理端点不能互换。作者使用不同 assay 的 replicate plates、48 h、20 点二倍稀释；本 scout 未把 replicate plates 进一步认定为独立培养或独立实验批次。 |

## 新颖性与运行设置

0 网络权限意味着本 scout 没有做当前查新。库有 2026 来源也不等于覆盖全部领域。A 的相对效价/曲线配准/单指标模型、B 的药理靶点反卷积与逻辑模型目前仍需 root 精确原文核查；这些名称在本报告中是必须比较的标准替代，不是已完成的先例穷尽。

- native requested model/effort：收到的任务消息未给出实际 spawn 参数；以 root dispatch ledger 为准，scout 不猜测。
- native effective model/effort：unknown；无运行元数据证明。
- actual token usage / monetary usage：unknown；没有此代理的原生计费遥测。
- 研究单元：共享 3 单元/12 请求预算中的探索份额，不将三条 lead 或文件数另算预算。公共访问逻辑动作实际 0。
- 初稿建立前未读 INDEX 或旧报告。初稿完成后才开始档案对照，具体名单写在 neutral_archive_comparison.md；四件原文上限不随阶段重置。
