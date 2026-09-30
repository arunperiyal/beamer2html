"""Low-level readers for LaTeX syntax: {arguments}, [options], environments."""
import re

from .log import warn


def skip_ws(s, i):
    while i < len(s) and s[i] in " \t\n":
        i += 1
    return i


def read_group(s, i, open_="{", close="}"):
    """s[i] must be open_; returns (content, index after close)."""
    depth, j = 0, i
    while j < len(s):
        c = s[j]
        if c == "\\":
            j += 2
            continue
        if c == open_:
            depth += 1
        elif c == close:
            depth -= 1
            if depth == 0:
                return s[i + 1:j], j + 1
        j += 1
    raise ValueError("unbalanced %s at: %s" % (open_, s[i:i + 60]))


def read_arg(s, i):
    """Mandatory argument: {...} or a single token. Returns (arg, i); a missing
    argument gives ("", i) and a warning."""
    j = skip_ws(s, i)
    if j < len(s) and s[j] == "{":
        return read_group(s, j)
    if j < len(s) and s[j] == "\\":
        m = re.match(r"\\[A-Za-z@]+|\\.", s[j:])
        return m.group(0), j + len(m.group(0))
    if j < len(s):
        return s[j], j + 1
    warn("a command is missing an argument (near: %s)" % " ".join(s[-40:].split()))
    return "", i


def read_opt(s, i):
    """Optional argument [...]. Returns (arg or None, i)."""
    j = skip_ws(s, i)
    if j < len(s) and s[j] == "[":
        return read_group(s, j, "[", "]")
    return None, i


def find_end(s, i, env):
    """Index range of the body of \\begin{env} whose body starts at i."""
    pat = re.compile(r"\\(begin|end)\{" + re.escape(env) + r"\}")
    depth = 1
    for m in pat.finditer(s, i):
        depth += 1 if m.group(1) == "begin" else -1
        if depth == 0:
            return m.start(), m.end()
    raise ValueError("no \\end{%s}" % env)


def split_items(body, cmd="item"):
    """Split a list body at its own \\item's -- or \\<cmd>'s -- not those of
    nested lists."""
    items, depth, start = [], 0, None
    for m in re.finditer(r"\\(begin|end)\{[^}]*\}|\\%s\b" % cmd, body):
        tok = m.group(0)
        if tok.startswith("\\begin"):
            depth += 1
        elif tok.startswith("\\end"):
            depth -= 1
        elif depth == 0:
            if start is not None:
                items.append(body[start:m.start()])
            start = m.end()
    if start is not None:
        items.append(body[start:])
    return items


def split_top(s, sep=","):
    """Split at `sep` outside {braces}."""
    parts, depth, cur = [], 0, ""
    for c in s:
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
        if c == sep and depth == 0:
            parts.append(cur)
            cur = ""
        else:
            cur += c
    parts.append(cur)
    return parts


def keyvals(opt):
    """'autoplay, width=3cm, controls={play,step}' ->
    {'autoplay': True, 'width': '3cm', 'controls': 'play,step'}"""
    out = {}
    for part in split_top(opt or ""):
        if "=" in part:
            k, v = part.split("=", 1)
            v = v.strip()
            if v.startswith("{") and v.endswith("}"):
                v = v[1:-1]
            out[k.strip()] = v.strip()
        elif part.strip():
            out[part.strip()] = True
    return out
