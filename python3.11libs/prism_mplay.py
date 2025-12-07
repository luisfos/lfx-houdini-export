import sys
import logging
from PySide6 import QtWidgets, QtCore, QtGui

# --- Logging Setup ---
def setup_logger():
    logger = logging.getLogger(__name__)
    if not logger.handlers:
        logger.setLevel(logging.DEBUG)
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger

logger = setup_logger()

# --- Global variable to hold dialog reference ---
dialog_instance = None

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
    font-size: 18px;
    font-weight: bold;
    padding: 5px;
}

#CloseButton {
    background-color: transparent;
    color: #FE9532;
    border: none;
    font-size: 20px;
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
    font-size: 14px;
    font-weight: bold;
}

/* Inputs */
QLineEdit, QTextEdit, QSpinBox, QComboBox {
    background-color: #1a1c1e;
    color: #e0e0e0;
    border: 1px solid #4a4d50;
    border-radius: 4px;
    padding: 5px;
    font-size: 14px;
}

QLineEdit:focus, QTextEdit:focus, QSpinBox:focus, QComboBox:focus {
    border: 1px solid #FE9532;
}

/* Checkboxes */
QCheckBox {
    color: #c0c0c0;
    font-size: 14px;
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
    font-size: 18px;
    padding: 10px;
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
    def get_main_window():
        if QtWidgets.QApplication.instance() is None:
            QtWidgets.QApplication(sys.argv)
        return None

class SaveInterface(QtWidgets.QDialog):
    def __init__(self, parent=get_main_window()):
        super(SaveInterface, self).__init__(parent)
        
        # Make window frameless; avoid global always-on-top
        # We'll raise/activate on show to keep above MPlay
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        
        self.setWindowTitle("MPlay Prism Save")
        # Fixed dialog width; height grows downward as needed
        self.setMinimumWidth(450)
        # self.setFixedWidth(550)
        
        # For moving the frameless window
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
        self.setStyleSheet(STYLESHEET.replace("v_arrow.png", f"data:image/png;base64,{base64_data}"))
        
        self.create_custom_title_bar()
        self.create_widgets()
        self.create_layouts()
        self.update_widget_states() # Set initial state

        # Set the main layout for the container
        main_layout = QtWidgets.QVBoxLayout(self.container)
        main_layout.setContentsMargins(2, 2, 2, 2)
        main_layout.setSpacing(10)
        main_layout.addWidget(self.title_bar)
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

        title_label = QtWidgets.QLabel("MPLAY PRISM SAVE")
        title_label.setObjectName("TitleLabel")

        close_button = QtWidgets.QPushButton("X")
        close_button.setObjectName("CloseButton")
        close_button.setFixedSize(40, 40)
        close_button.clicked.connect(self.close)

        title_layout.addWidget(title_label)
        title_layout.addStretch()
        title_layout.addWidget(close_button)

    def create_widgets(self):
        self.context_label = QtWidgets.QLabel("CONTEXT")
        self.context_value = QtWidgets.QLabel("ASSET - TOPHE")
        self.context_value.setStyleSheet("text-transform: none; font-weight: normal; color: #c0c0c0;")

        self.identifier_label = QtWidgets.QLabel("IDENTIFIER")
        # Single editable dropdown for identifier
        self.identifier_combo = QtWidgets.QComboBox()
        self.identifier_combo.setEditable(True)
        self.identifier_combo.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)

        self.auto_version_checkbox = QtWidgets.QCheckBox("AUTO VERSION")
        self.auto_version_checkbox.setChecked(True)
        self.auto_version_checkbox.stateChanged.connect(self.update_widget_states)
        self.version_label = QtWidgets.QLabel("VERSION:")
        self.version_spinbox = QtWidgets.QSpinBox()
        self.version_spinbox.setValue(1)
        self.version_spinbox.setMinimum(1)

        self.format_label = QtWidgets.QLabel("FORMAT")
        self.format_combobox = QtWidgets.QComboBox()
        self.format_combobox.addItems(["JPG", "PNG", "EXR", "TIF"])
        self.format_combobox.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Fixed)


        self.preview_path_label = QtWidgets.QLabel("PREVIEW PATH")
        self.preview_path_value = QtWidgets.QLabel("...V0001/MY_IDENTIFIER_V0001.$F4JPG")
        self.preview_path_value.setStyleSheet("text-transform: none; font-weight: normal; color: #c0c0c0;")
        self.preview_path_value.setWordWrap(True)

        # Comment section
        self.comment_label = QtWidgets.QLabel("COMMENT")
        self.comment_edit = QtWidgets.QTextEdit("MY COMMENT")
        self.comment_edit.setFixedHeight(60)

        # Export Video section as a checkable folder/group
        self.export_video_group = QtWidgets.QGroupBox("EXPORT VIDEO")
        self.export_video_group.setCheckable(True)
        self.export_video_group.setFlat(True)
        self.export_video_group.setChecked(False)
        self.export_video_group.toggled.connect(self.update_widget_states)

        self.export_video_content = QtWidgets.QWidget()
        ev_layout = QtWidgets.QHBoxLayout(self.export_video_content)
        ev_layout.setContentsMargins(10, 0, 0, 0)
        self.video_codec_label = QtWidgets.QLabel("VIDEO CODEC")
        self.video_codec_combobox = QtWidgets.QComboBox()
        self.video_codec_combobox.addItems(["AV1 (WEBM)", "H.264 (MP4)", "PRORES (MOV)"])
        self.video_codec_combobox.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Fixed)
        ev_layout.addWidget(self.video_codec_label)
        ev_layout.addWidget(self.video_codec_combobox)
        ev_layout.addStretch()
        ev_group_layout = QtWidgets.QVBoxLayout(self.export_video_group)
        ev_group_layout.setContentsMargins(10, 6, 10, 6)
        ev_group_layout.addWidget(self.export_video_content)

        # Export button
        self.export_button = QtWidgets.QPushButton("EXPORT")
        self.export_button.setObjectName("ExportButton")

    def create_layouts(self):
        self.content_layout = QtWidgets.QVBoxLayout()
        self.content_layout.setContentsMargins(20, 10, 20, 20)
        self.content_layout.setSpacing(15)

        form_layout = QtWidgets.QFormLayout()
        form_layout.setSpacing(10)
        form_layout.setLabelAlignment(QtCore.Qt.AlignLeft)
        form_layout.setFieldGrowthPolicy(QtWidgets.QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        
        form_layout.addRow(self.context_label, self.context_value)
        # Identifier row: line edit + dropdown
        form_layout.addRow(self.identifier_label, self.identifier_combo)

        version_layout = QtWidgets.QHBoxLayout()
        version_layout.addWidget(self.auto_version_checkbox)
        version_layout.addWidget(self.version_label)
        version_layout.addWidget(self.version_spinbox)
        version_layout.addStretch()
        form_layout.addRow(version_layout)

        form_layout.addRow(self.format_label, self.format_combobox)
        form_layout.addRow(self.preview_path_label, self.preview_path_value)

        self.content_layout.addLayout(form_layout)

        # Comment Layout
        self.content_layout.addWidget(self.comment_label)
        self.content_layout.addWidget(self.comment_edit)

        # Export Video as checkable group
        self.content_layout.addWidget(self.export_video_group)

        self.content_layout.addStretch()

        # Export button
        self.content_layout.addWidget(self.export_button)

    def update_widget_states(self):
        """Enable/disable widgets based on checkbox states and update paths."""
        self.version_spinbox.setEnabled(not self.auto_version_checkbox.isChecked())

        # Toggle video settings visibility based on group toggle
        is_enabled = self.export_video_group.isChecked()
        self.export_video_content.setVisible(is_enabled)
        self.video_codec_combobox.setEnabled(is_enabled)

        # Refresh path and identifier list
        try:
            self.generate_playblast_path()
        except Exception:
            pass

        # Avoid resizing/jumping on toggle; size is fixed at show

    def showEvent(self, event):
        super().showEvent(event)
        # Fix window size to accommodate the largest state (export section open)
        prev = self.export_video_group.isChecked()
        # Force open to compute the maximum required size
        self.export_video_group.blockSignals(True)
        self.export_video_group.setChecked(True)
        self.export_video_content.setVisible(True)
        QtWidgets.QApplication.processEvents()
        self.adjustSize()
        # Anchor width; set only minimum height to the largest required so opening sections expands downward
        self.setMinimumHeight(self.size().height())
        # Restore previous checked state without resizing window
        self.export_video_group.setChecked(prev)
        self.export_video_content.setVisible(prev)
        self.export_video_group.blockSignals(False)

    def closeEvent(self, event):
        global dialog_instance
        dialog_instance = None
        super().closeEvent(event)


    def generate_playblast_path(self):
        """Generates and displays the playblast output path based on Prism env vars."""
        try:
            import hou
        except ImportError:
            self.preview_path_value.setText("hou module not found. Cannot generate path.")
            return

        # Fetch environment variables
        prism_job = "$PRISM_JOB"#hou.getenv("PRISMJOB")
        prism_shot = hou.getenv("PRISM_SHOT")
        prism_asset = hou.getenv("PRISM_ASSET")
        prism_sequence = hou.getenv("PRISM_SEQUENCE")
        prism_department = hou.getenv("PRISM_DEPARTMENT") or "dept"
        prism_task = hou.getenv("PRISM_TASK") or "task"

        if not prism_job:
            self.preview_path_value.setText("PRISMJOB environment variable not set.")
            return

        # Construct the path
        base = f"{prism_job}/03_Production"
        etype = "Playblasts"
        
        ctype = "shot" if prism_shot else "asset"
        cshasset = prism_shot or prism_asset
        
        if not cshasset:
            self.preview_path_value.setText("PRISM_SHOT or PRISM_ASSET not set.")
            return

        if ctype == "shot":
            if not prism_sequence:
                self.preview_path_value.setText("PRISM_SEQUENCE not set for shot context.")
                return
            shasset_path = f"Shots/{prism_sequence}/{cshasset}"
        else: # asset
            shasset_path = f"Assets/{cshasset}"

        # Base folder
        playblast_base_path = f"{base}/{shasset_path}/{etype}/"

        # Update context label to show shasset_path
        self.context_value.setText(shasset_path)

        # Populate identifier dropdown from existing folders
        try:
            self.populate_identifiers(base, shasset_path)
        except Exception:
            pass

        # Compose identifier, version string, frame and extension
        identifier = (self.identifier_combo.currentText().strip() or "identifier")
        version_num = int(self.version_spinbox.value())
        version_str = f"v{version_num:04d}"
        frame = "$F4"  # placeholder frame token
        extension = (self.format_combobox.currentText() or "jpg").lower()

        # Filename pattern: department-task_identifier_version.frame.extension
        filename = f"{prism_department}-{prism_task}_{identifier}_{version_str}.{frame}.{extension}"

        full_path = f"{playblast_base_path}{identifier}/{version_str}/{filename}"

        print(full_path)
        self.preview_path_value.setText(full_path)

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

        current_items = [self.identifier_combo.itemText(i) for i in range(self.identifier_combo.count())]
        if items != current_items:
            self.identifier_combo.blockSignals(True)
            self.identifier_combo.clear()
            if items:
                self.identifier_combo.addItems(items)
            self.identifier_combo.blockSignals(False)


    # --- Window Dragging Methods ---
    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self.old_pos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        if self.old_pos is not None:
            delta = event.globalPosition().toPoint() - self.old_pos
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.old_pos = event.globalPosition().toPoint()

    def mouseReleaseEvent(self, event):
        self.old_pos = None


def main(kwargs):
    global dialog_instance
    logger.debug(f"main called with kwargs: {kwargs}")
    action_id = kwargs.get("toolname")
    import hou
    # print(hou.hipFile.path())
    # print(hou.getenv('HIP'))
    # print(hou.getenv('PRISMJOB'))
    # print(hou.getenv('PRISM_SHOT'))
    # print(hou.getenv('PRISM_SEQUENCE'))
    # print(hou.getenv('DRIVER'))
    # print(hou.text.expandString("$HIP"))
    # print(hou.hscript("echo $HIP"))
    
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
    elif action_id == "Debug":
        logger.info("Debug action triggered")
    elif action_id == "Reload":
        logger.info("prism_mplay module reloaded.")
    else:
        logger.warning(f"Unknown action: {action_id}")

