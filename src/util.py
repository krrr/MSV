import json
import ctypes
import sys
import threading
import win32con
import collections
import logging
import logging.handlers
import os
import multiprocessing as mp
import math
from ctypes import c_buffer, windll
from random import random

_config = None
config_file = 'config.json'


def _winmm_command(*command):
    buf = c_buffer(255)
    command = ' '.join(command).encode(sys.getfilesystemencoding())
    errorCode = int(windll.winmm.mciSendStringA(command, buf, 254, 0))
    if errorCode:
        errorBuffer = c_buffer(255)
        windll.winmm.mciGetErrorStringA(errorCode, errorBuffer, 254)
        exceptionMessage = ('\n    Error ' + str(errorCode) + ' for command:'
                                                              '\n        ' + command.decode() +
                            '\n    ' + errorBuffer.value.decode())
        raise Exception(exceptionMessage)
    return buf.value


def play_sound(name):
    # https://github.com/TaylorSMarks/playsound
    sound = 'resources\\sound\\' + name + '.mp3'
    alias = 'playsound_' + str(random())
    _winmm_command('open "' + sound + '" alias', alias)
    _winmm_command('set', alias, 'time format milliseconds')
    duration_in_ms = _winmm_command('status', alias, 'length')
    _winmm_command('play', alias, 'from 0 to', duration_in_ms.decode())


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


class QueueLoggerHandler(logging.Handler):
    def __init__(self, level, logger_queue):
        super().__init__(level)
        self.logger_queue = logger_queue

    def emit(self, record):
        if self.logger_queue:
            self.logger_queue.put(("log", self.format(record)))


def copy_ev_queue(src: mp.Queue, dst, root):
    while True:
        try:
            dst.append(src.get())  # get() is blocking
            root.event_generate("<<ev>>", when="tail")
        except (ValueError, AssertionError):  # queue closed
            return


def setup_tesseract_ocr():
    if os.path.exists('../Tesseract-OCR'):
        p = os.path.realpath('../Tesseract-OCR')
        os.environ['PATH'] += ';' + p
        os.environ['TESSDATA_PREFIX'] = os.path.join(p, 'tessdata')
        if hasattr(os, 'add_dll_directory'):  # py 3.8+
            os.add_dll_directory(p)


_user32 = ctypes.windll.user32


class GlobalHotKeyListener:
    """bind windows global hotkey
    https://stackoverflow.com/questions/6023172/ending-a-program-mid-run/40177310#40177310
    """
    HotKey = collections.namedtuple('HotKey', ('id', 'modifier_key', 'virtual_key', 'callback'))

    def __init__(self, hotkeys):
        self.thread = threading.Thread(target=GlobalHotKeyListener.loop, args=(hotkeys,))
        self.thread.setDaemon(True)
        self.thread.start()

    @staticmethod
    def loop(hotkeys):
        # register hotkey with Win API
        for i in hotkeys:
            if not _user32.RegisterHotKey(None, i.id, i.modifier_key, i.virtual_key):
                print("Unable to register hotkey with id " + str(i.id), file=sys.stderr)

        callback_map = {i.id: i.callback for i in hotkeys}
        hotkey_down = {}  # virtual_key -> bool

        msg = ctypes.wintypes.MSG()
        try:
            # blocking call, will return 0 if received WM_QUIT
            while _user32.GetMessageA(ctypes.byref(msg), None, 0, 0) != 0:
                if msg.message == win32con.WM_HOTKEY:
                    vk = msg.lParam >> 16
                    if not hotkey_down.get(vk):
                        hotkey_down[vk] = True
                        _user32.SetTimer(None, 0, 200, None)
                        callback = callback_map.get(msg.wParam)
                        if callback:
                            callback()
                elif msg.message == win32con.WM_TIMER:
                    for i in list(hotkey_down.keys()):
                        if not _user32.GetKeyState(i) & 0x8000:  # key is not down
                            del hotkey_down[i]
                    if len(hotkey_down) == 0:
                        _user32.KillTimer(None, msg.wParam)
                _user32.TranslateMessage(ctypes.byref(msg))
                _user32.DispatchMessageA(ctypes.byref(msg))
        finally:
            for i in hotkeys:
                _user32.UnregisterHotKey(None, i.id)

    def unregister(self):
        _user32.PostThreadMessageA(self.thread.ident, win32con.WM_QUIT, 0, 0)
        self.thread.join()


def color_distance(c1, c2):
    return math.sqrt((c1[0]-c2[0])**2 + (c1[1]-c2[1])**2 + (c1[2]-c2[2])**2)

