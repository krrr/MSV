import time, ctypes
import win32api
import win32con
import math
import random
from msv import driver, winapi, util
import msv.directinput_constants as dic


# C struct redefinitions
PUL = ctypes.POINTER(ctypes.c_ulong)


class KeyBdInput(ctypes.Structure):
    _fields_ = [("wVk", ctypes.c_ushort),
                ("wScan", ctypes.c_ushort),
                ("dwFlags", ctypes.c_ulong),
                ("time", ctypes.c_ulong),
                ("dwExtraInfo", PUL)]


class HardwareInput(ctypes.Structure):
    _fields_ = [("uMsg", ctypes.c_ulong),
                ("wParamL", ctypes.c_short),
                ("wParamH", ctypes.c_ushort)]


class MouseInput(ctypes.Structure):
    _fields_ = [("dx", ctypes.c_long),
                ("dy", ctypes.c_long),
                ("mouseData", ctypes.c_ulong),
                ("dwFlags", ctypes.c_ulong),
                ("time", ctypes.c_ulong),
                ("dwExtraInfo", PUL)]


class Input_I(ctypes.Union):
    _fields_ = [("ki", KeyBdInput),
                ("mi", MouseInput),
                ("hi", HardwareInput)]


class Input(ctypes.Structure):
    _fields_ = [("type", ctypes.c_ulong),
                ("ii", Input_I)]


# http://robertpenner.com/easing/
# t: current_time
def ease_in_out_quad(t, start, delta, duration):
    t /= duration / 2
    if t < 1:
        return delta / 2 * t * t + start
    t -= 1
    return -delta / 2 * (t * (t - 2) - 1) + start


def load_keymap():
    saved = util.get_config().get('keymap')
    if saved:
        for k, v in saved.items():  # convert config from old version
            if isinstance(v, list):
                saved[k] = v[0]
        return saved.copy()
    else:
        return DEFAULT_KEY_MAP.copy()


class InputManager:
    """
    This is an attempt to manage input from a single source. It remembers key "states" , which consists of keypress
    modifications, and actuates them in a single batch.
    """
    def __init__(self, debug=False, use_driver=False):
        """
        Class variables:
        self.key_state: Temporary state dictionary before being actuated. Dictionary with DIK key names as keys with
        0 or 1 as keys (0 for release, 1 for press)
        self.actual_key_state: Actual key state dictionary. This dictionary is used to keep track of which keys are
        currently being pressed. Same format as self.key_state
        :param debug: Debug flag
        """
        self.key_state = {}
        self.actual_key_state = {}
        self.debug = debug
        self.use_driver = use_driver

    def get_key_state(self, key_code=None):
        """
        Returns key state or states of current manager state
        :param key_code : DIK key name of key to look up. Please refer to directinput_constants.py. If undefined, returns enture key state
        :return: None"""
        if key_code:
            if key_code in self.key_state.keys():
                return self.key_state[key_code]
            else:
                return None
        else:
            return self.key_state

    def set_key_state(self, key_code, value):
        """
        Explicitly sets key state for key_code by value
        :param key_code: DIK Key name of keycode
        :param value: 0 for released, 1 for pressed
        :return: None"""
        self.key_state[key_code] = value

    def single_press(self, key_code, duration=0.06, additional_duration=0):
        """
        Presses key_code for duration seconds. Since it uses time.sleep(), it is a blocking call.
        :param key_code: DIK key code of key
        :param duration: Float of keypress duration in seconds
        :param additional_duration: additinal delay to be added
        :return: None
        """
        self.direct_press(key_code)
        time.sleep(duration)
        self.direct_release(key_code)
        if additional_duration != 0:
            time.sleep(additional_duration)

    def translate_key_state(self):
        """
        Acuates key presses in self.key_state to self.actual_key_state by pressing keys and storing state in self.actual_key_state
        self.actual_key_state becomes self.key_state, and self.key_state will get reset
        :return: None
        """
        for keycode, state in self.key_state.items():
            if keycode in self.actual_key_state.keys():
                if self.actual_key_state[keycode] != state:
                    if state:
                        self.press_key(keycode)
                        self.actual_key_state[keycode] = 1
                    elif not state:
                        self.release_key(keycode)
                        self.actual_key_state[keycode] = 0
            else:
                if state:
                    self.press_key(keycode)
                    self.actual_key_state[keycode] = 1
                elif not state:
                    self.release_key(keycode)
                    self.actual_key_state[keycode] = 0

        self.key_state = {}

    def direct_press(self, key_code):
        self.press_key(key_code)
        self.actual_key_state[key_code] = 1

    def direct_release(self, key_code):
        self.release_key(key_code)
        self.actual_key_state[key_code] = 0

    def mouse_move(self, x, y):
        start_pos = self.get_cursor_pos()
        deltas = x - start_pos[0], y - start_pos[1]
        dis = int(math.sqrt(deltas[0]**2 + deltas[1]**2))
        step = max((dis // 50, 5))
        for i in range(1, step+1):
            pos_x = ease_in_out_quad(i, start_pos[0], deltas[0], step)
            pos_y = ease_in_out_quad(i, start_pos[1], deltas[1], step)
            self.mouse_move_absolute(pos_x, pos_y)
            time.sleep(0.02)
        self.mouse_move_absolute(x, y)

    def mouse_left_click(self):
        self.mouse_click_left(True)
        time.sleep(0.02)
        self.mouse_click_left(False)

    def mouse_left_click_at(self, x, y, rand=0):
        if rand != 0:
            x += random.randint(-rand, rand)
            y += random.randint(-rand, rand)
        self.mouse_move(x, y)
        self.mouse_left_click()

    def reset(self):
        """
        Safe way of releasing all keys and resetting all states.
        :return: None
        """
        for keycode, state in self.key_state.items():
            if keycode in self.actual_key_state.keys():
                self.key_state[keycode] = 0
        for keycode, state in self.actual_key_state.items():
            self.key_state[keycode] = 0
        self.translate_key_state()

    def press_key(self, hexKeyCode):
        extra = ctypes.c_ulong(0)
        ii_ = Input_I()
        ii_.ki = KeyBdInput(0, hexKeyCode, win32con.KEYEVENTF_SCANCODE, 0, ctypes.pointer(extra))
        self._send_input(Input(win32con.INPUT_KEYBOARD, ii_))

    def release_key(self, hexKeyCode):
        extra = ctypes.c_ulong(0)
        ii_ = Input_I()
        ii_.ki = KeyBdInput(0, hexKeyCode, win32con.KEYEVENTF_SCANCODE | win32con.KEYEVENTF_KEYUP, 0, ctypes.pointer(extra))

        self._send_input(Input(win32con.INPUT_KEYBOARD, ii_))

    def mouse_move_absolute(self, x, y):
        x = int(x * 65536.0 / win32api.GetSystemMetrics(win32con.SM_CXSCREEN))
        y = int(y * 65536.0 / win32api.GetSystemMetrics(win32con.SM_CYSCREEN))
        extra = ctypes.c_ulong(0)
        ii_ = Input_I()
        ii_.mi = MouseInput(x, y, 0, win32con.MOUSEEVENTF_MOVE | win32con.MOUSEEVENTF_ABSOLUTE, 0, ctypes.pointer(extra))
        self._send_input(Input(win32con.INPUT_MOUSE, ii_))

    def mouse_click_left(self, down):
        extra = ctypes.c_ulong(0)
        ii_ = Input_I()
        ii_.mi = MouseInput(0, 0, 0, win32con.MOUSEEVENTF_LEFTDOWN if down else win32con.MOUSEEVENTF_LEFTUP, 0, ctypes.pointer(extra))
        self._send_input(Input(win32con.INPUT_MOUSE, ii_))

    def _send_input(self, input_struct):
        if input_struct.ii.ki.wScan in dic.EXTENDED_KEYS:
            input_struct.ii.ki.dwFlags |= win32con.KEYEVENTF_EXTENDEDKEY

        if self.use_driver:
            driver.send_input(1, ctypes.addressof(input_struct), ctypes.sizeof(input_struct))
        else:
            winapi.SendInput(1, ctypes.byref(input_struct), ctypes.sizeof(input_struct))

    def get_cursor_pos(self):
        point = ctypes.wintypes.POINT()
        if winapi.GetCursorPos(ctypes.pointer(point)) == 1:
            return point.x, point.y
        else:
            return None


DEFAULT_KEY_MAP = {
    "jump": dic.DIK_SPACE,
    "eight_legs_easton": dic.DIK_A,
    "nautilus_strike": dic.DIK_Q,
    "death_trigger": dic.DIK_R,
    "ugly_bomb": dic.DIK_W,
    "upward_charge": dic.DIK_D,
    "interact": dic.DIK_C,
    "whalers_potion": dic.DIK_END,
    "holy_symbol": None,
    "rope": dic.DIK_EQUALS,
    "wild_totem": None,
    "nightmare_invite": dic.DIK_T,
    "true_arachnid_reflection": dic.DIK_H,
    "target_lock": dic.DIK_E,
    "roll_dice": dic.DIK_DELETE,
    "paochuan": dic.DIK_1,
    "paotai": dic.DIK_2,
    "scurvy_summons": dic.DIK_LSHIFT,
    "bullet_barrage": dic.DIK_X,
    "nautilus_assault": dic.DIK_Z,
}

KEY2DISPLAY_NAME = {
    "jump": "Jump",
    "eight_legs_easton": "Eight-Legs Easton",
    "nautilus_strike": "Nautilus Strike",
    "death_trigger": "Death Trigger",
    "ugly_bomb": "Ugly Bomb",
    "upward_charge": "Wings",
    "interact": "Interact",
    "whalers_potion": "Whaler's Potion",
    "holy_symbol": "Holy Symbol",
    "rope": "Rope",
    "wild_totem": "Wild Totem",
    "nightmare_invite": "Erda Shower",
    "true_arachnid_reflection": "True Arachnid Reflection",
    "target_lock": "Burning Soul Blade",
    "roll_dice": "Roll of the Dice",
    "paochuan": "Broadside",
    "paotai": "Siege Bomber",
    "scurvy_summons": "Scurvy Summons",
    "bullet_barrage": "Bullet Barrage",
    "nautilus_assault": "Nautilus Assault",
}
