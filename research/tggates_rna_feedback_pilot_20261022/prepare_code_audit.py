"""Bind actual implementation sources to one independent API audit request."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];C=Path(__file__).resolve().parent
P=ROOT/'log/20261022/tggates_rna_feedback_pilot';d=P/'api_reviews/implementation_skeptic'
d.mkdir(exist_ok=True)
prompt='你是实施审查者。下面是首次数值模型执行前的实际代码，而非方案。找出真实bug、泄漏、违反冻结合同、计数错误或缺失关键对照；不要提出扩数据/改门槛/新架构。源24、dev7且High在模型输入中全NaN、later未开。真实CEL已开始独立单阵列转换，但未聚合建模。普通受限联合预测不是新核心。请优先给出可复现问题与最小修正，明确严重度；没发现就说没有。特别审查RR、g derivative、nested owner bank、weighted refit完整重算source残差、devHigh隔离、64配置4336fits预算、source选择偏差、输入聚合数据身份和null关联诊断。下列三项现在定死：四基因共享同一basebank的alpha和同一内外折；weighted deploymentMiddle refit发生在prediction seal之前且无High；null只复用basebank不再拟合base。rho0保留零列与两block尺度；weighted原transform均值/RMS不变但WLS内部居中和截距重算。失败首CEL只有QC accessor修复，旧code/receipt保留。\n'
prompt+='\n数值协议修订：\n'+(P/'NUMERICAL_AMENDMENTS.md').read_text(encoding='utf-8')
paths=[C/name for name in ['linear_models.py','pilot_core.py','prepare_numeric_inputs.py','run_pilot.py','score_pilot.py','test_pilot_core.py','test_linear_models.py']]
hashes={}
for path in paths:
    hashes[path.relative_to(ROOT).as_posix()]=hashlib.sha256(path.read_bytes()).hexdigest()
    prompt+='\n\n--- '+path.name+' ---\n'+path.read_text(encoding='utf-8')
with (d/'INPUT_HASHES.json').open('x') as f:json.dump(hashes,f,indent=2)
with (d/'PROMPT.md').open('x',encoding='utf-8') as f:f.write(prompt)
