"""Render the five published supplement pages for read-only visual review."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "log/20261022/serial_antibiotic_alternatives/supplement_followup"
render_dir = OUT / "render"
if render_dir.exists():
    raise FileExistsError("No render overwrite")
render_dir.mkdir()
executable = shutil.which("pdftoppm")
if not executable:
    raise RuntimeError("Poppler pdftoppm not available")
command = [executable, "-f", "1", "-l", "5", "-r", "110", "-png",
           str(OUT / "msaf115_supplementary_data.pdf"), str(render_dir / "page")]
completed = subprocess.run(command, capture_output=True, text=True)
(OUT / "RENDER_STDERR.txt").write_text(completed.stderr, encoding="utf-8")
completed.check_returncode()
files = [{"path": str(file), "bytes": file.stat().st_size,
          "sha256": hashlib.sha256(file.read_bytes()).hexdigest()} for file in sorted(render_dir.glob("page-*.png"))]
assert len(files) == 5
(OUT / "RENDER_RECEIPT.json").write_text(json.dumps({"command": command, "files": files}, indent=2), encoding="utf-8")
print(json.dumps({"rendered_pages": len(files)}, indent=2))
