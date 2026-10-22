# 独立 non-fit 实现审查

2026-10-22。读取当前 `gate.py`、`test_gate.py`、`PROTOCOL.md`、root已保存的synthetic输出/verification；不读raw/XLSX、assay/QC/feature/label数组，不fit、不执行gate或测试套件、不联网，不改root代码/协议。初稿与CROSS不改。实现审查期间root正在按零响应条件修订；下列hash是核对修复后的快照，不把早期读到的已知待修版本当最终。

- gate.py SHA256 `fb6b2a15ae3dee9a7de6a25ed2693bd0c1b4b07c52ea70c94ff5a2cca7946f56`
- test_gate.py SHA256 `8279097f89c46abc618368ea6d2c88570c081d2ac4b3b50ade7d6e2573cb5619`
- PROTOCOL.md SHA256 `3db9df46dacd7231361341e602fe9785d3767e3f5ecf23255937690561b64c56`

**裁决：GO，尚需实际freeze与一次预注册执行；当前无未解决blocking issue。** 这是对所述窄direct-information程序的运行前许可判断，非数据资格/性能结果，也不晋升world、agent或RSI。若文件继续改动，应核对新差异再freeze。

## 已解决的实质问题

本次新增条件性阻塞曾是cached-formula temporal leakage：早期地址的cached数值不保证只用早期信息，例如早期公式可以引用future target。原parser只留formula bool而允许其cache作为观察，地址白名单不能独自排除该情况。

root在零响应时的V4选择更简洁保守规则：**所有选中prefix/target公式一律formula_disallowed**，不读其引用、不评估、不转cache数值，进入原来相同分母/阈值资格规则。已核parser先判断formula而跳过float、测试预期公式value=None，protocol V4明确覆盖旧许可。此改动解决所提implementation边界，不要求恢复export script或反复检索。普通numeric literal的上游处理仍靠source资格与exported-readout范围，不称获得了逐cell绝对时间来源认证。

root此前自查的待修项在当前版本亦已核对：bootstrap显式接收全部frozen test groups，包括零complete observations的group；`role_groups`按去重group计数而非names；test-target reader重读已保存prefix ledger以核预测/abstention与prefix eligibility一致。collision synthetic确认组完整资格少一个但其他602合法rows仍保留；不会误把group guard当整组drop mask。

## 与scope、公平性和stop的代码对应

1. `make_manifest`仅用既存metadata建5499named exported rows，固定collision pair同组，所有screen同role；读取sourcebytes只作SHA校验。限定columns与已核header对应：T98G seven4h prefix和AU72，U2OS跳过2h中间frame且CV72。没有87匿名rows、QC表或side结果表数值地址。
2. `project_numeric`只对allowed地址转数值；错误/字符串/boolean/absence/nonfinite/negative无合法观察，零合法。closed cells不求值；selected formula V4无cache转换。`observations`仅把valid cells放入数组，非法观察NaN不被补零。
3. `coverage`分母为所有role×screen named entries；group guard按该group全部members/contexts的complete判断，仅计数不删合法rows。fit/score的共同complete mask独立于该guard。L-valid、dual-valid、D额外失败、target/complete均导出。train/validation fail在任何fit前写qualification terminal并返回；test fail在评分前返回，不写useful pass。
4. 五臂features正确为19/20/20/21/26，L坐标全共享、history严格含三种snapshot/endpoints；不含ratio、D slope、name/group/row/chemical/plate。14config同候选、同监督/scaler/权重与validation scorer，lexicographic tie、独立选后train+validation refit，精确75fits。HGB固定300iterations/early_stopping=False；没有意外内部验证切分或不同arm额外search。权重每次用实际拟合集重算N/(3*n_screen)，fit的三screen总权重一致。
5. 所有test keys的五臂与两anchor预测/abstention先写完整JSON，再SHA seal；test-target read必须验证seal/key/model集合、有限预测/null abstention及先前prefix eligibility。此前只授权train/validation L72，无crossfit reuse。test L72不能进入features/scaler/selection，最终target-valid仅用于共同score mask。
6. metric为各screen row-MAE再三screen等权。bootstrap以全部367test groups的multiplicity重复原合法row，重算screen sums/counts，不先平均group；空screen draw重抽并报告count，protocol已数值前追加这个边界。门槛对每baseline均为overall .05和10%及三screen正值；history需包括joint endpoints全部过。CI不是新增gate，也不产生生物/run显著性。

## 验证证据和限制

root保存的 `TESTS_PRE_RESPONSE.txt` 为10/10通过，覆盖whitelist/closed-cell、授权、特征嵌套、权重与budget、collision/group guard、prediction seal与bootstrap multiplicity。`VERIFICATION_PRE_RESPONSE.json`报告283 checks通过、含历史冻结产物hash。反方阅读这些产物及相关测试实现，**未重新运行其含synthetic Ridge fit的测试，也未自行重做283项历史校验**。10个逻辑测试不是生物复现，更不能替代未开的raw数值资格。

freeze应保留本审查与最终代码/协议/role manifest/sourcehash，实际run不得使用审后又静默变更文件。异常统一写`IMPLEMENTATION_FAILURE.json`是通用取证文件名；异常身份不自动证明是可重跑的implementation bug。任何异常仍须按具体原因区分source/qualification/implementation，不能凭文件名绕过one-run规则。代码已有RUN_START与exclusive writes防静默覆盖，未见自动retry。

STOP仍限定固定source、named entries、24→72h、完整双通道条件与注册direct家族；source/coveragefail不是channelnegative，qualified主增益失败也不证明所有D无信息。阳性仍只是marker forecast surrogate与有限程序价值；无triage成本/新hit、独立viability、动态因果、world同信息优势、agent/继承/联合/RSI实测。
