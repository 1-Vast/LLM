
## 18. STATE response research: raw reconstruction, state sensitivity and retrospective prediction

本轮从实际 HEAD `1d8c9440070b77f43094c9f5da81d3f88a3964f4` 继续，保留已有未提交修改；未发现磁盘 AGENTS.md，采用用户提供的 Karpathy 约束。先记录 A/B/C/D 假设与可验证条件，再独立推进输入恢复、真实状态敏感性、回顾性任务及知识负结果诊断。

[本轮完整报告](../../tools/datasets/audit_results/20261001_state_response/REPORT.md) 和 [最少新增采集事件](../../tools/datasets/audit_results/20261001_state_response/collection_addendum.md) 位于新目录 `20261001_state_response`。所有新原件、运行、失败、冻结和收据均保存在新目录；上一轮冻结输出未改写。

### 18.1 原始 RNA 接入取得部分技术结果，完整认证仍未通过

官方模型的正确名称为 `arcinstitute/ST-HVG-Tahoe`。本轮取得固定 revision 的实际 `generalization.toml`，更正上一轮旧 `ST-Tahoe` 名称获取失败不能代表正确官方资产不可得。实际训练暴露仍 unknown，配置文件名/执行来源尚未完全对应，不能把 zeroshot 命名或评估器留出视为真实未见。

原 2,000 轴中 31 个未知坐标：25 个全零，各有 26,097 个全零基因数值匹配；另 6 个各仅一个非零细胞，仍有 2–5 个候选。官方代码、notebook、issues、PR 和另一个 HVG checkpoint 没有提供所需权威子轴。没有猜测、补零或删除坐标。

另取官方 `st-x-replogle-full/k562_0.99@48ad5f70215ab4c58caa5a68e77d837601d29d35`，权重 SHA256 `e616f13fc127d0c46ebfebfe21b2b1f12e7e1e63d65ed09230b41c5f96f6e15b`，有完整 6,546 维有序轴。通过固定源 HTTP Range、原始条码及背景关联，取得 32 条真实 HepG2 raw UMI 与 processed 记录。全 9,624 存储基因 CP10,000→log1p→固定轴的最大重建误差 4.7684e-7，通过预定输入容差；独立重新获取的数组和轴完全一致。重复 HSPA14 符号由不同 Ensembl ID 明确映射，不合并。

真实加载经历两次兼容失败：现代 transformers 对 hidden328/12 的隐含整除检查，与旧 checkpoint 显式 head_dim64 不一致；仅替换方法还遗留缓存 validator。核验 8 层实际投影形状后，用只接受该几何结构的进程内适配修复，保留 strict load，不改权重或环境。最终 2 个真实请求、6 次 forward 成功。

但重建/官方加工输入产生的预测最大差 2.2650e-6，预定 `atol=rtol=1e-6` 输出等价检查失败。dtype/运算顺序排查未消除差异，未放宽容差。v3 summary 中泛化过宽的 `technical_reconstruction: passed` 通过单独勘误纠正，原文件及正确的 `paired_output_tolerance_pass:false` 保留。原始导出配方/基因全集处理仍不全，转换器默认拒绝通用外部新 RNA；只能显式研究重建。输入部分成功不等于前瞻认证完成。

### 18.2 真实 STATE 响应状态，但选择变化主要涉及拒答

原登记 Tahoe 权重重新核验 SHA256 `2c9b2e74f59c2fdde73e77c3eec8a8ed26a00e5237d2b5bb3b02122475f623a3`。从真实 NCI-H596 控制中按元数据选 plate1/10/11，每池 30 细胞，固定三档 Trametinib 剂量、每动作 16 查询、种子 17/42/103，EGR1 预测均值最小化、前两名差 ≤1e-6 拒答。9 请求/36 forward 成功。它们是历史终点控制池，非认证决策前状态或独立培养。

池间配对 RMS 0.11723，同池种子 RMS 0.10262，比值 1.1423。9 个池间配对中 7 个选择器输出变化，但只有 **1 个具体动作切换，6 个涉及拒答**；同池跨种子也有 4/9 变化。三个池的种子平均都选 5 µM，没有稳定的状态特异排名优势。同背景整池置换也已计算。预测误差、动作正确性和物理效用均未在这项技术测试中测量，不能把敏感性称为预测改善。

### 18.3 ReSisTrace 已实际完成限定回顾性状态预测

新增 8 份原始 UMI 和 8 份 metadata，固定原始分析代码，构建全部已沉积 baseline group 的查询。pre-only `sisters` 构造输入；`prer_r_group` 只在之后关联已测后代 RNA，`drugSens` 不作输入或筛选。不存在后代记录不等于死亡。基线 aliquot 与 sister 后代是破坏性采样关系，不写为同一细胞轨迹。

独立命名 **RidgeRNA**（非 STATE/TxPert）以 rep1 训练、rep2 作探索性测试；256 基因仅由 rep1 pre RNA 方差选出，α10 固定，盲参考取 rep1 对应背景的 pre 基线均值，可见/盲模型族和预算相同。同 action/replicate 内预先置乱；样本 ID、源行、文件 SHA、变换、缺失和预测/观测关联保留。

测试 Carboplatin 214/4,432 组有匹配后代（4.83%），growth control 211/1,870（11.28%）；两背景合计 425 个评分单元。两背景等权 MSE：可见 0.466879、盲参考/上下文均值 0.261722、置乱 0.637695、无变化 0.520990。**状态可见比盲参考高约 78.39%，为本辅助模型的限定预测负结果。** 优于置乱不代表优于强基线。

这是条件于已沉积、可精确关联后代的 RNA 预测；覆盖率分母不是全部入组尝试。replicate 物理培养独立性和未检出机制未知，不报告物理 CI、不声称存活/死亡/因果药效。前瞻可读取时点缺失不再阻止这项预测研究，但仍阻止当时 RNA 决策结论。原 STATE 生物学状态误差比较仍未运行。

### 18.4 先诊断知识负结果，再做嵌套开发收缩

保存强基线新文献，复核已有 TxPert 公开实现/匹配控制边界；未运行 TxPert 或新增大图。当前 PublicTargetGOKernel 无逐问题状态、方向/效力/占有率语义。170 对同药同剂量跨 plate 响应 cosine 中位数 0.02195；10,186 对同 plate/剂量 GO 与响应相似的 Spearman 0.02787；536 个外折记录有 35 个无同剂量正 GO 邻居。预测平方能量远高于有效对齐项，解释无变化为何占优。

唯一改进为内层留出选一个 [0,1] 收缩系数，仍按 whole plate 外折并内外 purge 同化学身份。首次三个内折无支持而失败，保留冻结；元数据支持核验后改成 leave-one-plate-out，两个模型相同预算共 94 次拟合。旧结局已查看，所有新结果明确为嵌套**开发验证**。

MSE：收缩剂量 0.00848447879、收缩 GO 0.00848443997、无变化 0.00848988964；GO 对剂量差仅 3.88e-8，且 MAE 仍劣于无变化。没有确认知识增益，也不归为 STATE 结果。旧约 4.67% 负结果保持历史。

### 18.5 环境、验证和剩余证据

实际使用 `D:\anaconda\envs\maestro\python.exe`，Python 3.11.16、torch2.7.0+cu126、transformers5.17.0。本轮无依赖安装/升级，生产 src 未改。新增研究代码在 tools/datasets；14 个必要边界测试连同此前相关测试共 **176 passed，0 failure/error/skip**。命令、耗时、源码哈希、XML、stdout 在新报告链接中；测试通过不覆盖替代模型已失败的输出容差。

公共请求及 Range 分块均留原件/失败/时间/大小/SHA；费用 unknown，未调用外部模型推理 API，未联系作者或购买服务。源许可逐类记录，公开可访问不等于任意再分发。HTTP200 的 BioC 错误体没有被当成成功全文证据。历史 356 个文件的 hash/日志前缀及各冻结 manifest 经最终核验；根 README 只加导航。

尚无前瞻动作比较或部署净价值结论。最少缺口是完整输入导出契约与配对精度认证、独立开发盲参考培养、真实可读取→决策→随机分配→执行事件、共同终点、全部取消/失败/QC/成本及独立培养映射。新采集补充列出验收及功效所需参数。成本未知不阻止限定预测，但不能由 API 或任意数值界限补成部署价值。
