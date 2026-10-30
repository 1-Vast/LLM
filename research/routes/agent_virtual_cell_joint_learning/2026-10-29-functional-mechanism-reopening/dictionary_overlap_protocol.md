# B2静态交集资格核查（不是效果实验）

2026-10-29，运行前固定。问题仅为：已经读过的2018 HEK293/crizotinib或dasatinib、2025 Jurkat/dasatinib或dinaciclib，是否在既有普通GDSC2拟合表中有可核名字/药物与浓度范围的候选交集。不是证实靶点机制、选择性误差界或Agent收益；不选H/效应指标，不看功能响应。

固定源tmp/extq1/GDSC2_fitted_dose_response.csv，预期SHA2560883b3ef6e440603094c43c74044e1d333fce61e92e3efa374ea3a54f0b50302。仅访问列DATASET,CELL_LINE_NAME,SANGER_MODEL_ID,COSMIC_ID,DRUG_ID,DRUG_NAME,MIN_CONC,MAX_CONC中实际存在者；不访问LN_IC50/AUC/RMSE或其他响应。CSV整行暂时分词，名字只casefold并去ASCII空格/连字符/下划线；不合并HEK293T、不同clone或凭靶标猜药名。目标cell名字JURKAT/HEK293，目标drug名字DASATINIB/DINACICLIB/CRIZOTINIB，固定匹配所有行并导出唯一metadata行及原件行数。浓度单位无正式原件合同时保留unknown，不以默认uM的数值范围作已证物理交集。

一次主metadata扫描、CPU60秒/wall90秒/采样内存256MiB/输出≤2MB，0安装/GPU/作者代码/拟合/科学效果运行；输出新receipt存在则拒绝自动重跑。资格结果可为无名字交集、候选交集但clone/时间/单位/体系未匹配等，不把未找到解读成全部公开数据不存在。先核source hash，结束再核原件未变；原始response不转任何数值/输出。

DeepSeek预留DS030一次，用禁工具固定packet整理本次候选metadata及已核原文浓度/时间字段、按主负责人固定Decimal公式换算nM/uM与分钟/秒；不决定资格、H、指标或方法。新workspace/DSH_HOME、180秒/2048输出tokens/12000B stdin、声明USD0.025（非已验证硬美元cap），0自动重试/后端替换；历史21，授权新增1。root独立验字段/公式后采用。局部缺字段记录不阻其余已授权字段；本任务只到固定packet，结束查新task，无则在明确packet/预算内继续原默认source-well/time/control/repeats主线，不假称活后台。
