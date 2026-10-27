# record —— R192-R2 阶段 2 独立执行（时间线 / 命令 / 预算 / 决定 / 局限）

2026-10-27，独立 runner（task-12）。工作目录 `D:\MAESTRO`；解释器 `D:\anaconda\envs\maestro\python.exe`（Python 3.11.16 / numpy 2.4.6 / scipy 1.17.1 / pandas 2.3.3）。本文件记录**过程**；判定与数字见 [report.md](report.md)、[stage2.json](stage2.json)、[preflight.json](preflight.json)。

## 1. 范围与纪律

- 只写 `research/2026-10-27-drugcomb-replication/` 与 `tmp/`；未修改 `PROTOCOL_STAGE2.md` / 两个 AMENDMENT / `challenge_STAGE2.md` / `drugcomb-annotation/` / `drugcomb-endpoint/` / `drugcomb-qualification/` / INDEX / SYNTHESIS / git / 源数据。
- 只读输入：v1.4 summary（`block_id/drug_row/drug_col/cell_line_name/synergy_bliss`）+ mapping v2（主）/ v1（敏感性）+ P-B/P-B2 冻结产物与协议。**未下载任何数据**（本轮不需要新增网络取数）。
- 响应列只读 `synergy_bliss`；未读其它响应列。测试标签只用于最终打分/CI/adjusted 描述性分析；未用于标准化、λ、特征、切分或臂选择。
- 阶段 A（`preflight.py`）先于任何 identity/annotation 模型；`preflight.json` gates 全过后才允许并实际运行阶段 B（`stage2.py` 运行时断言该条件）。

## 2. 协议版本与口径确认

- 读到 v1 后收到 Lead 的关键口径更正：`AMENDMENT-002.md` 已更新为 v3 最终版（① 主 CI/F3 的双向聚类维度 = **药对×细胞**（不是药×细胞）；仅留出药聚类为敏感性；② 预注册一步阶梯 r=0.50→0.55；F3 后）——按 Lead 要求**重读 v3 全文**并以 v3 为准实现。
- 最终协议哈希：`PROTOCOL_STAGE2.md` `AEF22C72…F77EC`；`AMENDMENT-001.md` `AA1562B8…0BD95`；`AMENDMENT-002.md`（最终版）`FAFAE127…81E75`。
- F3(b) 的 `se_null` 在 AMENDMENT-002 §1 文本存在两读（字面：零模型 ρ 分布 SD = SE_two_way；或 R3 对照为 10 次均值 → SE/√10）。实现取**字面读法为主**，把替代读法全部报告；选定阶梯 r=0.55 在两种读法下均 ≥0.80（primary 0.8335 / alt 0.8525），r=0.50 在主读法下不过（0.767），故阶梯结论不依赖该歧义。

## 3. 实际命令与耗时

| 步骤 | 命令（cwd = `research/2026-10-27-drugcomb-replication`） | 结果/耗时 |
|---|---|---|
| 结构/口径侦察 | 只读脚本（`tmp/proto_stage2*.py`）：切分口径对照、F1/F2 计数、F3 SE 预演、r=0.55 预演 | v1 前缀切分复现 scoping 32,299/5,342/108/27,230；v3 种子置换切分 r=0.50 为 37,726/7,216/106/22,576 |
| 阶段 A | `python preflight.py` | **35.4 s**；写 `preflight.json`；r=0.50 F3 不过 → 阶梯 r=0.55 全过 F1–F4 → 选定 r=0.55 |
| 阶段 B | `python stage2.py` | **212–224 s**；写 `stage2.json`、`rows.csv`；判定 `not_replicated` |
| 确定性复核 | 连续两次运行 `stage2.py`，比较产物 SHA256 | **逐字节相同**：`stage2.json` `89C34E3C…C05CF`、`rows.csv` `A6FA3FC3…4D0` |
| 全链复核 | 修正读入 QC 后 `preflight.py` + `stage2.py` 从头重跑 | preflight 35.4 s + stage2 ≈224 s；本报告数字全部来自该次冻结运行 |

单命令均远低于 15 分钟上限；内存峰值 <1 GB（Gram 最大约 2,000²，逐臂释放）。

## 4. 决定与理由

1. **阶梯**：r=0.50 的 F3(b) 字面主读法 0.767<0.80（替代读法 0.8045；master seed 0.7825）→ 按 AMENDMENT-002 §4 用同一 seed-permutation 规则生成 r=0.55；r=0.55 F3(a) MDE80=0.0670、F3(b) primary 0.8335 / alt 0.8525、F1/F2/F4 全过 → **选定 r=0.55**（split SHA `BBEB1FFB…C687B5`），写入 preflight.json，之后不再改。选择只依据 pre-flight，未看任何 identity/annotation 效应。
2. **判定**：按 v3 复合规则 R1∧R2∧R3 → `not_replicated`（R1 差 0.00006；R2/R3 主口径 CI 含 0）。**不换规则/端点/聚类口径来救**。
3. **口径敏感性如实报告而不改判定**：pair-cluster-only / held-out-drug / E1 / v1 映射的 CI 不含 0，主口径（药对×细胞）含 0；差异与"预测向量在 pathway-pair 上大量并列 × 细胞重采样"有关。主口径按 v3 裁决；其余列诊断。
4. **功率校准限制如实披露**：F3 的 MDE80=0.0670，但实际拟合臂 realized SE=0.0536 → MDE80 等价 0.150；固定 iid 零预测诊断（0.0492）与 F3 一致，说明差异来自结构化预测向量而非实现错误。P-B 的 MDE80 在 δ=0.1149 处经验 power=0.708（<0.80）也提示该 MDE 定义偏乐观。**不宣称"已充分检定力"**。
5. **adjusted 解读**：partial ρ 控制 study proxy=0.0102（CI 含 0）、控制 cell=0.0234（CI 含 0）；分层 ρ 随 proxy bin 符号翻转；Xboth+proxy 诊断臂 ρ=0.221。→ 观测到的弱关联由 study/cell 组成驱动，不能作为注释特异性证据。正式 `confounded_unresolved` 降级规则仅在 R1–R3 全过时适用（此处未触发），但报告按"实质混杂未解决"措辞处理，未使用"稳健/已解释"。

## 5. QC 事件（实现缺陷，已修正并完整重跑）

- **端点掩码越界**（`s2lib.load_v14`）：`np.isfinite(vals)` 作用于预分配容量 700,000 的数组（n=466,033），未切片到 `[:n]`，导致未初始化尾部被计入 `ok`；表现为 F4 聚合校验 `combo_blocks_finite_endpoint=700000`、缺失块为负。修正为 `vals[:n]` / `unit_code[:n]`，并校验：466,033 组合块全部端点有限、380,418 单元、缺失 0。修正后**从 preflight 开始完整重跑**；修正前错误仅污染第 1 个单元（额外零权重把 y 拉向 0）且该单元不在最终分析池，最终数字与修正前一致到 6 位。
- **其他实现 QC**（均在冻结运行前修正）：`BinaryRidge` 与稠密参考解的自校验（Gram/标准化/eigendecomposition 对齐，`selftest_binary_ridge`）；`build_pools` 的单元注释掩码索引（`a_map[up]` 而非 `a_map[pair_a]`）；`np.unique(..., return_inverse=True)` 返回值顺序；F4 常量臂在聚类 bootstrap 中的零方差保护。
- 自校验 `selftest_binary_ridge()` 在每次 preflight 开始时运行（通过才继续）。

## 6. 预算

- 无新增下载（输入均为本机已有只读文件；v1.4 summary 193,184,734 B 等）。
- 计算：preflight 35.4 s + stage2 ≈212–224 s + 确定性重跑 ≈224 s；总 wall ≈9 分钟（含侦察/调试）。
- token/费用：运行时不可得，`usage.json` 记 `null`（不记 0）。

## 7. 产物

| 文件 | SHA256 |
|---|---|
| `preflight.py` | `893FC1106154596532CF1407964A07008C9DF67023C503C842FD83708372E8A7` |
| `stage2.py` | `1649FD0ACC6019942F669F8EF31900239BB2CE603512C20334CF93BE17017B3E` |
| `s2lib.py` | `B39BEA1D7A62FA70CCCD8F9ECDEB2AA6C67789E15B7D0670FB07CB9257CBBCAF` |
| `preflight.json` | `B6D337704E46DF3586D46C45D0E5DEE17FE5BF212E4E88A0C0CC3BA5DECE22FA` |
| `stage2.json` | `89C34E3C5F602244847D01CAE9929FFB9B4CD7E86E6EC8BF98DF3FCE730C05CF` |
| `rows.csv` | `A6FA3FC38EF406A6314C9C99D252AC035EA1F640B19FA3305ADDCC86D7ACD4D0` |

## 8. 局限（详见 report.md §4/§7/§9）

- 功率校准不足（F3 解析近似、realized SE 更大、P-B 自校验 0.708）；`not_replicated` 只能解释为"该设定未检出"。
- 主判定对聚类口径敏感（主口径含 0；多种敏感性不含 0），按协议不换口径。
- adjusted 显示 study proxy/cell 组成可解释弱关联；单切分、细胞不参与切分、注释子集选择偏差（37.56% 注释宇宙、11.87% 全宇宙、多 block 暴露 8.85%）。
- 三重构造差异未解决（跨 r 0.55 vs 0.20、端点 synergy_bliss vs ΔEMAX、注释 KEGG-argmax 93 水平 vs 项目 38 双侧 one-hot）。
- 未做/未宣称：机制/临床、独立 Jaaks 确认、效应量级复现、DrugComb 不可复现。
