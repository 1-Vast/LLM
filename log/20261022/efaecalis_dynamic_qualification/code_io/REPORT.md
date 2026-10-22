# Pinned v1.0 original-code I/O qualification

2026-10-22。**CODE_ASSUMPTIONS_QUALIFIED; INPUT_DATA_PROVENANCE_AND_SAMPLE_JOIN_NOT_QUALIFIED.** 依协议3 GET全部HTTP200，combined body **39,382bytes**；无redirect、retry、403、作者代码执行或datafile读取。source receipt/URL/UTC/hash在`NETWORK.json`，原GitHub JSON与decodedsource保留。README与source的Gitblob SHA1由 `blob <length>\0<bytes>`独立重算一致。

## Exact source identities

- Repo/tag：`jamaltas/Temporal_Collateral_Sensitivity`，**v1.0**，由官方Zenodoversionmanifest认证关联。
- **完整tree SHA `1a2c164ab019510d45c1e9165b109492b6ad7236`**；41entries，truncated=false。此为treeSHA，不称commitSHA。
- `README.md` blobSHA **`e88892c6df960990946e1b282098efaee9159af8`**，982decodedbytes，SHA256 `0465f0176bd0a9835edc42a037f5619c67cc7552740a3bb9a2d230270644da06`。
- `main_td.rs` blobSHA **`0abcf093fcbf14a3c1856e4eb46fa8fb47fd9f75`**，19,427decodedbytes，SHA256 `9cf1999dea486b1eca82ad04c9ac685ca89f6d9a588114b94f98232dee477b3e`。

没有notebook，无outputs/plots/response arrays。先以`MDP_NUMERIC_REDACTED.txt`保守遮去全部numericliteral读完整方法；此redactor也改变了部分Rusttype/range的文本形态，故它只是带原line号的审阅投影，**不能当作者源码语法或执行输入**。随后`MDP_IO_CONTRACT.json`只导出明确scalar算法参数、discretization、rowindex与add/clip语句，均为方法常数，不是observed response。rawsource未执行。

## Transition exact operator

`main_td.rs` L17–24设5drug维度、4replicates，枚举每个坐标从−5到25的完整离散state笛卡尔积。L33–47、65–79、94–108、123–137分别读取day8/day6/day4/day2 CSV并为所有state构建transition。药物d与replicater只用 **row `d*4+r`** 选profile，完全不按currentstate再选择row。

`discretize_data` L203–227对每个输入float作固定阈值离散：`<−2→−2`，`[−2,−.25)→−1`，`[−.25,.25)→0`，`[.25,2)→1`，`≥2→2`。这是方法设计，不是实测响应。

`get_next_resistance_state` L229–236逐坐标 **`s′=clip(s+discretized_profile[d,r],−5,25)`**。因此同一drug/replicate/timeprofile增量被运输到任意枚举的耐药state；除边界clip外，增量不依赖s、previousdrug/genotype或state产生历史。源码没有从不同startingbackground或真实switchbranches估计conditionaldelta，也没有验证这种translationinvariance。

**不能由本源码断言该CSV row确为“WT累计collateral delta”或“相邻时点差分”。** `main_td.rs`直接离散CSV，不作day8−day6等差分；四个CSV实际数值/构造代码未取得。论文实验测相对ancestor的collateralprofile，与源码的additive-delta用途之间仍需真实CSV生成/列schema衔接。该未资格桥不能默认为因果actiontransition，也不能擅自诊断作者算错。

`one_step_lookahead` L285–307在replicate维等权求平均；`simulate_policy` L390–409每step重新uniform随机抽replicate，未绑定同一真实lineage身份跨step。这是一个有限经验增量的随机仿真，不是观察到每条真实lineage在任意action下的轨迹。

## Future profiles are explicitly available to planner

程序先读 **day8_rust.csv**为6→8时段，算末段policy，模拟每个initialstate的future reward(L33–63)。再读day6、day4、day2，依次把后段future-reward vector送入早段 `calc_optimal_policy_td` (L82、111、140)，`calc_future_rewards_projection`按末态查询下一段futurevalue(L428–442)。

因此早段policy已使用更晚测得的profiles和这些profiles下模拟出来的values。这里称**已知未来profile的规划/oracle信息条件**，不是指违规或projectheldout泄漏：原论文就是用已完成实验的时变profiles展示规划，源码未声称自身在线预测未知未来profile。若本项目比较前瞻研究Agent，所有臂必须同样知道未来，或必须只把pastcut观测给估计器；不能让此oracle与无futuredirect模型不公平比较，也不能把该planning函数命名为RSI。

源码的ordinaryvalueiteration及MonteCarlofuturevalue是原作已有普通操作；没有可编辑研究程序、跨新任务继承或共同起点改进策略实验。此资格不产生WM/Agent/RSI效果。

## Actual I/O and keys

唯一选中源码的四个必需CSV **`day8_rust.csv`、`day6_rust.csv`、`day4_rust.csv`、`day2_rust.csv`全部不在完整v1.0tree**。这只是该pinnedtree的明确缺项，不推断全网/其他版本不存在。

`read_csv` L186–201使用csvReader逐行numericparse；parse失败用0.0，未读入sample/drug/lineage/time的命名字段，也未显式按headers做身份mapping。主循环隐含每timefile按5drug×4replicates的rowblock排列、每row抵达5个state坐标；没有所需drug-order映射或真实lineageID。每profile长度经zip使用，源码未为identity/schema建立独立验证。它不是可直接拿来认证samplejoin的manifest。

time只由filename与调用变量命名；source输出 `opt_policy(0-2/2-4/4-6/6-8).pickle`和`transition_matrix1..4.pickle`。这些是生成结果，不是新的实测状态。README说大policyfiles未放GitHub；该statement不能认证运行可复现，因为输入CSV缺项且本轮未执行。

完整tree存在：

- `TempData.mat`与`AnalyzeIC50s.m`；README说用于IC50分析及Figures2C/S1/S2/S3。
- `*_WT/day2/day4/day6/day8*.mat`文件组，文件名前缀含CRO_DOX、CIP_CRO、DAP_CRO；README说QuickLook/MakeHeterogeneity脚本读time-dependentMAT生成Figure3。文件名不自动认证两drug角色、drug菜单全体或replicate/samplekeys。
- `HeatmapWorkspace.mat`、`enumerate_plot_all.py`，README指向S6ABCD。
- reward/statepickle及plot_mdp_data.py；本轮全部未下载。

没有从tree文件名找到evolvedWGS/transcriptome身份；不据此证明分子数据绝不存在。现数据状态仍按phenotypicresistanceprofile。

## Minimum next objects, not auto-authorized

原3GET预算已用完；若独立资格仍有需要，可先读 **`AnalyzeIC50s.m` blob `a774f7ebaab6518c99be48ea4158ef780ead31a6`**（6,061bytes）核对TempData.mat变量/columnorders与5drug/lineage/time mapping；它可比MAT响应读取更早确定schema。若专门核实timepointMAT，下一源码为`QuickLook2CRODOXFigPanel.m` blob `a50221c16d5de779117e263da2a83f30f2c1c0e1`，4,497bytes。两者均是具体下一对象，不额外执行GET。

最重要仍是四个 `day*_rust.csv` 的来源与“cumulativevsincrement”生成语义；当前tree未给出对应生成文件，读plot或data不能自动弥补。S1Data由另一个functional auditor独立核验，本人未重复PLOS GET或读取其response。若该表能提供exactkeys，可完成phenotypehistory→laterfunction的窄任务资格；它不自动验证任意state的additive transport或任意多轮换药MDP。

## Decision boundary

原作确有dynamicphenotypeMDP，而且这份代码的两个关键假设现在可审计：**state-independentadditiveprofiletransport**与**未来profile已知的backwardplanning**。是否能从真实prefix状态预测未来profile、是否需要state-dependenttransition以及研究程序能否更有效改进，均未由本源码回答。本轮不提出新机制，不重开已停候选，不把取得代码当性能或新颖性。
