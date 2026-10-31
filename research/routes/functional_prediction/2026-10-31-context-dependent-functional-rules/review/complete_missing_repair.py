"""Complete the same unlaunched repair after independent v4 inspection."""
from pathlib import Path

EP = Path(__file__).resolve().parent.parent
code = (EP/'experiment_v4.py').read_text(encoding='utf-8')
old = "return np.nan if text.strip()=='' else float(text)"
assert code.count(old)==1
code = code.replace(old,"if text.strip()=='':\n        return np.nan\n    value = float(text)\n    assert np.isfinite(value) and value>=0 and value.is_integer()\n    return value")
old = "selected.update(genes=len(genes)"
assert code.count(old)==1
code = code.replace(old,"""t0_pass = (c[:,0]>=30).all(0)
    ut_complete = t0_pass & np.isfinite(c[:,1]).all(0)
    selected['input_mask_counts'] = {'t0_only':int(t0_pass.sum()),'after_UT_complete':int(ut_complete.sum()),
        'after_common_paid_controls':int(mask.sum()),'UT_missing_removed':int((t0_pass&~ut_complete).sum()),
        'paid_control_missing_removed':int((ut_complete&~mask).sum())}
    selected['source_development_unobservable_by_culture'] = [int(((folds<=7)&~np.isfinite(source_labels[r])).sum()) for r in range(2)]
    selected.update(genes=len(genes)""")
code = code.replace('protocol_v4.md','protocol_v5.md')
protocol = (EP/'protocol_v4.md').read_text(encoding='utf-8')
protocol += '\nV5 completes this same unlaunched repair: only stripped-empty tokens may map to NaN; every nonempty token must parse as a finite nonnegative integer. Save T0-only, UT-availability and common paid-control mask counts/removals and source-development missing labels by culture. Current exact executables are experiment_v5.py/check_arithmetic_v5.py/launcher_v5.py; numeric_freeze_v5.json supersedes v4 before its launch. Remaining1794.406s and all scientific choices are unchanged.\n'
launcher = (EP/'launcher_v4.py').read_text(encoding='utf-8').replace('numeric_freeze_v4.json','numeric_freeze_v5.json').replace('experiment_v4.py','experiment_v5.py')
check = (EP/'check_arithmetic_v4.py').read_text(encoding='utf-8').replace('experiment_v4 as e','experiment_v5 as e')
check += "\nfor text in ['nan','inf','-1','0.5','NA']:\n    try:\n        e.count_value(text)\n    except (AssertionError,ValueError):\n        pass\n    else:\n        raise AssertionError('Nonempty invalid count accepted: '+text)\n"
freeze = (EP/'review/freeze_numeric_v4.py').read_text(encoding='utf-8').replace('numeric_freeze_v4.json','numeric_freeze_v5.json')
freeze = freeze.replace('protocol_v4.md','protocol_v5.md').replace('experiment_v4.py','experiment_v5.py').replace('check_arithmetic_v4.py','check_arithmetic_v5.py').replace('launcher_v4.py','launcher_v5.py')
for name,text in [('experiment_v5.py',code),('protocol_v5.md',protocol),('launcher_v5.py',launcher),
                  ('check_arithmetic_v5.py',check),('review/freeze_numeric_v5.py',freeze)]:
    target = EP/name
    assert not target.exists()
    target.write_text(text,encoding='utf-8')
print('Same repair completed before launch; v4 frozen bytes unchanged.')
