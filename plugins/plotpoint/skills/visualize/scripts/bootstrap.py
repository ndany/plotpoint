"""Dependency check for visualize.py. Standard library only: it runs before ppviz
(which imports the dependencies) so a missing package ends in a clear message,
not a traceback.

Exit code EXIT_SETUP (3) means: nothing was done; the environment needs setup.
"""

from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
from pathlib import Path

MIN_PYTHON = (3, 11)
EXIT_SETUP = 3
GUARD = "PLOTPOINT_BOOTSTRAPPED"  # set in the re-run so it can't loop

# import name -> package name in requirements.txt
DEPENDENCIES = {
    "jsonschema": "jsonschema",
    "yaml": "PyYAML",
    "vl_convert": "vl-convert-python",
}

REQUIREMENTS = Path(__file__).resolve().parent / "requirements.txt"


def missing_packages() -> list[str]:
    """Package names whose import name can't be found."""
    return [
        pkg
        for mod, pkg in DEPENDENCIES.items()
        if importlib.util.find_spec(mod) is None
    ]


def venv_dir() -> Path:
    """The per-user cache location for plotpoint's virtual environment."""
    home = Path.home()
    if sys.platform == "win32":
        base = Path(os.environ.get("LOCALAPPDATA") or home / "AppData" / "Local")
    elif sys.platform == "darwin":
        base = home / "Library" / "Caches"
    else:
        base = Path(os.environ.get("XDG_CACHE_HOME") or home / ".cache")
    return base / "plotpoint" / "venv"


def venv_python() -> Path:
    sub = ("Scripts", "python.exe") if sys.platform == "win32" else ("bin", "python")
    return venv_dir().joinpath(*sub)


def _in_cache_venv() -> bool:
    try:
        return Path(sys.prefix).resolve() == venv_dir().resolve()
    except OSError:
        return False


def _q(path: object) -> str:
    text = str(path)
    return f'"{text}"' if " " in text else text


def setup_message(missing: list[str], too_old: bool = False) -> str:
    """What to tell the user; commands are for the current OS."""
    windows = sys.platform == "win32"
    venv = venv_dir()
    py = venv_python()
    script = Path(__file__).resolve().parent / "visualize.py"
    lines = ["plotpoint: the environment is not ready, so nothing was done."]
    if too_old:
        have = ".".join(str(n) for n in sys.version_info[:3])
        want = ".".join(str(n) for n in MIN_PYTHON)
        lines.append(f"Python {want} or later is required; this is Python {have}.")
    if missing:
        lines.append(f"Missing Python packages: {', '.join(missing)}.")
    lines += [
        "",
        "Easiest, if uv is installed:",
        f"  uv run {_q(script)} <command> ...",
        "",
        "Otherwise create a virtual environment once (Python 3.11 or later):",
        f"  {'py -3' if windows else 'python3'} -m venv {_q(venv)}",
        f"  {_q(py)} -m pip install -r {_q(REQUIREMENTS)}",
        "then run the script with that environment's Python:",
        f"  {_q(py)} {_q(script)} <command> ...",
        "",
        "Do not use `pip install --break-system-packages` or install into the",
        "system Python; the system Python is managed by your OS or package manager.",
    ]
    return "\n".join(lines) + "\n"


def ensure() -> None:
    """Return if Python and the packages are usable. Otherwise run this script again
    with the cache venv's Python if one exists (and exit with its code), else print
    the setup message and exit with EXIT_SETUP."""
    too_old = sys.version_info < MIN_PYTHON
    missing = missing_packages()
    if too_old or missing:
        py = venv_python()
        if py.exists() and not os.environ.get(GUARD) and not _in_cache_venv():
            script = Path(__file__).resolve().parent / "visualize.py"
            env = dict(os.environ, **{GUARD: "1"})
            proc = subprocess.run(  # noqa: S603 - our own cache venv, argv forwarded as-is
                [str(py), str(script), *sys.argv[1:]], env=env
            )
            raise SystemExit(proc.returncode)
        sys.stderr.write(setup_message(missing, too_old))
        raise SystemExit(EXIT_SETUP)
