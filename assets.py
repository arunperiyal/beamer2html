"""Files the tool keeps and installs into each project on every run, so a
project only needs its own .tex sources, figures and .bib:

    assets/            -> <project>/html/   deck.js, deck.css, MathJax
    beamer2html.sty    -> <project>/        the beamer templates

beamer2html.sty is found in latex/ (the source repository), in ../../tex/
(the CTAN package: scripts/beamer2html/ next to tex/), or by kpsewhich (a
TeX distribution that has it installed).

Edit the originals, not the copies in a project: the copies are replaced
whenever they differ. (A project's beamer2html.sty that was edited in the
project is kept as beamer2html.sty.bak before being replaced; see
install_latex.) A deck from before the rename that loads titletemplates,
and so has a titletemplates.sty, gets that file updated too.
"""
import filecmp
import hashlib
import json
import os
import shutil
import subprocess

from .log import warn

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(HERE, "assets")
LEGACY = "titletemplates.sty"                  # the package's name before beamer2html


def find_sty():
    """Path of beamer2html.sty, or None."""
    for d in (os.path.join(HERE, "latex"), os.path.join(HERE, "..", "..", "tex")):
        path = os.path.normpath(os.path.join(d, "beamer2html.sty"))
        if os.path.isfile(path):
            return path
    try:
        out = subprocess.run(["kpsewhich", "beamer2html.sty"], capture_output=True,
                             text=True, timeout=20).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return None
    return out if out and os.path.isfile(out) else None


STY = find_sty()


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
    """Copy beamer2html.sty next to the project's main .tex file (and
    refresh a titletemplates.sty there, for decks that still load it).

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
    if not STY:
        warn("beamer2html.sty not found (not next to the tool, nor by kpsewhich): "
             "not installed into the project")
        return
    with open(STY, "rb") as f:
        sty = f.read()
    files = {"beamer2html.sty": sty}
    if os.path.isfile(os.path.join(root, LEGACY)):
        files[LEGACY] = sty.replace(b"\\ProvidesPackage{beamer2html}",
                                    b"\\ProvidesPackage{titletemplates}", 1)
    for name, data in files.items():
        dst = os.path.join(root, name)
        if os.path.isfile(dst):
            with open(dst, "rb") as f:
                if f.read() == data:
                    record[name] = _sha(dst)
                    continue
            if record.get(name) != _sha(dst):          # edited in the project
                shutil.copy2(dst, dst + ".bak")
                warn("%s was changed in this project: replaced by the tool's version, "
                     "your copy kept as %s.bak (make lasting changes in %s)"
                     % (name, name, STY))
        with open(dst, "wb") as f:
            f.write(data)
        record[name] = _sha(dst)
    os.makedirs(os.path.dirname(record_path), exist_ok=True)
    with open(record_path, "w", encoding="utf-8") as f:
        json.dump(record, f, indent=2)
