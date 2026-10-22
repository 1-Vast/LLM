# Retained image-locator failure

Original script SHA256: fa03f172c6032c0071bb1e7bb0ba310747ac20642dbdb0b36d855806d8f4afa7.

inspect_caf_images.py first invocation exited1 at `assert len(rows[i-1]['images'])==1` for Supplementary Fig9. OOXML has an empty paragraph between the actual drawing at paragraph45 and its caption at47. The one-paragraph-adjacency assumption was false. No image outputs or provenance file had yet been written; only the empty destination directory existed. This is a parser failure, not an absent figure or scientific negative.

Correction: skip preceding empty OOXML paragraphs and require the first nonempty/drawing paragraph to contain exactly one image. Do not change any scientific decision, numeric targets or predecessor files. Corrected run completed and source-image provenance is retained; all3figures were visually inspected. Original tool traceback remains in conversation; this note records the exact failure site and cause.

A later combined apply_patch failed because a final documentation context omitted the beginning of a long paragraph. The patch was atomic: CAF_SOURCE_FINDINGS.md had not been created, confirmed by Test-Path=False. Retried as a corrected patch; no source evidence or scientific result was overwritten. This was a documentation edit failure.
