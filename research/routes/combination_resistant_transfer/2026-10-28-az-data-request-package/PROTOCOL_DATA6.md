# R204-DATA6 协议：AZ DATA1 数据请求包（联系人核验 + 草稿；不发送）

**版本 v1，FROZEN（在请求包定稿与任何发送动作之前冻结）** ｜ 2026-10-28 ｜ 执行：lit-verifier（task-191）
工作目录 `D:\MAESTRO`。只写 `research/2026-10-28-az-data-request-package/` 与 `tmp/`；**不改 R202/X1/X2/DATA1–5 产物**；**不发送邮件、不提交表单、不绕过登录/许可**。

## 1. 目标与范围

为 R204 主线的 **AZ/GDSC 2024 DATA1 作者补充路径**准备一个**可授权发送**的请求包（本任务不发送）：
1. 从公开来源核验 **通讯作者/数据访问联系人**（邮箱或公开表单）并记录 URL/引文/锚点；
2. 起草 ≤350 词英文请求信（non-commercial academic；P0/P1 字段见 §4）；
3. 将 DATA1 spec 的 P0/P1/P2 与草稿对齐，列出**发送前用户必须确认/授权的项**；
4. 明确发送状态 = `not_sent_awaiting_user_authorization`。

不在范围：发送/提交、伪造或猜测联系人、索取私有/伦理未覆盖数据、任何效果/湿实验、任何新颖性/药理/决策/迁移/机制主张、修改旧判定。

## 2. 输入（只读）

- `../2026-10-28-az-data-acquisition/report_data1.md`、`PROTOCOL_DATA1.md`、`requests/data_request_spec.json`、`requests/request_template.md`；
- `../2026-10-28-az-code-hunt/report_data2.md`；
- `../2026-10-28-data-readiness/DECISION_R204_DATA_READINESS.md`；
- 登记表 C200/C202/C203/C205/C210/C211/C214（边界：公开数据不足，但**不写"不存在/作者未做"**；mapping 可由作者补充，真实功能确认需新测量）。

## 3. 联系人核验规则（冻结）

- 只使用**公开**来源：Europe PMC REST（core + fullTextXML）、Figshare 公开 API、GDSC/Wellcome Sanger 公开页面、论文页面（若可公开访问）。
- 对每个联系记录：`name/role/affiliation/email|form`、`source_url`、`anchor`（XML 节点/页面区块）、**逐字引文≤40 词**、`receipt`（保存的原始响应 + SHA256）、`status`。
- 状态（且仅这些）：
  - `verified_public_in_fulltext`：论文公开全文中明确列出（Correspondence 块）；
  - `verified_public_obfuscated_mailto`：公开页面的编码 mailto（解码后记录原串+解码串）；
  - `verified_public_generic`：机构通用联系（非数据访问专用；必须标注）；
  - `not_found_in_public_text`：公开文本中未发现（**不得猜测/编造**；不写"不存在"）；
  - `restricted_HTTP_403`：出版商页面受限（不绕过；用 Europe PMC 公开全文替代）。
- 不提交表单；不创建账号；不绕过 paywall/登录。

## 4. 请求信约束（冻结）

- 英文，**≤350 词**；non-commercial academic；说明研究目的=独立验证 Agent×虚拟细胞决策模型的数据可行性（不称新颖性/收益）。
- 列 P0/P1 字段（与 DATA1 spec 对齐，不扩张）：
  - **P0**：`BARCODE/cmatrix/CELL_ID → experiment/occasion/technical replicate/treatment date/passage/culture` 映射（7 具名系 109 pairs/6 occasions×3 technical；尽量 754 系）；7 系×6 实验×3 technical 的官方计数/映射（含是否独立培养；与 301 exact-18/161 6×3 对账）；Fig 4E/F、5C/D、6C–E caspase/PARP/western numeric source + uncropped blots。
  - **P1**：72h/CellTiter-Glo 2.0/Caspase-Glo 3/7/QVD 逐批协议映射；Figshare 各 dataset README/数据字典（`CELL_ID` stock expansion vs passage、`cmatrix` 语义）、公开 notebook/代码。
- 承诺：仅 non-commercial academic 使用；按 CC BY 4.0 或作者指定 terms；**不 re-identify、不超许可再分发、不绕过限制**；引用论文与数据版本；**不把技术重复当独立培养**除非作者确认。
- 不承诺未授权事项（不承诺合作/署名/资金/不发表等）；不索取 DATA1 spec 的 `do_not_request` 列表内容。

## 5. 发送门槛（冻结）

- 发送状态：`not_sent_awaiting_user_authorization`。**本任务不发送、不提交**。
- 发送前用户必须确认：① 收件人（主收件人/cc）；② 发信人身份与签名；③ 附件政策；④ 许可/terms 与承诺措辞；⑤ 是否同时联系 Figshare 项目维护者（无公开邮箱）与通用 fallback 是否使用；⑥ 声明措辞不得含新颖性/收益/机制主张。
- 任何发送行为须用户在会话中**明确授权**；本包只提供草稿与证据。

## 6. 输出（本目录）

`PROTOCOL_DATA6.md`、`verify_contacts.py`、`contacts_verified.json`、`REQUEST_LETTER_DRAFT.md`、`request_package_summary.json`、`report_data6.md`、`record_data6.md`、`usage_data6.json`、`receipts/`（公开来源原始响应 + SHA256 + receipts index）。

## 7. 边界

metadata-only；不发送/不提交；不伪造/猜测联系人/邮箱；不绕过许可；技术三重复≠独立培养；PDF 图≠numeric 功能数值；`not_found_in_public_text` ≠ 不存在；不改旧判定；不称新颖性/药理/真实决策/迁移/机制；不晋升代码。

## 8. 复现

```powershell
cd D:\MAESTRO\research\2026-10-28-az-data-request-package
& D:\anaconda\envs\maestro\python.exe verify_contacts.py
# 只读公开 API/页面；不发送任何请求/表单；原始响应写入 receipts/；然后由数据核验脚本生成 contacts_verified.json
```
