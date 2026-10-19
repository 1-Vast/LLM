# MAESTRO-FAR：开发实验、复现与审计

**当前结论：`FAR_NOT_SUPPORTED`。** 当前 kernel/kNN + L1000 transfer 实现未证明 FAR slice 选择优于 exploit-first；不等于证伪整个 Agent + Virtual Cell 研究方向。

先读 [复现与方法审计](audit_20261019/REPORT.md)，再读 [原实验结果](REPORT.md) 和 [冻结决策](DECISION.json)。原报告中的“严格三阶段隔离”“所有策略严格等药物数成本”和“future-task headroom”须结合审计修正理解。

## 文件用途

| 类别 | 文件 | 状态与用途 |
|---|---|---|
| 冻结核心 | `far_core.py`, `far_data.py`, `MODEL.json`, `VALUE_MODEL.pkl`, `FREEZE_PROTOCOL.md` | 由 `FREEZE.json` 锁定，整理不改动 |
| 已完成实验 | `records_*.npz`, `ATLAS_*.json`, `CONTRASTS_*.json`, `DECISION.json`, `V2_SEARCH.json` | 原始结果保留；vault 为已曝光数据复用 |
| 只读验证 | `verify.py`, `far_decide.decide()` | 校验 freeze、重算原门槛、检查保存记录的一项主对比；不写回结果、不训练模型 |
| 深度复现 | `audit_20261019/audit.py` | 独立重算 118 项对比、重建 select/test 的 54 个策略组合、检查数据和阶段依赖；只写审计子目录 |
| 历史生成器 | `far_run.py`, `far_v2_search.py`, `far_vault.py`, `far_analyse.py`, `qualify_edges.py` | 保留复现来源；已有阶段/模型的生成命令会提前拒绝覆盖。分析和 metadata 生成命令仍会写回对应 JSON，日常检查使用只读入口 |
| 早期方案 | `AUDIT.md`, `PROTOCOL.md`, `EDGES.json` | Phase 0 审计和初稿；其中“尚未运行”仅指当时状态。实际执行定义以 `FREEZE_PROTOCOL.md` 为准 |
| 研究轨迹 | `DEVIATIONS.json`, `discarded_run0/` | 保留偏差与被丢弃的 unequal-cost 记录；完全相同的 atlas/model 副本已去重 |
| 整理回归 | `test_maintenance.py`, `CLEANUP.json` | 记录非冻结脚本整理及只读/防覆盖回归检查 |

## 日常检查

在 `D:/MAESTRO` 的 PowerShell 执行：

```powershell
& 'D:\anaconda\envs\maestro\python.exe' -B research/maestro_far_20261019/verify.py
& 'D:\anaconda\envs\maestro\python.exe' -B -m pytest research/maestro_far_20261019/test_maintenance.py -p no:cacheprovider
```

需要完整策略复现时，使用原依赖环境；当前 `maestro` 中 sklearn 1.9.0 不能直接加载原 sklearn 1.6.1 pickle：

```powershell
& 'D:\anaconda\python.exe' -B -c 'import os,runpy; h=os.add_dll_directory("D:/anaconda/Library/bin"); runpy.run_path("research/maestro_far_20261019/audit_20261019/audit.py",run_name="__main__")' --original-env
```

深度复现会更新对应审计结果 JSON。单线程、原默认线程和 `maestro` 的不同环境结果包含不同的兼容性/敏感性证据，均保留。历史审计结果的 `predecessor_sha256` 描述当次运行的文件版本；非冻结 driver 的后续整理见 `CLEANUP.json`，不应把历史 hash 当成当前代码 hash。

## 下一步边界

重新研究 MoA/靶点能否预测 assay 价值之前，先确定严格隔离的 references、完整 MoA/结构身份分组、精确成本和 evaluator 访问边界，再冻结新协议。当前 test/vault 都已曝光，重新拆分仍是开发证据。Agent、2×2、transfer 不满足原前置门槛，本次未运行。
