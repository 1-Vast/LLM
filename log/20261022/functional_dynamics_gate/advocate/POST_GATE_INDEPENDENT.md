# HTS001 gate 后独立支持方审查

2026-10-22；先审 frozen `HTS001_GATE_PROTOCOL.md`、`hts_gate/RESULT.json`、`MODEL_FREEZE_BEFORE_TEST_TARGETS.json`，后才发起本次对抗交叉。未读反方 post-gate 稿、未 fit、未 network、未改 endpoint/split/window/model/threshold。读了结果与冻结记录，包括已暴露 test-target／prediction 值；未打开原 CSV 响应表或 HCT116 数据。

**独立决定：STOP_THIS_SIMPLE_CONFIGURATION。** 这是一个真实测量支持的负向推进决定，不是否认该数据集有预测信息，也不排除尚未测试的 HCT116 dual-channel 问题。总 goal 未完成。

## 保留的小观察

训练8药在固定11点网格选出 alpha=.5，冻结后给3个留出药、420 wells 的共同 fresh initial model 与相同反馈：local ψ0 MAE .303590122，ψ1 .230026401，改善 .073563721 log2(N+1)，相对24.23%。3个 drug 的差均为正，但 osimertinib 只有 .000601333；这个事实只能是条件于本 screen／这些药的描述，不能用420 wells提升研究任务 n，也不能以三药 bootstrap 的下界>0声称一般化确认。

可保留的实用经验是：**在这个已冻结的短前缀外推中，全信最近窗口斜率会比结合早、晚斜率更差，温和收缩能降低该 baseline 的误差。** “最近斜率必定更适应当前动力学”的直觉不应无条件采用。这不是 birth/death 识别，不是学到独有更新策略。

之所以不能进一步归因于“学习 alpha 必需”：固定 .5 mixture 与 ψ1 完全同结果，独立算的 equal-budget search 同结果；训练选中的值正好就是预先给出的简单对照。共同 fresh start 排除了携带该测试孔修复 θ 的解释，却没有排除普通混合／调参。

## 什么被否定，什么未被测试

- 预登记推进条件失败。vs ψ0 的相对改善超过10%，绝对 .07356 未达 .10；vs direct 的差为 -.050940457，候选更差；vs full-prefix refit 为 -.000770584，候选略差。不能改阈值把 relative pass 转成总体 pass。
- 普通 full refit MAE .229255816，几乎同 ψ1且略优。无需额外研究智能体来取得这个 accuracy level；本结果没有显示候选独有的更新收益。
- 选定 strong direct MAE .179085944；0.5 direct/world blend .178211404，仅降低 .000874539（约0.49%），远小于预定有用门槛，且其中 osimertinib 从 .170623665 变差到 .220530861。不以微小平均变化宣称 joint gain。
- direct 用 train+validation refit、ψ只在train选alpha，是协议明示的训练使用不对称；这限制“纯结构世界模型劣于所有direct”的解释。**它不能挽救本 gate**：公平 simple .5 mixture／同grid search 精确等价以及 ordinary full refit 不劣，已独立阻止独有贡献的主张。不能事后给 ψ补validation再重开同test。
- source 是 nucleus count 的 net-growth surrogate，无独立 dead channel、clearance 或 birth/death 真值。这次没有测试 dual κ、机制特异纠错、真实 acquisition／AL、执行型 research agent、完整 CL、cross-run transfer，或 updater-of-updater Ω 变得更会学习 ψ。
- 七项 synthetic tests（root 报告通过）支持预设的软件性质；不代替生物学可识别性或跨 run 性能。本审查未重新跑测试，也不声称作了完整独立实现审计。

## 冻结检查和不允许的补救

freeze 中 alpha=.5，selected direct=`extratrees_None_3`，`test_target_values_accessed=false`；保存了 test predictions。当前 script／protocol／source SHA256 与 freeze 的三条身份一致。我仅做 hash read，不重算预测。这支持使用已保存的冻结版本，单凭 JSON 字段本身不构成密码学证明或替代访问日志。

没有观察到需要修复后再跑的 implementation failure。被结果否定的是既定simple configuration的推进；不能把failed scientific gate改称实现错误，或调整drug split、窗口、endpoint、alpha grid、门槛直到通过。

HCT116 的合法后续若开展，必须另冻结其真实 live/dead stock observation model、independent units、endpoint 与 strongest BESTDR/direct/EB/search controls。可以因不同观测与问题而做新 gate；不能只把此处 α 换成两个 κ 当作逃避失败。没有累计 death event时，仍禁止套原始闭式GammaPoisson计数推导。

## 待实际 cross 的两个问题

1. 相同 fixed .5 mixture 完全复现是否已足够停止“学出的更新程序是必要机制”，同时保留上述局部斜率收缩的小观察？反方如认为该观察也应删去，需指出它超出了哪些真实比较。
2. 能否明确负结果范围：它停止这一 scalar net-growth/shrinkage 配置；不能由此直接否定含 calibrated dead-stock/clearance 的两通道 prediction/update。但 HCT后续应给出什么新增可检验信息，才不算换名字重跑？
