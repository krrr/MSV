import random

from msv.player_controller import PlayerController
from msv.input_manager import InputManager
import msv.directinput_constants as dc
import time
from msv.util import random_number
from msv.screen_processor import ScreenProcessor
from msv.screen_processor import StaticImageProcessor
from win32gui import SetForegroundWindow
from msv.mapscripts.royal_library_section6 import RoyalLibrarySection6

wcap = ScreenProcessor()
scrp = StaticImageProcessor(wcap)
hwnd = wcap.get_game_hwnd()
SetForegroundWindow(hwnd)
kbd_mgr = InputManager()
player_manager = PlayerController(kbd_mgr, scrp)


macro = RoyalLibrarySection6()
macro.load_and_process_platform_map('../../msv/resources/platform/royal_library_section6.platform')
# macro.loop_entry()
macro.update()
macro.navigate_to_platform('c6cd2ea8')
macro.player_manager.blade_fury()


# player_cntrlr.optimized_horizontal_move(36)
# player_cntrlr.teleport_right()
# time.sleep(0.5)
# player_cntrlr.teleport_right()
