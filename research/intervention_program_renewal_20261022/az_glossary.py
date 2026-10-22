"""Read the archive's field glossary without opening data rows."""
import json
from pathlib import Path
import shutil
import subprocess
import zipfile

from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "log/20261022/intervention_program_renewal/az_design"
with zipfile.ZipFile(OUT / "matrix_well_stats_GDSC_007_010_plus_Spiper1.zip") as source:
    pdf = OUT / "Glossary_combo_well_stats.pdf"
    pdf.write_bytes(source.read("Glossary_combo_well_stats.pdf"))
reader = PdfReader(pdf)
text = "\n\n".join(f"PAGE {i+1}\n{page.extract_text()}" for i, page in enumerate(reader.pages))
(OUT / "GLOSSARY.txt").write_text(text, encoding="utf-8")
poppler = shutil.which("pdftoppm")
if poppler is None:
    raise RuntimeError("Poppler not on PATH")
result = subprocess.run([poppler, "-scale-to", "1800", "-png", str(pdf), str(OUT / "glossary")], capture_output=True, text=True)
(OUT / "GLOSSARY_RENDER.json").write_text(json.dumps({"pages": len(reader.pages), "returncode": result.returncode, "stdout": result.stdout, "stderr": result.stderr}, indent=2), encoding="utf-8")
result.check_returncode()
print(text)
