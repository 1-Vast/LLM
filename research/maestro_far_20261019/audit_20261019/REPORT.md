# FAR 复现与方法审计（2026-10-19）

**结论：保留 `FAR_NOT_SUPPORTED`，但应将证据描述为“已曝光数据上的交叉验证开发实验”，不能描述成严格隔离的 search → select → test 验证。** 原结果的数值能够在本机原运行环境中复现；当前 `maestro` 环境则不能完整复现。没有测试新的 MoA/靶点假设，也没有重训或修改冻结模型。

后续整理说明：本报告中“原 verifier 写回 decision”和“runner 覆盖检查过晚”描述审计时的版本；整理后已改为只读验证和提前拒绝覆盖。冻结核心、模型、门槛及原实验结果未改，非冻结脚本的整理与回归验证见 [工作入口](../README.md) 和 `../CLEANUP.json`。

## 已执行的验证

1. 在 `D:/anaconda/envs/maestro/python.exe` 运行原 `verify.py`：输出 `VERIFIED`，原文件未改变。
2. 用独立的“按 family 聚合后重采样”实现重算 search/select/test/vault 的全部 **118 个已保存对比**（utility 与 hits，4,000 次 bootstrap）：与保存的点估计、95% 区间、单侧下界一致，误差小于 `1e-9`。这验证了存档记录到统计表的计算，不证明原评估设计独立。
3. 从原 PRISM/L1000/SMILES 数据重建 select fold 2 和 test folds 3、4；使用冻结模型运行 **54 个 fold × policy × repair 组合**，对比每个药物的 utility/hits 贡献数组；重建三个 failure signatures 的 atlas。
4. 在原环境（base，依赖版本见下表）和默认线程配置下，上述所有数组与 atlas **逐项一致，最大误差 0**，FAR-v2 也成功加载并复现。
5. 在当前 `maestro` 环境重跑，其余 51 个组合均完成，但记录不完全相同，FAR-v2 加载失败；另外完成原环境单线程敏感性检查。
6. 用合成数据扰动验证阶段依赖，并审计 ID、MoA 与 slice 大小。原研究目录直属文件的前后 SHA-256 一致；审计产物均在本子目录。

search/vault 本轮只重算已保存记录的统计，不重新拟合 search 模型、不再次运行 vault outcome replay。vault 原本就不是独立确认。

## 主结论的复现结果

以下为原环境完整复现的原冻结结果，不是新的独立实验。utility 单位为每次 nomination 的 selective killing log2FC。

| 对比 | select | test |
|---|---:|---:|
| FAR − exploit-first | −0.01342 [−0.02773, −0.00420] | +0.00606 [−0.00279, +0.01774] |
| FAR-v2 − exploit-first | −0.01993 [−0.03834, −0.00661] | −0.00012 [−0.00655, +0.00627] |
| FAR assay + gate − no assay | +0.02104 [+0.00004, +0.04923] | +0.03895 [+0.00944, +0.08502] |

两个主要对比均未达到预设 practical threshold `0.010` 的下界门槛；不运行 Agent、2×2、transfer 的原决策保持成立。这不能推导出 FAR 总体无效，也不能验证现代 foundation Virtual Cell 的证伪/修复能力：本实验只测试当前 kernel/kNN + L1000 transfer 实现。

## 需要纠正的方法表述

### 1. 阶段不是严格隔离的（主要问题）

`far_core.py:19` 的实际 reference 定义为：

| 当前评估 | 预测模型使用的 reference outcomes |
|---|---|
| search fold 0 | folds 1、**2（select）** |
| search fold 1 | folds 0、**2（select）** |
| select fold 2 | folds 0、1 |
| test fold 3 | folds 0、1、2、**4（另一个 test）** |
| test fold 4 | folds 0、1、2、**3（另一个 test）** |

因此 search 时已经使用 select 的 PRISM 标签；test 的两个 fold 相互提供训练标签。合成扰动检查中，更改 fold 2 标签使 search 预测最大改变 5.270，更改 fold 4 标签使 test fold 3 预测最大改变 7.385，确认存在实际计算依赖。

这可以定义为已冻结程序的交叉拟合评估：每个 query fold 本身未作为自己的训练 reference。**它不等于严格三阶段留出评估**；尤其不能把 select 称为从未参与 search 的保留集。跨 test fold 的共享训练依赖也没有被原来的“各 fold 独立抽 family”的 bootstrap 重建。

`far_data.load()` 每次直接读取整张 PRISM CSV；`Campaign` 提前计算所有 query L1000 的 transfer/repair，之后才用 measured mask 限制应用。主 FAR/FAR-v2 的 acquisition features 在合成检查中不随 query L1000 值变化（最大变化 0），没有发现主 acquisition 显式使用未购买 L1000 值。但这里没有独立 evaluator 强制执行的隐藏数据访问边界，文件哈希也不能证明历史上的访问时间顺序。

### 2. “严格等成本、25%”不成立（主要问题）

`np.array_split(order, 16)` 只保证 slice 大小相差不超过 1。若把成本定义为购买四个固定大小 plate/block，则 action 数可以相同；若按原报告所说的“测量药物数”计费，成本就不完全相同：

| pool | 单 slice 大小 | 买 4 slices 的可能药物数 | FAR 实际均值 | exploit 实际均值 |
|---|---|---:|---:|---:|
| select fold 2，113 drugs | 7 或 8 | 28–29 | 28.346 | 28.172 |
| test fold 3，149 drugs | 9 或 10 | 36–40 | 37.563 | 37.254 |
| test fold 4，180 drugs | 11 或 12 | 44–48 | 45.221 | 45.024 |

当前主 FAR 相比 exploit 略多测量，不能称为严格等药物数对比。差异远小于被丢弃的 run0，但仍应报告；本轮未通过事后调整预算重写原结果。

### 3. 数据对齐与 family 边界仍不完整

* L1000 的 `pert_ids` 可包含 `BRD-...|BRD-...`。当前代码将整串作为 key；在所有 HTS treatment metadata 中，精确匹配为 1,491 个 ID，按 `|` 拆开后的 token 匹配为 1,737 个，漏掉 246 个潜在 ID 匹配。**这不是说 arena 必定应多 246 个药物**：还需要经过 tier、signature coverage、结构身份与去重检查。
* 所有去重后的 HTS treatment rows 中有 2,015 行逗号连接 SMILES；其中 109 行含不止一种 canonical SMILES。当前“取第一个”的解析均能成功，但“重复字符串”和“结构相同”不是同一件事；差异可能涉及盐型、立体化学或其他标准化问题，需要逐条身份审计。此计数针对完整 HTS metadata，不能当作 848 个 dev 药物的歧义计数。
* family 只使用第一个 MoA 标签。保留的 dev 药物中发现 **27 个完整 MoA 标签跨 fold**，例如 FLT3、KIT、PDGFR 等；当前是“首个 MoA + chemistry 连通 family”留出，不是所有 MoA 标签均隔离。若改用全部标签，必须重新确定分组与可用样本量，不能直接沿用原折号和区间。

### 4. 区间与 headroom 的范围需要收窄

原 bootstrap 对已经确定的 nomination 贡献数组按药物 family 加权，并不重训模型、重选 slices 或重排名；cell lineage/source 也未重采样。因此这些是对固定 replay 的条件性区间，不能直接用于新 context、新 assay 或整个训练/选择流程的泛化保证。

split-line oracle 在相同药物上，用其他随机半数细胞系的真实 outcome 选 slices；它提供该 arena 内的 hindsight headroom 线索。随机分半未隔离 lineage，共享药物及响应结构，不能把它当作“在未来独立任务已证实有可学 headroom”。MoA/target 仍是未测试假说。

### 5. 可复现性和检查范围

| 库 | 本轮 `maestro` | 完整复现环境（base） |
|---|---|---|
| NumPy | 2.4.6 | 1.26.4 |
| pandas | 2.3.3 | 2.3.2 |
| SciPy | 1.17.1 | 1.10.1 |
| scikit-learn | 1.9.0 | 1.6.1 |
| RDKit | 2026.3.6 | 2025.9.2 |

`maestro` 加载 `VALUE_MODEL.pkl` 报 `ModuleNotFoundError: No module named '_loss'`。当前环境重跑 FAR − exploit 的 test 点估计约 +0.00213，而原环境为 +0.00606；都没有达到原 practical floor。本轮没有修改环境包或转换 pickle，也没有把不同环境结果当作新的测试集结果。

原环境默认 OpenBLAS 24 threads / MKL 20 threads 可完整复现；限制为单线程时，fold 3 某些离散决策会变化（split-line oracle utility 改变约 +0.00208），fold 2/4 仍一致。这里只确认版本/线程配置敏感，未进一步归因于某一个库或具体浮点路径。

原 `verify.py` 只从记录重算一个 test 对比，并从已有 JSON 重算 decision，不加载 FAR-v2 或复跑模型；此外强制预期 verdict 为 `FAR_NOT_SUPPORTED`。所以其 `VERIFIED` 只能用于其声明的文件/统计一致性检查。

冻结 hash 不包含 runner、analysis、vault runner、decision logic 和原始数据；本轮额外保存当前输入文件的 SHA-256 供以后对照，不能倒推出冻结时的数据版本。`far_decide.py` 对两个 contrast 都使用 2.5% 下分位门槛，实质上是保守的 Bonferroni 型规则，不是完整的 Holm step-down；本次两项都未通过，因此不改变 verdict。

另有复跑操作隐患：`far_run.py search` 的 write-once 判断晚于 `MODEL.json` 重写；不宜直接在原目录重跑该命令。本审计使用只读重建路径，避免了该问题。

## 后续应如何使用这份证据

保留两点：当前 failure signatures 没有达到门槛；在当前固定 replay 中，L1000 + gate 的辅助信息收益能复现，但尚无 FAR 特异优势。

若将来重开研究，先冻结真正隔离的 reference/selection/evaluation 规则、结构与多 MoA 分组、精确计费、数据/运行依赖版本及 evaluator 边界，再在 search 数据上研究 MoA/target 是否预测 assay 价值。原 test 与 vault 均已曝光；重新划分它们只提供开发证据。外部确认需要另行核定尚未曝光的数据与协议。本轮没有推进新分支。

## 产物与复现命令

* `audit.py`：独立统计实现、只读策略 replay、metadata 与合成依赖检查。
* `RESULTS.json`：`maestro` 环境结果与兼容性失败记录。
* `RESULTS_original_env.json`：原环境默认线程，所有复现检查通过。
* `RESULTS_original_env_1thread.json`：原环境单线程敏感性结果（历史审计运行记录）。

从 `D:/MAESTRO` 的 PowerShell 执行：

```powershell
& 'D:\anaconda\envs\maestro\python.exe' -B research/maestro_far_20261019/audit_20261019/audit.py

# Windows 上原环境需要先注册其 DLL 目录；只影响该子进程。
& 'D:\anaconda\python.exe' -B -c 'import os,runpy; h=os.add_dll_directory("D:/anaconda/Library/bin"); runpy.run_path("research/maestro_far_20261019/audit_20261019/audit.py",run_name="__main__")' --original-env
```

没有下载、付费/LLM 调用、wet lab、PRISM 24Q2 或其他新 sealed outcome 访问；没有 commit/push。未运行整个仓库测试套件：本轮只增加独立审计工具和报告，未改产品代码。
