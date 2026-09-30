"""Walks the document: preamble settings (\\Set..., options), then the body's
sections, frames and template slides (\\SeminarTitleFrame, ...)."""
import re

from . import log
from .bibliography import bib_to_js
from .converter import Converter
from .images import resolve_image
from .log import warn
from .parsing import find_end, keyvals, read_arg, read_group, read_opt, skip_ws
from .source import read_tex
from .units import length_px

# \SetX{...} in titletemplates.sty -> DECK_CONFIG key in deck.js
SETTERS = {"SetTitle": "title", "SetSeminar": "seminar", "SetDegree": "degree",
           "SetPresenter": "presenter", "SetRollNo": "rollNo",
           "SetSupervisor": "supervisor", "SetDepartment": "department",
           "SetInstitute": "institute", "SetLogo": "logo",
           "SetAuthorOne": "author1", "SetAuthorTwo": "author2",
           "SetConference": "conference", "SetShortTitle": "shortTitle",
           "SetFootAuthor": "footAuthor"}

# option switches -> (DECK_CONFIG key, value)
SWITCHES = {"TitleBarOn": ("titleBar", "on"), "TitleBarOff": ("titleBar", "off"),
            "SectionNameOn": ("sectionName", "on"), "SectionNameOff": ("sectionName", "off"),
            "FooterOn": ("footer", "full"), "FooterNumberOnly": ("footer", "number"),
            "FooterOff": ("footer", "off"),
            "showdividers": ("dividers", "on"), "hidedividers": ("dividers", "off")}

# slide-making commands -> data-template in deck.js
TEMPLATE_CMDS = {"SeminarTitleFrame": "seminar", "ConferenceTitleFrame": "conference",
                 "OverviewFrame": "overview", "ReferencesFrame": "references",
                 "ThankYouFrame": "thanks"}

DEFAULTS = {"titleBar": "on", "sectionName": "on", "footer": "full", "titleHeight": 88,
            "dividers": "off"}


def convert(tex_path, root):
    """Convert `tex_path` (relative to `root`). Returns (config, slides) where
    config is the DECK_CONFIG dict and slides a list of <section> strings.
    Also writes html/references.js for every \\addbibresource."""
    src = read_tex(tex_path, root)
    pre, _, body = src.partition("\\begin{document}")
    body = body.partition("\\end{document}")[0]
    cv = Converter(root)

    config, state = read_preamble(cv, pre)
    slides = read_body(cv, body, state, default=dict(state))

    bib_to_js(re.findall(r"\\addbibresource\{([^}]*)\}", pre), root)
    return config, slides


# beamer class options that set the base font size
CLASS_SIZES = {"smaller": 10, "bigger": 12}


def class_font_size(pre):
    """Base font size in pt from \\documentclass[..., 8pt]{beamer} (default 11)."""
    m = re.search(r"\\documentclass\s*\[([^\]]*)\]", pre)
    for opt in (m.group(1).split(",") if m else []):
        opt = opt.strip()
        mm = re.fullmatch(r"(\d+)pt", opt)
        if mm:
            return int(mm.group(1))
        if opt in CLASS_SIZES:
            return CLASS_SIZES[opt]
    return 11


def read_preamble(cv, pre):
    """\\SetX{...} fields and the option switches before \\begin{document}."""
    config, state = {"fontSize": class_font_size(pre)}, dict(DEFAULTS)
    i = 0
    for m in re.finditer(r"\\([A-Za-z]+)", pre):
        if m.start() < i:
            continue
        name = m.group(1)
        if name in SETTERS:
            val, i = read_arg(pre, m.end())
            val = cv.inline(val).strip()
            if name == "SetLogo":
                val = resolve_image(re.sub(r"<[^>]+>", "", val), cv.root) or val + ".png"
            config[SETTERS[name]] = val
        elif name in SWITCHES:
            k, v = SWITCHES[name]
            state[k] = v
        elif name == "SetTitleHeight":
            val, i = read_arg(pre, m.end())
            px = length_px(val)
            if px is not None:
                state["titleHeight"] = px
    config.update(state)
    return config, state


def read_body(cv, body, state, default):
    """Top-level commands of the document body, in order. Option switches
    between frames change `state` for the frames after them."""
    slides = []
    pending_section = None
    token = re.compile(r"\\(begin\{frame\}|section\*?|[A-Za-z]+)")
    i = 0
    while True:
        m = token.search(body, i)
        if not m:
            break
        tok, i = m.group(1), m.end()
        if tok == "begin{frame}":
            end, after = find_end(body, i, "frame")
            slides.append(safe_frame(cv, body[i:end], state, default, pending_section,
                                     len(slides) + 1))
            pending_section = None
            i = after
        elif tok.startswith("section"):
            _, i = read_opt(body, i)
            title, i = read_arg(body, i)
            if pending_section:
                warn("section '%s' has no slides" % pending_section)
            pending_section = cv.inline(title).strip()
        elif tok in TEMPLATE_CMDS:
            opt, i = read_opt(body, i)
            attrs = ' data-template="%s"' % TEMPLATE_CMDS[tok]
            if opt:
                attrs += ' data-title="%s"' % cv.inline(opt).replace('"', "&quot;")
            slides.append("<section class=\"slide\"%s></section>" % attrs)
        elif tok in SWITCHES:
            k, v = SWITCHES[tok]
            state[k] = v
        elif tok == "SetTitleHeight":
            val, i = read_arg(body, i)
            px = length_px(val)
            if px is not None:
                state["titleHeight"] = px
        elif tok == "note":                    # \note after a frame: belongs to it
            aside = cv.note(body, i)
            i = cv.note_end
            if slides and slides[-1].endswith("</section>"):
                slides[-1] = slides[-1][:-len("</section>")] + aside + "\n</section>"
            else:
                warn("\\note outside a frame, with no frame before it: ignored")
        elif tok in ("def", "newcommand", "renewcommand"):
            _, i, _ = cv.command(tok, body, i)
        elif tok in ("printbibliography", "tableofcontents", "appendix", "nocite"):
            if tok == "nocite":
                _, i = read_arg(body, i)
        else:
            warn("ignored top-level command \\%s" % tok)
    log.where = ""
    return slides


def safe_frame(cv, s, state, default, section, number):
    """frame_html(), but warnings name the slide, and a frame that cannot be
    converted is reported and replaced by an error slide instead of stopping
    the whole run."""
    title = frame_titles(s, read_opt(s, 0)[1])[0]
    log.where = 'slide %d "%s"' % (number, " ".join((title or "").split()))
    try:
        return frame_html(cv, s, state, default, section)
    except Exception as e:                     # keep converting the other slides
        warn("could not convert this slide (%s: %s)" % (type(e).__name__, e))
        attrs = ' data-section="%s"' % section.replace('"', "&quot;") if section else ""
        return ('<section class="slide"%s>\n<h2>%s</h2>\n<div class="figure-placeholder">'
                'tex2html could not convert this slide -- see the warning in the '
                'terminal</div>\n</section>' % (attrs, cv.inline(title or "")))


def frame_html(cv, s, state, default, section):
    """One frame -> <section class="slide" ...> with <h2>/<h3> and its body."""
    opt, i = read_opt(s, 0)
    opts = keyvals(opt)
    title, sub, rest = frame_titles(s, i)
    cv.plus = 0                                    # `+` in overlay specs restarts

    attrs = []
    if section:
        # already HTML-escaped by inline(); only quotes need escaping here
        attrs.append('data-section="%s"' % re.sub(r"<[^>]+>", "", section).replace('"', "&quot;"))
    if "t" in opts:
        attrs.append('data-align="top"')
    for k, a in (("titleBar", "data-title-bar"), ("sectionName", "data-section-name"),
                 ("footer", "data-footer"), ("dividers", "data-dividers")):
        if state[k] != default[k]:
            attrs.append('%s="%s"' % (a, state[k]))
    if state["titleHeight"] != default["titleHeight"]:
        attrs.append('data-title-height="%d"' % state["titleHeight"])
    if "plain" in opts:
        attrs.append('data-footer="off"')

    parts = []
    if title is not None:
        parts.append("<h2>%s</h2>" % cv.inline(title).strip())
    if sub:
        parts.append("<h3>%s</h3>" % cv.inline(sub).strip())
    parts.append(cv.flow(rest))
    return '<section class="slide"%s>\n%s\n</section>' % (
        (" " + " ".join(attrs)) if attrs else "", "\n".join(parts))


def frame_titles(s, i):
    """Title and subtitle given as {..}{..} after \\begin{frame}, or with
    \\frametitle / \\framesubtitle inside. Returns (title, subtitle, rest)."""
    title = sub = None
    j = skip_ws(s, i)
    if j < len(s) and s[j] == "{":
        title, i = read_group(s, j)
        j = skip_ws(s, i)
        if j < len(s) and s[j] == "{":
            sub, i = read_group(s, j)
    rest = s[i:]
    m = re.search(r"\\frametitle", rest)
    if m and title is None:
        _, k = read_opt(rest, m.end())
        title, k = read_arg(rest, k)
        rest = rest[:m.start()] + rest[k:]
    m = re.search(r"\\framesubtitle", rest)
    if m and sub is None:
        sub, k = read_arg(rest, m.end())
        rest = rest[:m.start()] + rest[k:]
    return title, sub, rest
