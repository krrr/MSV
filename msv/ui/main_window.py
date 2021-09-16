import multiprocessing, time, os, signal, pickle
import base64
import win32con
import threading
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtMultimedia import *
from msv import driver, mapscripts, winapi, APP_TITLE, __version__
from msv.ui import fix_sizes_for_high_dpi
from msv.ui.main_window_ui import Ui_MainWindow
from msv.util import get_config, save_config, GlobalHotKeyListener, read_qt_resource
# from msv.screen_processor import ScreenProcessor
from msv.macro_script import macro_process_main
from msv.ui.key_bind_window import KeyBindWindow
from msv.ui.auto_star_force_window import AutoStarForceWindow
# from msv.terrain_editor import TerrainEditorWindow
from msv.screen_processor import ScreenProcessor


class MainWindow(QMainWindow, Ui_MainWindow):
    ALERT_SOUND_CD = 2
    macro_out_q_signal = pyqtSignal(object)

    def __init__(self):
        super().__init__(None, Qt.CustomizeWindowHint | Qt.WindowMinimizeButtonHint | Qt.WindowCloseButtonHint)  # disable maximize button
        self.setupUi(self)
        fix_sizes_for_high_dpi(self)
        self.actionAutoSolveRune.setChecked(get_config().get('auto_solve_rune', True))
        self.actionAutoSolveRune.triggered.connect(lambda x: self._onOptChange('auto_solve_rune', x))
        self.actionKernelDriver.setChecked(get_config().get('kernel_driver', False))
        self.actionKernelDriver.triggered.connect(lambda x: self._onOptChange('kernel_driver', x))
        self.actionDebugMode.setChecked(get_config().get('debug_mode', False))
        self.actionDebugMode.triggered.connect(lambda x: self._onOptChange('debug_mode', x))
        self.macro_out_q_signal.connect(self._onMacroQMessage)

        self.keymap = None
        self.macro_running = False
        self.macro_process = None
        self.platform_file_path = None
        self.macro_process_in_q = multiprocessing.Queue()

        self.log(APP_TITLE + " version: v" + __version__)
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

        self.presetComboBox.insertSeparator(6)  # insert will change index

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
                self.log('kernel driver loaded')
            except Exception as e:
                QMessageBox.critical(self, 'Error', 'Driver failed to load: ' + str(e))

    def closeEvent(self, event):
        # lambda may cause leak
        self.actionAutoSolveRune.triggered.disconnect()
        self.actionKernelDriver.triggered.disconnect()
        self.actionDebugMode.triggered.disconnect()

        if self.macro_process:
            try:
                self.macro_process_in_q.put(("stop",))
                os.kill(self.macro_process.pid, signal.SIGTERM)
            except Exception:
                pass

        get_config()['geometry'] = base64.b64encode(bytes(self.saveGeometry())).decode('ascii')
        save_config()

        self.hotkeyListener.unregister()

        super().closeEvent(event)

    def start_macro(self):
        if not winapi.IsUserAnAdmin():
            QMessageBox.critical(self, 'Error', 'Please run as administrator')
            return

        if not self.macro_process:
            self.toggle_macro_process()
        keymap = get_config().get('keymap')
        if not keymap:
            QMessageBox.critical(self, 'Error', "The key setting could not be read. Please reset the key.")
            return

        if not self.platform_file_path:
            QMessageBox.critical(self, 'Error', "Please select a terrain file.")
            return

        cap = ScreenProcessor()
        if not cap.get_game_hwnd():
            QMessageBox.critical(self, 'Error', "MapleStory window not found")
            return

        rect = cap.ms_get_screen_rect()
        if get_config().get('debug'):
            self.log("Game Window Rect:", rect)
        if rect is None:
            QMessageBox.critical(self, 'Error', "Failed to get Maple Window location.\nMove MapleStory window so "
                                                 "that the top left corner of the window is within the screen.")
            return

        self.beepUpSound.play()
        cap.set_foreground()
        self.macro_process_in_q.put(("start", keymap, self.platform_file_path, self._get_preset()))
        self._set_macro_status(True)

    def stop_macro(self):
        self.beepDownSound.play()
        self.macro_process_in_q.put(("stop",))
        self.log("Stopping.")
        self._set_macro_status(False)

    def _set_macro_status(self, running):
        self.macro_running = running
        self.macroToggleBtn.setText("Stop Macro" if running else "Start Macro")
        self.openTerrainBtn.setDisabled(running)
        self.presetComboBox.setDisabled(running)

    def log(self, *args):
        txt = ' '.join(str(i) for i in args)
        self.logTextArea.append(txt)
        scrollbar = self.logTextArea.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def toggle_macro_process(self):
        if not self.macro_process:
            self.processToggleBtn.setEnabled(False)
            self.processStatusLabel.setText("Running..")
            self.processStatusLabel.setStyleSheet("color: orange")
            self.log("Macro process starting...")
            self.macro_process_in_q = multiprocessing.Queue()
            macro_process_out_q = multiprocessing.Queue()
            self.macro_process = multiprocessing.Process(
                target=macro_process_main, args=(self.macro_process_in_q, macro_process_out_q), daemon=True)
            self.macro_process.start()
            threading.Thread(target=self._macroOutQToSignal, args=(macro_process_out_q,), daemon=True).start()

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

            self.log("SIGTERM %d" % self.macro_process.pid)
            os.kill(self.macro_process.pid, signal.SIGTERM)
            self.log("Process terminated")
            self.macro_process = None
            self.processToggleBtn.setEnabled(True)
            self.processStatusLabel.setText("Stopped")
            self.processStatusLabel.setStyleSheet("color: red")
            self.processToggleBtn.setText("Run")

    def _macroOutQToSignal(self, q):
        """Read from macro process out queue from separate thread, and notify main thread
        using signal"""
        while True:
            try:
                self.macro_out_q_signal.emit(q.get())  # get() is blocking
            except (ValueError, AssertionError):  # queue closed
                return

    def _get_preset(self):
        idx = self.presetComboBox.currentIndex()
        return self.preset_names[idx] if idx != -1 else None

    def _setPlatformFile(self, path):
        try:
            if path.startswith(':'):
                content = read_qt_resource(path, False)
            else:
                with open(path, "rb") as f:
                    content = f.read()

            data = pickle.loads(content)
            platforms = data["platforms"]
            # minimap_coords = data["minimap"]
            self.log("Terrain file loaded (platforms: %s)" % len(platforms.keys()))
        except Exception as e:
            QMessageBox.critical(self, 'Error', "Failed to load terrain file: %s\n%s" % (path, str(e)))
        else:
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
        path = ':/platform/' + mapscripts.map2platform[preset] + '.platform'
        self._setPlatformFile(path)

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
        else:
            # TerrainEditorWindow(self.master, self.platform_file_path)
            pass

    @pyqtSlot()
    def on_actionCreate_triggered(self):
        # TerrainEditorWindow(self.master)
        pass

    @pyqtSlot()
    def on_actionAutoStarForce_triggered(self):
        win = AutoStarForceWindow(self)
        win.show()

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
        platform_file_path = QFileDialog.getOpenFileName(self, "Terrain file selection", '.',
                                                         "Terrain file (*.platform)")
        if platform_file_path and os.path.exists(platform_file_path[0]):
            self._setPlatformFile(platform_file_path[0])
            get_config()['platform_file'] = platform_file_path[0]
            if self.presetComboBox.currentIndex() != -1:
                self.presetComboBox.setCurrentIndex(-1)
                get_config()['preset'] = None

    @pyqtSlot(object)
    def _onMacroQMessage(self, ev):
        if ev[0] == "log":
            self.log(time.strftime('%H:%M:%S') + ' - ' + str(ev[1]))
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
        elif ev[0] == 'play_sound':
            self.whiteRoomSound.play()
        elif ev[0] == 'alert_sound':
            self._alertSound(ev[1])

    @pyqtSlot()
    def on_actionAbout_triggered(self):
        QMessageBox.information(self, 'About', '''\
Version: v%s
Author: Dashadower, krrr
Source code: https://github.com/krrr/MSV-Kanna-Ver

Please be known that using this macro may get your account banned. By using this software,
you acknowledge that the developers are not liable for any damages caused to you or your account.
''' % (__version__,))
