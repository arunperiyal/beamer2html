"""Command line:  tex2html [main.tex] [-o slides.html] [--pack [talk.zip] [--compress [PX]]]
               [--watch]"""
import argparse
import os
import sys
import time

from . import __doc__ as package_doc
from . import log
from .assets import ASSETS, LATEX, install_assets, install_latex
from .document import convert
from .pack import pack, referenced_files
from .page import render_page
from .watch import watch


def main(argv=None):
    ap = argparse.ArgumentParser(
        prog="tex2html", description=package_doc.split("\n\n")[0],
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("tex", nargs="?", default="main.tex",
                    help="main .tex file (default: main.tex); its folder is "
                         "the project folder all paths are relative to")
    ap.add_argument("-o", "--output", default="slides.html",
                    help="HTML file to write, relative to the project folder "
                         "(default: slides.html)")
    ap.add_argument("--pack", nargs="?", const="", metavar="ZIP",
                    help="also write a zip with the deck and only the files it "
                         "uses, to copy to the presenting computer (default "
                         "name: the HTML file's name with .zip)")
    ap.add_argument("--compress", nargs="?", type=int, const=960, metavar="PX",
                    help="with --pack: put the images and animation frames in the "
                         "zip as WebP, at most PX pixels wide and high (default "
                         "960) -- a much smaller zip; the project's files are "
                         "not changed")
    ap.add_argument("-w", "--watch", action="store_true",
                    help="keep running and rebuild whenever a source file "
                         "changes (like latexmk -pvc); an open deck reloads "
                         "itself. Ctrl+C to stop")
    a = ap.parse_args(argv)

    tex = os.path.abspath(a.tex)
    root = os.path.dirname(tex)
    if not os.path.isfile(tex):
        ap.error("%s not found" % a.tex)
    if a.watch and a.pack is not None:
        ap.error("--pack makes a copy for presenting: run it without --watch")
    if os.path.splitext(a.output)[1].lower() not in (".html", ".htm"):
        ap.error("-o %s: -o names the HTML file (e.g. -o talk.html); the zip's "
                 "name goes after --pack (--pack talk.zip)" % a.output)
    if a.compress is not None and a.pack is None:
        ap.error("--compress goes with --pack")
    if a.compress is not None and a.compress < 64:
        ap.error("--compress %d: give the largest size in pixels, e.g. 960" % a.compress)
    out = a.output if os.path.isabs(a.output) else os.path.join(root, a.output)

    if a.watch:
        def rebuild(changed):
            if changed:
                names = ", ".join(os.path.relpath(p, root) for p in changed[:3])
                more = " and %d more" % (len(changed) - 3) if len(changed) > 3 else ""
                print("[%s] changed: %s%s" % (time.strftime("%H:%M:%S"), names, more),
                      flush=True)
            try:
                files, _ = build(tex, root, out, live=True)
                print_warnings()
                return files
            except Exception as e:             # keep watching; last good deck stays
                print("[%s] build failed (%s: %s) -- slides.html left as it was" % (
                    time.strftime("%H:%M:%S"), type(e).__name__, e), file=sys.stderr)
                return None
        watch(rebuild)
        return 0

    _, config = build(tex, root, out)
    if a.pack is not None:
        do_pack(a.pack, root, out, config, a.compress)
    print_warnings()
    return 0


def build(tex, root, out, live=False):
    """Convert once. Returns (files whose change should trigger a rebuild,
    DECK_CONFIG). With live=True the page reloads itself after rebuilds."""
    log.warnings.clear()
    log.where = ""
    install_assets(root)                       # html/deck.js, deck.css, MathJax
    install_latex(root)                        # titletemplates.sty
    config, slides, sources = convert(os.path.basename(tex), root)
    stamp = str(time.time_ns())
    if live:
        config["watch"], config["build"] = True, stamp

    tmp = out + ".tmp"                         # never leave a half-written deck
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(render_page(os.path.basename(tex), config, slides))
    os.replace(tmp, out)
    if live:                                   # tells an open deck to reload
        with open(os.path.join(root, "html", "build.js"), "w", encoding="utf-8") as f:
            f.write("window.TEX2HTML_BUILD = %r;\n" % stamp)

    prefix = "[%s] " % time.strftime("%H:%M:%S") if live else ""
    print("%swrote %s (%d slides)" % (prefix, os.path.relpath(out, root), len(slides)),
          flush=True)

    # what to watch: the sources, the images the slides use, and the tool's
    # own files that get installed into the project
    with open(out, encoding="utf-8") as f:
        used = referenced_files(f.read(), root, config)
    files = set(sources)
    files.update(os.path.join(root, p) for p in used
                 if p.split(os.sep)[0] != "html" and p != os.path.relpath(out, root))
    for folder in (ASSETS, LATEX):
        for dirpath, dirs, names in os.walk(folder):
            dirs[:] = [d for d in dirs if d != "vendor"]
            files.update(os.path.join(dirpath, n) for n in names)
    return files, config


def do_pack(dest, root, out, config, size=None):
    zip_path = os.path.abspath(dest) if dest else os.path.splitext(out)[0] + ".zip"
    if os.path.relpath(out, root).startswith(".."):
        log.warn("--pack: the HTML file must be inside the project folder; not packed")
        return
    count, size, _ = pack(root, out, zip_path, config, size)
    shown = os.path.relpath(zip_path)
    if shown.startswith(".."):
        shown = zip_path
    print("packed %s: %d files, %.1f MB -- unzip it and open %s/%s" % (
        shown, count, size / 1e6, os.path.splitext(os.path.basename(zip_path))[0],
        os.path.join(os.path.dirname(os.path.relpath(out, root)), "slides.html")))


def print_warnings():
    for w in log.warnings:
        print("warning:", w, file=sys.stderr)
