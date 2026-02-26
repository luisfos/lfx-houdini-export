# Contributing

## Local Python environment

This project uses a repo-local virtual environment at `.venv` and pins VS Code to it via workspace settings.

### Why we use `uv`

- Fast environment creation and package installs.
- Minimal project trace for local-only dependencies (no global installs required).
- Easy cleanup: remove `.venv`.
- Works well for quick UI iteration (for example, testing `PySide6` without full Houdini startup).

## First-time setup (Windows)

From the repository root:

```powershell
uv venv --python 3.11 .venv
uv pip install --python .\.venv\Scripts\python.exe PySide6
```

Optional quick check:

```powershell
.\.venv\Scripts\python.exe -c "from PySide6 import QtWidgets; print(QtWidgets.__name__)"
```

## VS Code interpreter

This repo is configured to use:

- `${workspaceFolder}\\.venv\\Scripts\\python.exe`

If VS Code doesn’t pick it automatically, run **Python: Select Interpreter** and choose `.venv\Scripts\python.exe`.

## Notes

- Do not install `PySide6` globally for this project.
- On a new machine, rerun the setup commands above after cloning.
- To clean up local env artifacts, delete `.venv`.
