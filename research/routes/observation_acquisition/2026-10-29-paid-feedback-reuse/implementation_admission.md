# C6 实现准入审阅

2026-10-29。独立候选审阅者继续承担有界实现准入；本检查不是独立科学复算，也不是实际功能验证。未运行main，未打开原CSV、训练NPZ、开发结果或任何sealed文件；无网络。仅静态读C6实现、C4依赖源码、候选及运行前澄清。未与独立结果作者共享实现。

**结论：所读版本未发现阻止单次开发运行的具体逻辑缺陷；input_freeze完成并覆盖实际依赖后，可以按既定单次预算运行。** 此结论沿用初审的科学边界：即使开发阳性，也不能认证独立真实功能收益或Agent专有机制。

## 版本绑定

- e_c6_reuse.py SHA256 `132b3f3e2a66387b93dd4872682634fb4ae4807a6d69ee9f10641dce29a89f7f`
- candidate_c6_v1.md（包括运行前澄清）SHA256 `7d2c92f75473b6613fa328e22df685a5f8f4427be23ade704843b51abb11d765`
- C4/e_c4_budget.py SHA256 `1f84dc577410f3c056fdecfb391ff90514b4decc7f47bd4cd570f1e318c8553c`

input_freeze在准备中，本检查不假称已核其内容。启动前应记录上述实际实现/候选/依赖，以及C4 metadata_freeze、training_freeze、training_model的哈希；原CSV另由main按metadata源哈希核对。main逐项核input_freeze；训练工件还与training_freeze中的artifact哈希核对，训练/开发ID及566/243维度也断言一致。若准备过程修改已审实现，当前准入不自动覆盖该修改。

## 逐项核对

| 条款 | 静态观察及判断 |
|---|---|
| 首6来源 | 仅训练event/finite/global_rate与train tissue计算5伪样本收缩率；tissue13前6为首批。无开发响应或mask参与首批选择。无同组织训练样本时式子精确回退global_rate。 |
| 机会成本及13尝试 | rank8/rank1/knn/matched_blind均为首6+排除首批后的7项；所有策略断言13项且无重复。缺失只减少实际更新，不补测或扣除尝试。静态直接13项；未把首6作为预算外免费探针。 |
| matched_blind | 与rank8使用相同batch；概率来自未更新的rank8经验先验m/P和相同noise/CDF/窗。唯一被去掉的是消费首批反馈；不是拿另一个静态组织先验冒充matched模型。 |
| tissue_continuation | batch+组织剩余前7与tissue13断言完全一致；按澄清不另造重复实验臂。 |
| 训练冻结 | 不再调用fit_model，不重训/调秩/调噪声/换菜单；直接载入C4已冻结rank1/rank8及s、mu、sd、event、finite等。归一化方向和窗概率坐标与C4一致。 |
| 依赖副作用 | C4顶层仅定义/导入，其main在__name__ guard下；C6导入不会调用C4 main、读取CSV/NPZ或写C4研究产物。受控复用函数为sha/select_raw/number/labels/update/direct/probabilities/choose/paired_bounds。 |
| 决策oracle | select_raw读CSV字符串和metadata选行，按最小整数NLME_RESULT_ID及源行顺序选，不将未选响应转数。query仅对allowed首6项转换；后7项只在动作全冻结后的末态检查转换。不存在用后续读数回流选择的代码路径。同进程仍不是安全隔离，与协议披露相符。 |
| 全动作先落盘 | 全243细胞及全部7策略动作完成、直接解误差和实现/候选哈希检查后，先写actions_only.npz、actions_freeze.json及query_trace，再做选中后续末态验证；最后才完整转换菜单truth进行评分。 |
| 高斯全历史等价 | 对每个细胞的实际有限首6反馈，递推与直接精度矩阵解比较m/P，max差≤1e−8，并断言后7动作相同；末态再对自身已选13项中有限反馈核直接解。不把直接解计为独立科学臂。 |
| CDF和并列 | 复用scipy.special.ndtr的同一概率函数；负尾差截0，窗为空概率0；稳定argsort保持冻结菜单顺序，排除已选。kNN距离只用有限已见首批，训练缺失已在冻结s填0，稳定前5及1/(distance+.1)符合候选。 |
| 主事件 | labels为finite、严格log低高窗内各1e−8容差、LN_IC50≤0；未知保持未知，不当阴性。概率连续窗不加该容差，符合继承定义。 |
| 配对缺失 | paired_bounds先按集合移除共同动作；独有已知事件之差减对手独有未知得下界，加本方独有未知得上界。共同未知不会错误扩大差界。 |
| bootstrap/主门 | 243 SIDM等权，default_rng(20261029).integers(0,n,(2000,n))一份共享索引；linear 2.5%/97.5%分位。各比较下界均值≥.5且CI下端>0；联合门仅索引static_global13、static_tissue13、matched_blind。random/rank1/kNN诊断不替换主门。 |
| 单次预算及日志 | main入口拒绝已存在experiment_receipt；首次转换前标功能消费，记录逐次feedback accesses、动作及固定哈希。结束检查CPU≤1200s、峰值工作集≤2GB。只检查结束时预算，不是硬杀进程的资源沙箱；协调者仍须按预算监管。运行错误后不能删除receipt冒充首次。 |

## 实际执行的轻量检查

`python -B e_c6_reuse.py --synthetic`通过，输出“Synthetic contracts passed; no real data loaded”。其合成断言覆盖共同未知抵消、稳定并列/排除、两项有限反馈的递推/直接高斯一致、空概率窗。它不运行main，也不证明完整真实数据管线正确。

对C6源码调用py_compile.compile，输出写临时目录并随上下文清除，通过；未执行main。Python使用-B避免导入写入项目__pycache__。两项命令合计墙钟约1.94秒，未接近30秒CPU检查预算。未新写科学测试、未修改主实现或共享记录，仅保存本审阅文件。

## 保留条件

这是代码准入，通过意味着可消费已经授权的唯一一次开发运行，不意味着假设通过。真实运行仍需另一作者独立实现/核对行选择、端点、信息边界、后验、动作和主指标；任何实质差异先标invalid，不调规则重跑。初审对结果启发选择、共享NLME、拟合代理、两批真实费用及独立功能路径未落实的异议保持有效。

## 入口保护版本差异准入短注

同日运行前再次静态核入口：只有精确`--synthetic`调用合成检查，无参数调用main，其他参数直接SystemExit，不会因拼错参数启动科学运行。当前实现SHA256为`5c8964d50aa6b0e4ec672e9fa6aa2e194f0731d2cf9b18d56a6f16a32338a332`。将当前源码入口尾部静态还原为原三元表达式后，重建源码SHA256精确等于初审版本`132b3f3e2a66387b93dd4872682634fb4ae4807a6d69ee9f10641dce29a89f7f`，故科学main/函数部分未变。

已只读核input_freeze.json现有8项：前7项内容保持，追加C6实际实现的上述哈希和12771字节，并保留旧freeze哈希`1b56b3ccffd930ebd6020d19245209290289097193f2f503d77c50561639afda`。依赖覆盖准备条件已满足；本次未重读或重哈希CSV/NPZ等数值文件，真正启动时由main逐项核内容哈希。此入口保护及冻结清单变化获准，原准入结论扩展至此版本；未重跑合成/编译或科学检查，未消费真实数据。
