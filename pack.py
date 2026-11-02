"""--pack: put the generated deck and exactly the files it uses into a zip.

    slides.html                       the deck
    html/                             deck.js, deck.css, references.js, MathJax
    images the slides refer to        <img src>, the title-slide logo
    videos                            <video src>, and their poster images
    animation frames                  every frame of each animateinline

The zip holds one folder named after the zip (talk.zip -> talk/), so it
unpacks cleanly; open talk/slides.html. Nothing else from the project (.tex,
.bib, PDFs, unused figures) is included.

With --slide-range only the chosen slides go in (and only the files they
use); the deck numbers them from 1.

With --compress the raster images and animation frames go in as WebP copies
no larger than the given size (they are shown far smaller than they are
usually rendered); the deck in the zip points at them. The copies are cached
in html/cache/webp-<size>/, so packing again only converts what changed; the
project's own files are not touched.
"""
import html
import json
import os
import re
import zipfile
from concurrent.futures import ProcessPoolExecutor

from .log import warn

STORED = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".woff", ".woff2", ".mp4", ".zip",
          ".webm", ".m4v", ".mov", ".ogv"}
RASTER = {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff"}    # not .gif: may be animated
QUALITY = 82                                   # WebP: no visible loss on renders


def referenced_files(page, root, config):
    """Relative paths of the project files the generated page loads."""
    files = set()

    def add(path):
        path = html.unescape(path).split("?")[0].split("#")[0]
        if not path or re.match(r"^[a-z]+:", path) or path.startswith("/"):
            return                                     # URL, data:, absolute
        files.add(os.path.normpath(path))

    for m in re.finditer(r'\s(?:src|href|poster)="([^"]+)"', page):
        add(m.group(1))
    logo = config.get("logo")
    if logo and os.path.isfile(os.path.join(root, logo)):   # missing: placeholder shown
        add(logo)

    # animations: data-src="…_{n}.png" for every frame in data-frames="a:b:step"
    # of the animation, or of the panel's own <img> (\animpanel[frames=..]);
    # class "anim", plus anim-labelled / anim-grid from \begin{animation}
    start = re.compile(r'<div class="anim(?: [^"]*)?"([^>]*)>')
    frames = re.compile(r'data-frames="(-?\d+):(-?\d+)(?::(-?\d+))?"')

    def frame_nums(fr):
        first, last, step = int(fr.group(1)), int(fr.group(2)), int(fr.group(3) or 1)
        return range(first, last + (1 if step > 0 else -1), step)

    for m in start.finditer(page):
        fr = frames.search(m.group(1))
        if not fr:
            continue
        nums = frame_nums(fr)
        nxt = start.search(page, m.end())
        block = page[m.end():nxt.start() if nxt else len(page)]
        for img in re.finditer(r'<img\b[^>]*>', block):
            src = re.search(r'data-src="([^"]+)"', img.group(0))
            if not src:
                continue
            own = frames.search(img.group(0))
            for n in frame_nums(own) if own else nums:
                add(re.sub(r"\{n(?::(\d+))?\}",
                           lambda mm: str(n).zfill(int(mm.group(1))) if mm.group(1) else str(n),
                           src.group(1)))

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


def webp(src, dst, size):
    """Write a WebP copy of src at dst, fitted in size x size pixels (never
    enlarged). Returns an error message or None."""
    try:
        from PIL import Image
        with Image.open(src) as im:
            im.thumbnail((size, size), Image.LANCZOS)
            if im.mode not in ("RGB", "RGBA"):
                im = im.convert("RGBA" if "A" in im.mode or "transparency" in im.info
                                else "RGB")
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            tmp = dst + ".tmp"
            im.save(tmp, "WEBP", quality=QUALITY, method=4)
        os.replace(tmp, dst)
    except Exception as e:                     # unreadable image: packed as it is
        return "%s: %s" % (type(e).__name__, e)
    return None


def compress(root, files, size):
    """WebP copies of the raster files: {rel: (packed rel, cached copy)}."""
    try:
        from PIL import features
        if not features.check("webp"):
            raise ImportError
    except ImportError:
        warn("--compress needs Pillow with WebP (pip install pillow); images packed as they are")
        return {}
    cache = os.path.join(root, "html", "cache", "webp-%d" % size)
    out, todo, taken = {}, [], set(files)
    for rel in sorted(files):
        full = os.path.join(root, rel)
        if os.path.splitext(rel)[1].lower() not in RASTER or not os.path.isfile(full):
            continue
        new = os.path.splitext(rel)[0] + ".webp"
        if new in taken:                       # a.png and a.jpg (or a.webp): keep this one
            continue
        taken.add(new)
        copy = os.path.join(cache, new)
        out[rel] = (new, copy)
        if not os.path.isfile(copy) or os.path.getmtime(copy) < os.path.getmtime(full):
            todo.append((full, copy))
    if todo:
        print("compressing %d images (%d cached) ..." % (len(todo), len(out) - len(todo)),
              flush=True)
        with ProcessPoolExecutor() as ex:
            errors = list(ex.map(webp, *zip(*todo), [size] * len(todo), chunksize=8))
        for (full, copy), err in zip(todo, errors):
            if err:                            # its bytes under the new name: browsers
                rel = os.path.relpath(full, root)  # go by the content, not the name
                warn("--compress: %s packed as it is (%s)" % (rel, err))
                out[rel] = (out[rel][0], full)
    return out


def rewrite(page, conv, config):
    """The page with its image paths pointing at the WebP copies."""
    def attr(m):
        path = html.unescape(m.group(2))
        if "{n" in path:                       # animation frames: converted together
            frame = re.compile(r"\d+".join(map(re.escape, re.split(r"\{n(?::\d+)?\}",
                                                              os.path.normpath(path)))) + "$")
            new = path
            if any(frame.match(r) for r in conv):
                new = os.path.splitext(path)[0] + ".webp"
        else:
            hit = conv.get(os.path.normpath(path.split("?")[0].split("#")[0]))
            new = hit[0].replace(os.sep, "/") if hit else path
        return '%s="%s"' % (m.group(1), html.escape(new)) if new != path else m.group(0)
    page = re.sub(r'(\s(?:src|href|poster|data-src))="([^"]+)"', attr, page)
    logo = config.get("logo")
    if logo and os.path.normpath(logo) in conv:
        new = conv[os.path.normpath(logo)][0].replace(os.sep, "/")
        page = page.replace('"logo": %s' % json.dumps(logo, ensure_ascii=False),
                            '"logo": %s' % json.dumps(new, ensure_ascii=False))
    return page


def pack(root, out_html, zip_path, config, size=None, page=None):
    """Write zip_path with out_html and its files; with size, raster images
    as WebP fitted in size x size pixels; with page, that page in place of
    out_html's content (some of the slides only). The page is always named
    slides.html in the zip (the viewer apps look for it), whatever -o named
    it. Returns (number of files, total bytes, missing paths)."""
    own = page is not None
    if not own:
        with open(out_html, encoding="utf-8") as f:
            page = f.read()
    files = referenced_files(page, root, config)
    out_rel = os.path.relpath(out_html, root)
    conv = compress(root, files, size) if size else {}
    files.add(out_rel)

    folder = os.path.splitext(os.path.basename(zip_path))[0]
    missing, total, count = [], 0, 0
    with zipfile.ZipFile(zip_path, "w") as z:
        for rel in sorted(files):
            full = os.path.join(root, rel)
            if not os.path.isfile(full):
                missing.append(rel)
                continue
            name = rel
            if rel in conv:
                name, full = conv[rel]
            elif rel == out_rel:
                name = os.path.join(os.path.dirname(rel), "slides.html")
            kind = zipfile.ZIP_STORED if os.path.splitext(name)[1].lower() in STORED \
                else zipfile.ZIP_DEFLATED
            if rel == out_rel and (conv or own):
                data = rewrite(page, conv, config).encode("utf-8")
                info = zipfile.ZipInfo.from_file(full, os.path.join(folder, name))
                info.compress_type = kind
                z.writestr(info, data)
                total += len(data)
            else:
                z.write(full, os.path.join(folder, name), compress_type=kind)
                total += os.path.getsize(full)
            count += 1
    for rel in missing:
        warn("--pack: file used by the slides not found: %s" % rel)
    return count, total, missing
