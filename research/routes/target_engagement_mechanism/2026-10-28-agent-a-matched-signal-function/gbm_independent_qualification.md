**GBM FAK–MEK 2025：独立资源资格核查**

日期：2026-10-28。`effective_model: unknown`。先读 BRIEF，再独立读指定原文；未读父 agent 分析。仅核本地全文、章节抽取和来源回执；0 联网、0 训练、0 sealed 读取，未读取数值功能表挑 split 或阈值。以下“未知/未核”是本次证据边界，不等于断言网上不存在数据。

结论：这是确有同研究信号与功能测量、并有遗传干预参照的候选资源，值得追索数值附件；**当前不能启动 CL1 的整药留出程序充分性试验**。RPPA 只覆盖一个 MEK 化学实现和一个 FAK 化学实现，功能与 RPPA 的精确剂量、重复及培养合同尚未逐行闭合，也未取得可追溯数值矩阵。可发展限定的同背景预测问题；尚不能声称已识别机制、跨药迁移或新增药物决策收益。

**来源与定位约定**

原文为 *Drug Combinations Targeting FAK and MEK Overcomes Tumor Heterogeneity in Glioblastoma*，DOI `10.3390/pharmaceutics17050549`，PMCID `PMC12114623`，2025 年。证据源为 `sources/gbm_fak_mek_2025.xml`；`sources/gbm_fak_mek_2025_sections.json`用于核对章节。XML 的 front/article-meta/article-title、article-id、history 可核身份。回执记录 EPMC fullTextXML、HTTP 200、177728 bytes；本核查未重新联网验证回执。

下文“§3.6 P1”表示 XML `sec3dot6-pharmaceutics-17-00549` 的第一个直接子 `p`，其他章节同理；Fig.7 表示 XML `pharmaceutics-17-00549-f007` 的 caption。Supplement 为 `app1-pharmaceutics-17-00549`；Data availability 为 `notes4`，在 associated-data 中另有重复声明 `_adda93_`。这些 ID 比单行 XML 的行号更能稳定定位原文。

**药物、背景、暴露与功能覆盖**

| 实验块 | 原文可核合同与测量 | 对 CL1 的边界与定位 |
|---|---|---|
| NPE 遗传筛选 | 小鼠神经干细胞衍生 NPE：Nf1/Pten 缺失、EGFRvIII；CRISPR 敲除 FAK 后，在同一克隆群体重表达 WT 或 K454R kinase-deficient FAK。四库合计作者报告 2586 化合物，30/100/300/1000 nM，48 h，终浓度 0.1% DMSO；PrestoBlue 代谢活性，按板背景扣除及 DMSO 归一化。 | 有 FAK 催化活性改变的遗传参照；这不是多独立克隆验证。未见 NPE 的 RPPA 矩阵。§2.1 P1、§2.2 P1、§2.3 P1、§3.1 P1、§4 P1。2586 是作者库条目数，唯一化学实体数未知。 |
| NPE 药理验证 | trametinib、GDC-0623、cobimetinib、mirdametinib 四种 MEK 抑制剂验证 WT/KD 敏感性差异。后续 VS4718 × trametinib 或 GDC-0623，2D/3D 的 7×7 矩阵，有单药臂。命中复测 8 点 10–1000 nM；NPE 功能终点 48 h。 | 同类有不同化学实现的功能证据；不能将它们视为已测相同程序。WB 有 pFAK/pERK 验证，但正文/图注不足以恢复 Fig.2F 的完整剂量、时间、样本行。§2.2 P2、§2.6 P1、§3.1 P2、§3.2 P1–P3、Fig.1–2。 |
| 人源 2D 功能 | 14 株患者来源 GBM stem cell；单药 VS4718、trametinib、GDC-0623，72 h。组合包括两 MEKi（trametinib、GDC-0623）×两 FAKi（VS4718、AMP-945），7×7 矩阵，Hoechst 核计数经 DMSO 归一化为 % cell survival。典型 2D 剂量：FAKi 100–500 nM，MEKi 1–25 nM。Fig.5 报告 36 个组合实例、1296 剂量变化，部分组合 QC 失败移除。 | 14 背景×4 配对不能自行扩成完整 56 组合；具体缺失/QC 行未知。核计数是细胞数量端点，不能直接当作死亡率；PrestoBlue 也不是直接死亡计数。§2.1 P2、§2.4 P1、§2.6 P1、§3.4 P1–P3、Fig.4–5。 |
| 人源 RPPA | E13、E57 的 2D，DMSO 0.1%、trametinib 100 nM、VS4718 300 nM、两药组合，24 h。G7 3D 另做“a corresponding experiment”；叙述对应相同处理方案，但 G7 各样本实际剂量仍须核 Fig.7B 标签/样本表。总/磷酸化蛋白抗体信号，按总蛋白 Fast Green 归一化，再计算相对 DMSO 的 log2 fold change。 | 最多是 3 个背景–培养组合×4 臂的名义条件，不能当作 12 个独立生物重复。未见 GDC-0623 或 AMP-945 的 RPPA；更没有四种 MEKi 均具实测程序。E13/E57 是作者按单药耐受/敏感选择的背景，不能再包装成盲选的独立外部评价。§2.11 P1、§3.6 P1、Fig.7。 |
| 人源 3D 功能 | 2000 cells/well，先成单球 3–4 天，4 mg/mL Matrigel，随后加药；每 3 h 记录侵袭，方法写 12 天。Fig.6 图注写 11 天，并以 72 h 标“day 0”、264 h 标约 8 天加药后。附件目录的 Fig.6 视频标 trametinib 100 nM、VS4718 750 nM。方法的“典型 3D”剂量另写 MEKi 250 nM、FAKi 3 µM。 | 这些条目不能替代逐样本给药记录；需厘清播种、成球、加药三个时间原点。侵袭面积明确排除球芯面积，不能换成球大小/活性。若 RPPA 使用 300 nM VS4718，则不能与 750 nM/3 µM 功能视作精确配对。§2.6 P1、§2.7 P1、§3.5 P1、Fig.6、Supplement。G7 有 caspase-3 附图线索（§3.6 P2、Fig.S7 目录），实际数值与完整条件未知。 |
| 体内参照 | NPE 和 G7 颅内移植；VS4718 75 mg/kg 每日两次、每周 7 天；trametinib 0.5 mg/kg 每日一次、每周 5 天，0.5% hydroxypropyl methylcellulose，四臂。NPE 结果为两周，G7 结果为一周；Fig.3/8 各组 n=5，组织染色面积终点。 | Methods §2.9 统一写两周，而 §3.7 明写 G7 一周，需保留差异，不能自动统一。体内外剂量、培养、暴露均不同，不能直接拼成 RPPA→体内功能的匹配样本。§2.9 P1、§3.3 P1–P2、§3.7 P1、Fig.3/8。作者报告组合组部分体重下降；不宜只用肿瘤面积定义无代价决策效用。 |

正文还有身份/单位不一致：§3.2 P1 写 GDC0632，后文为 GDC-0623；§3.4 P3 写 VS4728，Fig.5 为 VS4718；§3.4 P1 将 VS4718 单药上限写作 1 mM，不能自行改成 1 µM。应由附件化合物 ID/剂量字段解除歧义，而不是静默修正。

**RPPA 与功能：同研究成立，精确条件配对尚未成立**

1. E13/E57 的候选配对是 24 h 四臂 RPPA → 72 h 2D 核计数。早晚来自独立终点取样，原文没有声称同细胞配对；这种设计原则上可做条件层面的预测。但 RPPA 的 trametinib 100 nM 超出 §2.6 写的典型 2D 组合 1–25 nM。单药 dose–response 覆盖某个剂量，也不证明组合矩阵含有 100/300 nM 这对剂量。必须取得真实行标签才能宣告交集。
2. G7 的 3D 24 h RPPA → 后期侵袭/凋亡也是候选，实际剂量与培养阶段尚未逐行闭合。一般方法、视频名称和“对应实验”不是可互换的样本清单。不得以最近剂量、改换功能端点或重新定义时间来制造配对。
3. 通用培养基和载体记录优于跨研究名义药名拼接，但它不自动证明 RPPA 与功能实验的播种密度、预处理时间、加药/补药、培养基更换、成球成熟度、批次完全相同。当前只可说“同研究、候选条件相连”，不能说“同暴露已验证”。§2.1、§2.6–2.7、§3.6。
4. RPPA 报告 127 抗体（Methods/Results），Discussion §4 P4 写 136 targets including controls；真实特征集/控制探针/缺失值仍待附件。§3.6 P2 的 pMEK 位点写 Ser217/224，§4 P4 写 Ser217/221；抗体 ID/特异性应以 S2 原表和原始样本表核实。不能据文字生成精确程序字段。

**重复单位及所谓 target engagement**

| 证据 | 可核重复/测法 | 不可外推的结论 |
|---|---|---|
| 功能剂量复测、矩阵、3D 侵袭 | §2.3 写 triplicate 且至少 3 biological replicates；§2.6 写矩阵 triplicate、至少 3 biological replicates；§2.7 写侵袭 3 biological replicates；人源成像 §2.4 也写至少 3 biological replicates。 | 生物重复运行、技术孔、plate、日期及克隆对应表未取得；“n=3”图注不能替代 run_id。技术孔、每孔 6 个视野和每板 48 DMSO 孔不作生物 CI。 |
| RPPA | §2.11 为每裂解样本四点稀释、线性拟合 QC（R²>0.9）、重复阵列/slide 技术流程。 | 四点稀释是技术标定，不是四次生物实验。RPPA 每条件独立裂解/生物重复数未明示；Fig.7 的“三次独立实验”指 C–E Western 验证，不能移给 A–B RPPA。 |
| Western | §2.8 明写 3 biological replicates；Fig.7 C–E 最少三次 separate experiments。§3.2 P3 用降低 pFAK/pERK 验证“on-target”。 | 这是通路药效标志物，不是直接药物–蛋白占据测量；MEK 抑制后 pERK 是下游读出。 |
| 体内“target engagement” | §3.3 P1：trametinib 0.1/0.5/1 mg/kg、VS4718 75 mg/kg，口服灌胃三天后，肿瘤裂解 WB 检测 pFAK(Y397)、pERK(T202/Y204) 下降；对应 Fig.S4 目录。 | 实际方法不是 CETSA、NanoBRET、竞争结合或化学蛋白组占据；本文未报告这类直接测法。三天取样也未被证明与随后肿瘤面积终点为同只动物；其生物 n 未在该正文段落给出。 |

遗传 WT/K454R 对照增强了“FAK 催化活性改变会影响 MEKi 功能反应”的干预依据，但该证据在小鼠 NPE 背景；它不能自动识别人源 E13/E57/G7 中每条 RPPA 因果链。未见在这些人源条件下对 RSK2 进行遗传扰动/药理救援并同时测信号与功能。pRSK2S227 降低和 c-PARP/caspase-3 增加仍是作者已报告的关联/药效线索，不足以证明 RSK2 是组合疗效必要中介。§2.1 P1、§3.6 P2、§4 P4–P5/P8。

**公开数值和附件的实际状态**

| 项目 | 本地/原文可核状态 | 仍未知 |
|---|---|---|
| 全文与章节抽取 | 已读 XML 177728 bytes、sections JSON；正文含图注、条件和作者汇总。 | 这不是可执行的条件×重复×蛋白/功能数值矩阵。没有从热图反推功能值。 |
| 正式补充 ZIP | XML `supplementary-material` 的 media 指向 `pharmaceutics-17-00549-s001.zip`；另有 associated-data 重复节点，不能算两个独立附件。Supplement 给出官方 `/s1` 链接。 | 本次 sources 清单中无 ZIP；未下载、未展开，大小、文件清单、表内数值/完整性未知。 |
| 附件目录 | Fig.S1–S8；Table S1 分子背景、S2 抗体表、S3 screening data and hit selection；四个 Fig.6 视频。§3.1 P2 称 S3 是 complete ranking。 | 不保证 S3 含完整原始剂量×重复、所有 QC 失败记录或人源组合；目录未明确列 RPPA 原始矩阵或 Fig.4–6/7 的 source-data 工作簿。§2.8 又称 S2 是 Western 抗体表，实际用途须开表确认。 |
| Edinburgh DataShare | Data availability 原文为 “will be made available ... via an open access doi link”，仅给 `https://datashare.ed.ac.uk/` 根网址；另称其他数据材料 upon request。 | 当前全文不含具体数据集 DOI/accession。不能把未来式承诺当已公开数值，也不能据本次未联网宣告全网无数据。RPPA 是否属于公开“drug screening data”亦未明示。 |

**最小可提出的预测问题与启动条件**

最小问题可限定为：**在 E13 或 E57 的固定 2D 背景中，固定精确给药/培养合同后，24 h 实测蛋白信号能否预测 72 h DMSO 归一化核计数？** 该问题允许不同时间、不同取样细胞；目标必须明确为后期细胞数量，不将它命名为机制识别。它目前是候选问题，尚未达到数值试验可执行状态。

最小启动包是：按真实 `cell_line × culture_2D_3D × compound_id × concentration_nM × treatment_start/harvest_time × vehicle × biological_run_id × technical_well_id` 对接的 RPPA 和预定功能数值；缺失、QC、归一化、重复层级及培养合同；同条件 DMSO。先只核字段、单位、计数与条件交集，再冻结终点、split 和程序定义，避免查看功能值选出有利背景/剂量。若精确交集为空，应保留该负资格结论。

即使拿到 E13/E57 各四臂完整数值，也只有每背景控制、两个单药、一个组合的稀疏条件集，不能把 127 抗体或技术重复扩成有效样本量。以所有 127 读数直接充当“程序”可能只是记住处理臂；以本论文已筛出的 pRSK2/c-PARP 作为最佳程序再用同批功能评价，也有后验选标风险。若把已发表发现作为先验，仍需独立评价其预测增益。

对原 CL1 问题“给定背景和预定义实测程序后，药物身份是否仍预测功能残差”，本资源当前额外缺少：

- **跨药程序：**功能端有 GDC-0623、AMP-945 等不同化学实现，但 RPPA 端只见 trametinib/VS4718。需要至少同程序语义下的另一化学实现同时有精确信号与功能，并独立校准程序。相同 target 注释或不同药物都“有效”不足以定义同一程序；只把唯一 MEKi 整药留出，会把药物身份与整个干预类别一同拿走。
- **机制：**直接占据不是唯一有效参照，本文确有 NPE 遗传证据；缺的是人源相关条件下可区分候选链条的干预/救援及其匹配数值。不能从反馈 pMEK、pRSK2 与 apoptosis 共变推导唯一机制。
- **决策：**尚无冻结的实际损失/方向、可行药物动作集、独立反馈/评价单元和基线误差/headroom 数值。侵袭可早增晚降、肿瘤面积有毒性代价，不能事后换时间/端点取得收益。CSS、synergy 及单药/组合优势均为原文已计算结果，不等于 Agent 相对同信息强直接预测器、普通程序模型、自由潜码辅助监督或充分重训练的独立决策收益。
- **跨背景/跨任务：**E13/E57 是按已有敏感性选择；G7 同时改变细胞背景和 2D→3D 培养，不能分离两者。14 个功能背景不代表 14 个匹配 RPPA 背景。整背景留出/向体内迁移需额外可比数据，当前不支持通过性结论。

**与原文发现的重复风险及下一证据**

FAK-KD 增强 MEKi 敏感性、多个 MEKi/FAKi 的组合、14 株人源谱系的加和/协同、侵袭动态、pMEK 反馈且 pERK 受抑、pRSK2S227 与凋亡标志物、体内面积下降，均已在本文 §3.1–3.7 和 §4 报告。重新得到“FAK+MEK 组合好”“RSK2 是共同标志物”不能算本项目发现；§4 P2/P8 还明确承认 FAK+MEK 在其他癌种的既有工作。原文把 RSK2 称 potential biomarker，不能升级成已证必要中介。

本项目可新增的内容只可能来自预先冻结、独立单位和同信息强基线下的程序充分性/证据更新/决策收益检验；本次没有做这些实验，也未证明存在足够可识别设计。

**下一项最小缺失证据：**先取并核官方 `s001.zip` 的文件清单和表字段，以及具体 DataShare 数据集 DOI；决定性核对是 E13/E57（及 G7）是否有与 24 h RPPA 精确剂量/培养对应的功能源行、RPPA 生物重复和数值矩阵。该交集成立后，仍需另一同类化学实现的匹配信号，才能把限定预测开发推进到原定跨药充分性检验。当前保留候选资源，不启动训练，不将数据资格替代机制/决策/迁移结论。
