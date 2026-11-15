"""The dependency check: message per OS, exit code, PEP 723 parity."""

from __future__ import annotations

import os
import re
import subprocess
import sys
import tomllib
from pathlib import Path

import bootstrap
import pytest
from conftest import SCRIPTS

VISUALIZE = SCRIPTS / "visualize.py"


def _requirements() -> list[str]:
    lines = (SCRIPTS / "requirements.txt").read_text(encoding="utf-8").splitlines()
    return [ln.strip() for ln in lines if ln.strip() and not ln.startswith("#")]


def _platform(monkeypatch, plat: str, home: Path) -> None:
    monkeypatch.setattr(sys, "platform", plat)
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: home))
    for var in ("LOCALAPPDATA", "XDG_CACHE_HOME"):
        monkeypatch.delenv(var, raising=False)


def test_message_macos(monkeypatch):
    _platform(monkeypatch, "darwin", Path("/h/pat"))
    msg = bootstrap.setup_message(["PyYAML"])
    venv = Path("/h/pat/Library/Caches/plotpoint/venv")
    py = venv / "bin" / "python"
    assert "Missing Python packages: PyYAML." in msg
    assert f"python3 -m venv {venv}" in msg
    assert f"{py} -m pip install -r {bootstrap.REQUIREMENTS}" in msg
    assert f"{py} {SCRIPTS / 'visualize.py'}" in msg
    assert "uv run" in msg
    assert "--break-system-packages" in msg and "Do not" in msg
    assert "py -3" not in msg


def test_message_linux_xdg(monkeypatch):
    _platform(monkeypatch, "linux", Path("/h/pat"))
    assert bootstrap.venv_dir() == Path("/h/pat/.cache/plotpoint/venv")
    monkeypatch.setenv("XDG_CACHE_HOME", "/var/cache/pat")
    assert bootstrap.venv_dir() == Path("/var/cache/pat/plotpoint/venv")
    assert "python3 -m venv" in bootstrap.setup_message(["jsonschema"])


def test_message_windows(monkeypatch):
    _platform(monkeypatch, "win32", Path("/h/pat"))
    monkeypatch.setenv("LOCALAPPDATA", "/local/pat")
    msg = bootstrap.setup_message(["PyYAML", "vl-convert-python"])
    venv = Path("/local/pat/plotpoint/venv")
    py = venv / "Scripts" / "python.exe"
    assert "Missing Python packages: PyYAML, vl-convert-python." in msg
    assert f"py -3 -m venv {venv}" in msg
    assert f"{py} -m pip install -r {bootstrap.REQUIREMENTS}" in msg
    assert f"{py} {SCRIPTS / 'visualize.py'}" in msg
    assert "uv run" in msg
    assert "--break-system-packages" in msg
    assert "python3 -m venv" not in msg


def test_windows_without_localappdata(monkeypatch):
    _platform(monkeypatch, "win32", Path("/h/pat"))
    assert bootstrap.venv_dir() == Path("/h/pat/AppData/Local/plotpoint/venv")


def test_paths_with_spaces_are_quoted(monkeypatch):
    _platform(monkeypatch, "darwin", Path("/h/Pat Smith"))
    venv = Path("/h/Pat Smith/Library/Caches/plotpoint/venv")
    assert f'-m venv "{venv}"' in bootstrap.setup_message(["PyYAML"])


def test_python_too_old(monkeypatch, capsys):
    monkeypatch.setattr(sys, "version_info", (3, 9, 1, "final", 0))
    monkeypatch.setattr(bootstrap, "missing_packages", list)
    with pytest.raises(SystemExit) as exc:
        bootstrap.ensure()
    assert exc.value.code == bootstrap.EXIT_SETUP == 3
    err = capsys.readouterr().err
    assert "Python 3.11 or later is required; this is Python 3.9.1." in err


def test_ok_when_everything_present():
    bootstrap.ensure()  # the dev environment has all dependencies


def test_missing_packages_listed(monkeypatch):
    monkeypatch.setattr(bootstrap, "DEPENDENCIES", {"no_such_module_xyz": "Fake-Pkg"})
    assert bootstrap.missing_packages() == ["Fake-Pkg"]


def test_cli_stops_when_dependencies_missing():
    """-S drops site-packages, so the dependencies are genuinely not importable."""
    proc = subprocess.run(
        [sys.executable, "-I", "-S", str(VISUALIZE), "validate", "renderRequest", "x"],
        env=dict(os.environ),
        capture_output=True,
        check=False,
    )
    err = proc.stderr.decode("utf-8")
    assert proc.returncode == 3
    assert proc.stdout == b""
    for pkg in ("jsonschema", "PyYAML", "vl-convert-python"):
        assert pkg in err
    assert "-m venv" in err and "pip install -r" in err and "uv run" in err
    assert "--break-system-packages" in err
    assert "Traceback" not in err


def test_cli_runs_normally_with_dependencies():
    proc = subprocess.run(
        [sys.executable, str(VISUALIZE), "--help"], capture_output=True, check=False
    )
    assert proc.returncode == 0


def test_pep723_dependencies_match_requirements():
    src = VISUALIZE.read_text(encoding="utf-8")
    block = re.search(r"^# /// script\n((?:#.*\n)+?)# ///$", src, re.M)
    assert block, "visualize.py needs a PEP 723 script block"
    toml = "".join(ln[2:] for ln in block.group(1).splitlines(keepends=True))
    meta = tomllib.loads(toml)
    assert meta["dependencies"] == _requirements()
    assert meta["requires-python"] == ">=3.11"
    assert bootstrap.MIN_PYTHON == (3, 11)


def test_dependency_map_covers_requirements():
    names = {p.lower() for p in bootstrap.DEPENDENCIES.values()}
    reqs = {re.split(r"[<>=]", ln)[0].strip().lower() for ln in _requirements()}
    assert names == reqs


# --- re-running with the cache venv ------------------------------------------------


@pytest.fixture(autouse=True)
def _isolated_cache(tmp_path, monkeypatch):
    """Never see a real cache venv; all platforms' cache roots point into tmp."""
    for var in ("HOME", "USERPROFILE", "LOCALAPPDATA", "XDG_CACHE_HOME"):
        monkeypatch.setenv(var, str(tmp_path / var))
    monkeypatch.delenv(bootstrap.GUARD, raising=False)


def _fake_venv_python() -> Path:
    py = bootstrap.venv_python()
    py.parent.mkdir(parents=True)
    py.write_text("", encoding="utf-8")
    return py


def _break_deps(monkeypatch):
    monkeypatch.setattr(bootstrap, "missing_packages", lambda: ["PyYAML"])


class _Recorder:
    def __init__(self, code: int = 0):
        self.calls: list[tuple[list[str], dict]] = []
        self.code = code

    def __call__(self, cmd, **kwargs):
        self.calls.append((cmd, kwargs))
        return subprocess.CompletedProcess(cmd, self.code)


def test_reruns_with_cache_venv_and_forwards_exit_code(monkeypatch, capsys):
    py = _fake_venv_python()
    _break_deps(monkeypatch)
    rec = _Recorder(code=7)
    monkeypatch.setattr(subprocess, "run", rec)
    monkeypatch.setattr(sys, "argv", ["visualize.py", "validate", "k", "f"])
    with pytest.raises(SystemExit) as exc:
        bootstrap.ensure()
    assert exc.value.code == 7
    ((cmd, kwargs),) = rec.calls
    assert cmd == [str(py), str(SCRIPTS / "visualize.py"), "validate", "k", "f"]
    assert kwargs["env"][bootstrap.GUARD] == "1"
    assert capsys.readouterr().err == ""  # the outer run prints no message


def test_no_rerun_without_cache_venv(monkeypatch, capsys):
    _break_deps(monkeypatch)
    rec = _Recorder()
    monkeypatch.setattr(subprocess, "run", rec)
    with pytest.raises(SystemExit) as exc:
        bootstrap.ensure()
    assert exc.value.code == 3 and not rec.calls
    assert "Missing Python packages: PyYAML." in capsys.readouterr().err


def test_no_rerun_when_already_in_cache_venv(monkeypatch, capsys):
    _fake_venv_python()
    _break_deps(monkeypatch)
    monkeypatch.setattr(sys, "prefix", str(bootstrap.venv_dir()))
    rec = _Recorder()
    monkeypatch.setattr(subprocess, "run", rec)
    with pytest.raises(SystemExit) as exc:
        bootstrap.ensure()
    assert exc.value.code == 3 and not rec.calls
    assert capsys.readouterr().err.count("not ready") == 1


def test_loop_guard(monkeypatch, capsys):
    _fake_venv_python()
    _break_deps(monkeypatch)
    monkeypatch.setenv(bootstrap.GUARD, "1")
    rec = _Recorder()
    monkeypatch.setattr(subprocess, "run", rec)
    with pytest.raises(SystemExit) as exc:
        bootstrap.ensure()
    assert exc.value.code == 3 and not rec.calls
    assert capsys.readouterr().err.count("not ready") == 1


def test_reruns_when_python_too_old(monkeypatch):
    _fake_venv_python()
    monkeypatch.setattr(sys, "version_info", (3, 9, 1, "final", 0))
    rec = _Recorder()
    monkeypatch.setattr(subprocess, "run", rec)
    with pytest.raises(SystemExit) as exc:
        bootstrap.ensure()
    assert exc.value.code == 0 and len(rec.calls) == 1


def _make_cache_venv(share_deps: bool) -> Path:
    venv = bootstrap.venv_dir()
    subprocess.run(
        [sys.executable, "-m", "venv", "--without-pip", str(venv)], check=True
    )
    if share_deps:  # lend the venv this environment's packages through a .pth file
        import yaml

        site = (
            subprocess.run(
                [
                    str(bootstrap.venv_python()),
                    "-c",
                    "import site;print(site.getsitepackages()[0])",
                ],
                capture_output=True,
                check=True,
            )
            .stdout.decode("utf-8")
            .strip()
        )
        (Path(site) / "deps.pth").write_text(
            str(Path(yaml.__file__).resolve().parent.parent), encoding="utf-8"
        )
    return venv


def _run_without_deps(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-I", "-S", str(VISUALIZE), *args],
        capture_output=True,
        check=False,
        env=dict(os.environ),
    )


def test_cli_reruns_in_real_cache_venv():
    _make_cache_venv(share_deps=True)
    proc = _run_without_deps("--help")
    assert proc.returncode == 0, proc.stderr.decode("utf-8")
    assert "usage" in proc.stdout.decode("utf-8").lower()
    assert proc.stderr == b""


def test_cli_unusable_cache_venv_prints_message_once():
    _make_cache_venv(share_deps=False)  # a venv without the packages
    proc = _run_without_deps("--help")
    err = proc.stderr.decode("utf-8")
    assert proc.returncode == 3
    assert err.count("not ready") == 1
