# tex2html

Converts a beamer presentation into a self-contained HTML slide deck that runs
offline in any modern browser — so animations, step-by-step reveals and speaker
notes work without depending on a particular PDF viewer.

It is built for decks that use the bundled `titletemplates.sty` (title slides,
title bar, footer, rows/columns, progress timeline, publications, literature
table). It understands that LaTeX, not LaTeX in general: anything unknown is
kept as plain text and reported as a warning.

## Starting a new deck

```sh
cp -r path/to/tex2html/template my-talk     # tutorial deck: every element, one section each
```

See [`template/README.md`](template/README.md).

## Usage

```sh
python3 path/to/tex2html                 # main.tex -> slides.html
python3 path/to/tex2html main.tex -o talk.html
python3 path/to/tex2html --pack talk.zip # also: zip for the presenting computer
python3 path/to/tex2html --watch         # rebuild on every change (like latexmk -pvc)
```

`--watch` (`-w`) keeps running and rebuilds whenever `main.tex`, an `\input`
file, the `.bib`, an image the slides use, or the tool's own `deck.js` /
`deck.css` / `titletemplates.sty` changes. An open deck built this way reloads
itself and stays on the same slide and step. A failed build leaves the last
good `slides.html` in place. Ctrl+C stops it. For the PDF, run
`latexmk -pdf -pvc main.tex` alongside.

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
| `html/cache/*.svg`, `*.png` | PDF figures: vector ones as SVG (`pdftocairo`, sharp at any size), ones with embedded bitmaps as PNG (`pdftoppm`, at least 2000 px on the longer side) |

A project copy of `titletemplates.sty` that was edited in the project is kept as
`titletemplates.sty.bak` before being replaced. Make lasting changes here, in
`latex/` and `assets/`.

Build the PDF as usual with `latexmk -pdf main.tex` (biblatex + biber).

## Neovim plugin

`nvim/` is a Neovim plugin (0.10+): build and watch in the background,
warnings in the quickfix list at their slide, and the browser opened at — or
moved to — the slide under the cursor. Add the folder to the runtime path:

```lua
vim.opt.rtp:append("path/to/tex2html/nvim")   -- then :helptags path/to/tex2html/nvim/doc
```

| Command | Mapping | |
|---------|---------|---|
| `:Tex2Html` | `<localleader>mb` | build (warnings → quickfix) |
| `:Tex2HtmlWatch` | `<localleader>mw` | watch on/off |
| `:Tex2HtmlOpen` | `<localleader>mo` | open the deck at the cursor's slide |
| `:Tex2HtmlSync` | `<localleader>ms` | move the open deck to the cursor (while watching) |
| `:Tex2HtmlPack [zip]` | `<localleader>mp` | zip for presenting |
| `:Tex2HtmlLog` | `<localleader>ml` | show the output |
| `:Tex2HtmlNew {dir}` | | new deck from `template/` |

`require("tex2html").setup{ autosync = true }` makes a watched deck follow the
cursor. With LuaSnip, snippets for the templates are added (`frame`, `cols`,
`rows`, `block`, `stab`, `lit`, `prog`, `pubs`, `note`, `fig`, `anim`, ...).
See `:help tex2html`.

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
| swipe left / right | next / previous step or slide (touch screens) |
| tap right / left third | next / previous; a tap on an animation plays / pauses it |

On a phone or tablet, open the deck through a web server rather than as a
file (browsers there do not load `html/` and `figures/` next to a local
file): `python3 -m http.server 8000` in the deck folder, then
`http://<computer's IP>:8000/slides.html` on the device (same Wi-Fi).

Copy the `--pack` zip (or the whole project folder) to the presenting computer.
Ctrl+P → Save as PDF gives a static backup, one page per slide.

## Supported LaTeX

- `titletemplates.sty`: `\Set…` fields, `\SeminarTitleFrame`, `\ConferenceTitleFrame`,
  `\OverviewFrame`, `\ReferencesFrame`, `\ThankYouFrame`, `\TitleBarOn/Off`,
  `\SetTitleHeight`, `\SectionNameOn/Off`, `\FooterOn/NumberOnly/Off`,
  `\SetTextMargins{left}{right}` (slide body; also between frames — beamer's
  `\setbeamersize{text margin left=…}` is read too, preamble only),
  `\SetBarMargin{len}` (title bar and footer), `\SetCaptionSize{\footnotesize}`
  (or beamer's `\setbeamerfont{caption}{size=…}`; preamble), `\slidetablestretch`,
  `\showdividers`/`\hidedividers`, `rows`/`row`, `progress`/`\task`,
  `publications`/`\pub`/`\pubtext`/`\pubsection`, `litreview`/`\study`/`\studytext`,
  `slidetable` (styles `plain`, `lines`, `header`, `striped`; first row = header;
  `p{3cm}`/`m{..}`/`b{..}` column widths carry over to the HTML),
  `\FigurePlaceholder`; a long `\ReferencesFrame` list continues on
  "References (cont.)" slides, in the PDF and the HTML
- shapes: `\begin{annotate}[grid] … \end{annotate}` around an image/table with
  `\shape<spec>[options]{kind}{x1,y1}{x2,y2}` lines (fractions of the element,
  origin bottom left), `\slideshape` (fractions of the slide) and `\slidegrid`.
  Kinds `rect`, `ellipse`/`circle`, `line`, `arrow`, `text` (`{x,y}{text}`),
  `axes` (`{x,y}{length}`: a coordinate indicator with `xlabel`, `ylabel`,
  `zlabel` for an oblique z axis, `oblique` its angle from x (225), `rotate`;
  an empty label leaves that axis out, e.g. `ylabel=, zlabel=$z$, oblique=45`);
  options `color` (xcolor, e.g. `green!60!black`), `width`, `fill`, `opacity`,
  `dashed`, `rounded`, `label`, `labelpos`, `textsize`; for `text`, `fill` is a
  background (opaque by default) and `border` (or `border=<colour>`) a frame.
  The grid (0.1 steps; also on while `\showdividers`) helps read off
  coordinates. Shapes never change the layout. Shapes and slide shapes stay
  visible over an animation in the PDF too (drawn as a read-only stamp
  annotation on pages with an animation; pdfLaTeX).
- beamer: frames (`[t]`, `[plain]`, `\frametitle`), `\section`, `\pause`, overlay
  specifications (`\item<2->`, `[<+->]`, `\only`, `\uncover`, `\visible`,
  `\invisible`, `\alt`, `\onslide`, environments with `<…>`), `columns`, `block`,
  `\note`, class font size option
- LaTeX: `figure` / `table` with `\caption` ("Figure n:", numbered through the deck),
  `\label` and `\ref` (also forward references), lists, `minipage`, `center`,
  `tabular`, math (MathJax 4, in a Times font when the preamble loads `newtxmath`,
  `mathptmx`, `txfonts` or `times`, else New Computer Modern), `\includegraphics`,
  font sizes/styles, `\color`, `\cite`, `\textcite`/`\citet`, `\citeauthor`, `\href`, `\def`/`\newcommand` without arguments
- animations: `animation` environment with `\animpanel{label}{path_\N}` lines
  (`frames=first:last:step`, `fps`, `width`, `controls` — including `hover`:
  buttons only on mouse-over in HTML, none in PDF — `autoplay`, `loop`,
  `subcaptions`, `dt` to show the time (frame number × dt) below the panels
  with `timelabel`, `timedigits`, `timeunit`, `time=false` to hide that value
  (the timebar keeps its end times), `timebar` for a progress bar
  under the panels (clickable in HTML), `columns=N` for rows of N panels
  (each label on its panel), `\animpanel[frames=a:b:s, dt=]` for a panel with
  its own range (each panel then shows its own time); put it in a `figure` for a
  caption), and `animate`'s own
  `animateinline` + `\multiframe` (synchronised panels, `controls` option)

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
| `watch.py` | `--watch`: rebuild on change (the page side is in `deck.js`) |
| `assets/` | browser side: `deck.js`, `deck.css`, MathJax 4.1 with its Termes and New Computer Modern fonts (all Apache-2.0, see `vendor/mathjax/LICENSE`) |
| `latex/titletemplates.sty` | the beamer templates |
| `template/` | starter deck using every template |
| `nvim/` | Neovim plugin (`plugin/`, `lua/tex2html/`, `doc/`) |

Requires Python 3.8+; poppler (`pdftocairo`, `pdftoppm`, `pdfimages`, `pdfinfo`) for PDF figures.
