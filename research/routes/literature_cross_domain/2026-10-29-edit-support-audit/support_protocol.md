# E.v1 结构支持审计冻结规则

2026-10-29。只检验普通公开数据能否提供所需的结构/观测交叉机会，不检验药效、机制或算法性能。规则在读取本轮化学支持计数前固定，不因计数改变。

输入为既有 `tmp/extq1/gsdc_well_stats.zip`（SHA256 `e8cb50f6ce860fa17586a555130cb3b019f6011ed1976c0f0d3e00fb072d3259`）完整 GDSC007 成员；同项目 `tmp/extq1/gdsc-007_matrix_results.csv` 的 drug ID/name；公开40,475B Tahoe chemical metadata（SHA256 `7a04c7a6611e74c92253163b994ff0a47191928ee7511f1c2ca508cee0e79f28`，本轮正规HuggingFace公开URL下载且与既有两份副本相同）。不读取Tahoe表达/功能矩阵；该小表只提供drug/canonical_smiles/pubchem_cid。旧GDSC化合物API实际410，不作结构来源。

CSV仅语义访问 PROJECT_ID、MASTER_CELL_ID、两侧 libN_drug_id/libN_drug/libN_conc；matrix仅两侧 libN_ID/libN_name。全行会暂时tokenize，但不保留/数值解析/使用 INTENSITY、y、yhat、IC50、AUC、拟合误差、组合抑制等其他字段。浓度Decimal正有限、单位µM依据已存glossary。完整成员不取响应相关子集，不访问其他原始成员/受保护数据。matrix和metadata输入hash执行前记录。

结构连接：ID/name必须无一对多冲突；名称仅strip+casefold精确匹配，小表同名必须有唯一canonical structure/CID记录；不模糊匹配、补别名、改药名、猜盐型。这个连接只能证明来源表名义一致，不独立认证实物身份；未映射/歧义单列，不能把缺失结构当没有编辑。只接受可解析、单连通、含碳、总形式电荷为0、无金属、重原子>=6的分子；保持同位素与立体化学，不中和、不选盐主片段、不归并tautomer。规范化仅RDKit canonical isomeric SMILES，重复结构记录但不当独立分子。

编辑定义：在加显式H后的分子上，枚举所有非环单键（含H键），只切一键；用同位点dummy map1规范化两片段，移除普通显式H但保留dummy相连的H。常量core重原子>=6；变量fragment重原子0–8（0仅H），core重原子>=2×变量。相同规范core的两个不同变量给单点fragment replacement。方向按变量SMILES字典序固定；编辑key还包含core接点邻原子的元素/芳香/在环标志与连接键型。core、变量和接点原文保留。相同分子的重复ID不构成编辑。

功能支持仅身份剂量：每(cell,drug)选字典序最小ref，不跨ref合并。对于每编辑实例，两分子在一细胞有精确共同Decimal浓度才有一个(cell,q)机会；至少两细胞才可形成一编辑×两背景矩形。同编辑跨母体要求两实例用四个不同规范分子、不同core，且有相同q与至少两个共同cell。主输出是这些最低结构机会；另报告core的Bemis-Murcko骨架是否不同，不能把不同core自动称独立化学系列。相同q只指相同物理量，不代表生物等效。只保存计数、完整结构边与最多20个事前字典序例子，不看功能值择例。

最低条件若满足只称 `structural_opportunity_present`；time/assay/control/source-well/培养重复和未暴露评定未审计齐全仍是 `full_measurement_qualification_unknown`。未映射覆盖不足时，零合格边只适用于可映射子集，不关闭整个公共数据路线。若无两实例则不可检验本稿跨母体命题，不增加稀有配套补救。两实例不等充分功效/样本量。

工程准入采用固定合成结构检查：benzene→toluene与fluorobenzene→fluorotoluene应共享H→CH3编辑；同一分子不能成为编辑，盐及带电分子按规则排除。它们只验证化学图实现，不是科学数据结果。主实现与一次独立原输入重写分别CPU120s、RAM1GiB采样守卫、wall180s、output30MB，0重试/安装/GPU。独立重写在看主实现/结果前冻结；比较身份、映射、结构边、支持例子及计数，不放宽规则救一致。不运行药效拟合或取值。

执行前澄清（独立实施者提出，真实支持计数尚未读取）：ref 就是白名单中的 libN_drug，ID 为 libN_drug_id。全部行逐侧采集身份/剂量，不读取组合语义。因此这里只能称结构与剂量机会，不能认证四项确为可比单药功能读数；这一点须在完整测量资格中另核。ID↔strip+casefold 名称两个方向的一对多冲突均排除。无金属判定固定为原子序数集合 {3,4,11,12,13} ∪ [19,31] ∪ [37,50] ∪ [55,84] ∪ [87,116]，区间含端点；B/Si/Ge/As/Sb/Te不作金属排除。不得因结果改变此集合。

名称连接仅用 matrix 的 libN_ID/libN_name，well 的 libN_drug 不是药名。不跨 ID 合并剂量或 ref；若不同 ID 对实现同一规范结构编辑，保留 ID 对观测实例，并另报规范结构边数。跨母体仍要求四个不同规范分子和不同 core，重复 ID 不能增加结构支持。
