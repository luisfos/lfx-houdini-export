import sys
import logging
import logging.handlers
from PySide6 import QtWidgets, QtCore, QtGui
import os
import json
from pprint import pprint
try:
    from shiboken6 import isValid as _qt_is_valid
except Exception:
    def _qt_is_valid(obj):
        try:
            return obj is not None
        except Exception:
            return False

# --- Logging Setup ---
def setup_logger():
    logger = logging.getLogger(__name__)
    if not logger.handlers:
        logger.setLevel(logging.DEBUG)
        # Primary stream handler
        handler = logging.StreamHandler(sys.stdout)
        # Remove timestamp from log output in console
        formatter = logging.Formatter('%(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        # Add a temporary buffer handler to capture early logs before UI exists
        buffer_handler = logging.handlers.BufferingHandler(capacity=1000)
        buffer_handler.setLevel(logging.DEBUG)
        buffer_handler.setFormatter(formatter)
        logger.addHandler(buffer_handler)
        # Store buffer handler on the logger for later flush
        logger._buffer_handler = buffer_handler
        # Allow propagation control later
        logger.propagate = True
    return logger

logger = setup_logger()

# --- Identifier discovery (copied/adapted from exporter_prism_callbacks) ---
def get_existing_identifiers_for_mplay() -> list[str]:
    """
    Finds existing identifiers in the output directory to populate the identifier dropdown.

    Mirrors the logic of exporter_prism_callbacks.get_existing_identifiers but derives paths
    from Prism environment variables for MPlay (Playblasts context).
    Returns a simple list of identifier names.
    """
    import os
    
    # Base path
    base_path = os.path.join(hou.getenv('PRISM_JOB') or '', '03_Production')
    prism_shot = hou.getenv('PRISM_SHOT') or ''
    prism_seq = hou.getenv('PRISM_SEQUENCE') or ''
    prism_assetpath = hou.getenv('PRISM_ASSETPATH') or ''

    if prism_shot:
        shasset_path = os.path.join('Shots', prism_seq, prism_shot)
    else:
        shasset_path = os.path.join('Assets', prism_assetpath)

    # MPlay deals with playblasts
    etype_path = 'Playblasts'

    lookup_dir = os.path.join(base_path, shasset_path, etype_path)
    if not os.path.isdir(lookup_dir):
        return []

    try:
        subfolders = [d for d in os.listdir(lookup_dir) if os.path.isdir(os.path.join(lookup_dir, d))]
        return sorted(subfolders)
    except OSError:
        return []


# --- Version Info Writer ---
def write_version_info(filepath: str, comment: str):
    """
    Write a `versioninfo.json` next to the given file path.

    Args:
        filepath: The output file path (image/movie) produced by imgsave.
        comment: User-entered comment to store in the JSON.
    """
    dest_folder = os.path.dirname(filepath)

    
    prism_user = hou.getenv("PRISM_USER")
    source_scene = hou.getenv("HIPFILE")
    source_scene = source_scene.replace(hou.getenv("PRISM_JOB"), "$PRISM_JOB")

    data = {
        "comment": comment or "",
        "user": prism_user,
        "sourceScene": source_scene,
    }

    # os.makedirs(dest_folder, exist_ok=True)
    out_path = os.path.join(dest_folder, "versioninfo.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

# --- Global variable to hold dialog reference ---
dialog_instance = None
USE_CUSTOM_STYLESHEET = False

# --- Stylesheet ---
STYLESHEET = """
/* General Window Style */
#MainContainer {
    background-color: #2a2d30;
    border: 2px solid #1a1c1e;
    border-radius: 8px; /* Rounded corners for the main window */
    font-family: 'Orbitron', sans-serif; /* A good sci-fi/tech font */
}

/* Custom Title Bar */
#TitleBar {
    background-color: #1a1c1e;
    border-bottom: 2px solid #4a4d50;
}

#TitleLabel {
    color: #FE9532;
    font-size: 14pt;
    font-weight: bold;
    padding: 5px;
}

#CloseButton {
    background-color: transparent;
    color: #FE9532;
    border: none;
    font-size: 15pt;
    font-weight: bold;
    padding: 0px 10px;
}
#CloseButton:hover {
    background-color: #c13d3d;
    color: #ffffff;
}

/* Labels */
QLabel {
    color: #FE9532;
    font-size: 10pt;
    font-weight: bold;
}

/* Inputs */
QLineEdit, QTextEdit, QSpinBox, QComboBox {
    background-color: #1a1c1e;
    color: #e0e0e0;
    border: 1px solid #4a4d50;
    border-radius: 4px;
    padding: 5px;
    font-size: 10pt;
}

QLineEdit:focus, QTextEdit:focus, QSpinBox:focus, QComboBox:focus {
    border: 1px solid #FE9532;
}

/* Checkboxes */
QCheckBox {
    color: #c0c0c0;
    font-size: 10pt;
}

QCheckBox::indicator {
    width: 16px;
    height: 16px;
    background-color: #1a1c1e;
    border: 1px solid #4a4d50;
}

QCheckBox::indicator:checked {
    background-color: #FE9532;
    image: url(none);
}

/* ComboBox */
QComboBox:hover {
    border: 1px solid #FE9532;
}

QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 25px;
    border-left-width: 1px;
    border-left-color: #4a4d50;
    border-left-style: solid;
    border-top-right-radius: 3px;
    border-bottom-right-radius: 3px;
}

QComboBox::down-arrow {
    image: url(v_arrow.png);
    width: 12px;
    height: 12px;
}

/* Menus and ToolButtons */
QToolButton {
    background-color: #4a4d50;
    color: #e0e0e0;
    border: 1px solid #5a5d60;
    border-radius: 4px;
    padding: 6px 10px;
    font-weight: bold;
}
QToolButton:hover {
    background-color: #5a5d60;
    border-color: #FE9532;
}
QToolButton::menu-indicator {
    image: none;
}
QMenu {
    background-color: #1a1c1e;
    border: 1px solid #4a4d50;
}
QMenu::item {
    padding: 6px 12px;
    color: #e0e0e0;
}
QMenu::item:selected {
    background-color: #5a5d60;
}

/* Buttons */
QPushButton {
    background-color: #4a4d50;
    color: #e0e0e0;
    border: 1px solid #5a5d60;
    border-radius: 4px;
    padding: 8px 12px;
    font-weight: bold;
}

QPushButton:hover {
    background-color: #5a5d60;
    border-color: #FE9532;
}

#ExportButton {
    background-color: #1a1c1e;
    color: #FE9532;
    border: 2px solid #FE9532;
    font-size: 14pt;
    padding: 10px;
}
/* Hover effect specifically for Export button */
#ExportButton:hover {
    background-color: #26282a;
    border-color: #ffa65a;
    color: #ffa65a;
}

/* Disabled State Styles */
QLineEdit:disabled, QTextEdit:disabled, QSpinBox:disabled, QComboBox:disabled {
    background-color: #2a2d30;
    color: #7f7f7f;
    border: 1px solid #4a4d50;
}

QPushButton:disabled {
    background-color: #4a4d50;
    color: #a0a0a0;
    border: 1px solid #5a5d60;
}
"""

# --- Custom Arrow Image for ComboBox ---
def create_arrow_pixmap():
    pixmap = QtGui.QPixmap(16, 16)
    pixmap.fill(QtCore.Qt.transparent)
    painter = QtGui.QPainter(pixmap)
    pen = QtGui.QPen(QtGui.QColor("#FE9532"), 2)
    painter.setPen(pen)
    painter.drawLine(3, 6, 8, 11)
    painter.drawLine(13, 6, 8, 11)
    painter.end()
    return pixmap

# To parent to Houdini's main window
try:
    import hou
    def get_main_window():
        try:
            return hou.qt.mainWindow()
        except AttributeError:
            if QtWidgets.QApplication.instance() is None:
                QtWidgets.QApplication(sys.argv)
            return None
except ImportError:
    class _HouFallback:
        class qt:
            @staticmethod
            def mainWindow():
                return None

        @staticmethod
        def getenv(key):
            return os.getenv(key)

    hou = _HouFallback()

    def get_main_window():
        return None

class SaveInterface(QtWidgets.QDialog):
    def __init__(self, parent=None):
        if parent is None:
            parent = get_main_window()
        super(SaveInterface, self).__init__(parent)
        
        # Use native title bar with only Close button (no Min/Max), keep resizable frame.
        self.setWindowFlags(
            QtCore.Qt.Window
            | QtCore.Qt.CustomizeWindowHint
            | QtCore.Qt.WindowTitleHint
            | QtCore.Qt.WindowCloseButtonHint
            | QtCore.Qt.WindowStaysOnTopHint
        )
        
        self.setWindowTitle("MPlay Save")
        # Fixed dialog width; height grows downward as needed
        self.setMinimumWidth(450)
        # self.setFixedWidth(550)
        self.old_pos = None
        
        # Main container widget for styling
        self.container = QtWidgets.QWidget()
        self.container.setObjectName("MainContainer") # Set object name for styling
        
        # Create and set custom arrow for combobox
        arrow_pixmap = create_arrow_pixmap()
        buffer = QtCore.QBuffer()
        buffer.open(QtCore.QIODevice.WriteOnly)
        arrow_pixmap.save(buffer, "PNG")
        base64_data = buffer.data().toBase64().data().decode()
        if USE_CUSTOM_STYLESHEET:
            self.setStyleSheet(STYLESHEET.replace("v_arrow.png", f"data:image/png;base64,{base64_data}"))
        
        self.create_widgets()
        self.create_layouts()
        self.update_widget_states() # Set initial state

        # Set the main layout for the container
        main_layout = QtWidgets.QVBoxLayout(self.container)
        main_layout.setContentsMargins(2, 2, 2, 2)
        main_layout.setSpacing(10)
        # Insert content directly; allow layout to grow but not shrink above minimum
        main_layout.addLayout(self.content_layout)
        main_layout.setSizeConstraint(QtWidgets.QLayout.SetMinAndMaxSize)

        # Set the container as the dialog's main layout
        dialog_layout = QtWidgets.QVBoxLayout(self)
        dialog_layout.setContentsMargins(0,0,0,0)
        dialog_layout.addWidget(self.container)

    def create_custom_title_bar(self):
        self.title_bar = QtWidgets.QWidget()
        self.title_bar.setObjectName("TitleBar")
        title_layout = QtWidgets.QHBoxLayout(self.title_bar)
        title_layout.setContentsMargins(10, 0, 0, 0)

        title_label = QtWidgets.QLabel("MPLAY SAVE")
        title_label.setObjectName("TitleLabel")

        close_button = QtWidgets.QPushButton("X")
        close_button.setObjectName("CloseButton")
        close_button.setFixedSize(40, 40)
        close_button.clicked.connect(self.close)

        title_layout.addWidget(title_label)
        title_layout.addStretch()
        title_layout.addWidget(close_button)

        # Enable click-drag moving by handling events on the title bar
        self._drag_start_global = None
        def _tb_mouse_press(event: QtGui.QMouseEvent):
            if event.button() == QtCore.Qt.LeftButton:
                self._drag_start_global = event.globalPosition().toPoint()
                event.accept()
        def _tb_mouse_move(event: QtGui.QMouseEvent):
            if self._drag_start_global is not None:
                delta = event.globalPosition().toPoint() - self._drag_start_global
                self.move(self.x() + delta.x(), self.y() + delta.y())
                self._drag_start_global = event.globalPosition().toPoint()
                event.accept()
        def _tb_mouse_release(event: QtGui.QMouseEvent):
            self._drag_start_global = None
            event.accept()
        self.title_bar.mousePressEvent = _tb_mouse_press
        self.title_bar.mouseMoveEvent = _tb_mouse_move
        self.title_bar.mouseReleaseEvent = _tb_mouse_release

    def create_widgets(self):
        self.filepath_type_label = QtWidgets.QLabel("Path Type")
        self.filepath_type_combo = QtWidgets.QComboBox()
        self.filepath_type_combo.addItems(["Constructed", "Explicit"])
        self.filepath_type_combo.currentTextChanged.connect(self.update_widget_states)

        self.base_folder_label = QtWidgets.QLabel("Base Folder")
        self.base_folder_edit = QtWidgets.QLineEdit("$HIP/flip")
        self.base_folder_edit.textChanged.connect(self.update_widget_states)

        self.output_path_label = QtWidgets.QLabel("Output Path")
        self.output_path_edit = QtWidgets.QLineEdit()
        self.output_path_edit.setPlaceholderText("Full output path (optionally without extension)")
        self.output_path_edit.textChanged.connect(self.update_widget_states)
        self.output_path_browse_button = QtWidgets.QPushButton("Browse...")
        self.output_path_browse_button.clicked.connect(self.browse_output_path)

        self.identifier_label = QtWidgets.QLabel("Identifier")        

        self.identifier_combo = QtWidgets.QComboBox()                
        self.identifier_combo.setEditable(True)
        self.identifier_combo.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Fixed)
        self.identifier_combo.setPlaceholderText("Name of Playblast")       
        self.identifier_combo.setEditText(hou.getenv("PRISM_TASK") or "playblast")                
        self.identifier_combo.addItems(get_existing_identifiers_for_mplay())                              
        self.identifier_combo.editTextChanged.connect(self.update_widget_states)

        self.auto_version_checkbox = QtWidgets.QCheckBox("Auto Version")
        self.auto_version_checkbox.setChecked(True)
        self.auto_version_checkbox.stateChanged.connect(self.update_widget_states)
        self.version_label = QtWidgets.QLabel("Version")
        self.version_spinbox = QtWidgets.QSpinBox()
        self.version_spinbox.setValue(1)
        self.version_spinbox.lineEdit().setTextMargins(8, 0, 4, 0)
        self.version_spinbox.setMinimum(1)
        self.version_spinbox.setMinimumWidth(54)
        self.version_spinbox.setMinimumHeight(28)
        # Update preview when version changes
        self.version_spinbox.valueChanged.connect(self.update_widget_states)

        self.format_label = QtWidgets.QLabel("Format")
        self.format_combobox = QtWidgets.QComboBox()
        self.format_combobox.addItems(["JPG", "EXR", "PNG"])
        self.format_combobox.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Fixed)
        # Update preview when format changes
        self.format_combobox.currentTextChanged.connect(self.update_widget_states)


        self.preview_path_label = QtWidgets.QLabel("Preview Path")
        self.preview_path_value = QtWidgets.QLineEdit("Undefined")
        self.preview_path_value.setReadOnly(True)
        self.preview_path_value.setStyleSheet("font-weight: normal; color: #c0c0c0;")

        # Export Video section as a checkable folder/group
        self.export_video_group = QtWidgets.QGroupBox("Export Video")
        self.export_video_group.setCheckable(True)
        self.export_video_group.setFlat(True)
        self.export_video_group.setChecked(True)
        self.export_video_group.toggled.connect(self.update_widget_states)

        self.export_video_content = QtWidgets.QWidget()
        ev_layout = QtWidgets.QHBoxLayout(self.export_video_content)
        ev_layout.setContentsMargins(10, 0, 0, 0)
        self.video_codec_label = QtWidgets.QLabel("Video Codec")
        self.video_codec_combobox = QtWidgets.QComboBox()
        # Removed ProRes; all codecs use MP4 containers
        self.video_codec_combobox.addItems(["H264", "AV1", "H265"])
        self.video_codec_combobox.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Fixed)
        self._ffmpeg_default_args_text = ""
        self.video_codec_combobox.currentTextChanged.connect(self._on_video_codec_changed)
        # New: keep image sequence toggle (default true)
        self.keep_sequence_checkbox = QtWidgets.QCheckBox("Keep Image Sequence")
        self.keep_sequence_checkbox.setChecked(False)

        self.ffmpeg_args_label = QtWidgets.QLabel("FFmpeg Args")
        self.ffmpeg_args_lineedit = QtWidgets.QLineEdit()
        self.ffmpeg_args_lineedit.setPlaceholderText("FFmpeg codec/filter args")
        self.ffmpeg_args_reset_button = QtWidgets.QPushButton("Reset")
        self.ffmpeg_args_reset_button.setMinimumHeight(24)
        self.ffmpeg_args_reset_button.setMaximumHeight(24)
        self.ffmpeg_args_reset_button.setMaximumWidth(54)
        self.ffmpeg_args_reset_button.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        self.ffmpeg_args_reset_button.clicked.connect(self._reset_ffmpeg_args_to_default)

        ev_layout.addWidget(self.video_codec_label)
        ev_layout.addWidget(self.video_codec_combobox)
        ev_layout.addWidget(self.keep_sequence_checkbox)
        ev_layout.addStretch()

        self.export_video_args_content = QtWidgets.QWidget()
        ev_args_layout = QtWidgets.QHBoxLayout(self.export_video_args_content)
        ev_args_layout.setContentsMargins(10, 0, 0, 0)
        ev_args_layout.addWidget(self.ffmpeg_args_label)
        ev_args_layout.addWidget(self.ffmpeg_args_lineedit)
        ev_args_layout.addWidget(self.ffmpeg_args_reset_button)

        ev_group_layout = QtWidgets.QVBoxLayout(self.export_video_group)
        ev_group_layout.setContentsMargins(10, 6, 10, 6)
        ev_group_layout.addWidget(self.export_video_content)
        ev_group_layout.addWidget(self.export_video_args_content)
        self._reset_ffmpeg_args_to_default()

        for combo in (self.filepath_type_combo, self.format_combobox, self.video_codec_combobox, self.identifier_combo):
            self._set_combobox_min_width(combo)
        # Keep short combos from stretching too wide in the form layout.
        self.format_combobox.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        self.video_codec_combobox.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        self.format_combobox.setMaximumWidth(self.format_combobox.minimumWidth() + 20)
        self.video_codec_combobox.setMaximumWidth(self.video_codec_combobox.minimumWidth() + 20)

        # Export button
        self.export_button = QtWidgets.QPushButton("EXPORT")
        self.export_button.setObjectName("ExportButton")
        export_font = self.export_button.font()        
        export_font.setBold(True)
        self.export_button.setFont(export_font)
        self.export_button.setStyleSheet("color: #FE9532;")
        self.export_button.clicked.connect(self.on_export_clicked)
        
        # Progress bar below export button
        self.progress_bar = QtWidgets.QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        
        # Console output for logger
        self.console_output = QtWidgets.QTextEdit()
        self.console_output.setReadOnly(True)
        self.console_output.setMinimumHeight(100)
        self.console_output.setStyleSheet("background-color: #1a1c1e; color: #c0c0c0; border: 1px solid #4a4d50;")
        # Use a readable monospace font for console
        try:
            mono = QtGui.QFont("Consolas")
            mono.setPointSize(8)
            self.console_output.setFont(mono)
        except Exception:
            pass

        self.open_folder_button = QtWidgets.QPushButton("Open Folder")
        self.open_folder_button.clicked.connect(self.open_folder)

    def create_layouts(self):
        self.content_layout = QtWidgets.QVBoxLayout()
        self.content_layout.setContentsMargins(20, 10, 20, 20)
        self.content_layout.setSpacing(15)

        form_layout = QtWidgets.QFormLayout()
        form_layout.setSpacing(10)
        form_layout.setLabelAlignment(QtCore.Qt.AlignLeft)
        form_layout.setFieldGrowthPolicy(QtWidgets.QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)

        form_layout.addRow(self.filepath_type_label, self.filepath_type_combo)

        base_folder_layout = QtWidgets.QHBoxLayout()
        base_folder_layout.addWidget(self.base_folder_edit)
        base_folder_layout.addWidget(self.open_folder_button)
        form_layout.addRow(self.base_folder_label, base_folder_layout)

        output_path_layout = QtWidgets.QHBoxLayout()
        output_path_layout.addWidget(self.output_path_edit)
        output_path_layout.addWidget(self.output_path_browse_button)
        form_layout.addRow(self.output_path_label, output_path_layout)

        
        # Identifier row: line edit + dropdown
        form_layout.addRow(self.identifier_label, self.identifier_combo)

        version_layout = QtWidgets.QHBoxLayout()
        # Keep VERSION label in place, then checkbox aligned with field column, spinbox aligned right
        # version_layout.addWidget(self.version_label)
        version_layout.addStretch()
        version_layout.addWidget(self.auto_version_checkbox)
        version_layout.addWidget(self.version_spinbox, alignment=QtCore.Qt.AlignRight)
        form_layout.addRow(self.version_label, version_layout)

        form_layout.addRow(self.format_label, self.format_combobox)
        form_layout.addRow(self.preview_path_label, self.preview_path_value)
        

        self.content_layout.addLayout(form_layout)


        # Export Video as checkable group
        self.content_layout.addWidget(self.export_video_group)

        self.content_layout.addStretch()

        # Export button
        self.content_layout.addWidget(self.export_button)
        # Progress bar and console output below export button
        self.content_layout.addWidget(self.progress_bar)
        self.content_layout.addWidget(self.console_output)
        
        # Attach logger handler now that console exists
        self.attach_logger_to_console()

    def _set_combobox_min_width(self, combobox: QtWidgets.QComboBox):
        fm = combobox.fontMetrics()
        style = combobox.style()
        max_text_width = 0
        for i in range(combobox.count()):
            max_text_width = max(max_text_width, fm.horizontalAdvance(combobox.itemText(i)))
        if combobox.isEditable():
            max_text_width = max(max_text_width, fm.horizontalAdvance(combobox.currentText() or combobox.placeholderText() or ""))
        # Extra padding equivalent to 2 characters to prevent style/theme clipping.
        max_text_width += fm.horizontalAdvance("00")
        frame = style.pixelMetric(QtWidgets.QStyle.PM_DefaultFrameWidth, None, combobox)
        arrow = style.pixelMetric(QtWidgets.QStyle.PM_ScrollBarExtent, None, combobox)
        combobox.setMinimumWidth(max_text_width + (frame * 2) + arrow + 20)

    def _expand_hip_token(self, path: str) -> str:
        """Expand $HIP using hou.getenv instead of hou.text.expandString (MPlay bug workaround)."""
        path = path or ""
        try:
            hip_value = hou.getenv("HIP") or ""
        except Exception:
            hip_value = os.getenv("HIP", "")
        if not hip_value:
            return path
        return path.replace("${HIP}", hip_value).replace("$HIP", hip_value)

    def _to_preview_path(self, path: str) -> str:
        """Path text for preview: expand $HIP only and keep frame token unexpanded."""
        return self._expand_hip_token(path).replace("\\", "/")

    def on_export_clicked(self):
        """Handle Export: save image sequence via hscript and log output.
        Step 1: Run `imgsave -a` with the preview path.
        """
        # Ensure UI state and preview path are up to date before exporting
        try:
            self.update_widget_states()
        except Exception:
            pass
        # Show busy progress and disable button
        try:
            self.progress_bar.setVisible(True)
            self.progress_bar.setRange(0, 0)  # indeterminate
            self.export_button.setEnabled(False)
        except Exception:
            pass

        # Build path fresh from function (avoid stale preview)
        try:
            output_path, _ = self._build_playblast_path()
        except Exception as e:
            logger.error(f"Cannot export: {e}")
            # Restore UI state
            try:
                self.progress_bar.setVisible(False)
                self.export_button.setEnabled(True)
            except Exception:
                pass
            return

        # Overwrite prevention: if any target sequence frames already exist, abort
        try:
            import hou
            # Determine current frame range
            fr_out, _ = hou.hscript("frange")
            start_frame, end_frame = None, None
            parts = fr_out.strip().replace("Frame range:", "").split("to")
            if len(parts) == 2:
                start_frame = int(parts[0].strip())
                end_frame = int(parts[1].strip())
            # Build a glob to check for existing files
            first_frame = start_frame if start_frame is not None else 1
            # Expand env vars safely ($HIP via hou.getenv) while preserving expected frame replacement
            check_first = os.path.expandvars(self._expand_hip_token(output_path.replace("$F4", f"{first_frame:04d}")))
            # Also check any frame pattern
            check_glob = os.path.expandvars(self._expand_hip_token(output_path.replace("$F4", "*").replace("$PRISM_JOB", os.getenv("PRISM_JOB", ""))))
            if os.path.exists(check_first):
                logger.error(f"Export aborted: target frame exists: {check_first}")
                # UI restore
                try:
                    self.progress_bar.setVisible(False)
                    self.export_button.setEnabled(True)
                except Exception:
                    pass
                return
            # If any matching files exist in version folder, abort to prevent overwrite
            try:
                import glob
                existing = glob.glob(check_glob)
                if existing:
                    logger.error("Export aborted: sequence already exists in target version folder.")
                    try:
                        self.progress_bar.setVisible(False)
                        self.export_button.setEnabled(True)
                    except Exception:
                        pass
                    return
            except Exception:
                pass
        except Exception:
            # If hou not available, proceed but log we couldn't pre-check
            logger.warning("Could not pre-check for existing frames; proceeding cautiously.")

        # Get the path from preview and escape $F for hscript
        resolved_output_path = os.path.expandvars(self._expand_hip_token(output_path)).replace("\\", "/")
        escaped_path = resolved_output_path.replace("$F", "\\$F")

        logger.info(f"Running imgsave for sequence: {escaped_path}")
        # Execute hscript and capture output
        try:
            import hou
            # Let the UI show the spinner briefly
            QtWidgets.QApplication.processEvents()
            QtCore.QThread.msleep(150)
            # Get frame range from hou.hscript("frange") output like: 'Frame range: 1 to 16\n'
            fr_out, _ = hou.hscript("frange")
            start_frame, end_frame = None, None
            parts = fr_out.strip().replace("Frame range:", "").split("to")
            if len(parts) == 2:
                start_frame = int(parts[0].strip())
                end_frame = int(parts[1].strip())
            if start_frame is not None and end_frame is not None:
                imgsave_cmd = f'imgsave -f {start_frame} {end_frame} "{escaped_path}"'
            else:
                # fallback to all frames
                imgsave_cmd = f'imgsave -a "{escaped_path}"'
            out, err = hou.hscript(imgsave_cmd)
            if out:
                logger.info(out.strip())
            if err:
                logger.error(err.strip())
            logger.info("Image sequence save completed.")

            # Step 1.5: Write versioninfo.json next to first frame
            logger.info("Writing versioninfo.json...")
            write_version_info(filepath=os.path.expandvars(self._expand_hip_token(output_path)), comment="")
            logger.info("versioninfo.json written.")
            # Step 2: If Export Video is enabled, encode sequence to a video
            try:
                if self.export_video_group.isChecked():
                    self.run_ffmpeg_encode()
            except Exception as ff_err:
                logger.exception(f"FFmpeg encode failed: {ff_err}")
        except Exception as e:
            logger.exception(f"imgsave failed: {e}")            
        finally:
            # Restore UI state
            try:
                self.progress_bar.setRange(0, 100)
                self.progress_bar.setValue(100)
                QtWidgets.QApplication.processEvents()
                QtCore.QTimer.singleShot(300, lambda: self.progress_bar.setVisible(False))
                self.export_button.setEnabled(True)
                # Update widgets after finishing export step
                try:
                    self.update_widget_states()
                except Exception:
                    pass
            except Exception:
                logger.exception("Failed to restore UI state after export.")
                pass

    def update_widget_states(self):
        """Enable/disable widgets based on checkbox states and update paths."""
        is_explicit = self.filepath_type_combo.currentText().lower() == "explicit"

        self.base_folder_label.setVisible(not is_explicit)
        self.base_folder_edit.setVisible(not is_explicit)
        self.open_folder_button.setVisible(not is_explicit)
        self.identifier_label.setVisible(not is_explicit)
        self.identifier_combo.setVisible(not is_explicit)
        self.version_label.setVisible(not is_explicit)
        self.auto_version_checkbox.setVisible(not is_explicit)
        self.version_spinbox.setVisible(not is_explicit)

        self.output_path_label.setVisible(is_explicit)
        self.output_path_edit.setVisible(is_explicit)
        self.output_path_browse_button.setVisible(is_explicit)

        self.version_spinbox.setEnabled((not self.auto_version_checkbox.isChecked()) and (not is_explicit))

        # Toggle video settings visibility based on group toggle
        is_enabled = self.export_video_group.isChecked()
        self.export_video_content.setVisible(is_enabled)
        self.export_video_args_content.setVisible(is_enabled)
        self.video_codec_combobox.setEnabled(is_enabled)
        self.keep_sequence_checkbox.setEnabled(is_enabled)
        self.ffmpeg_args_lineedit.setEnabled(is_enabled)
        self.ffmpeg_args_reset_button.setEnabled(is_enabled)

        
        self.generate_playblast_path()
        
        # Avoid resizing/jumping on toggle; size is fixed at show

        # Auto-version: look up next version when enabled
        
        if self.auto_version_checkbox.isChecked():
            next_ver = self.lookup_next_version()
            if next_ver:
                self.version_spinbox.blockSignals(True)
                self.version_spinbox.setValue(next_ver)
                self.version_spinbox.blockSignals(False)
        

    def showEvent(self, event):
        super().showEvent(event)
        self.attach_logger_to_console()

    def attach_logger_to_console(self):
        # Create a logging handler that writes to the QTextEdit
        if not hasattr(self, 'console_output'):
            return
        # Ensure logs do not propagate to Houdini/MPlay root logger
        logger.propagate = False
        # Remove any StreamHandler to stdout so only UI console receives logs
        try:
            for h in list(logger.handlers):
                if isinstance(h, logging.StreamHandler) and getattr(h, 'stream', None) is sys.stdout:
                    logger.removeHandler(h)
        except Exception:
            pass
        class QTextEditHandler(logging.Handler):
            def __init__(self, widget):
                super().__init__()
                self.widget = widget
                self.setLevel(logging.DEBUG)
                # Match global formatter: no timestamp
                fmt = logging.Formatter('%(levelname)s - %(message)s')
                self.setFormatter(fmt)
            def emit(self, record):
                # Guard against deleted Qt objects
                if not _qt_is_valid(self.widget):
                    return
                msg = self.format(record)
                try:
                    QtCore.QMetaObject.invokeMethod(
                        self.widget,
                        "append",
                        QtCore.Qt.QueuedConnection,
                        QtCore.Q_ARG(str, msg)
                    )
                    # Auto-scroll to bottom after appending
                    try:
                        QtCore.QMetaObject.invokeMethod(
                            self.widget,
                            "moveCursor",
                            QtCore.Qt.QueuedConnection,
                            QtCore.Q_ARG(QtGui.QTextCursor.MoveOperation, QtGui.QTextCursor.End)
                        )
                        QtCore.QMetaObject.invokeMethod(
                            self.widget,
                            "ensureCursorVisible",
                            QtCore.Qt.QueuedConnection
                        )
                    except Exception:
                        pass
                except RuntimeError:
                    # Widget likely deleted; ignore
                    pass
        # Avoid duplicate handlers targeting this console_output
        for h in logger.handlers:
            if isinstance(h, logging.Handler) and getattr(h, 'widget', None) is self.console_output:
                return
        self._console_log_handler = QTextEditHandler(self.console_output)
        logger.addHandler(self._console_log_handler)
        # Emit a small message confirming attachment
        logger.debug("Console logger attached")
        # Flush any buffered logs captured before UI existed
        try:
            buf = getattr(logger, "_buffer_handler", None)
            if buf and isinstance(buf, logging.handlers.BufferingHandler):
                for rec in list(buf.buffer):
                    logger.handle(rec)
                buf.flush()
                logger.removeHandler(buf)
                logger._buffer_handler = None
                logger.debug("Buffered logs flushed to console")
        except Exception:
            pass

    def closeEvent(self, event):
        global dialog_instance
        # Detach console logger handler to avoid emitting to deleted widget on reload
        try:
            if hasattr(self, '_console_log_handler') and self._console_log_handler in logger.handlers:
                logger.removeHandler(self._console_log_handler)
                self._console_log_handler = None
            # Also clear any buffer handler
            buf = getattr(logger, "_buffer_handler", None)
            if buf and buf in logger.handlers:
                logger.removeHandler(buf)
                logger._buffer_handler = None
        except Exception:
            pass
        dialog_instance = None
        super().closeEvent(event)


    def generate_playblast_path(self):
        """Generates and displays the playblast output path based on Prism env vars."""
        try:
            full_path, _ = self._build_playblast_path()
            self.preview_path_value.setText(self._to_preview_path(full_path))
        except Exception as e:
            self.preview_path_value.setText(str(e))

    def _build_playblast_path(self):
        """Construct the canonical playblast output path for normal exporter.
        Returns (full_path, shasset_path). Raises on invalid context.
        """
        import re

        extension = (self.format_combobox.currentText() or "jpg").lower()
        frame_token = "$F4"
        is_explicit = self.filepath_type_combo.currentText().lower() == "explicit"

        if is_explicit:
            explicit_path = self.output_path_edit.text().strip()
            if not explicit_path:
                raise RuntimeError("Output path is empty.")

            # Normalize frame token variants to our canonical token.
            # Supported forms: $F, $F1..$F4, ####, %04d (and similar printf variants).
            explicit_path = re.sub(r"\$F(?:[1-4])?", frame_token, explicit_path)
            explicit_path = re.sub(r"%0?\d*d", frame_token, explicit_path, flags=re.IGNORECASE)
            explicit_path = re.sub(r"#{1,8}", frame_token, explicit_path)

            # Always enforce selected extension for explicit output.
            explicit_root, explicit_ext = os.path.splitext(explicit_path)
            if explicit_ext:
                explicit_path = f"{explicit_root}.{extension}"
            else:
                explicit_path = f"{explicit_path}.{extension}"

            # Ensure frame token exists in filename (not just somewhere in the path).
            filename = os.path.basename(explicit_path)
            if frame_token not in filename:
                dirname = os.path.dirname(explicit_path)
                stem, _ = os.path.splitext(filename)
                normalized_name = f"{stem}.{frame_token}.{extension}"
                explicit_path = os.path.join(dirname, normalized_name) if dirname else normalized_name

            return explicit_path, ""

        base_folder = (self.base_folder_edit.text().strip() or "$HIP/flip").rstrip("/\\")
        identifier = (self.identifier_combo.currentText().strip() or "playblast")
        version_num = int(self.version_spinbox.value())
        version_str = f"v{version_num:04d}"

        filename = f"{identifier}_{version_str}.{frame_token}.{extension}"
        full_path = os.path.join(base_folder, identifier, version_str, filename)
        full_path = full_path.replace("\\", "/")
        return full_path, base_folder

    def lookup_next_version(self) -> int:
        """Scan constructed output folder for latest v#### and return next."""
        import os, re
        if self.filepath_type_combo.currentText().lower() == "explicit":
            return 1

        base = (self.base_folder_edit.text().strip() or "$HIP/flip").rstrip("/\\")
        try:
            base = os.path.expandvars(self._expand_hip_token(base))
        except Exception:
            base = os.path.expandvars(base)

        identifier = (self.identifier_combo.currentText().strip() or "identifier")
        lookup_dir = os.path.join(base, identifier)
        if not os.path.isdir(lookup_dir):
            return 1
        versions = []
        pat = re.compile(r"^v(\d+)$")
        try:
            for d in os.listdir(lookup_dir):
                m = pat.match(d)
                if m and os.path.isdir(os.path.join(lookup_dir, d)):
                    versions.append(int(m.group(1)))
        except OSError:
            return 1
        return (max(versions) + 1) if versions else 1

    def populate_identifiers(self, base: str, shasset_path: str):
        """Fill the identifier dropdown with existing folders under Playblasts."""
        import os
        lookup_dir = f"{base}/{shasset_path}/Playblasts"
        items = []
        if os.path.isdir(lookup_dir):
            try:
                items = sorted([d for d in os.listdir(lookup_dir)
                                if os.path.isdir(os.path.join(lookup_dir, d))])
            except OSError:
                items = []

        # Preserve current text while updating list
        current_text = self.identifier_combo.currentText()
        current_items = [self.identifier_combo.itemText(i) for i in range(self.identifier_combo.count())]
        if items != current_items:
            self.identifier_combo.blockSignals(True)
            self.identifier_combo.clear()
            if items:
                self.identifier_combo.addItems(items)
            if current_text:
                self.identifier_combo.setEditText(current_text)
            self.identifier_combo.blockSignals(False)

    def open_folder(self):
        """Open the current base folder directory."""
        try:
            import os
            import hou
            folder_path = (self.base_folder_edit.text() or "").strip()
            folder_path = os.path.expandvars(self._expand_hip_token(folder_path))
            folder_path = os.path.normpath(folder_path)
            if not folder_path:
                logger.warning("Base folder is empty.")
                return
            original = folder_path
            for _ in range(4):
                if os.path.exists(folder_path):
                    QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(folder_path))
                    return
                parent = os.path.dirname(folder_path)
                if parent == folder_path:
                    break
                folder_path = parent
            try:
                import hou
                hou.ui.displayMessage(f"Folder does not exist: {original}", severity=hou.severityType.Warning)
            except Exception:
                logger.warning(f"Folder does not exist: {original}")
        except Exception:
            logger.exception("Failed to open folder.")
            pass

    def browse_output_path(self):
        """Open a file picker to select explicit output path."""
        try:
            import os
            try:
                start_dir = os.path.expandvars(self._expand_hip_token(self.base_folder_edit.text().strip() or "$HIP"))
            except Exception:
                start_dir = os.path.expandvars(self.base_folder_edit.text().strip() or os.getcwd())

            current_value = self.output_path_edit.text().strip()
            if current_value:
                start_dir = os.path.dirname(current_value) or start_dir

            file_filter = "Images/Video (*.jpg *.jpeg *.png *.exr *.mp4 *.mov);;All Files (*)"
            selected_path, _ = QtWidgets.QFileDialog.getSaveFileName(
                self,
                "Select Output Path",
                start_dir,
                file_filter,
            )
            if selected_path:
                self.output_path_edit.setText(selected_path)
        except Exception:
            logger.exception("Failed to browse for output path.")

    def _default_ffmpeg_codec_args(self, codec: str) -> list[str]:
        if "AV1" in codec:
            return [
                "-c:v",
                "av1_nvenc",
                "-preset",
                "p3",
                "-cq",
                "24",
                "-pix_fmt",
                "yuv420p10le",
                "-vf",
                "crop=iw-mod(iw\\,2):ih-mod(ih\\,2)",
            ]
        if "H264" in codec or "H.264" in codec:
            return [
                "-c:v",
                "h264_nvenc",
                "-preset",
                "p4",
                "-cq",
                "22",
                "-pix_fmt",
                "yuv444p",
                "-vf",
                "crop=iw-mod(iw\\,2):ih-mod(ih\\,2)",
            ]
        if "H265" in codec or "H.265" in codec:
            return [
                "-c:v",
                "hevc_nvenc",
                "-preset",
                "p4",
                "-cq",
                "24",
                "-pix_fmt",
                "yuv444p",
                "-vf",
                "crop=iw-mod(iw\\,2):ih-mod(ih\\,2)",
            ]
        return [
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-crf",
            "20",
            "-pix_fmt",
            "yuv420p",
            "-vf",
            "crop=iw-mod(iw\\,2):ih-mod(ih\\,2)",
        ]

    def _on_video_codec_changed(self):
        old_default = self._ffmpeg_default_args_text
        current_value = self.ffmpeg_args_lineedit.text().strip()
        if not current_value or current_value == old_default:
            self._reset_ffmpeg_args_to_default()

    def _reset_ffmpeg_args_to_default(self):
        codec = self.video_codec_combobox.currentText()
        default_args = self._default_ffmpeg_codec_args(codec)
        default_text = " ".join(default_args)
        self._ffmpeg_default_args_text = default_text
        self.ffmpeg_args_lineedit.setText(default_text)

    def open_in_prism(self):
        # Placeholder: integrate with Prism to open path
        logger.info("Open in Prism triggered")


        # --- Window Dragging Methods ---
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(100)
        QtWidgets.QApplication.processEvents()
        QtCore.QTimer.singleShot(600, lambda: self.progress_bar.setVisible(False))
    def mouseMoveEvent(self, event):
        if self.old_pos is not None:
            delta = event.globalPosition().toPoint() - self.old_pos
            self.move(self.x() + delta.x(), self.y() + delta.y())

    def _build_sequence_glob_and_output(self):
        """Return (input_glob, output_video_path, container_ext, codec_args).
            # Re-enable stdout handler if needed by environment by adding a NullHandler
            try:
                if not logger.handlers:
                    logger.addHandler(logging.NullHandler())
            except Exception:
                pass
        Input glob is expanded file path with %04d replacing $F4.
        """
        import os
        try:
            import hou
        except Exception:
            raise RuntimeError("hou module not found")

        preview_value = self.preview_path_value.text().strip().replace("\\", "/")
        expanded = os.path.expandvars(self._expand_hip_token(preview_value)).replace("$F4", "%04d")
        # Replace frame token with printf-style pattern
        input_glob = expanded

        codec = self.video_codec_combobox.currentText()
        # Determine container
        if "AV1" in codec:
            container = "mp4"
        elif "H264" in codec or "H.264" in codec:
            container = "mp4"
        elif "H265" in codec or "H.265" in codec:
            container = "mp4"
        # ProRes removed
        else:
            container = "mp4"

        custom_args_text = self.ffmpeg_args_lineedit.text().strip()
        if custom_args_text:
            codec_args = custom_args_text.split()
        else:
            codec_args = self._default_ffmpeg_codec_args(codec)

        # Output path: same directory as sequence, with video container
        out_dir = os.path.dirname(expanded)
        base_name = os.path.splitext(os.path.basename(expanded))[0]
        # replace %04d with base name without frame token
        if "%04d" in base_name:
            base_name = base_name.replace("%04d", "").rstrip("._")
        output_video = os.path.join(out_dir, f"{base_name}.{container}")
        return input_glob, output_video, container, codec_args

    def run_ffmpeg_encode(self):
        """Run Houdini's hffmpeg using QProcess to keep UI responsive, and log elapsed time."""
        import os, time
        try:
            import hou
        except Exception:
            raise RuntimeError("hou module not found")

        hfs = hou.getenv("HFS")
        if not hfs:
            raise RuntimeError("HFS environment variable not set; cannot locate hffmpeg.exe")
        ffmpeg_path = os.path.join(hfs, "bin", "hffmpeg.exe")
        if not os.path.exists(ffmpeg_path):
            raise RuntimeError(f"hffmpeg not found at: {ffmpeg_path}")

        input_glob, output_video, container, codec_args = self._build_sequence_glob_and_output()
        # log input glob
        logger.info(f"Input Sequence: {input_glob}")
        logger.info(f"Encoding video: {output_video}")

        # Overwrite prevention for video output
        if os.path.exists(output_video):
            logger.error(f"Video encode aborted: target file exists: {output_video}")
            try:
                self.progress_bar.setVisible(False)
            except Exception:
                pass
            return

        # Build arguments for QProcess using scene FPS
        # Build args; codec_args already includes appropriate -pix_fmt
        fps = int(hou.fps())
        start_frame = 1
        try:
            fr_out, _ = hou.hscript("frange")
            parts = fr_out.strip().replace("Frame range:", "").split("to")
            if len(parts) == 2:
                start_frame = int(parts[0].strip())
        except Exception:
            start_frame = 1

        args = ["-y", "-framerate", str(fps)]
        if start_frame != 1:
            args += ["-start_number", str(start_frame)]
        args += ["-i", input_glob] + codec_args
        args += [output_video]

        # Show progress bar indeterminate during encode
        try:
            self.progress_bar.setVisible(True)
            self.progress_bar.setRange(0, 0)
            QtWidgets.QApplication.processEvents()
        except Exception:
            pass

        # Use QProcess for safer execution within Qt app
        self._ffmpeg_proc = QtCore.QProcess(self)
        self._ffmpeg_start_ts = time.time()

        def _read_stdout():
            try:
                data = self._ffmpeg_proc.readAllStandardOutput().data().decode(errors='ignore')
                for line in data.splitlines():
                    if line:
                        logger.info(line)
            except Exception:
                pass
        def _read_stderr():
            try:
                data = self._ffmpeg_proc.readAllStandardError().data().decode(errors='ignore')
                for line in data.splitlines():
                    if line:
                        logger.info(line)
            except Exception:
                pass
        def _finished(code, status):
            elapsed = 0.0
            try:
                elapsed = time.time() - (self._ffmpeg_start_ts or time.time())
            except Exception:
                pass
            if code == 0 and status == QtCore.QProcess.ExitStatus.NormalExit:
                logger.info("FFmpeg encode completed successfully.")
                logger.info(f"FFmpeg total time: {elapsed:.2f}s")
                if not self.keep_sequence_checkbox.isChecked():
                    try:
                        self._delete_sequence_files(input_glob)
                        logger.info("Image sequence deleted.")
                    except Exception:
                        logger.warning("Failed to delete image sequence.")
            else:
                # Avoid casting ExitStatus to int; use string representation
                try:
                    status_str = getattr(status, "name", str(status))
                except Exception:
                    status_str = str(status)
                logger.error(f"FFmpeg exited with code {code}, status {status_str}.")
                logger.info(f"FFmpeg total time: {elapsed:.2f}s")
            # Restore progress bar briefly, then hide
            try:
                self.progress_bar.setRange(0, 100)
                self.progress_bar.setValue(100)
                QtWidgets.QApplication.processEvents()
                QtCore.QTimer.singleShot(600, lambda: self.progress_bar.setVisible(False))
            except Exception:
                pass
            # Refresh UI state after full export finishes
            try:
                self.update_widget_states()
            except Exception:
                pass
            self._ffmpeg_proc = None

        self._ffmpeg_proc.readyReadStandardOutput.connect(_read_stdout)
        self._ffmpeg_proc.readyReadStandardError.connect(_read_stderr)
        self._ffmpeg_proc.finished.connect(_finished)

        self._ffmpeg_proc.start(ffmpeg_path, args)
        if not self._ffmpeg_proc.waitForStarted(3000):
            logger.error("Failed to start FFmpeg process.")
            try:
                self.progress_bar.setVisible(False)
            except Exception:
                pass

    def _delete_sequence_files(self, input_glob: str):
        """Delete all files matching the printf-style sequence glob."""
        import os, glob
        # Convert printf-style %04d to glob pattern
        pat = input_glob.replace("%04d", "????")
        for f in glob.glob(pat):
            try:
                os.remove(f)
            except Exception:
                pass
        # No UI interaction here; silent cleanup only

    def mouseReleaseEvent(self, event):
        self.old_pos = None


def main(kwargs):
    global dialog_instance
    # logger.debug(f"main called with kwargs: {kwargs}")
    action_id = kwargs.get("toolname")
    # import hou
        
    if action_id == "Save...":
        logger.info("'Save...' action triggered.")
        if dialog_instance and dialog_instance.isVisible():
            logger.debug("Found existing dialog instance. Raising and activating.")
            dialog_instance.raise_()
            dialog_instance.activateWindow()
            dialog_instance.show()  # ensure it's not minimized
            return

        logger.debug("Creating new SaveInterface dialog.")
        dialog_instance = SaveInterface()
        dialog_instance.show()
        logger.debug("SaveInterface dialog shown.")

    elif action_id == "Quicksave":
        logger.info("Quicksave action triggered")
    elif action_id == "debug":

        # MPlay variables are missing?
        # Custom variables like PRISM_JOB are passed through
        # builtins like HIPFILE and HIPNAME are lost to defaults
        # HIP comes through ONLY with hou.getenv() but not other methods
        print(hou.getenv("PRISM_JOB"))# ✅ S:/RockinVFX/01_Sandbox
        print(hou.getenv("HIP"))  #     ✅ S:/RockinVFX/01_Sandbox/03_Production/Assets/mifolder/anasset/Scenefiles/cpt/Concept
        print(hou.getenv("HIPFILE"))  # ❌ C:/Users/luisf/untitled.hip
        print(hou.getenv("HIPNAME"))  # ❌ untitled
        print(hou.text.expandString("$PRISM_JOB"))# ✅ S:/RockinVFX/01_Sandbox
        print(hou.text.expandString("$HIP"))  #     ❌ C:/Users/luisf
        print(hou.text.expandString("$HIPFILE"))  # ❌ C:/Users/luisf/untitled.hip
        print(hou.hscript("echo $PRISM_JOB"))  # ✅ ('S:/RockinVFX/01_Sandbox\n', '')
        print(hou.hscript("echo $HIP"))  #       ❌ ('C:/Users/luisf\n', '')
        print(hou.hscript("echo $HIPFILE"))  #   ❌ ('C:/Users/luisf/untitled.hip\n', '')
        print(os.environ['PRISM_JOB'])# ✅  S:/RockinVFX/01_Sandbox
        print(os.environ['HIP'])  #     ❌  C:/Users/luisf
        print(os.environ['HIPFILE'])  # ❌  C:/Users/luisf/untitled.hip

        print(hou.text.expandString("$RFSTART"))
        print(hou.text.expandString("$RFEND"))
        print(hou.text.expandString("$FPS")) # good

        print(hou.getenv("FPS")) # wrong
        print(hou.fps()) # good
        # print(hou.playbar.playbackRange())
        # print(hou.playbar.selectionRange())
        print(hou.hscript("frange"))
        print(hou.hscript("echo $RFSTART"))


        logger.info("Debug action triggered")
    elif action_id == "reload":
        logger.info("mplay_export module reloaded.")
    else:
        logger.warning(f"Unknown action: {action_id}")


if __name__ == "__main__":

    app = QtWidgets.QApplication.instance()
    if app is None:
        app = QtWidgets.QApplication(sys.argv)

    kwargs = {"toolname": "Save..."}
    main(kwargs)
    sys.exit(app.exec())