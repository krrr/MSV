import time
from msv.macro_script import MacroController
from msv.util import random_number
import msv.directinput_constants as dc


# Labyrinth Interior 1 script
class LabyrinthInterior1(MacroController):
    LEFT_X = 66
    RIGHT_X = 85

    def __init__(self, conn, config):
        super().__init__(conn, config)
        self.last_pickup_money_time = time.time() + 20

    def loop(self):
        ### Rune Detector
        self._rune_detect_solve()
        if not self.current_platform_hash:  # navigate failed, skip rest logic, go unstick fast
            return

        # set skills
        if (not self.elite_boss_detected and self.current_platform_hash in ('4e54fb89', '6c45ab2d') and
                self.set_skills(combine=True)):
            return

        # pickup money
        if (not self.elite_boss_detected and self.current_platform_hash == 'd5ad102e' and
                time.time() - self.last_pickup_money_time > self.pickup_money_interval):
            self.pickup_money()
            self.last_pickup_money_time = time.time()
            return

        if self.current_platform_hash == '4e54fb89':  # center left
            if self.player_manager.x > self.RIGHT_X - 4:
                self.player_manager.horizontal_move_goal(self.RIGHT_X)
                self.keyhandler.single_press(dc.DIK_RIGHT)
                self.player_manager.shikigami_haunting()
                self.player_manager.exorcist_charm(False)
                time.sleep(1.27 + random_number(0.04))
                self.player_manager.teleport_left()
                time.sleep(0.1 + random_number(0.05))
            else:
                self.player_manager.horizontal_move_goal(self.LEFT_X)

            self.player_manager.shikigami_haunting(wait_delay=False)
            time.sleep(0.1 + random_number(0.05))
            self.player_manager.teleport_down()
            time.sleep(0.07)
        elif self.current_platform_hash == 'd5ad102e':  # bottom
            if self.player_manager.x > self.RIGHT_X + self.player_manager.horizontal_goal_offset:
                self.player_manager.shikigami_haunting_sweep_move(self.RIGHT_X)
            elif self.player_manager.x < self.LEFT_X + 6:
                self.player_manager.shikigami_haunting(wait_delay=False)
                time.sleep(0.03)
                self.player_manager.teleport_right()
                time.sleep(0.09)
                self.update()
                self.player_manager.horizontal_move_goal(self.RIGHT_X)
                self.keyhandler.single_press(dc.DIK_RIGHT)
            else:
                self.player_manager.shikigami_haunting()
                self.player_manager.horizontal_move_goal(self.RIGHT_X)
                self.keyhandler.single_press(dc.DIK_RIGHT)
            self.player_manager.shikigami_haunting(wait_delay=False)
            time.sleep(0.02)
            self.player_manager.teleport_up()
            time.sleep(0.07)
        else:
            self.navigate_to_platform('4e54fb89')  # center left

        ### Other buffs
        self.buff_skills(yuki=False)

        # Finished
        return 0

    def pickup_money(self):
        self.logger.info('pick up money')
        if self.player_manager.is_skill_usable('true_arachnid_reflection'):
            self.player_manager.use_set_skill('true_arachnid_reflection')
            self.navigate_to_platform('d5ad102e')
        elif self.player_manager.is_skill_usable('spirit_domain'):
            self.navigate_to_platform('d5ad102e')  # go to bottom first
            self.player_manager.use_set_skill('spirit_domain')
            self.player_manager.vanquisher_move(dc.DIK_RIGHT, 5 + random_number(0.5))
        else:
            self.navigate_to_platform('d5ad102e')
        self.player_manager.shikigami_haunting_sweep_move(self.terrain_analyzer.platforms['d5ad102e'].end_x - 2)
        self.player_manager.stay(0.5 + random_number(0.05))
        self.update()
        self.poll_conn()
        self.navigate_to_platform('6c45ab2d')

        self.poll_conn()

        ### center right
        self.player_manager.horizontal_move_goal(self.terrain_analyzer.platforms['6c45ab2d'].end_x - 4)
        self.player_manager.stay(0.5 + random_number(0.05))
        self.player_manager.shikigami_haunting_sweep_move(self.terrain_analyzer.platforms['6c45ab2d'].start_x + 5)
        if time.time() - self.player_manager.last_skill_use_time['yaksha_boss'] >= 10:
            self.player_manager.last_skill_use_time['yaksha_boss'] = 0  # force setting yaksha boss
            self._place_set_skill('yaksha_boss')
        else:
            self.player_manager.stay(0.5 + random_number(0.05))
        self.player_manager.horizontal_move_goal(self.terrain_analyzer.platforms['6923e252'].start_x + 5)
        self.update()
        self.poll_conn()
        self.navigate_to_platform('6923e252')

        ### top right
        self.player_manager.shikigami_haunting_sweep_move(self.terrain_analyzer.platforms['6923e252'].end_x - 4)
        self.player_manager.stay(0.5 + random_number(0.05))
        self.player_manager.shikigami_haunting_sweep_move(self.terrain_analyzer.platforms['6923e252'].start_x)
        self.player_manager.jump_left(wait=False)
        time.sleep(0.06)
        self.player_manager.shikigami_haunting(wait_delay=False)
        self.player_manager.teleport_left()
        time.sleep(0.04)
        self.update()
        self.poll_conn()
        self.navigate_to_platform('8ff668b3')

        ### top left
        p = self.terrain_analyzer.platforms['8ff668b3']
        middle = (p.end_x + p.start_x) / 2
        self.player_manager.horizontal_move_goal(middle-2)
        self.player_manager.stay(0.85 + random_number(0.05), middle - 2)
        self.keyhandler.single_press(dc.DIK_LEFT)
        self.player_manager.shikigami_haunting()
        self.player_manager.shikigami_haunting()
        self.player_manager.horizontal_move_goal(middle+2)
        self.player_manager.shikigami_haunting()
        self.player_manager.shikigami_haunting()
        self.player_manager.stay(0.1 + random_number(0.05), middle + 2)
        self.player_manager.teleport_left()
        time.sleep(0.06)
        self.update()
        self.poll_conn()
        self.navigate_to_platform('4e54fb89')  # center left

        x = self.terrain_analyzer.platforms['4e54fb89'].start_x + 5
        self.player_manager.shikigami_haunting_sweep_move(x)
        self.player_manager.stay(0.7 + random_number(0.05), goal_x=x)
        self.player_manager.teleport_down()
        time.sleep(0.02)
        self.player_manager.shikigami_haunting(wait_delay=False)
        self.player_manager.stay(0.4 + random_number(0.05), goal_x=x)
        self.player_manager.teleport_right()
