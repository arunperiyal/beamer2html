# Working with the owner

The owner's standing rules. They apply to every session. (Ported from the RemoteTerm project, 2026-11-21, keeping the
parts that are not specific to Android.)

## Stages, tasks and git

- Work is planned in **stages** (`PLAN.md`, "Stages"): a few related tasks, one PR.
- **The owner does git**, except commits: the owner creates the stage's branch, pushes, opens the PR and merges.
  **Claude commits, one commit per task**, on the branch the owner made, and never creates branches, pushes, opens PRs,
  merges or rebases. If the current branch isn't the stage's (`git branch --show-current`), ask before committing.
  Only commit when asked or when the task list says so; planning and rules edits are not committed unprompted.
- **Never a git worktree**: work in the main folder, so the owner can build the branch there.
- A task, in order: code → a check on the template deck (`template/`) and a PDF build (`latexmk`) → README and
  `latex/beamer2html.sty` header comments updated → tick the item in `PLAN.md` (with what ran) → commit
  (Conventional Commits, the co-author line).
- Small requests from the owner mid-stage get their own commit and a PLAN entry, on the same branch.
- Report exactly what ran and what didn't; amend a local commit message that overstates.
- Stage files by name or `git add -A -- . ':!diagnose_claude.sh'`: `diagnose_claude.sh` is the owner's, untracked, and
  never committed.
- **Measure before choosing a fix when it's about speed.**

## Planning

- A plan is a file: `PLAN.md`, one section per stage, tasks as a checklist, an "Open questions" list and a decision
  log row for any new dependency, external tool or network access.
- Look at the code before planning; say what already exists. Recommend one approach, with the alternative in a line.
- Ask the open questions once, together.

## The owner's data

- The project folders under `/media/arunperiyal/Works/` hold the owner's real talks and papers: read what a task needs,
  never rewrite or delete their `.tex`, figures or PDFs. Test on `template/`, or a copy in the scratchpad.
- Don't commit generated output (`slides.html`, `html/cache/`, zips, `.aux`/`.log` files).

## Saving tokens

- **Read only what the task needs.** `latex/beamer2html.sty` (2500+ lines), `assets/deck.js` and `commands.py` are big:
  grep for the command or function, then read that range. Never read `assets/vendor/` (MathJax, fonts).
- Don't re-read a file you just wrote or edited; don't re-run a passing check without a change.
- Pipe long output through `tail`/`grep`, or into a scratchpad file and grep that (LaTeX logs especially).
- Ask once, with all questions together, instead of a question per turn. Reports are short: what changed, what ran,
  what's next.

## Shell notes

- zsh doesn't word-split `$var`: use a function or `${=var}`. A heredoc containing a line `EOF` ends early.
- `ffmpeg` here is the Tecplot copy (`/usr/local/tecplot/.../ffmpeg`) found first on `PATH`; `ffprobe` is `/usr/bin`.
  Check `ffmpeg -version` and the codecs it has before relying on one.
