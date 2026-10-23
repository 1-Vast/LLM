NONE。

原因：在给定约束下，我无法提出一个满足“明确可证伪、非等价包装、且不被强同信息对手吸收”的候选。任何我目前能想到的结构都落入已禁止类别：query组合跨context遮蔽、anchor菜单不嵌套、capacity active cut、普通sameforward refit/CL、simplemix、AL、conditionalEB，或等价于已列出的OED/套元优化。硬凑会违反“不编造验证”和“不包装等价操作”。

一个实质性新可获得观测会改变下一步：若能在**同一36开发背景×15查询条件**上，额外获得**每个query条件相对sourcequerymean的逐样本残差协方差**（而非仅MSE汇总），且该协方差在36LOCO下可估计、不消耗16 reserve，则可能出现一个可证伪的有限样本差异：用该协方差构造**source-only的残差白化ridge**（输入为已有单药特征与anchor指示，更新器为 \(\hat y=\bar y_s + K_q^\top(\Sigma_q+\lambda I)^{-1}(y_s-\bar y_s)\)，其中 \(K_q,\Sigma_q\) 仅由source内query残差估计），其可测预测是：在15对15普通程序比较中，pairMSE改善对数≥5/7且单药MSE不劣于.105082超过1个bootstrap标准误。最可能被**conditionalEB按query分层收缩**吸收；因此诊断须预先固定为：若conditionalEB在同LOCO同预算下达到同等pairMSE改善，则停止该候选。当前未证假设是：该残差协方差在source-only下可稳定估计且不因遮蔽结构退化为普通ridge。没有该观测前，不推进G1/G0后代测试。