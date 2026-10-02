"""Converter: turns LaTeX text into HTML.

The work is split across mixins -- commands.py (\\commands),
environments.py (\\begin{...}), animation.py (animateinline) and
overlays.py (<overlay specs>, \\only, \\uncover, ...) -- and this
module holds the core: the character-level inline pass and the block-level
flow pass that resolves paragraphs, \\hfill rows and \\centering.
"""
import html
import re

from .animation import AnimationMixin
from .commands import CommandsMixin
from .environments import EnvironmentsMixin
from .overlays import OverlayMixin
from .parsing import read_group
from .vocabulary import CENTER, HFILL, PARA


class Converter(CommandsMixin, EnvironmentsMixin, AnimationMixin, OverlayMixin):
    def __init__(self, root):
        self.root = root          # project folder; image paths are relative to it
        self.macros = {}          # \def\name{value}
        self.counters = {"figure": 0, "table": 0}   # \caption numbers, deck-wide
        self.floats = []          # open figure/table environments
        self.labels = {}          # \label key -> number (\ref is resolved at the end)

    # ---------------------------------------------------------- flows
    def flow(self, s):
        """Convert block-level content: paragraphs, \\hfill rows, \\centering."""
        return self.blocks(self.inline(s))

    def blocks(self, body):
        """Resolve the PARA / HFILL / CENTER markers of converted content."""
        center = CENTER in body
        body = body.replace(CENTER, "")
        out = []
        for para in re.split(re.escape(PARA), body):
            if not para.strip():
                continue
            if HFILL in para:
                cells = [c.strip() for c in para.split(HFILL)]
                cells = [c for c in cells if c]
                out.append('<div class="row">' +
                           "".join("<div>%s</div>" % c if not c.startswith("<div")
                                   else c for c in cells) + "</div>")
            elif para.strip().startswith('<div class="rows"'):
                out.append(para.strip())             # rows fill the body: no wrapper
            else:
                out.append('<div class="p">%s</div>' % para.strip())
        res = "\n".join(out)
        if center:
            res = '<div class="center">%s</div>' % res
        return res

    # ---------------------------------------------------------- inline
    def inline(self, s):
        """Convert text, commands, groups and math. Declarations such as
        \\small open a <span> that is closed at the end of the current group;
        at a paragraph/block break (PARA) the open spans are closed and
        reopened, so {\\scriptsize ... \\begin{table}...} applies to the block."""
        out, opened_tags, i = [], [], 0
        s = s.replace("\r", "")

        def add(piece):
            if opened_tags and PARA in piece:
                piece = piece.replace(PARA, "</span>" * len(opened_tags) + PARA
                                      + "".join(opened_tags))
            out.append(piece)

        while i < len(s):
            c = s[i]
            if c == "\\":
                m = re.match(r"\\([A-Za-z@]+\*?|.)", s[i:])
                if not m:
                    i += 1
                    continue
                name, i = m.group(1), i + len(m.group(0))
                res, i, opened = self.command(name, s, i)
                if opened:                         # res is the opening <span ...>
                    out.append(res)
                    opened_tags.append(res)
                else:
                    add(res)
            elif c == "{":
                inner, i = read_group(s, i)
                add(self.inline(inner))
            elif c == "}":
                i += 1
            elif c == "$":
                if s.startswith("$$", i):
                    j = s.index("$$", i + 2)
                    add("\\[" + html.escape(s[i + 2:j], quote=False) + "\\]")
                    i = j + 2
                else:
                    j = i + 1
                    while s[j] != "$" or s[j - 1] == "\\":
                        j += 1
                    add("\\(" + html.escape(s[i + 1:j], quote=False) + "\\)")
                    i = j + 1
            elif c == "~":
                add("&nbsp;")
                i += 1
            elif c == "\n" and re.match(r"\n[ \t]*\n", s[i:]):
                add(PARA)
                i = re.match(r"\n[ \t]*\n\s*", s[i:]).end() + i
            elif s.startswith("---", i):
                add("—"); i += 3
            elif s.startswith("--", i):
                add("–"); i += 2
            elif s.startswith("``", i):
                add("“"); i += 2
            elif s.startswith("''", i):
                add("”"); i += 2
            elif c == "`":
                add("‘"); i += 1
            elif c == "'":
                add("’"); i += 1
            else:
                add(html.escape(c, quote=False))
                i += 1
        return "".join(out) + "</span>" * len(opened_tags)

    def expand(self, s):
        """Replace \\def'd macros in raw text (used for file paths)."""
        for _ in range(5):
            new = re.sub(r"\\([A-Za-z@]+)",
                         lambda m: self.macros.get(m.group(1), m.group(0)), s)
            if new == s:
                break
            s = new
        return s.strip()
