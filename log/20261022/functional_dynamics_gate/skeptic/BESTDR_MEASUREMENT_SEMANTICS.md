# BESTDR：可用于预注册的测量语义边界

2026-10-22。只复用本代理已取得的原始 `BESTDR_PRIMARY.body`（SHA256 `ea88af53978f52b086dbb98f3326e24c141982eed0c83ba5203210d974b5725c`）及根代理传来的 CSV 表头/行数摘要；不新增 GET，不读取响应数值或源代码正文。CSV 文件存在与校验由根代理负责，本文件不独立认证其数据内容。

**可复制到预注册的段落：** 本实验先按作者原始论文把 HCT116 p53-VKI 视为单一已知细胞背景，药物为 cisplatin；作者方法为给药前24小时接种、给药后每4小时成像、持续72小时，具体 CSV `Elapsed` 的零点须经原始导出映射认证后再据其切 prefix。Incucyte 的 GFP+ 分割对象被作者称为 total cells，GFP+/RFP+ 共阳对象为当次图像中的 dead cells（ethidium-bromide 染色）；因此这些 dead readout 按**当前可检测死细胞存量**处理，不能当累计死亡事件 K。作者专门讨论 dead-cell clearance：脱附或崩解会使死细胞不再被计数；该机制在本文模拟中显式建模，但本 CSV 的 clearance 大小并未由方法正文认证。根代理所报 `tot_cells`、`intersect_dead_cells`、`intersect_live_cells` 只有表头身份，不能仅凭列名断言其数值满足 total=live+dead 或已实行何种交集/计数修正；须先认证后再用相应观测模型，不能以正增量累积伪造 death events。Fig2D 图注明确同孔三处区域、48孔，故 `img` 先作为潜在孔内空间技术子样本，须核对其与三处区域的映射；同孔 images 与连续时点不当独立培养/生物 run。`well` 作为物理培养孔标识使用，合并图像须先排除区域重叠和缺失，且孔数不能冒称独立给药日/培养批次。原文没有给出 CSV `seed` 的编码或含义；它既不能当随机数种子，也不能当已认证的接种密度/独立 run 标签。Date Time/Elapsed/row/col 也不自行建立独立 run。本文对其他实验的技术重复或三次独立 reprogramming 生物实验不能借给 HCT116。若无另行认证 run，分析限于此来源内部的孔/剂量或 chemical-heldout 开发，不声称跨 run 或跨细胞背景继承；相邻时间区间虽可构成条件似然因子，也不增加独立生物任务数。作者删除前20h、从24h后分析高剂量是已暴露的药效延迟选择，所有方法共享且不得根据 future 为新任务再选截断，不能把 post-delay 拟合称为早期延迟预测。

## 直接支持与未认证项

- 原文 Methods / Cell culture experiments 认证 96-well plate、Incucyte S3、10X、GFP total、GFP+/RFP+ dead、每4h/72h及给药时点。未具体认证 `intersect_live_cells` 的计算式、`seed` 取值含义、图像面积或 CSV 内 run 对应。
- Fig2D 原话："HCT116 p53-VKI cells were seeded and grown in cell culture for 72 hours in control (white) and 12.5 μmol/L cisplatin (turquoise) in 48 wells, recording viable cell count every 4 hours in three regions per well (dataset 1)." 不擅自把48解释为每臂48或48个生物实验。
- Results / Accounting for cell clearance 及 Fig3 明确 clearance 是脱附/崩解导致已死细胞从读数中消失。其 clear/no-clear 对比为 **in silico**，不证明真实 HCT116 表已测得该参数。
- Root 传来的两个表头为 `Date Time, Elapsed, well, img, tot_cells, intersect_dead_cells, intersect_live_cells, row, col, seed, concentration`，Replicates5472行，DoseResponse6624行；本文件不借这些行数倒推出独立样本数。
- Root 另报 HTS001 为14 drugs+control、7 PC9-derived backgrounds、各一plate，schema 缺 `expt.id`。本文原始方法给此类 HTS 每条件两个技术重复；这些信息不建立独立 run。本文正文另分析八个 breast-cancer lines/25 drugs，不得将该描述无条件强贴于当前 HTS001 文件。HTS001 的具体背景/plate roster 应以根代理实际 metadata 审计为准。

若后续只认证 stock 而未认证累计事件，建议采用含 measurement error/clearance 的普通 BESTDR 类 likelihood 或直接预测实际 readout；birth/death latent residual 仍须按模型推断报告。上述语义资格不构成 birth/death 参数识别、世界模型性能、继承或 RSI 证据。
