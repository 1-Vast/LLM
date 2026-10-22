# Data/evaluation auditor × skeptic: actual pre-response exchange

2026-10-22. V1 independent data-auditor draft was saved first (SHA256 `2c81355d310b3847c6bc31788c03d3ba3f33deb595d23af6bd8485a96b2e18da`); only then were current skeptic/advocate independent drafts read. This exchange concerns root's prospective V3 design. No raw/XLSX/assay values, implementation, network or fit was accessed in this exchange. A later non-fit code audit remains pending root notification.

## Auditor's actual questions

> Q1：认可V3最多证明注册forecasters下intermediateSGcoordinates超joint endpoints有价值，仍非动态因果/每一点必要或CMI？
>
> Q2：V3 groupguard现要求每member×3screencomplete，比分母按entries、panel仍percontextcomplete更保守；是否同意guard≠丢弃所有不满足guard的group全部rows？
>
> Q3：bootstrap仅固定fit后的test367roleclusters重采样，不含selection/refit/biologicaluncertainty；若95%CI跨0而点gates过，如何如实报告不临时改决策？

## Skeptic's actual answers and counterquestions

> 实际答Q1：认可，V3最多registeredforecasters的intermediateSG坐标集增量，非各点必要、时间顺序/动态因果或CMI。
>
> Q2：完全同意，all-member×3screencomplete是group数量资格guard，不是额外rowdrop规则；train/val/test每screen仍按共同prefix+target-valid rows打分/拟合，不能把其他合法行因同group某context缺失整组删除，也不能为凑guard放宽collisionpair。
>
> Q3：预定pointgates决定通过，CI跨0仍须原样报告point-pass但cluster-resamplingdirectionuncertain/不稳；不事后加CI>0 gate也不称显著/稳健复现，不隐藏interval或晋升core。bootstrap只固定fit条件testcluster敏感性，不含train/selection/refit/missingbias/biorep。
>
> 我的实际质疑A：实现应把coverageguard和scoringmask分开保存/测试，尤其collisionpair一member一screeninvalid时仍保留另member合法rows；你是否将此列为必须的syntheticcheck？
>
> B：group-bootstrap必须按抽样multiplicity给每row重复权重再每screen重算mean，不能先计算groupmean再等group平均（collisionpair2members和missing会改estimand），你是否接受？
>
> C：若train/val资格不达应fit前停，testcoverage失效不输出usefulpass；若代码仍算descriptive错误，是否要求结果status明确noverdict以免root引用残余MAE救结果？

## Auditor's actual replies

> 实际答A：是，必须syntheticcheck分离roweligibility与fullmembergroupguard：collisionpair某member一context无效→group不计完整组，但其他member/context合法row仍进入原per-screenpanel；不得为凑阈值整组drop/放宽。
>
> B：接受，bootstrap在367 frozenclusters上抽multiplicity，对其原eligible rows按multiplicity重复，再重算screenmean/macro；不能等group均值，否则双membergroup与missing改变estimand。
>
> C：接受，TV qualification fail即fit前停；test fail只DATA_QUALIFICATION_INSUFFICIENT/no useful verdict，不得从残余MAE救结果。若已有descriptive错误被计算/保存，须显式diagnostic-only并让gain/pass字段不可被当qualified结论，最清楚是不产任何usefulpass。CI跨0+pointgate过会原样报告point-pass但固定cluster方向不稳，不加posthoc gate也不称显著。将这些实际问答记录CROSS并向root作实施检查。

## Adopted consequences and remaining unknowns

The actual counterexample raised independently by this auditor and advocate was a history improvement caused solely by combining D0+D24. Root's pre-exposure joint-endpoints arm removes that simpler untested alternative under the registered models. Removing ratios also makes the channel ablation cleaner. This remains a finite-forecaster conditional prediction test, with no mechanism or world-model promotion.

The cross-examination creates concrete code-audit obligations: distinguish per-row fitting/scoring eligibility from complete-group qualification; include the two-entry collision counterexample in synthetic tests; preserve cluster sampling multiplicity without changing entry-weighted screen MAE; enforce qualification-before-verdict; retain the exact preregistered distinction between point gates and interval sensitivity.

There is no remaining interpretive disagreement among these two reviewers on V3. This does not certify uninspected code, legal numerical values, achieved coverage, useful information or biological replication. The code audit and single measured run may falsify the design's operational qualification or its prediction claim. Source/role/code/protocol freeze and closed-target tests remain required before exposure.
