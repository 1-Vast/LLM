# PRISM 19Q4 开发暴露与保护范围定向复核

2026-10-28。本episode第二项定向只读核查；不是“新细胞8个药敏反馈→预测另一药物菜单”假设的独立终审。没有读取sealed*/confirmation/.env/任何功能矩阵，没有新增网络、模型/API、实验或子代理，没有改共享索引。

**可以使用19Q4 primary作为已暴露开发来源，不能使用24Q2响应，也不能把19Q4新分割称作未暴露确认。** 历史普通协议对primary整体的“exposed input, never confirmation”及4,528 parsable training compounds有直接文字证据；没有找到为19Q4 primary另外保留的、仍未读的细胞/药物确认子队列。不过“没有找到”不是解除任何既有保护的授权；当前4,686发布列与历史4,528 canonical compounds的逐ID对应尚未完成，本核查不批准把未识别列自动加入。

## 1. 精确历史来源与读取范围

已通过 `python -m tools.retained_records --restore <exact source_id> --destination <当前episode/tmp_exposure_review>` 逐文件恢复五份**普通协议/开发计划**；没有恢复整个研究目录。原source_id、还原路径、SHA256及字节在 `sources/cheap_data/exposure_source_manifest.json`。下列行号针对该逐字还原本：

| 证据 | source_id及精确位置 | 原文所能支持 |
|---|---|---|
| E1 | `research/knowledge_reality_20261013/DEV_PLAN.md` L3–5 | “PRISM 19Q4 is already exposed to MAESTRO (blocks N and P, and the selective hit triage), so nothing here can be claimed as independent confirmation.” 该整个阶段为exploratory gate |
| E2 | `research/knowledge_reality_20261013/PROTOCOL.md` L99、L127–130 | Training compounds' outcomes明确为“PRISM 19Q4 primary, all 4,528 parsable compounds”；每臂拟合全部19Q4 compounds。全量parsable primary作为旧训练来源，不是仅某个开放小block |
| E3 | `research/selective_hit_triage_20261013/PROTOCOL.md` L25–28、L64–78 | PRISM primary明确“exposed input, never confirmation”；125 development/128 test封存拆分属于**CTRP v2确认终点**。不能因同一个药物处于CTRP test就错误推断其PRISM输入未暴露；也不能借PRISM已暴露读取CTRP确认数据 |
| E4 | `research/indication_triage_20261016/PROTOCOL.md` L24、L101、L411–418 | 锁定world model用all4,52819Q4 compounds，training19Q4 responses为允许模型输入；明确19Q4已暴露。24Q2 metadata已读但响应未读、与knowledge_reality共享封存资源，开放会影响另一协议，选择属owner |
| E5 | `research/knowledge_reality_20261013/PROTOCOL.md` L16、L20–33、L103–107 | 旧gate未过不运行stage2；下载24Q2须owner授权，先锁预测，再下载并核MD5；任何24Q2response禁止进入预测输入 |
| E6 | `log/20261022/prism_profile_opportunity/PROTOCOL.md` “Fixed split and permissions”“Numerical permission and coverage success/stop”段 | 这是HTS002 **secondary**的指定两池/板/化学结构切分。源565/dev211/test255、掩码权限和禁读primary均是该特定任务合同；并明确既有raw exposure不构成新生物holdout。不能直接移用其test标签/掩码，也不能把它的“禁primary”错误扩成整个项目永久禁primary |
| E7 | `data/INVENTORY.md` L34、L49、L70 | 现用`external/prism_19q4`登记exposed internal development；旧`data/raw/prism`为空；发布版本/谱系由RSD/program-revision冻结，不以文件名猜新颖性 |
| E8 | `log/RESEARCH_REPORT.md` L134、L195、L211 | knowledge_reality负gate与24Q2未开；secondary固定面板coverage失败且不得按观察mask换池/放松阈值冒充确认；indication_triage未冻结开发及传播复读问题保留 |

`research/INDEX.md`本轮只搜PRISM相关已登记条目（尤其L210、L255、L257）；它们是组合跨screen资格或分子—功能名义匹配，不能提供19Q4未暴露子队列证据。没有因为单一入口缺少细目就停查，已交叉核普通历史协议。

## 2. 对新问题可明确引用的开发输入

本地实际入口，来自本episode前一份资源核查：

- `D:/MAESTRO/data/external/prism_19q4/raw/primary-screen-replicate-collapsed-logfold-change.csv`，41,254,209B：发布、DMSO相对、ComBat校正、重复中位合并的功能矩阵；本轮原字典未认证重复类型，原草稿“技术重复”措辞撤除。**本资源核查未打开功能值**。不是原始well荧光，不支持假造新重复或独立培养。
- 同目录`primary-screen-replicate-collapsed-treatment-info.csv`，1,185,606B：药物/batch ID、名字、剂量、screen_id及矩阵列键。可作为冻结药物菜单与反馈候选集的metadata来源。
- 同目录`primary-screen-cell-line-info.csv`，46,849B：cell/DepMap ID、矩阵行键与STR metadata。可作为冻结新训练/新细胞分割的metadata来源。
- 同目录`primary-screen-readme.txt`，5,919B：归一、ComBat和重复合并的发布字典。现有primary没有本地重复级条件/池表；不要从secondary池映射伪造primary来源。

**最窄、历史证据明确的范围**是旧研究已经作为开发来源的19Q4 primary parsable compounds/原有cell panel；E1/E2/E3说明该范围可作开发，而非新确认。对“另一药物菜单”，只表示冻结feedback drugs与evaluation drugs分离；它不自动等于药物在整个旧历史未出现，也不等于独立实验/培养。新细胞也只能指新协议模型训练中未见，不能指项目从未看过这些公共标签。

本次没有从功能值或已有得分选8个药，也没有挑评估菜单、定义新阈值或评判哪个算法好。先以metadata冻结cell split、化学实体/别名合并、dose/screen角色和反馈/评分药物分离，后续获准的受限adapter才可访问相应值。所有来自测试细胞全菜单的均值、协方差、标准化、缺失模式筛选、面板搜索和超参数都不能提前反流给选择器。历史已暴露不会替新协议消除信息隔离要求。

## 3. 明确禁止/未知范围

| 范围 | 本轮判断 |
|---|---|
| PRISM24Q2响应：Figshare46630984/`Repurposing_Public_24Q2_Extended_Primary_Data_Matrix.csv` | **禁止下载/读取**。E5门控及当前父任务明确禁读均适用；gate失败不意味着可消费封存集。未访问census脚本/SEALED_CENSUS/响应 |
| 任意既有`*_sealed`、sealed目录、confirmation目录和各旧协议受保护oracle/cache | **不打开、不重映射、不因19Q4泛称exposed而解封**。包括derived block_n/block_p的sealed NPZ；没有读取其内容。原始来源允许开发与封存产物的访问限制必须分开处理 |
| CTRP v2旧确认test终点 | 本新任务未授权；PRISM输入已暴露不是其确认终点读取许可 |
| PRISM secondary两池固定面板test及隐藏audit masks/labels | 原任务停止/掩码权限不自动转移。新primary任务不需读取它们；不要用其结果选新面板/阈值再称未经观察 |
| 当前primary4,686列中的“4,528 parsable canonical”映射、未解析/特殊剂量/重复药批余列 | **尚未逐ID核实**。1列≠1化合物；前次metadata亲核screen=HTS/MTS004且dose有416种字符串。旧“2.5µM/4,528”不能当全部当前列相同剂量证明。可以继续metadata-only实体与dose核对，但没有核清的列不自动纳入新实验 |
| 当前588 cell_info行与旧561/545 panel映射 | **尚未逐ID核实**。含STR/NA等，不直接当588合格细胞；已有561/545是不同历史任务口径，不凭人数推断保留/禁止身份 |
| 19Q4 primary是否存在另一个普通合同明确保留的cell/drug子队列 | 本轮检查的E1–E8**未找到**；有整体暴露和全4,528训练文字。该负检索不认证所有历史合同均已穷尽。新协议应把暂未映射ID排除/待定，不先开全部数值来找答案 |

## 4. 停止条件与本次交付性质

可前进的部分是本地、已暴露19Q4 primary的metadata分割冻结和开发性重放准入，不需要24Q2或特殊仪器接口；现有旧结论不由本复核推翻。若逐ID核对发现某个候选cell/drug仍受另一个明确合同保护，保留该合同并排除它；不能把“公共数据”或“以前有人用过”当成解除保护。若未识别列无法解析，停在该列/子集，不阻塞其余明确来源的metadata准备。

没有批准科学方案、没有测试独立药物菜单覆盖/8次反馈的价值、没有给予独立培养或药物发现收益认证。全过程0网络/0模型API/0功能矩阵读取/0旧实验；仅按exact source_id恢复5份普通文字源到当前episode临时区，附SHA manifest。前次资源核查所见目录级sealed文件名没有被打开，本次不枚举该目录。
