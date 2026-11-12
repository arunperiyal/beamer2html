# beamer2html

beamer2html turns a beamer presentation into a self-contained HTML slide deck
that runs offline in any modern browser. Animations, step-by-step reveals,
interactive plots, videos and speaker notes then work without depending on a
particular PDF viewer, and the same sources still give the PDF.

It has two parts:

- `beamer2html.sty`, a LaTeX package used in the beamer source: title slides,
  title bar and footer, row/column layout, tables, a progress timeline,
  publication and literature lists, shapes over figures, videos, plots from
  data files (pgfplots), animations from image sequences (animate) and
  flowchart styles for TikZ.
- `beamer2html`, a Python program that writes `slides.html` (with an
  `html/` folder of scripts, styles and MathJax) from that source. It can
  also pack the deck and exactly the files it uses into one zip for the
  presenting computer.

The HTML deck has step-by-step reveals, a presenter view (notes, next slide,
timer, touch controls), a slide grid, interactive plots and animation
controls. The program understands the LaTeX of decks written with
beamer2html.sty, not LaTeX in general; anything it does not know is kept as
plain text and reported as a warning.

## Contents

| Path | |
|------|---|
| `doc/beamer2html.pdf` | the manual (source: `doc/beamer2html.tex`) |
| `doc/example/` | a working deck that shows every element, one section each |
| `tex/beamer2html.sty` | the LaTeX package |
| `scripts/beamer2html/` | the program (run `python3 scripts/beamer2html`, or the launcher `beamer2html.py` in it) and the files it installs into a project (`assets/`: deck.js, deck.css, MathJax, fonts) |

## Requirements

Python 3.8 or later. Poppler (`pdftocairo`, `pdftoppm`) for PDF figures; a
TeX distribution (`pdflatex`, `pdfcrop`) and Ghostscript for TikZ pictures;
optionally Pillow for smaller images in packed decks. For the PDF: beamer,
tikz, pgfplots, animate and biblatex, as usual.

## License

Copyright (C) 2026 Arun Periyal.

This material is subject to the LaTeX Project Public License 1.3c or later
(https://www.latex-project.org/lppl.txt). It has the LPPL maintenance status
"maintained"; the Current Maintainer is Arun Periyal.

Bundled third-party files keep their own licenses: MathJax and its fonts
(Apache License 2.0, `scripts/beamer2html/assets/vendor/mathjax/LICENSE`) and
a WOFF2 subset of TeX Gyre Termes (GUST Font License,
`scripts/beamer2html/assets/vendor/fonts/termes/GUST-FONT-LICENSE.txt`).

## Links

Source and issues: https://github.com/arunperiyal/tex2html

Version 1.0, 2026-11-12.
