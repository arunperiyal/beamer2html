"""Build the CTAN upload of beamer2html:  python3 ctan/build.py

Writes ctan/build/beamer2html/ (to look through) and ctan/build/beamer2html.zip
(to upload at https://ctan.org/upload), from the files git tracks (or would
track) in the working tree:

    beamer2html/
      README.md                 ctan/README.md
      LICENSE
      doc/beamer2html.pdf       compiled here from ctan/doc/beamer2html.tex
      doc/beamer2html.tex
      doc/example/              template/
      tex/beamer2html.sty       latex/beamer2html.sty
      scripts/beamer2html/      the program (*.py, assets/)

Left out: nvim/, the .git* files, generated files. Files are stored with
mode 644 and folders 755, as CTAN asks.
"""
import os
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile

CTAN = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(CTAN)
BUILD = os.path.join(CTAN, "build")
NAME = "beamer2html"


def tracked():
    """Repository files git tracks or would track (not ignored)."""
    out = subprocess.run(["git", "ls-files", "--cached", "--others", "--exclude-standard"],
                         cwd=REPO, capture_output=True, text=True, check=True).stdout
    return sorted(p for p in out.splitlines() if os.path.isfile(os.path.join(REPO, p)))


def layout(files):
    """{path in the package: source path} for the CTAN package."""
    out = {
        "README.md": os.path.join(CTAN, "README.md"),
        "LICENSE": os.path.join(REPO, "LICENSE"),
        "doc/beamer2html.tex": os.path.join(CTAN, "doc", "beamer2html.tex"),
        "tex/beamer2html.sty": os.path.join(REPO, "latex", "beamer2html.sty"),
    }
    for p in files:
        parts = p.split("/")
        if any(part.startswith(".") for part in parts):
            continue                                   # .gitignore, ...
        if len(parts) == 1 and p.endswith(".py"):
            out["scripts/%s/%s" % (NAME, p)] = os.path.join(REPO, p)
        elif parts[0] == "assets":
            out["scripts/%s/%s" % (NAME, p)] = os.path.join(REPO, p)
        elif parts[0] == "template":
            out["doc/example/" + "/".join(parts[1:])] = os.path.join(REPO, p)
    return out


def versions():
    """The version and date in __init__.py, the .sty and the manual."""
    def grab(path, pattern):
        with open(path, encoding="utf-8") as f:
            m = re.search(pattern, f.read())
        return m.groups() if m else None
    return {
        "__init__.py": grab(os.path.join(REPO, "__init__.py"),
                            r'__version__ = "([^"]+)"\s+__date__ = "([^"]+)"'),
        "beamer2html.sty": grab(os.path.join(REPO, "latex", "beamer2html.sty"),
                                r"\\ProvidesPackage\{beamer2html\}\[(\d+)/(\d+)/(\d+) v([^ \]]+)"),
        "manual": grab(os.path.join(CTAN, "doc", "beamer2html.tex"),
                       r"(?s)version ([0-9.]+)\}\s*\\author.*?\\date\{([^}]+)\}"),
    }


def manual(dest):
    """Compile the manual (pdflatex, twice) into dest."""
    with tempfile.TemporaryDirectory() as tmp:
        for _ in range(2):
            r = subprocess.run(["pdflatex", "-interaction=nonstopmode", "-halt-on-error",
                                "-output-directory", tmp, "beamer2html.tex"],
                               cwd=os.path.join(CTAN, "doc"), capture_output=True, text=True)
            if r.returncode:
                sys.exit("the manual does not compile: see %s\n%s" % (
                    os.path.join(tmp, "beamer2html.log"), r.stdout[-2000:]))
        shutil.copy(os.path.join(tmp, "beamer2html.pdf"), dest)


def main():
    v = versions()
    init = v["__init__.py"]
    sty = v["beamer2html.sty"]
    man = v["manual"]
    if not (init and sty and man):
        sys.exit("version not found in: %s" % ", ".join(k for k, x in v.items() if not x))
    version, date = init
    if sty[3] != version or "-".join(sty[:3]) != date or man != (version, date):
        sys.exit("versions differ: __init__.py %s %s, beamer2html.sty %s %s, manual %s %s"
                 % (version, date, sty[3], "-".join(sty[:3]), man[0], man[1]))

    files = layout(tracked())
    stage = os.path.join(BUILD, NAME)
    shutil.rmtree(BUILD, ignore_errors=True)
    for rel, src in files.items():
        dst = os.path.join(stage, rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copyfile(src, dst)
    manual(os.path.join(stage, "doc", "beamer2html.pdf"))

    zpath = os.path.join(BUILD, NAME + ".zip")
    count = 0
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
        for dirpath, dirs, names in os.walk(stage):
            dirs.sort()
            rel_dir = os.path.relpath(dirpath, BUILD)
            info = zipfile.ZipInfo(rel_dir + "/")
            info.external_attr = (0o40755 << 16) | 0x10
            z.writestr(info, "")
            for n in sorted(names):
                info = zipfile.ZipInfo.from_file(os.path.join(dirpath, n),
                                                 os.path.join(rel_dir, n))
                info.external_attr = 0o100644 << 16
                info.compress_type = zipfile.ZIP_DEFLATED
                with open(os.path.join(dirpath, n), "rb") as f:
                    z.writestr(info, f.read())
                count += 1
    print("beamer2html %s (%s): %d files, %.1f MB\n  %s\n  %s" % (
        version, date, count, os.path.getsize(zpath) / 1e6, stage, zpath))


if __name__ == "__main__":
    main()
