"""Finding image files; PDF figures are converted to PNG for the browser."""
import os
import subprocess

from .log import warn

IMG_EXTS = [".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".pdf"]


def resolve_image(path, root):
    """Find the file for an \\includegraphics path (extension optional).
    Returns a path relative to `root`; PDF files become a cached PNG."""
    cands = [path] if os.path.splitext(path)[1].lower() in IMG_EXTS else \
        [path + e for e in IMG_EXTS]
    for c in cands:
        if os.path.isfile(os.path.join(root, c)):
            if c.lower().endswith(".pdf"):
                return pdf_to_png(c, root)
            return c
    return None


def pdf_to_png(rel, root):
    """Render a PDF figure into html/cache/ (only when the PDF is newer)."""
    out_rel = os.path.join("html", "cache",
                           os.path.splitext(rel)[0].replace(os.sep, "__") + ".png")
    src, out = os.path.join(root, rel), os.path.join(root, out_rel)
    if not os.path.isfile(out) or os.path.getmtime(out) < os.path.getmtime(src):
        os.makedirs(os.path.dirname(out), exist_ok=True)
        try:
            subprocess.run(["pdftoppm", "-png", "-r", "200", "-singlefile", src,
                            out[:-4]], check=True, capture_output=True)
        except (OSError, subprocess.CalledProcessError):
            warn("could not convert %s to PNG (is pdftoppm installed?)" % rel)
            return rel
    return out_rel
