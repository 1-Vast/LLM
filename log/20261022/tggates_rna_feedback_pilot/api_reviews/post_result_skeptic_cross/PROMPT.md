你继续原立场。最多1000中文字符，明确回应对方具体意见：同意、反对、真实未决问题和最小验证。纠正双方任何错数或过度断言。不得假装双方共识是实证，也不得换门槛或开保留集。
自己的首轮原文：
**结论：无可用预测增量；判定与冻结STOP一致。**

- **增量与实际意义**：候选DNA MAE 0.0264561，LDH 0.0084149。最强非同构普通基线refit为0.0189510/0.0096016；绝对DNA增量 -0.0083643，相对 -44.14%，`useful_gain_gate=false`。故DNA劣于refit，LDH仅低0.0011867，未达门槛；无实际意义。冻结门槛：相对最强普通比较>0.02绝对且≥10%相对。`GATE_GEOMETRY_AUDIT`给出混合物必要条件：若direct≤0.04，绝对门在数学上不可达；此处direct=0.0225671，属该条件，故STOP是配置/效用判定，非RNA信息不存在之证。
- **RNA/路由**：`observed_rna_increment=false`；no_rna DNA 0.0221914优于候选0.0264561，LDH 0.0081047亦优于0.0084149，观测RNA无增量。`state_route_increment=true`、`function_route_increment=true`仅指严格较低MAE；route_01 0.0273589、route_11 0.0273153，与rho_0相同，属描述性，不证明统计显著。`fixed_half_mixture` DNA 0.0249412、LDH 0.0085854；混合未胜refit。
- **普通解释**：存在。`refit` DNA 0.0189510为最强普通基线；`prior_ridge_full_middle` LDH 0.0065386更低。`prior_constant_source_median` DNA 0.02475、`prior_middle_copy` 0.0233571均接近候选。候选被认定为普通受约束联合预测，非新算法；历史开发暴露与源选择仍在，区间仅描述性。
- **新颖性**：无。冻结文档明确“普通受约束联合预测，不是新算法”，且不得主张RSI/新核心。
- **未测项**：`agent_benefit`、`inheritance_benefit`、`rsi_c4`均NOT_TESTED；world模型、agent、继承、联合/RSI均未测。`later_opened=false`，`later_function_casts=0`。
- **证据**：支持STOP——refit更优、no_rna更优、`useful_gain_gate=false`、`decision=STOP_THIS_CONFIGURATION_EXPANSION`。反对“无信息”强结论——`GATE_GEOMETRY_AUDIT`指出门槛在direct=0.0225671时结构性受限；`REFERENCE_ASSEMBLY_AUDIT`仅数值聚合PASS，非生物验证。未决分歧：route增量是否具实际价值、mixture限制的解释边界。最小后续验证：在冻结门槛下报告候选-vs-pure-direct、noRNA、routes与mixture连续对比；不修改判定、不换端点、不删样本、不开保留集。
- **一致性**：与冻结STOP/GO判定一致，STOP。门槛与mixture限制只影响解释：STOP是效用/配置决策，不证明RNA信息缺失或世界模型不可能；不修改判定。
对方首轮原文：
**预测增量及实际意义**：未通过。冻结门槛要求相对最强普通非等构比较器（refit）严格>0.02绝对DNA MAE且≥10%相对。实测`absolute_dna_gain=-0.008364303766192367`，`relative_dna_gain=-0.44136390587501845`，`useful_gain_gate=false`。即候选（rbf DNA 0.02645605527716932）反而劣于refit（0.018951037125724768）。实际意义仅为普通受约束联合预测，无可用增量。

**RNA/路由贡献**：`observed_rna_increment=false`；no_rna DNA 0.022191382909513262优于rbf 0.02645605527716932，未见正向RNA增量。`state_route_increment=true`、`function_route_increment=true`，但route_11 DNA 0.027315340891917134与rho_0同值，route_01 0.027358881999131692、route_00 0.03219210114411654、route_10 0.03214856003690198；路由差异存在，但不足以救主门槛，且不证明因果或显著。

**普通解释**：存在。候选为普通受约束线性联合预测，最强普通非等构refit即优于它；历史Middle-copy 0.023357142857142823已独立迫使候选<0.00335714才可能过绝对门槛。

**新颖性**：无新算法核心；仅为普通联合预测。

**未测**：`agent_benefit=NOT_TESTED`、`inheritance_benefit=NOT_TESTED`、`rsi_c4=NOT_TESTED`；world模型、agent、继承、联合、RSI均未测，不能外推为所有世界模型不可能。

**证据**：支持侧—路由增量标志为真、refit DNA 0.018951037125724768为可保留普通基线、数值审计PASS（最大状态差3.4555691641457997e-15）。反对侧—主门槛失败、RNA无增量、候选劣于refit。未决分歧—路由/混合限制如何解释，非改判。最小后续验证：在冻结门槛下，仅报告连续candidate-vs-direct、noRNA、routes与mixture对比，不换端点/删样本/放宽门槛；agent/继承/RSI需另立预注册。

**与原冻结判定一致性**：一致，`decision=STOP_THIS_CONFIGURATION_EXPANSION`，非确认性（DEVELOPMENT_ONLY_NOT_CONFIRMATORY）。门槛与固定50/50 mixture仅影响解释（几何必要d−c>.04），不修改判定。

--- RNA_PILOT_RESULT.json ---
{
  "status": "DEVELOPMENT_ONLY_NOT_CONFIRMATORY",
  "scores": {
    "rbf": {
      "dna_mae": 0.02645605527716932,
      "ldh_mae": 0.008414909243689863
    },
    "direct": {
      "dna_mae": 0.022567071922444528,
      "ldh_mae": 0.008135536373579808
    },
    "four_gene": {
      "dna_mae": 0.025434511023108723,
      "ldh_mae": 0.009321086467891426
    },
    "no_rna": {
      "dna_mae": 0.022191382909513262,
      "ldh_mae": 0.008104710022825281
    },
    "refit": {
      "dna_mae": 0.018951037125724768,
      "ldh_mae": 0.009601641612839527
    },
    "rho_0": {
      "dna_mae": 0.027315340891917134,
      "ldh_mae": 0.009035285110724236
    },
    "rho_0.5": {
      "dna_mae": 0.027177152474603568,
      "ldh_mae": 0.00901780685076787
    },
    "rho_1": {
      "dna_mae": 0.027090629313040022,
      "ldh_mae": 0.009018583198948469
    },
    "fixed_half_mixture": {
      "dna_mae": 0.02494120640718083,
      "ldh_mae": 0.008585410742152038
    },
    "prior_constant_085": {
      "dna_mae": 0.11657142857142863,
      "ldh_mae": 0.1568571428571429
    },
    "prior_constant_source_median": {
      "dna_mae": 0.02475,
      "ldh_mae": 0.011178571428571451
    },
    "prior_middle_copy": {
      "dna_mae": 0.023357142857142823,
      "ldh_mae": 0.010714285714285692
    },
    "prior_median_residual": {
      "dna_mae": 0.02392857142857141,
      "ldh_mae": 0.01060714285714291
    },
    "prior_tanimoto_residual": {
      "dna_mae": 0.03635714285714283,
      "ldh_mae": 0.011499999999999939
    },
    "prior_ridge_dose_chem": {
      "dna_mae": 0.023585971028344383,
      "ldh_mae": 0.009020547416319968
    },
    "prior_krr_dose_chem": {
      "dna_mae": 0.023994302825844534,
      "ldh_mae": 0.009072008003433425
    },
    "prior_ridge_full_middle": {
      "dna_mae": 0.0261378575115753,
      "ldh_mae": 0.006538566468470952
    },
    "prior_krr_full_middle": {
      "dna_mae": 0.024443612270425068,
      "ldh_mae": 0.008630589618770486
    },
    "route_00": {
      "dna_mae": 0.03219210114411654,
      "ldh_mae": 0.00930899259284436
    },
    "route_01": {
      "dna_mae": 0.027358881999131692,
      "ldh_mae": 0.009025728021973465
    },
    "route_10": {
      "dna_mae": 0.03214856003690198,
      "ldh_mae": 0.009300484086573422
    },
    "route_11": {
      "dna_mae": 0.027315340891917134,
      "ldh_mae": 0.009035285110724236
    },
    "null_rho_0": {
      "dna_mae": 0.03234634752348252,
      "ldh_mae": 0.009036148775753412
    },
    "null_direct": {
      "dna_mae": 0.03065780076561884,
      "ldh_mae": 0.008662449470798686
    }
  },
  "losses": {
    "rbf": [
      {
        "label": "azathioprine",
        "dna_absolute_error": 0.0593384509710434,
        "ldh_absolute_error": 0.004048137831170084
      },
      {
        "label": "carbamazepine",
        "dna_absolute_error": 0.0097868990954747,
        "ldh_absolute_error": 0.003777837666049111
      },
      {
        "label": "chlorpromazine",
        "dna_absolute_error": 0.018487078894604325,
        "ldh_absolute_error": 0.007749563014796124
      },
      {
        "label": "glibenclamide",
        "dna_absolute_error": 0.04410722611984175,
        "ldh_absolute_error": 0.0023917110133757635
      },
      {
        "label": "ketoconazole",
        "dna_absolute_error": 0.017276040734477305,
        "ldh_absolute_error": 0.021249414815518897
      },
      {
        "label": "propylthiouracil",
        "dna_absolute_error": 0.01664817946941155,
        "ldh_absolute_error": 0.012159808119724058
      },
      {
        "label": "thioridazine",
        "dna_absolute_error": 0.019548511655332224,
        "ldh_absolute_error": 0.007527892245195011
      }
    ],
    "direct": [
      {
        "label": "azathioprine",
        "dna_absolute_error": 0.036660290290937536,
        "ldh_absolute_error": 0.002219536653715881
      },
      {
        "label": "carbamazepine",
        "dna_absolute_error": 0.0073523906500369,
        "ldh_absolute_error": 0.0043934377337015995
      },
      {
        "label": "chlorpromazine",
        "dna_absolute_error": 0.017136404923357662,
        "ldh_absolute_error": 0.0072126772721456955
      },
      {
        "label": "glibenclamide",
        "dna_absolute_error": 0.05341713993783792,
        "ldh_absolute_error": 0.0037506527606666618
      },
      {
        "label": "ketoconazole",
        "dna_absolute_error": 0.010633474318403446,
        "ldh_absolute_error": 0.022111409615808597
      },
      {
        "label": "propylthiouracil",
        "dna_absolute_error": 0.01661301590733333,
        "ldh_absolute_error": 0.010622807802464829
      },
      {
        "label": "thioridazine",
        "dna_absolute_error": 0.0161567874292049,
        "ldh_absolute_error": 0.006638232776555397
      }
    ],
    "four_gene": [
      {
        "label": "azathioprine",
        "dna_absolute_error": 0.0521925861559982,
        "ldh_absolute_error": 0.005305968688827933
      },
      {
        "label": "carbamazepine",
        "dna_absolute_error": 0.00938998733027252,
        "ldh_absolute_error": 0.003932748832356392
      },
      {
        "label": "chlorpromazine",
        "dna_absolute_error": 0.019530891342597112,
        "ldh_absolute_error": 0.010505624501872202
      },
      {
        "label": "glibenclamide",
        "dna_absolute_error": 0.0449635733949465,
        "ldh_absolute_error": 0.0002956998728300686
      },
      {
        "label": "ketoconazole",
        "dna_absolute_error": 0.02078083165188338,
        "ldh_absolute_error": 0.019011070921830964
      },
      {
        "label": "propylthiouracil",
        "dna_absolute_error": 0.0135371646100646,
        "ldh_absolute_error": 0.01478982381112992
      },
      {
        "label": "thioridazine",
        "dna_absolute_error": 0.017646542675998744,
        "ldh_absolute_error": 0.011406668646392504
      }
    ],
    "no_rna": [
      {
        "label": "azathioprine",
        "dna_absolute_error": 0.033050003801043726,
        "ldh_absolute_error": 0.0020604163099711137
      },
      {
        "label": "carbamazepine",
        "dna_absolute_error": 0.006868384331864763,
        "ldh_absolute_error": 0.004462768236258352
      },
      {
        "label": "chlorpromazine",
        "dna_absolute_error": 0.017863276404205708,
        "ldh_absolute_error": 0.0072736432395899
      },
      {
        "label": "glibenclamide",
        "dna_absolute_error": 0.05489448149500509,
        "ldh_absolute_error": 0.003826624551234281
      },
      {
        "label": "ketoconazole",
        "dna_absolute_error": 0.009616352707626508,
        "ldh_absolute_error": 0.02220826700423517
      },
      {
        "label": "propylthiouracil",
        "dna_absolute_error": 0.017345998042212485,
        "ldh_absolute_error": 0.010344794533905244
      },
      {
        "label": "thioridazine",
        "dna_absolute_error": 0.01570118358463457,
        "ldh_absolute_error": 0.006556456284582901
      }
    ],
    "refit": [
      {
        "label": "azathioprine",
        "dna_absolute_error": 0.011051658932222819,
        "ldh_absolute_error": 0.0002839956568156943
      },
      {
        "label": "carbamazepine",
        "dna_absolute_error": 0.0035178192681141196,
        "ldh_absolute_error": 0.0038208509144386227
      },
      {
        "label": "chlorpromazine",
        "dna_absolute_error": 0.023397723347925448,
        "ldh_absolute_error": 0.0119863863094547
      },
      {
        "label": "glibenclamide",
        "dna_absolute_error": 0.056773395051563535,
        "ldh_absolute_error": 0.00682978181444005
      },
      {
        "label": "ketoconazole",
        "dna_absolute_error": 0.011495823107571801,
        "ldh_absolute_error": 0.013374463561330652
      },
      {
        "label": "propylthiouracil",
        "dna_absolute_error": 0.008053856703694073,
        "ldh_absolute_error": 0.013167204835217383
      },
      {
        "label": "thioridazine",
        "dna_absolute_error": 0.01836698346898158,
        "ldh_absolute_error": 0.01774880819817959
      }
    ],
    "rho_0": [
      {
        "label": "azathioprine",
        "dna_absolute_error": 0.05349729375058809,
        "ldh_absolute_error": 0.004095133686653485
      },
      {
        "label": "carbamazepine",
        "dna_absolute_error": 0.009711277077011582,
        "ldh_absolute_error": 0.0040134077681033276
      },
      {
        "label": "chlorpromazine",
        "dna_absolute_error": 0.022332758899533567,
        "ldh_absolute_error": 0.010082412823204434
      },
      {
        "label": "glibenclamide",
        "dna_absolute_error": 0.04261676814179283,
        "ldh_absolute_error": 0.0003447594403227505
      },
      {
        "label": "ketoconazole",
        "dna_absolute_error": 0.019710572379663893,
        "ldh_absolute_error": 0.01933161923179183
      },
      {
        "label": "propylthiouracil",
        "dna_absolute_error": 0.020039681791502062,
        "ldh_absolute_error": 0.014868476240334827
      },
      {
        "label": "thioridazine",
        "dna_absolute_error": 0.023299034203327906,
        "ldh_absolute_error": 0.010511186584658994
      }
    ],
    "rho_0.5": [
      {
        "label": "azathioprine",
        "dna_absolute_error": 0.0528859321506453,
        "ldh_absolute_error": 0.00399157608017342
      },
      {
        "label": "carbamazepine",
        "dna_absolute_error": 0.009560448218209117,
        "ldh_absolute_error": 0.0040072959876118475
      },
      {
        "label": "chlorpromazine",
        "dna_absolute_error": 0.022169291954729275,
        "ldh_absolute_error": 0.010065441208194637
      },
      {
        "label": "glibenclamide",
        "dna_absolute_error": 0.04290544416645248,
        "ldh_absolute_error": 0.00031825547119446185
      },
      {
        "label": "ketoconazole",
        "dna_absolute_error": 0.019487134678580653,
        "ldh_absolute_error": 0.019311417477777537
      },
      {
        "label": "propylthiouracil",
        "dna_absolute_error": 0.020062121033105673,
        "ldh_absolute_error": 0.014863495750045086
      },
      {
        "label": "thioridazine",
        "dna_absolute_error": 0.023169695120502487,
        "ldh_absolute_error": 0.010567165980378102
      }
    ],
    "rho_1": [
      {
        "label": "azathioprine",
        "dna_absolute_error": 0.052509035255986936,
        "ldh_absolute_error": 0.0039833470280497
      },
      {
        "label": "carbamazepine",
        "dna_absolute_error": 0.009463039347529234,
        "ldh_absolute_error": 0.004008526027942105
      },
      {
        "label": "chlorpromazine",
        "dna_absolute_error": 0.022054497165478693,
        "ldh_absolute_error": 0.010052883071243413
      },
      {
        "label": "glibenclamide",
        "dna_absolute_error": 0.04307239900289361,
        "ldh_absolute_error": 0.00031934511243436603
      },
      {
        "label": "ketoconazole",
        "dna_absolute_error": 0.0193586091499639,
        "ldh_absolute_error": 0.019313354580309694
      },
      {
        "label": "propylthiouracil",
        "dna_absolute_error": 0.020074403346513114,
        "ldh_absolute_error": 0.014872392196025652
      },
      {
        "label": "thioridazine",
        "dna_absolute_error": 0.023102421922914673,
        "ldh_absolute_error": 0.010580234376634357
      }
    ],
    "fixed_half_mixture": [
      {
        "label": "azathioprine",
        "dna_absolute_error": 0.045078792020762815,
        "ldh_absolute_error": 0.003157335170184794
      },
      {
        "label": "carbamazepine",
        "dna_absolute_error": 0.008531833863524296,
        "ldh_absolute_error": 0.0042034227509024635
      },
      {
        "label": "chlorpromazine",
        "dna_absolute_error": 0.019734581911445614,
        "ldh_absolute_error": 0.008647545047675065
      },
      {
        "label": "glibenclamide",
        "dna_absolute_error": 0.04801695403981543,
        "ldh_absolute_error": 0.0020477061004946506
      },
      {
        "label": "ketoconazole",
        "dna_absolute_error": 0.01517202334903367,
        "ldh_absolute_error": 0.020721514423800214
      },
      {
        "label": "propylthiouracil",
        "dna_absolute_error": 0.01832634884941764,
        "ldh_absolute_error": 0.012745642021399828
      },
      {
        "label": "thioridazine",
        "dna_absolute_error": 0.019727910816266347,
        "ldh_absolute_error": 0.008574709680607251
      }
    ],
    "prior_constant_085": [
      {
        "label": "azathioprine",
        "dna_absolute_error": 0.0665,
        "ldh_absolute_error": 0.15000000000000002
      },
      {
        "label": "carbamazepine",
        "dna_absolute_error": 0.13350000000000006,
        "ldh_absolute_error": 0.16100000000000014
      },
      {
        "label": "chlorpromazine",
        "dna_absolute_error": 0.1070000000000001,
        "ldh_absolute_error": 0.14350000000000007
      },
      {
        "label": "glibenclamide",
        "dna_absolute_error": 0.1695000000000001,
        "ldh_absolute_error": 0.15349999999999986
      },
      {
        "label": "ketoconazole",
        "dna_absolute_error": 0.10150000000000003,
        "ldh_absolute_error": 0.17299999999999993
      },
      {
        "label": "propylthiouracil",
        "dna_absolute_error": 0.126,
        "ldh_absolute_error": 0.1755000000000001
      },
      {
        "label": "thioridazine",
        "dna_absolute_error": 0.1120000000000001,
        "ldh_absolute_error": 0.14150000000000007
      }
    ],
    "prior_constant_source_median": [
      {
        "label": "azathioprine",
        "dna_absolute_error": 0.06125000000000003,
        "ldh_absolute_error": 0.007249999999999979
      },
      {
        "label": "carbamazepine",
        "dna_absolute_error": 0.005750000000000033,
        "ldh_absolute_error": 0.003750000000000142
      },
      {
        "label": "chlorpromazine",
        "dna_absolute_error": 0.020749999999999935,
        "ldh_absolute_error": 0.013749999999999929
      },
      {
        "label": "glibenclamide",
        "dna_absolute_error": 0.041750000000000065,
        "ldh_absolute_error": 0.003750000000000142
      },
      {
        "label": "ketoconazole",
        "dna_absolute_error": 0.026249999999999996,
        "ldh_absolute_error": 0.01574999999999993
      },
      {
        "label": "propylthiouracil",
        "dna_absolute_error": 0.0017500000000000293,
        "ldh_absolute_error": 0.0182500000000001
      },
      {
        "label": "thioridazine",
        "dna_absolute_error": 0.01574999999999993,
        "ldh_absolute_error": 0.01574999999999993
      }
    ],
    "prior_middle_copy": [
      {
        "label": "azathioprine",
        "dna_absolute_error": 0.015999999999999903,
        "ldh_absolute_error": 0.0050000000000000044
      },
      {
        "label": "carbamazepine",
        "dna_absolute_error": 0.024499999999999966,
        "ldh_absolute_error": 0.0050000000000001155
      },
      {
        "label": "chlorpromazine",
        "dna_absolute_error": 0.02400000000000002,
        "ldh_absolute_error": 0.009999999999999787
      },
      {
        "label": "glibenclamide",
        "dna_absolute_error": 0.07000000000000006,
        "ldh_absolute_error": 0.010000000000000231
      },
      {
        "label": "ketoconazole",
        "dna_absolute_error": 0.0024999999999999467,
        "ldh_absolute_error": 0.011499999999999844
      },
      {
        "label": "propylthiouracil",
        "dna_absolute_error": 0.008499999999999952,
        "ldh_absolute_error": 0.01200000000000001
      },
      {
        "label": "thioridazine",
        "dna_absolute_error": 0.017999999999999905,
        "ldh_absolute_error": 0.021499999999999853
      }
    ],
    "prior_median_residual": [
      {
        "label": "azathioprine",
        "dna_absolute_error": 0.02499999999999991,
        "ldh_absolute_error": 0.004250000000000087
      },
      {
        "label": "carbamazepine",
        "dna_absolute_error": 0.015499999999999958,
        "ldh_absolute_error": 0.004250000000000309
      },
      {
        "label": "chlorpromazine",
        "dna_absolute_error": 0.015000000000000013,
        "ldh_absolute_error": 0.010749999999999815
      },
      {
        "label": "glibenclamide",
        "dna_absolute_error": 0.07900000000000007,
        "ldh_absolute_error": 0.01075000000000026
      },
      {
        "label": "ketoconazole",
        "dna_absolute_error": 0.006500000000000061,
        "ldh_absolute_error": 0.010750000000000037
      },
      {
        "label": "propylthiouracil",
        "dna_absolute_error": 0.01749999999999996,
        "ldh_absolute_error": 0.011249999999999982
      },
      {
        "label": "thioridazine",
        "dna_absolute_error": 0.008999999999999897,
        "ldh_absolute_error": 0.02224999999999988
      }
    ],
    "prior_tanimoto_residual": [
      {
        "label": "azathioprine",
        "dna_absolute_error": 0.008000000000000118,
        "ldh_absolute_error": 0.0044999999999999485
      },
      {
        "label": "carbamazepine",
        "dna_absolute_error": 0.029999999999999916,
        "ldh_absolute_error": 0.011500000000000288
      },
      {
        "label": "chlorpromazine",
        "dna_absolute_error": 0.03750000000000009,
        "ldh_absolute_error": 0.006499999999999506
      },
      {
        "label": "glibenclamide",
        "dna_absolute_error": 0.0685,
        "ldh_absolute_error": 0.014000000000000234
      },
      {
        "label": "ketoconazole",
        "dna_absolute_error": 0.0,
        "ldh_absolute_error": 0.010499999999999732
      },
      {
        "label": "propylthiouracil",
        "dna_absolute_error": 0.06849999999999978,
        "ldh_absolute_error": 0.005499999999999838
      },
      {
        "label": "thioridazine",
        "dna_absolute_error": 0.041999999999999926,
        "ldh_absolute_error": 0.028000000000000025
      }
    ],
    "prior_ridge_dose_chem": [
      {
        "label": "azathioprine",
        "dna_absolute_error": 0.07650164509531321,
        "ldh_absolute_error": 0.006111779486547286
      },
      {
        "label": "carbamazepine",
        "dna_absolute_error": 0.016517812676549393,
        "ldh_absolute_error": 0.00459110773636584
      },
      {
        "label": "chlorpromazine",
        "dna_absolute_error": 0.007074925725125469,
        "ldh_absolute_error": 0.009871435980322252
      },
      {
        "label": "glibenclamide",
        "dna_absolute_error": 0.036377212726872665,
        "ldh_absolute_error": 0.002916695155297022
      },
      {
        "label": "ketoconazole",
        "dna_absolute_error": 0.01101163908653513,
        "ldh_absolute_error": 0.018775874714664464
      },
      {
        "label": "propylthiouracil",
        "dna_absolute_error": 0.007793098682801869,
        "ldh_absolute_error": 0.01513367717825731
      },
      {
        "label": "thioridazine",
        "dna_absolute_error": 0.009825463205212936,
        "ldh_absolute_error": 0.005743261662785604
      }
    ],
    "prior_krr_dose_chem": [
      {
        "label": "azathioprine",
        "dna_absolute_error": 0.0725903624631159,
        "ldh_absolute_error": 0.006060384494180893
      },
      {
        "label": "carbamazepine",
        "dna_absolute_error": 0.01571057252855368,
        "ldh_absolute_error": 0.004507284550259172
      },
      {
        "label": "chlorpromazine",
        "dna_absolute_error": 0.007834938824737403,
        "ldh_absolute_error": 0.010380214160357282
      },
      {
        "label": "glibenclamide",
        "dna_absolute_error": 0.03929214201732012,
        "ldh_absolute_error": 0.0013492805068209268
      },
      {
        "label": "ketoconazole",
        "dna_absolute_error": 0.014710511801482085,
        "ldh_absolute_error": 0.01812965541808631
      },
      {
        "label": "propylthiouracil",
        "dna_absolute_error": 0.007663735636525004,
        "ldh_absolute_error": 0.01523066254693961
      },
      {
        "label": "thioridazine",
        "dna_absolute_error": 0.010157856509177554,
        "ldh_absolute_error": 0.007846574347389779
      }
    ],
    "prior_ridge_full_middle": [
      {
        "label": "azathioprine",
        "dna_absolute_error": 0.06837458043030364,
        "ldh_absolute_error": 0.0016028155248154485
      },
      {
        "label": "carbamazepine",
        "dna_absolute_error": 0.019257998851575864,
        "ldh_absolute_error": 0.003318051613084183
      },
      {
        "label": "chlorpromazine",
        "dna_absolute_error": 0.01455695347250019,
        "ldh_absolute_error": 0.006373086214548684
      },
      {
        "label": "glibenclamide",
        "dna_absolute_error": 0.050009427449923316,
        "ldh_absolute_error": 0.001241588293877216
      },
      {
        "label": "ketoconazole",
        "dna_absolute_error": 0.003598280002245491,
        "ldh_absolute_error": 0.017138594950620867
      },
      {
        "label": "propylthiouracil",
        "dna_absolute_error": 0.02478669048795301,
        "ldh_absolute_error": 0.01178797623007588
      },
      {
        "label": "thioridazine",
        "dna_absolute_error": 0.0023810718865255875,
        "ldh_absolute_error": 0.0043078524522743855
      }
    ],
    "prior_krr_full_middle": [
      {
        "label": "azathioprine",
        "dna_absolute_error": 0.06206650129259972,
        "ldh_absolute_error": 0.0034998529995393657
      },
      {
        "label": "carbamazepine",
        "dna_absolute_error": 0.018459894387292453,
        "ldh_absolute_error": 0.005033882542917922
      },
      {
        "label": "chlorpromazine",
        "dna_absolute_error": 0.012482341507461081,
        "ldh_absolute_error": 0.01016743973680212
      },
      {
        "label": "glibenclamide",
        "dna_absolute_error": 0.04884488948988319,
        "ldh_absolute_error": 0.00041008243133755506
      },
      {
        "label": "ketoconazole",
        "dna_absolute_error": 0.0064924202593865665,
        "ldh_absolute_error": 0.017939854679786427
      },
      {
        "label": "propylthiouracil",
        "dna_absolute_error": 0.01968499182874528,
        "ldh_absolute_error": 0.01402629338418837
      },
      {
        "label": "thioridazine",
        "dna_absolute_error": 0.003074247127607177,
        "ldh_absolute_error": 0.009336721556821637
      }
    ],
    "route_00": [
      {
        "label": "azathioprine",
        "dna_absolute_error": 0.07760351367746443,
        "ldh_absolute_error": 0.005994675504368274
      },
      {
        "label": "carbamazepine",
        "dna_absolute_error": 0.010090447668740454,
        "ldh_absolute_error": 0.0032734825581488547
      },
      {
        "label": "chlorpromazine",
        "dna_absolute_error": 0.030003339057753986,
        "ldh_absolute_error": 0.011197299075402789
      },
      {
        "label": "glibenclamide",
        "dna_absolute_error": 0.027862828861518918,
        "ldh_absolute_error": 0.0011121371623064036
      },
      {
        "label": "ketoconazole",
        "dna_absolute_error": 0.03198921679132749,
        "ldh_absolute_error": 0.017993663743107957
      },
      {
        "label": "propylthiouracil",
        "dna_absolute_error": 0.015078660026456747,
        "ldh_absolute_error": 0.01387579836295294
      },
      {
        "label": "thioridazine",
        "dna_absolute_error": 0.03271670192555376,
        "ldh_absolute_error": 0.011715891743623308
      }
    ],
    "route_01": [
      {
        "label": "azathioprine",
        "dna_absolute_error": 0.05378602773663288,
        "ldh_absolute_error": 0.004158036441239021
      },
      {
        "label": "carbamazepine",
        "dna_absolute_error": 0.00942308332273556,
        "ldh_absolute_error": 0.003950291032351894
      },
      {
        "label": "chlorpromazine",
        "dna_absolute_error": 0.02263527215773553,
        "ldh_absolute_error": 0.010139857726374268
      },
      {
        "label": "glibenclamide",
        "dna_absolute_error": 0.04232885928847674,
        "ldh_absolute_error": 0.0002815298577467651
      },
      {
        "label": "ketoconazole",
        "dna_absolute_error": 0.020002287863826296,
        "ldh_absolute_error": 0.019269897423016547
      },
      {
        "label": "propylthiouracil",
        "dna_absolute_error": 0.019751017675111116,
        "ldh_absolute_error": 0.01480554581097926
      },
      {
        "label": "thioridazine",
        "dna_absolute_error": 0.02358562594940372,
        "ldh_absolute_error": 0.010574937862106504
      }
    ],
    "route_10": [
      {
        "label": "azathioprine",
        "dna_absolute_error": 0.07731477969141964,
        "ldh_absolute_error": 0.005931772749782738
      },
      {
        "label": "carbamazepine",
        "dna_absolute_error": 0.010378641423016477,
        "ldh_absolute_error": 0.0033365992939002886
      },
      {
        "label": "chlorpromazine",
        "dna_absolute_error": 0.029700825799552022,
        "ldh_absolute_error": 0.011139854172232955
      },
      {
        "label": "glibenclamide",
        "dna_absolute_error": 0.028150737714835006,
        "ldh_absolute_error": 0.0010489075797304181
      },
      {
        "label": "ketoconazole",
        "dna_absolute_error": 0.03169750130716509,
        "ldh_absolute_error": 0.01805538555188324
      },
      {
        "label": "propylthiouracil",
        "dna_absolute_error": 0.015367324142847694,
        "ldh_absolute_error": 0.013938728792308508
      },
      {
        "label": "thioridazine",
        "dna_absolute_error": 0.032430110179477944,
        "ldh_absolute_error": 0.011652140466175798
      }
    ],
    "route_11": [
      {
        "label": "azathioprine",
        "dna_absolute_error": 0.05349729375058809,
        "ldh_absolute_error": 0.004095133686653485
      },
      {
        "label": "carbamazepine",
        "dna_absolute_error": 0.009711277077011582,
        "ldh_absolute_error": 0.0040134077681033276
      },
      {
        "label": "chlorpromazine",
        "dna_absolute_error": 0.022332758899533567,
        "ldh_absolute_error": 0.010082412823204434
      },
      {
        "label": "glibenclamide",
        "dna_absolute_error": 0.04261676814179283,
        "ldh_absolute_error": 0.0003447594403227505
      },
      {
        "label": "ketoconazole",
        "dna_absolute_error": 0.019710572379663893,
        "ldh_absolute_error": 0.01933161923179183
      },
      {
        "label": "propylthiouracil",
        "dna_absolute_error": 0.020039681791502062,
        "ldh_absolute_error": 0.014868476240334827
      },
      {
        "label": "thioridazine",
        "dna_absolute_error": 0.023299034203327906,
        "ldh_absolute_error": 0.010511186584658994
      }
    ],
    "null_rho_0": [
      {
        "label": "azathioprine",
        "dna_absolute_error": 0.076872230261811,
        "ldh_absolute_error": 0.0040245247947208185
      },
      {
        "label": "carbamazepine",
        "dna_absolute_error": 0.01486710612677622,
        "ldh_absolute_error": 0.003983827831103515
      },
      {
        "label": "chlorpromazine",
        "dna_absolute_error": 0.026611921718059484,
        "ldh_absolute_error": 0.010048456659129679
      },
      {
        "label": "glibenclamide",
        "dna_absolute_error": 0.029879485136573125,
        "ldh_absolute_error": 0.0004577955845719295
      },
      {
        "label": "ketoconazole",
        "dna_absolute_error": 0.029510937377038693,
        "ldh_absolute_error": 0.01942167788865401
      },
      {
        "label": "propylthiouracil",
        "dna_absolute_error": 0.018882654402461396,
        "ldh_absolute_error": 0.014889444158719511
      },
      {
        "label": "thioridazine",
        "dna_absolute_error": 0.029800097641657697,
        "ldh_absolute_error": 0.01042731451337442
      }
    ],
    "null_direct": [
      {
        "label": "azathioprine",
        "dna_absolute_error": 0.07118383468020995,
        "ldh_absolute_error": 0.0018045763575353924
      },
      {
        "label": "carbamazepine",
        "dna_absolute_error": 0.013847793765615846,
        "ldh_absolute_error": 0.002885675389898701
      },
      {
        "label": "chlorpromazine",
        "dna_absolute_error": 0.024024062797468715,
        "ldh_absolute_error": 0.007072911718414732
      },
      {
        "label": "glibenclamide",
        "dna_absolute_error": 0.03219891013397036,
        "ldh_absolute_error": 0.004404484661959862
      },
      {
        "label": "ketoconazole",
        "dna_absolute_error": 0.02527919963281655,
        "ldh_absolute_error": 0.023285122528258984
      },
      {
        "label": "propylthiouracil",
        "dna_absolute_error": 0.019426812775414914,
        "ldh_absolute_error": 0.013606835874533152
      },
      {
        "label": "thioridazine",
        "dna_absolute_error": 0.02864399157383557,
        "ldh_absolute_error": 0.007577539764989982
      }
    ]
  },
  "strongest_nonisomorphic_ordinary": "refit",
  "absolute_dna_gain": -0.008364303766192367,
  "relative_dna_gain": -0.44136390587501845,
  "useful_gain_gate": false,
  "state_route_increment": true,
  "function_route_increment": true,
  "observed_rna_increment": false,
  "decision": "STOP_THIS_CONFIGURATION_EXPANSION",
  "agent_benefit": "NOT_TESTED",
  "inheritance_benefit": "NOT_TESTED",
  "rsi_c4": "NOT_TESTED",
  "later_opened": false,
  "prediction_seal_sha256": "44dcf830630aafda4e7bf23bad1c7ffe73045831620a7efed74b653dce47dc23",
  "development_high_function_casts": 14,
  "later_function_casts": 0,
  "development_high_rna_opened": false,
  "warning": "Historical development exposure and source selection remain; intervals would be descriptive only."
}

--- NUMERICAL_RECEIPT.json ---
{
  "status": "PREDICTIONS_COMPLETE_UNSCORED",
  "estimator_fits": 4336,
  "base_packs": 602,
  "bank_cache_hits": 1378,
  "pipeline_evaluations": 1552,
  "operations": {
    "transform_fits": 3739,
    "coefficient_fits": 4336,
    "linear_solves": 3176,
    "svd_calls": 2320
  },
  "elapsed_seconds": 417.375,
  "peak_working_set_bytes": 368934912
}

--- REFERENCE_ASSEMBLY_AUDIT.json ---
{
  "status": "PASS",
  "utc": "2026-10-22T03:43:37.179219+00:00",
  "checks": [
    {
      "label": "WY-14643",
      "level": "Middle",
      "max_decimal_contrast_difference": 3.2890357104520263e-15
    },
    {
      "label": "WY-14643",
      "level": "High",
      "max_decimal_contrast_difference": 3.164135620181696e-15
    },
    {
      "label": "allyl alcohol",
      "level": "Middle",
      "max_decimal_contrast_difference": 3.219646771412954e-15
    },
    {
      "label": "allyl alcohol",
      "level": "High",
      "max_decimal_contrast_difference": 3.316791286067655e-15
    },
    {
      "label": "azathioprine",
      "level": "Middle",
      "max_decimal_contrast_difference": 3.219646771412954e-15
    },
    {
      "label": "benzbromarone",
      "level": "Middle",
      "max_decimal_contrast_difference": 3.3029134982598407e-15
    },
    {
      "label": "benzbromarone",
      "level": "High",
      "max_decimal_contrast_difference": 3.400058012914542e-15
    },
    {
      "label": "carbamazepine",
      "level": "Middle",
      "max_decimal_contrast_difference": 3.2890357104520263e-15
    },
    {
      "label": "carbon tetrachloride",
      "level": "Middle",
      "max_decimal_contrast_difference": 3.3306690738754696e-15
    },
    {
      "label": "carbon tetrachloride",
      "level": "High",
      "max_decimal_contrast_difference": 3.3029134982598407e-15
    },
    {
      "label": "chlorpromazine",
      "level": "Middle",
      "max_decimal_contrast_difference": 3.4416913763379853e-15
    },
    {
      "label": "cimetidine",
      "level": "Middle",
      "max_decimal_contrast_difference": 3.4555691641457997e-15
    },
    {
      "label": "cimetidine",
      "level": "High",
      "max_decimal_contrast_difference": 3.2855662635000726e-15
    },
    {
      "label": "cyclophosphamide",
      "level": "Middle",
      "max_decimal_contrast_difference": 3.247402347028583e-15
    },
    {
      "label": "cyclophosphamide",
      "level": "High",
      "max_decimal_contrast_difference": 3.219646771412954e-15
    },
    {
      "label": "diazepam",
      "level": "Middle",
      "max_decimal_contrast_difference": 3.3029134982598407e-15
    },
    {
      "label": "diazepam",
      "level": "High",
      "max_decimal_contrast_difference": 3.3584246494910985e-15
    },
    {
      "label": "diclofenac",
      "level": "Middle",
      "max_decimal_contrast_difference": 3.2751579226442118e-15
    },
    {
      "label": "diclofenac",
      "level": "High",
      "max_decimal_contrast_difference": 3.3306690738754696e-15
    },
    {
      "label": "ethionine",
      "level": "Middle",
      "max_decimal_contrast_difference": 3.191891195797325e-15
    },
    {
      "label": "ethionine",
      "level": "High",
      "max_decimal_contrast_difference": 3.2404634531246757e-15
    },
    {
      "label": "glibenclamide",
      "level": "Middle",
      "max_decimal_contrast_difference": 3.316791286067655e-15
    },
    {
      "label": "griseofulvin",
      "level": "Middle",
      "max_decimal_contrast_difference": 3.2890357104520263e-15
    },
    {
      "label": "griseofulvin",
      "level": "High",
      "max_decimal_contrast_difference": 3.247402347028583e-15
    },
    {
      "label": "haloperidol",
      "level": "Middle",
      "max_decimal_contrast_difference": 3.3306690738754696e-15
    },
    {
      "label": "haloperidol",
      "level": "High",
      "max_decimal_contrast_difference": 3.164135620181696e-15
    },
    {
      "label": "indomethacin",
      "level": "Middle",
      "max_decimal_contrast_difference": 3.3306690738754696e-15
    },
    {
      "label": "indomethacin",
      "level": "High",
      "max_decimal_contrast_difference": 3.1086244689504383e-15
    },
    {
      "label": "isoniazid",
      "level": "Middle",
      "max_decimal_contrast_difference": 3.273423199168235e-15
    },
    {
      "label": "isoniazid",
      "level": "High",
      "max_decimal_contrast_difference": 3.3306690738754696e-15
    },
    {
      "label": "ketoconazole",
      "level": "Middle",
      "max_decimal_contrast_difference": 3.2057689836051395e-15
    },
    {
      "label": "labetalol",
      "level": "Middle",
      "max_decimal_contrast_difference": 3.247402347028583e-15
    },
    {
      "label": "labetalol",
      "level": "High",
      "max_decimal_contrast_difference": 3.3861802251067274e-15
    },
    {
      "label": "lomustine",
      "level": "Middle",
      "max_decimal_contrast_difference": 3.3306690738754696e-15
    },
    {
      "label": "lomustine",
      "level": "High",
      "max_decimal_contrast_difference": 3.282096816548119e-15
    },
    {
      "label": "methapyrilene",
      "level": "Middle",
      "max_decimal_contrast_difference": 3.3653635433950058e-15
    },
    {
      "label": "methapyrilene",
      "level": "High",
      "max_decimal_contrast_difference": 3.247402347028583e-15
    },
    {
      "label": "omeprazole",
      "level": "Middle",
      "max_decimal_contrast_difference": 3.3029134982598407e-15
    },
    {
      "label": "omeprazole",
      "level": "High",
      "max_decimal_contrast_difference": 3.2057689836051395e-15
    },
    {
      "label": "perhexiline",
      "level": "Middle",
      "max_decimal_contrast_difference": 3.2751579226442118e-15
    },
    {
      "label": "perhexiline",
      "level": "High",
      "max_decimal_contrast_difference": 3.3341385208274232e-15
    },
    {
      "label": "phenylbutazone",
      "level": "Middle",
      "max_decimal_contrast_difference": 3.247402347028583e-15
    },
    {
      "label": "phenylbutazone",
      "level": "High",
      "max_decimal_contrast_difference": 3.164135620181696e-15
    },
    {
      "label": "phenytoin",
      "level": "Middle",
      "max_decimal_contrast_difference": 3.3306690738754696e-15
    },
    {
      "label": "phenytoin",
      "level": "High",
      "max_decimal_contrast_difference": 3.4416913763379853e-15
    },
    {
      "label": "propylthiouracil",
      "level": "Middle",
      "max_decimal_contrast_difference": 3.2127078775090467e-15
    },
    {
      "label": "rifampicin",
      "level": "Middle",
      "max_decimal_contrast_difference": 3.164135620181696e-15
    },
    {
      "label": "rifampicin",
      "level": "High",
      "max_decimal_contrast_difference": 3.191891195797325e-15
    },
    {
      "label": "tetracycline",
      "level": "Middle",
      "max_decimal_contrast_difference": 3.230055112268815e-15
    },
    {
      "label": "tetracycline",
      "level": "High",
      "max_decimal_contrast_difference": 3.3133218391157016e-15
    },
    {
      "label": "thioacetamide",
      "level": "Middle",
      "max_decimal_contrast_difference": 3.191891195797325e-15
    },
    {
      "label": "thioacetamide",
      "level": "High",
      "max_decimal_contrast_difference": 3.2751579226442118e-15
    },
    {
      "label": "thioridazine",
      "level": "Middle",
      "max_decimal_contrast_difference": 3.164135620181696e-15
    },
    {
      "label": "valproic acid",
      "level": "Middle",
      "max_decimal_contrast_difference": 3.2751579226442118e-15
    },
    {
      "label": "valproic acid",
      "level": "High",
      "max_decimal_contrast_difference": 3.3029134982598407e-15
    }
  ],
  "state_scalar_comparisons": 3007125,
  "function_mean_sd_comparisons": 316,
  "maximum_decimal_state_difference": 3.4555691641457997e-15,
  "development_high_function_casts": 0,
  "later_opened": false,
  "elapsed_seconds": 33.186999999918044,
  "scope": "Separate Decimal aggregation and identity/absence implementation; not independent MAS5 or biological validation."
}

--- GATE_GEOMETRY_AUDIT.json ---
{
  "status": "PASS",
  "biological_values_opened": 0,
  "model_fits": 0,
  "random_synthetic_instances": 10000,
  "inequality": "MAE((candidate+direct)/2)-MAE(candidate) <= (MAE(direct)-MAE(candidate))/2",
  "proof": "Triangle inequality pointwise, then average and subtract candidate MAE.",
  "necessary_for_original_absolute_gate": "direct_MAE-candidate_MAE > 0.04",
  "corollary": "If selected direct developmentMAE <=0.04, strict >0.02 gain over the candidate-containing half mixture is impossible.",
  "not_universal_impossibility": "direct=.05 and candidate=.001 gives mixture=.0255, gain=.0245; the full gate additionally requires beating all other alternatives and route/noRNA increments.",
  "exact_example": {
    "candidate": "0.001",
    "direct": "0.04",
    "mixture": "0.0205",
    "gain": "0.0195"
  },
  "decision": "KEEP_FROZEN_GATE; interpret stop as utility/configuration decision, not proof of absent information.",
  "frozen_code_changed": false,
  "reporting": "Report continuous candidate-vs-pure-direct, noRNA, routes and mixture contrasts separately. No post-result threshold relaxation, novel-core or RSI inference."
}

--- NUMERICAL_AMENDMENTS.md ---
# Frozen numerical protocol: authoritative amendments

Read with the adopted independent contract below. No biological RNA value has been opened when these decisions are frozen. Scope, split, assay units, original utility thresholds, nested fold ownership and stops are adopted unchanged. No new algorithm core is cleared. The experiment can falsify a useful feedback regularization hypothesis, and cannot establish agents, inheritance or RSI.

1. Preprocessing is PREPROCESS_PROTOCOL.md. Use original manufacturer CDF environment through native affy lookup; namespace installation failed. Fixed 54675 probe coordinates. Four-gene mapping is already independently frozen, so add the ordinary four-gene baseline now, before RNA conversion. Its eight configurations: shared b-alpha .1/1, direct penalty .01/.1/1/10. Predict y_H-b_H by ridge from [designM/H, y_M/SD, four mean-log difference gene values, b_M/b_H], with the shared fold-local base b; no actual all-probe x_M in this family. Add b_H. Same eight source-selection configurations.

2. Fit means one estimator coefficient solution, including multioutput with a shared loss. Two correction maps count two fits. A b/f/h pack counts three. Exact base cache uses 301 training sets x2 alphas x3=1806. Corrections:3rho x8configs x24outer x2maps +3selected x2=1158. Direct/KRR/noRNA:3x8x24+3=579. Weighted refit:8x24x3 +7development x3=597. Four-gene:8x24+1=193. Null:2maps+1direct=3. Total conservative ceiling4336 estimator fits. Pipeline evaluations, transform fits, SVD, retries, and cache hits are separate counters. No extra grid, retry selection or uncounted coefficient fits. If exact code factoring yields fewer actual solves, disclose reuse rather than pretend budget was spent. The old 3567 count is an error, not a valid alternative estimator accounting convention.

3. Weighted refit: source observation weights1 and exactly one added compound-mean Middle row weight w in {1,4,16,64}. Original source-fitted input block transforms retained (including original h transform), but weighted centering/intercepts recomputed. For each estimator minimize sum_i w_i||Y_i-predict_i||² + n_rows*alpha||A||². This fixes regularization convention: w acts as multiplicity; denominator is row count, not sum weights. Update b first; recompute b_new for ALL source and query rows, and recompute ALL h targets y-b_new and b-derived features. Update f with source M/H and queryMiddle. Update h using actual states and recomputed residuals. Each update is one coefficient fit, no hidden target. Refit prediction uses updated g(updated f_H,H). No queryHigh RNA/function.

4. One shared nuisance bank for corrections and all direct families. For outer i, inner j nuisance excludes BOTH i,j; targets for j are accessed only after that prediction, and outer i High cannot appear in any train feature/transform. Final error rows use leave-one-source-out; final nuisance is all-source. Fixed probeset coordinates across folds. Same fit/config maps for all 2x2 route masks; no retuning masks. v-only still uses observedRNA. Genuine no-observedRNA family removes all actualRNA-derived features.

5. Low-rank maps use float64 NumPy SVD with fixed software/version receipt, stable sorted singular values and explicit numerical-rank tolerance max(shape)*eps*smax. Q sign cancels in QQ'; no sign-dependent claims. rho0 retains two-block normalization and zeroed cross-block weights. Store low-rank factors. Centered RBF kernel uses a trained intercept. All block scales are training-only energy RMS. Ridge duplicate columns can change effective regularization; report the frozen feature set instead of claiming duplication invariance.

6. Relative to actual strongest nonisomorphic ordinary comparator, useful gain must be strictly >.02 absolute DNA MAE AND >=10% relative. All prior nine families and new ordinary families are reported. rho0's exact ordinary copy merged. Mixture is fixed50/50 and not tuned. Route comparisons and noRNA comparison require strictly lower MAE to support their respective increments; derangement is descriptive only, cannot rescue primary failure or establish significance. No bootstrap is confirmatory. Development already historically exposed. No single-N sample-efficiency claim.

7. Before modeling, code must pass independent primal/dual, weighted WLS, full-rank reduced-ridge identity, collapsed-sequential identity, train-only scaling, and fold-owner/heldoutHigh-sentinel tests. Seal exact numerical code/data/outputs and prediction files before isolated scoring reads developmentHigh function. This does not restore historical blinding. Numerical execution needs a separate code freeze; this protocol only permits the fixed array-local conversion after preprocessing authorization.

8. API audit: first two direct reviews used thinking with9000 completion tokens and returned EMPTY content with finish_reason=length (27264total tokens); these are failed review artifacts, not substantive reviews, despite the original client receipt label RESPONSE_RETAINED. Second calls use no-thinking and retained nonempty texts. Construction advocate and skeptic both treat candidate as ordinary constrained linear prediction. Root rejects reviewers' suggestions that the erroneous3567 count is valid under a second estimator convention, that duplicating ridge inputs never changes predictions, or that Q sign changes predictions. Root accepts source-residual recomputation, literal WLS weights, strict nuisance ownership and separate measurement ablation. Opposing replies and exact costs remain separate from empirical evidence.


--- GATE_GEOMETRY_INTERPRETATION.md ---
# Pre-result mathematical qualification of the fixed mixed comparator

This is an interpretation audit, not a protocol or code amendment. Download/array conversion remain live; no real fitted predictions or new development target scoring has occurred. Keep the original gate unchanged.

Let C and D denote the candidate and source-selected direct predictions, with equal-compound MAEs c and d on any target vector. Let m be the MAE of the frozen50/50 prediction mixture. Triangle inequality gives m≤(c+d)/2, hence m−c≤(d−c)/2. Because the strongest alternative has error at most m, exceeding it by strictly .02 requires d−c>.04. In particular if d≤.04 the absolute gate is impossible even for a perfect candidate. This is conditional, not a universal impossibility: c=.001,d=.05 and same-sign errors give m=.0255 and m−c=.0245, though other alternatives and ablations can still stop the configuration.

This clarifies why a failed utility gate does not prove absent RNA information, useless measured states, or invalid virtual-cell modeling. The ordinary pure-direct, no-observedRNA, route and fixed-mixture continuous errors must all be reported. The historical Middle-copy error .02335714 independently already forces candidate error<.00335714 for absolute utility; the mixed comparator imposes an additional necessary condition. These are demanding practical requirements chosen in the frozen study, not null hypotheses of zero effect.

The fixed mixture includes the candidate and requires its source selection plus the selected direct component. It has no extra observations or tuned mixing weight; its program/computation cost is the disclosed sum/reuse of its two components. Do not claim it is a standalone eight-configuration family or a compute-matched single model. The current RNA pilot tests predictive headroom, not a completed equal-budget program-search/CL/AL/agent/RSI benchmark. Those remain obligations of the full goal if a suitable core is later found.

No threshold, comparator inclusion, fitted method, representation, endpoint, sample selection, or later-set access changes. A conditional structural difficulty discovered in the gate must be preserved alongside any negative outcome. It may guide the design of a genuinely separate future preregistration, not rescue this one.


--- APPLICATION_SCOPE_NOTE.md ---
# Primary-method scope revalidation while the frozen experiment runs

This rechecks evidence already established in DOSE_LINEAGE_REPORT.md of the earlier functional qualification phase. It is not a new literature discovery or permission to change the running pilot. No new RNA, functional endpoint, later value, or HTTP response was opened for this check.

The exact retained original paper is Igarashi et al., DOI10.1093/nar/gku955. Its in-vitro highest concentration targets80–90%relative survival, with maximum-solubility exceptions. The paper does not authenticate which prescreen assay, time, or cell lot was used or its independence from released DNA/LDH. Thus dose choice carries prior functional-screening information, but it neither forces currentHigh outcomes to85% nor proves the present31-label outcome variance/noise floor. The frozen constant85% baseline and all actual observed baselines remain as registered.

Application remains confirmation within an already pre-screened, continuously exposed menu, using Middle2h molecular state and Middle24h functional feedback to forecast High24h published DNA/LDH survival assays. It is not unknown-compound safe-dose discovery, clinical hepatotoxicity prediction, withdrawal/rescue optimization, secretory liver function, or same-cell tracking. Microarray2h sampling does not certify2h result availability or a cost advantage over24h functional assays.

The six human hepatocyte lots in the original project do not establish sample-to-lot identities or independent donor tasks for this split. Compound/proxy grouping is the current unit; donor/culture generalization remains untested. Relative MAS5 signals also do not identify absolute RNA/cell under toxicity, as already recorded in preprocessing.

Conditional dose selection may limit the value of a later result for de-novo discovery, but cannot by itself predict this pilot's error or establish zero RNA information. Report continuous differences, the fixed mixture gate's geometric limitation, historical development exposure and all technical failures. Keep every source/development sample, target, model, comparator and threshold unchanged; later14 and AZ413 reserve remain unopened.

Locator failures retained: the initial broad local search included a nonexistent log/20261022/tggates_method_audit directory (the research directory exists under that name); XML stored as long lines made its display excessive. Follow-up used the actual existing dose-lineage report and XML paragraph parsing. These are retrieval limitations, not negative scientific evidence.


--- source-selected configurations (selection-exposed source scores) ---
{"rbf": {"config": {"family": "rbf", "alpha": 0.1, "penalty": 0.1, "factor": 2.0}, "dna_mae": 0.027922647443058238}, "direct": {"config": {"family": "direct", "alpha": 0.1, "penalty": 0.1}, "dna_mae": 0.02798040622240554}, "four_gene": {"config": {"family": "four_gene", "alpha": 0.1, "penalty": 1.0}, "dna_mae": 0.028627614432664455}, "no_rna": {"config": {"family": "no_rna", "alpha": 0.1, "penalty": 0.1}, "dna_mae": 0.028127719305035135}, "refit": {"config": {"family": "refit", "alpha": 1.0, "weight": 16.0}, "dna_mae": 0.02428217490725396}, "rho_0": {"config": {"family": "rho_0", "alpha": 0.1, "penalty": 1.0, "rank": 1, "rho": 0.0}, "dna_mae": 0.026990795605213506}, "rho_0.5": {"config": {"family": "rho_0.5", "alpha": 0.1, "penalty": 1.0, "rank": 2, "rho": 0.5}, "dna_mae": 0.02693037872464268}, "rho_1": {"config": {"family": "rho_1", "alpha": 0.1, "penalty": 1.0, "rank": 2, "rho": 1.0}, "dna_mae": 0.026891794695134533}}