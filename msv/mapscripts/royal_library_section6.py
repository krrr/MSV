import random
import time
from msv.macro_script import MacroController
from msv.util import random_number
import msv.input_manager as km
import msv.directinput_constants as dc


# Labyrinth Interior 1 script
class RoyalLibrarySection6(MacroController):
    ROPE_X = 141

    def __init__(self, keymap=km.DEFAULT_KEY_MAP, conn=None, config=None):
        super().__init__(keymap, conn, config)
        self.screen_processor.detect_friend = False
        self.pattern_count = 0

    def loop(self):
        ### Rune Detector
        self._rune_detect_solve()
        if not self.current_platform_hash:  # navigate failed, skip rest logic, go unstick fast
            return

        ### Buffs
        if self.current_platform_hash == 'b716ce7a':  # bottom
            self.buff_skills()

        if self.current_platform_hash == 'b716ce7a':  # bottom
            self.player_manager.dbl_jump_move(self.ROPE_X, attack=True)
            self.keyhandler.single_press(dc.DIK_LEFT)
            self.player_manager.rope_up(False)
            if self.pattern_count > 6:  # pick money
                time.sleep(0.75)
                self.player_manager.dbl_jump_left(wait=False, third=True)
                time.sleep(0.25 + random_number(0.02))
                self.player_manager.blades_of_destiny()
                time.sleep(0.05 + random_number(0.01))
                if random.random() < 0.5:
                    self.player_manager.blade_fury()
                else:
                    time.sleep(0.7 + random_number(0.05))
                self.pickup_money()
            else:
                time.sleep(0.41)
                self.player_manager.dbl_jump_left(wait=False, third=True)
                time.sleep(0.02)
                self.player_manager.blades_of_destiny()
                time.sleep(0.1)
                self.pattern_count += 1
        elif self.current_platform_hash == 'c6cd2ea8':
            if self.player_manager.x > 103:
                self.player_manager.horizontal_move_goal(103)
            self.keyhandler.direct_press(dc.DIK_LEFT)
            time.sleep(0.1 + random_number(0.05))
            self.player_manager.dbl_jump_left(third=True, jump=True, wait=False)
            self.keyhandler.direct_release(dc.DIK_LEFT)
            time.sleep(0.55 + random_number(0.02))
        elif self.current_platform_hash == '054d2c83':  # left upper
            if self.player_manager.x > 17:
                self.player_manager.dbl_jump_left(third=True, attack=True)
            self.keyhandler.single_press(dc.DIK_RIGHT)
            self.player_manager.drop(wait=False)
            time.sleep(0.03)
            self.player_manager.blade_tornado()
            time.sleep(0.1 + random_number(0.01))
        elif self.current_platform_hash == 'f004d199':  # left lower
            self.player_manager.drop(wait=False)
            time.sleep(0.55 + random_number(0.01))
        else:
            self.navigate_to_platform('b716ce7a')  # center left

        # Finished
        return 0

    def pickup_money(self):
        self.logger.info('pick up money')

        self.player_manager.update()
        self.player_manager.horizontal_move_goal(108)
        self.keyhandler.direct_press(dc.DIK_LEFT)
        self.player_manager.teleport_up()
        self.keyhandler.direct_release(dc.DIK_LEFT)
        # center top
        self.poll_conn()
        self.update()
        self.navigate_to_platform('2a5939b2')
        self.player_manager.blade_fury()
        self.player_manager.dbl_jump_left(wait=False, third=True, jump=True)
        time.sleep(1.2 + random_number(0.08))
        # left top
        self.player_manager.blade_fury()
        self.poll_conn()
        self.update()
        self.navigate_to_platform('08556150')
        if self.player_manager.x > 32:
            self.player_manager.horizontal_move_goal(32)
        self.keyhandler.direct_press(dc.DIK_LEFT)
        time.sleep(0.1 + random_number(0.04))
        self.player_manager.dbl_jump_left(wait=False)
        self.keyhandler.direct_release(dc.DIK_LEFT)
        time.sleep(0.72 + random_number(0.01))
        self.keyhandler.single_press(dc.DIK_RIGHT)
        self.player_manager.jump()

        self.pattern_count = 0
