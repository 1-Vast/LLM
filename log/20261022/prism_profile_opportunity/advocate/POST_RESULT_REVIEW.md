# 固定 bulk-profile 任务结果后审查：倡议立场

2026-10-22。审查者 `/root/mechanism_advocate`。本稿依据已保存的 `COVERAGE_RESULT.json` 与 `MASK_DESCRIPTION.json`，并记录与 skeptic/data 的真实往返；未读两位本阶段结果后审查稿来形成下述判断。未读取真实响应强度，未增加 GET、拟合、DeepSeek 调用或原始数值转布尔转换。

## 决定与结论边界

**STOP_BULK_PROFILE_COVERAGE。** 停止此固定 PRISM secondary HTS002、2.5 µM、两固定 paid pools、433 audit contexts、既定 chemical purge 与 plate split 的 bulk-profile 配置，且在拟合之前停止。不得更换 pool、seed、阈值、保留 plate 子集或将 PREP041 单独包装成新 test 来挽救本合同。

这是预注册任务的可观测性与样本覆盖资格失败。模型性能、update-value 异质性、世界模型贡献、智能体贡献、继承收益、联合收益及 C4/RSI 的改进策略继承，均为 **NOT_TESTED**。它既不是强直接预测模型战胜世界模型的结果，也不能证明所有部分目录任务不可能。现有部分目录的用途如需研究，必须另立应用与估计对象、公开历史暴露与选择过程；当前 STOP 不自动授权新实验。

## 已有证据

| 冻结资格项 | 观测 | 判定 |
|---|---:|---|
| source 至少 300 | 54/565 | FAIL |
| development 至少 80 | 0/211 | FAIL |
| test 至少 70%（至少 179） | 33/255，约 12.94% | FAIL |
| 至少六块 test plates 各至少 10 | 仅 PREP041 为 33，另六块为 0 | FAIL |
| 七块 test plates 各至少 1 | 仅一块非零 | FAIL |

原始 test 255 个，chemical purge 后仍 255 个；未通过的化合物与板不能从分母移除。开发集 P904 paid-pool 通过数为 0/211，因此它单独已阻断每个开发任务的联合资格；P933 通过 80/211，两个 audit 条件分别通过 101/211 与 109/211，不能补偿必要条件的失败。该结果没有提供缺失原因，不得解释为响应值全为零、药物无效或 assay 损坏。

test 的两个 audit 条件分别通过 204/255 与 210/255，也不能替代四条件的逐化合物联合资格。全体槽位 705191/942334 finite（约 74.8%）是槽位级描述，不是任务级成功率，不可用于越过任何失败门。源/开发/测试的统计与原始板分组均须保留，不能以一个 pooled average 掩盖开发集为空与板间缺失集中。

这些 feasibility floors 不是效能分析、噪声基线、临床阈值或独立样本量证据。即使覆盖通过，也只会允许冻结下一份模型比较协议，不会自动建立 raw-independent、prospective 或真实功能有效性；当前连该前置资格也未通过。

## 真正的交叉质疑

### 与 scientific_skeptic

对方首先提出最强问题：是否接受 bulk 配置停止、不 fit、不换 pool/板/阈值，以及不以全局约 74.8% finite 平均压过逐化合物门；partial 合同不可称 fresh holdout。

我的实际答复：全部接受。最强反驳针对结论外推，而非挽救结果：联合覆盖失败不构成模型性能阴性；两个 audit 边际通过数与 PREP041 的 33 个记录也不能救门。明确追问现有 33 个合格 test 是否只能支持 mask 描述，不能判定 update-value 异质性/C4/world/RSI；并反对从 P904 0/211 推断生物或 assay 原因。

对方实际回复：接受该边界；合同已经 STOP，33 条只能支持既定 mask/coverage 描述，不能判定 update-value 或 world/agent/inheritance/joint/C4/RSI。未来 partial 不被逻辑排除，但须另合同、完整披露 selection exposure，不能称 fresh confirmation。P904 0/211 是 paid-pool 门通过数，不是响应值全零、药物无效或 assay 损坏；跨 replicate 边际通过数不能取代联合资格。

解决状态：结论边界一致。没有以“倡议立场”要求额外拟合或后验子集分析。对部分目录能否支持一个不同应用，仍属未验证问题。

### 与 functional_auditor

对方首先提出最强问题：是否同意 STOP 仅限两固定 paid pools 到 bulk 433 contexts 的资格，而非 model/world 阴性；不得换 better pool 或仅留 PREP041；partial 另合同仍是 exposed catalog。

我的实际答复：全部接受。提出的最强数据/成本问题为：39178 逻辑 bundle accesses 应按 1031×38 记账，942334 numeric-to-bool attempts 应按 1031×914 记账，失败不能退款；但 parser tokenize 全 CSV 的事实必须保留，不能称从未接触全源文件，也不能将名义 acquisition 记为真实实验成本。请求其独立核实，并区分 P904 门阻断与因果归因。

对方实际回复：报告其已有 bool-mask 审计 41423 checks PASS，未重读 raw；确认每 execution 的 39178/942334 分别为逻辑 bundle/float→bool attempts，NPZ 仅有 1031×914 bool mask 与 Unicode 地址，无数值 cache。全 CSV 列的字符串 token contact、共享 ComBat 与历史 source exposure 均仍需披露。87 个联合合格记录不能使失败 attempts 退款。P904 dev 0/211 仅指通过 >=20/25 条件的任务为零，nominal slots 仍约 47% finite，原因未知。上述核验属于 data 的独立报告，本代理没有重做其检查。

对方最强反问：若事后 mask 显示另一 pool 更完整，能否借此复活本 bulk 任务？我的实际答复：不能；用 mask 结果选择新 pool 已产生 selection exposure，必须另立应用/合同并明确披露，仍不能称 fresh confirmatory 或新核心；87 qualified 也不退款。

解决状态：STOP、计费单位、字符串接触范围及事后选 pool 的限制一致。独立 raw normalization 与历史 source exposure 仍是新合同也须面对的外部限制，并未被本次 mask 检查修复。

## 对下一方向的倡议与约束

**不建议继续投入本 bulk 配置，也不建议用当前单板合格子集支撑核心创新。** 本阶段的积极信息是一个严格且便宜的资格门阻止了无效的后续模型搜索；它不是新机制本身，也不应作为 RSI 成功结果。

在既有合格证据范围内，尚无已确认能支持“药物功能响应、独立重复、后续任务、同预算反馈比较”的新来源。不能以广泛数据集名称替代资格证明，更不能将 RNA、形态或 captured cell counts 直接称为 viability 或药效。

若 root 决定转向真正不同的应用，当前最可说明的候选是已保存作者 loader/资产 metadata 的 CellFlow PBMC cytokine RNA 响应：12 donors×90 cytokines。它最多值得一次有界的 metadata/provenance 资格核验，应用须写成免疫扰动下的转录状态适应；它不是已就绪的药物功能或 C4/RSI 数据集。12 donors 的物理分组、重复、任务独立性、有效后续任务数和反馈成本尚未合格，约 13.1 GB 文件也不因“可获取”就值得立即下载。该优先级建议来自先前已经保存的作者级证据，本轮没有重新 GET 或补充可用性断言。

BBBC036/047 形态路线已有相近 controller 先例，plate/chemical 独立与 preprocessing 尚未资格化；Tahoe 不能将单细胞捕获数当作独立 viability；VCC2026 下载此前未合格。三者均不能被写成现成的替代功能验证集。若坚持原始药物功能目标，优先级应是承认当前缺少合格来源并限定下一次来源资格工作，而非对已失败的 PRISM 合同进行救援搜索。

后续新合同最低应先明确具体应用、可获得且有出处的测量、物理分组与重复、历史暴露、later-task 数量、反馈单位和停止条件；通过后再冻结同反馈强 direct、普通重训练、持续学习、主动学习、简单混合、等预算程序搜索与 world/agent/inheritance/joint 的分解。RSI 仍须独立证明继承的改进策略使后续改进更有效，不能用一次最佳子集结果代替。

## 审查完整性

封存结果 SHA256：`COVERAGE_RESULT.json` = `073f292f5b5b522d867d56b81ef363c72a81c813b2cee06b8301e5d76f2c3e43`；`MASK_DESCRIPTION.json` = `b730398864933e96c36ad4b461fd7d5c1cfdde1cdf43bc06ce0dc01f7bb8d74e`。

既有独立稿 `INDEPENDENT.md` SHA256 = `41fd805c3caff9026977946af00c98a262d517a33ddc1d3712d87da952403c0e`，既有 `CROSS.md` SHA256 = `ee606055762d10ce2ab75655e7ac7800d05f5812dd1b54cb7bb24f10e5ff36ac`；本阶段不回写。一次完整打印允许读取的大型 coverage JSON 导致工具输出截断；这是输出检查失误，不是实验失败，没有据截断输出进行新数值转换或选择。之后仅使用已保存的结果/mask摘要与文件哈希。
