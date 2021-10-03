import random
import time
from msv.macro_script import MacroController
from msv.util import random_number
import msv.directinput_constants as dc


class ToolKishin(MacroController):
    def __init__(self, keymap, conn, config):
        super().__init__(keymap, conn, config)
        self.x = self.y = None
        self.screen_processor.detect_friend = False

    def find_current_platform(self):
        return 'dummy'

    def loop(self):
        if self.loop_count == 0:  # first loop
            self.x = self.player_manager.x
        elif abs(self.player_manager.x - self.x) > 8:
            self.player_manager.horizontal_move_goal(self.x)

        if (time.time() - self.player_manager.last_skill_use_time['kishin_shoukan'] >
                self.player_manager.skill_cooldown['kishin_shoukan'] + random_number(3.5)):
            self.player_manager.use_set_skill('kishin_shoukan')

        if random.random() < 0.35:
            self.keyhandler.single_press(dc.DIK_RIGHT)
            self.player_manager.shikigami_haunting(False)
            self.player_manager.teleport_right()
            time.sleep(0.3 + random_number(0.2))

            if random.random() < 0.7:
                self.keyhandler.single_press(dc.DIK_LEFT)
                self.player_manager.shikigami_haunting(False)
            self.player_manager.wait_teleport_cd()
            self.player_manager.teleport_left()
        else:
            move_duration = 0.2 + random_number(0.15)
            self.keyhandler.press_key(dc.DIK_LEFT)
            time.sleep(move_duration)
            self.keyhandler.release_key(dc.DIK_LEFT)
            time.sleep(0.04 + random_number(0.03))
            self.player_manager.shikigami_haunting(False)
            time.sleep(0.2 + random_number(0.1))

            self.keyhandler.press_key(dc.DIK_RIGHT)
            time.sleep(move_duration)
            self.keyhandler.release_key(dc.DIK_RIGHT)
            time.sleep(0.04 + random_number(0.03))
            self.player_manager.shikigami_haunting(False)

        ### Other buffs
        self.player_manager.haku_reborn()

        time.sleep(0.4 + random_number(0.2))