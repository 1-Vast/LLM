# 实际交叉质疑记录

2026-10-22。本文件在 skeptic 独立稿封存后创建；不回写独立稿。只读本阶段协议、元数据、程序和 peer 审查文件，无新 GET、无真实响应转换或拟合。

## 与支持方 mechanism_advocate

支持方先提出：shared ComBat 与既往 anchor 暴露是否会被过度扩大成拒绝任何 conditional-catalog finite gate？其立场是支持 coverage-only，承认旧 STOP 与无 fresh claim，并且 aggregate 80% 不能在看结果后临时改为 per-pool 门。

反方实际答复：同意。已知依赖限制 prospective/no-target-dependency 及独立生物学解释，不否定条件发布目录缺失资格核验。不能把批处理依赖当作否定所有静态功能 world 的通用理由，也没有原始重复数据才能做任何目录描述的要求。

反方的两项主要反问：七板宏平均是否会丢掉不满足十个化合物的第七板？aggregate 80% 成功是否被包装成 18 个 pool 均验证？另追问 future source-coordinate 支持、共同 intersection、审计缺失图权限。

支持方已阅读反方封存稿并实际答复：接受全部实质反问。原话要点为“aggregate80%仅大部分fixedunpaidcontext可审计，不保证18pools有效；不加perpool门，逐pool零贡献保留”；“all7nonzero承诺必须PROTOCOL/MANIFEST/code/test落实”；“audit缺失mask属资格不自动送模型新反馈”。支持方亦澄清独立稿中的数学 menu 是将来的普通对照示例，不能先于 coverage 预写复杂拟合。双方无剩余原理分歧。

## 与数据审计方 functional_auditor

数据方先询问：是否接受 aggregate 80% 只做 availability、逐 pool 另报，共同 mask/权重未来另 freeze；以及原始 255 分母、179 最低数、all7≥1/6≥10 与 source 完整 profile60 / target2 成本是否均保留？

反方实际答复：全部接受。不能以跨 replicate 缺失不同的面板来虚构稳定机会，也不能将两个目标反馈 bundle 的预算套在全量 source 训练上。任何失败、缺失、弃权的已尝试 paid acquisition 仍收费。

反方再反问：root 初版 coverage.py 的 per_pool 只有 split×rep×pool 总计，是否会掩盖某化合物的整个 pool 缺失？有限 mask 虽可重算，建议在详情另列 per-compound×rep×pool 计数，但不追加资格门；未来是否禁止未购买的 audit missingness 偷当模型输入？

数据方实际答复：接受两项。FINITE_MASK 的 ids/slots 足以重算，但直接计数更清楚，已向 root 建议。未来若允许 X2/X3 mask 作为特征，需要额外合同与所有 baseline 相同信息，并不能声称仅有两个 paid payload。数据方确认 root 程序只对 retained 1031×914 slots 转换，unused/purged 不转换；不重复真实源转换，由反方做另实现复算。

## root 的实际回应及修订

- all7 nonzero 已写正式 PROTOCOL、prepare.py/coverage.py；初版 MANIFEST.json 保留，MANIFEST_v2.json 绑定补充门，分组无变化。反方已亲读 v2，确认门存在。
- root 进一步明确独立复算只允许 retained compounds 的 914 slots：48 paid-X1、433 unpaid-X2、433 unpaid-X3；不可转换 X1 unpaid 或 X2/X3 paid。
- 反方指出当前协议仍需把先前“1274×481×3 转换权限”与这一收缩权限同步。此为权限最小化与文字一致性修订，不是基于覆盖结果改门。
- 反方向 root 建议 per-compound pool 计数。此项仅增强透明度，不改变 aggregate 80% 门或选择分母。

## 新的独立复算准备

反方在看过 root 代码、但未读 root 数值结果的情况下另写 counter-only 实现；因此不冒称盲写。实现不 import root 程序，逐 context 只转换所允许 replicate/retained chemical，真实 response 不存盘，仅存 counts。执行要求 freeze 绑定独立程序及 v2 manifest。

三项合成测试已通过：整数阈值边界；已声明 missing 与非数值异常区分；将所有未付费/已 purge 槽放入 poison 字符串仍可运行、证明未转换那些槽。测试不打开真实矩阵。真实复算等待 root 正式冻结执行权限。

## 当前决策

**支持一次受限 mask-only gate，尚未执行。** 没有新核心、性能、世界模型/智能体/继承/联合/RSI 证据。若 gate 失败，停止这个准确 bulk-profile 配置；若通过，也只允许另行冻结普通模型机会协议。本次争论没有把失败外推成整个领域不可行。
