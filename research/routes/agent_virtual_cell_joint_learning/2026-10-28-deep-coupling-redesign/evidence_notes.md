# 证据、来源与查新边界

2026-10-28，Asia/Shanghai。主题检索12/12已用完；定点打开已知论文/版本、原文恢复与官方README另记，不作为新主题查询，也不用于无限扩展。搜索原文收据保留在sources/，合并查询账本为[queries.json](queries.json)。这是一轮有界发现，不是系统穷尽查新。

## 当前一手来源与实际阅读

下表P均表示相关部分，不能解释为通读、复现或生物适配已证。原文件按reference_library.py入库；manifest中的reading_scope保留角色与具体范围。

| 来源 | 读取范围 | 支持本轮哪一判断 | 未建立什么 |
|---|---|---|---|
| [CellForge / AI Scientists for Building Virtual-Cell Models，2508.02276v3](https://arxiv.org/html/2508.02276v3) | 生物scout：Formulation/Ideation/Execution、Discussion部分；协调者：Execution全文2286字符，h1题名核实 | Agent改表示、loss、训练及修代码已有先例；当前版本湿实验前瞻闭环仍属后续 | 不代表所有VC Agent都仅编排，也未复现其计算效果；v3题名与旧alias不同 |
| [VCWorld，2512.00306v2](https://arxiv.org/html/2512.00306v2) | 生物scout：§3.1–3.4部分 | KG/实体表示、正负案例检索和DE/DIR推理已有 | 所读方法没有认证真实实验回写闭环，不以局部阅读证明全篇或全领域不存在 |
| [PRAXIS，2609.29221v1](https://arxiv.org/abs/2609.29221) | 生物scout：PDF p14、p16–17 | 此版本Agent的数值/feature修改边界明确，experimental feedback列后续 | 不认证其他版本或所有框架的边界 |
| [AROMA，2604.20263v1](https://arxiv.org/html/2604.20263v1) | 本轮scout复用并核§3.5；早前部分§3.1–3.5 | 离线标签/格式奖励的GRPO已存在 | 不把离线奖励当真实取证反馈；未读全附录 |
| [BATCHIE，PMC11696745](https://europepmc.org/articles/PMC11696745) | 生物scout：Sec3、Sec5前段、Sec42；复用既有原文 | 含cell条件、后验更新、实际viability及受板约束的主动选择 | viability测量不直接等于死亡；本轮无复现和新外部确认 |
| [Diffusion Forcing，2407.01392v2](https://arxiv.org/html/2407.01392v2) | 结构scout：§3/3.1–3.2、Alg1–2部分 | 联合action/reward/observation和真实历史条件化已有 | 视觉/控制结论不能直接转成药理事实 |
| [History-Guided Video Diffusion，2502.06764v2](https://arxiv.org/html/2502.06764v2) | 结构scout：§3–4 Eq2–4、§5开头 | 独立时序噪声及history guidance的具体运算 | 没有药物干预可执行性保证 |
| [Diffusion Forcing Planner，2606.11019v1](https://arxiv.org/html/2606.11019v1) | 结构scout：§3.1–3.3 Eq1–8 | 历史退火、时间相关guidance的规划近邻 | 自动驾驶动作与培养物给药的控制权限不同 |
| [TTT-E2E，2512.23675v1](https://arxiv.org/html/2512.23675v1) | 结构scout：§2.1–2.3 Eq1–6 | 内层更新/外层优化是直接元学习近邻 | 本项目尚未通过原用户的独立决策与迁移门，不启动该线或RSI |
| [TD-JEPA，2510.00739](https://arxiv.org/html/2510.00739) | 协调者：§3.1全文3720字符、§3.2全文3344字符；challenger：PDF局部Eq5–9/Alg1 | 策略条件长期表征、单步TD与目标复用已有；使用(s,a,s′)数据 | 不是未配对生物快照上的现成解；实验/全证明未读 |
| [Control Realization of Schrödinger Bridges，2610.17965v1](https://arxiv.org/html/2610.17965v1) | challenger：II-A、Cor1、III-C/D部分；协调者：II-A前3000/6329字符 | 已知确定性非线性f、离散输入扩展及控制实现；限制M1宽泛新意主张 | 不能只用“随机药效”一词认证本候选新颖，未核高维未知核的覆盖边界 |
| [KoopCell，2609.33350v1](https://arxiv.org/html/2609.33350v1) | challenger：§2/3.1、A4.2/A4.4/B1部分；协调者：§3.1前3000/11721字符 | 稀疏未配对分布下弱传播估计与表示交替学习已有 | 未认证其可辨识所有受控药理算子、有限预算任务收益 |
| [DisKO，2609.34629v1](https://arxiv.org/html/2609.34629v1) | challenger：§3.1/3.2、G3部分；协调者：G3前2400/4523字符 | 分布空间学习及观测自主演化的充分性/不可辨识边界已有 | 分布拟合不认证单细胞机制或任意干预可组合性 |
| [DR策略评价，1511.03722v3](https://arxiv.org/html/1511.03722v3) | 协调者：§3.3前2500/2717字符 | 一步DR Eq8、独立评价要求是M3直接先例 | 不把一步均值校正称完整动力学更新或无条件序贯DR |

challenger另读committor/DGA/active importance sampling/漂移扩散可识别性等直接先例，具体段落和失败恢复见[sources/challenger/READ_RECEIPT.md](sources/challenger/READ_RECEIPT.md)；未全部入共享library，不伪造完整收集。它们导致撤回“前后向残差本身产生新信息”的v1主张。结构与生物来源收据分别见[sources/structural/READ_RECEIPT.md](sources/structural/READ_RECEIPT.md)、[sources/biology/ACCESS.md](sources/biology/ACCESS.md)。

## 当前项目证据的层级

- 已核的历史约束与失败解释：本轮复用[blocked复核](../2026-10-28-blocked-conclusion-review/report.md)与[功效范围报告](../2026-10-28-decision-power-scope/report_scope.md)。451/500的天花板、A22校准对象和旧rank规划范围不能改名重启；新N1/N2仍是计划，不是已执行的成功证据。
- 最新外部Agent审计：[R203-X2报告](../2026-10-28-az-export-coverage/report_x2.md)的结论与覆盖表已读。协调者未复算原始ZIP/计数，也未重新判断旧68键或Q1资格。其301、161等是审计报告结果，不是本轮新效果。QC上传日期不等于处理或独立培养日期。
- 原AZ论文[PMC11061612](https://europepmc.org/articles/PMC11061612)的处理、重复、部分凋亡验证在先前复核原JATS中已读；本轮只引用该核查及X2映射，不新下载原始实验数据。当前未取得正交功能numeric记录，不等于原实验未做，也不等于必须新湿实验。
- 构造例、方程展开、验证计划与反例是推理或设计，未作为科学实验运行；三项机制均没有本轮效应量/CI可报告。

## 访问与覆盖缺口

1. 两次协调者主题查询偏宽且有噪声；未宣称查完所有引用链。P3第一批原始响应是response-only字符串；查询文字从当前任务连续记录恢复，过滤器未按原始请求完整落盘，不伪称请求可逐字重放。
2. OpenReview TD-JEPA PDF下载返回HTML验证页，library工具拒绝保存为PDF；已用官方arXiv HTML恢复原文。该失败不是论文没有公开全文。原失败响应为sources/coordinator/tdjepa_open_raw.json。
3. TD-JEPA官方GitHub README已由challenger取回，raw重试在sources/challenger/tdjepa_readme_retry_raw.json；确认作者链接与arXiv入口，未下载/检查全部代码或运行。README中的许可声明不是LICENSE全文核验。协调者的暂存对象在上下文延续后不可读取，未冒充已保存另一份原始收据。
4. 本轮新增10个唯一paper ID及VCWorld一个额外版本，实际新原文11 HTML；无新增代码快照。共享库最终62篇唯一论文、54份正文文件（实际47 HTML、7 PDF，含额外版本），官方代码快照仍3份。verify原始状态中的45 downloaded_html是按论文状态计数，不应与含额外版本的文件数直接相加；errors/warnings均空。见[library_verify_final.json](library_verify_final.json)。
5. 官方模型文档定点打开发生重定向，只读到通用导航，未获得独立当前模型标识确认。代理requested设置来自实际调用；effective均unknown。未使用CLI/API模型桥接或改全局设置。

## 最接近工作的最终判断

M1一步投影被最大熵控制覆盖；M2固定函数/线性版本被受控EDMD及输入设计覆盖；M3一步分数被DR/TMLE及重要性加权覆盖。它们不因用于细胞就自动成为新算法。报告提出的研究空间是受实际生物观测约束的有限反馈能力：是否有新的可实现规划、主动辨识与迁移方法。当前尚无新算法、药理机制、净独立决策收益或跨任务迁移的验证结论。
