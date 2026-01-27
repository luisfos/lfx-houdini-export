import os
import tomllib

from PySide6 import QtCore, QtWidgets

PREFS_TOML_PATH = os.path.join(os.path.dirname(__file__), "pipe_parm_prefs.toml")

# Fill this after you tell me which prefs you want.
# Supported types: "str", "bool", "int", "float"
PREFS_SPEC = []

DEFAULT_PREFS = {spec["key"]: spec.get("default") for spec in PREFS_SPEC}

_DIALOG = None


def _toml_value(value):
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    text = "" if value is None else str(value)
    text = text.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{text}"'


def _toml_dumps(flat_dict):
    lines = []
    for key in sorted(flat_dict.keys()):
        lines.append(f"{key} = {_toml_value(flat_dict[key])}")
    return "\n".join(lines) + ("\n" if lines else "")


def _load_prefs():
    if not os.path.exists(PREFS_TOML_PATH):
        return dict(DEFAULT_PREFS)

    with open(PREFS_TOML_PATH, "rb") as f:
        data = tomllib.load(f)

    prefs = dict(DEFAULT_PREFS)
    for spec in PREFS_SPEC:
        key = spec["key"]
        if key in data:
            prefs[key] = data[key]
    return prefs


def _save_prefs(prefs):
    text = _toml_dumps(prefs)
    with open(PREFS_TOML_PATH, "w", encoding="utf-8") as f:
        f.write(text)


class PipeParmPrefsDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Pipe Parm Prefs")
        self.setWindowFlags(self.windowFlags() | QtCore.Qt.WindowType.Window)

        self.widgets_by_key = {}

        layout = QtWidgets.QVBoxLayout(self)

        form = QtWidgets.QFormLayout()
        layout.addLayout(form)

        if not PREFS_SPEC:
            form.addRow(QtWidgets.QLabel("No preferences defined yet."))
        else:
            for spec in PREFS_SPEC:
                key = spec["key"]
                label = spec.get("label", key)
                field_type = spec.get("type", "str")

                if field_type == "bool":
                    widget = QtWidgets.QCheckBox()
                elif field_type == "int":
                    widget = QtWidgets.QSpinBox()
                    widget.setRange(spec.get("min", -2147483648), spec.get("max", 2147483647))
                elif field_type == "float":
                    widget = QtWidgets.QDoubleSpinBox()
                    widget.setRange(spec.get("min", -1e12), spec.get("max", 1e12))
                    widget.setDecimals(spec.get("decimals", 3))
                else:
                    widget = QtWidgets.QLineEdit()

                self.widgets_by_key[key] = (widget, field_type)
                form.addRow(label, widget)

        buttons = QtWidgets.QHBoxLayout()
        layout.addLayout(buttons)

        self.btn_reset = QtWidgets.QPushButton("Reset to defaults")
        self.btn_save = QtWidgets.QPushButton("Save")
        self.btn_close = QtWidgets.QPushButton("Close")

        buttons.addWidget(self.btn_reset)
        buttons.addStretch(1)
        buttons.addWidget(self.btn_save)
        buttons.addWidget(self.btn_close)

        self.btn_reset.clicked.connect(self.reset_to_defaults)
        self.btn_save.clicked.connect(self.save)
        self.btn_close.clicked.connect(self.close)

        self.set_prefs(_load_prefs())

    def get_prefs(self):
        prefs = {}
        for key, (widget, field_type) in self.widgets_by_key.items():
            if field_type == "bool":
                prefs[key] = bool(widget.isChecked())
            elif field_type == "int":
                prefs[key] = int(widget.value())
            elif field_type == "float":
                prefs[key] = float(widget.value())
            else:
                prefs[key] = widget.text()
        return prefs

    def set_prefs(self, prefs):
        for key, (widget, field_type) in self.widgets_by_key.items():
            value = prefs.get(key, DEFAULT_PREFS.get(key))
            if field_type == "bool":
                widget.setChecked(bool(value))
            elif field_type == "int":
                widget.setValue(int(value or 0))
            elif field_type == "float":
                widget.setValue(float(value or 0.0))
            else:
                widget.setText("" if value is None else str(value))

    def reset_to_defaults(self):
        self.set_prefs(dict(DEFAULT_PREFS))

    def save(self):
        _save_prefs(self.get_prefs())


def show():
    global _DIALOG
    _DIALOG = PipeParmPrefsDialog()
    _DIALOG.show()
    _DIALOG.raise_()
    _DIALOG.activateWindow()
