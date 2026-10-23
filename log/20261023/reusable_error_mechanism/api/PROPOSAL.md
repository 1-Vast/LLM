机制：**单一决策裕度替代组合异质性**。共享一个决策裕度δ，不共享各候选功能预测、组合交互和绝对基线；反馈只改“是否用组合替代单药”的门槛，不改功能MSE。

公式≤6行：
1. 冻结功能预测\(\hat y_c\)；\(b_t=\max\)已观察单药真实功能。
2. 选择\(c_t=\arg\max_{c:\hat y_c\ge b_t+\delta_t}\hat y_c\)，否则选基线。
3. 反馈真实功能\(y_t\)：\(\delta_{t+1}=\delta_t+\eta[1\{y_t<b_t\}-1\{y_t\ge b_t+\delta_t\}]\)。
4. 批次汇总：\(\delta_T=\delta_0+\eta(\#失败-\#明显成功)\)。
5. 失效判据：同一反馈集不同顺序/分组给δ差超容差，或更新方向符号一致率≈0.5，则限制被推翻。

相比同信息direct/ordinary union refit，它只估1个决策参数，每次反馈O(1)，不需重估绝对功能、单药效应和组合交互；后者在有限反馈下需全局重拟合，已有实测约9.77倍拟合成本，episodic conditional/meta还需内循环，方差更大。新性质是“反馈只改选择、不改功能预测”，并宣称可继承的δ应具批次顺序不变性；不是anchor MSE、scalar calibration、shared potency shift、signedmean EB、quadratic reciprocity、shared kernel、transport survival或DiscoRL。最强替代解释：只是保守阈值减少选择，或δ捕捉批次漂移；负对照为随机打乱反馈更新δ，若后悔相同则无信息。

最小合成反例：\(b=0,\delta_0=0,\eta=0.6\)，反馈A:+0.3、B:-1。先A：A满足0.3≥0，δ变-0.6；再B失败，δ回0。先B：δ变0.6；A不再满足0.3≥0.6，δ留0.6。同反馈集终值不同，后续选择反转，操作被推翻。等价检查：用已曝K562双RNA反馈按不同随机顺序重放，比较δ与选择后悔。

最小功能实验：现有K562源，冻结普通RNA条件功能预测器不重拟合，留出双RNA反馈批次；只更新δ，任务为在双RNA候选中选真实功能高于最佳单RNA者；与固定δ、同反馈预算direct ridge比较决策后悔和顺序一致性。不碰Norman73 law、Emerald16保留背景、CDK/AML/ALL。只有一致性通过，最后才检验δ跨批次继承及组合特异裕度是否更好。