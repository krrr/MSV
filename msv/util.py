import json
import sys
import win32con
import collections
import logging
import logging.handlers
import os
import math
import random
import numpy as np
from multiprocessing.connection import Connection
from ctypes import c_buffer, windll
from PyQt5.QtCore import QFile, QAbstractNativeEventFilter, QTimer
from msv import winapi

_config = None
config_file = 'config.json'
resource_path = os.path.dirname(__file__) + '\\resources\\'
runtime_info = {}  # used in main thread


def read_qt_resource(path, numpy=False):
    if is_compiled():
        file = QFile(path)
        if file.open(QFile.ReadOnly):
            ret = file.readAll()
            file.close()
            if numpy:
                ret = np.frombuffer(ret, np.uint8)
            return ret
        else:
            raise Exception(file.errorString() + ': ' + path)
    else:
        if not path.startswith(':/'):
            raise Exception('path not starts with ":/"')
        with open(resource_path + path[2:].replace('/', '\\'), 'rb') as f:
            ret = f.read()
            if numpy:
                ret = np.frombuffer(ret, np.uint8)
            return ret


def _winmm_command(*command):
    buf = c_buffer(255)
    command = ' '.join(command).encode(sys.getfilesystemencoding())
    errorCode = int(windll.winmm.mciSendStringA(command, buf, 254, 0))
    if errorCode:
        errorBuffer = c_buffer(255)
        windll.winmm.mciGetErrorStringW(errorCode, errorBuffer, 254)
        exceptionMessage = ('Error ' + str(errorCode) + ' for command:\n' + command.decode() +
                            '\n' + errorBuffer.value.decode('utf-16'))
        raise Exception(exceptionMessage)
    return buf.value


def get_config():
    global _config
    if _config is None:
        if not os.path.exists(config_file):
            _config = {}
        else:
            try:
                with open(config_file, encoding='utf-8') as f:
                    _config = json.load(f)
            except Exception:
                _config = {}
    return _config


def save_config():
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(_config or {}, f, indent=True, sort_keys=True)


def get_file_log_handler(level=logging.DEBUG):
    fh = logging.handlers.RotatingFileHandler("logging.log", encoding='utf-8', maxBytes=1*1024*1024, backupCount=3)
    fh.setLevel(level)
    fh.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s', "%m-%d %H:%M:%S"))
    return fh


class ConnLoggerHandler(logging.Handler):
    def __init__(self, level, conn: Connection):
        super().__init__(level)
        self.conn = conn

    def emit(self, record):
        if self.conn:
            self.conn.send(("log", self.format(record)))


def setup_tesseract_ocr():
    path = 'Tesseract-OCR'
    if not os.path.exists(path):
        path = '..\\' + path
    if not os.path.exists(path):
        return False

    path = os.path.realpath(path)
    os.environ['PATH'] += ';' + path
    os.environ['TESSDATA_PREFIX'] = os.path.join(path, 'tessdata')
    if hasattr(os, 'add_dll_directory'):  # py 3.8+
        os.add_dll_directory(path)
    return True


class GlobalHotKeyListener(QAbstractNativeEventFilter):
    """bind windows global hotkey
    https://github.com/Skycoder42/QHotkey/blob/master/QHotkey/qhotkey_win.cpp
    """
    HotKey = collections.namedtuple('HotKey', ('id', 'modifier_key', 'virtual_key', 'callback'))

    def __init__(self, hotkeys):
        super().__init__()
        self.hotkeys = hotkeys
        for i in hotkeys:
            if not winapi.RegisterHotKey(None, i.id, i.modifier_key, i.virtual_key):
                print("Unable to register hotkey with id " + str(i.id), file=sys.stderr)

        self.callback_map = {i.id: i.callback for i in hotkeys}
        self.hotkey_down = {}  # virtual_key -> bool
        self.pollTimer = QTimer()
        self.pollTimer.setInterval(100)
        self.pollTimer.timeout.connect(self.pollForKeyRelease)

    def nativeEventFilter(self, eventType, message):  # PyQt specific
        if eventType == b'windows_generic_MSG':
            msg = winapi.MSG.from_address(message.__int__())
            if msg.message == win32con.WM_HOTKEY:
                vk = msg.lParam >> 16
                if not self.hotkey_down.get(vk):
                    self.hotkey_down[vk] = True
                    self.pollTimer.start()
                    callback = self.callback_map.get(msg.wParam)
                    if callback:
                        callback()
                return True, 0
        return False, 0

    def pollForKeyRelease(self):
        for i in list(self.hotkey_down.keys()):
            if not winapi.GetKeyState(i) & 0x8000:  # key is not down
                del self.hotkey_down[i]
        if len(self.hotkey_down) == 0:
            self.pollTimer.stop()

    def unregister(self):
        for i in self.hotkeys:
            winapi.UnregisterHotKey(None, i.id)


def color_distance(c1, c2):
    return math.sqrt((c1[0]-c2[0])**2 + (c1[1]-c2[1])**2 + (c1[2]-c2[2])**2)


def random_number(gen_range=0.1, digits=2, minus=False):
    """
    returns a random number x where 0<=x<=gen_range or -gen_range<=x<=gen_range rounded to digits number
    of digits under floating points
    :param gen_range: float for generating number x where -gen_range<=x<=gen_range
    :param digits: n digits under floating point to round. 0 returns integer as float type
    :param minus: include minus part
    :return: random number float
    """
    d = round(random.uniform(0, gen_range), digits)
    if minus and random.random() < 0.5:
        d *= -1
    return d


def is_compiled():
    """Detect is compiled using Nutika"""
    return not os.path.isfile(__file__)
