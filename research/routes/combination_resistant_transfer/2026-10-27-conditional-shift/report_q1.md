# R193-A1 独立执行报告：条件偏移 Q 的可复验性（design_check 先行）

2026-10-27。角色：**独立 runner**（不参与协议/挑战起草）。按已冻结的 [PROTOCOL_Q.md](PROTOCOL_Q.md)（v1 **FROZEN**，SHA256 `74FA675A…D1CF`）执行 R193 分析 A（H193a/H193b）。**严格按协议**：未改门槛/统计量/分层/判定；先做设计体检，体检未过即停，**未进入主 Q 复验计算**。A0 引用一律同时引用 [ERRATA_A0.md](ERRATA_A0.md) 与 [challenge_A0.md](challenge_A0.md)。

- 脚本：[q1.py](q1.py)；结果：[q1.json](q1.json)＋[q1_rows.csv](q1_rows.csv)（设计体检明细）
- 输入（只读，全部 SHA256 断言通过）：Jaaks Original/Validation fitted 表（`1188968C…`/`DCBD4C31…`）、A0 `matched_conditions.csv`（`73FD5085…`）、`matched_quadruples.csv`（`881A0DFC…`）、`a0.json`（`72BBAF6D…`）、协议、ERRATA、挑战全文
- 确定性：固定种子、JSON 键排序、无时间戳；连续两次运行 `q1.json` **逐字节相同**（见 §12）

## 0. 判定（一屏）

**`inconclusive`**（PROTOCOL_Q §6：design_check 未过 → 停，不救）。

| # | design_check 项（PROTOCOL_Q §3–4） | 实测 | 门槛 | 结果 |
|---|---|---|---|---|
| 1 | 主分层 `controlled_anchor` 四元组 | **92,039**（与 A0/ERRATA 一致） | ≥500 | **PASS** |
| 2 | 细胞对 cp（cp 需 ≥5 四元组） | **1,501**（96 细胞、291 条件；cp 四元组 6–134，中位 58） | ≥500 | **PASS** |
| 3 | barcode 分半可靠性覆盖率 | Original：**1,593** 个 ≥2-barcode 键 / **61** cp；Validation：8,974 / 1,501 | 每 screen ≥300 键、≥50 cp | **PASS**（Original 薄，披露） |
| 4 | rel 95% CI 下界 | Original **0.712**；Validation **0.662** | ≥0.20 | **PASS** |
| 5 | `rel_A` / `rel_B`（Spearman-Brown，点估计） | **0.864** / **0.741** | — | 报告 |
| 6 | `δ_min_obs = 0.10·sqrt(relA·relB)` | **0.0893**（保守上界口径）/ 0.0800（点估计口径） | — | 报告 |
| 7 | **`MDE80_obs ≤ δ_min_obs`** | **MDE80_obs = 0.2042**（保守上界口径 0.0893） | 要求 ≤ δ_min_obs | **FAIL** |
| 8 | 完整规则 joint power（latent 0.30） | **0.896** | ≥0.80 | **PASS** |
| 9 | 完整规则 type-I（置换零数据模拟） | **0.018** | ≤0.10 | **PASS** |

**唯一失败项是 MDE 门槛。** 另一句话：这个设计对"latent ρ=0.30"有功效（0.896），对"latent ρ=0.10"（δ_min 所在）只有 **0.174**——即**它无法分辨协议设定的最小有用条件偏移**。原因不是四元组不够（92,039 个、1,501 cp），而是 **1,501 个 cp 只来自 96 个细胞、有效独立样本 n_eff≈189**（cell-cluster bootstrap 的 SE 是 iid 的 ~2.8 倍）。

**因此：不进入主 Q，不报告主统计量/CI/H193b/选择偏差/次级统计量（协议 §7 明令禁止在体检未过时进入 Q 复验）；本报告不写任何"条件结构可复验/不可复验"的主张；B/C 不启动。**

## 1. 执行顺序与输入断言

`q1.py` 顺序 = PROTOCOL_Q §7：加载 → 断言输入/A0/ERRATA 事实 → **设计体检** → 若通过才进入主/次统计与 H193b。本轮流程日志：

```
[1] hash inputs + assert A0/ERRATA facts
[2] load fitted tables (A0 validity rule)   orig 291,180 valid / val 23,347 valid  ✓ 与 A0 一致
[3] matched keys / rep2                     cells 96 / conditions 291 / keys 9,154 (set-equal) /
                                            directed pairs 129 (ERRATA_A0) ✓
[4] controlled_anchor quadruples            92,039 / cp 1,501 / R4 full 6,223,367 (matches A0) ✓
[5] design check ...                        design_check_passed=False (MDE gate)
    PROTOCOL_Q section 7 gate: STOP - no cross-screen Q statistic is computed
```

- A0/ERRATA 断言：`disjoint_pairs` 更正口径 **4,612,633**、G1/G2-only M3 **4,412,540,421 / 7,234,325**、条件级有向药对 **129**、barcode-split R4 覆盖 46 细胞/583 cp 均作为 ERRATA 事实记录并核对（`q1.json → structure.errata_facts`）。
- 独立复算的关键计数全部命中 A0：Original 有效行 291,180、Validation 有效行 23,347、共同细胞 **96**、共同 cell×condition 键 **9,154**（与 `matched_conditions.csv` 集合完全相等）、R4 全量四元组 **6,223,367**、`controlled_anchor` **92,039**、细胞对 **1,501**。
- 单药列（H193b 用）实测**两表 7 列均无缺失、无 0 值**（Original/Validation 各自检查），与挑战 §附录 B 的"空值 0、无非数值哨兵"一致；H193b 在主路径未被执行（设计体检未过），此检查仅记录可用性。

## 2. 设计体检细节

### 2.1 可靠性（within-screen barcode 分半，先于任何跨 screen 对齐）

| screen | ≥2-barcode 键 | 分半可用 cp | 分半相关 r | Spearman–Brown `rel` | rel 95% CI | bootstrap SE(r) |
|---|---|---|---|---|---|---|
| Original (A) | 1,593 | **61** | **0.760** | **0.864** | [0.712, 0.984] | 0.106 |
| Validation (B) | 8,974 | **1,501** | **0.588** | **0.741** | [0.662, 0.810] | 0.048 |

- 分半规则（A0 冻结）：每键 barcode 排序，first ceil(n/2) vs rest；Q 在主分层内按四元组计算、cp 级取 median；相关为 cp 级 Spearman。CI 为 **cell-cluster bootstrap**（重采样 96 细胞、重建 cp 集合，B=500）。
- **限制（必须随结论）**：Original 侧分半只覆盖 **61 个 cp**（36 个 barcode-rich 细胞），rel 的 CI 很宽（0.712–0.984），`rel_A_hi` 贴 1；Validation 侧覆盖全部 1,501 cp，估计稳定。
- 读法：Q 的同一 screen 内可复现性本身不低（0.74–0.86），说明端点拟合噪声并非主导；**主导不确定性的不是 Q 的噪声，而是细胞层面的有效样本量**（见 2.3）。

### 2.2 δ_min（latent）与 δ_min_obs

- 协议冻结：`δ_min_latent = 0.10`（operational：低于此值的条件偏移可复验相关解释方差 <1%，不足以支持"用少量反馈改选未测组合"的后续实验）。
- `δ_min_obs = 0.10 · sqrt(relA·relB)`；按 **保守方向**（rel 上界，Lead 实现备注 2）取 `rel_A_hi=0.984`、`rel_B_hi=0.810` → **δ_min_obs = 0.0893**；点估计口径 = **0.0800**。
- 两个口径都远低于 MDE80_obs（0.152–0.204），**判定对 rel 界的选择不敏感**（`q1.json → judgment.reliability_uncertainty_note`）。

### 2.3 MDE80_obs（cell-cluster 结构；多种构造，主判定用主构造）

| 构造 | SE_null | **MDE80_obs** | 与 δ_min_obs=0.0893 比较 |
|---|---|---|---|
| **主：经验 cluster-adjusted**（Validation 分半可靠性 r=0.588，bootstrap SE=0.0476 → `n_eff=((1−r²)/SE)²=189.2`，`SE_null=1/√(n_eff−1)`） | 0.0729 | **0.2042** | **FAIL** |
| 去偏经验（用同 cp 结构的 iid 校准因子 0.875 校正 bootstrap 的 cp-set 收缩偏差） | 0.0544 | **0.1523** | FAIL |
| iid 解析（1/√(n_cp−1)，**忽略细胞聚类**，仅参考、不作门槛） | 0.0258 | 0.0723 | （若误用会"通过"） |
| 零模型 cell-share 0.00 / 0.25 / 0.50 / 0.75（悲观依赖界；见结构性 caveat） | 0.027–0.105 | 0.076 / 0.264 / 0.279 / 0.294 | 0.25+ 全 FAIL |
| Original 侧分半（61 cp，覆盖薄） | 0.2594 | 0.7267 | FAIL（覆盖不足，仅敏感性） |

- **主构造不含任何跨 screen Q 对齐**：`n_eff` 由 **within-screen barcode 分半可靠性** 及其 cell-cluster bootstrap SE 推出（这是"体检阶段允许读 y"的两项用途之一），与主统计量无关。
- **关键量**：名义 1,501 个 cp，但细胞聚类下 **n_eff≈189**（bootstrap SE 是 iid 的 ~2.8 倍）。也就是说，96 个细胞、1,501 个共享细胞的 cp 给出的独立信息量远小于名义 n。
- 结构性 caveat（写入 `q1.json`）：零模型的"cell-additive share"不是 Q 的忠实结构（加性 cell 主效应在 2×2 双差中**精确抵消**），只能作为**悲观依赖界**；主锚点是经验值 0.2042 与其去偏值 0.1523。
- **结论的稳健性**：除"完全忽略细胞聚类的 iid 解析"外，**所有考虑聚类的估计（经验、去偏经验、零模型 share≥0.25）都 > δ_min_obs（0.080–0.089）**；原始经验 bootstrap SE 已被 iid 校准证明不是抽样假象（iid 数据上该 bootstrap 的膨胀仅 1.36×，而实测为 2.8×）。

### 2.4 完整规则 joint power 与 type-I

完整判定规则（点 ≥ δ_min_obs ∧ cell-cluster CI 下界>0 ∧ 高于置换零分布 95 分位）在正态近似下等价于 `ρ̂ > max(δ_min_obs, 1.96·SE)`（置换 95 分位 = 1.645·SE 更弱、被 CI 条件覆盖）。2,000 次 MC：

| latent ρ | 观测尺度均值（×√(relA·relB)） | 完整规则拒绝率 | 门槛 |
|---|---|---|---|
| 0.00（type-I，置换零数据模拟） | 0 | **0.018** | ≤0.10 ✓ |
| **0.10（= δ_min）** | 0.0800 | **0.174** | 只报告 |
| **0.30** | 0.2399 | **0.896** | **≥0.80 ✓** |

- 主门槛（power@latent 0.30）通过；**但 power@latent 0.10 只有 0.174** —— 这正是 MDE 门槛失败的另一面。

## 3. 判定、停止与"未计算"清单

**判定：`inconclusive`**（PROTOCOL_Q §6：design_check 未过）。按协议：

- **主 Q 未计算**：`Spearman(Q_A^cp, Q_B^cp)`、cell-cluster CI、置换零分布 — **均未运行、未落盘**（`q1.json → judgment.main_q_computed=false`、`response_value_use_attestation.cross_screen_q_alignment_computed_before_design_check=false`；`q1.py` 在写入前有硬断言）。
- **H193b 单药交叉拟合调整未运行**——协议规定设计体检未过不得进入 Q 复验，H193b 是 Q 的解释项，随之停；单药列可用性已核验（§1），不是"不可用"。
- **选择偏差诊断（matched/unmatched 元数据比较、Original 内随机子集对照、回归到均值）与 barcode 分半主判定对照未运行**——同上，属主分析阶段；仅在此记录"未运行原因"，不替代。
- **次级统计量（条件对级、四元组级双向聚类、其它分层、三个端点）未运行**。
- 未写"reproducible/not_reproducible"；未写"条件结构存在/不存在"；B/C 不启动；冻结的普通加性/静态先验解释**不受影响**。

`q1_rows.csv` = 设计体检完整明细（11 个 gate 的 value/threshold/pass、reliability 与 MDE 各构造）；主分析行表**因协议停止而不存在**（不是漏交）。

## 4. 功率语义（必读，Lead 实现备注 3）

即使未来设计体检通过（或换更大的独立 cell 数），**本设计的完整规则只要求 latent ρ=0.30 处 power≥0.80，而 reproducible 阈值落在 latent≈0.10（真值 = δ_min 处通过率约 50% 是构造性的）**。因此：

> **0.10–0.30 区间的 latent 效应不能被本设计可靠分类**（本数据上 power(0.10)=0.174 vs power(0.30)=0.896）。任何未来的 `not_reproducible` 结果都**不能**被读成"该区间没有条件结构"——它只说明本设计分辨不了。

## 5. 为什么是 `inconclusive` 而不是 `not_reproducible`（避免误读）

- 体检失败的原因是**有效样本量/聚类**（n_eff≈189 from 96 cells），不是 Q 不变化、不是端点噪声大（rel 0.74–0.86）、不是四元组太少（92,039）。
- 若强行用 iid 解析 MDE（0.072 ≤ 0.089）"通过"体检并跑主 Q，将违反协议（§3 要求用聚类结构）且会给出**过窄 CI / 过高功效**的误导性结论——R192 的教训（pre-flight MDE 与 realized SE 可差 2 倍以上）正适用于此。
- 因此按协议 §6/§7 记录 `inconclusive` 并停，是**设计的限制结论**，不是"条件偏移不存在"的证据。

## 6. 敏感性汇总（不改主判定，只作稳健性披露）

| 不确定源 | 变化 | 对判定影响 |
|---|---|---|
| rel 界（点估计 vs 保守上界） | δ_min_obs 0.0800 → 0.0893 | **不影响**（MDE 0.152–0.204 均 > 两者） |
| MDE 构造（经验 / 去偏 / 零模型 share≥0.25） | 0.152–0.294 | **不影响**（全部 FAIL） |
| MDE 构造（iid 解析） | 0.072 | 仅此一个"通过"，但它忽略已证实的细胞聚类，协议不允许作门槛 |
| Original 分半覆盖（61 cp） | rel_A CI 宽 [0.712, 0.984] | 保守方向已用（rel_hi），不影响判定 |
| 多重性 | 主门槛为单一 design gate | 不涉及 |

## 7. 协议偏离 / 实现选择（全部披露，无协议修改）

协议文本未逐字规定、由 runner 预注册的实现选择（写在 `q1.py` 头注释与 `q1.json → pre_registered_implementation_notes`）：
1. 可靠性覆盖率门槛：每 screen `≥300` 个 ≥2-barcode 键、`≥50` 个分半可用 cp、rel CI 下界 `≥0.20`（Lead 实现备注 2 要求 runner 预注册；本轮全部通过，Original 侧"薄"已披露）。
2. `δ_min_obs` 用 rel 上界（保守方向）；点估计口径同时报告。
3. `MDE80_obs` 主构造 = 由 within-screen 分半可靠性的 cell-cluster bootstrap SE 推 `n_eff`；另报去偏/iid/零模型敏感性。
4. `q1.py` 运行时 gate：体检未过 → STOP，并在写盘前断言无跨 screen Q/主统计量；**本 runner 版本只实现"体检+停止"分支，若体检通过会显式 `SystemExit` 要求换经修订的 runner**（不静默跳过主分析）。
5. `controlled_anchor` 内 p,q 定向按 library_id 升序（协议未写死定向；对 cp 级 median 的符号一致性必要，已披露）。
6. 主路径未执行，故未实现主统计量/H193b/次级统计量的代码路径（见 4）。

**无协议门槛/统计量/分层/判定被修改；无 Q 调参或事后择优。**

## 8. 与 R193-A0 的关系（必须同时引用 ERRATA 与挑战）

- A0 资格判定 `matching_qualified` 与四道 gate 不受本报告影响；本报告**复算命中** A0 的 9,154 键、96 细胞、129 条件级有向药对、92,039 controlled_anchor、6,223,367 R4。
- 本报告采用 **ERRATA_A0.md** 的更正口径（disjoint_pairs 4,612,633、G1/G2-only M3 4,412,540,421/7,234,325、条件级有向药对 129、barcode-split 覆盖 46 细胞/583 cp）与 **challenge_A0.md** 的必改 1–5（尤其"单药列可用→H193b 必做"与"Validation 选择偏差须预注册"）。
- 本报告不重开 A0 资格，也不改 PROTOCOL_Q。

## 9. 复现

```powershell
cd D:\MAESTRO
$env:PYTHONHASHSEED="0"
& D:\anaconda\envs\maestro\python.exe research\2026-10-27-conditional-shift\q1.py
```

- 实测耗时 **59–70 s**；连续两次运行 `q1.json` 与 `q1_rows.csv` 均**逐字节相同**（`q1.json` SHA256 见 [usage_q1.json](usage_q1.json)）。
- 输入/协议/ERRATA/挑战/脚本 SHA256 全在 `q1.json → inputs / protocol / errata / challenge / script`。

## 10. 边界

- 本报告**不**主张条件偏移可复验或不可复验、不主张可迁移、不主张机制，不晋升代码、不启动 B/C；阴性/不确定性同样完整记录。
- 条件偏移 ≠ 机制；跨 screen 只说明 screen 间稳定性；screen 与批次完全混淆（A0/ERRATA 已披露）。
- 结论限定在 matched 子集与该 Validation 子集。
