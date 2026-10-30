# DQ1：同筛导出单药响应的观测资格，事前冻结

2026-10-29。此为数据质量/来源层级核查，不是算法优势或药理效应H。只读既有tmp/extq1/gsdc_well_stats.zip内combo_well_stats_GDSC_007_05May22.csv前20000行；先核原ZIP SHA256 `e8cb50f6ce860fa17586a555130cb3b019f6011ed1976c0f0d3e00fb072d3259`。固定前缀与前轮相同，不按响应筛样。

仅投影PROJECT_ID、BARCODE、MASTER_CELL_ID、CELL_ID、POSITION、cmatrix、lib1/2_drug_id、lib1/2_drug、lib1/2_conc及本轮首次允许的lib1/2_y。禁止读取/保留/解析yhat、IC50、AUC或inhibition作功能标签；csv行流字节包含它们，usecols排除。

两侧分别形成exported reference key=(project,cell,ref,conc_numeric)，浓度须有限非负、单位按原字典µM，零浓度单列。用Decimal从原文本解析；不舍入浓度，不强制把不同ref/plate合并。每键统计出现数、y原字符串唯一数、有限Decimal数及数值唯一数；数值相等要求exact Decimal equality，容差0，不在看到差异后放宽。缺失/非数/NaN/inf单列，不筛掉不利条目。超出[0,1]记录，不clip。核ref对plate/cell/drug映射冲突与同drug多ref；组合行POSITION不当单药源well。

资格结论逐项给出：若重复键均有唯一有限y、身份映射不冲突，则该键可作为同筛导出层级的一个确定观测单位，用于之后另冻的开发预测；这不认证一个原始仪器测量/独立培养、噪声均值或跨筛迁移。若一键多个不同y，说明键不足或响应处理不一致，禁止静默平均，保存冲突键数量与有限例以供后续追溯；此资源不准入该键上的独立评分。若只有部分键合格，报告范围而不自动选阳性子集运行算法。

保存dq1_result.json（摘要、全部规则/实际耗时/hash、开发暴露边界）与最多16个由键字典序固定选取的算术packet；不得按响应大小或冲突方向挑packet。不保存全响应矩阵，不开展拟合/选药比较。cpu120s/ram1GiB/output20MB、0GPU/安装/模型API。重要计算由root复核；若后续需要独立重写先给同协议，不将本次工程通过作科学成立。
