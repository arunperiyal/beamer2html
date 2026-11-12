"""references.bib -> html/references.js (browsers cannot read a .bib file
from file://, so its text is wrapped in a script; deck.js parses it)."""
import os

from .log import warn


def bib_to_js(bibs, root):
    """Write html/references.js from the given .bib files (always written, so
    the page never refers to a missing file; empty when there are none)."""
    texts = []
    for bib in bibs:
        path = os.path.join(root, bib if bib.endswith(".bib") else bib + ".bib")
        if not os.path.isfile(path):
            warn("bibliography file not found: %s" % os.path.relpath(path, root))
            continue
        with open(path, encoding="utf-8") as f:
            texts.append(f.read().replace("`", "'"))
    os.makedirs(os.path.join(root, "html"), exist_ok=True)
    text = "\n".join(texts)
    bib = ", ".join(bibs) or "no .bib file"
    with open(os.path.join(root, "html", "references.js"), "w", encoding="utf-8") as f:
        f.write("// Generated from %s by beamer2html -- do not edit by hand.\n"
                "window.BIBTEX = String.raw`%s`;\n" % (bib, text))
