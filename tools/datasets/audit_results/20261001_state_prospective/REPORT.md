# 双核心状态增益：真实 STATE 输入认证与自主知识回顾性实验

本轮从 `1d8c9440070b77f43094c9f5da81d3f88a3964f4` 的干净工作区开始，
在 `codex/state-prospective-certification-20261001` 工作。
用户后续要求加入自主知识发现与明确标注的回顾性预测研究，已实际执行。
生产 `src` 未改动；旧冻结文件未重写。所有本轮原始资料、失败、源码快照和结果均在本目录。

## 结论及证据等级

| 问题 | 本轮结果 | 边界 |
| --- | --- | --- |
| 找到合格的前瞻状态增益任务吗？ | **没有** | 六项新增原始来源审查均只能支持回顾/回放；另外两条线索尚未充分取得原始证据，未当作已排除 |
| STATE 前瞻输入软件路径是否实际测试？ | **通过限定的技术认证** | 最终版 4 次成功请求、12 次真实 checkpoint 前向；同基线、查询占位替换、未来文件替换三项最大差值均为 0 |
| 新采集 RNA 能否直接接入登记 STATE？ | **尚未认证，显式拒绝** | 2,000 个有序坐标中 31 个基因身份仍未知；还缺完整新样本变换与独立盲参考池 |
| 状态是否改善预测？ | **未运行生物学比较** | 技术不变性不衡量预测误差；不能写成“状态无增益” |
| 自主检索的知识能改善回顾性预测吗？ | **本回顾性留出评估的负结果** | PublicTargetGOKernel 在冻结的回顾性划分上比剂量基线 MSE 高 4.6749%；不是 STATE 或 TxPert 的模型结果，也不是物理总体显著负效应 |
| 预测是否改变动作？ | **未运行** | 没有用不合格观测伪造动作/策略比较 |
| 动作是否改善终局效用？ | **未识别、未运行** | 缺合法前瞻状态、分配/支持、完整失败及成本证据 |
| 计入状态成本后是否有价值？ | **未知、未识别** | API 与本地计算费用均记 unknown，没有填免费/零成本 |

`未运行`、`未识别`、`技术通过`、`回顾性负结果`在本报告中含义不同。
本轮没有进行物理实验，没有将任何预测请求记作实验尝试，也没有把条码缺失补成死亡。

## 1. 环境、checkpoint 与历史复核

实际解释器为 `D:\anaconda\envs\maestro\python.exe`，Python 3.11.16。
PyTorch 2.7.0+cu126、NumPy 2.4.6、pandas 2.3.3、anndata 0.12.19、
scanpy 1.11.5、pytest 9.1.1、lightning 2.6.5，完整版本见
[environment_before.json](environment_before.json)。RTX 4060 Laptop GPU / 8 GB 可用，
但上游 STATE 加载路径此次实际运行在 **CPU**，以 forward trace 为准。

为读取固定版本的原始 Parquet 元数据，只新增 `pyarrow==21.0.0`。
[dependency_receipt.json](dependency_receipt.json) 记录安装命令和环境差分：没有升级、降级或删除其他包。
没有安装 TxPert 要求的另一套 Python/Torch 环境。

登记模型 `state_generalization_zeroshot_X_hvg` 权重实查 SHA256：
`2c9b2e74f59c2fdde73e77c3eec8a8ed26a00e5237d2b5bb3b02122475f623a3`。
权重、配置、1,138 维精确 onehot 映射、var_dims、c39 输入、特征清单与 registry
均重新哈希，见 [contract.json](certification_v2/contract.json)。
80 个实际安装的 STATE Python 源文件哈希另存于
[checkpoint_contract_extra.json](checkpoint_contract_extra.json)。
其中 `_infer.py` 仍与已引用上游固定版本逐字节一致。

**追加勘误：**历史“有序 2,000 基因”应准确表述为“有序 2,000 坐标，其中 1,969
有经检验的基因身份，31 个身份未知”。原登记文件本已明确这些 null，先前摘要过于简化。
本轮在实际 fixture 的 30 个 control 细胞上再次逐坐标对照
`log1p(X)` 与已知 `X_hvg`，最大误差 `2.3841858e-7`；原 X 行和约为 4,000。
这仅验证现有标准化资产，不认证原始新计数的完整转换方案。下载的官方
62,710 基因元数据与 var_dims 全基因名列表均不能自动恢复那 31 个 HVG 坐标。

固定版本的 Hugging Face c39 LFS 哈希与本地文件一致。
新取得的 `generalization.toml` 与本地同名文件一致，但仍不是 checkpoint 配置引用的
`generalization_zeroshot.toml`，不能认证实际训练条件/结局暴露；模型仓库请求返回 401。
本地历史 scale=0.1876982144 来自 863 个开发条件、303 个化学单位；未登记区间校准。
本轮技术测试未应用或重拟合该 scale。整个 c39 已有历史开发暴露；评估器留出不等于
checkpoint 的真实未见数据。

已重读研究计划、可识别性说明、旧采集规范、当日日志 15/16 节、证据 HTML 与 ZIP
以及 followup/bundle-review 代码。ZIP 的九个成员哈希再次通过，四个 Cycloop 来源和
历史独立重建摘要一致。此次没有重新宣称执行了包内作者测试。
Cycloop 仍是 1,200/1,200 动作回放匹配，不能据此认证连续输入相同或硬件执行；
DeepCellControl 的最终刺激仍不能视为独立 Bernoulli；Gross 的对照仍是 A1/A3/A5。

## 2. 原始证据搜索与最接近的候选

[previous_exclusions.json](previous_exclusions.json) 整理了 12 个既有本地任务族、
GSE279162/LARRY/Thunor，以及四项在线/成像候选的具体排除证据。
没有新证据的旧候选未重复下载、改名重包。

本轮执行 14 个成功的 Europe PMC 检索查询，再按命中追到原文、GEO、GitHub/GitLab
既有证据、Hugging Face、ChEMBL、UniProt 和 Zenodo。
截至知识研究完成，共 **83 次公开资料请求，70 次完整成功，13 次失败或部分下载**，
保留约 36.0 MB 返回内容。费用均为 unknown，外部模型 API 调用为 0。
搜索只覆盖返回的有限页及定向追索，不声称系统综述穷尽。
[source_review_v3/api_summary.json](source_review_v3/api_summary.json) 保存服务、URL、版本、
开始/结束、耗时、字节、SHA256、重试及失败；
[search_coverage.json](source_review_v3/search_coverage.json) 保存实际查询与命中。

| 新审查候选 | 新取得的原始证据 | 判定与决定性缺口 |
| --- | --- | --- |
| Live-seq / RAW-G9；GSE141064 | Nature 原文、固定 GitHub 代码与 1,012 行/50 字段元数据 | 同细胞活检和后续轨迹有价值，但 RNA 处理不能供已报告的 LPS 决策使用；完整随机动作/策略比较、失败成本与物理培养不明；鼠细胞也不符合当前 STATE |
| ReSisTrace / Kuramochi；GSE223003 | 原文、GEO 样本字段、固定代码 `26203470...`、样本 pre/post 路径 | 最接近 sister RNA panel；基线处理可读取时点、动作间随机化、独立培养和全失败账本缺失；处理/恢复时长不同；条码未检出不能当死亡 |
| ReSisTrace / MOLM-13；GSE306484 | 原文、全部六个 GEO 样本、固定代码 `868e786e...` | RNA/处理两半的随机分样不等于两个药物之间随机分配；无处理完成时间、完整分母/成本；六个 library 不是六个独立培养 |
| Rewind；GSE161300 | NCBI 原始 BioC 全文（Europe PMC 500 后取得） | 先固定 carbon copy，约三周后从耐药细胞得到条码，再设计探针回收对应基线细胞；基线测量受未来命运引导且当时不可读 |
| ClonMapper | NCBI BioC 原文、冻存/处理/建库方法 | 扩增克隆和八平行 flask 不认证独立亲本多动作面板；基线处理可读取/完整账本未知；不同背景用不同组合不能混成菜单 |
| NanopoReaTA 实时 RNA | eLife 原文/方法 | 1/2/5/10/24 小时是测序开始后的分析时间；RNA 取自在培养/热激之后，不是已证明的干预前决策状态 |

逐字段时间、亲本、对照、分配、QC、许可和来源定位见
[candidate_review.json](candidate_review.json)。另外两条 2026 新线索保留为尚未完成来源审查，
没有把全文失败当作数据本身的负结论。

Live-seq 得到更强的**协议时间界限**：活检到 LPS 为 0.5–1.5 h，提取液冻存等待处理；
公开 Smart-seq2 方法仅 RT 的 90 min 加 24 个 PCR 延伸各 6 min 就至少 234 min，
尚未计建库/测序/分析，超过最大 90 min 窗口。不是伪造精确运行时戳。
元数据有 24 个非空 slope，论文分析为 40 个联合采样/追踪对象中 17 个通过 QC；
两个计数原样保留，不合并成独立实验分母。所有元数据原始行见
[liveseq_metadata_rows.jsonl](source_review_v3/liveseq_metadata_rows.jsonl)。

三种设计门槛仍分别适用：sister panel、随机完整策略、随机动作日志。
本轮没有要求每一个细胞同时拥有两个潜在结局；失败在实际证据条件。
没有其他识别条件成立且可界定缺失成本/结局的候选，因此也没有任意指定效用区间。

## 3. 真实 STATE 技术认证

最小研究构造器位于 `tools/datasets/state_prospective_input.py`。
基线只读 c39 同一 `plate1` 的 30 个 control 行；其预决策合法性未知，明确作为
历史开发技术 fixture。构造两个已映射 Trametinib 查询，每个 16 行，
所有虚拟行均标 `prediction_request`。未来结局文件不属于构造器参数或数据路径。
本次两组“同基线”只检验软件对称性，不是假称已取得独立盲基线。

`certification_v1` 保留第一次成功技术结果。`certification_v2` 添加实际未来文件
读取拦截，并改进缺失 control 的错误信息后复测。每版 4 次成功请求、12 个实际前向，
另有一次故意使用不存在 checkpoint 的真实失败请求。合计 24 个成功 forward；
所有测量/实验尝试计数仍为零。

| 检查 | 最终执行结果 |
| --- | --- |
| 可见与盲组输入同基线 | 输出逐位一致；最大绝对差 0 |
| 查询表达占位由 0 改为 123 | 输出逐位一致；最大绝对差 0 |
| 独立未来文件由 0 改为 -98765 | 文件哈希改变，输出逐位一致；最大绝对差 0 |
| 未来结局进入读取路径 | Python audit hook 无访问；另一个实际打开攻击测试被 PermissionError 拒绝 |
| 特征顺序错误、未知扰动、缺 control、错误背景 | 全部显式失败 |
| 不匹配 plate 的全局 control fallback、混入观测结局行 | 全部显式失败 |
| 新原始 RNA 不完整特征身份 | 明确拒绝，不补零伪装成功 |
| checkpoint 不存在 | 非零子进程返回；valid=false、valid_experiment=false |

每次前向记录实际 batch 键、精确动作、basal 输入哈希、设备和行数；
输出数值、请求 ID 和行数验证后才记有效预测。
最终完整收据见 [certification_v2/summary.json](certification_v2/summary.json)。
预设容差为 atol=1e-6、rtol=1e-5，结果比容差更严格。audit hook 限定为 Python 文件读取，
不是对任意恶意 native 扩展的安全认证。

两版技术运行累计记录耗时约 363.74 秒，含加载和预期失败；硬件/电费 unknown。
没有对新样本做未经认证的归一化，没有状态替代模型，也没有生物学误差/动作/效用分数。

## 4. 自主知识发现与实际回顾性预测

已直接核验 [TxPert 论文](https://www.nature.com/articles/s41587-026-03113-4) 和
[公开固定仓库](https://github.com/valence-labs/TxPert/tree/08d82eea86746b044cf7531f4ec8c5f60e1cb73f)：
模型结合 basal representation 与图扰动表示，强调 batch-matched control；
PxMap/TxMap 为私有资产。公开 checkpoint 主要是 K562 基因扰动任务，不是当前 NCI-H596
药物剂量输入。本轮没有运行 TxPert checkpoint，也没有把公开 GO 辅助模型叫成 TxPert。
公开权重位置/大小和许可原文均已核验；没有为不匹配任务下载约 292 MB 权重或重建环境。

自动识别到人源 NCI-H596，核对 ACH-000628/CVCL_1571；从元数据解析药物、剂量、靶点，
从实际基因轴选择 1,969 个固定具名坐标。公开药物注释来自 Tahoe 固定版本
`2dc57900...`，不使用 GPT approval notes。ChEMBL 的 Trametinib→MEK1/2 与 UniProt
MAP2K1→ERK cascade 作独立机制交叉核验。其余药物靶点明确标为 provider annotation，
不冒称已逐条独立证实。细胞突变注释（如 PIK3CA p.E545K）只是机制假设背景，
不直接宣布细胞敏感性或最优动作。

知识已经成为**可执行数值特征**：药物多靶点向量 → 公开 GO 加权邻域 →
L2 归一化 → 与剂量交互的 kernel ridge。辅助模型名为 **PublicTargetGOKernel**。
只使用公开 GO（9,853 节点、470,783 边），不使用来自测试扰动结局的图。
README/许可证与出处见 [knowledge_evidence.json](knowledge_evidence.json)；
TxPert 图资产适用其 Recursion 非商业 EULA，不能宣称无限制商业使用。

**评估单位与冻结。** 536 个条件/plate 组、160 个药物名、153 个去盐化学身份、
14 个 assay plate；每个预测目标为等权孔平均 log1p RNA 减同 plate control 均值。
五折整 plate 留出，并从训练集中清除测试化学身份在其他 plate 的全部记录。
不能认证 14 个 plate 为独立培养，因此不报告物理层级 CI。
知识库、算法、划分、α=1、种子42和端点在本轮读取 response matrix 前冻结，
但 **c39 历史上已被探索**，这里不是新确认试验或 STATE checkpoint holdout。

没有真实可见状态因子。此次是 A/C 方向的知识回顾性检验：所有模型都不接收
逐问题状态，输出对照中心化的扰动差值；每折只从训练 plate 保存盲参考。
测试 plate controls 只用于定义观测差值，不能进入特征、拟合或参考池。
B、D 两组没有运行；不会把处理后 control 改名为合法前瞻状态。

| 辅助预测器 | 化学身份等权 MSE | MAE | Pearson Δ |
| --- | ---: | ---: | ---: |
| 剂量基线 | 0.00955703 | 0.05413560 | 0.02448 |
| 公开靶点 | 0.00996543 | 0.05538362 | 0.02552 |
| 公开靶点＋GO | 0.01000381 | 0.05551736 | 0.02564 |
| 置乱的靶点＋GO | 0.01019088 | 0.05613207 | 0.02125 |
| 预测无变化 | **0.00848989** | **0.04762538** | 未定义 |

主比较 GO−剂量 MSE 差为 **+0.00044678（误差增加 4.6749%）**。
153 个化学身份中 66 个改善、87 个变差；按 plate 描述性聚合，0/14 改善。
相对 no-change，GO 模型误差更高。Pearson 的微小上升不能替代主误差指标，
低 pooled calibration slope（GO≈0.05435）也不支持校准良好。
该结果限制于此特征化、α、数据与回顾性划分，不能推广为知识、TxPert或STATE均无用。

743 个原有条件/plate 因公开图没有精确靶点覆盖被排除，另有 8 个不足5个已存细胞、
6 个无精确元数据药物名、3 个缺合法结构。全部排除行及原始 ID 保留。
它们不是试验失败分母；本研究也没有估计部署成功率。

保留了一个必要修复：v1 把置乱范围设为全部 379 个药物元数据行，可能引入无图特征
的药物；v2 仅在 160 个已覆盖药物中置乱，保持特征集合。所有主比较预测逐位不变，
见 [knowledge_control_correction.json](knowledge_control_correction.json)。没有改变队列、
超参数、主指标或按测试结局选模型。每组每折 1 次评分拟合 + 1 次相同预算泄漏审计重拟合；
20 项测试结局投毒检查全部通过。精确结果、预测和观测分离字段、freeze 及运行收据见
[knowledge_run_v2/summary.json](knowledge_run_v2/summary.json)。

## 5. 剩余缺口、最小采集与验收

可直接执行的五表模板、结构验证器命令、五 aliquot 最小方案、等待漂移、所有成本和
pilot 验收条件详见 [collection/README.md](collection/README.md)。
当前最少不可替代的新信息为：

1. RNA 处理完成/可读取/决策/随机分配/执行/终点的原始事件链。
2. 同亲本 sister 与独立培养、共享对照的映射，及全部入组/取消/失败账本。
3. 状态采集、处理、等待、动作、终点和拒答的实际耗时/成本。
4. STATE 全有序基因轴与新样本转换依据、独立开发盲参考池、实际训练暴露。

API 可以补知识与接口，不能生成这些历史事实或替代物理实验。
现已实现对时间倒置、同亲本关联、菜单、对照、失败分母、跨划分依赖、非有限终点、
虚拟行混入观测的校验。结构校验通过仍不自动宣称可识别。
确认功效所需培养级成对差方差、最小有意义净效应、失败/拒答/成本/漂移分布和
共享对照相关性均列明；没有据当前数据编造确认样本量。

## 6. 失败、验证与复现

HTTP 500、401、TLS EOF 和两份截断在 8 MiB 的 GEO 下载均保存原收据。
ClonMapper/Rewind 通过 BioC 恢复；GEO 改取 series 自身及单样本元数据；缺失 GSM 重试恢复。
bs4 和 Parquet 读取失败分别用标准库 HTMLParser、仅安装固定 pyarrow 解决。
source_review_v2 错把 UniProt TSV 搜索当 JSON，保留部分结果后限定 Europe PMC URL，
`source_review_v3` 重建成功。所有模型预期失败和置乱修复也均保留。

最终在 maestro 统一执行 **162 项相关测试，全部通过，零失败、零跳过**；结果
见 `final_verification.xml`、`final_pytest_stdout.txt` 和 `final_verification.json`。
对最终代码做语法检查、源码差异审查、历史文件哈希核验；没有写入生产 src。
旧证据及本轮冻结的独立核验见 [final_integrity.json](final_integrity.json)，
执行失败与修复定位见 [execution_failures.json](execution_failures.json)。
最终审查发现三条 Hugging Face 重定向回执携带临时 CDN 签名查询参数，
已从原回执及两份派生摘要中移除；公开源 URL、原始下载字节、模型冻结与输出均保留。
[receipt_url_redactions.json](receipt_url_redactions.json) 保存三份 JSON 的修改前后哈希。
旧清单不重写，最终完整性检查分别报告逐字节一致项和这项有记录的回执删改。
下载器已增加去除重定向 query/fragment 的最小修复及回归测试。
本轮第三方原文与大体积矩阵仍保留在本地；目录内 `.gitignore` 仅避免默认加入 Git，
不删除材料。下载计划、来源收据、代码与结果摘要可审查；交付清单同时覆盖本地文件。

```powershell
# 每次使用新的输出目录；不覆盖本报告冻结材料。
& 'D:\anaconda\envs\maestro\python.exe' -m tools.datasets.state_prospective_certify --root D:\MAESTRO --out outputs/state_prospective_reproduction
& 'D:\anaconda\envs\maestro\python.exe' -m tools.datasets.state_prospective_review --raw tools/datasets/audit_results/20261001_state_prospective --out outputs/state_sources_reproduction
& 'D:\anaconda\envs\maestro\python.exe' -m tools.datasets.state_knowledge_retrospective --root D:\MAESTRO --sources tools/datasets/audit_results/20261001_state_prospective/knowledge_sources --out outputs/state_knowledge_reproduction
& 'D:\anaconda\envs\maestro\python.exe' -m tools.datasets.state_panel_contract --templates outputs/state_collection_templates
& 'D:\anaconda\envs\maestro\python.exe' -m pytest -o addopts= -q tests/test_state_prospective_input.py tests/test_state_knowledge_retrospective.py tests/test_state_evidence_followup.py tests/test_state_search_build.py tests/test_state_identifiability.py tests/test_state_public_review.py tests/test_state_adapter.py tests/test_state_runner_paths.py tests/test_condition_response_modes.py tests/test_input_basis_identity.py tests/test_repository_shape.py
& 'D:\anaconda\envs\maestro\python.exe' tools/datasets/audit_results/20261001_state_prospective/verify_integrity.py --output outputs/state_integrity_reproduction.json
```

各 `*_plan.json` 可用既有 `state_search_acquire.py --plan <plan> --out <新目录>` 重取；
外部版本改变或请求失败不得冒充原始字节。通过 frozen receipts 离线重建不再调用 API。
