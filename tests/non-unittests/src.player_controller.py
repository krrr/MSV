from src.player_controller import PlayerController
from src.input_manager import InputManager
import time
from src.screen_processor import ScreenProcessor
from src.screen_processor import StaticImageProcessor
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

player_con.holy_symbol()
player_con.teleport_right()
# player_cntrlr.optimized_horizontal_move(36)
# player_cntrlr.teleport_right()
# time.sleep(0.5)
# player_cntrlr.teleport_right()
