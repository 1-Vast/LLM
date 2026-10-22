# LIST公开代码仓库：来源形态与关联边界

2026-10-22，Asia/Shanghai。按本阶段预登记完成4次GitHub公共metadata请求、**107,204bytes**，全部HTTP200且完整，停止本阶段新增请求。**发现有用的真实公开仓库与直接数据DOI链接；可执行处理—轨迹—功能菜单仍未认证。**

## 实际发现

精确title词组readme搜索返回0，不能据此说代码不存在。随后`microfluidics antibiotic in:readme`返回72个repo，本轮只读取前10条repo元数据，其中 [Uchicago-TAY/LIST](https://github.com/Uchicago-TAY/LIST) 为具体候选。没有审计全部72项，更没有将无关文献收藏repo当作者代码。

仓库metadata显示2025-06-23创建、default branch `Code`、本次updated-at为2026-08-17。官方README将平台称为 *LIST (Large-scale Integrated System for Testing), Ultra-multiplexed Microfluidic Platform for 3D Microbial Culture and Antibiotic Susceptibility Testing*；其maintainer标识与论文第一作者线索一致，但**同实验室/同作者不足单独认证目标论文关联**。

已取得[官方README](https://github.com/Uchicago-TAY/LIST/blob/Code/README.md)及完整tree metadata。tree SHA为`901539f1327832320b3808c0efda06f2dd2ca6ab`，151entries/137blobs，`truncated=false`；这是**tree SHA，不冒称commit SHA**。README blob SHA为`a0491e381e1fd657e4b6bc37945a80f0bcf0a8b2`、7,449bytes；本地按Git blob算法重算一致，并与tree内entry一致。解码原文保存在 `LIST_README.md`，机器清单为 `INVENTORY.json`。

README明确：GUI操作、real-time colony tracking、antibiotic组合分析；512条件示例、九抗生素名称（amikacin、cefepime、clindamycin、levofloxacin、nitrofurantoin、rifampicin、sulfamethoxazole、tetracycline、trimethoprim）；growth-curve分析注释包含simultaneous A+B及sequential A–B/B–A、Loewe/4PL。**这都是README对软件/示例的说明，不证明各动作均有真实测量。** 512二值组合控制配置与论文2,700 drug-dose菜单不应直接合并，不能由此补出实际dose/lag/菌株。

README直接声明：`Additional image data are available at DOI:10.5281/zenodo.18362221.` 因而 **repo→该Zenodo DOI的直接链接已认证**；目标paper DOI/title在这份README均不存在。另一独立审查者随后在 `title_registry_audit/ZENODO_DESCRIPTION_CITATIONS.json` 中核到记录22118144的description含目标bioRxiv DOI，这确实增强paper→image-record链，但该记录与README链接18362221的version/concept关系应由其metadata精确认证，不能因数字相近或同作者猜测。

## 只取得文件名/体积/SHA的菜单

| 精确repo路径（branch Code） | bytes | 本阶段含义 |
|---|---:|---|
| `3. Operational File for GUI/512 Chip Seq (Run).xlsx` | 27,740 | 潜在运行schedule；未打开，不能认证实际药物映射/时间。 |
| `3. Operational File for GUI/512 Chip Seq (Function).xlsx` | 113,741 | 潜在function/valve映射；未打开。 |
| `3. Operational File for GUI/Supplementary File (Multiplexing control).xlsx` | 2,029,932 | 可定位的supplementary配置文件；未下载，不将文件名当完整实验menu。 |
| `4. Colony Tracking, Combination Index/Colony analysis.m` | 14,280 | 潜在tracking/segmentation定义；仅文件metadata，尚未读源码。 |
| `4. Colony Tracking, Combination Index/Syngergy Calculation/Calculation.m` | 9,694 | 潜在growth/synergy定义；保留原路径拼写`Syngergy`；尚未读源码。 |
| `4. Colony Tracking, Combination Index/Syngergy Calculation/growth_data.csv` | 17,137 | 可能响应表，**保持未开**。 |
| `4. Colony Tracking, Combination Index/Syngergy Calculation/curve_fitting.csv` | 154 | 可能拟合参数，保持未开。 |
| `4. Colony Tracking, Combination Index/Syngergy Calculation/synergy_results.csv` | 7,595 | 可能派生响应，保持未开。 |
| `4. Colony Tracking, Combination Index/Syngergy Calculation/Set 2/growth_data.xlsx` | 24,295 | 可能第二示例响应，保持未开；Set2不是认证的独立任务。 |

tree还列出9组`Colony1..9` TIF/label TIF/CSV、9个`Results_i.xlsx`、GUI硬件接口代码、图示和CAD文件。它们的**存在/文件名**已经认证，内容未取。9个colony示例不能作9个strain或独立实验run。137blobs中61个.m、21个.xlsx、12个.csv、18个.tif；都不是独立生物样本数。

## 最小下一步与当前停止边界

最小依赖核查是上表两个固定SHA的.M源码I/O：先确定state/growth定义、是否用未来帧、input/output字段、treatment/run/chamber/colony键与示例常量，而非先读任何growth/synergy CSV。源码只阅读不执行；若源码本身含响应常量，则明确记作source exposure，不能充当未见终点。根代理已另授权一个独立2请求/100KB代码I/O阶段，其预注册与结果将置于单独目录，**不改写本4请求阶段结论**。

只有对应schedule和轨迹metadata可join、真实运行与示例区分、共同prefix第二动作分支及独立run/context认证后，才可考虑另行dev-only数值合同。共享成像growth与morphology仍需count/早期growth extrapolation、直接dose/order模型和普通动态模型的强比较。来源可用性也不自动产生world/Agent/继承/RSI的新颖贡献。

原始API JSON和receipt都在 `sources/`，无失败请求或source overwrite。metadata脚本与本地清单脚本分别为 `research/antibiotic_schedule_qualification_20261022/advocate_code_sources.py`、`advocate_code_inventory.py`；没有clone、图像或响应矩阵下载，没有执行第三方代码、模型、DeepSeek或实验。自动DOI提取曾把README句号包含在字符串末尾，已只移除末尾标点，raw README及source/hash未改。
