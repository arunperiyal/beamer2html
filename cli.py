"""Command line:  python3 tools/tex2html [main.tex] [-o slides.html]"""
import argparse
import os
import sys

from . import __doc__ as package_doc
from .assets import install_assets, install_latex
from .document import convert
from .log import warnings
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
    for w in warnings:
        print("warning:", w, file=sys.stderr)
    return 1 if not slides else 0
