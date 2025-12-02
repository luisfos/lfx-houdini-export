import os
import logging

from qtpy.QtCore import *
from qtpy.QtGui import *
from qtpy.QtWidgets import *

from PrismUtils.Decorators import err_catcher as err_catcher

import hou

logger = logging.getLogger(__name__)

class EntityDlg(QDialog):

    entitySelected = Signal(object)

    def __init__(self, origin, parent=None):
        super(EntityDlg, self).__init__()
        self.origin = origin
        self.parentDlg = parent
        self.plugin = self.origin.plugin
        self.core = self.plugin.core
        self.setupUi()

    @err_catcher(name=__name__)
    def setupUi(self):
        title = "Select entity"

        self.setWindowTitle(title)
        self.core.parentWindow(self, parent=self.parentDlg)

        import EntityWidget
        self.w_entities = EntityWidget.EntityWidget(core=self.core, refresh=True)
        self.w_entities.editEntitiesOnDclick = False
        self.w_entities.getPage("Assets").tw_tree.itemDoubleClicked.connect(self.itemDoubleClicked)
        self.w_entities.getPage("Shots").tw_tree.itemDoubleClicked.connect(self.itemDoubleClicked)
        self.w_entities.getPage("Assets").setSearchVisible(False)
        self.w_entities.getPage("Shots").setSearchVisible(False)

        self.lo_main = QVBoxLayout()
        self.setLayout(self.lo_main)

        self.bb_main = QDialogButtonBox()
        self.bb_main.addButton("Select", QDialogButtonBox.AcceptRole)
        self.bb_main.addButton("Close", QDialogButtonBox.RejectRole)

        self.bb_main.clicked.connect(self.buttonClicked)

        self.lo_main.addWidget(self.w_entities)
        self.lo_main.addWidget(self.bb_main)

    @err_catcher(name=__name__)
    def itemDoubleClicked(self, item, column):
        self.buttonClicked("select")

    @err_catcher(name=__name__)
    def buttonClicked(self, button):
        if button == "select" or button.text() == "Select":
            entities = self.w_entities.getCurrentData()
            if isinstance(entities, dict):
                entities = [entities]

            validEntities = []
            for entity in entities:
                if entity.get("type", "") not in ["asset", "shot"]:
                    continue

                validEntities.append(entity)

            if not validEntities:
                msg = "Invalid entity selected."
                self.core.popup(msg, parent=self)
                return

            self.entitySelected.emit(validEntities[0])

        self.close()

    @err_catcher(name=__name__)
    def sizeHint(self):
        return QSize(400, 400)