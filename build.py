import hashlib
import json
import os
import shutil
import subprocess
import sys

from pathlib import Path
from urllib.request import urlopen, urlretrieve
from zipfile import ZipFile

ROOT = Path(__file__).absolute().parent
SRC = ROOT / "src"

WIN32_PACKAGE_URL = "https://www.python.org/ftp/python/3.6.8/python-3.6.8-embed-amd64.zip"
WIN32_PACKAGE = "python-3.6.8-embed-amd64.zip"
NUGET_PACKAGE = "python"
NUGET_VERSION = "3.6.8"
WIN32_EXCLUDED = ["_distutils_findvs.pyd", "_msi.pyd", "pythonw.exe", "winsound.pyd"]

PACKAGE_FILTER = {}

with open(ROOT / "requirements.txt", "r", encoding="utf-8") as f:
    INSTALL = [
        (i[0], i[2])
        for i in (j.partition("==")
                  for j in (k.strip() for k in f)
                  if j and not j.startswith("#"))
        if i[1] == "=="
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
        names = []
        skipped = set()
        for n in zf.namelist():
            if n.partition("/")[0].endswith((".dist-info", ".data")):
                pass
            elif any(n.startswith(n2) for n2 in skipped):
                pass
            elif file_prefixes and any(n.startswith(n2) for n2 in file_prefixes):
                skipped.add(n + "/")
            else:
                names.append(n)
        zf.extractall(outdir, members=names)


def build_windows_package():
    subprocess.run(
        [sys.executable, "-m", "pymsbuild"],
        cwd=ROOT,
        env={
            **os.environ,
            "PYMSBUILD_WHEEL_TAG": "py36-cp36-win_amd64",
            "PYTHON_INCLUDES": str(ROOT / "deps/python/Include"),
            "PYTHON_LIBS": str(ROOT / "deps/python/libs"),
        },
        check=True,
    )

def build_windows(outdir, tmpdir, editable):
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
    for pkname, pkver in INSTALL:
        extract_whl(pkname, pkver, PACKAGE_FILTER.get(pkname, ()), pydir, tmpdir)

    if editable:
        with open(pydir / "python36._pth", "w", encoding="utf-8") as f:
            print(".", file=f)
            print("python36.zip", file=f)
            print(SRC, file=f)
        if (pydir / "obs").is_dir():
            shutil.rmtree(pydir / "obs")
    else:
        shutil.copytree(SRC / "obs", pydir / "obs", dirs_exist_ok=True)


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
    editable = "-e" in sys.argv
    inplace = "--inplace" in sys.argv
    print("Temporary dir:", tmpdir)
    outdir.mkdir(parents=True, exist_ok=True)
    tmpdir.mkdir(parents=True, exist_ok=True)
    if sys.platform == "win32":
        build_windows_package()
        if not inplace:
            build_windows(outdir, tmpdir, editable)
