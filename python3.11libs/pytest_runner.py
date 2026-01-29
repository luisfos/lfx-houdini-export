"""
Docstring for python3.11libs.pytest_runner

Note to user:
If pytest is not installed, install it via hython and pip:
Houdini -> Windows -> Shell
hython -m pip install pytest
"""

from __future__ import annotations

import os
import sys
import io
import contextlib
from pathlib import Path


def _repo_root() -> Path:
    # This file lives in <repo>/python3.11libs/
    return Path(__file__).resolve().parents[1]


def _tests_path(repo_root: Path) -> Path:
    # Tests live under <repo>/python3.11libs/tests
    return repo_root / "python3.11libs" / "tests"


def run() -> int:
    """Run pytest inside the current Houdini Python session.

    Designed to be called from a shelf tool:
        import pytest_runner
        pytest_runner.run()
    """
    import pytest

    repo_root = _repo_root()
    tests_path = _tests_path(repo_root).resolve()

    # Ensure local modules are importable when running in-process.
    for path in (repo_root, repo_root / "python3.11libs"):
        value = str(path)
        if value not in sys.path:
            sys.path.insert(0, value)

    # Clear cached modules that were imported from the tests folder,
    # so edits/new tests are picked up without restarting Houdini.
    tests_prefix = str(tests_path) + os.sep
    for name, mod in list(sys.modules.items()):
        mod_file = getattr(mod, "__file__", None)
        if mod_file and str(mod_file).startswith(tests_prefix):
            del sys.modules[name]

    # flags: https://docs.pytest.org/en/6.2.x/usage.html#modifying-python-traceback-printing
    # Keep output minimal: just the error/traceback, no captured stdout/stderr,
    # and no verbose per-test reporting.
    args = [
        str(tests_path),        
        "-v",
        "-l",                # show local variables in tracebacks        
        "--tb=short",         # concise tracebacks (avoids dumping full function source/docstrings)
        # "--show-capture=no",  # don't include captured stdout/stderr
        "--maxfail=1",        # stop after first failure
        "--disable-warnings", # less noise
    ]

    old_cwd = os.getcwd()
    buf = io.StringIO()
    try:
        os.chdir(str(repo_root))
        with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
            exit_code = int(pytest.main(args))
    finally:
        os.chdir(old_cwd)

    output = buf.getvalue()
    _show_message(
        f"pytest finished with exit code: {exit_code}",
        details=output,
        is_error=(exit_code != 0),
    )
    return exit_code


def _show_message(message: str, *, details: str = "", is_error: bool) -> None:
    """Display in Houdini UI if available; otherwise print."""
    print(message)
    print(details)
    try:
        import hou  # type: ignore

        severity = hou.severityType.Error if is_error else hou.severityType.Message
        hou.ui.displayMessage(message, details=details, severity=severity)
    except Exception:
        print(message)
        if details:
            print(details)
