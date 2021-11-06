import multiprocessing
import time
import os
import signal
import base64
import win32con
import threading
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtMultimedia import *
from msv import driver, mapscripts, winapi, APP_TITLE, util, __version__
from msv.ui import fix_sizes_for_high_dpi
from msv.ui.main_window_ui import Ui_MainWindow
from msv.util import get_config, save_config, is_compiled, GlobalHotKeyListener
from msv.macro_script import macro_process_main
from msv.ui.key_bind_window import KeyBindWindow
from msv.ui.auto_star_force_window import AutoStarForceWindow
from msv.ui.terrain_editor import TerrainEditorWindow
from msv.screen_processor import ScreenProcessor, MapleWindowNotFoundError


ABOUT_TXT = '''\
Version: %s
Author: Dashadower, krrr
Source code: https://github.com/krrr/MSV

ABSOLUTELY NO WARRANTY OF ANY KIND
'''


class MainWindow(QMainWindow, Ui_MainWindow):
    ALERT_SOUND_CD = 2
    macroProcSignal = pyqtSignal(object)

    def __init__(self, app_title=None, limit=False):
        super().__init__(None, Qt.CustomizeWindowHint | Qt.WindowMinimizeButtonHint | Qt.WindowCloseButtonHint)  # disable maximize button
        self.setupUi(self)
        fix_sizes_for_high_dpi(self)
        self.actionAutoSolveRune.setChecked(get_config().get('auto_solve_rune', True))
        self.actionAutoSolveRune.triggered.connect(lambda x: self._onOptChange('auto_solve_rune', x))
        self.actionVacuumPetPicking.setChecked(get_config().get('vacuum_pet_picking', False))
        self.actionVacuumPetPicking.triggered.connect(lambda x: self._onOptChange('vacuum_pet_picking', x))
        self.actionKernelDriver.setChecked(get_config().get('kernel_driver', False))
        self.actionKernelDriver.triggered.connect(lambda x: self._onOptChange('kernel_driver', x))
        self.actionDebugMode.setChecked(get_config().get('debug', False))
        self.actionDebugMode.triggered.connect(lambda x: self._onOptChange('debug', x))
        self.macroProcSignal.connect(self._onMacroProcMessage)

        self.app_title = (app_title or APP_TITLE) + ' Hero'
        self.setWindowTitle(self.app_title)

        self.keymap = None
        self.macro_running = False
        self.macro_process = None
        self.platform_file_path = None
        self.macro_proc_conn = None

        self.logTextArea.document().setDefaultStyleSheet('.time-part { color: #808080 }')
        self.log(self.app_title + " hero version: v" + __version__)
        current_user = util.runtime_info.get('username')
        if current_user:
            msg = 'Account: ' + current_user
            due = util.runtime_info.get('due')
            if due:
                msg += ', Expire: ' + due.strftime("%Y-%m-%d %H:%M")
            self.log(msg)
        self.log('\n')

        self.preset_names = tuple(mapscripts.map_scripts.keys())
        self.presetComboBox.addItems(self.preset_names)
        self.presetComboBox.setCurrentIndex(-1)

        saved_preset = get_config().get('preset')
        if saved_preset:
            try:
                self.presetComboBox.setCurrentIndex(self.preset_names.index(saved_preset))
            except ValueError:
                pass
            self._loadPresetPlatform(saved_preset)
        else:
            saved_platform_file = get_config().get('platform_file')
            if saved_platform_file and os.path.isfile(saved_platform_file):
                self._setPlatformFile(saved_platform_file)

        self.presetComboBox.insertSeparator(7)  # insert will change index
        self.presetComboBox.insertSeparator(17)

        # setup sounds
        self.beepUpSound = QSoundEffect(self)
        self.beepUpSound.setSource(QUrl("qrc:/sound/beep_up.wav"))
        self.beepDownSound = QSoundEffect(self)
        self.beepDownSound.setSource(QUrl("qrc:/sound/beep_down.wav"))
        self.beepSound = QSoundEffect(self)
        self.beepSound.setSource(QUrl("qrc:/sound/beep.wav"))
        self.beepSoundRemains = 0
        self.last_alert_sound = 0
        self.whiteRoomSound = QMediaPlayer(self)
        self.whiteRoomSound.setMedia(QMediaContent(QUrl("qrc:/sound/white_room.mp3")))

        self.hotkeyListener = GlobalHotKeyListener([
            GlobalHotKeyListener.HotKey(1, 0, win32con.VK_F1, lambda: self.stop_macro() if self.macro_running else self.start_macro()),
            GlobalHotKeyListener.HotKey(2, 0, win32con.VK_F2, lambda: self.toggle_macro_process())
        ])
        qApp.installNativeEventFilter(self.hotkeyListener)

        QTimer.singleShot(100, self.toggle_macro_process)

        if get_config().get('kernel_driver'):
            try:
                driver.load_driver()
                self.log('Kernel driver loaded')
            except Exception as e:
                QMessageBox.critical(self, self.app_title, 'Driver failed to load:\n' + str(e))

        self.limit = limit
        if limit:
            self.actionKernelDriver.setVisible(False)

    def closeEvent(self, event):
        # lambda may cause leak
        self.actionAutoSolveRune.triggered.disconnect()
        # self.actionKernelDriver.triggered.disconnect()
        self.actionDebugMode.triggered.disconnect()

        if self.macro_process:
            try:
                self.macro_proc_conn.send(("stop",))
                os.kill(self.macro_process.pid, signal.SIGTERM)
            except Exception:
                pass

        get_config()['geometry'] = base64.b64encode(bytes(self.saveGeometry())).decode('ascii')
        save_config()

        self.hotkeyListener.unregister()

        super().closeEvent(event)

    def start_macro(self):
        if not winapi.IsUserAnAdmin():
            QMessageBox.critical(self, self.app_title, 'Please run as administrator')
            return

        if not self.macro_process:
            self.toggle_macro_process()
        # if 'keymap' not in get_config():
        #     QMessageBox.critical(self, self.app_title, "Skill keys not set")
        #     return

        if not self.platform_file_path and self.presetComboBox.currentIndex() == -1:
            QMessageBox.critical(self, self.app_title, "Please select a terrain file")
            return

        cap = ScreenProcessor()
        if not cap.get_game_hwnd():
            QMessageBox.critical(self, self.app_title, "MapleStory window not found")
            return

        rect = cap.ms_get_screen_rect()
        if get_config().get('debug'):
            self.log("Game Window Rect: "+ str(rect))
        if rect is None:
            QMessageBox.critical(self, self.app_title, "Failed to get Maple Window location.\nMove MapleStory window so "
                                                 "that the top left corner of the window is within the screen.")
            return

        self.beepUpSound.play()
        cap.set_foreground()
        self.macro_proc_conn.send(("start", get_config(), self.platform_file_path, self.presetComboBox.currentText()))
        self._set_macro_status(True)

    def stop_macro(self):
        self.beepDownSound.play()
        self.macro_proc_conn.send(("stop",))
        self.log("Stopping.")
        self._set_macro_status(False)

    def _set_macro_status(self, running):
        self.macro_running = running
        self.macroToggleBtn.setText("Stop Macro" if running else "Start Macro")
        self.openTerrainBtn.setDisabled(running)
        self.presetComboBox.setDisabled(running)

    def log(self, txt):
        self.logTextArea.append(txt)
        scrollbar = self.logTextArea.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def toggle_macro_process(self):
        if not self.macro_process:
            self.processToggleBtn.setEnabled(False)
            self.processStatusLabel.setText("Running..")
            self.processStatusLabel.setStyleSheet("color: orange")
            self.log("Macro process starting...")

            parent_conn, child_conn = multiprocessing.Pipe()
            self.macro_proc_conn = parent_conn
            self.macro_process = multiprocessing.Process(target=macro_process_main, args=(child_conn,), daemon=True)
            self.macro_process.start()
            threading.Thread(target=self._macroOutQToSignal, args=(parent_conn,), daemon=True).start()

            self.log("Process started (pid: %d)" % self.macro_process.pid)
            self.processStatusLabel.setText("Executed")
            self.processStatusLabel.setStyleSheet("color: green")
            self.processToggleBtn.setEnabled(True)
            self.processToggleBtn.setText("Stop")
        else:
            self.stop_macro()
            self.processToggleBtn.setEnabled(False)
            self.processStatusLabel.setText("Stopping..")
            self.processStatusLabel.setStyleSheet("color: orange")

            os.kill(self.macro_process.pid, signal.SIGTERM)
            self.log("Process terminated")
            self.macro_process = None
            self.processToggleBtn.setEnabled(True)
            self.processStatusLabel.setText("Stopped")
            self.processStatusLabel.setStyleSheet("color: red")
            self.processToggleBtn.setText("Run")

    def _macroOutQToSignal(self, conn):
        """Read from macro process out queue from separate thread, and notify main thread
        using signal"""
        while True:
            try:
                self.macroProcSignal.emit(conn.recv())  # recv() is blocking
            except EOFError:  # closed
                return

    def _setPlatformFile(self, path):
        self.platform_file_path = path
        self.terrainFileLabel.setText(os.path.basename(path).split('.')[0])

    def _onOptChange(self, config_name, checked):
        get_config()[config_name] = checked
        save_config()  # let macro process read new value

    def _alertSound(self, times):
        if time.time() - self.last_alert_sound > self.ALERT_SOUND_CD:
            self.beepSoundRemains = times
            self._alertSoundInternal()
            self.last_alert_sound = time.time() + 0.3 * times

    def _alertSoundInternal(self):
        self.beepSound.play()
        self.beepSoundRemains -= 1
        if self.beepSoundRemains > 0:
            QTimer.singleShot(300, self._alertSoundInternal)

    def _loadPresetPlatform(self, preset):
        file_name = mapscripts.map2platform.get(preset)
        if file_name:
            path = ':/platform/' + file_name + '.platform'
            self._setPlatformFile(path)
        else:
            self.platform_file_path = None
            self.terrainFileLabel.setText('')

    @pyqtSlot(str)
    def on_presetComboBox_activated(self, preset):
        get_config()['preset'] = preset
        get_config()['platform_file'] = None
        self._loadPresetPlatform(preset)

    @pyqtSlot()
    def on_actionNormalAlert_triggered(self):
        self._alertSound(2)

    @pyqtSlot()
    def on_actionWhiteRoom_triggered(self):
        if self.whiteRoomSound.state() == QMediaPlayer.PlayingState:
            self.whiteRoomSound.stop()
        else:
            self.whiteRoomSound.play()

    @pyqtSlot()
    def on_actionSetKeys_triggered(self):
        w = KeyBindWindow(self)
        w.show()

    @pyqtSlot()
    def on_actionEditCurrent_triggered(self):
        if not self.platform_file_path:
            QMessageBox.critical(self, 'Error', 'No terrain file opened')
            return
        if self.platform_file_path.startswith(':/') and is_compiled():
            QMessageBox.critical(self, 'Error', 'Can not edit internal terrain')
            return

        try:
            TerrainEditorWindow(self, self.platform_file_path).show()
        except MapleWindowNotFoundError:
            QMessageBox.critical(self, 'Error', 'The MapleStory window was not found')

    @pyqtSlot()
    def on_actionCreate_triggered(self):
        try:
            TerrainEditorWindow(self).show()
        except MapleWindowNotFoundError:
            QMessageBox.critical(self, 'Error', 'The MapleStory window was not found')

    @pyqtSlot()
    def on_actionAutoStarForce_triggered(self):
        AutoStarForceWindow(self).show()

    @pyqtSlot()
    def on_processToggleBtn_clicked(self):
        self.toggle_macro_process()

    @pyqtSlot()
    def on_macroToggleBtn_clicked(self):
        if self.macro_running:
            self.stop_macro()
        else:
            self.start_macro()

    @pyqtSlot()
    def on_openTerrainBtn_clicked(self):
        dir_ = '.'
        if self.platform_file_path and not self.platform_file_path.startswith(':'):
            dir_ = os.path.dirname(self.platform_file_path)
        platform_file_path = QFileDialog.getOpenFileName(self, "Terrain file selection", dir_,
                                                         "Terrain file (*.platform)")
        if platform_file_path and os.path.exists(platform_file_path[0]):
            self._setPlatformFile(platform_file_path[0])
            get_config()['platform_file'] = platform_file_path[0]
            if self.presetComboBox.currentIndex() != -1:
                self.presetComboBox.setCurrentIndex(-1)
                get_config()['preset'] = None

    @pyqtSlot(object)
    def _onMacroProcMessage(self, ev):
        if ev[0] == "log":
            time_part = '<span class="time-part">' + time.strftime('%H:%M:%S') + '</span>'
            self.log(time_part + ' - ' + str(ev[1]))
        elif ev[0] == "stopped":
            self._set_macro_status(False)
        elif ev[0] == "exception":
            self._set_macro_status(False)
            self.macro_process = None
            self.processToggleBtn.setEnabled(True)
            self.processStatusLabel.setText("Stopped")
            self.processStatusLabel.setStyleSheet("color: red")
            self.processToggleBtn.setText("Running")
            self.log("Macro process terminated due to an error. Please check the log file.")
        elif ev[0] == 'play':
            if ev[1] == 'white_room':
                self.whiteRoomSound.play()
        elif ev[0] == 'alert_sound':
            self._alertSound(ev[1])

    @pyqtSlot()
    def on_actionAbout_triggered(self):
        if self.limit:
            QMessageBox.information(self, 'About', 'Version: %s\n%s hero jioben' % (__version__, self.app_title))
        else:
            QMessageBox.information(self, 'About', ABOUT_TXT % (__version__,))
