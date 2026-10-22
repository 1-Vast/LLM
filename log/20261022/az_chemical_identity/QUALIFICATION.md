# AZ 化学身份字典资格：NOT_ESTABLISHED

2026-10-22。这是独立于模型性能的只读身份核查，未修改冻结面板、源文件或实验方法。

## 已确认与未确认

既存纯元数据 census 含46个源药物ID；论文正文报告37种 individual drugs。两者计数差异需要确切字典解释，不能直接推出9组别名或任何特定ID等价。原文将化合物及组合信息指向 `EMS194010-supplement-Table_S2.xlsx`，其声明大小19,152字节、MD5为 `1661f9b51a2e204e9af8a3f6f94ebe80`。

当前冻结设计为12个target pairs、13个query pairs，共11个ID：2426、2427、2428、2429、2430、2431、2433、2434、2435、2436、2574。两池的无序source-ID pairs交集为空。该结果核实源ID层面的分离，不能核实化学组合分离。

**没有取得可核实的 sourceID→chemical 映射：全体46/46、当前设计11/11均保留 UNRESOLVED。** 所有156个query×target化学身份比较均无法裁决。没有发现可确证的别名泄漏，也不能据此宣称化学独立。字典与全部未解析ID分别保存在 `CHEMICAL_DICTIONARY.json` 和 `UNRESOLVED.json`，面板信息及判定在 `PAIR_QUALIFICATION.json`。

## 支持证据、冲突与访问结果

- 原始正文及其获取receipt已在既存log保存，当前读取后SHA256保持不变。`LOCAL_PRIMARY_PROJECTION.json`保存相关叙述、原始S2文件名与来源哈希。
- 原有Figshare项目/资源元数据只有响应文件清单；作者figure代码也未提供确切身份字典。旧glossary明确 `lib1/lib2` 是布局tag，`lib*_drug_id` 是内部GDSC标识，不能从这些字段直接还原化学名。
- 四次新primary HTTP请求已达到本次上限：直接PMC403、EuropePMC HTML403、由正文URN导出的CDN404、EuropePMC supplementaryFiles 200。
- 第四次请求为补充材料ZIP。为避免无界下载，达到64MiB上限后关闭并保留67,112,895字节原始前缀。实际保留量略超过阈值，因按网络chunk检查上限。离线仅检查ZIP local-header文件名，确认exact S2文件名不在该前缀中，详见 `ZIP_PREFIX_METADATA.json`。其他entry均未解码；没有打开S3、S13、S18等表的数值。
- 四份HTTP receipt分别保存URL、UTC、status、保留正文或前缀SHA256。第四份明确 `body_complete=false`，其哈希不是完整补充包哈希。未绕过403、未重试同URL、未增加第五次请求。

## 对当前实验解释的精确影响

当前任务仍可按其冻结定义描述为：利用其他source-ID pairs的付费观测，预测指定source-ID pair的CTG响应。身份资格缺口使“目标化学组合未被购买过”这一更强描述未建立，不等于已经证明target leakage。

即使后续取得同名、同结构或同active-moiety证据，也需要另核盐型、制剂、药剂、stock及剂量定义。化学身份相同不自动等价于同treatment；不能静默合并、修面板或据此重挑目标。任何确认的跨池别名应先显式报告资格漏洞，并按预先说明的边界解释现有结果。

本次按停止条件结束：没有确切字典，不猜测药名，不追加下载，不将不确定映射用于模型或选择。没有source CSV读取、paid arrays读取、模型结果读取或reserve数值响应访问。原设计所含reserve cell ID仅作为公开设计元数据曾显示，未作任何选择使用。

所有新代码在 `research/az_chemical_identity_20261022/`，所有探索、失败、字典与receipt均在本目录。`QUALIFICATION_RECEIPT.json`核对新HTTP body哈希、旧来源未改变及访问边界。
