# ON3 v0.2 设计说明（DRAFT；按 `challenge_ON3.md` 5 条必改修订）

2026-10-27 · 角色：ON1/ON2/ON2.2/ON3 执行者（非提案者）。配合 [PROTOCOL_ON3_v0_2.md](PROTOCOL_ON3_v0_2.md)；**本文件只作设计/理由/风险说明，未运行效果/训练/更新器，未读响应值做统计。**

## 1. v0.1 → v0.2 的 5 条必改映射

| challenge_ON3 必改 | v0.2 落实 | 位置 |
|---|---|---|
| ① 修掩码线性重建泄漏 | 改**整成员块掩码**（选 20% 药物=8 个，held-out 细胞中凡 partner/成员触及 M 的单元全部掩码）；**证明整上下文掩码仍不足**（跨上下文恒等式）；新增 model-free reconstruction audit（=0）+ context-ablation；重算覆盖 | protocol §2；本文件 §2–§4 |
| ② 锁死唯一 primary comparator | **B4 vs B2 唯一增量判定**；B3/B5 secondary；B0/B1 层级参照；**删除 B5-shuf**；完整比较表 | protocol §3 |
| ③ 修 MDE/rank 尺度错位 | MDE80 只用于 mean Δ/MAE；rank 用 B6 null-calibrated `Δρ_min_rank=max(0.10,Q95_null)` + 配对 bootstrap；0.10 明确为描述阈值非 rank MDE；δ_min 只 mean 尺度；单侧 95th 写死 | protocol §4 |
| ④ 冻结代码级 schema | B6 1,000 置换/seed/每次重拟合/单侧 95th；B5 `random_state`/5 折交叉拟合 TE；B4 ALS init/seed/tol/λ；bootstrap 按细胞配对 B/seed/百分位；mask key/tie/scope；两跑一致/≤45 min/10 项单测/输出 schema | protocol §5 |
| ⑤ 修 batch2 矛盾/覆盖/top-k/措辞/流程 | batch2 **仅披露**；覆盖计数表；top-k 移附录；阴性模板/失败类别冻结；DRAFT→v0.2→同一挑战者复核→Lead 批准→冻结 | protocol §6–§8 |

## 2. 为什么选整成员块掩码（而非整上下文掩码）

### 2.1 v0.1 的泄漏

v0.1 单元级 20% 掩码 + 同上下文 transductive context：对上下文内成员 a,a',c，
`Δ(a,a') = mean(a) − mean(a')`，而 `Δ(a,c) + Δ(c,a') = mean(a) − mean(a') = Δ(a,a')` —— **精确恒等式**，非统计学习。ON2 legal context 中位 18 成员，几乎必然可重建。

### 2.2 整上下文掩码仍不够

设 `g(x,y)` 为药对 `{x,y}` 的网格均值（角色定向对称：`(partner=b,role B,member=a)` 与 `(partner=a,role A,member=b)` 的成员曲线均值都是 `g(a,b)`）。则对任意 `b'`：

```
Δ(a,a';b) = g(a,b) − g(a',b)
          = [g(a,b) − g(a,b')] + [g(a,b') − g(a',b')] + [g(a',b') − g(a',b)]
          = Δ(b,b';a)     + Δ(a,a';b')        − Δ(b,b';a')
```

即：**即使整上下文 `(cell,partner=b,role B)` 被掩码，只要其他上下文（partner=a, b', a'）未掩码，掩码单元仍可被精确重建**。因此"整上下文掩码 + 审计"在一般 mask 下会审计失败；需要更严格的选择。

### 2.3 整成员块掩码（选择）

- 选 **8/38 个药物 M**（ceil 20%），确定性 hash+seed。
- **掩码规则**：held-out 细胞中，单元 `Δ(c;a,a';b)` 被掩码 iff **partner 或任一成员 ∈ M**。
- **精确不可重建性（系数论证）**：变量空间为 `g(c,{x,y})`；一个含 M 药物的 `g` 节点只出现在被掩码单元中（任何包含 M 药物的 pair 都被掩码），因此：非掩码单元的所有线性组合中，该 `g` 节点的系数恒为 0；而被掩码单元对它系数非 0 → 不在非掩码特征的张成空间内 → **不可精确重建**。
- 与 challenge 选项 B（整成员曲线掩码）一致；比选项 A（整上下文）更严格（因为 A 仍留跨上下文恒等式）。
- **代价**：20% 药物 → 掩码单元 **46.4%**（不是 20% 单元），评价集变小但仍足够（157,768 掩码单元、30,824–32,400/fold）；transductive context 只来自非 M 药物（每 cell ≥4,749 单元），可识别 cell 级 offset/低秩因子。
- **纯冷细胞（选项 C）** 作为确认性 sensitivity：held-out 细胞不使用任何 context，只作描述性对照，不进 primary/increment。

## 3. 覆盖与重建审计（设计性预计算；metadata/空值掩码 only）

- 来源：`tmp/_on3_v02_mask_design.py`（SHA `39557B04…`，wall **39.24 s**，只读身份/剂量/viability 空值掩码，未读响应值）→ `tmp/on3_v02_mask_design.json`（SHA `F49B6F92…`）。
- 掩码药物：`dinaciclib, erlotinib, methotrexate, mitomycine, sn38, sorafenib, topotecan, vinorelbine`（8/38）。
- 数字：batch1 单元 441,867；target30 340,088；**掩码 157,768（46.39%）**；非掩码 context 182,320；每 fold 掩码 30,824–32,400、掩码上下文 368–372、非掩码 35,680–37,338；每 held-out 细胞掩码 min 4,237（median 5,400）、非掩码 context min 4,749（median 6,223）；batch2 披露 1,129 单元/136 上下文。
- **覆盖门**：fold 掩码 ≥5,000（PASS 30,824+）；cell 掩码 ≥500（PASS 4,237+）；fold 掩码上下文 ≥50（PASS 368–372）；cell 非掩码 context ≥500（PASS 4,749+）。
- **model-free reconstruction audit = 0 / 157,768**（并查集：非掩码单元边的连通分量；掩码单元两端点若同分量则可重建）。执行时逐 fold 复算并断言 0。

## 4. context-ablation

- B4 含 cell context（c_cell、U_cell 由 held-out 非掩码单元估计）vs B4-ablated（c_cell=0、U_cell=0，仅训练结构）。
- 报告 `Δρ_context = ρ(B4) − ρ(B4-ablated)`；≤0 时只写"该设计下未观察到 context 描述性增益"，不得写"细胞上下文无用"。
- 这是对"条件结构"的补充描述，不替代 B4 vs B2 的 primary 判定。

## 5. Primary comparator 与指标/功效

- **唯一 primary：B4（层级+低秩，cell context）vs B2（静态强基线，partner×member-pair）**。
- **rank 主指标**：Spearman ρ；增量 = Δρ(B4−B2)；判定：Δρ ≥ `Δρ_min_rank = max(0.10, Q95_null(Δρ))`、bootstrap 单侧 95% 下界>0、B6 单侧 p≤0.05、≥4/5 folds 正；否则 `no_increment`。
- **mean 尺度**：MAE；MDE80=0.0287644381（实测 σ̂_e 推导）**只用于 mean Δ/MAE**；|ΔMAE|<MDE80 → `evaluation_cannot_distinguish`（mean 尺度不足）；δ_min=0.10 只 mean 尺度，**不是 rank MDE**。
- **0.10 的定位**：预注册描述阈值，非从 MDE 导出；rank 精度由 null 分布 + bootstrap 定义。
- 所有指标 pooled/per-fold/per-cell 报告；完整比较表；不允许"选最佳 X"。

## 6. 代码级 schema 要点（详见 protocol §5）

- **B6**：1,000 置换、seed `20261130`、每次重拟合 B4（同训练 24 细胞/同超参）、单侧上 95th；null 校准门：2.5–97.5 覆盖 0 且 mean|ρ_null|≤0.05。
- **B5**：HistGBM `random_state=20261130`；target-encoding **5 折交叉拟合（fold by training cells，seed 同）**；容量网格 {depth 2/3 × leaf 50/200}、lr 0.05、iter 200；无 cell id。
- **B4**：ALS init normal(seed=20261130, 0.01)；tol 1e-6；max_iter 25；rank {1,2,3,5}、λ {0.01,0.1,1,10}；c_cell/U_cell 只用非掩码 context；超参 24 训练细胞 leave-one-cell-out CV。
- **bootstrap**：按 held-out 细胞分层配对（5×6；B=5,000；seed=20261130；percentile 2.5/97.5 + 单侧 95th；预测固定不重拟合）。
- **mask**：M 选择 key `SHA256("ON3v0.2|M|20261130|"+归一名)` 升序取 8；tie 归一名；scope batch1/30 cells；规则见 §2.3。
- **确定性/预算**：两跑 `on3_exec.json` 逐字节一致；JSON 键排序/无时间戳/allow_nan=False；输入/脚本 SHA；单命令 ≤45 min（设计预计算 39 s；执行含 5 折×B4×1,000 置换需评估，见风险）。
- **单测 10 项**：mask 确定性/掩码规则/reconstruction=0/扰动/context-ablation/schema/两跑/折继承/无 Jaaks 路径/无 test 调参。

## 7. batch2/top-k/措辞/流程

- batch2 **仅披露**（5,214 行/1,129 单元/136 上下文），不进训练/指标/增量/敏感性；batch3 全失披露；702 个 15 行 pair-cell 排除计数。
- top-k **移附录 A**（k∈{1,3,5}，tie 归一名，无决策含义）。
- 阴性模板："在本资源/本设计下未观察到 B4 相对 B2 的预注册描述性增量；这不等于结构不存在、不可迁移或没有决策价值。"
- 流程：v0.2 → 同一挑战者复核 → Lead 批准 → 冻结 execution protocol → 执行；冻结后不改 mask/seed/fraction/超参/rank/λ/指标/差值规则。

## 8. 风险/限制

1. **掩码单元 46.4%**：评价集比 v0.1 小（157,768），但 5 折每折 30k+，足够描述；**不是** 20% 单元——披露。
2. **B4 容量/超参**：小数据上低秩可能过拟合；用训练细胞 CV + 固定网格；B5 作容量描述。
3. **B6 运行量**：1,000 置换 × 5 折 × B4（25 ALS）；若超 45 min 预算，必须**先验证**再冻结（不得事后减置换数）——执行前须做预算测试；若超预算，在**执行协议冻结前**改置换数（如 500）并披露，或改 null 构造为更省算力但预先冻结的方案。
4. **transductive context 非纯冷启动**：结论不能写迁移/新细胞；纯冷细胞只作确认性 sensitivity。
5. **MDE/rank 分离后**：rank 没有 MDE 保障；只能写 null-calibrated 描述性增量/不可区分。
6. **context-ablation 若为 0**：B4 的增量可能来自静态/收缩而非 cell context，须如实写，不升级为"条件结构成立"。
7. **masked-member 选择**可能影响结果（8 个药物）；冻结后不得改；披露选择规则。
8. 缺失机制未知、batch3 全失、702 个 15 行 pair-cell、无暴露时间/assay、单药参照未用、技术重复≠独立培养——仍为限制。

## 9. 对 challenge_ON3 §7 八问的回答

1. 单元级掩码不可接受 → 改整成员块掩码（比整上下文更强，因跨上下文恒等式）；transductive 披露；纯冷细胞作确认性 sensitivity。
2. 掩码选择：确定性分层（选 8 个药物=20% 药物）+ 固定 seed；单元比例 46.4% 披露；覆盖按新口径。
3. Δρ≥0.10/4-of-5/bootstrap/null 保留为**描述性**；B4-only、单侧 null、bootstrap 细节写死；不称 MDE/精度保障。
4. B2 足够强；backoff 写死；不用 held-out context；B2 通过不证明结构成立。
5. 单药工作簿必须先单独资格；primary 不用；仅未来敏感性。
6. B5 容量网格合理，但需写死 TE 交叉拟合/random_state；B5-shuf 删除（无效）。
7. top-k 降附录。
8. B6 1,000 置换/seed/refit/单侧 95th 写死；B5 负对照改由 B6 承担或删除（本版删除 B5-shuf）。

## 10. 执行前检查单（冻结 execution protocol 时逐项）

- [ ] mask M 列表/SHA/规则/覆盖表已写入；
- [ ] symbolic reconstruction 审计=0 可复算；
- [ ] B6/B5/B4/bootstrap schema 与单测 10 项；
- [ ] primary B4 vs B2 唯一；B3/B5 secondary；完整比较表；
- [ ] rank null-calibrated 规则与 mean/MAE MDE 分开；
- [ ] batch2 disclosure-only；top-k 附录；
- [ ] 阴性/阳性模板与失败类别；
- [ ] 两跑一致/≤45 min/预算测试；
- [ ] 同一挑战者复核 + Lead 批准。
