"""Entry point:  python3 path/to/beamer2html [main.tex] [-o slides.html]"""
import importlib
import os
import sys

if __package__ in (None, ""):          # run as a directory: python3 path/to/beamer2html
    here = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, os.path.dirname(here))
    main = importlib.import_module(os.path.basename(here) + ".cli").main
else:                                  # run as a module:  python3 -m beamer2html
    from .cli import main

sys.exit(main())
