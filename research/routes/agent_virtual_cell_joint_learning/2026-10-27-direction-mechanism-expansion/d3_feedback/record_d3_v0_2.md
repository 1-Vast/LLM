# record_d3_v0_2 —— R200-D3.1 修订记录（可行性裁定）

2026-10-27 · 角色：ON1/ON2/ON2.2/ON3 执行者（非提案者）· 任务：task-91（D3.1）。
**状态：design revision + feasibility stop；未执行效果，未拟合预测，未比较 acquisition，未读原始响应值做统计。**

## 1. 时间线

| 时间（本机） | 事件 |
|---|---|
| 22:41 | 读 task-91、`challenge_D3.md`、D3 v0.1 `PROTOCOL_D3.md`/`d3.py`/`d3.json`/`report_d3.md`/`record_d3.md`、ON2/ON2-EX calib、ON3 PEEK/QUICK、R200 BRIEF |
| 22:41–22:44 | 写 `d3_revision.py`：修正单 anchor SE/MDE（σ/√2，不是 σ/√32）；加 rank-level MDE（Fisher-z 保守）；计算候选聚合/wells/成本；加 ON3 non-blind/peek、强基线、反馈 pack/成本/失败树 |
| 22:44 | 运行 metadata-only `d3_revision.py` → `d3_v0_2.json`：**design_invalid: precision_insufficient**；mean MDE .1119678；rank MDE 2.2875/0.7625；required_n 1,573；候选全部 rank fail |
| 22:44–22:46 | 写 `PROTOCOL_D3_v0_2.md`/`report_d3_v0_2.md`/本记录/`usage_d3_v0_2.json`；核对 SHA；确认 v0.1 文件未改、未执行效果 |

## 2. 输入（只读）

| 文件 | 用途 |
|---|---|
| `d3_feedback/challenge_D3.md` | task-89 的 5 必改（MDE/rank/ON3 peek/基线/成本失败树） |
| `d3_feedback/{PROTOCOL_D3.md,d3.py,d3.json,report_d3.md,record_d3.md,usage_d3.json}` | v0.1 数据/设计（未改） |
| `exec_calibration/calib.json` | ON2-EX σ/SE/MDE；full-grid se_unit 口径 |
| `PEEK_DISCLOSURE_ON3.md` | ON3 non-blind/peek 规范披露 |
| `tmp/on3_exec_quick_debug.invalid.json` | ON3 QUICK invalid artifact（仅引用 SHA/primary 事实，不用于 D3 选择） |
| R200 BRIEF / ON2 v2.2 / ON3 文档 | 纪律、资源/预算/边界 |

- **未读**：O'Neil workbook、原始 viability 响应、任何表达/功能矩阵；未运行 d3.py 效果；未拟合预测。

## 3. 关键修正

- **单 anchor MDE 单位**：D3 unit=单 anchor 行，2 members×4 tech reps=8 wells；Δ variance=2σ²/4=σ²/2；SE=σ/√2=0.0978960；batch1 target30 σ=0.1384458171 → MDE80 n=6 **0.1119678>0.10**；all-batches σ=.1422665081 → **0.1150578**。v0.1 的 .0287644 是 full-grid σ/√32 错套，**不再作为 prior pass**。
- **rank-level MDE**：Fisher-z 保守 `2.801585√(2/(n_eff−3))`；n=6 **2.2875**，pooled30 **0.7625**，均>0.10；null/bootstrap 只答排除 0，不替代 rank MDE。
- **可行域**：rank MDE≤0.10 需 **≈1,573 独立细胞系**（独立误差）或误差相关≥.9828（n=30）/.9981（n=6）；O'Neil target30 只有 30；技术 wells/反馈量不能替代独立细胞系 n。
- **候选表**：A 单 anchor 4rep **fail**；B pooled30 mean pass/rank fail；C partner-average mean pass/rank fail；D full-grid mean pass/rank fail；E 6rep mean pass/rank fail；F full-grid pooled mean pass/rank fail。**无 overall pass；不挑最低成本方案。**
- **ON3 non-blind**：D3 与 ON3 同用 O'Neil；实现方已见 QUICK invalid primary（Δρ 0.0277068 等）；D3 是 **non-blind/inherited-peek**，不得称 blind/独立确认；**ON3 QUICK primary/results 未用于 D3 方向/阈值/切分/反馈预算/对照/指标**（D3 v0.1 MDE 错误来自 ON2-EX 口径，不是 ON3）。
- **强基线**：固定 primary=U_conflict vs C2；删除 "best ordinary control"；补 C7 tree/GBM、C8 matrix completion、C9 direct response prediction、C10 exact closure where applicable。
- **反馈 pack/成本/失败树**：24 units/fold（120 total），1 轮，每 support cell 1 unit，stratum/quota/seed/dedup/10% reserve 替换；8 wells/unit、11.0 plate-eq 为模拟采购预算（非真实湿实验）；每 arm 调参/计算 cap；N1/N2 1,000×5 folds；唯一失败映射（precision insufficiency→design_invalid；CI 含0→evaluation_cannot_distinguish；点<δ且CI排除0/等效→no_increment；全过→development_increment_present）。

## 4. 裁定

- **v0.1 D3：`design_invalid: precision_insufficient`；D3 当前停止。**
- **不提交 Lead 批准执行协议**；不把 v0.1 作为可执行设计；不改 v0.1 文件。
- 若 Lead 要改变问题（mean-Δ primary/full-grid/partner-average），必须**新预注册 + 重新挑战**；不能包装成原 H_D3 的修订后可行。
- 若坚持 rank primary，需外部队列 ~1,573 独立细胞系或可认证的 ≥.9828 误差相关；当前资源无法满足；不运行。

## 5. 产出（v0.2；不改 v0.1）

| 文件 | 说明 |
|---|---|
| `d3_revision.py` | metadata-only 修正/可行性算术；不拟合/不读响应 |
| `d3_v0_2.json` | 正确 MDE/rank MDE/候选/成本/ON3 peek/强基线/失败树；verdict design_invalid |
| `PROTOCOL_D3_v0_2.md` | 修订/停止裁定（design revision） |
| `report_d3_v0_2.md` | 修订/可行性报告 |
| `record_d3_v0_2.md` | 本记录 |
| `usage_d3_v0_2.json` | 命令/输入输出 SHA/attestation，最后写出 |

## 6. 边界

- **未执行效果/未拟合/未比较 acquisition/未读原始响应值**；只读元数据/文档/SHA；只写 v0.2 与 `tmp/`。
- 不称独立确认/迁移/决策收益/机制/新颖性；技术重复≠独立培养；O'Neil 仅开发性；batch3 全失/702 pair-cell/无双药参照/单 anchor 派生等限制不变。
- 未修改 v0.1 文件、其他目录/INDEX/git/A3；v0.2 是停止裁定，不是执行协议。
