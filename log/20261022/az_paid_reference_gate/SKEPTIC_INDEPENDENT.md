# Paid mono-effect residual transport：独立反方

2026-10-22。先读本phase初始PROTOCOL及上一冻结phase的DECISION、AZ_EDGE_COVER_PROTOCOL、AZ_METADATA_PROJECTION。**未读本phase新peer稿、完整measured protocol/code、ZIP行或targets；无GET、fit或旧freeze修改。** 此稿先于交叉审查。

**判断：支持一次有界、预注册的回顾性普通结构机会pilot；不先批准world/agent/RSI。** 这比继续资格清单更可证伪：同样付费参考、源训练资料与搜索预算下，mono-effect坐标的pair-specific残差是否比dose坐标和强direct更好。源内静态72hCTG功能表面是真实功能代理任务；不需另加RNA/动态toy，但也不证明细胞状态动力学或临床效力。

## 精确主张与反证

若源归一化抑制值用固定比例变成m∈实数，Bliss基线为`B=mA+mB−mA*mB`，候选`I_AB=B+h_AB(mA,mB)`；mA/mB只从两张付费其它pair的观测`lib*_y`取得。单位、缩放和异常值规则须先固定，不能默认为[0,1]再clip；yhat、IC50、目标AB附带mono均不可进入预测或残差构建。

核心是**已见pair在未见cell中的条件稳定性**，不是未见药物/未见pair泛化。平坦/非单调mono使不同dose落到同effect坐标；若其交互不同，纯effect函数必失信息。target mono剂量覆盖也不保证其effect落在训练支持域。两项应作为预先定义的机制诊断，不能事后丢弃低支持/非单调的test episode来改善结果。效应坐标之外再加入dose可能有效，但那是混合模型，不能说纯坐标不变性通过。

通用NN可表示本函数，不构成反证；有用的结构归纳偏置可在有限数据/预算下成立。反之，若只有“paid mono比无mono”获益，保留观测信息价值；若effect残差与strongdirect相当，保留普通预测/简化表示，不能宣布独有world贡献。是否构成新科学实证还需与既有Bliss/interaction-surface工作精确比较，本门不预授算法新颖性。

## 成本、角色与信息隔离

一个episode是一个hidden AB matrix和预选AC、BD两个其它pair bundles；不需C=D。所有AB repeats禁作witness，维持同source/project/model/stock/plate与精确dose要求。episode内两张bundle的**全部观测mono和combo**向全部比较者开放，记录读取行数、唯一dose观测和拟合成本；重复附带mono值不是独立生物重复。

两bundle是**每target episode成本2**。不同target episode从同一source checkpoint/合法源历史分叉，不把前一episode已购witness、适配权重或缓存观测默默累积到后一episode。否则某个hidden AB可能早已作为别的episode的witness被看见，且campaign成本会改变。若要研究整cell共享缓存，必须另定义行动流与总成本，不能把本门报告为全cell只付2。

MASTER_CELL_ID的全部stock、plate、repeat同role；菜单、角色、witness与tie只用metadata固定。来源与Jaaks已知重叠保留，这是内部回顾开发，不是新的独立wetlab确认。允许源训练cell的AB标签作为共同监督，但**各role中mono predictor仍按同paid-witness规则构造，不能偷偷拿AB附带mono当训练残差的免费特征**。任何额外源监督/预训练/先验必须对照共享。

## 最小且强的普通比较

以下都用相同训练/validation划分、相同已付两bundle与固定搜索上限，不用弱基线垫高结果：

1. **Bliss**：直接用paid observed mA/mB，无学得interaction；隔离参考信息与残差价值。
2. **Dose残差**：与候选相同pair pooling、函数类/容量和调参次数，输入换成实际dose坐标；同时报告无paid mono的source pair-mean dose surface。
3. **Strongdirect**：输入pair IDs、两dose、mA/mB及全部paid witness信息；最少包含有regularization的平滑/核回归与一个强非线性直接回归族（如HGB/ExtraTrees），validation择优。不能只给direct结构和dose，或把其已购combo信息丢掉。
4. **普通refit/在线适配**：从同源checkpoint利用两bundle全部combo反馈，至少检验一个共享cell residual/conditional-kernel更新；不允许用hidden AB适配。若所有方法都不消费combo反馈，也应明确那是只测reference通道的较窄对照，不能宣称击败全信息最强direct。
5. **简单混合**：dose、effect与direct的少量预定混合权重，validation选；与候选共享候选评价/拟合预算。混合获胜按其实际性质报告。

固定同一witness的本门没有主动选择或程序改进，AL/agent/继承/RSI贡献是NOT_TESTED。源内样本累积重训也不叫后续研究程序继承；将来如升级，才做同菜单AL、CL、等预算程序搜索、factorial和共同起点improver实验。

## Cell-cluster gate与停止

完整measured protocol应在开数值前固定一个主loss与δ_use，明确单位和用途。建议主结构终点用functional surface MAE，先逐matrix平均dose，再在同pair-cell的stock/plate/repeat间平均，最后pair平均到cell、cell宏平均；这样高重复/高覆盖cell不支配结果。若采用别的层级权重，必须前置固定并对所有臂相同。dose点/矩阵不是独立n。

配对bootstrap重抽test MASTER_CELL_ID，保留每cell内全部episode及重复关系；重抽10k或其他固定次数。比较者由validation预选/锁定，不能看test后挑某个容易胜的direct。report point gain、相对gain与cell-cluster interval；建议继续条件是**超过预定实用margin且95%下界>0**。若上界低于δ_use，停止实用贡献；CI宽则本预算内不确定，不能靠换终点、降低margin或增搜test续命。若dose获益而strongdirect/混合匹配，停止“残差结构独有增益”，保留普通信息收益。

资格分母从冻结metadata菜单算，witness可用性与target可评分性分别记录；不以target高/低响应、synergy、缺失模式选择最好panel。数值缺失的处理/coverage abort阈值须事先规定，common-case评分必须明确条件范围。test target最后开，仅用于同一固定panel评分，不用target决定witness、effect支持筛选或任何fit。一次有界pilot即可裁决，不再追加无期限source资格门。

若另报告recommendation regret，应前置说明**推荐什么、行动成本与utility**。仅最大CTG抑制的剂量选择可能退化成选最大dose，不能自动代表组合发现；纯表面MAE改善也不等于hit/毒性/临床决策改善。用test target定义oracle可作遗憾评价，但不是独立重复或无噪声可达oracle。当前可以合法先测结构预测机会，不能据此声称真实筛选节约已成立。

## 未知归一化来源的作用域

观测`lib*_y`也是exported normalized response，不等于新做两次实验即可独立生成的原始readout；同plate并不证明归一化、重复/平均、控制分母都与hidden AB无关。当前未知阻止**prospective两次湿实验可获取性、独立原始mono测量、因果interaction与临床utility**等强主张。

但并不自动阻止限定为“给定源exported observed references、按声明bundle计费”的回顾性比较；全部方法共享同样派生字段和限制，仍可测有用的条件预测结构。必须披露购买成本是retrospective bundle约定，未认证真实实验成本/可部署oracle。若后来发现mono字段直接使用hidden AB数值构造，则连hidden-target预测解释也被破坏，需停止该接口；目前不能把未知当已证明泄漏，也不必为此先无限寻找原始control。先锁边界、做一次诚实有界pilot，是合理下一步。

最终GO仅指上述普通机会测试经完整协议/实现交叉后可执行；没有新模型机制、新功能world动态、agent、继承、联合或RSI效果已建立。
