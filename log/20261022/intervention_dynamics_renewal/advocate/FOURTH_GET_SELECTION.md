# Fourth and final GET selection

官方primaryMethods/KeyResources明确公开 `https://github.com/zhoujw14/ADCC_model.git`，包含simulation与singlecellprocessingcode；data availability另给GSE255674（bulk术语但具体方法为ClariomS microarray）与PRJNA1076459 singlecell。因需确定实际公开functional/输入文件是否存在，最后GET选择官方repo **HEAD recursive Git tree metadata**：`https://api.github.com/repos/zhoujw14/ADCC_model/git/trees/HEAD?recursive=1`。repo未由paper给version，不假装pinnedpaperrelease；保留请求时完整treeSHA与truncated标志，只列文件名/size/blobSHA，不能执行/readblob/datacontent。

本块不再有第五GET或retry。若tree失败，保留失败；若有datafilepath，只算manifest身份，尚不算公开functionjoin。首轮本地primaryprojection的Results设计段落嵌套包含已发表figuretext与modelparameter表，已曝光的拟合数值为published/designexposure，不是本项目结果；没有下载/解析生物responsematrix。后续读段落时避开嵌套table，精确区分两者，不声称完全未见任何published numerical prose。
