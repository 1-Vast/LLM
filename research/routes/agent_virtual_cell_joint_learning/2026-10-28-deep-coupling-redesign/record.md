# Canonical research record

- Episode: 2026-10-28-deep-coupling-redesign；date basis Asia/Shanghai。
- User objective: 在现有证据上扩展较多有希望方向，提出至少三个具体机制，并提高虚拟细胞与Agent共同学习的深度及实质差异。
- Deliverables: [report.md](report.md)的九方向/三机制；[candidates_v3.md](candidates_v3.md)为最终限定规格；[evidence_notes.md](evidence_notes.md)记录来源、近邻和未读范围。
- Status: design_research_completed_with_conditional_recommendations；原核心目标未成立，未恢复/修改goal。不因完成报告而标记科研成功。

## Candidate ancestry and decisions

M1：v1的目标桥受不可达支持/标准控制质疑；v2改为有界倾斜和保持随机药效核的反向KL可执行投影；v3按复核明确τ>0等条件。2/2保守修订计数。有限式正确，最大熵控制直接覆盖；推荐作为具体能力研究，未给新高维求解器或效益。

M2：v1未配对弱算子过宽，被KoopCell/DisKO与系统辨识近邻收紧；v2改为任务相关函数、主动干预激发及受控弱矩；v3锁定cohort内固定随机化或正确联合矩。2/2。推荐主线，但固定φ/线性版本没有独有算法新意。报告补明完整动作标签不应故意聚合丢弃。

M3：v1 committor/前后向残差没有独立信息，撤其主张，不凑第四机制。v2改成真实功能的策略影响分数，连接targeting与分配；v3补错设偏差平方、有限logit解与功能层范围。2/2。只作为支撑假说，当前未更新完整动力学。标准DR/TMLE/加权重训覆盖保留。

历史I002/I-CD1/CL1/CL2/CL3及R201停止档不重置。新机制不是旧S-add、线性latent edit、分歧采样或伪RSI的改名。没有恢复旧阈值、减少旧分母或偷换未见任务。

## Actual team and independence

1. /root/deep_structural_scout：requested gpt-6-astra/high，fork none，effective unknown。独立结构初稿先存initial_structural.md；主题查询2。
2. /root/deep_biology_scout：requested gpt-6.1-sol/high，fork none，effective unknown。initial_biology.md先存，未接协调者候选；主题查询2。输出biology_scout.md。
3. /root/deep_mechanism_challenge：requested gpt-6.1-sol/xhigh，fork none，effective unknown。收到冻结v1、brief和原始来源入口，未收到scout/协调者说服性结论；initial_challenge.md先存；主题查询4。完成independent_challenge.md。
4. 协调者主题查询4。最后v2复核已接触前次质疑和解释，属于有曝光有界复核，不称新盲评；0新查询。recheck_v2.md确认公式条件并保留三机制假说、零一般算法新意已成立的意见。
5. v3为协调者落实已明确的公式/前提修正，未再次独立审阅。不循环寻求正判，不用代理一致性代替来源。

## Scope and evidence changes

最新X2导出覆盖报告生成后，本轮读取结论及覆盖表，撤“当前无重复记录”说法。没有独立复算X2计数或改变Q1资格；独立培养/功能numeric仍待映射。旧T1不可达门与A22不合格解释保留，既不泛化全框架失败，也不充成功。

本轮新主题查询12/12；已知先前三轮35+共同学习16=51条保留为祖先记录，其他Agent的R201-P/R202查询未假装汇总。定点读源另记。未量得token/cost总量，不估算为已测。

## Boundaries and verification

只写本episode、增量reference manifest/README及research索引。无数据/权重下载、依赖安装、科研模拟/训练/效果实验、生产代码改动/晋升、全局记忆改写、goal变更、外部消息或Git发布。

最终验证是JSON解析、文件/链接/版本存在性、有限证据快照及reference_library verify；不是药理效果实验。实际检查结果写入artifact_checks.json。不存在可报告的本轮科学效应CI。

后续只在预先冻结、同信息同物理/计算预算、可达的实用门下检验；完整范围见report.md。元学习/RSI须待独立决策和迁移成立，再与等预算普通程序搜索比较。
