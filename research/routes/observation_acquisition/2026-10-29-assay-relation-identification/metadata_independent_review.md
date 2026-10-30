# 固定三个精确剂量键的独立复算

2026-10-29，同轮第三单元必要数值核对，不增加研究 pass。先完整读本轮 `metadata_protocol.md`；未读 root 的 `audit_metadata.py` 或 `metadata_result.json`，未收到预计计数。独立脚本为 `metadata_independent_review.py`，一次执行产生 `metadata_independent_review.json`，其中保存各药完整 cell 集合及三者交集；未为求一致重跑。requested_model=gpt-6.1-sol、requested_effort=high；effective/usage/费用 unknown。

输入仅为 `../2026-10-29-edit-support-audit/primary_metadata.json`，SHA256 `d426f1c3fcbe23034235754d8cd418934a2eac150f82d0ffb7cea9e653559611`，实际匹配授权值。文件 2,109,777 字节，8058 条派生记录，字段限于 project/cell/drug_id/ref/doses_uM。

| project | drug_id | 精确正有限 Decimal 剂量/uM | 该项目该药记录数 | 剂量匹配记录数 | 不同 MASTER_CELL_ID 数 |
|---|---|---|---:|---:|---:|
| 2 | 2428 | 0.00100053 | 733 | 733 | 733 |
| 2 | 2429 | 0.00100053 | 733 | 733 | 733 |
| 2 | 2430 | 0.01000527 | 733 | 733 | 733 |

三个指定集合的交集为 **733 个不同 MASTER_CELL_ID**。按原字符串匹配项目/药物/细胞身份，用 Decimal 数值精确相等比较剂量，无浮点容差、四舍五入、跨项目身份合并或 ref 平均。扫描8058条输入记录以选择指定项目和三个药物，仅对选中2199条记录解析剂量并建集合；未枚举其他菜单、未重做全52185项组合、未认证全局最大。

本次一次固定元数据复算的进程测量：集合计算及内存查询后 CPU=0.015625秒，wall=0.018610秒，PeakWorkingSetSize=30,822,400字节；远低于30秒/1GB限制。该测量点在JSON序列化写出之前。命令为 `python metadata_independent_review.py`，退出码0。

结论仅为：该指定派生文件中，三个固定精确键存在733个共同登记的细胞ID，足以独立核对这一存在性证据。没有读取或认证原ZIP、原well、原始响应；不认证真实孔数、培养/生物独立重复、共同time/endpoint/control、功能关系、药效或新算法。0网络、响应读取、训练、安装、原输入复算、外部模型、派生代理和核心修改；既有独立挑战原稿未改。
