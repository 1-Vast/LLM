# 固定LIST源码I/O审查：有静态形态与posthoc增长分析，尚无认证轨迹连接

2026-10-22，Asia/Shanghai。**两份固定源码已取得、SHA/size校验通过；未执行。它们提供可核的I/O契约，但不足将公开图像与真实schedule、增长轨迹、独立run配对。** 本报告是独立后续，不改写原paper/code-discovery阶段记录。

本轮2次顺序GitHub固定blob请求均200，完整API body合计 **33,603bytes**；解码源码分别14,280/9,694bytes。原始JSON、源码副本与hash/UTC/bytes在 `sources/NETWORK.json`。没有下载或读取CSV/XLSX/TIF，没有模型/实验/DeepSeek调用。源码数字仅算已公开source exposure，不是heldout药物响应；本次源码未包含可识别的实测Growth行数组，只见算法默认参数、时间窗口及分割阈值。

## Colony analysis.m 的实际定义

固定Git blobSHA `f4a48f96172fa803d1506c505dd46dcb2b1499a8`，本地副本 [COLONY.m](D:/MAESTRO/log/20261022/antibiotic_schedule_qualification/code_io_followup/sources/COLONY.m)。以下行号均对应该未改源码。

| 问题 | 直接源码证据 | 可以与不可以推断什么 |
|---|---|---|
| 输入单位/文件范围 | L27–35：`for imageNum=1:9`、`Colony%d.tif`；L38–42缺文件skip。 | 这是九个命名图像/stack的处理脚本，不是512个实验run或9种菌株的证据。文件名本身未编码drug、schedule、time、strain、run/chamber。 |
| 多页的含义 | L44–61把TIF page全部作为`num_slices`、组装volume；L64–71相对于middle slice配准；L75–89插值/3D平滑/阈值；L108–109 max-intensity projection。 | 脚本**将页解释为z-stack**，不是显式时间轨迹。没有时间轴metadata或检查；若未来提供的是temporal pages，不能直接套此代码。middle-slice配准和maxprojection会用全部page，故必须先认证page是z而不是未来时间帧。不能凭这段就断言原实验实际用未来帧。 |
| 量化state | L150–178：Sobel/形态操作，connected-components、`regionprops(...,'all')`；L231–235输出`Colony,Circularity,Area_um2,Perimeter_um,Centroid_X_um,Centroid_Y_um,Diameter_um`。 | 这些是当前图像或maxprojection上的2D形态量。L91–104生成3D rendering，但表中没有明确3Dvolume/growth变量。`MeanIntensity`在L220取出，却未进入L232–235结果表。 |
| 物理单位 | L11–13的`Scale`设定被注释；L180–186物理换算全部被注释；L188–192只是各属性恒等拷贝；L212–223和234–235却称micrometers/um。 | **不能由输出列名认证μm/μm²**。当前代码未执行像素标定；若无外部已校准像素关系，原始regionprops像素量与声明物理单位不一致。没有修改原作者代码，也未声称所有paper图值因此错误。 |
| 是否真正tracking | L177的`bwlabel`产生当前图像component号；L291–297形态筛选后重新编号`1:height(sortedR)`。全文件无跨time的track-linking或persistent ID更新。 | 文件名/README的tracking叙事不能替代可执行的跨帧连接。这两段不能支持same-colony early→late或共同prefix第二动作分支。 |
| 筛选/失败分母 | L291只保留Circularity>0.4、Area<2000、Diameter>5；L293–300空表时skip Excel export，否则写`Results_%d.xlsx`。 | 输出是筛后形态对象；缺Excel不自动等于零生长或安全。全尝试/未检出/筛掉对象需另有身份账本，不能将缺失转阴性。阈值是源码常量，不是本轮根据数值调的。 |
| 附加操作 | L320–371单页且非空时读自己输出的表，重新分割同一图像，centroid选择/variability展示。 | 仍是同图像分析，不是第二个独立生物功能实验，也不产生时间戳/药序key。 |

因此，这份源码没有出现由真实molecular measurement形成的state；它认证的是静态/空间成像形态定义。早期形态可否预测以后功能仍取决于外部真实时间与condition manifest，不由脚本自行给出。

## Calculation.m 的实际定义

固定Git blobSHA `4472a4bf24c001e66980755fb2b07cf9cb5d828f`，本地副本 [CALCULATION.m](D:/MAESTRO/log/20261022/antibiotic_schedule_qualification/code_io_followup/sources/CALCULATION.m)。

| 问题 | 直接源码证据 | 解释边界 |
|---|---|---|
| 必需输入schema | L10、16读`growth_data.csv`；L23要求`Time,Dose_A,Dose_B,Growth,Dosing_Type`；L19–20trim/drop missing Dosing_Type。 | 第五个**代码要求的header确为`Dosing_Type`**，不是Treatment/Condition/Sequence。尚未据本报告读取实际CSV的第五header或行值；可由独立白名单worker据此增补header资格。 |
| 正/反/同步顺序 | L29允许`A+B,A-B,B-A`，L31–34拒绝其他type。 | 代码确实支持三类标签，但没有药物name或液体操作日志；A/B是占位名，不认证真实药名、洗脱/追加、持续时间和切换。 |
| 时间窗口/单位 | L68–70取unique doses/time；L73–76 A+B使用Time≤6，其他两类使用3<Time≤9；L78–80只检查是否有Time=3。 | 这是分析窗口。**源码未声明Time物理单位，也未读取Lag/Switch/Duration字段**，不能把数字3直接叫3小时给药间隔；需实验protocol/metadata认证。A+B与sequential窗口也不是共同terminal time比较。 |
| 生长定义 | L103–115按dose-pair/time筛选，重复行`Growth`按时间求mean/std；L151、174和193–194再对所选时间窗口求mean。 | Growth是外部表已有标量，源码没有给出其原图、area/count/volume/OD定义、baseline归一化或单位；最终是**窗口平均Growth**，不是已认证末帧生长或存活率。不能从这份代码建立morphology→Growth来源连接。 |
| 条件/重复/任务key | L65仅按Dosing_Type分组；L103–105仅dose/time匹配，L112–113按相同time汇总。 | 输入required schema没有strain、drug pair、nutrient/stiffness、run、chamber、colony、replicate或prefix ID。额外列即使存在也未用于grouping；除非一文件被外部manifest证明只含一固定pair/context，否则不能防止混组。std不是认证的独立培养重复不确定性。 |
| 4PL与CI | L38、47–50可读`curve_fitting.csv`参数；L41–44有默认bounds；L130–181分别用单药zero-other-dose数据拟合4PL；L193–220用同窗口Growth反求equivalent-dose及Loewe CI，再logistic变换。 | 这是对已测Growth的posthoc汇总/拟合，无动力学state transition或未测动作预测。`CI_normalized`不是作者之外的独立实测功能终点。A/B仅L138、161的generic label，不能从它获得真实药名。 |
| 是否用后续信息 | L134–135在整个该Dosing_Type的`c_data`求单药max（不局限v_t）；L151/174/193聚合窗口Growth，L156/179拟合。 | 此脚本本来就是全表descriptive analysis，没有earlier decision cutoff。若把其输出/拟合参数当早期已知state，会引入后续Growth；需要新的按query-history限定的实现，不能直接将该posthoc脚本说成online agent。此处未执行或修改它。 |
| 输出保留什么 | L241–249结果为`Dose_A,Dose_B,CI,CI_normalized,Mean_Growth,Std_Growth,Dosing_Type,R_squared_A,R_squared_B`；L254写`synergy_results.csv`。 | 丢掉Time与潜在run/colony标识，输出不是轨迹manifest；不能只用synergy_results恢复early/late配对、独立任务或同prefix分支。 |

## 资源决定与最少后续资格

本轮状态为 `SOURCE_IO_AUTHENTICATED / TEMPORAL_SCHEDULE_GROWTH_JOIN_NOT_ESTABLISHED`。已认证可公开获取的源码契约，不等于认证其中CSV是实测、数据完整或已够RSI任务。

根代理另已做schema-only检查，通知`growth_data.csv`有900数据行/5列，其事前白名单尚未导出第5header。本报告不重新下载或打开其sealed文件，只用已取得源码给出下一项白名单依据：`Dosing_Type`。最便宜的依赖检查是**仅身份/缺失流**：认证该header与三种label、Time/dose网格和每格重复/完整性，同时Growth只允许missing/非missing旗标；再找能把generic A/B和一个CSV映射到真实drug pair/strain/run/schedule的独立metadata。900行不能单独证明900actions或多个任务。

若外部映射不存在，保持未合格；不要从9个形态示例和一个generic Growth表拼接不存在的early state→future function世界。若取得真实时间轨迹，须先区分z/time，冻结当前时点可计算的count/area/增长率基线，并按同预算比较强直接prediction、普通动力学/重训、AL与程序搜索；不以源码存在批准架构。当前不提出性能、新颖性或继承/RSI成功。

本阶段source原样未改，未“修复”第三方脚本、没有运行它来产生任何数据。所有本阶段协议/报告/源码证据在此目录，下载/校验脚本只在 `research/antibiotic_schedule_qualification_20261022/advocate_code_io_sources.py`。两次请求均通过固定Git SHA及size校验；这些软件完整性检查不是生物实验结果。

## 主张范围追加：何时需要共同prefix

共同prefix的替代第二动作是**同colony/匹配prefix的state-feedback control或特定state-collision检验**所需资格，**不是所有跨实验query/update replay的前提**。合法的静态schedule菜单可以支持研究agent每次选择一个独立实验、更新模型并改进后续未查询schedule决策，只要动作真实、条件/终点/预算与失败可追溯。当前文件不足建立轨迹join，并不因此判定所有这种较弱replay不可能。原code-discovery末节将共同prefix泛列为dev开值前提，已另以 `../code_discovery/SCOPE_ADDENDUM.md` 追加范围更正；不改写已封阶段。
