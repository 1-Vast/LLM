# 本轮实际核读及改变的决定

2026-10-29，root。原件请求见sources/root/retrieval.jsonl和request_intents.jsonl；chemical2020另有worker回执。下载/解析不等于全文核读。当前续接没有native web搜索工具，新增来源用明确公开URL获取；原先四query的首批结果仍保留，不作全面查新。0作者代码执行、0新功能响应访问/拟合/科学效果实验。

- **CVPR2026 RL-MBA**：完整官方PDF8093426B、9页，SHA25624dd2e759460a32ab4c49c048e2340aee50328b5ad797dd6bcb41442255b6abf。最初8000000B截断原件保留且不可作方法依据。root实际读p1、pp3–5；Sec3.1的动作是既有多模态样本标注，Sec3.2–3.4有固定验证集/模态贡献和校准，Sec3.6 Eq8–9可用预计算基线曲线作奖励，Sec3.7用REINFORCE。未读全部结果/SI/代码；不能把标注预算解释为独立付费药物/剂量测量或省孔证据。
- **ACL2026 PIR**：官方PDF1981783B、22页。首面正确题名为Reasoning While Asking: Transforming Reasoning Large Language Models from Passive Solvers to Proactive Inquirers；search_log早期into Proactive Interactive Agents标题错误，以此更正但不重写旧记录。root读p1、pp3–5；p4 Eq1实际为观察token平均负logp，不是直接词表熵；SFT含模拟response，RL对response mask的段落已单独恢复，p5奖励有正确性门、交互/LLM judge及效率项。用户模拟器持hidden intent，不是生物观测律。未核全部附录、实验或官方代码。
- **NatureCommun2026 REAP**：正式JATS260207B，精确PMID42706258/PMC13550471/DOI10.1038/s41467-026-76264-2；正式HTML303的150B跳转不当正文。root累计读Sec3、4、12–16、26及front license；Sec3/12 RankReg混合pairwise和MSE，optional pair subsampling实际未用；冻结PLM、轻量head、100网络ensemble/UCB、新实验回流已有直接先例。少样本训练和验证两份成本不能合并成仅50测量。主文CC-BY-NC-ND4.0，公开报告只写独立方法说明/引用，不上传原文。未核全文/SI/作者代码或重现实验。
- **PNAS2014 Gujral等**：Crossref精确题名及EuropePMC身份返回DOI10.1073/pnas.1403080111、PMID24707051、PMC3977247。EuropePMC fullTextXML返回500，保留150B错误并停止该host当前批次；独立官方PMC HTML200、175877B、SHA256466e46883c3e86cea58b2829a1e92b5b214b04eaeb26c03e1272b6d127c20376，核正文身份后读s3、s5主反卷积/共线性段、s6验证段、s8/s10。s5图例有一次中段截断，未依赖未恢复图例；关键正文段可见。PCA/B4选药、elastic net反卷积、未测药预测及共线性边界已有明确领域先例；s6另用siRNA验证，s8列体外/细胞内和累积假设，生化profile/功能回归取500nM。不能归因为普通表型+免费类别标签独立识别分子机制。Astra worker独立局部读该原件及2018/2025结合/RAED原件，准确范围见dictionary_development.md；不冒称root已全文读后面三件。
- **JCIM2020 MMP来源**：身份恢复但方法正文未得，worker精确PubMed DOI请求TLS EOF；0自动重试/改后端，方法字段unknown。不把缺文当作者未做，也不拿2023正式JATS未引此文作方法缺失证明。该缺口不阻其他独立来源。

四个新增来源经正式reference_library.py record/paper命令登记，未手写清单；REAP JATS按工具格式契约存supplement，不伪装PDF。verify当前133唯一源/117文件、10代码快照关联9论文，errors/warnings/changed空；只证所登记资产完整性，不证全面查新/全文核读/作者复现。新源码尚未核，状态not_verified，PIR首面官方仓库仅核链接，未获取或执行。

本次明确源请求没有总数/字节停止上限；45秒每请求、0自动retry/redirect仍有效。保留旧上限与失败是历史证据，不阻重新明确计划的完整获取。首批双host并发ledger非原子问题保留，续接请求均顺序执行；不宣称该脚本是全网络硬预算控制器。
