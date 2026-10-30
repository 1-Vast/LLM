# Q1.v1.1：执行前澄清与冻结

2026-10-29。唯一H、A/B/B'、起始四叶、0.02宽、2048叶和停止条件全部沿用candidate_q1_v1.md。当前未执行数值实验。独立初判与细核已收到，允许本次必要性质检验，未推荐主机制。此为初稿后的第一次实质修订，不能按结果再修输入。

1. 数学：bin内余项是平均KL，只有这个平均不超过H(q)。r是各posterior坐标的上界，不是概率向量；单点KL不保证≤H(q)。正方差Gaussian在任一非空区间的真实质量正；无界区间密度inf=0与数值质量下溢是两件事。
2. 来源：arxiv2605.14917v1的P_Z固定，训练更新theta。候选共享z的Bayes权重更新是额外生成假设，当前单步实验不执行多轮更新，不证明共同学习。
3. 对照：raw MI-LB保留用于H；另列exact-merged MI-LB，合并完全相同(mu,var)，权重用math.fsum累加。固定tau=0.5 Bernoulli BALD、模型条件均值分歧和连续MI积分保留。不得用merged替换raw后改H。A同分布guard须显式标记，不能报告为经过细化收敛。
4. Q1实现先exact-merge并按(mu,var)升序排列；只比较精确相等的浮点参数及合并后权重，不近似合并。叶采用半开区间，端点零质量无影响。四初始叶先计算/检查再拆；按未裁剪d的精确浮点最大值、左端优先拆分，不用tie容差。有限区间中点；左/右无界分别向外8。达到2048叶不再拆。缓存未变化叶；记录每次被计算叶及每轮总L/U、被选叶、最终完整划分。raw/merged源分数分别计算。
5. Python float64、math.fsum、scipy.special.log_ndtr/logsumexp；运行输出Python/NumPy/SciPy版本。区间正尾用log-survival差，负尾用log-CDF差；跨均值选择稳定一侧，差用log(-expm1(delta))，无穷端显式处理。混合质量、密度界和posterior用log域。非空区间质量数值0/非有限、负d或q>r超过1e-12标numerical_failure；不裁剪、不重归一化、不换容差救分。L微小负值照录；低于-1e-12视失败。没有outward rounding，不称机器严格证明。
6. 参考连续MI一次积分固定[-16,16]，epsabs=epsrel=1e-12、quad limit=300；每点评估两个模型加权的p_z log(p_z/pbar)之和。区间外显式保留tail≤Pr(|Y|>16)*log(2)，与quad估计误差相加；总误差若>1e-10，或quad告警/非有限，则containment不可判，不能通过H。不通过增加精度/域/limit重试。记录有符号抵消风险与误差估计非形式证书的限制。参考误差范围须与最终数值界相容。
7. 计数：special scalar log-CDF/log-SF评价、Gaussian log-density标量评价、quad integrand评价、计算叶数、拆分数、每对照CPU秒分别记录，不混同实际实验成本。所有候选单次标量观测的解析成本1，湿实验0。主脚本一次运行；独立作者只读本协议、v1及原文，另写另跑一次，不看主代码/数值。各自CPU120s/RAM1073741824B/输出50000000B，0GPU/安装/功能响应读取/模型API。进程资源守卫另收receipt。

设计错误、数值失败、资源不足、H未支持、局部H支持分别记录。本次即使H支持，也只支持冻结合成例子的计算性质；没有新颖性、药物命中收益或模型共同学习证据，不晋升核心代码。
