"""tex2html -- convert this project's beamer deck (main.tex + sections/*.tex)
into slides.html, which is presented with html/deck.js + html/deck.css.

    python3 tools/tex2html                     # main.tex -> slides.html
    python3 tools/tex2html main.tex -o slides.html

It understands the LaTeX used in this deck (titletemplates.sty commands,
frames, lists, blocks, columns, figures, citations, math, animateinline,
\\pause and overlay specifications), not
LaTeX in general. Anything it does not know is kept as plain text and reported
as a warning, so nothing disappears silently.

It also installs titletemplates.sty next to the .tex file (kept in
tools/tex2html/latex/, so the beamer build has it too) and sets up everything
the page needs in <project>/html/: the slide engine (deck.js, deck.css,
MathJax -- kept in tools/tex2html/assets/),
references.js from the \\addbibresource .bib files, and PNG copies of PDF
figures (browsers cannot show PDF images) in html/cache/.

Modules
    cli           command line; writes the output files
    assets        installs assets/ into html/ and latex/*.sty into the project
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
from .document import convert

__all__ = ["convert"]
