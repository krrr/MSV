from src.player_controller import PlayerController
from src.keystate_manager import KeyboardInputManager
import time
from src.screen_processor import ScreenProcessor
from src.screen_processor import StaticImageProcessor
from win32gui import SetForegroundWindow

wcap = ScreenProcessor()
scrp = StaticImageProcessor(wcap)
hwnd = wcap.ms_get_screen_hwnd()
kbd_mgr = KeyboardInputManager()
player_cntrlr = PlayerController(kbd_mgr, scrp)

SetForegroundWindow(hwnd)
time.sleep(0.6)
scrp.update_image()
print('minimap rect', scrp.get_minimap_rect())
print('player marker', scrp.find_player_minimap_marker())
player_cntrlr.update()

print('player pos', player_cntrlr.x, player_cntrlr.y)

# player_cntrlr.optimized_horizontal_move(36)
player_cntrlr.shikigami_haunting_sweep_move(110)
# player_cntrlr.teleport_right()
# time.sleep(0.5)
# player_cntrlr.teleport_right()
