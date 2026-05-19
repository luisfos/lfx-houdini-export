"""Run pytest inside Houdini.

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
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
TESTS_PATH = (REPO_ROOT / "python3.11libs" / "lfx" / "tests").resolve()


def _pytest_args(tests_path: Path) -> list[str]:
    return [
        str(tests_path),
        "-v",
        "-l",
        "--tb=short",
        "--maxfail=1",
        "--disable-warnings",
        "--capture=no",
        "-p",
        "no:faulthandler",
    ]


def _find_hython() -> str:
    """Best-effort path to hython executable."""
    try:
        import hou  # type: ignore

        hfs = hou.getenv("HFS")
        if hfs:
            suffix = "hython.exe" if os.name == "nt" else "hython"
            candidate = Path(hfs) / "bin" / suffix
            if candidate.exists():
                return str(candidate)
    except Exception:
        pass

    if os.name == "nt":
        sidefx_root = Path(r"C:\Program Files\Side Effects Software")
        if sidefx_root.exists():
            houdini_dirs: list[tuple[tuple[int, int, int], Path]] = []
            for item in sidefx_root.iterdir():
                if not item.is_dir():
                    continue
                name = item.name
                if not name.startswith("Houdini "):
                    continue
                version_text = name.removeprefix("Houdini ").strip()
                parts = version_text.split(".")
                if len(parts) != 3 or not all(part.isdigit() for part in parts):
                    continue
                version = (int(parts[0]), int(parts[1]), int(parts[2]))
                houdini_dirs.append((version, item))

            for _, houdini_dir in sorted(houdini_dirs, key=lambda pair: pair[0], reverse=True):
                candidate = houdini_dir / "bin" / "hython.exe"
                if candidate.exists():
                    return str(candidate)

    suffix = "hython.exe" if os.name == "nt" else "hython"
    candidate = Path(sys.executable).with_name(suffix)
    if candidate.exists():
        return str(candidate)
    return sys.executable


def run() -> int:
    """Run pytest inside the current Houdini Python session.

    Designed to be called from a shelf tool:
        from lfx import pytest_runner
        pytest_runner.run()
    """
    repo_root = REPO_ROOT
    tests_path = TESTS_PATH

    import pytest

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

    test_files = sorted(tests_path.glob("test_*.py"))

    import hou
    if hou.isUIAvailable() and test_files:
        choices = [f.name for f in test_files]
        selected = hou.ui.selectFromList(
            choices,
            default_choices=tuple(range(len(choices))),
            message="Select tests to run:",
            title="Run Pytest",
            column_header="Test File",
            clear_on_cancel=True,
        )
        if not selected:
            return 0
        args = [str(test_files[i]) for i in selected] + _pytest_args(tests_path)[1:]
    else:
        args = _pytest_args(tests_path)

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
    import hou  
    hou.ui.displayMessage("Pytest finished, check the console for results.")    
    return exit_code


def run_hython() -> int:
    """Run pytest in a separate hython subprocess.

    Designed to be called from a shelf tool:
        from lfx import pytest_runner
        pytest_runner.run_hython()
    """
    repo_root = REPO_ROOT
    tests_path = TESTS_PATH

    command = [_find_hython(), "-m", "pytest", *_pytest_args(tests_path)]
    proc = subprocess.run(
        command,
        cwd=str(repo_root),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        shell=False,
    )

    output = (proc.stdout or "") + (("\n" + proc.stderr) if proc.stderr else "")
    exit_code = int(proc.returncode)

    _show_message(
        f"pytest (hython subprocess) finished with exit code: {exit_code}",
        details=output,
        is_error=(exit_code != 0),
    )
    try:
        import hou  # type: ignore

        hou.ui.displayMessage("Pytest finished, check the console for results.")
    except Exception:
        pass
    return exit_code


def _show_message(message: str, *, details: str = "", is_error: bool) -> None:
    print(message)
    if details:
        print(details)


if __name__ == "__main__":
    raise SystemExit(run_hython())
    