# record_pb2 —— R192-PB2 有注释宇宙 MDE/重开性（时间线 / 冻结 / 偏差 / 审计 / 局限）

2026-10-27。角色：端点与测量体制审计员。工作目录 `D:\MAESTRO`；解释器 `D:\anaconda\envs\maestro\python.exe`（Python 3.11.16 / numpy 2.4.6）。本文件记录**过程**；数字与判定以 [pb2.json](pb2.json) / [report_pb2.md](report_pb2.md) 为准。

## 1. 范围与纪律

- 只**新增** `PROTOCOL_PB2.md / pb2.py / pb2.json / report_pb2.md / record_pb2.md / usage_pb2.json`；**未修改** P-B 既有 7 个产物（`pb2.json → pb_artifacts_unchanged.unchanged = true`，运行前后 SHA256 逐个相同）、未改 P-A 冻结表、其它目录、INDEX、SYNTHESIS、git。
- **只做零模型与检定力**：不拟合 identity/annotation 模型、不评估任何臂的效应、不换端点（固定 `synergy_bliss` + P-B 块均值聚合）。
- 响应值只读 `synergy_bliss` 一个列；用途 = 冻结端点聚合、MDE 方差估计、检定力模拟（`pb2.json → response_use_attestation`）。

## 2. 协议前勘察（disclosure）

冻结（`PROTOCOL_PB2.md` SHA256 `87B1EDC9EF7A67899C33FB87207734E659D86CCE8DEDC8525BA6AF155D8989DE`）之前只做了**只读**勘察：

1. P-A 冻结表**结构**：`mapping_table.csv` 列名、`source_library` 三档各 4,088 行、S1 行中 `pathway!="unmapped"` 的映射药 = **1,418**（`drug_drop=="none"`）、SHA256 复核为 `45EDE635…38D4`。**未读任何响应值**。
2. P-A 报告/协议（只读）：主策略 = S1(KEGG)+规则 A；有注释宇宙 **88,118**；PA 切分 k=284 / both-unseen **2,682**；E1 切分 k=818 / both-unseen **3,739**；训练有注释单元 85,436 / 严格训练 58,788；映射药 1,418/4,088 = 34.69%；G2 在 r=0.20 上 62 个可分析水平。
3. P-B 产物（只读）：`pb.json` 的 MDE 方法、种子、z 常数、`synergy_bliss` 块均值口径、`mde.0.20.*` 结果。
4. v1.4 表头/结构事实沿用 P-B 结构预跑（未再读响应值）。

**未在冻结前计算任何 MDE/power/有注释宇宙的响应统计**。

## 3. 运行与耗时

| 步骤 | 命令 | 耗时/结果 |
|---|---|---|
| 首次运行（仅预注册 6 设计） | `python pb2.py` | 73.7 s；交叉核对全部命中（88,118 / 2,682 / 3,739 / 1,418）；预注册网格 6 设计全部不通过（min MDE80=0.1290，max power=0.658） |
| 加入补充设计后运行 | `python pb2.py` | 209.9 s；12 设计完成，但**末尾 print 语句 bug**（在 `write_json` 之后崩溃，结果文件已写；仅打印失败）→ 修 print 后重跑 |
| 最终运行 ×2 | `python pb2.py` | 209.1 s / 209.3 s；`pb2.json` **两次逐字节相同** SHA256 `CC5047A87F958440D458BD7CE7CD071A0211602290B4988865DF561B79DC198B` |

## 4. 相对冻结协议的偏差（全部披露；不改预注册判定）

1. **post-freeze 补充设计扩展（r={0.45,0.50,0.55}）**：预注册 §4 冻结的设计矩阵是 r∈{0.20,0.30,0.40}×{PA,E1}。首跑完成后发现预注册网格全部不通过（MDE80 最小 0.1290），而外推的最小所需有注释 both-unseen 单元数（14,387，Tier B）**只比网格内最大设计（13,795）高 4%**——这意味着"不可重开"的结论可能只是网格边界造成的假阴性。任务 §3 明确要求回答"**是否存在**可重开的设计（r 值 + 切分口径）"，因此遂在**首跑之后**加入 r=0.45/0.50/0.55 的补充计算（同算法、同门槛、同种子规则），并在 `pb2.json` 中标记为 `supplementary_design_exploration_post_freeze`（`status: post-freeze extension`）。**预注册判定仍按网格报告**（网格内：`not_reopenable`），补充结果作为"是否存在"的回答单独呈现；二者的决策规则阈值（δ_min=0.1183 / 0.0947、power≥0.80、训练≥5,000）**未改**。
2. **增加外推校验**（`extrapolation.supplementary_verification_post_freeze`）：把外推预测的 MDE80 与补充设计的实测 MDE80 对照，如实报告外推在小 n 端偏低（PA_r45 预测 0.1090 vs 实测 0.1208）→ 报告以实测通过点为准。
3. **修 print bug**：首次加入补充设计后，末尾 `recommendation['design']` KeyError 发生在 `pb2.json` 写入**之后**；只影响日志打印，不影响任何数字（重跑后确定性已复核）。
4. 其余（端点、聚合、切分规则、MDE 算法、种子、δ_min tiers、训练门槛、判定规则）与冻结协议逐字一致。

## 5. 关键决定

1. **回答分两层**：预注册网格 = 不可重开；"是否存在可辩护设计" = **存在，但 r=0.50/0.55 超出 R191 BRIEF 网格**，需 Lead 新冻结阶段 2 设计。这避免了把"网格边界"误报成"资源太小"（也避免了把"存在更大设计"误报成"已可重开"）。
2. **`design_recommendation` = PA_r50**（最小 r 通过 Tier B）：r=0.50、δ_min=0.1183、MDE80(双向)=0.1009、power@0.1183=0.938、训练有注释单元 21,645。Tier A（0.0947）需 r=0.55（PA_r55：0.0912/0.979）。
3. **δ_min 的正当化**：只允许取"复现目标效应"量级（Tier B = 冻结头条 0.1183；Tier A = 其 CI 下界 0.0947），**不退回到 P-B 的 0.03**（0.03 是冻结效应的 1/4，按"复现目标"逻辑本就不该作为本资源的 δ_min；P-B 用它是对 BRIEF 建议区间的字面执行，其 not_usable 判定在自身口径下不变）。
4. **不改端点/指标**；不因 power 不够而换指标。

## 6. 响应值/模型保护复核

- `pb2.py` 唯一读取的响应列是 `synergy_bliss`（`read_v14`）；下游只有：单元块均值（P-B 冻结规则）、bootstrap MDE、检定力模拟。
- **唯一的"拟合"**是预注册 §8 的外推：对 6 个设计点的 `(log n, log SE)` 做 2 参数 OLS（`np.linalg.lstsq`），用于把 MDE–n 关系外推到目标 SE；**与任何 identity/annotation 特征无关**，也不是响应模型。
- grep 复核（`tmp/pb2_grep_audit.txt`；模式 `ridge|sklearn|fit\(|predict|coef|train\(|gain|通路−identity|identity arm|annotation arm`）：`pb2.py` 9 处、`pb2.json` 20 处、`report_pb2.md` 1 处、`PROTOCOL_PB2.md` 1 处——逐条均为**良性**命中：① `coef` = 外推 OLS 系数；② `predict` = 零信息预测向量 / 外推预测值（字段名 `predicted_mde80_*`）；③ `gain` = "annotation gain 不假定相等"的免责声明与"no pathway-minus-identity gain"的边界声明。**没有** identity/annotation 模型拟合、没有臂对比、没有效应估计。
- `pb2.json → response_use_attestation` 三项 False（identity/annotation model fitted、effect estimated、training/feature selection on responses）。

## 7. 产物

| 文件 | 说明 | SHA256 |
|---|---|---|
| `PROTOCOL_PB2.md` | 运行前冻结 | `87B1EDC9…8989DE` |
| `pb2.py` | 确定性实现 | 见 `usage_pb2.json` |
| `pb2.json` | 全部设计/MDE/power/判定 | `CC5047A8…DC198B`（两次运行相同） |
| `report_pb2.md` | 报告 | 见 `usage_pb2.json` |
| `record_pb2.md` | 本文件 | — |
| `usage_pb2.json` | 运行时账 | — |
| `tmp/pb2_*.log`、`tmp/pb2_final_run1.json`、`tmp/pb2_grep_audit.txt` | 日志/确定性副本/grep 审计 | — |

## 8. 局限

- 外推 α 固定 1/2，实测 α̂≈−0.41/−0.45；小 n 端外推偏低 10–20%，**报告以实测补充设计为准**（Tier B 实测门槛在 (16,841, 22,200] 单元；Tier A 在 (22,200, 23,014]）。
- 未细扫 r=0.45–0.50 之间的最优点；r=0.50 是"通过 Tier B 的最小预注册外 r"，未必是最优。
- r=0.50/0.55 改变训练集大小（21,645/20,189 有注释单元 vs r=0.20 的 58,788）与留出药组成；冻结效应量级在 r=0.20 下测得，**不假定跨 r 相等**；P-A 的 G2 水平覆盖在 r=0.50 未验证（须新协议重跑）。
- 有注释宇宙只覆盖 108/112 细胞、18,258/62,826 药对；MDE–n 外推只在同一细胞/设计体制内成立。
- 未读 raw 剂量层；端点口径依赖 P-B 的 summary 层论证（未变）。
