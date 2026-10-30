"""Delegate only new-source protocol transcription and fixed conversions."""
from pathlib import Path
import hashlib
import json
import xml.etree.ElementTree as ET

episode = Path(__file__).resolve().parent
aux = episode.parent / "deepseek"
task = aux / "tasks/DS037"
assert not task.exists(), "Never replace or replay a task"
(task / "workspace").mkdir(parents=True)
source = episode / "evidence/p03.body"
tree = ET.parse(source).getroot()
passages = {sid: " ".join("".join(tree.find('.//sec[@id="' + sid + '"]').itertext()).split())
            for sid in ["Sec27", "Sec29", "Sec44"]}
packet = {"source": str(source), "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
          "doi": "10.1038/s41467-026-75772-5", "passages": passages}
(task / "source_packet.json").write_text(json.dumps(packet, indent=2) + "\n", encoding="utf-8")
rules = """DS037: fixed supplied-passage transcription only. No hypothesis, method, metric or mechanism choice.
Return one JSON object, no extra prose. Do not infer live counts from CCK8 or borrow colony conditions for CCK8.
Use null for fields not stated in supplied passages; unknown means not stated here, not globally absent.
substrate: material(string), ratios_soft_to_stiff(list of literal strings), curing_temperature_c(number), curing_hours(number), curing_seconds(number), collagen_mg_ml(number).
cck8: drugs(list of literal drug names), wavelength_nm(number), plate_wells(integer), starting_cells(integer or null), exposure_hours(number or null).
colony: backgrounds(list), perturbation(string), starting_cells(integer), plate_wells(integer), gemcitabine_nm(number), ferr1_um(number), duration_days([lower,upper]), duration_seconds([lower,upper]), endpoint(string).
replication: minimum_repeats(integer), kind(string: explicit source kind or 'not specified'). Repeated at least N times does not certify biological versus technical repeats.
unknowns: list of supplied-passage missing field paths. task_id='DS037'.
Only prescribed conversions: hours*3600; days*86400. Keep physical curing time separate from drug exposure.
At each small-step boundary, new formal task first; otherwise continue supplied human-source units/readout/preparation fields; missing local fields do not stop others.
Budget: one tools-disabled call,180s,2048outputtokens,12000Bstdin,declaredUSD0.025; effective backend/cost/hard dollar cap unknown. No retry/backend change.
INPUT:
"""
prompt = (rules + json.dumps(packet, indent=2)).encode("utf-8")
assert len(prompt) <= 12000
(task / "prompt.txt").write_bytes(prompt)
job = {"task_id": "DS037", "task_version": "v1", "status": "assigned_ready_for_execution",
       "is_execution_authorization": True, "transport": "isolated_headless_stdin_no_tools",
       "objective": "New human functional source: separate substrate curing, CCK8 and colony assay conditions",
       "inputs": [{"path": str(task / "source_packet.json"), "sha256": hashlib.sha256((task / "source_packet.json").read_bytes()).hexdigest()}],
       "prompt_sha256": hashlib.sha256(prompt).hexdigest(),
       "budget": {"wall_seconds": 180, "max_output_tokens": 2048, "max_stdin_bytes": 12000, "model_calls": 1, "automatic_retries": 0, "new_downloads": 0, "declared_cost_cap_usd": 0.025, "hard_dollar_cap_verified": False},
       "agent_permissions": "All tools disabled; isolated workspace/DSH_HOME; supplied original methods only",
       "allowed_write_root": str(task), "deliverables": ["receipt.json", "events.jsonl", "final.md", "usage.json"],
       "acceptance_criteria": ["Literal conditions match original supplied clauses", "Separate physical curing and assay-specific drug exposure", "Exact prescribed duration conversions", "Keep unstated CCK8 fields and repeat kind unknown; no scientific inference"],
       "requires_main_agent_review": True,
       "mainline": "New formal task first; otherwise supplied HUMAN source/unit/readout/preparation fields; continue unaffected fields."}
(task / "task.json").write_text(json.dumps(job, indent=2) + "\n", encoding="utf-8")
status = """# DS037 assigned — new human support-context source (2026-10-30)

Supplied original Nat Commun methods Sec27/29/44 only: separate substrate curing from CCK8/colony treatment, preserve unspecified fields and repeat kind, perform prescribed time conversions. One isolated tools-disabled call;180s/2048outputtokens/12000Bstdin/declaredUSD0.025 (hard dollar cap unknown),0retry/backendchange. Historical attempts28 retained. No raw outcomes or scientific decisions. Check new formal tasks after each small step, otherwise continue this supplied field packet and unaffected fields. Main-agent review before adoption; no task file proves a live worker. Historical entries below remain historical.

"""
for name in ["CURRENT_TASK.md", "MAINLINE.md", "TASK_QUEUE.md"]:
    target = aux / name
    target.write_text(status + target.read_text(encoding="utf-8"), encoding="utf-8")
print(json.dumps({"task": "DS037", "stdin_bytes": len(prompt), "source_sha256": packet["source_sha256"]}))
