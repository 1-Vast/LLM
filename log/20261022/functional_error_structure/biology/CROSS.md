# 冻结误差审计：实际交叉与解释范围

2026-10-22。biology/INDEPENDENT.md 独立封存后，已实际读 skeptic/INDEPENDENT.md、frontier/INDEPENDENT.md 与 root 的 research/functional_error_structure_20261022/decompose.py；随后读 RESULT.json 的两配置、全cell分量与交换账本。Frontier 首次读稿时文件不存在，此后实际读到完成稿。不新增 arrays/模型/来源请求、不独立执行诊断；结果归属 root。不修改独立稿。

## 代码静态核查

脚本只取已保存四组预测与已开40-cell cache中的10 development truth，按同cell 887pair×8query计算三项，逐cell复核其和等于MSE及旧保存MSE。排序与旧 run.py 一致，明确 kind='stable'，固定89；进入与退出集合等数，同cell真实均值和差/89复核regret差。共同入选与oracle消去，身份正确。没有重新训练/调参，也未读取其他候选预测或closed分配。NPZ成员读取会先物化已开40cell，不能说只物理解码10cell。

## 与 skeptic 的实际双向质询

本角色接受 skeptic 最强挑战：C项包含正比例scale误差，其下降不等于rank改善；G/D虽对当前pair均值排序无作用，也不能直接叫生物/assay校准。数学误差方向不辨识测量原因。

Skeptic 又指出本角色独立稿提到的“少量高代价交换主导”超出当前最小账本：只有集合成员数和净truth总差，不足分析贡献集中性，进入/退出成员亦无天然配对。本角色明确接受。当前仅能说多少集合成员变化伴随该cell总regret变化，不能讲某个进入药物替代某个退出药物的因果故事，也不在本轮追加匹配/子组分析。独立稿保留，新增范围修正在此。

本角色反问：即便C下降而top89恶化，也只能说明固定平方误差与cutoff选择代价未同步改善/该开发决策不稳，不能说缺少功能信息或必然需要decision-aware新训练。Skeptic 实际答复接受；普通噪声/选择也可能解释，当前审计不辨识因果。双方确认truth总和只供回顾，不能变成实验前可见门或生物机制证据。

## 与 frontier 的实际双向质询

Frontier 质疑本角色独立稿的条件句“gain主要在排序不变项则MSE门奖励决策不用方向”：这只能是数值误差账本，不能当成移除某些训练目标的干预实验。A/B程序会同时改变G/C/D，不能据投影保证删去一项训练目标不影响C的泛化。本角色实际回信明确接受。Frontier亦确认C含scale误差、无新机制可晋升。

本角色反向询问：读结果后，是否只能收敛到pairmean平方误差已普遍改善但exclusion top89仍不稳，而非新生物门或校准因果？Frontier实际回应：C两配置10/10cell改善，结果排除收益主要common-offset/shape-only的解释，但不能说rank distortion已修复；交换只作集合记账，不以dev truth造gate。Skeptic亦实际回信接受相同范围。

## Root 结果审查：原先一种解释未获支持

Root执行exit0，脚本恒等式及旧MSE/regret逐cell复核通过。本角色仅审结果JSON和代码，未自行打开NPZ或复算预测。脚本最终还保存进入/退出各自truth总和及observed regret差，便于核查，不是新增指标选择。

主分析G/C/D净gain依次 .0000246726376、.000526307652、.000398020277；C是最大项且10/10cell改善，D亦10/10改善。Study-exclusion对应 .0000209438373、.000413159257、.000168769940；C仍最大且10/10cell改善，D为7/10改善。因此不支持“反馈收益主要只是全cell共同offset或dose形状”的候选解释。相反，排序使用的pairmean误差中心化平方项确实普遍改善；该事实仍不等价于rank修复，因为C也包括保序尺度误差，而且top89依赖cutoff附近误差方向与真值间隔。

已读两配置全部十cell交换账本：主分析每cell进入/退出成员数分别为3,3,6,4,1,2,2,5,7,6；exclusion为5,3,3,2,1,3,3,3,6,6。所有集合truth总差/89均与旧regret变化一致。主分析6/10cell regret改善、均值 .0086369803→.0077671489；exclusion为4/10、.0096032022→.0097194522。只说有限数量集合成员变化产生上述净差，不给成员强造一对一关系，也不推断少数高代价个例、真实噪声稳定性或生物机制。

结论是更具体的正向与限制并存：普通真实功能反馈不只改善dose形状，也改善pairmean平方误差；但后者未保证study敏感性下top89决策收益。它不支持“无功能信息”，也不证明必须增加world model/agent/teacher或新排序目标。当前没有独立可执行的新修复机制，维持NO_CANDIDATE / NO_PROMOTION及旧anchor-transport创新/RSI扩展STOP。完整目标ACTIVE / NOT_ACHIEVED；本阶段审查终态后不再追加数组或分析。
