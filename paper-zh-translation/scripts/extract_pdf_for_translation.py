import argparse
import json
import pathlib
import shutil
import sys


def import_fitz():
    try:
        import fitz
    except Exception as exc:
        raise SystemExit(
            "PyMuPDF is required. Install it with: python -m pip install pymupdf"
        ) from exc
    return fitz


def main():
    parser = argparse.ArgumentParser(
        description="Extract PDF text, image blocks, rendered pages, and metadata for Chinese paper translation."
    )
    parser.add_argument("--pdf", required=True, help="Input PDF path.")
    parser.add_argument("--out", required=True, help="Output directory.")
    parser.add_argument("--copy-name", default="source.pdf", help="Copied source PDF filename.")
    parser.add_argument("--render-scale", type=float, default=1.8, help="Scale for full-page PNG renders.")
    args = parser.parse_args()

    fitz = import_fitz()
    src = pathlib.Path(args.pdf).expanduser().resolve()
    if not src.exists():
        raise SystemExit("Input PDF not found: {}".format(src))

    out = pathlib.Path(args.out).expanduser().resolve()
    extracted = out / "extracted"
    assets = out / "assets"
    renders = out / "page_renders"
    for directory in (out, extracted, assets, renders):
        directory.mkdir(parents=True, exist_ok=True)

    copied_pdf = out / args.copy_name
    if src != copied_pdf:
        shutil.copyfile(str(src), str(copied_pdf))

    doc = fitz.open(str(copied_pdf))
    full_text = []
    block_meta = []
    image_meta = []

    for page_index, page in enumerate(doc, start=1):
        text = page.get_text("text")
        (extracted / "page_{:02d}.txt".format(page_index)).write_text(text, encoding="utf-8")
        full_text.append("\n\n===== PAGE {} =====\n{}".format(page_index, text))

        page_dict = page.get_text("dict")
        for block_index, block in enumerate(page_dict.get("blocks", [])):
            if block.get("type") == 0:
                lines = []
                for line in block.get("lines", []):
                    span_text = "".join(span.get("text", "") for span in line.get("spans", [])).strip()
                    if span_text:
                        lines.append(span_text)
                block_text = "\n".join(lines).strip()
                if block_text:
                    block_meta.append(
                        {
                            "page": page_index,
                            "block": block_index,
                            "bbox": block.get("bbox"),
                            "text": block_text,
                        }
                    )
            elif block.get("type") == 1:
                bbox = block.get("bbox")
                image_meta.append(
                    {
                        "page": page_index,
                        "block": block_index,
                        "bbox": bbox,
                        "width": block.get("width"),
                        "height": block.get("height"),
                        "ext": block.get("ext"),
                    }
                )
                rect = fitz.Rect(bbox)
                rect.x0 = max(0, rect.x0 - 5)
                rect.y0 = max(0, rect.y0 - 5)
                rect.x1 = min(page.rect.width, rect.x1 + 5)
                rect.y1 = min(page.rect.height, rect.y1 + 5)
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2), clip=rect, alpha=False)
                pix.save(str(assets / "p{:02d}_imageblock_{:02d}.png".format(page_index, block_index)))

        render = page.get_pixmap(
            matrix=fitz.Matrix(args.render_scale, args.render_scale), alpha=False
        )
        render.save(str(renders / "page_{:02d}.png".format(page_index)))

    (extracted / "full_text.txt").write_text("".join(full_text), encoding="utf-8")
    (extracted / "blocks.json").write_text(
        json.dumps(block_meta, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (extracted / "image_blocks.json").write_text(
        json.dumps(image_meta, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    manifest = {
        "source_pdf": str(copied_pdf),
        "page_count": doc.page_count,
        "text_chars": sum(len(page.get_text("text")) for page in doc),
        "text_blocks": len(block_meta),
        "image_blocks": len(image_meta),
        "outputs": {
            "full_text": str(extracted / "full_text.txt"),
            "blocks": str(extracted / "blocks.json"),
            "image_blocks": str(extracted / "image_blocks.json"),
            "assets": str(assets),
            "page_renders": str(renders),
        },
    }
    (out / "extraction_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
