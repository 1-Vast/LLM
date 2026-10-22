# Exact Day identity block sealed

2026-10-22. **SEALED_IDENTITY_ONLY.** 按root明确授权，仅解释/导出原始 MOESM9 `Fig.5a!E2:E61` 的数值Day，并与既有安全投影中的B/C/D字符串逐行核对；没有解释/导出F/G或其他数值单元。

- **60/60行一致**：E列Day等于同一行B=`Tetracycline {lineage}/Azithromycin/{day}`末段日期；C=`Tetracycline {lineage}`、D=`Azithromycin`也逐行一致。
- 身份键恰好为 **lineage{1..12} × day{2,3,5,7,10}**，共60个唯一键；重复、缺失和意外键均为0。
- 所有允许坐标均为不含公式的numeric整数日期。精确访问坐标、逐行身份、日期及比对结果在 `CENSUS.json`；F/G响应数值没有打开，未读取其他worksheet内容。
- **零HTTP / 零模型API**，无编辑、重算、渲染或workbook导出。原始workbook前后SHA256均为 `7121607f19a554b21a012a69839dff6abcfd37b2ea50581f48e3cd1552e4cc97`。10个冻结文件最终哈希全部不变。
- 9项合成测试通过，覆盖F/G/外部坐标排除、整数/公式/字符串类型守卫、缺失/重复坐标、逐行冲突、重复/意外谱系键及字节不变。首个测试命令的语法错误在未打开源数值前修复，失败原因保留于 `PRE_CENSUS_FAILURE.md`。

封存只认证谱系/日期身份。先前发表定性结果仍属design-exposed；本块不认证genomic state、F列药物目标、response测量质量、独立任务数量或任何模型/RSI性能。此前WGS文件名与Fig5a的36个名义身份匹配，现在获得明确Day列的一致性支持；物理样本、变异状态及功能数值的认证仍按root其他工作分别处理。
