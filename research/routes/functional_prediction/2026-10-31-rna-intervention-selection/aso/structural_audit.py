"""Outcome-blind structural admission audit; downloaded code is never executed."""
import json,re,itertools,collections
from pathlib import Path
import pandas as pd
import pyarrow.parquet as pq
import pyarrow.compute as pc
HERE=Path(__file__).resolve().parent
raw=HERE/'sources'
release=raw/'hf_in_vitro.parquet.hop1'
cols=[n for n in pq.ParquetFile(release).schema_arrow.names if n!='Inhibition_pct']
d=pq.read_table(release,columns=cols).to_pandas()
# Only validity is accessed. No effect values are converted, logged or analysed.
d['measured']=pc.is_valid(pq.read_table(release,columns=['Inhibition_pct'])['Inhibition_pct']).to_numpy()
gcols=['USPTO ID','Table Number','Compound ID','HELM Annotation','target_RNA']
gextra=['canonical_transcript_id','aso_transcript_matches','aso_match_count','ensembl_gene_id','mapping_source']
g=pq.read_table(raw/'in_vitro_genomic.parquet',columns=gcols+gextra).to_pandas()
g=g.drop_duplicates(gcols+gextra)
ambiguous=int(g.duplicated(gcols,keep=False).sum())
g=g.drop_duplicates(gcols,keep=False)
d=d.merge(g,on=gcols,how='left',validate='many_to_one',indicator=True)
def parse(h):
 if not isinstance(h,str):return None
 m=re.fullmatch(r'RNA1\{\{(.+)\}\}\$\$\$\$',h)
 if not m:return None
 ts=m[1].split('.')
 parts=[re.fullmatch(r'([^()]*)\(([^()]*)\)([^()]*)',t) for t in ts]
 if not all(parts):return None
 return tuple((x[1],x[2],x[3]) for x in parts)
def region(row):
 if pd.isna(row['canonical_transcript_id']) or pd.isna(row['aso_transcript_matches']):return None
 try:a=json.loads(row['aso_transcript_matches'])
 except (ValueError,TypeError):return None
 if len(a)!=1:return None
 return (row['canonical_transcript_id'],int(a[0]['start']),int(a[0]['end']))
d['tokens']=d['HELM Annotation'].map(parse)
d['region']=[region(r) for _,r in d.iterrows()]
context=['USPTO ID','Table Number','target_RNA','cell_line','cell_line_species','dosage_nm','treatment_period_hrs','transfection_method','cells_per_well']
strict=d[d['measured'] & d['tokens'].notna() & d['region'].notna() & d[context].notna().all(axis=1)].copy()
# All pair counts are unique chemistry structures within an exact source/table/context.
strict=strict.drop_duplicates(context+['HELM Annotation','region'])
counts=collections.Counter(); sources=collections.defaultdict(set); genes=collections.defaultdict(set)
chemistry_pairs=[];tiling_pairs=[]
for key,group in strict.groupby(context,dropna=False,sort=False):
 records=group.to_dict('records')
 # Same canonical transcript and exact site, identical bases, exactly one monomer token edited.
 for site,rs in itertools.groupby(sorted(records,key=lambda r:r['region']),key=lambda r:r['region']):
  rs=list(rs)
  for a,b in itertools.combinations(rs,2):
   ta,tb=a['tokens'],b['tokens']
   if len(ta)!=len(tb):continue
   diffs=[i for i,(x,y) in enumerate(zip(ta,tb)) if x!=y]
   if len(diffs)==1 and all(x[1]==y[1] for x,y in zip(ta,tb)):
    chemistry_pairs.append((a['USPTO ID'],a['Table Number'],a['target_RNA'],a['Compound ID'],b['Compound ID'],diffs[0]))
    counts['single_token_chemistry_pairs']+=1;sources['chemistry'].add(key[0]);genes['chemistry'].add(key[2])
 # Same length/sugar/backbone pattern, interval shift of exactly one base; not a base-substitution experiment.
 buckets=collections.defaultdict(list)
 for r in records:
  t=r['tokens'];reg=r['region']
  buckets[(reg[0],len(t),tuple((x[0],x[2]) for x in t))].append(r)
 for rs in buckets.values():
  starts=collections.defaultdict(list)
  for r in rs:starts[r['region'][1]].append(r)
  for start,aa in starts.items():
   for a in aa:
    for b in starts.get(start+1,[]):
     if b['region'][2]-a['region'][2]!=1:continue
     tiling_pairs.append((a['USPTO ID'],a['Table Number'],a['target_RNA'],a['Compound ID'],b['Compound ID']))
     counts['one_base_tiling_pairs']+=1;sources['tiling'].add(key[0]);genes['tiling'].add(key[2])
report={'release_rows':len(d),'release_patents':d['USPTO ID'].nunique(),'release_targets':d.target_RNA.nunique(),'non_null':{c:int(d[c].notna().sum()) for c in cols},'measured_rows':int(d.measured.sum()),'genomic_source_rows':pq.ParquetFile(raw/'in_vitro_genomic.parquet').metadata.num_rows,'ambiguous_genomic_join_rows':ambiguous,'joined_release_rows':int((d['_merge']=='both').sum()),'unique_transcript_region_rows':int(d.region.notna().sum()),'parsed_helm_rows':int(d.tokens.notna().sum()),'strict_complete_rows_after_structure_dedup':len(strict),'strict_patents':strict['USPTO ID'].nunique(),'strict_targets':strict.target_RNA.nunique(),'pair_counts':dict(counts),'pair_patents':{k:len(v) for k,v in sources.items()},'pair_targets':{k:len(v) for k,v in genes.items()},'verified_legal_patent_family_count':None,'verified_protocol_equivalence_class_count':None,'verified_controlled_base_substitution_pairs':0}
(HERE/'audit_counts.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
pd.DataFrame(chemistry_pairs,columns=['patent','table','target','compound_a','compound_b','edited_token_zero_based']).to_csv(HERE/'chemistry_candidate_pairs.csv',index=False)
pd.DataFrame(tiling_pairs,columns=['patent','table','target','compound_a','compound_b']).to_csv(HERE/'tiling_candidate_pairs.csv',index=False)
print(json.dumps(report,indent=2))
