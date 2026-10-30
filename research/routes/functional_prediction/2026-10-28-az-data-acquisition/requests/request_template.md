# R204-DATA1 请求模板（作者/Figshare）

**用途**：向 AZ/GDSC 2024 论文通讯作者或 Figshare project 163378 维护者请求公开导出缺失的映射/源数据。**不是**声称实验未做；只是请求可分析记录。发送前按 Figshare/期刊要求走公开联系方式，不伪造邮箱。

## 主题

Request for data dictionary/mapping and functional source data for AZ/GDSC 2024 combination screen (Cancer Discovery CD-23-0388; Figshare project 163378)

## 正文要点（可直接改写）

您好，

我们正在复用贵团队 2024 年 Cancer Discovery 论文（CD-23-0388；PMC11061612）公开在 Figshare project 163378 的 7×7 matrix 组合筛选数据。该导出提供了 raw well ZIP、matrix summaries、plate QC（部分 article 直链）与字段 glossary；我们非常感谢这些公开资源。

我们注意到论文 Methods 报告：
- 72 h 药物处理 + CellTiter-Glo 2.0；
- A375、HT-29、PC-14、U-2-OS、SW620、C32、MHH-ES-1 七个细胞系在 6 次实验中作技术三重复（每 compound 18 replicates，若 plate 过 QC）；
- Fig 4E/F、5C/D、6C–E 有 cleaved PARP/cleaved caspase-3 等 apoptosis 验证。

当前公开导出/补充中，我们可以识别 raw well/matrix 结构，但**没有找到**：
1. `BARCODE`/`cmatrix`/`CELL_ID` 到 experiment/occasion/technical replicate/treatment date/passage/culture 的映射；
2. Fig 4/5/6 的 caspase/PARP/western numeric source data（Europe PMC supplement 只有 Supplementary Figures PDF，无 numeric 表）；
3. 7 系 ×6 实验 ×3 technical triplicate 的官方计数/映射与 72 h/CellTiter-Glo/Caspase-Glo/QVD 的逐批协议字段。

如果您方便，能否提供（按优先级）：
- **P0**：一张 mapping 表（每行一个 BARCODE/cmatrix/cell/pair/well；字段包括 experiment/occasion、technical replicate index、treatment/read date、passage/culture ID、QC flag），覆盖 7 个重复细胞系（如可，覆盖全部 754 系）；
- **P0**：Fig 4E/F、5C/D、6C–E 的 numeric source data / quantification，以及未裁剪 western blot 原图、抗体/加载对照/时间点/重复信息；
- **P1**：72 h/CellTiter-Glo 2.0/Caspase-Glo 3/7/QVD 与 BARCODE/PROJECT/DRUGSET 的批次映射；
- **P1**：各 Figshare dataset 的 README/字段字典（含 `CELL_ID` 的 stock expansion 语义），以及用于生成/校验映射的公开 notebook/代码；
- **P2**：补充图/表 numeric source data（CSV/XLSX）。

格式 CSV/TSV + README 即可；不需要重做实验，也不要求私有/伦理未覆盖的数据。若没有现成 mapping，能否确认是否可以用公开 `BARCODE/SCAN_ID/DRUGSET_ID/cmatrix` 与 plate QC 生成候选映射、并由贵团队确认 technical/biological 语义？

我们会在研究记录中注明数据来源/版本/许可，不绕过任何访问限制，也不会把技术三重复当作独立培养。

谢谢！

（署名/机构/日期）
