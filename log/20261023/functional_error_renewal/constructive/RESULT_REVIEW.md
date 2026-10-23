# 独立数值审计：预冻结停止条件已触发

2026-10-23。根已告知点T和下界；本审计不是结果盲审。实际执行`D:/anaconda/envs/maestro/python.exe -B research/functional_error_renewal_20261023/constructive/audit.py`，exit0。代码不导入根moments/run。仅读取隔离SOURCE.npz、PAIRS.json、BOOTSTRAP.npy、RESULT.json，没有raw、原缓存、开发或保护结果读取；未修改冻结原稿/协议。

## 实际复算

从SOURCE每个患者行直接筛pair共同有限值、先减各自配对均值，再以np.dot算中心化平方与交叉和。独立枚举全部165药物无序pair，四cell各至少25人的资格名单精确匹配7278pairs。每patient唯一，四cell大小105/104/91/83与保存结果一致。对全部7278×4=29112个pair-cells重建n、r、样本covariance、Yj对Yi的OLS斜率、数值constant。检查全部pair身份、两个half的contrast及数值。

最大绝对差：n=0；r=2.8694e-13；covariance=1.2888e-10；slope=3.9502e-13；contrast=2.8455e-13。预设容差covariance1e-8、其他连续字段1e-10，T1e-12；全部通过。直接中心化审计未发现根raw二阶矩消减引起的实质差异，不能据此保证任意数据尺度。

独立T=0.011067340493952993。反号计数discovery1432、replication1361、两半467；contrast同向率0.5721352019785655；constant计数0，全部精确匹配。对保存2000bootstrap数组重新取.05/.025/.975分位，分别0.0012573006343350995、-0.0013017531363783206、0.027848689855939246，与RESULT逐值一致。

另用同seed、按声明四cell顺序直接生成重复患者行，逐pair中心化复算前三个完整bootstrap T：0.010847884295662597、0.024234045567132427、0.004467944689218885；与保存前三个最大差4.3368e-16。**没有重跑其余1997次bootstrap生成**。全部2000的分位审计不等于全部2000生成过程独立复现。本审计没有认证原始提取/测量真值或临床语义。

第一次执行即通过，无修复重跑、无拟合、无结果择优或改门。审计程序内计时约1.75秒，工具进程wall约2.83秒；不是算法效率对照。JSON详情在AUDIT.json。

## 决策

**STOP_THIS_CD14_STRATIFIED_SOURCE_RATIONALE**。预冻结要求lower>.01，而实际lower=.0012573；点T略>.01、lower>0或两半467个反号pair都不能替换原门。保留正相关contrast对齐的探索性描述，不把它叫新预测性能、干预机制发现或world/agent/继承/联合/改进策略收益。

不切467pair做救援，不换marker/cut/split/seed，不启动该依据上的更新器fit。停止只限此次单marker源内screen，没有证明所有conditional response为零、全局协方差最优、世界模型或RSI不可能。既有BeatAML普通反馈正收益与所有历史限定STOP都保留。
