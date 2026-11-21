"""Video posters: the first frame of a video, and a YouTube thumbnail.

LaTeX cannot run ffmpeg or download a picture, so with --posters the converter
makes them, and beamer2html.sty finds them by name:

    figures/flow.mp4         ->  figures/flow.poster.jpg      (ffmpeg, one frame)
    \\slidevideo{youtu.be/ID} ->  html/cache/yt-ID.jpg         (downloaded once)

Both are only made when `enabled` is set (--posters), when the author gave no
poster=, and when the file is missing or older than the video. Without ffmpeg
(or without network) there is one warning and the deck builds as before.
ffmpeg is looked up on PATH; BEAMER2HTML_FFMPEG names another one.
"""
import os
import re
import shutil
import subprocess
import urllib.request

from .log import warn

enabled = False                      # set by --posters

YT_ID = r"[A-Za-z0-9_-]{11}"
YT_RE = re.compile(
    r"^(?:https?://)?(?:(?:www\.|m\.)?youtube(?:-nocookie)?\.com/(?:watch\?(?:[^#]*&)?v=|embed/|shorts/|live/)"
    r"|youtu\.be/|youtube:)(" + YT_ID + r")(?![A-Za-z0-9_-])")
THUMB = "https://i.ytimg.com/vi/%s/hqdefault.jpg"
CACHE = os.path.join("html", "cache")


def youtube_id(path):
    """The video id of a YouTube address (youtu.be/ID, youtube.com/watch?v=ID,
    /embed/ID, /shorts/ID, or youtube:ID), else None."""
    m = YT_RE.match(path.strip().replace("\\_", "_").replace("\\&", "&"))
    return m.group(1) if m else None


def poster_path(video):
    """figures/flow.mp4 -> figures/flow.poster.jpg"""
    return os.path.splitext(video)[0] + ".poster.jpg"


def yt_thumb_path(vid):
    return os.path.join(CACHE, "yt-%s.jpg" % vid)


def _fresh(out, source=None):
    if not os.path.isfile(out) or os.path.getsize(out) == 0:
        return False
    return source is None or os.path.getmtime(out) >= os.path.getmtime(source)


def _ffmpeg():
    exe = os.environ.get("BEAMER2HTML_FFMPEG") or shutil.which("ffmpeg")
    if not exe:
        warn("--posters: ffmpeg not found, so no video posters (install it, or set "
             "BEAMER2HTML_FFMPEG)")
    return exe


def make_poster(video, root, start=None):
    """Make `<video>.poster.jpg` (relative path returned) unless it is there
    and newer than the video. The frame is at `start` seconds, else 1 s in
    (the first frame for a shorter clip); at most 1280 px wide. None on failure."""
    out_rel = poster_path(video)
    out = os.path.join(root, out_rel)
    src = os.path.join(root, video)
    if _fresh(out, src):
        return out_rel
    exe = _ffmpeg()
    if not exe:
        return None
    try:
        t = float(start) if start else 1.0
    except ValueError:
        t = 1.0
    for at in (t, 0.0):                           # a time past the end gives no frame
        if os.path.isfile(out):
            os.remove(out)
        cmd = [exe, "-v", "error", "-y", "-ss", "%g" % at, "-i", src, "-frames:v", "1",
               "-vf", "scale='min(1280,iw)':-2", "-q:v", "3", "-update", "1", out]
        try:
            subprocess.run(cmd, check=True, capture_output=True, timeout=60)
        except (OSError, subprocess.SubprocessError):
            continue
        if _fresh(out):
            return out_rel
    warn("--posters: could not take a frame from %s" % video)
    return None


def fetch_thumb(vid, root):
    """Download the YouTube thumbnail to html/cache/yt-ID.jpg once. This is the
    converter's only network access, and only with --posters."""
    out_rel = yt_thumb_path(vid)
    out = os.path.join(root, out_rel)
    if _fresh(out):
        return out_rel
    try:
        os.makedirs(os.path.dirname(out), exist_ok=True)
        with urllib.request.urlopen(THUMB % vid, timeout=10) as r:
            data = r.read()
        if not data:
            raise OSError("empty")
        with open(out, "wb") as f:
            f.write(data)
        return out_rel
    except (OSError, ValueError) as e:
        warn("--posters: could not download the YouTube thumbnail of %s (%s)" % (vid, e))
        return None
