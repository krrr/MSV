import ctypes
from src.input_manager import InputManager
ctypes.windll.user32.SetProcessDPIAware()

from src.directinput_constants import *
mgr = InputManager()
# mgr.single_press(DIK_INSERT)
mgr.mouse_move_absolute(1900, 1)
# mgr.mouse_left_click()
