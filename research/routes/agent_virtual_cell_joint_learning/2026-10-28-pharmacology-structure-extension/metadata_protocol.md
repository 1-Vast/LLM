# P7 只读附件核查边界

冻结于2026-10-28，读取任何工作簿单元格前。目的仅为核实 Punzi Extended Data 5 的实验条件、分组和重复身份，决定再挑战问题的资源资格；不是药效分析。

- 输入限已下载官方 MOESM8 ZIP 内 `Source Data/Extended Data 5.xlsx`；不运行宏、公式或作者代码，不修改原件。
- 读取 workbook/rels、sheet 名与 dimension、单元格类型计数；仅导出包含明确药物/细胞/协议词的短字符串标签，保留 sheet/cell 定位。数值单元格、公式值和全部其他字符串不导出。
- 预定标签词：FOLFOX/FOLFIRI/HCT116/DMSO/control/untreated/treatment/rechallenge/holiday/replicate/experiment/oxaliplatin/irinotecan/5-FU/5FU；单独的图分面标识只可用作定位。标签不是功能结果，也不是独立培养身份认证。
- 若剂量、时间或重复身份保存在数值区，本次保持 unknown；后续只有在原始表头与类型确定后另行冻结指定坐标。
- 输出 worksheet 清单、筛选标签、原工作簿与 ZIP SHA256。任何未导出字段记未核，不能记0或不存在。
- DeepSeek 只核给定标签的固定字段归类及缺失/歧义记录；数值工作由确定性程序完成，科学资格由 root 判断。

schema初查后追加：已有SFig5原图明确有CTRL，初版白名单control未包含该缩写；增加CTRL以核唯一未导出的字符串标签，不扩大数值区读取。保留初版DS012的原packet及其4标签范围。

本项为资料元数据检查，不占科学效果实验额度。不读取 sealed/confirmation/.env 或任何既有盲态预测。
