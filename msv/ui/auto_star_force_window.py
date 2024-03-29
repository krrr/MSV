import threading
import multiprocessing as mp
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from msv.ui import fix_sizes_for_high_dpi
from msv.tools import tool_macro_process
from msv.tools.auto_star_force import AutoStarForce


class AutoStarForceWindow(QWidget):
    macroProcSignal = pyqtSignal(object)

    def __init__(self, parent=None):
        super().__init__(parent, Qt.Window | Qt.WindowTitleHint | Qt.WindowCloseButtonHint)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setFixedSize(300, 130)

        self.macroProcSignal.connect(self._onMacroProcMessage)
        self.setWindowTitle("Auto Star Force")
        self.running = False
        self.macro_process = None
        self.macro_proc_conn = None

        mainLayout = QVBoxLayout(self)
        mainLayout.setContentsMargins(0, 0, 0, 4)
        mainLayout.setSpacing(4)
        self.setLayout(mainLayout)

        frame = QFrame(self)
        frame.setLineWidth(1)
        frame.setFrameStyle(QFrame.StyledPanel | QFrame.Plain)
        mainLayout.addWidget(frame)
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)
        frame.setLayout(layout)

        helpLabel = QLabel(frame)
        helpLabel.setText("Open enhance window (leave it at initial position)\n and set equipment first.")
        helpLabel.setMinimumHeight(28)
        layout.addWidget(helpLabel)
        spacer = QWidget(frame)
        spacer.setFixedHeight(6)
        layout.addWidget(spacer)

        optFrame1 = QWidget(frame)
        layout.addWidget(optFrame1)
        layout1 = QHBoxLayout(optFrame1)
        layout1.setAlignment(Qt.AlignHCenter)
        layout1.setContentsMargins(20, 0, 20, 0)
        optFrame1.setLayout(layout1)
        label = QLabel(optFrame1)
        label.setText('Target Star:')
        layout1.addWidget(label)
        self.targetStarInput = QLineEdit(optFrame1)
        self.targetStarInput.setValidator(QIntValidator(1, 25, self))
        layout1.addWidget(self.targetStarInput)

        optFrame2 = QWidget(frame)
        layout.addWidget(optFrame2)
        layout2 = QHBoxLayout(optFrame2)
        layout2.setAlignment(Qt.AlignHCenter)
        layout2.setContentsMargins(0, 0, 0, 0)
        optFrame2.setLayout(layout2)
        self.starCatchCheckbox = QCheckBox(optFrame2)
        self.starCatchCheckbox.setText('Star Catch')
        layout2.addWidget(self.starCatchCheckbox)
        self.safeGuardCheckbox = QCheckBox(optFrame2)
        self.safeGuardCheckbox.setText('Safe Guard')
        layout2.addWidget(self.safeGuardCheckbox)

        actionBtnFrame = QWidget(self)
        mainLayout.addWidget(actionBtnFrame)
        layout3 = QHBoxLayout(actionBtnFrame)
        layout3.setAlignment(Qt.AlignHCenter)
        layout3.setContentsMargins(0, 0, 0, 0)
        actionBtnFrame.setLayout(layout3)
        self.toggleBtn = QPushButton(actionBtnFrame)
        layout3.addWidget(self.toggleBtn)
        self.toggleBtn.setText('Enhance')
        self.toggleBtn.setMinimumWidth(100)
        self.toggleBtn.clicked.connect(self.toggle_macro)

        fix_sizes_for_high_dpi(self)

    def toggle_macro(self):
        if self.running:
            self.macro_proc_conn.send(('stop',))
            self._set_macro_status(False)
        else:
            if not self.targetStarInput.hasAcceptableInput():
                QMessageBox.critical(self, 'Error', 'target star not valid')
                return
            target_star = int(self.targetStarInput.text())

            parent_conn, child_conn = mp.Pipe()
            self.macro_proc_conn = parent_conn
            tool_args = (target_star, self.starCatchCheckbox.isChecked(), self.safeGuardCheckbox.isChecked())
            self.macro_process = mp.Process(target=tool_macro_process, args=(child_conn, AutoStarForce, tool_args), daemon=True)
            self.macro_process.start()
            threading.Thread(target=self._macroOutQToSignal, args=(parent_conn,), daemon=True).start()
            self._set_macro_status(True)

    def _macroOutQToSignal(self, conn):
        """Read from macro process out queue from separate thread, and notify main thread
        using signal"""
        while True:
            try:
                self.macroProcSignal.emit(conn.recv())  # recv() is blocking
            except EOFError:  # closed
                return

    @pyqtSlot(object)
    def _onMacroProcMessage(self, ev):
        if ev[0] == "log":
            self.parent().log(ev[1])
        elif ev[0] == "stopped":
            self._set_macro_status(False)
            self.parent().log('enhancing stopped')
        elif ev[0] == "exception":
            self._set_macro_status(False)
            self.macro_process = None
            self.parent().log(str(ev[1]))

    def _set_macro_status(self, running):
        self.running = running
        self.toggleBtn.setText("Stop" if running else "Enhance")

    def closeEvent(self, ev):
        super().closeEvent(ev)
