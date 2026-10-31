"""Remove the possible one-second timeout overrun; preserve v2 unchanged."""
from pathlib import Path

EP = Path(__file__).resolve().parent.parent
text = (EP/'launcher_v2.py').read_text(encoding='utf-8').replace('numeric_freeze_v2.json','numeric_freeze_v3.json')
old = "process = subprocess.run([sys.executable,'-X','utf8',str(EP/'experiment_v2.py'),stage],cwd=EP.parents[3],\n                env=environment,stdout=stdout,stderr=stderr,timeout=max(1,1800-(time.monotonic()-started)))"
new = "remaining = 1800-(time.monotonic()-started)\n            if remaining <= 0:\n                raise subprocess.TimeoutExpired(stage,1800)\n            process = subprocess.run([sys.executable,'-X','utf8',str(EP/'experiment_v2.py'),stage],cwd=EP.parents[3],\n                env=environment,stdout=stdout,stderr=stderr,timeout=remaining)"
assert text.count(old)==1
target = EP/'launcher_v3.py'
assert not target.exists()
target.write_text(text.replace(old,new),encoding='utf-8')
freeze = (EP/'review/freeze_numeric_v2.py').read_text(encoding='utf-8')
freeze = freeze.replace('numeric_freeze_v2.json','numeric_freeze_v3.json').replace("'launcher_v2.py'","'launcher_v3.py'")
target = EP/'review/freeze_numeric_v3.py'
assert not target.exists()
target.write_text(freeze,encoding='utf-8')
print('V3 changes only the launcher remaining-time calculation; experiment/protocol remain frozen v2.')
