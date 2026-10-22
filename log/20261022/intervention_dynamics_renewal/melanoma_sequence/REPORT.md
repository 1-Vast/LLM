# WM1366 药序小工作簿：独立身份资格

2026-10-22；scientific_skeptic。**结论：认证一个真实、单次成像导出内的两药序人口水平时间序列；可用于极窄的同孔早期死亡读数→后期死亡读数回顾性预测/机制压力测试。当前不具备 held-out biological-run 的世界模型/智能体/继承/RSI 评估资格，不启动拟合。** 缺口是独立成像run及完整处理/分子状态连接，不能拿三技术孔或flow三独立天补足。

## 收据与读取边界

先读已存在的 `functional_scout/REPORT.md`、`EVIDENCE.json` 与manifestreceipt，复用其PMC13338063全文XML。Primary为 *Systematic interrogation of drug sensitivities in melanoma reveals potent synergistic and antagonistic drug combinations with translational potential*，DOI **10.1038/s43856-026-01583-w**（2026-04-30）。

本轮仅1GET：`https://zenodo.org/api/records/18962045/files/Suppl%20Data%2003.xlsx/content`。HTTP200，**13,994bytes**，MD5 **61e96850942060d93915800cd08946dc** 与manifest完全相同；SHA256 **d55859b3d3338dc2c114a884e5cd649e60cf642bd26d30f921b5703b2cd93fa7**。无redirect/retry，timeout25s，cap100,000bytes未触及。精确receipt在 `RECEIPT.json`，原始body为 `Suppl Data 03.xlsx`。没有其他请求、大文件或作者联系。

先做OOXML结构/受限stringheaders，再把 **B6:B22** 登记为header-qualified `Elapsed` 设计数字白名单后才导出。响应区 **C6:Q22** 无论numeric或sharedstring均保持封闭；未导出其sharedstring索引或payload、未计算统计/图表。需要特别注意该文件多数响应以sharedstring存储，“只读strings”并不自动等于不读响应。本次只访问允许的header/condition/date字段。

Spreadsheet技能的read-only/scientific要求用于保持来源、单位和缺失语义；不修改/重算/导出源workbook，未使用会展开responses的常规inspection/rendering。

## 精确schema与设计身份

只有一个sheet：**`Fig 4B data`，A1:Q22，无merged cells**。

| 坐标 | 身份/定义 |
|---|---|
| A1 | `Vessel Name: Pilar_cytotox_cyt_clad_2nd` |
| A2 | `Metric: High green intensity cells normalized to total cells (per well)`（原文双空格不影响身份） |
| A3 | `Analysis: Refined green classification_Pilar_WM1366` |
| A5 / B5 | `Date Time` / `Elapsed` |
| A6:A22 | 2024-09-16 13:12 至 2024-09-18 13:12，按3h连续timestamp |
| B6:B22 | **0,3,6,…,48 h**，17个时点；B14=24h、B15=27h、B22=48h |
| C5:E5 | DMSO0.2%，plate wells A1/A2/A3 |
| F5:H5 | Abemaciclib0.2 `ÂµM`，wells A10/A11/A12 |
| I5:K5 | Cladribine0.2 `ÂµM`，wells B7/B8/B9 |
| L5:N5 | `Clad -> Abe 0.2 ÂµM`，wells E7/E8/E9 |
| O5:Q5 | `Abe -> Clad 0.2 ÂµM`，wells F7/F8/F9 |

`ÂµM`是源header的mojibake；报告按microM理解该单位并保留原字符串证据，没有编辑源文件。Abemaciclib单药0.2µM在本header中得到比原scouttext更具体的支持。序贯header同样标0.2，但它没有单独列两阶段的concentrationfields；完整per-phase控制方案仍应以Fig4A认证，不能靠典型剂量补全。

响应metadata census：17times ×15wells = **255 response slots**，15numericcells、240sharedstringcells，全部坐标存在且有vnode，无formula。这里只检查node/type/presence；**没有确认responsefinite、数值scale、missing-string或有效范围**。不能把“坐标存在”写成全部有效观测。

Workbook没有独立biologicalrun、passage、batch或separateplate字段。Vessel名字中的`_2nd`可能是作者内部命名；它不证明有多少独立run，更不能在未取得其他导出时把它算作第二个可用训练/测试run。

## Response单位、重复与同run状态

本代理再次直接读取已存PrimaryXML的Fig4caption及Methods（投影 `PRIMARY_DESIGN_ALIGNMENT.json`），确认：

- Fig4B用Cytotox Green检测dead cells；**relative cell death定义为Cytotox-green-positive cells/total cell number**。WorkbookA2是per-well normalized high-green-cell metric，与此定义一致。它是无量纲人口水平归一化读数；表头没有给出百分数标记，不通过数值范围猜ratio或percent存储表示。
- Fig4B图注明确 **three technical replicates per treatment**。该文件每个condition的三个platewell与图注吻合，不能称三个独立生物实验。
- ImagingMethods说每biologicalreplicate包括three technicalwells，但不认证Fig4B独立biologicalrun数。当前取得的是一个vessel的十五条welltrajectories；这不是证明作者只做过一个biologicalrun，而是**当前资产仅提供一个可定位导出**。
- Imaging在0h扫描后加药、每3h扫描；**24h扫描之后**才两次freshmediumwash并加入下一处理，继续到48h。故每well rows6–14的0–24h prefix在换药前确实已可用；rows15–22的27–48h为后续读数。同一列明确连接同一well的earlypopulationresponse与laterresponse，不需借另一个assay拼时间。
- 当前export没有各自的rawCytotox count、totalcount、细胞周期或γH2Ax数值列。可用earlystate只限已经导出的per-well normalizeddeathhistory；不能把Methods提到“totalcount”就宣称rawtotalcount作为独立feature已公开在该表。
- FlowMethods的 **three independent experiments on differentdays**只属于flow；没有flowdatafile、pre-switchflow时刻或flow-sample→imagingwell/run连接。Fig4C是另一assay，即使同condition也不能自动给成像三独立run或早期molecularstate。

此外，24h wash可能移走dead/detached cells并改变分母/群体组成。因此这条relative-fraction曲线不是自动成立的累计死亡概率，也不能由`1−fraction`直接当survival或真实hazard。可研究测量读数的预测，但任何半群/质量守恒/不可逆累积杀伤约束须处理wash造成的measurement/populationreset。

## 当前最小任务与它不能回答什么

合法的最小任务定义是：**条件于此WM1366成像批次和既定export-defined药序，用同一孔0–24h的normalizeddeathprefix及已知Clad→Abe或Abe→Clad标签，预测该孔48h（或预先固定27–48h）的同一读数。** 它是phenotypicreadoutforecasting，不是分子虚拟细胞、一般drugtransition或临床治疗优化。两个药序各有三个technicalwell，只有两个固定actionprograms。

如果以后允许数值，仍必须事先选择一个诚实范围：

- 同well单轨迹prefix-only外推，可以作小型机制/软件压力测试；直接persistence、局部趋势、简单受控动力学和同historydirect模型应共享信息。
- 若训练中使用另一个technicalwell的同药序future，而test只留一个well，测到的是**同批次已知药序的technicalreplicate泛化**。它不等同于在24h未知future时做前瞻forecast，也不等同于unseenbiologicalrun或unseenorder预测。训练future来自已完成历史任务的时间含义必须写清。
- Whole-orderholdout只有两个序贯conditions；单drugcontrols的第二阶段处理尚未由图形scheme核验，不能假装有完整state×nextdrug菜单。任何一般化性能或uncertainty都应承认这个极小范围。

当前没有一个可支持用户核心机制主张的独立任务集合。技术孔、17timepoints、255cells和多个曲线端点不是独立researchtasks。选择第二药的adaptivepolicy也未在原实验中执行；仅事后选择两个已测program之一不能证明智能体反馈改善研究过程。

早期扫描与后期扫描属于同一Incucyte运行；没有认证querycost/可节省的独立assaybundle。可以研究一个预先限定的logicaloracle信息分配，但不能把少揭示几行存档当实际减少湿实验或仪器时长。当前不为凑agentheadroom另加LLM/API/search。

## 精确资产缺口与资源决定

1. **独立imagingruns**：至少更多原始vessel导出、biologicalrun/batch/passages和相同arm身份，才能做held-out-run预测或有意义的参数/程序迁移。Flow三天和MeWo筛选三replicates都不能填此缺口。
2. **完整Fig4A处理设计**：尤其单药/DMSO控制在24h wash后的操作、每phase确切dose和duration；当前预算不允许图像请求，缺口如实保留。两个orderlabel与24h switch已认证，不推断未列出的schedule。
3. **早期分子state资格**（若要主张此模态）：数值flowdata、其相对switch的真实时点、condition/run配对。缺此项不禁止现有deathprefix任务，但禁止molecular-state增益主张。
4. **分母/群体mass信息**（若要主张deathprocess而非读数预测）：rawcount或可解释的wash/removal/segmentation记录。当前只normalizeexport，不用累计hazard解释替代。

**本次决定：`QUALIFIED_SINGLE_EXPORT_WELL_TRAJECTORIES; NO_BIOLOGICAL_RUN_HOLDOUT; NO_MODEL_FIT_AUTHORIZED_BY_THIS_AUDIT`。** 保留这个小资产用于来源/机制对照；对世界模型、researchagent、继承、联合收益及RSI保持NOT_TESTED。若后续没有独立run/更多actioncontexts，停止本来源上的框架扩展，而不是用技术重复扩样。此限制不否定该原文药序现象或所有phenotypicforecasting任务。

所有原始body、receipt、header/time/celltypeprojection和本报告在本log目录；researchscript在 `research/intervention_dynamics_renewal_20261022/`。没有拟合、数值outcome访问、额外数据请求或交叉辩论性能结论。
