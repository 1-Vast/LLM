# 证据、来源与访问边界

研究日期2026-10-27。O=实际核查的本地记录；P=原文相关部分；A=摘要；R=题录。作者报告、项目观测、推导和计划分开。本轮没有训练/模拟/生物效果实验，纸面例子不登记为实验通过。

## 项目证据

O1—O4的精确结果、单位、SHA256和最终审查定位见[latest_evidence.md](latest_evidence.md)。本轮证据代理实际读取JSON/报告/挑战，协调者读取其证据表和关键边界；独立机制质疑者再次读取结果必要字段与构造代码。不是两次生物复现。

- **O1 R196v2**：`../2026-10-27-c130-audit/r196_v2.json`、`report_r196_v2.md`、`challenge_R196_v2.md`最终§5。正点估计/CI与设计MDE、wall gate并存，最终inconclusive。共享65药的多分割不充独立药物/生物重复。
- **O2 R197v2**：`../2026-10-27-q-structure/r197_v2.json`、`report_r197_v2.md`、`challenge_R197_v2.md`最终§5。随机条目插值的大增益是描述量；覆盖门混淆可辨识性，但独立MDE门仍失败。经验分半可靠性不支持旧0.868认证。
- **O2a Q构造**：同目录`r197.py` build_q约207–310行及r197_v2.py导入；Q=full(ca,p)−full(ca,q)−full(cb,p)+full(cb,q)，full来自cell×condition×barcode聚合。该线性关系只从聚合endpoint到Q。尚未构建/检验实际A_T的rank或rowspan，更未复算增益的闭包份额。
- **O3 R199关系资格**：`../2026-10-27-innovation-scouting/conflict_signal/stage0/real_run/relations_check.json`和record_p0a_check.md。135候选中全门仅2，覆盖2/171；原stop不改。R199执行期loader等修正与未执行阶段保留。
- **O4 Q0**：`../2026-10-27-core-module-design/qualification/q0.json`、report_q0.md。无公平source→target，O’Neil只有条件内部开发资格。其完整确认大规模门是为该强主张设计，不能强加给所有窄预测任务。
- **O5 历史边界**：本轮通过现有record和上轮evidence_notes复用I002/线性编辑等价、BATCHIE元数据/重复缺口、R187无优势、R192功效不足、A2/A3/A4/A5的实际阶段。并未逐份重读所有旧DECISION或跑旧脚本。“旧action_substitution误差改善而决策未改”只可作历史二级摘要，报告不使用其数值作新事实。

## 本轮入库一手来源

共享资料库绝对路径`D:/MAESTRO/reference/`。下表hash为库中实际HTML的前12位；JATS是原始独立文件，另有receipt与完整SHA256，格式不混计。P级只表示所列部分读过，不是全文及补充全读或复现。

| ID / paper_id / 身份 | 读取定位、级别与hash | 支持的具体主张及不能推出的结论 |
|---|---|---|
| **P-EX1** `doi-10.1038-s41467-026-72903-w`，Bernett等，DrEval，Nature Communications，2026-05-12 | P；原始`primary/PMC13168506.xml` Sec4“Models learn limited biological signals beyond drug means”、Sec7“Weak generalization across datasets”、Sec14“Data splitting and hyperparameter tuning”；Sec20部分。协调者补读Sec4前2600字符与Sec14全文；Sec7通过本轮实际web读取。库HTML`caa1e09a2385`，h1已核 | 在其单药任务里，均值和调参树模型强、药物/cell依赖与跨研究偏移重要。不是对组合Agent、所有深模型或某一生物机制的否证。作者将跨study差异主要归技术，不以此证明完全无生物差异 |
| **P-EX2** `doi-10.3390-genes17070816`，Sun等，A Neural-Network-Free Calibration…，Genes，2026-07-17 | P；`primary/PMC13409800.xml` `sec5-genes-17-00816`“5. Method: AMM-SimWMag”前1900/此前约2200字符，`sec14`“Limitations”由前半轮读取并补核前2200字符；库HTML`d92e01b1e99d`，h1已核 | 控制依赖幅度、方向和affine校准是必须比较的简单对手；single-perturbation LOCO/log-HVG，不覆盖组合/剂量/轨迹。论文中部分深baseline用默认设置，不能推断其普遍最优，也不能将作者reported结果当本项目复现 |
| **P-EX3** `doi-10.1186-s13321-026-01242-1`，Cheng等，Unified heterogeneity-aware benchmark…，J Cheminformatics，2026-06-30 | P；`primary/PMC13587485.xml` Sec8“Dataset collection and preprocessing”先读前4200/4927字符，末段另补读；Sec9“Synergy score calculation method”全文；库HTML`5b3ce79d3d80`，h1已核 | 多资源/技术重复/不同协同定义处理重要；其随机triples5折不等于strict cold transfer。原文13dataset/454794triples等为作者报告，未独立核算。不同模型还有其原方法预处理差别，不称所有信息完全一致 |
| **P-EX4** `doi-10.1016-j.cell.2012.03.031`，Lee等，Sequential application…，Cell2012 | A；P4_1原始Europe PMC完整摘要，XML HTTP500，PMC恢复HTML是验证码；库abstract_only，无全文hash | 直接先例：时序EGFR抑制、状态/信号重接使后续genotoxic drugs更敏感。“顺序影响细胞状态”已不是空白；摘要不能判洗脱恢复、A′迁移或最少见证是否已解决 |
| **P-EX5** `doi-10.1371-journal.pone.0063583`，Chan等，A simple high-content cell cycle assay…，PLoS One2013 | P；`primary/p4_challenge/PMC3656927.xml`摘要、Compound Treatment、Comparison of Assay Formats、Time Dependence of Inter-assay Format Variation；协调者补核后两节前2100字符。库HTML`74b0cba5f1ca` | 真实平行板多读出近邻；ATP/细胞数映射依药物、时间和背景变化，有非单调现象。支持M3共同映射必须可拒绝，不支持本项目已校正这些差异 |
| **P-EX6** `doi-10.1016-j.chembiol.2017.10.010`，Vasta等，Quantitative, Wide-Spectrum Kinase Profiling…，首次在线2017-11-22，正式issue2018 | P；`primary/p4_challenge/PMC5814754.xml`摘要、参与/kinase activity对应及ATP干扰章节由独立质疑者读取；库HTML`25ff9c2bd083` | 活细胞参与与biochemical affinity有区别，参与测量不是新概念。并非完整跨细胞存活×参与×rescue资源；年份按在线/issue分列，不能把在线日期当issue日期 |
| **P-EX7** `doi-10.1016-j.mcpro.2025.100963`，Glocker等，A Probe-Based Target Engagement Assay…，MCP，2025-04-03 | P；`primary/p4_challenge/PMC12076712.xml`摘要、Experimental Design and Statistical Rationale、Discussion。协调者与原生web定点核Discussion“complex-specific”段；库HTML`6e1a9969161d` | 参与读数平均不同conformation/activation state/complex；细胞进入、分布等可影响结果。相同部分平均参与不认证完整干预实现，不自动识别下游规律 |

P-EX4/5/6属于更早的直接新意威胁，故保留；最新证据目标窗为2025-01-01—2026-10-27。P-EX6第一次issue归年写作2017的过程表述已在此与原稿中澄清为2017在线/2018issue，不删除原始过程。

## 旧库与跨领域原则

本轮发展沿用上一episode已核的BATCHIE、PDTSyn、DECANT、AlphaEdit、LOGICZSL、Compositional Behavioral Semantics、Generalised Transportability、Task-Aware Exploration、SPI-Active、Poke and Strike及contrastive AL。精确旧读取位置见`../2026-10-27-core-module-design/evidence_notes.md`与本轮结构scout稿；当前协调者未把它们全部重新阅读。

- BATCHIE已覆盖细胞条件、后验反馈、整板设计和决策距离。反馈+分歧+选板本身无新意。
- PDTSyn已有共享基与细胞特异系数；DECANT转录原型不是参与和独立药效。
- CV概念逻辑、NLP局部编辑与RL行为抽象未给现有数据新增混合/功能/因果信息；旧等价覆盖不能改名重开。
- 机器人系统辨识启发M2的真实激发，而不是提供可直接复用到破坏性、无reset、异质群体细胞的定理。图同步对M3是来源类比；本轮未取得/读取其原始定理，不引用其理论认证。
- 线性可估性、GLS、GP、PKPD、测量校准和最优设计都是成熟原则。候选的潜在贡献在具体未解问题/能力、最小可识别测量设计与真实迁移，不以领域换名成立。

本轮其他摘要/题录线索包括2026 proteome-guided degrader toxicity（10.1038/s41589-026-02347-2）、成像与CTG（10.1016/j.slasd.2026.100337）、U-Pert（10.64898/2026.06.30.735555）。未逐篇方法核查/资源准入，不作为推荐已能实现的证据，也不以下载缺失证明没有公开资源。

## 作者代码

DrEval正文Code availability指向`https://github.com/daisybio/drevalpy`。本轮先读取公开tree元数据确认265文件约9.3MB，无识别出的数据/权重blob，再用reference_library.py存入`reference/code/daisybio-drevalpy/c5a7274e9c84/`，完整commit `c5a7274e9c843dc4f24797986446d39d22124195`。当前development分支，不知是否论文对应提交。实际读取README、MIT LICENSE、experiment.py入口/函数声明；不是复现或完整代码审查。主要入口为experiment.py及cli_run_cv.py，未执行。

其余新论文源码核查不完整，清单准确保留not_verified；没有把论文中的几个GitHub链接都称已验证源码。DrEval另两个pipeline/preprocessing链接与Cheng论文疑似子路径链接只作线索，本轮未完成对应版本/内容核验，不宣称全部官方软件已收齐。

## 查询、原文与工具可用性

主题新增查询**14/16**，继承前两episode报告的16+5=21条；其中早一轮4条原样查询未留存的历史缺口不由本轮补造。P1结构4条在sources/P1_structural/；P2四条、P3两条在search/00_index/searched_queries.tsv；P4四条在search/p4_challenge/。本轮14条原文均实际落盘。查询总数与独立研究数量不同，跨query也有重复命中。

P1各total/returned：53/20、85/20、60/20、1/1；P2/P3：49/49、61/61、6/6、868/80、1124/60、30/30；P4：2/2、66/15、11/11、15/15。P2d/P3a明显噪声高，788/1064条未展开；P4近24个月query混入2024-10-27以后基础线索，仅15/66。未全面覆盖OpenReview、引文链和所有顶会/期刊，不做“查新无人做过”结论。

开始时没有原生web/search工具，使用Europe PMC/arXiv公开API；中途工具更新新增web，之后仅open已知官方页、find原文相关段，没有新增主题search。Nature页转cookie认证、MDPI429、一次PMC显示captcha均记录并停该网页，继续使用此前合法保存的原始XML/已核HTML；不绕过访问控制。PMC12076712与DrEval原生web成功。来源宿主不同访问结果不能混成全部全文可用或全部失败。

全文获取和已知DOI元数据查询是定点来源核实，另留receipts，不算扩大主题。XML实际6份成功，Lee2012另有失败/验证码证据。库入库HTML6份，与XML分别计数，不重复算独立论文。一次HTML text误用--pages被工具拒绝，未据其声称读到正文；一次PowerShell内Python字符串转义语法失败已用无转义表达式重读，未执行科研计算。

开始库33篇/24正文（22HTML+2PDF）/2份官方代码；本轮增量7篇，其中6份HTML正文、1仅摘要，新增官方代码1份。最终40篇/30正文（28HTML+2PDF）、3 pending、6 restricted、1 abstract_only；3份官方链接代码快照。verify的errors/warnings空。文件存储/哈希/源码MIT许可都不等于方法效果、机制或临床收益认证。

## 主张状态

- 已知：最新限定结果、Q的实际构造、已核原文中的具体操作和限制。
- 推断：真实闭包可能影响R197解释；静态终点缺失的信息需靠相应真实测量；标准模型对一般操作有强覆盖。
- 待验证：未识别方向的源迁移、历史签名复用、桥后独立功能决策改善、参与局部充分性及跨背景共享响应。
- 不主张：闭包已解释大增益、三/四项算法首创成立、已识别药理因果机制、已完成外部确认或RSI。
