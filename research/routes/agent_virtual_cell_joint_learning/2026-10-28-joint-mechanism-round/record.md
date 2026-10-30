# Agent×虚拟细胞共同学习：证据约束的新一轮

日期：2026-10-28（Asia/Shanghai）。状态：active，目标尚未实现。

## 研究简报与预算

负责人保留科学问题、算法、指标、实验设计及裁决；DeepSeek Harness辅助角色只处理明确规则下的资料、元数据、复算与格式。生物场景为药物发现中的细胞背景、剂量、时间及干预历史下的功能决策。目标是简洁且有可区分算法增量的共同学习原则，不以架构堆叠、文件存在或工程PASS作为成功。

本轮先查整个历史档案和最新证据，再比较多个问题与跨领域原则。整轮最多6次问题限定的检索扩展（所有子代理共享；前2次留给事实与结构探索，2次用于必要条件和方法，1次质疑，1次最终先例检查），每个初始候选最多2次实质修改。最多新增下载2 GB，不新增付费API支出；现有订阅工具费用未知，不记为0成本。最多一个冻结假设的最小实验及一次独立复核；CPU累计上限60分钟，科学GPU训练0次，湿实验0次。原始/sealed/confirmation及未授权盲态结果不读取；元数据资格先于效果检查。若后续现行协议已授权且需读功能值，将明确冻结输入、估计对象和边界，不默认为全项目解盲。

实验与代码仅在本episode下；不改src或tools，除非科学独立验证与明确晋升决定均已满足。使用已存在的maestro环境，不安装或修改全局环境。

## 本轮优先决策

1. 哪些历史阴性是科学否证，哪些是资格、功效、实现或比较错误？不只延续最新分支。
2. 2025—2026年原始论文及较早最近邻中，有没有改变可辨识性、数据条件或最小机制的证据？
3. 对真正有用的功能决策，药物×细胞交叉、剂量/时间、靶点或遗传参照、独立功能终点与重复分别够不够？
4. 哪个最小观察能区分所提共同学习机制与静态模型、固定实验设计及标准主动辨识/决策方法？

## 事实与读取边界

现行项目入口：README.md、log/STORAGE_POLICY.md。log/RESEARCH_REPORT.md是维护的全局综合；冻结来源不改写。既有大量未提交文件属于用户工作，不清理、不覆盖。项目历史及新产物先独立核实再采纳。

当前DeepSeek文件入口已有DS005—DS008。已有连接报告记录本地Host未认证业务接口401；该历史证据不能证明当前活会话或已派发。尚未取得本轮实际接收receipt；禁止从凭据、内存或浏览器存储绕过认证。继续检查受支持载体和现行任务，不因局部连接缺口停止核心研究。

## 用量与团队

root：当前模型继承，effective_model未由运行元数据证实。模型/子代理有效配置只以工具回执为准。预算上限与实际用量分开记录，未知token/费用为null。子代理分工、来源、冻结候选、异议及判决将随实际产物追加，协调者独占共享索引写入。

## 用户补充的已验证Harness路径

用户本轮提供D:/Rice/代码/computer_agent.py（harness_cli、prepare_harness_home）、D:/Rice/产出/named-title-context-20261028/run-harness-review.py及独立profile样例。该新证据取代“缺已认证GUI接口就不能调用”的旧前提：可以用安装CLI headless --json -；不再探测匿名HTTP。为当前任务创建全新workspace及DSH_HOME。已有本地凭据只在内存和子进程环境传递，不复制至本仓库、runtime配置或日志，不打印。

应用户要求新增本轮Harness预算：最多3次调用，先1次小任务，核接收回执/结果后才允许后2次；每次timeout180秒；总输出上限6144 tokens（1024+2560+2560），stdin总上限36000 UTF-8 bytes。使用已跑通的deepseek-flash、thinking disabled、指定DeepSeek Messages baseURL；禁用工具、自动重试、备用后端、会话自动命名和持久化。按官方2026-10-28页面峰值flash价保守估算，上限预算USD0.10；该金额是预算，非已测成本。CLI若不暴露输入token/费用，记unknown并不宣称硬计费上限；本轮请求数量、输出maxTokens、stdin字节、wall timeout可由wrapper严格限制。结果不确定不重试。DSH_HOME位于项目外临时目录，所有交付与审计保存在research/deepseek/tasks的新任务目录。

用户后续更新目标强调2025—2026顶刊原始方法；本轮继续当前范围，不将顶刊等级当科学验收标准。

## 本轮实际推进与收口状态

上一goal turn归类progress：取得原始JATS/固定代码及DS009/DS010真实回执，改变了可执行路径与数据资格判断。本次继续完成DS011并拒收实质计算错误，完成Q001独立实现核对、C1 v1独立质疑、一次v2发展及独立代数审查，并取得论文链接的2025原始发布包。目标保持ACTIVE / NOT_ACHIEVED；本轮预算收口不等于整个目标完成或暂停。

检索PASS1原始方法（primary_evidence，4query+8访问）、PASS2结构探索（structural_scout，4query+6原文尝试）、PASS3顺序给药资源与PASS4精确数据资格（root，原临时检索返回未完整持久化，具体URL/获取收据及限制保留，不虚构完整query列表）、PASS5独立质疑（4query+6原始访问，sources/challenger）、PASS6最终限定刷新（2arXiv query、Zenodo官方record1次、原ZIP1次、原始HTML3次，共7公开请求）。6/6pass已使用；无全域穷尽、引用链全覆盖或首次声明。PASS6两条查询各只取10/21、10/44条，不以截断召回当无先例。

实际科学效果实验0、GPU训练0、湿实验0。Q001仅参数资格；独立有理代数检查仅核数学实例。Q001主程序记录CPU秒，整轮累计CPU及订阅token/费用未暴露，记unknown，不捏造为0；没有大型训练/模拟。公开下载在各收据记录字节（本轮外取原件为MB量级），未重新下载受限Dryad/SI、未安装环境。无需把未用效果实验额度用完。

Harness预算已封账：3/3调用，26,935stdin字节、3,676事件输出tokens，0重试/备用后端；实际用量及账单unknown边界在harness_usage.json。DS009验收，DS010有保留，DS011关键计算拒收。旧“缺已认证GUI”状态仅为早期载体历史，当前headless已交付，不再作为阻断理由。默认资料主线和具体断点已更新CURRENT_TASK/MAINLINE，没有新后台任务。

本次实际新句柄：/root/mechanism_development_v1 请求gpt-6.1-sol/high（v1及一次v2）；/root/independent_challenge_v1 请求gpt-6-astra/high，fresh none上下文，先保存初评再读v2；/root/terra_stage_governance_2 请求用户指定gpt-6.1-terra/high并实际使用organize-files，仅写stage_synthesis。所有effective_model均未被服务元数据确认，记录unknown；请求接受不等于已验证后端型号。前轮primary_evidence、structural_scout、terra_stage_governance产物保留；旧mechanism_development句柄本次已缺失且无文件，不计完成，由新句柄接续，未宣称后台仍运行。

root对Terra综合进行独立内容审读，核原始方法、Q001身份与独立结果、DS011拒收和v2适用边界；不靠16条链接存在作科学验收。主要结论/下一研究决定见report.md；没有src/tools晋升、提交、上传、物理清理或全局配置改变。项目索引由root统一更新；reference库核验仅认证清单完整性，不认证机制成立。
