# 来源、查询与判断范围

2026-10-27；本轮一手来源刷新截止该日。有限问题重审，不是系统综述。没有重跑旧效果实验，只有原产物读取、代码检查和明确标注的小算例。

## 实际检索

PASS1（最近先例身份核对，原生web）：

1. `"One-hot news" drug synergy models shortcut molecular features`
2. `"GoBOED" decision focused Bayesian experimental design`
3. `"2605.20885" drug response`
4. `"SynVerse" "2025" drug synergy`

PASS2（后续问题及替代原理，原生web；以下为同pass预定问题的具体查询）：

1. `"2025" "2026" "drug combination" "active learning" "decision" Bayesian`
2. `"DeepSynBa" dose response synergy 2026`
3. `"2025" "2026" "experimental design" "model discrimination" "misspecification" decision`
4. `"2605.04895" regime Bayesian optimization`
5. `"Active Learning of Model Discrepancy" "Bayesian Experimental Design"`
6. `"drug combination" "2025" "2026" "active learning" "BATCHIE"`

后续只打开已发现论文/已知原文的版本与相关段落，未另起第三扩展。非穷尽；未检出不作不存在证据。未使用付费LLM API、未安装包。官方模型指南只作配置核对，不计科研检索：旧developers URL重定向至learn.chatgpt.com/docs/models；本轮代理均继承配置，未暴露有效model/effort，记unknown。

## 关键一手文献

| 来源与版本 | 实际读取 | 用于判断与局限 |
|---|---|---|
| [One-hot News, Bioinformatics 2026, btag040](https://academic.oup.com/bioinformatics/article/42/3/btag040/8440676)；本地R180文本/方法审计 | 已存切分段、线上索引原文方法/表格；publisher正文失败，PMC web验证页 | 已有LDO与身份/特征对比；不把双药未见比较本身当创新；未重做全部实验 |
| [Heo, arxiv2605.20885v1](https://arxiv.org/html/2605.20885v1)，2026-05-20预印本 | global/per-drug指标、MoA训练分层、pilot matching和迁移边界 | 单药：主效应掩盖条件排序；拼接MoA不同于训练分层；功能匹配已有。无组合验证；作者解释非本轮独立事实 |
| [GoBOED, arxiv2605.26093v1](https://arxiv.org/html/2605.26093v1)，2026-05-25 | 摘要、§2.2、§3.1与凸决策限制 | 预后验决策价值已有；实际single-step non-adaptive，不等于所有序贯取证均已实现；非组合板复现 |
| [Decision-Focused Sequential Design, arxiv2602.05340v1](https://arxiv.org/html/2602.05340v1)，2026 | 问题/SPO目标及尺度不变性段落 | 序贯性/决策方向不是自动新意；未全面核理论和代码 |
| [R-IDeA, arxiv2506.07805v3](https://arxiv.org/html/2506.07805v3)，2026-03-31，页面标AISTATS2026 camera-ready | 摘要、§3误差分解、§4相关门控，本地全文 | 错设/偏移可放大主动学习误差；一般乘积先例不证明具体方法同一。v1题名Generalization Analysis...无R-IDeA，v3有，已核版本沿革 |
| [Yang et al., arxiv2502.05372v2](https://arxiv.org/html/2502.05372v2)，2025；期刊DOI10.1016/j.cma.2025.118198 | §2.2–2.3、Algorithm1、错设/不可识别段落 | 设计与偏差交替更新已有；原文承认某些设计误导更新；PDE数值验证非药理证据 |
| [DeepSynBa, Bioinformatics 2026, btag416](https://pmc.ncbi.nlm.nih.gov/articles/PMC13341016/) | 摘要、剂量表面结构、§3.8与Discussion限制 | 完整剂量表面及potency/efficacy已有；未验证全部性能/毒性主张；publisher失败，PMC全文实际下载核题名 |

## 资料库与访问

沿用 `D:/MAESTRO/reference/`。初始verify：15论文/10正文文件，0 errors/0 warnings；新增Heo、Yang、DeepSynBa三篇公开HTML，脚本保存URL、版本、字节与SHA。末次verify：18论文/13正文文件、12 HTML+1 PDF、1 pending、4 restricted，0 errors/0 warnings。源码仍只有1份官方模板快照，未声称复现；新三篇源码未完成核验。未绕过验证、登录或付费限制。

## 分工与独立性

- 统计审查：stats_audit.md及toy代码/结果，原材料只读，未参与候选发展。
- 结构侦察：scout_initial.md；初始三方向在收到先例摘要前消息留痕；落盘前收到摘要，已披露；未读本轮候选。
- 协调者：来源/代码复查、audit_arithmetic.py/json、候选v1与综合。
- 新上下文挑战：challenge.md，对象为具体候选和原来源，不含期望判决。

代理均用工具默认继承；有效model/effort、tokens、费用没有确认，unknown/null。独立上下文不等于独立生物证据或独立模型家族。
