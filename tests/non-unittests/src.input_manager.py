import sys
sys.path.insert(0, 'src')

import ctypes
import driver
from input_manager import InputManager
from directinput_constants import *
ctypes.windll.user32.SetProcessDPIAware()

driver.load_driver()
mgr = InputManager(use_driver=True)
mgr.single_press(DIK_HOME)
# mgr.mouse_move_absolute(1900, 1)
# mgr.mouse_left_click()
