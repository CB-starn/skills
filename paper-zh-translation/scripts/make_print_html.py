import argparse
import html
import pathlib
import re


def inline(text):
    text = html.escape(text)
    text = re.sub(r"\^([^^]+)\^", r"<sup>\1</sup>", text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<em>\1</em>", text)
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    text = re.sub(r"(https?://[^\s<]+)", r'<a href="\1">\1</a>', text)
    return text


def close_table(parts, state):
    if state["in_table"]:
        parts.append("</tbody></table>")
        state["in_table"] = False


def table_row(cells, header):
    tag = "th" if header else "td"
    return "<tr>" + "".join("<{0}>{1}</{0}>".format(tag, inline(c)) for c in cells) + "</tr>"


def build(md_path, html_path):
    lines = md_path.read_text(encoding="utf-8").splitlines()
    body = []
    state = {"in_table": False}
    i = 0

    while i < len(lines):
        raw = lines[i].rstrip()

        if not raw:
            close_table(body, state)
            i += 1
            continue

        image_match = re.match(r"^!\[([^\]]*)\]\(([^)]+)\)$", raw)
        if image_match:
            close_table(body, state)
            alt = html.escape(image_match.group(1))
            src = html.escape(image_match.group(2))
            caption = ""
            j = i + 1
            while j < len(lines) and not lines[j].strip():
                j += 1
            if j < len(lines) and lines[j].startswith("**图 "):
                caption = lines[j].rstrip()
                i = j
            body.append(
                '<figure class="figure-box">'
                '<div class="image-frame"><img src="{}" alt="{}"></div>'.format(src, alt)
                + ("<figcaption>{}</figcaption>".format(inline(caption)) if caption else "")
                + "</figure>"
            )
            i += 1
            continue

        if raw.startswith("|") and raw.endswith("|"):
            cells = [c.strip() for c in raw.strip("|").split("|")]
            if not state["in_table"]:
                body.append('<table class="data-table"><thead>')
                body.append(table_row(cells, header=True))
                body.append("</thead><tbody>")
                state["in_table"] = True
            elif all(re.fullmatch(r":?-{3,}:?", c) for c in cells):
                pass
            else:
                body.append(table_row(cells, header=False))
            i += 1
            continue

        close_table(body, state)
        heading = re.match(r"^(#{1,6})\s+(.*)$", raw)
        if heading:
            level = len(heading.group(1))
            body.append("<h{0}>{1}</h{0}>".format(level, inline(heading.group(2))))
        elif re.match(r"^\d+\.\s+", raw):
            body.append('<p class="listitem">{}</p>'.format(inline(raw)))
        else:
            body.append("<p>{}</p>".format(inline(raw)))
        i += 1

    close_table(body, state)

    css = """
@page { size: A4; margin: 15mm 14mm 16mm 14mm; }
* { box-sizing: border-box; }
body { font-family: "Noto Serif CJK SC", "Source Han Serif SC", "SimSun", "Microsoft YaHei", serif; line-height: 1.62; color: #111; max-width: 980px; margin: 34px auto; padding: 0 28px; background: #fff; }
h1 { font-size: 29px; line-height: 1.25; margin: 0 0 18px; }
h2 { font-size: 22px; border-bottom: 1px solid #d5dbe5; padding-bottom: 6px; margin: 34px 0 14px; }
h3 { font-size: 17px; margin: 25px 0 10px; }
p { margin: 9px 0; text-align: justify; }
a { color: #075db3; text-decoration: none; }
code { font-family: Consolas, "Courier New", monospace; font-size: 0.95em; }
.figure-box { border: 1px solid #d9e0ea; border-radius: 8px; padding: 10px 12px 11px; margin: 18px 0 20px; background: #fbfcfe; break-inside: avoid; page-break-inside: avoid; }
.image-frame { background: #fff; border: 1px solid #eef1f5; border-radius: 6px; padding: 6px; overflow: hidden; }
.figure-box img { display: block; width: auto; max-width: 100%; max-height: 210mm; margin: 0 auto; object-fit: contain; }
figcaption { font-size: 12px; line-height: 1.48; margin-top: 8px; color: #222; text-align: justify; }
.data-table { border-collapse: collapse; width: 100%; font-size: 13px; line-height: 1.35; margin: 14px 0 18px; break-inside: avoid; page-break-inside: avoid; }
th, td { border: 1px solid #cfd5df; padding: 5px 7px; }
th { background: #f2f5f8; }
.listitem { padding-left: 1.6em; text-indent: -1.6em; text-align: left; }
@media print { body { max-width: none; margin: 0; padding: 0; } h1, h2, h3 { break-after: avoid; page-break-after: avoid; } .figure-box, .data-table { break-inside: avoid; page-break-inside: avoid; } }
"""
    doc = (
        '<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">'
        "<title>{}</title><style>{}</style></head><body>\n".format(
            html.escape(md_path.stem), css
        )
        + "\n".join(body)
        + "\n</body></html>\n"
    )
    html_path.write_text(doc, encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Build print-optimized HTML with figure boxes from translated Markdown.")
    parser.add_argument("--md", required=True, help="Input translated Markdown.")
    parser.add_argument("--out", required=True, help="Output HTML.")
    args = parser.parse_args()
    build(pathlib.Path(args.md).resolve(), pathlib.Path(args.out).resolve())
    print(pathlib.Path(args.out).resolve())


if __name__ == "__main__":
    main()
