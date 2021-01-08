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
    fh.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s', "%m-%d %H:%M:%S"))
    return fh


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