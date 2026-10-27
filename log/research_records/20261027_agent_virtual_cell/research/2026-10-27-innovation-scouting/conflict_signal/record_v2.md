# record_v2 — R198-A1v2 修订过程记录（设计修订；无效果运行）

2026-10-27。角色：R198-A1 提案者（响应独立挑战 challenge_A1.md 的 5 必改）。**本轮只做规格/协议修订设计，不运行效果、不训练、不读响应做效果、不声称新颖性。** 原 A1 文件（spec.md/prior_art.md/protocol_draft.md/record.md/usage.json）**未改动**，修订全部以新文件呈现。

## 1. 范围与纪律

- 输入：`challenge_A1.md`（task-36 独立挑战，revise）、原 A1 五件、R198 record（A1/A2 挑战状态、C176/C177）、SYNTHESIS 相关 C 边界、R193/R194 产物引用（A0/A1 数字）。
- 只写 `research/2026-10-27-innovation-scouting/conflict_signal/` 下新增文件：`spec_v2.md`、`protocol_draft_v2.md`、`REVISION_A1.md`、`relations_check_design.md`、`record_v2.md`、`usage_v2.json`；**不改**原 spec/protocol/其它目录/INDEX/SYNTHESIS/git；未读任何 S/U 响应。
- 不做：运行 relations_check、constructive 体检、MDE 预检、任何 acquisition/训练/效果；不编造 δ_min 数值；不声称"三类已区分"。

## 2. 修订动作（对应挑战 5 必改）

| # | 挑战要求 | v2 落实 |
|---|---|---|
| 1 | 判据可成立（n_min/退出上限/注入体检） | [spec_v2.md](spec_v2.md) §3.1：n_ctx_min=12、α=0.01、BH q≤0.10、primary 族≤10；MDE=p1≥0.95 时 80% 功效（n=12：k≥11 p=0.00317；p1=0.95→0.882、0.90→0.659）；[protocol_draft_v2.md](protocol_draft_v2.md) P0b（注入体检：≥30/类、recall/precision≥0.80、type-I≤0.10）、P6（not_identifiable≤15%、ambiguous≤10%，超限 `design_invalid`）。 |
| 2 | 分类可证伪（第四解释/多解释/依赖 χ²/σ/d_rel） | spec_v2 §2(iv) 新增 `setup_error`；§3.3 多解释惩罚拟合替代顺序规则；§3.2 双层块置换/κ 膨胀（C174 ~10.33× 警示）+ σ 带内一致；§2(i) d_rel 降为描述量；protocol P4.1–P4.5、P6 `model_misspecified`。 |
| 3 | 关系集可执行（R_min/max/单位/Cond/半分离/S-disjoint/screen/lineage） | spec_v2 §4 + [relations_check_design.md](relations_check_design.md)：R_min=20/R_max=200、n_ctx=12、区间宽度≤min(2σ,0.10×效用范围)、|μ|≥0.5σ、覆盖≥50%、A/B 构造/校准半分离+交换、参考 84/S 24/U≈17 三元不交、screen/batch 进 nuisance、非重聚合 lineage、`relations_check.json` SHA 冻结；`data_unavailable` 判据。 |
| 4 | 机制对照补齐（投影核/区间 ridge/soft-penalty/P1 样本外/P2 主/M2 先例/释放集规模） | spec_v2 §5.1（四个必比对照与等价条件：等式+无激活才等价投影核；区间激活=QP 不等价）、§5.2（P1 样本外诊断增量、P2 主机制检验、释放集 |R|≤30 精确/否则贪心+LP 下界、60 s/单元、J_max=min(5,ceil(0.1|R|))）、§5.3（VOI/2602.05340/GoBOED/EVSI/ENBS+Poke&Strike 差异，Stage 2 必比 VOI 基线）。 |
| 5 | 协议可执行性（δ_min blocked/U/预算/类别/标题/Stage1 两类/A4/措辞） | protocol_draft_v2：标题 R198-A1；P0a–P0d 前置；δ_min 未定义→`blocked_by_utility_definition`；P6 失败类别（setup_error/model_misspecified/ambiguous_conflict/design_invalid/proxy_only/not_identifiable/completed_null/pass_to_stage2）；P8 墙钟与 bootstrap/置换次数；Stage 1 只判 (i)/(ii)/(setup)、(iii) 只 proxy；A4/A5 接口；spec_v2 §10 措辞模板。 |

## 3. 关键数字（写死在 v2；本轮不验证）

- **X_flip**：n_ctx_min=12；精确单侧符号检验 α=0.01；BH q≤0.10（primary 关系族 ≤10 条）；n=12 时 k≥11 的 p=0.00317、k=12 为 0.000244；功效：p1=0.95→0.882、p1=0.90→0.659；预注册 MDE=p1≥0.95 时 80% 功效。
- **退出上限**：`not_identifiable` ≤15% 反馈单元；`ambiguous_conflict` ≤10%；超限 → `design_invalid`（停）。
- **注入体检**：每类 (i)/(ii)/(setup) ≥30 单元、效应量≥MDE；recall ≥0.80、precision ≥0.80；置换零假判 (ii) ≤0.10；退出率 ≤上限。
- **关系集**：R_old∈[20,200]；每关系 n_ctx≥12；A/B 方向一致率 ≥0.90（交换复核）；区间宽度 ≤min(2σ_r, 0.10×效用范围)；|μ_r|≥0.5σ_r；覆盖≥50%；每 tissue ≥3 条；primary ≤10 条；A(42)/B(42)/S(24)/U(≈17) 三元不交（Jaaks 125 细胞）。
- **释放集**：|R|≤200；精确 |R|≤30（分支定界/LP，60 s/单元）；否则贪心+LP 下界；J_max=min(5, ceil(0.10|R|))。
- **预算/时间**：relations_check ≤30 min；体检 ≤20 min；MDE 预检 ≤15 min；Stage 1 每臂 ≤45 min、总 ≤2 h；bootstrap/置换 ≥2,000（固定 seed）。
- **δ_min**：必须由成本/效用定义，未定义 → `blocked_by_utility_definition`（不编造）。

## 4. 决定与理由

1. **保留 v1 最可信部分**：三类对照量（R_abs/C_conf/L_lev/O_rep）与确定性反例；只把"判据不可成立/不可证伪/不可执行"的部分重写，不改"关系冲突不是残差改名"的核心。
2. **X_flip 采用"高一致性、低 n"而非放宽 α**：n_min=12 + α=0.01 + MDE p1=0.95，明确"只检测接近确定性的关系翻转"；预期低于 MDE 就必须增大 n（P0c 模拟），不能用多重比较/阈值事后放宽。
3. **第四解释不并入三类**：`setup_error` 单列（含 model_misspecified/interval_miscalibrated），先重估再判类；否则噪声模型错误会被误归 (ii) 或 (iii)。
4. **关系集采用细胞级受控对比 + 收缩组均值**（不是单四元组区间），Cond_r 元数据化，构造/校准半分离；这是把"普通细胞异质性 vs 关系失效"分开的关键。
5. **S/参考 disjoint 采用同 screen 三元细胞切分**（参考 84 / S 24 / U 余），跨 screen 仅敏感性；避免 R193-A0 已登记的 screen 混淆。
6. **δ_min 保持 blocked**：没有成本/效用就不冻结；不借用 C136/旧 CI 数值。A5 修订前 Stage 2 不启动。
7. **不声称新颖性**：机制成分均有先例；v2 只提高"可判定性"。

## 5. 产物与审阅快照（SHA256）

| 文件 | SHA256 |
|---|---|
| `spec_v2.md` | 见 §6 写后哈希 |
| `protocol_draft_v2.md` | 见 §6 |
| `REVISION_A1.md` | 见 §6 |
| `relations_check_design.md` | 见 §6 |
| `record_v2.md` | 本文件 |
| `usage_v2.json` | 见 §6 |

只读输入（未改）：
- `challenge_A1.md`（task-36）与 A1 原五件：原文件 SHA 与 record §5 一致（spec `488F719D…`、prior_art `1753352C…`、protocol `550E9AE1…`），本轮**未改动**。
- 上下文：`research/2026-10-27-innovation-round-r198/record.md`（A1 挑战结论/A2/A5 状态、C176/C177）、SYNTHESIS（C 边界）。

## 6. 写后哈希

| 文件 | SHA256 |
|---|---|
| `spec_v2.md` | `52959E29D71CE9F9D6A30083B7100E4B84FB641731273690D196EE4A89C4D765` |
| `protocol_draft_v2.md` | `15C7DA5853F6705D7FD39EBB931AF684F47750F6D62C7D9E000EF0EAB3D5260A` |
| `REVISION_A1.md` | `5CF8661FF2DA7DC4808823FB8B54736CE03DA736C48355B8A81CE8EAA6FE4589` |
| `relations_check_design.md` | `00D087AD632E65BFB2654E9C7AC01F477F0C300712E347BE9C2DE58A3A79D207` |
| `record_v2.md` / `usage_v2.json` | 自引用文件，哈希由外部复算（不含自身值以免循环） |

原 A1 文件（只读，未改）快照：`spec.md` `488F719D…99DD`、`prior_art.md` `1753352C…4193`、`protocol_draft.md` `550E9AE1…7FD6` 与 challenge_A1 §8 记录一致；`record.md` `4926B4EF…92A`、`usage.json` `2A47428F…524`（本轮未改）。

## 7. 局限（本轮）

- **未验证**：n_min=12 的 MDE 推导、注入体检、关系集可达性（R_min=20 在 Jaaks 125 细胞中能否达到 n_ctx=12/tissue 覆盖）均需下一轮 Stage 0/P0 实测；本轮全部是协议设计。
- **δ_min 无值**：成本/效用未冻结，冻结状态 blocked；Stage 1 主指标无法实际执行。
- **(iii) 不可认证**：只 proxy；依赖 A4 的可测状态结论。
- **先例补充有限**：M2 新补 VOI/EVSI 等仅依据既有本地已核记录（R189 evidence/技能档案），本轮不新读全文；原 prior_art.md 不改，以 spec_v2 §9 为 additive。
- **A5 接口未定**：A5 正按 challenge_A5 修订，Stage 2 成本/菜单不可用。
- 未运行任何效果/训练/拟合；不写机制/迁移/决策收益/新颖性结论。
