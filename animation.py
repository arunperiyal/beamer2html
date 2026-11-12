"""animateinline (package `animate`) -> the frame player in html/deck.js
-- mixin for Converter."""
import html
import os
import re

from .images import resolve_image
from .log import warn
from .parsing import keyvals, read_arg, read_opt
from .units import length_css
from .vocabulary import PARA


class AnimationMixin:
    def env_animation(self, body):
        """\\begin{animation}[fps=3, frames=a:b:step, width=, controls=, autoplay=,
        loop=, subcaptions, columns=N] with \\animpanel{label}{path with \\N} lines
        (beamer2html.sty). Panels play in sync, labels above them."""
        opt, j = read_opt(body, 0)
        o = keyvals(opt)
        fr = re.match(r"\s*(-?\d+)\s*:\s*(-?\d+)\s*(?::\s*(-?\d+))?\s*$", o.get("frames") or "")
        if not fr:
            warn("animation: frames=first:last[:step] is required")
            return ""
        first, last, step = int(fr.group(1)), int(fr.group(2)), int(fr.group(3) or 1)

        def flag(name, default):
            v = o.get(name, default)
            return v is True or str(v).strip().lower() in ("true", "")
        panels = []
        rest = body[j:]
        for m in re.finditer(r"\\animpanel", rest):
            popt, k = read_opt(rest, m.end())       # \animpanel[frames=a:b:s, dt=]
            label, k = read_arg(rest, k)
            path, k = read_arg(rest, k)
            po = keyvals(popt)
            own = None
            if isinstance(po.get("frames"), str):
                pf = re.match(r"\s*(-?\d+)\s*:\s*(-?\d+)\s*(?::\s*(-?\d+))?\s*$", po["frames"])
                if pf:
                    own = (int(pf.group(1)), int(pf.group(2)), int(pf.group(3) or 1))
                else:
                    warn("\\animpanel: frames=first:last[:step] not understood: %s" % po["frames"])
            pdt = po.get("dt") if isinstance(po.get("dt"), str) and po["dt"].strip() else None
            panels.append((label, path.strip().replace("\\N", "{n}"), own, pdt))
        # panels with their own range or dt: each shows its own time
        per_panel = any(own or pdt for _, _, own, pdt in panels)
        if not panels:
            warn("animation: no \\animpanel")
            return ""
        width = o.get("width")
        css = length_css(width) if isinstance(width, str) else None
        style = ' style="flex:0 0 %s"' % css if css else ""
        figs = []
        dt = o.get("dt")
        dt = dt.strip() if isinstance(dt, str) and dt.strip() else None
        tlabel = o.get("timelabel", "$t = $")
        tlabel = self.inline(tlabel if isinstance(tlabel, str) else "").strip()
        unit = o.get("timeunit", "")
        unit = ("&nbsp;" + self.inline(unit).strip()) if isinstance(unit, str) and unit.strip() else ""
        for n, (label, path, own, pdt) in enumerate(panels, 1):
            label = self.inline(label).strip()
            if flag("subcaptions", False):
                label = "(%s)&nbsp;%s" % (chr(96 + n), label)
            pattrs = ""
            if own:
                pattrs += ' data-frames="%d:%d:%d"' % own
            if pdt:
                pattrs += ' data-dt="%s"' % html.escape(pdt.strip())
            ptime = ""
            if per_panel and (pdt or dt) and flag("time", True):
                ptime = ('<div class="anim-ptime"><span class="anim-time-label">%s</span>&nbsp;'
                         '<span class="anim-ptime-value"></span>%s</div>' % (tlabel, unit))
            figs.append('<figure%s><figcaption class="anim-label">%s</figcaption>'
                        '<img data-src="%s"%s alt="">%s</figure>'
                        % (style, label,
                           html.escape(self.frame_pattern(path, own[0] if own else first)),
                           pattrs, ptime))
        fps = str(o.get("fps", "3")).strip()
        attrs = ' data-fps="%s" data-frames="%d:%d:%d"' % (html.escape(fps), first, last, step)
        cls = "anim anim-labelled"
        cols = str(o.get("columns", "")).strip()
        if cols:                                   # rows of N panels
            if not cols.isdigit() or int(cols) < 1:
                warn("animation: columns=%s should be a whole number" % cols)
            elif int(cols) < len(panels):
                cls += " anim-grid"                # exactly N per row, width= per column
                attrs += ' style="--anim-cols:%s%s"' % (cols, ";--anim-w:%s" % css if css else "")
        if flag("autoplay", True):
            attrs += " data-autoplay"
        if flag("loop", True):
            attrs += " data-loop"
        controls = o.get("controls", "all")
        controls = "all" if controls is True else re.sub(r"\s+", "", str(controls))
        if controls == "hover":                    # buttons only while hovered
            attrs += ' data-controls="all" data-hover'
        elif controls != "none":
            attrs += ' data-controls="%s"' % html.escape(controls)
        time = bar = ""
        timed = False                              # a valid dt for the shared range
        if dt:                                     # time = frame number x dt
            try:
                float(dt)
            except ValueError:
                warn("animation: dt=%s is not a number" % dt)
            else:
                timed = not per_panel
                digits = str(o.get("timedigits", "2")).strip()
                attrs += ' data-dt="%s" data-time-digits="%s"' % (html.escape(dt.strip()),
                                                                  html.escape(digits))
                if timed and flag("time", True):   # else: below each panel
                    time = ('<div class="anim-time"><span class="anim-time-label">%s</span>&nbsp;'
                            '<span class="anim-time-value"></span>%s</div>' % (tlabel, unit))
        if flag("timebar", False):                 # progress bar, first/last times
            ends = ("", "")
            if timed:                              # end times: shared range only
                d = int(str(o.get("timedigits", "2")).strip() or 2)
                ends = tuple('<span class="anim-bar-end">%.*f</span>' % (d, n * float(dt))
                             for n in (first, last))
            bar = ('<div class="anim-bar">%s<div class="anim-bar-track" title="Click to go to a frame">'
                   '<div class="anim-bar-fill"></div></div>%s</div>' % ends)
        return PARA + '<div class="%s"%s><div class="panels">%s</div>%s%s</div>' % (
            cls, attrs, "".join(figs), bar, time) + PARA

    def animation(self, body):
        """animateinline + \\multiframe{N}{iT=a+b}{...\\includegraphics{..\\iT}...}
        Each \\includegraphics in the frame becomes one synchronised panel.
        Options as in `animate`: autoplay, loop, controls[=all|play,step,stop,speed]
        -- without `controls` there is no control bar (click / P still play)."""
        opt, j = read_opt(body, 0)
        fps, j = read_arg(body, j)
        opts = keyvals(opt)
        m = re.search(r"\\multiframe", body)
        if not m:
            warn("animateinline without \\multiframe is not supported")
            return ""
        k = m.end()
        count, k = read_arg(body, k)
        spec, k = read_arg(body, k)
        frame, k = read_arg(body, k)
        vm = re.match(r"\s*([A-Za-z]+)\s*=\s*(-?[\d.]+)\s*\+\s*(-?[\d.]+)", spec)
        var, first, step = vm.group(1), int(float(vm.group(2))), int(float(vm.group(3)))
        last = first + (int(count) - 1) * step
        frame = self.expand(frame.replace("\\" + var, "{n}"))

        panels = []
        for gm in re.finditer(r"\\includegraphics", frame):
            gopt, q = read_opt(frame, gm.end())
            path, q = read_arg(frame, q)
            width = keyvals(gopt).get("width")
            css = length_css(width) if width else None
            style = ' style="flex:0 0 %s"' % css if css else ""
            panels.append('<figure%s><img data-src="%s" alt=""></figure>'
                          % (style, html.escape(self.frame_pattern(path.strip(), first))))

        attrs = ' data-fps="%s" data-frames="%d:%d:%d"' % (fps.strip(), first, last, step)
        if "autoplay" in opts:
            attrs += " data-autoplay"
        if "loop" in opts:
            attrs += " data-loop"
        controls = opts.get("controls")                # absent -> no control bar
        if controls and controls != "none":
            attrs += ' data-controls="%s"' % ("all" if controls is True else
                                               re.sub(r"\s+", "", controls))
        return PARA + '<div class="anim"%s><div class="panels">%s</div></div>' % (
            attrs, "".join(panels)) + PARA

    def frame_pattern(self, path, first):
        """Add the file extension to a frame path pattern ('.../x_{n}'),
        found by looking up the first frame on disk."""
        if os.path.splitext(path)[1]:
            return path
        probe = path.replace("{n}", str(first))
        found = resolve_image(probe, self.root)
        if found and not found.startswith("html/cache"):
            return path + os.path.splitext(found)[1]
        warn("animation frames not found: %s" % probe)
        return path
