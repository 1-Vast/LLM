# 独立数据与实验可识别性审查

日期：2026-10-21 启动，2026-10-22 完成，Asia/Shanghai；沿用本研究回合指定的 20261021 日志目录。角色：数据/实验设计审查者；本审查没有读取封存的原始 MT/LDH、细胞数、形态特征、图片或任何预留结局。只读既有开放身份表、schema/覆盖/相等性审计、协议、公开源代码及官方文件目录。未下载特征 payload、未运行科学性能实验、未调用模型 API。本报告不是代理共识产生的实验支持。

## 决定

**OASIS 的已认证结构子集不存在必须暂停全部真实数据工作的身份阻塞。当前最小可执行研究是开发区原始功能重复/QC 资格，继而进行真实形态相对 count、dose、chemistry 的增量信息资格。** 这个动作不会重新启动既有阴性世界模型/继承分支，也不检验“应修复细胞模型还是测量过程”的新机制。后者因无对应真实过程干预而仍不可测试。

现阶段不能把该资格实验升级为世界模型、智能体、继承或 RSI 的有效性结论。一个 PHH 五供体池只是一种混合背景；化学组是迁移任务单位，不是独立供体、时间轨迹或新细胞背景。

## 已解决与仍待解决的身份问题

优先级应服从较新的审计，而不能仅重复早期 source REPORT 的“未建分区/尚未配对”。实际状态如下。

| 项目 | 最新允许证据 | 对下一步的含义 |
|---|---|---|
| 重复物理孔 | 22,624 源行、22,464 物理孔；128 重复组、多 160 行。既有 `DUPLICATE_READ_CONSISTENCY.json` 显示四个 raw 字段全部相同、冲突为零 | 按固定 source/plate/well 键每孔只计一次；不计为额外重复，不按响应大小保留版本 |
| 化学身份 | 960 标签有源结构，119 缺失、6 冲突 | 125 标签继续隔离；不需要为运行已认证子集先猜出全部药物身份 |
| 分区 | v2 14 项完整性检查通过；662 化学组，dev/selection/reserve 标签 641/163/156、组 400/137/125；跨角色最高 Morgan Tanimoto 0.6923077 | 固定 v2；初始失败 reservation 不可用；不改 seed、阈值或角色以改善样本数 |
| 形态来源键 | raw biochem、compiled metadata、image index 三方精确配对 21,256 孔，无 compound-dose 冲突 | 证明已配对来源身份；尚不自动证明具体 CNN 文件行/特征的完整性 |
| 研究动作 | 配对 8,668/8,680 个 compound-dose；1,073 标签有八剂量、12 标签七剂量 | 缺失动作不是阴性，也不以全菜单覆盖推断可用形态覆盖 |
| dev 配对可行性 | 新增纯身份汇总：9,690 孔、5,122 动作、641 标签；4,568 动作两孔、554 单孔 | 重复一致性与跨孔交叉读出只在真实双孔单位成立；单孔可用于另行明确的预测分析 |
| dev plate controls | 身份表显示配对 dev 涉及 61 plate，每个 69 个 DMSO 物理孔，共 4,209 孔 | 有足够的控制菜单可审查；这是配对 dev plate 的控制计数，不保证所有 raw dev plate 都在此集合；是否有动态范围/异常 plate 必须由 dev raw QC 决定 |

三方配对缺失集中于上游排除的三块不同显微镜 plate，以及少量其他孔。依据身份与已知采集差异定义排除是允许的；不能根据新打开的 MT/LDH 或模型误差重新定义资格子集。双 plate 不等于已认证独立培养重复，当前应称物理孔/plate 重复。

新身份计算使用现有开放的 `IDENTITY_ROWS.json`、`PAIRED_IDENTITIES.json` 和 `RESERVATION_v2.json`；结果见 `data_auditor_sources/IDENTITY_FEASIBILITY.json`。没有新源数值参与。

## CP-CNN 的准确资产与血缘

官方资产为 [Zenodo 17067683](https://zenodo.org/records/17067683) 的 `cpcnn_raw.parquet`，**48,201,019 bytes**，MD5 `d79b1cebc8aa3999fa993ea2500fab8d`。确切 URL：

`https://zenodo.org/api/records/17067683/files/cpcnn_raw.parquet/content`

记录元数据为 2025-09-06、CC BY 4.0；API version 为 null，不能据此杜撰版本号。API 目录、来源 hash 和本次请求收据保存在 `data_auditor_sources/`。

在固定 commit `ca4872de0f1f0a4f203bee41271a6512b314a076`：

- [`1C_download_cpcnn.py`](https://github.com/broadinstitute/2024_09_09_Axiom_OASIS/blob/ca4872de0f1f0a4f203bee41271a6512b314a076/0_prepare_data/1C_download_cpcnn.py) 从 `workspace_dl/profiles/cpcnn_zenodo_7114558/{prod_25,prod_26,prod_27,prod_30}/plate_*.parquet` 取 embedding。
- [`2C_format_cpcnn.py`](https://github.com/broadinstitute/2024_09_09_Axiom_OASIS/blob/ca4872de0f1f0a4f203bee41271a6512b314a076/0_prepare_data/2C_format_cpcnn.py) 按 `Metadata_Plate/Metadata_Well` 聚合，非 Metadata 列取中位数，Metadata 取 first，最后 join compiled metadata。该脚本未做跨样本标准化或功能监督拟合。这里的 raw 是 embedding 汇总，不是原始图像。
- [`2A_format_metadata.py`](https://github.com/broadinstitute/2024_09_09_Axiom_OASIS/blob/ca4872de0f1f0a4f203bee41271a6512b314a076/0_prepare_data/2A_format_metadata.py) 会把 raw/normalized/ridge-normalized MT/LDH、药物注释和 count 都带入 Metadata，因此完整 DataFrame 不能直接作为输入矩阵。表名 raw 不保证 Metadata 不含结局。
- [`normalize.py`](https://github.com/broadinstitute/2024_09_09_Axiom_OASIS/blob/ca4872de0f1f0a4f203bee41271a6512b314a076/1_snakemake/preprocessing/normalize.py) 是另外的后续步骤：MAD 使用 plate 控制统计，spherize 选择 DMSO。未来独立实验应自行固定 dev/control-only 归一化与特征处理，不读取作者 processed profiles 来规避本地分区。

上游 [CellPainting-CNN checkpoint 7114558](https://zenodo.org/records/7114558) 是 2022-09-26 v1.0 的 EfficientNet，元数据称使用五个来源数据集的 488 treatments 加两个阴性控制的单细胞 Cell Painting 图片训练。它不能被本项目称为“已认证无监督”或“已证明预训练化学身份与预留绝无交集”。本次没有取得五个训练集的全部化学单位清单。可作为公开冻结表征开展 G0，所有对照均同样获此表征；严格 unseen-pretraining-chemistry 主张继续保留为未认证。上游逐图处理与 S3 plate 特征的全部实现链亦未穷尽审计，因此报告的是编译前后的边界，不是对生成过程的绝对保证。

**CNN 的先行放行条件**：在独立过程先核来源 hash、schema、身份键、行唯一性/重复关系、与既有三方配对键一致性。仅按已冻结的身份可用性纳入 dev。特征必须取经过 schema 审核的 embedding 列白名单；任何 `Metadata_mtt*`、`Metadata_ldh*`、临床/靶点/通路注释不能因为位于同一个文件而进入 X。Count 仅作为明确列名的强对照输入。

## 最小可执行真实数据实验

1. **G0a 开发区 raw/control 资格。** 先冻结允许的 dev 标签、物理孔、DMSO、源 hash、重复去重和 plate/control 归一化规则；独立 worker 只导出这些允许值。审查 raw MT 与 LDH 的控制稳定性、真实双孔一致性、可用动态范围、plate 与位置依赖。MT 是 RealTime-Glo MT 代谢读出，不称 ATP、死亡真值或临床安全。LDH 的 signal/background/raw 差值关系需要核验；不能把 background 列当 spike-recovery 实验。
2. **G0b 真实状态信息资格。** 只有 G0a 达标且 CNN 来源/键通过时，使用开发化学组内部交叉拟合，所有同药的剂量/重复在同一折。比较 dose、chemistry+dose、count+dose、count+chemistry+dose 与 measured CNN+count+chemistry+dose。直接模型至少包括适当正则化线性/核与非线性模型，给予相同调参预算。拟合 imputer/scaler/PCA/残差化/特征选择均限训练折；control 统计的输入与计费预先固定。
3. **评价单位与边界。** 药物/化学组是推断与重抽样单位；8 剂量、多个细胞或图像不增大独立 n。跨孔形态→功能诊断应只用两个真实孔的动作，并报告同孔结果作为另一个信息条件；同孔并发读出不产生时间预测。保留单孔/缺失覆盖，不把它们悄然丢成“可完整复现”样本。

开发区 G0 的成功是“信号可测量且真实形态在强同信息对照上有可复核的增量”，不是新机制被证实。先用重复噪声和用途定义有实际意义的 margin，再冻结后续选择/预留判据；不能看到结果后挑 endpoint、阈值或药族。若 raw 重复主要反映噪声/plate，或 count+chemistry 已解释可达信息，停止当前形态世界模型分支。若真实形态不能提供值得购买的信息，不应先训练预测形态再用别的指标挽救。

## selection/reserve 防泄漏应如实描述

Parquet 的一个 row group 可以混有多个角色。`read_table(...).filter(...)` 在过滤前可能已经物理解码非 dev 数值；同一 Python 进程事后 mask 不能声称“预留从未被读取”。建议采用单独的来源过滤进程：先读 ID 列建立允许键，然后以数值字段白名单和 dev/control 条件输出到开发资产；优化/审查进程只获得该资产。其保证是**非 dev 数值未向优化暴露**，不是对底层解码的虚假保证。

必须保留过滤代码 hash、输入/输出 schema 与角色计数、源 hash、输出 manifest；日志不能输出逐个 reserve 的值、全体 feature moments、全体归一化参数或可用于隐式筛选的异常排名。共享 DMSO 是固定实验控制信息，允许哪个 plate 的控制应预先写清，不能混为来自 reserve 药物的结局。真正严格的隐藏性最终需要外部评价或进程权限边界；现有明文目录隔离是约定与数据流限制，不是密码学或 OS 保密。

## 后续四类贡献与 RSI 是否可识别

| 主张 | 最小辨别设计 | 当前资格 |
|---|---|---|
| 世界模型贡献 | 相同化学/剂量/真实状态监督，比较直接函数、多输出模型与“预测状态→功能”；共同查询历史以固定信息，再评价决策效用 | G0 尚未完成；仅拟合 CNN 不能确证 |
| 智能体贡献 | 相同可选实验、初始信息与预算的闭环；与普通主动学习、固定查询、简单 mixture、等预算程序搜索比较 | 菜单可用于固定 44h 的离线功能查询；没有真正时序状态或过程控制 |
| 程序继承收益 | 源任务冻结程序后，在新化学组共同起点/支持/计算预算对比分别重启、检索历史、固定蒸馏和普通持续学习 | 单 PHH 背景最多开发化学迁移；参数继续训练不等于程序继承 |
| 联合收益 | world/no-world × inherited-agent/reset-or-fixed-agent 的共同历史与闭环两套对照，报告交互而非仅最终赢家 | 目前未实验 |
| RSI 策略本身 | 固定旧/新改进策略，从完全相同的模型、程序、历史与算力/查询预算出发，在未用于策略选择的任务上比较每单位成本的后继净改进，并计入学习策略前期成本 | 不是看 generation score 上升；现有一个池与化学分区不足自动完成此项 |

“区分生物模型误差与测量过程误差”的候选在 OASIS 无认证 blank/spike/流程改变动作及独立生物裁决。只用 MT/LDH/形态的相关性不能识别误差归因。这个机制应继续 NOT_TESTABLE，普通 G0 良好也不会解除该停止条件。

## NCATS 现有资格记录的处置

仅核对既有盲审计：85,503 sample/assay 行、13,506 sample、3,302 重复 sample-assay 键，字典无 plate/replicate/time，正交 follow-up 与主 assay 重叠有限且选择机制不明。总行数不能当独立任务数，也不能认证可区分观测误差的共同细胞状态。遵循本轮决定，不进一步读取该病原体相关来源的结局、功能剂量或设计/优化实验。它不作为当前虚拟细胞真实验证的替代数据。

## 收据、失败与后续动作

新代码仅在 `research/autonomous_rsi_round1/data_auditor_metadata.py` 与 `data_auditor_lineage.py`，全部输出仅在本目录。元数据/代码请求 body 合计 93,348 bytes；未请求任何 embedding、图像或功能表 body。源脚本是只读文本，未执行其下载/分析逻辑。

环境失败一次：误用 `.venv/Scripts/python.exe`，其无 `requests`，在任何请求前退出；改用用户指定 `conda run -n maestro` 成功。一次 Windows glob 形式导致 rg 路径错误，改为明确文件读取。首次宽泛文本索引产生大量截断的匹配路径/公开审计文字，随后全部改成显式允许文件；未打开 sealed 文件，也不以该检索作为数值证据。以上都未修改既有研究。新增代码没有为一次性元数据脚本制造测试框架；它的输出通过 pinned URL/hash、固定身份源及人工源码审查验证。

**下一步具体建议：立即执行有 opening receipt 的 dev-only G0a；同时可按上述来源放行条件获取一次 48.2 MB CNN，先核 schema/identity 再导出 dev。保留 selection/reserve 数值不向优化开放，直到 dev 信号、强基线、后续效用/margin/停止条件冻结。** 不需要为此下载大 bundle、重跑旧阴性分支或搭建新的世界模型/RSI 架构。
