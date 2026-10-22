# 失败运行后的独立反方审查

2026-10-22。范围：读取 frozen implementation、冻结清单、prefix-only kinetic cache、运行/失败与 synthetic test 输出；**未读 raw CSV、未拟合、未执行 gate/fit、未追加 GET**。审计代码 `research/dead_stock_information_gate_20261022/skeptic_audit_outputs.py`，结果 `skeptic/POST_RUN_AUDIT.json`。独立审计 **56/56 checks pass**；这是产物/规则一致性审计，不是 56 个生物实验或独立模型性能验证。

**裁决：DATA_TARGET_QUALIFICATION_ABORT_NO_INFORMATION_RESULT。** 不存在本 gate 的主要或支持性分数，不能记录为 dead-channel negative、模型预测失败或新机制阴性。root 已明确不 filter、clip、换 target 或重跑这次 gate。整体 world/agent/inheritance/RSI 目标仍未完成。

## 发生了什么，哪些数据确实被打开

在 96 孔全部 prefix-only local fits 完成并保存缓存后，首次 outer fold 的 `ytrain = labels(...)` 经 `mean_field(...,72,'intersect_live_cells')` 触发 `ValueError: invalid_observed_readout`。这是预定的逐 image 非有限/负数 guard，并非优化器或预测器的数值异常。审计未读 raw CSV，因此不代替专门的 target semantic diagnostic 判断其究竟是哪种原始值。

训练标签转换已开始，不能宣称所有 72h LIVE 数值从未被访问；但完整 ytrain 未返回，尚未进入任何 direct 配置拟合/validation selection。产物中仅有冻结清单、完整 prefix cache 与 FAILURE；没有 FOLD、ALL_OUTER_PREDICTIONS_BEFORE_SCORING 或 RESULT。故不能从这次失败推断 L-only/LD 的性能关系。未来单独语义诊断打开已授权 bad cases 亦不补成本 gate 的科学结果。

冻结清单中的 implementation/protocol SHA256 与审计时文件一致。八 dose、每 dose 四 opaque contexts×三孔，96 unique physical-well keys 均核对；所有 outer/inner 分组及 canonical concentration 的 hash validation 选择符合预定规则。prefix cache 标记 target 未访问，与源代码保存顺序相符；随后才发生训练目标访问失败。

## 前缀动力学产物与优化分歧

live-only：96 local fits、384 starts，全部 success=True；总 nfev 10125，选中未收敛=0，全四 start 未收敛=0。dual：96 local fits、384 starts，全部 success=True；总 nfev 13478，选中未收敛=0，全四 start 未收敛=0。所有导出参数在界内、cost/72h forecast 有限，选中 index 与最小 prefix cost/tie-first 一致，winner prediction 与缓存一致；live-only c 全为 0。

因此反方“selected nonconverged 应 abort”与 root“固定 cap 内有限 feasible iterate 可作 forecast diagnostic”的分歧，已在 `PRE_RUN_RESOLUTION.md` 和数值前最终 protocol 原样保留，**本批实际没有触发它**。scipy success 只说明数值停止条件满足，不说明 latent birth/death/injury 被辨识，也不将该小 ODE 变为完整 BESTDR。

前缀 `total−L−D` 的最大聚合绝对差约 `7.82e−14`。这只是近乎精确的导出算术关系，不证明独立 marker、真实 viable cells、累计死亡事件或观测噪声独立。更不能用该等式修补未来无效目标。

原 pre-data synthetic failure 与修复后 9 tests 输出均保留。测试涵盖 future values 不影响 prefix、未来 D/total 非必需、panel/well 单位、固定-r/clearance 的 L 非作用、独立 solve_ivp 对照等。9 tests 通过支持实现符合所写 ODE 及访问边界；不证明细胞机制正确。旧 repeated-rate fallback 出错在真实数据前已修复，与此次 observed-readout abort 是两件事。

## 实现审阅与剩余限制

family selection 使用 `best['macro_mae']`，该值来自 refit 前 six-dose-trained validation，refit 只改变模型对象而不重算该 score；没有把 seven-dose in-sample validation 当选择证据。ratio 为 raw D/(L+1)，log 为 log2(raw mean+1)。labels 的数值 field 只有未来 LIVE；prefix 可读 L/D/total，identity 检查只读各时间标识。

一处应留痕的文字/编码差异：protocol 的“全部七个 log L、其相对 L24 值、L0/L24”容易读为同时给 absolute 和 relative 两套七点；实现实际给七个 relative 值加 absolute L0/L24。该编码能精确还原完整 L prefix，所以未少给任何信息；但冗余坐标会改变 ridge regularization 与树 split 的 inductive bias，不能说与两套特征的模型行为完全等同。direct 分支本次未执行，故没有受影响的性能结论；若未来另有合格资产，须在其新 protocol 中把精确坐标写清，不能据此把本次资格失败改成允许重跑。

专门的 source/observation diagnostic 应解释触发 guard 的原因，查已授权 bad cases 的原始导出语义，保留否定/缺失/矛盾的证据。无论该诊断发现 exporter 定义、计数减法、缺失或其他原因，当前 registered raw-count、log2(mean+1)、完整 panel 不修复的目标已经不合格。它可以帮助将来独立任务选对 observation model，不能 retroactively 将本 gate 改成 channel 信息结论。

独特算法、真实机制、跨药物价值、world-model 同信息优势、agent、普通重训/CL/AL、继承、联合收益及 improvement-of-improver 均未由本次测出。停止并完整保留该失败资产使用方式，才与数值前规则一致。
