"""Prepare one fixed protocol-field extraction packet, not scientific delegation."""
from pathlib import Path
import hashlib
import json
import xml.etree.ElementTree as ET

root = Path(__file__).resolve().parent
aux = root.parent / "deepseek"
task = aux / "tasks/DS035"
assert not task.exists(), "Do not overwrite an existing assignment"
(task / "workspace").mkdir(parents=True)
source = root / "evidence/p5_negative_hysteresis.xml"
article = ET.parse(source).getroot()
plain = lambda element: " ".join("".join(element.itertext()).split())
sections = {}
for element in article.iter("sec"):
    if element.get("id") in ["Sec13", "Sec14", "Sec16"]:
        sections[element.get("id")] = [plain(p) for p in element.findall("p")]
packet = {"source_doi": "10.1038/s41467-026-71178-5",
          "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
          "passages": sections,
          "artifact_rows": [{"attachment": "MOESM2", "label": "Description of Additional Supplementary File", "file": "41467_2026_71178_MOESM2_ESM.pdf"},
                            {"attachment": "MOESM18", "label": "Source Data", "file": "41467_2026_71178_MOESM18_ESM.xlsx"}],
          "fixed_flags": ["OD_is_not_CFU", "dose_selection_uses_growth_outcomes", "wash_scope_is_PA14_CAR_GEN", "raw_workbook_not_accessed"]}
source_packet = task / "source_packet.json"
source_packet.write_text(json.dumps(packet, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
rules = """Extract fixed protocol fields from the supplied original-method passages. No tools, no lookup, no hypothesis, metric/method selection or scientific verdict. JSON only, exact keys:
screen: {interval_minutes, duration_hours, plate_wells, pretreatment_MIC_fractions, main_MIC_fractions}; numbers/lists only, preserving passage order.
cfu: {main_treatment_sampling_hours, main_treatment_sampling_seconds}; lists of numbers. Convert hours to seconds by multiplying exactly by3600. Include all scheduled main-treatment sampling times, not pretreatment duration.
wash: {PBS_washes, PBS_mL_per_wash, centrifugation_minutes, centrifugation_g, temperature_C, replicate_n, replicate_label}; numeric fields plus replicate_label copied as 'biological replicates'.
artifacts: copy artifact_rows exactly.
flags: copy fixed_flags exactly in order.
missing_fields: [] when all required fields explicit, otherwise list only missing key names and continue other fields. Do not infer identical replicate nesting for the large OD screen or biological generality. Do not add provenance, interpretation, new flags or commentary. At each outer small-step boundary check new formal task first; without one resume supplied source/unit/time/replicate fields. Missing local fields do not stop independent fields.
One isolated call, tools disabled,180s,2048 output tokens,12000Bstdin,declaredUSD0.025 (hard dollar cap/effective backend/cost unverified),0retry/backend change.
INPUT:
"""
prompt = (rules + json.dumps(packet, ensure_ascii=False, indent=2)).encode("utf-8")
assert len(prompt) <= 12000
(task / "prompt.txt").write_bytes(prompt)
job = {"task_id": "DS035", "task_version": "v1", "status": "assigned_ready_for_execution",
       "is_execution_authorization": True, "transport": "isolated_headless_stdin_no_tools",
       "objective": "Extract fixed OD/CFU/wash protocol fields and supplied attachment identities; no mechanism judgment",
       "inputs": [{"path": str(source_packet), "sha256": hashlib.sha256(source_packet.read_bytes()).hexdigest()}],
       "prompt_sha256": hashlib.sha256(prompt).hexdigest(),
       "budget": {"wall_seconds": 180, "max_output_tokens": 2048, "max_stdin_bytes": 12000,
                  "model_calls": 1, "automatic_retries": 0, "new_downloads": 0,
                  "declared_cost_cap_usd": 0.025, "hard_dollar_cap_verified": False},
       "agent_permissions": "All tools disabled; isolated workspace/DSH_HOME; supplied method passages only",
       "allowed_write_root": str(task), "deliverables": ["receipt.json", "events.jsonl", "final.md", "usage.json"],
       "acceptance_criteria": ["All fixed screen/CFU/wash fields match original source clauses", "Hour*3600 exact for every scheduled time", "Supplied attachment rows and flags exact; no added scientific inference"],
       "requires_main_agent_review": True,
       "mainline": "New formal task first after each small step, otherwise source/unit/time/replicate checkpoint within explicit inputs/rules/budget; independent fields continue under local ambiguity."}
(task / "task.json").write_text(json.dumps(job, indent=2) + "\n", encoding="utf-8")
status = """# DS035 assigned — fixed recent-source protocol fields (2026-10-29)

New focused extension retains historical26Harness attempts and priorDS032–034new3/3; allocates at mostDS035/036two NEW calls. DS035 is one tool-disabled isolated packet,180s/2048tokens/12000Bstdin,declaredUSD0.025(not verified hard cap),0retry/backendchange. Supplied NatureCommun2026 methods only: fixed OD,CFU,wash units/times and attachment identities, no raw outcomes or scientific decisions.

At each small-step boundary check formal new tasks first; otherwise resume the explicit source/unit/time/replicate/format breakpoint, recording ambiguity while other authorized fields continue. No prior task replay, protected access or live background process is inferred. Old completed allocation statements below remain historical. Completion requires actual receipt/output and main review.

"""
for name in ["CURRENT_TASK.md", "MAINLINE.md", "TASK_QUEUE.md"]:
    path = aux / name
    path.write_text(status + path.read_text(encoding="utf-8"), encoding="utf-8")
print(json.dumps({"task": str(task), "stdin_bytes": len(prompt), "source_sha256": packet["source_sha256"]}))
