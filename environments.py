"""LaTeX environments (\\begin{...} ... \\end{...}) -- mixin for Converter."""
import html
import re

from .log import warn
from .parsing import keyvals, read_arg, read_group, read_opt, skip_ws, split_items
from .units import length_css
from .vocabulary import MATH_ENVS, PARA

LISTS = ("itemize", "enumerate", "description")
BLOCKS = ("block", "alertblock", "exampleblock")
TABLES = ("tabular", "tabular*", "array")


class EnvironmentsMixin:
    def environment(self, env, body):
        """Convert \\begin{env} body \\end{env}. Block-level results are
        wrapped in PARA markers so they start on their own line."""
        if env in LISTS:
            return self.env_list(env, body)
        if env in BLOCKS:
            title, j = read_arg(body, 0)
            return PARA + ('<div class="block"><div class="block-title">%s</div>'
                           '<div class="block-body">%s</div></div>'
                           % (self.inline(title), self.flow(body[j:]))) + PARA
        if env == "columns":
            opt, j = read_opt(body, 0)
            o = keyvals(opt)
            cls = " middle" if "c" in o else ""    # [c]: vertically centred
            if "onlytextwidth" in o:               # space only between columns
                cls += " otw"
            return PARA + '<div class="columns%s">%s</div>' % (
                cls, self.inline(body[j:]).replace(PARA, "")) + PARA
        if env == "column":
            _, j = read_opt(body, 0)
            w, j = read_arg(body, j)
            css = length_css(w)
            return '<div class="col" data-size="%s" style="flex:0 0 %s">%s</div>' % (
                css, css, self.flow(body[j:]))
        if env == "rows":
            return PARA + '<div class="rows">%s</div>' % (
                self.inline(body).replace(PARA, "")) + PARA
        if env == "row":
            pos, j = read_opt(body, 0)
            frac, j = read_arg(body, j)
            size = "%g%%" % (float(frac) * 100)
            return '<div class="row-cell" data-size="%s" data-pos="%s" style="flex:0 0 %s">%s</div>' % (
                size, (pos or "c").strip(), size, self.flow(body[j:]))
        if env == "minipage":
            _, j = read_opt(body, 0)
            _, j = read_opt(body, j)
            _, j = read_opt(body, j)
            w, j = read_arg(body, j)
            return '<div class="minipage" style="width:%s">%s</div>' % (
                length_css(w), self.flow(body[j:]))
        if env in ("figure", "figure*", "table", "table*"):
            return self.env_float(env.rstrip("*"), body)
        if env == "center":
            return PARA + '<div class="center">%s</div>' % self.flow(body) + PARA
        if env in MATH_ENVS:
            return PARA + html.escape("\\begin{%s}%s\\end{%s}" % (env, body, env),
                                      quote=False) + PARA
        if env in TABLES:
            return self.env_tabular(env, body)
        if env == "progress":
            return self.env_progress(body)
        if env == "slidetable":
            return self.env_slidetable(body)
        if env == "tikzpicture":                   # compiled by LaTeX: tikz.py
            return self.tikz_env(body)
        if env == "litreview":
            return self.env_litreview(body)
        if env == "publications":                  # \pub.. commands: commands.py
            return PARA + '<div class="publications">%s</div>' % (
                self.blocks(self.inline(body))) + PARA
        if env == "animation":
            return self.env_animation(body)
        if env == "slideplot":                     # plot.py
            return self.env_slideplot(body)
        if env == "annotate":                      # \shape: commands.py
            opt, j = read_opt(body, 0)
            grid = ' data-grid' if "grid" in keyvals(opt) else ""
            return PARA + '<div class="annotate"%s>%s</div>' % (   # flow: blocks
                grid, self.flow(body[j:])) + PARA                  # (animation) stay inside
        if env == "animateinline":
            return self.animation(body)
        warn("unknown environment {%s} (kept its content)" % env)
        return self.inline(body)

    def env_list(self, env, body):
        """itemize / enumerate / description -> <ul> / <ol>. Overlay specs:
        \\item<2->, \\item<+->, or one for all items: \\begin{itemize}[<+->]."""
        tag = "ol" if env == "enumerate" else "ul"
        opt, j = read_opt(body, 0)
        default = opt[1:-1] if opt and opt.startswith("<") and opt.endswith(">") else None
        lis = []
        for it in split_items(body[j:]):
            spec, k = self.read_spec(it, 0)
            label, k = read_opt(it, k)
            if spec is None:
                spec, k = self.read_spec(it, k)         # \item[label]<spec>
            if spec is None and default:
                spec = self.resolve_spec(default)
            content = self.inline(it[k:])
            content = self.blocks(content) if PARA in content else content.strip()
            if label:
                content = "<b>%s</b> %s" % (self.inline(label), content)
            lis.append("<li%s>%s</li>" % (self.spec_attr(spec), content))
        return PARA + "<%s>%s</%s>" % (tag, "".join(lis), tag) + PARA

    def env_progress(self, body):
        """Research-progress timeline: \\task<spec>[status]{title}{when}."""
        opt, j = read_opt(body, 0)
        tasks = []
        for it in split_items(body[j:], "task"):
            spec, k = self.read_spec(it, 0)
            status, k = read_opt(it, k)
            title, k = read_arg(it, k)
            when, k = read_arg(it, k)
            status = (status or "done").strip()
            if status not in ("done", "ongoing", "planned"):
                warn("\\task[%s]: status should be done, ongoing or planned" % status)
            tasks.append('<div class="task" data-status="%s"%s><span class="when">%s</span>'
                         '<span class="marker"></span><span class="what">%s</span></div>'
                         % (status, self.spec_attr(spec), self.inline(when).strip(),
                            self.inline(title).strip()))
        legend = "" if (opt or "").strip() == "nolegend" else (
            '<div class="progress-legend">' + "".join(
                '<span data-status="%s"><span class="marker"></span>%s</span>' % (st, label)
                for st, label in (("done", "Done"), ("ongoing", "Ongoing"),
                                  ("planned", "Planned"))) + "</div>")
        return PARA + '<div class="progress">%s%s</div>' % ("".join(tasks), legend) + PARA

    def env_litreview(self, body):
        """Literature table: \\study<spec>{keys}{summary} / \\studytext{who}{summary}.
        Each key becomes an author-year citation, filled in by deck.js."""
        opt, j = read_opt(body, 0)
        left = "%g%%" % (float(opt) * 100) if opt else "30%"
        k = skip_ws(body, j)
        if k < len(body) and body[k] == "{":        # \begin{litreview}{0.2\textwidth}
            width, j = read_group(body, k)
            left = length_css(width) or left
        body = body[j:]
        marks = list(re.finditer(r"\\(studytext|study)\b", body))
        rows = []
        for n, m in enumerate(marks):
            seg = body[m.end():marks[n + 1].start() if n + 1 < len(marks) else len(body)]
            spec, k = self.read_spec(seg, 0)
            who, k = read_arg(seg, k)
            what, k = read_arg(seg, k)
            if m.group(1) == "study":
                who = "<br>".join('<cite data-ref="%s" data-style="authoryear"></cite>'
                                  % html.escape(key.strip())
                                  for key in who.split(",") if key.strip())
            else:
                who = self.inline(who).strip()
            rows.append('<tr%s><td class="lit-who">%s</td><td class="lit-what">%s</td></tr>'
                        % (self.spec_attr(spec), who, self.inline(what).strip()))
        return PARA + '<table class="litreview" style="--lit-left:%s">%s</table>' % (
            left, "".join(rows)) + PARA

    def env_float(self, kind, body):
        """figure / table: a centred block (beamer's floats do not float);
        \\caption inside it is numbered "Figure n:" / "Table n:"."""
        _, j = read_opt(body, 0)                    # placement [htbp]: ignored
        self.floats.append({"kind": kind, "n": None})
        try:
            content = self.flow(body[j:])
        finally:
            self.floats.pop()
        return PARA + '<figure class="float" data-kind="%s"><div class="center">%s</div></figure>' % (
            kind, content) + PARA

    def env_slidetable(self, body):
        """\\begin{slidetable}[style]{colspec}: first row is the header; the
        style (plain, lines, header, striped) draws rules and shading."""
        style, j = read_opt(body, 0)
        style = (style or "plain").strip()
        if style not in ("plain", "lines", "header", "striped"):
            warn("slidetable: unknown style '%s' (plain, lines, header, striped)" % style)
        spec, j = read_arg(body, j)
        cols = column_specs(spec)
        # p/m/b columns: their width; the row's cells line up as in LaTeX
        # (p: first lines at the top, m: middle, b: bottom)
        valign = next(({"p": "top", "b": "bottom"}.get(k, "middle")
                       for _, _, k in cols if k in "pmb"), None)
        rows = []
        for r in re.split(r"\\\\(?:\[[^\]]*\])?", body[j:]):
            r = re.sub(r"\\(hline|toprule|midrule|bottomrule|cline\{[^}]*\})", "", r)
            if r.strip():
                rows.append([self.inline(c).strip() for c in re.split(r"(?<!\\)&", r)])
        if not rows:
            return ""

        def cell_style(k):
            align, width, _ = cols[k] if k < len(cols) else ("left", None, "l")
            return "text-align:%s%s%s" % (align, ";width:%s" % width if width else "",
                                          ";vertical-align:%s" % valign if valign else "")

        def tr(cells, tag):
            return "<tr>%s</tr>" % "".join(
                '<%s style="%s">%s</%s>' % (tag, cell_style(k), c, tag)
                for k, c in enumerate(cells))
        stretch = self.macros.get("slidetablestretch", "1.3").strip()
        try:
            stretch = "%g" % float(stretch)
        except ValueError:
            warn("\\slidetablestretch should be a number, not '%s'" % stretch)
            stretch = "1.3"
        return PARA + ('<div class="slidetable-wrap"><table class="slidetable" data-style="%s"'
                       ' style="--tab-stretch:%s"><thead>%s</thead><tbody>%s</tbody></table></div>'
                       % (style, stretch, tr(rows[0], "th"),
                          "".join(tr(r, "td") for r in rows[1:]))) + PARA

    def env_tabular(self, env, body):
        """tabular -> <table>; \\hline / booktabs rules become borders."""
        if env == "tabular*":
            _, j = read_arg(body, 0)
            body = body[j:]
        _, j = read_arg(body, 0)                       # column spec
        trs = []
        for r in re.split(r"\\\\(?:\[[^\]]*\])?", body[j:]):
            hline = "\\hline" in r or "\\toprule" in r or "\\midrule" in r
            r = re.sub(r"\\(hline|toprule|midrule|bottomrule|cline\{[^}]*\})", "", r)
            if not r.strip():
                if hline and trs:                      # closing rule under the last row
                    trs[-1] = trs[-1].replace("<tr", '<tr data-bottom="1"', 1)
                continue
            cells = re.split(r"(?<!\\)&", r)
            trs.append("<tr%s>%s</tr>" % (' class="rule"' if hline else "",
                       "".join("<td>%s</td>" % self.inline(c).strip() for c in cells)))
        return PARA + '<table class="tab">%s</table>' % "".join(trs) + PARA


def column_specs(spec):
    """'l >{\\bfseries}r p{3cm} @{}' -> [('left', None, 'l'), ('right', None, 'r'),
    ('left', '240px', 'p')]: alignment, CSS width (p/m/b columns), column type"""
    cols, i, pre = [], 0, None
    while i < len(spec):
        c = spec[i]
        if c in "lcrpmbX":
            align = {"c": "center", "r": "right"}.get(c, "left")
            if pre and "\\centering" in pre:          # >{\centering}p{..}
                align = "center"
            elif pre and "\\raggedleft" in pre:
                align = "right"
            pre = None
            i += 1
            width = None
            if c in "pmb":                         # {width}
                w, i = read_arg(spec, i)
                width = length_css(w)
            cols.append((align, width, c))
        elif c == ">":                             # >{..}: applies to the next column
            pre, i = read_arg(spec, i + 1)
        elif c in "@!<":                           # @{..} !{..} <{..}
            _, i = read_arg(spec, i + 1)
        elif c == "*":                             # *{3}{c}
            n, i = read_arg(spec, i + 1)
            sub, i = read_arg(spec, i)
            cols += column_specs(sub) * int(n) if n.strip().isdigit() else []
        elif c == "{":                             # c{1cm}: a width needs p/m/b
            w, i = read_arg(spec, i)
            warn("column spec: {%s} after a column without a width (use p{%s})" % (w, w))
        else:
            i += 1                                 # | and spaces
    return cols
