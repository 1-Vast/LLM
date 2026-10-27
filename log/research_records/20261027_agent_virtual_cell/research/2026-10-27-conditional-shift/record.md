# record — R193-A0 匹配资格审计（时间线 / 命令 / 预算 / 决定 / 局限）

2026-10-27。角色：A0 匹配资格审计员（独立；不做效果分析、不估 Q）。工作目录 `D:\MAESTRO`；解释器 `D:\anaconda\envs\maestro\python.exe`（Python 3.11.16 / pandas 2.3.3 / numpy 2.4.6 / openpyxl 3.1.5）。本文件记录**过程**；判定与数字见 [report.md](report.md)、[a0.json](a0.json)。

## 1. 范围与纪律

- 只写 `research/2026-10-27-conditional-shift/` 与 `tmp/`；未改 `PROTOCOL_A0.md` 冻结后内容、其它研究目录、INDEX、SYNTHESIS、git、源数据。
- 只读输入：Jaaks `Original screen_All tissues_fitted data.csv`（198,893,607 B）、`Validation screen_All tissues_fitted data.csv`（11,774,397 B）、`Glossary.xlsx`（12,193 B）。
- **响应盲**：只读元数据列（身份/方向/剂量设计/screen-板）与 Glossary 文本；26 个响应/派生列从未被读取为数值。端点可用性只用流式 csv **空串存在性检查**（不解析、不转换、不聚合），输出仅"空值行数/比例"。
- 先冻结 `PROTOCOL_A0.md`（匹配定义、独立组定义、门槛 500 / ≥10 细胞 / ≥10 药对、失败判据、局限）再运行最终 a0.py；冻结前只做**元数据侦察**（不涉及响应值），用于确认口径与门槛可执行性。门槛按 BRIEF 默认 500 冻结，未按实测更改。
- 不联网；未下载任何数据。

## 2. 协议与输入哈希

| 对象 | SHA256 |
|---|---|
| `PROTOCOL_A0.md` | `D77316ED9983D803D0671EF0C7D51F58BCDD439CFCCF253110BEA9B19539AA93` |
| `a0.py`（最终） | `444E939CDDD2F2DBDAD805C298F73B89A538320CE1A4A6C2E7037C8CB66C3525` |
| `a0.json` | `72BBAF6DF9BF80BBD19BF946A8D7A369003861FF21BD95561BC6DA48021ECA22` |
| `matched_conditions.csv` | `73FD5085A7586BB1F33768E34A587668953DA4C13735693DCF2FCCCBC51353FF` |
| `matched_quadruples.csv` | `881A0DFC62A7D70DE158F5795AE1F2766E8EA1091BF6ED4F7280BA4A8211CCF9` |
| Original fitted | `1188968CE7FDCFB66D03791CF266515B7C7A2794E1FC73C966DBA40266FFA278` |
| Validation fitted | `DCBD4C3108D212FA771C52AE977C8E1C01A421162A2232CDC4273FAF257B2775` |
| Glossary | `E29D8D2DCCF230CE5E17B530C1A012389659142FDF78AE20C55B20A4C34619CE` |

## 3. 实际命令与耗时

| 步骤 | 命令（cwd = `D:\MAESTRO`） | 结果/耗时 |
|---|---|---|
| 结构侦察 1 | `python tmp\a0_probe1.py` | 检查 fitted 表元数据列；因复合值 `1032\|1372` 类型错误中止（3.4 s，无产物） |
| 结构侦察 2 | `python tmp\a0_probe2.py` | 板/条件/重复结构；复合浓度值 `0.125\|0.003` 再次中止（4.4 s） |
| 可行性侦察 | `python tmp\a0_probe3.py` → `tmp\a0_probe3.json` | 6.7 s；给出重叠/结构初值（其中 cell×condition 共同键数 4,690 后来发现是 `ANCHOR_CONC` 字符串化口径错误；最终以 a0.py 的 `format(float,'.10g')` 口径为准，并用独立 verify 脚本确认共同键 **9,154**） |
| 端点/碰撞/板核验 | `python -c`（一次性元数据核验） | 两文件 4 个 Δ 端点空值均 0；barcode 集合交集 0；细胞名并集无碰撞；药名 1 个归一碰撞（仅标签） |
| 冻结 | 写 `PROTOCOL_A0.md` | 匹配定义/独立组/门槛/失败判据写死后再跑计数 |
| 审计实现 | 写 `a0.py` | 单文件：元数据读入 + 端点存在性流式扫描 + 组合计数 + CSV + a0.json |
| 最终运行（冻结版） | `python research\2026-10-27-conditional-shift\a0.py` | **26–35 s**；写 a0.json / 两份 CSV；判定 `matching_qualified` |
| 确定性复核 | 连续两次运行，`Get-FileHash` 比较 | 三份产物 SHA256 **逐字节相同**（a0.json `72BBAF6D…ECA22`；条件 CSV `73FD5085…153FF`；四元组 CSV `881A0DFC…1CCF9`） |

单命令均远低于 15 分钟上限；无大数据下载；内存峰值 < 2 GB（pandas 仅读 20 个元数据列，响应列不进入内存）。

## 4. 观测（数字均来自 a0.json）

- **结构**：Original 296,707 行（剔除复合合并行 5,527 → 有效 291,180），125 细胞 / 1,975 有向药对 / 1,269 无序药对 / 4,528 条件 / 3,106 板；Validation 23,505 行（剔除 158 → 有效 23,347），97 细胞 / 130 有向对 / 98 无序对 / 295 条件 / 454 板。每细胞条件数 Original 576/1,299/2,550（min/median/max），Validation 76/102/118。
- **端点存在性**：两文件 `SYNERGY_DELTA_EMAX/AUC/fAUC/XMID` 空值均为 **0**（仅存在性计数，未读数值）。
- **重叠**：细胞 96（原 125 / Val 97）；有向药对 130/130；cell×condition 键 Original 211,504 / Validation 9,649 / 共同 **9,154（Validation 键的 94.87%）**；barcode 集合**交集 0**（原 14,482–39,392；Val 33,044–63,257）。
- **剂量可比性**：anchor 浓度水平 26 vs 20，共同 20；`LIBRARY_CONC` 水平 12 vs 11，共同 10；127 个共同有向药对存在多个共同设计元组；完整 library 浓度点集不可得（拟合表只发布最高浓度）。
- **四元组**：R4（两主组共同）= **6,223,367**；R3 半匹配 = 802,445；复制水平 R0 4,034,637,772 / R1 177,515,510 / R2 214,664,684 / R3 802,445 / R4 6,223,367；G1-only 4,415,971,041；G2-only 7,301,337；barcode 分半 R4 = 43,208,857（31,019 键参与）。
- **分层/覆盖**：controlled_anchor 92,039；same_anchor_any_conc 568,029；same_library 309,351；disjoint_pairs 5,345,987；same_tissue 6,217,553 / cross_tissue 5,814。R4 涉及 96 细胞（Breast 33 / Colon 35 / Pancreas 28）、291 条件、98 有向药对、31 anchor、38 library、3,418 细胞对。细胞 degree 33,814 / 128,333 / 165,672（min/median/max）；有向药对 degree 39,733 / 90,997 / 353,268。
- **图结构**：匹配复制子图节点 387（96 细胞 + 291 条件）、边 9,154、4-回路 6,223,367。
- **判定门槛**：R4≥500 ✓；两独立组 ✓；各组可独立构成 ≥500 四元组 ✓；覆盖 ≥10 细胞/≥10 药对 ✓；端点可用 ✓ → `matching_qualified`。

## 5. 决定与理由

1. **冻结前只做元数据侦察**：BRIEF 允许侦察后写死门槛；侦察仅使用身份/方向/剂量设计/端点存在性，无响应值参与。门槛按 BRIEF 默认 500 冻结（未因实测巨大而调整——上调会改变资格语义、下调不必要）。
2. **主独立组 = Original vs Validation 两文件**（而非只用 barcode 分半）：两者 barcode 集合不相交、为两次独立筛；barcode 分半作为次级敏感性（拟合表无板日期，独立性弱）。
3. **剂量匹配口径**：以 `ANCHOR_CONC` + `LIBRARY_CONC`（最高浓度）+ 有向药对作为条件元组；完整 library 浓度点集无法从拟合表获得，如实作为限制而非用假设补齐。
4. **宽定义为主、受控分层为报告项**：主四元组允许 p、q 为任意不同药对（ΔEMAX 归一化端点可比），同时报告 `controlled_anchor`（同 anchor/同剂量、仅 library 不同，92,039 个）供 A1 选择更受控的子设计；不把任一分层当主门槛。
5. **响应盲**：端点仅做存在性检查；匹配/分层/去重不使用响应值；Q 与效应全部留给 A1。
6. **实现 QC（已修正并完整重跑）**：`count_levels` 用 defaultdict 下标访问 `a1[c]`/`a2[c]` 会为缺失细胞创建空条目，污染重叠统计（一度显示 cells=126/126/126）；改为 `.get(c, set())`，重叠统计只计非空键集合；修正后重跑并复核确定性。另修正侦察脚本中浓度的字符串化口径（改用 `format(float,'.10g')`），最终共同键 9,154 由独立 verify 脚本交叉确认。
7. **CSV 上限**：R4=6.22M > 冻结上限 200,000 → `matched_quadruples.csv` 写字典序前 200,000 行（a0.json 记录完整计数；A1 可重生成全表）；`matched_conditions.csv` 含全部 9,154 双组可用键，供 A1 重建。

## 6. 预算

- 计算：侦察 ~15 s + 最终 a0.py 26–35 s ×3（含一次确定性复核）；总 wall 约 3–4 分钟（不含书写）。
- 无新增下载；无 GPU；无湿实验；未读取任何响应数值。
- token/费用：运行时不可得，[usage.json](usage.json) 记 `null`（不记 0）。

## 7. 局限

- 匹配资格 ≠ Q 稳定/可迁移：Q 的存在、大小、方向、可比性全部是 A1 的问题；本审计不做任何条件结构主张。
- 剂量匹配只到已发布设计列（`ANCHOR_CONC`、`LIBRARY_CONC` 最高浓度）；拟合表无完整 library 浓度点集，本机无 Validation raw 板布局 → 孔级剂量等价不可验证。
- Original 重复板无日期/批次元数据 → barcode 分半独立性弱于跨 screen；主独立组使用跨 screen。
- "独立测量组"与 screen/批次完全混淆：A1 只能主张跨 screen 条件稳定性，不能主张纯 test–retest 可迁移性。
- 匹配四元组高度嵌套冗余（6.22M 来自 9,154 键），不是独立样本量；A1 必须按细胞/药对聚类并报 MDE。
- 匹配宇宙仅覆盖 Validation 的 98 无序药对（130 有向）/96 细胞（原筛 1,975 有向 /125 细胞）；跨组织匹配稀少（same_tissue 6,217,553 vs cross_tissue 5,814），实际可检验范围主要是同组织细胞对。
- 单药参照列存在但按 A0 协议 DENY（未读数值）；H193b 的 adjusted Q 需 A1 显式解禁并冻结用法。
- 文本/ID 归一匹配不证明生物学同一实体；未联网、未引入外部 ID 库。
