import pathlib,csv,json,openpyxl,collections
b=pathlib.Path('research/routes/functional_prediction/2026-10-31-rna-context-intervention-laws/investigator')
with (b/'sources/promoter_425a.csv.hop1').open(encoding='utf-8-sig',newline='') as f:
 schema={'processed_csv_header':next(csv.reader(f))}
w=openpyxl.load_workbook(b/'sources/promoter_library.xlsx',read_only=True,data_only=False)
schema['library_sheets']={s.title:[list(next(s.iter_rows(values_only=True)))] for s in w.worksheets}
(b/'promoter_schema2.json').write_text(json.dumps(schema,indent=2,default=str),encoding='utf8'); print(json.dumps(schema,indent=2,default=str))
