from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QFrame, QCheckBox
from os.path import join
from ...icons import icons_dir

path_delete = join(icons_dir,'delete.png')
path_new = join(icons_dir,'new.png')
path_add_off = join(icons_dir,'add_off.png')
path_add_on = join(icons_dir,'add_on.png')
path_edit_off = join(icons_dir,'edit_off.png')
path_edit_on = join(icons_dir,'edit_on.png')

class QtLayerButtons(QFrame):
    def __init__(self, layers):
        super().__init__()

        self.layers = layers
        self.editCheckBox = QtEditCheckBox(self.layers)
        self.additionCheckBox = QtAdditionCheckBox(self.layers)
        self.deleteButton = QtDeleteButton(self.layers)
        self.newLayerButton = QtNewLayerButton(self.layers)

        layout = QHBoxLayout()
        layout.addWidget(self.editCheckBox)
        layout.addWidget(self.additionCheckBox)
        layout.addStretch(0)
        layout.addWidget(self.newLayerButton)
        layout.addWidget(self.deleteButton)
        self.setLayout(layout)

class QtDeleteButton(QPushButton):
    def __init__(self, layers):
        super().__init__()

        self.layers = layers
        self.setIcon(QIcon(path_delete))
        self.setFixedWidth(28)
        self.setFixedHeight(28)
        self.setToolTip('Delete layers')
        self.setAcceptDrops(True)
        styleSheet = """QPushButton {background-color:lightGray; border-radius: 3px;}
            QPushButton:pressed {background-color:rgb(0, 153, 255); border-radius: 3px;}
            QPushButton:hover {background-color:rgb(0, 153, 255); border-radius: 3px;}"""
        self.setStyleSheet(styleSheet)
        self.clicked.connect(self.layers.remove_selected)

    def dragEnterEvent(self, event):
        event.accept()
        self.hover = True
        self.update()

    def dragLeaveEvent(self, event):
        event.ignore()
        self.hover = False
        self.update()

    def dropEvent(self, event):
        event.setDropAction(Qt.CopyAction)
        event.accept()

class QtNewLayerButton(QPushButton):
    def __init__(self, layers):
        super().__init__()

        self.layers = layers
        self.setIcon(QIcon(path_new))
        self.setFixedWidth(28)
        self.setFixedHeight(28)
        self.setToolTip('Add layer')
        styleSheet = """QPushButton {background-color:lightGray; border-radius: 3px;}
            QPushButton:pressed {background-color:rgb(0, 153, 255); border-radius: 3px;}
            QPushButton:hover {background-color:rgb(0, 153, 255); border-radius: 3px;}"""
        self.setStyleSheet(styleSheet)
        self.clicked.connect(self.layers.viewer._new_markers)

class QtEditCheckBox(QCheckBox):
    def __init__(self, layers):
        super().__init__()

        self.layers = layers
        self.setToolTip('Edit mode')
        self.setChecked(False)
        styleSheet = """QCheckBox {background-color:lightGray; border-radius: 3px;}
                        QCheckBox::indicator {subcontrol-position: center center; subcontrol-origin: content;
                            width: 28px; height: 28px;}
                        QCheckBox::indicator:checked {background-color:rgb(0, 153, 255); border-radius: 3px;
                            image: url(""" + path_edit_off + """);}
                        QCheckBox::indicator:unchecked {image: url(""" + path_edit_off + """);}
                        QCheckBox::indicator:unchecked:hover {image: url(""" + path_edit_on + ");}"
        self.setStyleSheet(styleSheet)
        self.stateChanged.connect(lambda state=self: self._set_mode(state))
        self.layers.viewer.events.mode.connect(self._set_button)

    def _set_mode(self, bool):
        if bool:
            self.layers.viewer._set_mode('edit')
        else:
            self.layers.viewer._set_mode(None)

    def _set_button(self, event):
        with self.layers.viewer.events.blocker(self._set_button):
            if self.layers.viewer.mode == 'edit':
                self.setChecked(True)
            else:
                self.setChecked(False)


class QtAdditionCheckBox(QCheckBox):
    def __init__(self, layers):
        super().__init__()

        self.layers = layers
        self.setToolTip('Addition mode')
        self.setChecked(False)
        styleSheet = """QCheckBox {background-color:lightGray; border-radius: 3px;}
                        QCheckBox::indicator {subcontrol-position: center center; subcontrol-origin: content;
                            width: 28px; height: 28px;}
                        QCheckBox::indicator:checked {background-color:rgb(0, 153, 255); border-radius: 3px;
                            image: url(""" + path_add_off + """);}
                        QCheckBox::indicator:unchecked {image: url(""" + path_add_off + """);}
                        QCheckBox::indicator:unchecked:hover {image: url(""" + path_add_on + ");}"
        self.setStyleSheet(styleSheet)
        self.stateChanged.connect(lambda state=self: self._set_mode(state))
        self.layers.viewer.events.mode.connect(self._set_button)

    def _set_mode(self, bool):
        if bool:
            self.layers.viewer._set_mode('add')
        else:
            self.layers.viewer._set_mode(None)

    def _set_button(self, event):
        with self.layers.viewer.events.blocker(self._set_button):
            if self.layers.viewer.mode == 'add':
                self.setChecked(True)
            else:
                self.setChecked(False)
