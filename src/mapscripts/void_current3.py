import time
from macro_script import MacroController
import directinput_constants as dc


# void current 3 script
class Vc3MacroController(MacroController):
    LEFT_X = 36
    RIGHT_X = 57

    def __init__(self, keymap, log_queue, cmd_queue):
        super().__init__(keymap=keymap, log_queue=log_queue, cmd_queue=cmd_queue)
        self.last_pickup_money_time = time.time() + 20

    def loop(self):
        ret = self._loop_common_job()
        if ret != 0:
            return ret

        ### Rune Detector
        self._rune_detect_solve()
        if not self.current_platform_hash:  # navigate failed, skip rest logic, go unstick fast
            return

        # set skills
        if (not self.elite_boss_detected and self.current_platform_hash not in ('24aa7e4b', 'b0397a99')
                and self.set_skills(combine=True)):
            return

        # pickup money
        if (not self.elite_boss_detected and self.current_platform_hash == '24aa7e4b' and
                time.time() - self.last_pickup_money_time > self.pickup_money_interval):
            self.pickup_money()
            self.last_pickup_money_time = time.time()
            return

        if self.current_platform_hash == '24aa7e4b':  # top of 3
            self.player_manager.horizontal_move_goal(self.LEFT_X)

            self.keyhandler.single_press(dc.DIK_LEFT)
            self.player_manager.shikigami_haunting()
            self.player_manager.teleport_right()
            time.sleep(0.04)
            self.update()
            self.player_manager.horizontal_move_goal(self.RIGHT_X)
            self.player_manager.exorcist_charm(False)
            time.sleep(1.24 + abs(self.player_manager.random_duration(0.04)))
            self.player_manager.teleport_down()
            time.sleep(0.07)
        elif self.current_platform_hash == 'b0397a99':  # left bottom of 3
            self.player_manager.horizontal_move_goal(self.LEFT_X)
            self.keyhandler.single_press(dc.DIK_LEFT)
            self.player_manager.shikigami_haunting()
            self.player_manager.teleport_up()
            time.sleep(0.07)
        elif self.current_platform_hash == '88ad2786':  # right bottom of 3
            if self.player_manager.x > self.RIGHT_X + self.player_manager.horizontal_goal_offset:
                self.player_manager.shikigami_haunting_sweep_move(self.RIGHT_X)
            else:
                self.player_manager.horizontal_move_goal(self.RIGHT_X)
                self.keyhandler.single_press(dc.DIK_RIGHT)
            self.player_manager.shikigami_haunting()
            self.player_manager.teleport_left()
            time.sleep(0.07)
        elif self.current_platform_hash == '11609f5a':  # bottom
            if self.player_manager.x < 50:
                self.navigate_to_platform('b0397a99')  # left bottom of 3
            else:
                self.player_manager.shikigami_haunting_sweep_move(self.RIGHT_X)
                self.navigate_to_platform('88ad2786')  # right bottom of 3
        else:
            self.navigate_to_platform('88ad2786')  # right bottom of 3

        ### Other buffs
        self.buff_skills()
        time.sleep(0.04)

        # Finished
        self.loop_count += 1
        return 0

    def pickup_money(self):
        self.logger.info('pick up money')
        self.navigate_to_platform('aff7769e')
        self.player_manager.shikigami_haunting_sweep_move(self.terrain_analyzer.platforms['aff7769e'].end_x - 3)
        self.player_manager.teleport_right()
        time.sleep(0.1)
        self.player_manager.shikigami_haunting(False)
        time.sleep(0.03)
        self.player_manager.teleport_right()
        time.sleep(0.07)
        self.update()
        self.navigate_to_platform('ffdc3934')
        self.player_manager.shikigami_haunting_sweep_move(self.terrain_analyzer.platforms['ffdc3934'].end_x - 3)
        self.navigate_to_platform('ea784df3')
        self.player_manager.shikigami_haunting_sweep_move(self.terrain_analyzer.platforms['ea784df3'].end_x - 3)
        self.player_manager.shikigami_haunting_sweep_move(self.terrain_analyzer.platforms['ea784df3'].start_x + 3)

        self.check_cmd_queue()
        self.update()
        # Quick other player sound notify
        if self.screen_processor.find_other_player_marker():
            self.alert_sound()

        self.navigate_to_platform('88ad2786')
        self._place_set_skill('yaksha_boss')

        self.navigate_to_platform('ca8bd0be')
        self.player_manager.shikigami_haunting_sweep_move(self.terrain_analyzer.platforms['ca8bd0be'].end_x - 3)
        self.navigate_to_platform('11609f5a')  # bottom
        self.player_manager.shikigami_haunting_sweep_move(5)
        self.player_manager.teleport_up()
        time.sleep(0.07)
        self.player_manager.shikigami_haunting_sweep_move(self.LEFT_X)
