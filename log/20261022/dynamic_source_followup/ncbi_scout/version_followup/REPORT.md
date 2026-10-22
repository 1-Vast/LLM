# Official version metadata authenticated

2026-10-22。按Root新增独立协议 **1 GET / 4,090bytes、HTTP200**，未redirect或retry。原4GET scout的302→本version身份链保留：conceptDOI `10.5281/zenodo.14064963`，versionDOI **`10.5281/zenodo.14064964`**，version **v1.0**。原块488,928bytes与本块4,090bytes分账，合计5请求493,018bytes；第4请求官方302未自动跟随，第5请求是获准的显式新请求。

官方registry title：**jamaltas/Temporal_Collateral_Sensitivity: Data for manuscript**。Description为“Data for Dynamic collateral sensitivity profiles highlight opportunities and challenges for optimizing antibiotic sequences”，与最终论文title尾词treatments不同；不能只凭近似title推出关联。但最终论文DataAvailability明确链接conceptDOI，正式versionmetadata确认相同conceptrecid，因此链可认证。

唯一registered file：

- `jamaltas/Temporal_Collateral_Sensitivity-v1.0.zip`
- **3,880,800bytes**
- checksum **`md5:016c1273da5492848aa8f60e9f511554`**
- metadata直接给file-content URL，未访问。

registry `related_identifiers`明确 `isSupplementTo` / software / **`https://github.com/jamaltas/Temporal_Collateral_Sensitivity/tree/v1.0`**。open、CC-BY4.0。该metadata仅认证archive和repo版本身份，**没有认证zip内部是否含raw OD、IC50、daily浓度、lineage IDs或所有attempts，也不证明存在molecular state。** 未取zip、repo tree、README、S1Data或任何response file。

可交独立source auditor的最低成本下一对象是上述 **GitHub v1.0 tree metadata/README**，先列data/code路径、文本schema及原版SHA，不需要先下载3.88MBzip或打开响应。论文另一精确身份为S1Data `pbio.3002970.s001.xlsx`。要审查的join见父目录REPORT：主5drug×4lineages×day2/4/6/8与单独CRO14day×20populations的DOX24h挑战，clone/population、dose/control/assayreplicate与真正postchallenge continuation。没有这些身份，不能把4timepoints或400combinations视为全动态任务。

现阶段state只按**phenotypic collateral resistance profile**；未知evolved molecular state。原文已做phenotypic Markov/dynamic-programming模型与timed second-drug challenge，不把它包装为新world/agent算法。此source discovery没有证明任何项目性能、新颖性、继承或RSI。

Receipt与rawrecord在本目录 `NETWORK.json` / `RECORD.json`；最小投影 `MANIFEST.json`。本次没有失败或覆盖；原302如实保留。到此本授权单GET已用完，不继续请求。
