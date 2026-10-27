# record_p0a_check — R199-A1v4.1 批准后 P0a relations_check 运行记录

2026-10-27。依据 Lead 批准文件 [APPROVAL_P0A_CHECK.md](APPROVAL_P0A_CHECK.md)（P0a-metadata PASS + 输出 SHA `338A234E…F58247` 冻结；two-key；Lead 批准）。**只运行 `relations_check.py --confirm-run`（P0a relations_check；参考 A/B 响应可读、≤30 min）；未运行 P0b/P0c/P0d、未进入 Stage 1。**

## 0. 判定

**`p0a_relations_check_fail` → `data_unavailable`（stop）**：最终冻结输出 `status=data_unavailable`，`reasons=["R_below_min","coverage_below_min"]`；`accepted_relations=2 < R_min=20`，`coverage=2/171=1.17% < 86/171`。按批准与协议：**不降分母/不加回 Pancreas/不改 S 大小/不放宽 α**；本批准窗口内不重试、不改判据。该结果**不是**"关系不存在"的证据，只是冻结协议下资格门未通过、按 `data_unavailable` 停。

## 1. 批准窗口与 gate

| 项 | 值 |
|---|---|
| 基线 config SHA（`real_run_enabled=false`） | `BB1FE3230B70EB53B5A39EF7D7D37DF256F296E866133939881E0E3E909CF9B4` |
| 窗口 config SHA（仅 `real_run_enabled=true`，其它键未改） | `B60CC8D0E8B567322F831DA3E8D83A11B1042A617B4AC36D95A68A890803D946` |
| 回写后 config SHA | `BB1FE3230B70EB53B5A39EF7D7D37DF256F296E866133939881E0E3E909CF9B4`（逐字节还原） |
| 默认 / 仅 `--confirm-run` | 运行前与回写后均 exit 3 `refused` |
| 命令 | `relations_check.py --confirm-run`（full 路径 = 内部 P0a-metadata + 参考 A/B 的 relations_check；未跑其它阶段） |
| 预算 | 30 min；最终有效运行 **6.8 s**（CPU 单进程≈wall） |

## 2. 执行期实现修正（须 Lead 复核）

本批准窗口内发现 2 个与冻结协议不一致的实现点，修正后重跑（**阈值/分母/分配/α 未改**）：

1. **候选集未与 P0a 冻结网格联动**：首次运行从 fitted 条件 union 枚举出 **27,600** 个候选并截断到 200；与 `s_milp_optimum=106/网格 171` 的 P0a 冻结候选集不一致。修正：把 P0a 的 `_candidate_keys`（171 网格 key，浓度 canonical）传入 relations_check，候选集限定为 P0a 网格；有效候选 135（A/B 各≥12 的 P0a supply）。
2. **多重比较层与冻结协议不一致**：原实现把 BH q≤0.10 直接施于全部 tested relations（135），与"每关系 α=0.01；primary 族≤10；primary 族内 BH q≤0.10；exploratory 仅报告"不符（过严）。修正：① 每关系精确单侧符号检验 **α=0.01** 过门；② accepted 按预注册排序取 primary ≤10；③ **primary 族内 BH q≤0.10**；exploratory 保留报告；旧"全 tested 族 BH"降为 **sensitivity only**（`strict_full_family_bh_pass_sensitivity`）。
- 连同 P0a-metadata 批准窗口内 3 个 loader/枚举修复，本轮 A1v4.1 实现累计 **5 个执行期修正**；`relations_check.py` SHA 由冻结的 `90CC80BB…` → `88ACAFD2…` → 本次最终 **`0694A4F3…0B2E`**。逻辑链无设计变更（分配/分母/α/阈值/覆盖目标均未动）。

**中间运行（同判 data_unavailable，均被覆盖，不冻结、不引用）**：
- Run A（未联动 P0a 网格）：candidates 27,600→truncated 200；accepted 82；coverage 0.41；`relations_check.json` `CD928731…`、`relations.csv` `F16F22E9…`、splits `C36C9E5B…`；wall 9.8 s。
- Run B（已联动网格、全族 BH 过严）：candidates 135；alpha 过门未实现；accepted 2（全族 BH）；`relations_check.json` `5BB2AFED…`、`relations.csv` `89531F12…`、splits `C36C9E5B…`；wall 6.9 s。
- Run C（最终协议层）：见 §3；`relations_check.json` `9AE302B8…`；wall 6.8 s。

## 3. 最终运行结果（冻结）

| 指标 | 值 |
|---|---|
| status | **`data_unavailable`**（`R_below_min`, `coverage_below_min`） |
| candidates_evaluable / tested | **135 / 135**（P0a 网格 171 中 A/B≥12 的 supply） |
| **alpha_pass（α=0.01）** | **17** |
| accepted relations（α + direction/swap/interval/|μ| 全过） | **2**（Breast 2 / Colon 0） |
| R_min / R_max | 20 / 200 → **R=2 < 20**（fail） |
| coverage | **2/171 = 1.17%** < 86（fail） |
| primary family | **2**（≤10 ✓）；primary BH q≤0.10 通过 **2** |
| exploratory | 0 |
| 拒绝原因（首因） | `alpha_not_significant`:118、`direction_agreement_B_low`:9、`swap_check_failed`:6 |
| sensitivity（旧全族 BH） | `strict_full_family_bh_pass_sensitivity=20` |
| 已接受关系 n_ctx | n_A=13、n_B=12（均 ≥12）；p=0.00024414（k=12 单侧）；direction_agreement=1.0；swap=1 |
| accepted 的区间/|μ| | 2σ_r 宽度门与 |μ|≥0.5σ_r 均通过（relation CSV 已冻结） |
| 分组 | accepted_by_group = {Breast: 2}（Colon 0） |

**设计体检（按冻结规则逐项）**：n_ctx≥12（所有 tested 候选 A/B 各≥12 才可评估）✓；α=0.01 已作为逐关系门（17 过）✓；primary≤10（2）✓；primary BH q≤0.10（2 过）✓；区间宽度仅 2.0σ_r（P0a；utility 在 P0d）✓；|μ|≥0.5σ ✓；A/B 半分离+交换（方向一致率≥0.90、swap）已执行 ✓；R∈[20,200] **fail**；覆盖≥86/171 **fail**；失败分类 = **`data_unavailable`**（不是 design_invalid/blocked）。
- **S/U 响应**：P0a 阶段只用 S 的元数据（Cond_r 覆盖预检）；relations_check 的响应读取只传入 `splits["A"] + splits["B"]` 给流式 loader（84 reference 细胞），**S/U 细胞响应从未进入 stream/内存/区间估计**。已接受关系的区间只由 B 参考细胞估计。
- 运行内部用的 P0a 结果仍为冻结的 `338A234E…`（未重写）；relation_splits.json 仅含 A/B/S/U 计数与 sorted-cell-list SHA（默认不写细胞名）。

## 4. 冻结输出（SHA256；sidecar 与文件一致）

| 文件 | SHA256 |
|---|---|
| `stage0/real_run/relations_check.json` | **`9AE302B8749CD992D3201E00E322C683486D6B4C1BFFC03163DA967BA1026552`** |
| `stage0/real_run/relations.csv` | **`89531F12A97F14BE564CDEA00E30AF13CF7E17FABEC81805DFB9714CDFC4FE1D`**（2 个 accepted 关系行 + 表头） |
| `stage0/real_run/relation_splits.json` | **`C36C9E5B6B183D89C4AFA35C5D36FF03DA96127353E5AF72A21B5C05D12723EF`** |
| `stage0/real_run/p0a_metadata.json`（既有冻结） | `338A234E931E11C27105952839BC69F9681D4D8516419B4B78D2F81C36F58247` |

最终代码/配置/自检 SHA：`relations_check.py` `0694A4F3B6206277240668D3CD2ED897AB7DFA4A419C832353FC079D5CDD0B2E`；`relations_check_config.json` `BB1FE323…CF9B4`（回写后）；`synthetic_selfcheck.py` `914CDFC61F0FDE140C0FA5623F7DB96972FA7F1EFB413788F216CB2D7BA21EE8`；`SELFCHECK.json` `3135ABACBD55AEB22DCF62F8DFE1F44306617705344E4BC78DB1FA2701BC7E0E`（16/16）；`README.md` `A6954E43…2E97E`。

## 5. 边界与下一步

- **`data_unavailable` 不是"关系不存在"的阴性结论**；只是冻结协议的资格门（R/覆盖）未过；不得降分母、不加回 Pancreas、不改 S 大小、不放宽 α。
- **relations_check 通过 ≠ 关系成立 ≠ Stage 1 ≠ 效果/迁移/决策**（本结果连"通过"都不是）。
- 本批准范围已用尽：不再重跑、不改判据；P0b/P0c/P0d 未运行；Stage 1 未进入。
- 交 Lead 复核本记录 + 3 个输出 SHA + 2 个执行期实现修正（另加 P0a-metadata 的 3 个 loader/枚举修正，累计 5 个）；由 Lead 决定是否重审协议/资源/是否继续 A1 线。

## 6. 局限

- 全流程只**一次**最终有效运行（Run C）；Run A/B 为执行期修正过程记录，均被覆盖不引用。
- CPU 未单独采样（单进程，wall≈CPU）。
- 未做 cluster bootstrap/置换敏感性（协议列为 P0b/P0c/后续 Stage 1 设计的一部分；本轮只做 Stage 0 关系资格）。
- 未读 S/U 响应；未运行 P0b/P0c/P0d；无新先例检索；不声称新颖性。
