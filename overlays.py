"""Beamer overlay specifications -- mixin for Converter.

    \\item<2->   \\begin{itemize}[<+->]   \\begin{block}<3->{..}
    \\onslide<2->{..}  \\uncover<2->{..}  \\visible<2->{..}  \\invisible<2>{..}
    \\only<2>{..}      \\alt<2>{on}{off}   \\onslide<3->  (switch: rest of frame)

Content is marked with data-spec="<beamer slide numbers>"; html/deck.js shows
it on the matching steps (step s of a slide = beamer overlay s+1). Hidden
content keeps its space, except for \\only and \\alt, which remove it.
`+` (incremental) is resolved here, counting from 1 in each frame.
"""
import re

from .parsing import read_arg
from .vocabulary import PARA

OVERLAY_CMDS = ("onslide", "uncover", "visible", "invisible", "only", "alt")


class OverlayMixin:
    plus = 0                     # last value of `+` in the current frame

    def read_spec(self, s, i):
        """Overlay spec <...> starting at s[i] (no space allowed, as in beamer).
        Returns (resolved spec or None, index after it)."""
        if i < len(s) and s[i] == "<":
            j = s.index(">", i)
            return self.resolve_spec(s[i + 1:j]), j + 1
        return None, i

    def resolve_spec(self, spec):
        """'+-' -> '3-' (next increment), '.-' -> '2-' (current); drops beamer
        actions and modes ('alert@2', '| handout:0')."""
        spec = spec.split("|")[0]
        spec = ",".join(p for p in spec.split(",") if "@" not in p)
        spec = re.sub(r"\s+", "", spec)
        spec = re.sub(r"\(\d*\)", "", spec)            # +(1) offsets: ignored
        if "+" in spec:
            self.plus += 1
            spec = spec.replace("+", str(self.plus))
        spec = spec.replace(".", str(max(self.plus, 1)))
        return spec or "1-"

    def overlay(self, name, s, i):
        """\\onslide, \\uncover, \\visible, \\invisible, \\only, \\alt."""
        spec, i = self.read_spec(s, i)
        if spec is None:
            spec = "1-"
        if name == "onslide":
            j = i
            while j < len(s) and s[j] in " \t":
                j += 1
            if j >= len(s) or s[j] != "{":             # switch form: rest of frame
                return '<span class="onslide" data-spec="%s"></span>' % spec, i, 0
        arg, i = read_arg(s, i)
        if name == "alt":
            other, i = read_arg(s, i)
            return (self.with_spec(arg, spec, only=True) +
                    self.with_spec(other, spec, only=True, invert=True)), i, 0
        return self.with_spec(arg, spec, only=(name == "only"),
                              invert=(name == "invisible")), i, 0

    def with_spec(self, raw, spec, only=False, invert=False):
        """Wrap converted content in an element carrying the overlay spec:
        a <span> for inline content, a <div> when it contains paragraphs."""
        attrs = ' data-spec="%s"' % spec
        if only:
            attrs += ' data-mode="only"'
        if invert:
            attrs += " data-invert"
        body = self.inline(raw)
        if PARA in body:
            return PARA + "<div%s>%s</div>" % (attrs, self.blocks(body)) + PARA
        return "<span%s>%s</span>" % (attrs, body)

    def spec_attr(self, spec):
        return ' data-spec="%s"' % spec if spec else ""
