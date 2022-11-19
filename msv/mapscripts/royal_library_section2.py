import time
from msv.macro_script import MacroController
from msv.util import random_number
import msv.directinput_constants as dc


class RoyalLibrarySection2(MacroController):
    BURNING_SOUL_X = 85
    ROPE_X = 130

    def __init__(self, conn=None, config=None):
        super().__init__(conn, config)
        self.pattern_count = 0
        self.vacuum_pet_picking = config.get('vacuum_pet_picking', False)

    def loop(self):
        ### Rune Detector
        self._rune_detect_solve()
        if not self.current_platform_hash:  # navigate failed, skip rest logic, go unstick fast
            return

        if self.current_platform_hash == '9b0eddb6':  # bottom
            self.buff_skills()

            self.player_manager.dbl_jump_move(self.ROPE_X, attack=True)

            stone_tremor_usable = self.player_manager.is_skill_usable('stone_tremor')
            if stone_tremor_usable:
                self.keyhandler.single_press(dc.DIK_RIGHT)
                time.sleep(0.04)
                self.player_manager.stone_tremor()

            self.keyhandler.single_press(dc.DIK_LEFT)
            time.sleep(0.1 + random_number(0.02))
            self.player_manager.rope_up(True)
            time.sleep(0.9 + random_number(0.03))
            if not self.vacuum_pet_picking and self.pattern_count > 10:  # pick money
                self.pickup_money()
            else:
                self.player_manager.horizontal_move_goal(121)
                self.player_manager.dbl_jump_left(attack=True)
                time.sleep(0.02)
                self.player_manager.horizontal_move_goal(89)
                self.player_manager.dbl_jump_left(wait=False)
                time.sleep(0.04)
                self.player_manager.gold_banded_cudgel()
                time.sleep(0.45 + random_number(0.03))  # wait drop
                self.keyhandler.single_press(dc.DIK_RIGHT, duration=0.15)
                self.pattern_count += 1
        else:
            self.navigate_to_platform('9b0eddb6')  # bottom

        # Finished
        return 0

    def pickup_money(self):
        self.logger.info('pick up money')

        self.update()
        # top right
        self.navigate_to_platform('b6de4b5d')
        self.player_manager.horizontal_move_goal(139)
        self.player_manager.as_you_will_fan()
        self.keyhandler.single_press(dc.DIK_LEFT)
        self.player_manager.as_you_will_fan()
        time.sleep(0.5 + random_number(0.1))
        self.poll_conn()
        self.update()
        # top right 2
        self.navigate_to_platform('dc949bac')
        self.player_manager.as_you_will_fan()
        self.player_manager.horizontal_move_goal(101)
        self.player_manager.as_you_will_fan()
        time.sleep(0.6 + random_number(0.1))
        self.player_manager.dbl_jump_left()
        self.poll_conn()
        self.update()
        # top right 3
        self.navigate_to_platform('75726649')
        self.keyhandler.single_press(dc.DIK_RIGHT)
        self.player_manager.as_you_will_fan()
        self.player_manager.as_you_will_fan()
        time.sleep(0.6 + random_number(0.1))
        self.player_manager.dbl_jump_left()
        self.poll_conn()
        self.update()
        # # top left
        self.navigate_to_platform('1a3b14b8')
        self.player_manager.as_you_will_fan()
        self.player_manager.as_you_will_fan()
        time.sleep(0.6 + random_number(0.1))
        self.player_manager.horizontal_move_goal(42)
        time.sleep(0.4)
        self.poll_conn()
        self.update()
        # middle left
        self.navigate_to_platform('cb641f75')
        self.player_manager.horizontal_move_goal(43)
        self.player_manager.as_you_will_fan()
        self.player_manager.as_you_will_fan()
        time.sleep(0.3 + random_number(0.1))
        self.player_manager.horizontal_move_goal(57)
        time.sleep(0.4)


        self.pattern_count = 0
