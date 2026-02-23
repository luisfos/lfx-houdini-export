Use Pep8 for Python code.

Prefer small local changes over large global ones.
Avoid comments on simple code.
Avoid using Try-Except unless absolutely necessary.
Avoid Try/Except with `import hou`
Prefer asserting conditions and using type hints to catch errors at development time.
Prefer print over hou.ui.displayMessage.

## Testing

- Only run tests after large multi-file changes
- Run tests using: ./python3.11libs/lfx/pytest_runner.py
- Do NOT run `pytest` directly.