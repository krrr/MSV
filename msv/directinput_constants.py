# If keyboard input does not work, run as admin
# http://www.flint.jp/misc/?q=dik&lang=en DirectInput Key Codes

DIK_ESCAPE = 0x01
DIK_1 = 0x02
DIK_2 = 0x03
DIK_3 = 0x04
DIK_4 = 0x05
DIK_5 = 0x06
DIK_6 = 0x07
DIK_7 = 0x08
DIK_8 = 0x09
DIK_9 = 0x0A
DIK_0 = 0x0B
DIK_MINUS = 0x0C
DIK_EQUALS = 0x0D
DIK_BACK = 0x0E
DIK_TAB = 0x0F
DIK_Q = 0x10
DIK_W = 0x11
DIK_E = 0x12
DIK_R = 0x13
DIK_T = 0x14
DIK_Y = 0x15
DIK_U = 0x16
DIK_I = 0x17
DIK_O = 0x18
DIK_P = 0x19
DIK_LBRACKET = 0x1A
DIK_RBRACKET = 0x1B
DIK_RETURN = 0x1C
DIK_LControl = 0x1D
DIK_A = 0x1E
DIK_S = 0x1F
DIK_D = 0x20
DIK_F = 0x21
DIK_G = 0x22
DIK_H = 0x23
DIK_J = 0x24
DIK_K = 0x25
DIK_L = 0x26
DIK_SEMICOLON = 0x27
DIK_APOSTROPHE = 0x28
DIK_GRAVE = 0x29
DIK_LSHIFT = 0x2A
DIK_BACKSLASH = 0x2B
DIK_Z = 0x2C
DIK_X = 0x2D
DIK_C = 0x2E
DIK_V = 0x2F
DIK_B = 0x30
DIK_N = 0x31
DIK_M = 0x32
DIK_COMMA = 0x33
DIK_PERIOD = 0x34
DIK_SLASH = 0x35
DIK_RSHIFT = 0x36
DIK_MULTIPLY = 0x37
DIK_LMENU = 0x38
DIK_SPACE = 0x39
DIK_CAPITAL = 0x3A
DIK_F1 = 0x3B
DIK_F2 = 0x3C
DIK_F3 = 0x3D
DIK_F4 = 0x3E
DIK_F5 = 0x3F
DIK_F6 = 0x40
DIK_F7 = 0x41
DIK_F8 = 0x42
DIK_F9 = 0x43
DIK_F10 = 0x44
DIK_NUMLOCK = 0x45
DIK_SCROLL = 0x46
DIK_NUMPAD7 = 0x47
DIK_NUMPAD8 = 0x48
DIK_NUMPAD9 = 0x49
DIK_SUBTRACT = 0x4A
DIK_NUMPAD4 = 0x4B
DIK_NUMPAD5 = 0x4C
DIK_NUMPAD6 = 0x4D
DIK_ADD = 0x4E
DIK_NUMPAD1 = 0x4F
DIK_NUMPAD2 = 0x50
DIK_NUMPAD3 = 0x51
DIK_NUMPAD0 = 0x52
DIK_DECIMAL = 0x53
DIK_F11 = 0x57
DIK_F12 = 0x58
DIK_F13 = 0x64
DIK_F14 = 0x65
DIK_F15 = 0x66
DIK_KANA = 0x70
DIK_CONVERT = 0x79
DIK_NOCONVERT = 0x7B
DIK_YEN = 0x7D
DIK_NUMPADEQUALS = 0x8D
DIK_CIRCUMFLEX = 0x90
DIK_AT = 0x91
DIK_COLON = 0x92
DIK_UNDERLINE = 0x93
DIK_KANJI = 0x94
DIK_STOP = 0x95
DIK_AX = 0x96
DIK_UNLABELED = 0x97
DIK_NUMPADENTER = 0x9C
DIK_RCONTROL = 0x9D
DIK_NUMPADCOMMA = 0xB3
DIK_DIVIDE = 0xB5
DIK_SYSRQ = 0xB7
DIK_RMENU = 0xB8
DIK_PAUSE = 0xC5
DIK_HOME = 0xC7
DIK_UP = 0xC8
DIK_PRIOR = 0xC9
DIK_LEFT = 0xCB
DIK_RIGHT = 0xCD
DIK_END = 0xCF
DIK_DOWN = 0xD0
DIK_NEXT = 0xD1
DIK_INSERT = 0xD2
DIK_DELETE = 0xD3
DIK_LWIN = 0xDB
DIK_RWIN = 0xDC
DIK_APPS = 0xDD
DIK_POWER = 0xDE
DIK_SLEEP = 0xDF

EXTENDED_KEYS = {DIK_LEFT, DIK_UP, DIK_RIGHT, DIK_DOWN,
                 DIK_INSERT, DIK_DELETE, DIK_HOME, DIK_END, DIK_PRIOR, DIK_NEXT,
                 DIK_DIVIDE, DIK_RCONTROL, DIK_RMENU}


keysym_map = {
    "escape": DIK_ESCAPE,
    "alt_l": DIK_LMENU,
    "alt_r": DIK_RMENU,
    "control_l": DIK_LControl,
    "control_r": DIK_RCONTROL,
    "space": DIK_SPACE,
    "comma": DIK_COMMA,
    "period": DIK_PERIOD,
    "home": DIK_HOME,
    "insert": DIK_INSERT,
    "end": DIK_END,
    "shift_r": DIK_RSHIFT,
    "prior": DIK_PRIOR,
    "next": DIK_NEXT,
    "semicolon": DIK_SEMICOLON,
    "quoteleft": DIK_GRAVE,
    "delete": DIK_DELETE,
    "minus": DIK_MINUS,
    "equal": DIK_EQUALS,
    "backspace": DIK_BACK,
    "tab": DIK_TAB,
    "slash": DIK_SLASH,
    "backslash": DIK_BACKSLASH,
    "return": DIK_RETURN,
    "quoteright": DIK_APOSTROPHE,
    "bracketleft": DIK_LBRACKET,
    "bracketright": DIK_RBRACKET,
    "a": DIK_A,
    "b": DIK_B,
    "c": DIK_C,
    "d": DIK_D,
    "e": DIK_E,
    "f": DIK_F,
    "g": DIK_G,
    "h": DIK_H,
    "i": DIK_I,
    "j": DIK_J,
    "k": DIK_K,
    "l": DIK_L,
    "m": DIK_M,
    "n": DIK_N,
    "o": DIK_O,
    "p": DIK_P,
    "q": DIK_Q,
    "r": DIK_R,
    "s": DIK_S,
    "t": DIK_T,
    "u": DIK_U,
    "v": DIK_V,
    "w": DIK_W,
    "x": DIK_X,
    "y": DIK_Y,
    "z": DIK_Z,
    "1": DIK_1,
    "2": DIK_2,
    "3": DIK_3,
    "4": DIK_4,
    "5": DIK_5,
    "6": DIK_6,
    "7": DIK_7,
    "8": DIK_8,
    "9": DIK_9,
    "0": DIK_0,
    "f1": DIK_F1,
    "f2": DIK_F2,
    "f3": DIK_F3,
    "f4": DIK_F4,
    "f5": DIK_F5,
    "f6": DIK_F6,
    "f7": DIK_F7,
    "f8": DIK_F8,
    "f9": DIK_F9,
    "f10": DIK_F10,
    "f11": DIK_F11,
    "f12": DIK_F12,
}

DIK2NAME = {
    DIK_ESCAPE: "Escape",
    DIK_LMENU: "Left Alt",
    DIK_RMENU: "Right Alt",
    DIK_LControl: "Left Control",
    DIK_RCONTROL: "Right Control",
    DIK_SPACE: "Space",
    DIK_COMMA: ",",
    DIK_PERIOD: ".",
    DIK_HOME: "Home",
    DIK_INSERT: "Insert",
    DIK_END: "End",
    DIK_LSHIFT: "Left Shift",
    DIK_RSHIFT: "Right Shift",
    DIK_PRIOR: "Page Up",
    DIK_NEXT: "Page Down",
    DIK_SEMICOLON: ";",
    DIK_GRAVE: "`",
    DIK_DELETE: "Delete",
    DIK_MINUS: "-",
    DIK_EQUALS: "=",
    DIK_BACK: "Back Space",
    DIK_TAB: "Tab",
    DIK_SLASH: "/",
    DIK_BACKSLASH: "\\",
    DIK_RETURN: "Enter",
    DIK_APOSTROPHE: "'",
    DIK_LBRACKET: "[",
    DIK_RBRACKET: "]",
    DIK_CAPITAL: "Caps Lock",
    DIK_SCROLL: "Scroll Lock",
    DIK_A: "A",
    DIK_B: "B",
    DIK_C: "C",
    DIK_D: "D",
    DIK_E: "E",
    DIK_F: "F",
    DIK_G: "G",
    DIK_H: "H",
    DIK_I: "I",
    DIK_J: "J",
    DIK_K: "K",
    DIK_L: "L",
    DIK_M: "M",
    DIK_N: "N",
    DIK_O: "O",
    DIK_P: "P",
    DIK_Q: "Q",
    DIK_R: "R",
    DIK_S: "S",
    DIK_T: "T",
    DIK_U: "U",
    DIK_V: "V",
    DIK_W: "W",
    DIK_X: "X",
    DIK_Y: "Y",
    DIK_Z: "Z",
    DIK_1: "1",
    DIK_2: "2",
    DIK_3: "3",
    DIK_4: "4",
    DIK_5: "5",
    DIK_6: "6",
    DIK_7: "7",
    DIK_8: "8",
    DIK_9: "9",
    DIK_0: "0",
    DIK_F1: "F1",
    DIK_F2: "F2",
    DIK_F3: "F3",
    DIK_F4: "F4",
    DIK_F5: "F5",
    DIK_F6: "F6",
    DIK_F7: "F7",
    DIK_F8: "F8",
    DIK_F9: "F9",
    DIK_F10: "F10",
    DIK_F11: "F11",
    DIK_F12: "F12",
}