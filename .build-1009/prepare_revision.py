from pathlib import Path
import fitz
root = Path(r'D:\MAESTRO\.build-1009\revision')
root.mkdir(parents=True, exist_ok=True)
sources = {
 'map': r'C:\Users\59964\Zotero\storage\9DVWKHBV\Feng 等 - 2026 - A knowledge-driven framework for predicting single-cell responses for unprofiled drugs.pdf',
 'robin': r'C:\Users\59964\Zotero\storage\I4QF8UAI\Ghareeb 等 - 2026 - A multi-agent system for automating scientific discovery.pdf'
}
for name, paper, page, rect in [
 ('map_knowledge', 'map', 2, (40,48,556,328)),
 ('map_predictor', 'map', 2, (40,332,295,570)),
 ('robin_architecture','robin',1,(90,46,515,437)),
 ('robin_evidence','robin',5,(40,228,557,417)),
]:
 doc=fitz.open(sources[paper])
 doc[page].get_pixmap(matrix=fitz.Matrix(3,3),clip=fitz.Rect(rect)).save(root / (name+'.png'))
print(root)
