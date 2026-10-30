# `bridge_transcriptome_viability.csv` 追溯审计

日期：2026-10-30（Asia/Shanghai）

## 判定

该 684 行文件是一个 **derived cross-assay bridge**，不是同一条件下采集的转录代理—独立功能配对矩阵。它可用于已暴露内部开发中的描述性关联或普通预测基线；不准入 I304/R2 的功能反馈、误差层定位、等预算省实验或机制验证。

## 可复核字节与字段

- 文件：`data/processed/maestro_vc_v1/bridge_transcriptome_viability.csv`
- 行数：684（含表头 685 行）；SHA-256：`dd44e96674dd85a6a048c9d96ca59cd616915552a0eb7ba5e188d0eced7ebd09`，与 `data/manifests/maestro_vc_v1_manifest.json` 一致。
- 数据集分布：`sciplex3` 219 行，`l1000` 465 行；细胞背景只有 A549、MCF7、PC3；化合物 296 个；PRISM screen 为 HTS002、MTS006、MTS010。
- 所有 684 个 `unit_id` 都编码为 `24h|10000nM`。这只描述转录状态的条件键；桥表没有 PRISM 的暴露时间、vehicle、检测板、培养制备或独立重复字段。
- `block` 是结构/药物批次连接键；同一 block 大多对应一个 `broad_id`，不是独立培养或重复身份。

## 两端的来源语义不一致

### 转录端

`sciplex3` 和 `l1000` 是不同的转录资源。项目清单将 SciPlex3 原始文件标为缺失，`data/external/sciplex_family` 为空，桥表所引用的 `outputs/dynamic_world_model_20260926/prepared/conditions.csv` 和 `outputs/sequence_audit_20260926/l1000/prepared/conditions.csv` 当前也不存在。因此无法从当前文件重核每一行的原始样本、vehicle、plate 或 biological preparation。

### PRISM 端

当前可读的 PRISM 19Q4 secondary README 说明：

- pooled-cell-line viability screen 使用 8-step、4-fold dilution，起始 10 µM；
- viability 先按 replicate-level log-fold change 处理，随后 median-collapse drug-dose-cell-line，并用 `drc` 拟合 dose-response curve；
- `MTS010` 是 147 个既有 oncology compounds 的 technical redo；不能自动当作新的生物培养重复；
- replicate metadata 有 `detection_plate`、`compound_plate`、`well`，但桥表没有这些键；collapsed metadata 只有 compound/dose/screen 等字段，且没有 exposure-time 列。

桥表的 `viability_auc` 与 `viability_curve_r2` 来自已拟合的曲线摘要；当前 PRISM 目录没有与桥表一起保存的曲线参数文件或生成脚本。它们不能被解释为 `24h, 10000 nM` 的单点功能读出。`viability` 仍是 pooled survival/response 代理，也不是独立于转录代理的正交功能终点（例如 washout recovery、clonogenicity、apoptosis 或分泌功能）。

## 数据契约逐项结果

| 条件 | 结果 | 说明 |
|---|---|---|
| drug × cell/background | 部分满足 | 296 个化合物、3 个细胞名可连接；不是同一实验单位证明 |
| dose | 不满足 | 转录端是 10,000 nM；PRISM AUC 汇总多剂量曲线，未证明单点剂量相同 |
| exposure time | 不满足 | 转录端写 24 h；PRISM bridge/metadata 没有匹配时间 |
| vehicle/control | 不满足 | PRISM 原始处理相对 DMSO，但桥表没有同条件 control 键，转录源也无法追溯 |
| preparation/plate | 不满足 | PRISM 原表有 plate/well，但桥表丢失；转录源 preparation 不可核 |
| independent biological repeat | 不满足 | MTS010 是 technical redo；桥表没有 biological replicate 身份 |
| independent function | 不满足 | 只有跨 assay 的 transcript 与 pooled viability 摘要，没有正交功能终点 |
| target/genetic reference | 不满足 | MoA/target 是注释，不是同条件 target engagement 或遗传干预参照 |
| raw provenance | 不满足 | bridge 没有 sidecar；转录 prepared/source 文件当前缺失，PRISM 曲线摘要来源未登记 |

## 结论与后续

当前桥只能保留为 **exploratory derived association / ordinary baseline**。不使用它训练或比较 Agent×虚拟细胞共同学习机制，不把 `discordance` 计为可定位的机制错误，不以文件存在、字段齐全或 parser 通过宣称配对证据。

只有取得同一条件 ID 下的 drug、cell/background、physical dose、exposure time、vehicle、preparation/plate、independent biological replicate、proxy 与真正独立功能终点，并按整药物/整背景冻结 holdout 后，才可重开 R2 最小实验。当前状态为 `data_unavailable`、`NO_EXPERIMENT`、`NO_PROMOTION`。
