"""Source-only follow-up permitted by SOURCE_QUALIFICATION_PROTOCOL.md."""
import json
from concurrent.futures import ThreadPoolExecutor
from fetch_primary import fetch
SOURCES={
 'caf_oa_locator':'https://www.ncbi.nlm.nih.gov/pmc/utils/oa/oa.fcgi?id=PMC13680625',
 'caf_supplement_methods':'https://static-content.springer-cdn.com/esm/art%3A10.1038%2Fs41392-026-02965-1/MediaObjects/41392_2026_2965_MOESM1_ESM.docx',
 'caf_supplement_sample_information':'https://static-content.springer-cdn.com/esm/art%3A10.1038%2Fs41392-026-02965-1/MediaObjects/41392_2026_2965_MOESM2_ESM.xlsx',
 'caf_hra011931_landing':'https://ngdc.cncb.ac.cn/gsa-human/browse/HRA011931',
 'caf_hra008021_landing':'https://ngdc.cncb.ac.cn/gsa-human/browse/HRA008021'}
if __name__=='__main__':
    with ThreadPoolExecutor(max_workers=5) as pool:
        for result in pool.map(fetch,SOURCES.items()):print(json.dumps(result),flush=True)
