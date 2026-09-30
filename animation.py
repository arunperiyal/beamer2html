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
