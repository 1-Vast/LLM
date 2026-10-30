# R200-D5.1 记录（record_d5_v0_2）

2026-10-27 ｜ 执行：cellstate-lit（task-96） ｜ 工作目录：`D:\MAESTRO`。
对象：按 `challenge_D5.md`（endpoint-auditor，`revise`，5 必改）修订 D5 资格/primary/字段/门为 v0.2。**不运行效果、不拟合预测、不读表达/响应矩阵。**
只写 `research/2026-10-27-direction-mechanism-expansion/d5_temporal/` 下 **v0.2 新文件** 与 `tmp/`；**v0.1 六文件冻结不改**。

## 0. 纪律与范围

- 未训练/未拟合/未运行效果或预测统计；未读 h5ad 表达矩阵 `X` 数值、`obsm`/`layers`、任何响应/功能矩阵；未联网。
- v0.2 唯一执行代码：`d5_revision.py`（metadata-only：h5ad obs/var 元数据 + v0.1 JSON 读入 + 文件 SHA）；输出 `d5_v0_2.json`。**不写 v0.1 产物。**
- 所有数据数字来自 h5ad obs 元数据计数；v0.1 只作输入/交叉核对（SHA 登记）。

## 1. 读过什么

| 输入 | 用途 | 证据状态 |
|---|---|---|
| `challenge_D5.md`（11,300 B；SHA `6a00257e…`） | 5 必改依据 | 已读 |
| v0.1 六文件（`PROTOCOL_D5.md`/`d5.py`/`d5.json`/`report_d5.md`/`record_d5.md`/`usage_d5.json`） | 冻结不改；SHA 登记；数字交叉核对 | 已读/哈希 |
| `data/external/mixseq_scperturb/mcfarland_2020.h5ad` **obs/var 元数据** | active dose/ChEMBL、V1 合法线、V2 配对集合、折清单 | metadata-only |
| 背景（R200 BRIEF、direction report/mechanisms_v3、R199 BRIEF、ERRATA_A3、A3v2 文件） | 边界/纪律（v0.1 已读；本轮只读 challenge 与 v0.1） | 已读（前轮） |

**未读**：h5ad `X` 值；PRISM/Tahoe/GDSC/kinetic_horizon 任何响应/功能内容；其它研究目录 effect 结果。

## 2. 实际执行

### 2.1 `d5_revision.py`（metadata-only；确定性）

命令：
```text
D:\anaconda\envs\maestro\python.exe research\2026-10-27-direction-mechanism-expansion\d5_temporal\d5_revision.py
```
行为：
1. 读 v0.1 六文件 SHA 与 `challenge_D5.md` SHA；读 h5ad obs/var 元数据（不读 X 值）。
2. **active-dose/identity 分类**（metadata-level）：每 arm 的 `dose_value`/`dose_unit`/`chembl-ID`；`dose>0 + unit + ChEMBL` 为 conditional pass。
   - Bortezomib 2.5 µM / CHEMBL325041；Idasanutlin 2.5 µM / CHEMBL2402737；Trametinib 0.1 µM / CHEMBL2103875 → conditional pass。
   - BRD3379 0.0 µM / 无 ChEMBL → **fail**（zero-dose/vehicle-like control，排除出 primary）；control 0.0 µM → reference。
3. 重算 V1 合法线：active drugs **22/24/24**；BRD3379 secondary **95**（保留数字但无 primary 权重）。
4. 重算 V2 对比/配对集合：target24h E1/E2 n=18/15、**paired=15**；target48h n=19/16/15、**paired E1/E2=16、E2/E3=15**。
5. 生成 V1 3 药折清单（manifest SHA `0056d69e…`）、BRD3379 secondary 折、V2 折。
6. 生成 MDE 上界（active only）：0.865/0.826/0.826；r_err 0.987/0.985/0.985。
7. 输出 `d5_v0_2.json`（含 revision_changes、active qualification、V1 primary/secondary、V2 corrected、G0a/G0b、E1–E12 执行清单、失败/停止、verdicts、v0.1 cross-check、inputs SHA、script SHA）。
8. v0.1 cross-check：**合法线/对比 n 与 v0.1 一致**；记录 v0.1 `paired_n=2` bug 与正确 15/16/15。

**未执行**：任何 `X` 读取、任何模型拟合/预测/效应统计、任何网络请求。

### 2.2 轮次

`d5_revision.py` 共运行 3 次：run1 成功（G0b 措辞 patch 前）；patch 后 run2、run3 连续运行，`d5_v0_2.json` 逐字节一致（最终 SHA `d41ed20f…`）。

## 3. 验证

```text
v0.1/challenge SHA 与 challenge_D5.md §4 报告值一致：
  d5.py 1422CB54… / d5.json 82330743… / PROTOCOL_D5 3923FE7D… / report C94E0F9F…
  record D15286BA… / usage E360377C… / challenge 6A00257E…
d5_v0_2.json:
  cross-check v1_eligible_lines_match = true; v2_eligible_lines_match = true
  两次连续运行逐字节一致：SHA256 d41ed20fc6a4545e2e8cada3b14702edd9c044093bfa4e1a018988358d207830 (32,951 B)
  json.load OK
未读表达/响应；未拟合；未联网；v0.1 未改
```

**无**任何效果/预测计算；以上仅为元数据计数、交叉核对、文件哈希与确定性检查。

## 4. 产物与 SHA256

| 文件 | 字节 | SHA256 |
|---|---:|---|
| `PROTOCOL_D5_v0_2.md`（新，DRAFT） | 17,965 | `d1abd7c65a1db5c452cf761914456885053663a6c907bbc4493fd6b94769e7b0` |
| `report_d5_v0_2.md`（新） | 8,617 | `4b742a0d6f4f89ffb1d819f8aeb65c076c019e3b4df4fe26b4c3b37d940001d4` |
| `d5_revision.py`（新） | 31,093 | `6a89039c7073782c71083d9095cc72172718ec374b84890e213788233057d199` |
| `d5_v0_2.json`（新） | 32,951 | `d41ed20fc6a4545e2e8cada3b14702edd9c044093bfa4e1a018988358d207830` |
| `record_d5_v0_2.md`（本文件） | — | 见 `usage_d5_v0_2.json` |
| `usage_d5_v0_2.json`（新） | — | 见文件 |
| v0.1 输入（不改） | — | 见 §3 / `d5_v0_2.json:inputs_sha256` |
| `challenge_D5.md`（只读） | 11,300 | `6a00257e65336089de7361924bbb6b6cc6bee7682572817054bccc6e8265ad73` |

**v0.1 未改**：`PROTOCOL_D5.md`/`d5.py`/`d5.json`/`report_d5.md`/`record_d5.md`/`usage_d5.json` 的 SHA 与 challenge 记录一致；v0.1 4 药 primary 在 v0.2 中**撤回**（历史文本保留，不作运行依据）。

## 5. 决定与理由

1. **BRD3379 排除出 primary**：0.0 µM 不构成 active perturbation；其 95 线占 primary 极大权重，混入等于把 zero-dose/vehicle-like control 当 active drug。v0.2 只作 secondary/zero-dose control，并强制标签。
2. **3 active drugs primary**：Bortezomib/Idasanutlin/Trametinib 均有 dose>0 + ChEMBL 注释（metadata-level）；n=22/24/24 满足 ≥20；主统计量为 3 药等权平均（不做跨药配对）。
3. **V2 paired 修正**：`paired_n` 必须是配对细胞系数（交集），v0.1 的 `len(dict)` bug 记录在案；执行只用 paired sets（15/16/15）。
4. **G0 加 active-dose/identity 门**：BRD3379/control fail；3 药为 metadata-level conditional pass，执行前须再核化合物/剂量/vehicle，避免把注释当独立认证。
5. **不运行效果**：任务要求；预运行 MDE 上界仍高（24 线级需 r_err≈0.985 才能 ≤δ_min），G3 高失败风险；先再挑战，避免高成本低判别运行。

## 6. 限制 / 未完成

- 本轮只做文档/资格/设计修订；**不运行效果/不拟合/不读表达**；门只是冻结规则。
- active-dose 仅 metadata-level；未做独立剂量/化合物 identity 测定；执行前必须重核。
- 功能终点/同细胞配对/batch/exposure/独立培养/重复仍缺；`time_axis_unverified`。
- V2 n<20 仅 exploratory；BRD3379 secondary 不能复活 4 药 primary。
- 执行协议 E1–E12 已列清单但**未实现**；需另立执行任务 + 独立挑战。
- v0.1 未改（保留历史）；v0.2 是唯一运行依据候选。

## 7. 下一执行者从哪里开始

1. 读 `PROTOCOL_D5_v0_2.md`（§0 五必改、§2.1–2.3 3 药/paired、§8 门、§11 执行清单）与 `report_d5_v0_2.md`。
2. **再提交独立挑战**（建议：是）：审 active-dose 排除、3 药 primary/MDE、V2 paired 15/16/15、G0b/G3、E1–E12 清单；挑战通过前 `approve_to_lead_exec=false`。
3. 挑战通过并获准后：另立执行协议/任务，按 E1–E12 冻结实现（仍只分子层；不改 δ_min/切分/配对语义）；先报 G1–G3，再报 G4。
4. **功能/决策/轨迹主张停止**：等新测量；不换名重启；不重开 R196v2/R197v2。
