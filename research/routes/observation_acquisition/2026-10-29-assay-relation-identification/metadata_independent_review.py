"""Check only three fixed metadata keys; no menu search or response analysis."""
import ctypes
import hashlib
import json
import time
from ctypes import wintypes
from decimal import Decimal
from pathlib import Path

started_cpu = time.process_time()
started_wall = time.perf_counter()
source = Path(r'D:\MAESTRO\research\2026-10-29-edit-support-audit\primary_metadata.json')
expected_sha256 = 'd426f1c3fcbe23034235754d8cd418934a2eac150f82d0ffb7cea9e653559611'
raw = source.read_bytes()
actual_sha256 = hashlib.sha256(raw).hexdigest()
assert actual_sha256 == expected_sha256
records = json.loads(raw.decode('utf-8-sig'))
fixed = {'2428': Decimal('0.00100053'),
         '2429': Decimal('0.00100053'),
         '2430': Decimal('0.01000527')}
cells = {drug: set() for drug in fixed}
selected_records = {drug: 0 for drug in fixed}
matched_records = {drug: 0 for drug in fixed}
assert isinstance(records, list)
for record in records:
    assert set(record) == {'project', 'cell', 'drug_id', 'ref', 'doses_uM'}
    if record['project'] != '2' or record['drug_id'] not in fixed:
        continue
    drug = record['drug_id']
    assert isinstance(record['cell'], str)
    selected_records[drug] += 1
    doses = [Decimal(value) for value in record['doses_uM']]
    if any(dose.is_finite() and dose > 0 and dose == fixed[drug] for dose in doses):
        matched_records[drug] += 1
        cells[drug].add(record['cell'])
common = set.intersection(*cells.values())

class MemoryCounters(ctypes.Structure):
    _fields_ = [('cb', wintypes.DWORD), ('PageFaultCount', wintypes.DWORD)] + [
        (name, ctypes.c_size_t) for name in (
            'PeakWorkingSetSize', 'WorkingSetSize', 'QuotaPeakPagedPoolUsage',
            'QuotaPagedPoolUsage', 'QuotaPeakNonPagedPoolUsage',
            'QuotaNonPagedPoolUsage', 'PagefileUsage', 'PeakPagefileUsage')]

kernel = ctypes.WinDLL('kernel32', use_last_error=True)
kernel.GetCurrentProcess.restype = wintypes.HANDLE
psapi = ctypes.WinDLL('psapi', use_last_error=True)
psapi.GetProcessMemoryInfo.argtypes = [wintypes.HANDLE,
                                      ctypes.POINTER(MemoryCounters), wintypes.DWORD]
counters = MemoryCounters()
counters.cb = ctypes.sizeof(counters)
assert psapi.GetProcessMemoryInfo(kernel.GetCurrentProcess(), ctypes.byref(counters), counters.cb)
result = {
    'input_path': str(source), 'input_sha256': actual_sha256,
    'input_bytes': len(raw), 'input_record_count': len(records),
    'project': '2', 'drug_results': {
        drug: {'dose_uM': str(fixed[drug]),
               'project_drug_record_count': selected_records[drug],
               'matching_record_count': matched_records[drug],
               'distinct_MASTER_CELL_ID_count': len(cells[drug]),
               'MASTER_CELL_IDs': sorted(cells[drug])}
        for drug in fixed},
    'intersection_distinct_MASTER_CELL_ID_count': len(common),
    'intersection_MASTER_CELL_IDs': sorted(common),
    'cpu_seconds': time.process_time() - started_cpu,
    'wall_seconds': time.perf_counter() - started_wall,
    'peak_working_set_bytes': counters.PeakWorkingSetSize,
    'scope': 'Three prespecified exact positive finite Decimal dose keys only; '
             'derived metadata existence check, no global enumeration or raw-source certification.'}
assert result['cpu_seconds'] < 30
assert result['peak_working_set_bytes'] < 1024 ** 3
output = Path(__file__).with_suffix('.json')
output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({key: value for key, value in result.items()
                  if key not in {'drug_results', 'intersection_MASTER_CELL_IDs'}}, ensure_ascii=False))
for drug, item in result['drug_results'].items():
    print(json.dumps({'drug_id': drug, **{key: value for key, value in item.items()
                                        if key != 'MASTER_CELL_IDs'}}, ensure_ascii=False))
