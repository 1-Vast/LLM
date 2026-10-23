from pathlib import Path
import hashlib,json,datetime,subprocess
root=Path('D:/MAESTRO');out=root/'log/20261022/native_operation/biology'
inputs=[Path('C:/Users/59964/.codex/attachments/45d9c2f9-b12a-4e71-bd4a-9f6cc5eb5ce9/goal-objective.md'),root/'research/REPORT.md',root/'log/20261022/mse_source_gate/DECISION.md',root/'log/20261022/mse_source_gate/CONTINUATION.md',root/'log/20261022/cipa_control_information/PROJECT_CAPABILITY_AUDIT.md']
def item(p):return {'path':str(p),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
p=out/'INDEPENDENT_SEAL.json';assert not p.exists()
record={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'git_head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip(),'independent_before_peer_reads':True,'root_criteria_message_disclosed_in_position':True,'inputs':[item(p) for p in inputs],'artifacts':[item(p) for d in [out,root/'research/native_biological_20261022'] for p in sorted(d.iterdir()) if p.is_file()]}
p.write_text(json.dumps(record,indent=2),encoding='utf8')
print(json.dumps({'seal':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'artifacts':len(record['artifacts'])},indent=2))
