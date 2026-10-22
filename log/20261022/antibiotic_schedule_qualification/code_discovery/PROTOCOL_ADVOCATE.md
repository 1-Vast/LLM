# 抗生素3D论文：作者公开代码关联资格

2026-10-22，Asia/Shanghai。请求前登记。只围绕 Jeong/Tay et al. 2025，DOI10.1101/2025.10.30.684665，*Massively multiplexed microfluidics maps combinatorial and sequential antibiotic responses in 3D*。既有3次paper请求、2次exact DOI登记查询区块均已结束，本阶段不改其结论。

最多4次公共metadata GET、combined body≤2,000,000bytes、初始15分钟；顺序singlewriter，输出存在则在请求前拒绝覆盖，任何失败立即保存原始body/hash/status/UTC。优先GitHub官方repository搜索，若识别候选再读取其公开README/树manifest；不clone、不取dataset矩阵/响应/图像、不执行第三方代码、不检索DataCite/Zenodo/Figshare（另一独立代理负责）、不重试publisher429、不绕过全文格式限制、不发送email/messages。

初始查询采用精确title词组 `"Massively multiplexed microfluidics" in:readme`；若无候选，再用 `microfluidics antibiotic in:readme`。搜索返回最多10repo元数据；只把明确提到该paper title/DOI的README、CITATION或official关联作为linkage认证，不以同作者/同实验室/相近名字代替。后续manifest只观察公开路径/文件名/README声明，不读取数值内容。

需输出repo URL/owner/default branch/commit或tree SHA/公开日期、title/DOI实质关联证据、source/data文件菜单与是否需申请、处理schedule/轨迹/功能identity键是否已认证。无结果或API失败不证明source不存在。搜索到只有citation条目的无关review也不算作者release。来源可得性不是新机制或world/Agent/RSI批准。

脚本仅 `research/antibiotic_schedule_qualification_20261022/advocate_code*`，来源、协议、失败、结果仅本 `code_discovery/` 日志目录。
