"""Count released treatment/condition identities without casting assay responses."""
from discover import OUT
import collections
import json
import zipfile
import xml.etree.ElementTree as ET
from cipa_workbook import NS

if __name__=='__main__':
    with zipfile.ZipFile(OUT/'cipa_blinova_workbook.body') as archive:
        shared=[''.join(n.itertext()) for n in ET.fromstring(archive.read('xl/sharedStrings.xml')).findall('s:si',NS)]
        root=ET.fromstring(archive.read('xl/worksheets/sheet1.xml'))
        rows=[]
        for row in root.findall('s:sheetData/s:row',NS):
            cells={}
            for cell in row.findall('s:c',NS):
                value=cell.find('s:v',NS)
                if value is None:
                    continue
                column=''.join(x for x in cell.get('r') if x.isalpha())
                if column in ('A','B','D','F','I'):
                    cells[column]=shared[int(value.text)] if cell.get('t')=='s' else value.text
            if cells.get('A') and cells['A']!='Drug_Name':
                rows.append(cells)
    drug_counts=collections.Counter(row.get('A') for row in rows)
    contexts=collections.Counter((row.get('B'),row.get('D'),row.get('I')) for row in rows)
    units=collections.Counter((row.get('A'),row.get('B'),row.get('D'),row.get('I'),row.get('F')) for row in rows)
    summary={'rows_with_drug_identity':len(rows),'drug_counts':dict(drug_counts),'context_counts':[{'cell_type':k[0],'platform':k[1],'site':k[2],'rows':v} for k,v in contexts.items()],'drug_context_dose_units':len(units),'unit_rowcount_histogram':dict(collections.Counter(units.values())),'drug_name_alias_candidate':['D,l,Sotalol','D,l Sotalol'],'treatment_dose_strings_exposed':True,'assay_scalar_casts':0,'notes':'Type_of_EADs string outcomes and risk labels are present in acquired file. Identity counting excludes columns C/E/G/H (risk/event-class/EAD/ddFPDc). No replicate IDs were authenticated; rows per unit are not automatically independent biological replicates.'}
    (OUT/'CIPA_IDENTITY_AUDIT.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    print(json.dumps(summary))
