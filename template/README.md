# Starter deck

A complete example deck using every template of `titletemplates.sty`, with
placeholders to replace. Copy it to start a new presentation:

```sh
cp -r path/to/tex2html/template my-talk
cd my-talk
tex2html               # -> slides.html (installs titletemplates.sty and html/)
latexmk -pdf main.tex  # -> main.pdf
```

| File | Shows |
|------|-------|
| `main.tex` | all settings: title-slide fields, title bar / section name / footer switches, `\showdividers`, bibliography |
| `sections/01-introduction.tex` | bullets, citations, block, `\pause`, `\item<3->`, speaker notes, columns with a figure |
| `sections/02-research-progress.tex` | `progress` timeline |
| `sections/03-literature-review.tex` | `litreview` table |
| `sections/04-method.tex` | `rows` holding `columns` (grid), display math |
| `sections/05-results.tex` | `slidetable`; an `animateinline` example (commented out: needs frame images) |
| `sections/06-conclusion.tex` | numbered list, block |
| `sections/07-publications.tex` | `publications` with status badges |
| `references.bib` | placeholder entries |
| `figures/` | put images (and the logo, `figures/logo.png`) here |

Delete the sections you do not need and their `\input` lines in `main.tex`.
