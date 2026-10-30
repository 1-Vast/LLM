# R204-DATA6 报告：AZ DATA1 数据请求包（联系人核验 + 草稿，**未发送**）

2026-10-28 ｜ 执行：lit-verifier（task-191）｜ 工作目录 `D:\MAESTRO`
**协议**：[PROTOCOL_DATA6.md](PROTOCOL_DATA6.md)（v1 FROZEN）｜**状态：`not_sent_awaiting_user_authorization`——本任务未发送邮件、未提交任何表单。**
**边界**：metadata-only；只读公开页面/API；不伪造/猜测联系人；不绕过登录/许可；技术三重复≠独立培养；PDF 图≠numeric 功能数值；不称新颖性/药理/真实决策/迁移/机制；不改旧判定；不晋升代码。

## 0. 结论（先行）

1. **联系人已从公开全文核验**：通讯作者 **Mathew J. Garnett**（Wellcome Sanger Institute）`mg12@sanger.ac.uk` 与 **Jerome Mettetal**（AstraZeneca Oncology R&D）`jay.mettetal@astrazeneca.com`，来自 Europe PMC 公开全文 XML 的 Correspondence 块（`<corresp id="CR1">`；DOI 10.1158/2159-8290.cd-23-0388 / PMID 38456804 / PMC11061612）。附机构页二次来源（Garnett 页面编码 mailto 解码为 `mathew.garnett@sanger.ac.uk`，仅作旁证）。
2. **Figshare 维护者无公开邮箱**（Howard Lightfoot / Elizabeth Coker；10 个 article 均 CC BY 4.0；project 页面 HTTP 202 空体/SAP 门控）→ 按纪律记 `not_found_in_public_text`，**不猜测个人地址**。
3. **GDSC 专用数据访问邮箱在公开文本未发现**（gdsc-combinations 页面为 JS shell，HTTP 200/5,444 B 无联系文本）；Sanger 通用邮箱 `contact@sanger.ac.uk` 可作**标注为 generic 的 fallback**（来源 Sanger contact 页）。
4. **请求信草稿已完成**（英文，总 **343** 词/正文 **317** 词 ≤350；P0×3 + P1×2；non-commercial academic；含不 re-identify/不超许可再分发/不把技术重复当独立培养的承诺；发信人/署名留占位待用户填）。
5. **DATA1 spec 对齐**：REQ-MAP-01/REQ-REP-01/REQ-FUNC-01（P0）与 REQ-PROT-01/REQ-DICT-01/REQ-CODE-01（P1）已入信；REQ-SUPP-01（P2）**有意留作后续**，避免首封信过长。
6. **是否建议用户授权发送**：**建议授权**（正式、低风险、non-commercial academic 的公开数据补充请求，收件人为论文公开通讯作者；不索取私有数据、不绕过许可）。但**发送前必须由用户确认** §4 的 8 项（收件人/cc、署名、附件、许可措辞、无收益承诺、是否联 Figshare、是否用 generic fallback）。**本包未发送。**

## 1. 联系人核验结果

| ID | 联系人/角色 | 邮箱/渠道 | 状态 | 来源锚点与逐字引文（≤40 词） |
|---|---|---|---|---|
| C-AZ-01 | **Mathew J. Garnett**（通讯作者，Sanger/GDSC 侧） | `mg12@sanger.ac.uk`（+441223 834244） | `verified_public_in_fulltext` | Europe PMC fullTextXML PMC11061612，`<corresp id="CR1">`：**"Correspondence: Mathew J. Garnett, Wellcome Sanger Institute, Hinxton, Cambridgeshire, CB10 1SA, UK. mg12@sanger.ac.uk"**（引文为 XML 去标签文本片段）；回执 `receipts/epmc_fulltext_PMC11061612.xml`（SHA 见 contacts_verified.json） |
| C-AZ-02 | **Jerome Mettetal**（通讯作者，AZ 侧） | `jay.mettetal@astrazeneca.com`（+1781-672-4277） | `verified_public_in_fulltext` | 同一 `<corresp id="CR1">` 块：**"Jerome Mettetal, Oncology R&D, AstraZeneca, 266 2nd Ave #200, Waltham, MA 02451, USA. jay.mettetal@astrazeneca.com"**；同一回执 |
| C-FS-01 | Figshare project 163378 数据上传者 **Howard Lightfoot / Elizabeth Coker** | 无公开邮箱；project 页面 HTTP 202 空体 | `not_found_in_public_text` | Figshare API project/articles metadata（10 articles，均 CC BY 4.0，只有作者名）；回执 `receipts/figshare_project_163378_articles.json`、`receipts/figshare_article_*.json`。**不写不存在、不猜地址** |
| C-GDSC-01 | Wellcome Sanger Institute general enquiries（**generic fallback，非 GDSC 专用**） | `contact@sanger.ac.uk` | `verified_public_generic` | `https://www.sanger.ac.uk/about/contact/` 页面文本：**"General enquiries: contact@sanger.ac.uk"**（上下文另列 HR/recruitment 等）；回执 `receipts/sanger_contact.html` |
| C-PUB-01 | AACR 出版商页面 | — | `restricted_HTTP_403` | `https://aacrjournals.org/cancerdiscovery/article/14/6/1014/744431` 返回 403；**未绕过**，改用 Europe PMC 公开全文 |

补充旁证（非主收件人）：`https://www.sanger.ac.uk/person/garnett-mathew/` 的公开 mailto 为 URL 编码 `%6d%61the%77%2E...`，解码后 `mathew.garnett@sanger.ac.uk`；已在 `contacts_verified.json` 记录原串+解码串，**论文 Correspondence 邮箱仍为主**。

数据可用性声明（公开全文）：**"Fitted and raw data are available through Figshare and the GDSC Combination website"**（Europe PMC fullTextXML 纯文本逐字命中；锚=Data availability 段）——说明公开的是 fitted/raw 数据页，**mapping 与 Fig 4/5/6 numeric 不在公开 listing**（DATA1 报告 `partial`），本请求正是补这两类缺口；**不推断作者未做**。

许可（Figshare API metadata 实测）：project 163378 全部 **10 个 article 均 CC BY 4.0**（`receipts/figshare_article_*.json`）；请求信据此承诺按原许可或作者指定 terms 使用、不超许可再分发。

## 2. 请求信草稿（[REQUEST_LETTER_DRAFT.md](REQUEST_LETTER_DRAFT.md)）

- 主题：Data request - mapping and functional source data for AZ/GDSC 2024 combination screen (CD-23-0388; Figshare project 163378)。
- 收件人：`[Mathew J. Garnett]`（主）/`[Jerome Mettetal]`（cc 待用户定）；发信人 `[Name]/[position]/[institution]/[address]/[email]` 占位。
- 结构：non-commercial academic 目的 → 已公开内容致谢 → **P0**：① BARCODE/cmatrix/CELL_ID→experiment/occasion/technical replicate/treatment date/passage/culture 映射（7 系/754 系）；② 7×6×3 官方计数/映射 + technical vs independent + 与 301 exact-18/161 6×3 对账；③ Fig 4E/F、5C/D、6C–E caspase/PARP/western numeric + uncropped blots；**P1**：④ 72h/CTG/Caspase-Glo/QVD 逐批协议映射；⑤ README/字段字典+公开 notebook。→ 承诺（不 re-identify、不超许可再分发、技术重复不当独立培养）→ 回复方式。
- 词数：总 343 / 正文 317（≤350）；无新颖性/收益/机制措辞；无合作/署名/资金承诺。

## 3. 与 DATA1 spec 的对齐（详见 [request_package_summary.json](request_package_summary.json)）

| spec id | 优先级 | 草稿位置 | 入信 |
|---|---|---|---|
| REQ-MAP-01（BARCODE→occasion/replicate/date/passage/culture） | P0 | P0-1 | ✅ |
| REQ-REP-01（7 系×6×3 官方计数/映射；technical vs independent） | P0 | P0-2 | ✅ |
| REQ-FUNC-01（Fig 4/5/6 caspase/PARP/western numeric + blots） | P0 | P0-3 | ✅ |
| REQ-PROT-01（72h/CTG/Caspase-Glo/QVD 批次映射） | P1 | P1-4 | ✅ |
| REQ-DICT-01 + REQ-CODE-01（README/字段字典/notebook） | P1 | P1-5 | ✅ |
| REQ-SUPP-01（补充图表 numeric） | P2 | 未入信（有意留后续） | ⏸ |

## 4. 发送前需用户确认/授权（未完成前不得发送）

1. 主收件人是否用 `mg12@sanger.ac.uk`（或改用另一通讯作者）；2. 是否 cc `jay.mettetal@astrazeneca.com`；3. 发信人姓名/职位/机构/地址/邮箱（占位待填）；4. 附件政策（建议**无附件**首封；或一页字段清单，用户定）；5. 许可/terms 措辞（公开数据 CC BY 4.0；共享文件按作者 terms；不 re-identify/不超许可再分发）；6. 确认信中**无任何新颖性/决策收益/机制主张**、无合作/署名/资金承诺；7. 是否同时联系 Figshare 维护者（无公开邮箱；平台渠道可能需账号；**不得猜地址**）；8. 是否允许把 generic `contact@sanger.ac.uk` 作为 fallback（须标注 generic）。

## 5. 回执与限制

- 回执：`receipts/` 共 **21** 个文件（Europe PMC core/fulltext XML、Figshare project/articles JSON ×11、Sanger 页面 HTML、GDSC/AACR 状态回执等）；`contacts_verified.json` 内含逐文件 SHA256 index。
- 公开来源限制：AACR 页面 403（未绕过）；Figshare project 页面 202 空体（SPA/门控，未用其判定）；GDSC-combinations 页面为 JS shell（无联系文本）；depmap contact 页一次 SSL unexpected EOF（未重试成功，不据此判不可得）；GDSC 专用数据访问邮箱**有界检索未发现公开地址，不写不存在**。
- **未发送**：`emails_sent=0`、`forms_submitted=0`、`automated_sending=false`；状态 `not_sent_awaiting_user_authorization`。

## 6. 产物 SHA256（关键）

| 文件 | SHA256 |
|---|---|
| `contacts_verified.json` | `7D5CE000D91179B11A233EDD144E06BF8EECA7FE36F2D0E92FDD2A5986FCDFCD` |
| `REQUEST_LETTER_DRAFT.md` | `41C781564059360BF5140594922B1E09AC9B2FD18327B036665B11DB02096405` |
| `verify_contacts.py` | `5F350F1BD426E6EECA58410A830FC6B2CC6F9EE8E31C95BD5D418B09502010F4` |
| `PROTOCOL_DATA6.md` / `request_package_summary.json` | 见 usage_data6.json（定稿后记录） |
