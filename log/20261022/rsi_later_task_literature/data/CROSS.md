# 实际交叉审查：后续任务更新选择器的合法反馈与最简证据

2026-10-22。先保存并哈希 data/INDEPENDENT.md，再实际阅读 advocate/INDEPENDENT.md、skeptic/INDEPENDENT.md，并向两者直接提问、收到实质答复。独立稿保持不变。无 AZ/保留集访问，无拟合，无新的表达/HDF5下载；新增 HTTP 仅核同一 CellScientist 一手工作族的固定代码版本。

## 支持及已经闭合的异议

**静态世界响应组件合法，不强加全局动力学门。** 两方均接受：静态 RNA、形态或可用功能终点可以支持合法的 action-conditioned response model。序列数据是多步生物转移、可达性、组合律、真实动态研究闭环等较强主张的资格要求，不应被扩大为所有世界模型组件的必要前提。我向 skeptic 进一步质疑其状态划分修订方向是否必须先有纵向数据；其答复接受：独立 replicate 的静态状态—功能失配及更丰富状态的预测消融也可检验这种有限 conditional-response 候选，仍需控制测量噪声和与 MoE、representation learning、强 direct 公平比较，不能据此推出真实动力学。

**同起点 swap 与总系统继承各有作用。** 我支持其共同 checkpoint、相同允许历史与预算的 old/new improver 替换，用于隔离策略效应；同时质疑把它扩成所有完整回合均回同点是否不必要。skeptic 接受：另报允许共同演化的 total-system 轨迹与初始/继承模型 × 旧/新策略的2×2；swap 不胜不抹去真实的总产品继承收益，也不因此证明策略改善。summary 无需逐字还原 raw history 才合法：在相同原始信息来源、观测成本与训练权限下，可以比较压缩/泛化偏置，但训练费用和继承 payload 要入账，不能声称凭摘要创造了信息。

**最简 later-task 选择器可保留为普通元学习研究。** advocate 的3–5个普通更新动作、小 state-to-action value map、source 随机动作轨迹、封存 later tasks、固定 evaluator 与强普通策略对照，是可理解且简洁的能力问题。双方均明确其普通解释很强；策略 swap、persisted memory、诊断路由或低维价值表并不构成新核心。advocate 已直接承认：若普通 bandit、检索或等预算程序搜索复现收益，就保留普通结果而停止该新机制主张。其指出的 STOP/MetaRSI/Sivia/AIDE2 等前驱在本轮只由审计间接指向，不能当成已精读或留白；正式 novelty 决策仍需回原文。

## 我提出的执行性缺口及对方答复

**“8次被评价更新”需要合法 feedback，而不能暗用隐藏 target。** 我向 advocate 提出：若任务只有两个已付 AC/BD，而 AB 全部封存隐藏，则不能每步读 AB loss 选择后继或 early-stop，再把最后 AB 叫 audit；也不能把矩阵级购买默改成免费单剂量。source 训练阶段可以依法使用 source 目标训练更新价值，但 later task 的目标不能反向参与策略动作。

advocate 明确接受并给出最简合法解释：冻结 source 学得的 ψ，仅依据两 paid 观测、其残差和允许 metadata 决定普通更新；多次 fit 是计算，**不是新增湿实验反馈**。整个轨迹和预测先 seal，AB 只作终端或封存后逐 checkpoint 的统一 audit，不用于挑后继。这样检验的是有限观测下 source 策略迁移，不能写成八轮闭环实验。若将来研究真正逐轮反馈，必须另定义可获得的 development 动作域、完整 group 收费、字段权限与独立 final audit。BBBC fold4/fold5 可在合同合格后承担 development/audit，但只支持形态程序改进。

**数据资产存在不等于已具足够独立 later-task 样本。** advocate 反问：四个 BBBC 文件都来自 U2OS，是否已核全局 plate/SMILES/scaffold 不重叠与足够独立任务族？我答复：尚未下载/检查 HDF5 metadata，未核全局重叠、reference/pre 来源与足够 source→selection→later 三分样本量；因此只能给 metadata 资格方案，不能宣布已有可执行 later-task 功效或跨 cell-line 泛化。不得将 plate/smiles 两种重排文件当成互相独立的两个生物数据集。

## CellScientist 固定公开版本核查

两方都质疑独立稿中的768候选/10评估与原 v1 论文标题不同，是否混合了实现版本。为闭合该问题，我抓取作者 main ref、固定 Git tree、controller/config，并把之前捕获的 README、data schema 和 HF manifest 计算 Git blob hash，与该 tree 核对。

- 固定作者 commit：`e27a5941378e8259cbeca7d336a26f52a09f7cc4`。
- `CELLSCIENTIST_COMMIT_BINDING.json`：README.md、data/README.md、data/release_manifest.json、cellscientist/controllers.py、configs/bbbc036_047_formal.json **5/5 blob匹配**。
- 当前 config `protocol_id=cellscientist_bbbc036_047_release_20260728`，budget10，seeds11/22/33/44/55，四个036/047 plate/smiles task，fold1–3训练、4feedback、5test，selection_rule为feedback_selection_mean。
- 当前 controller 是**固定诊断优先级先排序，最多两个 typed address 各确定一个 canonical atomic edit，再让 LLM 二选一；无LLM或合同错误则固定 top1 fallback**。不是 LLM 任意搜索整个768空间，也没有已学习的跨任务更新策略参数。它使用 history 中 feedback metrics 与见过候选，属于直接必要的普通固定诊断对照。
- 模块明确说公开 release **不包括 baselines、ablations 或 comparative-search policies**。因此不能用“仓库包含”替代实现这些公平比较者；候选空间、evaluator、runner 及实际费用还需在后续复现资格中审查。

这足以冻结“current public CellScientist diagnostic implementation”的来源与部分语义，**不证明它等同 2026-05-08 arXiv v1 的实现，也不复现论文成绩**。两方已收到并接受这个边界。HF数据revision仍为独立稿记录的4171f94...；代码commit和数据revision分别计。

## 未决分歧、实用限制与下一步

当前没有剩余的方向性分歧：可保留普通 later-task 元学习和静态世界响应组件；没有候选因此获新颖性认证。尚未解决的是实证资格：合法 development feedback 的实际资产与字段、全局任务分组、reference/pre 来源、足够任务数、source 训练和后续适配的真实费用，以及药物用途所需的独立功能 assay。公开 scRNA/morphology 的任务效用可如实定义为其观测终点，但不能直接称疗效/存活率。

后续验证建议按依赖顺序做，尚非新执行注册：

1. 只做 metadata/provenance 资格：固定代码/数据版本，核原始来源与 pre/reference 构造、控制共享、plate/replicate映射、全局 canonical SMILES/scaffold 重叠、有效任务数；拆分后不足则停止该数据方案。未经这些核查，不借源文件数或单细胞数夸大任务级样本量。
2. 明确每个 later-task 动作真正能看到什么：若没有新实验 feedback，就只做付费历史条件下的 frozen-policy 迁移；有 development oracle 时，先固定 whole-group 费用和 final-audit 屏障。所有普通对照享有同历史、数据与策略训练信息。
3. 冻结少量普通动作与最简单更新价值策略，并实现 current fixed diagnostic、同历史 LLM、固定/UCB/contextual bandit、简单检索/混合、等预算搜索、普通重训/CL/AL。比较实际计算/观测预算，不能只匹配 accepted candidates 或迭代次数。
4. 共同起点只交换 ψ，另做 solver继承×ψ 的2×2与总系统轨迹；如讨论世界模型必要性，再加同信息强 direct 分支和 world×policy。audit 不参与选择。正式样本量/实用阈值由合格 source 阶段设计，不直接继承其它 assay 的.02或.01。
5. 只有获得具体可证伪的细胞结构差异并且普通解释不能复现，才再次进行不同立场的创新性评审；先核实际 STOP/MetaRSI 等原文。普通优势、有限 improver gain、继承收益可保留，不因为缺新核心或缺动力学而一并否定。

**交叉裁决：metadata/provenance 资格与普通元学习问题 CONDITIONAL-GO；泛化“反馈→诊断→程序修订→继承”作为新核心 NO-GO；完整功能药物发现/动态细胞/RSI联合成功 NOT_ESTABLISHED。** 没有新增数值实验、未打开 reserve、未修改独立稿或 AZ frozen 文件。
