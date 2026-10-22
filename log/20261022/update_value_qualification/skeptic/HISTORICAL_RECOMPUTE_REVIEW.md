# 历史cross-synthetic-noise选择审计：独立重算

2026-10-22。根在独立draft完成后明确追加授权读取三份已exposed旧scoreexports；不读raw/reserve、0newfit、0newmeasurement/API。本代理先独立实现并跑3项syntheticcase，再读旧exports重算，未importrootaudit或旧pipeline。初次数值调用因Windowsbackslash与manifestPOSIXkey不一致在recordopen前失败；仅verification代码as_posix修复，首stdout与AUDIT_FAILURES保留。run02成功。

`HISTORICAL_INDEPENDENT_RECOMPUTE.json`保存完整重算与before/afterhash，`HISTORICAL_COMPARISON.json`将root输出作identity/key明确映射后核3161项：**PASS，maxdiff1.1102230246251565e-16，0mismatch**。差异是均值差与先逐campaign差再均值的浮点顺序，低于1e-12。所有36campaign的原始hitstable、choices、LOFOchoices/值、fold汇总、ties/sign/correlation和原成员/family/index一致。3尾不完整campaign29/46/19compound明确排除，无性能挑选。

| 方向 | cross-selected hits/64 | 对alwaysridge | 对alwaysR1 / evaluation-hindsightbestfixed | 对LOFO训练选择fixed |
|---|---:|---:|---:|---:|
|1→2|2.805555556|+0.500000000|−0.361111111|0.000000000|
|2→1|3.000000000|+0.361111111|+0.222222222|+0.222222222|

对称hindsightfixedgain−0.069444444，对称LOFOgain+0.111111111。每draw各6tie；双draw严格非tie24campaign中13同号、11反转，同号率0.541666667；差值Pearson0.303929516。不能仅凭正correlation宣布可用策略价值。事前冻结双方向均≥0.1875hits/64门FAIL。方向不对称需原样保留，不只报反方向正值。

**局部决策：停止凭此outcome-argmax/two-draw诊断支持selector扩展。** 它用隐藏gradedoutcomes选法，是不可部署诊断；并非真实valueoracle严格上界，也不排除合法descriptor+shrinkage可能更好。因此FAIL不证明二菜单所有selector不可能，更不否定所有静态functionalworld或RSI。既存noise是对同publishedY的syntheticprobe扰动，不能当独立技术/生物测量重复。36campaign含混合family、共有context/source，不报伪iidCI、p值或生物功效。

独立稿提出的替代继续条件未用于改变root已冻结门。root与支持方实际问答使scope进一步明确，见CROSS.md。支持方在独立重算执行期间已来信披露两个方向摘要；独立稿和算法代码先已写定，后续解释不声称完全未见方向。root完整JSON是在独立输出落盘后才读并比对。
