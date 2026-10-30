# Agent A第一轮：两个边界已澄清，尚未得到新算法

2026-10-28。完成3个实际独立角色的资料/结构/质疑工作、指定论文定点核读、官方数据可访问性核查及一次精确代数检查。长期研究目标未成立，保持active。用户最新要求转向从该论文的细胞—语言结合方式出发迁移CV/NLP原理，后续见[新轮brief](../2026-10-28-agent-a-cell-language-mechanisms/BRIEF.md)。

最重要的新证据：DrugReflector已经实现真实表型反馈修改转录组签名并选择新药，故不能把这个宽泛闭环作本项目首创。用户指定论文的实验反馈修订的是候选评分规则，所读方法没有在该轮重训练CellQ；对照边界和有用思想见[分析](USER_PAPER_ANALYSIS.md)。官方OMIX017117当前受控且不可下载，并非已取得数据；没有启动真实训练或论文复现。

M2具体构造的相同源响应、相反最优程序和.25最坏世界期望simple regret成立。但新取证直接测了候选AB的值，强基线同样达到零遗憾；没有显示未查询程序或跨背景收益。[v2](CANDIDATE_v2.md)已吸收动作证据、span仅充分、功能反馈不等于整核等质疑，停止该版本的主算法主张。反例与等价检查见[实际结果](exact_results.json)，仅精确代数，无生物效应或CI。

执行exact_cohort_check.py一次，maestro环境，计算wall .3334s，CPU .2656s，peak working set 37,339,136 bytes；命令返回wall .9143s、exit0。源代码与[协议](PROTOCOL_exact_v2.md)均保留。没有科研重跑、依赖安装或src晋升。

初始候选有真实独立审阅，见independent_challenge.md。修订后续审和指定论文新方向的续审各遭401，未产生新复核文件；后续机制不据此声称通过独立评审。原始错误不复述密钥片段。

主题检索8/8（结构2、证据2、协调者2、独立质疑2），另独立质疑1条已知标题定点查询；用户指定论文扩展3条定点query，打开/API元数据与官方GSA访问另计。引用库登记已完成，实际命令见library_registration_log.json；与下一轮合并的最终库收据见../2026-10-28-agent-a-cell-language-mechanisms/library_verify_final.json（72唯一论文、63正文文件，errors/warnings均空），未把下载/入库当通读。对方M1进程曾观察到PID13592、后PID5980；两次时间点均未见最终结果，后者已退出的事实不等于对方研究目标失败，不介入其运行。
