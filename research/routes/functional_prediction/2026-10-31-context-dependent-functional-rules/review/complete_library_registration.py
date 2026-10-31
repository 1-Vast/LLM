"""Resume code metadata through supported owner fields; no downloads or code execution."""
from pathlib import Path

EP = Path(__file__).resolve().parent.parent
source = (EP/'review/register_library_resume.py').read_text(encoding='utf-8')
head = source[:source.index("pid = 'arxiv-2205.09162'")]
loop = source[source.index('for rid,pid,directory,archive in specifications:'):]
loop = loop.replace("    run('code',LIB,rid,'--existing',directory,'--paper',pid,'--relation','official','--evidence',evidence)",
                    "    if 'bottlenecks' not in rid:\n        run('code',LIB,rid,'--existing',directory,'--paper',pid,'--relation','official','--evidence',evidence)")
loop = loop.replace("fields += ['archive_sha256='+hashlib.sha256((EP/'root/sources'/archive).read_bytes()).hexdigest()]",
                    "fields[-1] += ' Original archive SHA256='+hashlib.sha256((EP/'root/sources'/archive).read_bytes()).hexdigest()")
text = head+"""area = EP/'root/code_slices'
specifications = [
 ('functional-bottlenecks-zenodo18131102','doi-10.1371-journal.pcbi.1014000',area/'functional-bottlenecks-zenodo18131102','bottleneck_Library.zip'),
 ('yeast-fitness-zenodo19827560','doi-10.1093-nargab-lqag084',area/'yeast-fitness-zenodo19827560','yeast_fitness_code.zip'),
 ('dspin-official-source-slice-20261031','doi-10.1016-j.cell.2026.04.028',area/'dspin-official-source-slice-20261031',None)]
tree = json.loads((EP/'root/sources/dspin_tree.json').read_text())
"""+loop
text = text.replace('library_registration_resume_receipts.jsonl','library_registration_completion_receipts.jsonl')
target = EP/'review/register_library_complete.py'
assert not target.exists()
target.write_text(text,encoding='utf-8')
print('Supported-field completion prepared; failed owner calls remain preserved.')
