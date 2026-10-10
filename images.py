"""Finding image files; PDF figures are converted for the browser: to SVG
when they are pure vector graphics (sharp at any size), else to a PNG."""
import os
import re
import subprocess

from .log import warn

IMG_EXTS = [".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".pdf"]


def resolve_image(path, root):
    """Find the file for an \\includegraphics path (extension optional).
    Returns a path relative to `root`; PDF files become a cached SVG/PNG."""
    cands = [path] if os.path.splitext(path)[1].lower() in IMG_EXTS else \
        [path + e for e in IMG_EXTS]
    for c in cands:
        if os.path.isfile(os.path.join(root, c)):
            if c.lower().endswith(".pdf"):
                return pdf_to_web(c, root)
            return c
    return None


VIDEO_EXTS = [".mp4", ".webm", ".m4v", ".mov", ".ogv"]


def resolve_video(path, root):
    """Find the file for a \\slidevideo path (extension optional), relative
    to `root`."""
    cands = [path] if os.path.splitext(path)[1].lower() in VIDEO_EXTS else \
        [path + e for e in VIDEO_EXTS]
    for c in cands:
        if os.path.isfile(os.path.join(root, c)):
            return c
    return None


# a PNG gets at least this many pixels on its longer side, however small the
# PDF page is (a 2-inch plot at a fixed 200 dpi was only 400 px wide)
PNG_MIN_PX = 2000


def pdf_to_web(rel, root):
    """Render a PDF figure into html/cache/ (only when the PDF is newer):
    SVG if it has no embedded raster images, PNG otherwise."""
    src = os.path.join(root, rel)
    base = os.path.join("html", "cache", os.path.splitext(rel)[0].replace(os.sep, "__"))
    ext = ".png" if has_raster(src) else ".svg"
    out = os.path.join(root, base + ext)
    newest = max(os.path.getmtime(src), os.path.getmtime(__file__))  # or this converter
    if os.path.isfile(out) and os.path.getmtime(out) >= newest:
        return base + ext                        # up to date from an earlier run
    os.makedirs(os.path.dirname(out), exist_ok=True)
    try:
        if ext == ".svg":
            subprocess.run(["pdftocairo", "-svg", src, out], check=True, capture_output=True)
        else:
            subprocess.run(["pdftoppm", "-png", "-r", str(png_dpi(src)), "-singlefile",
                            src, out[:-4]], check=True, capture_output=True)
    except (OSError, subprocess.CalledProcessError):
        warn("could not convert %s for the browser (are poppler's pdftocairo and "
             "pdftoppm installed?)" % rel)
        return rel
    other = os.path.join(root, base + (".png" if ext == ".svg" else ".svg"))
    if os.path.isfile(other):                    # stale copy in the other format
        os.remove(other)
    return base + ext


def has_raster(src):
    """Does the PDF embed bitmap images (photos, rendered contours)? Those
    would be copied into an SVG as large base64 blobs."""
    try:
        r = subprocess.run(["pdfimages", "-list", "-f", "1", "-l", "1", src],
                           check=True, capture_output=True, text=True)
    except (OSError, subprocess.CalledProcessError):
        return True                              # can't tell: PNG is the safe choice
    return len(r.stdout.strip().splitlines()) > 2   # beyond the two header lines


def png_dpi(src):
    """Resolution giving the page at least PNG_MIN_PX on its longer side."""
    try:
        r = subprocess.run(["pdfinfo", src], check=True, capture_output=True, text=True)
        m = re.search(r"Page size:\s*([\d.]+) x ([\d.]+) pts", r.stdout)
        longest_in = max(float(m.group(1)), float(m.group(2))) / 72
        return max(200, min(1200, round(PNG_MIN_PX / longest_in)))
    except (OSError, subprocess.CalledProcessError, AttributeError, ValueError):
        return 300
