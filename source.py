"""Reading the LaTeX source."""
import os
import re

from .log import warn


def strip_comments(s):
    """Remove % comments (but keep \\%). As in TeX, the comment also removes
    its line break and the next line's indentation, so a commented-out line
    does not create a paragraph break."""
    return re.sub(r"(?<!\\)%[^\n]*\n?[ \t]*", "", s)


def read_tex(path, root, seen=None):
    """Read a .tex file with \\input / \\include expanded, comments removed.
    Relative paths are taken from `root` (the project folder). The full
    paths of all files read are added to `seen`."""
    if seen is None:
        seen = set()
    full = path if path.endswith(".tex") else path + ".tex"
    full = os.path.join(root, full) if not os.path.isabs(full) else full
    if full in seen:
        return ""
    seen.add(full)                 # also when missing: --watch waits for it
    if not os.path.isfile(full):
        warn("\\input{%s}: file not found, skipped" % path)
        return ""
    with open(full, encoding="utf-8") as f:
        s = strip_comments(f.read())
    return re.sub(r"\\(?:input|include)\{([^}]*)\}",
                  lambda m: read_tex(m.group(1), root, seen), s)
