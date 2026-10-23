# 一次有界反馈传播误差诊断

在冻结主实验完成、独立原始数值/指标审计PASS后制定。主实验和门不变；本诊断是事后探索，不是新确认实验。仅使用20fit->10tune（不读development query、不读后20cell），不新增候选或纠偏拟合。

目标：检查普通selected B1 RBF剩余误差是否仍与合法anchor innovation存在跨tune-cell同向关系。innovation固定为观测高高组合点减source-only B0 RBF对该点预测。每个query位置分别计算：B0与B1的pred−truth对innovation的中心化协方差、相关系数和回归斜率；每cell对887pair中心化计算再报告细胞方向，避免将887pair说成独立生物重复。全体pooled值只作描述。

计算两种固定source条件：全部20fit，以及逐pair剔与tune target同study的source（重新估source均值/尺度/核）。B0/B1固定已在主选择中选中的RBF参数，不以诊断调参。每个episode仅自身solo/anchor输入；模型仍不读query。各cell/query残差评价可读其已许可tune真值。

停止边界：相关性若不存在，或same-study敏感性不稳，则不据此构造更新规则；若存在，也只定位普通核尚有相关误差，标准残差回归/stacking就能表达，不能因此宣布新机制、增加模块或打开reserve。仅当随后能提出区别于普通核/残差校正的具体技术假设，且通过新颖性独立交叉评审，才允许另一方法实验。本次诊断不会训练校正器、不产生新架构或新门。
