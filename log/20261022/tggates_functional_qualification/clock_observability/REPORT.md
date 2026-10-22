# 时钟修正代数审计：一般诊断不可识别，有限模型预测仍可检验

2026-10-22。先写 `PROTOCOL.md`，然后执行5项数学不变量测试（全通过），再执行拒绝覆盖的 `audit.py`，结果及3输入hash存 `RESULT.json`。无真实药物响应，无CEL、DNA/LDH数值，无训练/API调用。该审计是构造反例，不是生物实验。

`T(exp(eta)*t)` 在线性状态轨迹上就是相对于初始状态的幅度放缩，最大浮点误差2.22e-16；幂律输出 `b+a*t^p` 上等于 `a'=a*exp(p*eta)`，误差3.64e-11。单幂律 clock/amplitude 切向量矩阵秩1。双输出使用不同幂次时，clock与**一个共同**amplitude可有秩2，因此不能说clock总与幅度相同；给两个输出各自amplitude后，clock重新落在其span（加clock前后秩均2）。可分辨性取决于公开且预定的替代更新族及约束，不是命名。

更强的三切面反例在整个[2,24]单调：

`fA(t)=t/24`

`fB(t)=t/24+0.02*(t-2)*(t-8)*(t-24)*(t-4)/(-3840)`

二者在2/8/24h完全同值；导数在各切面均不同。对固定warp=1/2，已付费8h支持映射到4h，两者预测都为1/6；未付费24h目标映射到12h，两者预测分别0.50和0.52。全区间导数最小分别1/24和0.005，第二曲线的单调性由导数临界点与端点计算，不只查离散网格。分歧发生在观测时间范围内部，无需36h外推或剧烈非单调振荡。

所以三固定时间及一个相同支持值不能在不限制连续曲线族时确定时间导数或唯一的withheld预测。不同可逆潜坐标也可保持输出完全相同；但**潜坐标自由本身不取消一个固定可观测时间放缩的预测定义**。更具体的问题是有限观测无法证明修复的是真实生物速度而非head/shape偏差；足够灵活的head也能在有限状态点复制输出修正。

该结果关闭的是未经限制的诊断/因果识别主张，**不反驳预先固定的非线性动力学族可在低样本下凭归纳偏置获得实用预测增量**。例如饱和指数曲线在两个时间下的clock/amplitude通常可区分；这仍需真实噪声/heldout检验。实用比较应把clock明确列为标准time-warp/system-ID基线，不能以预测有益反推其新颖性、世界模型必要性、Agent或RSI。

命令与已观察结果：

```powershell
& 'D:/anaconda/envs/maestro/python.exe' -B -m pytest research/tggates_clock_observability_20261022/test_audit.py -q -o cache_dir=log/20261022/tggates_functional_qualification/clock_observability/pytest_cache
# ..... [100%], exit 0
& 'D:/anaconda/envs/maestro/python.exe' -B research/tggates_clock_observability_20261022/audit.py
# RESULT.json created; exit 0
```

可复核代数预期与断言均在代码/测试。没有把5项软件测试计作5次科学验证，没有从任意合成误差推导真实药物效用差阈值。
