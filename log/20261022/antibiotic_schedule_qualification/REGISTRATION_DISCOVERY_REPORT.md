# DOI关联登记检索结果

2026-10-22，Asia/Shanghai。按独立预登记 `REGISTRATION_DISCOVERY_PROTOCOL.md` 顺序执行2次metadata请求；**两种登记查询均未返回关联记录，未获得公开data/code linkage**。这不证明作者没有公开数据、没有代码，亦不证明其只upon-request。

| metadata来源 | 实际查询 | 返回 |
|---|---|---|
| DataCite REST | `relatedIdentifiers.relatedIdentifier`分别精确匹配bare `10.1101/2025.10.30.684665`或`https://doi.org/10.1101/2025.10.30.684665`，OR连接；page size10 | HTTP200，`meta.total=0`，305bytes |
| Zenodo REST | DOI完整双引号短语查询；size10 | HTTP200，`hits.total=0`，457bytes |

实际请求URL、raw JSON、status、hash、UTC与body完整性保存在 `registration_sources/`。两次完整response body合计 **762bytes**，无截断，低于1MB。本阶段没有publisher mirror、全文格式绕过、dataset payload或code内容获取。只尝试这两种原样DOI关联，不扩大同义词、作者、标题或其他archive，因此零结果是该有限检索的证据，不是穷尽source availability的证明。

原3次paper来源请求和其结论保持原样：EuropePMC500；NCBI EFetch200但仅front+abstract，publisher明确不允许full XML；bioRxiv429，无重试。原阶段19,181bytes加本阶段762bytes，共5次scripted GET、**19,943bytes**。若加根代理先前的PubMed发现请求，须另用其ledger计算，不能声称这里覆盖全部研究开销。

最终保持 `EXACT_INTERVENTION_STATE_FUNCTION_MENU_NOT_QUALIFIED`：没有已认证drug/order/dose/lag、strain/run/chamber/colony、state-time/growth-frame、共同prefix替代行动及data/code manifest。**按授权结束本轮来源扩大，不再请求。** 不下载图像、表达/形态矩阵或功能值，不构造不可得schedule，也不据摘要启动模型/Agent/RSI。
