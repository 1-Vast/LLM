"""Preserve the failed owner call; resume only after the two registered JATS files."""
from pathlib import Path

EP = Path(__file__).resolve().parent.parent
source = (EP/'review/register_library.py').read_text(encoding='utf-8')
start = source.index('new = [')
end = source.index("pid = 'arxiv-2205.09162'",start)
source = source[:start]+source[end:]
source = source.replace('library_registration_receipts.jsonl','library_registration_resume_receipts.jsonl')
source = source.replace('other_ids=EUSIPCO','alt_id=EUSIPCO')
target = EP/'review/register_library_resume.py'
assert not target.exists()
target.write_text(source,encoding='utf-8')
print('Resume retains partial registration and failed field-name receipt; uses owner alt_id column.')
