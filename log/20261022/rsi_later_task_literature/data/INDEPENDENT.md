# 独立数据条件审查：细胞世界模型、研究程序继承与后续任务

2026-10-22。立场：先问数据是否能证伪所称机制。独立阅读六个一手工作族的作者论文、仓库或资产说明；未读任何本轮 peer 新稿。末段收到 skeptic 的交叉提问，留待本稿保存后答复；未据此重写来源结论。未触及 AZ、reserve、真实新数据集表达/HDF5 内容，未拟合。HTTP 原始 body 和 status/url/SHA256/UTC 保存在本目录成对文件中；以下是可取得资产的审查，并非已下载或验证生物学数值。

**结论：这六个来源提供了真实可取得的静态扰动响应、少量跨时间群体快照、以及程序修订环境；本审查没有核到同时具备“可持续选择的细胞干预—独立功能结果—后续任务—学习改进策略”的公开轨迹。** 可以准备有明确边界的后续任务控制器实验；尚不能据此启动或宣称完整药物发现 RSI 世界模型机制。公开近邻已覆盖诊断路由、局部模型修订、保护任务合同、历史记录、等预算比较；这些模块本身的新颖性不足。

## 六个来源及真实资产

| 一手工作与可核证据 | 真实资产、干预及数据成本 | 时间、功能和后续任务边界 |
|---|---|---|
| **State，2025**：[作者仓库](https://github.com/ArcInstitute/state)，[论文 DOI 页面](https://www.biorxiv.org/content/10.1101/2025.06.26.661135v2)。`state_readme.body`；作者页面标注 2025-06-23。 | 可运行 ST 训练/推理、SE 表征代码，训练配置明确支持 held-out cell type 与 few-shot perturbation；例子使用 Replogle-Nadig 和 Tahoe。仓库不是新的功能反馈数据集。完整训练/GPU 成本不能从 README 的 CLI 示例推出。代码/权重许可也有非商业条件。 | 预测干预后表达分布是有效任务；“transition”命名不证明同一细胞的真实连续轨迹、动作可达性或策略学习。提供强 perturbation-model 基线与冻结 cell-context split 接口；没有公开证据表明改进策略在后来任务上变得更有效。 |
| **CellFlow，2025**：[作者仓库](https://github.com/theislab/CellFlow)，论文 10.1101/2025.04.11.648220；`cellflow_dataset_code.body` 与作者 combo notebook。 | 作者加载器指向 [theislab/cellflow-datasets](https://huggingface.co/datasets/theislab/cellflow-datasets)：`ineurons.h5ad` **7,235,766,706 B**，`pbmc_parse.h5ad` **13,101,592,422 B**，`zesta.h5ad` **6,243,134,744 B**，均由 HF 资产列表核到，未下载。PBMC 为 **12 donors × 90 cytokines**；zesta 为 **5 time points、至多23 genetic perturbations**。另有通过 pertpy 读取的 A549 combinatorial drug scRNA 示例，作者说明该示例剂量恒定。 | zesta 是本组六来源中最明确的多时间干预资产，但输出是破坏性群体 scRNA 快照；不等于同细胞轨迹或可反复 reset 的湿细胞过程。PBMC 可建立 donor 后续任务；drug combo 示例仍是固定菜单的表达终点，无 viability/疗效奖励。物理 donor/plate/replicate 成本需进一步核数据 provenance，不能把每个单细胞当一个独立购买。flow matching 的生成积分时间不能冒充生物时间。 |
| **Tahoe-100M，2025**：[作者数据卡](https://huggingface.co/datasets/tahoebio/Tahoe-100M)，论文 10.1101/2025.02.20.639398。`tahoe_readme.body`、HF metadata 列表与 sample schema。 | **50 cancer cell lines、1,100 small molecules**；发布 split 实为 95,624,334 cells，压缩下载 **337,644,770,670 B**，逻辑数据 **1,693,653,078,843 B**。可 streaming，或先用 `metadata/pseudobulk_differential_expression/train-*`。`sample_metadata.parquet` 仅 **65,636 B**，**1,344 sample rows**，字段为 sample、plate、QC means、drug、drugname_drugconc；plate 为1–14，DMSO_TF 要按 plate 匹配。 | 数据卡明确为混合细胞 spheroid 的处理样本；sample 区分 replicate，drugname_drugconc 提供浓度。此公开 sample schema **没有 time、viability 或独立功能终点**。cell number、mitochondrial fraction 是捕获/QC或群体组成信息，不能直接当校准存活率。可测试 held-out drug/context 表达预测和静态主动揭示，但不能据此识别多步干预动力学。相同 treatment sample 的多 cell-line 输出在同一混合实验中，不能伪装成50次独立 wet-lab 反馈或廉价重置。 |
| **Virtual Cell Challenge，2025/2026**：[作者 Atlas 目录](https://github.com/ArcInstitute/arc-virtual-cell-atlas/tree/main/virtual-cell-challenge)、[主办方网站](https://virtualcellchallenge.org/)。`vcc_atlas_readme.body`、GCS listing、当前 home 页面。 | 2025 为 **H1 hESC、约300,000 cells、300 target genes**。匿名 GCS listing 实核：`virtual-cell-challenge/2025/train/adata_Training.h5ad` **15,482,497,461 B**；validation **6,928,967,541 B**；test **11,950,739,168 B**，并有 pert_counts CSV 和 gene_names.csv；仅列目录未开数值。指标 DES/PDS/MAE，仍为表达。 | 2025 的 train/validation/test 文件不是自然发生的连续行动历史，且单 cell line 不提供跨细胞系任务独立性。2026 首页确实宣布 **six cell lines、新实验、只给 non-targeting controls、不训练任何该新数据**，有潜在真正 later-context 外部评测价值；但 `/datasets` 虽 HTTP200，页面 payload 是 **404 not found**，本轮未核到2026可下载资产，不能写“已可用”。也未见允许在线逐轮获取 functional reward 的合同。 |
| **CellScientist，2026**：[arXiv:2605.07335v1](https://arxiv.org/html/2605.07335v1)、[作者仓库](https://github.com/limengran98/CellScientist)、[固定数据 manifest](https://github.com/limengran98/CellScientist/blob/main/data/release_manifest.json)。论文 v1 标题为 Dual-Space Hierarchical Orchestration，当前 README 标题改为 From Execution Feedback to Auditable Model-Revision Trajectories，二者版本不能混同。 | 作者 HF `Boom5426/CellScientist` revision **4171f94a78695243f69a8e209a9006383d7c1a94**。四个 BBBC036/047 plate/smiles 文件分别 **94,140,923 / 114,288,824 / 341,482,876 / 424,864,595 B**，合计约0.975GB；两 CPG0016 文件 **4,755,296,459 / 5,905,213,484 B**。schema `combined/{morphology_pre,morphology_post,dose,smiles,plate_id,split_id}`。当前公开控制器 **768候选、10 evaluated candidates、5 seeds**，fold1–3 fit、fold4 group-disjoint feedback/selection、fold5 test。 | 这是最近的程序修订先例：history、保护任务语义、诊断驱动局部修订、候选等预算已经存在。`morphology_pre` 是 **reference morphology**，没有证据是同一活细胞的纵向前后观测。036/047/CPG 都是 U2OS，跨文件不自动等于跨 cell-line 独立任务，plate/smiles split 需全局查重。形态终点是 phenotype proxy；schema 没有独立 efficacy/viability。论文报告跨 benchmark 的流程适用性，不等于“从早期任务学到的改进策略提高后续改进效率”的因果试验。 |
| **Biomni / Biomni-R0，2025**：[作者仓库](https://github.com/snap-stanford/Biomni)，原论文 10.1101/2025.05.30.656746，[R0 作者 model card](https://huggingface.co/biomni/Biomni-R0-32B-Preview)。 | A1 的 biomedical tools/datalake 环境（README 约 **11GB**）；Eval1 是 **433 instances、10类任务**。R0 model card：基座 **Qwen3-32B**、端到端 RL、公开权重，推理建议 **2×80GB GPU 或4×40GB**。README 曾写 Qwen-32B，具体 base 以该 card 为准。未下载权重或执行 agent。 | 原论文 abstract 是通用流程、协议与可检验假设生成；没有可取得的同细胞连续功能反馈轨迹。R0 card 能证实作者发布“由 agent interaction RL 训练的 agent”及权重，不能单凭 card 验证训练集、RL 预算、跨 later-task 的反馈隔离。链接的 technical report 实际 **404**，故不采信其未核实的 SOTA/改进速率细节。学习一个 agent policy 仍不自动是学习改进策略的 RSI。 |

六个“工作族”分别计为六个实质来源；相关论文/仓库/资产 manifest 用来交叉核证同一工作，不另扩文献清单。下载体积是字节层面真实数据成本，不是计算或湿实验金钱预算。未取得物理成本来源时明确不填假数。

## 数据可以支持的最小实验与不支持的主张

**最小可检验机会A：跨后续任务的更新选择器。** 若只验证研究程序改进，可用 CellScientist 已发布的轻量 BBBC 文件，在全局 plate/SMILES/scaffold 去重后建立前期训练任务、meta-validation 与封存 later tasks；训练期真实执行产生 `诊断、可选改动、预算、训练/选择结果` 轨迹，学习一个小的更新选择器。此时 CellScientist 的 fixed diagnostic controller、同历史 LLM、random/Bayesian/equal-menu search、warm-start、普通重训必须是同候选空间/评测次数/计算记账的直接比较者。仅有历史检索或 best-so-far 保留不足以证明新机制。应用是形态预测程序改进，尚不是药效发现。

必要证伪：对完全未用于训练改进策略的任务，固定同一起点程序与可见数据，只替换旧/新改进策略；比较后续几次真实改进的误差或任务效用随**实际预算**的曲线，而不只比较已有模型分数。还应做“继承初始模型但冻结策略”与“策略已更新但初始模型重置”的交叉，以免把好的起始权重误作更好的改进方法。若无等预算未来曲线优势，停止 RSI 扩展；若精确匹配有限搜索即可复现，则新颖性/必要性主张不成立。这里仅提出应注册的下一步，不执行搜索或预设成功阈值。

**最小可检验机会B：干预模型在独立 donor 的适配。** CellFlow 的12 donor ×90 cytokine 资产可在 metadata/provenance 合格后按 donor 分层，构造严格 later-donor 任务，按整 intervention group 计 logical disclosure，而非按单细胞。状态生成模型与强 direct/pseudobulk/conditional-mean 预测器同信息比较，普通重训/持续学习/主动学习同预算；模型对选择下一 cytokine 是否有增益与预测质量分开验证。其真实结果仍是 scRNA 分布，不应把选 marker program 最大的 cytokine 当已验证的功能治疗策略。12 donors 的任务级样本数不大，不能用数百万 cells 伪造 improver 统计功效。

**时间模型的有限机会：zesta。** 5实测时间点允许检验条件群体分布随发育时间的外推；必须区别真实 `timepoint` 与生成 solver 的积分时间，且无配对 lineage 时不能用生成路径证明单细胞可达轨迹或多次药物干预组合律。其生物问题是胚胎遗传扰动，和药物功能发现有显著距离。

这三个机会都不满足完整药物发现功能反馈条件。继续前至少要核到同一 perturbation/context/dose/assay 的可对齐功能终点（如独立 viability、分泌、分化成功率或 target-relevant assay），真实实验分组/复制/成本、可获得动作菜单，以及后续任务封存边界；若只能取得表达/形态，就限定为代理终点方法学，或暂停该应用。不能把 Tahoe 捕获细胞数、VCC DES、Cell Painting PCC 称为药效奖励。

## 方法必要性与新颖性裁决

1. **世界模型贡献必须单独成立。** State/CellFlow 可作强条件分布基线；若同信息直接预测或简单混合达到同样功能/选择效用，额外 rollout、latent dynamics 或 agent 模块没有必要。静态终点不迫使采用动态世界模型。
2. **程序改进与学习如何改进要区分。** CellScientist 已经在固定任务内使用 execution feedback 修订模型；Biomni-R0 已有 agent policy RL 的作者发布。新工作至少需要后来任务中对“更新后的改进策略”的干预式比较，不能仅以日志越来越长、选中更好的程序或 RL 更新过权重命名 RSI。
3. **继承是待验证收益，不是存盘事实。** 同一污染源的别名数据/重叠化合物不构成独立 later task；必须冻结 raw-history、summary/model、策略参数等允许继承内容并分别消融。继承收益也不能替代世界模型和 agent 各自的直接对照。
4. **简洁性优先。** 当前最可信新增问题是一项跨任务更新选择机制和其清晰反事实评测，而非再叠多个 agents、memory、flow model 与自我改写。只有当任务数据要求持续状态和多步动作，才考虑更复杂动力学。六来源审查本身没有证明这种必要性。

本稿建议：允许开展未来资格验证和独立评审；**不因这些文献而直接升级当前普通 pilot 为世界模型/agent/继承/RSI 成功，不启动新的大规模训练。** 2026 VCC 的实际发布可作为后续外部独立 context 机会重新核查，但当前不可用资产不计入已有实验条件。
