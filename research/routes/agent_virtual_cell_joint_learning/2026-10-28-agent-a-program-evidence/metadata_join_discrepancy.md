# 元数据连接差异：缺失化合物ID互连，非浮点剂量误差

2026-10-28。保留原 `audit_metadata.py`、`metadata_counts.json`、`program_data_audit.md`；新增本报告、`audit_join_discrepancy.py`与`metadata_join_discrepancy.json`。未联网、未读取效果矩阵、未训练。

**结论：应保留原计数6,303/566药/30细胞与3,790/575药/7细胞。** 同时采用原先声明的 `BRD-[AK]八位数字` 非空core规则和原始十进制精确名义剂量相等，得到的完整键集合与原审计一致。父核对器原先的6,373/567与3,808/576包含不合法的空ID互连，不能解释为Decimal获得更多有效配对。

## 原因与重算

父 `verify_evidence.py` 原 `core()`仅识别 `BRD-[AK]`。`BRD-U…` 返回None，而原 `nominal_joins()`同时允许PRISM `actions[(None,dose)]`与LINCS `cid=None`参加连接；多个不同U类标识因此被压成一个“药物”。原审计先做 `dropna()` 和有效core交集，排除了该类别。

| 来源 | 原浮点重放 | 原父Decimal算法，允许空ID | 修正Decimal，排除空ID | 修正后完整键集合 |
|---|---:|---:|---:|---|
| GSE92742→secondary | 6,303 / 566药 / 30细胞 | 6,373 / 567药 / 30细胞 | 6,303 / 566药 / 30细胞 | 与原浮点完全相等 |
| GSE70138→secondary | 3,790 / 575药 / 7细胞 | 3,808 / 576药 / 7细胞 | 3,790 / 575药 / 7细胞 | 与原浮点完全相等 |

额外70/18键的core全部为None；没有额外的非空药物键。所谓多1个药物是把None也计为一个药物，而非发现新化合物。两期缺失键的原始LINCS单位分别全部为µM、um，**没有nM乘0.001引发的差异**。

## 三个原始剂量与连接例子

下表均是错误中间算法所生成的候选关系；不是有效药物配对。三个例子的背景均为A375、RNA时间24 h、PRISM screen HTS002。错误键均为 `(None, A375, 10 uM, 24 h, HTS002)`；Decimal规范字符串将10写成`1E+1`，数值相同。

| 例子 | LINCS signature / pert_id | LINCS原始剂量字符串 | PRISM broad_id / 原始剂量字符串 |
|---|---|---|---|
| 1 | GSE92742 `BRAF001_A375_24H:BRD-U73308409-000-01-9:10`；`BRD-U73308409` | `10 µM` | `BRD-U25960968-000-01-9`；`10.0` |
| 2 | GSE92742同上；`BRD-U73308409` | `10 µM` | `BRD-U45393375-000-01-6`；`10.0` |
| 3 | GSE70138 `LJP005_A375_24H:M07`；`BRD-U64521890` | `10.0 um` | `BRD-U25960968-000-01-9`；`10.0` |

例如例1的PRISM列名为`BRD-U25960968-000-01-9::10::HTS002`。LINCS与PRISM原始药物ID不同，不能因为两者均无法被当前regex识别就判为同药。所有示例的pandas数值、Python原始字符串float和Decimal均为10；两侧float十六进制均为`0x1.4000000000000p+3`。这些例子没有数值解析或二进制乘法不等。

JSON保存了所有70/18个额外键及对应原始signature、药物ID、剂量字符串、PRISM列名、float repr/hex和逐条原因。修正后的Decimal与原float键集合对称差为空，因而在本次有效core支持集上未发现导致计数不同的float解析误差；这不推广为浮点连接对任意数据都安全。

## 修复、保存与可重复性

父Agent已在其核对器两侧排除 `cid=None`，并以`--repair-join-only`仅重算连接，保存 `verification_v1.json`。本轮读取该文件核实：Decimal计数分别为6,303/566/30和3,790/575/7，`join_matches_agent_count=true`。原 `verification.json`保留了含bug的中间计数；它不是最终连接凭据。此修复未重跑父核对器的其他精确数值诊断。

新增脚本独立读取csv/gzip和原始剂量字符串，同时只执行原审计中读取开放元数据、构造连接的前缀以核对原算法；不执行原审计写JSON的末段。输入哈希全部与原冻结审计相符。原三个产物的执行前后SHA256完全一致，详见JSON的`preserved_artifacts_before/after`与`protected_artifacts_unchanged=true`。

本结论遵守原先声明的A/K core范围。若未来纳入BRD-U，应显式扩展身份解析并逐个核对实际U标识，而不是将空值互连；那是改变身份支持集，不能声称在原算法上完全复现。剂量相等仍只表示名义剂量相同，不表示物理暴露、独立培养、功能效果或近端作用相等。

重放：`D:\anaconda\envs\maestro\python.exe D:\MAESTRO\research\2026-10-28-agent-a-program-evidence\audit_join_discrepancy.py`。脚本仅写新增的差异JSON，原审计文件保持不变。
