# Open TG-GATEs 身份资格结论

2026-10-22，Asia/Shanghai。**跨 lot 校正/继承资格：IDENTITY_NOT_ESTABLISHED，暂不进入数值实验。时间任务：有明确候选菜单，尚待功能配对与剂量选择血缘资格，不能说不可测试。** 未读取 DNA、LDH 或 CEL 数值，没有修改 OASIS 的 FAIL/STOP。

本区块在获取前登记 `PROTOCOL.md`。初始旧仓库路径与文本搜索未找到先前 TG-GATEs 数据、代码或实验使用证据，仅找到本轮刚新增的 `POST_RESULT_ADVOCATE.md` 中对这项资格的提及。这个阴性搜索不等于证明从未存在库外曝光，也不能用新目录重置历史。新下载属于元数据，不是新的独立实验。

## 官方身份资产实际提供了什么

根据 [官方 README](https://dbarchive.biosciencedbc.jp/data/open-tggates/LATEST/README_e.html)，cell sample 可用 experiment/group/individual、药物、浓度、时间与 barcode 关联表达和功能菜单。下载的两个身份档案都没有 lot、culture、source 或 donor 字段。

| 身份项 | 本次直接解析结果 |
|---|---:|
| 人原代肝细胞 sample / CEL attribute 行 | 2,610 / 2,605 |
| 药物标签 | 158 |
| 每药 experiment 数 | 全部为 1 |
| experiment/group/individual 重复键 | 0 |
| sample barcode 可与 attribute 精确对应 | 2,605 / 2,610 |
| individual ID | 1、2，各 1,305 行；不能等同两个供体 |
| Material ID | 全为 A；按官方定义是组织/材料片段编号，不能冒充 lot |
| sample 时间行数 | 2 h：424；8 h：1,082；24 h：1,104 |

浓度单位并不统一；有 μM、ng/mL、μg/mL，以及原样标为 μg/kg 的人 in-vitro 记录。保留原样，后续未认证前不将其换算/猜成 μM。相同药名、浓度、单位、时间的少量聚合会得到 4 或 6 行，不能在不保留 dose-level/group/individual 身份的情况下直接当额外生物重复。

两个 archive 的列白名单与纯人源身份输出见 `IDENTITY_CENSUS.json`、`HUMAN_CELL_IDENTITIES.json`、`HUMAN_CEL_IDENTITIES.json`。`CELL_VIABILITY` 链接列未被读取，更未下载功能表；因此本次不能推断 DNA/LDH 每个条件都有完整值。

## 跨 lot 与跨时间必须分开判断

[原始论文](https://pmc.ncbi.nlm.nih.gov/articles/PMC4384023/) 说明项目期间用了六 lot，来源涉及两家供应商，但这并不认证六 donor 或每个药跨六 lot 测量。论文指向 Supplementary Table S2；本次未取得该表。欧洲 PMC 的 supplementaryFiles 返回的 zip 只有八个论文图片/schema 图附件，列名检查确认没有 S2，未解码这些图片；不把 API 成功等于已看过补充表。

没有 sample→lot 映射，也就无法计算“同 compound-dose-time 跨至少两个真实 lot”的数量。当前是 **身份未建立**，不是证明其数量为零。六 lot 若只是不同药物批次，药物与背景会混淆；同药一 experiment、两个 individual 的现有布局不足以排除此问题。

时间菜单则确实存在：只用非 control 的药名、十进制定值浓度和原始单位匹配，396 个 compound-dose-unit 条件中，**156 个条件覆盖 2/8/24 h，涉及 52 药**；227 个覆盖 8/24 h，10 个仅 24 h，3 个覆盖 2/8 h。见 `TEMPORAL_IDENTITY.json`。这是后续早期状态/晚期功能反馈任务的线索，尚无数值或可预测性证据。不同时间的破坏性表达测量不是同一个细胞的纵向轨迹，也没有认证共同培养批次。

## 下一轮可以执行的资格及停止条件

只做以下身份/方法资格即可，无须本轮开值：

1. **DNA/LDH 完整菜单配对。** 独立白名单 worker 核功能表 schema 与 experiment/group/individual 的精确键、时间、实际浓度和单位；只输出覆盖、null-count、重复冲突及配对数，不输出 DNA/LDH 值、分布、活性标签或药物 shortlist。确认它是同条件对应的功能测量，还是不同培养/平行孔，并解释五个无 CEL attribute 的 sample。若必要功能/早期状态无法精确配对，停止相应时间任务。
2. **剂量选择血缘。** 论文方法明确 in-vitro 最高剂量按预实验生存率区间设置，难溶药受溶解度限制。因此 released high dose 自带先前反馈/选择信息。需要确认预实验采用哪种 viability、哪个时间/lot，与随后 DNA/LDH 是否独立；不能把已针对功能选择的剂量当未筛选的任意安全剂量菜单。`DOSE_LEVEL`、实际剂量及药物纳入都有此设计依赖，仅删除 High 标签不足以消除它。若作为已知先验允许，应对全部基线开放并计入初始反馈/成本，任务结论条件于该菜单；若无法厘清，停止“无先验新药剂量发现”主张。
3. **跨 lot 重开条件。** 取得 S2 或官方 sample/culture→lot 映射，认证 vendor/lot/donor/培养关系，并在实际 compound-dose-time 身份上展示跨 lot 重叠；再定义源/后续任务与支持反馈。没有共同动作或关系仍不清楚，就保持 cross-lot NOT_QUALIFIED，不改称 RSI。时间任务资格可以独立继续，不需等同于跨 lot 资格。

即使上述资格通过，仍需新的化学去重/分区和数值访问合同、强直接预测/普通重训练/主动学习等公平对照。仅获得 CEL 与早晚读出不能证明世界模型、智能体、程序继承，更不能证明改进策略本身在后续任务更有效。

## 来源、资源与失败

全部新代码仅在 `research/tggates_source_qualification_20261022/`，本目录保留来源、hash 与 `NETWORK.json`。脚本记录六次顺序请求共 **718,719 bytes**，低于 2 MB 的记录预算；web 检索工具不提供精确 body bytes，因此不宣称这是含工具检索的完整网络量。未下载 CEL/基因表达、DNA/LDH 表或 all-attributes 1.7 MB 混合结果 bundle。

官方两个 zip 是小型身份档案；解压后 CEL attributes 约 3.2 MB，仅为身份 CSV，预算约束为 HTTP body，并非解压字节。主 PMC 页面本次显示验证码而无法读取，因此改用欧洲 PMC 对同一论文提供的公开方法 XML。NAR 页面读取失败及 supplementary API 未返回 S2 均保留为未认证事项，不继续扩大下载。

一次身份解析因官方 CSV 的 CP932 编码而 UTF-8 解码失败，随后明确使用 CP932，未丢行或忽略字节；没有数值曝光。未运行模型、GPU、DeepSeek、任何 endpoint 实验；获取身份资料与可测试任务资格分别报告。
