# 最新辅助研究更新：独立只读审计

2026-10-28。**新增结果是真实进展，但仍未补齐本对话 CL1/CL2 所需的实测作用锚、独立功能决策收益或迁移证据。** H1b 保存结果确为 16/16 通过，不过其统计量只观察第一输出维度的量化余数；S2c 已发展到 v0.2 并取得执行批准，其设计期 headroom 还存在真值公式与条件采样合同问题；M3 已有追加纠正，原始 `no_increment` 保存，不能再解释成所宣称 M3/TMLE 的合格否证。

本报告独立读取实际协议、代码和保存 JSON，再对已存数值及字节作核对。没有导入科研 runner、训练、模拟、联网或读取 sealed 文件；仅新增本报告与 [计数及完整清单](D:/MAESTRO/research/2026-10-28-agent-a-proximal-program-pilot/latest_auxiliary_update_counts.json)。继承父配置，`effective_model=unknown`，不声称 Terra 身份。旧审计只用于定位；以下判断逐项针对本次实际版本。

## 本次真实文件与版本

完整文件名、字节数、UTC mtime 和 SHA256 在计数 JSON 的 `inventory`，另有依赖、纠正及临时副本的 `supplementary_inventory`。本次清单共 49 个目标文件：

| 目录 | 文件数 | 本次实际最新状态 |
|---|---:|---|
| `2026-10-28-m1-stage2b-h1b-prereg` | 10 | floor 校准、新测量协议、独立挑战与执行批准均存在 |
| `2026-10-28-m1-stage2b-h1b-run` | 9 | 保存 `h1b_measurement_pass`，16/16 通过 |
| `2026-10-28-m1-s2c-planning-prereg` | 19 | 审计期间新增 v0.2、挑战与 Lead 批准；本报告已重读，不停留在 v0.1 |
| `2026-10-28-m3-stage3-run` | 11 | 原运行结果与两份追加纠正并存 |

关键证据指纹：

| 文件 | mtime UTC | SHA256 |
|---|---|---|
| `h1b_result.json` | 08:10:03 | `2eca912bf74100674af8e6b02ffcecd000e22ed3d44611fb5eb5feb6b21f06c9` |
| `run_h1b.py` | 07:58:23 | `4872d865700e63a3f35da45563b09c71a5d7083e7994c3597b37a04e35c928f4` |
| `headroom_design_m1_s2c_v0_2.json` | 08:29:18 | `89c3586b596013a23651c768913bb84a41ea33b2da00718ba590b21375013741` |
| `headroom_design_m1_s2c_v0_2.py` | 08:29:04 | `40f44dd4ebdfb187e5e388e639b7552094beb464a10cd8c540a3fee92070d5b1` |
| `DECISION_R204_M1_S2C_EXEC.md` | 08:31:29 | `add6b81b3c24cbaf614ce4e2751fe39fdac33f825546a88395305b876f15e4dd` |
| `m3_stage3.json` | 07:28:43 | `609283453042b9a64c2cd3822725c0beb1e2730ccac8b342ac32001a536eb68c` |
| `ERRATA_M3_STAGE3.md` | 07:49:13 | `6cd990188cb01f93ccd48ba51752ecb31b615aa2629a1790e3cda7468e82c7f3` |

这些时间描述本地文件，不证明外部预注册不可修改。各项含义由实际内容核定，SHA 只证明字节。

## H1b：保存通过成立，四维条件密度认证不成立

[新协议](D:/MAESTRO/research/2026-10-28-m1-stage2b-h1b-prereg/PROBLEM_H1B.md)和[执行结果](D:/MAESTRO/research/2026-10-28-m1-stage2b-h1b-run/h1b_result.json)确实属于独立的新 H1b 测量：B=16、N_eval=32768、K=1，固定动作 a=0，16 个 d×N_train 格。独立读取保存数值重新判门，16/16 标志均正确，TV 最小 0.0096435546875、最大 0.02337646484375；最小容差余量为 0.02462353515625。floor 表有 60 行；按保存表重新执行选择算术，选中项和由 q95 推导的容差均一致。14 个冻结链条目当前哈希全部匹配。

本次实际比较了 `tmp/h1b_run1/h1b_result_final.json` 与正式 JSON，字节相同；final CSV、diagnostics 也相同。因此不能沿用“只有自报两跑、未找到副本”的旧缺口。它证明现存副本一致，独立进程执行过程仍属于记录所述，不能单凭相同文件推断。

关键限制来自[当前源码第 58 行](D:/MAESTRO/research/2026-10-28-m1-stage2b-h1b-run/run_h1b.py:58)：

`cell = (q0 + 256*q1 + 65536*q2 + 16777216*q3) % 16 = q0 % 16`。

这是精确代数恒等式。q1、q2、q3 完全不影响分箱；q0 也只保留低四位。校准网格所有 B∈{16,32,64,128,256} 都整除 256，均不能看到后面三个维度。该量可以在后三维任意改变时保持不变；第一维相隔 16 个量化格的值也可落在同一桶。TV 在这个粗化映射上小，不能推出原四维 TV 小。

另外，[run_cell](D:/MAESTRO/research/2026-10-28-m1-stage2b-h1b-run/run_h1b.py:71)把不同 X 的 Y 汇总成一个直方图，只训练、评价 a=0。因此它既不认证给定 X 的条件规律，也不认证 a=1/2/3，更不覆盖 S2c 四动作规划所需的全部条件核。**恰当可取结论是：在该合成环境、a=0 和退化分箱统计量下达到冻结阈值。** 不据此认定已训练 C-MDN 实际失败或发生条件反转。

floor 还有三项需要收窄：

- [floor oracle_y](D:/MAESTRO/research/2026-10-28-m1-stage2b-h1b-prereg/floor_calib_h1b.py:95)生成 X、分量、Y 后整体拒绝越界样本，下一批重新抽 X；这是对联合样本按 Y∈box 筛选，会按接受概率重加权 X。H1b 执行则固定正态 X，调用 `PTheta.sample_y(x,a)` 作条件截断。两者没有相同的 X 边际合同；本次未量化这一差异对 q95 的大小影响。
- [power 算术](D:/MAESTRO/research/2026-10-28-m1-stage2b-h1b-prereg/floor_calib_h1b.py:205)直接把旧 4×4×4×4 分箱的 excess=.0599，加到新余数分箱的 floor 上作正态近似。不同粗化统计量的 excess 无法这样搬用；`power≈1` 不是本新统计量对旧模型误差的已验证功效。
- 实际 p 估计种子是 `20261801+d`，即 20261809、20261817、20261833、20261865；20261833 与一个 H1b cell seed 数值重合，与“floor 801–810、集合 disjoint”文字不符。不同随机库的数值重合本身不证明泄漏。执行 JSON 把四个 d 的 `floor_q95` 都写成 worst-case .01642609，和校准中 d8/d32/d64 的专属值不符；不影响本次 TV≤tol 的算术，但不应据该字段宣称逐维 floor≤tol/3。

H1b 新 pass 不改变旧 C216 的冻结输出；关于 C217 的“q95 不是不可达下界”纠正也继续保留。新协议没有授权把旧失败改为通过。

## S2c v0.2：分析合同有改进，执行资格仍有实质缺口

[v0.2 设计](D:/MAESTRO/research/2026-10-28-m1-s2c-planning-prereg/DESIGN_M1_S2C_v0_2.md)和 [Lead 决定](D:/MAESTRO/research/2026-10-28-m1-s2c-planning-prereg/DECISION_R204_M1_S2C_EXEC.md)已经存在。v0.1 的 `.05` 停止与 `.10` 进入标准冲突已修复：v0.2 明确 `headroom_required=.10`，停止条件统一为 `<2δ=.10`。本报告不再用已修复的阈值冲突否定 v0.2。

可取进展包括：在候选结果前计算基线 regret；六个 `candidate−baseline` 比较统一 Holm；改善使用单侧下尾；计划把 raw regret 和 paired D 分存、按独立 replicate 给 CI；规定等价与标准方法复制的停止条件。这些改进直接对应了 M3 暴露的错误。

当前保存内容仍是 `design_headroom_only_not_candidate_execution`，不是候选收益结果。保存 full mean=.22625306，CI [.22094996,.23155615]；constrained mean=.15141651，CI [.15007466,.15275836]。用保存 mean/SE 重算 t19 区间与其在舍入精度内一致，两个 mean 都超过 .10；full 所选动作 3 为18次、1为2次，constrained 的20次均为1。JSON 未保存每次 replicate 的 raw regret，因此这是区间算术一致性核对，不能称完整 raw 重算。

**“解析高精度真值”当前有源码错误。** [v0.2 第 130 行](D:/MAESTRO/research/2026-10-28-m1-s2c-planning-prereg/headroom_design_m1_s2c_v0_2.py:130)用 `exp(log_phi_lo + log(max(zlo,1e-300)) - log_prob)` 表示截断正态矩中的 `zlo*phi(zlo)/Z`。当 zlo<0 时，这会把应有的负贡献变成近零正值；zhi<0 的相应项也存在同类问题。正确方差中的项为 `(zlo*phi(zlo)-zhi*phi(zhi))/Z`，不能丢掉符号。文件采用 log-space 并不修复该代数错误。本次没有重跑真值或候选，不能判断修复后 headroom 是否仍超过 .10，不能把现值认证为正确真值下的 headroom。

**条件采样也不保持逐个 X。** [sample_reward 第 157 行](D:/MAESTRO/research/2026-10-28-m1-s2c-planning-prereg/headroom_design_m1_s2c_v0_2.py:157)按“已接受数 got”切下一段 X，接受掩码中的被拒 X 没有被逐项保留；若一批中间拒绝了部分行，下一批从 got 开始，可重复已接受背景并跳过某些被拒背景。函数因此没有实现其所称“每个给定 X 下的截断条件采样”。另在评价阶段直接删除非有限真值的 X，却未保存每次删除数和实际有效 N；应核定评价人口是否仍为冻结分布。静态代码足以定位这些问题，但本次没有计算其数值影响。

本次用文件差异核实：v0.2 仅新增阈值/语义字段、停止条件及输出文件名，以上采样与矩公式未变。因此这些是当前版本问题；不是把 v0.1 缺口无条件迁移到新版。

同信息、同预算目前也只能视为计划：

- 主基线 `P_empirical_mean` 每动作4096样本，明确丢弃 X；条件模型击败它最多说明使用背景信息的价值，不能单独证明新的共同学习原理。
- 候选定义就是 C-MDN 条件密度+每动作 MC；同族又列 `P_conditional_density_MC`，尚未给出两者可区分的模型/学习/推断合同。需要先判等价；单列名字不形成强基线。
- 没有候选与各基线实际消费的共享训练记录、标签、oracle 可见性、调参次数、训练与推断计算 ledger。总 caps 和 S=4096/动作不能替代逐方法同预算核验。H1b 的 a=0 通过也不能替代四动作训练覆盖。

这些问题不抹掉现有批准文件，但独立科学判断不能由批准或 SHA 匹配替代。现阶段不足以接受“headroom 已正确认证、候选比较可直接解释为独立增量”的说法。

## M3：纠正记录可确认，原始负结果的解释已收窄

[ERRATA](D:/MAESTRO/research/2026-10-28-m3-stage3-run/ERRATA_M3_STAGE3.md)、[主审通知](D:/MAESTRO/research/2026-10-28-m3-stage3-run/ROOT_CORRECTION_NOTICE.md)和 [corrections_result.json](D:/MAESTRO/research/2026-10-28-science-contract-corrections/corrections_result.json)均真实存在。原结果 SHA 与纠正文件所存 SHA 相同，也与 `tmp/m3_stage3_final1`、`final2` 的现存 JSON 字节相同。本次保留原 `no_increment`。

独立对照源码及保存数据，以下纠正确实成立：

- [原比较映射](D:/MAESTRO/research/2026-10-28-m3-stage3-run/run_m3_stage3.py:222)用 baseline-vs-standard 的 p 做 Holm，candidate 不在映射中，随后默认其 p=1；[单侧函数](D:/MAESTRO/research/2026-10-28-m3-stage3-run/run_m3_stage3.py:174)对改善方向 D<0 使用上尾。保存数组实际是 `R_arm−R_standard`，不是字段名所称的 raw regret。
- 本次从保存差值重建六个 candidate−baseline 比较，均值依次为 +.01/+.01/0/0/+.01/+.01；非零比较 t9 CI=[−.01262157,.03262157]、单侧下尾 p=.82828180，Holm 后均为1。观察没有变成正面；这是审计重算，不替换原冻结分析。
- [headroom=1−regret](D:/MAESTRO/research/2026-10-28-m3-stage3-run/run_m3_stage3.py:359)保存为 .9797；原基线 mean regret 由它反推为 .0203，故本已评价批次的最大可能改善小于 δ=.05。raw baseline R 未持久化，不能说完成了 raw R 全量重算。
- [生成器](D:/MAESTRO/research/2026-10-28-m3-stage3-run/run_m3_stage3.py:106)按实际 w 采反馈，[learner](D:/MAESTRO/research/2026-10-28-m3-stage3-run/run_m3_stage3.py:127)却除旧 b。本次直接用已存九格表作期望算术：target=.455、用旧 b 的 DR=.38436007334764205、用实际 w 的 DR=.455，浮点恒等残差约5.6e−17，与追加纠正一致。这是权重合同检查，不是修复后的 learner 效果。
- candidate 是固定 `0.5+0.5*score`；所称 TMLE 是 `sigmoid(2*score)`，均未拟合预注册 epsilon。full-history/standard 同为格点经验均值；固定格内 H 的 IW 也约成均值，value-aware 为正仿射。没有七种可区分强算法。

源码确实在各 arm 之间复用同一反馈和评价流，各 arm 的评价使用自己的 argmax 动作与 held-out h、已知 μ。这些正确部分可保留。实际概率/损失/目标合同错误仍不能由共享流和相同预算消除。新增的 epsilon 数值拟合检查是构造合同测试，不表示原七臂已按正确算子重训。

因此最新 M3 应解释为：**原输出保留；所宣称方法的合格比较尚未成立；没有新增有效算法成功或失败结论。**

## 和 CL1/CL2 的实际关系

以本对话[冻结候选 v3](D:/MAESTRO/research/2026-10-28-agent-a-cell-language-mechanisms/CANDIDATES_v3.md)为参照，不能只因同有“生成模型/规划”一词就合流。

| 本对话所需证据 | 最新辅助结果能提供什么 | 仍未解决什么 |
|---|---|---|
| CL1：真实近端作用 m、固定外部功能 Y、剂量/时间及独立重复 | H1b 提醒测量必须保留条件和语义；M3 提醒把实际学习算子写清 | 四目录没有新增真实作用或功能数据、条件配对表或独立培养重复 |
| CL1：真实反馈同时更新程序概率与响应模型，并复用到整药/背景留出 | 可以借用共享输入、raw/paired 分存和等价审计的记录方式 | 没有程序责任/策略与执行模型共同学习结果，没有同信息普通程序网络/自由潜码检验，没有化学实现或背景迁移 |
| CL2：给定冻结 q0 的前逆合同、真实反馈、独立功能验收 | S2c 的合法菜单、真值隔离及六比较规则可作评价设计素材；M3 的实际 w/b 纠正有直接合同价值 | S2c 是四动作前向密度+枚举 MC，没有统一前逆学习、参考先验 q0 校验或独立真实功能验收 |
| 独立药物决策收益与迁移 | 有合成端点评价和失败解释的改进 | 没有药物收益、迁移或 LLM 特有增量证据；小菜单枚举也未建立逆生成必要性 |

有价值的接续是共享这些具体的合同纠正和测量盲点。进入新的比较前，需要核定 S2c 的有符号截断矩与逐 X 采样、保存 raw R 和有效样本数、明确候选与条件密度+MC的差异及完整预算；本报告没有执行修复或重跑。CL1 的下一项决定性证据仍是源表核定后的实测作用—条件—功能接口，CL2 则仍需受控分配与独立功能面板。辅助合成结果不能代替这些数据。

审计范围以计数 JSON 的快照时间和文件指纹为界；这里没有读取或认证任何后来新建的 S2c 执行目录，也没有修改对方文件、旧 verdict 或共享索引。
