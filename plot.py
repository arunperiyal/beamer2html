"""slideplot environment (beamer2html.sty) -> an interactive plot drawn by
html/deck.js -- mixin for Converter.

    \\begin{slideplot}[xlabel={$t$}, ylabel={$y/D$}, height=5cm]
      \\plotline[x=time, y=aleDisp_y, label={$U_r = 4$}]{data/U4/data_dy.csv}
      \\plotline<2->[x=time, y=aleDisp_y, label={$U_r = 6$}]{data/U6/data_dy.csv}
    \\end{slideplot}

Panels side by side or stacked, with shared axes and one legend:

    \\begin{slideplot}[rows=2, xlabel={$t$}, legend=outer east]
      \\plotpanel[ylabel={$y/D$}]
        \\plotline[x=time, y=disp, label=Helical]{data/helical.csv}
      \\plotpanel[ylabel={$C_L$}]
        \\plotline[x=time, y=cl, label=Helical]{data/helical.csv}
    \\end{slideplot}

The data files are read here and their columns embedded in the page (a deck
opened as a file cannot load them itself); the PDF plots the same files with
pgfplots.
"""
import html
import json
import os
import re

from .colors import css_color
from .log import warn
from .parsing import keyvals, read_arg, read_opt
from .units import length_css
from .vocabulary import PARA

SEPARATORS = {"comma": ",", "semicolon": ";", "tab": "\t", "space": None}
LEGEND = ("north east", "north west", "south east", "south west", "outer east", "outer north",
          "none")
LINE_STYLES = ("solid", "dashed", "dotted")
SHARES = ("x", "y", "both", "none")
TOO_MANY = 200000       # points in one plot: warn, the page gets large


def read_table(path, sep):
    """Rows of a data file: (header names or None, rows of strings). Lines
    starting with # or % are comments; the first row is a header when it is
    not all numbers (as pgfplots decides)."""
    rows = []
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line or line[0] in "#%":
                continue
            rows.append([c.strip() for c in (line.split(sep) if sep else line.split())])
    header = None
    if rows and not all(number(c) is not None for c in rows[0]):
        header = rows.pop(0)
    return header, rows


def number(s):
    try:
        v = float(s)
    except ValueError:
        return None
    return v if v == v and abs(v) != float("inf") else None


def column(spec, header, what, path):
    """Index of a column given by name or by number (from 1)."""
    spec = spec.strip()
    if spec.isdigit():
        return int(spec) - 1
    if header and spec in header:
        return header.index(spec)
    warn("\\plotline: no column '%s' (%s=) in %s%s" % (
        spec, what, path, " -- columns: " + ", ".join(header) if header else
        " (it has no header row: give the column's number)"))
    return None


class PlotMixin:
    def env_slideplot(self, body):
        """\\begin{slideplot}[width, height, xlabel, ylabel, xmin, xmax, ymin,
        ymax, grid, legend, rows, columns, share] with \\plotline<spec>[x, y,
        label, color, style, offset, xscale, yscale, sep, pdfevery]{file} lines -- or with
        \\plotpanel<spec>[title, xlabel, ylabel, xmin, xmax, ymin, ymax] lines,
        each followed by the
        \\plotline lines of that panel."""
        opt, j = read_opt(body, 0)
        o = keyvals(opt)
        rest = body[j:]
        marks = list(re.finditer(r"\\plot(panel|line)\b", rest))
        multi = any(m.group(1) == "panel" for m in marks)
        panels = [] if multi else [{"spec": None, "opts": {}, "lines": []}]
        for m in marks:
            spec, k = self.read_spec(rest, m.end())
            popt, k = read_opt(rest, k)
            if m.group(1) == "panel":
                panels.append({"spec": spec, "opts": keyvals(popt), "lines": []})
                continue
            path, k = read_arg(rest, k)
            if not panels:
                warn("slideplot: \\plotline before the first \\plotpanel (left out)")
                continue
            panels[-1]["lines"].append((spec, keyvals(popt), self.expand(path).strip()))

        # layout: rows x columns, filled row by row; the other one from the count
        def count(key):
            v = o.get(key)
            if not isinstance(v, str) or not v.strip():
                return None
            if not v.strip().isdigit() or int(v) < 1:
                warn("slideplot: %s=%s should be a whole number" % (key, v))
                return None
            return int(v)
        rows, cols = (count("rows"), count("columns")) if multi else (1, 1)
        n = len(panels)
        cols = cols or (-(-n // rows) if rows else 1)
        rows = rows or -(-n // cols)
        if n > rows * cols:
            warn("slideplot: %d panels do not fit in %d x %d (the last ones left out)"
                 % (n, rows, cols))
            panels, n = panels[:rows * cols], rows * cols
        share = str(o.get("share", "")).strip()
        if share and share not in SHARES:
            warn("slideplot: share=%s (one of %s)" % (share, ", ".join(SHARES)))
            share = ""
        if not share:                      # stacked: x, side by side: y, grid: both
            share = "x" if cols == 1 < rows else "y" if rows == 1 < cols else "both"

        # lines: one colour and one legend entry per label, across the panels
        colors, keys, out, used = {}, [], [], 0
        for p in panels:
            series = []
            for spec, lo, path in p["lines"]:
                line = self.plot_line(path, lo)
                if line is None:
                    continue
                data, label, color, style = line
                if label and label in colors:
                    color, key = colors[label]
                else:
                    if not color:
                        used += 1
                        color = css_color("plotcolor%d" % ((used - 1) % 7 + 1))
                    key = -1
                    if label:
                        key = len(keys)
                        colors[label] = (color, key)
                        keys.append((label, color, style, spec))
                data.update(color=color, style=style, spec=spec or "", key=key)
                series.append(data)
            out.append({"series": series})
        if not any(p["series"] for p in out):
            warn("slideplot: no \\plotline with data")
            return ""
        total = sum(len(s["x"]) for p in out for s in p["series"])
        if total > TOO_MANY:
            warn("slideplot: %d points embedded in the page -- thin the data file "
                 "if the deck gets slow" % total)

        def limits(opts, what):
            axis = {}
            for k in ("xmin", "xmax", "ymin", "ymax"):
                v = opts.get(k)
                if isinstance(v, str) and v.strip():
                    if number(v) is None:
                        warn("%s: %s=%s is not a number" % (what, k, v))
                    else:
                        axis[k] = number(v)
            return axis
        axis = limits(o, "slideplot")
        shared = {"x": share in ("x", "both"), "y": share in ("y", "both")}
        for p, d in zip(panels, out):          # a panel's own range: unshared axes only
            own = limits(p["opts"], "\\plotpanel")
            for k in [k for k in own if shared[k[0]]]:
                warn("\\plotpanel: %s ignored -- the %s axis is shared (share=%s)"
                     % (k, k[0], share))
                del own[k]
            if own:
                d["axis"] = own
        grid = str(o.get("grid", "true")).strip().lower() in ("true", "")
        pos = str(o.get("legend", "north east")).strip()
        if pos not in LEGEND:
            warn("slideplot: legend=%s (one of %s)" % (pos, ", ".join(LEGEND)))
            pos = "north east"
        width = length_css(o["width"]) if isinstance(o.get("width"), str) else None
        height = length_css(o["height"]) if isinstance(o.get("height"), str) else None
        if height and height.endswith("%"):
            warn("slideplot: height=%s -- give an absolute length (cm, pt)" % o["height"])
            height = None
        payload = json.dumps({"panels": out, "axis": axis, "grid": grid, "rows": rows,
                              "cols": cols, "share": shared},
                             separators=(",", ":")).replace("</", "<\\/")

        def text(opts, key):
            v = opts.get(key)
            return self.inline(v).strip() if isinstance(v, str) else ""
        legend = "".join(
            '<button type="button" class="plot-key" data-key="%d"%s>'
            '<span class="plot-swatch" style="--c:%s" data-style="%s"></span>'
            '<span class="plot-name">%s</span></button>'
            % (k, self.spec_attr(spec) + (' data-mode="only"' if spec and not multi else ""),
               html.escape(color), style, label)     # one panel: the box shrinks
            for k, (label, color, style, spec) in enumerate(keys))
        keybox = ('<div class="plot-legend" data-pos="%s">%s</div>' % (pos.replace(" ", "-"), legend)
                  if legend and pos != "none" else "")
        inner = "" if pos.startswith("outer") else keybox
        last_row = (n - 1) // cols * cols          # first panel of the last row
        corner = {"north east": min(cols, n) - 1, "north west": 0,
                  "south east": n - 1, "south west": last_row}.get(pos, 0)
        titles = [text(p["opts"], "title") for p in panels]
        pxl = [text(p["opts"], "xlabel") for p in panels]
        pyl = [text(p["opts"], "ylabel") for p in panels]
        cells = []
        for i, p in enumerate(panels):
            cells.append(
                '<div class="plot-panel"%s>%s<div class="plot-cell">%s'
                '<div class="plot-area" data-panel="%d">%s<div class="plot-tip" hidden></div></div>'
                '</div>%s</div>'
                % (self.spec_attr(p["spec"]),
                   '<div class="plot-title">%s</div>' % titles[i] if any(titles) else "",
                   '<div class="plot-ylabel"><span>%s</span></div>' % pyl[i] if any(pyl) else "",
                   i, inner if i == corner else "",
                   '<div class="plot-xlabel">%s</div>' % pxl[i] if any(pxl) else ""))
        xlabel, ylabel = text(o, "xlabel"), text(o, "ylabel")
        return PARA + (
            '<div class="plot%s" style="width:%s">%s'
            '<div class="plot-main">%s<div class="plot-panels" style="--cols:%d;--rows:%d;%s">%s</div>'
            '%s</div>%s'
            '<script type="application/json" class="plot-data">%s</script></div>'
            % (" plot-multi" if multi else "", width or "100%",
               keybox if pos == "outer north" else "",
               '<div class="plot-ylabel"><span>%s</span></div>' % ylabel if ylabel else "",
               cols, rows, "height:%s" % height if height else "aspect-ratio:2", "".join(cells),
               keybox if pos == "outer east" else "",
               '<div class="plot-xlabel">%s</div>' % xlabel if xlabel else "",
               payload)) + PARA

    def plot_line(self, path, o):
        """One \\plotline: ({x, y}, label HTML, CSS colour or None (not given),
        line style), or None."""
        full = os.path.join(self.root, path)
        if not os.path.isfile(full):
            warn("plot data not found: %s" % path)
            return None
        self.data_files.add(full)
        sep = str(o.get("sep", "")).strip()
        if sep and sep not in SEPARATORS:
            warn("\\plotline: sep=%s (one of %s)" % (sep, ", ".join(SEPARATORS)))
            sep = ""
        sep = SEPARATORS[sep] if sep else ("," if path.lower().endswith(".csv") else None)
        header, rows = read_table(full, sep)
        xi = column(str(o.get("x", "1")), header, "x", path)
        yi = column(str(o.get("y", "2")), header, "y", path)
        if xi is None or yi is None:
            return None
        def num(key, default):
            v = o.get(key, "")
            v = number(v) if isinstance(v, str) and v.strip() else default
            if v is None:
                warn("\\plotline: %s=%s is not a number" % (key, o[key]))
                v = default
            return v
        offset, xscale, yscale = num("offset", 0), num("xscale", 1), num("yscale", 1)
        if not xscale or not yscale:
            warn("\\plotline: xscale / yscale = 0 (left at 1)")
            xscale, yscale = xscale or 1, yscale or 1
        xs, ys = [], []
        for r in rows:
            x = number(r[xi]) if xi < len(r) else None
            if x is None:
                continue
            y = number(r[yi]) if yi < len(r) else None
            xs.append(float("%.7g" % (x * xscale + offset)))   # offset: shifted along x
            ys.append(None if y is None else float("%.6g" % (y * yscale)))   # None: a gap
        if not xs:
            warn("\\plotline: no numbers in %s" % path)
            return None
        color = o.get("color")
        color = css_color(color) if isinstance(color, str) and color.strip() else None
        style = str(o.get("style", "solid")).strip()
        if style not in LINE_STYLES:
            warn("\\plotline: style=%s (one of %s)" % (style, ", ".join(LINE_STYLES)))
            style = "solid"
        label = o.get("label")
        label = self.inline(label).strip() if isinstance(label, str) else ""
        data = {"x": xs, "y": ys}
        if offset or xscale != 1:                   # the readout also gives the file's x
            data.update(offset=offset, xscale=xscale)
        return data, label, color, style
