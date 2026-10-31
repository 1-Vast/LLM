"""Preserve v1 and make only the identified pre-execution corrections."""
from pathlib import Path

EP = Path(__file__).resolve().parent.parent


def replace(text,old,new):
    assert text.count(old)==1,old
    return text.replace(old,new)


code = (EP/'experiment.py').read_text(encoding='utf-8')
code = code.replace("EP/'protocol_v1.md'","EP/'protocol_v2.md'")
code = replace(code,'profile = np.mean((qgrid[0][:,val,:]-source_y[:,val][...,None])**2,axis=(0,1))',
    'culture_profiles = np.mean((qgrid[0][:,val,:]-source_y[:,val][...,None])**2,axis=1)\n            profile = culture_profiles.mean(axis=0)')
code = replace(code,'lambda_compatible=GRID[compatible].tolist(),source_mean=source_mean)',
    'lambda_compatible=GRID[compatible].tolist(),source_mean=source_mean,\n                            lambda_culture_validation_profiles=culture_profiles.tolist())')
code = replace(code,"'predicted_outside_range_fraction':float(np.mean((v<lo)|(v>hi))),",
    "'predicted_outside_range_fraction':float(np.mean((v<lo)|(v>hi))),\n                    'allowed_input_histogram':np.histogram(np.r_[ys[r,0][active],ys[r,0][single_mask],ys[r,condition+1][single_mask]],bins=bins)[0].tolist(),\n                    'allowed_input_outside_range_fraction':float(np.mean((np.r_[ys[r,0][active],ys[r,0][single_mask],ys[r,condition+1][single_mask]]<lo)|(np.r_[ys[r,0][active],ys[r,0][single_mask],ys[r,condition+1][single_mask]]>hi))),")
code = replace(code,"signal = float(np.mean(y**2)) > glucose['culture_disagreement']",
    "result['target_pair_variation'] = float(np.var(y,axis=1).mean())\n    signal = result['target_pair_variation'] > glucose['culture_disagreement']")
protocol = (EP/'protocol_v1.md').read_text(encoding='utf-8').replace('I054.v1 numerical protocol','I054.v1 numerical protocol v2')
protocol = protocol.replace('If target variation is no larger than the culture-disagreement diagnostic,',
    'Target variation is the mean across cultures of the centered variance of Q across held pairs. If it is no larger than the culture-disagreement diagnostic,')
protocol = protocol.replace('Report fraction of test pairs with >=half of retained UT/target double counts <10 as a count-floor diagnostic',
    'Report fraction of test pairs where >=half of retained constructs have either their UT count OR their target count <10 as a count-floor diagnostic')
protocol = protocol.replace('at most4 CPU threads and1800s hard subprocess timeout',
    'at most4 logical CPUs via inherited Windows process affinity,4threads per computational pool, and1800s hard subprocess timeout')
protocol += '\nV2 is a pre-execution reconciliation after the actual independent v1 code review. It preserves v1 files/freeze, implements the originally intended centered-variation gate, adds promised culture-specific lambda profiles and allowed-input occupancy, specifies the count-floor diagnostic exactly, and enforces the CPU ceiling. The scientific candidate/family and all source-only model choices are unchanged. No biological response has yet been opened or model fitted. Current executable files are experiment_v2.py, launcher_v2.py and check_arithmetic_v2.py.\n'
launcher = (EP/'launcher.py').read_text(encoding='utf-8')
launcher = launcher.replace('numeric_freeze_v1.json','numeric_freeze_v2.json').replace("EP/'experiment.py'","EP/'experiment_v2.py'")
launcher = replace(launcher,"started = time.monotonic()",'''# Constrain this launcher and inherited children to four available logical CPUs.
import ctypes
from ctypes import wintypes
kernel = ctypes.WinDLL('kernel32',use_last_error=True)
kernel.GetCurrentProcess.restype = wintypes.HANDLE
kernel.GetProcessAffinityMask.argtypes = [wintypes.HANDLE,ctypes.POINTER(ctypes.c_size_t),ctypes.POINTER(ctypes.c_size_t)]
kernel.SetProcessAffinityMask.argtypes = [wintypes.HANDLE,ctypes.c_size_t]
handle = kernel.GetCurrentProcess()
available,system = ctypes.c_size_t(),ctypes.c_size_t()
assert kernel.GetProcessAffinityMask(handle,ctypes.byref(available),ctypes.byref(system))
bits = [1<<i for i in range(8*ctypes.sizeof(ctypes.c_size_t)) if available.value & (1<<i)]
chosen = sum(bits[:4])
assert kernel.SetProcessAffinityMask(handle,chosen)
started = time.monotonic()''')
launcher = replace(launcher,"'threads':4,'stages':[]}","'threads_per_pool':4,'logical_cpu_affinity_mask':chosen,'stages':[]}")
check = (EP/'check_arithmetic.py').read_text(encoding='utf-8').replace('import experiment as e','import experiment_v2 as e')
freeze = (EP/'review/freeze_numeric.py').read_text(encoding='utf-8').replace('numeric_freeze_v1.json','numeric_freeze_v2.json')
freeze = freeze.replace("'protocol_v1.md','experiment.py','launcher.py','check_arithmetic.py'",
    "'protocol_v2.md','experiment_v2.py','launcher_v2.py','check_arithmetic_v2.py'")
for name,text in [('experiment_v2.py',code),('protocol_v2.md',protocol),('launcher_v2.py',launcher),
                  ('check_arithmetic_v2.py',check),('review/freeze_numeric_v2.py',freeze)]:
    path = EP/name
    assert not path.exists(),path
    path.write_text(text,encoding='utf-8')
print('Preserved all v1 bytes; five v2 files prepared before any numerical access.')
