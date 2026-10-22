"""Audit finite intervention menu using identities and exposure decimals only."""
from discover import OUT
from cipa_workbook import NS
from decimal import Decimal
import collections
import json
import zipfile
import xml.etree.ElementTree as ET

if __name__=='__main__':
    with zipfile.ZipFile(OUT/'cipa_blinova_workbook.body') as archive:
        shared=[''.join(n.itertext()) for n in ET.fromstring(archive.read('xl/sharedStrings.xml')).findall('s:si',NS)]
        root=ET.fromstring(archive.read('xl/worksheets/sheet1.xml'))
    units=collections.Counter()
    aliases=[]
    for row in root.findall('s:sheetData/s:row',NS):
        vals={}
        for cell in row.findall('s:c',NS):
            value=cell.find('s:v',NS)
            col=''.join(x for x in cell.get('r') if x.isalpha())
            if value is not None and col in ('A','B','D','F','I'):
                vals[col]=shared[int(value.text)] if cell.get('t')=='s' else value.text
        if vals.get('A') in (None,'Drug_Name'):
            continue
        name=vals['A']
        if name=='D,l,Sotalol':
            aliases.append({'row':row.get('r'),'original':name,'provisional_alias':'D,l Sotalol','metadata':vals})
            name='D,l Sotalol'
        key=(name,vals.get('B'),vals.get('D'),vals.get('I'),str(Decimal(vals['F']).normalize()))
        units[key]+=1
    menus=collections.defaultdict(set)
    for name,cell,platform,site,dose in units:
        menus[(name,cell,platform,site)].add(dose)
    summary={'provisional_alias_rule_only':'D,l,Sotalol -> D,l Sotalol, consistent with single named D,L-sotalol drug in author text; source alias remains unmodified','aliases':aliases,'canonical_drugs':len({k[0] for k in units}),'canonical_units':len(units),'drug_context_pairs':len(menus),'dose_count_distribution':dict(collections.Counter(len(v) for v in menus.values())),'non_four_dose_menus':[{'drug':k[0],'cell':k[1],'platform':k[2],'site':k[3],'doses':sorted(v)} for k,v in menus.items() if len(v)!=4],'numeric_assay_casts':0,'numeric_exposure_decimal_conversions':'conc only','source_design_exception':'Author text says site 10 used sequential additions, other sites one concentration per well; initial same-history comparison must account for or omit site10.'}
    (OUT/'CIPA_DESIGN_AUDIT.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    print(json.dumps(summary))
