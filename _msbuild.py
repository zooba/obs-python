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

INCLUDES = Path(getenv("OBS_SOURCE")) / "libobs"
CL_COMPILE = ItemDefinition(
    "ClCompile",
    AdditionalIncludeDirectories=ConditionalValue(str(INCLUDES) + ";", prepend=True)
)

LIBS = Path.cwd() / "deps/obs"
LINK = ItemDefinition(
    "Link",
    AdditionalDependencies=ConditionalValue("obs.lib;", prepend=True),
    AdditionalLibraryDirectories=ConditionalValue(str(LIBS) + ";", prepend=True)
)

PACKAGE = Package(
    "obs",
    PyFile(r"obs\*.py"),
    CythonPydFile(
        "_helper",
        CL_COMPILE,
        LINK,
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
