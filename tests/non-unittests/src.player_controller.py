import util
from msv.player_controller import PlayerController
from msv.input_manager import InputManager
from msv.screen_processor import ScreenProcessor
from msv.screen_processor import StaticImageProcessor
from win32gui import SetForegroundWindow
from msv.mapscripts.train_no_dest1 import TrainNoDest1

wcap = ScreenProcessor()
scrp = StaticImageProcessor(wcap)
hwnd = wcap.get_game_hwnd()
SetForegroundWindow(hwnd)
kbd_mgr = InputManager()
# player_manager = PlayerController(kbd_mgr, scrp, util.get_config().get('keymap'))
# player_manager.dbl_jump_left(attack=True)
# player_manager.dbl_jump_left(attack=True)


macro = TrainNoDest1(config=util.get_config())
macro.load_and_process_platform_map('msv/resources/platform/train_no_dest1.platform')
macro.loop_entry()

