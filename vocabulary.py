"""Lookup tables for the LaTeX the converter understands, and the internal
markers it uses while building HTML."""

# {\small ...} etc. -> font-size in em
SIZES = {"tiny": 0.5, "scriptsize": 0.7, "footnotesize": 0.8, "small": 0.9,
         "normalsize": 1, "large": 1.2, "Large": 1.44, "LARGE": 1.73,
         "huge": 2.07, "Huge": 2.49}

# {\bfseries ...} etc. -> CSS
DECLS = {"bfseries": "font-weight:bold", "itshape": "font-style:italic",
         "mdseries": "font-weight:normal", "upshape": "font-style:normal",
         "rmfamily": "", "sffamily": "font-family:sans-serif",
         "ttfamily": "font-family:monospace"}

# \textbf{...} etc. -> HTML tag
WRAPS = {"textbf": "b", "emph": "em", "textit": "i", "underline": "u",
         "texttt": "code", "textsf": "span", "textrm": "span", "mbox": "span",
         "text": "span", "textup": "span", "textsc": "span"}

# commands dropped without a warning
IGNORE = {"centering", "raggedright", "raggedleft", "noindent",
          "par", "relax", "protect", "linebreak", "newline", "smallskip",
          "medskip", "bigskip", "vfill", "null", "strut", "leavevmode",
          "maketitle", "clearpage", "newpage", "frametitle", "framesubtitle",
          "usebeamerfont", "usebeamercolor", "setlength", "addtolength"}

# environments passed to MathJax unchanged
MATH_ENVS = {"equation", "equation*", "align", "align*", "gather", "gather*",
             "multline", "multline*", "eqnarray", "eqnarray*", "split"}

# \& \% \, ... -> HTML
TEXT_SYMBOLS = {"&": "&amp;", "%": "%", "_": "_", "$": "$", "#": "#",
                "{": "{", "}": "}", ",": "&thinsp;", ";": "&ensp;",
                " ": " ", "!": "", "-": "&shy;", "/": ""}

# colour names from beamer2html.sty -> CSS (others pass through: red, gray...)

# \pause -> empty marker element; html/deck.js hides whatever follows the
# k-th marker of a slide until step k is reached.
PAUSE = '<span class="pause"></span>'

# \ref{key} -> REF_MARK % key; resolved after the whole document is read,
# so a reference may come before its \label.
REF_MARK = "\x00R:%s\x00"
REF_RE = "\x00R:([^\x00]*)\x00"

# Internal markers placed in the HTML while converting, resolved by
# Converter.flow(): paragraph break, \hfill, \centering.
PARA, HFILL, CENTER = "\x00P\x00", "\x00H\x00", "\x00C\x00"
