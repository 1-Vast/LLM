# 中止后的真实交叉质询与语义诊断补记

2026-10-22。`POST_RUN_REVIEW.md` 和 56-check 审计先完成；其后收到 advocate 的独立稿与限域诊断消息，再读 `data_auditor/target_failure_audit/DIAGNOSTIC.json`。未读 raw CSV、未拟合、未重跑、未追加网络。原 independent/review/failure/cache/protocol 均不改写。支持方另存原始消息 `advocate/POST_FAILURE_RAW.md`。

## 支持方向反方的两个问题与实际回答

**问1：首折训练标签转换失败且尚无 direct fit/折结果，是否严格保留 D 条件信息为未检验？前缀收敛与 L+D≈total 分别最多支持什么？**

回答：是，本次 D 条件信息没有可用判决，不能写 channel negative。训练未来 LIVE 转换已开始，但完整 ytrain 未返回，未进入 direct fitting、无 FOLD/combined/RESULT。prefix success 最多说明给定参数化、边界、starts、cap 下满足该优化器数值停止条件并给有限 forecast；不证明参数可识别、生物真实或未来预测准确。L+D≈total 最多证明已暴露 prefix 的导出算术关系与共用信息；不证明死亡事件数、true viability 或独立误差，不能据此修补 L72。

**问2：若 L72 有值不满足非负域，新来源最低需要什么测量/独立性资格，才不是换字段救结果？**

回答：在新本地性能数值之前，先锁定 primary assay/endpoint、字段单位与符号语义（计数或 signed/normalized readout）、活/死/总生成关系及适配 observation/likelihood、time-zero/合法 prefix/实际 future target、固定 well/image panel 与共同缺失规则。记录 physical well、experiment/run、文件复用与样本重叠，以及与开发来源的关系；不确定 metadata 保留 opaque 并限制运输解释。若只是 operational-readout forecast，不强求新湿实验或虚构生物 run；若升级 core/general functional claim，必须实际有多药/背景与独立结果验证。新数据或新 observation model 均须有独立科学理由、完整曝光声明和新预注册问题；旧 gate 仍是 qualification abort，不能被未来结果替代。

## 反方向支持方的挑战与实际答复

挑战：若负值均兼容 `total−D`，会否过强推断整个来源无用/全部 live 导出不可靠？反过来，即使 total 非负、GFPtotal 被口头近似为 live，能否明确拒绝本 gate 换 target 重跑？未来什么一手定义足以支持 total 的 operational-readout 使用而不误称 viability？

支持方实际答复：不把当前非负计数目标失效扩张为整源无用。4/288 个 image 的 finite negatives 与 exact difference 只支持差值式导出算术及其与当前域冲突，不证明背景校正、制作意图或 true viable 定义。明确拒绝在本 gate 用 total 当 LIVE 重跑：非负 total 可能是不同的标记库存、回答不同问题。

未来若 primary methods/source scripts 逐项定义 GFP/RFP、total 的计数/校正/聚合/丢失过程，并有独立功能关联，或把问题明确限制为标记总量预测，则 total 可作其 operational readout。仅口头 GFPtotal≈live 不足称 viability。仍需新科学理由、曝光声明与 protocol，不恢复本 gate，也不自动产生药物发现功能价值。支持方另强调：测量定义合格不等于 D 有信息，仍需保留 D0/D24 与强 direct 对照。

反方接受上述边界。这里“新任务/独立理由”不等于禁止所有同资产的测量研究；它要求不将已暴露异常后的新 endpoint 包装成当前冻结检验或独立确认。当前本 gate 不继续改字段/transform。

## 限域诊断带来的新增事实与解释限制

诊断只读 72h LIVE 的 288 image records/96 wells：284 非负，4 finite negative，无 missing/malformed/nonfinite。四负值均为 25µM：H7/mcer-1e3/img1=-2；H12/mcer-3e3/img1/2/3=-24/-1/-15。仅此四坏行额外打开 D/total，分别为 `142−144=-2`、`357−381=-24`、`468−469=-1`、`472−487=-15`，全精确；未开其他 future D/total。

H7 的三 image mean=26/3，仍违反事前 per-image 非负规则；H12 的 mean=−40/3，其 `mean+1<0`，因此**即使事后想改成只要求均值合法，也仍不能定义注册的 log2(mean+1)**。这不是仅以过严 image guard 误杀一个全体均值有效的资产。不能以少数坏值为由过滤、clipping、填补或换未来时间。

该诊断与 arithmetic-compatible subtraction 一致；不认证作者有意使用 signed convention、背景 correction、mask overlap、真实死亡多于总细胞或真实活细胞为负。current nonnegative-count transform 与观察不兼容，不能由此推全资产生物内容失真或所有 observation model 无效。288 image 不是 288 独立生物单位。

## 对 functional_auditor 的实际质询

已发三个具体问题：exact total−D=L 是否仅能叫 difference-compatible、明确拒绝背景/制作意图/真实细胞解释；是否保留 H7 per-image 与 H12 mean 两层资格；未来 signed observation 理论上可研究是否仍不授权本次改 likelihood/total target 重跑。

functional_auditor 实际答复接受三问：其最终 REPORT 明确不推作者 intent、background correction、mask overlap、负 viable 或 D>total 的生物解释；仅称四行 difference-compatible arithmetic。保留 H7/H12 两层区别，不因 signed-difference 的理论可能性授权改 likelihood、total 或 retest。288 image 只作审计分母而非独立 n；无科学信息比较，仅 prefix 程序执行与 export 诊断。其自有 `target_failure_audit/POST_FAILURE_CROSS.md` 亦保留双方原问答。至此与支持方、审计方两次真实交叉均已完成。

## 阶段决定

支持 root 的 `STOP_REGISTERED_OBSERVATION/TRANSFORM; NOT_CHANNEL_NEGATIVE`。当前 D-history vs L-only/D0/D24、同信息 kinetics vs strong direct、mixture/family、world/agent、继承、联合与 RSI 均未获本 gate 科学比较。已记录的是数值程序执行资格、导出算术与目标域失败。

STACK v1 的 snapshot 资格与后续 raw manifest 是新来源资格任务，不能从可见 landing/snapshot 直接推 raw 可用、功能 readout 合格或独立性成立。本反方未对此追加 GET 或性能分析。
