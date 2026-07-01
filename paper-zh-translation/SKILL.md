---
name: paper-zh-translation
description: Use when translating academic PDFs or papers into Chinese paper-style readers, especially when the user asks to preserve figures, tables, captions, source traceability, original layout cues, or export Markdown/HTML/PDF for sharing.
---

# Paper Zh Translation

## Overview

Translate full academic papers into Chinese paper-style reading artifacts. Preserve structure, figures, tables, captions, citations, units, gene/protein symbols, Latin species names, and source traceability; do not degrade into a summary unless the user explicitly asks for one.

## Core Workflow

1. **Prepare source**
   - Copy the input PDF to a stable work directory with an ASCII filename when paths contain Chinese or spaces.
   - Inspect page count, text extractability, image objects, and whether OCR is needed.
   - If the user mentions BabelDOC only as a reference, use its translation principles; do not run BabelDOC unless explicitly requested.

2. **Extract material**
   - Run `scripts/extract_pdf_for_translation.py --pdf <input.pdf> --out <output-dir>`.
   - Use `extracted/page_XX.txt`, `extracted/full_text.txt`, `assets/pXX_imageblock_YY.png`, and `page_renders/page_XX.png` to reconstruct reading order and figure locations.
   - If figure extraction misses vector graphics, crop from rendered pages with PyMuPDF and save as `assets/figNN.png`.

3. **Translate conservatively**
   - Translate the whole extractable paper, not just abstract/introduction.
   - Use formal Chinese academic prose.
   - Keep citations, numbers, units, formulas, group labels, gene/protein symbols, database names, and Latin species names unchanged.
   - Keep author names and reference entries in their source form unless the user explicitly asks to translate them.
   - Translate figure/table captions and section headings; do not redraw figure internals unless requested.

4. **Build artifacts**
   - Primary: `paper_zh.md`.
   - Required support: `assets/`, `source_map.json`, `translation_notes.md`.
   - Sharing output: `paper_zh_print.html` and `paper_zh_share.pdf`.
   - Use figure blocks in Markdown:

```markdown
![图1](assets/fig01.png)

**图 1. 中文图题。** 中文图注，保留统计方法、单位、P 值和组别标签。
```

5. **Generate shareable PDF**
   - Run `python scripts/make_print_html.py --md paper_zh.md --out paper_zh_print.html`.
   - Install Playwright locally if needed: `npm install --prefix .node_tools playwright --no-save --no-package-lock`.
   - Run `NODE_PATH=<output>/.node_tools/node_modules node scripts/print_pdf.js --html paper_zh_print.html --pdf paper_zh_share.pdf`.
   - The print HTML wraps each image and its caption in a single figure box so they are less likely to split across pages.

## Output Contract

Produce these files unless the user asks for a narrower output:

| File | Purpose |
|---|---|
| `paper_zh.md` | Main Chinese translation with figures, captions, tables, and references |
| `assets/figNN.png` | Clean figure/table crops used by the translation |
| `paper_zh_print.html` | Print-optimized HTML with figure boxes |
| `paper_zh_share.pdf` | Shareable A4 PDF |
| `source_map.json` | Section/page/figure/table source mapping |
| `translation_notes.md` | Translation policy, known limitations, and uncertainty notes |

## Quality Checks

Before final response:

- Parse `source_map.json` as JSON.
- Verify every Markdown image path exists.
- Verify every expected figure has an asset and caption.
- Verify `paper_zh_share.pdf` exists, has extractable text, and embeds the expected number of images.
- Render representative PDF pages with PyMuPDF and inspect: first page, first major figure, a middle figure/table page, and last page.
- Check no browser headers/footers or `file:///...` URL text appear in the PDF.
- Fix tight crops that cut panel labels, axis titles, legends, or figure borders.

## Common Mistakes

| Mistake | Correction |
|---|---|
| Only translating the abstract or making a summary | Translate the full extractable paper unless explicitly scoped down |
| Losing figures/tables | Extract or crop every major figure/table and cite it near the relevant text |
| Splitting figure and caption across pages | Use the print HTML figure-box workflow |
| Translating gene names, Latin names, units, group labels, or citations | Preserve them exactly |
| Translating reference entries freely | Keep source bibliographic entries unless requested |
| Trusting extraction order blindly | Reconcile text order against rendered pages, especially around multi-column figures |
| Delivering without visual QA | Render PDF pages and inspect before claiming completion |

## Script Notes

- Scripts assume Python 3.8+ and PyMuPDF (`fitz`) for PDF extraction/rendering.
- `print_pdf.js` requires Node.js and Playwright. It can use system Chrome when available; otherwise Playwright's bundled Chromium may work.
- Scripts are helpers, not replacements for translation judgment.
