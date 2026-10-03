"""Files the tool keeps and installs into each project on every run, so a
project only needs its own .tex sources, figures and .bib:

    assets/                 -> <project>/html/   deck.js, deck.css, MathJax
    latex/titletemplates.sty -> <project>/        the beamer templates

Edit the originals here in tools/tex2html/, not the copies in a project: the
copies are replaced whenever they differ. (A project's titletemplates.sty
that was edited in the project is kept as titletemplates.sty.bak before being
replaced; see install_latex.)
"""
import filecmp
import hashlib
import json
import os
import shutil

from .log import warn

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(HERE, "assets")
LATEX = os.path.join(HERE, "latex")


def install_assets(root):
    """Copy assets/ into <root>/html/, updating files that differ.
    Returns the number of files copied."""
    dest_root = os.path.join(root, "html")
    copied = 0
    for dirpath, _, files in os.walk(ASSETS):
        rel = os.path.relpath(dirpath, ASSETS)
        dest_dir = os.path.normpath(os.path.join(dest_root, rel))
        os.makedirs(dest_dir, exist_ok=True)
        for name in files:
            src, dst = os.path.join(dirpath, name), os.path.join(dest_dir, name)
            if not os.path.isfile(dst) or not filecmp.cmp(src, dst, shallow=False):
                shutil.copy2(src, dst)
                copied += 1
    # html/vendor/ is all ours: drop files a newer version no longer has
    # (e.g. MathJax 2 after the move to MathJax 4)
    vendor = os.path.join(dest_root, "vendor")
    for dirpath, _, files in os.walk(vendor, topdown=False):
        src_dir = os.path.join(ASSETS, os.path.relpath(dirpath, dest_root))
        for name in files:
            if not os.path.isfile(os.path.join(src_dir, name)):
                os.remove(os.path.join(dirpath, name))
        if not os.listdir(dirpath) and not os.path.isdir(src_dir):
            os.rmdir(dirpath)
    return copied


def _sha(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def install_latex(root):
    """Copy latex/*.sty next to the project's main .tex file.

    The fingerprint of each installed copy is kept in html/.installed.json.
    A project copy that still matches it is the tool's own older version and
    is replaced silently; one that does not was edited in the project, so it
    is saved as <name>.bak first and a warning is given."""
    record_path = os.path.join(root, "html", ".installed.json")
    try:
        with open(record_path, encoding="utf-8") as f:
            record = json.load(f)
    except (OSError, ValueError):
        record = {}
    for name in sorted(os.listdir(LATEX)):
        src, dst = os.path.join(LATEX, name), os.path.join(root, name)
        if os.path.isfile(dst):
            if filecmp.cmp(src, dst, shallow=False):
                record[name] = _sha(dst)
                continue
            if record.get(name) != _sha(dst):          # edited in the project
                shutil.copy2(dst, dst + ".bak")
                warn("%s was changed in this project: replaced by the tool's version, "
                     "your copy kept as %s.bak (make lasting changes in "
                     "tools/tex2html/latex/)" % (name, name))
        shutil.copy2(src, dst)
        record[name] = _sha(dst)
    os.makedirs(os.path.dirname(record_path), exist_ok=True)
    with open(record_path, "w", encoding="utf-8") as f:
        json.dump(record, f, indent=2)
