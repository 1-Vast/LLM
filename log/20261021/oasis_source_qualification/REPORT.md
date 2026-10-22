# OASIS 盲schema与动作覆盖资格，2026-10-21

**结论：功能菜单的基本覆盖已确认；精确“1085药×8剂量×2独立重复”以及完整形态配对尚未认证。允许继续身份/QC协议准备，不启动模型拟合。** 当前只有一个五供体PHH混池，不能支持未见供体/背景或RSI确认。本轮是单独肝毒性任务资格，不修改任何既有负结果。

## 已建立的结构证据

按预先冻结协议下载68个公开biochem Parquet，**8,257,426 bytes**，全部保存在`sealed_source/`，SHA256/原始URL/ETag/日期见`SOURCE_MANIFEST.json`。raw S3许可由官方Cell Painting Gallery README/LICENSE确认为CC0 1.0；代码版本、Zenodo不同许可及收据见`LICENCE_RECORD.md`。

独立Python进程只输出schema、标识、缺失和覆盖，没有输出或优化任何MTT/LDH值、分布、相关性或候选药。它读取到22,624条源记录，其中：

| 资格项 | 盲审计结果 |
|---|---|
| 研究药身份 | `library=oasis`且非DMSO：17,568行；1085个药物标签；与全部非DMSO记录完全一致 |
| 浓度覆盖 | 每个标签8个浓度，共8680个compound-dose动作；所有标识和剂量非缺失 |
| 每动作观测 | 8608动作2条、48动作4条、16动作6条、8动作8条；因此不是未经清理的严格8×2 |
| 不同plate | 8672动作2个plate、7动作3个plate、1动作4个plate；所有动作至少两个plate标识 |
| 重复键 | 160条重复`source/plate/well`；无字节完全相同的源文件，不能直接认定重复读板或删行 |
| 参考plate | 640行，均无非DMSO研究药；compound plate含全部17,568研究药记录 |
| 显式重复ID | 无replicate/replicate_id列；不把plate计数直接认证为独立培养重复 |
| OASIS_ID | 15,616行非缺失；其余需化学身份表补齐，不把药名字符串当已认证独立化合物 |
| 原始功能列 | `mtt_lumi`、`ldh_abs_signal`、`ldh_abs_background`、`ldh_abs`，null/NaN缺失均0 |
| 派生功能列 | 除`ldh_ridge_norm`有29缺失外，所列归一化列缺失0；本轮没有用其数值 |

这证明命名动作有真实公开功能字段及不少于两个plate记录，**不证明测量信号、动态范围、生物QC或两次独立实验合格**。药物标签数相符不替代结构/盐型/别名去重。全部源记录保留，无按功能或“凑1085”筛选。

## CellPainting来源配对

完整profile目录listing为398个对象，未截断。以`batch/plate`键匹配，68个biochem来源中**67个有原始plate.csv.gz profile对象**；缺少`prod_25/plate_41002698`。上游准备代码也将此plate与另两个不同显微镜plate列为排除项；这里仅记录来源，不据此自动删除功能行。

没有读取任何CellPainting特征body、图片或profile内部well字段。因此当前是**plate目录来源匹配**，不是已完成compound-dose-well精确配对。匹配对象URL/大小/日期/ETag见`COVERAGE_FINAL.json`；下一块必须仅提取其ID字段或相应纯well清单认证配对，不能以目录存在替代。

## 继续条件与停止边界

1. 在不读取功能值的前提下解释160个重复键及72个多于两条记录的动作；认证实际重复单位、化合物结构/别名/盐型、OASIS_ID缺失与plate/well唯一性。不得按功能值选择保留版本。
2. 认证67个形态plate的well键、药物和剂量，说明缺失plate对菜单的影响；不从完整功能菜单推定形态菜单完整。
3. 另立生物QC及控制归一化协议。未来优先用raw读出与协议指定control；任何数据驱动归一化参数只在开发部分拟合。**published mtt_ridge_norm/ldh_ridge_norm可能使用全体响应，未经血缘审计不能进入独立预留。** 缺失0不等于生物QC通过。
4. 下一次正式任务先建化学组独立预留与开发分区，再开放允许的开发数值；当前**尚未形成独立化学组预留**，只保持未数值优化状态。固定compound/dose菜单后才能定义安全剂量误差、查询成本及直接/世界模型/主动学习对照。
5. 目前不评价跨供体/背景、支持药跨背景校正、继承或RSI，不输出实验候选药。

## 协议修正、隔离与失败

`PROTOCOL.md`先于下载冻结，`PRE_DOWNLOAD_FREEZE.json`原始字节保留。主代理在首次盲审计前发现NaN缺失与control认证问题；追加`AUDIT_AMENDMENT_01.md`，修前/修后hash记入`PRE_AUDIT_FREEZE.json`，未发生科学值曝光或优化。修前blind hash `767fa81b562da2c8c7c22c98ee169846631295bbd467cd5df6a1ad85675f5744`，修后 `e8431b4c0b32a81eb3bf39208e4637cedf4b7355b1ecded08ae6330f14e29334`。

隔离来自**独立进程和字段白名单的数据流约束**，不是OS沙箱、加密或不可访问vault。代理只读了允许输出的schema/标识汇总；raw文件保持明文日志资产，未来仍需外部评价访问合同。

计量失败：获取profile目录时与功能下载并行写NETWORK.json，后写覆盖了一条目录请求记录。精确可证功能payload为8,257,426 bytes，最终HTTP ledger为8,314,214 bytes；另有完整398对象目录响应未保住精确字节数。按该固定结构目录响应预留1,000,000 bytes，source body保守合计不超过9,314,214 bytes；许可web检索工具未提供网络字节测量，不声称整轮精确网络量。没有因此重取目录或扩大下载。另一次冻结hash查询因Windows路径分隔符KeyError失败，修正键后成功；不涉及数据内容。

## 复现与资源

代码统一在`research/oasis_source_qualification_20261021/`：先`source_list.py`元数据清单，再`acquire_sealed.py`；来源文件下载前拒绝已有路径覆盖。`blind_audit.py`独立进程生成盲结果，`coverage_finalize.py`只读允许的ID结果和对象目录进行汇总。profile目录通过同一`source_list.listing('cpg0037-oasis/axiom/workspace/profiles/')`函数获取，保存`PROFILE_SOURCE_CATALOGUE.json`；不得与下载并行运行，以免重现ledger故障。

```powershell
python research/oasis_source_qualification_20261021/blind_audit.py
python research/oasis_source_qualification_20261021/coverage_finalize.py
```

源获取/盲审计于14:57:11 UTC前完成，距14:48:45约8分26秒；此后只完成文档和有限核验，文档收尾超过10分钟边界，明确记为时间偏差。无拟合、无外部模型API、无GPU，种子不适用。没有下载864.8MB bundle、图片或CellPainting特征。原始文件hash逐文件验证后才进入盲审计；`verify.py`再次只核hash/输出字段白名单/布尔缺失输出/冻结修正链。未来运行相同盲脚本不等于新的独立生物证据。
