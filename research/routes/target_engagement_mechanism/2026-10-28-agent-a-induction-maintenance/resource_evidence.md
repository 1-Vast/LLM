# 形成与维持：公开生物协议资格核查

2026-10-28；角色为原始生物证据。requested gpt-6.1-sol/medium；effective unknown。使用 lit-survey 的定向核验/P级证据规则。结论：取得一篇2025原始论文，真实支持“建立persister→撤药→功能敏感性恢复”这一历史过程；**没有核实到同一干预在形成前与形成后首次启动的完整比较**。因此可用作科学问题的直接近祖和协议锚点，不能当作已资格通过的维持机制决策数据。本轮新core=1，外部操作2/2，0重试，0拟合/实验/安装/API模型调用。

## 查询前选择门

见 sources/resource_evidence/precommit.md。能改变选择的结果是：耐受已建立后才首次撤除环境或启动机制干预，并有再挑战、独立存活/克隆功能和明确重复单位。若仅同步保护/联合给药，就不能以其声称逆转已建立耐药。优先2025—2026；不因没取得补充就称缺失。

## 本地复用与范围

先查 reference/papers.tsv（含已有2024 monoclonal-subpopulation、2015 eLife和2025PNAS记录），读已有PNAS JATS的参考文献列表，识别其R5/R7/R8/R77等直接候选。未重复获取PNAS，未取得其SI；SI由协调者核验。没有读取任何药效/RNA矩阵、S3或封存数据，没有提取效果数组。此报告不以矩阵或表达差异认证功能。

## 唯一新资源：Punzi et al., 2025

[Early tolerance and late persistence as alternative drug responses in cancer](https://www.nature.com/articles/s41467-024-54728-7)，Nature Communications 16:1291；页面原文发表日期2025-02-03，DOI 10.1038/s41467-024-54728-7。实际取到完整主文HTML（有Abstract、Results、Methods、Data/Code availability及补充链接），虽最终URL含cookie参数，但内容不是仅认证占位页。实际阅读等级P，范围见下；没有读补充原件或全部原文。搜索命中综述仅作发现线索，不支持本报告的方法结论。

### 可核事实

- 背景与操作：HCT116 CRC；主文Results说明初始16h后追加两周化疗，再撤药5周（drug holiday），并指向Supplementary Fig5a/c的设计与恢复化疗敏感性。Methods更精确规定persister制备为1.2×10^6 HCT116/6cm皿、持续两周，每4天换液补药；撤药加完整培养基，以chemonaive细胞为对照。两处16h+两周与Methods“两周”的微小计时口径差保留，不能自作统一。
- 药物×背景：HCT116 persister条件中的FOLFOX写作5-FU 10µM + oxaliplatin 1µM，FOLFIRI对应5-FU 10µM + SN38 10nM。这里是作者对体外组合的命名，不擅自补入leucovorin。早期8/16h条件浓度不同，不能视为唯一变量仅为时间。
- 靶点/遗传参照：ULK1i SBI-0206965，HCQ与ATG2A/ATG5/ATG12 silencing用于自噬对照；PINK1 shRNA有两条序列ID，scrambled shRNA；HNF4A esiRNA有LUC对照。Methods描述PINK1在化疗前感染/筛选，非可核的形成后诱导开关。
- 真正有关维持的Fig6g：mCRC PDO17**先感染**silence PINK1或SCR，**然后**FOLFOX/FOLFIRI一周，图虚线为drug holiday；n=3 experimental repeats。Results说该设计涉及撤药后的恢复。不能据此把PINK1作用分解成“形成概率”与“形成后维持”的独立因果效应。
- 独立功能：主文Methods有晶紫存活/增殖和克隆形成（1000 cells/6-well、给药24h后、7天终点、triplicate）；不同于RNA代理。但这个克隆实验是同步组合，自身不是建立后逆转。恢复敏感性指向SFig5c，尚未获得那里的浓度、再挑战持续时间、洗脱/传代和重复定义。图6g给3实验重复，主文未把它细化为不同患者或独立起始克隆；不得把n=3称3患者。
- 状态与谱系：Fig4a所述HCT116 time points为8h/16h/2weeks/5weeks DH，2 experimental replicas；有barcode过程。这里只核方法存在，没有读取barcode数组；2个实验重复不能替代功能再挑战重复。

### 数据入口与尚缺资格

主文Data availability声明Source Data及ArrayExpress E-MTAB-12946/12948/12947/12952/12953（bulk），E-MTAB-12949/12950/12951（single-cell/barcode），E-MTAB-13597（CUT&Tag）；入口存在不等于功能矩阵已核验。本轮不访问这些数据。

官方补充方法/图入口（只从本地主文提取，未请求）：https://media.springernature.com/original/springer-static/esm/art%3A10.1038%2Fs41467-024-54728-7/MediaObjects/41467_2024_54728_MOESM1_ESM.docx 。文章末亦列MOESM3–6 XLSX和MOESM8 ZIP；未下载、未确定哪一项承载功能原始值。不能承诺配对历史×后续动作表可直接构建。

**能检验什么（推断）**：若补充验证再挑战和重复，可建立不同既往暴露→撤药→再次同药的预测问题，并以功能作终点；可拒绝把“持续用药16h和两周”当同一耐受状态。**还不能检验什么**：同一ULK1/PINK1干预在形成前与形成后首次给定的时间因果交互；也无跨化学实现干预的唯一预测资格。最缺的是建立后才开启靶点干预、匹配起始persister数量与再挑战独立功能重复。现有工作足以否定“撤药可逆或早/晚状态区别本身新颖”，不足以否定更严格的维持机制假设。

## 原始回执、时钟和阅读定位

sources/resource_evidence/search_receipt.json保留唯一主题查询工具响应；search_manifest.json记录查询UTC、回执bytes/hash，工具未暴露网络payload字节数，故不编造。原生查询结果没有升级全文证据。请求2的起止UTC 2026-10-28T11:56:15.883084+00:00—11:56:22.156152+00:00，6.273s，HTTP200 text/html，694917 bytes，SHA256 b1aab3c40b13096880ef11447d8aca3b6622cb7c7b618bcba1273f35e7db21b4。完整请求状态见fetch_receipt.json；原始punzi_2025.html。下载原件共694917 bytes，少于2MB；搜索响应payload大小未知，单独保留回执大小，不混称下载原件。

本地派生punzi_2025_reading.txt的阅读范围：23–30（身份日期），86（摘要），114/129/133（功能协议/重复说明），139–146（给药→撤药及barcode方法描述），151–162（PINK1/HNF4A及Fig6g协议），175–181（功能/培养协议），214（遗传参照），267–270（数据/代码声明）。初次输出曾截断，随后单独恢复139–146、157、175–181、214、267–270；无截断段落承担具体资格结论。没有据任何文献药效结果运行本项目实验。全文取得不等于补充和重复全通过。

## 停止门

已耗尽本角色1条查询+1次获取；不重试、不为补充换来源。报告合格“直接近祖/部分协议”，完整形成vs维持干预资源仍NOT QUALIFIED，尚未取得不等于不存在。下一步必须先恢复该文SFig5/6及功能源数据结构，或取得建立后才开干预的等价原始协议，才可考虑正式实验。
