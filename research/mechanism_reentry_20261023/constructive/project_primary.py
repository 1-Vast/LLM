"""Project exact primary Methods sections and availability, without assay payloads."""
import json
from pathlib import Path
import xml.etree.ElementTree as ET

p=Path('D:/MAESTRO/log/20261023/mechanism_reentry/constructive')
wanted={
 'artemis':{'2.3 Modeling latent time-series with Schrödinger bridges','2.4 Joint optimization of VAE and Schrödinger bridges for smooth time-series dynamics in latent space','2.6 Datasets and preprocessing','Data availability'},
 'scbalflow':{'2.1.1 Training data','2.1.4 Imbalance training','2.2.1 Training data','2.2.3 Flow matching model','2.2.4 Datasets and preprocessing','Data availability'},
}
for name,titles in wanted.items():
    root=ET.parse(p/(name+'.body')).getroot()
    rows=[{'title':s.findtext('title',''),'text':' '.join(''.join(s.itertext()).split())}
          for s in root.findall('.//sec') if s.findtext('title','') in titles]
    (p/(name+'.exact_methods.json')).write_text(json.dumps(rows,indent=2,ensure_ascii=False),encoding='utf-8')
    print(name,len(rows))
