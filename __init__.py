"""beamer2html -- convert a beamer deck (main.tex + \\input files) into
slides.html, a self-contained HTML slide deck presented with html/deck.js +
html/deck.css, offline, in any modern browser.

    beamer2html                              # main.tex -> slides.html
    beamer2html main.tex -o talk.html        # (or: python3 path/to/beamer2html)

It understands the LaTeX of decks written with beamer2html.sty (its
templates, frames, lists, blocks, columns, figures, citations, math,
animations, plots, \\pause and overlay specifications), not LaTeX in
general. Anything it does not know is kept as plain text and reported as a
warning, so nothing disappears silently.

It also installs beamer2html.sty next to the .tex file (so the beamer build
has it too) and sets up everything the page needs in <project>/html/: the
slide engine (deck.js, deck.css, MathJax -- kept in assets/), references.js
from the \\addbibresource .bib files, and SVG / PNG copies of PDF figures
(browsers cannot show PDF images) in html/cache/.

Copyright (C) 2026 Arun Periyal. LaTeX Project Public License 1.3c or later.

Modules
    cli           command line; writes the output files
    watch         --watch: rebuild whenever a source file changes
    pack          --pack: zip of the deck and the files it uses
    assets        installs assets/ into html/ and beamer2html.sty into the project
    document      walks the document: preamble settings, sections, frames
    converter     Converter: block flow and inline text
    commands      LaTeX commands        (Converter mixin)
    environments  LaTeX environments    (Converter mixin)
    animation     animateinline         (Converter mixin)
    overlays      <overlay specs>, \\only, \\uncover, ... (Converter mixin)
    vocabulary    lookup tables and internal markers
    parsing       low-level readers for {args}, [opts], environments, \\item
    units         LaTeX lengths -> CSS
    source        reading .tex files with \\input expanded
    images        image lookup, PDF -> PNG
    bibliography  references.bib -> html/references.js
    page          the slides.html template
    log           warning collection
"""
__version__ = "1.0"
__date__ = "2026-11-12"

from .document import convert

__all__ = ["convert"]
