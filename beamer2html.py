#!/usr/bin/env python3
"""beamer2html command: a launcher a TeX distribution can link to (it runs
the package in the folder this file is in, following symlinks).

    beamer2html [main.tex] [-o slides.html] [--pack ...] [--watch]
"""
import importlib
import os
import sys

here = os.path.dirname(os.path.realpath(__file__))
sys.path[0] = os.path.dirname(here)        # not this folder: this file would shadow the package
sys.exit(importlib.import_module(os.path.basename(here) + ".cli").main())
