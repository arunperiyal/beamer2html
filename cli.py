"""Command line:  tex2html [main.tex] [-o slides.html] [--pack [talk.zip]]"""
import argparse
import os
import sys

from . import __doc__ as package_doc
from .assets import install_assets, install_latex
from .document import convert
from .log import warn, warnings
from .pack import pack
from .page import render_page


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
    a = ap.parse_args(argv)

    tex = os.path.abspath(a.tex)
    root = os.path.dirname(tex)
    if not os.path.isfile(tex):
        ap.error("%s not found" % a.tex)
    install_assets(root)                       # html/deck.js, deck.css, MathJax
    install_latex(root)                        # titletemplates.sty
    config, slides = convert(os.path.basename(tex), root)

    out = a.output if os.path.isabs(a.output) else os.path.join(root, a.output)
    with open(out, "w", encoding="utf-8") as f:
        f.write(render_page(os.path.basename(tex), config, slides))
    print("wrote %s (%d slides)" % (os.path.relpath(out, root), len(slides)))

    if a.pack is not None:
        zip_path = os.path.abspath(a.pack) if a.pack else os.path.splitext(out)[0] + ".zip"
        if os.path.relpath(out, root).startswith(".."):
            warn("--pack: the HTML file must be inside the project folder; not packed")
        else:
            count, size, missing = pack(root, out, zip_path, config)
            shown = os.path.relpath(zip_path)
            if shown.startswith(".."):
                shown = zip_path
            print("packed %s: %d files, %.1f MB -- unzip it and open %s/%s" % (
                shown, count, size / 1e6,
                os.path.splitext(os.path.basename(zip_path))[0],
                os.path.relpath(out, root)))

    for w in warnings:
        print("warning:", w, file=sys.stderr)
    return 1 if not slides else 0
