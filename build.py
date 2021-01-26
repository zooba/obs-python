import hashlib
import json
import shutil
import sys

from pathlib import Path
from urllib.request import urlopen, urlretrieve
from zipfile import ZipFile

SRC = Path(__file__).absolute().parent / "src"

WIN32_PACKAGE_URL = "https://www.python.org/ftp/python/3.6.8/python-3.6.8-embed-amd64.zip"
WIN32_PACKAGE = "python-3.6.8-embed-amd64.zip"
WIN32_EXCLUDED = ["_distutils_findvs.pyd", "_msi.pyd", "pythonw.exe", "winsound.pyd"]

INSTALL = [
    ("requests", "2.25.1", ["requests/"]),
    ("urllib3", "1.26.2", ["urllib3/"]),
    ("certifi", "2020.12.5", ["certifi/"]),
    ("chardet", "4.0.0", ["chardet/"]),
    ("idna", "2.10", ["idna/"]),
]


def file_sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1024*1024), b""):
            h.update(b)
    return h.hexdigest()


def extract_whl(package, version, file_prefixes, outdir, tmpdir):
    with urlopen(f"https://pypi.org/pypi/{package}/json") as r:
        info = json.load(r)["releases"][version]
    whls = [i for i in info if i["packagetype"] == "bdist_wheel"]
    if len(whls) > 1:
        raise RuntimeError("unable to decide between {}".format(
            [i["filename"] for i in whls]
        ))
    whl = whls[0]
    whlfile = tmpdir / whl["filename"]
    if not whlfile.is_file() or file_sha256(whlfile) != whl["digests"]["sha256"]:
        print("Downloading", whl["url"], "to", whlfile)
        urlretrieve(whl["url"], filename=whlfile)
        if file_sha256(whlfile) != whl["digests"]["sha256"]:
            raise RuntimeError("downloaded file does not match digest")

    print("Extracting", whlfile, "to", outdir)
    with ZipFile(whlfile) as zf:
        names = [n for n in zf.namelist()
                 if any(n.startswith(p) for p in file_prefixes)
                 or not file_prefixes]
        zf.extractall(outdir, members=names)


def build_windows(outdir, tmpdir):
    pydir = outdir / "python"
    pydir.mkdir(parents=True, exist_ok=True)
    package = tmpdir / WIN32_PACKAGE
    if not package.is_file():
        print("Downloading", WIN32_PACKAGE_URL, "to", package)
        urlretrieve(WIN32_PACKAGE_URL, filename=package)
    print("Extracting", package, "to", pydir)
    with ZipFile(package) as zf:
        names = [n for n in zf.namelist() if n not in WIN32_EXCLUDED]
        zf.extractall(pydir, members=names)
    for pkname, pkver, pknames in INSTALL:
        extract_whl(pkname, pkver, pknames, pydir, tmpdir)

    #shutil.copytree(SRC / "obs", pydir / "obs", dirs_exist_ok=True)
    with open(pydir / "python36._pth", "w", encoding="utf-8") as f:
        print(".", file=f)
        print("python36.zip", file=f)
        print(SRC, file=f)


if __name__ == "__main__":
    try:
        outdir = Path(sys.argv[sys.argv.index("-o") + 1])
    except (LookupError, ValueError):
        outdir = Path.cwd() / "out"
    print("Building to:", outdir)
    try:
        tmpdir = Path(sys.argv[sys.argv.index("-t") + 1])
    except (LookupError, ValueError):
        tmpdir = Path.cwd() / "tmp"
    print("Temporary dir:", tmpdir)
    outdir.mkdir(parents=True, exist_ok=True)
    tmpdir.mkdir(parents=True, exist_ok=True)
    if sys.platform == "win32":
        build_windows(outdir, tmpdir)
