"""Export exact author concentration strings and verify joins to known drug keys."""
from discover import OUT
import json
import re
from pypdf import PdfReader

if __name__=='__main__':
    reader=PdfReader(OUT/'cipa_supplement_tables.pdf')
    text=reader.pages[2].extract_text()
    table=text[:text.index('Supplemental Table 3')]
    rows=[]
    pattern=re.compile(r'^(.+?)\s+([0-9.]+)\s+([0-9.]+)\s+([0-9.]+)\s+([0-9.]+)\s+([0-9.]+)\s+((?:1/2 )?log)\s*$')
    for line in table.splitlines():
        match=pattern.match(line.strip())
        if match:
            name,cmax,*rest=match.groups()
            doses=rest[:4]
            rows.append({'drug':name,'cmax_uM_string':cmax,'dose_code_to_uM_string':dict(zip(('1','2','3','4'),doses)),'interval':rest[4]})
    original=json.loads((OUT/'CIPA_IDENTITY_AUDIT.json').read_text(encoding='utf-8'))
    names=set(original['drug_counts']); names.remove('D,l,Sotalol')
    assert len(rows)==28 and {r['drug'] for r in rows}==names
    result={'source':'Supplemental Table 2, PDF page3','visual_render':'cipa_concentrations_page3.png','rows':rows,'checks':{'all_28_workbook_drugs_join':True,'all_112_drug_dose_codes_mapped':True,'sotalol_source_punctuation':'D,l Sotalol'},'physical_concentrations_are_nominal_not_measured_free_well_exposure':True,'numeric_assay_casts':0,'metadata_numeric_strings_exported':True,'published_outcome_exposure':'Table3 same page visually visible; full mixed supplement text extracted and treated designer-exposed.'}
    with (OUT/'CIPA_PHYSICAL_DOSE_MAPPING.json').open('x',encoding='utf-8') as f:
        json.dump(result,f,indent=2)
    print(json.dumps({'mapped_drugs':len(rows),'mapped_drug_codes':len(rows)*4,'checks':result['checks'],'examples':[r for r in rows if r['drug'] in ('Dofetilide','Ibutilide','Loratadine')]}))
