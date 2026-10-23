# FF 已知药对、新细胞：单点组合反馈的有限开发实验

2026-10-22；响应读取前协议。完整研究目标 ACTIVE / NOT_ACHIEVED。本轮只有普通功能反馈价值假设，没有新算法、智能体或RSI候选。

应用：用新细胞的一条组合功能观测改善相同药对其他剂量的公开PercentGrowth预测，为后续组合筛选研究寻找具体纠错对象。不是临床效力、真实湿实验成本节约、动力学或未见药对泛化。

## 固定元数据任务

采用新root/DESIGN_SUMMARY.json、DESIGN_TASKS.json、SPLIT.json。FF 150525合格网格，canonical NSC+SAMPLE与精确浓度字符串后148681任务，1844组重复各2份；不平均，固定最小原始CSV行号对应的完整网格为代表，不以日期解释 chronology。药轴按sample身份字符串排序，浓度轴Decimal排序；精确字符串匹配保守保留，不容差合并。同cell/samplepair多dose方案若均合格按设计hash选一个。

60个cell经固定hash顺序分20fit/10tune/10development/10selection_closed/10later_closed。公共目录须前40cell均有完全相同samplepair/actualdose格；887药对，35480任务，2148其他pair-dose设计因覆盖不全排除，记录而不补值。此完整目录由元数据选择，不能推断代表全部化学空间。

所有相关physical(lab,study,plate)在FF资格范围仅1cell；各分区板不交叉。study仍大量跨cell/分区共有，不能声称独立study或生物重复认证。源/目标同pair合法。目标pair不能使用其他目标pair的组合锚点或单药作额外校准；仅自身6solo+B1锚点。公开端点已有作者归一化，其跨测量依赖未独立认证。

## 信息与预处理

唯一数值列PERCENTGROWTH，除100成比例单位，不裁负值、不按值剔样。读取仅前40cell所选35480网格的319320组合记录、122871唯一solo记录。原始重复/其他网格及后20cell响应不解码；readers物理解压CSV但只按允许行索引该列并转数值。OD、EXPECTEDGROWTH、SCORE、NOTZ均禁止索引为数值或特征。遇缺失/非有限停止，不根据值改筛选。

B0已知6solo，B1另已知canonical(2,2)即最高×最高组合点；二者共同query固定扁平0..7。源fit/tune可用其完整曲面，development query只评估，不能参与选择。source/tune揭露和计算是实际历史成本，不能免费抹除。单药共享按unique source row记账；B1条件回放一task一anchor，但不是已认证真实孔成本。

## 冻结普通模型菜单

所有模型按pair独立拟合，故没有跨目标pair/plate信息聚合。NCI期望从合法solo按官方负值min分支与正值clip-product重算。source残差r=combination−NCI。

每B候选15个：NCI；source-pair平均残差（B1以0.5倍anchor残差差值整体平移，B0不平移）；直接ridge残差回归λ∈{.01,.1,1}；非线性RBF kernel ridge残差回归带宽∈{.5,2}×λ∈{.01,.1,1}；普通联合Gaussian条件残差预测对协方差对角收缩α∈{.1,.5,.9}；固定50:50 ridge(.1)+Gaussian(.5)混合。direct输入为6solo，B1再加anchor残差；Gaussian以同样变量与9维残差建立联合协方差。输入仅source均值/标准差归一化，std下限.05；kernel按输入维度平均平方距离。正则按source数缩放；数值jitter1e−8，不按目标调参数。B1额外允许source-selected整个B0回退，因此16候选；这是明确的轻微选择机会差异，不声称等预算agent search收益。

20fit->10tune的cell等权MSE一次选择每B程序（固定列表顺序破同分）；按原参数30source重新拟合->10development，无development调参。保存所有候选预测和tune风险，不事后择优替代选择器。普通ridge重拟合、直接support输入、Gaussian后验与简单混合属于普通预测对照，不宣称持续学习/继承创新。

预定敏感性：对每一个target pair单独排除source中与该target grid同study的记录，重拟合同一已选择程序，不重新调参；报告源n最小/分布和风险。它只隔离同pair study条目，不能保证全局study独立。若任一pair剩余source<2则停止该敏感性并报告不可估，不能删pair凑通过。

## 指标、判定与STOP

主MSE先query8点、再887pair、再10development cell等权。次MAE、各dose/cell风险；排序真值固定为每pair的8个query平均growth，报告每cell选择10% pair（ceil，即89对）的selection regret：预测所选89对的真实均值，减去真实均值最低89对的均值。不替换MSE主门，非治疗决策。选择按预测8点均值排序并固定pair顺序破同分。

开发分配门仅用于是否值得诊断：selected B1−B0的MSE降低为正，10000次seed20261022固定预测cell bootstrap95%gain区间下界>0，至少7/10cell改善，删除任意单cell后平均gain均>0，且same-study排除敏感性平均gain>0。所有条件需满足。bootstrap条件于已拟合模型和共享目录/study，不是独立生物学显著性或临床有用阈值。未认证噪声/成本，不能发明临床效益门槛。

若门失败，STOP本固定目录/anchor菜单向WM/agent/RSI扩张，不开reserve、不换endpoint/lab/anchor、不追分扩大菜单。若门通过，仅GO误差诊断：普通方法正结果不能升格机制。只有发现可合法观察、重复存在的强方法错误，并提出具体不同的修正操作后，另作独立新颖性/简洁性评审。若错误无可迁移结构或完全被普通方法解释，停止其创新扩张。

## 校验与成本

开值前绑定协议、代码、SPLIT/DESIGN、独立/交叉评审及元数据审计；合成测试须证明development query更改不影响预测/选择，B0不读anchor、B1不跨pair读取、输出有限、共同query不含anchor。开值后另做独立原始坐标/数值与指标审计，范围如实报告。零新湿实验；DeepSeek未调用时记0；maestro运行wall、版本、HEAD、seed及原生API成本可见性保留。旧冻结文件/STOP/reserve不改。
