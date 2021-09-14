from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from msv.ui import fix_sizes_for_high_dpi
from msv.ui.key_bind_window_ui import Ui_KeyBindWindow
from msv.util import get_config
from msv import directinput_constants
from msv.input_manager import DEFAULT_KEY_MAP, KEY2DISPLAY_NAME, load_keymap


class KeyListener(QObject):
    def __init__(self, parent, callback):
        super().__init__(parent)
        self.callback = callback

    def eventFilter(self, obj, event):
        if event.type() == QEvent.KeyPress:
            scanCode = event.nativeScanCode()
            if scanCode & 0x100:  # is extended key
                scanCode = (scanCode & 0xFF) + 0x80  # why this works?
            ret = self.callback(scanCode)
            if ret:
                obj.removeEventFilter(self)
            return True
        else:
            return super().eventFilter(obj, event)


class KeyBindWindow(QDialog, Ui_KeyBindWindow):
    PLEASE_INPUT_TXT = 'Please input...'

    def __init__(self, parent):
        super().__init__(parent, Qt.WindowTitleHint | Qt.WindowCloseButtonHint)
        self.setupUi(self)
        fix_sizes_for_high_dpi(self)

        self.keymap = load_keymap()
        self.keyname2widget = {}

        icoSize = QSize(32, 32) * self.logicalDpiX() / 96
        idx = 0
        for keyName, displayName in KEY2DISPLAY_NAME.items():
            container = QFrame(self.keyListWidget)
            container.setFixedHeight(40)
            layout = QHBoxLayout(container)
            layout.setSpacing(4)
            layout.setContentsMargins(3, 3, 3, 3)
            # skill icon
            icoLabel = QLabel(container)
            pixmap = QPixmap(':/skill_icon/' + keyName + '.png')
            if not pixmap.isNull():
                pixmap = pixmap.scaled(icoSize.width(), icoSize.height(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            icoLabel.setPixmap(pixmap)
            icoLabel.setContentsMargins(0, 0, 0, 0)
            icoLabel.setFixedSize(32, 32)
            layout.addWidget(icoLabel)
            # skill text
            layout.addWidget(QLabel(displayName, container))
            # set button
            btn = QPushButton(self.keyListWidget)
            btn.setMaximumWidth(125)
            layout.addWidget(btn)
            self.keyListLayout.addWidget(container)
            fix_sizes_for_high_dpi(container)  # don't affect spacer's height
            saved = self.keymap.get(keyName)
            if saved is not None:
                btn.setText(directinput_constants.DIK2NAME.get(saved, '-ERROR-'))

            btn.setProperty('keyName', keyName)
            btn.clicked.connect(self._onSetKeyBtnClicked)

            # add spacer
            if idx < len(DEFAULT_KEY_MAP) - 1:
                line = QFrame(self.keyListWidget)
                line.setFixedHeight(1 if self.logicalDpiX() < 192 else 2)
                line.setStyleSheet('background: rgb(185, 185, 185)')
                self.keyListLayout.addWidget(line)
            idx += 1

    def keyPressEvent(self, event):
        if event.key() != Qt.Key_Escape:  # prevent ESC close
            super().keyPressEvent(event)

    def accept(self):
        super().accept()
        get_config()['keymap'] = self.keymap

    def _setKey(self, scanCode, btn):
        keyName = btn.property('keyName')
        if scanCode == directinput_constants.DIK_ESCAPE:  # unbind this key
            self.keymap[keyName] = None
            btn.setText('')
            return True
        elif scanCode in directinput_constants.DIK2NAME:
            self.keymap[keyName] = scanCode
            btn.setText(directinput_constants.DIK2NAME[scanCode])
            return True
        else:
            QMessageBox.critical(self, "Key Settings", "Unsupported key. Scan code: " + hex(scanCode))
            return False

    def _onSetKeyBtnClicked(self):
        btn = self.sender()
        if btn.text() != self.PLEASE_INPUT_TXT:
            btn.setText(self.PLEASE_INPUT_TXT)
            btn.installEventFilter(KeyListener(self, lambda k: self._setKey(k, btn)))

    @pyqtSlot()
    def on_resetBtn_clicked(self):
        get_config()['keymap'] = DEFAULT_KEY_MAP.copy()
        QMessageBox.information(self, 'Key Settings', 'Default settings restored')
        self.close()

