# Starter deck and tutorial

A working deck that shows every element of `titletemplates.sty`, one
section per element. Each slide is a live example, and the comments above
each frame in the `.tex` files list the options. Copy it to start a new
presentation:

```sh
cp -r path/to/tex2html/template my-talk
cd my-talk
tex2html               # -> slides.html (installs titletemplates.sty and html/)
latexmk -pdf main.tex  # -> main.pdf
```

| File | Shows |
|------|-------|
| `main.tex` | all settings: title-slide fields, title bar / section name / footer switches, margins, caption size, `\showdividers`, bibliography |
| `sections/01-text.tex` | `itemize`, `enumerate`, `description`, text styles and sizes, math (`align`), `block` |
| `sections/02-layout.tex` | `columns`, `rows` holding columns (a grid), `\SetTextMargins` between frames |
| `sections/03-figures.tex` | `figure` + `\caption` + `\label` / `\ref` (PDF and PNG figures), `\FigurePlaceholder`, `slideplot` (interactive plot from a CSV file; panels with shared axes) |
| `sections/04-tables.tex` | `slidetable` in its four styles: `plain`, `lines`, `header`, `striped` |
| `sections/05-animations.tex` | `animation` with panels in one row and in a grid (`columns=2`), `dt`, `timebar`, `controls=hover`, `subcaptions` |
| `sections/06-shapes.tex` | `annotate` + `\shape` over a figure (with `grid`, overlays), `\slideshape`, `\slidegrid` |
| `sections/07-overlays.tex` | `\item<2->`, `\only`, `\uncover`, `\alt`, `\pause` |
| `sections/08-citations.tex` | `\cite`, `\textcite`, `\citeauthor`, `litreview` table |
| `sections/09-research.tex` | `progress` timeline, `publications` with status badges |
| `sections/10-slide-options.tex` | `\TitleBarOff`, `\FooterNumberOnly` between frames, speaker notes (`\note`) |
| `references.bib` | placeholder entries |
| `figures/` | sample images (`make_samples.py` regenerates them); put your own figures and the logo (`figures/logo.png`) here |

To make it your own: fill in the `[placeholders]` in `main.tex`, write your
sections (copy the frames you need from the tutorial ones), change the
`\input` lines, and delete the tutorial sections and the sample figures.

`\cmd{name}` (used on these slides) prints `\name` in typewriter type, for
slides that talk about LaTeX commands.
