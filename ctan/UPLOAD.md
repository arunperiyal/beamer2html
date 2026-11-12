# Uploading beamer2html to CTAN

1. Build the package (needs `pdflatex` for the manual):

   ```sh
   python3 ctan/build.py
   ```

   It checks that the version and date agree in `__init__.py`,
   `latex/beamer2html.sty` and `ctan/doc/beamer2html.tex`, then writes
   `ctan/build/beamer2html/` (look through it) and
   `ctan/build/beamer2html.zip` (upload this).

2. Open https://ctan.org/upload and fill in the form with the values below.
   Attach `ctan/build/beamer2html.zip`.

3. The CTAN team replies by email; answer their questions there. After it is
   accepted, the package appears at https://ctan.org/pkg/beamer2html and an
   announcement goes out if you asked for one.

For a new version: raise `__version__` / `__date__` in `__init__.py`, the
`\ProvidesPackage` line in `latex/beamer2html.sty` and the title and
`\date` of `ctan/doc/beamer2html.tex` (plus an entry under "Changes" there),
build again and upload the whole package again with the same form.

## Form values

| Field | Value |
|-------|-------|
| Name of the contribution | `beamer2html` |
| Version | `1.0` |
| Author | Arun Periyal |
| Uploader email | your email address |
| Summary | Convert beamer presentations into offline HTML slide decks |
| Suggested CTAN directory | `/macros/latex/contrib/beamer-contrib/beamer2html` or `/support/beamer2html` (the team decides) |
| License | LaTeX Project Public License 1.3c (bundled: Apache License 2.0 for MathJax, GUST Font License for the TeX Gyre Termes subset) |
| Home page | https://github.com/arunperiyal/beamer2html |
| Bug tracker | https://github.com/arunperiyal/beamer2html/issues |
| Repository | https://github.com/arunperiyal/beamer2html |
| Topics (suggestion) | presentation, beamer, HTML, conversion, animation |

### Description

> beamer2html turns a beamer presentation into a self-contained HTML slide
> deck that runs offline in any modern browser, so animations, step-by-step
> reveals, interactive plots, videos and speaker notes work without depending
> on a particular PDF viewer; the same sources still give the PDF. It
> consists of beamer2html.sty, a package with title slides, title bar and
> footer, layout, tables, plots from data files (pgfplots), animations from
> image sequences (animate), shapes over figures, videos and flowchart styles,
> and beamer2html, a Python program that writes the HTML deck from that
> source and can pack it with exactly the files it uses into one zip. The
> HTML deck has a presenter view with notes and touch controls, a slide grid,
> interactive plots and animation controls.

### Notes to the CTAN team

> beamer2html has a LaTeX package (tex/beamer2html.sty) and a Python 3
> program (scripts/beamer2html/, a package folder). The program can be run as
> `python3 scripts/beamer2html` or through the launcher
> scripts/beamer2html/beamer2html.py, which follows symlinks, so a
> distribution can link it as the `beamer2html` command. It finds
> beamer2html.sty next to itself or via kpsewhich.
>
> scripts/beamer2html/assets/ holds the files the program copies into each
> converted deck. They include MathJax 4.1 with its fonts (Apache-2.0, license
> file included) and a WOFF2 subset of TeX Gyre Termes (GUST Font License,
> license file included). Both are bundled on purpose: the decks must work
> offline, opened from a local file, where browsers cannot load fonts or
> scripts from elsewhere. If you would rather not have them in the package,
> please tell me how you would like this handled.
>
> doc/example/ is a working example deck (sources and small sample images);
> doc/beamer2html.pdf is the manual, with its source.
>
> The package was called tex2html (with titletemplates.sty) during
> development; it was never on CTAN under that name.
