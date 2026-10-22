# Explicit official version identity followup

2026-10-22。原4GET区块已先完成REPORT/STATUS，不改原预算。Root在收到官方302后明确另授权 **1GET、response≤3,000,000bytes** 至唯一Location `https://zenodo.org/api/records/14064964`。这是显式版本身份读取，不使用自动redirect或retry；若再redirect/失败/超cap立即保留并停止。

只metadata：title、DOI、version/concept关系、文件名/size/checksum/links、availability description作为published/source-design文字。不得读取responsefiles、工作簿、zip、codefiles或FASTQ。完整原metadata/receipt只存本日志目录，研究代码只research/dynamic_source_followup_20261022/，maestro -B。目标是真实file manifest，未知state modality仍写phenotype，不导向novelty-positive。
