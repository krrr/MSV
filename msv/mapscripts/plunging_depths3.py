import time
from msv.macro_script import MacroController
from msv.util import random_number
import msv.directinput_constants as dc


class PlungingDepths3(MacroController):
    ROPE_X = 38

    def __init__(self, conn=None, config=None):
        super().__init__(conn, config)
        self.player_manager.blind_poses = [(52, 73)]

    def loop(self):
        ### Rune Detector
        self._rune_detect_solve()
        if not self.current_platform_hash:  # navigate failed, skip rest logic, go unstick fast
            return

        if self.player_manager.is_skill_usable('true_arachnid_reflection'):
            self.player_manager.use_set_skill('true_arachnid_reflection')

        if self.current_platform_hash == '8a395a67':  # bottom
            self.player_manager.dbl_jump_move(self.ROPE_X, attack=True)
            stone_tremor_usable = self.player_manager.is_skill_usable('stone_tremor')
            if stone_tremor_usable:
                time.sleep(0.04)
                self.keyhandler.single_press(dc.DIK_RIGHT)
                time.sleep(0.04)
                self.player_manager.stone_tremor()
                time.sleep(0.03)
                self.keyhandler.single_press(dc.DIK_LEFT)

            self.player_manager.rope_up(wait=False)
            time.sleep(0.85 + random_number(0.05))
            self.player_manager.gold_banded_cudgel()
            time.sleep(0.3 + random_number(0.1))

            # self.player_manager.horizontal_move_goal(121)
            # self.player_manager.dbl_jump_left(attack=True)
            # time.sleep(0.02)
            # self.player_manager.horizontal_move_goal(89)
            # self.player_manager.dbl_jump_left(wait=False)
            # time.sleep(0.04)
            # self.player_manager.gold_banded_cudgel()
            # time.sleep(0.45 + random_number(0.03))  # wait drop
            # self.keyhandler.single_press(dc.DIK_RIGHT, duration=0.15)
            self.player_manager.dbl_jump_right(attack=True)
            self.update()
            self.navigate_to_platform('93a07f38')
        elif self.current_platform_hash == '93a07f38':  # left upper
            self.player_manager.horizontal_move_goal(81)
            self.player_manager.dbl_jump_right(wait=False)

            time.sleep(0.5 + random_number(0.08))
            # self.player_manager.worldreaver()
            time.sleep(0.6 + random_number(0.1))

            self.update()
            self.player_manager.horizontal_move_goal(135)
        else:
            self.navigate_to_platform('8a395a67')  # bottom

        # Finished
        return 0
