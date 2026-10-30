import io,json,zipfile,openpyxl
from collections import Counter,defaultdict
from pathlib import Path
p=Path(r'research/2026-10-27-oneil-transfer-qualification');z=zipfile.ZipFile(p/'combocat_dense_supp_data1.zip');w=openpyxl.load_workbook(io.BytesIO(z.read(z.namelist()[0])),read_only=True,data_only=True);it=w['data'].iter_rows(values_only=True);head=next(it);ix={x:i for i,x in enumerate(head)};roots=defaultdict(set);d1=Counter();d2=Counter();plate=Counter();n=0
for row in it:
 n+=1;root=row[ix['root_id']];roots[str(root)].add(str(row[ix['replicate']]));d1[str(row[ix['drug1_name']])]+=1;d2[str(row[ix['drug2_name']])]+=1;plate['nonempty' if row[ix['Plate Barcode']] not in (None,'','NA') else 'empty']+=1
out={'rows':n,'root_ids':len(roots),'replicates_per_root':dict(Counter(len(x) for x in roots.values())),'drug1_names':dict(d1),'drug2_names':dict(d2),'plate_barcode':dict(plate),'root_samples':list(roots)[:12],'limits':'metadata only; same-plate technical replicates per glossary; root-id parsing not validated'}
(p/'combocat_metadata.json').write_text(json.dumps(out,indent=2),encoding='utf8');print(json.dumps(out,indent=2));w.close();z.close()
