import time
from macro_script import MacroController
import directinput_constants as dc


# void current 3 script
class LabyrinthInterior1(MacroController):
    LEFT_X = 66
    RIGHT_X = 85

    def __init__(self, keymap, log_queue, cmd_queue):
        super().__init__(keymap=keymap, log_queue=log_queue, cmd_queue=cmd_queue)
        self.last_pickup_money_time = time.time() + 20

    def loop(self):
        ### Rune Detector
        self._rune_detect_solve()
        if not self.current_platform_hash:  # navigate failed, skip rest logic, go unstick fast
            return

        # set skills
        if not self.elite_boss_detected and self.set_skills(combine=True):
            return

        # pickup money
        if (not self.elite_boss_detected and self.current_platform_hash == 'd5ad102e' and
                time.time() - self.last_pickup_money_time > self.pickup_money_interval):
            self.pickup_money()
            self.last_pickup_money_time = time.time()
            return

        if self.current_platform_hash == '4e54fb89':  # center left
            self.player_manager.horizontal_move_goal(self.RIGHT_X)
            self.keyhandler.single_press(dc.DIK_RIGHT)
            self.player_manager.shikigami_haunting()
            self.player_manager.exorcist_charm(False)
            time.sleep(1.27 + abs(self.player_manager.random_duration(0.04)))
            self.player_manager.teleport_left()
            time.sleep(0.1 + abs(self.player_manager.random_duration(0.05)))
            self.player_manager.shikigami_haunting(wait_delay=False)
            time.sleep(0.1 + abs(self.player_manager.random_duration(0.05)))
            self.player_manager.teleport_down()
            time.sleep(0.07)
        elif self.current_platform_hash == 'd5ad102e':  # bottom
            if self.player_manager.x > self.RIGHT_X + self.player_manager.horizontal_goal_offset:
                self.player_manager.shikigami_haunting_sweep_move(self.RIGHT_X)
            elif self.player_manager.x < self.LEFT_X + 5:
                self.player_manager.shikigami_haunting(wait_delay=False)
                time.sleep(0.02)
                self.player_manager.teleport_right()
                time.sleep(0.07)
                self.update()
                self.player_manager.horizontal_move_goal(self.RIGHT_X)
                self.keyhandler.single_press(dc.DIK_RIGHT)
            else:
                self.player_manager.shikigami_haunting()
                self.player_manager.horizontal_move_goal(self.RIGHT_X)
                self.keyhandler.single_press(dc.DIK_RIGHT)
            self.player_manager.shikigami_haunting(wait_delay=False)
            self.player_manager.teleport_up()
            time.sleep(0.07)
        else:
            self.navigate_to_platform('4e54fb89')  # center left

        ### Other buffs
        self.buff_skills(yuki=False)
        time.sleep(0.04)

        # Finished
        self.loop_count += 1
        return 0

    def pickup_money(self):
        self.logger.info('pick up money')
        self.navigate_to_platform('d5ad102e')
        self.player_manager.shikigami_haunting_sweep_move(self.terrain_analyzer.platforms['d5ad102e'].end_x - 2)
        self.player_manager.stay(0.5 + abs(self.player_manager.random_duration(0.05)))
        self.update()
        self.check_cmd_queue()
        self.navigate_to_platform('6c45ab2d')

        self.check_cmd_queue()

        self.player_manager.horizontal_move_goal(self.terrain_analyzer.platforms['6c45ab2d'].end_x - 4)
        self.player_manager.stay(0.5 + abs(self.player_manager.random_duration(0.05)))
        self.player_manager.shikigami_haunting_sweep_move(self.terrain_analyzer.platforms['6c45ab2d'].start_x + 5)
        if time.time() - self.player_manager.last_skill_use_time['yaksha_boss'] >= 10:
            self.player_manager.last_skill_use_time['yaksha_boss'] = 0  # force setting yaksha boss
            self._place_set_skill('yaksha_boss')
        else:
            self.player_manager.stay(0.5 + abs(self.player_manager.random_duration(0.05)))
        self.player_manager.horizontal_move_goal(self.terrain_analyzer.platforms['6923e252'].start_x + 5)
        self.update()
        self.check_cmd_queue()
        self.navigate_to_platform('6923e252')

        ### top right
        self.player_manager.shikigami_haunting_sweep_move(self.terrain_analyzer.platforms['6923e252'].end_x - 4)
        self.player_manager.stay(0.5 + abs(self.player_manager.random_duration(0.05)))
        self.player_manager.shikigami_haunting_sweep_move(self.terrain_analyzer.platforms['6923e252'].start_x)
        self.player_manager.jumpl()
        time.sleep(0.06)
        self.player_manager.shikigami_haunting(wait_delay=False)
        self.player_manager.teleport_left()
        time.sleep(0.04)
        self.update()
        self.check_cmd_queue()
        self.navigate_to_platform('8ff668b3')

        p = self.terrain_analyzer.platforms['8ff668b3']
        middle = (p.end_x + p.start_x) / 2
        self.player_manager.horizontal_move_goal(middle)
        self.player_manager.stay(0.65 + abs(self.player_manager.random_duration(0.05)), goal_x=middle)
        self.keyhandler.single_press(dc.DIK_RIGHT)
        self.player_manager.shikigami_haunting()
        self.player_manager.shikigami_haunting()
        self.player_manager.stay(0.1 + abs(self.player_manager.random_duration(0.05)), goal_x=middle)
        self.keyhandler.single_press(dc.DIK_LEFT)
        self.player_manager.shikigami_haunting()
        self.player_manager.shikigami_haunting()
        self.player_manager.stay(0.1 + abs(self.player_manager.random_duration(0.05)), goal_x=middle)
        self.update()
        self.check_cmd_queue()
        self.navigate_to_platform('4e54fb89')  # center left

        x = self.terrain_analyzer.platforms['4e54fb89'].start_x + 4
        self.player_manager.shikigami_haunting_sweep_move(x)
        self.player_manager.stay(0.75 + abs(self.player_manager.random_duration(0.05)), goal_x=x)
        self.player_manager.teleport_down()
        time.sleep(0.04)
        self.player_manager.shikigami_haunting(wait_delay=False)
        self.player_manager.stay(0.5 + abs(self.player_manager.random_duration(0.05)), goal_x=x)
        self.player_manager.teleport_right()