# 第二轮深整理：职责合并与固定证据保留

2026-10-06。本轮整理针对新导入的同条件重复研究，以及相邻知识、单药研究的维护入口。原 94 项 repeat ZIP 成员、ZIP、本地冻结证据和用户报告不改写。本文与新增查询测试属于当前维护层，不是重新训练或新的生物学确认。

## 已落实的简化

没有为重复研究新建第三个 SQLite 查询器。现有 `tools/datasets/biological_knowledge.py` 增加 `repeat_features` 操作，继续使用同一个显式路径、只读连接、关闭连接和 CLI 入口。它只处理这次真实交付的 feature catalog：按精确 SIDM 查询 pathway、hotspot、dependency，保留源信息、缺行、NULL 与热点 0，拒绝含 `measurement`、`assay_condition`、`candidate_prediction` 的实验数据库及不兼容特征 schema。

工具不导入实验训练器，不重新计算分数，不读取确认结果。原 `context`、`drug`、`paths` 操作保持原合同；repeat catalog 缺少旧网络和 ChEMBL 表，不能把它传给 `drug`/`paths`。新操作的来源查询容许缺少来源表或字段，并返回明确的 `unavailable`/`incomplete`，不制造来源哈希。

特别是热点源 URL、哈希和许可并未存进 `feature_catalog.sqlite` 独立源表；行只带 release 标签。新查询明确标为来源信息不完整，真实采集收据仍在 `next_sources/mutation_acquisition.json`、`evidence_catalog_manifest.json`。不为补字段改写固定数据库。

新增 `test_repeat_features.py` 四项契约：只读和零/NULL保持；精确身份及整模态缺失；部分来源字段保留；拒绝结局数据库及不兼容 schema。与旧知识 18 项检查合并执行，**22 项通过**。真实 HT-29（SIDM00136）读取 14 个 pathway、542 个 hotspot、61 个 dependency；严格 JSON 序列化成功。查询前后数据库 SHA256 都为 `448343645f4289fb3b15ee3e4d58b4f81cee275115c0c6feea9d1e4d54060ea6`，与目录原资产清单相符。实验数据库被明确拒绝。

```powershell
$env:PYTHONPATH='src;.'
& D:/anaconda/envs/maestro/python.exe -m tools.datasets.biological_knowledge --database research/astra/repeat_signal_20261005/feature_catalog.sqlite repeat_features SIDM00136
& D:/anaconda/envs/maestro/python.exe -m pytest -o addopts= research/astra/repeat_optimization_20261006/test_repeat_features.py research/astra/knowledge_optimization_20261004/test_knowledge.py -q
```

输出默认只到标准输出，不更新原 catalog 或研究回执。无需加公共 wrapper、注册表、缓存服务或新的生产后端。父任务将新测试登记在 research scope，生产默认测试范围不扩大。

## 当前入口应该只承担各自责任

| 入口 | 维护角色 | 应停止并行维护的内容 |
|---|---|---|
| `knowledge_transfer_20261004/` | 固定三项探索及原网络/背景/补充证据 | 不刷新旧下载端点、不改冻结学习器 |
| `knowledge_optimization_20261004/` | 固定导入核验和首次查询契约的维护来源 | 其“下一步单药预训练”已由后续研究完成，应只链接结果，避免继续当现行任务 |
| `mono_pretraining_20261005/` | 已完成的 v1/v1.1 开发负结果、独立核查、E 未评估 | 不把再次收缩或重新抽样变成第二个活跃训练分支 |
| `repeat_signal_20261005/` | 94 个固定交付成员、实际重复/原始孔/训练结果 | 不运行原 `finalize_evidence` 再次追加、不重打包覆盖 ZIP |
| `repeat_optimization_20261006/` | 当前独立收据核验、科学勘误、维护测试和用户补充报告 | 不再复制研究 DB、模型源码或维护第二个读取器 |
| `tools/datasets/biological_knowledge.py` | 唯一当前 SQLite 只读检索操作入口 | 不承担模型训练、冻结、事件账本或效果判决 |

父任务负责两级 README 和日志，建议 README 只作导航与生命周期表；实际结果只在各自报告保持一个权威版本。`USER_REPORT_ZH.md` 是用户最新补充的保留副本，不应因为与 ZIP 报告仅少量字节不同就删除、覆盖或自动正规化；本审查确认它与当前根级用户报告逐字节相同。

新 successor 的验证应统一到一个 `verify_snapshot.py`：归档/冻结哈希、保存结果重建、动作开销和范围诊断可由同命令报告。科学审查者已提供固定筛选下验证上界的标量算法，应并入该现行核验入口；不要再建 `check_headroom.py`、`audit_import.py` 等相互重复的当前脚本。原包 `verify_results.py`/`finalize_evidence.py` 留作历史复现来源，不作为更新本地固定包的推荐命令。

## 实际重复与大资产清理判断

只按维护职责识别重复，不设任意文件/行数目标。本次逐字节跨最近目录比较发现两项重复：

- `knowledge_transfer_20261004/context/pathway_125_lines.csv` 与 repeat 的 `inputs/pathway_125_lines.csv`：34,223 字节。
- `knowledge_transfer_20261004/context/pinned_sources.json` 与 repeat 的 `inputs/context_sources.json`：2,225 字节。

这两项都是各自固定交付引用的输入证据，应保留原字节，不通过移动或符号链接去重。后续新研究直接读取已登记快照，而非又复制一套活动输入。知识研究的两个 SQLite 也不能删除：一个是实验实际使用的网络库，一个是后补检索库。repeat 的两个 SQLite 同样不能合并：15,126,528 字节 feature catalog 无响应标签；59,256,832 字节 experimental evidence 则含结局及全候选排名，两者隔离有实际科学作用。

检查时最近目录的主要资产如下；数值包含当时生成缓存，仅用于资产盘点，不能充当科学样本数量或压缩目标。

| 目录 | 当时总字节 | 主要大资产与处置 |
|---|---:|---|
| knowledge transfer | 180,166,073 | 网络/组装 DB、上游 TF、三组原回执：固定证据 |
| knowledge optimization | 100,776 | 小维护记录；原 14 合成检查已接入 pytest，无需再抄 |
| mono pretraining | 98,896,761 | v1/v1.1 开发 pickle 和单药标签：保存负结果的复现资料 |
| repeat signal | 86,514,371 | 两个 DB、热点源与原始孔派生表：保留源/结果分离 |

mono `results/s2_dev_records.pkl` 名称看似缓存，但当前 v1.1 freeze 引用了它，不能删；`s2_dev_records_v1_1.pkl` 和 `mono_labels.csv.gz` 仍被已完成研究/核验使用，未登记在某个 freeze 不等于已无消费者，不以名称“cache”作为删除依据。`archive_v1/` 是结果后开发修复前的源码证据，不是另一套活跃实现。

唯一明确可重建的非证据残留为 `__pycache__/*.pyc`。检查时 knowledge transfer 有 8 个、knowledge successor 2 个、repeat 4 个；均为自动生成缓存，repeat/knowledge 导入成员清单没有它们。它们不属于94/83项证据，不应纳入 Git。各导入目录已有忽略规则，仓库一般忽略也应继续生效。不需要反复删除它们来宣称结构更简单；测试会再次生成。若最终清理执行，只针对列出的已解析工作区 cache 目录，先确认没有并发测试在运行，不动日志、源收据或资产。

## 安全复现与来源边界

导入 repeat 的 README 已说明多数模型 runner 拒绝已有结果目录；`finalize_evidence` 却会更新两个数据库和 manifest，`make_manifest.py` 还会覆写归档。它们只能在独立 replay copy 的原环境使用，不能用于本地“最新同步”操作。新核验命令只读；写报告使用新的独占目标并拒绝覆盖，不自动重冻结。

DepMap 24Q4 v1 的来源许可记录为 CC BY 4.0；热点与依赖的源全文件 SHA/MD5、派生 SHA、缺模态名单仍在原收据。依赖429MB源未随小包交付，不要求为了查询5,734个已登记派生值重下载。GDSC footprint 的 GPL-3.0 文件与原源码保留；不同来源不得由一个 SQLite 或 ZIP 名称获得统一许可。

查询中的 CRISPR gene effect 是长时间基因敲除读数；热点0不是认证野生型；派生 basal 通路分数不是新培养的动态状态。实验库54,228条候选 score 是排名预测，不是54,228次独立实验或校准概率。保持这些边界比去掉几个目录更有价值。

本轮没有湿实验、模型重训、Vis开启或生产模型推广。实际减少的是独立维护的查询职责，并补上重复研究已交付数据可直接复用的只读入口。
