"""LaTeX lengths -> CSS lengths."""
import re

from .log import warn

PX_PER_CM = 80           # slide is 16 cm wide in beamer, 1280 px in HTML


def length_css(v, quiet=False):
    """'0.32\\linewidth' -> '32%', '4.5cm' -> '360px', '2em' -> '2em'.
    None (and a warning, unless quiet) if it is not a length."""
    v = (v or "").strip()
    m = re.match(r"^([\d.]*)\s*\\(linewidth|textwidth|columnwidth|paperwidth|textheight)$", v)
    if m:
        return "%g%%" % (float(m.group(1) or 1) * 100)
    m = re.match(r"^(-?[\d.]+)\s*(cm|mm|in|pt|em|ex|px)$", v)
    if m:
        n, u = float(m.group(1)), m.group(2)
        if u == "cm":
            return "%gpx" % (n * PX_PER_CM)
        if u == "mm":
            return "%gpx" % (n * PX_PER_CM / 10)
        if u == "in":
            return "%gpx" % (n * PX_PER_CM * 2.54)
        if u == "pt":
            return "%gpx" % (n * PX_PER_CM / 28.45)
        return "%g%s" % (n, u)
    if not quiet:
        warn("length not understood: %s" % v)
    return None


def length_px(v):
    """Length as a whole number of pixels, or None if it is not absolute."""
    css = length_css(v)
    if css and css.endswith("px"):
        return round(float(css[:-2]))
    return None
