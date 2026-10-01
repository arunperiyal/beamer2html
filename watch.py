"""--watch: rebuild whenever a source file changes (like latexmk -pvc).

Changes are detected by polling modification times, so nothing has to be
installed and it works on any OS. The list of watched files comes from each
build (main .tex, every \\input file, the .bib, the images the slides use,
and the tool's own deck.js/deck.css/titletemplates.sty), so files added to
the deck are picked up. A deck built in watch mode reloads itself in the
browser after each rebuild (see the live-reload part of deck.js).
"""
import os
import time

POLL = 0.5          # seconds between checks
SETTLE = 0.3        # wait after a change, so the editor has finished writing


def snapshot(paths):
    state = {}
    for p in paths:
        try:
            state[p] = os.stat(p).st_mtime_ns
        except OSError:
            state[p] = None                    # missing (e.g. mid-save): also a change
    return state


def watch(build):
    """build(changed) -> set of files to watch, or None if the build failed
    (the previous list is kept). Called once at the start with changed=None,
    then after every change. Runs until Ctrl+C."""
    files = build(None) or set()
    state = snapshot(files)
    print("watching %d files -- Ctrl+C to stop" % len(files), flush=True)
    try:
        while True:
            time.sleep(POLL)
            now = snapshot(files)
            changed = sorted(p for p in files if now[p] != state.get(p))
            if not changed:
                continue
            time.sleep(SETTLE)
            files = build(changed) or files
            state = snapshot(files)
    except KeyboardInterrupt:
        print("\nstopped watching")
