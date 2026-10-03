"""LaTeX commands (\\name ...) -- mixin for Converter."""
import html
import re

from .colors import css_color
from .images import resolve_image
from .log import warn
from .parsing import find_end, keyvals, read_arg, read_opt
from .units import length_css
from .vocabulary import (CENTER, DECLS, HFILL, IGNORE, PARA, PAUSE,
                         REF_MARK, SIZES, TEXT_SYMBOLS, WRAPS)

from .overlays import OVERLAY_CMDS

CITE_CMDS = ("cite", "citep", "parencite", "footcite", "autocite")
TEXTCITE_CMDS = ("textcite", "Textcite", "citet", "Citet")    # "Liu et al. [13]"
AUTHORCITE_CMDS = ("citeauthor", "Citeauthor")                # "Liu et al."
PUB_STATUSES = ("published", "accepted", "review", "submitted", "preparation")


class CommandsMixin:
    def command(self, name, s, i):
        """Convert the command `name` whose arguments start at s[i].
        Returns (html, new index, number of <span> opened until group end)."""
        if name in self.macros:
            return self.inline(self.macros[name]), i, 0
        if len(name) == 1 and not name.isalpha():
            return self.symbol(name, s, i)

        if name == "begin":
            env, i = read_arg(s, i)
            start = i
            end, after = find_end(s, start, env)
            spec, k = self.read_spec(s, start)          # \begin{block}<2->{..}
            if spec:
                res = self.environment(env, s[k:end]).replace(PARA, "").strip()
                if res.startswith("<") and not res.startswith("</"):
                    # put the spec on the element itself (keeps flex layouts
                    # such as rows / columns intact)
                    res = re.sub(r"^<(\w+)", r'<\1 data-spec="%s"' % spec, res, count=1)
                else:
                    res = '<div data-spec="%s">%s</div>' % (spec, res)
                return PARA + res + PARA, after, 0
            return self.environment(env, s[start:end]), after, 0
        if name in ("def", "gdef", "edef", "newcommand", "renewcommand", "providecommand"):
            return self.define(name, s, i)

        # ---- fonts and colours
        if name in SIZES:
            return '<span style="font-size:%gem">' % SIZES[name], i, 1
        if name in DECLS:
            return '<span style="%s">' % DECLS[name], i, 1
        if name == "color":
            col, i = read_arg(s, i)
            return '<span style="color:%s">' % css_color(col), i, 1
        if name == "textcolor":
            col, i = read_arg(s, i)
            txt, i = read_arg(s, i)
            return '<span style="color:%s">%s</span>' % (css_color(col), self.inline(txt)), i, 0
        if name in WRAPS:
            txt, i = read_arg(s, i)
            tag = WRAPS[name]
            return "<%s>%s</%s>" % (tag, self.inline(txt), tag), i, 0

        # ---- citations, figures
        if name in CITE_CMDS + TEXTCITE_CMDS + AUTHORCITE_CMDS:
            _, i = read_opt(s, i)
            _, i = read_opt(s, i)
            keys, i = read_arg(s, i)
            style = (' data-style="text"' if name in TEXTCITE_CMDS
                     else ' data-style="author"' if name in AUTHORCITE_CMDS else "")
            return '<cite data-ref="%s"%s></cite>' % (
                html.escape(keys.replace(" ", "")), style), i, 0
        if name == "includegraphics":
            opt, i = read_opt(s, i)
            path, i = read_arg(s, i)
            return self.image(self.expand(path), keyvals(opt)), i, 0
        if name == "FigurePlaceholder":
            w, i = read_opt(s, i)
            h, i = read_arg(s, i)
            if length_css(h, quiet=True) is None:      # \FigurePlaceholder{label}
                warn("\\FigurePlaceholder{%s}: needs {height}{label}, e.g. "
                     "\\FigurePlaceholder{3cm}{%s}" % (h, h))
                label, h = h, "3cm"
            else:
                label, i = read_arg(s, i)
            style = "height:%s" % length_css(h)
            if w:
                style += ";width:%s" % length_css(w)
            return '<div class="figure-placeholder" style="%s">%s</div>' % (
                style, self.inline(label)), i, 0

        # ---- spacing and alignment
        if name in ("vspace", "vspace*"):
            ln, i = read_arg(s, i)
            css = length_css(ln)
            return (PARA + '<div style="height:%s"></div>' % css + PARA) if css else "", i, 0
        if name in ("hspace", "hspace*"):
            ln, i = read_arg(s, i)
            css = length_css(ln)
            return '<span style="display:inline-block;width:%s"></span>' % css if css else "", i, 0
        if name in ("hfill", "hfil", "hss"):
            return HFILL, i, 0
        if name == "centering":
            return CENTER, i, 0

        # ---- step-by-step reveals
        if name == "pause":
            _, i = read_opt(s, i)                      # \pause[n]: number ignored
            return PAUSE, i, 0

        # ---- publications list (inside \begin{publications})
        if name == "pubsection":
            title, i = read_arg(s, i)
            return PARA + '<div class="pub-section">%s</div>' % self.inline(title) + PARA, i, 0
        if name in ("pub", "pubtext"):
            status, i = read_opt(s, i)
            arg, i = read_arg(s, i)
            status = (status or "").strip()
            if status and status not in PUB_STATUSES:
                warn("\\%s[%s]: status should be one of %s" % (name, status, ", ".join(PUB_STATUSES)))
            badge = '<span class="pub-badge" data-status="%s"></span>' % status if status else ""
            if name == "pub":                      # entry filled in by deck.js from the .bib
                return PARA + '<div class="pub" data-key="%s">%s<span class="pub-entry"></span></div>' % (
                    html.escape(arg.strip()), badge) + PARA, i, 0
            return PARA + '<div class="pub">%s<span class="pub-entry">%s</span></div>' % (
                badge, self.inline(arg)) + PARA, i, 0

        # ---- speaker notes (shown only in the presenter view)
        if name == "note":
            return self.note(s, i), self.note_end, 0

        # ---- shapes (\begin{annotate} is in environments.py)
        if name in ("shape", "slideshape"):
            return self.shape(name, s, i)
        if name == "slidegrid":
            return '<span class="slide-grid"></span>', i, 0

        # ---- links, notes
        if name == "caption":
            return self.caption(s, i)
        if name in ("href", "url", "footnote", "label", "ref"):
            return self.reference(name, s, i)
        if name in OVERLAY_CMDS:
            return self.overlay(name, s, i)

        # ---- text
        if name in ("ldots", "dots"):
            return "…", i, 0
        if name == "LaTeX":
            return "LaTeX", i, 0
        if name == "textbackslash":                # TeX drops the space after it
            while i < len(s) and s[i] in " \t":
                i += 1
            return "\\", i, 0
        if name == "cmd":                          # \cmd{shape} -> \shape in monospace
            arg, i = read_arg(s, i)
            return "<code>\\%s</code>" % self.inline(arg).strip(), i, 0
        if name in ("item", "today", "hline") or name in IGNORE:
            return "", i, 0                            # \item: handled by list envs
        warn("unknown command \\%s (kept its text)" % name)
        return "", i, 0

    # ---------------------------------------------------------- helpers
    def symbol(self, name, s, i):
        """Single-character commands: \\\\  \\[ \\]  \\( \\)  \\&  \\%  \\,  ..."""
        if name == "\\":                               # \\ or \\[len]
            _, i = read_opt(s, i)
            return "<br>", i, 0
        if name == "[":
            j = s.index("\\]", i)
            return "\\[" + html.escape(s[i:j], quote=False) + "\\]", j + 2, 0
        if name == "(":
            j = s.index("\\)", i)
            return "\\(" + html.escape(s[i:j], quote=False) + "\\)", j + 2, 0
        return TEXT_SYMBOLS.get(name, html.escape(name)), i, 0

    def define(self, name, s, i):
        """\\def\\x{..} and \\newcommand{\\x}{..} (without arguments)."""
        if name in ("def", "gdef", "edef"):
            m = re.match(r"\s*\\([A-Za-z@]+)", s[i:])
            val, j = read_arg(s, i + m.end())
            self.macros[m.group(1)] = val
            return "", j, 0
        nm, i = read_arg(s, i)
        nargs, i = read_opt(s, i)
        val, i = read_arg(s, i)
        if nargs:
            warn("\\newcommand with arguments not supported: %s" % nm)
        else:
            self.macros[nm.lstrip("\\")] = val
        return "", i, 0

    def note(self, s, i):
        """\\note{..}, \\note[item]{..}, \\note<2>{..} -> <aside class="note">.
        The overlay spec is ignored: the presenter view shows a slide's notes
        on all its steps. Sets self.note_end to the index after the note."""
        _, i = self.read_spec(s, i)
        opt, i = read_opt(s, i)
        text, self.note_end = read_arg(s, i)
        body = self.inline(text)
        body = self.blocks(body) if PARA in body else body.strip()
        return '<aside class="note"%s>%s</aside>' % (
            " data-item" if (opt or "").strip() == "item" else "", body)

    def shape(self, name, s, i):
        """\\shape<spec>[options]{kind}{x1,y1}{x2,y2} (in annotate) and
        \\slideshape (on the slide): a placeholder span that deck.js turns
        into SVG. Coordinates are fractions, origin bottom left."""
        spec, i = self.read_spec(s, i)
        opt, i = read_opt(s, i)
        kind, i = read_arg(s, i)
        p1, i = read_arg(s, i)
        p2, i = read_arg(s, i)
        kind = kind.strip()
        if kind not in SHAPES:
            warn("\\%s: unknown shape '%s' (use %s)" % (name, kind, ", ".join(SHAPES)))
            return "", i, 0
        o = keyvals(opt)
        size = (o.get("textsize") or "\\small").strip().lstrip("\\")
        attrs = {
            "kind": "ellipse" if kind == "circle" else kind,
            "p1": point(p1),
            "p2": "" if kind == "text" else point(p2),
            "color": css_color(o.get("color") or "red"),
            "width": shape_px(o.get("width"), 1),
            "fill": "" if o.get("fill") in (None, True, "none") else css_color(o["fill"]),
            "opacity": o.get("opacity") or "0.25",
            "dashed": "" if o.get("dashed") in (None, "false") else "1",
            "rounded": shape_px(o.get("rounded") if o.get("rounded") is not True else "3pt", 0),
            "labelpos": o.get("labelpos") or "above",
            "size": SIZES.get(size, 0.9),
        }
        text = p2 if kind == "text" else (o.get("label") if o.get("label") is not True else "")
        cls = "shape" + (" slide-shape" if name == "slideshape" else "")
        data = "".join(' data-%s="%s"' % (k, html.escape(str(v))) for k, v in attrs.items()
                       if v != "")
        return '<span class="%s"%s%s>%s</span>' % (
            cls, data, self.spec_attr(spec), self.inline(text or "").strip()), i, 0

    def caption(self, s, i):
        """\\caption[short]{text} in a figure/table: "Figure n: text"."""
        _, i = read_opt(s, i)
        text, i = read_arg(s, i)
        if not self.floats:
            warn("\\caption outside figure or table (kept as text)")
            return self.inline(text), i, 0
        f = self.floats[-1]
        self.counters[f["kind"]] += 1
        f["n"] = self.counters[f["kind"]]
        name = {"figure": "Figure", "table": "Table"}[f["kind"]]
        return PARA + ('<figcaption><span class="caption-name">%s&nbsp;%d:</span>&nbsp;%s</figcaption>'
                       % (name, f["n"], self.inline(text).strip())) + PARA, i, 0

    def reference(self, name, s, i):
        """\\href, \\url, \\footnote, \\label (after a \\caption: names its
        number) and \\ref (resolved at the end of the document)."""
        if name == "href":
            url, i = read_arg(s, i)
            txt, i = read_arg(s, i)
            return '<a href="%s">%s</a>' % (html.escape(url), self.inline(txt)), i, 0
        arg, i = read_arg(s, i)
        if name == "url":
            return '<a href="%s">%s</a>' % (html.escape(arg), html.escape(arg)), i, 0
        if name == "footnote":
            return '<span class="footnote">%s</span>' % self.inline(arg), i, 0
        key = arg.strip()
        if name == "ref":
            return REF_MARK % html.escape(key), i, 0
        if self.floats and self.floats[-1]["n"] is not None:    # \label after \caption
            self.labels[key] = self.floats[-1]["n"]
        return "", i, 0

    def image(self, path, opts):
        """<img> for \\includegraphics, with width/height from its options."""
        style = []
        for k in ("width", "height"):
            if k in opts:
                css = length_css(opts[k])
                if css:
                    style.append("%s:%s" % (k, css))
        found = resolve_image(path, self.root)
        if not found:
            warn("image not found: %s" % path)
            found = path
        return '<img src="%s" style="%s" alt="">' % (html.escape(found), ";".join(style))


SHAPES = ("rect", "ellipse", "circle", "line", "arrow", "text")


def point(arg):
    """'0.45, 0.05' -> '0.45,0.05' (fractions; warns on anything else)"""
    try:
        x, y = (float(v) for v in arg.split(","))
        return "%g,%g" % (x, y)
    except ValueError:
        warn("shape point not understood: {%s} (expected {x,y})" % arg)
        return "0,0"


def shape_px(length, default_pt):
    """Line width / corner radius in slide pixels (default given in pt)."""
    css = length_css(length or "%gpt" % default_pt, quiet=True)
    if css and css.endswith("px"):
        return "%.2f" % float(css[:-2])
    warn("shape length not understood: %s" % length)
    return "%.2f" % float(length_css("%gpt" % default_pt)[:-2])
