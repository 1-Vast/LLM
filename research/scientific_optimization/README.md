# MAESTRO 双核心调整：2026-09-27

本次按“技术调研＋最小实现＋测试与实验”执行。新增可训练的条件群体流后端，
修复现有世界模型丢失 RNA 方向的问题，并修复智能体两处科学解释歧义。
没有替换默认 State checkpoint，也没有将开发集成绩写成机制发现或药物疗效提升。

## 世界模型的实际变化

1. `src/virtual_cell/learned_response.py`：原 RMS 汇总保留，同时支持
   `rna_gene:<gene>` 和显式注册的 `rna_set:<identifier>`。相反方向的响应不再
   被同一个 RMS 数字混同。基因集成员、来源和来源哈希进入模型版本；缺失成员拒绝查询。
   三个种子的范围仅表示模型分歧，不是预测置信区间，更不是细胞异质性。
2. `src/virtual_cell/population_flow.py`：新增实验性 **control population →
   conditional population** 后端。以单细胞状态、对照群体均值/标准差、药物指纹、
   剂量及数值流时间作为输入；使用 minibatch 最优传输构造未配对群体间的训练路径，
   训练条件速度场，以 midpoint 积分输出细胞群体。验证集 MMD 选择 epoch。
   零剂量严格保留输入群体；预测随细胞排列等变。
3. 群体均值/标准差是最小的集合编码器。没有声称复现 STACK 的二维注意力、
   State 的 set Transformer，或完整 CellFlow。未实现蛋白/ATAC 解码器，
   因为现有本试验没有这些模态的配对测量。流时间 0–1 不对应生物学小时；
   OT 配对不对应真实细胞谱系。模型保持输入细胞数，不预测增殖或死亡数量。

旧世界模型读数接口已经改动。新群体流目前使用 `predict_population` 数组接口，
**尚未接入智能体的默认 `PredictionRequest` 路由**；其 PCA 坐标输出也不冒充
有名称的 RNA、靶点占有率或功能活性。这是明确的实验后端边界。

## 两个真实数据实验

### 单细胞群体流：小规模筛查通过，未晋级默认

方案见 `POPULATION_PROTOCOL.md`，运行器为 `population_pilot.py`。
实际读取 4,245 个独立行 ID 对应的真实细胞，24 个化学连接结构组，共 42 个条件群体。
16/4/4 个结构组用于训练/验证/测试；测试有 8 个群体。部分药物只有一个满足条件
的重复，因此条件群体数不是 48。每个群体采样 64 个细胞，同板、同重复匹配对照。
采用已审计基因标注偏移；128 基因筛选和 16 维 PCA 仅拟合训练对照细胞。

| 方法 | 等药物权重 MMD² ↓ | 群体均值 MSE ↓ | 群体方差 MSE ↓ |
|---|---:|---:|---:|
| 保持对照不变 | 0.038351 | 0.379862 | 2.067822 |
| 训练平均位移 | 0.038312 | 0.380179 | 2.067822 |
| 化学近邻位移 | 0.077254 | 0.906975 | 2.067822 |
| 条件群体流 | **0.035625** | **0.359014** | **2.038099** |

验证集选择第 7 个 epoch，未根据测试结果重新调参。相对平均位移，MMD² 下降
约 7.0%，方差误差下降约 1.4%；不能把有限的群体分布改善说成完整刻画了细胞异质性。
这里只有 A549、24 h、1000 nM；不证明跨组织、跨时间、跨剂量泛化。
不同药物可能共用对照细胞；4 个结构组不是充分的独立外部验证。历史 2473 基因
候选池曾利用全部对照，故不能宣称整个预处理都对本次测试全盲。

结果：`outputs/scientific_optimization_20260927/population_pilot_run2/summary.json`。
同目录保存 checkpoint、坐标变换、行 ID、分割、学习曲线、预测和条件级指标。
第一次启动在元数据读取阶段因未选中行也含空标签而终止，未训练或评分；修正为
保留空值并在目标条件筛选中排除后得到 run2。原空目录保留，不覆盖任何既有结果。

### 定向 RNA 读数回归：筛查失败，未替换原模型

方案见 `PROTOCOL.md`。2,250 条件、188 药物、185 连接结构组、50 个冻结 Hallmark
RNA 读数，复用历史 5 折预测作比较。直接读数 ridge 的等结构组 MSE 为
0.00107017；现有化学 ridge 为 0.00106410。两者差异的描述性 95% 区间跨零，
相对近邻的区间同样跨零，因此候选不满足预设的全部基线优势门槛。
比零效应和均值基线好，不足以支持替换强基线。

结果：`outputs/scientific_optimization_20260927/readout_pilot/summary.json`。
这也意味着“保留方向信息”是接口正确性改进，不能自动推出新训练目标更优。

## 智能体实际变化

- `src/agent/planner.py`：两个假设必须有不同的非空 ID 和明确描述；不再为缺失
  科学定义填入默认占位文字，违规返回进入现有有限重试流程。
- `src/maestro/outcome.py`：重复规则 ID 拒绝注册；同一观测匹配多个规则时返回
  歧义，不再根据注册顺序选第一条并淘汰假设。已有跨轮假设一致性和证据准入逻辑复用。

以上是实际生产解释路径的修复。没有运行新的真实干预实验，也没有证明前提修复
或动作选择收益；现有任务可识别性、所选动作风险校准问题仍需单独解决。

## 使用与复现

在仓库根目录、已安装 research 依赖的 Python 环境执行，输出目录必须不存在：

```powershell
python research/scientific_optimization/population_pilot.py --output outputs/my_population_run
python research/scientific_optimization/readout_pilot.py --output outputs/my_readout_run
python -m pytest tests -q -p no:cacheprovider
```

新后端最小推理 API：

```python
from virtual_cell.population_flow import ConditionalPopulationFlow
import torch

model = ConditionalPopulationFlow(dimensions=16, condition_size=129)
model.load_state_dict(torch.load(checkpoint_path, map_location="cpu", weights_only=True))
predicted_cells = model.predict_population(control_pca, condition_vector, dose_gate)
```

`control_pca` 必须使用保存的基因顺序、归一化和 PCA 变换；`condition_vector`
为本试验 Morgan-128 加剂量坐标，不能把任意 embedding 填入同样长度的数组。
本后端不提供生物适用性认证、测量噪声或域外不确定性估计。

## 下一步优先级

先扩大群体基准并增加化学 ridge、标准 State/CellFlow 与训练均值对照，按化学结构、
研究/供者和细胞背景分别留出；分开测均值、方差、分布、RNA 方向和高效应条件。
再消融群体上下文、OT 配对与非线性流，判断收益来自哪里。
有足够证据后才注册到智能体推理路由，并对所选动作重新校准。
STACK 式处理群体 prompt 需明确其在查询时可得，禁止拿待预测条件的目标细胞作 prompt。
多模态功能读数和 D-SPIN 调控程序需要相应测量及独立验证后再添加。

技术来源与核查范围见 `METHODS.md`；测试收据见输出目录的 `verification.json`。
