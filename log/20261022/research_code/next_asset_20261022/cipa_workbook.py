"""Acquire released worksheet; inspect identities, strings and OOXML counts only."""
from cipa_assets import get
from discover import OUT
import io
import json
import zipfile
import xml.etree.ElementTree as ET

NS={'s':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
if __name__=='__main__':
    response=get('cipa_blinova_workbook','https://cipaproject.org/wp-content/uploads/2018/09/Blinova_etal_2018_data.xlsx')
    response.raise_for_status()
    with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
        shared=[]
        if 'xl/sharedStrings.xml' in archive.namelist():
            root=ET.fromstring(archive.read('xl/sharedStrings.xml'))
            shared=[''.join(n.itertext()) for n in root.findall('s:si',NS)]
        workbook=ET.fromstring(archive.read('xl/workbook.xml'))
        sheets=[n.attrib for n in workbook.findall('s:sheets/s:sheet',NS)]
        summary={'sheets':sheets,'strings':shared,'worksheets':[],'assay_scalar_casts':0}
        for name in archive.namelist():
            if name.startswith('xl/worksheets/sheet') and name.endswith('.xml'):
                root=ET.fromstring(archive.read(name))
                numeric=sum(1 for n in root.findall('.//s:c',NS) if n.get('t') not in ('s','inlineStr','str') and n.find('s:v',NS) is not None)
                string_cells=[]
                for cell in root.findall('.//s:c',NS):
                    value=cell.find('s:v',NS)
                    if cell.get('t')=='s' and value is not None:
                        string_cells.append({'cell':cell.get('r'),'text':shared[int(value.text)]})
                summary['worksheets'].append({'path':name,'dimension':root.find('s:dimension',NS).get('ref'),'numeric_cell_tags':numeric,'string_cells':string_cells})
    (OUT/'CIPA_WORKBOOK_SCHEMA.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    print(json.dumps({'sheets':sheets,'strings':shared[:100],'worksheets':[{k:v for k,v in sheet.items() if k!='string_cells'} for sheet in summary['worksheets']]}))
