# tex2html

Converts a beamer presentation into a self-contained HTML slide deck that runs
offline in any modern browser — so animations, step-by-step reveals and speaker
notes work without depending on a particular PDF viewer.

It is built for decks that use the bundled `titletemplates.sty` (title slides,
title bar, footer, rows/columns, progress timeline, publications, literature
table). It understands that LaTeX, not LaTeX in general: anything unknown is
kept as plain text and reported as a warning.

## Usage

```sh
python3 path/to/tex2html                 # main.tex -> slides.html
python3 path/to/tex2html main.tex -o talk.html
python3 path/to/tex2html --pack talk.zip # also: zip for the presenting computer
```

`--pack` (default name: the HTML file's name with `.zip`) collects the deck,
`html/` and exactly the images and animation frames the slides use into a zip
that unpacks to one folder; open `slides.html` inside it. Sources, the `.bib`,
PDFs and unused figures are left out.

Run it in the folder with your `main.tex`. Each run also installs into that
project:

| Installed            | From                              |
|----------------------|-----------------------------------|
| `titletemplates.sty` | `latex/` (the beamer templates)   |
| `html/deck.js`, `html/deck.css`, `html/vendor/mathjax/` | `assets/` |
| `html/references.js` | the `\addbibresource` `.bib` file |
| `html/cache/*.png`   | PDF figures, converted with `pdftoppm` |

A project copy of `titletemplates.sty` that was edited in the project is kept as
`titletemplates.sty.bak` before being replaced. Make lasting changes here, in
`latex/` and `assets/`.

Build the PDF as usual with `latexmk -pdf main.tex` (biblatex + biber).

## Presenting

Open `slides.html` and use:

| Key | Action |
|-----|--------|
| → ↓ Space PgDn / ← ↑ PgUp | next / previous step or slide |
| Home / End, *number* Enter | first / last / go to slide |
| F | fullscreen |
| S | presenter view: notes, next slide, timer (second window) |
| P | play / pause the animation on the slide |
| H | help |

Copy the `--pack` zip (or the whole project folder) to the presenting computer.
Ctrl+P → Save as PDF gives a static backup, one page per slide.

## Supported LaTeX

- `titletemplates.sty`: `\Set…` fields, `\SeminarTitleFrame`, `\ConferenceTitleFrame`,
  `\OverviewFrame`, `\ReferencesFrame`, `\ThankYouFrame`, `\TitleBarOn/Off`,
  `\SetTitleHeight`, `\SectionNameOn/Off`, `\FooterOn/NumberOnly/Off`,
  `\showdividers`/`\hidedividers`, `rows`/`row`, `progress`/`\task`,
  `publications`/`\pub`/`\pubtext`/`\pubsection`, `litreview`/`\study`/`\studytext`,
  `\FigurePlaceholder`
- beamer: frames (`[t]`, `[plain]`, `\frametitle`), `\section`, `\pause`, overlay
  specifications (`\item<2->`, `[<+->]`, `\only`, `\uncover`, `\visible`,
  `\invisible`, `\alt`, `\onslide`, environments with `<…>`), `columns`, `block`,
  `\note`, class font size option
- LaTeX: lists, `minipage`, `center`, `tabular`, math (MathJax), `\includegraphics`,
  font sizes/styles, `\color`, `\cite`, `\href`, `\def`/`\newcommand` without arguments
- `animate`: `animateinline` + `\multiframe` (synchronised panels, `controls` option)

Not supported: TikZ drawings (export them as images), commands with arguments
defined in the document, `\alert<…>`.

## Code layout

| Module | Role |
|--------|------|
| `cli.py`, `__main__.py` | command line |
| `document.py` | preamble settings, sections, frames, template slides |
| `converter.py` | core: inline text and block flow |
| `commands.py`, `environments.py`, `animation.py`, `overlays.py` | LaTeX commands, environments, animations, overlay specs |
| `vocabulary.py`, `parsing.py`, `units.py`, `source.py`, `images.py`, `bibliography.py`, `page.py`, `log.py` | helpers |
| `assets.py` | installs `assets/` and `latex/` into projects |
| `pack.py` | `--pack`: zip of the deck and the files it uses |
| `assets/` | browser side: `deck.js`, `deck.css`, MathJax 2 (Apache-2.0, see `vendor/mathjax/COPYRIGHT`) |
| `latex/titletemplates.sty` | the beamer templates |

Requires Python 3.8+; `pdftoppm` (poppler) for PDF figures.
