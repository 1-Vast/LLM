# 真实双向交叉质询与阶段裁决

2026-10-22，scientific_skeptic。独立稿 `INDEPENDENT.md` 先落盘，再读支持方独立稿并发生以下实际消息问答。没有读数值 CSV 或拟合结果，没有增加网络请求。支持方原提 context holdout；root 在数值开启前已改为八 dose LOCO，此处审查的是最终候选的适用范围，不把原建议静默改写成双方一开始就同意。

## 支持方向反方发问，反方实际回答

**Q1：BESTDR 已联合拟合 L/D 与 hierarchy，它是否实际完成了“相同完整 live prefix + metadata，加入 D，heldout 后期 LIVE”的条件消融，还是只有同类操作？**

回答：我已读的 BESTDR 正文没有直接展示该严格条件 contrast；它明确有联合 L/D、clearance、随机分支与 measurement likelihood、层级共享等同类操作。操作已存在不等于此特定信息性质已被同条件检验；同样，这一次有界正文阅读不保证所有相关文献绝无该检验。新算法目前 NONE，经验问题仍可作窄 gate。

**Q2：原 opaque-context hash2/1/1，仅一个测试 context、八浓度，可允许什么跨 context 结论？D 是否更可能只是 context 校准，而非浓度 holdout 的信息？**

回答：原方案只支持来源内单个未见 opaque 标签的条件预测描述，不能称独立生物 run 外推；D 可帮助校准未知 context/测量环境，不能自动命名生物状态。root 的新八 dose LOCO 则估计同一药物、细胞、来源、已见 context 下未训练浓度的预测；它不是未见 context、未见药物或 RSI。两种设计回答不同问题，不按结果选其中更优者。

支持方随后明确接受：LOCO 是 within-source unseen-dose 的估计量，nested CV 不是 globally untouched，也不是八个独立任务；`intersect_live` 仅作 operational exported readout，无已文档化 complement 关系便不推 viablity 解释。

## 反方向支持方发问，支持方实际回答

**挑战：高 turnover→后期 q·birth 的代数例子只是一个充分动机。D stock 同时受 D0、clearance、标记延迟和共享观测误差影响。若 full D 胜 L-only 却未按同阈值胜 D0/D24，是否撤回“动态死亡历史必要/潜在损伤被辨识”的解释？即使 full D 都胜，下一项什么独立干预或对照能区分 turnover 与时间变化的观测校准，且不靠同源追加模块？**

支持方明确回答：

- 若 full D 未按预定同阈值超过 D0/D24，撤回 dynamic-death-history 必要/latent-damage 识别；即使都胜也只支持历史 readout 的信息价值。高 turnover→q·birth 是动机，普通未知参数联合学习或噪声解释都可替代。
- 区分需与当前 GFP/RFP parser 独立的 birth/death event 或后续 viable endpoint，最好来自相同 dose/time/cell conditions 的独立 matched run。无增殖、预先杀死细胞的面板可测荧光消退、标记延迟/重叠及药物条件依赖，以约束 measurement/clearance；校准须公平共享给全部模型。
- 单独固定 dead observation 校准不能证明 turnover。独立短窗口分裂/死亡事件与 orthogonal 后期 viability 才能检验真实 d 与 later growth 的联系。当前来源未认证这些 paired controls，故本轮无 turnover 识别。
- 后续先资格已有独立数据；没有则保持预测 scope 或停止机制晋升。不在同来源加模块冒作验证，也不以强制新湿实验阻止一个诚实的 readout forecast gate。

上述是确实收到的答复摘要，非反方替支持方代写。支持方另保留其 `CROSS_RAW.md`/`CROSS.md` 消息记录。

## 共同结论、反对证据和未决项

**共同结论：值得一次预冻结的条件信息实验；当前新算法 NONE，独特生物机制未成立。** primary 必须是未来 LIVE readout，不能被未来 D/joint loss 救回。普通常率模型在 r 未知、先验相关或测量有噪声时也可能从 D 改善 r 推断，不能声称“常率就不可能利用 D”。同信息、同搜索预算的 direct、普通 compartment/clearance、固定混合均是必要对照，非 agent/RSI。

支持该 gate 的证据：有可操作的同孔早期 L/D 与未来 LIVE-labeled readout；条件信息问题具体可证伪；已读最近邻没有直接展示完全相同条件的 holdout-LIVE 对比。后一项只是有限文献暴露判断，不是全面新颖性担保。

反对机制晋升的证据：BESTDR 已覆盖大部分联合建模操作；phase-specific 及 ROS/growth 原始工作已有多状态/时变出生死亡与功能细胞数关系；本来源是单药、单细胞系、技术/条件单位，不支持广泛运输或独立任务继承。D stock 不唯一对应死亡事件或损伤，未来 exported readout gain 不能唯一定位生物因果。

未决项：同条件严格 contrast 是否已在完整相邻文献/补充中存在；当前来源中 marker/segmentation/clearance 的独立校准；是否存在可用的 matched orthogonal event/viable endpoints；最终实现是否正确隔离 own-fold targets、使用原始比例、处理未收敛。最后一项可由代码/运行前测试解决，前三项不能用本 gate 分数直接解决。

下一步仅执行冻结 gate 并做非拟合审计。通过后先作同条件独立资料资格与观察机制区分；未过预定全部信息判据则停止该具体 24→72h 应用，保留阴性与异质性。世界模型同信息优势、agent、继承、联合和 RSI 的整体研究目标仍待实证，不能用本 gate 完成。
