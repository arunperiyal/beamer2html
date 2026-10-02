"""--pack: put the generated deck and exactly the files it uses into a zip.

    slides.html                       the deck
    html/                             deck.js, deck.css, references.js, MathJax
    images the slides refer to        <img src>, the title-slide logo
    animation frames                  every frame of each animateinline

The zip holds one folder named after the zip (talk.zip -> talk/), so it
unpacks cleanly; open talk/slides.html. Nothing else from the project (.tex,
.bib, PDFs, unused figures) is included.
"""
import html
import os
import re
import zipfile

from .log import warn

STORED = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".woff", ".woff2", ".mp4", ".zip"}


def referenced_files(page, root, config):
    """Relative paths of the project files the generated page loads."""
    files = set()

    def add(path):
        path = html.unescape(path).split("?")[0].split("#")[0]
        if not path or re.match(r"^[a-z]+:", path) or path.startswith("/"):
            return                                     # URL, data:, absolute
        files.add(os.path.normpath(path))

    for m in re.finditer(r'\s(?:src|href)="([^"]+)"', page):
        add(m.group(1))
    logo = config.get("logo")
    if logo and os.path.isfile(os.path.join(root, logo)):   # missing: placeholder shown
        add(logo)

    # animations: data-src="…_{n}.png" for every frame in data-frames="a:b:step"
    for m in re.finditer(r'<div class="anim"([^>]*)>', page):
        fr = re.search(r'data-frames="(-?\d+):(-?\d+)(?::(-?\d+))?"', m.group(1))
        if not fr:
            continue
        first, last, step = int(fr.group(1)), int(fr.group(2)), int(fr.group(3) or 1)
        nums = range(first, last + (1 if step > 0 else -1), step)
        end = page.find('<div class="anim"', m.end())
        block = page[m.end():end if end > 0 else len(page)]
        for src in re.findall(r'data-src="([^"]+)"', block):
            for n in nums:
                add(re.sub(r"\{n(?::(\d+))?\}",
                           lambda mm: str(n).zfill(int(mm.group(1))) if mm.group(1) else str(n),
                           src))

    # the whole html/ folder (engine, MathJax, references.js), except the
    # PDF-figure cache: only the images actually used from it are added above
    for dirpath, dirs, names in os.walk(os.path.join(root, "html")):
        rel = os.path.relpath(dirpath, root)
        if rel.split(os.sep)[:2] == ["html", "cache"]:
            continue
        for name in names:
            if not name.startswith(".") and name not in ("build.js", "goto.js"):  # --watch only
                files.add(os.path.normpath(os.path.join(rel, name)))
    return files


def pack(root, out_html, zip_path, config):
    """Write zip_path with out_html (as slides.html's own name) and its files.
    Returns (number of files, total bytes, missing paths)."""
    with open(out_html, encoding="utf-8") as f:
        page = f.read()
    files = referenced_files(page, root, config)
    files.add(os.path.relpath(out_html, root))

    folder = os.path.splitext(os.path.basename(zip_path))[0]
    missing, total, count = [], 0, 0
    with zipfile.ZipFile(zip_path, "w") as z:
        for rel in sorted(files):
            full = os.path.join(root, rel)
            if not os.path.isfile(full):
                missing.append(rel)
                continue
            kind = zipfile.ZIP_STORED if os.path.splitext(rel)[1].lower() in STORED \
                else zipfile.ZIP_DEFLATED
            z.write(full, os.path.join(folder, rel), compress_type=kind)
            total += os.path.getsize(full)
            count += 1
    for rel in missing:
        warn("--pack: file used by the slides not found: %s" % rel)
    return count, total, missing
