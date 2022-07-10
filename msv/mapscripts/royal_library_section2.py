import time
from msv.macro_script import MacroController
from msv.util import random_number
import msv.directinput_constants as dc


class RoyalLibrarySection2(MacroController):
    BURNING_SOUL_X = 85
    ROPE_X = 130

    def __init__(self, conn=None, config=None):
        super().__init__(conn, config)
        self.screen_processor.detect_friend = False
        self.pattern_count = 0
        self.vacuum_pet_picking = config.get('vacuum_pet_picking', False)

    def loop(self):
        ### Rune Detector
        self._rune_detect_solve()
        if not self.current_platform_hash:  # navigate failed, skip rest logic, go unstick fast
            return

        if self.current_platform_hash == '9b0eddb6':  # bottom
            self.buff_skills()

            if self.player_manager.is_skill_usable('burning_soul_blade'):  # place burning soul blade
                self.player_manager.dbl_jump_move(self.BURNING_SOUL_X, attack=True)
                self.player_manager.burning_soul_blade(set=True)

            self.player_manager.dbl_jump_move(self.ROPE_X, attack=True)

            rising_rage_usable = self.player_manager.is_skill_usable('rising_rage')
            if rising_rage_usable:
                self.keyhandler.single_press(dc.DIK_RIGHT)
                time.sleep(0.04)
                self.player_manager.rising_rage()

            self.keyhandler.single_press(dc.DIK_LEFT)
            time.sleep(0.1 + random_number(0.02))
            self.player_manager.teleport_up(False)
            time.sleep(0.9 + random_number(0.03))
            if not self.vacuum_pet_picking and self.pattern_count > 10:  # pick money
                self.pickup_money()
            else:
                if not rising_rage_usable and self.player_manager.is_skill_usable('worldreaver'):
                    self.player_manager.worldreaver()
                self.player_manager.horizontal_move_goal(121)
                self.player_manager.dbl_jump_left(attack=True)
                time.sleep(0.02)
                self.player_manager.horizontal_move_goal(89)
                self.player_manager.dbl_jump_left(wait=False)
                time.sleep(0.04)
                self.player_manager.bean_blade()
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
        self.player_manager.raging_blow()
        self.keyhandler.single_press(dc.DIK_LEFT)
        self.player_manager.raging_blow()
        time.sleep(0.5 + random_number(0.1))
        self.poll_conn()
        self.update()
        # top right 2
        self.navigate_to_platform('dc949bac')
        self.player_manager.raging_blow()
        self.player_manager.horizontal_move_goal(101)
        self.player_manager.raging_blow()
        time.sleep(0.6 + random_number(0.1))
        self.player_manager.dbl_jump_left()
        self.poll_conn()
        self.update()
        # top right 3
        self.navigate_to_platform('75726649')
        self.keyhandler.single_press(dc.DIK_RIGHT)
        self.player_manager.raging_blow()
        self.player_manager.raging_blow()
        time.sleep(0.6 + random_number(0.1))
        self.player_manager.dbl_jump_left()
        self.poll_conn()
        self.update()
        # # top left
        self.navigate_to_platform('1a3b14b8')
        self.player_manager.raging_blow()
        self.player_manager.raging_blow()
        time.sleep(0.6 + random_number(0.1))
        self.player_manager.horizontal_move_goal(42)
        time.sleep(0.4)
        self.poll_conn()
        self.update()
        # middle left
        self.navigate_to_platform('cb641f75')
        self.player_manager.horizontal_move_goal(43)
        self.player_manager.raging_blow()
        self.player_manager.raging_blow()
        time.sleep(0.3 + random_number(0.1))
        self.player_manager.horizontal_move_goal(57)
        time.sleep(0.4)


        self.pattern_count = 0
