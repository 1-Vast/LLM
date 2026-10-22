# G0a 独立只读代码审查

日期：2026-10-21，Asia/Shanghai。审查对象：`research/rsi_next_qualification_20261021/blend_qualification.py`、本包 `PROTOCOL.md`、运行输出和其依赖的旧 `run_models.py` / `ptv_tasks.py` / `ptv_direct.py` / `ptv_data.py` / `ptv_models.py`。未修改主代码、未重训练、未调用 API、未查看任何新的封存观测。当前旧 final 明确是暴露开发数据。

## 总体判断

**未发现能够推翻本次局部 STOP 的数据流或统计错误。** 四类权重在 selection 上都选到 0；实际主要比较全是同一个 B1。应报告“预设选择程序未选择加入这些缓存模型分数”，不能把差值 [0,0] 当作对一个不同世界模型效应的精确否定或等价检验。

当前数据支持停止对该配置继续投入架构/程序搜索，不支持“所有 PTV 方法均无潜力”“轨迹机制被排除”“世界模型没有额外信息”等宽结论。

## 发现与修正状态

### 1. 必须修复的资源记录：Windows 内存 API 失败被报为 0（已即时通知协调者）

初次运行 `RESOURCES.json` 的 `peak_working_set_bytes` 为 0。初版没有声明 `GetCurrentProcess` 和 `GetProcessMemoryInfo` 的 ctypes 函数签名，也没有检查 BOOL 返回值。64 位 Windows 上伪句柄/参数转换错误可使调用失败，结构体默认 0 被写成貌似合法内存结果。

审查过程中已观察到协调者将其改成独立 `peak_memory()`：`HANDLE` / `BOOL` 签名、`use_last_error=True`、失败抛 `WinError`。**该代码修复方向正确。** 在看到带有非零有效计数的新运行记录之前，初次 0 记录不能用来证明满足 RAM 目标。应保留这次失败和更正，不从另一个短进程读取 RSS 冒充原过程峰值。此问题不改变科学 STOP。

初次结果的脚本哈希为 `d698e6c4b1ab1753d49901c73446ae71405241b75fc0af333772a0b14c93e1d1`，`wall_seconds=20.7001112001`，`process_cpu_seconds=22.828125`。这些是审查时读到的第一版结果，不代表随后修复重跑值。

### 2. final 上选择最强比较者：当前退化情形安全，通用 CI 不应照搬

`best = max(alternatives, key=lambda a: macro(table, a))` 用旧 final 的均值选择比较者 family；每一 family 内的 mixing weight 确实只按 selection 选。因此没有发现 final 标签进入权重优化，但 strongest comparator 的 family 是事后选择的。

当前三种 `selected_nonworld` 全都等于 B1，比较者无论如何选择都得到相同向量，对 STOP 无影响。若以后并列不成立，该 pairwise bootstrap 区间没有纳入比较者选择过程；需预先按 selection 冻结 family，或报告/门控所有预定比较并采用相应同时区间。不能把现在的实现升级为一般的确认性最强对照检验。

### 3. “保存权重后才加载 final outcome”的注释字面不成立

`prep = T.Prep()` 内部 `Release()` 已在选择前载入所有原始 phenotype 标签和 expression cache；`ex=experiments(1)` 也含原 final 标签。检查计算依赖后，final 标签未进入 `selection_direct`、`choose_weights` 或 `SELECTED_WEIGHTS` 的选择计算，这是正确的。

应写“权重只依赖 selection，原 final 标签未用于该计算”，不要写物理上直到冻结后才读取 final。旧结果已暴露，本包也始终标开发，所以不影响当前结论，但新独立研究需要真正 evaluator 隔离而非变量命名隔离。

### 4. 数据身份复现记录尚可加强

当前 snapshot 验证 161 个旧冻结文件和 repair 全部 71 文件，共 232；它不覆盖 `data/external/ptv1_proteintalks_20261021` 的本次实际 CSV / cache 内容。`INPUTS.json` 记录 `SOURCE_MANIFEST.json` 的 hash，不能单独证明当前源文件仍等于 receipt。`attach_world` 已验证当前功能标签与缓存标签逐项相等，但 baseline/fingerprint/cache 仍可能独立漂移。

若声称本包重新验证来源身份，应补核实际 source bytes / cache identity；否则明确依赖历史 source 验证。无需为当前负结论重开旧试验。本条是可复现证据边界，不是已有输入漂移证据。

## 已核实正确或已充分披露的项目

| 项目 | 审查结果 |
| --- | --- |
| 训练谱系范围 | 旧 `run_models.py` 中 selection 是 dev+sel，排除 held-out lineage；新 direct_scores 同样排除 lineage。不是错误地将“应仅 dev”的训练 scope 扩大。final 都用 dev+sel。 |
| complete-case 训练标签 | 读源 metadata 计 1535 个实验；9 个缺失完整 6/24/48 h 轨迹的单元全是 HCC1937 双药。dev+sel 共 943 条条件，旧 world 保留 934；单药有标签训练记录 677，未因缺轨迹不公平地减少。 |
| 分子监督仍不一致 | M1 使用 934 条单/双药分子监督，M2 及 direct 不使用同样 molecular objective。这是目前明确承认的非识别，不能称 same-supervision 机制消融。 |
| selection 配置 | 样例 DU4475 的 full 来自 sel30、no_traj 来自 sel，二者同 train_cells、n_train=871、CUDA、hidden=16；均取 p_e30。no_traj 保存过45 epoch不影响使用已存30 epoch预测。 |
| 输入和药池配对 | 代码将全部 arms 先 inner-join 同一 stock+drug frame，validate one_to_one，并检查缓存/source 标签；最终每个背景药池均14，7 stock / 7 lineage。未跨用 repair 的20药池数字。 |
| 潜在静默排除 | inner join 一般会静默丢失缺预测单元；本次 metadata 缺轨迹仅双药，最终 n_pool 与旧14药池一致，未见改变结论的排除。未来应保存 join 前后 census/反连接。 |
| selection 权重 | 四 family 均5 slots，相同 selection macro precision@5、先 stock 后 lineage；tie 偏低 world/direct 权重，协议一致。selection B1=0.82，其余任何非零权重均更低。 |
| 随机种子 | 两个缓存 final seed 单独报告，不把种子计为生物 n；direct HGB 固定 seed0 是确定基准，合理。旧 seed 在模型初始化后才设置，不能声称受控相同初始化或完整训练复现；本包明确列限制。 |
| state 污染 | 没有新 world fine-tune 或跨 episode state update；直接模型每次 fit_predict 重建 sklearn estimator，未见持久训练状态把 held-out 标签带回模型。 |
| 输入型跨阶段处理 | Direct PCA 使用所有已知背景 baseline，且 fingerprint PCA 使用整个已知药库；是明示 transductive preprocessing，不能外推未见输入归纳泛化。没有发现 treated outcome 被传入直接预测 features。 |
| bootstrap 单位 | contrast 先按 lineage+arm 平均，抽取7个 paired lineage 差值、有放回、有重数；没有把 stock/cell/seed当额外生物重复。当前 final 每谱系一个 stock。 |
| 缺失标签 | source和缓存均先排除缺标签，无把 missing 当negative的路径；AUROC 单类时返回 null。 |
| 停止计算 | 需要两个 seed 都达到0.09且 lower>0才继续；当前都不通过。固定半混合也均未胜 B1。没有因换终点或微小概率改善而晋级。 |
| 操作边界 | 代码只写本包 log，`-B`/dont_write_bytecode 防旧目录字节码写入；未发现旧目录 mutation、GPU训练、API请求或下载路径。 |

## 独立轻量复核数字

读取保存的 `decisions.csv` 按 seed+arm 重算均值：B1 两 seed 均 0.742857；M1 0.514286 / 0.542857；固定半 M1 两 seed 均 0.685714；固定半 logistic / HGB 均 0.714286；四类 selected mixture 全为 0.742857。与 RESULTS 一致。

selection grid：B1 0.82；full 权重 .25/.5/.75/1 对应 .74/.66/.60/.64；no_traj 对应 .74/.66/.66/.60；logistic 对应 .74/.74/.74/.70；HGB 对应 .74/.60/.60/.52。四个零权重选择不是 tie-break 人为制造的优胜。

复核只读取文件，用 `D:/anaconda/envs/maestro/python.exe -B -c ...` 检查 metadata 时间集合、读取当前输出 CSV 分组；没有运行/重训原模型。源码审查采用 `Get-Content` 和 `rg -n -g '*.py'`，未访问 `.env`。

## 可接受的交付表述

“在已暴露 PTV-1 的原14药候选池上，用同一训练谱系范围和相同五点混合搜索，selection 对四种新增分数都选择零权重；两个缓存模型运行均未产生加入世界模型分数的开发依据。固定半混合也低于 B1。按预设资源门停止该配置搜索。该结果未识别轨迹机制、Agent、继承或 RSI，且不能排除其他训练/校准方案。”
