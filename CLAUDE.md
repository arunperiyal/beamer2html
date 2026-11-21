# CLAUDE.md

Guidance for Claude Code (and humans) working in this repository.

## Project

**beamer2html** turns a Beamer `.tex` deck into a self-contained HTML slide deck (`slides.html` + `html/`), with the
PDF still built by LaTeX from the same source through `latex/beamer2html.sty`. Python, no dependencies for the
converter; the deck is `assets/deck.js` + `assets/deck.css` (MathJax and fonts vendored in `assets/vendor/`).

- **Plan, stages, decision log:** `PLAN.md`.
- **Features and options:** `README.md`. `\slidevideo`, `\slidevideo<2->`, plots, animations: see its feature list.

## Layout

- `cli.py`, `converter.py`, `document.py`, `page.py`: entry point and page assembly.
- `commands.py` (`\command`s), `environments.py` (`\begin{..}`), `overlays.py`, `animation.py`, `plot.py`, `tikz.py`.
- `images.py` (file lookup), `pack.py` (`--pack` zip), `assets.py`, `watch.py`.
- `latex/beamer2html.sty`: the PDF side of every command the converter understands.
- `template/`: a sample deck to try changes on. `nvim/`: the Neovim plugin. `ctan/`: CTAN packaging.

## Rules

- **Every command has two sides**: the converter's HTML and the `.sty`'s PDF. A change to one needs the other (or a
  line saying why not), and the header comment of the command in the `.sty` plus the README feature list.
- A missing file or bad option is a `warn(...)` (`log.py`), never a crash; the deck still builds.
- Anything the deck loads goes through `pack.py`'s `referenced_files`, so `--pack` stays complete. External URLs are
  skipped there; say so in the README when a feature needs the network.
- The HTML deck works offline and from `file://`: no fetches at load time, no build step, no CDN.
- New Python files stay dependency-free (standard library only). External tools (`ffmpeg`) are optional: the feature
  degrades with a warning when it's missing.

## Working notes for Claude

- The owner's standing rules (git, planning, their data, saving tokens) are in `.claude/rules/`. Read them first.
- Find the current stage in `PLAN.md`, reading only that part; tick items there when done.
- Don't add dependencies, tools or network access without a "Decision log" row in `PLAN.md`.
