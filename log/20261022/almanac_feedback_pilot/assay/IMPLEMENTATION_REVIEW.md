# 响应前实现复核

2026-10-22。完整静态阅读models.py、prepare.py、run.py、test_models.py；未运行prepare/run，未打开响应文件或CSV。独立运行assay_study_design.py只访问冻结设计元数据。结论：**本冻结任务范围PASS，无必须修复的实现问题；允许root完成freeze之后运行已限定pilot。** 此结论不证明全pipeline已由扰动测试验证。

## Reader与信息隔离

prepare只从冻结task索引产生40cell允许行集合，唯一数值访问为这些行的PERCENTGROWTH/100；其他行仅CSV结构解析，不转响应，不输出payload。实际values键与allowed完全相等、finite断言、不按值筛样，保留原行索引。freeze哈希验证在读取前执行，后20cell及丢弃重复不在冻结task索引范围。VALUES包含dev query作评估存储，不意味着预测器可用，隔离依赖run的数据流。

run source20拟合、tune10选择、source30重拟合、dev10预测，没有dev query参与模型选择。dev仅solo与B1 anchor传入predict_catalog；返回8query不包含anchor。每pair循环且只切本pair输入，不跨target pair共享。B0传None，不读target anchor；B1 fallback复用selected B0，study sensitivity遇fallback用budget0及其原程序重拟合，正确。

## 数学与菜单

expectation按canonical第一药外循环、第二药内循环展开9格，负值min、非负上限1乘积与缩放字典相符。残差为组合减NCI，不利用发布Score。ridge中心化source特征、残差并用source数归一，截距为source残差均值。RBF按特征维均方距离，与协议一致。

Gaussian对标准化solo/可选anchor残差的xx协方差做对角收缩，xy也乘(1-alpha)，对应整个joint covariance的对角收缩后条件均值，不是少写一项；源均值、scale和协方差均在predict_pair内计算。study exclusion先mask source再进入predict_pair，因此预处理也排除了同study，正确。固定mix与mean的0.5残差平移匹配协议。

每B菜单15候选；B1额外selectedB0回退，16vs15如实披露。select在平衡10×887×8上取均方误差，等价cell/pair/query等权；字典插入顺序给固定破同分规则。普通程序不是新机制，也未验证与agent程序搜索等预算优势。

## 指标与门

metrics八query均值排序，k=ceil(0.1×887)=89；稳定argsort给固定pair顺序破同分；regret用预测所选89实际均值减oracle89实际均值，已解决协议原先minimum/mean歧义。主MSE/MAE、dose/cell风险、paired cell bootstrap seed/10000、7/10cell、删除任意cell均值正、study平均gain正均正确。只有保存selectedB0/B1产生gate，其他候选dev分数只记录，未事后改selector。

run中若study剩source<2会抛异常且中断，而非保存敏感性不可估。对此没有要求添加无用异常框架：本次独立metadata检查8870个dev-pair的剩source范围20..30，全部≥2，记录于STUDY_SOURCE_SIZE.json，该路径在冻结目录不可达。未来若改目录必须重新验证，不能拿本次PASS覆盖新设计。

## 合成证据的实际强度

test_models对所有30个模型预算组合检查：改变target query不改变预测；B0改变anchor不改变预测；改变另一target pair的solo/anchor不影响本pair；输出shape/finite；NCI正负分支。这些是有意义的模型接口信息隔离检查。

其中所谓selection独立性只创建一个未传入select的later数组，再同输入调用select。它证明不了全pipeline dev扰动隔离、reader行白名单或选择器调用链；必须如实称为固定输入的重复调用。当前全pipeline隔离证据来自以上静态数据流审阅，不伪称扰动实测。可后续把run orchestration纯函数化再测，但不为此窄任务引入大重构；本次不开值前并无必须变更要求。

prepare实际白名单和原始坐标/值映射、saved predictions及gate的独立复核仍须在开值后执行。成功只说明普通功能反馈是否有用；bootstrap条件于拟合模型与共同目录，不覆盖生物重复/共享study/训练不确定性。
