# 晚期信息门：拟合前独立代码审查

2026-10-22。recursive_distinct。只读本阶段 PROTOCOL.md、evaluate_late.py、test_evaluate_late.py；未读任何新24h或其他背景数值、未加载准备数据、未运行生物拟合。实际执行了现有合成测试。原晚期信息门协议审查与root随后同意的五panel／两独立family修订作为合同。

**结论：未发现阻断本次预固定评估的科学实现bug。** source-only预处理、同候选预算、预计算gamma=scale核、独立family选择与主／敏感性门均符合读到的协议。建议冻结前补一个直接检验模态隔离的合成测试；下面的计数／warning归属属于记录完整性改进，不据此扩模型或新信息。

## 通过的代码检查

- `normalized_block` 的保留蛋白列、nanmedian、StandardScaler、化学均值和块RMS仅由train输入得到。验证／test只apply源统计。全源缺失蛋白返回零块，源常量块对目标亦归零，与协议一致。mask使用finite-status，本身不读取标签。
- `main` 每次inner拆分以source/validation重新调用blocks，outer则以train/test重算；没有复用整个600群体的插补或缩放。hash盐与旧分区相同，outer源／目标化学组有显式不交断言。
- C/Craw/E/M/V按声明拼接，Craw不中心化／归一；E不拼24h，M只拼24h mask，V再拼late值。拼接按声明块数sqrt缩放。因此C、E、M、V之间正则化约定发生的变化已是预固定合同，不能把差值直接叫生物条件互信息。
- `kernels` 在源特征a上计算`1/(n_features*a.var())`，source方差为0时用1，正是SVC `gamma='scale'`的规则；test核是rbf(test,source)而非test拟合gamma。每panel／split共用同一个kernel_pair，不跨外折缓存。
- 各family/panel各自有三个C，每次内折AP列表独立；`max(valid,key=mean_AP)`在相同AP时保留GRID顺序，满足小C优先。没有跨logistic/SVC挑选。原始decision_function分别保存为两个family，因此不存在某折logistic／某折SVC混排的原问题。
- source单类按源prevalence返回并标mode，validation不可评分时记录跳过；不改分区。正常全部可评分情况下，每panel-family是5×(9inner+1outer)=50次实际fit，总500。
- 每family的pooled、fold、macro独立报告；V对C/Craw/E/M逐个差值都≥0.02，逐个至少4折严格正，且全部foldAP有定义才过门。RBF也报告同一诊断字段，但scope明确主logistic，不能用RBF的pass救主分析。没有Brier、sigmoid伪概率或混合classifier portfolio。
- bootstrap固定2000次、固定seed、共享化学组抽样和同一draw的V/E/M得分，仅重采样已有OOF、不重调参；抽到单类跳过。它依旧只是固定预测排名敏感性，不是独立背景置信区间。

## 合成测试实际执行

`D:/anaconda/envs/maestro/python.exe -B research/ptpc_late_information_20261022/test_evaluate_late.py`：**3 tests，全部OK**。覆盖test数值不能改变source归一变换、常量／全缺失块不发明信号、预计算RBF SVC与原生gamma=scale的decision_function数值一致（atol/rtol=1e-12）。最后一个测试实际运行的只是24行合成分类器，不含生物输入，不属于新增科研模型搜索。

此前从仓库root用`python -m unittest research/.../test_evaluate_late.py`调用因测试局部`from evaluate_late import ...`无法找到模块而在导入阶段失败；改用脚本声明的直接入口后全部通过。此为调用路径问题，没有执行或隐藏一次生物fit，也不构成三项测试本身失败。

## 建议的最小补充与记录限制

1. 最有价值的新增测试不是再比较一个模型，而是**模态不干扰**：只改late有限数值、保持缺失位置不变，C/Craw/E/M的panel_features应逐元素不变；改late缺失位置时C/Craw/E应不变。V／M允许按对应信息变化。当前代码的切片结构看起来满足，但现有三测试没有直接覆盖这个关键V−M隔离合同。我已把此建议发给root，不并发修改其脚本。
2. `len(ledger)`在含unscorable_validation_skipped时也把一个status记录称为fit；source_prevalence_fallback同样没有训练分类器。因此打印的`fits`只有全数正常训练时才是实际分类器数。若边界出现，应从mode=classifier统计实际fit，并另外报opportunity/skipped/fallback次数，不能把status行算实际算力。当前是否触发要等结果，审查未打开数据。
3. warning字符串已保留，但其family/panel/outer/inner/C归属没有结构化绑定。若出现warning，应借ledger补关联，不能泛称所有fit均正常。没有warning时该限制不污染数值。
4. 本代码依赖PREDICTION_FREEZE的bindings绑定准备npz和身份／准备记录；在真正执行前需确认freeze实际包含这些输入、协议和最终脚本，而不是只绑定部分文件。这属于调用前封存范围，不在此伪称已经检查尚未生成的freeze。

本审查没有独立复核准备agent对24h读取范围、聚合和配对600条件的实现；那仍需独立source/prepare审查。现在的结论是评估代码可以在最终冻结及必要输入检查后进入有限运行，不是信息门已通过，更不是候选机制新颖性恢复。

## 封存前修订复查

root在初步审查消息后补入 `test_late_value_and_mask_information_are_separated`。我读取新测试并再次直接运行，**4 tests全部OK**：保持缺失模式只改late目标值时，C/Craw/E/M特征逐元素不变、V改变；改late目标缺失模式时，C/Craw/E不变、M改变。

同时复查root对计数及warning的修订：classifier_fit_count只计mode=classifier，另报fallback_count和unscorable_inner_splits；进度打印ledger_entries；warning结构化关联outer/inner/family/panel/C；ledger增加feature和block数量。上述第1–3项具体记录建议已落实，不再是当前代码的未修问题。最后seal绑定这一修订后代码与测试；没有因修订读取任何新生物值。
