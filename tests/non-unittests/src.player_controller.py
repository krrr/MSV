import util
import time
from msv.directinput_constants import DIK_RIGHT, DIK_DOWN, DIK_LEFT, DIK_UP
from msv.player_controller import PlayerController
from msv.input_manager import InputManager
from msv.screen_processor import ScreenProcessor
from msv.screen_processor import StaticImageProcessor
from win32gui import SetForegroundWindow
from msv.mapscripts.end_of_the_world2_4 import EndOfTheWorld2_4

wcap = ScreenProcessor()
scrp = StaticImageProcessor(wcap)
hwnd = wcap.get_game_hwnd()
SetForegroundWindow(hwnd)
kbd_mgr = InputManager()
# player_manager = PlayerController(kbd_mgr, scrp, util.get_config().get('keymap'))
# player_manager.ground_shattering_wave()
# player_manager.consuming_flames(True)
#
macro = EndOfTheWorld2_4(None, config=util.get_config())
macro.load_and_process_platform_map('msv/resources/platform/end_of_the_world2_4.platform')
macro.loop_entry()

