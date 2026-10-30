# R193-A0 勘误（ERRATA，2026-10-27）

依据：独立挑战 [challenge_A0.md](challenge_A0.md) 的只读复核（Lead 已核对挑战给出的复算口径）。**本勘误不改变 A0 资格判定 `matching_qualified`（R4/覆盖/端点/独立组四道 gate 均不受影响）**；只更正被 A1 复用的计数/口径与披露。

## 1. 计数/口径更正

| 项 | A0 报告/a0.json 原值 | 更正后 | 说明 |
|---|---|---|---|
| `disjoint_pairs`（p,q 不共享任何 drug id，任意朝向） | 5,345,987 | **4,612,633** | a0.py 只减 same_anchor+same_library，漏掉 `p.anchor==q.library` / `p.library==q.anchor` 的跨朝向共享（差 733,354）；A1 若用"最干净 disjoint 层"须用更正后口径，或重算 |
| G1-only / G2-only（按 M3 冻结的**无序**药对剔除） | 4,415,971,041 / 7,301,337 | **4,412,540,421 / 7,234,325** | a0.py 用"同有向药对"剔除；与 PROTOCOL_A0 M3 的无序口径不一致；R4 主计数用无序口径、已正确（6,223,367） |
| `matched_conditions.csv` 条件级有向药对数 | report §4 写 130 | **129** | 130 是药对级重叠；条件级匹配后少一个（A1 明确用 129） |
| barcode-split R4 覆盖 | 只写 keys 31,019 | **46 细胞 / 583 细胞对**（keys 31,019） | A1 的 within-screen 可靠性参照只能覆盖这些细胞对 |
| Validation 选择偏差 | 未披露 | **必须披露**：R31 记录验证筛仅 4.4% 键、"极可能就是挑过的子集"；F9 报告 96/125 细胞与组织构成偏移 | A1 须预注册 matched/unmatched 元数据比较、Original 内随机子集对照、回归到均值/衰减诊断，结论限定在该 Validation 子集 |
| 条件间剂量差 | A0 只声明"设计列可比" | **A1 必须固定 dose-matched 主分层**（`controlled_anchor`：同 anchor、同 anchor_conc、同 library_conc，仅 library 不同；A0 报 92,039 个） | 否则 Q 会混入 cell×剂量项 |

## 2. 对 A1 的影响

- 上述更正不改变 `matching_qualified`；A1 引用 A0 时必须同时引用本 ERRATA。
- `PROTOCOL_Q.md`（v1 冻结）已按更正后的口径与补充披露设计主分层、选择偏差诊断与可靠性/衰减分析。
- 旧报告不改写；本 ERRATA 为更正入口（登记表 C170）。
