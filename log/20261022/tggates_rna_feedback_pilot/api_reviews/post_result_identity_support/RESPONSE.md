纠错如下（支持方，仅据所给材料）：

1. **主候选误标**：两首评把rbf（DNA .02645605527716932/LDH .008414909243689863）当作主候选。主候选是rho_0（DNA .027315340891917134/LDH .009035285110724236）；rbf是对照。-0.008364303766192367是rho_0相对refit的DNA增益，不能配rbf指标。

2. **LDH门**：LDH不在DNA主门内，不应编造“LDH未达门槛”。冻结门槛是DNA绝对>0.02且相对≥10%；LDH仅作描述。

3. **source state**：是选择暴露诊断（selection_exposed=true），非独立state确认（independent_development_state_accuracy=false）。no_rna仍保留source-trained world，不能称“无源状态”。

4. **几何条件**：direct=.022567071922444528满足已证明的d≤.04条件，故所选direct的半混合门确实不可达；refit<.02单独使严格>.02改善不可能。但这是本配置/混合物条件性结论，非全领域不可能，不改STOP。

5. **归因**：候选即使去掉门槛也实际差于direct（-.004748268969472606）、no_rna（-.005123957982403872）、refit（-.008364303766192367），不能只归因门几何。

6. **继承/重启**：一般继承transfer vs restart与C4 old/new improver共同起点不同；joint不必超加，不得当已证。

7. **证据边界**：保留证据——refit DNA .018951037125724768最强普通基线、no_rna .022191382909513262更优、route_11=rho_0同值、数值审计PASS。反对证据——主门槛失败、RNA无增量、候选劣于refit/direct/no_rna。未决——route增量（state/function=true）实际价值、mixture限制解释边界；均描述性非显著。后续最小证据：冻结门槛下连续报告candidate-vs-direct/noRNA/routes/mixture，不换端点、不删样本、不放宽门槛、不开保留集；agent/继承/RSI另立预注册。同模型角色共识不作实证。