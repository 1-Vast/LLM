import subprocess,sys,urllib.parse,json
from pathlib import Path
base=Path(__file__).parent
queries=['active experiment selection task relevant world models robot','decision focused active learning representations','adaptive testing language models identify knowledge gaps']
for i,q in enumerate(queries,1):
 url='https://api.crossref.org/works?'+urllib.parse.urlencode({'query':q,'filter':'from-pub-date:2025-01-01,until-pub-date:2026-10-30','rows':8,'select':'title,DOI,published,URL,abstract'})
 label=f'q{i:02d}'
 try:subprocess.run([sys.executable,str(base/'fetch_once.py'),url,label],timeout=25,check=False)
 except subprocess.TimeoutExpired:
  with (base/'requests.jsonl').open('a',encoding='utf-8') as f:f.write(json.dumps({'label':label,'url':url,'error':'hard25s timeout','bytes':'unknown'})+'\n')
 try:
  x=json.loads((base/(label+'.body')).read_text(encoding='utf-8'))
  print('QUERY',q)
  for y in x['message']['items']:print(y.get('title'),y.get('DOI'))
 except Exception as e:print(type(e).__name__)
