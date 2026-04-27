import os
import shutil
import tomllib
from pathlib import Path

from PySide6 import QtCore, QtGui, QtWidgets

try:
    import hou
except Exception:
    hou = None

PREFS_TOML_PATH = os.path.join(os.path.dirname(__file__), "user", "preferences_config.toml")
PRISM_CONFIG_TOML_PATH = os.path.join(os.path.dirname(__file__), "user", "exporter_prism_config.toml")
DEFAULTS_DIR = os.path.join(os.path.dirname(__file__), "defaults")
DEFAULT_PREFS_TOML_PATH = os.path.join(DEFAULTS_DIR, "preferences_config.toml")
DEFAULT_PRISM_CONFIG_TOML_PATH = os.path.join(DEFAULTS_DIR, "exporter_prism_config.toml")

PREFS_PIPELINE_GLOBAL_OPTIONS = ["From config", "Base", "Prism"]
PREFS_PIPELINE_NODE_OPTIONS = ["Base", "Prism"]


def _pipeline_to_storage(text: str | None) -> str:
    if text is None:
        return "from config"
    value = str(text).strip().lower()

    # Backwards-compatible mapping: older configs used 'hip'.
    if value in ("hip", "base"):
        return "base"
    if value in ("prism",):
        return "prism"
    if value in ("from config", "from_config", "fromconfig"):
        return "from config"
    return "from config"


def _pipeline_to_display(text: str | None) -> str:
    value = _pipeline_to_storage(text)
    if value == "base":
        return "Base"
    if value == "prism":
        return "Prism"
    return "From config"


def _expand_hou_var(expr: str) -> str:
    """Expand Houdini-style vars like "$HIP".

    Uses hou.text.expandString when available, otherwise falls back to os.environ.
    """
    if hou is not None:
        try:
            return str(hou.text.expandString(expr))
        except Exception:
            pass

    # Fallback: only handle a single token like "$HIP".
    if isinstance(expr, str) and expr.startswith("$") and len(expr) > 1:
        return os.environ.get(expr[1:], "")
    return ""


def is_scene_in_prism_project() -> bool:
    """Return True if $HIP is inside (or equal to) $PRISM_JOB.

    This is a lightweight Prism-compatibility check for UI gating.
    """
    hip = _expand_hou_var("$HIP")
    prism_job = _expand_hou_var("$PRISM_JOB") or _expand_hou_var("$PRISMJOB")

    if not hip or not prism_job:
        return False

    try:
        hip_path = Path(hip).resolve()
        prism_path = Path(prism_job).resolve()
    except Exception:
        return False

    # Windows is case-insensitive; normalize via casefold() on string forms.
    hip_str = str(hip_path).casefold()
    prism_str = str(prism_path).casefold()
    if hip_str == prism_str:
        return True
    return hip_str.startswith(prism_str.rstrip("/\\") + "\\") or hip_str.startswith(
        prism_str.rstrip("/\\") + "/"
    )


def resolve_effective_pipeline(pipeline: str | None, prism_compatible: bool) -> str:
    """Return the effective pipeline in storage form ('base'|'prism'|'from config').
    """
    if not prism_compatible:
        return "base"
    value = _pipeline_to_storage(pipeline)
    if value == "prism":
        return "prism"
    if value == "base":
        return "base"
    return "from config"


def get_effective_node_pipeline(prefs: dict, node_name_with_category: str, prism_compatible: bool) -> str:
    """Compute effective pipeline for a node.

    Rules:
    - If not prism_compatible -> 'base'
    - If global pipeline != 'from config' -> global (clamped by prism_compatible)
    - Else -> per-node pipeline (clamped by prism_compatible)
    """
    if not prism_compatible:
        return "base"

    global_choice = resolve_effective_pipeline(prefs.get("pipeline"), prism_compatible)
    if global_choice in ("base", "prism"):
        return global_choice

    nodes = prefs.get("nodes") or {}
    node_entry = nodes.get(node_name_with_category) if isinstance(nodes, dict) else None
    node_pipeline = "base"
    if isinstance(node_entry, dict) and "pipeline" in node_entry:
        node_pipeline = str(node_entry.get("pipeline"))
    return resolve_effective_pipeline(node_pipeline, prism_compatible)

# Supported types: "str", "bool", "int", "float", "enum"
PREFS_SPEC = [
    {
        "key": "base_folder",
        "label": "Base Folder",
        "type": "str",
        "default": "$HIP",
    },
    {
        "key": "auto_add_to_new_node",
        "label": "Auto add to new node",
        "type": "bool",
        "default": True,
    },
    {
        "key": "pipeline",
        "label": "Pipeline to use",
        "type": "enum",
        "options": PREFS_PIPELINE_GLOBAL_OPTIONS,
        "default": "From config",
    },
]

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


def _toml_key(key: str) -> str:
    text = "" if key is None else str(key)
    text = text.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{text}"'


def _default_node_prefs() -> dict:
    """Build default node prefs from exporter_prism_config.toml rop_settings keys."""
    if not os.path.exists(PRISM_CONFIG_TOML_PATH):
        os.makedirs(os.path.dirname(PRISM_CONFIG_TOML_PATH), exist_ok=True)
        shutil.copyfile(DEFAULT_PRISM_CONFIG_TOML_PATH, PRISM_CONFIG_TOML_PATH)

    try:
        with open(PRISM_CONFIG_TOML_PATH, "rb") as f:
            data = tomllib.load(f)
    except Exception:
        return {}

    rop_settings = data.get("rop_settings") or {}
    node_names = [k for k in rop_settings.keys() if isinstance(k, str) and "/" in k]

    nodes: dict[str, dict] = {}
    for node_name in sorted(set(node_names)):
        nodes[node_name] = {"enabled": True, "pipeline": "base"}
    return nodes


def _toml_dumps(prefs_dict: dict) -> str:
    lines: list[str] = []

    # top-level simple keys
    for key in sorted(prefs_dict.keys()):
        if key == "nodes":
            continue
        if key == "pipeline":
            lines.append(f"{key} = {_toml_value(_pipeline_to_storage(prefs_dict[key]))}")
        else:
            lines.append(f"{key} = {_toml_value(prefs_dict[key])}")

    nodes = prefs_dict.get("nodes") or {}
    if isinstance(nodes, dict) and nodes:
        for node_name in sorted(nodes.keys()):
            node_entry = nodes.get(node_name) or {}
            enabled = bool(node_entry.get("enabled", False))
            pipeline = _pipeline_to_storage(node_entry.get("pipeline", "base"))
            lines.append("")
            lines.append(f"[nodes.{_toml_key(node_name)}]")
            lines.append(f"enabled = {_toml_value(enabled)}")
            lines.append(f"pipeline = {_toml_value(pipeline)}")

    return "\n".join(lines) + ("\n" if lines else "")


def _load_prefs():
    defaults = dict(DEFAULT_PREFS)
    defaults["nodes"] = _default_node_prefs()

    if not os.path.exists(PREFS_TOML_PATH):
        os.makedirs(os.path.dirname(PREFS_TOML_PATH), exist_ok=True)
        shutil.copyfile(DEFAULT_PREFS_TOML_PATH, PREFS_TOML_PATH)

    with open(PREFS_TOML_PATH, "rb") as f:
        data = tomllib.load(f)

    prefs = dict(DEFAULT_PREFS)
    for spec in PREFS_SPEC:
        key = spec["key"]
        if key in data:
            prefs[key] = data[key]

    if "pipeline" in prefs:
        prefs["pipeline"] = _pipeline_to_storage(prefs.get("pipeline"))

    # nodes: merge defaults with saved values
    nodes = _default_node_prefs()
    saved_nodes = data.get("nodes") if isinstance(data, dict) else None
    if isinstance(saved_nodes, dict):
        for node_name, node_entry in saved_nodes.items():
            if not isinstance(node_name, str) or not isinstance(node_entry, dict):
                continue
            nodes.setdefault(node_name, {"enabled": True, "pipeline": "base"})
            if "enabled" in node_entry:
                nodes[node_name]["enabled"] = bool(node_entry["enabled"])
            if "pipeline" in node_entry:
                nodes[node_name]["pipeline"] = _pipeline_to_storage(node_entry["pipeline"])

    prefs["nodes"] = nodes
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
        self.setMinimumSize(720, 560)

        self.widgets_by_key = {}
        self.node_table = None
        self.config_box = None
        self.config_box_content = None
        self.lbl_prism_warning = None
        self.lbl_dirty = None
        self.prism_compatible = True
        self._loading = False
        self._baseline_prefs = None

        layout = QtWidgets.QVBoxLayout(self)

        def _make_widget(spec: dict):
            field_type = spec.get("type", "str")
            if field_type == "bool":
                return QtWidgets.QCheckBox(), field_type
            if field_type == "int":
                w = QtWidgets.QSpinBox()
                w.setRange(spec.get("min", -2147483648), spec.get("max", 2147483647))
                return w, field_type
            if field_type == "float":
                w = QtWidgets.QDoubleSpinBox()
                w.setRange(spec.get("min", -1e12), spec.get("max", 1e12))
                w.setDecimals(spec.get("decimals", 3))
                return w, field_type
            if field_type == "enum":
                w = QtWidgets.QComboBox()
                options = spec.get("options") or []
                w.addItems([str(o) for o in options])
                # Don't let combo boxes stretch across the whole dialog.
                w.setSizeAdjustPolicy(QtWidgets.QComboBox.SizeAdjustPolicy.AdjustToContents)
                w.setSizePolicy(
                    QtWidgets.QSizePolicy.Policy.Fixed, QtWidgets.QSizePolicy.Policy.Fixed
                )
                w.setMaximumWidth(220)
                return w, field_type
            return QtWidgets.QLineEdit(), field_type

        form = QtWidgets.QFormLayout()
        layout.addLayout(form)

        for spec in PREFS_SPEC:
            key = spec["key"]
            label = spec.get("label", key)
            widget, field_type = _make_widget(spec)
            self.widgets_by_key[key] = (widget, field_type)
            form.addRow(label, widget)

        # Widget tooltips
        auto_add_widget = self.widgets_by_key.get("auto_add_to_new_node", (None, None))[0]
        if isinstance(auto_add_widget, QtWidgets.QCheckBox):
            auto_add_widget.setToolTip(
                "Automatically add Pipe/Prism helper parameters to newly created nodes."
            )

        pipeline_widget = self.widgets_by_key.get("pipeline", (None, None))[0]
        if isinstance(pipeline_widget, QtWidgets.QComboBox):
            pipeline_widget.setToolTip(
                "Controls how pipeline behaviour is selected.\n"
                "- From config: use per-node settings in the table below\n"
                "- Base / Prism: force that pipeline for all nodes"
            )

        base_folder_widget = self.widgets_by_key.get("base_folder", (None, None))[0]
        if isinstance(base_folder_widget, QtWidgets.QLineEdit):
            base_folder_widget.setToolTip(
                "Base folder used by the Base pipeline.\n"
                "You can use Houdini variables like $HIP."
            )

        # Prism compatibility warning (hidden by default)
        warn = QtWidgets.QLabel("Scene is not inside the Prism project")
        warn.setWordWrap(True)
        warn.setStyleSheet("color: rgb(220, 160, 0);")
        warn.setVisible(False)
        form.addRow("", warn)
        self.lbl_prism_warning = warn

        # Spacer between top prefs and config table
        layout.addSpacing(12)

        # Config table
        nodes_box = QtWidgets.QGroupBox("Config")
        nodes_layout = QtWidgets.QVBoxLayout(nodes_box)
        content = QtWidgets.QWidget()
        content_layout = QtWidgets.QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        nodes_layout.addWidget(content)
        layout.addWidget(nodes_box)

        self.config_box = nodes_box
        self.config_box_content = content

        table = QtWidgets.QTableWidget()
        table.setColumnCount(3)

        # Column headers + tooltips
        h0 = QtWidgets.QTableWidgetItem("Enable")
        h0.setToolTip(
            "Enable/disable auto-add for this node type when Pipeline is 'From config'."
        )
        table.setHorizontalHeaderItem(0, h0)

        h1 = QtWidgets.QTableWidgetItem("Node Type")
        h1.setToolTip("Houdini node type (type().nameWithCategory()).")
        table.setHorizontalHeaderItem(1, h1)

        h2 = QtWidgets.QTableWidgetItem("Pipeline")
        h2.setToolTip(
            "Pipeline to use for this node type when global Pipeline is 'From config'.\n"
            "If global Pipeline is set to Base/Prism, this column is locked."
        )
        table.setHorizontalHeaderItem(2, h2)

        table.horizontalHeader().setStretchLastSection(True)
        table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        # Houdini/Qt themes can make alternate rows unreadable (e.g. bright white on dark UI).
        table.setAlternatingRowColors(False)
        content_layout.addWidget(table)
        self.node_table = table

        buttons = QtWidgets.QHBoxLayout()
        layout.addLayout(buttons)

        self.btn_reset = QtWidgets.QPushButton("Reset to defaults")
        self.btn_save = QtWidgets.QPushButton("Save")
        self.btn_close = QtWidgets.QPushButton("Cancel")

        self.lbl_dirty = QtWidgets.QLabel("Unsaved changes")
        self.lbl_dirty.setVisible(False)
        self.lbl_dirty.setStyleSheet("color: rgb(220, 160, 0);")

        buttons.addWidget(self.btn_reset)
        buttons.addStretch(1)
        buttons.addWidget(self.lbl_dirty)
        buttons.addWidget(self.btn_save)
        buttons.addWidget(self.btn_close)

        self.btn_reset.clicked.connect(self.reset_to_defaults)
        self.btn_save.clicked.connect(self.save)
        self.btn_close.clicked.connect(self.close)

        # Auto add controls table visibility
        if isinstance(auto_add_widget, QtWidgets.QCheckBox):
            auto_add_widget.stateChanged.connect(self._on_any_changed)
            auto_add_widget.stateChanged.connect(self._update_table_visibility)

        if isinstance(pipeline_widget, QtWidgets.QComboBox):
            pipeline_widget.currentTextChanged.connect(lambda _text: self._on_any_changed())
            pipeline_widget.currentTextChanged.connect(lambda _text: self._update_table_visibility())

        self.prism_compatible = is_scene_in_prism_project()
        self.set_prefs(_load_prefs())
        self._apply_prism_compatibility_rules()
        self._set_baseline_from_current()

    def get_prefs(self):
        prefs = {}
        for key, (widget, field_type) in self.widgets_by_key.items():
            if field_type == "bool":
                prefs[key] = bool(widget.isChecked())
            elif field_type == "int":
                prefs[key] = int(widget.value())
            elif field_type == "float":
                prefs[key] = float(widget.value())
            elif field_type == "enum":
                prefs[key] = str(widget.currentText())
            else:
                prefs[key] = widget.text()

        prefs["nodes"] = self._get_nodes_from_table()
        return prefs

    def set_prefs(self, prefs):
        self._loading = True
        for key, (widget, field_type) in self.widgets_by_key.items():
            value = prefs.get(key, DEFAULT_PREFS.get(key))
            if field_type == "bool":
                widget.setChecked(bool(value))
            elif field_type == "int":
                widget.setValue(int(value or 0))
            elif field_type == "float":
                widget.setValue(float(value or 0.0))
            elif field_type == "enum":
                # If the stored value isn't a valid option, keep current (index 0).
                if value is None:
                    continue
                # Match case-insensitively, and normalize pipeline labels.
                display_val = (
                    _pipeline_to_display(value) if key == "pipeline" else str(value)
                )
                index = widget.findText(display_val)
                if index >= 0:
                    widget.setCurrentIndex(index)
            else:
                widget.setText("" if value is None else str(value))

        self._set_nodes_in_table(prefs.get("nodes") or {})
        self._apply_prism_compatibility_rules()
        self._update_table_visibility()

        self._loading = False
        self._refresh_dirty_state()

    def reset_to_defaults(self):
        # Requirement: overwrite the prefs TOML on disk with the defaults file.
        if os.path.exists(DEFAULT_PREFS_TOML_PATH):
            try:
                os.makedirs(os.path.dirname(PREFS_TOML_PATH), exist_ok=True)
                shutil.copyfile(DEFAULT_PREFS_TOML_PATH, PREFS_TOML_PATH)
            except Exception:
                # Fall back to in-memory defaults if copy fails.
                defaults = dict(DEFAULT_PREFS)
                defaults["nodes"] = _default_node_prefs()
                self.set_prefs(defaults)
                self._set_baseline_from_current()
                return

            # Reload from disk (still merges in any new node types from exporter_prism_config.toml)
            self.set_prefs(_load_prefs())
            self._set_baseline_from_current()
            return

        # Fall back to previous behavior if defaults file is missing.
        defaults = dict(DEFAULT_PREFS)
        defaults["nodes"] = _default_node_prefs()
        self.set_prefs(defaults)
        self._set_baseline_from_current()

    def save(self):
        _save_prefs(self.get_prefs())
        self._set_baseline_from_current()

    def _update_table_visibility(self) -> None:
        """Apply UI state rules for Auto add / Pipeline / Config table."""
        if self.config_box is None:
            return
        auto_add_widget = self.widgets_by_key.get("auto_add_to_new_node", (None, None))[0]
        auto_add_enabled = True
        if isinstance(auto_add_widget, QtWidgets.QCheckBox):
            auto_add_enabled = bool(auto_add_widget.isChecked())

        pipeline_widget = self.widgets_by_key.get("pipeline", (None, None))[0]
        if isinstance(pipeline_widget, QtWidgets.QComboBox):
            # 2) If auto-add disabled, disable pipeline menu.
            pipeline_widget.setEnabled(auto_add_enabled and self.prism_compatible)

        # Requirement: hide config table when Auto add is disabled.
        self.config_box.setVisible(auto_add_enabled)

        # Lock/unlock the pipeline column depending on global selection.
        self._apply_global_pipeline_lock()

    def _apply_prism_compatibility_rules(self) -> None:
        """If scene isn't in a Prism project, force Base pipeline and hide Prism option."""
        pipeline_widget = self.widgets_by_key.get("pipeline", (None, None))[0]
        if not isinstance(pipeline_widget, QtWidgets.QComboBox):
            return

        if self.prism_compatible:
            if self.lbl_prism_warning is not None:
                self.lbl_prism_warning.setVisible(False)
            # Ensure Prism option exists
            if pipeline_widget.findText("Prism") < 0:
                pipeline_widget.addItem("Prism")
            return

        # Not Prism compatible: force Base, remove Prism option, show warning.
        if self.lbl_prism_warning is not None:
            self.lbl_prism_warning.setVisible(True)

        # Remove Prism option if present.
        idx = pipeline_widget.findText("Prism")
        if idx >= 0:
            pipeline_widget.removeItem(idx)

        # Force selection to Base.
        base_idx = pipeline_widget.findText("Base")
        if base_idx >= 0:
            pipeline_widget.setCurrentIndex(base_idx)

        # Lock pipeline selector to Base (forced).
        pipeline_widget.setEnabled(False)
        self._update_table_visibility()

    def _apply_global_pipeline_lock(self) -> None:
        """Lock per-row pipeline comboboxes when global pipeline != 'from config'.

        When locked, the UI shows the forced value but we preserve each row's
        stored pipeline in the Node Type item UserRole so toggling back to
        'From config' restores the user's per-node choices.
        """
        if self.node_table is None:
            return

        pipeline_widget = self.widgets_by_key.get("pipeline", (None, None))[0]
        global_choice = "from config"
        if isinstance(pipeline_widget, QtWidgets.QComboBox):
            global_choice = _pipeline_to_storage(pipeline_widget.currentText())

        locked = global_choice != "from config"
        locked_display = _pipeline_to_display(global_choice)

        table = self.node_table
        for row in range(table.rowCount()):
            name_item = table.item(row, 1)
            combo = table.cellWidget(row, 2)
            if name_item is None or not isinstance(combo, QtWidgets.QComboBox):
                continue

            # Row-enabled state still disables the combo.
            row_enabled = True
            enabled_widget = table.cellWidget(row, 0)
            if enabled_widget is not None:
                chk = enabled_widget.findChild(QtWidgets.QCheckBox)
                if chk is not None:
                    row_enabled = bool(chk.isChecked())

            if locked:
                # Show forced value, but don't overwrite stored per-node pipeline.
                idx = combo.findText(locked_display)
                if idx >= 0:
                    with QtCore.QSignalBlocker(combo):
                        combo.setCurrentIndex(idx)
                combo.setEnabled(False)
            else:
                # Restore from stored value.
                stored = name_item.data(QtCore.Qt.ItemDataRole.UserRole)
                display = _pipeline_to_display(stored)
                idx = combo.findText(display)
                if idx >= 0:
                    with QtCore.QSignalBlocker(combo):
                        combo.setCurrentIndex(idx)
                combo.setEnabled(row_enabled)

    def _set_nodes_in_table(self, nodes: dict):
        if self.node_table is None:
            return
        if not isinstance(nodes, dict):
            nodes = {}

        table = self.node_table
        row_keys = sorted(nodes.keys())
        table.setRowCount(len(row_keys))

        for row, node_name in enumerate(row_keys):
            node_entry = nodes.get(node_name) or {}
            enabled = bool(node_entry.get("enabled", False))
            stored_pipeline = _pipeline_to_storage(node_entry.get("pipeline", "base"))
            pipeline = _pipeline_to_display(stored_pipeline)

            # Centered checkbox widget
            chk = QtWidgets.QCheckBox()
            chk.setChecked(enabled)
            chk.setFocusPolicy(QtCore.Qt.FocusPolicy.NoFocus)
            chk.stateChanged.connect(lambda _state, r=row: self._update_config_row_enabled(r))
            chk_container = QtWidgets.QWidget()
            chk_layout = QtWidgets.QHBoxLayout(chk_container)
            chk_layout.setContentsMargins(0, 0, 0, 0)
            chk_layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
            chk_layout.addWidget(chk)
            table.setCellWidget(row, 0, chk_container)

            name_item = QtWidgets.QTableWidgetItem(str(node_name))
            name_item.setFlags(QtCore.Qt.ItemFlag.ItemIsEnabled | QtCore.Qt.ItemFlag.ItemIsSelectable)
            name_item.setData(QtCore.Qt.ItemDataRole.UserRole, stored_pipeline)
            table.setItem(row, 1, name_item)

            combo = QtWidgets.QComboBox()
            combo.addItems(PREFS_PIPELINE_NODE_OPTIONS)
            idx = combo.findText(pipeline)
            if idx >= 0:
                combo.setCurrentIndex(idx)
            combo.currentTextChanged.connect(
                lambda text, r=row: self._on_row_pipeline_changed(r, text)
            )
            table.setCellWidget(row, 2, combo)

            self._update_config_row_enabled(row)

        table.resizeColumnsToContents()
        table.setColumnWidth(0, max(table.columnWidth(0), 60))

    def _update_config_row_enabled(self, row: int) -> None:
        if self.node_table is None:
            return

        table = self.node_table

        enabled = True
        enabled_widget = table.cellWidget(row, 0)
        if enabled_widget is not None:
            chk = enabled_widget.findChild(QtWidgets.QCheckBox)
            if chk is not None:
                enabled = bool(chk.isChecked())

        palette = table.palette()
        if enabled:
            brush = QtGui.QBrush(palette.color(QtGui.QPalette.ColorRole.Text))
        else:
            brush = QtGui.QBrush(
                palette.color(QtGui.QPalette.ColorGroup.Disabled, QtGui.QPalette.ColorRole.Text)
            )

        name_item = table.item(row, 1)
        if name_item is not None:
            name_item.setForeground(brush)

        combo = table.cellWidget(row, 2)
        if isinstance(combo, QtWidgets.QComboBox):
            # Global pipeline locking may override enabled state.
            combo.setEnabled(enabled)

        # Re-apply global lock after row state change.
        self._apply_global_pipeline_lock()

        self._on_any_changed()

    def _on_row_pipeline_changed(self, row: int, text: str) -> None:
        if self._loading or self.node_table is None:
            return

        # Persist per-node pipeline selection even if UI gets locked later.
        name_item = self.node_table.item(row, 1)
        if name_item is not None:
            name_item.setData(QtCore.Qt.ItemDataRole.UserRole, _pipeline_to_storage(text))
        self._on_any_changed()

    def _normalized_prefs(self, prefs: dict) -> dict:
        """Return prefs in a stable, comparable form."""
        out = dict(prefs)
        out["pipeline"] = _pipeline_to_storage(out.get("pipeline"))
        nodes = out.get("nodes")
        if isinstance(nodes, dict):
            out_nodes = {}
            for node_name, node_entry in nodes.items():
                if not isinstance(node_entry, dict):
                    continue
                out_nodes[str(node_name)] = {
                    "enabled": bool(node_entry.get("enabled", False)),
                    "pipeline": _pipeline_to_storage(node_entry.get("pipeline")),
                }
            out["nodes"] = out_nodes
        return out

    def _set_baseline_from_current(self) -> None:
        self._baseline_prefs = self._normalized_prefs(self.get_prefs())
        if self.lbl_dirty is not None:
            self.lbl_dirty.setVisible(False)

    def _refresh_dirty_state(self) -> None:
        if self._baseline_prefs is None:
            return
        current = self._normalized_prefs(self.get_prefs())
        dirty = current != self._baseline_prefs
        if self.lbl_dirty is not None:
            self.lbl_dirty.setVisible(dirty)

    def _on_any_changed(self) -> None:
        if self._loading:
            return
        self._refresh_dirty_state()

    def _get_nodes_from_table(self) -> dict:
        if self.node_table is None:
            return {}

        table = self.node_table
        nodes: dict[str, dict] = {}

        for row in range(table.rowCount()):
            name_item = table.item(row, 1)
            if name_item is None:
                continue
            node_name = name_item.text().strip()
            if not node_name:
                continue

            enabled = False
            enabled_widget = table.cellWidget(row, 0)
            if enabled_widget is not None:
                chk = enabled_widget.findChild(QtWidgets.QCheckBox)
                if chk is not None:
                    enabled = bool(chk.isChecked())

            # Preserve per-node pipeline even when the UI is locked to a global choice.
            pipeline = "base"
            stored = name_item.data(QtCore.Qt.ItemDataRole.UserRole)
            if stored is not None:
                pipeline = _pipeline_to_storage(stored)
            else:
                combo = table.cellWidget(row, 2)
                if isinstance(combo, QtWidgets.QComboBox):
                    pipeline = _pipeline_to_storage(combo.currentText())

            nodes[node_name] = {"enabled": enabled, "pipeline": pipeline}

        return nodes


def show():
    global _DIALOG
    _DIALOG = PipeParmPrefsDialog()
    _DIALOG.show()
    _DIALOG.raise_()
    _DIALOG.activateWindow()
