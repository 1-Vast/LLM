**判定：当前证据下我不能诚实提出可发表的新 core。** 不给新名字；只给一个会改变“是否继续建机制”的可执行检查。核验：已有强 direct/kernel/meta/search 阴性及组合功能数据格式成立；猜测：少量功能反馈可能编译为状态条件方向约束并改变后续候选生成。未核验任何新 paper/DOI。

**(1) 用途与单位。** 药物组合/单药在目标细胞系的下一批实验选择与排序；最小数据为“药物对×细胞系”的真实功能标签（如 inhibition/viability）加单药 expected；合法 feedback 仅预注册目标系少量槽位；later-task 单位是同一目标系剩余预注册 pairs 的决策及一次模型/程序改进。RNA/形态只作 proxy，绝不称 viability/疗效。反馈只能来自已获准槽位，不能偷读 held-out。

**(2) 唯一技术实质（≤12行伪码）。** 反馈不拟合响应面，只编译为“状态-模块方向/序可行性”约束 \(K\)，并要求 \(K\) 改变后续候选集；否则归约即停。

```text
输入 H, 预算B, 候选C0, 预注册反馈槽F
生成 C=C0；支付F⊂C的真实功能y
对状态s、模块m：r=sign(y_s,m-expected_s,m) 或有序差符号
仅当 r 在同s重复一致且留一相似s可迁移，加入 K
用 K 过滤/重排 C\F，得后续候选 C_K
同预算拟合/搜索 I(K,H,B)，输出下一批
later: 同起点H、同权限、同B，比较 I(K,H,B) vs I(∅,H,B)
及 strong direct / active / kernel / meta-search
关键：K 不写回数值残差；若 K 可由 expected/历史直接构造，或
不改变 C_K，或不改善 held-out 功能决策，则归约，停止。
```

**(3) 与 ordinary direct/kernel/meta/search 的精确差异。** direct 用反馈拟合 \(y\)；kernel 条件写残差；meta/learned optimizer 学参数更新；search 用历史排序/记忆。本检查只承认一种非平凡性：反馈产生**可执行的状态条件符号/序约束**，且该约束改变后续候选生成，并在 held-out 功能决策上有同预算收益。若只是提高预测分数、增加标签、调超参或约束仍由普通监督/主动学习复现，则完全归约，不建。

**(4) 最便宜决定性实验与 success/stop。** 用已有完整组合矩阵，冻结一个目标细胞系和少量预注册反馈槽，隐藏其余真实功能标签；同标签数、候选数、拟合/搜索调用、起点/历史/权限比较 strong direct、active learning、kernel conditioning、普通 meta/search。Success 预注册：\(K\) 使后续候选集明显改变，且 held-out 功能 hit/排序/实验选择优于所有 baseline 的配对置信区间下界>0；Stop：候选不变、收益≤best baseline、或收益只在 toy/分子 proxy 上出现。离线通过只证明决策机制，不称药效；真实湿实验是后续确认，不是本检查前提。

**(5) 可证伪与公平预算。**
- **world**：独立重复/相似状态中方向约束不存在或不可迁移；或 expected/单药已直接给出同约束。
- **agent**：同预算下约束不改变下一批候选或改进轨迹。
- **inheritance**：任务A得到的 \(K\) 在任务B同起点/同预算下不优于 old improver；随机打乱状态标签应破坏收益。
- **joint**：约束+改进器联合收益不高于单用约束或单用改进器的 pre-registered 比较。
- **C4**：old/new improver 在同一 later solver、同 history、同 permissions、同 budget 下，new 的后续改进不优于 old，或差值不能由 \(K\) 解释，即 fail。
公平 baseline 必须同反馈槽数、同候选实验数、同模型/搜索调用、同起点与权限；不得给 new 额外标签或算力。若检查失败，停止该方向，不重命名已有模块。