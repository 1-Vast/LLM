# 实际执行与故障记录

1. 读取现有档案、R196/R197撤回及原始结果/协议，定下BRIEF和有限预算；不重跑效果。
2. native web/search工具未暴露，使用已安装sources.py学术API。首个S1调用因missing 00_index在本地退出、未发出请求；init_survey.py后成功执行S1-S4，继而T1。原样查询在00_index，原始响应在raw。
3. 新发现3篇设计负载原文，经reference_library.py record/paper入库；HTML文本抽取首次拟用bs4，但环境无该模块，改用Python标准库/库text工具，无依赖安装。
4. 3名真实子代理分别做候选前结构侦察、证据审计和新上下文独立质疑。初判后两次实质修订，最后仅编辑一致性校正；各版本和原始批评保留。
5. 论文明确链接作者traca代码。库工具首次rename遇WinError32，第二次下载成功，commit30eb685ac6725efd3cbc15abdd5c53998182a0be，79文件。未执行代码、安装或取数据，许可unknown。
6. library verify前后均无error/warning；最终33篇、24份正文、2份作者链接代码。5条查询不是全面查新，下载不等于阅读或复现。

训练、效果实验、数据/权重下载、src晋升、外部模型桥接均未执行。当前证据不能认证独有算法、药理机制或净决策收益。
