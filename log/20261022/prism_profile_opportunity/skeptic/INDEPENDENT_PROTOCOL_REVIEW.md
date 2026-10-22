# 独立反方协议审查（数值运行前）

日期：2026-10-22。审查者：scientific_skeptic。本稿在阅读本阶段 advocate/data 审查稿前形成。只读合同与元数据，不读响应数值、不作新 GET、不运行模型。已收到 root 对此前具体质疑的书面回复，下面将其与当前文件内容分开记录。

## 判断与适用范围

原则上同意开展一次 mask-only 覆盖资格核验；该核验只能决定这个固定、已暴露发布目录中的“两池反馈→大部分剩余面板”任务是否值得另立预测实验，不能建立世界模型、智能体、继承、联合收益或 RSI 的创新与性能。当前 PROTOCOL.md 还需在运行前写入 root 已承诺的“全部七张 test plate 至少一个合格化合物，否则 STOP”，并使 MANIFEST/code/test 对齐。满足这点后，本人不以尚未制定的预测评分细节阻止纯覆盖核验。

此阶段没有新的核心机制。把普通机会诊断写清楚是合理的研究止损步骤，但不能用“有两个反馈池”或“有跨任务化合物”直接改名为世界模型或 RSI。

## 固定对象与支持理由

- 一个任务是一个化合物在 HTS002、精确 2.5 µM、固定 481 个 STR context、20 个 pool 上的发布响应 profile；付费两个完整 X1 pool，目标为另 18 个 pool 的 X2/X3。固定 contexts 不支持未见细胞迁移主张。
- 分板 hash 与化学 purge 不依赖响应。保留全部 test 原始候选，dev 对 test 的 parent OR 精确 Murcko（包括空 scaffold）清除，source 对原始 dev/test 清除，有助于约束人为挑选；不能消除已知单连通依赖或建立 iid N。
- 源文件与既往 anchor_purchase 暴露相同。输入 X1 可能经共享控制、检测板归一化及跨 pool/replicate ComBat 依赖 X2/X3。因此合法解释是条件发布目录补全；独立湿实验验证或前瞻无目标依赖并未得到证明。
- 整池成本明确，付费池的缺失、失败和弃权不能返还成本；源数据、开发选择、目标反馈和审计分别记账比“只花两个点”更可复核。
- root 将 source≥300、dev≥80 限定为可用性门，80%/70% 限定为任务和选择范围的实用约束，而非 assay 标准、统计功效或临床价值。这些解释是必要且足够的阶段边界。

## 具体挑战及 root 已答边界

1. **80% 是什么面板？** 初始方案可能被读为每个未付费 pool 均≥80%。root 已澄清：X2 与 X3 各自在全部未付费 context 的合计分母上达到 80%；逐 pool 报告覆盖率，零贡献也保留，不追加逐 pool 门。这一较弱门可以接受，但结论必须写成“大部分固定未付费 contexts 可审计”，不能声称每个 18 pool 都得到有效验证。它可能容许一个或多个 audit pool 完全缺失，报告必须显式呈现。

2. **谁被选择、原分母是什么？** test 原始分母为 255 个化合物、七张原始板；不能在评分或摘要时只保留“通过的六张板”。至少 70% 保留门可限制极端子集选择，但不能证明缺失可忽略，也不保证每张板保留 70%。root 接受另加全部七张至少一个合格化合物，才允许以后定义七板宏平均；当前读到的 PROTOCOL 与 MANIFEST 尚未含该补充，须数值运行前同步。

3. **source/dev 能不能训练？** 300/80 只保证数量可用，不保证每个未付费 target coordinate 有源标签、协方差可估或 kNN 有效。root 已同意以后另冻结模型训练与 menus 才 fit。因此本阶段通过不能自动授权任意模型拟合；下阶段需指定坐标支持、降级/弃权、正则与搜索预算。

4. **X2/X3 究竟是两个什么结果？** 本阶段分别计算覆盖，不混为独立实验。root 已答：未来预测若拟合，需锁定共同 finite intersection，或明确定义两个不同 estimand、不得将不同面板上的分数变化解释为 repeat 稳定性。单独 gate 通过仍不保证共同 intersection 够用；这只能在将来另立合同，不能在这次失败后改门。

5. **mask-only 与标签隔离。** root 已承诺 adapter 只保存 bool mask/count，不缓存真实 labels，不运行 model class；以后先 seal predictions，再由独立审计 converter 打开 audit labels。该承诺应由代码审计与输出清单验证。资格审查可使用 audit 缺失性，但以后模型不应悄悄把未购买 X2/X3 缺失图作为额外反馈；若要允许，须将其明确作为所有 baseline 相同的信息并改变权限合同。

6. **hash 与成本单位。** root 已确认 pool hash 为 `SHA256("prism-profile-20261022-v1|pool|" + pool_id)`，不是嵌套 hash；两池全局固定。两池付费是每个目标化合物两个逻辑 bundle，不是两个完整 20-pool profile。源/开发完整 profile、审计读取、失败槽、所有实际拟合与程序搜索都需分别记录。这里不能倒推实际湿实验成本。

## 尚未决定、应由后续模型协议解决

- 固定 row→pool→compound→plate 的主权重。按化合物平均与按七板宏平均不同；如主指标用七板宏平均，所有七张必须在定义域内，绝不能只平均非空或合格数量多的板。
- 固定实际应用效用、top-k 或损失单位和最低有意义增益。常数 offset 可改变 MSE，不能改变同一化合物内排序；不能以 offset 的损失收益宣称筛选收益。
- 将化学 direct、同反馈 direct、普通重训练/正则更新、source covariance/ridge/kNN、identity/no-update 与简单混合实际实现并给予相同 source 标签、反馈数组/mask和开发/搜索预算。方法名字不足以构成公平对照。
- 区分同次 audit 上的 hindsight menu max、跨 repeat 的 selector 与合法反馈 selector；任何 X2 调参后 X3 收益都不能叫独立确认。
- 若没有普通条件目录预测机会，不应扩展为高复杂度 world/agent/RSI。若将来出现收益，也须分别消融世界模型、智能体、继承与联合贡献，并检验“改进策略使后续改进更有效”，才触及原始目标。

## 成功、停止与可证伪性

本阶段可证伪主张仅为：预先指定两池在足够多固定化合物上具有≥80%有限反馈，同时各自 X2/X3 的剩余大部分固定 contexts 可审计，并满足冻结的 source/dev/test/plate 数量门。整数判断应为 `5*finite >= 4*nominal`，70% 同样使用整数比，不靠浮点近似。

任一门失败，停止这个确切的 bulk-profile 配置、保留失败和全部原分母；不得挑新板、换池、降低阈值、改剂量、改 replicate 或按表现替换任务后把它算作原检验成功。STOP 不推出“所有 partial-profile、普通主动学习或细胞建模都无效”。通过只授权另立冻结模型协议，不代表科学创新获得支持。

## 本稿证据边界

本稿读到的新阶段文件：PROTOCOL.md、MANIFEST.json。参考的已归档只读元数据：FIELD_CONTRACT.json、DEPMAP_METADATA_JOIN.json、MANIFEST_GEOMETRY.json。已知元数据为 1274 合格候选、原 source/dev/test=763/256/255，purge 后=565/211/255，paid pools=P933/P904；这些数量不是有限响应数量。本稿未以既往未知率或相关性替代本次资格核验。精确输入 hash 单列在 REVIEW_BINDINGS.json。
