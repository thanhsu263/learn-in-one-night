#!/usr/bin/env python3
"""Extract text from course materials into UTF-8 .txt files for study-guide building.

Usage:
    python extract_sources.py <file-or-folder> [...] -o <out-dir>

Supports: .pptx .ppt .pdf .docx .xlsx .svg .txt .md .html .htm .csv .json
Writes <out-dir>/<name>.txt per source (with "### Slide N" / "### Page N" markers),
embedded SVG/PPTX images to <out-dir>/_img/<name>/, and <out-dir>/_index.md summarising
everything plus warnings (scanned PDFs, unsupported formats, empty files).

Optional libraries are used when installed (python-pptx, olefile, pypdf / pymupdf,
openpyxl); otherwise zip/XML fallbacks are used where possible.
"""
import argparse
import base64
import html
import os
import re
import struct
import sys
import zipfile

TEXT_EXT = {".txt", ".md", ".csv", ".json"}
HTML_EXT = {".html", ".htm"}
SUPPORTED = {".pptx", ".ppt", ".pdf", ".docx", ".xlsx", ".svg"} | TEXT_EXT | HTML_EXT
OLD_OFFICE = {".doc", ".xls"}
IMG_EXT = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp"}
# Slide-master placeholder text that carries no content
MASTER_JUNK = re.compile(
    r"^(Click to edit Master.*|(Second|Third|Fourth|Fifth) [Ll]evel|Title|Notes|\*|\d+-\*|‹#›|)$"
)


def strip_xml(s):
    s = re.sub(r"<a:br/>|<w:br/>|</a:p>|</w:p>", "\n", s)
    s = re.sub(r"<[^>]+>", "", s)
    return html.unescape(s)


def natural_key(name):
    return [int(t) if t.isdigit() else t for t in re.split(r"(\d+)", name)]


# ---------- PPTX ----------
def pptx_text(path, img_dir):
    out = []
    with zipfile.ZipFile(path) as z:
        slides = sorted(
            [n for n in z.namelist() if re.match(r"ppt/slides/slide\d+\.xml$", n)],
            key=natural_key,
        )
        for i, name in enumerate(slides, 1):
            xml = z.read(name).decode("utf-8", "ignore")
            paras = re.findall(r"<a:p>.*?</a:p>|<a:p .*?</a:p>", xml, flags=re.S)
            lines = [strip_xml(p).strip() for p in paras]
            lines = [l for l in lines if l and not MASTER_JUNK.match(l)]
            note_name = name.replace("slides/slide", "notesSlides/notesSlide")
            notes = ""
            if note_name in z.namelist():
                nx = z.read(note_name).decode("utf-8", "ignore")
                notes = " ".join(
                    strip_xml(p).strip()
                    for p in re.findall(r"<a:p>.*?</a:p>|<a:p .*?</a:p>", nx, flags=re.S)
                ).strip()
                notes = re.sub(r"^\d+\s*$", "", notes)
            out.append(f"### Slide {i}")
            out.extend(lines)
            if notes:
                out.append(f"[notes] {notes}")
            out.append("")
        media = [n for n in z.namelist() if n.startswith("ppt/media/")]
        n_img = 0
        for m in media:
            if os.path.splitext(m)[1].lower() in IMG_EXT and z.getinfo(m).file_size > 15000:
                os.makedirs(img_dir, exist_ok=True)
                with open(os.path.join(img_dir, os.path.basename(m)), "wb") as f:
                    f.write(z.read(m))
                n_img += 1
    return "\n".join(out), {"slides": len(slides), "images": n_img}


# ---------- PPT (binary, PowerPoint 97-2003) ----------
def ppt_text(path, img_dir):
    import olefile  # pip install olefile

    ole = olefile.OleFileIO(path)
    data = ole.openstream("PowerPoint Document").read()
    chunks = []
    slide_no = [0]

    def walk(off, end):
        while off + 8 <= end:
            verinst, rtype, rlen = struct.unpack_from("<HHI", data, off)
            body = off + 8
            if rtype == 0x03EE:  # Slide container
                slide_no[0] += 1
                chunks.append(f"\n### Slide {slide_no[0]}")
            if verinst & 0xF == 0xF:
                walk(body, min(body + rlen, end))
            elif rtype == 0x0FA0:  # TextCharsAtom
                chunks.append(data[body:body + rlen].decode("utf-16-le", "ignore"))
            elif rtype == 0x0FA8:  # TextBytesAtom
                chunks.append(data[body:body + rlen].decode("latin-1", "ignore"))
            off = body + rlen

    walk(0, len(data))
    lines = []
    for c in chunks:
        c = c.replace("\r", "\n").replace("\x0b", "\n").strip()
        c = "\n".join(l for l in c.split("\n") if not MASTER_JUNK.match(l.strip()))
        if c.strip():
            lines.append(c)
    note = {"slides": slide_no[0]}
    if slide_no[0] == 0:
        note["warn"] = "no slide markers found; text order may follow the master/outline"
    return "\n".join(lines), note


# ---------- PDF ----------
def pdf_text(path, img_dir):
    pages = []
    try:
        import pymupdf as fitz  # type: ignore
    except ImportError:
        try:
            import fitz  # type: ignore
        except ImportError:
            fitz = None
    if fitz is not None:
        doc = fitz.open(path)
        for p in doc:
            pages.append(p.get_text())
    else:
        try:
            from pypdf import PdfReader
        except ImportError:
            from PyPDF2 import PdfReader  # type: ignore
        r = PdfReader(path)
        for p in r.pages:
            pages.append(p.extract_text() or "")
    out = []
    for i, t in enumerate(pages, 1):
        out.append(f"### Page {i}")
        out.append(t.strip())
        out.append("")
    text = "\n".join(out)
    note = {"pages": len(pages)}
    real = sum(len(t.strip()) for t in pages)
    if pages and real < 40 * len(pages):
        note["warn"] = (
            f"very little text ({real} chars for {len(pages)} pages) - probably scanned; "
            "read the pages as images (Read tool with pages=...)"
        )
    return text, note


# ---------- DOCX ----------
def docx_text(path, img_dir):
    with zipfile.ZipFile(path) as z:
        xml = z.read("word/document.xml").decode("utf-8", "ignore")
    xml = re.sub(r"<w:tab/>", "\t", xml)
    xml = re.sub(r"</w:tc>", " | ", xml)
    paras = re.findall(r"<w:p[ >].*?</w:p>", xml, flags=re.S)
    lines = [strip_xml(p).strip() for p in paras]
    return "\n".join(l for l in lines if l), {}


# ---------- XLSX ----------
def xlsx_text(path, img_dir):
    import openpyxl  # pip install openpyxl

    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    out = []
    rows = 0
    for ws in wb.worksheets:
        out.append(f"### Sheet {ws.title}")
        for row in ws.iter_rows(values_only=True):
            cells = ["" if v is None else str(v) for v in row]
            if any(c.strip() for c in cells):
                out.append(" | ".join(cells).rstrip(" |"))
                rows += 1
        out.append("")
    return "\n".join(out), {"rows": rows}


# ---------- SVG ----------
def svg_text(path, img_dir):
    s = open(path, encoding="utf-8", errors="ignore").read()
    texts = []
    for m in re.finditer(r"<text\b.*?</text>", s, flags=re.S):
        t = html.unescape(re.sub(r"<[^>]+>", " ", m.group(0)))
        t = re.sub(r"\s+", " ", t).strip()
        if t:
            texts.append(t)
    for m in re.finditer(r"<foreignObject\b.*?</foreignObject>", s, flags=re.S):
        t = html.unescape(re.sub(r"<[^>]+>", " ", m.group(0)))
        t = re.sub(r"\s+", " ", t).strip()
        if t:
            texts.append(t)
    n_img = 0
    for m in re.finditer(r'data:image/(png|jpe?g|gif|webp);base64,([A-Za-z0-9+/=\s]+)', s):
        raw = base64.b64decode(re.sub(r"\s", "", m.group(2)))
        if len(raw) < 5000:
            continue
        os.makedirs(img_dir, exist_ok=True)
        ext = "jpg" if m.group(1).startswith("jp") else m.group(1)
        with open(os.path.join(img_dir, f"{n_img:02d}.{ext}"), "wb") as f:
            f.write(raw)
        n_img += 1
    note = {"text_items": len(texts), "images": n_img}
    if not texts and n_img:
        note["warn"] = "SVG has no text elements; content is in the images - view them"
    return "\n".join(texts), note


def plain_text(path, img_dir):
    raw = open(path, "rb").read()
    for enc in ("utf-8-sig", "cp1258", "cp1252", "latin-1"):
        try:
            return raw.decode(enc), {}
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", "ignore"), {}


def html_text(path, img_dir):
    s, _ = plain_text(path, img_dir)
    s = re.sub(r"<(script|style)\b.*?</\1>", "", s, flags=re.S | re.I)
    s = re.sub(r"<br\s*/?>|</p>|</li>|</tr>|</h\d>|</div>", "\n", s, flags=re.I)
    s = html.unescape(re.sub(r"<[^>]+>", " ", s))
    s = re.sub(r"[ \t]+", " ", s)
    s = re.sub(r"\n\s*\n+", "\n\n", s)
    return s.strip(), {}


HANDLERS = {
    ".pptx": pptx_text, ".ppt": ppt_text, ".pdf": pdf_text, ".docx": docx_text,
    ".xlsx": xlsx_text, ".svg": svg_text,
    **{e: plain_text for e in TEXT_EXT}, **{e: html_text for e in HTML_EXT},
}


def collect(paths, out_dir):
    files, skipped = [], []
    out_abs = os.path.abspath(out_dir)
    for p in paths:
        if os.path.isdir(p):
            for root, dirs, names in os.walk(p):
                if os.path.abspath(root).startswith(out_abs):
                    continue
                dirs[:] = [d for d in dirs if not d.startswith((".", "_extract"))]
                for n in sorted(names, key=natural_key):
                    fp = os.path.join(root, n)
                    ext = os.path.splitext(n)[1].lower()
                    if n.startswith("~$"):
                        continue
                    if ext in SUPPORTED:
                        files.append(fp)
                    elif ext in OLD_OFFICE:
                        skipped.append((fp, "old Office format - ask the user to resave as .docx/.xlsx/.pdf"))
                    elif ext in IMG_EXT:
                        skipped.append((fp, "image - view it directly with the Read tool if relevant"))
        elif os.path.isfile(p):
            ext = os.path.splitext(p)[1].lower()
            if ext in SUPPORTED:
                files.append(p)
            else:
                skipped.append((p, f"unsupported extension {ext}"))
        else:
            skipped.append((p, "path not found"))
    return files, skipped


def safe_name(path, used):
    base = re.sub(r"[^\w.\-]+", "_", os.path.basename(path), flags=re.U).strip("_") or "file"
    name, i = base, 2
    while name in used:
        name = f"{base}_{i}"
        i += 1
    used.add(name)
    return name


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("paths", nargs="+")
    ap.add_argument("-o", "--out", required=True, help="output directory")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    files, skipped = collect(a.paths, a.out)
    used = set()
    rows = []
    for fp in files:
        ext = os.path.splitext(fp)[1].lower()
        name = safe_name(fp, used)
        img_dir = os.path.join(a.out, "_img", name)
        try:
            text, note = HANDLERS[ext](fp, img_dir)
        except ImportError as e:
            rows.append((fp, "", 0, {"warn": f"missing library: {e.name} (pip install {e.name})"}))
            continue
        except Exception as e:  # keep going on one bad file
            rows.append((fp, "", 0, {"warn": f"failed: {type(e).__name__}: {e}"}))
            continue
        out_fp = os.path.join(a.out, name + ".txt")
        with open(out_fp, "w", encoding="utf-8") as f:
            f.write(f"SOURCE: {fp}\n\n{text}\n")
        if len(text.strip()) == 0 and "warn" not in note:
            note["warn"] = "no text extracted"
        rows.append((fp, out_fp, len(text), note))

    lines = ["# Extracted sources", "", "| Source | Output | Chars | Info |", "|---|---|---|---|"]
    for fp, out_fp, n, note in rows:
        info = ", ".join(f"{k}={v}" for k, v in note.items() if k != "warn")
        if "warn" in note:
            info = (info + "; " if info else "") + "**WARN: " + note["warn"] + "**"
        lines.append(f"| {fp} | {os.path.basename(out_fp) if out_fp else '-'} | {n} | {info} |")
    if skipped:
        lines += ["", "## Not extracted", ""]
        lines += [f"- {fp}: {why}" for fp, why in skipped]
    total = sum(r[2] for r in rows)
    lines += ["", f"Total: {len(rows)} files, {total} chars."]
    with open(os.path.join(a.out, "_index.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
