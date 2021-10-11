from msv.player_controller import PlayerController
from msv.input_manager import InputManager
import time
from msv.screen_processor import ScreenProcessor
from msv.screen_processor import StaticImageProcessor
from win32gui import SetForegroundWindow

wcap = ScreenProcessor()
scrp = StaticImageProcessor(wcap)
hwnd = wcap.get_game_hwnd()
kbd_mgr = InputManager()
player_con = PlayerController(kbd_mgr, scrp)

SetForegroundWindow(hwnd)
time.sleep(0.3)
scrp.update_image()
print('minimap rect', scrp.get_minimap_rect())
print('player marker', scrp.find_player_minimap_marker())
player_con.update()

print('player pos', player_con.x, player_con.y)

# player_con.dbl_jump_right(True, True)
# player_con.teleport_up()

# player_cntrlr.optimized_horizontal_move(36)
# player_cntrlr.teleport_right()
# time.sleep(0.5)
# player_cntrlr.teleport_right()
