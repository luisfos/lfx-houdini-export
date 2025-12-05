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

# To parent to Houdini's main window
try:
    import hou
    def get_main_window():
        try:
            return hou.qt.mainWindow()
        except AttributeError:
            # hou.qt is not available in this context (e.g. mplay), create a standalone app.
            if QtWidgets.QApplication.instance() is None:
                # This line is crucial for running a standalone PySide app
                QtWidgets.QApplication(sys.argv)
            return None
except ImportError:
    def get_main_window():
        # If not in Houdini, create a standalone app for testing
        if QtWidgets.QApplication.instance() is None:
            QtWidgets.QApplication(sys.argv)
        return None

class SaveInterface(QtWidgets.QDialog):
    def __init__(self, parent=get_main_window()):
        super(SaveInterface, self).__init__(parent)
        self.setWindowTitle("Save Interface")
        self.setMinimumWidth(400)

        self.create_widgets()
        self.create_layouts()

    def create_widgets(self):
        # General section
        self.general_label = QtWidgets.QLabel("General")
        font = self.general_label.font()
        font.setBold(True)
        self.general_label.setFont(font)

        self.context_label = QtWidgets.QLabel("context:")
        self.context_value = QtWidgets.QLabel("Asset - Tophe")

        self.identifier_label = QtWidgets.QLabel("Identifier:")
        self.identifier_edit = QtWidgets.QLineEdit("my_identifier")
        self.change_button = QtWidgets.QPushButton("Change")

        self.auto_version_checkbox = QtWidgets.QCheckBox("Auto Version")
        self.auto_version_checkbox.setChecked(True)
        self.version_label = QtWidgets.QLabel("Version:")
        self.version_spinbox = QtWidgets.QSpinBox()
        self.version_spinbox.setValue(1)
        self.version_spinbox.setMinimum(1)


        self.format_label = QtWidgets.QLabel("Format:")
        self.format_combobox = QtWidgets.QComboBox()
        self.format_combobox.addItems(["jpg", "png", "exr", "tif"])
        self.format_combobox.setCurrentText("jpg")

        self.preview_path_label = QtWidgets.QLabel("Preview Path:")
        self.preview_path_value = QtWidgets.QLabel("...v0001/my_identifier_v0001.$F4jpg")
        self.preview_path_value.setWordWrap(True)

        # Comment section
        self.comment_checkbox = QtWidgets.QCheckBox("Comment")
        self.comment_checkbox.setChecked(True)
        self.comment_edit = QtWidgets.QTextEdit("my comment")
        self.comment_edit.setFixedHeight(80)

        # Export Video section
        self.export_video_checkbox = QtWidgets.QCheckBox("Export Video")
        self.export_video_checkbox.setChecked(True)

        self.video_codec_label = QtWidgets.QLabel("Video Codec:")
        self.video_codec_combobox = QtWidgets.QComboBox()
        self.video_codec_combobox.addItems(["AV1 (webm)", "H.264 (mp4)", "ProRes (mov)"])

        # Export button
        self.export_button = QtWidgets.QPushButton("Export")

    def create_layouts(self):
        main_layout = QtWidgets.QVBoxLayout(self)

        # General Layout
        main_layout.addWidget(self.general_label)
        
        line1 = QtWidgets.QFrame()
        line1.setFrameShape(QtWidgets.QFrame.HLine)
        line1.setFrameShadow(QtWidgets.QFrame.Sunken)
        main_layout.addWidget(line1)

        form_layout = QtWidgets.QFormLayout()
        form_layout.setSpacing(10)
        form_layout.setContentsMargins(10, 10, 10, 10)
        
        form_layout.addRow(self.context_label, self.context_value)

        identifier_layout = QtWidgets.QHBoxLayout()
        identifier_layout.addWidget(self.identifier_edit)
        identifier_layout.addWidget(self.change_button)
        form_layout.addRow(self.identifier_label, identifier_layout)

        version_layout = QtWidgets.QHBoxLayout()
        version_layout.addWidget(self.auto_version_checkbox)
        version_layout.addStretch()
        version_layout.addWidget(self.version_label)
        version_layout.addWidget(self.version_spinbox)
        form_layout.addRow(version_layout)

        form_layout.addRow(self.format_label, self.format_combobox)
        form_layout.addRow(self.preview_path_label, self.preview_path_value)

        main_layout.addLayout(form_layout)

        # Comment Layout
        main_layout.addWidget(self.comment_checkbox)
        main_layout.addWidget(self.comment_edit)

        # Export Video Layout
        main_layout.addWidget(self.export_video_checkbox)
        
        video_codec_layout = QtWidgets.QHBoxLayout()
        video_codec_layout.addWidget(self.video_codec_label)
        video_codec_layout.addWidget(self.video_codec_combobox)
        video_codec_layout.addStretch()
        main_layout.addLayout(video_codec_layout)

        main_layout.addStretch()

        # Export button
        main_layout.addWidget(self.export_button)


def main(kwargs):
    global dialog_instance
    # This function is called by the menu items in MainMenuMPlay.xml
    logger.debug(f"main called with kwargs: {kwargs}")
    action_id = kwargs.get("toolname")

    # We can have logic here to decide what to do based on the action_id
    # For now, we just show the same save interface for "Save..."
    
    if action_id == "Save...":
        logger.info("'Save...' action triggered.")
        # Check if an instance already exists to avoid multiple windows
        if dialog_instance:
            logger.debug("Found existing dialog instance. Raising and activating.")
            dialog_instance.raise_()
            dialog_instance.activateWindow()
            return

        logger.debug("Creating new SaveInterface dialog.")
        dialog_instance = SaveInterface()
        dialog_instance.show()
        logger.debug("SaveInterface dialog shown.")

    elif action_id == "Quicksave":
        logger.info("Quicksave action triggered")
        # Here you would implement the quicksave logic without showing a UI
    elif action_id == "Debug":
        logger.info("Debug action triggered")
        # Here you can put debug specific code
    elif action_id == "Reload":
        logger.info("prism_mplay module reloaded.")
    else:
        logger.warning(f"Unknown action: {action_id}")

