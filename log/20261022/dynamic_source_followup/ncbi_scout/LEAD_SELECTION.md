# Primary lead selected before third GET

2 GET后，PubMed broad query183条，只阅读relevance默认前10条，不声称穷尽。十条包括colistin同研究的preprint/正式发表duplicate、clinical longitudinal单背景、无关metabolomics/production/sensor条目。2024 Weaver etal., PMID38607932, DOI10.1073/pnas.2303165121是经验fitness landscape上的模拟RL，不能当真实换药实验。

选择 **Maltas / Huynh / Wood, Dynamic collateral sensitivity profiles highlight opportunities and challenges for optimizing antibiotic treatments**, PMID39774800，PMC11709278，DOI10.1371/journal.pbio.3002970，2025 PLoS Biology。摘要明确E.faecalis实验进化、400strain–antibiotic combinations、4timepoints、真实timed drug switching；尚不知state是纯phenotype还是genome、具体evolution/task数、public matrix/代码与lineage/drug/time/switch/function join。`rg`未在现有log/research Markdown报告中找到该PMID/DOI/title，不据此声称从未被任何人看过。

第三GET仅NCBI PMC EFetch official fullXML；若成功只离线投影Methods/Data availability及明确repository/accession/补充文件manifest。作者published narrative/design可读但不冒充本项目证据；不解析response table arrays。第四GET只沿明确available source做identity metadata，或不用。不是新颖机制批准。

第三GET成功后，DataAvailability明确Zenodo10.5281/zenodo.14064963及S1Data工作簿。第四且最后GET固定`https://zenodo.org/api/records/14064963`，只读取registry title/DOI/description中的文件身份、file manifest/link/size/checksum与paper关系，不开文件内容。Methods认证5drugs/4replicates/day2/4/6/8与另14dayCRO/DOX研究，但不完整写switch配置；为核实“实际switch”线索，可从已保存XML补投影对应figure caption及明确实验设计叙述，全部design-exposed；不解析响应table/array。
