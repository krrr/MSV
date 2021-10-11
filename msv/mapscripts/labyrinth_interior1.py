import random
import time
from msv.macro_script import MacroController
from msv.util import random_number
import msv.directinput_constants as dc


# Labyrinth Interior 1 script
class LabyrinthInterior1(MacroController):
    X = 84

    def __init__(self, keymap, conn, config):
        super().__init__(keymap, conn, config)
        self.screen_processor.detect_friend = False
        self.set_skill_count = 0

    def loop(self):
        ### Rune Detector
        self._rune_detect_solve()
        if not self.current_platform_hash:  # navigate failed, skip rest logic, go unstick fast
            return

        # set skills
        if (not self.elite_boss_detected and self.current_platform_hash in ('4e54fb89', '6c45ab2d', 'd5ad102e')
                and self.player_manager.is_skill_usable('dark_flare')):
            if self.set_skill_count % 2 == 0 and self.set_skill_count > 0:  # pickup money
                self.pickup_money()
            else:
                if self.current_platform_hash == '4e54fb89' and self.player_manager.is_skill_usable('dark_lord_omen'):
                    self.player_manager.use_set_skill('dark_lord_omen')
                self.set_skills(combine=True)
            self.set_skill_count += 1
            return

        if self.current_platform_hash == '4e54fb89':  # center left
            if abs(self.player_manager.x - self.X) > 4:
                self.player_manager.horizontal_move_goal(self.X)

            self.left_right_showdown()
            time.sleep(0.1 + random_number(0.1))

            # dummy key
            if random.random() < 0.2:
                self.keyhandler.single_press(dc.DIK_PERIOD)
            if random.random() < 0.3:
                self.keyhandler.single_press(dc.DIK_8)
        else:
            if self.current_platform_hash == '6c45ab2d':
                self.keyhandler.single_press(dc.DIK_LEFT)
                self.player_manager.shurrikane()
            self.navigate_to_platform('4e54fb89')  # center left

        ### Other buffs
        self.buff_skills()

        # Finished
        return 0

    def pickup_money(self):
        self.logger.info('pick up money')
        if self.player_manager.is_skill_usable('true_arachnid_reflection'):
            self.player_manager.use_set_skill('true_arachnid_reflection')
        elif self.player_manager.is_skill_usable('dark_lord_omen'):
            self.player_manager.use_set_skill('dark_lord_omen')

        self.player_manager.dbl_jump_move(self.terrain_analyzer.platforms['4e54fb89'].start_x + 2)
        self.player_manager.stay(0.1 + random_number(0.05))
        if self.current_platform_hash == '4e54fb89':
            self.player_manager.drop()
        self.update()
        self.poll_conn()

        # bottom
        self.keyhandler.single_press(dc.DIK_RIGHT)
        self.player_manager.shurrikane()
        self.player_manager.dbl_jump_right()
        self.update()
        self._place_set_skill('dark_flare')
        self.player_manager.stay(0.1 + random_number(0.05))
        self.update()
        self.poll_conn()
        self.navigate_to_platform('6c45ab2d')
        self.poll_conn()

        ### center right
        p = self.terrain_analyzer.platforms['6c45ab2d']
        middle = (p.end_x + p.start_x) // 2
        self.player_manager.horizontal_move_goal(middle)
        if self.player_manager.is_skill_usable('nightmare_invite'):
            self._place_set_skill('nightmare_invite')
        self.left_right_showdown()
        self.player_manager.stay(0.5 + random_number(0.05))
        self.update()
        self.poll_conn()
        self.navigate_to_platform('6923e252')

        ### top right
        self.player_manager.dbl_jump_right()
        self.player_manager.stay(0.5 + random_number(0.05))
        self.player_manager.dbl_jump_move(self.terrain_analyzer.platforms['6923e252'].start_x + 3)
        self.player_manager.stay(0.15 + random_number(0.05))
        self.update()
        self.poll_conn()
        self.navigate_to_platform('8ff668b3')

        ### top left
        p = self.terrain_analyzer.platforms['8ff668b3']
        middle = (p.end_x + p.start_x) // 2
        self.player_manager.horizontal_move_goal(middle-2)
        self.player_manager.stay(0.85 + random_number(0.05), middle - 2)
        self.keyhandler.single_press(dc.DIK_LEFT)
        self.player_manager.showdown()
        self.player_manager.showdown()
        self.player_manager.horizontal_move_goal(middle+2)
        self.player_manager.showdown()
        self.player_manager.showdown()
        self.player_manager.stay(0.1 + random_number(0.05), middle + 2)
        time.sleep(0.06)
        self.update()
        self.poll_conn()
        self.navigate_to_platform('4e54fb89')  # center left

    def left_right_showdown(self):
        left = random.random() < 0.5
        self.keyhandler.single_press(dc.DIK_LEFT if left else dc.DIK_RIGHT)
        self.player_manager.showdown()
        time.sleep(0.2 + random_number(0.05))
        self.keyhandler.single_press(dc.DIK_RIGHT if left else dc.DIK_LEFT)
        self.player_manager.showdown()
        time.sleep(0.05 + random_number(0.1))
