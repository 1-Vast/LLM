"""Read-only PDF page/heading inventory; mask numerical caption tokens."""
import hashlib
import json
from pathlib import Path
import re

from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "log/20261022/serial_antibiotic_alternatives/supplement_followup"
SOURCE = OUT / "msaf115_supplementary_data.pdf"


def main():
    if (OUT / "PDF_INVENTORY.json").exists():
        raise FileExistsError("No inventory overwrite")
    if hashlib.sha256(SOURCE.read_bytes()).hexdigest() != "4dfc44aa78d1f176871c49abde5694fe3b46c97c68dfe6cae8c30ffcb8f80b4b":
        raise ValueError("PDF source changed")
    reader = PdfReader(SOURCE)
    pages, text = [], []
    for index, page in enumerate(reader.pages, 1):
        page_text = page.extract_text()
        text.append(f"PAGE {index}\n{page_text}")
        headings = []
        for line in page_text.splitlines():
            if re.match(r"\s*(?:(?:Supplementary\s+)?(?:Fig(?:ure)?\.?|Table)\s*S?\d+|Supplementary (?:Information|Data|Material|Tables|Figures))", line, re.I):
                headings.append(re.sub(r"\d+(?:\.\d+)?", "[NUM]", line.strip()))
        pages.append({"page": index, "text_characters": len(page_text), "heading_lines_numbers_masked": headings})
    (OUT / "sealed_extracted_text.txt").write_text("\n\n".join(text), encoding="utf-8")
    result = {"pages": pages, "page_count": len(pages), "pdf_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
              "code_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              "response_values_exported": False, "raw_text_kept_separate": True}
    (OUT / "PDF_INVENTORY.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
