# G1.v1.1 独立数值复算

独立结论：冻结数据资格成立；两个主比较均是点改善、95%类别聚类重采样区间跨0，唯一开发假设未获支持。按冻结停止门，停止当前G1实现/设定，不调参或换数据求阳性。此结果不证明条件几何不存在，更不支持新算法、真实生物协方差或共同学习。

## 独立性与边界

从原始CSV重写实现，仅以protocol_g1_v1_1.md、input_freeze_v1_1.json、preexecution_freeze_receipt.json定义任务；按其中SHA核对metadata_projection和旧metadata_freeze指定剂量窗。投影路径由协调者只提供定位，没有提供数值或实现。接收并保存本结论时，未看root实现、root数值、旧候选/旧结果或本轮审查意见；未联网、读sealed/confirmation/.env、安装包或调用模型API。实现及结果只写independent_g1；本文件单独交付，不修改共享研究索引。

模型/scorer采用独立子进程：planner输入只含125训练条件全8cell标签、训练类别、固定28对和开发类别。全部B0/B1/C共144个动作及SHA回执落盘后，scorer才创建delta释放文件。predictor收到的开发反馈每条只有q<r有符号LN_IC50差；开发绝对值、完整中心和未测差值保留在scorer。预测阶段固定模型参数。

## 复算结果

源CSV SHA为0883b3ef6e440603094c43c74044e1d333fce61e92e3efa374ea3a54f0b50302，20,355,833字节；扫描135,242行，冻结173×8=1384交叉均唯一且finite，Decimal剂量窗与药名/PATHWAY_NAME核对成功，125训练/48开发、18开发类别。没有按响应过滤、替换面板或删除坏行。仅访问LN_IC50及DRUG_ID、DRUG_NAME、SANGER_MODEL_ID、PATHWAY_NAME、MIN_CONC、MAX_CONC。

125折均全重拟合均值、类计数、池化协方差、类别协方差、收缩及ridge。7000条逐折/策略/动作raw pair-MSE保存于loo_fold_pair_losses.csv；28候选的均值与选择保存于loo_selection.json。B0、B1均选0基[3,5]，即SIDM00517与SIDM00686；raw LOO均损失分别1.4996353679737378、1.4785286836227416。开发共同D来自完整训练ridge前C0，为1.7239887126603863。

| 策略 | 48药平均归一损失 |
|---|---:|
| B0 | 1.0307361109683164 |
| B1 | 1.0212386501515178 |
| C | 1.0142323468276304 |
| no-query，仅诊断 | 1.1832274249382302 |

| 主比较，正值为C改善 | 平均Δ | 类别cluster bootstrap双侧95%稳定性区间 | 主门 |
|---|---:|---|---|
| B0−C | 0.01650376414068655 | [−0.06095329153863276, 0.0844516153258215] | 未达 |
| B1−C | 0.007006303323887585 | [−0.05107278550411543, 0.0652276913399134] | 未达 |

C在48开发条件使用11个不同pair，动作多样性门达到；但不能抵消两个主门未达到。PCG64(20261029)一次生成9999×18 int64 draws，两个主比较共享该矩阵；每个抽中类别保留全部药物及重复次数，按合并条件数加权，NumPy quantile(method=linear)。draw .npy文件SHA为68c8b4c309144a53e53e66b5fbad7999e747d09405152669c803345538bd66b0。该区间只是已暴露拟合标签上的重采样稳定性，不是生物或药物总体覆盖保证。

## 资源和自检

唯一一次独立复算，maestro Python；实验Windows Job及其全部后代的wall 1.682338399999935秒、process CPU(user+kernel)1.234375秒。Windows逐进程peak working set最大43,991,040字节；10ms采样并发working set之和峰值79,183,872字节，Windows Job peak commit 82,489,344字节。Job硬限制总commit 1,073,741,824字节、user CPU120秒；另10ms守卫监测聚合user+kernel CPU120秒、working set及输出50,000,000字节并超限终止。限制实际没有触发。working set之和是采样值，未将其冒称连续时间精确峰值。实验输出约2.16MB，0GPU、湿实验、安装、重试和调参。

动作冻结时间早于delta释放时间，释放回执的动作SHA与冻结回执相同；B0/B1/C各48动作、96曲线尝试。独立预测、每药损失、逐动作delta、28对V、LOO、bootstrap draws/replicates、输入/代码/文件SHA、自检和资源回执已保存在independent_g1。实现SHA为e5cf446f35e80f9487683f5c5332b852a0cc4f1feb3d58bc45fd2b7afbfef7c7。成功退出仅是工程证据，科学结论由冻结主比较决定。

实际角色：独立数值作者g1_independent_numeric；requested model=gpt-6.1-sol、reasoning_effort=high、fork_turns=none（协调者提供的实际spawn工具请求）；effective model/effort没有运行时元数据确认，记unknown。此复算没有接触协调者数值，跨实现一致性应由协调者随后核验，不在此先行声称一致。

元数据更正记录：独立实现、数值输出和上述结论保存后，协调者指出spawn请求字段的原记录不准确；本次仅据实际工具请求更正requested配置及fork_turns，effective仍unknown。未改科学实现或计算输出，未重跑。independent_g1目录未发现同类错误角色字段。
