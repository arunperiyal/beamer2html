"""Entry point:  python3 tools/tex2html [main.tex] [-o slides.html]"""
import os
import sys

if __package__ in (None, ""):          # run as a directory: python3 tools/tex2html
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from tex2html.cli import main
else:                                  # run as a module:  python3 -m tex2html
    from .cli import main

sys.exit(main())
