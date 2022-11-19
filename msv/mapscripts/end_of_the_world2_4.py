import time
from msv import directinput_constants as dc
from msv.util import random_number
from msv.macro_script import MacroController


# End of the World 2-4 script
# noinspection PyPep8Naming
class EndOfTheWorld2_4(MacroController):
    CENTER_X = 83

    def __init__(self, conn=None, config=None):
        super().__init__(conn, config)
        self.first_loop = True
        self.screen_processor.detect_friend = False

    def loop(self):
        ### Rune Detector
        self._rune_detect_solve()
        if not self.current_platform_hash:  # navigate failed, skip rest logic, go unstick fast
            return

        if self.first_loop:
            self.player_manager.miracle_tonic()
            self.place_set_skills()
            self.first_loop = False

        if self.current_platform_hash == '268ff3c9':  # middle
            self.player_manager.iron_fan_gale2222(95)
            self.player_manager.horizontal_move_goal(92)
            self.navigate_to_platform('444ae3dc')
            self.keyhandler.single_press(dc.DIK_RIGHT)
            self.player_manager.ground_shattering_wave()
            self.player_manager.consuming_flames(True)
        elif self.current_platform_hash == '444ae3dc':
            if not self.place_set_skills():
                self.navigate_to_platform('268ff3c9')
        else:
            self.navigate_to_platform('268ff3c9')

        ### Other buffs
        self.buff_skills()

        # Finished
        return 0

    def place_set_skills(self):
        # set skills
        if not self.elite_boss_detected and self.set_skills(combine=True):
            if self.first_loop:
                return True

            self.player_manager.dbl_jump_move(31)
            self.player_manager.drop()
            self.player_manager.drop()
            self.update()
            self.navigate_to_platform('059285fa')

            if self.player_manager.is_skill_usable('tiger_of_songyu') and self.player_manager.is_skill_usable('miracle_tonic'):  # place tiger
                self.player_manager.miracle_tonic()
                time.sleep(3 + random_number(0.1))
                self.player_manager.use_set_skill('tiger_of_songyu')
            elif self.player_manager.is_skill_usable('true_arachnid_reflection'):
                self.player_manager.use_set_skill('true_arachnid_reflection')

            self.keyhandler.single_press(dc.DIK_RIGHT)
            self.player_manager.dbl_jump_right(attack=True)
            self.player_manager.dbl_jump_right(attack=True, wait=False)
            time.sleep(0.5)

            return True
        return False
