# R203-N1.3（v0.4）报告：V4 独立验证 + 代码残留修复 + 披露（设计/校准；不运行效果比较）

2026-10-28。对象：R203-N1（机制账）。依据：N1.2-C1 复核（revise，3 必改）、[challenge_N1_v0_3.md](challenge_N1_v0_3.md)、R203-P1 链、A 线停止记录。
**只做设计/算术/pre-effect 校准：未运行效果比较、未报告方法效果指标、未读 O'Neil 响应、未用 A/B 资源；机制账 only；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定/门槛；0 wells/compute-only。**
- 修正问题定义：[PROBLEM_N1_v0_4.md](PROBLEM_N1_v0_4.md)（`5C513D94…`）
- 修正执行设计：[DESIGN_N1_v0_4.md](DESIGN_N1_v0_4.md)（`94BAB805…`）
- 生成器/算术：[generator_n1_v0_4.py](generator_n1_v0_4.py)（`AA5D454A…`）→ [generator_n1_v0_4.json](generator_n1_v0_4.json)（`35E41136…`）
- **V4 独立验证**：[V4_validation_v0_4.json](V4_validation_v0_4.json)（`254BEBAB…`）
- canonical pilot：[timing_n1_pilot_v0_4.json](timing_n1_pilot_v0_4.json)（`A4C7E0F6…`）
- 记录/用量：[record_N1_design_v0_4.md](record_N1_design_v0_4.md)、[usage_N1_design_v0_4.json](usage_N1_design_v0_4.json)
- **v0.1–v0.3 产物未改**。

## 0. 3 必改落实

| # | N1.2-C1 问题 | v0.4 落实 |
|---|---|---|
| ① **V4 不是独立 gate** | **V4_MODEL_SPEC 在运行前冻结**（soft state responsibilities + weighted ridge λ=1.0；features 21+12；初始化 1/S；forward posterior；无调参；spec SHA `A69B845D…`）；**独立 seed=20261062、200 组全新样本重跑 V4：mean ΔELPD=503.0425、SE=64.4214、95% CI=[376.779, 629.306] → PASS**；**首轮 FAIL −456.6、oracle 诊断 +4147.6、filter 改动全部披露**；只有独立 V4 PASS 作 gate（dev seed=20261061 的 306.1577 标为 **post-hoc 诊断，不作 gate**）；oracle gate（seed=20261063：4988.236/248.226/[4501.72,5474.75]）仅 fallback/补充 |
| ② **代码注释残留 359/288** | `generator_n1_v0_4.py` 注释/摘要修正为 2-active-basis h：compact 107/312、**full 143/600（rank140/nullity3）**；**grep 359/288 无残留**；129 仅在明确标注的 v0.1 历史算术上下文中出现，不作 full 摘要 |
| ③ **PROBLEM/DESIGN 未披露 adaptive 历史** | PROBLEM §4 / DESIGN §4 写入首轮 FAIL（−456.6）、oracle（+4147.6）、filter 从等权→soft-responsibility/weighted ridge(λ=1)、规则/阈值/seed/n_rep/held-out 未改但**模型实现是在看到 V4 失败后改变**、dev 306.16 为 post-hoc 诊断、**独立 seed=20261062 PASS 作为 gate**；不再只写最终 PASS |

## 1. V4 独立验证细节（gate）

- **冻结模型规格**：static S-add ridge（21 特征，λ=1e-2）vs nonstatic state-dependent filter（33 特征=21+12 interaction；soft state responsibilities 作回归权重；weighted ridge λ=1.0；forward posterior；初始化 1/S；无调参）；held-out 仅 T_hold=2 轮。
- **首轮历史（披露）**：初始 filter 等权分配观测 → V4 **FAIL（mean −456.6）**；oracle-state 诊断 **+4147.6** 确证生成器状态信号；改 soft-responsibility/weighted ridge；dev seed=20261061 重跑 306.1577/65.4612/[177.856,434.459] PASS —— **post-hoc 诊断，不作 gate**。
- **独立验证（gate 依据）**：**seed=20261062、n_rep=200、新样本（不同 RNG 流，非 20261061/非同一 200 组）**：**mean 503.0425、SE 64.4214、95% CI [376.779, 629.306] → PASS**（mean>0 ∧ mean≥2SE ∧ CI lower>0）；**gate mode = V4_independent（valid rename_static_Sadd gate）**。
- **fallback oracle gate**：seed=20261063、n_rep=200：mean 4988.236、SE 248.226、95% CI [4501.72, 5474.75] PASS；仅当独立 V4 无法验证时降级使用；**不得同 seed post-hoc PASS 作 gate、不得迭代到通过**。
- **失败路径**：独立 V4 FAIL 且 oracle FAIL → `design_invalid: rename_static_Sadd`、不进入效果。

## 2. 保持不变（N1.2-C1 item 4）

- **n_units=300、MDE80=0.04798、n_req=278≤300**；G1 point=.0488（976/20000）≤.05、Wilson=.05187≤.075；G2 powers=1.000/1.000/1.000；G3 full **143/600/rank140/nullity3（参数 gauge=3）**；compact 107/312/95/12；函数空间冗余 compact 129（v0.1 历史算术）/full 255。
- B1–B6 等 compute/query 基线；**B2 等价审计 PASS**（initial-data hash/menus/query count=6/prior/tuning=20/shared seed）；caps **1800 s/2 h/8 GB/0 wells**；两跑/schema/失败类别/边界不变。
- **最终实现重跑 pilot/G7**：per-rep **0.05622 s**、projected main **25.3 s**、memory **0.037 GB**；逐方法 **B1 .00376 / B2 .00254 / B3 .00251 / B4 .03587 / B5 .00038 / B6 .00275 / M .00841 s**；B2 审计 PASS；G7 引用同一 canonical telemetry。
- 主预算：n_units=300、R=50、methods=7、T=6；0 wells/compute-only；结果 JSON 无 telemetry。

## 3. 边界

机制账 only；不称药理/真实决策/迁移/机制/新颖性；合成≠药理；不晋升代码；不恢复停止实验；不改旧门槛/判定；N1 效果执行须另立执行预注册 + 独立挑战 + Lead 批准；本任务不运行效果比较。

## 4. 产物/确定性/SHA

| 文件 | SHA256 |
|---|---|
| `PROBLEM_N1_v0_4.md` | `5C513D9461FAEDBD3372463A4FDD1868C927EB4850BC0CDEB7643FF6FA0649A` |
| `DESIGN_N1_v0_4.md` | `94BAB8052EF4864BD745986326F4869D9054C2935794FEDAD8733733B57C029C` |
| `generator_n1_v0_4.py` | `AA5D454A82366BF3B7FC9E7F67FAA3499098621FAD45B84804485550E6EDCC97` |
| `generator_n1_v0_4.json` | `35E41136E344AAF6C51A73B19418FF5CBEAD9460697BB8B1EE92F9E16D610263` |
| `V4_validation_v0_4.json` | `254BEBAB201AA8A0EA33AEA8A47BC7D37A99ADE1436319D159603061DC8E2ECF` |
| `timing_n1_pilot_v0_4.json` | `A4C7E0F675B0020B99A93CC022572B3E85F30A26E391493AF45FAA3C005586C7` |
| report/record/usage | 见 `usage_N1_design_v0_4.json` |

**确定性**：`generator_n1_v0_4.json` 与 `V4_validation_v0_4.json` 两跑逐字节一致（`35E41136…` / `254BEBAB…`；wall 10.7/11.0 s）；结果 JSON 无 telemetry（canonical pilot 在 timing 文件）；文档 SHA 写入 JSON 且一致。

## 5. 建议

1. **提交 v0.4 做独立复核/再挑战**（重点：V4_MODEL_SPEC 预冻结 + 独立 seed 20261062 PASS 503.04/64.42/[376.78,629.31]；首轮 FAIL/oracle/模型改动披露；代码无 359/288 残留；full 143/600/140/3；v0.4 pilot .05622/25.3/.037；G1/G2/B2 审计/caps 不变）。
2. 复核通过后请 Lead 批准 **N1 执行预注册**（仅合成机制账；不批效果外推/药理/真实决策/迁移/机制/新颖性）；N1 效果执行另立执行预注册 + 独立挑战 + Lead 批准。
3. **不做**：效果比较/结论、代码晋升、旧判定修改、合成升级为药理。
