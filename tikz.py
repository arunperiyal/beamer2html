"""TikZ pictures -- mixin for Converter.

    \\begin{tikzpicture} ... \\end{tikzpicture}     \\tikz ... ;   \\tikz{...}

TikZ is drawn by LaTeX itself: each picture is compiled on its own, in a
plain beamer frame with the deck's preamble (same class options, fonts,
colours, libraries and \\tikzset styles), so the HTML shows exactly what the
PDF shows. Every overlay of that frame becomes one SVG; the deck shows the
one of the current step (\\node<2->, visible on=<3->, \\pause, <+-> ...).
The frame starts at the step the picture has on the real slide, so specs
and \\pause continue the slide's own count.

    pdflatex   one page per overlay
    gs         inked area of each page; all pages are cropped to their union,
               so the picture keeps its size from step to step
    pdfcrop    the crop
    pdftocairo each page -> SVG (consecutive identical pages are merged)

Results are cached in html/cache/tikz-<hash>* (the hash covers the picture,
the preamble and the starting step); cache files of pictures no longer in
the deck are removed at the end of a run.
"""
import glob
import hashlib
import html
import json
import os
import re
import shutil
import subprocess
import tempfile

from .log import warn
from .parsing import find_end, read_group, read_opt, skip_ws
from .units import length_css
from .vocabulary import PAUSE

VERSION = "1"                     # part of the cache key: bump when output changes
CACHE = os.path.join("html", "cache")
MARGIN = 0.5                      # pt around the inked area

# preamble packages left out of a picture's document: bibliography, the
# animation engine (slow, and nothing to draw), hyperlinks (beamer has them)
SKIP_PACKAGES = {"biblatex", "natbib", "animate", "hyperref"}


def diagram_preamble(pre):
    """The deck's preamble for compiling a picture: its \\documentclass options
    (but not handout, which would merge the overlays), without the packages
    in SKIP_PACKAGES and \\addbibresource."""
    m = re.search(r"\\documentclass\s*(?:\[([^\]]*)\])?\s*\{[^}]*\}", pre)
    opts = [o.strip() for o in (m.group(1) or "").split(",")] if m else []
    opts = [o for o in opts if o and o != "handout"]
    body = pre[m.end():] if m else pre

    def package(mm):
        names = [n.strip() for n in mm.group(2).split(",")]
        keep = [n for n in names if n and n not in SKIP_PACKAGES]
        if not keep:
            return ""
        return "\\usepackage%s{%s}" % (mm.group(1) or "", ",".join(keep))
    body = re.sub(r"\\usepackage\s*(\[[^\]]*\])?\s*\{([^}]*)\}", package, body)
    body = re.sub(r"\\addbibresource\s*(\[[^\]]*\])?\s*\{[^}]*\}", "", body)
    return "\\documentclass[%s]{beamer}\n%s" % (",".join(opts), body.strip())


def local_packages(pre, root):
    """Fingerprint of the project's own packages in the preamble (e.g.
    beamer2html.sty with the flow styles): editing one re-draws the
    pictures."""
    h = hashlib.sha1()
    for group in re.findall(r"\\usepackage\s*(?:\[[^\]]*\])?\s*\{([^}]*)\}", pre):
        for name in group.split(","):
            path = os.path.join(root, name.strip() + ".sty")
            if os.path.isfile(path):
                with open(path, "rb") as f:
                    h.update(f.read())
    return h.hexdigest()


# after the deck's preamble: nothing on the page but the picture
SETUP = r"""
\ifdefined\hidedividers\hidedividers\fi
\setbeamertemplate{navigation symbols}{}
\setbeamercolor{background canvas}{bg=}
\makeatletter
\def\ttdiagramend{\immediate\typeout{TT-PAUSES=\the\c@beamerpauses}}
\makeatother
"""


def find_tool(*names):
    for n in names:
        if shutil.which(n):
            return n
    return None


class TikzMixin:
    pauses = 0                    # \pause's so far in the current frame
    tikz_preamble = None          # set by document.convert
    tikz_deps = ""                # local_packages(): part of the cache key
    tikz_used = None              # cache keys of this run's pictures
    tikz_missing = False          # tools missing: warned once

    def tikz_env(self, body):
        return self.tikz_picture("\\begin{tikzpicture}%s\\end{tikzpicture}" % body)

    def tikz_command(self, s, i):
        """\\tikz[opts]{...} or \\tikz[opts] path ... ; -> (html, index)."""
        _, j = read_opt(s, i)
        k = skip_ws(s, j)
        if k < len(s) and s[k] == "{":
            _, end = read_group(s, k)
        else:                                     # up to the ; ending the path
            depth, end = 0, k
            while end < len(s):
                c = s[end]
                if c == "\\":
                    end += 2
                    continue
                if c in "{[":
                    depth += 1
                elif c in "}]":
                    depth -= 1
                end += 1
                if c == ";" and depth == 0:
                    break
        return self.tikz_picture("\\tikz" + s[i:end]), end

    def tikz_picture(self, src):
        """HTML for one picture: an <img> per distinct overlay, each shown on
        its steps; then a \\pause marker for each \\pause inside the picture,
        so what follows it on the slide waits as in beamer."""
        start = 1 + self.pauses + self.plus           # beamer's pause counter here
        inner_pauses = len(re.findall(r"\\pause(?![A-Za-z])", src))
        meta = self.tikz_render(src, start)
        if meta is None:
            return ('<div class="figure-placeholder">TikZ picture not converted '
                    '-- see the warning in the terminal</div>')
        # beamer's counter after the picture: \pause's are markers below,
        # the rest (<+->) continues the slide's `+`
        self.plus += max(0, meta["end"] - start - inner_pauses)
        self.pauses += inner_pauses
        width = length_css("%gpt" % meta["w"])
        runs = meta["runs"]
        imgs = []
        for n, (a, b, name) in enumerate(runs):
            spec = ""
            if len(runs) > 1:
                last = n == len(runs) - 1
                spec = "%d-" % a if last else ("%d" % a if a == b else "%d-%d" % (a, b))
                spec = ' data-spec="%s" data-mode="only"' % spec
            imgs.append('<img src="%s" alt=""%s>' % (
                html.escape(os.path.join(CACHE, name).replace(os.sep, "/")), spec))
        return ('<span class="tikz" style="width:%s">%s</span>' % (width, "".join(imgs))
                + PAUSE * inner_pauses)

    def tikz_render(self, src, start):
        """Compile (or take from the cache) one picture. Returns its metadata
        {w, h, runs: [[first overlay, last overlay, svg file]], end} or None."""
        key = hashlib.sha1("\n".join(
            (VERSION, self.tikz_preamble or "", self.tikz_deps, str(start), src)
        ).encode()).hexdigest()[:16]
        if self.tikz_used is not None:
            self.tikz_used.add(key)
        cache = os.path.join(self.root, CACHE)
        meta_path = os.path.join(cache, "tikz-%s.json" % key)
        if os.path.isfile(meta_path):
            with open(meta_path, encoding="utf-8") as f:
                meta = json.load(f)
            if all(os.path.isfile(os.path.join(cache, r[2])) for r in meta["runs"]):
                return meta

        engine = "lualatex" if re.search(r"\\usepackage\s*(\[[^\]]*\])?\s*\{[^}]*"
                                         r"\b(fontspec|unicode-math)\b", self.tikz_preamble or "") \
            else "pdflatex"
        tools = {"tex": find_tool(engine), "gs": find_tool("gs", "gswin64c", "gswin32c"),
                 "crop": find_tool("pdfcrop"), "svg": find_tool("pdftocairo")}
        if not all(tools.values()):
            if not TikzMixin.tikz_missing:
                warn("TikZ pictures need %s, Ghostscript (gs), pdfcrop and pdftocairo "
                     "(missing: %s)" % (engine, ", ".join(
                         {"tex": engine, "gs": "gs", "crop": "pdfcrop", "svg": "pdftocairo"}[k]
                         for k, v in tools.items() if not v)))
                TikzMixin.tikz_missing = True
            return None

        os.makedirs(cache, exist_ok=True)
        tmp = tempfile.mkdtemp(prefix=".tikz-build-", dir=cache)
        try:
            return self.tikz_compile(src, start, key, tools, tmp, cache, meta_path)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def tikz_compile(self, src, start, key, tools, tmp, cache, meta_path):
        doc = "%s\n%s\n\\begin{document}\n\\begin{frame}[plain]\n" \
              "\\setcounter{beamerpauses}{%d}\n%s\n\\ttdiagramend\n\\end{frame}\n" \
              "\\end{document}\n" % (self.tikz_preamble or "\\documentclass{beamer}"
                                     "\n\\usepackage{tikz}", SETUP, start, src)
        tex = os.path.join(tmp, "d.tex")
        with open(tex, "w", encoding="utf-8") as f:
            f.write(doc)
        log_path = os.path.join(tmp, "d.log")
        try:                                       # from the project folder: its
            subprocess.run([tools["tex"], "-interaction=nonstopmode", "-halt-on-error",
                            "-output-directory", tmp, tex], cwd=self.root,   # .sty, images
                           capture_output=True, timeout=180, check=True)
        except subprocess.TimeoutExpired:
            warn("TikZ picture: %s took too long (over 3 minutes)" % tools["tex"])
            return None
        except subprocess.CalledProcessError:
            kept = os.path.join(cache, "tikz-%s.log" % key)
            if os.path.isfile(log_path):
                shutil.copy(log_path, kept)
            warn("TikZ picture could not be compiled: %s (full log: %s)"
                 % (tex_error(log_path), os.path.relpath(kept, self.root)))
            return None
        with open(log_path, encoding="utf-8", errors="replace") as f:
            m = re.search(r"TT-PAUSES=(\d+)", f.read())
        end = int(m.group(1)) if m else start
        pdf = os.path.join(tmp, "d.pdf")

        # inked area of every page; all pages are cropped to their union
        r = subprocess.run([tools["gs"], "-q", "-dNOPAUSE", "-dBATCH", "-sDEVICE=bbox", pdf],
                           capture_output=True, text=True)
        boxes = [tuple(map(float, b)) for b in re.findall(
            r"%%HiResBoundingBox:\s*([-\d.]+)\s+([-\d.]+)\s+([-\d.]+)\s+([-\d.]+)", r.stderr)]
        boxes = [b for b in boxes if b[2] > b[0] and b[3] > b[1]]     # empty pages
        if not boxes:
            warn("TikZ picture draws nothing")
            return None
        x0, y0 = min(b[0] for b in boxes) - MARGIN, min(b[1] for b in boxes) - MARGIN
        x1, y1 = max(b[2] for b in boxes) + MARGIN, max(b[3] for b in boxes) + MARGIN
        cropped = os.path.join(tmp, "c.pdf")
        subprocess.run([tools["crop"], "--bbox", "%g %g %g %g" % (x0, y0, x1, y1),
                        pdf, cropped], capture_output=True, check=True)

        # one SVG per page; consecutive identical pages are one run
        pages = int(re.search(r"Pages:\s*(\d+)", subprocess.run(
            ["pdfinfo", cropped], capture_output=True, text=True).stdout).group(1))
        runs, prev = [], None
        for p in range(1, pages + 1):
            out = os.path.join(tmp, "p%d.svg" % p)
            subprocess.run([tools["svg"], "-svg", "-f", str(p), "-l", str(p), cropped, out],
                           capture_output=True, check=True)
            with open(out, "rb") as f:
                data = f.read()
            if data == prev:
                runs[-1][1] = p
                continue
            name = "tikz-%s-%d.svg" % (key, p)
            shutil.move(out, os.path.join(cache, name))
            runs.append([p, p, name])
            prev = data
        meta = {"w": round(x1 - x0, 2), "h": round(y1 - y0, 2), "runs": runs, "end": end}
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(meta, f)
        return meta


def tex_error(log_path):
    """The first error of a LaTeX log, with its line, in one line."""
    try:
        with open(log_path, encoding="utf-8", errors="replace") as f:
            log = f.read()
    except OSError:
        return "no log written"
    m = re.search(r"^! (.*)$", log, re.M)
    if not m:
        return "unknown error"
    msg = [m.group(1).strip()]                 # messages wrap over several lines
    for ln in log[m.end():].lstrip("\n").splitlines():
        if not ln.strip() or re.match(r"(See the|Type |l\.\d+|\(\w+\)\s*$)", ln):
            break
        msg.append(ln.strip())
    msg = " ".join(msg)
    line = re.search(r"^l\.\d+ (.*)$", log[m.end():], re.M)
    if line and "\\end{frame}" not in line.group(1):
        msg += " (at: %s)" % line.group(1).strip()
    return msg


def clean_cache(root, used):
    """Remove the cache files of pictures that are no longer in the deck."""
    for path in glob.glob(os.path.join(root, CACHE, "tikz-*")):
        m = re.match(r"tikz-([0-9a-f]{16})", os.path.basename(path))
        if m and m.group(1) not in used and os.path.isfile(path):
            os.remove(path)
