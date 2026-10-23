"""Inspect only the S8 Legend annotation text, never images or sheet outcomes."""
from pathlib import Path
from io import BytesIO
import json
import xml.etree.ElementTree as ET
import zipfile

root = Path('D:/MAESTRO')
out = root/'log/20261022/generative_repair_renewal/source/archive_followup'
with zipfile.ZipFile(out/'archive.body') as outer:
    with zipfile.ZipFile(BytesIO(outer.read('TableS8_PTPC_info_0703.xlsx'))) as archive:
        paths = [name for name in archive.namelist() if 'comment' in name.lower() or 'drawing' in name.lower()]
        # A_metadata has no comment file. The Legend sheet is empty sheetData
        # and references drawing1; inspect only DrawingML text nodes, not media.
        text = []
        if 'xl/drawings/drawing1.xml' in paths:
            drawing = ET.fromstring(archive.read('xl/drawings/drawing1.xml'))
            text = [item.text or '' for item in drawing.findall('.//{http://schemas.openxmlformats.org/drawingml/2006/main}t')]
        result = dict(legend_sheet_xml=archive.read('xl/worksheets/sheet1.xml').decode(),
                      comment_and_drawing_paths=paths,legend_drawing_text=text,
                      image_read=False,outcome_cells_read=False)
(out/'S8_ANNOTATION_METADATA.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(result,ensure_ascii=False,indent=2))
