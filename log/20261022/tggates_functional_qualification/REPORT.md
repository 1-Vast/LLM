# TG-GATEs 功能身份与缺失菜单资格

2026-10-22，独立 functional auditor。结论为 **FUNCTIONAL_IDENTITY_QUALIFIED_WITH_EXPLICIT_MISSINGNESS；只可进入新开发集开值协议设计，不自动准许数值开值、CEL 下载或模型实验。** 官方相同 experiment/group/individual 身份可精确连接现有功能表和表达属性，保留了可研究的早期表达→晚期功能菜单；尚未证明功能信号、独立培养/lot、可干预世界模型或 RSI。

## 来源与访问边界

在读取已登记 `PROTOCOL.md` 后，`acquire.py` 只获取一个官方对象：[open_tggates_cell_viability.zip](https://dbarchive.biosciencedbc.jp/data/open-tggates/LATEST/open_tggates_cell_viability.zip)。HTTP 200，51,898 body bytes；SHA256 `f790d45a5cb40e653bb3dada1aa2f40bfdd26b8bd1f7fdb86decc9c908c9cb14`。原始 bytes 在 `sealed_source/`，完整 headers/UTC/用时在 `NETWORK.json`。本区块无其他 HTTP 请求，低于 2 MB 预算；无 CEL、表达、API 或 GPU 使用。

先完成 23 项纯合成测试，再冻结 13 个代码/协议/源/旧身份/测试文件（`PRE_OPEN_FREEZE.json`），随后单独启动 `worker.py`。只有该进程解码官方 CP932 CSV 的 DNA/LDH 字符串用于预定缺失和精确字符串相等判断；它不将响应转为数字。研究者、主进程、census 和 verifier 只读白名单身份及布尔标志；未输出任何响应值、范围、分布、活性、排名或 shortlist。该隔离为进程和数据流约束，**不是 OS 文件权限/加密保证**；原 ZIP 不应在后续无协议情况下直接打开。

CSV 实际 header 与 README 已认证的 12 列一致；包含 5,986 总行，Human 2,606、其他物种 3,380。保持所有身份原字符串，包括 `GROUP_ID` 前导零和原单位。零响应字符串非缺失；未知非缺失字符串不被当缺失，也不被认证为有效数字。重复按原始非缺失响应字符串判断冲突，绝不按数值大小选行。

## 精确连接与缺失

| 身份/可用性 | 直接计数 |
|---|---:|
| 既有 human sample / CEL attribute | 2,610 / 2,605 |
| human 功能行 / 唯一 sample key | 2,606 / 2,606 |
| 功能重复 key / identity 冲突 / DNA、LDH 冲突 | 0 / 0 / 0、0 |
| 相同 key 的十项身份字段或 CEL barcode 差异 | 0 |
| sample 无功能 key / 功能无 sample key | 4 / 0 |
| sample 无 CEL attribute / CEL attribute 无 sample | 5 / 0 |
| DNA missing / LDH missing（在存在的 2,606 功能行中） | 602 / 2 |
| 两 endpoint 均非缺失 | 2,002 |
| 全部 2,610 sample 中匹配且 DNA 非缺失 / LDH 非缺失 | 2,004 / 2,604 |

不把四个完全无源行的 sample 藏进 missing denominator；它们分别为 `5339/10/2`（transforming growth factor beta 1，2 hr，High）和 `5340/04/1`、`5340/04/2`、`5340/10/2`（hepatocyte growth factor, human，2 hr）。`FUNCTIONAL_CENSUS.json` 保留原浓度、单位和身份。

五个没有 CEL attribute 的 sample **全部在既有 cell-sample 表中 BARCODE 为空**，也没有该 sample key 的 CEL attribute；五个功能 key 均存在。因此这是释放身份资产中的表达链接缺失，而非本轮 join 错误或功能缺失。对应为：`5322/08/2` trimethadione、`5323/08/1` bromoethylamine、`5327/08/1` 与 `/2` phorone、`5333/08/1` LPS，均为 24 hr/High。缺失原因、原始 CEL 是否另有储存、功能数值是否有效均未认证，不能猜测是死亡或表达 QC 失败。

## 时间菜单要按应用所需观测定义

粗 compound/decimal-dose/原单位菜单完全复现旧结论：396 非 control 条件，156 条件/52 标签具 2/8/24 hr。三时点均要求每时点两份匹配 CEL 加 DNA 和 LDH 非缺失时，剩 **144 条件/48 标签**；只要求 LDH 是 **153** 个完整双重复三时点条件。此处减少主要来自早期功能行/缺失，不意味着早期 CEL→晚期 LDH 预测也缺失。

因此另外从安全投影计算真正的早期 CEL→晚期功能 availability（`EARLY_LATE_MENU_COUNTS.json`）。这一步在白名单输出后新增脚本，仅处理身份/缺失标志；没有回开源响应，也不伪称其代码属于第一次冻结。条件键保留 EXP_ID、药名、十进制浓度、原单位、DOSE_LEVEL：

| 早期 CEL→晚期 endpoint | 两份早期 CEL、两份晚期功能，且有对应两份早期表达控制与晚期功能控制 | 标签数 |
|---|---:|---:|
| 2→8 hr，LDH | 159 | 53 |
| 2→8 hr，DNA 与 LDH | 144 | 48 |
| 2→24 hr，LDH | 156 | 52 |
| 2→24 hr，DNA 与 LDH | 144 | 48 |
| 8→24 hr，LDH | 385 | 152 |
| 8→24 hr，DNA 与 LDH | 286 | 119 |

8→24 hr 的 385 个 LDH 条件中，381 个还具所有晚期 CEL；其余四个条件受上述五条缺失属性影响。这是释放身份的可用性计数，包含下述未认证浓度，**不是 385 个已认证有效正剂量动作**。表中控制只是同 EXP_ID/时点的记录身份配对；没有证明同一个物理孔、细胞、培养、lot 或 donor。重复时间为破坏性样本，不能当同细胞轨迹，individual 1/2 也未被认证为两个供体。

**浓度身份另有必须处理的问题。** 42 条非 control 记录、8 个药名、10 个 dose-level 条件的 released DOSE 实为字符串 `0`；其中 rotenone 和 amphotericin B 各有 Low/Middle 同为 `0`，所以保留 dose level 后的 8/24 菜单为 385，粗浓度菜单仅 383。这不是新增实验，也不能当额外非零浓度信息。24 条非 control 记录单位为 `μg/kg`。`CONCENTRATION_IDENTITY_DIAGNOSTICS.json` 记录此身份异常；未修补、转换或按 endpoint 排除。未来浓度建模需在任何响应开值前固定排除/认证规则，不能用 log-dose 强行处理零或猜测小浓度被舍入。

## 下一步的明确边界

本轮只支持继续设计一个**条件于已释放剂量菜单**的早期表达→晚期功能/后续实验选择任务。root 的独立 `DOSE_LINEAGE_REPORT.md` 未认证 prescreen assay/time/lot。最高剂量依赖先前 survival prescreen，不能表述为无先验的新药剂量发现；DOSE_LEVEL、实际剂量和既有选择先验必须对所有模型开放并记账。官方 README 将 DNA(%) 与 LDH(%) 都定义为 relative survival，后者由培养上清泄漏酶活计算；不能把已发布 LDH(%) 当原始 LDH 泄漏值，也不能继承 OASIS 的数值方向/阈值。

任何下一次数值 gate 之前须有新的不可覆盖协议/冻结：

1. 明确选择 2→24 或 8→24 应用、每个动作的实验单位与费用，允许的早期输入/晚期 endpoint/控制；说明不同破坏性样本而非同细胞轨迹。不得把“功能表存在”当成世界模型可识别性。
2. 以结构认证/保守药名分组先固定开发、选择、保留与 quarantine；蛋白/混合物、相同药不同名字、零剂量和异常单位不得靠猜测处理。现有缺失标志可用于预定可观测菜单，不可按活性挑药。
3. 固定剂量 prescreen 先验与预算政策、DNA/LDH 已发布相对生存率的归一化含义/控制使用方法、纯开发集数值导出合同。未认证 assay/lot 独立性时，结论须条件于菜单与实验身份。
4. 在开值前设定与应用 loss/尾部决策相关的可证伪 gate、实用改进 margin 和停止条件；保留失败/缺失观测。不得无理由照抄 OASIS 的全菜单 rank gate，也不得看到活动尾部后再改 gate。
5. 先确认信号和简单直接预测/普通更新机会，再考虑 CEL 获取规模及架构；强直接、普通重训练、持续学习、主动学习、简单混合、等预算程序搜索与相同起点继承/元改进对照仍全部未测试。

不存在数值信号、模型性能、世界模型、智能体、继承或 RSI 的通过结论。跨 lot 资格仍为 IDENTITY_NOT_ESTABLISHED。

## 验证与保留问题

23 项合成测试覆盖精确白名单无值泄漏、零和未知字符串处理、重复/冲突不选优、不合 schema 的无值错误、非人数据不导出、同 key 错剂量/错 barcode 和功能缺失不计完整菜单。首次 pytest 缓存目录重命名出现 WinError 5 警告，测试断言全部通过；原日志保留，不把它改写成干净运行。

`verify.py` 完成 **5,282 项 PASS 检查**：13 冻结文件、源 bytes/hash、2,606 行投影的精确字段和布尔类型、缺失/配对 arithmetic，以及独立 pandas 聚合重建所有早晚至少一份/两份菜单数。verifier 未解码功能 ZIP 响应。`POST_PROJECTION_FREEZE.json` 另记录原 13 文件实际复核及之后新增代码/输出的 hash，明确 postprojection 文件不能伪称 worker 前冻结。验证范围是协议/身份/可用性，完全不验证生物信号或模型有效性。

新代码全部位于 `research/tggates_functional_qualification_20261022/`，新源、协议、测试/执行日志、冻结、投影、计数和结论全部位于本 log 目录；未改旧 source 资格证据或任何 OASIS STOP。
