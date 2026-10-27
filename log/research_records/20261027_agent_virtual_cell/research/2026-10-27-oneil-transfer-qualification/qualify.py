import hashlib,json,unicodedata
from pathlib import Path
from collections import defaultdict,Counter
import pandas as pd,openpyxl
ROOT=Path(r'D:\MAESTRO');OUT=ROOT/'research/2026-10-27-oneil-transfer-qualification';G=ROOT/'data/external/gdsc_combinations/jaaks2022_figshare/Original screen_All tissues_fitted data.csv';O=ROOT/'data/raw/oneil2026_qualification/15357163mct150843-sup-156849_1_supp_1_w2lrww.xls'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for c in iter(lambda:f.read(1048576),b''):h.update(c)
 return h.hexdigest()
def key(x):return ''.join(c for c in unicodedata.normalize('NFKC',str(x)).casefold() if c.isalnum())
def main():
 d=pd.read_csv(G,usecols=['CELL_LINE_NAME','ANCHOR_NAME','LIBRARY_NAME'],low_memory=False).dropna();gs={(str(c).strip(),str(a).strip(),str(b).strip()) for c,a,b in d.itertuples(index=False,name=None)};os=set();counts=Counter()
 with O.open('rb') as f:
  wb=openpyxl.load_workbook(f,read_only=True,data_only=True);rows=wb.worksheets[0].iter_rows(values_only=True);head=next(rows);ix={str(x):i for i,x in enumerate(head)}
  for r in rows:
   c,a,b,batch=(r[ix[k]] for k in ('cell_line','drugA_name','drugB_name','BatchID'))
   if None in (c,a,b,batch):continue
   counts[str(batch)]+=1;os.add((str(c).strip(),str(a).strip(),str(b).strip(),str(batch)))
  wb.close()
 aliases={'drug':defaultdict(set),'cell':defaultdict(set)}
 for c,a,b in gs:
  aliases['cell'][key(c)].add(c);aliases['drug'][key(a)].add(a);aliases['drug'][key(b)].add(b)
 for c,a,b,_ in os:
  aliases['cell'][key(c)].add(c);aliases['drug'][key(a)].add(a);aliases['drug'][key(b)].add(b)
 amb={t:{k:sorted(v) for k,v in m.items() if len({s.casefold() for s in v})>1} for t,m in aliases.items()}
 def convert(c,a,b):
  c,a,b=key(c),key(a),key(b)
  return None if c in amb['cell'] or a in amb['drug'] or b in amb['drug'] else (c,tuple(sorted((a,b))))
 g={t for c,a,b in gs if (t:=convert(c,a,b))};o={t for c,a,b,_ in os if (t:=convert(c,a,b))}
 gc={x[0] for x in g};oc={x[0] for x in o};gp={x[1] for x in g};op={x[1] for x in o};gd={n for a,b in gp for n in (a,b)};od={n for a,b in op for n in (a,b)}
 overlap={'cells':sorted(gc&oc),'drugs':sorted(gd&od),'pairs':[list(p) for p in sorted(gp&op)],'cell_pair':[[c,*p] for c,p in sorted(g&o)]}
 out={'source_sha256':{'jaaks':sha(G),'oneil':sha(O)},'protocol_sha256':sha(OUT/'PROTOCOL.md'),'script_sha256':sha(Path(__file__)),'raw_unique_records':{'jaaks_cell_directed_pair':len(gs),'oneil_cell_directed_pair_batch':len(os),'oneil_batch_rows':dict(counts)},'counts':{'jaaks':{'cells':len(gc),'drugs':len(gd),'pairs':len(gp),'cell_pairs':len(g)},'oneil':{'cells':len(oc),'drugs':len(od),'pairs':len(op),'cell_pairs':len(o)},'intersection':{k:len(v) for k,v in overlap.items()}},'normalization_collisions':amb,'limits':['conservative name normalization; cross-source aliases unresolved','overlap with complete Jaaks table, not a particular training split','raw cell-pair sets, not target comparability or independent cultures']}
 (OUT/'counts.json').write_text(json.dumps(out,indent=2,ensure_ascii=False),encoding='utf8');(OUT/'overlap.json').write_text(json.dumps(overlap,indent=2,ensure_ascii=False),encoding='utf8');print(json.dumps(out,indent=2,ensure_ascii=False),flush=True)
if __name__=='__main__':main()
