"""slideplot environment (titletemplates.sty) -> an interactive plot drawn by
html/deck.js -- mixin for Converter.

    \\begin{slideplot}[xlabel={$t$}, ylabel={$y/D$}, height=5cm]
      \\plotline[x=time, y=aleDisp_y, label={$U_r = 4$}]{data/U4/data_dy.csv}
      \\plotline<2->[x=time, y=aleDisp_y, label={$U_r = 6$}]{data/U6/data_dy.csv}
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
        ymax, grid, legend] with \\plotline<spec>[x, y, label, color, style,
        offset, sep, pdfevery]{file} lines."""
        opt, j = read_opt(body, 0)
        o = keyvals(opt)
        rest = body[j:]
        series, legend = [], []
        for n, m in enumerate(re.finditer(r"\\plotline\b", rest)):
            spec, k = self.read_spec(rest, m.end())
            popt, k = read_opt(rest, k)
            path, k = read_arg(rest, k)
            line = self.plot_line(self.expand(path).strip(), keyvals(popt), n)
            if line is None:
                continue
            data, label, color, style = line
            series.append(data)
            if label:
                legend.append('<button type="button" class="plot-key" data-series="%d"%s>'
                              '<span class="plot-swatch" style="--c:%s" data-style="%s"></span>'
                              '<span class="plot-name">%s</span></button>'
                              % (len(series) - 1, self.spec_attr(spec) +
                                 (' data-mode="only"' if spec else ""),   # the box shrinks
                                 color, style, label))
            data.update(color=color, style=style, spec=spec or "")
        if not series:
            warn("slideplot: no \\plotline with data")
            return ""
        total = sum(len(s["x"]) for s in series)
        if total > TOO_MANY:
            warn("slideplot: %d points embedded in the page -- thin the data file "
                 "if the deck gets slow" % total)

        axis = {}
        for k in ("xmin", "xmax", "ymin", "ymax"):
            v = o.get(k)
            if isinstance(v, str) and v.strip():
                if number(v) is None:
                    warn("slideplot: %s=%s is not a number" % (k, v))
                else:
                    axis[k] = number(v)
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
        style = "width:%s" % (width or "100%")
        area = ' style="height:%s"' % height if height else ""
        payload = json.dumps({"series": series, "axis": axis, "grid": grid},
                             separators=(",", ":")).replace("</", "<\\/")

        def label(key):
            v = o.get(key)
            return self.inline(v).strip() if isinstance(v, str) else ""
        xlabel, ylabel = label("xlabel"), label("ylabel")
        keys = ('<div class="plot-legend" data-pos="%s">%s</div>' % (pos.replace(" ", "-"), "".join(legend))
                if legend and pos != "none" else "")
        inner, east, north = (keys, "", "") if not pos.startswith("outer") else \
            ("", keys, "") if pos == "outer east" else ("", "", keys)
        return PARA + (
            '<div class="plot" style="%s">%s'
            '<div class="plot-main">%s<div class="plot-area"%s>%s'
            '<div class="plot-tip" hidden></div></div>%s</div>%s'
            '<script type="application/json" class="plot-data">%s</script></div>'
            % (style, north,
               '<div class="plot-ylabel"><span>%s</span></div>' % ylabel if ylabel else "",
               area, inner, east,
               '<div class="plot-xlabel">%s</div>' % xlabel if xlabel else "",
               payload)) + PARA

    def plot_line(self, path, o, n):
        """One \\plotline: ({x, y}, label HTML, CSS colour, line style), or None."""
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
        offset = o.get("offset", "")
        offset = number(offset) if isinstance(offset, str) and offset.strip() else 0
        if offset is None:
            warn("\\plotline: offset=%s is not a number" % o["offset"])
            offset = 0
        xs, ys = [], []
        for r in rows:
            x = number(r[xi]) if xi < len(r) else None
            if x is None:
                continue
            y = number(r[yi]) if yi < len(r) else None
            xs.append(float("%.7g" % (x + offset)))      # offset: shifted along x
            ys.append(None if y is None else float("%.6g" % y))   # None: a gap
        if not xs:
            warn("\\plotline: no numbers in %s" % path)
            return None
        color = o.get("color")
        color = css_color(color) if isinstance(color, str) and color.strip() \
            else css_color("plotcolor%d" % (n % 7 + 1))
        style = str(o.get("style", "solid")).strip()
        if style not in LINE_STYLES:
            warn("\\plotline: style=%s (one of %s)" % (style, ", ".join(LINE_STYLES)))
            style = "solid"
        label = o.get("label")
        label = self.inline(label).strip() if isinstance(label, str) else ""
        data = {"x": xs, "y": ys}
        if offset:
            data["offset"] = offset                 # the readout also gives the file's x
        return data, label, html.escape(color), style
