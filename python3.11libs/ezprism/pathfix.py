import hou
from pathlib import Path
from hutil.Qt import QtWidgets, QtCore, QtGui
from hutil.Qt.QtCore import Qt
from pprint import pprint
from typing import Any, Iterable, List, Optional, Sequence, Union


class RuleModel(QtCore.QAbstractTableModel):
    column_labels = ("Name", "Parm Value")

    NameColumn = 0
    PatternColumn = 1
    ExtensionColumn = 2
    RegexColumn = 3
    SpaceColumn = 4

    ItemRole = Qt.UserRole + 1

    def __init__(self, config: None, parent: QtCore.QObject = None):
        super().__init__(parent)
        self._config = config
        # self._rules: OCIO.FileRules = config.getFileRules()
        self._dragicon = QtGui.QPixmap()

    def config(self):
        return self._config

    def setConfig(self, config: None):
        self.beginResetModel()
        # self._config: OCIO.Config = config
        # self._rules = config.getFileRules()
        self.endResetModel()
    
    def rowCount(self, parent: QtCore.QModelIndex = None) -> int:
        return self._rules.getNumEntries()

    def columnCount(self, parent: QtCore.QModelIndex = None) -> int:
        return len(self.column_labels)

    def headerData(self, section: int, orientation: Qt.Orientation,
                   role: int = Qt.DisplayRole) -> Any:
        if orientation == Qt.Horizontal:
            if role == Qt.DisplayRole:
                return self.column_labels[section]
            elif role == Qt.SizeHintRole:
                return QtCore.QSize(-1, HEADER_HEIGHT)

    def flags(self, index: QtCore.QModelIndex) -> Qt.ItemFlags:
        if index.isValid():
            row = index.row()
            column = index.column()
            rules = self._rules
            flags = Qt.ItemIsEnabled | Qt.ItemIsSelectable
            # Default item is not draggable
            if not self.isDefaultRule(index):
                flags |= Qt.ItemIsDragEnabled
            # Name field is not editable
            if index.column() != self.NameColumn:
                is_default = rules.getName(row) == "Default"
                # For the default rule, the only thing you can edit is the space
                if not is_default or column == self.SpaceColumn:
                    flags |= Qt.ItemIsEditable
        else:
            flags = Qt.ItemIsDropEnabled
        return flags

    def data(self, index: QtCore.QModelIndex, role: int = Qt.DisplayRole
             ) -> Any:
        if not (index and index.isValid()):
            return
        rules = self._rules
        row = index.row()
        column = index.column()

        if role in (Qt.DisplayRole, Qt.EditRole):
            if column == self.NameColumn:
                return rules.getName(row)
            elif column == self.ExtensionColumn:
                return rules.getExtension(row)
            elif column == self.PatternColumn:
                return rules.getPattern(row)
            elif column == self.RegexColumn:
                return rules.getRegex(row)
            elif column == self.SpaceColumn:
                return rules.getColorSpace(row)
        elif column == self.NameColumn and role == Qt.DecorationRole:
            # Don't show a drag indicator on the default rule
            if self.isDefaultRule(index):
                return BLANK_ICON
            else:
                return self._dragicon
        elif role == Qt.FontRole:
            font = QtGui.QFont()
            if column in (self.PatternColumn, self.ExtensionColumn,
                          self.SpaceColumn):
                font.setFamily(MONOSPACE_FONT_FAMILY)
                return font
            elif self.isDefaultRule(index):
                font.setItalic(True)
                return font
        elif role == Qt.SizeHintRole:
            return QtCore.QSize(-1, ROW_HEIGHT)

    def setData(self, index: QtCore.QModelIndex, value: Any,
                role: int = Qt.EditRole) -> bool:
        edited = False
        if not (index and index.isValid()):
            return edited
        rules = self._rules
        row = index.row()
        column = index.column()

        if role in (Qt.DisplayRole, Qt.EditRole):
            if column == self.PatternColumn:
                if value and value != rules.getPattern(row):
                    rules.setPattern(row, value)
                    edited = True
            elif column == self.ExtensionColumn:
                if value and value != rules.getExtension(row):
                    rules.setExtension(row, value)
                    edited = True
            elif column == self.RegexColumn:
                if value and value != rules.getRegex(row):
                    rules.setRegex(row, value)
                    edited = True
            elif column == self.SpaceColumn:
                if value and value != rules.getColorSpace(row):
                    rules.setColorSpace(row, value)
                    edited = True

        if edited:
            start = self.index(row, 0)
            end = self.index(row, len(self.column_labels))
            self.dataChanged.emit(start, end)
        return edited

    def isDefaultRule(self, index: QtCore.QModelIndex) -> bool:
        if index and index.isValid():
            return self._rules.getName(index.row()) == "Default"
        else:
            return False

    def insertRule(self, index: int, name: str, space: str, pattern: str = "",
                   ext: str = "", regex: str = ""):
        rules = self._rules
        if regex:
            rules.insertRule(index, name, space, regex)
        else:
            rules.insertRule(index, name, space, pattern, ext)
        self.insertRow(index)

    def removeRow(self, row: int, parent: QtCore.QModelIndex = None):
        parent = parent or QtCore.QModelIndex()
        rules = self._rules
        if row < 0 or row >= self.rowCount():
            return

        self.beginRemoveRows(parent, row, row)
        # Raises an exception if you try to remove the default rule
        rules.removeRule(row)
        self.endRemoveRows()



class FileTable(QtWidgets.QTableWidget):
    def __init__(self, *args, **kwargs):
        super(FileTable, self).__init__(*args, **kwargs)
        self.setColumnCount(4)
        self.setHorizontalHeaderLabels(["Select", "Parameter", "Filepath", "Filesize"])

    def add_row(self, parameter, filepath, checkbox, filesize):
        row_position = self.rowCount()
        self.insertRow(row_position)
        checkbox_item = QtWidgets.QTableWidgetItem()
        checkbox_item.setCheckState(QtCore.Qt.Checked if checkbox else QtCore.Qt.Unchecked)
        self.setItem(row_position, 0, checkbox_item)
        
        self.setItem(row_position, 1, QtWidgets.QTableWidgetItem(parameter))
        self.setItem(row_position, 2, QtWidgets.QTableWidgetItem(filepath))
        self.setItem(row_position, 3, QtWidgets.QTableWidgetItem(filesize))

class MainWindow(QtWidgets.QDialog):
    def __init__(self, parent: QtWidgets.QWidget = None):
        # parent = parent or hou.qt.mainWindow()
        super(MainWindow, self).__init__(parent)

        # Basic window setup
        self.setWindowTitle("Path Fixing")
        self.setMinimumSize(600,80)
        self.setWindowFlags(self.windowFlags() ^ QtCore.Qt.WindowContextHelpButtonHint) # removes help button
        # self.table = FileTable()        
        # Element creation        
        self.buildUI()

    def buildUI(self):
        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)
        
        self.table = FileTable()
        layout.addWidget(self.table)
        self.table.resizeColumnsToContents() # squeeze columns fit?
        table_width = self.table.sizeHint().width()
        # self.resize(table_width, self.height())
        self.table.add_row("parm","C:/myfileapth", True, "4kb")
            


def create_interface(parent: None):
    # app = QtWidgets.QApplication([])
    main = MainWindow(parent)
    main.show()
    # app.exec_()

def test():
    refs = hou.fileReferences()
    # returns seq of tuple of [parm, string]
    
    # filter refs 
    pprint(refs)
    print("\n filtering refs \n")
    refs = [x for x in refs if isValidRef(x)]
    pprint(refs)
    

def isValidRef(houFileReference) -> bool:
    # check if parm is ok, then return true
    parm = houFileReference[0]
    path = houFileReference[1]    
    posix_path = Path(path).as_posix()
    # print("posix path: ", posix_path)

    if parm == None:        
        return False  

    if parm.path().startswith("/tasks/topnet1"):
        return False

    if parm.node().isInsideLockedHDA():
        if not parm.node().isEditableInsideLockedHDA():
            return False
    
    to_match = [":/", "$", ":\\"]
    # if (":/" in path[0:3]) or "$" in path[0:3]:
    if not any(item in posix_path[0:3] for item in to_match):
        print("found match for:", path)
        
    return True
    

def fromShelf():
    create_interface(parent=hou.qt.mainWindow())

def main():
    create_interface(parent=None)
    test()

if __name__ == "__main__":
    print("hello im running?")
    main()    
