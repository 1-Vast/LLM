"""Admit independently retrieved novelty threats through the existing library tool."""
from pathlib import Path
import re
import subprocess
import sys
from html import unescape

HERE = Path(__file__).resolve().parent
LIB = Path(r"D:\MAESTRO\reference")
TOOL = Path(r"D:\CodexData\.codex\skills\lit-survey\scripts\reference_library.py")
SOURCE = HERE / "sources/challenger"


def run(*args):
    subprocess.run([sys.executable, str(TOOL), *args], check=True)


entries = [
    ("arxiv-2512.10016", "LAWM", "https://arxiv.org/abs/2512.10016", SOURCE / "arxiv-2512.10016v1.html", "html", "Challenger inspected sections 2-3 and joint objectives/reward; no reproduction."),
    ("arxiv-2610.23615", "HIJP", "https://arxiv.org/abs/2610.23615", SOURCE / "arxiv-2610.23615v1.html", "html", "Challenger inspected sections 3 and 6; goal-conditioned inverse model and hindsight; no reproduction."),
    ("pmlr-v306-guo26g", "Constrained Bayesian Experimental Design via Online Planning", "https://proceedings.mlr.press/v306/guo26g.html", SOURCE / "guo26g.pdf", "pdf", "Challenger PDF pages 1-5, sections 3.1-3.4 partial; scenario tree and known deterministic constraint transition."),
    ("icaps2016-bor", "Bayesian Optimization with Resource Constraints and Production", "https://web.engr.oregonstate.edu/~afern/papers/icaps16-dolatnia.pdf", SOURCE / "icaps16-dolatnia.pdf", "pdf", "Challenger PDF pages 1-4; inventory/production actions and POMDP; older direct novelty threat."),
    ("pmlr-v37-osogami15", "Robust partially observable Markov decision process", "https://proceedings.mlr.press/v37/osogami15.pdf", SOURCE / "osogami15.pdf", "pdf", "Challenger sections 2 and 3.2-3.3; rectangular/local transition ambiguity; older direct novelty threat."),
    ("pmlr-v155-wang21c", "CLOUD", "https://proceedings.mlr.press/v155/wang21c/wang21c.pdf", SOURCE / "wang21c.pdf", "pdf", "Challenger PDF pages 2-4, section 3; joint state/action and forward/inverse representation; older direct novelty threat."),
]
for pid, title, url, path, kind, scope in entries:
    if kind == "html":
        match = re.search(r"<h1\b[^>]*>(.*?)</h1>", path.read_text(encoding="utf-8"), re.S)
        if match:
            title = unescape(re.sub("<[^>]+>", " ", match.group(1)))
            title = " ".join(title.split())
    run("record", str(LIB), "paper", pid, "title=" + title, "landing_page=" + url,
        "type_status=original research; see official source for conference/preprint version",
        "reading_level=P", "reading_scope=" + scope,
        "note=Original download URL/date/HTTP/bytes recorded in research/2026-10-27-agent-cell-colearning/sources/challenger/fixed_retrieval_manifest.json; imported original file without format conversion.")
    run("record", str(LIB), "code", pid, "download_status=not_verified", "note=Code availability not fully checked in this bounded innovation round.")
    args = ["paper", str(LIB), pid, "--file", str(path), "--version", "original-challenger-retrieval"]
    if kind == "html":
        args.append("--html")
    run(*args)
run("paper", str(LIB), "arxiv-2510.26433", "https://arxiv.org/html/2510.26433v2", "--html", "--version", "arxiv-v2")
