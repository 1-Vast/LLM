# DECISION_R204_DATA_READINESS：真实功能数据就绪性汇总裁定（2026-10-28）

依据 R204 全部数据审计：C203（AZ 导出覆盖）、C205（AZ 获取性 partial）、C210（公开代码无 mapping/功能数值）、C211（下载+本地复算，same-platform structural only）、C212（多时间群体数据 not_qualified）、C214（功能时间进程 not_qualified）；以及用户"允许下载公开数据"授权下的实际下载核验。

## 1. 当前实际可用（仅同平台结构/描述，dev_only）
- AZ/GDSC 2024：raw well/matrix/Table S18 已下载并本地复算（68,710 单元/84,055 matrix/4,398≥2/301 exact-18/161 6×3，与 X2/X3 一致）。
- 可用分析：`same_platform_technical_repeat_structure`、`plate_barcode_qc_date_stratified_descriptive`、`partial_field_mapping`（cell/drug/dose/plate/cmatrix/QC date/SCAN 代理键）——**qualified_with_caveats、同平台结构/描述，非独立培养、非功能、非决策**。
- 多时间 RNA：GSE149428（0–24h）、GSE129012（4/8h）、GSE154932（0/7/10w）、GSE248450（4/12/20d）等可下载，但**无公开功能 numeric**，RNA 时间序列≠功能时间序列。
- M2/M1/M3 的 Stage1/Stage2 合成诊断均在 compute-only、0 wells 下完成或进行；仅机制账证据。

## 2. 仍不可做（真实阶段 data_unavailable；不得合成/RNA/预测替代）
- **独立培养/独立板重复**：AZ 仅技术三重复/QC 上传日结构；GDSC parser 无法生成 occasion/technical/passage/culture。
- **官方 6 次 occasion 认证/per-barcode 18 映射**：需作者数据字典。
- **正交功能 numeric**：Fig 4/5/6 caspase/PARP/western 仅论文图/PDF；公开数据（GSE154932 Incucyte、GSE248450 FUCCI、AZ、ctos）无 per-well/per-time numeric。
- **记录 π/随机化分配**：所有公开候选缺。
- **独立功能决策收益/跨背景迁移/真实药理确认**：无合格实测功能+暴露+独立评估+配对功效资源。
- **M2 Stage2 D1–D7、M1 Stage3、M3 Stage3**：数据门未过，均不执行。

## 3. 精确所需测量（若未来资源到位）
1) 每 (cell, directed pair, dose) ≥2 独立培养/板（不同日/passage/flask；技术孔不算）；
2) 数字剂量+暴露时间/检测方法（72h/CTG 等协议字段）；
3) 与目标端点同族（或单药参照校准）；不得 raw viability 直接混 ΔEMAX；
4) ≥1 正交功能读数（apoptosis/caspase/靶点参与/再生长/live imaging）的 per-well/per-time numeric；
5) 记录 π/动作/时间点/剂量与配对 RNA/计数（同处理同时间）；
6) 跨背景/独立任务留出与独立评估；
7) 决策收益按端点配对功效规划（不采用 6,282 通用门；MDE/headroom/cluster 预注册；需≈6,282 独立细胞仅适用 Fisher-z 相关系数比较，非通用门）。
8) 若仅补 mapping（不需新湿实验）：向作者/Figshare 发 DATA1 P0/P1 请求（mapping、per-barcode 18 映射、Fig4/5/6 numeric、README）；公开 download 路线已核（C210/C211/C212/C214），未发现该数据，**不写"不存在"**。

## 4. 裁定
- **真实功能/决策路径：data_unavailable（数据就绪性 open，等待作者补充或新湿实验）**；不再重复公开数据"更大组合表"检索（已多次有界检索未发现；继续搜不产生独立培养/功能 numeric）。
- **机制账路径：M2 Stage1 PASS（C206）、M1 Stage1 检查 PASS 但一步投影撤（C208）、M1 Stage2 合成诊断执行中、M3 Stage1/Stage2 诊断 PASS（C209/C213）**；这些仅是合成/受控真值证据，不称药理/真实决策/迁移/机制/新颖性。
- 不晋升代码；不改旧判定；不恢复已停止实验；不写"只能新湿实验"（mapping 可 authors 补充），但**真实功能确认必须新测量**（此前证据已表明公开资源不足）。
