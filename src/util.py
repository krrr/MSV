import json
import ctypes
import sys
import threading
import win32con
import collections
import logging
import logging.handlers
import os

_config = None


def get_config():
    global _config
    if _config is None:
        if not os.path.exists('config.json'):
            _config = {}
        else:
            try:
                with open('config.json', encoding='utf-8') as f:
                    _config = json.load(f)
            except Exception:
                _config = {}
    return _config


def save_config():
    with open('config.json', 'w', encoding='utf-8') as f:
        json.dump(_config or {}, f, indent=True, sort_keys=True)


def get_file_log_handler(level=logging.DEBUG):
    fh = logging.handlers.RotatingFileHandler("logging.log", encoding='utf-8', maxBytes=1*1024*1024, backupCount=3)
    fh.setLevel(level)
    fh.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    return fh


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
            if not ctypes.windll.user32.RegisterHotKey(None, i.id, i.modifier_key, i.virtual_key):
                print("Unable to register hotkey with id " + str(i.id), file=sys.stderr)

        callback_map = {i.id: i.callback for i in hotkeys}

        msg = ctypes.wintypes.MSG()
        try:
            # blocking call, will return 0 if received WM_QUIT
            while ctypes.windll.user32.GetMessageA(ctypes.byref(msg), None, 0, 0) != 0:
                if msg.message == win32con.WM_HOTKEY:
                    callback = callback_map.get(msg.wParam)
                    if callback:
                        callback()
                ctypes.windll.user32.TranslateMessage(ctypes.byref(msg))
                ctypes.windll.user32.DispatchMessageA(ctypes.byref(msg))
        finally:
            for i in hotkeys:
                ctypes.windll.user32.UnregisterHotKey(None, i.id)

    def unregister(self):
        ctypes.windll.user32.PostThreadMessageA(self.thread.ident, win32con.WM_QUIT, 0, 0)
        self.thread.join()