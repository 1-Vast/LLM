# Third GET source selection

完整v1.0tree SHA `1a2c164ab019510d45c1e9165b109492b6ad7236`，truncated=false。README pinned blob `e88892c6df960990946e1b282098efaee9159af8`明确：`main_td.rs`、`lib.rs`和Cargo生成t-MDP policy/rewards；`plot_mdp_data.py`是读取pickle重画Figure5；`AnalyzeIC50s.m`读取TempData.mat做figures；QuickLook读取day*.mat。

唯一剩余GET选择 **main_td.rs**，Gitblob **`0abcf093fcbf14a3c1856e4eb46fa8fb47fd9f75`**，19,427decodedbytes。理由：它最接近transition/valueiteration与time-dependentoracle生成器；不读取data.mat、pickle或plot数据。源码若含hardcodedresponsearrays，先做numeric-literal-redacted投影后再读，raw代码仅保留在来源文件不执行。不得为数据读入再加GET；若不足报告pinned下一对象。
