"""Collect selected primary papers only; never execute their code."""
from pathlib import Path
import subprocess
import sys

ROOT = Path(r"D:\MAESTRO")
TOOL = Path(r"D:\CodexData\.codex\skills\lit-survey\scripts\reference_library.py")
PAPERS = [
    ("2608.09696", "Model Discovery Agent: LLM-assisted Bayesian experiment design for data-efficient discovery of mechanistic world models"),
    ("2606.02372", "CoMap: Co-Evolving World Models and Agent Policies for LLM Agents"),
    ("2510.26433", "CoLA-World"),
    ("2607.01531", "OPINE-World"),
    ("2512.00306", "VCWorld: A Biological World Model for Virtual Cell Simulation"),
    ("2609.29221", "PRAXIS-VirtualCell: A Programmable and Trustworthy Framework for Agentic Virtual Cell Experiments"),
]

for ident, title in PAPERS:
    pid = "arxiv-" + ident
    base = [sys.executable, str(TOOL)]
    subprocess.run(base + ["record", str(ROOT / "reference"), "paper", pid,
        "title=" + title, "alt_id=arxiv:" + ident, "type_status=preprint; acceptance not verified",
        "landing_page=https://arxiv.org/abs/" + ident,
        "date_basis=Official arXiv identifier and v1 full text; exact first-public day not yet recorded",
        "reading_level=R", "reading_scope=Identity and method sections to be checked during joint-learning research",
        "note=Bounded 2026-10-27 co-learning prior check; initial bibliographic title may require full-text correction."], check=True)
    subprocess.run(base + ["record", str(ROOT / "reference"), "code", pid,
        "download_status=not_verified", "note=Code availability not yet checked; no execution or reproduction."], check=True)
    subprocess.run(base + ["paper", str(ROOT / "reference"), pid,
        "https://arxiv.org/html/" + ident + "v1", "--html", "--version", "arxiv-v1"], check=True)
