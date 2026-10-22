# 独立登记检索阶段：公开data/code linkage

2026-10-22，Asia/Shanghai。原支持方3请求来源资格已经结束并保持 `EXACT_INTERVENTION_STATE_FUNCTION_MENU_NOT_QUALIFIED`，本阶段不改预算/结论，也不通过publisher mirror获取受限全文。

根代理授权一项依赖于已认证DOI的不同检索：最多2次metadata GET、combined response body≤1,000,000 bytes；DataCite REST的exact relatedIdentifier检索（bare DOI或https DOI URL两种精确写法），以及Zenodo REST的exact DOI短语检索，各至多10条记录。不请求dataset文件、图像、矩阵或source-code内容，不打开原始响应值。顺序单writer，即时保存status/hash/bytes/UTC及失败body，请求前拒绝覆盖；达到限制后停止，不扩展搜索词、mirror或其他archive。

目标是认证metadata记录与DOI10.1101/2025.10.30.684665的直接关联，并只读title/creators/relatedIdentifiers/public文件名与size/数据代码URL。命中须检查relationType及identifier实际值，不能以title相似当认证。无命中只意味着这两种登记查询未取得关联，不证明public数据不存在；API错误/访问限制更不能算阴性科学证据。若无法认证，结束本轮来源扩大，不启动模型。

新增脚本 `research/antibiotic_schedule_qualification_20261022/registration_discovery.py`，原始metadata与receipt在本目录 `registration_sources/`。
