from os import getenv
from pathlib import Path
from pymsbuild import *
from pymsbuild.cython import *

METADATA = {
    "Metadata-Version": "2.1",
    "Name": "obs-python",
    "Version": "1.0.0",
    "Author": "Steve Dower",
    "Author-email": "steve.dower@python.org",
    "Description": File("README.md"),
    "Description-Content-Type": "text/markdown",
    "Classifier": [
        "Development Status :: 3 - Alpha",
        "Programming Language :: Python :: 3.6",
    ],
}

INCLUDE = str(Path.cwd() / "deps/obs/Include")

PACKAGE = Package(
    "obs",
    PyFile(r"obs\*.py"),
    CythonPydFile(
        "_helper",
        ItemDefinition("ClCompile",
            AdditionalIncludeDirectories=ConditionalValue(INCLUDE + ";", prepend=True)
        ),
        PyxFile(r"obs\_helper.pyx"),
    ),
    source="src",
)

def init_PACKAGE(wheel_tag=None):
    ext = {
        "py36-cp36-win_amd64": ".cp36-win_amd64.pyd",
        "py37-cp37-win_amd64": ".cp37-win_amd64.pyd",
        "py38-cp38-win_amd64": ".cp38-win_amd64.pyd",
        "py39-cp39-win_amd64": ".cp39-win_amd64.pyd",
    }.get(wheel_tag, ".pyd")

    for p in PACKAGE:
        if isinstance(p, PydFile):
            p.options["TargetExt"] = ext
