# LIST抗生素药序公开资产：来源认证，当前完整replay配置停止

2026-10-22，Asia/Shanghai。**STOP_THIS_PUBLIC_ASSET_CONFIGURATION**：确实找到
原作者相关代码、公开图像版本和一个增长表，但当前取得的文件不足建立真实
药物/给药时间/独立实验单位→早期状态→未来功能的可执行关联。未训练模型或
进行真实功能性能、Agent、继承或RSI试验。总目标继续ACTIVE/NOT_ACHIEVED。

## 发生实质变化的证据

上一阶段只有摘要与精确DOI检索零项；本轮标题/作者/README和官方元数据交叉核查
找到了[Uchicago-TAY/LIST](https://github.com/Uchicago-TAY/LIST)及
[README所指Zenodo18362221](https://zenodo.org/records/18362221)。该record说明
直接引用目标论文DOI10.1101/2025.10.30.684665v1，公开来源关联已经认证。
不能继续把本源称作“没有公开代码或数据入口”。

独立代理发现的新版[22118144](https://zenodo.org/records/22118144)与旧版同concept
18362220，但旧版7个512腔TIF/ZIP/PPTX、新版6个1024腔PNG/ZIP，没有同名文件。
版本不能替换或合并成一个数据集。两版作者description均明确：完整raw/analysed
datasets太大不能公开分享，研究用途可向通讯作者reasonable request；主要支持结果
在paper及Supplementary Information。该声明不否定公开额外图像，也不能证明补充
材料没有可用processed table。没有联系作者，没有绕过publisher限制。

## 为什么没有直接开数值建模

- 固定源码`Colony analysis.m`将TIF页作为z-stack处理，跨slice配准和投影；
  没有时间track或persistent colony ID。物理标定被注释，输出um名称不认证单位。
  这不证明论文没有time-lapse，而是这份脚本不能提供early/late连接。
- `Calculation.m`是已有Growth的posthoc窗口均值与4PL/Loewe分析，没有声明
  Growth的原始测量/归一化定义、真实药名、菌株、run、chamber或colony键。
  分析窗口数字不是已认证给药间隔；作者CI不是独立实测功能标签。
- 固定SHA的`growth_data.csv`含900行，三种Dosing_Type各300；共75个
  nominal dose/type组、300个唯一time/dose/type键，600个重复身份行。没有
  replicate键，不能把这些行当独立生物重复；也未认证该表是实测而非演示。
  图像、控制workbook和增长表之间没有可核join。Growth payload已下载并由
  schema worker解码，**研究者未见响应值或分布**；不能笼统称“未下载响应表”。

具体原始来源、逐行源码证据、身份计数和信息边界见
`code_discovery/REPORT_ADVOCATE.md`、`code_io_followup/REPORT_ADVOCATE.md`、
`schema_audit/REPORT.md`及`title_registry_audit/version_followup/REPORT.md`。
原阶段记录保持原样，后续版本/源码发现通过明确追加和新报告更新。

## 应用、范围与重新进入条件

可能的应用限于3D细菌微菌落抗菌实验选择，不称人细胞、PHH或临床疗效。
完整静态schedule表足以支持跨实验query→update→下一实验的研究agent；
**共同prefix的第二动作分支不是所有replay的门槛**。只有同colony state-feedback
控制或特定历史collision检验才需相应continuation交叠。停止当前配置的理由是
真实动作、响应来源和独立单位尚未认证，没有把弱任务擅自升级后再拒绝。

不下载多GB图像来猜缺失处理表，不将9个形态示例与generic A/B表拼接。
若将来取得公开或已授权的精确processed treatment/run/colony/time映射、功能定义
及全尝试/失败账本，可重新做outcome-blind资格；需在开dev前固定实际动作/utility、
group splits、查询成本和实用gain/停止阈值。作者申请或发消息不是本阶段授权动作。

## 实际交叉审查、测试与成本

支持方独立定位公开repo并审源码；数据审查方独立认证registry、版本和availability；
反方独立审查信息时序/同图像渠道/独立任务问题。根审查了三方证据并单独核CSV
identity，支持方修正其最初把共同prefix泛列为所有dev门槛的过强表述。

本轮LIST各新增阶段：repo4请求107,204bytes；registry/title/version5请求
47,803bytes；两源码2请求33,603bytes；两小表2请求2,820,980bytes。
**共13请求3,009,590 HTTP decoded body bytes**，不包括上阶段5请求19,943bytes。
原始body、状态/UTC/hash、失败与源码审计留在各阶段；没有模型/DeepSeek调用。
registry第一阶段29检查、version19检查及新增2个description合成检查通过；
root schema3个及identity5个不同检查通过。检查单位不同，不合并为生物样本量。

## 与核心机制和总目标的关系

同时提出的最小历史状态细分候选已进入独立立场评审和正式交叉辩论，见
`../antibiotic_state_refinement_review/`。它的新颖性不能由这个dataset的序贯性提供。
本次来源停止也不是“所有菌落世界模型无效”的结论。

真实世界模型贡献、Agent贡献、权重/程序继承、联合收益以及改善策略本身的
共同起点后继改善效率均NOT_TESTED。强直接模型、普通refit、持续学习、标准AL、
简单混合与等预算搜索仍是后续合格资产上的必要实际比较，不以软件测试代替。

下一项有具体方法/公共基因组入口的线索为Tripartite Loops，独立报告在
`../serial_antibiotic_alternatives/REPORT.md`。其完整功能菜单亦未认证；另登记的
metadata follow-up先查官方supplement/package入口和BioProject-linked身份，
不把SRA原始基因组误称完整MIC/growth replay。

## 小型技术偏差

根的一次PowerShell JSON只读失败：manifest含空字符串extension键，需要
`ConvertFrom-Json -AsHashtable`，后续改为该解析方式；没有写入或改变来源。
另一次尝试读取尚不存在的通用`STATUS.json`失败；实际支持方文件使用其自身名称。
这两次是本地只读错误，不是网络访问失败或科学阴性；后续改读已存在报告。
