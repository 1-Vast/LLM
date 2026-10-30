# record_q1 —— R193-A1 独立执行过程记录（时间线 / 纪律 / 实现备注 / 偏离 / 局限）

2026-10-27。角色：**独立 runner**（不参与 PROTOCOL_Q/挑战起草）。工作目录 `D:\MAESTRO`；解释器 `D:\anaconda\envs\maestro\python.exe`（Python 3.11.16 / numpy 2.4.6 / pandas 2.3.3 / scipy）。本文件记录**过程**；判定与数字见 [q1.json](q1.json) 与 [report_q1.md](report_q1.md)。

## 1. 范围与纪律

- 只写 `research/2026-10-27-conditional-shift/`（新增 `q1.py / q1.json / q1_rows.csv / report_q1.md / record_q1.md / usage_q1.json`）与 `tmp/`；**未改** PROTOCOL_Q/A0 产物/ERRATA/challenge/其它目录/INDEX/SYNTHESIS/git。
- 严格按 `PROTOCOL_Q.md`（v1 FROZEN，SHA256 `74FA675A…D1CF`）执行；未改门槛、主统计量、分层、判定；未做 Q 调参或事后择优。
- **设计体检未过即停**：未进入主 Q、未计算任何跨 screen Q_A–Q_B 对齐、未写"可复验/不可复验"主张（`q1.py` 写盘前有硬断言；`q1.json → response_value_use_attestation`）。
- A0 引用一律同时引用 [ERRATA_A0.md](ERRATA_A0.md) 与 [challenge_A0.md](challenge_A0.md)；本执行复算命中 A0 的 9,154 键 / 96 细胞 / 129 条件级有向药对 / 92,039 controlled_anchor / 6,223,367 R4。

## 2. Lead 三条非阻塞实现备注的落位（不改协议，不影响执行）

**备注 1｜design-check 数据顺序必须写清。** 已按此实现并在 `q1.py` 落运行 gates：
- 体检阶段只读 `y` 用于 (i) **within-screen barcode 分半可靠性**（同 screen 内两半、不做跨 screen 对齐）与 (ii) **由 n_p/零模型/解析构造估 SE**（含主构造：用分半可靠性的 cell-cluster bootstrap SE 推 `n_eff`，仍不涉及跨 screen）。
- **绝不计算或保留真实 Q_A–Q_B 对齐**：体检函数只产生 per-screen 的 `Q_half1/Q_half2` 与 cp 级值；跨 screen 统计量在代码里位于 gate 之后。
- `q1.py` 在写盘前断言：`response_value_use_attestation.main_q_computed is False` 且输出中不存在 `main_analysis`；体检未过分支显式打印 "PROTOCOL_Q section 7 gate: STOP - no cross-screen Q statistic is computed"。

**备注 2｜rel 的不确定性与覆盖门槛。** 在 `q1.py` 内预注册（写在此处，先于执行）：
- 覆盖/rel 门槛：每 screen 要求 `≥300` 个 ≥2-barcode 的 matched 键、`≥50` 个 barcode-split 可用 cp、rel 95% CI 下界 `≥0.20`；任一不满足 → 该项 gate fail（本数据全部通过；Original 侧仅 61 cp 属"薄"，已作为限制披露）。
- `δ_min_obs` 用**保守方向 rel 界**（rel 上界；rel 高 → δ_min_obs 高 → 主判定更难通过）计算：`δ_min_obs = 0.10·√(rel_A_hi·rel_B_hi) = 0.0893`；点估计口径 0.0800 同时报告。
- `q1.json` 记录 rel 点估计/CI/上界、两种 δ_min_obs、MDE 主构造与全部敏感性；`judgment.reliability_uncertainty_note` 说明两口径下判定不变。**未新增改变主判定的数字。**

**备注 3｜power 目标语义。** 报告 §4 已写死："**0.10–0.30 区间的 latent 效应不能被本设计可靠分类**（本数据 power(0.10)=0.174 vs power(0.30)=0.896）；未来 `not_reproducible` 不能读成该区间无结构。" 同句写入 `q1.json → judgment.power_semantics_note`。

## 3. 时间线与运行

| 步骤 | 内容 | 结果/耗时 |
|---|---|---|
| 读协议/ERRATA/挑战/A0 | 冻结口径、必改 1–5、A0 计数 | — |
| 结构探针（`tmp/a1_probe.py`） | 只读身份/元数据：valid 行数、96 细胞、9,154 键、92,039 四元组、1,501 cp | 与 A0 全部一致 |
| 设计探针（`tmp/a1_design_probe.py`） | **仅结构**（无响应值）：n_p=1,501 下不同 cell-share 零模型的 SE/MDE 量级 | 用于确认 pipeline 可行性 |
| within-screen 探针（`tmp/a1_rel_probe.py`） | **只读同 screen 分半**：relA/relB 与 cell-bootstrap SE（**无跨 screen 对齐**） | relA≈0.86（61 cp）、relB≈0.74（1,501 cp） |
| `q1.py` 首次运行 | 实现后按 §7 顺序执行 | 5 s 内在 [2]–[4] 后因 cond_full 索引 bug 失败（实现 bug，非数据） |
| `q1.py` 修正后运行 | 逐 bug 修正（cond_full 索引、zero-model 数组尺寸、最终 runtime gate） | 59–70 s；design_check=False（仅 MDE gate） |
| 确定性复核 | 连续两次运行比较 SHA256 | `q1.json` 两次**逐字节相同**（见 §8）；`q1_rows.csv` 相同 |

> 探针均在**设计体检阶段**运行，只涉及结构/within-screen 可靠性；**任何探针都没有计算或保存跨 screen Q_A–Q_B 统计量**，也未影响协议门槛（门槛来自冻结协议文本）。

## 4. 判定与停止（复述）

- **判定：`inconclusive`**，唯一失败 gate = `mde80_obs_le_delta_min_obs`（MDE80_obs=0.2042 > δ_min_obs=0.0893；10/11 gates 通过）。
- 主 Q / H193b / 选择偏差 / 次级统计量**均未运行**（PROTOCOL_Q §7 禁止体检未过进入 Q 复验）；`q1_rows.csv` 只含设计体检明细。
- 未写条件结构结论；B/C 不启动；A0 资格与冻结解释不受影响。

## 5. 实现选择 / 偏离（全部披露；无协议修改）

1. **可靠性覆盖率门槛**（runner 预注册，见 §2 备注 2）。
2. **δ_min_obs 用保守 rel 上界**；点估计口径并列报告。
3. **MDE80_obs 主构造**：within-screen 分半可靠性 → cell-cluster bootstrap SE → `n_eff=((1−r²)/SE)²` → `SE_null=1/√(n_eff−1)` → `MDE80=2.801585·SE_null`。另报去偏经验（iid 校准因子 0.875）、iid 解析（仅参考）、零模型 cell-share 0/0.25/0.5/0.75（**结构性 caveat**：加性 cell 主效应在 Q 双差中精确抵消，故该族只是悲观依赖界）。
4. **`q1.py` 运行时 gate**：体检未过 → STOP + 写盘前断言；**本 runner 版本只实现"体检+停止"分支，若体检通过会显式 `SystemExit`**（要求经修订的 runner；不静默跳过主分析）——这是为了不让未实现的主路径产生半成品输出，已在报告 §7 披露。
5. `controlled_anchor` 内 p,q 定向：按 library_id 升序（协议未写死定向；cp 级 median 需要一致符号；已披露）。
6. 单药列可用性核验：两表 7 个单药列**无缺失、无 0 值**（与挑战附录 B 一致）；H193b 未执行（体检未过）。

## 6. 响应值/模型保护复核

- `q1.py` 在设计阶段只读主端点 `SYNERGY_DELTA_EMAX`；用途 = within-screen barcode 分半可靠性、结构 SE 构造。
- **没有** identity/annotation 模型、没有 Q_A–Q_B 对齐、没有主统计量、没有 H193b 拟合、没有次级统计量。
- grep 复核（`tmp/q1_grep_audit.txt`；模式 `ridge|sklearn|fit\(|predict|coef|train\(|gain|通路−identity`）：`q1.py` 1 处、`q1.json` 1 处（均为边界措辞 'algorithmic gain'）；`q1_rows.csv` / `report_q1.md` 0 处；`record_q1.md` 的命中为自指审计文本。**没有** ridge/sklearn/fit(/predict/coef/train( 形式的模型拟合；唯一数值相关计算是可靠性分半与 SE 构造中的 Spearman 相关，无响应模型、无跨 screen 对齐。

## 7. 产物（SHA256 见 [usage_q1.json](usage_q1.json)）

| 文件 | 说明 |
|---|---|
| `q1.py` | 独立 runner（确定性、固定种子、JSON 键排序、无时间戳、运行时 gate） |
| `q1.json` | 输入 SHA、结构、design_check 全部数字、judgment=`inconclusive`、边界声明 |
| `q1_rows.csv` | 设计体检明细（11 gates + reliability + MDE 各构造） |
| `report_q1.md` / `record_q1.md` / `usage_q1.json` | 报告 / 本文件 / 运行时账 |
| `tmp/a1_probe.py`、`tmp/a1_design_probe.py`、`tmp/a1_rel_probe.py`、日志 | 只读探针与运行日志（不入正式交付） |

## 8. 局限与后续（解冻条件）

- 体检失败的本质：**96 个细胞 → n_eff≈189**（cell-cluster bootstrap SE 是 iid 的 ~2.8 倍），在 1,501 个 cp 上无法达到 latent 0.10 的检定力（power 0.174），即使四元组有 92,039 个。Original 侧 barcode 分半只覆盖 61 cp（rel CI 宽），是可靠性估计的薄点（保守方向已用）。
- 后续若要重开 A1：① 更大的独立细胞数/独立测量组；② 有 operational 理由的更小 `δ_min_latent`（协议禁止用旧 CI 反推）；③ 有效独立样本更大的分析单元（不是把同一 96 细胞换聚合方式）。以上都不是本 runner 能决定的；B/C 不启动。
- 条件偏移 ≠ 机制；跨 screen 只说明 screen 间稳定性；screen 与批次完全混淆（A0/ERRATA 已披露）；结论限定 matched 子集与该 Validation 子集。
