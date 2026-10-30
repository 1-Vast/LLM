# R204-DATA6 记录（record_data6.md）

2026-10-28 ｜ 执行：lit-verifier（task-191）｜ 工作目录 `D:\MAESTRO`
**状态：`not_sent_awaiting_user_authorization`。本任务未发送任何邮件/未提交任何表单；只读公开页面/API。**
写入范围：只新建 `research/2026-10-28-az-data-request-package/` 与 `tmp/`；**未改 R202/X1/X2/DATA1–5 产物**、其它目录、INDEX/git。

## 1. 本轮做了什么

1. 读必读：`2026-10-28-az-data-acquisition/{report_data1.md,PROTOCOL_DATA1.md,requests/data_request_spec.json,requests/request_template.md}`、`2026-10-28-az-code-hunt/report_data2.md`、`2026-10-28-data-readiness/DECISION_R204_DATA_READINESS.md`；核对 C205/C210/C211/C214 边界（公开数据 `partial`；不写"不存在/作者未做"；mapping 可由作者补充，真实功能确认需新测量）。
2. **联系人核验（公开来源，只读）**：
   - Europe PMC REST：`PMCID:PMC11061612` core 元数据（title/DOI/PMID/作者）→ 保存 `receipts/epmc_core_PMC11061612.json`；
   - Europe PMC `fullTextXML` → 保存 `receipts/epmc_fulltext_PMC11061612.xml`；定位 `<corresp id="CR1">`：两位通讯作者 + 邮箱 + 电话（Mathew J. Garnett `mg12@sanger.ac.uk`；Jerome Mettetal `jay.mettetal@astrazeneca.com`）；数据可用性段"Fitted and raw data are available through Figshare and the GDSC Combination website"逐字命中；
   - Figshare API：project 163378 的 10 个 article 全部取 metadata → 作者（Howard Lightfoot / Elizabeth Coker）、DOI、license（**全部 CC BY 4.0**）、public URL；保存 `receipts/figshare_project_163378_articles.json` + 10 × `receipts/figshare_article_*.json`；project 公共页返回 HTTP 202 空体（SPA/门控，未据此判定），**无公开邮箱/未验证公开表单** → `not_found_in_public_text`；
   - GDSC/Wellcome Sanger：`gdsc-combinations.depmap.sanger.ac.uk/`（HTTP 200，5,444 B JS shell，无联系文本）、`/downloads`（同 shell）；`cancerrxgene.org` HTTP 410 Gone；`sanger.ac.uk/about/contact/`（HTTP 200）含 `contact@sanger.ac.uk` 等通用邮箱 → 作**generic fallback**（非 GDSC 专用）；Sanger Garnett person 页含 URL 编码 mailto，解码 `mathew.garnett@sanger.ac.uk` → 仅旁证；
   - AACR 出版商页面 HTTP 403（受限，未绕过）；depmap contact 页一次 SSL unexpected EOF（记录，不据此判不可得）。
3. 生成 `contacts_verified.json`（结构化联系人 + 来源 URL/锚点/逐字引文/回执 SHA + 许可 + data availability + not_claimed）。
4. 起草 `REQUEST_LETTER_DRAFT.md`（英文；总 343 词/正文 317 词 ≤350；P0×3 + P1×2；含承诺与回复方式；发信人/署名占位）。
5. 生成 `request_package_summary.json`（DATA1 spec P0/P1/P2 对齐、用户授权清单 8 项、附件/许可、发送约束与状态）。
6. 写本记录、report、usage；整理 receipts（21 文件，含 SHA index 于 contacts_verified.json）。

## 2. 关键发现（摘要）

- 论文：**Large-scale Pan-cancer Cell Line Screening Identifies Actionable and Effective Drug Combinations**（DOI 10.1158/2159-8290.cd-23-0388；PMID 38456804；PMC11061612；2024）。
- **两位通讯作者均有公开邮箱**（Europe PMC fullTextXML `<corresp id="CR1">`）：Garnett（Sanger）与 Mettetal（AZ）——足够作为正式数据请求收件人候选。
- Figshare project 163378：10 个 article 均 **CC BY 4.0**；作者为 Howard Lightfoot / Elizabeth Coker；**无公开邮箱** → 不猜；Figshare 平台渠道未验证可用。
- GDSC 专用数据访问邮箱**有界检索未发现公开地址**（不写"不存在"）；Sanger 通用联系仅作 generic fallback。
- 请求内容与 DATA1 spec 对齐；P2 补充图 numeric 有意留后续。

## 3. 失败/限制

- AACR 出版商页面 403：未绕过，未用其联系方式；以 Europe PMC 公开全文为准。
- Figshare project 页面 HTTP 202 空体：SPA/门控，无法从页面读联系；未创建账号、未提交表单。
- GDSC-combinations 为 JS shell：公开页面文本无联系信息；未使用浏览器自动化绕过。
- depmap contact 页 SSL EOF：一次失败记录，不判不可得。
- 联系人不保证回复；请求不保证数据可得；**未发送=未验证渠道可用性**。
- `not_found_in_public_text` ≠ 不存在；技术三重复≠独立培养；PDF 图≠numeric 功能数值；不称新颖性/决策收益/机制。

## 4. 复现

```powershell
cd D:\MAESTRO\research\2026-10-28-az-data-request-package
& D:\anaconda\envs\maestro\python.exe verify_contacts.py
# 只读公开 API/页面；原始响应写入 receipts/；无发送/无表单提交
```

## 5. 下一步（待 Lead/用户）

1. 用户按 `request_package_summary.json` 的 8 项授权清单确认（收件人/cc、署名、附件、许可措辞、无收益承诺、是否联 Figshare、是否用 generic fallback）；
2. 用户在会话中**明确授权**后，才可发送（本任务不发送）；
3. 若作者回复：登记回复日期/渠道/提供文件 SHA 到本目录；随后交 R204 数据 readiness/资格线处理；**不改旧判定，不把技术重复当独立培养**；
4. 若 30 天内无回复：可再考虑 Figshare 平台渠道或 generic fallback（须用户确认），但**不重复骚扰、不猜地址**。
