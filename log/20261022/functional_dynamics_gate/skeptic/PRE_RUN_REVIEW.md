# HTS001 gate：响应开启前独立审查

2026-10-22。只读 `HTS001_GATE_PROTOCOL.md`、`root_scout/HTS001_IDENTITY_SCHEMA.json` 和 `root_scout/CSV_HEADERS.json`。未读 HTS001/HCT116 响应、未来模型输出或实现代码；不声称做了实现审计。以下建议已通过实际消息在本轮数值访问前告知根代理。

**结论：没有需要取消这一次 gate 的科学错误。完成下列可修复澄清后，可以执行一次诚实的 within-screen net-growth/shrinkage 开发试验。** 它不能验证 birth/death、独立生物 run 泛化、agent、AL 或新算法/RSI核心。

## 执行前应明确的五项小修

1. **区分 test prefix 与 test target。** 协议“test parsing/evaluation happens only after all models/predictions are saved”按字面无法执行：同孔 fresh θ0、r1 和 direct 特征必须读取合法 test prefix。应明确模型/超参数先冻结；只允许 test 的 `time<=34h` 响应生成输入及预测，目标附近及其他 future 响应保持关闭，预测保存并校验后才进入独立 target-score loader。不能先用全轨迹计算归一化、速率、插值或诊断再声称 target 未参与预测。身份/时间可先读。
2. **冻结插值边界。** 只用当前合法 prefix 内真实时间点插值。如果固定4/32h等特征落在该孔已观测 `[first,last]` 之外，预先规定 boundary carry 或结构失败，不得借用 post34h 数据补端点。Eligibility 的点数条件本身不保证覆盖每个固定特征时间。r0/r1、anchor 与 horizon 均使用实际观测时刻；不把34h当所有孔的共同最后测量。
3. **冻结所有平分处理与宏权重。** alpha 网格与 direct 配置 validation MAE 平分时采用固定顺序（例如事先配置顺序），不能看 test 选。训练 alpha 的目标、direct 的 validation 选择、主要 test 评价都明确采用 drug→background→dose→well 宏平均。源 schema 显示每背景一 plate；不能让帧数或某药剂量/孔数变成任务权重。单独计算的普通网格搜索要使用相同 tie 规则，数值差异按实现失败处理。
4. **修正单位解释。** `0.10 log2(count+1)` 精确对应 `(N+1)` 的约7.2%倍率差，并不为低计数 N 提供相同相对误差保证。保留原 log-scale 实用阈值及“非噪声估计”说明，不事后把它换成 raw-count 百分比门槛。任何 raw-count accuracy 只作另列描述，不能替换已冻结 MAE 成功判据。
5. **修正 HCT116 的 run 用语。** 末段的“2 HCT116 runs/dose tables”应为两个 source files/tables；现有文件数不认证两个独立生物 run。它们不进入本试验、也不增加 HTS001 的药物任务数。

## 三个 test drug、fresh start 与 direct 比较的判断

整药分组、全部背景/浓度/孔随药固定、按身份 hash 分8/3/3且在数值前保存，是合法的 within-screen untouched-response 划分。**三个 test compound 是至多三个研究任务簇**；七个 PC9-derived backgrounds、2156孔轨迹及连续帧都不能扩大为独立生物实验。background 与 plate 一一对应，不能分离真实背景效应与 plate 效应。三簇 bootstrap 可按协议显示条件性敏感度和逐药方向，但不能给出稳健总体泛化 CI 或依赖其“显著性”升级；三个药的正方向也不证明普适迁移。

每个新孔从共同 θ0 分叉，接受相同 feedback 与最新 anchor；ψ0 为 alpha1局部 refit、ψ1为历史学得 alpha，能检查固定信息下常规更新规则继承的描述性收益。必须不携带已修复测试孔权重，也不使用另一测试孔的 future 结果继续更新 alpha/共享先验。冻结初始/no-feedback 与 readout-only baseline 是必要的：后者可辨别 gain 是否只是买到了新 anchor。它们与主要同反馈比较的信息条件不同，应按用途报告，不当成同信息胜利。

direct 得到完整合法 prefix、实际时间/剂量/背景、r0/r1，包含非线性基线且用 validation 选配置；这足以支持本窄 gate 的诚实强直接预测比较。direct 最终 train+validation refit，而继承 alpha 仅用 train，给了 direct 更多共享训练信息；协议已明示这一不对称，不能称严格相同训练预算。无须因此削弱 direct；若世界模型胜过它，比较更保守；若失败，只停止这份具体配置，不能证明共享 updater 永无价值或没有 headroom。不能报告 best-test direct，不能 test 后调 α、窗口、模型容量或 loss。

普通同网格 search 应与 alpha 方法完全相同，打平是预期，不是一个待战胜的独立算法。direct/world 简单混合可以检验补充预测价值；混合改善不构成 agent 或 joint framework 贡献。pooled-rate warm start 只是所声明的 surrogate，不能替代完整 CL 比较。

## 可报告与停止的边界

可报告：此 source 内真实同孔 prefix→near60h 的 log-count MAE、每 test drug 的结果、固定 fresh-start 条件下 ψ1/ψ0 的差及简单混合的描述。响应异常应按已声明诊断失败停止，不可筛掉不利药/孔继续评分。任何修复只针对可证实实现错误并保留原执行；不得因科学结果不佳而 rerun。

无论结果：新算法主张已被精确普通 search/收缩归约终止；birth/death机制、独立-run继承、可执行研究 agent、AL、完整 CL、联合框架和改进策略进一步变得更会改进仍 **NOT_TESTED**。预定两项实用比较失败时停止这一 net-growth/shrinkage 配置；通过时也只保留后续更大 compound/batch、完整随机动力学及公平全套控制的资格，不能完成总目标。
