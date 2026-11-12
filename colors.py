"""xcolor colour expressions -> CSS colours.

    red            -> rgb(255,0,0)        (xcolor's values, not CSS's names)
    green!60!black -> 60% green, 40% black
    red!30         -> 30% red, 70% white
    bannerblue     -> \\definecolor'd in beamer2html.sty or the preamble
"""
import re

from .log import warn

# xcolor's base colours (always available), as 0..1 RGB
BASE = {
    "red": (1, 0, 0), "green": (0, 1, 0), "blue": (0, 0, 1),
    "cyan": (0, 1, 1), "magenta": (1, 0, 1), "yellow": (1, 1, 0),
    "black": (0, 0, 0), "white": (1, 1, 1), "gray": (.5, .5, .5),
    "darkgray": (.25, .25, .25), "lightgray": (.75, .75, .75),
    "brown": (.75, .5, .25), "lime": (.75, 1, 0), "olive": (.5, .5, 0),
    "orange": (1, .5, 0), "pink": (1, .75, .75), "purple": (.75, 0, .25),
    "teal": (0, .5, .5), "violet": (.5, 0, .5),
}
# CSS for colours the deck's stylesheet already names
CSS_NAMES = {"bannerblue": "var(--blue)", "bannertext": "#fff"}

DEFINED = {}

DEFINE_RE = re.compile(r"\\definecolor\s*\{([^}]*)\}\s*\{([^}]*)\}\s*\{([^}]*)\}")


def read_definecolors(tex):
    """Remember the \\definecolor{name}{model}{values} in a .tex/.sty text."""
    for name, model, vals in DEFINE_RE.findall(tex):
        rgb = parse_model(model.strip(), vals.strip())
        if rgb:
            DEFINED[name.strip()] = rgb


def parse_model(model, vals):
    try:
        if model == "HTML":
            return tuple(int(vals[k:k + 2], 16) / 255 for k in (0, 2, 4))
        nums = [float(v) for v in vals.split(",")]
        if model == "RGB":
            return tuple(n / 255 for n in nums)
        if model == "rgb":
            return tuple(nums)
        if model == "gray":
            return (nums[0],) * 3
        if model == "cmyk":
            c, m, y, k = nums
            return tuple((1 - x) * (1 - k) for x in (c, m, y))
    except (ValueError, IndexError):
        pass
    return None


def named(name):
    name = name.strip()
    return DEFINED.get(name) or BASE.get(name)


def to_rgb(expr):
    """xcolor expression -> 0..1 RGB tuple, or None."""
    parts = [p.strip() for p in expr.split("!")]
    rgb = named(parts[0])
    if rgb is None:
        return None
    k = 1
    while k < len(parts):
        try:
            pct = float(parts[k]) / 100
        except ValueError:
            return None
        other = named(parts[k + 1]) if k + 1 < len(parts) else BASE["white"]
        if other is None:
            return None
        rgb = tuple(pct * a + (1 - pct) * b for a, b in zip(rgb, other))
        k += 2
    return rgb


def css_color(expr):
    """CSS for an xcolor expression; unknown names are passed through (CSS
    understands many of them), with a warning if CSS would not either."""
    expr = (expr or "").strip()
    if expr in CSS_NAMES:
        return CSS_NAMES[expr]
    rgb = to_rgb(expr)
    if rgb:
        return "rgb(%d,%d,%d)" % tuple(round(255 * c) for c in rgb)
    if "!" in expr or not re.fullmatch(r"#?[A-Za-z0-9]+", expr):
        warn("colour not understood: %s" % expr)
    return expr
