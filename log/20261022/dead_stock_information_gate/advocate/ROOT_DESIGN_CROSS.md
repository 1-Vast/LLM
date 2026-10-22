# 对 root 数值前设计的实际交叉意见

2026-10-22；在 INDEPENDENT.md 保存后。root 提出 DoseResponse-only，relative24h→72h LIVE primary，8外层 leave-one-concentration-out；每折 holdout一浓度全部contexts/wells；剩余7dose中hash定1validation／6train，选direct后7dose refit；两臂同完整liveprefix与staticfeatures，仅增dead；另D0-only／D24-only；replicates文件可能重叠，不进gate。

advocate 已实际回复支持这一设计，比自己的context2/1/1更贴近未测dose应用。以下问题已在响应开启前发给 root，不是事后更换分析：

1. **pooled out-of-fold ≠ 一个全局未见test。** 每个dose在它作为outertest时未进入该fold拟合，但会进入其余fold训练。这是nestedCV。全部fold、feature、model family、trials、threshold先锁，不能看8fold结果后选模型／窗口再用同结果确认。
2. **inner只1valdose的选模不稳。** 两臂同家族、同budget、同split、同fit/scaler边界；选择后可用7dose refit，但须对称且不用outertest。该限制决定解释范围，不在结果后改内层策略。
3. **独立性与权重。** 主评分dose→opaquecontext→well等权。若8dose含0剂量，明说control在readout总体里，不当额外drug任务；8dose同一药，不宣称跨drug／biologicalrun。没有跨run CI，也不以图像／wells填充n。
4. **预锁三层解释。** fullD优于Lonly=额外通道信息；若D0或D24同样好，只能static/calibration。不能把最好的D变体在fullD失败后替换成primary并宣称原gate通过；动态历史／latent turnover需额外证据。
5. **来源重叠。** 两source可能包含共同0/12µM数据，本轮完全不进replicates文件，避免伪external验证。
6. **deadstock定义。** 不用rawdead差分作death events，不按后来dead值选子组，目标仍真实LIVEreadout。

数据反方实际交叉后的语义修订：主文GFP定义为total、genericattachdata没有documented`intersect_live`补集映射，故上面的“真实LIVE”收窄为 **exact exported operational L count/readout**，在补集/分类映射认证前不称已证明的viablecellcount。不得用D≤L、列名或合理相关性猜语义。若模型预测阳性，首先只证明此测量读数的extra-channel value；不用于出生／死亡守恒或cell-survival机制主张。

另接受数据方要求：same-image固定均值是合法readout，不需证明三images互不重叠，但必须 `(file,context,well,dose,img,time)` 唯一，L/D同record、同imagepanel、同weights，missingness/masks/图像数在两臂一致；同image跨时间不等于谱系连续性。

这份设计回应覆盖独立稿的split建议；独立稿原样保留，不伪称LOCO为支持方最初独立提案。尚无数值、模型或新算法判断。
