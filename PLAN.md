# beamer2html — Plan

Working rules: `.claude/rules/working-with-the-owner.md`. Features as they are today: `README.md`.

## Stage 1 — YouTube embeds and automatic video posters

State today: `\slidevideo[opts]{file}` plays a local MP4/WebM (`commands.py:video`, `deck.js` "videos" section,
`.sty` "Videos"). In the PDF it is the `poster=` image or a grey box with the file name, linked with
`\href{run:…}` (or `\movie` with `multimedia`). Gaps: no online videos, and without `poster=` the PDF shows a box.

### A. YouTube (and Vimeo later) embeds

**Same command, a URL as the argument:** `\slidevideo[width=0.8\linewidth, start=30]{https://youtu.be/ID}`.
`\slidevideo<2->` and `\caption` in a figure work as they do for files. Accepted forms: `youtu.be/ID`,
`youtube.com/watch?v=ID`, `/embed/ID`, `/shorts/ID`; the id is checked (`[\w-]{11}`).

**HTML**
- `commands.py`: `video()` sees a YouTube URL and returns
  `<div class="video yt" data-yt="ID" data-start data-end data-autoplay data-loop data-muted style="width;aspect-ratio:16/9">`
  holding only a poster `<img>` and a play button (a facade). No `<iframe>` in the page, so no network on load and no
  cookies until someone clicks, and thumbnails and the overview strip stay light. Options keep their meaning:
  `width`, `height`, `poster`, `autoplay`, `loop`, `muted`, `controls`, `start`, `end`.
- `deck.js`: on play (click, `P`, or autoplay when the slide or step comes up) create the `<iframe>`
  `https://www.youtube-nocookie.com/embed/ID?enablejsapi=1&playsinline=1&rel=0&start=&end=&autoplay=1&mute=&controls=&loop=1&playlist=ID`.
  On leaving the slide pause it by `postMessage({event:"command",func:"pauseVideo"})`, and remove the iframe after a
  few slides away. `syncVideos()`/`videoShown()` are reused, so the step logic is the same as for files. `P` toggles.
  `deck.css`: `.video.yt` box, play button, iframe `border:0; width/height:100%`.
- Poster for the facade: `poster=` if given; else `https://i.ytimg.com/vi/ID/hqdefault.jpg` loaded lazily by the
  browser (so the deck shows a thumbnail online, and the grey box offline).
- Offline: the facade says "needs the internet" after a failed load (iframe `error`/timeout), and the link
  `https://youtu.be/ID` stays on it.
- `pack.py`: the URL is skipped by `referenced_files` (it already ignores `scheme:`); a given local `poster=` is
  packed. README states that embeds need the network.

**PDF** (`beamer2html.sty`)
- `\slidevideo{<URL>}` is recognised (`\str_if_in:nnT {#3} {://}` or `youtu`) and set as the same box as a file video:
  poster if given, else a box with a play sign and the short URL, linked with `\href{https://youtu.be/ID?t=start}`
  (a normal link: it opens in the browser; `\movie` is not used for online video).
- Poster in the PDF must be a local file (LaTeX can't download). Two ways to get one, both through task B:
  `poster=figures/x.png` by hand, or the converter fetching the thumbnail once with `--posters` (see B). With none,
  the box shows.
- `width`, `height`, `start` (in the link), and the overlay spec behave as for files; `autoplay`, `loop`, `muted`,
  `controls` are ignored in the PDF.

**Tasks**
- [x] `images.py`: `youtube_id(url)` (returns the id or None), unit-checked on the four URL forms and on bad input.
- [x] `commands.py`: `video()` branch for a YouTube id, `warn` on a bad id or on `controls=false` with an embed.
- [x] `deck.js` + `deck.css`: facade, lazy iframe, pause on leaving, `P`, step-aware autoplay, offline message.
- [x] `beamer2html.sty`: URL detection, link box, `start` in the link, header comment.
- [x] `template/`: a sample slide with an embed; README feature list and the offline note.
- [x] `nvim/` snippet `youtube`.

### B. Automatic poster from the video's first frame (ffmpeg)

The PDF can't run ffmpeg, so posters are made by the converter, written next to the project, and picked up by the
`.sty`, which already finds files by name.

- **Where:** `<dir>/<name>.poster.jpg` next to the video (e.g. `figures/flow.mp4` → `figures/flow.poster.jpg`). Not in
  `html/cache/`: LaTeX needs to see it, and it is plain output the owner can keep, replace or ignore (add it to
  `.gitignore` of their project if they want).
- **When:** `beamer2html main.tex --posters` (also with `--watch`). For each `\slidevideo` file without `poster=`
  and without an existing, newer `.poster.jpg`: `ffmpeg -ss <start or 1s> -i video -frames:v 1 -q:v 3 out.jpg`
  (frame at `start`, else 1 s in, else the first frame for a shorter clip; `ffprobe` gives the duration).
  Skipped when the poster is newer than the video. Output is the same size as the video, capped at 1280 px wide.
- **HTML:** `<video poster=…>` uses it, so the slide shows a frame before play (and the facade above uses the same for
  local files). `--pack` includes it (it's a `poster` attribute already covered by `referenced_files`).
- **PDF:** `.sty` `\__tt_video:n`: if `poster=` is empty, `\file_if_exist:nT {<basename>.poster.jpg}` sets it. Order:
  run `beamer2html --posters` once, then `latexmk`; before that the PDF shows the grey box as today. Documented.
- **Without ffmpeg:** `warn("ffmpeg not found: no video posters")` once, nothing else changes. No ffmpeg dependency
  in the install; `ffmpeg` found on `PATH`, `BEAMER2HTML_FFMPEG` overrides it (the Tecplot copy on the owner's
  machine may lack JPEG; check `ffmpeg -encoders | grep mjpeg`, fall back to PNG).
- **YouTube thumbnails** (same flag): for an embed without `poster=`, `--posters` downloads
  `https://i.ytimg.com/vi/ID/hqdefault.jpg` once to `figures/yt-ID.poster.jpg` (stdlib `urllib`, 10 s timeout,
  failure is a warning). This is the converter's only network access, only on `--posters`, and it sends nothing about
  the project. Decision log row below.

**Tasks**
- [x] `video_poster.py` (new): `make_poster(video, start) -> path|None`, `fetch_youtube_thumb(id) -> path|None`,
  freshness check, ffmpeg lookup; `cli.py`: `--posters` flag, run before the page is written.
- [x] `commands.py:video()` uses an existing `.poster.jpg` when `poster=` is absent (so HTML works without the flag
  after one run).
- [x] `.sty`: automatic `.poster.jpg` lookup; header comment.
- [x] README: "Posters" paragraph and the build order; `template/`: a sample with no `poster=`.
- [x] Check: template builds with and without ffmpeg on `PATH`, with `--pack`, with `--watch`; PDF shows the frame.

**Done 2026-11-21 (uncommitted; on `main`, so waiting for the owner's stage branch).** Changes from the plan above:
- The facade has **no remote thumbnail**: poster from `poster=`, else `html/cache/yt-ID.jpg` (from `--posters`), else a
  black box with a play button. So the page makes no request to YouTube until played (the earlier text said it would
  load `i.ytimg.com` lazily; that is a request at load, so it was dropped). The thumbnail cache is `html/cache/`, not
  `figures/`.
- `controls=false` is passed to YouTube as `controls=0` instead of warning (the click-to-toggle of file videos can't
  work inside an iframe).
- `youtube:ID` is also accepted. The id is checked in Python (`video_poster.youtube_id`) and in the `.sty`.
- Poster freshness: a poster newer than its video is kept, even if `start=` changed; delete it to remake.
- Ran: template copy in the scratchpad with `--posters` (poster 11 KB, thumbnail downloaded), `latexmk` with no errors,
  the PDF shows both posters and `/URI (https://youtu.be/jNQXAC9IVRw?t=2)`, `--pack` includes both, no ffmpeg gives the
  one warning, `node --check deck.js`. **Not run: the deck in a browser** (the Chrome extension was not connected), so
  the facade click, the iframe, pause on leaving the slide and `P` still need a manual look: open a built template deck,
  go to slide 17 ("Posters and YouTube").

### Decision log

| Date | Decision | Why |
|---|---|---|
| 2026-11-21 | YouTube via `youtube-nocookie.com`, an iframe created on play (facade) | No network or cookies at load; keeps the deck light and `file://`-safe |
| 2026-11-21 | Pause YouTube through the iframe `postMessage` API (`enablejsapi=1`), no `iframe_api` script | No third-party script; works from `file://` |
| 2026-11-21 | ffmpeg optional, called as a subprocess; posters written next to the video | LaTeX must see the file; no new Python dependency |
| 2026-11-21 | Network access only for `--posters` (YouTube thumbnail download) | The PDF needs a local image; opt-in flag, one GET per video |

### Open questions

1. Should `--posters` be on by default when ffmpeg exists (convenient; writes files into the project each run), or an
   explicit flag as planned (predictable)? Recommended: explicit flag.
2. (Answered: later.) Vimeo in the same stage, or later? It is the same facade with a different embed URL and thumbnail API; the
   recommendation is later, after YouTube works.
3. Poster location: `figures/x.poster.jpg` next to the video as planned, or a single `posters/` folder?
