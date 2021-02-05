import directinput_constants as dic
import time, ctypes
import win32api
import win32con
import math
import random


SendInput = ctypes.windll.user32.SendInput
GetCursorPos = ctypes.windll.user32.GetCursorPos
# C struct redefinitions
PUL = ctypes.POINTER(ctypes.c_ulong)
KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_SCANCODE = 0x0008
MOUSEEVENTF_MOVE = 0x0001
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
MOUSEEVENTF_VIRTUALDESK = 0x4000
MOUSEEVENTF_ABSOLUTE = 0x8000


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


def PressKey(hexKeyCode):
    extra = ctypes.c_ulong(0)
    ii_ = Input_I()
    ii_.ki = KeyBdInput(0, hexKeyCode, 0x0008, 0, ctypes.pointer(extra) )
    x = Input(ctypes.c_ulong(1), ii_)
    SendInput(1, ctypes.pointer(x), ctypes.sizeof(x))


def ReleaseKey(hexKeyCode):
    extra = ctypes.c_ulong(0)
    ii_ = Input_I()
    ii_.ki = KeyBdInput(0, hexKeyCode, KEYEVENTF_SCANCODE | KEYEVENTF_KEYUP, 0, ctypes.pointer(extra))
    x = Input(ctypes.c_ulong(1), ii_)
    SendInput(1, ctypes.pointer(x), ctypes.sizeof(x))


def MouseMoveAbsolute(x, y):
    x = int(x * 65536.0 / win32api.GetSystemMetrics(win32con.SM_CXSCREEN))
    y = int(y * 65536.0 / win32api.GetSystemMetrics(win32con.SM_CYSCREEN))
    extra = ctypes.c_ulong(0)
    ii_ = Input_I()
    ii_.mi = MouseInput(x, y, 0, MOUSEEVENTF_MOVE | MOUSEEVENTF_ABSOLUTE, 0, ctypes.pointer(extra))
    command = Input(ctypes.c_ulong(0), ii_)
    SendInput(1, ctypes.pointer(command), ctypes.sizeof(command))


def MouseLeftClick(down):
    extra = ctypes.c_ulong(0)
    ii_ = Input_I()
    ii_.mi = MouseInput(0, 0, 0, MOUSEEVENTF_LEFTDOWN if down else MOUSEEVENTF_LEFTUP, 0, ctypes.pointer(extra))
    x = Input(ctypes.c_ulong(0), ii_)
    SendInput(1, ctypes.pointer(x), ctypes.sizeof(x))


def GetMouseCursorPos():
    point = ctypes.wintypes.POINT()
    if GetCursorPos(ctypes.pointer(point)) == 1:
        return point.x, point.y
    else:
        return None


# http://robertpenner.com/easing/
# t: current_time
def ease_in_out_quad(t, start, delta, duration):
    t /= duration / 2
    if t < 1:
        return delta / 2 * t * t + start
    t -= 1
    return -delta / 2 * (t * (t - 2) - 1) + start


class InputManager:
    """
    This is an attempt to manage input from a single source. It remembers key "states" , which consists of keypress
    modifications, and actuates them in a single batch.
    """
    def __init__(self, debug=False):
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
                        PressKey(keycode)
                        self.actual_key_state[keycode] = 1
                    elif not state:
                        ReleaseKey(keycode)
                        self.actual_key_state[keycode] = 0
            else:
                if state:
                    PressKey(keycode)
                    self.actual_key_state[keycode] = 1
                elif not state:
                    ReleaseKey(keycode)
                    self.actual_key_state[keycode] = 0

        self.key_state = {}

    def direct_press(self, key_code):
        PressKey(key_code)
        self.actual_key_state[key_code] = 1

    def direct_release(self, key_code):
        ReleaseKey(key_code)
        self.actual_key_state[key_code] = 0

    def mouse_move_absolute(self, x, y):
        MouseMoveAbsolute(x, y)

    def mouse_move(self, x, y):
        start_pos = GetMouseCursorPos()
        deltas = x - start_pos[0], y - start_pos[1]
        dis = int(math.sqrt(deltas[0]**2 + deltas[1]**2))
        step = max((dis // 50, 5))
        for i in range(1, step+1):
            pos_x = ease_in_out_quad(i, start_pos[0], deltas[0], step)
            pos_y = ease_in_out_quad(i, start_pos[1], deltas[1], step)
            self.mouse_move_absolute(pos_x, pos_y)
            time.sleep(0.02)
        MouseMoveAbsolute(x, y)

    def mouse_left_click(self):
        MouseLeftClick(True)
        time.sleep(0.02)
        MouseLeftClick(False)

    def mouse_left_click_at(self, x, y, rand=0):
        if rand != 0:
            x += random.randint(0, rand)
            y += random.randint(0, rand)
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


DEFAULT_KEY_MAP = {
    "jump": [dic.DIK_RSHIFT, "Jump"],
    "teleport": [dic.DIK_SPACE, "Teleport"],
    "shikigami_haunting": [dic.DIK_RCONTROL, "Shikigami Haunting"],
    "kishin_shoukan": [dic.DIK_Q, "Kishin Shoukan"],
    "yaksha_boss": [dic.DIK_O, "Yaksha Boss"],
    "holy_symbol": [dic.DIK_PRIOR, "Holy Symbol"],
    "speed_infusion": [dic.DIK_HOME, "Speed Infusion"],
    "haku_reborn": [dic.DIK_END, "Haku Reborn"],
    "yuki_musume": [dic.DIK_1, "Yuki-musume Shoukan"],
    "interact": [dic.DIK_PERIOD, "Interact / Harvest"],
    "shikigami_charm": [dic.DIK_SEMICOLON, "Shikigami Charm"],
    "exorcist_charm": [dic.DIK_Y, "Exorcist Charm"],
    "mihaha_link": [None, "Mihaha Link"],
    "nightmare_invite": [None, "Nightmare Invite"]
}

